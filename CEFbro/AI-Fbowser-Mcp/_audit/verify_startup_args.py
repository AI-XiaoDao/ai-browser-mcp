# -*- coding: utf-8 -*-
"""验收 browser_startup_args: 存的开关**是否真的进了 CEF 命令行**。

判据用 `--user-agent=<独特串>` 做**可判别、不可覆盖**的观测(读 navigator.userAgent):
  T1 基线: 未配置任何开关 → UA 不含探针串
  T2 action=set 写入 --user-agent=McpStartupProbe/9.9 → 响应必须说明"需重启"
  T3 重启应用 → UA **必须**含探针串(证明开关真的在 CEF 初始化前被应用了)
  T4 action=list → 如实列出 1 个开关与文件路径
  T5 action=clear + 重启 → UA 必须**恢复**为不含探针串(反向对照: 排除"UA 本来就带"的可能)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
PROBE = "McpStartupProbe/9.9"
res = []


def call(name, args, timeout=45):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:95]))


def ua():
    e, t, _ = call("browser_execute_js", {"code": "String(navigator.userAgent)"})
    return (None if e else t)


def restart():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            time.sleep(4.5)
            return True
        except Exception:
            pass
    return False


def find_args_file():
    for base in (os.path.dirname(EXE), ROOT):
        p = os.path.join(base, "chromium_args.txt")
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(EXE), "chromium_args.txt")


print("== 0) 干净起点: 清掉可能残留的开关文件 ==")
f = find_args_file()
if os.path.exists(f):
    os.remove(f)
    print("  已删除残留: %s" % f)
if not restart():
    print("  启动失败"); sys.exit(2)

print("\n== T1 基线: UA 不应含探针串 ==")
u1 = ua()
rec("基线 UA 不含探针串", bool(u1) and PROBE not in u1, str(u1)[:80])

print("\n== T2 action=set 写入开关 ==")
e, t, dt = call("browser_startup_args", {"action": "set", "args": "--user-agent=" + PROBE})
rec("写入成功", not e, t.replace("\n", " ")[:100])
rec("响应明确要求重启才生效", "重启" in t, t.replace("\n", " ")[:110])

print("\n== T3 重启后 UA 应含探针串(证明开关真的进了 CEF) ==")
if not restart():
    print("  启动失败"); sys.exit(2)
u3 = ua()
rec("重启后 UA 含探针串", bool(u3) and PROBE in u3, str(u3)[:110])
rec("开关文件已落盘", os.path.exists(f), f)

print("\n== T4 action=list 如实反映 ==")
e, t, dt = call("browser_startup_args", {"action": "list"})
rec("list 成功且含探针开关", (not e) and (PROBE in t), t.replace("\n", " ")[:110])

print("\n== T5 反向对照: clear + 重启后 UA 必须恢复 ==")
e, t, dt = call("browser_startup_args", {"action": "clear"})
rec("clear 成功", not e, t.replace("\n", " ")[:90])
if not restart():
    print("  启动失败"); sys.exit(2)
u5 = ua()
rec("重启后 UA 不再含探针串(排除 UA 本来就带)", bool(u5) and PROBE not in u5, str(u5)[:110])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
