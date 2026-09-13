# -*- coding: utf-8 -*-
"""browser_get_source 是否真的不稳定(同源 CEF JS 回调家族)?

背景: browser_get_source 走 框架.取源码_异步 (CEF JS 回调), 本轮我**没有**改它。
probe_native_reads.py 里它连续两次 15s 超时; 而更早一次是成功的(717 字节)。
为区分"真实不稳定"与"测量污染(协议锁被前一个用例占住)", 本脚本:
  1) 先确保链路空闲(取 health),
  2) 单发重复测 browser_get_source,
  3) 与 browser_dom_get_html(空 selector = 全文源码, 走另一条原生路径)做对照,
  4) 每次记录耗时, 给出成功率。
"""
import importlib.util
import json
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
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5

# 干净页面(唯一 URL, 避免同址导航被跳过)
v4.call("browser_navigate",
        {"url": "%s?gs=%d" % (URL, int(time.time())), "wait_for_load": True}, 60)
time.sleep(1.5)
print("页面就绪; /health = %s" % json.dumps(
    {k: v for k, v in json.loads(
        urllib.request.urlopen(BASE + "/health", timeout=10).read()).items()
     if k in ("cdp_ready", "active_requests", "async_tasks")}, ensure_ascii=False))
print()


def series(tag, tool, args):
    ok = 0
    times = []
    fails = []
    for k in range(N):
        t0 = time.time()
        e, t, _ = v4.call(tool, args, timeout=45)
        dt = time.time() - t0
        times.append(dt)
        good = (not e) and ("Example Domain" in t)
        if good:
            ok += 1
        else:
            fails.append("%.1fs err=%s %s" % (dt, e, t[:80].replace("\n", " ")))
        time.sleep(0.8)
    print("  %-34s 成功 %d/%d  耗时 %s" % (
        tag, ok, N, " ".join("%.1fs" % x for x in times)))
    for f in fails:
        print("        失败: %s" % f)
    return ok


print("== 单发重复测试 ==")
a = series("browser_get_source {sync_wait:true}", "browser_get_source",
           {"max_chars": 200000, "sync_wait": True})
b = series("browser_dom_get_html {} (全文源码)", "browser_dom_get_html", {})
c = series("browser_get_source {async_only:true}", "browser_get_source",
           {"max_chars": 200000, "async_only": True})
print()
print("结论: get_source(sync)=%d/%d  dom_get_html(全文)=%d/%d  get_source(async)=%d/%d"
      % (a, N, b, N, c, N))
if a < N and b == N:
    print("=> browser_get_source 的同步路径确实不稳定, 而 dom_get_html 全文路径稳定")
    print("   (两者都取页面源码, 后者可作为可靠替代/回退目标)")
elif a == N:
    print("=> 本次 get_source 全部成功, 说明先前超时更可能是测量污染而非稳定缺陷")
