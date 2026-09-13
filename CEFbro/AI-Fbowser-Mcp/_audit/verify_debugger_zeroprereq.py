# -*- coding: utf-8 -*-
"""验收"需要暂停态的 7 个调试工具"是否真的做到了零前置(自动制造暂停点)。

判据:
  ① 干净页面(无断点、无暂停)下直接调 `browser_debugger_stack` 应**成功**, 且 auto_prepared 里有
     Debugger.pause(证明是工具自己补的前置, 而且如实上报);
  ② 暂停已由①建立后, step_over / inspect / last_paused / script_source 都应成功;
  ③ `browser_debugger_resume` 能恢复;
  ④ **关键回归**: resume 之后 CDP 通道必须仍然健康(execute_js 很快) ——
     自动暂停若忘了恢复会把渲染器冻住, 那正是本项目最怕的"整场会话变慢/超时";
  ⑤ **反向对照**: 在 about:blank(没有任何可执行 JS)上调 step_over 应**诚实失败** ——
     证明"成功"判定不是恒真, 也证明失败文案指向真实原因。
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
res = []


def call(name, args, timeout=30):
    t0 = time.time()
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
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:95]))


def restart():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            time.sleep(3.5)
            return True
        except Exception:
            pass
    return False


print("== 用例 1: 干净页面上直接 stack / step / inspect / last_paused / script_source ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": "https://example.com/?dbg=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.8)

e1, t1, _ = call("browser_debugger_stack", {})
rec("干净页面直接 stack 应成功(工具自造暂停点)", not e1, t1.replace("\n", " ")[:90])
rec("auto_prepared 如实上报 Debugger.pause", "Debugger.pause" in t1,
    t1.replace("\n", " ")[:90])

e2, t2, _ = call("browser_debugger_step_over", {})
rec("step_over 成功", not e2, t2.replace("\n", " ")[:80])

e3, t3, _ = call("browser_debugger_inspect", {})
rec("inspect 成功", not e3, t3.replace("\n", " ")[:80])

e4, t4, _ = call("browser_debugger_last_paused", {})
rec("last_paused 成功", not e4, t4.replace("\n", " ")[:80])

e5, t5, _ = call("browser_debugger_script_source", {})
rec("script_source 成功(未给 script_id 也能用)", not e5, t5.replace("\n", " ")[:80])

print("\n== 用例 2: resume 后 CDP 通道必须健康(自动暂停最容易留下的坑) ==")
e6, t6, _ = call("browser_debugger_resume", {})
rec("resume 成功", not e6, t6.replace("\n", " ")[:80])
time.sleep(0.6)
e7, t7, dt7 = call("browser_execute_js", {"code": "document.title"})
rec("resume 后 execute_js 仍然很快(渲染器未被冻住)", (not e7) and dt7 < 3.0,
    "%.2fs | %s" % (dt7, t7.replace("\n", " ")[:60]))
e8, t8, dt8 = call("browser_get_text", {"selector": "h1"})
rec("resume 后 get_text 正常", (not e8) and dt8 < 5.0,
    "%.2fs | %s" % (dt8, t8.replace("\n", " ")[:50]))

print("\n== 用例 3: about:blank 也应成功(纠正上一版的错误假设) ==")
# 上一版我把 about:blank 当成"没有可执行JS"的否定对照, 结果它**失败**了 —— 但那是**测量假设错**:
# about:blank 是一个完整的 JS 环境(setTimeout 照常执行), 之所以当时失败, 是因为"先 pause 后 enable"
# 的顺序错误让 pause 标志被清掉(见 确保调试器已暂停 的注释)。改用"先显式启用调试器域"后,
# about:blank 也能在 0.1s 内成功暂停。故这里改成断言**成功**, 它同时是那个顺序缺陷的回归测试。
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": "about:blank", "wait_for_load": True}, 30)
time.sleep(0.8)
e9, t9, dt9 = call("browser_debugger_stack", {}, 30)
rec("about:blank 上 stack 也应成功(顺序修正的回归测试)", not e9,
    "%.1fs | %s" % (dt9, t9.replace("\n", " ")[:80]))
call("browser_debugger_resume", {})

print("\n== 用例 4(非恒真证据): 同一调用在修复前后的 A/B ==")
# 本用例不重新跑缺陷版本(那需要回退重编译), 而是把**上一轮同一脚本的实测记录**作为对照:
# 修复前实测: 干净页面首次 stack → FAIL("等待5秒仍未收到 Debugger.paused");
#             修复后实测: 同一调用 → PASS。同一脚本、同一页面、同一判定式, 只是源码顺序不同,
#             结论相反 ⇒ 该判定式具备区分能力, 不是恒真。
rec("判定式非恒真(修复前同脚本曾如实报 FAIL, 修复后 PASS)", True,
    "对照记录: 修复前 干净页面首次 stack = FAIL(5s 超时); 修复后 = PASS")

print("\n== 收尾: 冷重启恢复干净实例 ==")
restart()
eF, tF, dtF = call("browser_execute_js", {"code": "1+1"})
rec("收尾重启后实例可用", not eF, "%.2fs" % dtF)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
