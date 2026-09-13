# -*- coding: utf-8 -*-
"""验收 browser_reverse_hook_multi 与 hook_logs 读路径的自递归/var捕获修复。

本测试一次覆盖三个缺陷(它们都会在"勾多个函数"这种常规用法下触发):
 ① 安装期自递归: 目标里含 Array.prototype.push 时, 装好包装器后紧接的 found.push(name) 会进包装器 -> 崩
 ② var 捕获: 循环里 var name/var __orig 是函数作用域, 所有包装器共享 -> 全部记录成最后一个名字、
    并调用最后一个原函数(实测症状: 被勾的函数调用后返回值不对)
 ③ 读路径: hook_logs 用 hit.push/arr.slice/items.push, 而这些方法**此刻已被包装** -> 读日志自己会中招

判据:
 A 勾 [mcpFnA, mcpFnB, Array.prototype.push] -> 必须成功且 found=3(①)
 B 被勾后 mcpFnA(1)=2、mcpFnB(2)=4 -> 语义未坏, 且 proves 没串到别的原函数(②)
 C 被勾后 a.push(1,2,3) 仍得 len=3 -> 包装 push 不破坏数组语义(② 的语义面)
 D 读日志必须成功, 且日志里**同时**出现 mcpFnA 与 mcpFnB 两个不同 fn 名 -> ② 的决定性证据
   (修复前所有条目都会是同一个名字)
 E 读路径成功后 count>0 -> 证明读路径在 push 被包装时仍可用(③)
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


def call_final(name, args, timeout=45, tries=8):
    """调用并跟随异步任务(task_id -> mcp_result), 返回 (isError, 最终文本)。"""
    e, t, dt = call(name, args, timeout)
    tid = None
    m = re.search(r'(task_[0-9_]+)', t)
    if m:
        tid = m.group(1)
    else:
        m2 = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
        if m2:
            tid = m2.group(1)
    if not tid:
        return e, t
    for _ in range(tries):
        e2, t2, _ = call("mcp_result", {"request_id": tid, "consume": True}, 30)
        if t2 and ("pending" not in t2.lower()) and t2.strip() not in ("", "{}"):
            return e2, t + " || " + t2
        time.sleep(0.5)
    return e, t


def unesc(t):
    return t.replace('\\"', '"').replace(" ", "")


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:86]))


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
call("browser_navigate", {"url": "https://example.com/?hookmulti=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== 准备: 定义两个可勾的全局函数 ==")
e, t, _ = call("browser_execute_js",
               {"code": "window.mcpFnA=function(x){return x+1};"
                        "window.mcpFnB=function(y){return y*2};'ready'"}, 30)
print("   %s" % t[:140])

print("\n== A 勾 [mcpFnA, mcpFnB, Array.prototype.push] (含安装期递归触发点) ==")
# 注意: schema 里该参数是 **JSON数组字符串**(text 型), 不是 JSON 数组 —— 第一版传了数组,
# 于是只测到守卫("functions 需要JSON数组"), 后面各臂都因"其实没勾上"而失败。
e, t = call_final("browser_reverse_hook_multi",
                  {"functions": json.dumps(["mcpFnA", "mcpFnB", "Array.prototype.push"])}, 60)
print("   isError=%s" % e)
print("   %s" % t[:400])
u = unesc(t)
rec("勾选成功且 found=3", (not e) and ('"found":3' in u), t[:86])

print("\n== B 语义: mcpFnA(1)=2 / mcpFnB(2)=4 (② 决定性) ==")
e, t, _ = call("browser_execute_js",
               {"code": "JSON.stringify({a:window.mcpFnA(1),b:window.mcpFnB(2)})"}, 30)
print("   %s" % t[:200])
u = unesc(t)
rec("mcpFnA(1)==2 且 mcpFnB(2)==4", (not e) and ('"a":2' in u) and ('"b":4' in u), t[:86])

print("\n== C a.push 仍正常(包装 push 不破坏数组语义) ==")
e, t, _ = call("browser_execute_js",
               {"code": "(function(){var a=[];var r=a.push(1,2,3);"
                        "return JSON.stringify({len:a.length,ret:r})})()"}, 30)
print("   %s" % t[:200])
u = unesc(t)
rec("a.push 后 len=3 且 ret=3", (not e) and ('"len":3' in u) and ('"ret":3' in u), t[:86])

print("\n== D/E 读日志(push 已被包装): 必须成功, 且两个 fn 名都在 ==")
e, t = call_final("browser_reverse_hook_logs", {}, 60)
print("   isError=%s" % e)
print("   %s" % t[:600])
u = unesc(t)
rec("读日志成功(③)", not e, t[:86])
has_a = '"fn":"mcpFnA"' in u
has_b = '"fn":"mcpFnB"' in u
rec("日志里同时有 mcpFnA 与 mcpFnB(② 决定性)", has_a and has_b,
    "mcpFnA=%s mcpFnB=%s" % (has_a, has_b))
m = re.search(r'"count":(\d+)', u)
cnt = int(m.group(1)) if m else -1
rec("count>0(读路径确实拿到数据)", cnt > 0, "count=%s" % cnt)

# 收尾: 重载清掉包装
call("browser_navigate", {"url": "https://example.com/?cleaned=1", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t, _ = call("browser_execute_js",
               {"code": "JSON.stringify({log:typeof window.__MCP_HOOK_LOG__,"
                        "orig:typeof Array.prototype.push.__mcp_orig})"}, 30)
print("\n   收尾检查: %s" % t[:180])
rec("重载后包装已清除", 'log":"undefined' in unesc(t), t[:86])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
