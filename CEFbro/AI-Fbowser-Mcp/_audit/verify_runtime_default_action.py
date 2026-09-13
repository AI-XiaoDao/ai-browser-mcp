# -*- coding: utf-8 -*-
"""验收 browser_reverse_runtime 的"缺省动作"修复(零前置 / 一次成功)。

缺陷(实测): 文档写"默认properties", 而 properties **必填 object_id** ->
`browser_reverse_runtime {}` 必然返回 "properties 需要 object_id"。
对 AI 调用方 = 第一次调用必失败 -> 换个方法再试, 正是用户抱怨的模式。

修法: action 省略时按**调用方已给的关键参数**自动选可用动作
(object_id->properties / expression->evaluate / 都没有->global), 并记录到 auto_prepared。

判据:
 ① 空参调用 -> 必须**成功**(自动走 global)
 ② 只给 expression -> 自动走 evaluate 并成功
 ③ 显式 action=properties 但缺 object_id -> 仍必须**失败**(真误用不该被掩盖)
 ④ 上报链路: auto_prepared 报告由"响应构建器"消费并清除, 而这两个工具经
    **异步派发回执**返回(回执不走构建器) -> 需判断这次自动选择是"延后到下一个响应"还是"丢失"。
    做法: 先调一次会记录说明的工具, 紧接着调一个走构建器的工具(browser_status), 看说明是否出现。

注: 本轮**未能**验证 "evaluate 产出 objectId -> properties 消费" 这条链路 ——
    异步结果的正确取回方式(task_id 正则 + mcp_result 轮询)在本脚本里没跑通,
    故不写断言、不假装通过(见报告 97.x)。
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


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:90]))


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
call("browser_navigate", {"url": "https://example.com/?rtfix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① 空参调用 -> 必须成功(自动走 global) ==")
e, t, dt = call("browser_reverse_runtime", {}, 45)
print("   isError=%s 用时=%.2fs" % (e, dt))
print("   resp: %s" % t[:300])
rec("空参调用成功(不再必失败)", not e, t[:90])
rec("自动选了 global(而非必失败的 properties)",
    ("globalLexicalScopeNames" in t) or ("global" in t), t[:90])

print("\n== ② 只给 expression -> 自动走 evaluate ==")
e, t, dt = call("browser_reverse_runtime", {"expression": "1+1"}, 45)
print("   isError=%s" % e)
print("   resp: %s" % t[:300])
rec("成功且自动选了 evaluate", (not e) and ("Runtime.evaluate" in t), t[:90])

print("\n== ③ 显式 properties 缺 object_id -> 仍应失败(真误用不该被掩盖) ==")
e, t, dt = call("browser_reverse_runtime", {"action": "properties"}, 45)
print("   resp: %s" % t[:200])
rec("显式误用仍被拒绝且可行动", e and ("object_id" in t), t[:90])

print("\n== ④ auto_prepared 上报链路: 是'延后到下一个响应'还是'丢失'? ==")
call("browser_reverse_runtime", {}, 45)
e2, t2, _ = call("browser_status", {}, 45)
print("   browser_status resp: %s" % t2[:400])
seen = "auto_prepared" in t2
rec("说明至少在后续响应里出现(未丢失)", seen, t2[:90] if seen else "未出现")
if seen:
    print("   (说明被延后到后续响应 —— 归因不精确, 但信息未丢失; 已记入报告待修)")
else:
    print("   !! 说明既未随本次回执出现、也未在下一个响应出现 -> 需查为何被吞掉")

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
