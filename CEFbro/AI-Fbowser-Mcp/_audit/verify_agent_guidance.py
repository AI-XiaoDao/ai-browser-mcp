# -*- coding: utf-8 -*-
r"""验证第129轮(其二): 面向代理的两处"说明"必须真的到得了代理手里。

① MCP `initialize` 的 `instructions` 字段(由 MCP_Server.wsv 的 指引 变量产生):
   本轮补了"所有工具通用参数"与"大参数 1MB 墙"两段 —— 这是**代理加载 MCP 后最先读到**的文案,
   改它必须用 `initialize` 真调一次确认, 不能只看源码(上一轮就踩过"改了但运行时没生效")。
② `mcp_help` 的提示段: 本轮补了"本列表是速览 / 完整清单用 tools/list / 通用参数 / 1MB 墙"。

用法: py -3 _audit\verify_agent_guidance.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


def rpc(method, params=None, rid=7):
    b = {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode("utf-8"))


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


print('== ① initialize.instructions（代理最先读到的文案）==')
o = rpc("initialize", {"protocolVersion": "2025-06-18",
                       "capabilities": {}, "clientInfo": {"name": "verify", "version": "1"}})
res = o.get("result") or {}
ins = str(res.get("instructions") or "")
print('   instructions 长度=%d' % len(ins))
rec("initialize 成功且带 instructions", bool(ins), ins[:70])
rec("写明'所有工具通用参数'(browser_id/max_ms/async_only/sync_wait)",
    ("所有工具通用参数" in ins) and ("browser_id" in ins) and ("sync_wait" in ins), ins[:90])
rec("写明 1MB 大参数限制与替代通道", ("1MB" in ins) and ("body_file" in ins), ins[-110:])
rec("原有核心流程说明未被破坏", "browser_navigate" in ins and "mcp_help" in ins, ins[:60])

print('\n== ② mcp_help 的提示段 ==')
o2 = rpc("tools/call", {"name": "mcp_help", "arguments": {}})
t2 = "".join(i.get("text") or "" for i in (o2.get("result") or {}).get("content") or [] if i.get("type") == "text")
h = ""
try:
    h = str(json.loads(t2).get("help") or "")
except Exception:
    h = t2
rec("help 文本可解析", bool(h), h[:60])
rec("写明'本列表是速览, 完整清单用 tools/list'", "速览" in h and "tools/list" in h, h[-200:][:90])
rec("写明通用参数与 1MB 限制", ("通用参数" in h) and ("1MB" in h), h[-160:][:90])

print('\n== ③ 工具清单本身仍是权威面(323 个) ==')
tl = rpc("tools/list")
rec("tools/list 返回 323 个工具", len((tl.get("result") or {}).get("tools") or []) == 323,
    "count=%d" % len((tl.get("result") or {}).get("tools") or []))

bad = [x for x, ok in RES if not ok]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
