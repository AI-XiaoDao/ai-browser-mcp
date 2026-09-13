# -*- coding: utf-8 -*-
"""验收 browser_kernel_watch 的读取路径(此前"只写不读")。
判据(独立分析给的三条): ① list 响应**不是空体**; ② 含 changes_json; ③ 值变更后 changes_json 里真能看到。
对照臂: stop/clear 仍要正常工作(避免"为了读而写坏别的动作")。
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


def raw_call(name, args, timeout=30):
    """返回 (http状态, 原始body, 耗时) —— 需要看原始 body 才能判定"空响应"。"""
    t0 = time.time()
    req = urllib.request.Request(BASE + "/mcp",
                                 data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                  "method": "tools/call",
                                                  "params": {"name": name,
                                                             "arguments": args}},
                                                 ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), time.time() - t0
    except Exception as ex:
        return -1, "EXC:%s" % ex, time.time() - t0


def call(name, args, timeout=30):
    st, body, dt = raw_call(name, args, timeout)
    if st != 200:
        return True, body, dt
    try:
        resp = json.loads(body)
    except Exception:
        return True, "非JSON:%s" % body[:120], dt
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, dt


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:100]))


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


print("== browser_kernel_watch 读取路径验收 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
call("browser_navigate", {"url": "https://example.com/?w=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.5)

# 1) 注册监视任务
e, t, _ = call("browser_kernel_watch", {"action": "start", "expression": "document.title",
                                        "key": "mcp_w1", "interval_ms": 500})
rec("start 成功", not e, t.replace("\n", " ")[:80])

# 2) 制造一次真实变更(改标题), 等主循环节拍(500ms)把它记进 event_log
call("browser_execute_js", {"code": "document.title='WATCH-A-%d';'ok'" % int(time.time() % 100000)})
time.sleep(3.0)
call("browser_execute_js", {"code": "document.title='WATCH-B-%d';'ok'" % int(time.time() % 100000)})
time.sleep(3.0)

# 3) list —— 关键: 先看是不是"空响应", 再看内容
st, body, dt = raw_call("browser_kernel_watch", {"action": "list"})
rec("list 响应非空体(0 字节即此前回退的那个缺陷)", bool(body.strip()),
    "HTTP=%s 长度=%d 耗时=%.2fs" % (st, len(body), dt))
try:
    outer = json.loads(body)
    ok_json = True
except Exception as ex:
    outer, ok_json = None, False
    print("     解析失败原文: %s" % body[:200])
rec("list 响应是合法 JSON-RPC", ok_json, body[:90])
has_changes = "changes_json" in body
rec("list 含 changes_json 字段", has_changes, body[:120])

if ok_json:
    try:
        # 注意: 响应经 命令成功_原始JSON -> 构建带数据字段JSON, 负载在 result.content[0].text,
        # 且**外面还包一层 data**(第一次测量就栽在这一层, 把 4 项误判为 FAIL)。
        inner = outer["result"]["content"][0]["text"]
        payload = json.loads(inner)
        rec("响应结构: 存在 data 包装层", isinstance(payload.get("data"), dict),
            "顶层键=%s" % list(payload.keys()))
        node = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        ch = node.get("changes_json")
        rec("changes_json 是 JSON 数组(未被转义成字符串)", isinstance(ch, list),
            "type=%s" % type(ch).__name__)
        # ch 的元素是 JSON 对象(字典), 不能直接切片 —— 第一次写这里时用 ch[0][:90] 抛了 slice 异常
        first = json.dumps(ch[0], ensure_ascii=False)[:90] if ch else ""
        rec("changes_json 里确有监视到的变更(不再只写不读)", bool(ch),
            "条数=%s 首条=%s" % (len(ch or []), first))
        rec("watches 仍为数组, watch_count 为整数",
            isinstance(node.get("watches"), list) and isinstance(node.get("watch_count"), int),
            "watches=%s watch_count=%s" % (node.get("watches"), node.get("watch_count")))
    except Exception as ex:
        rec("解析 list 负载", False, "EXC:%s | body=%s" % (ex, body[:200]))

# 4) 对照臂: stop / clear 仍正常
e, t, _ = call("browser_kernel_watch", {"action": "stop", "key": "mcp_w1"})
rec("对照: stop 仍正常", not e, t.replace("\n", " ")[:70])
e, t, _ = call("browser_kernel_watch", {"action": "clear"})
rec("对照: clear 仍正常", not e, t.replace("\n", " ")[:70])
e, t, dt = call("browser_kernel_watch", {"action": "list"})
rec("clear 后 list 仍正常返回(非空体)", not e and len(t) > 2, t.replace("\n", " ")[:70])

# 5) 顺带: 事件日志读取工具仍可用(改动过 查询事件日志)
e, t, _ = call("browser_event", {"limit": 5})
rec("对照: browser_event 仍可用(查询事件日志改动的回归检查)", not e,
    t.replace("\n", " ")[:70])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
