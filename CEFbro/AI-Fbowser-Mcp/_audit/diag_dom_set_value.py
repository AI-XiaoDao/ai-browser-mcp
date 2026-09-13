# -*- coding: utf-8 -*-
"""定位 browser_dom_set_value "报成功但值没变" 的根因。

browser_dom_set_value 走 类_MCP_存在后填表回调 的 set_value 分支, 其 JS 为(见 MCP_Callbacks.wsv:217):
  (function(){var e=document.querySelector('SEL');if(e){try{e.focus();
    var n=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value');
    if(n&&n.set)n.set.call(e,'VAL');else e.value='VAL';
    ...dispatch keydown/beforeinput/input/keyup/change...}
    catch(x){e.value='VAL';e.dispatchEvent(new Event('input',{bubbles:true}));
             e.dispatchEvent(new Event('change',{bubbles:true}));}}})()
对照: browser_fill_set_value 走 填表框架.置元素内容 (原生)。

本脚本分离两个变量:
  A. 手工用 browser_execute_js 跑同一段 JS  -> 若值变了, 说明 JS 没问题, 是链路问题
  B. 调 browser_dom_set_value              -> 复现"报成功但值没变"
"""
import importlib.util
import sys
import time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("pw", "probe_writes.py")
pw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pw)

N = [0]


def fresh():
    N[0] += 1
    run = "d%d%s" % (N[0], str(int(time.time()))[-4:])
    pw.call("browser_navigate",
            {"url": "https://example.com/?diag=%s" % run, "wait_for_load": True}, 60)
    time.sleep(0.8)
    eid = "in" + run
    pw.oracle("document.body.insertAdjacentHTML('beforeend','<input id=\"%s\">');'ok'" % eid)
    time.sleep(0.3)
    return eid


def orc(expr, tries=4, label=""):
    for _ in range(tries):
        v = pw.oracle(expr)
        if not v.startswith("<ORACLE-ERR"):
            return v
        time.sleep(2.0)
    print("     (预言机 %s 仍超时: %s)" % (label, v[:60]))
    return v


print("== A. 手工执行 类_MCP_存在后填表回调 的 set_value JS ==")
eid = fresh()
print("  基线 value = %r" % orc("document.getElementById('%s').value" % eid, label="基线"))
js = ("(function(){var e=document.querySelector('#%s');if(e){try{e.focus();"
      "var n=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value');"
      "if(n&&n.set)n.set.call(e,'MANUAL');else e.value='MANUAL';"
      "e.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,cancelable:true}));"
      "e.dispatchEvent(new Event('beforeinput',{bubbles:true,cancelable:true}));"
      "e.dispatchEvent(new InputEvent('input',{bubbles:true,cancelable:true,inputType:'insertText',data:'MANUAL'}));"
      "e.dispatchEvent(new KeyboardEvent('keyup',{bubbles:true,cancelable:true}));"
      "e.dispatchEvent(new Event('change',{bubbles:true,cancelable:true}));}"
      "catch(x){e.value='MANUAL';e.dispatchEvent(new Event('input',{bubbles:true}));"
      "e.dispatchEvent(new Event('change',{bubbles:true}));}}})()") % eid
e, t = pw.call("browser_execute_js", {"code": js}, 30)
print("  执行JS返回: err=%s %s" % (e, t[:90]))
print("  执行后 value = %r   <-- 若为 'MANUAL' 则 JS 本身没问题" %
      orc("document.getElementById('%s').value" % eid, label="A后"))

print("\n== B. 调 browser_dom_set_value ==")
eid2 = fresh()
print("  基线 value = %r" % orc("document.getElementById('%s').value" % eid2, label="基线"))
e, t = pw.resolve("browser_dom_set_value", {"selector": "#" + eid2, "value": "VIA-TOOL"})
print("  工具返回: err=%s %s" % (e, t[:150]))
print("  执行后 value = %r   <-- 若为空则确认'报成功但未生效'" %
      orc("document.getElementById('%s').value" % eid2, label="B后"))

print("\n== C. 对照: browser_fill_set_value (原生填表) ==")
eid3 = fresh()
e, t = pw.resolve("browser_fill_set_value", {"selector": "#" + eid3, "value": "VIA-FILL"})
print("  工具返回: err=%s %s" % (e, t[:150]))
print("  执行后 value = %r" % orc("document.getElementById('%s').value" % eid3, label="C后"))

print("\n== D. 只读一次: dom_set_value 后立刻连读 3 次 value(排除时序抖动) ==")
eid4 = fresh()
pw.resolve("browser_dom_set_value", {"selector": "#" + eid4, "value": "T1"})
for k in range(3):
    time.sleep(1.2)
    print("   第%d次读: %r" % (k + 1, orc("document.getElementById('%s').value" % eid4,
                                         label="D%d" % k)))
