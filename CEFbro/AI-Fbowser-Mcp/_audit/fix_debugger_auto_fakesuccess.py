# -*- coding: utf-8 -*-
"""修复 browser_debugger_auto 的"静默假成功", 并新增"断点零命中"判别 helper。

=== 缺陷(违反本项目核心不变量「不静默假成功」) ===
`MCP_Server_Core.wsv` 的 browser_debugger_auto 分支, 循环等待断点命中, 超时只 `跳出循环`,
随后**无条件** `auto汇总.加入逻辑值成员 ("success", 真)` —— 于是"一次命中都没有"也返回
`success:true, hits:0`。而该工具默认等待预算 60000ms/次, 客户端常 15s 就放弃,
调用方拿到的是"超时 + 假成功"的双重坏结论。

=== 同时新增 helper: CDP断点是否零命中 ===
`Debugger.setBreakpointByUrl` 在 urlRegex/行号匹配到 **0 个脚本位置**时**仍然返回成功**
(带 `"locations":[]`)。所以"断点设置成功"和"永远不可能命中"是两件事。
- 若调用方**不传 url**(不会导航), 0 位置就是终局失败 -> 应立即失败, 而不是把预算等满;
- 若调用方**传了 url**(会导航), 新脚本加载后 urlRegex 会重新解析 -> 此时不该提前失败。

本脚本用 chr(92)/chr(34) 拼接, 规避转义歧义; 每处锚点断言恰好出现 1 次; 先备份。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '调试器假成功与零命中判定-写入前')
B = chr(92)
Q = chr(34)


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


# ---------- 编辑A: 在 MCP_Server.wsv 新增 helper ----------
A_ANCHOR = '\n'.join([
    '        errText = 取CDP同步结果错误 (存储JSON)',
    '        返回 (寻找文本 (errText, ' + Q + 'already exists' + Q + ', 0, 假) != -1)',
    '    }',
])
A_NEW = '\n'.join([
    '',
    '    方法 CDP断点是否零命中 <公开 静态 类型 = 逻辑型 @输出名 = "CDPBreakpointHasZeroLocations" @强制输出 = 真>',
    '    参数 存储JSON <类型 = 文本型 @输出名 = "StoreJSON">',
    '    {',
    '        // 为什么要单独一个 helper: Debugger.setBreakpointByUrl 在 urlRegex/行号匹配到 **0 个**',
    '        // 脚本位置时**仍然返回成功**(带 "locations":[])。所以"断点设置成功"与"永远不可能命中"',
    '        // 是两件事 —— browser_debugger_auto/flow 曾据此把 0 命中判成设置成功, 然后死等到超时。',
    '        // 判据: 同步**成功** 且 结果体里 locations 是空数组。',
    '        // 用法注意: 只有"调用方不会导航"时 0 位置才是终局失败; 若会导航, urlRegex 会在新脚本上重新解析。',
    '        如果 (CDP同步结果是否成功 (存储JSON) == 假)',
    '        {',
    '            返回 (假)',
    '        }',
    '        变量 体文本 <类型 = 文本型>',
    '        体文本 = 取CDP同步结果体文本 (存储JSON)',
    '        如果 (体文本 == "")',
    '        {',
    '            返回 (假)',
    '        }',
    '        如果 (寻找文本 (体文本, ' + Q + B + Q + 'locations' + B + Q + ':[]' + Q + ', 0, 假) != -1)',
    '        {',
    '            返回 (真)',
    '        }',
    '        返回 (寻找文本 (体文本, ' + Q + B + Q + 'locations' + B + Q + ': []' + Q + ', 0, 假) != -1)',
    '    }',
])

# ---------- 编辑B: auto 默认等待预算 ----------
B_OLD = '                autoMaxMs = 60000'
B_NEW = '\n'.join([
    '                // 原默认 60000ms/次: 远超常见客户端耐心(实测台账客户端 15s 就放弃),',
    '                // 结果是"客户端超时 + 服务端还在等" —— 调用方只会看到一次次失败。',
    '                // 压到 12000ms: 让服务端**在客户端放弃之前**给出明确结论(命中或诚实的失败)。',
    '                // 需要更久可显式传 max_ms。',
    '                autoMaxMs = 12000',
])

# ---------- 编辑C: 零命中快速失败(不传 url 时) ----------
C_ANCHOR = '\n'.join([
    '            如果 (MCP命令服务器.CDP设置断点结果是否成功 (autoBpRaw) == 假)',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "断点设置失败: " + MCP命令服务器.取CDP同步结果错误 (autoBpRaw)))',
    '            }',
])
C_ADD = '\n'.join([
    '            // ★ 加(可诊断性 + 不白等): 断点匹配 0 个位置且调用方**不会导航**时, 永远不可能命中,',
    '            //   立即失败并给出可行动指引, 而不是把 max_ms 预算等满(原来会白等 60000ms×N)。',
    '            如果 (MCP命令服务器.CDP断点是否零命中 (autoBpRaw) && autoNavUrl == "")',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "断点匹配 0 个脚本位置(locations 为空), 且未传 url(不会导航) -> 该断点永远不可能命中, 已立即失败而不等待 | breakpoint: " + autoBpUrl + " | 可行动: ①用 browser_reverse_get_possible_breakpoints 查该脚本真正可下断的行/列(混淆脚本常整包压成一行, 按行下断必然 0 位置) ②确认 url_regex 能匹配到目标脚本 ③若需加载时触发, 传 url 让本工具自动导航"))',
    '            }',
])

# ---------- 编辑D: 记录停止原因 ----------
D1_OLD = '            变量 autoResults <类型 = 文本数组类>'
D1_NEW = '\n'.join([
    '            变量 autoResults <类型 = 文本数组类>',
    '            变量 auto停止原因 <类型 = 文本型>',
    '            auto停止原因 = "未知(循环提前结束)"',
])

D2_OLD = '\n'.join([
    '                如果 (MCP命令服务器.MCP正在关闭 || MCP_编排分派.工作流应停止)',
    '                {',
    '                    跳出循环',
    '                }',
])
D2_NEW = '\n'.join([
    '                如果 (MCP命令服务器.MCP正在关闭 || MCP_编排分派.工作流应停止)',
    '                {',
    '                    auto停止原因 = "服务正在关闭或工作流已请求停止"',
    '                    跳出循环',
    '                }',
])

D3_OLD = '\n'.join([
    '                autoPausedRaw = MCP命令服务器.等待CDP事件 ("Debugger.paused", autoMaxMs, 假)',
    '                如果 (autoPausedRaw == "")',
    '                {',
    '                    跳出循环',
    '                }',
])
D3_NEW = '\n'.join([
    '                autoPausedRaw = MCP命令服务器.等待CDP事件 ("Debugger.paused", autoMaxMs, 假)',
    '                如果 (autoPausedRaw == "")',
    '                {',
    '                    auto停止原因 = "等待 Debugger.paused 超时(" + 到文本 (autoMaxMs) + "ms): 该窗口内页面未执行到断点位置"',
    '                    跳出循环',
    '                }',
])

# ---------- 编辑E: 0 命中 -> 诚实失败; 否则如实标注是否跑满 ----------
E_OLD = '\n'.join([
    '            变量 auto汇总 <类型 = YYJSON对象类>',
    '            auto汇总.创建自文本 ("{}")',
    '            auto汇总.加入逻辑值成员 ("success", 真)',
    '            auto汇总.加入整数成员 ("hits", autoHits)',
    '            auto汇总.加入文本成员 ("breakpoint", autoBpUrl)',
    '            auto汇总.加入文本成员 ("results", MCP_编排分派.步骤JSON片段列表到数组文本 (autoResults))',
    '            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, auto汇总.到可读文本 (YYJSON格式化选项.压缩)))',
])
E_NEW = '\n'.join([
    '            如果 (autoHits >= autoMaxHits)',
    '            {',
    '                auto停止原因 = "已达最大命中数(" + 到文本 (autoMaxHits) + ")"',
    '            }',
    '            // ★ 修(不静默假成功): 原来这里**无条件**写 success:真 —— 于是"一次命中都没有"',
    '            //   也会返回 success:true, hits:0, 调用方会据此以为断点链路是好的。',
    '            如果 (autoHits == 0)',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "未捕获到任何断点命中(0 hits) | 停止原因: " + auto停止原因 + " | 常见原因: ①断点匹配 0 个位置 ②等待窗口内页面没有执行到该代码 ③未传 url 且当前页面本就不会触发该代码 | 可行动: 用 browser_reverse_get_possible_breakpoints 查可下断行列; 或用 browser_debugger_flow 并传 url 触发; 或显式传更大的 max_ms"))',
    '            }',
    '            变量 auto汇总 <类型 = YYJSON对象类>',
    '            auto汇总.创建自文本 ("{}")',
    '            auto汇总.加入逻辑值成员 ("success", 真)',
    '            auto汇总.加入逻辑值成员 ("completed", autoHits >= autoMaxHits)',
    '            auto汇总.加入整数成员 ("hits", autoHits)',
    '            auto汇总.加入文本成员 ("stop_reason", auto停止原因)',
    '            auto汇总.加入文本成员 ("breakpoint", autoBpUrl)',
    '            auto汇总.加入文本成员 ("results", MCP_编排分派.步骤JSON片段列表到数组文本 (autoResults))',
    '            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, auto汇总.到可读文本 (YYJSON格式化选项.压缩)))',
])


def apply(path, edits, label):
    t = rd(path)
    for i, (old, new) in enumerate(edits, 1):
        n = t.count(old)
        if n != 1:
            print("!! [%s 编辑%d] 锚点出现 %d 次(预期 1), 中止未写入" % (label, i, n))
            return None
        t = t.replace(old, new)
    return t


def main():
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, CORE):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)

    s = apply(SRV, [(A_ANCHOR, A_ANCHOR + A_NEW)], 'MCP_Server')
    if s is None:
        return 1
    wr(SRV, s)
    print("OK [MCP_Server.wsv] 新增 helper CDP断点是否零命中")

    c = apply(CORE, [(B_OLD, B_NEW), (C_ANCHOR, C_ANCHOR + '\n' + C_ADD),
                     (D1_OLD, D1_NEW), (D2_OLD, D2_NEW),
                     (D3_OLD, D3_NEW), (E_OLD, E_NEW)], 'MCP_Server_Core')
    if c is None:
        return 1
    wr(CORE, c)
    print("OK [MCP_Server_Core.wsv] auto: 预算 60000->12000 / 零命中快速失败 / 停止原因 / 0命中诚实失败 / completed 标注")

    for p in (SRV, CORE):
        with io.open(p, 'rb') as f:
            raw = f.read()
        print("复核 %s: BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
