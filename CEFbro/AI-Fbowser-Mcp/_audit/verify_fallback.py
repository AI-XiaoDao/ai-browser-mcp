# -*- coding: utf-8 -*-
import importlib.util, sys, time
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.2)

def state(tag):
    r = {}
    e,t,_ = v4.call("browser_dom_query", {"selector":"h1"}, 40);   r["dom_query"] = "OK" if "Example Domain" in t else t.replace(chr(10)," ")[:18]
    e,t,_ = v4.call("browser_dom_rect", {"selector":"h1"}, 40);    r["dom_rect"]  = "OK" if '"width"' in t else t.replace(chr(10)," ")[:18]
    e,t,_ = v4.call("browser_get_text", {"selector":"h1"}, 40);    r["get_text"]  = "OK" if "Example Domain" in t else t.replace(chr(10)," ")[:18]
    e,t,_ = v4.call("browser_get_text", {}, 40);                   r["full_text"] = "OK" if "Example Domain" in t else t.replace(chr(10)," ")[:18]
    print("  %-22s %s" % (tag, "  ".join("%s=%s" % kv for kv in r.items())))
    return all(v == "OK" for v in r.values())

a = state("初始")
print("  [破坏 CDP] vip_enable_js_env {enable:true}")
v4.call("browser_vip_enable_js_env", {"enable":True}, 40); time.sleep(2.0)
b = state("CDP 被破坏后")
print()
print("  结论: 初始OK=%s, CDP破坏后OK=%s -> %s" % (a, b,
      "回退修复生效: CDP 坏掉后工具仍返回真值" if b else "仍失败, 需继续排查"))

print("\n=== 附带: scrape 提取(CDP 坏掉状态下) ===")
import re, json
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
e,t,resp = v4.call("browser_scrape", {"url":"https://example.com/","extract_selector":"h1","max_ms":20000}, 90)
blob = json.dumps(resp or {}, ensure_ascii=False)+t
m = re.search(r"task_\d+_\d+_\d+", blob)
tid = m.group(0) if m else None
final = t; t0=time.time()
while tid and time.time()-t0 < 40:
    if "Example Domain" in final or "超时" in final: break
    time.sleep(1)
    e2,t2,_ = v4.call("mcp_result", {"request_id":tid}, 40)
    if t2: final = t2
print("  用时 %.1fs -> %s" % (time.time()-t0, final.replace(chr(10)," ")[:150]))
print("  判定: %s" % ("PASS (返回真值)" if "Example Domain" in final else "FAIL"))
