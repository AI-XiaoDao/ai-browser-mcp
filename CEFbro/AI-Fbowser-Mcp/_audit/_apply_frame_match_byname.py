# -*- coding: utf-8 -*-
r"""修正 解析框架执行上下文 的 CDP 框架匹配 v2: **名字优先, 地址兜底**。

实测根因(本轮): 上一版按"地址 + 名次"匹配, 对**同名同址**的 srcdoc 框架不可靠 ——
CEF 清单顺序与 CDP 框架树顺序**并不一致**, 于是外层(mcpfr)与内层(mcpfr2)的 about:srcdoc 被对调:
实测 frame_id=外层 读到了内层的内容(IFRAME2), frame_id=内层 读到了外层的内容(IFRAME1) —— 典型的静默错答案。

改法:
  1) 目标框架先取 **取框架名()**(类库), 名字非空时**只认同名项**(必要时再用地址加固);
  2) 名字为空(匿名框架)才退回"地址 + 名次"的最佳努力;
  3) 名字与地址都拿不到时, 仅在两侧条数一致时才按序号兜底, 否则如实返回 -1(失败, 不猜)。

顺带把这段扫描逻辑抽成可复用方法 CDP框架树找ID, 主方法只负责选择策略。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

A_START = '        // 目标框架的**地址**: 用于在 CDP 框架树里按键匹配。'
A_END = '''        如果 (命中ID == "")
        {
            返回 (-1)
        }'''

HELPER_ANCHOR = '    # 解析"要操作哪个框架对象"(原生 CEF 框架对象, 用于在该框架**自己的页面主世界**执行 JS)。'

NEW_MAIN = '''        // 目标框架的**名字**与**地址**: 在 CDP 框架树里按键匹配用。
        // 依据(实测): CEF 的框架清单顺序与 CDP 框架树的顺序**并不一致** —— 只按"地址 + 名次"匹配时,
        // 同一地址的 srcdoc 框架(外层/内层)会被对调: frame_id=外层 读到内层内容。名字才是可靠区分键。
        变量 目标名 <类型 = 文本型>
        目标名 = ""
        变量 目标地址 <类型 = 文本型>
        目标地址 = ""
        如果 (目标框架ID != "")
        {
            变量 目标框架对象 <类型 = 类_FBrowser_框架>
            目标框架对象 = 浏览器.取框架_ID (目标框架ID)
            如果 (目标框架对象.是否为空 () == 假 && 目标框架对象.是否有效 ())
            {
                目标名 = 目标框架对象.取框架名 ()
                目标地址 = 目标框架对象.取地址 ()
            }
        }
        // 匿名框架(名字为空)只能按地址 + 名次最佳努力: 名次取自 CEF 清单里同地址出现的次序
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
        变量 命中ID <类型 = 文本型>
        命中ID = ""
        如果 (目标名 != "")
        {
            命中ID = CDP框架树找ID (树体, 目标名, 目标地址, 0)
        }
        如果 (命中ID == "" && 目标地址 != "")
        {
            命中ID = CDP框架树找ID (树体, "", 目标地址, 地址名次)
        }
        // 名字与地址都取不到时: 仅当两侧条数一致才按序号兜底, 否则如实失败(不猜)
        如果 (命中ID == "" && 目标名 == "" && 目标地址 == "")
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

HELPER = '''    # 在 CDP 框架树文本里找出目标框架的 frameId: **名字优先, 地址兜底**。
    # 为什么不能只按地址: 实测 CEF 框架清单顺序与 CDP 框架树顺序并不一致, 同名同址的 srcdoc 框架
    # (外层/内层都是 about:srcdoc)会被对调 —— 只按地址匹配时 frame_id=外层 读到了内层的内容。
    # 名字(类库 取框架名)是这类框架之间唯一可靠的区分键; 名字为空(匿名框架)才退回"地址 + 名次"。
    # 返回: 命中项的 frameId; 找不到返回 ""(调用方据此如实失败, 绝不猜)。
    方法 CDP框架树找ID <公开 静态 类型 = 文本型 @输出名 = "FindCDPFrameID" @强制输出 = 真>
    参数 树体 <类型 = 文本型 @输出名 = "TreeBody">
    参数 目标名 <类型 = 文本型 @输出名 = "TargetName">
    参数 目标地址 <类型 = 文本型 @输出名 = "TargetURL">
    参数 地址名次 <类型 = 整数 @默认值 = 0 @输出名 = "URLOrdinal">
    {
        变量 强命中 <类型 = 文本型>
        强命中 = ""
        变量 弱命中 <类型 = 文本型>
        弱命中 = ""
        变量 同址已见 <类型 = 整数>
        同址已见 = 0
        变量 扫描位 <类型 = 整数>
        扫描位 = 0
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
            // 同一框架对象内 name / url 都紧跟这条 id 之后(下一条 id 之前); 缺字段则视为空
            变量 下条ID起 <类型 = 整数>
            下条ID起 = 寻找文本 (树体, "\\"id\\":\\"", 本条ID终, 假)
            变量 本条名 <类型 = 文本型>
            本条名 = ""
            变量 本条URL <类型 = 文本型>
            本条URL = ""
            变量 值字段 <类型 = 整数>
            值字段 = 0
            判断循环 (值字段 < 2)
            {
                变量 键名 <类型 = 文本型>
                如果 (值字段 == 0)
                {
                    键名 = "\\"name\\":\\""
                }
                否则
                {
                    键名 = "\\"url\\":\\""
                }
                变量 字段起 <类型 = 整数>
                字段起 = 寻找文本 (树体, 键名, 本条ID终, 假)
                如果 (字段起 != -1 && (下条ID起 == -1 || 字段起 < 下条ID起))
                {
                    变量 字段值起 <类型 = 整数>
                    字段值起 = 字段起 + 取文本长度 (键名)
                    变量 字段终 <类型 = 整数>
                    字段终 = 寻找文本 (树体, "\\"", 字段值起, 假)
                    如果 (字段终 != -1)
                    {
                        如果 (值字段 == 0)
                        {
                            本条名 = 取文本中间 (树体, 字段值起, 字段终 - 字段值起)
                        }
                        否则
                        {
                            本条URL = 取文本中间 (树体, 字段值起, 字段终 - 字段值起)
                        }
                    }
                }
                值字段 = 值字段 + 1
            }
            如果 (目标名 != "")
            {
                如果 (本条名 == 目标名)
                {
                    如果 (目标地址 != "" && 本条URL == 目标地址)
                    {
                        强命中 = 本条ID
                        跳出循环
                    }
                    如果 (弱命中 == "")
                    {
                        弱命中 = 本条ID
                    }
                }
            }
            否则
            {
                如果 (目标地址 != "" && 本条URL == 目标地址)
                {
                    如果 (同址已见 == 地址名次)
                    {
                        强命中 = 本条ID
                        跳出循环
                    }
                    同址已见 = 同址已见 + 1
                }
            }
            扫描位 = 本条ID终 + 1
        }
        如果 (强命中 != "")
        {
            返回 (强命中)
        }
        返回 (弱命中)
    }

'''


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
    ha = find_anchor(lines, HELPER_ANCHOR)
    assert len(hs) == 1, '起始锚点 %d' % len(hs)
    assert len(he) == 1, '结束锚点 %d' % len(he)
    assert len(ha) == 1, 'helper 锚点 %d' % len(ha)
    s, e = hs[0], he[0] + len(A_END.split('\n'))
    assert not any('CDP框架树找ID' in l for l in lines), '已应用过'
    old = lines[s:e]
    new = NEW_MAIN.split('\n')
    po, bo = depth_delta(old)
    pn, bn = depth_delta(new)
    assert (po, bo) == (pn, bn), '主段净额 %s/%s -> %s/%s' % (po, bo, pn, bn)
    out = lines[:s] + new + lines[e:]
    helper = HELPER.rstrip('\n').split('\n')
    ph, bh = depth_delta(helper)
    assert (ph, bh) == (0, 0), 'helper 净额 %s/%s' % (ph, bh)
    h2 = find_anchor(out, HELPER_ANCHOR)
    assert len(h2) == 1
    out = out[:h2[0]] + helper + [''] + out[h2[0]:]
    assert depth_delta(out) == depth_delta(lines), '整文件净额变化'
    print('主段 %d..%d: %d 行 -> %d 行; helper %d 行; 行数 %d -> %d'
          % (s + 1, e, len(old), len(new), len(helper), len(lines), len(out)))
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
