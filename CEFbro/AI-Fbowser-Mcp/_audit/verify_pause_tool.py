# -*- coding: utf-8 -*-
r"""第138轮验收: `browser_debugger_pause` 是否**真的可用且安全**(不是"能看到但只会失败")。

判据:
  ① 调用成功(不再返回"已禁用"), 回执 `paused:true`;
  ② 暂停是**真的**: 暂停态下 `browser_debugger_last_paused` 能给出暂停现场;
  ③ 暂停**不会卡死实例**: 暂停态下直接调 `browser_execute_js`, 应经"卡死自救"(resume + 续等原请求)成功;
  ④ 幂等/恢复: 再次 pause 仍成功; `browser_debugger_resume` 成功后 execute_js 回到 0.03s 级;
  ⑤ 无 JS 执行点的页面(about:blank): 允许成功, 也允许**有界失败**(必须给出原因与替代), 但**不得挂起**;
  ⑥ 全程实例健康(browser_status 可用)。

用法: py -3 _audit\verify_pause_tool.py
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


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
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


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-44s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?pause=%d" % int(time.time())})
_e, _t, d0 = call("browser_execute_js", {"code": "1+1"})
print('   基线 execute_js: %.2fs' % d0)

print('\n== ① pause 必须成功 ==')
e1, t1, d1 = call("browser_debugger_pause", {}, to=60)
rec("pause 调用成功(不再『已禁用』)", (not e1) and ("paused" in t1), "%.2fs %s" % (d1, t1[:90]))
rec("回执含暂停说明(note)", "browser_debugger_resume" in t1, "")

print('\n== ② 暂停是真的: 暂停态下能读现场 ==')
e2, t2, d2 = call("browser_debugger_last_paused", {}, to=60)
rec("last_paused 可用且有内容", (not e2) and len(t2) > 5, "%.2fs %s" % (d2, t2[:90]))

print('\n== ③ 暂停不卡死实例: 暂停态下 execute_js 应经自救成功 ==')
e3, t3, d3 = call("browser_execute_js", {"code": "2+2"}, to=60)
rec("暂停态 execute_js 仍成功(<10s)", (not e3) and ("4" in t3), "%.2fs %s" % (d3, t3[:110]))

print('\n== ④ 再次 pause(幂等) + resume 后通道回到 0.03s 级 ==')
e4, t4, d4 = call("browser_debugger_pause", {}, to=60)
rec("第二次 pause 仍成功(幂等)", (not e4), "%.2fs %s" % (d4, t4[:70]))
e5, t5, d5 = call("browser_debugger_resume", {}, to=60)
rec("resume 成功", (not e5), "%.2fs %s" % (d5, t5[:70]))
_e6, _t6, d6 = call("browser_execute_js", {"code": "5+5"})
rec("resume 后 execute_js 快(<1s)", d6 < 1.0, "%.2fs" % d6)

print('\n== ⑤ 无 JS 执行点的页面(about:blank): 允许失败但不得挂起 ==')
call("browser_navigate", {"url": "about:blank"})
e7, t7, d7 = call("browser_debugger_pause", {}, to=60)
bounded = d7 < 25.0
rec("about:blank 上 pause 有界返回(不挂起)", bounded, "%.2fs %s" % (d7, t7[:80]))
rec("失败时给出原因与替代(若成功则免检)", (not e7) or ("Debugger" in t7), "")
call("browser_debugger_resume", {}, to=30)

print('\n== ⑥ 实例健康 ==')
call("browser_navigate", {"url": "https://example.com/?pause_end=%d" % int(time.time())})
e8, t8, d8 = call("browser_status", {}, to=60)
rec("browser_status 可用", (not e8), "%.2fs" % d8)
_e9, _t9, d9 = call("browser_execute_js", {"code": "1+1"})
rec("收尾 execute_js 快(<1s)", d9 < 1.0, "%.2fs" % d9)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
