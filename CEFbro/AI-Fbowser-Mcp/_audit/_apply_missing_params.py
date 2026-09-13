# -*- coding: utf-8 -*-
r"""第127轮(其二): 按只读审计 `_schema_audit_A.md` 补齐"实现真读却未声明"的参数 + 修正两处与实现相反的描述。

每一项都已在源码里核实过读取点(不是照抄审计结论):
  · `allow_empty`  → Core:2011 `yyjson取整数 (参数JSON, "allow_empty") == 0`（dom_set_value 用它决定能否清空字段）
  · `auto_enable`  → Core:3511（browser_network list 的自动启用开关）
  · `inject_id`    → Core:3395 / 3412（browser_inject）
  · `url_pattern`  → Core:7598（browser_reverse_hook 的 URL 模式）
  · touch 三件套   → 描述承诺 `kernel:true`，而 schema 只有 x/y（同族 mouse_* 都声明了 kernel，家族内自相矛盾）
  另修两处描述与实现相反：
  · `browser_view_source` 描述写"在新标签打开 view-source"，实现（Core:4203 注释）明写**只回文本、不弹任何窗口**
    （不调用原生 源码视图()，那会弹记事本阻塞控制台）；同时补声明它真正读取的 `max_chars`；
  · `browser_file_dialog` 描述写"打开文件对话框"，实现**不弹真对话框**（只配置/返回响应）—— 如实改写。

用法: py -3 _audit\_apply_missing_params.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

EDITS = [
    # ① dom_set_value: 补 allow_empty(实现真读; 报错文案本来就指向它 ⇒ 原状是死路)
    ("browser_dom_set_value",
     '属性项JSON ("value", "text", "值") + ","',
     '属性项JSON ("value", "text", "值") + "," + 属性项JSON ("allow_empty", "integer", "允许把值设为空(1/true=允许)。**实现会读它**: 不带它时 value 为空会被拒绝(报错文案此前指向一个未声明的参数, 属死路)") + ","',
     '① 补 allow_empty'),
    # ② browser_network: 补 auto_enable
    ("browser_network", '属性项JSON ("limit", "integer", "list 时的条数(默认500, 上限1000)")',
     '属性项JSON ("limit", "integer", "list 时的条数(默认500, 上限1000)") + "," + 属性项JSON ("auto_enable", "boolean", "list 时是否自动启用网络日志(默认true; 传 false 可只查询不改开关)")',
     '② 补 auto_enable'),
    # ③ browser_inject: 补 inject_id
    ("browser_inject", '属性项JSON ("persist", "boolean", "持久(V8预注入,type=handler时须persist)"), "\\"type\\",\\"code\\""))',
     '属性项JSON ("persist", "boolean", "持久(V8预注入,type=handler时须persist)") + "," + 属性项JSON ("inject_id", "text", "注入标识(实现会读它, 用于随后撤销/替换同一次注入)"), "\\"type\\",\\"code\\""))',
     '③ 补 inject_id'),
    # ④ browser_reverse_hook: 补 url_pattern
    ("browser_reverse_hook", '属性项JSON ("capture_stack", "boolean", "捕获调用栈"), ""))',
     '属性项JSON ("capture_stack", "boolean", "捕获调用栈") + "," + 属性项JSON ("url_pattern", "text", "仅命中该 URL 模式才 Hook(type=xhr_fetch/websocket 时生效; 实现会读它)"), ""))',
     '④ 补 url_pattern'),
    # ⑤ view_source: 描述改为与实现一致 + 补声明它真读的 max_chars(该行原本**没有 schema**, 须一并加上)
    ("browser_view_source", '"在新标签打开当前页面源码视图(view-source:)| 取源码字符串请用 get_source")',
     '"返回当前页面源码**文本** | 说明书更正(第127轮): 本工具**不会**打开 view-source 标签页, 也不弹任何窗口'
     '(实现刻意不调用类库 源码视图(), 那会弹记事本并阻塞控制台) —— 旧描述写「在新标签打开 view-source」与实现相反; '
     '要取源码字符串同样可用 browser_get_source, 二者等价", 多属性Schema文本 (属性项JSON ("max_chars", "integer", '
     '"返回源码的最大字符数(实现会读它; 缺省用内置上限)"), ""))',
     '⑤ view_source 描述改准 + 补 max_chars'),
    # ⑥ file_dialog: 描述改为与实现一致
    ("browser_file_dialog", '"打开文件对话框"',
     '"配置文件对话框的**自动化响应** | 说明书更正(第127轮): 本工具**不会弹出真实的系统文件对话框**'
     '(控制台程序无人值守场景下弹窗会永久阻塞), 而是登记「若页面触发文件选择则用哪些文件/如何响应」, '
     '供受控上传流程使用; 未登记时页面触发文件选择不会被自动处理"',
     '⑥ file_dialog 描述改准'),
]

# ⑦ touch 三件套: 补 kernel(与同族 mouse_* 对齐)
TOUCH_TOOLS = ["browser_touch_press", "browser_touch_move", "browser_touch_release"]
TOUCH_OLD = '双XY_Schema文本 ("x", "y", "X", "Y")'
TOUCH_NEW = ('双XY_Schema文本 ("x", "y", "X", "Y") + "," + 属性项JSON ("kernel", "boolean", '
             '"true=内核级注入(会破坏本会话 CDP 通道, 需重启恢复); 默认 false=CDP 派发")')


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
    n0, b0 = len(txt.split('\n')), balance(txt)
    lines = txt.split('\n')
    done = []
    for tool, old, new, tag in EDITS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if new in lines[i]:
            done.append(tag + ' (已存在)')
            continue
        assert lines[i].count(old) == 1, '%s 旧子串 %d 次: %s' % (tool, lines[i].count(old), old[:44])
        lines[i] = lines[i].replace(old, new, 1)
        done.append(tag)
    # touch 三件套(同一子串, 逐个工具处理)
    for tool in TOUCH_TOOLS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if 'kernel", "boolean", "true=内核级注入' in lines[i]:
            done.append('⑦ %s kernel (已存在)' % tool)
            continue
        assert lines[i].count(TOUCH_OLD) == 1, '%s X/Y 锚点 %d' % (tool, lines[i].count(TOUCH_OLD))
        lines[i] = lines[i].replace(TOUCH_OLD, TOUCH_NEW, 1)
        done.append('⑦ %s 补 kernel' % tool)
    out = '\n'.join(lines)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server.wsv: 行数 %d 不变; 完成 %d 项:' % (n0, len(done)))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        for must in ('"allow_empty"', '"auto_enable"', '"inject_id"', '"url_pattern"',
                     '不会**打开 view-source', '不会弹出真实的系统文件对话框'):
            assert must in c, '缺少 %s' % must
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
