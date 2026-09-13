# -*- coding: utf-8 -*-
r"""验证第125轮补的缺口: browser_get_frames 的 **parent_id**(补类库 取父框架) 与 **is_focused**。

预言机 = **框架名字链**(名字由本脚本设定, 不依赖被测工具):
  主页注入 outer(srcdoc) → inner(srcdoc); 于是"名字→id"与"父id"必须构成链:
    main.parent_id == ""(主框架无父) 且 id == 名为 outer 的框架的 parent_id
    inner.parent_id == 名为 outer 的框架的 id
  另外: is_focused 必须**恰好一个**为真(键盘输入只能落在一个框架)。

用法: py -3 _audit\verify_frames_parent.py
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
OUTER = "pfx_outer"
INNER = "pfx_inner"


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
    print('  [%s] %-48s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def frames():
    """取框架列表: 回包形如 {id,success,data:{frames:[...]}} 或 {...,frames:[...]}"""
    e, t = call("browser_get_frames", {})
    if e:
        return None, t
    try:
        o = json.loads(t)
    except Exception as ex:
        return None, 'JSON解析失败 %r | 原文: %s' % (ex, t[:200])
    d = o.get("data") if isinstance(o.get("data"), dict) else o
    fr = d.get("frames") if isinstance(d, dict) else None
    if fr is None and isinstance(d, list):
        fr = d
    return fr, t


print('== 前置: 建一个"两层嵌套 srcdoc iframe"的页面(名字固定, 作为预言机) ==')
_e, tt = call("browser_navigate", {"url": "https://example.com/?pfx=%d" % int(time.time())})
print('   navigate: %s' % tt[:70])
js = ("(function(){var o=document.getElementById('pfx_o');if(o)o.remove();"
      "var d=document.createElement('div');d.id='pfx_o';"
      "d.innerHTML='<iframe name=\"%s\" srcdoc=\"<iframe name=%s srcdoc=<p>inner</p>></iframe>\"></iframe>';"
      "document.body.appendChild(d);return 'ok'})()" % (OUTER, INNER))
_e2, t2 = call("browser_execute_js", {"code": js})
print('   注入: %s' % t2[:80])
time.sleep(1.2)

fr, raw = frames()
rec("browser_get_frames 成功且可解析", fr is not None, (raw or "")[:90])
if not fr:
    print('\n结果: 0/%d 通过(列表取不到, 后续断言无法进行)' % len(RES))
    sys.exit(1)

print('   框架清单: %s' % json.dumps(
    [{"name": f.get("name"), "id": (f.get("id") or "")[:8], "parent": (f.get("parent_id") or "")[:8],
      "main": f.get("is_main"), "focused": f.get("is_focused")} for f in fr], ensure_ascii=False)[:400])

by_name = {f.get("name"): f for f in fr if f.get("name")}
main = next((f for f in fr if f.get("is_main") is True), None)
outer = by_name.get(OUTER)
inner = by_name.get(INNER)

rec("清单一共至少 3 个框架(主 + 外层 + 内层)", len(fr) >= 3, "len=%d names=%s" % (len(fr), list(by_name.keys())))
rec("能找到主框架(is_main=true)", main is not None, str(main)[:80])
rec("能按名字找到外层/内层框架(且两个 id 不同)",
    outer is not None and inner is not None and outer.get("id") != inner.get("id"),
    "outer=%s inner=%s" % ((outer or {}).get("id", "")[:8], (inner or {}).get("id", "")[:8]))

rec("每项都带 parent_id 字段(不能缺字段)", all("parent_id" in f for f in fr),
    "缺字段项: %s" % [f.get("name") for f in fr if "parent_id" not in f])
rec("每项都带 is_focused 字段", all("is_focused" in f for f in fr),
    "缺字段项: %s" % [f.get("name") for f in fr if "is_focused" not in f])

if main and outer and inner:
    rec("主框架 parent_id 为空串(无父, 如实表达)", main.get("parent_id") == "",
        "main.parent_id=%r" % main.get("parent_id"))
    rec("外层框架的父 = 主框架 id(链第 1 环)",
        outer.get("parent_id") == main.get("id"),
        "outer.parent=%s main.id=%s" % ((outer.get("parent_id") or "")[:8], (main.get("id") or "")[:8]))
    rec("内层框架的父 = 外层框架 id(链第 2 环)",
        inner.get("parent_id") == outer.get("id"),
        "inner.parent=%s outer.id=%s" % ((inner.get("parent_id") or "")[:8], (outer.get("id") or "")[:8]))
    rec("内层框架的父**不是**主框架(证明不是一次性平铺)", inner.get("parent_id") != main.get("id"),
        "inner.parent=%s main.id=%s" % ((inner.get("parent_id") or "")[:8], (main.get("id") or "")[:8]))
else:
    rec("三层链断言(前置项齐备)", False, "缺 main/outer/inner 之一, 后面 4 条断言未执行")

focused = [f.get("name") for f in fr if f.get("is_focused") is True]
rec("is_focused 恰好一个为真", len(focused) == 1, "focused=%s" % focused)

print('\n== 清理 ==')
call("browser_execute_js", {"code": "(function(){var o=document.getElementById('pfx_o');if(o)o.remove();return 'ok'})()"})

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
