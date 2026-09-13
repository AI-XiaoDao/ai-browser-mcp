# -*- coding: utf-8 -*-
"""严格复测: 每次用**全新页面 + 唯一ID**, 消除"同名元素残留导致 querySelector 命中旧元素"
这一测试自身缺陷(上一轮复测即因此把 dom_set_value 的读数污染成上一轮的值)。

同时覆盖 browser_fill_form (批量填表) 的未命中行为。
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

RUN = str(int(time.time()))[-6:]


def fresh():
    """全新文档 + 唯一ID, 彻底避免残留元素。"""
    pw.call("browser_navigate", {"url": "about:blank", "wait_for_load": True}, 60)
    time.sleep(0.8)
    ids = {"i": "i" + RUN, "b": "b" + RUN, "s": "s" + RUN, "x": "x" + RUN}
    js = ("document.body.insertAdjacentHTML('beforeend',"
          "'<input id=\"%s\"><button id=\"%s\">go</button>"
          "<select id=\"%s\"><option value=a>a</option>"
          "<option value=b selected>b</option></select><div id=\"%s\">x</div>');"
          "window.__c=0;"
          "document.getElementById('%s').addEventListener('click',function(){window.__c++;});"
          "'ok'") % (ids["i"], ids["b"], ids["s"], ids["x"], ids["b"])
    pw.oracle(js)
    time.sleep(0.4)
    return ids


def orc(expr, tries=4):
    for _ in range(tries):
        v = pw.oracle(expr)
        if not v.startswith("<ORACLE-ERR"):
            return v
        time.sleep(2.0)
    return v


def check(tag, tool, args, expr, want):
    e, t = pw.resolve(tool, args)
    got = orc(expr)
    ok = (not e) and got == want
    pw.rec(tag, ok, "err=%s 预言机=%r 期望=%r | %s" % (e, got, want, t[:80]))


print("== 严格正例(全新页面 + 唯一ID) ==")
ids = fresh()
pw.call("browser_fill_set_value", {"selector": "#" + ids["i"], "value": "v-fill"}, 40)
check("fill_set_value -> inp.value", "browser_fill_set_value",
      {"selector": "#" + ids["i"], "value": "v-fill2"},
      "document.getElementById('%s').value" % ids["i"], "v-fill2")

ids = fresh()
check("dom_set_value -> inp.value", "browser_dom_set_value",
      {"selector": "#" + ids["i"], "value": "v-dom"},
      "document.getElementById('%s').value" % ids["i"], "v-dom")

ids = fresh()
check("dom_click -> __c", "browser_dom_click",
      {"selector": "#" + ids["b"]}, "String(window.__c)", "1")

ids = fresh()
check("dom_select index=0 -> selectedIndex", "browser_dom_select",
      {"selector": "#" + ids["s"], "index": 0},
      "String(document.getElementById('%s').selectedIndex)" % ids["s"], "0")

ids = fresh()
check("dom_set_html -> innerHTML", "browser_dom_set_html",
      {"selector": "#" + ids["x"], "html": "<b>H</b>"},
      "document.getElementById('%s').innerHTML" % ids["x"], "<b>H</b>")

ids = fresh()
check("fill_click -> __c", "browser_fill_click",
      {"selector": "#" + ids["b"]}, "String(window.__c)", "1")

ids = fresh()
check("fill_select value=b -> selectedIndex", "browser_fill_select",
      {"selector": "#" + ids["s"], "value": "b"},
      "String(document.getElementById('%s').selectedIndex)" % ids["s"], "1")

print("\n== browser_fill_form 未命中行为 ==")
ids = fresh()
e, t = pw.resolve("browser_fill_form",
                  {"fields": '[{"selector":"#nope-xyz","value":"1"}]'}, 45)
print("  fill_form 未命中: err=%s resp=%s" % (e, t[:220]))

print("\n== 汇总 ==")
bad = [x for x in pw.results if not x[1]]
print("  通过 %d / %d" % (len(pw.results) - len(bad), len(pw.results)))
for tag, _, d in bad:
    print("  未通过: %s -> %s" % (tag, str(d)[:150]))
