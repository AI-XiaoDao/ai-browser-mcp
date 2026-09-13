# -*- coding: utf-8 -*-
"""把台账里"跳过(致命/污染全局)"的 6 个工具**受控地实际测一遍**, 逐条记录真实结果。

台账默认跳过它们(怕把实例搞死/污染全局状态), 于是这 6 个一直"未测"。
但它们也是能力的一部分, 应该给它们**受控测量**——设计如下(每个都尽量选"不伤主实例"的路径):

  ① browser_set_preference   : 把一个 webkit 首选项设成**它本来就是的值**(无害), 看是否成功
  ② browser_set_s5_proxy     : 设一个**本机无效代理**(127.0.0.1:1) 看是否成功, 随后立刻重启清掉
  ③ browser_reverse_patch    : 用 **dry_run:true** —— 工具自己提供"只验证编译不实际替换", 零破坏
  ④ browser_close            : **先创建第二个后台浏览器**, 然后只关 browser_id=2(不动主浏览器)
  ⑤ browser_close_try        : 无参数; 按文档它会关掉浏览器 -> 很可能终止程序, 故放在靠后
  ⑥ browser_shutdown         : confirm=true + delay_seconds 短延迟, 必然终止程序, 放最后

每步都记录: 调用结果原文 + 之后实例是否还活(用 browser_status 计时对比基线)。
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
rows = []


def call(name, args, timeout=40):
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


def start_app():
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
            return True
        except Exception:
            pass
    return False


def alive():
    """实例是否还活: 用 browser_status 计时(原生路径, 最轻)。"""
    e, t, dt = call("browser_status", {}, 15)
    return (not e) and dt < 8


def probe(tag, name, args, note=""):
    e, t, dt = call(name, args)
    live = alive()
    rows.append((tag, name, not e, dt, live, t[:200]))
    print("   [%s] %-26s isError=%-5s %5.2fs 存活=%s" % ("PASS" if not e else "FAIL", name, e, dt, live))
    print("        %s" % t[:230].replace("\n", " "))
    if note:
        print("        (设计: %s)" % note)
    return e, t, live


print("== 准备: 干净实例 ==")
start_app()
call("browser_navigate", {"url": "https://example.com/?skipped=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("\n== ① browser_set_preference (设成它本来就该有的值, 无害) ==")
probe("① set_preference", "browser_set_preference",
      {"name": "webkit.webprefs.javascript_enabled", "value": "true"},
      "值与该首选项的常态一致, 不改变行为")

print("\n== ② browser_set_s5_proxy (指向本机无效端口, 随后重启清掉) ==")
probe("② set_s5_proxy", "browser_set_s5_proxy", {"address": "127.0.0.1:1"},
      "无效地址, 且测完立刻重启, 不留代理设置")
print("   -> 重启清场")
start_app()
call("browser_navigate", {"url": "https://example.com/?skipped=2", "wait_for_load": True}, 45)
time.sleep(0.5)

print("\n== ③ browser_reverse_patch (dry_run:true, 只验证编译不替换) ==")
probe("③ reverse_patch(dry)", "browser_reverse_patch",
      {"source": "(function(){return 1})()", "dry_run": True},
      "工具自带 dry_run, 零破坏")

print("\n== ④ browser_close (先造第二个后台浏览器, 只关它) ==")
e, t, _ = call("browser_create", {"url": "https://example.com/?second=1", "background": True}, 60)
time.sleep(1.0)
print("   create: isError=%s %s" % (e, t[:160]))
e, t, live = probe("④ close(bid=2)", "browser_close", {"browser_id": 2},
                   "只关后台浏览器, 不动主浏览器")
if not live:
    print("   -> 主实例受影响, 重启")
    start_app()
    call("browser_navigate", {"url": "https://example.com/?skipped=4", "wait_for_load": True}, 45)

print("\n== ⑤ browser_close_try (文档: 会关闭浏览器 -> 可能终止程序) ==")
probe("⑤ close_try", "browser_close_try", {}, "放靠后, 因为它可能终止程序")
time.sleep(2)
print("   -> 无条件重启, 保证后续可用")
start_app()

print("\n== ⑥ browser_shutdown (confirm=true, 短延迟; 必然终止程序) ==")
probe("⑥ shutdown", "browser_shutdown", {"confirm": True, "delay_seconds": 2},
      "最后一项, 必然终止, 之后重启")
time.sleep(5)
print("   -> 重启")
start_app()

print("\n===== 汇总(逐条) =====")
ok = 0
for tag, name, good, dt, live, txt in rows:
    print("%-22s %-28s %s  %.2fs  存活=%s" % (tag, name, "成功" if good else "失败", dt, live))
    if good:
        ok += 1
print("\n调用成功 %d/%d" % (ok, len(rows)))
print("(逐条原文见上面每步的输出; 本脚本不修改台账, 结果写进报告)")
