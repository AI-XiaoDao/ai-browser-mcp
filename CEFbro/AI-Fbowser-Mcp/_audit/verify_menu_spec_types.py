# -*- coding: utf-8 -*-
"""验收 browser_context_menu 扩展后的规格类型（修改已存在条目）。

规格(每行 类型|标签|命令ID|参数|父命令ID|快捷键):
  item|测试项|0|1|0|            创建(自动分配 26501)
  relabel|改后标签|26501|1|0|   改标签
  dis||26501|1|0|              禁用
  vis||26501|0|0|              隐藏
  mark||26501|1|0|             勾选
  accel||26501|1|0|70C         设快捷键
  noaccel||26501|1|0|          移除快捷键
  accel||100|1|0|70S           对**浏览器默认菜单项**(CEF 标准ID 100)设快捷键 <- 验证标准区间被接受
  del||26501|1|0|              删除

判据:
  · spec_lines=9(全部被接受为合法行)
  · last_error 为空  -> 说明 100 这个标准ID**没有**被"须 26500..28500"那套校验拒掉
  · last_applied_items >= 8 -> 类库对应方法真的返回成功(不是我们自报)
另测校验臂: 修改类给 ID=0 必须明确拒绝并给出指引。
每次只右键一次(原生菜单无法用 CDP 关闭)。
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
SPEC = "\n".join([
    "item|测试项|0|1|0|",
    "relabel|改后标签|26501|1|0|",
    "dis||26501|1|0|",
    "vis||26501|0|0|",
    "mark||26501|1|0|",
    "accel||26501|1|0|70C",
    "noaccel||26501|1|0|",
    "accel||100|1|0|70S",
    "del||26501|1|0|",
])
R = []


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:280])


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
call("browser_navigate", {"url": "https://example.com/?specext=1", "wait_for_load": True}, 90)
time.sleep(0.6)

print("== A) 校验臂: 修改类给 ID=0 必须拒绝 ==")
e, t = call("browser_context_menu", {"action": "set", "items": "del||0|1|0|"})
print("   -> isError=%s %s" % (e, t[:260]))
arm("修改类 ID=0 被拒绝且给出指引", e and ('已存在的命令ID' in t or '26500' in t or '标准ID' in t), t[:240])

print("\n== B) set 九行规格 ==")
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print("   -> isError=%s | %s" % (e, t[:360]))
arm("set 接受全部 9 行(spec_lines=9)", (not e) and ('"spec_lines":9' in t), t[:300])

print("\n== C) 右键一次, 施加修改类操作 ==")
for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
    call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                             "params": {"type": typ, "x": 120, "y": 120,
                                        "button": "right", "clickCount": 1,
                                        "buttons": btn}}, 40)
time.sleep(1.2)
e, t = call("browser_context_menu", {"action": "get"})
print("   -> %s" % t[:460])
m_app = re.search(r'"apply_count":(\d+)', t)
m_it = re.search(r'"last_applied_items":(\d+)', t)
m_err = re.search(r'"last_error":"([^"]*)"', t)
app = int(m_app.group(1)) if m_app else -1
items = int(m_it.group(1)) if m_it else -1
err = m_err.group(1) if m_err else '?'
arm("回调确实被调用(apply_count>0)", app > 0, "apply_count=%s" % app)
arm("★类库方法真的成功(last_applied_items>=8)", items >= 8, "last_applied_items=%s" % items)
arm("★默认菜单项的标准ID(100)未被区间校验拒掉(last_error 为空)", err == '', "last_error=%r" % err)

print("\n== D) 非法类型仍应被拒绝(回归) ==")
e, t = call("browser_context_menu", {"action": "set", "items": "bogus|x|26501|1|0|"})
print("   -> isError=%s %s" % (e, t[:240]))
arm("非法类型仍被拒绝", e and ('创建类' in t), t[:220])

call("browser_context_menu", {"action": "clear"})
ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
