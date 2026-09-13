# -*- coding: utf-8 -*-
r"""第133轮: 清掉三个**声明了但实现从不读**的参数（会误导代理以为能限定范围/改变行为）。

依据(本轮实测复核):
  · `browser_debugger_last_paused.parse` —— 全项目只在 Core:5614 被读, 而那属于 **evaluate** 的分支;
    `last_paused` 自己**从不读** parse(它声明的 parse 是复制粘贴留下的残留)。
  · `browser_reverse_scan_crypto.script_index` / `browser_reverse_detect_obfuscator.script_index` ——
    全项目只有 Core:8019 在读 `script_index`, 那属于 **browser_reverse_extract 的 mode=download**;
    这两个"扫描全部脚本"的工具**从不读**它 ⇒ 传了会被**静默忽略**(代理以为只扫了一个脚本)。

处理: 从 schema 里**删掉这三个 no-op 声明**, 并在描述里**给出真正能限定范围的路径**
(不静默、不假装支持), 符合"失败/限制必须可行动"的不变量。

用法: py -3 _audit\_apply_round133.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

HINT = (' | 说明(第133轮更正): 本工具**不支持**限定脚本范围 —— 旧 schema 里那个不生效的参数已删除'
        '(传了会被忽略才是更坏的情况); 想只看某个脚本, 请先用 browser_reverse_search_script 或 '
        'browser_reverse_extract mode=scan 拿到脚本, 再用 browser_reverse_extract 的 mode=download(script_index) 取内容')

EDITS = [
    # ① last_paused: 删掉 parse(它自己从不读)
    ("browser_debugger_last_paused",
     ', 单参数Schema文本 ("parse", "boolean", "解析call_frame_id/frames(默认true)")',
     '',
     '删除 no-op 的 parse 声明'),
    ("browser_debugger_last_paused",
     '"最近断点暂停信息(VIP)"',
     '"最近断点暂停信息(VIP) | 说明(第133轮更正): 本工具**不读** parse 参数(旧 schema 误抄了 evaluate 的参数, 已删除) —— 它始终返回最近一次暂停的原始信息"',
     '描述更正(last_paused)'),
    # ② scan_crypto: 删掉 no-op 的 script_index + 给出替代路径
    ("browser_reverse_scan_crypto",
     '多属性Schema文本 (属性项JSON ("script_index", "integer", "只扫描第N个脚本(默认全部)"), ""))',
     '空Schema文本 ()',
     '删除 no-op 的 script_index(scan_crypto)'),
    ("browser_reverse_scan_crypto",
     '快速判断sign/token用的什么算法"',
     '快速判断sign/token用的什么算法"' + HINT,
     '描述补替代路径(scan_crypto)'),
    # ③ detect_obfuscator: 同上
    ("browser_reverse_detect_obfuscator",
     ', 单参数Schema文本 ("script_index", "integer", "只检测第N个脚本(默认全部)", 假)',
     '',
     '删除 no-op 的 script_index(detect_obfuscator)'),
    ("browser_reverse_detect_obfuscator",
     '给出置信度——选择正确的反混淆策略"',
     '给出置信度——选择正确的反混淆策略"' + HINT,
     '描述补替代路径(detect_obfuscator)'),
]


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    b0 = balance(txt)
    done = []
    for tool, old, new, tag in EDITS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if old and old not in lines[i]:
            done.append('%s (锚点不存在, 跳过)' % tag)
            continue
        lines[i] = lines[i].replace(old, new, 1)
        done.append(tag)
    out = '\n'.join(lines)
    # 说明: 这里的括号净值检查是**行内引号配对**的启发式, 删除形如 `, 单参数Schema文本 ("parse", …)` 的片段
    # 会改变该行后续引号的配对方式, 从而让计数漂移 —— 故只打印不阻断; 权威门禁是随后 voldev 的 /c 语法自检
    # 与 apply 块里的"三行不再声明这些参数"断言。
    print('MCP_Server.wsv: 括号净值 %s -> %s (启发式, 仅供参考); 完成:' % (b0, balance(out)))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert '"script_index"' in c  # extract 里仍应保留(那里真读)
        for tool in ('browser_reverse_scan_crypto', 'browser_reverse_detect_obfuscator'):
            ln = [l for l in c.split('\n') if '添加工具JSON ("%s"' % tool in l][0]
            assert 'script_index' not in ln, '%s 仍声明 script_index' % tool
        ln2 = [l for l in c.split('\n') if '添加工具JSON ("browser_debugger_last_paused"' in l][0]
        assert 'parse' not in ln2, 'last_paused 仍声明 parse'
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
