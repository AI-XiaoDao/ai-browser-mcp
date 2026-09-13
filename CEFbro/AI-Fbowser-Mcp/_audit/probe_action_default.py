# -*- coding: utf-8 -*-
"""定向取证: "省略 action/关键参数 -> 静默变成另一个动作, 却返回 success" 这一类。

审计列出多处以 `如果 (动作 == "" || 动作 == "xxx")` 或 `如果 (action == "") { action = "list" }`
的形式把"没传参数"降级成另一种动作。本脚本只测**能安全观察**的那些, 目标 <20 秒。

判定原则: 缺参时应当报错(或至少不能静默改变全局状态/执行动作); 显式传参必须成功。
"""
import json
import re
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
res = []


def call(name, args, timeout=30):
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


def val(t):
    s = (t or "").strip()
    try:
        j = json.loads(s)
        if isinstance(j, dict) and "message" in j:
            return str(j["message"])
    except Exception:
        pass
    return s.strip('"')


def show(tag, tool, args):
    e, t = call(tool, args)
    brief = t.replace("\n", " ")[:120]
    is_err = "报错(好)" if e else "成功"
    print("  %-34s %-8s %s" % (tag, is_err, brief))
    res.append((tag, e, brief))
    return e, t


print("== 准备 ==")
call("browser_navigate", {"url": "https://example.com/?ad=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.6)

print("\n== 1) browser_kernel_* 省略 action(修复后应报错) ==")
bad = 0
for tool in ("browser_kernel_cert", "browser_kernel_download", "browser_kernel_cdp_monitor",
             "browser_kernel_reactor", "browser_kernel_watch"):
    e, t = show("%s {}" % tool, tool, {})
    if not e:
        bad += 1
print("  -> 缺参未报错的数量 = %d (期望 0)" % bad)

print("\n== 2) scroll_by: 显式 0 必须等于不滚动 ==")
e1, t1 = show("scroll_by {} (文档默认800)", "browser_scroll_by", {})
e2, t2 = show("scroll_by {x:0,y:0} (显式零)", "browser_scroll_by", {"x": 0, "y": 0})


def scrolled_y(t):
    m = re.search(r'scrolled_by_y\\?"\s*:\s*(-?\d+)', t.replace('\\"', '"'))
    return int(m.group(1)) if m else None


d1, d2 = scrolled_y(t1), scrolled_y(t2)
print("  -> 未传时 scrolled_by_y=%s (期望 800, 文档声明的默认)" % d1)
print("  -> 显式0时 scrolled_by_y=%s (期望 0 —— 修复前也是 800, '不滚动'无法表达)" % d2)

print("\n== 3) 未知 preset 必须报错, 不能谎报'已部署/持久生效' ==")
e3, t3 = show("antidetect_presets {preset:乱填}", "browser_antidetect_presets",
              {"preset": "zzz-nonexistent"})

print("\n== 判定 ==")
judge = [
    ("kernel_* 缺 action 全部报错", bad == 0),
    ("scroll_by 未传 -> 800(文档默认)", d1 == 800),
    ("scroll_by 显式0 -> 0(不滚动可表达)", d2 == 0),
    ("未知 preset 报错", bool(e3)),
]
for name, ok in judge:
    print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
sys.exit(0 if all(o for _, o in judge) else 1)
