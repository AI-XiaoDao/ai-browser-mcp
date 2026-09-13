# -*- coding: utf-8 -*-
r"""启动期开关通道验收(A/B 判别实验)。

判别观测量的选择: 开关只对**新进程**生效, 所以必须找一个"同一条命令、开关前后结果不同"的页面真值。
`disable_gpu` 满足: 关掉 GPU 后 Chromium 会用软件渲染, WebGL 的 UNMASKED_RENDERER 字符串会变
(通常出现 SwiftShader / Software)。而它是**同步** JS, 一次调用即可读(本项目 CDP 的 awaitPromise=false,
异步 IIFE 拿不到值, 故刻意不用 async)。

流程: ① 读基线 WebGL renderer → ② 写 config(disable_gpu=true) → ③ 重启进程 → ④ 再读 → ⑤ 断言两者不同
       → ⑥ 恢复 config 并打印"实际应用的开关"报告字段(若实现提供了的话)。
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE_DIR = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker')
EXE = os.path.join(EXE_DIR, 'AI-Fbowser-Mcp.exe')
CFG = os.path.join(EXE_DIR, 'mcp_config.json')
BAK = os.path.join(ROOT, '备份', 'mcp_config-开关实验前.json')

WEBGL = ("(function(){try{var c=document.createElement('canvas');"
         "var g=c.getContext('webgl')||c.getContext('experimental-webgl');"
         "if(!g)return 'NO_WEBGL';"
         "var d=g.getExtension('WEBGL_debug_renderer_info');"
         "return d?String(g.getParameter(d.UNMASKED_RENDERER_WEBGL)):String(g.getParameter(g.RENDERER));"
         "}catch(e){return 'ERR:'+e.message}})()")


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        j = json.loads(t)
        return str(j.get("message", j))
    except Exception:
        return t


def renderer():
    call("browser_navigate", {"url": "https://example.com/?swprobe=%d" % int(time.time()),
                              "wait_for_load": True})
    e, t = call("browser_execute_js", {"code": WEBGL})
    return val(t)


def restart():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    subprocess.Popen([EXE], cwd=EXE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
            time.sleep(4.0)
            return True
        except Exception:
            pass
    return False


print('== ① 基线(当前 config 未开任何启动开关) ==')
r1 = renderer()
print('   WebGL renderer: %s' % r1[:120])

print('\n== ② 写 config: disable_gpu=true ==')
cfg = json.load(open(CFG, encoding='utf-8'))
print('   改前: %s' % json.dumps(cfg, ensure_ascii=False))
os.makedirs(os.path.dirname(BAK), exist_ok=True)
if not os.path.exists(BAK):
    shutil.copy2(CFG, BAK)
cfg2 = dict(cfg)
cfg2['disable_gpu'] = True
open(CFG, 'w', encoding='utf-8', newline='\n').write(json.dumps(cfg2, ensure_ascii=False, indent=2))
print('   改后: %s' % json.dumps(cfg2, ensure_ascii=False))

print('\n== ③ 重启进程(开关只对新进程生效) ==')
ok = restart()
print('   重启: %s' % ('就绪' if ok else '失败'))
if not ok:
    shutil.copy2(BAK, CFG)
    sys.exit(1)

print('\n== ④ 再读 WebGL renderer ==')
r2 = renderer()
print('   开 disable_gpu 后: %s' % r2[:120])

print('\n== ⑤ 判别 ==')
same = (r1.strip() == r2.strip()) or r2.startswith('NO_WEBGL') or r2.startswith('ERR:')
print('   基线: %s' % r1[:80])
print('   之后: %s' % r2[:80])
print('   [%s] 开关确实改变了渲染路径(renderer 字符串不同)' % ('PASS' if not same else 'FAIL'))

print('\n== ⑥ 恢复 config ==')
shutil.copy2(BAK, CFG)
cfg3 = json.load(open(CFG, encoding='utf-8'))
print('   已恢复: %s' % json.dumps(cfg3, ensure_ascii=False))
# 报告字段: 若实现提供了"已应用开关", 打印出来(找不到也不算失败, 只是未实现上报)
for tool, args in (("browser_status", {}), ("browser_kernel_switches", {"action": "list"})):
    e, t = call(tool, args)
    if not e and ('switch' in t.lower() or '开关' in t):
        print('   %s -> %s' % (tool, t[:260]))
print('\n注: 恢复 config 后需再次重启才会回到基线(本脚本不自动重启, 避免影响后续测试)')
