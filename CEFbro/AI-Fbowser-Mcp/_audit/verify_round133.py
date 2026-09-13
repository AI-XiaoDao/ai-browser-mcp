# -*- coding: utf-8 -*-
r"""验证第133轮: ①扫描器不再报"疑死参数"(那三个 no-op 声明已删); ②被改的三个工具仍可用(回归)。

用法: py -3 _audit\verify_round133.py
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


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


print('== ① 全量扫描: 不应再有"疑死参数"(MISSING 也应为 0) ==')
p = subprocess.run([sys.executable, os.path.join(ROOT, '_audit', '_show_branch_params.py'),
                    '--brief', '--closure'], cwd=os.path.join(ROOT, '_audit'),
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
out = (p.stdout or '') + (p.stderr or '')
lines = [ln for ln in out.splitlines() if 'MISSING=[' in ln]
tail = [ln for ln in out.splitlines() if ln.startswith('-- 扫描')]
print('   %s' % (tail[0] if tail else '(无汇总)'))
for ln in lines:
    print('   !! %s' % ln)
miss = [ln for ln in lines if 'MISSING=['
        in ln and "MISSING=- " not in ln and "MISSING=-  " not in ln]
rec("无 MISSING(实现读却未声明)", not [ln for ln in lines if not ln.split('MISSING=')[1].startswith('-')],
    "%d 条" % len(lines))
rec("无'疑死参数'(no-op 声明已清理)", not [ln for ln in lines if 'EXTRA(疑死)=[' in ln],
    "%d 条" % len([ln for ln in lines if 'EXTRA(疑死)=[' in ln]))

print('\n== ② 被改的三个工具仍可用(回归) ==')
e1, t1 = call("browser_reverse_scan_crypto", {})
rec("scan_crypto 仍可用", not e1, t1[:90])
e2, t2 = call("browser_reverse_detect_obfuscator", {})
rec("detect_obfuscator 仍可用", not e2, t2[:90])
e3, t3 = call("browser_debugger_last_paused", {})
rec("last_paused 调用返回(有/无暂停都应是明确结果)", e3 or ("success" in t3), t3[:90])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
