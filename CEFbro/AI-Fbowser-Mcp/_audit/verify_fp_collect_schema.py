# -*- coding: utf-8 -*-
r"""验证第129轮: `browser_fingerprint`(17 个) 与 `browser_collect`(4 个) 的未声明参数已补齐。

分两层:
  ① 声明层: 参数必须真的出现在 tools/list（**这条不能省** —— 上一轮踩过"改了 schema 但运行时没生效"的坑）;
  ② 行为层: 两个工具原有的 action 仍可用（回归）; 且新声明的参数传进去**不被当作未知参数拒绝**。

用法: py -3 _audit\verify_fp_collect_schema.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []
FP_EXPECT = {"min", "max", "seed", "sample_rate", "channels", "frames_per_buffer",
             "public_ip", "local_ip", "host", "disable", "offset_h", "offset_m",
             "name", "iana", "tls_min", "tls_max", "ciphers"}
CL_EXPECT = {"keyword", "limit", "clear", "max_ms"}


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
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:106]))


T = {t["name"]: t for t in json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())["tools"]}


def props(name):
    return set(((T.get(name, {}).get("inputSchema") or {}).get("properties") or {}).keys())


print('== ① 声明层: 新增参数必须真的出现在 tools/list ==')
fp = props("browser_fingerprint")
rec("browser_fingerprint 19 个参数齐备", FP_EXPECT <= fp, "缺: %s" % sorted(FP_EXPECT - fp))
rec("browser_fingerprint 保留了 action/config", {"action", "config"} <= fp, sorted(fp)[:6])
cl = props("browser_collect")
rec("browser_collect 补上 keyword/limit/clear/max_ms", CL_EXPECT <= cl, "缺: %s" % sorted(CL_EXPECT - cl))
rec("browser_collect 描述写明参数已补齐", "参数已按实现补齐" in T.get("browser_collect", {}).get("description", ""),
    T.get("browser_collect", {}).get("description", "")[:80])
rec("browser_fingerprint 描述写明参数已补齐", "参数已按实现补齐" in T.get("browser_fingerprint", {}).get("description", ""),
    T.get("browser_fingerprint", {}).get("description", "")[:80])

print('\n== ② 行为层: 回归 + 新参数被接受(不被当未知参数拒绝) ==')
e1, t1 = call("browser_fingerprint", {"action": "count"})
rec("fingerprint action=count 仍可用(回归)", not e1, t1[:80])
e2, t2 = call("browser_collect", {"action": "console_get", "keyword": "zzz-no-such-keyword", "limit": 5})
rec("collect console_get + keyword/limit 可用(回归+新参数生效)", not e2, t2[:90])
e3, t3 = call("browser_fingerprint", {"action": "count", "min": 1, "max": 2, "seed": 3,
                                     "tls_min": 0, "tls_max": 0, "ciphers": "", "disable": False,
                                     "offset_h": 0, "offset_m": 0, "name": "", "iana": "",
                                     "public_ip": "", "local_ip": "", "host": "",
                                     "sample_rate": 0, "channels": 0, "frames_per_buffer": 0})
rec("一次性传全部 17 个新参数: 不报'未知参数'(被实现接受)", not e3, t3[:80])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
