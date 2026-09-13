# -*- coding: utf-8 -*-
r"""第131轮: 全量扫 323 个工具 → 12 个工具共 20 个"实现真读却未声明"的参数, 一次补齐。

数据来源(本轮实测, 非审计结论): `_audit/_show_branch_params.py --brief`(全量 323 工具) +
`--diff <工具>`(取类型)。扫描器本轮还修了两个自身缺陷:
  · 花括号配平**要跳过字符串字面量**(分支体里内嵌 JS 的 `{}` 会把分支切到几十行之外,
    实测把 `browser_debugger_script_source` 误报出 60 多条 MISSING);
  · 不给工具名时默认**全量扫**。
修好后全量结果: **323 个工具, 有差异 48 个**, 其中 **MISSING(实现读了却代理看不到)= 12 个工具 / 20 个参数** —— 本补丁全部补齐。
(其余 36 个是 EXTRA: schema 声明了但分支体内没读到 —— 绝大多数是**委托给共享助手**读取所致
 (如 debugger_flow→执行Debugger断点流程JSON、kernel_reactor→分派_反应器), 属扫描器已知局限, **不动**。)

各参数类型均由实现里的读取函数判定(整数/文本/逻辑), 不是猜的。

用法: py -3 _audit\_apply_round131_schema.py [--apply]
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

P = '属性项JSON ("%s", "%s", "%s")'
PLAN = {
    "browser_back": [
        P % ("wait_for_load", "boolean", "是否等待载入完成(实现会读; 与 navigate 同名参数)"),
        P % ("async_only", "boolean", "true=立刻返回 task_id 不等结果"),
    ],
    "browser_forward": [
        P % ("wait_for_load", "boolean", "是否等待载入完成(实现会读; 与 navigate 同名参数)"),
        P % ("async_only", "boolean", "true=立刻返回 task_id 不等结果"),
    ],
    "browser_reload": [P % ("async_only", "boolean", "true=立刻返回 task_id 不等结果")],
    "browser_navigate": [P % ("async_only", "boolean", "true=立刻返回 task_id 不等结果(与 wait_for_load 互斥语义)")],
    "browser_cdp_event": [P % ("event", "text", "CDP 事件名(与 event_name 等价; 实现两者都读)")],
    "browser_console_eval": [P % ("file", "text", "从本地文件读取要执行的 JS(绝对路径) —— **大脚本请用本参数**, 避免走 HTTP 通道约 1MB 的 arguments 限制")],
    "browser_file_dialog": [
        P % ("file_path", "text", "要回给页面的文件路径(与 path 等价; 实现两者都读)"),
        P % ("path", "text", "同 file_path(任给其一)"),
    ],
    "browser_intercept": [
        P % ("width", "integer", "popup_config: 弹窗宽度"),
        P % ("height", "integer", "popup_config: 弹窗高度"),
        P % ("x", "integer", "popup_config: 弹窗 X 位置"),
        P % ("y", "integer", "popup_config: 弹窗 Y 位置"),
    ],
    "browser_reverse_extract": [P % ("script_id", "text", "限定在某个脚本内提取(取自 browser_reverse_search_script 的 scriptId)")],
    "browser_reverse_instrument_script": [P % ("verify", "boolean", "false=跳过安装后的自检(默认会自检并如实回报 verified:false 与卡死风险)")],
    "browser_reverse_websocket": [P % ("requestId", "text", "CDP 原生拼写, 等价于 request_id(action=query 用)")],
    "mcp_help": [
        P % ("name", "text", "查单个工具: 传工具名可得该工具的完整说明(实现会读 name 或 tool)"),
        P % ("tool", "text", "同 name(任给其一)"),
    ],
}
# 行尾形如 `, "\"a\",\"b\""))` / `, ""))` / `, 假))`(单参数Schema的必填开关) → 在最后实参之前插入新属性
TAIL = re.compile(r', ("(?:\\"|[^"])*"|假|真)\)\)\s*$')
MYFILE = os.path.join(ROOT, '_audit', '_show_branch_params.py')


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    done = []
    for tool, props in PLAN.items():
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        new_names = re.findall(r'属性项JSON \("([a-zA-Z_0-9]+)"', ' + '.join(props))
        already = [n for n in new_names if ('"%s"' % n) in lines[i]]
        todo = [p for p, n in zip(props, new_names) if n not in already]
        if not todo:
            done.append('%s (已存在)' % tool)
            continue
        m = TAIL.search(lines[i])
        if m:
            add = ' + "," + ' + ' + "," + '.join(todo)
            lines[i] = lines[i][:m.start()] + add + ', ' + m.group(1) + '))'
            done.append('%s +%d(扩展已有 schema)' % (tool, len(todo)))
        else:
            # 该工具**原本没有 schema**(只有描述, 形如 …, "描述")) —— 直接补一个多属性 schema
            assert lines[i].rstrip().endswith('")'), '%s 行尾既非 schema 也非纯描述: …%s' % (tool, lines[i][-60:])
            body = ' + "," + '.join(todo)
            lines[i] = lines[i].rstrip()[:-2] + '", 多属性Schema文本 (' + body + ', ""))'
            done.append('%s +%d(新建 schema)' % (tool, len(todo)))
    out = '\n'.join(lines)
    print('MCP_Server.wsv: 处理 %d 个工具:' % len(PLAN))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        for must in ('"wait_for_load", "boolean"', '"script_id", "text"', '"verify", "boolean"',
                     '"requestId", "text"', '"file_path", "text"', '"width", "integer"'):
            assert must in c, '缺少 %s' % must
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
