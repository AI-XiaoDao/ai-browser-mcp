# -*- coding: utf-8 -*-
r"""验证第127轮第二批: 补齐的"实现真读却未声明"的参数 + 两处与实现相反的描述。

声明层断言(tools/list) + 一条行为层断言(dom_set_value 的 allow_empty 原本是死路):
  · allow_empty / auto_enable / inject_id / url_pattern / view_source.max_chars 必须出现在 schema;
  · touch 三件套必须声明 kernel(与 mouse_* 家族一致);
  · view_source / file_dialog 描述必须不再承诺做不到的事(不打开 view-source / 不弹真对话框);
  · 行为层: `browser_dom_set_value {selector}`(不带 value) 的拒绝文案必须指向一个**已声明**的参数。

用法: py -3 _audit\verify_missing_params.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


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
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:108]))


T = {t["name"]: t for t in json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())["tools"]}


def props(name):
    return set(((T.get(name, {}).get("inputSchema") or {}).get("properties") or {}).keys())


def desc(name):
    return T.get(name, {}).get("description", "")


print('== ① 补齐的参数必须出现在 schema(代理才看得到) ==')
for tool, key in (("browser_dom_set_value", "allow_empty"), ("browser_network", "auto_enable"),
                  ("browser_inject", "inject_id"), ("browser_reverse_hook", "url_pattern"),
                  ("browser_view_source", "max_chars")):
    rec("%s 声明了 %s" % (tool, key), key in props(tool), sorted(props(tool)))
for tool in ("browser_touch_press", "browser_touch_move", "browser_touch_release"):
    rec("%s 声明了 kernel(与 mouse_* 家族一致)" % tool, "kernel" in props(tool), sorted(props(tool)))

print('\n== ② 描述不得再承诺做不到的事 ==')
rec("view_source 描述写明不打开 view-source 标签", ("不会" in desc("browser_view_source")) and ("view-source" in desc("browser_view_source")),
    desc("browser_view_source")[:100])
rec("file_dialog 描述写明不弹真对话框", "不会弹出真实的系统文件对话框" in desc("browser_file_dialog"),
    desc("browser_file_dialog")[:100])

print('\n== ③ 行为层: dom_set_value 的清空路径不再是死路 ==')
e1, t1 = call("browser_execute_js", {"code": "'ok'"})
e2, t2 = call("browser_dom_set_value", {"selector": "h1"})
rec("不带 value 被拒绝(守卫仍在)", e2, t2[:70])
rec("拒绝文案指向的 allow_empty **已在 schema 里声明**",
    ("allow_empty" in t2 or "value" in t2) and ("allow_empty" in props("browser_dom_set_value")),
    "schema=%s | msg=%s" % (sorted(props("browser_dom_set_value")), t2[:60]))

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
