# -*- coding: utf-8 -*-
"""量一量: 自动暂停到底"留不留得住"。

## 为什么要量
第 68 轮我给 7 个调试工具加了 `确保调试器已暂停`(自动启用调试器域 + 安排执行点 + Debugger.pause),
验收脚本里 `stack`/`step_over`/`last_paused` 都成功了。但本轮实测:
  先调 `browser_debugger_stack`(返回 OK) → 再调 `browser_debugger_wait_paused` → **超时 15s**。
`wait_paused` 不调用 确保已暂停, 所以它拿不到暂停事件这件事说明: **暂停可能在调用之间就没了**。
若属实则第 68 轮那句"确实进入过暂停态"要打折 —— 每个工具其实是在各自调用里各自重新暂停了一次。

## 怀疑机制(待证)
`执行CDP并同步等待` 里有"卡死自救": 等待超时**且**存在未处理 `Debugger.paused` 事件时,
会自动发 `Debugger.resume` 并重试一次。而 `Debugger.pause` 之后渲染器就冻结了, 它的**命令响应**
可能等不到 → 触发自救 → **把刚建立的暂停又 resume 掉**。若如此, `确保调试器已暂停` 是"靠
缓存里残留的暂停事件"误判成功的。

判据(逐个打印, 不靠推测): stack 之后, 立刻问 last_paused 是否还看得到暂停事件;
再问 wait_paused(短超时) 是否立刻拿到; 以及 wait_paused 之后再问一次 last_paused。
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


def call(name, args, timeout=25):
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


def show(tag, e, t, dt):
    print("  %-42s %-5s %5.2fs  %s" % (tag, "ERR" if e else "OK", dt,
                                       t.replace("\n", " ")[:96]))


print("== 干净重启 + 导航 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": "https://example.com/?wp=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.8)

print("\n== 步骤 1: 起始态(应无暂停) ==")
show("last_paused(起始, 期望失败)", *call("browser_debugger_last_paused", {}))

print("\n== 步骤 2: 自动暂停 ==")
show("stack(期望 OK + auto_prepared)", *call("browser_debugger_stack", {}))

print("\n== 步骤 3: 暂停还在吗(紧随其后, 不同请求) ==")
show("last_paused(期望能看到暂停事件)", *call("browser_debugger_last_paused", {}))
show("wait_paused(max_ms=2500, 期望立刻拿到)", *call("browser_debugger_wait_paused",
                                                    {"max_ms": 2500}, 30))

print("\n== 步骤 4: wait_paused 之后暂停还在吗 ==")
show("last_paused(再次)", *call("browser_debugger_last_paused", {}))

print("\n== 步骤 5: 只有 ensure 时, 暂停是否被自己 resume 掉 ==")
show("stack(第二次, 期望 OK)", *call("browser_debugger_stack", {}))
show("step_over(期望 OK)", *call("browser_debugger_step_over", {}))
show("last_paused(step 之后)", *call("browser_debugger_last_paused", {}))

print("\n== 收尾: resume + 健康检查 ==")
show("resume", *call("browser_debugger_resume", {}))
show("execute_js(应很快)", *call("browser_execute_js", {"code": "document.title"}))
