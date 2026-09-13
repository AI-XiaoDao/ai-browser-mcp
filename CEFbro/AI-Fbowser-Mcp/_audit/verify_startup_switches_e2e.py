# -*- coding: utf-8 -*-
r"""端到端验收: 改 linker 配置 → 重启 → 用 browser_startup_args 核对开关是否**真的**落到内核命令行。

三组判别:
  A. 合法规格: enable_cross_frame / disable_proxy / startup_switches{lang, force-device-scale-factor}
     -> applied_switches 必须出现这些名字, 且 command_line_raw 里必须能看到 --force-device-scale-factor=1
  B. 非法值:   disable-features 里塞非法字符 -> 必须进 rejected_switches(不静默丢弃)
  C. 白名单外的名: 一律忽略(白名单即契约) —— 只核对其**不出现**在 command_line_raw 里
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKER_CFG = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker', 'mcp_config.json')
BASE = "http://127.0.0.1:9222"
R = []


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


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:400]) if detail else ''))


def write_cfg(patch):
    raw = open(LINKER_CFG, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf')
    txt = raw.decode('utf-8')
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    d = json.loads(txt)
    d.update(patch)
    body = json.dumps(d, ensure_ascii=False, indent=2).replace('\n', term)
    with open(LINKER_CFG, 'wb') as f:
        f.write(body.encode('utf-8'))
    json.loads(open(LINKER_CFG, 'rb').read().decode('utf-8'))


def restart():
    print('   -- 重启进程(loop.py) --')
    p = subprocess.run([sys.executable, os.path.join(ROOT, '_audit', 'loop.py')],
                       cwd=ROOT, capture_output=True)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    ok = '[启动] 就绪' in out
    print('      重启%s' % ('成功' if ok else '可能失败'))
    if not ok:
        print('      ' + out[-400:])
    time.sleep(1.0)
    return ok


print('== A. 写入合法规格 + 非法值 + 白名单外名, 然后重启 ==')
write_cfg({
    "enable_cross_frame": True,
    "disable_proxy": True,
    "startup_switches": {
        "lang": "en-US",
        "force-device-scale-factor": "1",
        "disable-features": "Bad Feature!!",
        "not-in-whitelist": "x",
    },
})
restart()

e, t = call("browser_startup_args", {})
print('   回执: %s' % t[:900])
try:
    d = json.loads(t)
except Exception:
    d = {}
applied = d.get('applied_switches', '')
rawline = d.get('command_line_raw', '')
rec('A1 cmdline_available = 真(命令行对象可用)', d.get('cmdline_available') is True, d.get('cmdline_available'))
rec('A2 applied_switches 含 enable_cross_frame;', 'enable_cross_frame;' in applied, applied)
rec('A3 applied_switches 含 disable_proxy;', 'disable_proxy;' in applied, applied)
rec('A4 applied_switches 含 lang; 与 force-device-scale-factor;',
    'lang;' in applied and 'force-device-scale-factor;' in applied, applied)
rec('A5 ★内核命令行里出现 --force-device-scale-factor=1(名值表真的落到内核)',
    '--force-device-scale-factor=1' in rawline, rawline[-260:])
rec('A6 内核命令行里出现 --lang=en-US(覆盖了类库默认的 --lang=zh-CN)',
    '--lang=en-US' in rawline, rawline[-200:])
rec('B1 非法值进了 rejected_switches(不静默丢弃)',
    'disable-features' in d.get('rejected_switches', ''), d.get('rejected_switches'))
rec('C1 白名单外的名一律未下发到内核',
    'not-in-whitelist' not in rawline and 'not-in-whitelist' not in applied, applied)

print('\n== D. 恢复默认(false/{}) 再重启, 回执应回到"没应用任何开关" ==')
write_cfg({"enable_cross_frame": False, "disable_proxy": False, "startup_switches": {}})
restart()
e, t = call("browser_startup_args", {})
try:
    d2 = json.loads(t)
except Exception:
    d2 = {}
rec('D1 恢复后 applied_switches 为空', d2.get('applied_switches') == '', d2.get('applied_switches'))
rec('D2 恢复后命令行里不再有 --force-device-scale-factor',
    '--force-device-scale-factor' not in d2.get('command_line_raw', ''), d2.get('command_line_raw', '')[-160:])
rec('D3 恢复后 enable_cross_frame 回报为假', d2.get('enable_cross_frame') is False, d2.get('enable_cross_frame'))

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
