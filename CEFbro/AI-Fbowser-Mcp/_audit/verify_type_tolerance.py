# -*- coding: utf-8 -*-
"""验证"类型倒挂"是否真被读取器容错修复了（目标 ≤20 秒）。

背景: `_audit/type_mismatch.py` 静态检出 7 处"schema 声明 text、代码却用 取小数 读":
  browser_vip_fingerprint_geolocation 的 lat / lng / accuracy
  browser_vip_fingerprint_battery 的 level / charging_time / discharging_time
按 schema **正确传字符串**（"39.9"）时，修复前会被读成 0 → 定位被静默置成 (0,0)（Null Island）还报成功。
第 60 节给 4 个共享读取器加了类型容错，本脚本做**端到端真机确认**。

预言机: navigator.geolocation 是异步 API, 而 CDP 求值用的是 awaitPromise=假,
故用"回调把结果写到 window 全局 + 轮询"的方式取回。
"""
import json
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


def js(code):
    e, t = call("browser_execute_js", {"code": code})
    return None if e else val(t)


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:100]))


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s" % (h.get("tool_count"), h.get("cdp_ready")))
except Exception as ex:
    print("  !! 服务未就绪(%s) -> 作废" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?geo=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.5)

# 先读基线(未设置时可能是默认或报错)
base = js("(function(){window.__geo=null;navigator.geolocation.getCurrentPosition("
          "function(p){window.__geo=p.coords.latitude+','+p.coords.longitude},"
          "function(e){window.__geo='ERR:'+e.message});return 'asked'})()")
t0 = time.time()
while time.time() - t0 < 3:
    time.sleep(0.4)
    g = js("String(window.__geo)")
    if g and g not in ("null", "undefined", ""):
        break
print("  基线 geolocation = %r" % (g,))

print("\n== 按 schema 传**字符串**设置定位 (lat='39.9', lng='116.4') ==")
e, t = call("browser_vip_fingerprint_geolocation",
            {"lat": "39.9", "lng": "116.4", "accuracy": "20"}, 40)
print("  工具回复: err=%s %s" % (e, t.replace("\n", " ")[:130]))
rec("设置调用成功", not e, t.replace("\n", " ")[:80])

call("browser_reload", {"wait_for_load": True}, 45)
time.sleep(1.0)

js("(function(){window.__geo2=null;navigator.geolocation.getCurrentPosition("
   "function(p){window.__geo2=p.coords.latitude+','+p.coords.longitude},"
   "function(e){window.__geo2='ERR:'+e.message});return 'asked'})()")
t0 = time.time()
g2 = ""
while time.time() - t0 < 4:
    time.sleep(0.4)
    g2 = js("String(window.__geo2)") or ""
    if g2 and g2 not in ("null", "undefined", ""):
        break
print("  设置后 geolocation = %r" % (g2,))

# 判定: 字符串参数必须被解析成 39.9/116.4, 而不是 0,0
if g2.startswith("39.9"):
    rec("字符串 lat/lng 生效(非 0,0)", True, g2)
elif g2.startswith("ERR:"):
    rec("字符串 lat/lng 生效(非 0,0)", False,
        "定位不可用(%s) -> 本用例无法判定, 需人工确认" % g2[:40])
elif g2.startswith("0,0") or g2.startswith("0,"):
    rec("字符串 lat/lng 生效(非 0,0)", False,
        "!! 仍被读成 (0,0) —— 类型倒挂未修复: %s" % g2)
else:
    rec("字符串 lat/lng 生效(非 0,0)", False, "得到 %r, 期望以 39.9 开头" % g2)

# 还原: 设成中性的 (0,0) 之外的值意义不大, 用真实常见坐标复位
call("browser_vip_fingerprint_geolocation", {"lat": 0.0, "lng": 0.0}, 40)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
sys.exit(1 if bad else 0)
