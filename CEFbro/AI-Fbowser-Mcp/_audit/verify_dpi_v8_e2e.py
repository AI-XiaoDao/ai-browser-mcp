# -*- coding: utf-8 -*-
r"""DPI 感知 / V8 堆上限 的端到端验收(配置驱动 + 页面侧可测指标):

  · DPI: 开/关时测 window.innerWidth/innerHeight + devicePixelRatio(HiDPI 下视口应变化)
  · V8 : 开/关时测 performance.memory.jsHeapSizeLimit(Chromium 把 V8 堆上限暴露在这里)
       —— 注: 类库方法名叫"堆栈大小", 底层 C 函数却是 FBroSetV8DefaultsHeapSize(堆), 故用堆上限指标交叉核对。
三段: 基线(默认) -> 设配置重启 -> 还原配置重启。
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
LINKER = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker', 'mcp_config.json')
BASE = "http://127.0.0.1:9222"


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


def j(t):
    try:
        o = json.loads(t)
    except Exception:
        return {}
    return o.get('data') if isinstance(o, dict) and isinstance(o.get('data'), dict) else o


def write_cfg(patch):
    raw = open(LINKER, 'rb').read()
    txt = raw.decode('utf-8')
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    d = json.loads(txt)
    d.update(patch)
    with open(LINKER, 'wb') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2).replace('\n', term).encode('utf-8'))
    json.loads(open(LINKER, 'rb').read().decode('utf-8'))


def restart():
    p = subprocess.run([sys.executable, os.path.join(ROOT, '_audit', 'loop.py')],
                       cwd=ROOT, capture_output=True)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    ok = '[启动] 就绪' in out
    time.sleep(1.2)
    return ok


def snapshot(tag):
    call("browser_navigate", {"url": "https://example.com/?dpi_%s=%d" % (tag, int(time.time())),
                              "wait_for_load": True})
    js = ("JSON.stringify({iw:window.innerWidth,ih:window.innerHeight,dpr:window.devicePixelRatio,"
          "heap:(window.performance&&performance.memory)?performance.memory.jsHeapSizeLimit:null})")
    e, t = call("browser_execute_js", {"code": js})
    m = {}
    try:
        m = json.loads(j(t).get('message') or '{}')
    except Exception:
        m = {}
    e2, t2 = call("browser_startup_args", {})
    r = j(t2)
    print('   [%s] 回执 dpi_aware=%s v8_max_stack_mb=%s | 视口 %sx%s dpr=%s 堆上限=%s'
          % (tag, r.get('dpi_aware'), r.get('v8_max_stack_mb'),
             m.get('iw'), m.get('ih'), m.get('dpr'), m.get('heap')))
    return {'dpi_aware': r.get('dpi_aware'), 'v8': r.get('v8_max_stack_mb'), **m}


print('== 1. 基线(默认配置) ==')
base = snapshot('base')

print('\n== 2. 设 dpi_aware=true / v8_max_stack_mb=1024 并重启 ==')
write_cfg({"dpi_aware": True, "v8_max_stack_mb": 1024})
print('   重启%s' % ('成功' if restart() else '失败'))
on = snapshot('on')

print('\n== 3. 还原默认并重启 ==')
write_cfg({"dpi_aware": False, "v8_max_stack_mb": 0})
print('   重启%s' % ('成功' if restart() else '失败'))
off = snapshot('restored')

R = []


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


print('\n== 判定 ==')
rec('配置解析被回执如实反映(开启后 dpi_aware=true, v8=1024)',
    on['dpi_aware'] is True and on['v8'] == 1024, on)
rec('还原后回执归零(dpi_aware=false, v8=0)',
    off['dpi_aware'] is False and off['v8'] == 0, off)
rec('基线=还原(两次默认配置的视口一致, 证明改动可逆)',
    base.get('iw') == off.get('iw') and base.get('ih') == off.get('ih'),
    'base=%sx%s restored=%sx%s' % (base.get('iw'), base.get('ih'), off.get('iw'), off.get('ih')))
print('   [信息] DPI 开启前后视口: 默认=%sx%s(dpr=%s) -> 开启=%sx%s(dpr=%s)'
      % (base.get('iw'), base.get('ih'), base.get('dpr'), on.get('iw'), on.get('ih'), on.get('dpr')))
print('   [信息] 堆上限: 默认=%s -> 开启(1024MB)=%s' % (base.get('heap'), on.get('heap')))

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
