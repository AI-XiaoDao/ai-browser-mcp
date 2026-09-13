# -*- coding: utf-8 -*-
r"""验证第125轮新增工具 browser_menu_alias(菜单命令ID ⇄ 别名)。

为什么值得单独验: 它是"读 context_menu_command 事件"的唯一解释器(事件只给数字), 且是**纯函数** ——
故可以用**强预言机**验证: 清单里每一项都做 to_name(to_id(x)) / to_id(to_name(x)) 往返, 往返不上即失败。
(这条往返性质正是不重复造轮子的证据: 反向查表由既有正向链 解析菜单命令ID 求值而来。)

用法: py -3 _audit\verify_menu_alias.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []
# 预言机: 期望值**照抄源码**(MCP_Server.wsv 方法 解析菜单命令ID 的正向链), 不凭印象
EXPECT = {"back": 100, "forward": 101, "reload": 102, "reload_nocache": 103, "stop": 104,
          "undo": 110, "redo": 111, "cut": 112, "copy": 113, "paste": 114, "delete": 115,
          "selectall": 116, "find": 130, "print": 131, "viewsource": 132,
          "nosuggestions": 205, "addtodict": 206}


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:112]))


def obj(txt):
    """把回包解成可判定的 dict: **必须解 data 包裹层** —— 实测 命令成功_原始JSON 会把载荷放在
    {"id":..,"success":true,"data":{...}} 里; 第一版探针直接在顶层取 aliases, 于是 9 条**假失败**。"""
    try:
        o = json.loads(txt)
    except Exception:
        return None
    if isinstance(o, dict) and isinstance(o.get("data"), dict):
        d = dict(o["data"])
        d.setdefault("auto_prepared", o.get("auto_prepared"))
        return d
    return o


print('== ① action=list: 清单必须与源码正向链逐项一致 ==')
e0, t0 = call("browser_menu_alias", {"action": "list"})
o0 = obj(t0) or {}
items = o0.get("aliases") or []
got = {}
for it in items:
    if isinstance(it, dict) and it.get("alias"):
        got[it["alias"]] = it.get("command_id")
rec("list 返回成功且非空", (not e0) and len(items) > 0, "count=%s len=%s" % (o0.get("count"), len(items)))
rec("清单与源码正向链**逐项一致**", got == EXPECT,
    "差异: %s" % (set(got.items()) ^ set(EXPECT.items()) or '无'))
rec("回复带诚实边界说明(caveat)", bool(o0.get("caveat")), str(o0.get("caveat") or "")[:70])

print('\n== ② 往返自检: 每一项 to_id→to_name 与 to_name→to_id 都能对上 ==')
bad = []
for alias, cid in EXPECT.items():
    _e1, t1 = call("browser_menu_alias", {"action": "to_id", "name": alias})
    _e2, t2 = call("browser_menu_alias", {"action": "to_name", "command_id": cid})
    o1, o2 = obj(t1) or {}, obj(t2) or {}
    if o1.get("command_id") != cid:
        bad.append("to_id(%s)->%s" % (alias, o1.get("command_id")))
    if (o2.get("alias") or "").lower() != alias or o2.get("recognized") is not True:
        bad.append("to_name(%s)->%s/%s" % (cid, o2.get("alias"), o2.get("recognized")))
rec("17 项全部往返一致(强预言机)", not bad, "; ".join(bad[:4]) or "17/17 一致")

print('\n== ③ action 可省略(零前置): 按已给参数自动选 ==')
_e3, t3 = call("browser_menu_alias", {"command_id": 113})
o3 = obj(t3) or {}
rec("只给 command_id → 自动 to_name=copy", o3.get("action") == "to_name" and o3.get("alias") == "copy",
    "action=%s alias=%s" % (o3.get("action"), o3.get("alias")))
_e4, t4 = call("browser_menu_alias", {"name": "paste"})
o4 = obj(t4) or {}
rec("只给 name → 自动 to_id=114", o4.get("action") == "to_id" and o4.get("command_id") == 114,
    "action=%s id=%s" % (o4.get("action"), o4.get("command_id")))
_e5, t5 = call("browser_menu_alias", {})
o5 = obj(t5) or {}
rec("空参 → 自动 list(不报缺参)", o5.get("action") == "list" and len(o5.get("aliases") or []) > 0,
    "action=%s" % o5.get("action"))

print('\n== ④ 未知/自定义 ID: 如实回答"没识别到", 不编造 ==')
_e6, t6 = call("browser_menu_alias", {"command_id": 26501})
o6 = obj(t6) or {}
rec("自建项 26501 → recognized=false 且区间=service_custom",
    o6.get("recognized") is False and o6.get("alias") == "" and o6.get("id_range") == "service_custom",
    "alias=%r range=%s" % (o6.get("alias"), o6.get("id_range")))
_e7, t7 = call("browser_menu_alias", {"command_id": 999999})
o7 = obj(t7) or {}
rec("未知 ID → 区间=unknown", o7.get("id_range") == "unknown", "range=%s" % o7.get("id_range"))

print('\n== ⑤ 失败必须可行动 ==')
e8, t8 = call("browser_menu_alias", {"action": "to_id", "name": "no-such-alias-zz"})
rec("未知别名: 报错并指向 action=list", e8 and ("未知菜单命令别名" in t8) and ("action=list" in t8), t8[:90])
e9, t9 = call("browser_menu_alias", {"action": "to_name"})
rec("to_name 缺 command_id: 报错并给例子", e9 and ("需要 command_id" in t9) and ("113" in t9), t9[:90])
e10, t10 = call("browser_menu_alias", {"action": "zzz"})
rec("未知 action: 报错并列出支持的 action", e10 and ("未知 action" in t10) and ("to_name" in t10), t10[:90])

bad2 = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad2), len(RES)))
for x in bad2:
    print('   未通过: %s' % x)
sys.exit(1 if bad2 else 0)
