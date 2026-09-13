# -*- coding: utf-8 -*-
r"""G1b 验收: browser_execute_js {frame_id} 能否在**指定框架**(含**嵌套** iframe)内求值。

判别设计: 主框架 / 外层 iframe / **内层嵌套 iframe** 三层各放一个 `#tgt`, 值分别为
MAIN / IFRAME1 / IFRAME2(三值互异) -> 同一段 JS 在三层必须读出三个不同值。
  · 只有"真的切了执行上下文"才能读出后两个; 若实现是静默回退主框架, 三条臂会全部读到 MAIN。
  · 未知 frame_id 那一臂用**带副作用**的代码(写 window.__mcp_mark), 然后回主框架读该标记:
    标记必须仍不存在 —— 这才证明"没有偷偷在主框架执行"(只比对回包文本是证明不了这一点的)。
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
                            ('\n        ' + str(detail)[:320]) if detail else ''))


def js(expr, frame=None, world=None):
    a = {"code": expr}
    if frame is not None:
        a["frame_id"] = frame
    if world is not None:
        a["world"] = world
    e, t = call("browser_execute_js", a)
    v = ('ERR:' if e else '') + val(t)
    if world == 'main' and e:
        # world=main 走**原生"带返回值 JS"通道**, 实测约 8% 概率回调丢失(与主框架 browser_evaluate 同源性质)。
        # 这里如实重试一次并标注, 以便既验证能力、又不把已知抖动误判成功能缺陷。
        e2, t2 = call("browser_execute_js", a)
        v2 = ('ERR:' if e2 else '') + val(t2)
        return v2 + '   [需重试一次(原生通道固有抖动)]'
    return v


# 预言机: 从主框架穿透读三层(三层都是 srcdoc, 同源, 可直接穿 contentDocument)
V_MAIN = "document.querySelector('#tgt').value"
V_OUT = "document.getElementById('fr1').contentDocument.querySelector('#tgt').value"
V_NEST = ("document.getElementById('fr1').contentDocument.getElementById('fr2')"
          ".contentDocument.querySelector('#tgt').value")

BUILD = '''(function(){
  document.body.insertAdjacentHTML('beforeend',"<input id='tgt' value='MAIN'>");
  var f1=document.createElement('iframe');
  f1.id='fr1'; f1.name='mcpfr';
  f1.srcdoc="<input id='tgt' value='IFRAME1'><iframe id='fr2' name='mcpfr2' srcdoc=\\"<input id='tgt' value='IFRAME2'>\\"></iframe>";
  document.body.appendChild(f1);
  return 'built';
})()'''

print('== 造页面: 主框架 / 外层 iframe(名 mcpfr) / **嵌套** iframe(名 mcpfr2) 各一个 #tgt ==')
call("browser_navigate", {"url": "https://example.com/?framexec=%d" % int(time.time()),
                          "wait_for_load": True})
e, t = call("browser_execute_js", {"code": BUILD})
print('   注入回包: isError=%s %s' % (e, val(t)[:80]))
time.sleep(1.5)
vm, vo, vn = js(V_MAIN), js(V_OUT), js(V_NEST)
print('   预言机: 主=%r 外层=%r 嵌套=%r' % (vm, vo, vn))
rec('基线: 三层各自可读且三值互异(判别有效)',
    vm == 'MAIN' and vo == 'IFRAME1' and vn == 'IFRAME2',
    '主=%r 外=%r 嵌=%r' % (vm, vo, vn))

e, t = call("browser_get_frames", {})
frames = []
try:
    frames = json.loads(t).get("frames") or []
except Exception as ex:
    print('   解析 frames 失败: %r / 原文 %s' % (ex, t[:200]))
print('   browser_get_frames: %d 个框架' % len(frames))
for f in frames:
    print('      id=%-14s name=%-22s main=%s' %
          (f.get('id'), f.get('name'), f.get('is_main')))
out_f = next((f for f in frames if f.get('name') == 'mcpfr'), None)
nest_f = next((f for f in frames if f.get('name') == 'mcpfr2'), None)
print('   外层 id=%r 嵌套 id=%r' % ((out_f or {}).get('id'), (nest_f or {}).get('id')))

# 诊断(非判定): 两侧清单是否仍然同序
e2, t2 = call("browser_cdp_call", {"method": "Page.getFrameTree", "params": {}})
cdp_ids = []
try:
    inner = json.loads(t2).get("message") or t2
    print('   CDP getFrameTree 原文片段: %s' % str(inner)[:220])
    import re
    cdp_ids = re.findall(r'"id"\s*:\s*"([0-9A-Fa-f]+)"', str(inner))
except Exception as ex:
    print('   CDP 框架树解析失败: %r' % ex)
print('   CDP 侧顺序 ids = %s' % cdp_ids)
print('   CEF 侧顺序 ids = %s' % [f.get('id') for f in frames])

print('\n== A. ★ frame_id = 嵌套 iframe 的 id: 必须在**内层**求值 ==')
if nest_f:
    got = js(V_MAIN, nest_f.get('id'))
    print('   同一段 JS 在嵌套框架里 -> %r' % got)
    rec('★嵌套 iframe 内读出 IFRAME2(证明真的切了上下文)', got == 'IFRAME2', got)
    got2 = js(V_OUT, nest_f.get('id'))
    print('   (反证)同一嵌套上下文里读它自己的外层引用 -> %r' % got2)
else:
    rec('★嵌套 iframe 内读出 IFRAME2', False, 'browser_get_frames 里没有 name=mcpfr2 的框架')

print('\n== B. frame_id = 外层 iframe(**按名字**): 读到 IFRAME1, 与嵌套区分 ==')
got = js(V_MAIN, 'mcpfr')
print('   -> %r' % got)
rec('按框架名定位到外层(值 IFRAME1, 非 MAIN/IFRAME2)', got == 'IFRAME1', got)

print('\n== C. frame_id = 外层 iframe(**按 id**) ==')
if out_f:
    got = js(V_MAIN, out_f.get('id'))
    print('   -> %r' % got)
    rec('按框架 id 定位到外层', got == 'IFRAME1', got)
else:
    rec('按框架 id 定位到外层', False, '取不到外层 id')

print('\n== D. frame_id = 嵌套 iframe 的**序号**(文本数字) ==')
if nest_f:
    idx = frames.index(nest_f)
    got = js(V_MAIN, str(idx))
    print('   序号=%d -> %r' % (idx, got))
    rec('按序号定位到嵌套框架', got == 'IFRAME2', got)
else:
    rec('按序号定位到嵌套框架', False, '无嵌套框架')

print('\n== E. 不带 frame_id / frame_id=main: 主框架(向后兼容回归) ==')
got_no = js(V_MAIN)
got_main = js(V_MAIN, 'main')
print('   不带=%r  main=%r' % (got_no, got_main))
rec('不带 frame_id 仍是主框架', got_no == 'MAIN', got_no)
rec('frame_id=main 仍是主框架', got_main == 'MAIN', got_main)

print('\n== F. ★未知 frame_id: 必须报错, 且**不得在任何框架内执行**(副作用判据) ==')
js("window.__mcp_mark=undefined")
e, t = call("browser_execute_js", {"code": "window.__mcp_mark=1;'x'",
                                   "frame_id": "no-such-frame-zzz"})
print('   回包: isError=%s %s' % (e, val(t)[:200]))
mark = js("String(window.__mcp_mark)")
print('   主框架 window.__mcp_mark = %r' % mark)
rec('未知 frame_id 返回错误', e, val(t)[:200])
rec('错误信息可行动(提到框架/未找到)', ('框架' in val(t)) or ('frame' in val(t).lower()), val(t)[:200])
rec('★未在主框架偷偷执行(标记仍为 undefined)', mark == 'undefined', mark)

print('\n== G. JS 通道健康回归: 主框架写入后能读回 ==')
js("window.__mcp_mark2=0")
js("window.__mcp_mark2=42")
got = js("String(window.__mcp_mark2)")
rec('主框架赋值/读回一致(正常路径未被本次改动破坏)', got == '42', got)

print('\n== H. ★world=main: 子框架内是该框架的**页面主世界**(能读页面自己挂的全局/函数) ==')
# 从主框架穿过 contentDocument.defaultView 写进各框架的**页面主世界**
o = js("(function(){var f=document.getElementById('fr1');"
       "f.contentDocument.defaultView.__fg='OUT_WORLD';"
       "f.contentDocument.defaultView.__pgfn=function(){return 'PAGE_FN_OK'};"
       "var g=f.contentDocument.getElementById('fr2');"
       "g.contentDocument.defaultView.__fg='NEST_WORLD';"
       "return f.contentDocument.defaultView.__fg+'/'+g.contentDocument.defaultView.__fg})()")
print('   页面侧标记: %s' % o)
rec('基线: 三层主世界标记已就位', o == 'OUT_WORLD/NEST_WORLD', o)
go = js("String(window.__fg)", 'mcpfr', 'main')
gn = js("String(window.__fg)", 'mcpfr2', 'main')
print('   world=main 外层 String(window.__fg) = %r ; 嵌套 = %r' % (go, gn))
rec('★world=main 外层读到页面主世界的 OUT_WORLD(非 undefined)', go == 'OUT_WORLD', go)
rec('★world=main 嵌套读到页面主世界的 NEST_WORLD(非 undefined)', gn == 'NEST_WORLD', gn)
gf = js("(typeof window.__pgfn==='function')?window.__pgfn():'NO_FN'", 'mcpfr', 'main')
print('   外层调用页面定义的函数 -> %r' % gf)
rec('★可调用页面在子框架主世界定义的函数(隔离世界做不到)', gf == 'PAGE_FN_OK', gf)

print('\n== I. 缺省(隔离世界)的**边界**如实呈现: 读不到页面全局, 但 DOM 正常 ==')
gi = js("String(window.__fg)", 'mcpfr')
di = js("document.querySelector('#tgt').value", 'mcpfr')
print('   缺省 String(window.__fg) = %r ; DOM = %r' % (gi, di))
rec('缺省下 DOM 可读(隔离世界的主要用途成立)', di == 'IFRAME1', di)
rec('缺省下页面全局不可见(与文档所述一致, 属已知边界而非故障)',
    gi == 'undefined', gi)

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
