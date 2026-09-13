# -*- coding: utf-8 -*-
r"""验证第132轮: ①全量扫描 MISSING 归零(geolocation 的 latitude/longitude 已声明);
             ②`browser_fingerprint {action:geolocation, lat:…, lng:…}` 的**别名路径**真被接受。

用法: py -3 _audit\verify_round132.py
"""
import json
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


print('== ① 全量扫描: MISSING 必须为 0(闭包分析开) ==')
p = subprocess.run([sys.executable, os.path.join(ROOT, '_audit', '_show_branch_params.py'),
                    '--brief', '--closure'],
                   cwd=os.path.join(ROOT, '_audit'), capture_output=True, text=True,
                   encoding='utf-8', errors='replace')
out = (p.stdout or '') + (p.stderr or '')
miss = [ln for ln in out.splitlines() if 'MISSING=[' in ln]
tail = [ln for ln in out.splitlines() if ln.startswith('-- 扫描')]
print('   %s' % (tail[0] if tail else '(无汇总行)'))
for ln in miss:
    print('   !! %s' % ln)
rec("全量 323 工具 MISSING=0", not miss, "%d 条残留" % len(miss))

print('\n== ② 别名路径真被接受(实现两者都读) ==')
e1, t1 = call("browser_fingerprint", {"action": "geolocation", "lat": 31.23, "lng": 121.47})
rec("用 lat/lng 调 geolocation 成功(不再静默忽略)", (not e1) and ("定位" in t1), t1[:90])
e2, t2 = call("browser_fingerprint", {"action": "geolocation", "latitude": 39.9, "longitude": 116.4})
rec("用 latitude/longitude 调 geolocation 成功(原写法保持可用)", (not e2) and ("定位" in t2), t2[:90])
e3, t3 = call("browser_fingerprint", {"action": "count"})
rec("指纹族其他 action 未受影响(回归)", not e3, t3[:70])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
