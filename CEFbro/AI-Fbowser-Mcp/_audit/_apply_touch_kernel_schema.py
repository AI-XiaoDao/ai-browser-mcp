# -*- coding: utf-8 -*-
r"""修正上一批 patch 在 touch 三件套上留下的**无效 schema 拼接**，改用 多属性Schema文本 正确声明 kernel。

问题(被 `_audit/verify_missing_params.py` 抓出, 3 条 FAIL):
  上一批我在 `双XY_Schema文本 ("x","y","X","Y")` **之后**追加 `+ "," + 属性项JSON(...)`,
  但 `双XY_Schema文本` 返回的是**整段** `"inputSchema":{...}` 字符串（见 MCP_Server.wsv:11799,
  它以 `}` 收尾并含 required 列表），在其后拼接属性片段会得到**非法 JSON** ——
  运行时工具 schema 里仍然只有 x/y（实测 `properties=['x','y']`），即"改了但没生效"。
正确做法: 整段替换为 `多属性Schema文本 (属性项JSON(...) + ... , "\"x\",\"y\"")`，保持 x/y 必填不变。

用法: py -3 _audit\_apply_touch_kernel_schema.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

TOOLS = ["browser_touch_press", "browser_touch_move", "browser_touch_release"]

BAD = ('双XY_Schema文本 ("x", "y", "X", "Y") + "," + 属性项JSON ("kernel", "boolean", '
       '"true=内核级注入(会破坏本会话 CDP 通道, 需重启恢复); 默认 false=CDP 派发")')

GOOD = ('多属性Schema文本 (属性项JSON ("x", "integer", "X") + "," + 属性项JSON ("y", "integer", "Y") + "," + '
        '属性项JSON ("kernel", "boolean", "true=内核级注入(会破坏本会话 CDP 通道, 需重启恢复); 默认 false=CDP 派发"), '
        '"\\"x\\",\\"y\\"")')

PLAIN = '双XY_Schema文本 ("x", "y", "X", "Y")'


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
    lines = txt.split('\n')
    b0 = balance(txt)
    done = []
    for tool in TOOLS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if BAD in lines[i]:
            lines[i] = lines[i].replace(BAD, GOOD, 1)
            done.append('%s: 无效拼接 → 多属性Schema文本' % tool)
        elif GOOD in lines[i]:
            done.append('%s: 已是正确写法' % tool)
        else:
            assert lines[i].count(PLAIN) == 1, '%s 找不到原始 schema 片段' % tool
            lines[i] = lines[i].replace(PLAIN, GOOD, 1)
            done.append('%s: 原始 XCT 片段 → 多属性SchemaText' % tool)
    out = '\n'.join(lines)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server.wsv: 行数不变 %d; 处理 %d 个工具' % (len(lines), len(done)))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert c.count('多属性Schema文本 (属性项JSON ("x", "integer", "X")') >= 3
        assert BAD not in c, '无效拼接仍残留'
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
