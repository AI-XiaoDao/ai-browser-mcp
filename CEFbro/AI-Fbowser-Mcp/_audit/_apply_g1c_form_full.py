# -*- coding: utf-8 -*-
r"""G1c(Form 侧) 补丁: 填表族的框架感知 —— 前置校验 / attr_get / get_text / set_text。

三件事(每处都用**连续多行唯一锚点**定位, 任一断言不过即退出且不写盘):

F1 ★关键: 前置存在校验 签名加 (浏览器, 参数JSON) 并在其中走 CDP执行JS按框架。
   它被 7 个写分支调用(set_value/click/focus/scroll/attr_set/trigger/select), 而它此前恒在**主框架**探测元素
   -> selector 只存在于 iframe 内时会被判"匹配到 0 个元素"直接失败, 于是"Schema 有 frame_id 的写工具"
   在 iframe 里根本走不到原生执行。7 个调用点同步补参数。
F2 browser_fill_attr_get 的两条 CDP 路径(230/250) 改走 CDP执行JS按框架; 并在框架解析失败时明确报错,
   不再落到 260 行那条"只用原生填表框架"的兜底上(它虽然也看 frame_id, 但报错文案是"填表框架无效", 不指向真因)。
F3 browser_fill_get_text / browser_fill_set_text 补上 frame_id 能力: 三处 CDP 调用改走框架感知入口
   (get_text 294 / set_text 334 与回读 347), 且 get_text 增加"框架错误明确报错"分支
   (它此前会把 {"error":...} 当**成功消息**原样返回)。Schema 里的 frame_id 由另一脚本
   (_apply_g1c_descriptions.py) 统一补, 本脚本只改 .wsv 代码。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_Form.wsv')

# ---- F2: attr_get 两条 CDP 路径 ----
A2A = '                    js属性值 = MCP命令服务器.CDP执行JS并等待 (js属性码, 10000, 真)'
N2A = '''                    js属性值 = MCP命令服务器.CDP执行JS按框架 (browser, 参数JSON, js属性码, 10000)
                    // 约束: 指定了框架却解析不到 -> 明确报错。否则会落到"只用原生填表框架"的兜底,
                    // 报出与真因无关的"填表框架无效", 更难定位。
                    如果 (是否以 (js属性值, "{\\"error\\"") && MCP命令服务器.yyjson取文本 (参数JSON, "frame_id") != "" && MCP命令服务器.yyjson取文本 (参数JSON, "frame_id") != "main")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, js属性值 + " | 该框架内取属性未成功, 未回退到主框架取(否则会读到主框架元素)"))
                    }'''

A2B = '                    js文本值 = MCP命令服务器.CDP执行JS并等待 (js文本码, 10000, 真)'
N2B = '''                    js文本值 = MCP命令服务器.CDP执行JS按框架 (browser, 参数JSON, js文本码, 10000)
                    如果 (是否以 (js文本值, "{\\"error\\"") && MCP命令服务器.yyjson取文本 (参数JSON, "frame_id") != "" && MCP命令服务器.yyjson取文本 (参数JSON, "frame_id") != "main")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, js文本值 + " | 该框架内取文本未成功, 未回退到主框架取(否则会读到主框架元素)"))
                    }'''

# ---- F3: fill_get_text / fill_set_text ----
A3A = '            js值 = MCP命令服务器.CDP执行JS并等待 (js码, 10000, 真)'
N3A = '''            js值 = MCP命令服务器.CDP执行JS按框架 (browser, 参数JSON, js码, 10000)
            // 约束: 框架解析失败时不能把 {"error":…} 当成功消息返回(此前的兜底分支会把任何未命中哨兵的值
            // 原样当成功消息发出, 于是调用方看到 success:true + 一段错误文本)。
            如果 (是否以 (js值, "{\\"error\\""))
            {
                返回 (MCP_响应构建.命令失败 (命令ID, js值 + " | 该框架内取 innerText 未成功"))
            }'''

A3B = '            设值 = MCP命令服务器.CDP执行JS并等待 (设码, 10000, 真)'
N3B = '            设值 = MCP命令服务器.CDP执行JS按框架 (browser2, 参数JSON, 设码, 10000)'

A3C = '            读值 = MCP命令服务器.CDP执行JS并等待 (读码, 10000, 真)'
N3C = '            读值 = MCP命令服务器.CDP执行JS按框架 (browser2, 参数JSON, 读码, 10000)'

# ---- F1: 前置存在校验 —— 拆成 3 个唯一锚点(整行匹配), 比整段块锚点稳健 ----
A1A = '    参数 操作名 <类型 = 文本型 @输出名 = "OperationName">'
N1A = '''    参数 操作名 <类型 = 文本型 @输出名 = "OperationName">
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 参数JSON <类型 = YYJSON只读对象类 @输出名 = "ParamJSON">'''

A1B = '        js值 = MCP命令服务器.CDP执行JS并等待 (js码, 10000, 真)'
N1B = '''        // 框架感知: 带 frame_id 时在**该 iframe 内**探测。此前恒在主框架探测, 于是"元素只在 iframe 里"的
        // 写操作会被这里判成"匹配到 0 个元素"直接失败 —— 原生框架路径根本没机会执行。
        js值 = MCP命令服务器.CDP执行JS按框架 (浏览器, 参数JSON, js码, 10000)
        变量 校验框架 <类型 = 文本型>
        校验框架 = ""
        如果 (参数JSON.是否为空 () == 假)
        {
            校验框架 = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
        }
        如果 (是否以 (js值, "{\\"error\\"") && 校验框架 != "" && 校验框架 != "main" && 校验框架 != "主框架")
        {
            // 框架解析失败: **不放行**。放行会让下面的原生写在主框架执行, 那是静默跑错框架。
            返回 (MCP_响应构建.命令失败 (命令ID, 操作名 + "未执行: " + js值))
        }'''

A1C = '            返回 (MCP_响应构建.命令失败 (命令ID, 操作名 + "未执行: 选择器在当前页面匹配到 0 个元素 -> " + 选择器 + " | 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择器; 注意 iframe 内元素需先切换框架, 元素可能在滚动后才加载"))'
N1C = '''            如果 (校验框架 != "" && 校验框架 != "main" && 校验框架 != "主框架")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, 操作名 + "未执行: 框架(" + 校验框架 + ")内匹配到 0 个元素 -> " + 选择器 + " | 建议: 先用 browser_get_frames 确认框架标识, 再用 browser_dom_query {frame_id} 确认能取到该元素"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, 操作名 + "未执行: 选择器在当前页面匹配到 0 个元素 -> " + 选择器 + " | 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择器; 若元素在 iframe 内请传 frame_id(取自 browser_get_frames)"))'''

CALL_SITES = [
    ('前置失败 = 前置存在校验 (命令ID, selector, "设置值")',
     '前置失败 = 前置存在校验 (命令ID, selector, "设置值", browser, 参数JSON)'),
    ('前置失败 = 前置存在校验 (命令ID, selector, "点击")',
     '前置失败 = 前置存在校验 (命令ID, selector, "点击", browser, 参数JSON)'),
    ('前置失败 = 前置存在校验 (命令ID, selector, "设置焦点")',
     '前置失败 = 前置存在校验 (命令ID, selector, "设置焦点", browser, 参数JSON)'),
    ('前置失败 = 前置存在校验 (命令ID, selector, "滚动到元素")',
     '前置失败 = 前置存在校验 (命令ID, selector, "滚动到元素", browser, 参数JSON)'),
    ('前置失败 = 前置存在校验 (命令ID, selector, "设置属性")',
     '前置失败 = 前置存在校验 (命令ID, selector, "设置属性", browser, 参数JSON)'),
    ('前置失败 = 前置存在校验 (命令ID, selector, "触发事件")',
     '前置失败 = 前置存在校验 (命令ID, selector, "触发事件", browser, 参数JSON)'),
    ('前置失败 = 前置存在校验 (命令ID, selector, "设置select选中项")',
     '前置失败 = 前置存在校验 (命令ID, selector, "设置select选中项", browser, 参数JSON)'),
]


def find_anchor(lines, anchor):
    a = anchor.split('\n')
    return [i for i in range(len(lines) - len(a) + 1) if lines[i:i + len(a)] == a]


def nets(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@'):
            continue
        # 跳过整行注释, 避免注释里的括号影响净额判断
        if st.startswith('#') or st.startswith('//'):
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


def detect_term(txt):
    """判定该文件的真实行尾序列(实测 MCP_Server_Form.wsv 是 CR CR LF, 不是 CRLF)。"""
    if '\r\r\n' in txt:
        return '\r\r\n'
    if '\r\n' in txt:
        return '\r\n'
    return '\n'


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    txt = raw.decode('utf-8')
    term = detect_term(txt)
    n_term = txt.count(term)
    # 行尾必须**统一**为同一种序列, 否则拒绝改写(避免把混合行尾静默归一)
    rest = txt.replace(term, '')
    assert '\r' not in rest and '\n' not in rest, '存在其它行尾序列, 拒绝改写'
    print('目标 %s | 大小 %d | 行尾=%r x %d (非 LF 属该文件既有约定, 原样保留)'
          % (TARGET, len(raw), term, n_term))
    lines = txt.replace(term, '\n').split('\n')
    assert not any('CDP执行JS按框架' in l for l in lines), '已应用过'

    pairs = [('F1a-签名参数', A1A, N1A), ('F1b-校验本体', A1B, N1B), ('F1c-错误文案', A1C, N1C),
             ('F2a-attr_get属性', A2A, N2A), ('F2b-attr_get文本', A2B, N2B),
             ('F3a-get_text', A3A, N3A), ('F3b-set_text写', A3B, N3B), ('F3c-set_text回读', A3C, N3C)]
    for tag, old, new in pairs:
        hits = find_anchor(lines, old)
        assert len(hits) == 1, '%s 锚点命中 %d 次(期望 1)' % (tag, len(hits))
        print('   %-16s @%d  %d 行 -> %d 行' % (tag, hits[0] + 1, len(old.split('\n')), len(new.split('\n'))))

    # 调用点: 用"去缩进后逐字相等"匹配并保留原缩进(该文件这几处缩进各不相同, 硬编码缩进易错)
    call_idx = []
    for old, new in CALL_SITES:
        hits = [i for i, l in enumerate(lines) if l.strip() == old.strip()]
        assert len(hits) == 1, '调用点锚点命中 %d 次: %s' % (len(hits), old[:60])
        call_idx.append((hits[0], old, new))
    print('   7 个调用点锚点各自唯一 OK')

    p0, b0 = nets(lines)
    # 应用(先做调用点, 保留原缩进; 再做整段)
    for i, old, new in call_idx:
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        lines[i] = indent + new.strip()
    for tag, old, new in pairs:
        i = find_anchor(lines, old)[0]
        lines = lines[:i] + new.split('\n') + lines[i + len(old.split('\n')):]

    p1, b1 = nets(lines)
    assert (p1, b1) == (p0, b0), '括号净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    out = '\n'.join(lines)
    assert out.count('CDP执行JS按框架') == 6, '框架感知入口命中 %d 处(期望 6)' % out.count('CDP执行JS按框架')
    assert out.count('前置存在校验 (命令ID, selector,') == 7
    assert out.count(', browser, 参数JSON)') >= 7

    if '--apply' in sys.argv:
        out = out.replace('\n', term)
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(out)
        chk = open(TARGET, 'rb').read()
        assert not chk.startswith(b'\xef\xbb\xbf'), '写盘后带 BOM'
        back = chk.decode('utf-8')
        assert back == out, '写盘回读不一致'
        assert back.count(term) == out.count(term) and '\r' not in out.replace(term, ''), '行尾序列被破坏'
        print('已写入 %s (行数 %d -> %d, 行尾保持 %r)' % (TARGET, len(lines), len(out.split(term)), term))
    else:
        print('[dry-run] 圆括号净额 %d->%d 花括号 %d->%d; 未落盘' % (p0, p1, b0, b1))
        print('框架感知入口 6 处 / 前置校验调用点 7 处 / 新签名已就位 — 断言全部通过')


main()
