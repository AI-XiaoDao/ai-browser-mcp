# -*- coding: utf-8 -*-
r"""M15 — 企业级 MCP 就绪度评估

对照 MCP 规范(2025-06-18 / Streamable HTTP 传输)与生产实践, 实测服务端当前行为。
每项给出 [有/无/部分] 与证据, 用于定出补齐清单。
"""
import json, urllib.request, urllib.error, time, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
OUT = os.path.dirname(os.path.abspath(__file__))
rows = []


def http(method, path, body=None, headers=None, timeout=10):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, dict(r.headers), raw
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()


def rpc(method, params=None, rid=1, extra=None):
    b = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        b["params"] = params
    if extra:
        b.update(extra)
    return http("POST", "/mcp", b)


def add(cat, item, status, ev=""):
    rows.append({"cat": cat, "item": item, "status": status, "ev": ev})


# ---------- 1. 协议基础 ----------
st, hd, raw = rpc("initialize", {"protocolVersion": "2025-06-18",
                                 "capabilities": {},
                                 "clientInfo": {"name": "probe", "version": "1.0"}},
                  1, {"_meta": {"progressToken": "tok-1"}})
try:
    d = json.loads(raw.decode("utf-8"))
except Exception:
    d = {}
res = d.get("result") or {}
add("协议", "initialize 返回 protocolVersion", "有" if res.get("protocolVersion") else "无",
    str(res.get("protocolVersion")))
add("协议", "initialize 返回 capabilities", "有" if res.get("capabilities") else "无",
    json.dumps(res.get("capabilities") or {}, ensure_ascii=False)[:120])
add("协议", "initialize 返回 serverInfo", "有" if res.get("serverInfo") else "无",
    json.dumps(res.get("serverInfo") or {}, ensure_ascii=False)[:80])
add("传输", "返回 Mcp-Session-Id 会话头", "有" if any(k.lower() == "mcp-session-id" for k in hd) else "无",
    ",".join(k for k in hd if "session" in k.lower()))

# ---------- 2. 能力声明完整度 ----------
caps = res.get("capabilities") or {}
for k in ["tools", "resources", "prompts", "logging", "completions"]:
    add("协议", "capabilities.%s 声明" % k, "有" if k in caps else "无",
        json.dumps(caps.get(k), ensure_ascii=False) if k in caps else "")

# ---------- 3. 方法覆盖 ----------
for m, params in [("tools/list", {}), ("resources/list", {}), ("prompts/list", {}),
                  ("resources/templates/list", {}), ("completion/complete",
                   {"ref": {"type": "ref/prompt", "name": "x"}, "argument": {"name": "a", "value": "b"}}),
                  ("logging/setLevel", {"level": "info"}), ("ping", {})]:
    st, hd, raw = rpc(m, params, 2)
    try:
        dd = json.loads(raw.decode("utf-8"))
    except Exception:
        dd = {}
    if "result" in dd:
        add("协议", "方法 %s" % m, "有", "")
    elif "error" in dd:
        code = dd["error"].get("code")
        add("协议", "方法 %s" % m, "无" if code == -32601 else "错误", "code=%s" % code)
    else:
        add("协议", "方法 %s" % m, "无响应", raw[:80].decode("utf-8", "replace"))

# ---------- 4. 通知 ----------
for m in ["notifications/initialized", "notifications/cancelled",
          "notifications/progress", "notifications/tools/list_changed"]:
    st, hd, raw = rpc(m, {}, None)
    body = raw.decode("utf-8", "replace")[:60]
    add("协议", "接受通知 %s" % m, "有" if st == 200 else "HTTP %d" % st, body)

# ---------- 5. Streamable HTTP 传输 (2025-03-26+) ----------
st, hd, raw = http("POST", "/mcp",
                   {"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {}},
                   {"Accept": "application/json, text/event-stream"})
ct = hd.get("Content-Type", "")
add("传输", "POST /mcp 支持 Accept: text/event-stream(SSE 响应)", "有" if "event-stream" in ct else "无",
    "Content-Type=%s" % ct)
st, hd, raw = http("GET", "/mcp", None, {"Accept": "text/event-stream"}, timeout=4)
add("传输", "GET /mcp 可建立服务端 SSE 流", "有" if st == 200 else "无", "HTTP %d" % st)
st, hd, raw = http("DELETE", "/mcp", None, {}, timeout=4)
add("传输", "DELETE /mcp 会话终止", "有" if st in (200, 202, 204) else "无", "HTTP %d" % st)

# ---------- 6. JSON-RPC 边界 ----------
st, hd, raw = http("POST", "/mcp", [{"jsonrpc": "2.0", "id": 1, "method": "ping"},
                                    {"jsonrpc": "2.0", "id": 2, "method": "ping"}])
try:
    bd = json.loads(raw.decode("utf-8"))
    isarr = isinstance(bd, list)
except Exception:
    isarr = False
add("协议", "JSON-RPC 批量请求(数组)", "有" if isarr else "无", raw[:70].decode("utf-8", "replace"))

st, hd, raw = rpc("tools/call", {"name": "不存在的工具", "arguments": {}}, 3)
try:
    dd = json.loads(raw.decode("utf-8"))
    code = (dd.get("error") or {}).get("code")
except Exception:
    code = None
add("协议", "未知工具返回 -32601", "有" if code == -32601 else "错误", "code=%s" % code)

st, hd, raw = http("POST", "/mcp", {"jsonrpc": "2.0", "id": 0, "method": "ping"})
try:
    dd = json.loads(raw.decode("utf-8"))
    ok0 = dd.get("id") == 0 and "result" in dd
except Exception:
    ok0 = False
add("协议", "id:0 必须响应且回显数值 0", "有" if ok0 else "无", raw[:60].decode("utf-8", "replace"))

# ---------- 7. 可观测性 ----------
for p in ["/health", "/metrics", "/api", "/json/version", "/tools/brief"]:
    st, hd, raw = http("GET", p, None, {}, timeout=4)
    add("可观测", "端点 GET %s" % p, "有" if st == 200 else "无", "HTTP %d, %d B" % (st, len(raw)))

st, hd, raw = http("GET", "/health", None, {}, timeout=4)
try:
    h = json.loads(raw.decode("utf-8"))
    keys = set(h.keys())
except Exception:
    keys = set()
for k, why in [("uptime_ms", "运行时长"), ("tool_count", "工具数"), ("browsers", "浏览器数"),
               ("latency_ms", "请求延迟统计"), ("requests_total", "累计请求数"),
               ("errors_total", "累计错误数"), ("cdp_ready", "CDP 就绪")]:
    add("可观测", "/health 含 %s(%s)" % (k, why), "有" if k in keys else "无", "")

# ---------- 输出 ----------
print("=" * 104)
print("M15 企业级 MCP 就绪度评估")
print("=" * 104)
print()
cur = None
n_yes = n_all = 0
for r in rows:
    if r["cat"] != cur:
        cur = r["cat"]
        print()
        print("## %s" % cur)
        print("-" * 104)
    n_all += 1
    if r["status"] == "有":
        n_yes += 1
    mark = {"有": "✓", "无": "✗", "部分": "~"}.get(r["status"], "!")
    print("  %s %-52s %-8s %s" % (mark, r["item"], r["status"], r["ev"][:52]))
print()
print("=" * 104)
print("就绪度: %d / %d (%.0f%%)" % (n_yes, n_all, 100.0 * n_yes / max(1, n_all)))
print("=" * 104)
json.dump(rows, open(os.path.join(OUT, "enterprise.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
