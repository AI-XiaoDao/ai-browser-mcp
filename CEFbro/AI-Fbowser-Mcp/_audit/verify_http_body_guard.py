# -*- coding: utf-8 -*-
r"""验证第126轮: 超限请求体必须得到**可行动错误**而不是"连接被关、无响应"。

背景(本轮实测): 入参 1020KB 通过、1024KB 时客户端收到 RemoteDisconnected(服务端直接关连接, 无任何响应)。
现已在 POST /mcp 读到正文前按 Content-Length 拦下并回标准 JSON-RPC 错误。验收:
  ① 512KB(正常量级)仍然成功 —— 守卫不能误伤;
  ② 1.5MB(超限)必须**拿到响应**, 且文案含"请求体过大"+ 上限 + 两条替代通道(WebSocket/stdio);
  ③ 失败后实例仍健康(守卫是在读正文前返回, 不应影响后续请求)。

用法: py -3 _audit\verify_http_body_guard.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:112]))


def call_raw(name, args, to=90):
    """返回 (异常对象, 回包文本)。异常与回包分开, 便于区分"无响应"与"有响应的失败"。"""
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": name, "arguments": args}}
    data = json.dumps(b, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(BASE + "/mcp", data=data,
                               headers={"Content-Type": "application/json"})
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    except Exception as ex:
        return ex, ""
    rr = o.get("result") or {}
    return None, "".join(i.get("text") or "" for i in (rr.get("content") or [])
                         if i.get("type") == "text") or json.dumps(o, ensure_ascii=False)


print('== ① 正常量级(512KB 入参) 必须仍然成功(守卫不误伤) ==')
ex1, t1 = call_raw("browser_execute_js", {"code": "/*" + "p" * (512 * 1024) + "*/ 1+1"})
rec("512KB 调用成功", ex1 is None and '"success":true' in t1, (str(ex1) or t1[:70]))
rec("512KB 返回了正确结果", "2" in t1, t1[:50])

print('\n== ② 超限(1.5MB 入参) 必须拿到**可行动响应**(而不是连接被关) ==')
ex2, t2 = call_raw("browser_execute_js", {"code": "/*" + "p" * (1536 * 1024) + "*/ 1+1"})
rec("超限调用**没有**抛连接异常(关键修复点)", ex2 is None, "异常=%r" % (ex2,))
rec("回包是 JSON 且含错误说明", ('"error"' in t2) and ("请求体过大" in t2), t2[:110])
rec("文案给出实测上限与安全上限", ("1048576" in t2) and ("安全上限" in t2), t2[:110])
rec("文案给出两条替代通道(WebSocket / stdio)",
    ("WebSocket" in t2) and ("stdio" in t2), t2[-110:])
rec("文案说明「无响应」这一症状(避免被当成随机故障)", "无响应" in t2, t2[:110])

print('\n== ③ 守卫之后实例仍健康, 且普通调用照常 ==')
ex3, t3 = call_raw("browser_status", {})
rec("实例健康", ex3 is None and '"success":true' in t3, (str(ex3) or t3[:60]))
ex4, t4 = call_raw("browser_execute_js", {"code": "1+1"})
rec("普通调用照常成功", ex4 is None and "2" in t4, (str(ex4) or t4[:50]))

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
