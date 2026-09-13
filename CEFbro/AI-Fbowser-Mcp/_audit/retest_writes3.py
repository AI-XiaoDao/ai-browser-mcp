# -*- coding: utf-8 -*-
"""严格复测 v3: 每次导航到**唯一 URL**(带递增查询串)以强制真实重新载入。

前两轮测试自伤记录:
  v1: 预言机 browser_execute_js 自身 5s 超时 -> 误判 3 个写操作为"未生效"(协议锁排队污染)。
  v2: browser_navigate 到**同一** about:blank 被实现判定为"已在该地址"而跳过重载
      -> 文档残留、__c 累加、querySelector 命中旧元素 -> 又被误判。
本版用唯一 URL 彻底消除这两类污染。
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
    """唯一 URL 强制真实导航 + 唯一ID。返回该页面的元素ID字典。"""
    N[0] += 1
    run = "r%d%s" % (N[0], str(int(time.time()))[-4:])
    pw.call("browser_navigate",
            {"url": "https://example.com/?probe=%s" % run, "wait_for_load": True}, 60)
    time.sleep(0.8)
    ids = {"i": "i" + run, "b": "b" + run, "s": "s" + run, "x": "x" + run}
    js = ("document.body.insertAdjacentHTML('beforeend',"
          "'<input id=\"%s\"><button id=\"%s\">go</button>"
          "<select id=\"%s\"><option value=a>a</option>"
          "<option value=b selected>b</option></select><div id=\"%s\">x</div>');"
          "window.__c=0;"
          "document.getElementById('%s').addEventListener('click',function(){window.__c++;});"
          "'ok'") % (ids["i"], ids["b"], ids["s"], ids["x"], ids["b"])
    pw.oracle(js)
    time.sleep(0.3)
    # 自检: 页面必须干净(基线值正确), 否则本轮读数不可信
    base_c = pw.oracle("String(window.__c)")
    base_v = pw.oracle("document.getElementById('%s').value" % ids["i"])
    if base_c != "0" or base_v != "":
        print("  !! 页面基线不干净 (__c=%r value=%r) -> 本轮读数不可信, 中止" % (base_c, base_v))
        sys.exit(2)
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
    pw.rec(tag, ok, "err=%s 预言机=%r 期望=%r" % (e, got, want))


print("== 严格正例 v3(唯一URL + 唯一ID + 基线自检) ==")
ids = fresh()
check("fill_set_value -> value", "browser_fill_set_value",
      {"selector": "#" + ids["i"], "value": "v1"},
      "document.getElementById('%s').value" % ids["i"], "v1")

ids = fresh()
check("dom_set_value -> value", "browser_dom_set_value",
      {"selector": "#" + ids["i"], "value": "v2"},
      "document.getElementById('%s').value" % ids["i"], "v2")

ids = fresh()
check("dom_click -> __c", "browser_dom_click",
      {"selector": "#" + ids["b"]}, "String(window.__c)", "1")

ids = fresh()
check("fill_click -> __c", "browser_fill_click",
      {"selector": "#" + ids["b"]}, "String(window.__c)", "1")

ids = fresh()
check("dom_select idx=0 -> selectedIndex", "browser_dom_select",
      {"selector": "#" + ids["s"], "index": 0},
      "String(document.getElementById('%s').selectedIndex)" % ids["s"], "0")

ids = fresh()
check("fill_select value=b -> selectedIndex", "browser_fill_select",
      {"selector": "#" + ids["s"], "value": "b"},
      "String(document.getElementById('%s').selectedIndex)" % ids["s"], "1")

ids = fresh()
check("dom_set_html -> innerHTML", "browser_dom_set_html",
      {"selector": "#" + ids["x"], "html": "<b>H</b>"},
      "document.getElementById('%s').innerHTML" % ids["x"], "<b>H</b>")

ids = fresh()
check("fill_attr_set data-k=9", "browser_fill_attr_set",
      {"selector": "#" + ids["x"], "attribute": "data-k", "value": "9"},
      "document.getElementById('%s').getAttribute('data-k')" % ids["x"], "9")

ids = fresh()
check("fill_focus -> activeElement", "browser_fill_focus",
      {"selector": "#" + ids["i"]}, "document.activeElement.id", ids["i"])

print("\n== 汇总 ==")
bad = [x for x in pw.results if not x[1]]
print("  通过 %d / %d" % (len(pw.results) - len(bad), len(pw.results)))
for tag, _, d in bad:
    print("  未通过: %s -> %s" % (tag, str(d)[:150]))
