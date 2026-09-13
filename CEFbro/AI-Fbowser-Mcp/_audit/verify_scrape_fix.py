# -*- coding: utf-8 -*-
"""验收"同名键被重复追加 -> 状态机永久卡死"是否已修（旗舰工具 browser_scrape）。

修复前实测（可复现）:
  browser_scrape {url, extract_selector:"h1"} 永远停在 phase 2, 直到 max_ms 超时报错;
  /health 的 db_async_results 每轮轮询 +2（说明 phase 2 每轮重跑、每轮重提交提取子任务）;
  直接读 mcp_cache.db 可见该行 "_phase" 出现 9 次且**第一个是 0**。

根因: 加入整数成员 -> yyjson_mut_obj_add_*（追加, 不覆盖）; 取整数 -> yyjson_obj_get（取第一个）。
修法: 新增 覆盖整数成员/覆盖文本成员（先 删除成员 再追加）, 并把 11 处状态键写回改为覆盖写。

本脚本判定三件事:
  1) scrape 是否能**在数秒内正常完成**并返回与页面真值一致的文本;
  2) 轮询期间 db_async_results 是否**不再线性增长**（不再重复提交）;
  3) 该任务的库行里 _phase 是否**只出现 1 次**（回归检测器口径）。
"""
import importlib.util
import json
import re
import sqlite3
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
WANT = "Example Domain"
DB = (r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
      r"\_int\AI-Fbowser-Mcp\debug\x64\linker\mcp_cache.db")

results = []


def rec(tag, ok, detail):
    results.append((tag, ok, detail))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:150]))


def health():
    return json.loads(urllib.request.urlopen(BASE + "/health", timeout=10).read())


def db_row(task_id):
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    r = con.execute("SELECT result_json FROM async_results WHERE task_id=?",
                    (task_id,)).fetchone()
    return r[0] if r else None


print("== 检索库行里 _phase 出现次数(修复前该行为 9 次, 第一个为 0) ==")
v4.call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
time.sleep(1.0)

h0 = health()
print("  基线 db_async_results = %s" % h0["db_async_results"])

e, t, resp = v4.call("browser_scrape",
                     {"url": URL, "extract_selector": "h1", "max_ms": 20000}, 90)
blob = json.dumps(resp or {}, ensure_ascii=False) + t
m = re.search(r"task_\d+_\d+_\d+", blob)
tid = m.group(0) if m else None
print("  提交 task = %s" % tid)

t0 = time.time()
final = t
err = e
polls = 0
while tid and time.time() - t0 < 60:
    if WANT in final or "超时" in final or ("失败" in final and "_waiting" not in final):
        break
    time.sleep(1.0)
    e2, t2, _ = v4.call("mcp_result", {"request_id": tid}, 40)
    polls += 1
    if t2:
        final, err = t2, e2

h1 = health()
elapsed = time.time() - t0
delta = h1["db_async_results"] - h0["db_async_results"]
print("  轮询 %d 次, 用时 %.1fs, db_async_results %d -> %d (+%d)"
      % (polls, elapsed, h0["db_async_results"], h1["db_async_results"], delta))
print("  最终响应: %s" % final.replace("\n", " ")[:200])
print()

# 判定 1: 必须成功并返回真值(与页面真值一致)
rec("scrape 完成且返回真值(不与预言机比对则无意义)",
    (not err) and (WANT in final) and ("超时" not in final),
    "err=%s 用时%.1fs %s" % (err, elapsed, final.replace("\n", " ")[:110]))

# 判定 2: 不再重复提交(修复前每轮 +2)
rec("轮询期间未重复提交子任务(db 增量应 <= 3)",
    delta <= 3, "增量 = %d (修复前每轮 +2)" % delta)

# 判定 3: 库行内状态键**不得重复**(回归口径)
# 注意: 任务完成后该行会被**最终结果**覆盖(如 {"success":true,"text":"Example Domain"}),
# 此时根本不出现 _phase —— 所以正确断言是 "<= 1 次" 而不是 "== 1 次"。
# 修复前该行是 {"_phase":0, ..., "_phase":3, ...} 共 9 次。
row = db_row(tid) if tid else None
if row is None:
    rec("库行可读", False, "取不到 task 行(可能已被保留期清理)")
else:
    n_phase = len(re.findall(r'"_phase"\s*:', row))
    n_extract = len(re.findall(r'"_extract_task_id"\s*:', row))
    rec("库行状态键无重复(_phase/_extract_task_id 各 <= 1)",
        n_phase <= 1 and n_extract <= 1,
        "_phase=%d 次, _extract_task_id=%d 次 | %s" % (n_phase, n_extract, row[:150]))

# 判定 4: 与预言机对齐(取页面 h1 真值比对; 预言机带重试, 避免被前序负载污染)
oracle_t = ""
for attempt in range(2):
    e3, t3, _ = v4.call("browser_execute_js",
                        {"code": "document.querySelector('h1').textContent"}, 30)
    v = (t3 or "").strip().strip('"')
    if (not e3) and v and not v.startswith("<") and "超时" not in v:
        oracle_t = v
        break
    time.sleep(2)
rec("返回文本与预言机一致", bool(oracle_t) and oracle_t in final,
    "预言机=%r 响应=%s" % (oracle_t[:40], final.replace("\n", " ")[:90]))

print("\n== 汇总 ==")
bad = [x for x in results if not x[1]]
print("  通过 %d / %d" % (len(results) - len(bad), len(results)))
for tag, _, d in bad:
    print("  未通过: %s -> %s" % (tag, str(d)[:140]))
sys.exit(1 if bad else 0)
