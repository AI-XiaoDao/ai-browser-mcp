# -*- coding: utf-8 -*-
"""收敛上一版的"零命中快速失败": 改为**只记录不提前失败**。

为什么改(我自己的正对照逼出来的):
  上一版在 `locations 为空 且 未传 url` 时立即失败。但诊断 `_audit/diag_breakpoint_locations.py`
  实测: 本页**所有**已注册脚本的 `url` 都是空串(8/8, 含我注入的内联脚本), 于是任何 urlRegex
  都得到 `"locations":[]`。也就是说"0 位置"**并不等于**"永远不可能命中" ——
  若之后有带真实 URL 的脚本加载(真实站点的外部脚本、SPA 动态加载), urlRegex 会在那时重新解析并命中。
  立即失败就会把这种**合法等待**误判成失败, 反而制造用户最反感的"失败 + 反复换方法"。

保留的部分(这些都在修复"静默假成功", 与上面无关):
  · 0 命中 -> 诚实失败(原来**无条件** success:true);
  · 记录停止原因;
  · 默认预算 60000ms -> 12000ms;
  · 新增 completed / stop_reason 字段。
新增: 把"断点当时 0 位置"作为**诊断信息**记下来, 并只在 0 命中的失败信息里附带 —— 信息保留, 但不越权替调用方结束等待。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '零命中改为只记录-写入前')

FASTFAIL = '\n'.join([
    '            // ★ 加(可诊断性 + 不白等): 断点匹配 0 个位置且调用方**不会导航**时, 永远不可能命中,',
    '            //   立即失败并给出可行动指引, 而不是把 max_ms 预算等满(原来会白等 60000ms×N)。',
    '            如果 (MCP命令服务器.CDP断点是否零命中 (autoBpRaw) && autoNavUrl == "")',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "断点匹配 0 个脚本位置(locations 为空), 且未传 url(不会导航) -> 该断点永远不可能命中, 已立即失败而不等待 | breakpoint: " + autoBpUrl + " | 可行动: ①用 browser_reverse_get_possible_breakpoints 查该脚本真正可下断的行/列(混淆脚本常整包压成一行, 按行下断必然 0 位置) ②确认 url_regex 能匹配到目标脚本 ③若需加载时触发, 传 url 让本工具自动导航"))',
    '            }',
])

REPLACED = '\n'.join([
    '            // 记录"下断当时是否 0 位置"作为**诊断信息**, 但**不据此提前失败**。',
    '            // ★ 实测依据(为什么不能提前失败): 本页所有已注册脚本的 url 都是空串(8/8), 于是任何',
    '            //   urlRegex 都得到 locations:[]; 而 0 位置**不等于**永远不可能命中 —— 之后若有带真实',
    '            //   URL 的脚本加载(真实站点外部脚本/SPA 动态加载), urlRegex 会在那时重新解析并命中。',
    '            //   提前失败会把这种合法等待误判成失败, 反而制造"失败 + 反复换方法"。',
    '            //   故这里只置标志, 由 0 命中时的失败信息附带说明(信息保留, 不越权结束等待)。',
    '            autoBp零命中 = MCP命令服务器.CDP断点是否零命中 (autoBpRaw)',
])

DECL_OLD = '\n'.join([
    '            变量 auto停止原因 <类型 = 文本型>',
    '            auto停止原因 = "未知(循环提前结束)"',
])
DECL_NEW = '\n'.join([
    '            变量 auto停止原因 <类型 = 文本型>',
    '            auto停止原因 = "未知(循环提前结束)"',
    '            变量 autoBp零命中 <类型 = 逻辑型 值 = 假>',
])

MSG_OLD = ('                返回 (MCP_响应构建.命令失败 (命令ID, "未捕获到任何断点命中(0 hits) | 停止原因: " '
           '+ auto停止原因 + " | 常见原因: ①断点匹配 0 个位置 ②等待窗口内页面没有执行到该代码 '
           '③未传 url 且当前页面本就不会触发该代码 | 可行动: 用 browser_reverse_get_possible_breakpoints '
           '查可下断行列; 或用 browser_debugger_flow 并传 url 触发; 或显式传更大的 max_ms"))')

MSG_NEW = '\n'.join([
    '                变量 auto零命中说明 <类型 = 文本型>',
    '                如果 (autoBp零命中)',
    '                {',
    '                    auto零命中说明 = " | 注: 下断当时该 urlRegex 匹配到 0 个脚本位置(locations 为空) —— 若之后有带真实 URL 的脚本加载仍可能命中, 可传 url 让本工具导航触发, 或显式传更大的 max_ms 继续等"',
    '                }',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "未捕获到任何断点命中(0 hits) | 停止原因: " + auto停止原因 + auto零命中说明 + " | 常见原因: ①断点此刻未匹配到脚本位置 ②等待窗口内页面没有执行到该代码 ③未传 url 且当前页面本就不会触发该代码 | 可行动: 用 browser_reverse_get_possible_breakpoints 查可下断行列; 或用 browser_debugger_flow 并传 url 触发; 或显式传更大的 max_ms"))',
])


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    c = rd(CORE)
    for label, old in (("快速失败块", FASTFAIL), ("声明处", DECL_OLD), ("0命中失败信息", MSG_OLD)):
        n = c.count(old)
        print("[%s] 锚点出现 %d 次" % (label, n))
        if n != 1:
            print("!! 预期 1 次, 中止")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(CORE, os.path.join(BAK, os.path.basename(CORE)))
    print("已备份到 %s" % BAK)
    c = c.replace(FASTFAIL, REPLACED).replace(DECL_OLD, DECL_NEW).replace(MSG_OLD, MSG_NEW)
    wr(CORE, c)
    print("OK: 零命中改为只记录 + 0命中失败信息附带该诊断")
    with io.open(CORE, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
