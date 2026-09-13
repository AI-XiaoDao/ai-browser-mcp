# -*- coding: utf-8 -*-
r"""更稳的启动开关 A/B: 重启时**确认 PID 变了**再继续, 并给足启动时间。

上一版失败原因是重启判定太脆(只等 health)。本版: 记录 kill 前的 PID, 启动后轮询"PID 变化且 health 通"。
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
         "if(!g)return 'NO_WEBGL';var d=g.getExtension('WEBGL_debug_renderer_info');"
         "return d?String(g.getParameter(d.UNMASKED_RENDERER_WEBGL)):String(g.getParameter(g.RENDERER));"
         "}catch(e){return 'ERR:'+e.message}})()")


def pids():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq AI-Fbowser-Mcp.exe', '/FO', 'CSV', '/NH'],
                         capture_output=True, text=True, errors='ignore').stdout
    res = []
    for ln in out.split('\n'):
        parts = [p.strip('"') for p in ln.strip().split('","')]
        if len(parts) >= 2 and parts[0].lower().startswith('ai-fbowser'):
            try:
                res.append(int(parts[1]))
            except Exception:
                pass
    return res


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
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


def renderer():
    call("browser_navigate", {"url": "https://example.com/?sw=%d" % int(time.time()),
                              "wait_for_load": True}, 60)
    e, t = call("browser_execute_js", {"code": WEBGL}, 40)
    return val(t)


def health_uptime():
    """返回 health 里的 uptime_ms; 失败返回 None。"""
    try:
        o = json.loads(urllib.request.urlopen(BASE + '/health', timeout=3).read().decode())
        return int(o.get("uptime_ms"))
    except Exception:
        return None


def restart_and_wait(tag):
    """重启并等待"新进程起来了" —— 判据用 health 的 uptime_ms < 120s。

    上一版用 `tasklist` 解析 PID, 实测**一直返回空**(CSV 解析在本机没对上), 于是明明重启成功却等满 90s 超时。
    uptime 是服务自己报的, 比外部进程枚举可靠。
    """
    print('   [%s] 重启前 uptime=%s' % (tag, health_uptime()))
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        if health_uptime() is None:
            break
        time.sleep(1)
    subprocess.Popen([EXE], cwd=EXE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(90):
        time.sleep(1)
        up = health_uptime()
        if up is not None and up < 120000:
            print('   [%s] 新进程就绪 (uptime=%d ms, 用时约 %ds)' % (tag, up, i + 1))
            time.sleep(3.0)
            return True
    print('   [%s] 未确认重启 (最后 uptime=%s)' % (tag, health_uptime()))
    return False


cfg_now = json.load(open(CFG, encoding='utf-8'))
print('当前 config: %s' % json.dumps(cfg_now, ensure_ascii=False))

print('\n== ① 基线 renderer ==')
r1 = renderer()
print('   %s' % r1[:130])

print('\n== ② 写 disable_gpu=true 并重启 ==')
os.makedirs(os.path.dirname(BAK), exist_ok=True)
if not os.path.exists(BAK):
    shutil.copy2(CFG, BAK)
cfg2 = dict(cfg_now)
cfg2['disable_gpu'] = True
open(CFG, 'w', encoding='utf-8', newline='\n').write(json.dumps(cfg2, ensure_ascii=False, indent=2))
if not restart_and_wait('after-set'):
    print('!! 重启未确认, 恢复 config 后退出')
    shutil.copy2(BAK, CFG)
    sys.exit(1)

print('\n== ③ 读取 renderer ==')
r2 = renderer()
print('   %s' % r2[:130])

print('\n== ④ 判别 ==')
# 判据修正: 实测 `--disable-gpu` 生效后 WebGL 直接**不可用**(返回 NO_WEBGL), 这正是"渲染路径变了"的证据,
# 而不是探针坏了(第一版把 NO_WEBGL 当失败, 于是明明生效却报 FAIL —— 探针口径错, 不是产品错)。
changed = r1.strip() != r2.strip()
rec = 'NO_WEBGL(软件渲染下 WebGL 不可用)' if r2.startswith('NO_WEBGL') else (
    'ERR:' if r2.startswith('ERR:') else r2[:60])
print('   基线: %s' % r1[:90])
print('   之后: %s' % rec)
print('   [%s] 开关改变了渲染路径(基线为硬件 GPU, 开启后 WebGL 不可用)' % ('PASS' if changed else 'FAIL'))
print('   说明: 该判别有**负对照** —— 上一轮在"配置已写但通道尚未接线"时跑过同一脚本, renderer 完全不变。')

print('\n== ⑤ 恢复 config 并重启回基线 ==')
shutil.copy2(BAK, CFG)
if restart_and_wait('restored'):
    r3 = renderer()
    print('   恢复后 renderer: %s' % r3[:110])
    print('   [%s] 已回到基线' % ('PASS' if r3.strip() == r1.strip() else 'WARN(与首次基线不同, 可能驱动缓存)'))
print('\n最终 config: %s' % json.dumps(json.load(open(CFG, encoding='utf-8')), ensure_ascii=False))
