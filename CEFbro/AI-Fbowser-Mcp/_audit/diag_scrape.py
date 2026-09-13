# -*- coding: utf-8 -*-
"""定位 browser_scrape 阶段机超时: 是我改的 extract 路径坏了, 还是驱动/参数问题?

隔离设计:
  A) extract_selector="body"  -> 走 提交异步取文本任务(本轮未改动)
  B) extract_selector="h1"    -> 走本轮改成 CDP 优先的提取路径
若 A 也超时 => 与我的改动无关(阶段机驱动/参数问题);
若仅 B 超时 => 我的提取路径改动有问题, 需修。
每次轮询都打印信封, 以便看清阶段推进到哪一步停住。
"""
import importlib.util
import json
import re
import sys
import time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("v4", "verify_round4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

URL = "https://example.com/"


def scrape_case(tag, extract, max_ms=40000, poll_s=1.0, budget=70):
    print("\n=== %s (extract_selector=%r, max_ms=%d) ===" % (tag, extract, max_ms))
    v4.call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
    time.sleep(0.8)
    args = {"url": URL, "max_ms": max_ms}
    if extract is not None:
        args["extract_selector"] = extract
    is_err, txt, resp = v4.call("browser_scrape", args, timeout=90)
    blob = json.dumps(resp or {}, ensure_ascii=False) + txt
    m = re.search(r"task_\d+_\d+_\d+", blob)
    print("  提交: err=%s task=%s msg=%s" % (is_err, m.group(0) if m else None, txt[:110]))
    if not m:
        return False
    t0 = time.time()
    n = 0
    while time.time() - t0 < budget:
        time.sleep(poll_s)
        n += 1
        e, t, _ = v4.call("mcp_result", {"request_id": m.group(0)}, timeout=40)
        phase = re.search(r"phase=(\d+)", t)
        brief = t.replace("\n", " ")[:150]
        print("  轮询%2d (%4.1fs) err=%s phase=%s | %s"
              % (n, time.time() - t0, e, phase.group(1) if phase else "-", brief))
        if ("Example Domain" in t) or ("body" in t and len(t) > 300) or "超时" in t \
                or "失败" in t or "不存在" in t:
            break
    ok = ("Example Domain" in t) and ("超时" not in t)
    print("  -> %s" % ("成功" if ok else "未成功"))
    return ok


a = scrape_case("A 对照: extract=body(未改动的路径)", "body")
b = scrape_case("B 被测: extract=h1(本轮改为 CDP 优先)", "h1")
print("\n结论: A=%s B=%s -> %s" % (
    a, b,
    "阶段机驱动/参数问题, 与我的改动无关" if (not a and not b)
    else ("仅我的提取路径有问题" if (a and not b)
          else ("两条路径均正常" if (a and b) else "需进一步分析(仅body失败)"))))
