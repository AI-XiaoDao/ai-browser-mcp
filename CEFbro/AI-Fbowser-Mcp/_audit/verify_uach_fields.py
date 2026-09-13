# -*- coding: utf-8 -*-
"""验收 UA-CH 四字段: 设置后, 页面的 navigator.userAgentData 必须真的变。

这是**回读验证**(不靠工具自报): 直接问页面自己的 navigator.userAgentData。
判据:
 ① 基线读数(设置前)记录下来
 ② 设置 brands/platform_version/full_version/full_version_list + ua -> 工具应回"需刷新"
 ③ 刷新后回读: brands / platformVersion / fullVersion 应变成我们设的值
 ④ 若没变: 必须区分"本机没授权 VIP(全部静默 no-op)"与"工具没生效" ——
    这属于审计 §5 明确列为**未核实**的事项, 本脚本会如实打印现象, 不硬下结论。
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

# 注意: platformVersion / fullVersion / fullVersionList 是**高熵**字段,
# 低熵对象 navigator.userAgentData 上它们是 undefined(JSON.stringify 会直接丢掉键),
# 必须用 getHighEntropyValues() 取。第一版探针就踩了这个坑(误报 FAIL)。
KICK_JS = ("(function(){if(!navigator.userAgentData){window.__mcp_uach='null';return 'no-uach';}"
           "navigator.userAgentData.getHighEntropyValues("
           "['platformVersion','fullVersion','fullVersionList','architecture','bitness','model'])"
           ".then(function(v){window.__mcp_uach=JSON.stringify({lo:{brands:navigator."
           "userAgentData.brands,mobile:navigator.userAgentData.mobile,platform:navigator."
           "userAgentData.platform},hi:v})},function(e){window.__mcp_uach='ERR:'+e});"
           "return 'submitted'})()")
READ_JS = "String(window.__mcp_uach)"

WANT_BRANDS = "Chromium:120,Google Chrome:120"
WANT_FVL = "Chromium:120.0.6099.109,Google Chrome:120.0.6099.109"
WANT_PV = "15.0.0"
WANT_FV = "120.0.6099.109"


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or "" for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def unesc(t):
    return t.replace('\\"', '"')


def read_uach(tag):
    e, t = c("browser_evaluate", {"code": KICK_JS})
    time.sleep(0.9)
    e2, t2 = c("browser_evaluate", {"code": READ_JS})
    print("   [%s] kick=%s isError=%s %s" % (tag, unesc(t)[:60], e2, unesc(t2)[:600]))
    return unesc(t2)


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

c("browser_navigate", {"url": "https://example.com/?uach=1", "wait_for_load": True})
time.sleep(0.8)
print("== ① 设置前的基线 navigator.userAgentData ==")
before = read_uach("before")

print("\n== ② 调用 browser_fingerprint_ua 设置 UA-CH 四字段 ==")
args = {"ua": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        "platform": "Windows", "platform_version": WANT_PV,
        "full_version": WANT_FV, "brands": WANT_BRANDS,
        "full_version_list": WANT_FVL, "mobile": False}
e, t = c("browser_fingerprint_ua", args)
print("   isError=%s -> %s" % (e, unesc(t)[:260]))

print("\n== ③ 刷新后回读(指纹变更需刷新才生效) ==")
c("browser_reload", {}, 60)
time.sleep(1.5)
after = read_uach("after")

print("\n== 判定 ==")
checks = [("brands 含 Chromium:120", "Chromium" in after and "120" in after),
          ("platformVersion == %s" % WANT_PV, WANT_PV in after),
          ("fullVersion == %s" % WANT_FV, WANT_FV in after)]
for label, ok in checks:
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
print("\n   基线是否本就不同: %s" % (before.strip() != after.strip()))
if not any(ok for _, ok in checks):
    print("   注意: 三项都没变 —— 需区分'本机未授权 VIP(全部静默 no-op)'与'工具未生效';")
    print("        两者都不是本脚本能静态判定的(审计 §5 已列为未核实事项)。")
