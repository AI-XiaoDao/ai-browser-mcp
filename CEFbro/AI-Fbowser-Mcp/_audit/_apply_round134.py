# -*- coding: utf-8 -*-
r"""第134轮: `browser_execute_js/evaluate` 的 `file` 参数**实现了但报错误导** + `code_base64` **未声明**。

实测(本轮, `_audit/probe_exec_file_scope.py`):
  · 运行目录**内**的 .js → `file` 正常工作(execute_js 与 evaluate 都返回 RUN_DIR_FILE_OK:5);
  · 运行目录**外**的路径(如 C:\Windows\notepad.exe 或 %TEMP%) → 报
    `缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径)` —— 而调用方**明明给了 file**,
    真实原因是安全守卫 `验证安全路径 (code, 真)` 只允许**进程运行目录内**的文件。
    ⇒ 误导性失败: 调用方会以为参数没传到, 于是换方法反复试错(正是本目标要消灭的体验)。
  · `code_base64` 是源码里既有的**免转义通道**(实测可用), 但两个工具的 schema **都没声明它**。

修法:
  ① Core 的 execute_js 缺参报错改为**可行动**: 指明三种传法 + 运行目录限制 + 怎样规避;
  ② schema 补声明 `code_base64`, 并把 `file` 的描述补上"仅限运行目录内"这一真实约束。

用法: py -3 _audit\_apply_round134.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

MSG_OLD = '返回 (MCP_响应构建.命令失败 (命令ID, "缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径)"))'
MSG_NEW = ('返回 (MCP_响应构建.命令失败 (命令ID, "未能取得要执行的 JS: 三种传法都试过了 | ① code(内联字符串) '
           '② code_base64(Base64, 免转义) ③ file(文件路径) —— **file 仅允许进程运行目录内的文件**(安全守卫), '
           '目录外路径会被拒绝; 若你确实给了 file 却看到本错误, 请把脚本放到运行目录下, 或改用 code/code_base64 | '
           '另: file 指向的文件必须存在且非空"))')

FILE_DESC_OLD = '属性项JSON ("file", "text", "JS文件路径(与code二选一)")'
FILE_DESC_NEW = ('属性项JSON ("file", "text", "JS文件路径(与code二选一)。**限制(实测): 只允许进程运行目录内的文件**'
                 ' —— 目录外/不存在/空文件都会被拒绝") + "," + '
                 '属性项JSON ("code_base64", "text", "JS代码的 Base64(免转义, 适合含引号/换行/超大脚本)")')

EV_FILE_OLD = '属性项JSON ("file", "text", "JS文件路径(推荐:避免转义)")'
EV_FILE_NEW = ('属性项JSON ("file", "text", "JS文件路径(推荐:避免转义)。**限制(实测): 仅允许进程运行目录内的文件**") + "," + '
               '属性项JSON ("code_base64", "text", "JS代码的 Base64(免转义; 与 code/file 三选一)")')


def main():
    ctxt = io.open(CORE, encoding='utf-8').read()
    has_cr = '\r' in ctxt
    # 该误导性报错在 Core 里有**两处**(execute_js 与另一个 JS 工具), 两处都要改成可行动
    assert ctxt.count(MSG_OLD) == 2, 'Core 报错锚点 %d(期望 2)' % ctxt.count(MSG_OLD)
    c_out = ctxt.replace(MSG_OLD, MSG_NEW)
    print('MCP_Server_Core.wsv: 2 处"取不到 JS"报错已改为可行动(点明运行目录限制与三种传法)')

    lines = io.open(SERVER, encoding='utf-8').read().split('\n')
    done = []
    for tool, old, new in (('browser_execute_js', FILE_DESC_OLD, FILE_DESC_NEW),
                           ('browser_evaluate', EV_FILE_OLD, EV_FILE_NEW)):
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if 'code_base64' in lines[i]:
            done.append('%s (已声明)' % tool)
            continue
        assert lines[i].count(old) == 1, '%s file 锚点 %d' % (tool, lines[i].count(old))
        lines[i] = lines[i].replace(old, new, 1)
        done.append('%s 补 code_base64 + file 限制说明' % tool)
    s_out = '\n'.join(lines)
    print('MCP_Server.wsv:')
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        c = io.open(CORE, encoding='utf-8').read()
        s = io.open(SERVER, encoding='utf-8').read()
        assert '进程运行目录内的文件' in c and ('\r' in c) == has_cr
        for tool in ('browser_execute_js', 'browser_evaluate'):
            ln = [l for l in s.split('\n') if '添加工具JSON ("%s"' % tool in l][0]
            assert '"code_base64"' in ln, '%s 未声明 code_base64' % tool
        assert '\r' not in s
        print('已写入 Core + Server 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
