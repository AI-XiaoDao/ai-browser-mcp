# -*- coding: utf-8 -*-
"""L2 语义正确性交叉验证 —— 用独立预言机核对工具返回值是否**真的正确**。

预言机:
  · browser_execute_js 在页面里取真值(最权威)
  · Python 标准库(base64/urllib)对纯函数做等值/往返校验

纪律:
  · 先判定响应成功/失败, 再做内容断言(严禁"字符串出现过就算通过")
  · 期望值来自页面真值或标准库, 不凭记忆
  · 每个用例输出 实际值 / 期望值 / 判定

注意: 多数工具默认异步(返回 _async + task_id), 必须经 mcp_result 轮询取回真实结果,
否则会拿 task_id 去和真值比对而产生假通过/假失败。
"""
import base64
import json
import re
import time
import urllib.parse
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


def raw_call(tool, args, timeout=30):
    b = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": tool, "arguments": args}},
                   ensure_ascii=False).encode("utf-8")
    rq = urllib.request.Request(BASE + "/mcp", data=b,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        raw = json.loads(r.read().decode("utf-8"))
    if "error" in raw:
        return False, "RPC_ERR:" + json.dumps(raw["error"], ensure_ascii=False)[:150]
    res = raw.get("result", {})
    txt = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    return (not res.get("isError")), txt


def call(tool, args, timeout=30, poll=True):
    """返回 (ok, text)。若工具走异步, 自动经 mcp_result 轮询取回真实结果。"""
    ok, txt = raw_call(tool, args, timeout)
    if not ok or not poll:
        return ok, txt
    if '"_async":true' not in txt and '"_async": true' not in txt:
        return ok, txt
    m = re.search(r'task_id\\?"\s*:\s*\\?"([^"\\]+)', txt)
    if not m:
        return ok, txt
    tid = m.group(1)
    for _ in range(25):
        time.sleep(0.4)
        ok2, txt2 = raw_call("mcp_result", {"request_id": tid, "consume": True})
        if ok2 and "未找到" not in txt2 and "仍在执行" not in txt2:
            return ok2, txt2
    return False, "POLL_TIMEOUT:" + txt[:120]


def js(expr, timeout=25):
    """预言机: 在页面里求值(强制同步)"""
    ok, txt = call("browser_execute_js", {"code": expr, "sync_wait": True, "max_ms": 8000},
                   timeout, poll=True)
    if not ok:
        return None, txt
    # 结果可能被包在 {"ok":..,"result":..} 里
    m = re.search(r'\\?"result\\?"\s*:\s*\\?"?(.*?)\\?"?\s*[,}]', txt)
    if m:
        return m.group(1), txt
    return txt.strip(), txt


def show(label, actual, expected, ok=None):
    verdict = "通过" if (ok if ok is not None else str(actual) == str(expected)) else "★不一致"
    print("   %-34s 实际=%-42s 期望=%-42s %s"
          % (label, str(actual)[:42], str(expected)[:42], verdict))
    return verdict == "通过"


print("=" * 100)
print("准备: 导航到受控页面")
print("=" * 100)
ok, txt = call("browser_navigate", {"url": "https://example.com", "sync_wait": True})
print("   navigate: ok=%s %s" % (ok, txt[:100]))
time.sleep(1)

PASS, FAIL = [], []

print()
print("=" * 100)
print("A. 导航类 —— 与页面真值比对")
print("=" * 100)
truth_url, _ = js("location.href")
truth_title, _ = js("document.title")
print("   页面真值(预言机): url=%s title=%s" % (truth_url, truth_title))

ok, got = call("browser_get_url", {})
(PASS if (ok and truth_url and truth_url in got) else FAIL).append("browser_get_url")
show("browser_get_url", got[:60], truth_url, ok and bool(truth_url) and truth_url in got)

ok, got = call("browser_get_title", {})
(PASS if (ok and truth_title and truth_title in got) else FAIL).append("browser_get_title")
show("browser_get_title", got[:60], truth_title, ok and bool(truth_title) and truth_title in got)

print()
print("=" * 100)
print("B. DOM/文本类 —— 与 JS 取值比对")
print("=" * 100)
truth_h1, _ = js("document.querySelector('h1')?document.querySelector('h1').textContent:''")
print("   页面真值: h1.textContent = %r" % truth_h1)

ok, got = call("browser_get_text", {"selector": "h1"})
same = bool(truth_h1) and truth_h1.strip()[:20] in got
(PASS if (ok and same) else FAIL).append("browser_get_text(selector=h1)")
show("browser_get_text selector=h1", got[:60], truth_h1, ok and same)

truth_links, _ = js("document.querySelectorAll('a').length")
ok, got = call("browser_dom_query", {"selector": "a"})
has = bool(truth_links) and str(truth_links) in got
(PASS if (ok and has) else FAIL).append("browser_dom_query(a)")
show("browser_dom_query a(count=%s)" % truth_links, got[:60], "含 %s" % truth_links, ok and has)

print()
print("=" * 100)
print("C. 纯函数类 —— 与 Python 标准库做等值/往返校验")
print("=" * 100)
payload = "hello-mcp-测试"
exp_b64 = base64.b64encode(payload.encode("utf-8")).decode()
ok, got = call("browser_base64_encode", {"value": payload})
(PASS if (ok and exp_b64 in got) else FAIL).append("browser_base64_encode")
show("base64_encode", got[:60], exp_b64, ok and exp_b64 in got)

ok, got = call("browser_base64_decode", {"value": exp_b64})
(PASS if (ok and payload in got) else FAIL).append("browser_base64_decode")
show("base64_decode(往返)", got[:60], payload, ok and payload in got)

exp_uri = urllib.parse.quote(payload, safe="")
ok, got = call("browser_uri_encode", {"value": payload})
(PASS if ok and exp_uri in got else FAIL).append("browser_uri_encode")
show("uri_encode", got[:60], exp_uri, ok and exp_uri in got)

ok, got = call("browser_uri_decode", {"value": exp_uri})
(PASS if ok and payload in got else FAIL).append("browser_uri_decode")
show("uri_decode(往返)", got[:60], payload, ok and payload in got)

print()
print("=" * 100)
print("D. 截图 —— 校验返回的 base64 是否为**合法 PNG**")
print("=" * 100)
ok, got = call("browser_screenshot", {})
m = re.search(r'base64,([A-Za-z0-9+/=]{100,})', got)
valid_png = False
detail = "未拿到 base64"
if m:
    try:
        blob = base64.b64decode(m.group(1) + "===")
        magic = blob[:8] == b"\x89PNG\r\n\x1a\n"
        # 再校验 PNG 结束块 IEND
        has_iend = b"IEND" in blob[-16:]
        valid_png = magic and has_iend
        detail = "magic=%s IEND=%s 大小=%dB" % (magic, has_iend, len(blob))
    except Exception as ex:
        detail = "base64 解码失败: %s" % ex
(PASS if (ok and valid_png) else FAIL).append("browser_screenshot")
show("screenshot 合法PNG", detail, "PNG magic + IEND", ok and valid_png)

print()
print("=" * 100)
print("E. Cookie 往返 —— 写入后用**另一个工具**独立读回 (L4 交叉)")
print("=" * 100)
ok1, t1 = call("browser_set_cookie", {"name": "mcp_lt2", "value": "v-2026", "url": "https://example.com/"})
print("   set_cookie: ok=%s %s" % (ok1, t1[:90]))
time.sleep(0.5)
ok2, t2 = call("browser_get_cookies", {})
found = "mcp_lt2" in t2 and "v-2026" in t2
(PASS if (ok1 and ok2 and found) else FAIL).append("cookie 往返")
show("get_cookies 读回写入值", ("含 mcp_lt2=v-2026" if found else t2[:50]), "含 mcp_lt2=v-2026", found)

print()
print("=" * 100)
print("L2 汇总:  通过 %d   不一致 %d" % (len(PASS), len(FAIL)))
print("=" * 100)
for x in PASS:
    print("   ✅ %s" % x)
for x in FAIL:
    print("   ★ %s" % x)
