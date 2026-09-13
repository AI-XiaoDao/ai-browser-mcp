# -*- coding: utf-8 -*-
"""验收 browser_vip_enable_devtools_observer 的"取值白名单"修复。

=== 缺陷(修复前, 有台账实录) ===
该分支原来只挡住了**空文本/缺省**这一种情况:

    目标状态 = 开关布尔                       # 非布尔节点取逻辑 -> 假
    如果 ("false"/"0"/"off") 目标状态 = 假
    否则 ("true"/"1"/"on")   目标状态 = 真
    如果 (开关文本 == "" 且 开关布尔 == 假) -> 拒绝
    enableObs = 目标状态

传 enable:"mcp_probe" 时: 开关文本非空 -> 旧守卫不触发 -> 既不匹配 true 形式也不匹配
false 形式 -> 目标状态沿用 假 -> **把 CDP 观察者关掉了**。
即"最危险的分支成了兜底"。实录那一批台账调用之后紧跟一次必须的冷重启, 正是被这个动作搞坏的。

=== 判别性观测的选择(关键) ===
不能只看返回文本: 该分支后面还有"VIP 是否可用"的检查, 成功/失败会被 VIP 可用性干扰。
真正的判别量是 **CDP 通道的生死**, 用 browser_cdp_call 探测 —— 它经 执行CDP命令 直达内核,
**没有原生回退**(Core: browser_cdp_call 分支), 且注释明确"仅检查不注册", 不会被顺带重新注册。
对照: browser_execute_js 走 CDP->原生 回退, 通道死了也可能"成功", 故**不能**用作存活判据。

=== 判据 (可证伪) ===
  ① baseline             -> CDP 存活 (测量环境有效性前提; 不成立则整轮作废)
  ② enable 缺省          -> 拒绝(取值无法识别), 且 CDP 存活
  ③ enable:"mcp_probe"   -> 拒绝, 且 CDP 存活      <-- 修复前这一条会关掉 CDP(核心缺陷臂)
  ④ enable:true (布尔)   -> 不被拒, 且 CDP 存活
  ⑤ enable:"true" (文本) -> 不被拒, 且 CDP 存活
  ⑥ enable:"false"(文本) -> 唯一允许关闭的取值; 关闭后 CDP **必须能被探到死亡**
                            (正对照: 证明探针不瞎, 否则 ②③ 的"存活"毫无意义)
  ⑦ 重启后               -> CDP 恢复存活
"""
import json
import os
import re
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
TOOL = "browser_vip_enable_devtools_observer"
REJECT_MARK = "取值无法识别"
res = []


def call(name, args, timeout=45):
    t0 = time.time()
    try:
        req = urllib.request.Request(
            BASE + "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": name, "arguments": args}},
                            ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def cdp_alive():
    """被动观测 CDP 通道是否在册: 直接读 /health 的 cdp_ready(= CDP观察者已注册 标志本体, HTTP.wsv:148)。
    走 HTTP 健康端点、**不经 MCP 派发**, 因此不可能有副作用。

    ★ 这里**不能**用 browser_cdp_call 当探针 —— 第一版本就是那么写的, 正对照(⑥)当场把它否掉:
      执行CDP命令_带参数 在 CDP观察者已注册==假 时**会自动重新注册观察者**(自身注释: "CDP通道自动就绪"),
      于是"探测"把要测的东西给修好了 —— 观测动作改变了被观测对象, 结论不可信。
      正对照的价值正在于此: 它证明了探针没有判别力, 而不是证明修复无效。
    """
    t0 = time.time()
    try:
        with urllib.request.urlopen(BASE + "/health", timeout=8) as r:
            h = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return None, "EXC:%s" % ex
    dt = time.time() - t0
    if "cdp_ready" not in h:
        return None, "%.2fs | /health 无 cdp_ready 字段: %s" % (dt, str(h)[:70])
    val = bool(h.get("cdp_ready"))
    return val, "%.2fs | cdp_ready=%s" % (dt, val)


def cdp_dispatch_ok():
    """一次真实 CDP 派发(会触发自愈), 用于⑦验证"关掉之后是否真需要重启"。"""
    e, t, dt = call("browser_cdp_call",
                    {"method": "Runtime.evaluate",
                     "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"},
                    timeout=20)
    return (not e), "%.2fs | %s" % (dt, t[:80])


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:92]))


def arm_enable(value, tag, expect_reject, expect_close=False, expect_inreg=True,
               tool=TOOL):
    """跑一个 enable 取值臂, 并立刻**被动**观测观察者是否仍在册。
    value=_MISSING 表示"不带 enable"。expect_inreg=False 用于关闭臂(⑥/⑪, 它本就该注销)。
    tool 可切换为同族的 browser_vip_enable_inspector。
    """
    if value is _MISSING:
        e, t, dt = call(tool, {})
    else:
        e, t, dt = call(tool, {"enable": value})
    # 两个工具的"拒绝"文案不同: devtools_observer 走白名单, enable_inspector 缺键时是"必须显式指定"
    rejected = (REJECT_MARK in t) or ("必须显式指定" in t)
    print("    %-22s -> isError=%s 拒绝标记=%s 用时=%.2fs" % (tag, e, rejected, dt))
    print("      resp: %s" % t[:150])
    if expect_reject:
        rec("%s 被拒绝(可行动)" % tag, rejected, t[:88])
    else:
        rec("%s 未被拒(非白名单误伤)" % tag, not rejected, t[:88])
        if expect_close:
            rec("%s 如实报告已关闭" % tag, "已关闭" in t, t[:88])
        else:
            rec("%s 未报已关闭" % tag, "已关闭" not in t, t[:88])
    inreg, det = cdp_alive()
    if expect_inreg:
        rec("%s 之后观察者仍在册(被动观测)" % tag, inreg is True, det)
    else:
        rec("%s 之后观察者已注销(被动观测, 正对照)" % tag, inreg is False, det)
    return inreg


class _Missing(object):
    pass


_MISSING = _Missing()

# ---- 已知干净状态起步 ----
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

call("browser_navigate", {"url": "https://example.com/?obs=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① baseline: 观察者必须在册(否则本轮测量环境无效) ==")
base_alive, det = cdp_alive()
rec("baseline 观察者在册", base_alive is True, det)
if not base_alive:
    print("\n!! baseline 就不通, 本轮结论一律作废, 先修环境")
    sys.exit(2)

print("\n== ② enable 缺省 -> 拒绝且不关 CDP ==")
arm_enable(_MISSING, "缺省", True)

print("\n== ③ enable:\"mcp_probe\" -> 拒绝且不关 CDP (核心缺陷臂) ==")
arm_enable("mcp_probe", "\"mcp_probe\"", True)

print("\n== ④ enable:true (布尔) -> 不得被拒 ==")
arm_enable(True, "布尔 true", False)

print("\n== ⑤ enable:\"true\" (文本) -> 不得被拒 ==")
arm_enable("true", "文本 \"true\"", False)

print("\n== ⑥ enable:\"false\" -> 唯一允许关闭; 被动观测必须看到它真的关掉(该臂自身就是正对照) ==")
inreg_after_close = arm_enable("false", "文本 \"false\"", False,
                               expect_close=True, expect_inreg=False)
if inreg_after_close is False:
    print("      正对照成立: 关闭动作确实被被动观测到 -> ②③ 的'仍在册'具备判别力")
else:
    print("      !! 正对照不成立: 关了观察者 cdp_ready 却没变 -> ②③ 的'仍在册'没有证据价值")

print("\n== ⑦ 关闭之后的一次真实 CDP 派发 -> 观察是否自愈(决定'需重启'这句是否属实) ==")
call("browser_navigate", {"url": "https://example.com/?obs=heal", "wait_for_load": True}, 45)
time.sleep(0.4)
ok, det = cdp_dispatch_ok()
rec("关闭后 CDP 派发仍可用", ok, det)
healed, det2 = cdp_alive()
print("      自愈后: %s" % det2)
rec("[记录] 观察者被自动重新注册(自愈)", healed is True, det2)

print("\n== ⑧ 重启后观察者应在册 ==")
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
call("browser_navigate", {"url": "https://example.com/?obs=2", "wait_for_load": True}, 45)
time.sleep(0.6)
alive, det = cdp_alive()
rec("重启后观察者在册", alive is True, det)

# ================= 同族工具 browser_vip_enable_inspector =================
# 它是**同一缺陷类**的第二个实例(原来只挡"键缺失", 非空但无法识别的取值同样掉进 注销CDP观察者)。
# 故把同一组臂在它上面再跑一遍 —— 修复一个点之后必须横扫同族, 否则等于没修。
TOOL2 = "browser_vip_enable_inspector"
print("\n== ⑨ [同族] enable_inspector 缺 enable -> 拒绝 ==")
arm_enable(_MISSING, "[insp] 缺省", True, tool=TOOL2)

print("\n== ⑩ [同族] enable_inspector enable:\"mcp_probe\" -> **必须拒绝**(修复前会注销观察者) ==")
arm_enable("mcp_probe", "[insp] \"mcp_probe\"", True, tool=TOOL2)

print("\n== ⑪ [同族] enable_inspector enable:false(布尔) -> 该工具文档接受为关闭(正对照) ==")
arm_enable(False, "[insp] 布尔 false", False, expect_close=True,
           expect_inreg=False, tool=TOOL2)

print("\n== ⑫ [同族] 再用 true 打开 -> 恢复在册 ==")
arm_enable(True, "[insp] 布尔 true", False, tool=TOOL2)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)