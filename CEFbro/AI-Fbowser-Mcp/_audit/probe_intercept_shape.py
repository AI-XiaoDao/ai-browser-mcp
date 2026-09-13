# -*- coding: utf-8 -*-
"""Network.setRequestInterception 的 patterns **元素形状** 对照探针。

已知: {"patterns":[{"urlPattern":"*","requestStage":"Request"}]} 被接受。
待定:
  S1 {"patterns":["*"]}                        <- 现有代码构造的形状(裸字符串)
  S2 {"patterns":[{"urlPattern":"*"}]}         <- 对象但不带 requestStage
只有实测能定案, 不猜。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def c(n, a, to=45):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return "".join(i.get("text") or "" for i in (rr.get("content") or [])
                   if i.get("type") == "text").replace('\\"', '"')[:260]


def cdp(method, params):
    return c("browser_cdp_call", {"method": method, "params": params})


c("browser_navigate", {"url": "https://example.com/?shape=1", "wait_for_load": True})
c("browser_cdp_call", {"method": "Network.enable", "params": {}})

arm = [("S1 裸字符串(现有代码)", {"patterns": ["*"]}),
       ("S2 对象无 requestStage", {"patterns": [{"urlPattern": "*"}]}),
       ("S3 对象带 requestStage ", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]}),
       ("S4 复位 []            ", {"patterns": []})]
for label, p in arm:
    t = cdp("Network.setRequestInterception", p)
    verdict = "接受" if t.strip().startswith("{}") or '"error"' not in t else "拒绝"
    print("   [%s] %s -> %s" % (verdict, label, t))

# 收尾: 再确认一次已复位, 且页面网络未被卡住
print("   收尾回读 evaluate: %s"
      % c("browser_evaluate", {"code": "'alive:'+document.title"}, 20)[:120])
