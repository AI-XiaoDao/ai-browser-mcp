# -*- coding: utf-8 -*-
"""验收 browser_fill_get_text / browser_fill_set_text。

★核心区分性判据: 造一个**含隐藏子元素**的节点:
    <div id="tt">可见<span style="display:none">隐藏</span></div>
  · innerText    = "可见"      (渲染后文本, 隐藏的不算)
  · textContent  = "可见隐藏"  (原始文本, 隐藏的也算)
若本工具返回的是"可见"、而 browser_fill_attr_get(不传 attribute) 返回"可见隐藏",
即证明本工具**确实读的是 innerText**, 不是在重复既有工具。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
R = []


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:260])


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?innertext=1", "wait_for_load": True}, 90)
time.sleep(0.5)

print("== 0) 造一个含**隐藏子元素**的节点, 以及一个用于写入的节点 ==")
e, t = call("browser_execute_js", {"code":
    "document.body.insertAdjacentHTML('beforeend',"
    "'<div id=\"tt\">可见<span style=\"display:none\">隐藏</span></div>"
    "<div id=\"wr\">原文</div>');'ok'"}, 40)
print("   注入: isError=%s %s" % (e, t[:120]))

print("\n== 1) ★innerText vs textContent 对照 ==")
e1, t1 = call("browser_fill_get_text", {"selector": "#tt"})
print("   browser_fill_get_text(#tt)      -> isError=%s %s" % (e1, t1[:160]))
e2, t2 = call("browser_fill_attr_get", {"selector": "#tt"})
print("   browser_fill_attr_get(#tt,无attr)-> isError=%s %s" % (e2, t2[:160]))
arm("本工具返回 innerText(不含隐藏文本)", (not e1) and ('可见' in t1) and ('隐藏' not in t1),
    "get_text=%s" % t1[:120])
arm("既有工具返回 textContent(含隐藏文本) —— 证明两者确实不同",
    (not e2) and ('可见' in t2) and ('隐藏' in t2), "attr_get=%s" % t2[:120])

print("\n== 2) h1 读取 ==")
e, t = call("browser_fill_get_text", {"selector": "h1"})
print("   -> isError=%s %s" % (e, t[:160]))
arm("读到 h1 的 innerText", (not e) and ('Example Domain' in t), t[:140])

print("\n== 3) 元素不存在 -> 必须明确报错(不返回空串冒充) ==")
e, t = call("browser_fill_get_text", {"selector": "#not-exist-xyz"})
print("   -> isError=%s %s" % (e, t[:220]))
arm("元素不存在时明确报错", e and ('元素不存在' in t), t[:200])

print("\n== 4) set_text 写入 + 回读 ==")
e, t = call("browser_fill_set_text", {"selector": "#wr", "text": "新文本ABC"})
print("   set -> isError=%s %s" % (e, t[:220]))
e2, t2 = call("browser_fill_get_text", {"selector": "#wr"})
print("   get -> %s" % t2[:160])
arm("写入成功且回读一致", (not e) and ('新文本ABC' in t2), "set=%s | get=%s" % (t[:100], t2[:120]))

print("\n== 5) set_text 缺 text -> 必须拒绝(防误清空) ==")
e, t = call("browser_fill_set_text", {"selector": "#wr"})
print("   -> isError=%s %s" % (e, t[:220]))
arm("省略 text 被拒绝并提示可显式传空串", e and ('text 不能省略' in t), t[:200])

print("\n== 6) set_text 显式空串 -> 允许清空 ==")
e, t = call("browser_fill_set_text", {"selector": "#wr", "text": ""})
print("   -> isError=%s %s" % (e, t[:200]))
e2, t2 = call("browser_fill_get_text", {"selector": "#wr"})
print("   get -> %s" % t2[:140])
arm("显式空串可清空且回读为空", (not e) and ('""' in t2 or t2.strip().endswith('""')), t2[:140])

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
