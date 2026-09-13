# -*- coding: utf-8 -*-
r"""修正 解析框架执行上下文 的 CDP 框架匹配: 由"按序号对齐"改为"按框架地址(URL)匹配 + 同名次消歧"。

实测根因(本轮新增证据): 跨域 iframe 是 **OOPIF**, 其框架**不在**页面级 Page.getFrameTree 里:
    CEF 清单 3 条 [main, samefr(6-), xofr(8-)]   vs   CDP 树 2 条 [main, srcdoc-samefr]
于是"CEF 第 i 项 == CDP 第 i 项"的假设在**存在 OOPIF 时**会错位:
  · 若 OOPIF 排在某个同源框架**之前**, 按 id/按名传那个同源框架 -> 序号对齐会落到**另一个框架**上,
    静默在错误的框架里读写(最难发现的一类错误答案); 传 OOPIF 自身则 CDP 侧根本没有对应项。
修正后的匹配规则:
  1. 先定位目标 CEF 框架(按 id / 按名 / 纯数字序号, 与原来一致);
  2. 取该框架的**地址**(类库 类_FBrowser_基础框架.取地址 = CefFrame::GetURL);
  3. 在 CDP 树里找**地址相同**的项; 若同地址有多项(如多个 about:srcdoc), 用"在 CEF 清单里同地址的第几个"
     作名次消歧(DFS 顺序在同类项之间保持一致);
  4. 一项都找不到 -> 返回 -1(**如实的"够不到"**, 例如 OOPIF); 绝不退回按序号猜。

安全: 只替换 解析框架执行上下文 里"抽取 CDP 框架 id"那一段, 锚点唯一, 括号净额不变。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

A_START = '        // CDP 框架树: 顺序即树序(主框架在前, 深度优先) —— 与 CEF 侧清单同序, 故按序号对齐即可。'
A_END = '''        如果 (命中ID == "")
        {
            返回 (-1)
        }'''

NEW = '''        // 目标框架的**地址**: 用于在 CDP 框架树里按键匹配。
        // 约束: **不能**再按"CEF 第 i 项 == CDP 第 i 项"对齐 —— 跨域 iframe(OOPIF)不在页面级
        // Page.getFrameTree 里(实测 CEF 3 条 vs CDP 2 条), 一旦 OOPIF 排在同源框架之前, 序号对齐
        // 会把请求落到**另一个框架**上, 静默在错误的框架里读写。
        变量 目标框架ID <类型 = 文本型>
        目标框架ID = ""
        如果 (目标序号 >= 0 && 目标序号 < id数组.取个数 ())
        {
            目标框架ID = id数组.取数据 (目标序号)
        }
        变量 目标地址 <类型 = 文本型>
        目标地址 = ""
        如果 (目标框架ID != "")
        {
            变量 目标框架对象 <类型 = 类_FBrowser_框架>
            目标框架对象 = 浏览器.取框架_ID (目标框架ID)
            如果 (目标框架对象.是否为空 () == 假 && 目标框架对象.是否有效 ())
            {
                目标地址 = 目标框架对象.取地址 ()
            }
        }
        // 同地址在 CEF 清单里的**名次**(同名次消歧用; 多个 about:srcdoc 之类会撞地址)
        变量 地址名次 <类型 = 整数>
        地址名次 = 0
        如果 (目标地址 != "")
        {
            变量 前位 <类型 = 整数>
            前位 = 0
            判断循环 (前位 < 目标序号)
            {
                变量 前框架对象 <类型 = 类_FBrowser_框架>
                前框架对象 = 浏览器.取框架_ID (id数组.取数据 (前位))
                如果 (前框架对象.是否为空 () == 假 && 前框架对象.是否有效 () && 前框架对象.取地址 () == 目标地址)
                {
                    地址名次 = 地址名次 + 1
                }
                前位 = 前位 + 1
            }
        }
        变量 树文本 <类型 = 文本型>
        树文本 = 执行CDP并同步等待 ("mcp_frametree_" + 到文本 (取启动时间 ()), "Page.getFrameTree", "{}", 8000)
        变量 树体 <类型 = 文本型>
        树体 = 取CDP结果文本 (树文本)
        如果 (树体 == "" || 寻找文本 (树体, "frameTree", 0, 假) == -1)
        {
            返回 (-1)
        }
        变量 扫描位 <类型 = 整数>
        扫描位 = 0
        变量 同址已见 <类型 = 整数>
        同址已见 = 0
        变量 命中ID <类型 = 文本型>
        命中ID = ""
        判断循环 (真)
        {
            变量 本条ID起 <类型 = 整数>
            本条ID起 = 寻找文本 (树体, "\\"id\\":\\"", 扫描位, 假)
            如果 (本条ID起 == -1)
            {
                跳出循环
            }
            变量 本条ID值起 <类型 = 整数>
            本条ID值起 = 本条ID起 + 6
            变量 本条ID终 <类型 = 整数>
            本条ID终 = 寻找文本 (树体, "\\"", 本条ID值起, 假)
            如果 (本条ID终 == -1)
            {
                跳出循环
            }
            变量 本条ID <类型 = 文本型>
            本条ID = 取文本中间 (树体, 本条ID值起, 本条ID终 - 本条ID值起)
            // 同一框架对象内 url 紧跟这条 id 之后(下一条 id 之前); 超出则该框架没有 url 字段
            变量 本条URL <类型 = 文本型>
            本条URL = ""
            变量 URL起 <类型 = 整数>
            URL起 = 寻找文本 (树体, "\\"url\\":\\"", 本条ID终, 假)
            变量 下条ID起 <类型 = 整数>
            下条ID起 = 寻找文本 (树体, "\\"id\\":\\"", 本条ID终, 假)
            如果 (URL起 != -1 && (下条ID起 == -1 || URL起 < 下条ID起))
            {
                变量 URL值起 <类型 = 整数>
                URL值起 = URL起 + 7
                变量 URL终 <类型 = 整数>
                URL终 = 寻找文本 (树体, "\\"", URL值起, 假)
                如果 (URL终 != -1)
                {
                    本条URL = 取文本中间 (树体, URL值起, URL终 - URL值起)
                }
            }
            如果 (目标地址 != "" && 本条URL == 目标地址)
            {
                如果 (同址已见 == 地址名次)
                {
                    命中ID = 本条ID
                    跳出循环
                }
                同址已见 = 同址已见 + 1
            }
            扫描位 = 本条ID终 + 1
        }
        // 地址取不到(类库未给出)时的兜底: 仅当两侧条数一致才按序号对齐, 否则如实失败
        如果 (命中ID == "" && 目标地址 == "")
        {
            变量 cdp条数 <类型 = 整数>
            cdp条数 = 0
            变量 数位 <类型 = 整数>
            数位 = 0
            判断循环 (真)
            {
                变量 找位 <类型 = 整数>
                找位 = 寻找文本 (树体, "\\"id\\":\\"", 数位, 假)
                如果 (找位 == -1)
                {
                    跳出循环
                }
                cdp条数 = cdp条数 + 1
                数位 = 找位 + 6
            }
            如果 (cdp条数 == id数组.取个数 ())
            {
                变量 序号找位 <类型 = 整数>
                序号找位 = 0
                变量 序号见过 <类型 = 整数>
                序号见过 = 0
                判断循环 (真)
                {
                    变量 序位 <类型 = 整数>
                    序位 = 寻找文本 (树体, "\\"id\\":\\"", 序号找位, 假)
                    如果 (序位 == -1)
                    {
                        跳出循环
                    }
                    如果 (序号见过 == 目标序号)
                    {
                        变量 序值起 <类型 = 整数>
                        序值起 = 序位 + 6
                        变量 序终 <类型 = 整数>
                        序终 = 寻找文本 (树体, "\\"", 序值起, 假)
                        如果 (序终 != -1)
                        {
                            命中ID = 取文本中间 (树体, 序值起, 序终 - 序值起)
                        }
                        跳出循环
                    }
                    序号见过 = 序号见过 + 1
                    序号找位 = 序位 + 6
                }
            }
        }
        如果 (命中ID == "")
        {
            返回 (-1)
        }'''


def depth_delta(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@'):
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
    a = anchor.split('\n')
    return [i for i in range(len(lines) - len(a) + 1) if lines[i:i + len(a)] == a]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')

    hs = find_anchor(lines, A_START)
    he = find_anchor(lines, A_END)
    assert len(hs) == 1, '起始锚点命中 %d 次' % len(hs)
    assert len(he) == 1, '结束锚点命中 %d 次' % len(he)
    s, e = hs[0], he[0] + len(A_END.split('\n'))
    assert s < e, '区间顺序异常'
    assert not any('同址已见' in l for l in lines), '已应用过'
    old = lines[s:e]
    new = NEW.split('\n')
    p0, b0 = depth_delta(old)
    p1, b1 = depth_delta(new)
    assert (p0, b0) == (p1, b1), '区间括号净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    whole_before = depth_delta(lines)
    out = lines[:s] + new + lines[e:]
    whole_after = depth_delta(out)
    assert whole_before == whole_after, '整文件净额 %d -> %d' % (whole_before, whole_after)
    print('区间 %d..%d: %d 行 -> %d 行; 区间净额 %s/%s -> %s/%s; 整文件 %s -> %s'
          % (s + 1, e, len(old), len(new), p0, b0, p1, b1, whole_before, whole_after))

    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        chk = open(TARGET, 'rb').read()
        assert not chk.startswith(b'\xef\xbb\xbf') and b'\r\n' not in chk, '写盘校验失败'
        print('已写入 %s (行数 %d -> %d)' % (TARGET, len(lines), len(out)))
    else:
        print('[dry-run] 未落盘')


main()
