# -*- coding: utf-8 -*-
"""对首轮 TIMEOUT 结果做复检: 新进程 + 更长超时 + 先恢复 CDP。

首轮探测存在自污染: browser_vip_enable_inspector 的 enable 非必填, 探测未传参 ->
走 else 分支关闭了 CDP 监管者 -> 之后所有 CDP 类工具的 TIMEOUT 不可信。
本脚本: 先显式 enable 恢复 CDP, 再用 30s 超时重测首轮判为 TIMEOUT 的工具。
"""
import io
import json
import os
import re
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:9222"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mass_probe import build_args, classify  # noqa: E402
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

TIMEOUT_S = 30


def post(payload, timeout=TIMEOUT_S):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    prev = json.load(io.open(os.path.join(HERE, "_probe_result.json"), encoding="utf-8"))
    targets = [r for r in prev if r["verdict"] in ("TIMEOUT", "ERR_WEAK")]
    print("复检对象: %d 个 (首轮 TIMEOUT %d + ERR_WEAK %d)"
          % (len(targets),
             sum(1 for r in prev if r["verdict"] == "TIMEOUT"),
             sum(1 for r in prev if r["verdict"] == "ERR_WEAK")))

    h0 = get("/health")
    print("复检前 cdp_ready=%s browsers=%s" % (h0.get("cdp_ready"), h0.get("browsers")))

    # 1) 显式恢复 CDP 监管者 (首轮被探测行为本身关掉了)
    try:
        r = post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": "browser_vip_enable_inspector",
                             "arguments": {"enable": True}}})
        txt = json.dumps(r, ensure_ascii=False)
        print("恢复 CDP: %s" % txt[:160])
    except Exception as ex:
        print("恢复 CDP 失败: %s" % ex)

    # 2) 建索引以便复用首轮 schema
    tl = get("/tools/list", timeout=20)
    byname = {t["name"]: t for t in tl.get("tools", [])}

    out = []
    for r in targets:
        name = r["name"]
        t = byname.get(name, {})
        args, notes = build_args(t.get("inputSchema", {}), t.get("description", ""))
        if name == "browser_vip_enable_inspector":
            args = {"enable": True}
            notes = ["显式 enable=true"]
        st = time.time()
        resp, err = None, None
        try:
            resp = post({"jsonrpc": "2.0", "id": 20000, "method": "tools/call",
                         "params": {"name": name, "arguments": args}}, TIMEOUT_S)
        except Exception as ex:
            err = str(ex)
        el = time.time() - st
        verdict, detail = classify(name, args, resp, el, err)
        out.append({"name": name, "first_verdict": r["verdict"], "verdict": verdict,
                    "args": args, "elapsed": round(el, 2), "detail": detail})
        print("  %-42s %-12s -> %-12s %5.2fs %s"
              % (name, r["verdict"], verdict, el, detail[:60]))

    io.open(os.path.join(HERE, "_reprobe_result.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))

    print()
    print("=" * 96)
    tally = {}
    for o in out:
        k = "%s -> %s" % (o["first_verdict"], o["verdict"])
        tally[k] = tally.get(k, 0) + 1
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("  %-30s %d" % (k, tally[k]))


if __name__ == "__main__":
    main()
