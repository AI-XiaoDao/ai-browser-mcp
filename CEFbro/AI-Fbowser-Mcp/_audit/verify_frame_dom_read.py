# -*- coding: utf-8 -*-
r"""G1c 验收: DOM/填表族的**读取类**工具能否按 frame_id 读进 iframe(此前一律在主框架求值)。

判别设计: 主框架与 iframe **放同一个选择器 #tgt、值不同**(MAIN / IFRAME1 / IFRAME2),
  于是"给了 frame_id 却仍读主框架"这种最难发现的错误答案会立刻暴露(读到 MAIN 即判失败)。
另加: 写操作双向验证(只改 iframe、主框架不动)、未知 frame_id 必须报错且不得回主框架,
以及"不给 frame_id 时行为不变"的回归臂。预言机用 browser_execute_js 直接读 DOM(与被测工具无关)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:260]) if detail else ''))


def js(expr, frame=None):
    a = {"code": expr}
    if frame is not None:
        a["frame_id"] = frame
    e, t = call("browser_execute_js", a)
    return ('ERR:' if e else '') + val(t)


# 主框架: #tgt=MAIN + #mtxt ; 外层 iframe(名 mcpfr) 内含 #tgt=IFRAME1 及若干可读元素, 再套一层(名 mcpfr2)。
# 约束: 必须**整棵结构都用 srcdoc 一次性建好** —— 新 append 的 srcdoc iframe 其 contentDocument.body 当时为 null,
# "append 后立刻 d1.body.innerHTML" 会抛异常导致整页没建起来(上一版探针就栽在这, 误报成工具失败)。
BUILD = '''(function(){
  document.body.insertAdjacentHTML('beforeend',"<input id='tgt' value='MAIN'><div id='mtxt'>MAIN_TEXT</div>");
  var f1=document.createElement('iframe');
  f1.id='fr1'; f1.name='mcpfr';
  f1.srcdoc="<input id='tgt' value='IFRAME1'><input id='in1' value='VAL1'>"
    +"<input id='ck' type='checkbox' checked><select id='se'><option value='a'>A</option>"
    +"<option value='b' selected>B</option></select><div id='txt'>TEXT_IN_FRAME_1</div>"
    +"<iframe id='fr2' name='mcpfr2' srcdoc=\\"<input id='tgt' value='IFRAME2'><div id='txt'>TEXT_IN_FRAME_2</div>\\"></iframe>";
  document.body.appendChild(f1);
  return 'built';
})()'''

print('== 造页面: 主框架/外层(mcpfr)/嵌套(mcpfr2), #tgt 三值互异 ==')
call("browser_navigate", {"url": "https://example.com/?g1c=%d" % int(time.time()),
                          "wait_for_load": True})
print('   注入: %s' % js(BUILD))
time.sleep(1.5)
baseline = [js("document.querySelector('#tgt').value"),
            js("document.querySelector('#tgt').value", 'mcpfr'),
            js("document.querySelector('#tgt').value", 'mcpfr2')]
print('   预言机(经 CDP 隔离世界直读): %s' % baseline)
rec('基线: 三层 #tgt 互异(判别有效)', baseline == ['MAIN', 'IFRAME1', 'IFRAME2'], baseline)

e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
out_f = next((f for f in frames if f.get('name') == 'mcpfr'), None)
nest_f = next((f for f in frames if f.get('name') == 'mcpfr2'), None)
FID_OUT = (out_f or {}).get('id')
FID_NEST = (nest_f or {}).get('id')
print('   外层 id=%r 嵌套 id=%r' % (FID_OUT, FID_NEST))

# (标签, 工具, 参数, 期望子串, 必须不含)
ARMS = [
    ('回归/主框架 dom_query', 'browser_dom_query',
     {"selector": "#tgt", "attribute": "value"}, 'MAIN', None),
    ('★外层 dom_query(按名)', 'browser_dom_query',
     {"selector": "#tgt", "attribute": "value", "frame_id": 'mcpfr'}, 'IFRAME1', 'MAIN'),
    ('★外层 dom_query(按id)', 'browser_dom_query',
     {"selector": "#tgt", "attribute": "value", "frame_id": FID_OUT}, 'IFRAME1', 'MAIN'),
    ('★嵌套 dom_query(按id)', 'browser_dom_query',
     {"selector": "#tgt", "attribute": "value", "frame_id": FID_NEST}, 'IFRAME2', 'MAIN'),
    ('★嵌套 dom_query(按序号)', 'browser_dom_query',
     {"selector": "#tgt", "attribute": "value",
      "frame_id": (str(frames.index(nest_f)) if nest_f in frames else '2')}, 'IFRAME2', 'MAIN'),
    ('★外层 dom_rect', 'browser_dom_rect',
     {"selector": "#in1", "frame_id": 'mcpfr'}, None, None),
    ('★外层 dom_checked', 'browser_dom_checked',
     {"selector": "#ck", "frame_id": 'mcpfr'}, None, None),
    ('★外层 dom_selected', 'browser_dom_selected',
     {"selector": "#se", "frame_id": 'mcpfr'}, None, None),
    ('★外层 dom_get_html', 'browser_dom_get_html',
     {"selector": "#txt", "frame_id": 'mcpfr'}, 'TEXT_IN_FRAME_1', None),
    ('★嵌套 dom_get_html', 'browser_dom_get_html',
     {"selector": "#txt", "frame_id": FID_NEST}, 'TEXT_IN_FRAME_2', None),
    ('★外层 fill_attr_get', 'browser_fill_attr_get',
     {"selector": "#in1", "attribute": "value", "frame_id": 'mcpfr'}, 'VAL1', None),
    ('★外层 fill_get_text', 'browser_fill_get_text',
     {"selector": "#txt", "frame_id": 'mcpfr'}, 'TEXT_IN_FRAME_1', None),
    ('★外层 browser_get_text', 'browser_get_text',
     {"selector": "#txt", "frame_id": 'mcpfr'}, 'TEXT_IN_FRAME_1', None),
    ('回归/主框架 fill_attr_get', 'browser_fill_attr_get',
     {"selector": "#tgt", "attribute": "value"}, 'MAIN', None),
    ('回归/主框架 browser_get_text', 'browser_get_text',
     {"selector": "#mtxt"}, 'MAIN_TEXT', None),
]

print('\n== A. 读取类: 给 frame_id 必须读到 iframe;**不得**读到主框架 ==')
for label, tool, args, want, forbid in ARMS:
    e, t = call(tool, args)
    got = val(t)
    ok = not e
    if want:
        ok = ok and (want in got)
    if forbid:
        ok = ok and (forbid not in got)
    rec(label, ok, '%s -> %s' % (tool, got[:150]))

print('\n== B. ★写操作: 带 frame_id 只改 iframe, 主框架不受影响 ==')
e, t = call("browser_dom_set_value", {"selector": "#in1", "value": "SET_IN_FRAME",
                                      "frame_id": 'mcpfr'})
time.sleep(0.4)
in1 = js("document.getElementById('in1')?document.getElementById('in1').value:'__NONE__'", 'mcpfr')
main_has_in1 = js("String(!!document.getElementById('in1'))")
print('   回包 %s | iframe #in1=%r | 主框架存在 #in1=%s' % (val(t)[:100], in1, main_has_in1))
rec('★iframe 内 #in1 被写入 SET_IN_FRAME', in1 == 'SET_IN_FRAME', in1)
rec('主框架根本没这个元素(无串扰)', main_has_in1 == 'false', main_has_in1)

print('\n== C. 未知 frame_id: 必须报错, 且**不得**回落到主框架读取 ==')
for tool, args in (('browser_dom_query', {"selector": "#tgt", "attribute": "value"}),
                   ('browser_fill_attr_get', {"selector": "#tgt", "attribute": "value"}),
                   ('browser_get_text', {"selector": "#txt"})):
    a = dict(args)
    a["frame_id"] = "no-such-frame-zzz"
    e, t = call(tool, a)
    got = val(t)
    rec('★%s 未知 frame_id 报错且无主框架内容' % tool,
        e and ('MAIN' not in got), 'isError=%s %s' % (e, got[:140]))

print('\n== D. 不带 frame_id 时读**主动拒绝** frame 内元素(判别: 不能读到 IFRAME 内容) ==')
e, t = call("browser_get_text", {"selector": "#txt"})
got = val(t)
rec('无 frame_id 时 #txt 取不到(该元素只在 iframe 内)', 'TEXT_IN_FRAME_1' not in got,
    'isError=%s %s' % (e, got[:140]))

print('\n== E. ★跨域 iframe: 主框架**读不到**, 带 frame_id 的工具**能读到**(真实能力判别) ==')
js("(function(){var f=document.createElement('iframe');f.id='xofr';f.name='xofr';"
   "f.src='https://example.org/';document.body.appendChild(f);return 'added'})()")
time.sleep(3.0)
e2, t2 = call("browser_get_frames", {})
fr2 = json.loads(t2).get("frames") or []
xo = next((f for f in fr2 if f.get('name') == 'xofr'), None)
print('   跨域框架: %r' % ((xo or {}).get('id')))
blocked = js("(function(){try{var d=document.getElementById('xofr').contentDocument;"
             "return d?('LEAK:'+d.title):'NULL'}catch(e){return 'SECURITY:'+e.name}})()")
print('   主框架直读跨域文档 -> %r' % blocked)
rec('基线: 主框架读跨域文档被同源策略拦下(证明这确实是跨域)',
    str(blocked).startswith('SECURITY') or blocked == 'NULL', blocked)
if xo:
    e3, t3 = call("browser_dom_get_html", {"selector": "h1", "frame_id": xo.get('id')})
    got3 = val(t3)
    print('   browser_dom_get_html{frame_id=跨域id} -> %s' % got3[:160])
    rec('★工具在跨域 iframe 内读到 h1(Example Domain)',
        (not e3) and ('Example Domain' in got3), got3[:200])
    e4, t4 = call("browser_dom_get_html", {"selector": "h1", "frame_id": 'xofr'})
    got4 = val(t4)
    print('   browser_dom_get_html{frame_id=按名} -> %s' % got4[:160])
    rec('★按名定位跨域 iframe 亦可', (not e4) and ('Example Domain' in got4), got4[:200])
else:
    rec('★工具在跨域 iframe 内读到 h1', False, '未取到跨域框架 id')

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
