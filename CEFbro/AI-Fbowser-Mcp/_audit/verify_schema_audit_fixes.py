# -*- coding: utf-8 -*-
r"""验证第125轮"schema↔实现一致性修正"(依据只读审计 `_audit/_schema_audit_B.md`)。

分两层验证(都必要):
  ① **声明层**(tools/list): 实现真读的参数必须出现在 schema; 必填列表必须与实现守卫一致。
     这类缺陷的后果是"代理看不到参数 ⇒ 只能猜/反复试错", 光看回包发现不了。
  ② **行为层**(真机调用): 描述/必填改完后, 实际调用必须与之一致 —— 尤其:
     · `browser_vip_fingerprint_ssl` 传未知 tls 值必须**明确失败**(修正前会静默回退成不限制却回 success);
     · `browser_fill_attr_get` 省略 attribute 必须**成功**(修正前 schema 把它标成必填, 与描述自相矛盾);
     · `browser_vip_enable_js_env` 不带 confirm 必须给出**可行动拒绝**(它现在在 schema 里可见了)。
     注意: **不会**用 confirm=true 真去启用 JS 环境(实测会破坏本会话 CDP 通道), 那是刻意保留的闸门。

用法: py -3 _audit\verify_schema_audit_fixes.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


def tools():
    d = json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())
    return {t["name"]: t for t in d.get("tools", [])}


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
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


T = tools()
print('== ① 声明层: schema 必须暴露实现真读的参数 ==')


def props(name):
    return set(((T.get(name, {}).get("inputSchema") or {}).get("properties") or {}).keys())


def required(name):
    return set(((T.get(name, {}).get("inputSchema") or {}).get("required") or []))


rec("browser_vip_enable_js_env 声明了 confirm(实现真读)",
    "confirm" in props("browser_vip_enable_js_env"), sorted(props("browser_vip_enable_js_env")))
rec("browser_vip_touch_cancel 声明了 x/y(实现真读)",
    {"x", "y"} <= props("browser_vip_touch_cancel"), sorted(props("browser_vip_touch_cancel")))
rec("browser_fill_attr_get 的必填只有 selector(描述说可省略 attribute)",
    required("browser_fill_attr_get") == {"selector"}, sorted(required("browser_fill_attr_get")))
rec("browser_fill_attr_set 的必填含 attribute/value(实现硬必填)",
    {"selector", "attribute", "value"} <= required("browser_fill_attr_set"),
    sorted(required("browser_fill_attr_set")))
rec("browser_fill_select 的必填含 value(实现硬必填)",
    {"selector", "value"} <= required("browser_fill_select"), sorted(required("browser_fill_select")))
rec("browser_set_preference 的必填含 value(实现硬必填)",
    {"name", "value"} <= required("browser_set_preference"), sorted(required("browser_set_preference")))
rec("browser_vip_execute_js_context 的必填含 code(实现唯一硬必填)",
    "code" in required("browser_vip_execute_js_context"), sorted(required("browser_vip_execute_js_context")))

print('\n== ② 声明层: 描述必须与实现事实一致(不再承诺做不到的事) ==')
d_run = T.get("browser_get_run_style", {}).get("description", "")
rec("run_style 描述已去掉「恒为 0」错误结论",
    ("1(谷歌)" in d_run) and ("已被实测推翻" in d_run) and ("故 runtime_style 当前恒为 0" not in d_run),
    d_run[-70:])
d_cache = T.get("browser_get_global_cache_dir", {}).get("description", "")
rec("cache_dir 描述如实说明真值来源(类库 getter 编译不过 + cache_dir_source)",
    ("cache_dir_source" in d_cache) and ("编译不过" in d_cache), d_cache[:70])
d_msg = T.get("browser_send_message", {}).get("description", "")
rec("send_message 描述如实说明实际是广播到渲染进程",
    ("渲染进程" in d_msg) and ("恒失败" in d_msg), d_msg[:70])
d_emul = T.get("browser_vip_touch_emulation", {}).get("description", "")
rec("touch_emulation 描述写清 enable 缺省=false 会关闭已开启的转换",
    ("enable 缺省视为 false" in d_emul) or ("enable 缺省" in d_emul), d_emul[-70:])

print('\n== ③ 行为层: 未知 tls 值必须明确失败(修正前是静默假成功) ==')
e1, t1 = call("browser_vip_fingerprint_ssl", {"tls_min": 999})
rec("非法 tls_min 返回失败(不再回 success)", e1, t1[:80])
rec("失败文案列出支持值(可行动)", ("769" in t1) and ("792" in t1) and ("0(不限制)" in t1), t1[:100])
e2, t2 = call("browser_vip_fingerprint_ssl", {"tls_max": 12345})
rec("非法 tls_max 同样被拒", e2 and "非法 tls_max" in t2, t2[:80])

print('\n== ④ 行为层: attr_get 省略 attribute 必须成功(与新的必填表一致) ==')
_e3, t3 = call("browser_execute_js", {"code": "document.title"})
e4, t4 = call("browser_fill_attr_get", {"selector": "h1"})
rec("browser_fill_attr_get {selector} 成功(取 textContent)", not e4, t4[:80])

print('\n== ⑤ 行为层: vip_enable_js_env 不带 confirm 给可行动拒绝 ==')
e5, t5 = call("browser_vip_enable_js_env", {"enable": True})
rec("不带 confirm 被拒(闸门仍在)", e5, t5[:80])
rec("拒绝文案点名 confirm(代理据此一次补参即可)", "confirm" in t5, t5[:100])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
