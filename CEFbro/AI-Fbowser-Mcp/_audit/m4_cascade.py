# -*- coding: utf-8 -*-
r"""M4 — 验证假设: 慢调试工具持有协议锁, 阻塞无关请求

实验设计:
  A) 基线: 连续调用 browser_get_url 5 次, 记录延迟
  B) 并发: 后台线程发起 browser_debugger_enable(慢), 同时主线程持续调用
          browser_get_url, 记录每次延迟
  C) 判定: 若 B 阶段的 browser_get_url 延迟出现数量级跃升 -> 协议锁被长持有,
          即"单个慢工具会冻结整个 MCP 服务", 对 AI 代理是严重可用性问题
"""
import json, os, sys, threading, time, urllib.request, urllib.error
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


def call(name, args=None, rid=1, timeout=90.0):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                       "params": {"name": name, "arguments": args or {}}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        dt = time.time() - t0
        res = d.get("result") or {}
        txt = ""
        try:
            txt = res["content"][0]["text"][:90]
        except Exception:
            txt = json.dumps(d, ensure_ascii=False)[:90]
        return dt, ("ERR" if res.get("isError") else "OK"), txt
    except Exception as e:
        return time.time() - t0, "TIMEOUT" if "timed out" in str(e).lower() else "ERR", str(e)[:90]


print("=" * 100)
print("M4 协议锁阻塞实验")
print("=" * 100)
print()
print("--- A 基线: browser_get_url × 5 (无并发干扰) ---")
base = []
for i in range(5):
    dt, st, tx = call("browser_get_url", {}, 10 + i, 30)
    base.append(dt)
    print("   #%d  %6.2fs  %-8s %s" % (i + 1, dt, st, tx))
tb = sum(base) / len(base)
print("   基线均值: %.2fs" % tb)

print()
print("--- B 并发: 后台发 browser_debugger_enable, 主线程持续 get_url ---")
slow_result = {}


def slow():
    dt, st, tx = call("browser_debugger_enable", {}, 100, 120)
    slow_result["dt"], slow_result["st"], slow_result["tx"] = dt, st, tx
    print("   [后台] browser_debugger_enable 完成: %.2fs  %s  %s" % (dt, st, tx))


th = threading.Thread(target=slow, daemon=True)
th.start()
time.sleep(0.4)          # 让后台请求先进入服务端
probe = []
t_start = time.time()
i = 0
while th.is_alive() and time.time() - t_start < 60:
    i += 1
    dt, st, tx = call("browser_get_url", {}, 200 + i, 15)
    probe.append(dt)
    tag = "  <<< 被阻塞" if dt > max(2.0, tb * 5) else ""
    print("   [主线程] #%d  %6.2fs  %-8s %s%s" % (i, dt, st, tx[:60], tag))
    if i >= 25:
        break
th.join(timeout=5)

print()
print("=" * 100)
print("结论")
print("=" * 100)
if probe:
    pm = max(probe)
    pa = sum(probe) / len(probe)
    print("   基线 get_url 均值      : %.2fs" % tb)
    print("   并发期 get_url 均值    : %.2fs" % pa)
    print("   并发期 get_url 最大    : %.2fs" % pm)
    print("   慢工具耗时             : %s" % slow_result.get("dt", "n/a"))
    ratio = pa / max(0.01, tb)
    print("   均值放大倍数           : %.1fx" % ratio)
    print()
    if ratio > 3 or pm > 5:
        print("   >>> 判定: **确认协议锁/执行锁被长持有, 慢工具会阻塞无关请求**")
        print("       对 AI 代理的影响: 一次 debugger/reverse 调用可能让整个会话")
        print("       卡住数十秒, 客户端超时后重试会进一步排队恶化。")
    else:
        print("   >>> 判定: 未观察到明显阻塞 (请求可并发处理)")

json.dump({"baseline": base, "concurrent": probe, "slow": slow_result},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cascade.json"),
               "w", encoding="utf-8"), ensure_ascii=False, indent=1)
