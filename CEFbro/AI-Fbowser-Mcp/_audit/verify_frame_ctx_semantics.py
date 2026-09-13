# -*- coding: utf-8 -*-
r"""量测: browser_execute_js {frame_id} 里, 用户代码处在**哪个 JS 世界**。

为什么要量: 框架内求值目前经 Page.createIsolatedWorld 取上下文。隔离世界与页面脚本共享 DOM,
但 **全局对象是分开的** —— 若页面自己在子框架里挂了变量(app 常见), 隔离世界里读不到,
那会是"看起来成功、其实换了个世界"的静默差异, 必须查清并如实告知/修正。

判别设计: 主框架 / 外层 / 嵌套三层**各自的页面主世界**里各写一个 __fg 标记(值互异),
再用 frame_id 让工具去读同一个表达式 String(window.__fg):
  · 读到对应层的值 -> 工具落在该框架的**页面主世界**(可直接读页面全局)
  · 读到 undefined  -> 工具落在**隔离世界**(DOM 可达、页面全局不可达)
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
                            ('\n        ' + str(detail)[:300]) if detail else ''))


def js(expr, frame=None):
    a = {"code": expr}
    if frame is not None:
        a["frame_id"] = frame
    e, t = call("browser_execute_js", a)
    return ('ERR:' if e else '') + val(t)


BUILD = '''(function(){
  document.body.insertAdjacentHTML('beforeend',"<input id='tgt' value='MAIN'>");
  var f1=document.createElement('iframe');
  f1.id='fr1'; f1.name='mcpfr';
  f1.srcdoc="<input id='tgt' value='IFRAME1'><iframe id='fr2' name='mcpfr2' srcdoc=\\"<input id='tgt' value='IFRAME2'>\\"></iframe>";
  document.body.appendChild(f1);
  return 'built';
})()'''

print('== 造页面并在**三层各自的页面主世界**里各写一个标记 ==')
call("browser_navigate", {"url": "https://example.com/?framectx=%d" % int(time.time()),
                          "wait_for_load": True})
call("browser_execute_js", {"code": BUILD})
time.sleep(1.5)
# 主框架主世界
print('   主: %s' % js("window.__fg='MAIN_WORLD'; String(window.__fg)"))
# 外层/嵌套: 从主框架穿过 contentDocument.defaultView 写(那是各框架的**页面主世界**)
o1 = js("(function(){var f=document.getElementById('fr1');"
        "f.contentDocument.defaultView.__fg='OUT_WORLD';"
        "var g=f.contentDocument.getElementById('fr2');"
        "g.contentDocument.defaultView.__fg='NEST_WORLD';"
        "return f.contentDocument.defaultView.__fg+'/'+g.contentDocument.defaultView.__fg})()")
print('   外/嵌: %s' % o1)
rec('基线: 三层主世界的标记都已就位(判别有效)', o1 == 'OUT_WORLD/NEST_WORLD', o1)

e, t = call("browser_get_frames", {})
frames = []
try:
    frames = json.loads(t).get("frames") or []
except Exception:
    pass
out_f = next((f for f in frames if f.get('name') == 'mcpfr'), None)
nest_f = next((f for f in frames if f.get('name') == 'mcpfr2'), None)

print('\n== A. 主框架(默认上下文)应落在页面主世界 ==')
got = js("String(window.__fg)")
print('   -> %r' % got)
rec('主框架读到 MAIN_WORLD', got == 'MAIN_WORLD', got)

print('\n== B. ★外层 iframe: 用户代码看到的是哪个世界 ==')
if out_f:
    got = js("String(window.__fg)", 'mcpfr')
    print('   frame_id=mcpfr -> String(window.__fg) = %r' % got)
    if got == 'OUT_WORLD':
        rec('★落在该框架的**页面主世界**(可读页面全局)', True, got)
    elif got == 'undefined':
        rec('★落在该框架的**页面主世界**(可读页面全局)', False,
            'undefined -> 隔离世界: DOM 可达但页面全局不可达')
    else:
        rec('★落在该框架的页面主世界', False, '意外值 %r' % got)
else:
    rec('★外层 iframe 世界量测', False, '取不到外层框架')

print('\n== C. 嵌套 iframe 同一量测 ==')
if nest_f:
    got = js("String(window.__fg)", 'mcpfr2')
    print('   frame_id=mcpfr2 -> %r' % got)
    rec('嵌套框架的世界一致性(与 B 同结论)', (got == 'NEST_WORLD') or (got == 'undefined'), got)
else:
    rec('嵌套 iframe 世界量测', False, '取不到嵌套框架')

print('\n== D. DOM 可达性(两种世界都应成立) ==')
if nest_f:
    got = js("document.querySelector('#tgt').value", 'mcpfr2')
    rec('嵌套框架内 DOM 可读(值 IFRAME2)', got == 'IFRAME2', got)

print('\n== E. 页面自己在子框架里定义的原生函数是否可调用 ==')
if out_f:
    js("(function(){var f=document.getElementById('fr1');"
       "f.contentDocument.defaultView.__pageFn=function(){return 'PAGE_FN_RESULT'}})()")
    got = js("(typeof window.__pageFn==='function')?window.__pageFn():'NO_FN'", 'mcpfr')
    print('   -> %r' % got)
    rec('可调用该框架主世界的页面函数', got == 'PAGE_FN_RESULT', got)

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过(结论见上, B/C 为量测臂) ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
