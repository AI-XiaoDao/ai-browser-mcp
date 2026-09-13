# -*- coding: utf-8 -*-
"""判定 browser_scrape 卡在 phase=2 的根因。

两个互斥假设:
  H1) phase 2 每轮都在重新执行(即 `_phase=3` 的写回没生效) -> 每轮都会新建一个提取子任务,
      因此 /health 的 db_async_results 会随轮询次数**线性增长**。
  H2) phase 2 只执行一次, 但 `_phase` 的**读取**每轮都拿到旧值(2) -> db_async_results 只涨 1。

用 /health 的 db_async_results 计数做判据, 这是服务器自己报的持久层事实, 不依赖我的推断。
"""
import importlib.util
import json
import re
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("v4", "verify_round4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

BASE = "http://127.0.0.1:9222"
URL = "https://example.com/"


def health():
    return json.loads(urllib.request.urlopen(BASE + "/health", timeout=10).read())


v4.call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
time.sleep(1.0)

h0 = health()
print("基线: db_async_results=%s async_tasks=%s" % (h0["db_async_results"], h0["async_tasks"]))

is_err, txt, resp = v4.call("browser_scrape",
                            {"url": URL, "extract_selector": "h1", "max_ms": 60000}, 90)
blob = json.dumps(resp or {}, ensure_ascii=False) + txt
m = re.search(r"task_\d+_\d+_\d+", blob)
tid = m.group(0)
print("提交 task=%s" % tid)

for k in range(1, 6):
    time.sleep(1.0)
    e, t, _ = v4.call("mcp_result", {"request_id": tid}, 40)
    h = health()
    ph = re.search(r"phase=(\d+)", t)
    print("  第%d轮: phase=%s db_async_results=%s (较基线 +%d) | %s"
          % (k, ph.group(1) if ph else "-", h["db_async_results"],
             h["db_async_results"] - h0["db_async_results"],
             t.replace("\n", " ")[:90]))

h1 = health()
delta = h1["db_async_results"] - h0["db_async_results"]
print("\n5 轮轮询后 db_async_results 增量 = %d" % delta)
if delta >= 5:
    print("=> H1 成立: phase 2 每轮重新执行, `_phase=3` 的写回没生效(每轮新建提取子任务)")
elif delta <= 2:
    print("=> H2 成立: phase 2 只执行了一次; 卡住的原因是 `_phase` 读取每轮拿到旧值")
else:
    print("=> 介于两者之间, 需进一步区分")

# 补充证据: 直接连查 3 次同一 id, 看是否 phase 会变
print("\n补充: 连续 3 次查询同一 id 的原始响应")
for k in range(3):
    e, t, _ = v4.call("mcp_result", {"request_id": tid}, 40)
    print("   %d) %s" % (k + 1, t.replace("\n", " ")[:160]))
    time.sleep(0.6)
