# -*- coding: utf-8 -*-
"""验收本轮对 browser_get_text 的两处修复。

判据:
 ① 主浏览器正常元素仍然读得到(回归);
 ② **元素存在但文本本来就是空**时, 应如实返回空串 —— 修复前它会退到原生路径并给出字面 null;
 ③ 元素不存在时仍是明确的失败(不因改动而变成"成功返回空串");
 ④ `browser_id` 指向第二个浏览器时, 能读到它自己的内容; 若仍读不到, 必须给出**可行动的失败**
    而不是字面 null(不静默假成功)。
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
res = []


def call(name, args, timeout=45):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:95]))


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

call("browser_navigate", {"url": "https://example.com/?gt2=main", "wait_for_load": True}, 45)
time.sleep(0.5)
# 造一个"存在但文本为空"的元素
call("browser_execute_js", {"code":
     "var d=document.createElement('div');d.id='emptyProbe';"
     "document.body.appendChild(d);'ok'"})

print("== (1) 主浏览器正常元素(回归) ==")
e, t, dt = call("browser_get_text", {"selector": "h1"})
rec("读到 Example Domain", (not e) and ("Example Domain" in t), "%.2fs | %s" % (dt, t[:70]))

print("\n== (2) 元素存在但文本为空 -> 应如实返回空串(修复前为 null) ==")
e, t, dt = call("browser_get_text", {"selector": "#emptyProbe"})
rec("成功且内容为空串", (not e) and ("\"message\":\"\"" in t.replace(" ", "")), t[:90])
rec("不再是字面 null", "null" not in t.lower().replace("null:", ""), t[:90])

print("\n== (3) 元素不存在 -> 仍应是明确失败 ==")
e, t, dt = call("browser_get_text", {"selector": "#totallyMissing"})
rec("明确失败且给出建议", e and ("不存在" in t), t[:90])

print("\n== (4) 第二个浏览器(browser_id=2) ==")
call("browser_create", {"url": "https://example.com/?gt2=second", "background": True}, 60)
time.sleep(1.0)
e, t, dt = call("browser_get_text", {"selector": "h1", "browser_id": 2})
ok_val = (not e) and ("Example Domain" in t)
rec("读到第二个浏览器自己的 h1", ok_val, "%.2fs | %s" % (dt, t[:90]))
if not ok_val:
    rec("未读到但**是明确失败**而非字面 null(不静默假成功)",
        e and ("null" != t.strip()), t[:90])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
sys.exit(1 if bad else 0)
