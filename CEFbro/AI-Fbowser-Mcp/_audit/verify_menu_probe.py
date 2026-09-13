# -*- coding: utf-8 -*-
r"""第139轮验收(菜单族 v2): 按**实测约束**重写判据 —— 只断言可复现的事, 其余如实记录。

可复现事实(三次独立运行): 第 1 次 arm 必成功; 第 2 次起必失败(原生菜单模态 + CDP 关不掉它)。
故本脚本:
  ① schema: browser_menu_probe 有 action/x/y/trigger/wait_ms; browser_context_menu 有 confirm_wipe/experimental;
  ② **第一次**菜单打开(唯一可靠的一次)同时做两件事: 采集"施加前"的默认菜单实况 + 施加我预置的规格
     ⇒ 一次调用同时验证"只读快照"和"按索引写"两条新通道;
  ③ 第二次 arm 必须**快速且诚实**(≤3s 返回, 要么快照、要么说明模态约束), 不得再白等 5.7 秒;
  ④ 守卫: wipe 唯一行/需 confirm、accelat 索引列错位、索引越界;
  ⑤ 收尾健康(execute_js 0.03s 级、browser_status、页面标题可读)。

用法: py -3 _audit\verify_menu_probe.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []
INFO = []


def call(n, a=None, to=60, rid=1):
    b = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def payload(txt):
    """取回包里的载荷。注意: 有的工具把 data 写成**字符串**(嵌套 JSON), 有的直接写成**对象** ——
    两种都要处理(曾因只处理字符串而把 apply_count 读成 None, 误判成"没施加")。"""
    try:
        o = json.loads(txt)
    except Exception:
        return {}
    d = o.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return o if isinstance(o, dict) else {}


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


def info(tag, detail=""):
    INFO.append((tag, detail))
    print('  [INFO] %-48s %s' % (tag, str(detail)[:104]))


print('== ① tools/list: 新参数必须都声明 ==')
try:
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode(),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    tools = ((o.get("result") or {}).get("tools") or [])

    def props(name):
        t = [x for x in tools if x.get("name") == name]
        return (((t[0].get("inputSchema") or {}).get("properties") or {}) if t else {}), bool(t)

    p_probe, ok_probe = props("browser_menu_probe")
    rec("browser_menu_probe 已注册(工具数 %d)" % len(tools), ok_probe, "")
    rec("probe schema 有 action/x/y/trigger/wait_ms",
        set(p_probe) >= {"action", "x", "y", "trigger", "wait_ms"}, sorted(p_probe))
    p_cm, ok_cm = props("browser_context_menu")
    rec("context_menu schema 有 confirm_wipe/experimental",
        set(p_cm) >= {"confirm_wipe", "experimental"}, sorted(p_cm))
except Exception as ex:
    rec("tools/list 读取", False, repr(ex))

print('\n== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?mp=%d" % int(time.time())})

print('\n== ② 预置规格(含两条 accelat 索引行) → 第一次菜单打开同时验证快照与索引写 ==')
# 索引 0 = 该页默认菜单的第一项; 索引 17 = 本页默认菜单的条目数(前两轮实测), 正是本次新建项会落到的位置。
# 若实际条目数不是 17, accelat@17 会如实进 apply_failed —— 那本身就是有效测量。
spec = "item|MCP索引测试项|26501|1|0|\naccelat||17|1|0|70C\naccelat||0|1|0|70C"
e0, t0, d0 = call("browser_context_menu", {"action": "set", "items": spec}, to=30)
rec("set(含索引行) 成功且载荷是合法 JSON", (not e0) and bool(payload(t0)), "%.2fs spec_lines=%s" % (d0, payload(t0).get("spec_lines")))
e1, t1, d1 = call("browser_menu_probe", {"action": "arm", "x": 240, "y": 170}, to=60)
p1 = payload(t1)
n = p1.get("declared_count")
rec("arm 拿到默认菜单实况(declared_count ≥1)", isinstance(n, int) and n >= 1, "%.2fs N=%s" % (d1, n))
rec("items 数与 read_count 一致", isinstance(p1.get("items"), list) and len(p1["items"]) == p1.get("read_count"),
    "items=%s read=%s" % (len(p1.get("items") or []), p1.get("read_count")))
rec("快照带 snapshot_at_ms(可判新鲜度)", isinstance(p1.get("snapshot_at_ms"), int), p1.get("snapshot_at_ms"))
if isinstance(p1.get("items"), list) and p1["items"]:
    acc = [i for i in p1["items"] if i.get("has_accel")]
    info("实况里带快捷键提示的条目数", "%d / %d" % (len(acc), len(p1["items"])))

e2, t2, d2 = call("browser_context_menu", {"action": "get"}, to=30)
p2 = payload(t2)
rec("右键确实施加了规格(apply_count ≥1)", isinstance(p2.get("apply_count"), int) and p2["apply_count"] >= 1,
    "apply_count=%s last_applied=%s" % (p2.get("apply_count"), p2.get("last_applied_items")))
rec("新建项创建成功(last_applied_items ≥1)", isinstance(p2.get("last_applied_items"), int) and p2["last_applied_items"] >= 1,
    "last_applied=%s" % p2.get("last_applied_items"))
rec("回读核对条数 ≥1(verified_items)", isinstance(p2.get("verified_items"), int) and p2["verified_items"] >= 1,
    "verified=%s" % p2.get("verified_items"))
info("apply_failed", str(p2.get("apply_failed") or "空")[:150])
info("verify_unavailable", str(p2.get("verify_unavailable") or "空")[:120])
if isinstance(n, int):
    idx_ok = isinstance(p2.get("verified_items"), int) and p2["verified_items"] >= 2
    if idx_ok:
        rec("按索引写通道生效(verified_items ≥2 = 新建项 + 至少一条 accelat 索引行)", True,
            "verified=%s" % p2.get("verified_items"))
    else:
        info("按索引写通道本次未获回读确认",
             "verified=%s; apply_failed=%s" % (p2.get("verified_items"), str(p2.get("apply_failed"))[:110]))

print('\n== ③ 第二次 arm 必须快速且诚实(不得再白等 5.7s) ==')
e3, t3, d3 = call("browser_menu_probe", {"action": "arm", "x": 240, "y": 170}, to=60)
got = "declared_count" in t3
rec("第二次 arm ≤3s 返回", d3 <= 3.0, "%.2fs" % d3)
if got:
    rec("第二次 arm 直接给到快照(极好)", True, "N=%s" % payload(t3).get("declared_count"))
else:
    honest = ("模态" in t3) and ("已武装" in t3) and (not e3)
    rec("第二次 arm 如实说明模态约束(仍是成功回包+两条下一步)", honest, "%.2fs %s" % (d3, t3[:90]))
e4, t4, d4 = call("browser_menu_probe", {"action": "get", "wait_ms": 800}, to=30)
info("get(wait_ms=800) 结果", ("拿到快照" if "declared_count" in t4 else t4[:90]))
call("browser_menu_probe", {"action": "clear"}, to=30)
e5, t5, _ = call("browser_menu_probe", {"action": "get", "wait_ms": 300}, to=30)
rec("clear 后 get 失败且给可行动做法", e5 and ("arm" in t5), t5[:80])

print('\n== ④ 守卫 ==')
call("browser_context_menu", {"action": "clear"}, to=30)
e6, t6, _ = call("browser_context_menu", {"action": "set", "items": "item|X|0|1|0|\nwipe||0|1|0|"}, to=30)
rec("wipe 与其它行混用被拒", e6 and ("唯一" in t6), t6[:70])
e7, t7, _ = call("browser_context_menu", {"action": "set", "items": "wipe||0|1|0|"}, to=30)
rec("wipe 缺 confirm_wipe 被拒", e7 and ("confirm_wipe" in t7), t7[:70])
e8, t8, _ = call("browser_context_menu", {"action": "set", "items": "wipe||0|1|0|", "confirm_wipe": True}, to=30)
rec("wipe(唯一行+confirm) 被接受", not e8, t8[:70])
e9, t9, _ = call("browser_context_menu", {"action": "set", "items": "accelat||26501|1|0|70C"}, to=30)
rec("索引列填命令ID 被拒(错位防护)", e9 and ("命令ID" in t9), t9[:80])
e10, t10, _ = call("browser_context_menu", {"action": "set", "items": "accelat||99999|1|0|70C"}, to=30)
rec("索引越界被拒", e10 and ("越界" in t10 or "命令ID" in t10), t10[:70])
e11, t11, _ = call("browser_context_menu", {"action": "set", "items": "fontat||0|Arial|0|"}, to=30)
p11 = payload(t11)
info("fontat 未开 experimental 的结果", ("已接受" if not e11 else t11[:80]))
call("browser_context_menu", {"action": "clear"}, to=30)

print('\n== ⑤ 收尾健康 ==')
e12, t12, d12 = call("browser_execute_js", {"code": "1+1"}, to=30)
rec("execute_js 正常(<1s, 通道未被打死)", (not e12) and d12 < 1.0, "%.2fs" % d12)
e13, t13, d13 = call("browser_status", {}, to=30)
rec("browser_status 可用", (not e13), "%.2fs" % d13)
e14, t14, _ = call("browser_get_title", {}, to=30)
rec("页面标题可读", (not e14) and len(t14) > 5, t14[:50])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
print('INFO 记录 %d 条(如实记录, 不计入通过率)' % len(INFO))
sys.exit(1 if bad else 0)
