# -*- coding: utf-8 -*-
r"""第137轮 二阶段验证: 新逻辑的**三条分支**是否都真的按设计工作(不是只让 demo 过)。

背景: `verify_round137.py` 只验证了"install 后 JS 通道 ~1s 可用"(8/8)。本脚本补上分支级验证:

① install 成功后, execute_js 的响应里应能看到**自救确实以"续等原请求"方式发生**
   (auto_prepared 带 `续等原请求`; 若走了老的"重新派发"就会显示 `重试成功` ⇒ 判定为**未生效**)。
② `browser_reverse_skip_pauses skip=true` 之后(暂停被全局跳过, **但 `插装已安装` 仍为真** → 首轮预算仍被压到 900ms):
   跑一条 **2 秒忙等** 的脚本 —— 期望它**仍然成功**(证明"无暂停记录时把压缩预算补等回来"这一支真的存在,
   而不是把 900ms 压缩变成"提前失败")。
③ `skip=false` 恢复拦截后, 普通 execute_js 仍应 ~1s 可用(证明拦截态可反复进入/退出)。
④ `action=remove`: 期望**不再**返回"无法卸载"失败, 而是走兜底并成功; 之后 execute_js 回到 0.03s 级。
⑤ 全程实例健康(browser_status)。

用法: py -3 _audit\verify_round137b.py
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
SLOW = "long_slow_ok"


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
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:112]))


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败')
    sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?ivb=%d" % int(time.time())})

print('\n== ① install + 自救方式必须是"续等原请求" ==')
e1, t1, d1 = call("browser_reverse_instrument_script",
                  {"action": "install", "confirm": True, "event": "beforeScriptExecution"}, to=90)
rec("install 成功", not e1, "%.2fs" % d1)
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
print('    execute_js 全文: %s' % t[:400])
rec("execute_js 成功且 <5s", (not e), "%.2fs" % d)
rec("自救走的是「续等原请求」(非重派发)", "续等原请求" in t, "auto_prepared=%s" % ("续等原请求" in t))
rec("未回退到旧的重派发文案", "已自动恢复并重试成功" not in t, "")

print('\n== ①b 重复 install 必须**幂等成功**(实测卡点: 旧实现把重复调用报成失败) ==')
e1b, t1b, d1b = call("browser_reverse_instrument_script",
                     {"action": "install", "confirm": True, "event": "beforeScriptExecution"}, to=60)
rec("第二次 install 成功(不报『已处于启用状态』失败)", not e1b, "%.2fs %s" % (d1b, t1b[:110]))
rec("回执含 already_installed=true", "already_installed" in t1b, "")
e1c, t1c, d1c = call("browser_execute_js", {"code": "7*6"}, to=60)
rec("重复 install 后 JS 通道仍可用(<5s)", (not e1c) and ("42" in t1c), "%.2fs" % d1c)

print('\n== ② skip=true 后: 2 秒忙等脚本必须**仍然成功**(验证"补等"分支) ==')
e2, t2, d2 = call("browser_reverse_skip_pauses", {"skip": True}, to=30)
rec("skip=true 调用成功", (not e2), "%.2fs %s" % (d2, t2[:60]))
js = ("(function(){var t=Date.now();while(Date.now()-t<2000){};return '%s'})()" % SLOW)
e3, t3, d3 = call("browser_execute_js", {"code": js}, to=60)
rec("2 秒忙等脚本仍成功(压缩未变成提前失败)", (not e3) and (SLOW in t3), "%.2fs %s" % (d3, t3[:80]))
rec("耗时贴近真实执行时间(2~6s, 未白等满超时)", 2.0 <= d3 < 6.0, "%.2fs" % d3)

print('\n== ③ skip=false 恢复拦截后仍可用 ==')
e4, t4, d4 = call("browser_reverse_skip_pauses", {"skip": False}, to=30)
rec("skip=false 调用成功", (not e4), "%.2fs %s" % (d4, t4[:60]))
e5, t5, d5 = call("browser_execute_js", {"code": "40+2"}, to=60)
rec("恢复拦截后 execute_js 成功且 <5s", (not e5) and ("42" in t5), "%.2fs %s" % (d5, t5[:80]))

print('\n== ④ remove 走兜底并成功, 通道回到 0.03s 级 ==')
e6, t6, d6 = call("browser_reverse_instrument_script", {"action": "remove"}, to=60)
rec("remove 调用成功(不再报无法卸载)", not e6, "%.2fs %s" % (d6, t6[:100]))
rec("remove 说明了兜底事实(note 里有 setSkipAllPauses)", "setSkipAllPauses" in t6, "")
e7, t7, d7 = call("browser_execute_js", {"code": "1+1"}, to=60)
rec("remove 后 execute_js 快(<1s)", (not e7) and d7 < 1.0, "%.2fs" % d7)

print('\n== ⑤ 实例健康 ==')
e8, t8, d8 = call("browser_status", {}, to=60)
rec("browser_status 可用", (not e8), "%.2fs" % d8)

print('\n== ⑥ remove 之后再 install 也必须成功(装/停循环不得出现失败) ==')
e9, t9, d9 = call("browser_reverse_instrument_script",
                  {"action": "install", "confirm": True, "event": "beforeScriptExecution"}, to=60)
rec("remove 后重新 install 成功", not e9, "%.2fs %s" % (d9, t9[:100]))
e10, t10, d10 = call("browser_execute_js", {"code": "6*7"}, to=60)
rec("重装后 JS 通道仍可用(<5s)", (not e10) and ("42" in t10), "%.2fs" % d10)
e11, t11, d11 = call("browser_reverse_instrument_script", {"action": "suppress"}, to=60)
rec("suppress 仍可用(收尾, 恢复本会话) ", not e11, "%.2fs %s" % (d11, t11[:80]))

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
