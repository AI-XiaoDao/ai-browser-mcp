# -*- coding: utf-8 -*-
r"""R1 守卫: browser_get_text 在**指定了子框架**时不得回退到主框架(否则是"带 frame_id 却读到主框架内容")。

问题(静态可证, 由 G1c 审计发现): selector 分支与"全文"分支的 CDP 求值失败后,
下游只认 `__MCP_NO_ELEM__` / `__MCP_TEXT__` / `__MCP_NO_BODY__` 三种哨兵前缀;
而框架感知入口在框架不存在时返回的是 `{"error":"未找到框架…"}` —— 匹配不上任何一种,
于是继续往下走到 `原生执行JS并等待` / `提交异步取文本任务`, 而这两条路**根本不看 frame_id**,
一律在**主框架**取值。结果: 传错 frame_id 也一样"成功", 只是答案是主框架的 —— 最难发现的一类假答案。

本补丁在两处回退链路之前各插一个守卫(锚点唯一、行数增加、括号净额不变)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

# 锚点1: selector 分支的原生回退前
A1 = '                    // 第二跳: 显式走**原生同步 JS**(复用既有 helper, 它内部用 取主浏览器 因而尊重 browser_id)。'
G1 = '''                    // 约束: 指定了子框架时**到此为止**。下面的原生链路(原生执行JS并等待 / 填表框架 / 异步回执)
                    // 都不看 frame_id, 一律去主框架取值 —— 那会让"带了 frame_id 却读到主框架内容"这种
                    // 最难发现的假答案通过。故这里把 CDP 的报错(含"未找到框架")原样上报。
                    变量 gt子框架 <类型 = 文本型>
                    gt子框架 = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                    如果 (gt子框架 != "" && gt子框架 != "main" && gt子框架 != "主框架")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "子框架(" + gt子框架 + ")内取文本失败: " + 取文本左边 (js取文值, 300) + " | 已在回退到主框架之前中止(后续回退链路不看 frame_id, 会读到主框架内容)"))
                    }
'''

# 锚点2: 全文分支的异步回退前
A2 = '''                    变量 fullText <类型 = 文本型>
                    fullText = MCP命令服务器.提交异步取文本任务 (browser)'''
G2 = '''                    // 约束: 同 selector 分支 —— 指定子框架时不得回退到主框架取全文。
                    变量 gt全文框架 <类型 = 文本型>
                    gt全文框架 = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                    如果 (gt全文框架 != "" && gt全文框架 != "main" && gt全文框架 != "主框架")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "子框架(" + gt全文框架 + ")内取全文失败: " + 取文本左边 (全文JS, 300) + " | 已在回退到主框架之前中止(回退链路不看 frame_id)"))
                    }
'''


def nets(lines):
    p = b = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
            continue
        k = 0
        in_str = False
        while k < len(ln):
            c = ln[k]
            if in_str:
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '(':
                    p += 1
                elif c == ')':
                    p -= 1
                elif c == '{':
                    b += 1
                elif c == '}':
                    b -= 1
            k += 1
    return p, b


def find_anchor(lines, anchor):
    """按**连续多行**匹配锚点, 返回所有起始下标(单行锚点同样适用)。"""
    a = anchor.split('\n')
    return [i for i in range(len(lines) - len(a) + 1) if lines[i:i + len(a)] == a]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')

    pos = {}
    for tag, anchor in (('A1', A1), ('A2', A2)):
        hits = find_anchor(lines, anchor)
        assert len(hits) == 1, '锚点 %s 命中 %d 次(期望 1)' % (tag, len(hits))
        pos[tag] = hits[0]
    assert not any('gt子框架' in l or 'gt全文框架' in l for l in lines), '已应用过'

    p0, b0 = nets(lines)
    i1 = pos['A1']
    i2 = pos['A2']
    assert i1 < i2, '锚点顺序异常 %d %d' % (i1, i2)

    out = lines[:i1] + G1.split('\n')[:-1] + lines[i1:]
    # 插入 G1 后 A2 位置右移: 重新定位
    hits2 = find_anchor(out, A2)
    assert len(hits2) == 1, '插入后 A2 命中 %d 次' % len(hits2)
    i2b = hits2[0]
    out = out[:i2b] + G2.split('\n')[:-1] + out[i2b:]

    p1, b1 = nets(out)
    # 约束: 计数器的口径是"字符串字面量之外的圆/花括号", 但不跳过 `//` 注释 —— 注释里的括号会让净额不为 0,
    # 故这里只要求**替换前后完全一致**(不变式), 不要求等于 0。
    assert (p1, b1) == (p0, b0), '括号净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    assert len(out) == len(lines) + G1.count('\n') + G2.count('\n'), \
        '行数增量异常 %d -> %d' % (len(lines), len(out))

    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        chk = open(TARGET, 'rb').read()
        assert not chk.startswith(b'\xef\xbb\xbf') and b'\r\n' not in chk, '写盘后校验失败'
        print('已写入 %s (行数 %d -> %d)' % (TARGET, len(lines), len(out)))
    else:
        print('[dry-run] 在 %d 行前插入 %d 行守卫; 在 %d 行前插入 %d 行守卫; 行数 %d -> %d'
              % (i1 + 1, G1.count('\n'), i2 + 1, G2.count('\n'), len(lines), len(out)))
        print('括号净额 圆 %d->%d 花 %d->%d' % (p0, p1, b0, b1))


main()
