# -*- coding: utf-8 -*-
r"""验证第127轮修复: `browser_dom_query` 的 **index 必须真的生效**（此前静默返回第 1 个匹配）。

预言机 = 页面上**自己注入的三个元素**（文本 A/B/C 与属性 k0/k1/k2 由脚本设定, 不依赖被测工具）:
  ① 省略 index → A（默认第 1 个，回归）; ② index=1 → B; ③ index=2 → C（**修复点**: 旧实现三步都给 A）;
  ④ attribute 模式同样按 index 取到正确的 k2; ⑤ 越界 → 可行动失败且告出"实际只有 3 个匹配";
  ⑥ 负索引 → 明确拒绝; ⑦ 选择器不存在 → 仍是原来的"元素不存在"错误(回归)。

用法: py -3 _audit\verify_dom_query_index.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []
CLS = "dqi_probe"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def msg(t):
    try:
        o = json.loads(t)
    except Exception:
        return t
    d = o.get("data")
    if isinstance(d, dict) and isinstance(d.get("message"), str):
        return d["message"]
    return str(o.get("message") or t)


print('== 前置: 注入三个同类元素(文本 A/B/C, 属性 k0/k1/k2) ==')
_e, _t = call("browser_navigate", {"url": "https://example.com/?dqi=%d" % int(time.time())})
call("browser_execute_js", {"code":
     "(function(){var o=document.querySelectorAll('.%s');for(var i=0;i<o.length;i++)o[i].remove();"
     "var h='';for(var j=0;j<3;j++){h+='<div class=\"%s\" data-k=\"k'+j+'\">'+String.fromCharCode(65+j)+'</div>';}"
     "document.body.insertAdjacentHTML('beforeend',h);return 'ok'})()" % (CLS, CLS)})
time.sleep(0.6)
_e2, t2 = call("browser_execute_js", {"code": "document.querySelectorAll('.%s').length" % CLS})
rec("页面已注入 3 个元素(预言机就位)", '"message":"3"' in t2, t2[:60])

print('\n== ① 省略 index → 第 1 个(A) 回归 ==')
e1, t1 = call("browser_dom_query", {"selector": "." + CLS})
rec("默认取第 1 个匹配", (not e1) and msg(t1) == "A", msg(t1)[:40])

print('\n== ②③ index=1/2 必须取到第 2/3 个(旧实现会静默给 A) ==')
e2, t2b = call("browser_dom_query", {"selector": "." + CLS, "index": 1})
rec("index=1 → B", (not e2) and msg(t2b) == "B", msg(t2b)[:40])
e3, t3 = call("browser_dom_query", {"selector": "." + CLS, "index": 2})
rec("index=2 → C(关键修复点)", (not e3) and msg(t3) == "C", msg(t3)[:40])

print('\n== ④ attribute 模式同样按 index 取 ==')
e4, t4 = call("browser_dom_query", {"selector": "." + CLS, "attribute": "data-k", "index": 2})
rec("attribute+index=2 → k2", (not e4) and msg(t4) == "k2", msg(t4)[:40])
e4b, t4b = call("browser_dom_query", {"selector": "." + CLS, "attribute": "data-k", "index": 0})
rec("attribute+index=0 → k0", (not e4b) and msg(t4b) == "k0", msg(t4b)[:40])

print('\n== ⑤⑥ 越界/负索引必须可行动失败(不许退回第一个) ==')
e5, t5 = call("browser_dom_query", {"selector": "." + CLS, "index": 5})
rec("越界返回失败", e5, msg(t5)[:60])
rec("失败文案告出实际匹配数(3)", "只有 3 个匹配" in msg(t5), msg(t5)[:90])
rec("失败文案给出改法(去掉 index)", "去掉 index" in msg(t5), msg(t5)[:90])
e6, t6 = call("browser_dom_query", {"selector": "." + CLS, "index": -1})
rec("负索引被明确拒绝", e6 and ("不能为负" in msg(t6)), msg(t6)[:70])

print('\n== ⑦ 回归: 不存在的选择器仍是原错误 ==')
e7, t7 = call("browser_dom_query", {"selector": ".no-such-elem-xyz"})
rec("不存在元素仍报'元素不存在或取不到值'", e7 and ("元素不存在" in msg(t7)), msg(t7)[:70])

print('\n== ⑧ schema 描述已说明越界行为 ==')
tl = json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())
d = {x["name"]: x for x in tl.get("tools", [])}
desc = ((d.get("browser_dom_query", {}).get("inputSchema") or {}).get("properties") or {}).get("index", {}).get("description", "")
rec("index 参数描述写明'越界会失败并告出匹配数'", "不会静默返回第 1 个" in desc, desc[:100])

call("browser_execute_js", {"code": "(function(){var o=document.querySelectorAll('.%s');for(var i=0;i<o.length;i++)o[i].remove();return 'cleanup'})()" % CLS})
bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
