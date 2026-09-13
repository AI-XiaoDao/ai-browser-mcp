# -*- coding: utf-8 -*-
"""累积待验证清单一次性回收 (针对 20:37:32 构建)。

严格断言: 成功 = 有 result 且无 error 且无 isError。
覆盖:
  (B) 字符串优先 enable 判据 —— 四种入参
  (A-app)/(C) 渲染侧 IPC 通道 —— 导航后 browser_kernel_ipc_queue 应出现 app_render_*
  基线: tool_count=280
"""
import json
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


def call(tool, args, timeout=30):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = json.loads(r.read().decode("utf-8"))
    if "error" in raw:
        return False, "RPC_ERR:" + json.dumps(raw["error"], ensure_ascii=False)[:140]
    res = raw.get("result", {})
    txt = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    return (not res.get("isError")), txt[:260]


def health():
    with urllib.request.urlopen(BASE + "/health", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


print("=" * 92)
print("0. 基线")
print("=" * 92)
h = health()
print("   tool_count=%s  cdp_ready=%s" % (h.get("tool_count"), h.get("cdp_ready")))

print()
print("=" * 92)
print("(B) 字符串优先 enable 判据 —— 四种入参")
print("=" * 92)
CASES = [
    ("缺省 {}", {}, "期望: 拒绝(不再关停 CDP)"),
    ("enable: true (布尔)", {"enable": True}, "期望: 启用"),
    ('enable: "true" (字符串)', {"enable": "true"}, "期望: 启用"),
    ('enable: "false" (字符串)', {"enable": "false"}, "期望: 关闭(显式)"),
]
for label, args, expect in CASES:
    ok, txt = call("browser_vip_enable_inspector", args)
    print("   %-26s ok=%-5s %s" % (label, ok, expect))
    print("         -> %s" % txt[:190])
    time.sleep(0.4)

# 恢复启用, 以便后续测试
call("browser_vip_enable_inspector", {"enable": "true"})
print("   (已恢复启用) cdp_ready=%s" % health().get("cdp_ready"))

print()
print("=" * 92)
print("(A-app)/(C) 渲染侧 IPC 通道 —— 核心验证点")
print("=" * 92)
ok, txt = call("browser_collect", {"action": "event_render_enable"})
print("   开渲染细节族: ok=%s %s" % (ok, txt[:120]))
ok, txt = call("browser_collect", {"action": "event_startup_enable"})
print("   开启动流程族: ok=%s %s" % (ok, txt[:120]))
ok, txt = call("browser_navigate", {"url": "https://example.com", "sync_wait": True})
print("   导航: ok=%s %s" % (ok, txt[:100]))
time.sleep(4)
ok, txt = call("browser_kernel_ipc_queue", {"action": "queue"})
print("   读 IPC 队列: ok=%s" % ok)
print("         -> %s" % txt[:600])
hit = [k for k in ("app_render_load_end", "app_render_load_start", "app_render_loading_state",
                   "app_render_v8_context_created", "app_startup") if k in txt]
print()
if hit:
    print("   ★ 队列中出现渲染侧应用事件: %s" % ", ".join(hit))
    print("   => (C) 方案① 生效: 渲染进程事件成功经页面 IPC 队列送达")
else:
    print("   ✗ 队列中未出现 app_render_* —— 需进一步排查")
