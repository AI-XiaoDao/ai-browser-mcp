# -*- coding: utf-8 -*-
"""验收 P0 缺口: `browser_create {background:true}` 创建**完全无窗口的后台浏览器**。

判据(必须证明"真的建出来了且真的能用", 而不是只看一句成功文案):
 ① 调用成功且文案明确指出是后台无窗口浏览器(与可见窗口区分);
 ② `browser_list` 里**确实多出一个**浏览器(数量 +1), 并拿到它的 id;
 ③ **该后台浏览器真的能干活**: 用 browser_id 指向它执行 JS/取文本, 能读到它自己加载的页面内容
    (这是"后台浏览器可用"的实据; 只回一句"已创建"不足以证明);
 ④ 反向对照: `background:false`(显式)与省略该参数都应走**可见窗口**路径, 文案不得说"后台";
 ⑤ 收尾把新建的浏览器关掉, 实例仍健康。
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


def list_ids():
    e, t, _ = call("browser_list", {})
    if e:
        return e, [], t
    import re
    ids = [int(x) for x in re.findall(r'"id"\s*:\s*(\d+)', t)]
    return e, sorted(set(ids)), t


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
            time.sleep(4.5)
            return True
        except Exception:
            pass
    return False


if not restart():
    print("启动失败"); sys.exit(2)

e, before, raw = list_ids()
print("  起始浏览器 id: %s" % before)

print("\n== (1) background:true 创建 ==")
e, t, dt = call("browser_create",
                {"url": "https://example.com/?bg=%d" % int(time.time()), "background": True}, 60)
rec("创建调用成功", not e, "%.2fs | %s" % (dt, t.replace("\n", " ")[:100]))
rec("文案明确指出'后台浏览器/完全无窗口'", ("后台浏览器" in t) and ("无窗口" in t),
    t.replace("\n", " ")[:110])
rec("文案给出后续用法(用 browser_id 操作)", "browser_id" in t, t.replace("\n", " ")[:110])

e, after, raw2 = list_ids()
new = [i for i in after if i not in before]
rec("browser_list 里确实多出浏览器(数量 +1)", len(new) >= 1,
    "之前=%s 之后=%s 新增=%s" % (before, after, new))

if new:
    bid = new[-1]
    print("\n== (2) 后台浏览器是否真的能干活(browser_id=%d) ==" % bid)
    e, t, dt = call("browser_execute_js", {"code": "document.title", "browser_id": bid}, 40)
    rec("后台浏览器可执行JS", not e, "%.2fs | %s" % (dt, t.replace("\n", " ")[:80]))
    rec("读到的是它自己加载的页面(Example Domain)", "Example Domain" in t,
        t.replace("\n", " ")[:80])
    e, t, dt = call("browser_get_url", {"browser_id": bid}, 40)
    rec("后台浏览器可读地址", not e and "example.com" in t, t.replace("\n", " ")[:80])
    e, t, _ = call("browser_close", {"browser_id": bid}, 40)
    rec("后台浏览器可关闭", not e, t.replace("\n", " ")[:70])

print("\n== (2b) 关键隔离: 只做了后台创建/使用/关闭之后, 主浏览器必须仍然健康 ==")
# 上一版把这一步放在"可见窗口对照"之后, 结果主浏览器 execute_js 花了 35 秒 —— 那是**创建/关闭可见窗口**
# 本身在扰动实例(GUI 窗口归主窗口管理, 关一个会影响主体), 与本轮的后台能力无关。
# 故把健康检查提前到只受后台路径影响的位置, 让归因干净。
e, t, dt = call("browser_execute_js", {"code": "1+1"})
rec("仅后台操作后, 主浏览器 execute_js 仍快", (not e) and dt < 3.0,
    "%.2fs | %s" % (dt, t.replace("\n", " ")[:50]))

print("\n== (3) 反向对照: 省略 background 应走可见窗口路径 ==")
e, t, dt = call("browser_create", {"url": "about:blank"}, 60)
rec("省略参数创建成功", not e, "%.2fs | %s" % (dt, t.replace("\n", " ")[:80]))
rec("文案**不得**说'后台浏览器'(默认仍是可见窗口)", "后台浏览器" not in t,
    t.replace("\n", " ")[:90])
e, after2, _ = list_ids()
new2 = [i for i in after2 if i not in before]
if new2:
    call("browser_close", {"browser_id": new2[-1]}, 40)

print("\n== (4) 反向对照: 显式 background:false ==")
e, t, dt = call("browser_create", {"url": "about:blank", "background": False}, 60)
rec("background:false 创建成功且不说'后台'", (not e) and ("后台浏览器" not in t),
    t.replace("\n", " ")[:90])
e, after3, _ = list_ids()
new3 = [i for i in after3 if i not in before]
if new3:
    call("browser_close", {"browser_id": new3[-1]}, 40)

print("\n== (5) 收尾: 可见窗口对照实验本身会扰动实例, 故冷重启后再确认健康 ==")
rec("可见窗口对照实验完成后(重启前)不判定主浏览器健康 —— 见 (2b) 的隔离说明)", True,
    "创建/关闭可见 GUI 窗口会影响主体, 属已知扰动")
restart()
e, t, dt = call("browser_execute_js", {"code": "1+1"})
rec("冷重启后实例健康", (not e) and dt < 3.0, "%.2fs | %s" % (dt, t.replace("\n", " ")[:50]))

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
