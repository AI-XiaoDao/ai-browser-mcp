# -*- coding: utf-8 -*-
"""按失败分诊(_audit/_failure_triage.md)落地 A 类(测试假象)的覆盖值, 并修一个"静默吞覆盖"的结构性缺陷。

两件事:
 ① **结构缺陷**: build_args 的覆盖循环写着 `if pname in props:` —— 参数不在 schema.properties 里时
    覆盖会被**静默丢弃**(不报错、不进 note, 台账上完全看不出来)。而 browser_file_dialog 与
    browser_forward 的 inputSchema 就是空 {"type":"object"}(无 properties), 于是给它们写覆盖永远无效。
    改为无条件赋值, 并在 note 里点明"该参数不在 schema 里"。
 ② **A 类覆盖**: 30 个失败里属"探针没给真实值/没造状态"的, 按分诊给的**具体值**补上。
    追加在文件**末尾**(用 .update()), 这样不依赖 TOOL_ARG_OVERRIDES / TOOL_PRE_CALLS 的定义顺序 ——
    上一轮我把 setdefault 写在定义之前, 直接把整个台账 import 弄崩过。

B 类(8 个)按分诊建议**不覆盖**: 它们要么消息已可行动, 要么覆盖本身有害
(如 browser_vip_enable_js_env / browser_reverse_instrument_script 是确认闸门、browser_vip_mouse_wheel 调用即坏 CDP 通道)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP = os.path.join(ROOT, '_audit', 'mass_probe.py')
BAK = os.path.join(ROOT, '备份', '台账A类覆盖-写入前')

BUG_OLD = '\n'.join([
    '    for pname, v in (TOOL_ARG_OVERRIDES.get(tool_name) or {}).items():',
    '        if pname in props:',
    '            old = args.get(pname, "<未填>")',
    '            args[pname] = v',
    '            notes.append("%s=%r(工具级覆盖, 原值 %r: 通用取值不适用于该工具)"',
    '                         % (pname, v, old))',
])
BUG_NEW = '\n'.join([
    '    for pname, v in (TOOL_ARG_OVERRIDES.get(tool_name) or {}).items():',
    '        # ★ 修(静默吞覆盖): 原来这里写的是 `if pname in props:` —— 参数不在 schema.properties 里时',
    '        #   覆盖会被**悄悄丢掉**(不报错、不进 note, 台账上完全看不出来)。browser_file_dialog 与',
    '        #   browser_forward 的 inputSchema 就是空 {"type":"object"}, 给它们写的覆盖因此永远无效。',
    '        #   现改为无条件赋值, 并在 note 里点明该参数不在 schema 中(如实, 不隐藏事实)。',
    '        old = args.get(pname, "<未填>")',
    '        args[pname] = v',
    '        extra = "" if pname in props else "(注意: 该参数不在 schema.properties 里)"',
    '        notes.append("%s=%r(工具级覆盖, 原值 %r: 通用取值不适用于该工具)%s"',
    '                     % (pname, v, old, extra))',
])

APPEND = '''

# ============================================================================
# 失败分诊(_audit/_failure_triage.md)落地的 A 类覆盖 —— 追加在**文件末尾**,
# 用 .update() 保证不依赖上面两个表的定义顺序(曾因顺序问题把 import 弄崩过)。
# 依据逐条见分诊文档 §2; 这里只写"给什么值", 理由见文档。
# ============================================================================

# A-1 读/交互类: 分诊确认 h1 在页面上真实存在(browser_highlight{selector:h1}->highlighted:1,
# browser_reverse_dom_resolve{selector:h1}->object_id 非空); 点 h1 没有事件处理器,
# 不会导航(对比: 点 a 会跳 iana.org 污染后续测量, 故不用 a)。
TOOL_ARG_OVERRIDES.update({
    "browser_dom_query": {"selector": "h1"},
    "browser_dom_rect": {"selector": "h1"},
    "browser_dom_inner_html": {"selector": "h1"},
    "browser_dom_click": {"selector": "h1"},
    "browser_fill_click": {"selector": "h1"},
    "browser_fill_focus": {"selector": "h1"},
    "browser_fill_scroll": {"selector": "h1"},
    "browser_fill_trigger": {"selector": "h1"},
})

# A-2 需要"真实可写控件": example.com 现行版本没有 input/checkbox/select,
# 所以这几个工具**给什么 selector 都打不到实现** -> 先注入控件再指向它们。
_TOUCH_PROBE_JS = (
    "(function(){"
    "if(document.getElementById('mcpProbeSelect'))return 'exists';"
    "var i=document.createElement('input');i.id='mcpProbeInput';i.type='text';document.body.appendChild(i);"
    "var c=document.createElement('input');c.id='mcpProbeCheck';c.type='checkbox';document.body.appendChild(c);"
    "var s=document.createElement('select');s.id='mcpProbeSelect';"
    "var o1=document.createElement('option');o1.value='mcpA';o1.text='A';s.appendChild(o1);"
    "var o2=document.createElement('option');o2.value='mcpB';o2.text='B';s.appendChild(o2);"
    "document.body.appendChild(s);return 'made';})()"
)
_TOUCH_PRE = ("browser_execute_js", {"code": _TOUCH_PROBE_JS})
TOOL_PRE_CALLS.update({
    "browser_dom_checked": [_TOUCH_PRE],
    "browser_dom_selected": [_TOUCH_PRE],
    "browser_dom_set_value": [_TOUCH_PRE],
    "browser_fill_set_value": [_TOUCH_PRE],
    "browser_fill_select": [_TOUCH_PRE],
})
TOOL_ARG_OVERRIDES.update({
    "browser_dom_checked": {"selector": "#mcpProbeCheck"},
    "browser_dom_selected": {"selector": "#mcpProbeSelect"},
    "browser_dom_set_value": {"selector": "#mcpProbeInput", "value": "mcp-test"},
    "browser_fill_set_value": {"selector": "#mcpProbeInput", "value": "mcp-test"},
    "browser_fill_select": {"selector": "#mcpProbeSelect", "value": "mcpA"},
})

# A-3 真实 HTML 属性: 页面上的 <a href=...>Learn more</a> 必然带 href(双重佐证);
# attribute 在 schema 里是可选 -> 探针从不填。
TOOL_ARG_OVERRIDES.update({
    "browser_fill_attr_get": {"selector": "a", "attribute": "href"},
    "browser_fill_attr_set": {"selector": "a", "attribute": "data-mcp-probe", "value": "1"},
})

# A-4 缺"语义必填"入参的守卫类(值都取只读/无副作用的那个分支)。
TOOL_ARG_OVERRIDES.update({
    "browser_wait": {"what": "selector", "value": "h1"},
    "browser_intercept": {"action": "clear"},
    # file_dialog 的 schema 没有 properties -> 依赖上面的"无条件赋值"修复才生效。
    "browser_file_dialog": {"path": r"C:\\Windows\\win.ini"},
    "workflow_get": {"name": "hello"},
    "browser_cdp_call": {"method": "Runtime.evaluate",
                         "params": "{\\"expression\\":\\"1\\",\\"returnByValue\\":true}"},
    "browser_kernel_auth": {"action": "list"},
    "browser_kernel_scheme": {"action": "list"},
    # 这两个实现**已支持未写入文档的 list 只读分支**(信息更多、副作用更小) -> 用 list。
    "browser_kernel_reactor": {"action": "list"},
    "browser_kernel_watch": {"action": "list"},
    "browser_vip_execute_js_context": {"code": "document.title"},
    "browser_vip_dom_search": {"query": "Example Domain"},
})

# A-5 需要"先造状态"的 4 个。
TOOL_ARG_OVERRIDES.update({
    "browser_cdp_event": {"event_name": "Debugger.paused"},
})
TOOL_PRE_CALLS.update({
    # 与已通过的 browser_debugger_wait_paused 同款手法: stack 会触发零前置自动暂停,
    # 之后 Debugger.paused 会被写进 cdp_event:Debugger.paused 异步缓存。
    "browser_cdp_event": [("browser_debugger_stack", {})],
    # 这两个只在 Debugger.paused 时有效 -> 同样先自动暂停。
    "browser_reverse_return_value": [("browser_debugger_stack", {})],
    "browser_reverse_set_variable": [("browser_debugger_stack", {})],
    # 前进历史: 连续两次导航再后退, 产生 forward 栈(wait_for_load=False 只为造历史, 不必等载入)。
    "browser_forward": [
        ("browser_navigate", {"url": "https://example.com", "wait_for_load": False}),
        ("browser_navigate", {"url": "https://example.com/?mcpForwardProbe=1", "wait_for_load": False}),
        ("browser_back", {}),
    ],
})
'''


def main():
    t = io.open(MP, encoding='utf-8', newline='').read()
    n = t.count(BUG_OLD)
    print("[结构缺陷锚点] 出现 %d 次" % n)
    if n != 1:
        print("  !! 预期 1 次, 中止")
        return 1
    if '失败分诊' in t:
        print("  !! 似乎已追加过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(MP, os.path.join(BAK, os.path.basename(MP)))
    print("已备份到 %s" % BAK)
    t = t.replace(BUG_OLD, BUG_NEW) + APPEND
    io.open(MP, 'w', encoding='utf-8', newline='').write(t)
    print("OK: 结构缺陷已修 + A 类覆盖已追加(%d 行)" % APPEND.count('\n'))
    # 立即自检: 能否 import(上一轮就是因为 import 崩了导致台账整体无声失败)
    import importlib
    sys.path.insert(0, os.path.dirname(MP))
    mp = importlib.import_module('mass_probe')
    print("自检: import 成功; TOOL_ARG_OVERRIDES=%d 项, TOOL_PRE_CALLS=%d 项"
          % (len(mp.TOOL_ARG_OVERRIDES), len(mp.TOOL_PRE_CALLS)))
    # 抽查 file_dialog 的覆盖现在能不能真的落到 args 里
    args, notes = mp.build_args({"type": "object"}, "d", "browser_file_dialog")
    print("自检: browser_file_dialog 覆盖后 args=%r" % (args,))
    return 0


if __name__ == '__main__':
    sys.exit(main())
