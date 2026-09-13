# -*- coding: utf-8 -*-
"""验收新能力 browser_show_window(显示/隐藏窗口)。

判据:
 ① 隐藏(visible=false) -> 成功且 verified=true, visible_after=false
 ② **独立回读**: browser_get_run_style 返回的原始 window_style, 其 WS_VISIBLE 位(0x100000000/16=0x10000000)
    必须被清掉 —— 不靠工具自报, 自己按位判断
 ③ 显示(visible=true) -> 成功且 verified=true, visible_after=true, 且原始 style 的该位**重新置上**
 ④ 缺 visible -> 必须拒绝(不接受缺省)
 ★ 收尾**无论成败**都把窗口显示回来: 隐藏的是用户眼前的窗口, 留在隐藏状态不可接受。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
WS_VISIBLE = 0x10000000
res = []


def call(name, args, timeout=45):
    t0 = time.time()
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def unesc(t):
    return t.replace('\\"', '"')


def raw_style():
    """独立读取原始窗口样式(不经被测工具)。"""
    e, t, _ = call("browser_get_run_style", {}, 20)
    try:
        obj = json.loads(t)
        inner = obj.get("data") if isinstance(obj.get("data"), dict) else obj
        if isinstance(inner, str):
            inner = json.loads(inner)
        return int(inner.get("window_style")), t
    except Exception as ex:
        return None, "解析失败:%s | %s" % (ex, t[:200])


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:84]))


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?showwin=1", "wait_for_load": True}, 45)
time.sleep(0.6)

try:
    print("== 基线: 独立读取原始 window_style ==")
    s0, t0 = raw_style()
    print("   window_style=%s (WS_VISIBLE 位=%s)" % (s0, (s0 & WS_VISIBLE) != 0 if s0 else "?"))
    rec("能独立读到 window_style", s0 is not None, str(s0))

    print("\n== ① 隐藏窗口 visible=false ==")
    e, t, dt = call("browser_show_window", {"visible": False}, 45)
    print("   isError=%s" % e)
    print("   %s" % t[:300])
    u = unesc(t)
    rec("调用成功", not e, t[:84])
    rec("verified=true", '"verified":true' in u.replace(" ", ""), t[:84])
    rec("visible_after=false", '"visible_after":false' in u.replace(" ", ""), t[:84])

    print("\n== ② 独立回读: WS_VISIBLE 位必须被清掉 ==")
    s1, t1 = raw_style()
    vis1 = (s1 & WS_VISIBLE) != 0 if s1 is not None else None
    print("   隐藏后 window_style=%s (WS_VISIBLE=%s)" % (s1, vis1))
    rec("独立回读确认窗口已不可见", vis1 is False, "style=%s" % s1)

    print("\n== ③ 显示回来 visible=true(收尾必须成功) ==")
    e, t, dt = call("browser_show_window", {"visible": True}, 45)
    print("   isError=%s" % e)
    print("   %s" % t[:300])
    u = unesc(t)
    rec("调用成功", not e, t[:84])
    rec("verified=true", '"verified":true' in u.replace(" ", ""), t[:84])
    s2, t2 = raw_style()
    vis2 = (s2 & WS_VISIBLE) != 0 if s2 is not None else None
    print("   显示后 window_style=%s (WS_VISIBLE=%s)" % (s2, vis2))
    rec("独立回读确认窗口已可见", vis2 is True, "style=%s" % s2)

    print("\n== ④ 缺 visible -> 必须拒绝 ==")
    e, t, dt = call("browser_show_window", {}, 30)
    print("   %s" % t[:200])
    rec("缺 visible 被拒绝且可行动", e and ("visible 不能省略" in t), t[:84])
finally:
    # 无论成败, 都把窗口显示回来
    print("\n== 收尾: 确保窗口可见 ==")
    call("browser_show_window", {"visible": True}, 45)
    s3, _ = raw_style()
    print("   window_style=%s (WS_VISIBLE=%s)" % (s3, (s3 & WS_VISIBLE) != 0 if s3 else "?"))

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
