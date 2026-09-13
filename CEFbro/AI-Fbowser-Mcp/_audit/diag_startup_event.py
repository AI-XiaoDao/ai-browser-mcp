# -*- coding: utf-8 -*-
"""把应用 stdout 接到文件跑一次, 看启动期那行回报有没有出现 —— 判定 `即将处理命令行` 到底有没有触发。

只做观测, 不改任何东西:
 1. 写入一个开关到 chromium_args.txt(经工具), 保证启动参数列表非空;
 2. 关掉应用, **带 stdout 重定向**重新启动;
 3. 打印日志里所有含"启动开关"/"AI浏览器"的行。
若一行都没有 => 该覆盖方法没有被调用(或调用发生在读文件之后), 开关自然应用不上。
"""
import io
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
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_startup_args.log")


def call(name, args, timeout=45):
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
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    return bool(rr.get("isError")), "".join(
        i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")


def start_capture():
    logf = io.open(LOG, "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                            stdout=logf, stderr=subprocess.STDOUT)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            time.sleep(4.5)
            break
        except Exception:
            pass
    return logf, proc


# 先确保有一个开关(经工具写, 顺带验证工具本身)
e, t = call("browser_startup_args", {"action": "set", "args": "--user-agent=McpStartupProbe/9.9"})
print("写入开关: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:90]))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
logf, proc = start_capture()
e, t = call("browser_execute_js", {"code": "String(navigator.userAgent)"})
print("重启后 UA: %s" % t.replace("\n", " ")[:110])
logf.flush()
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
try:
    logf.close()
except Exception:
    pass

print("\n== 启动日志中与启动开关/AI浏览器相关的行 ==")
# 注意: 项目的 控制台输出 是**按 GBK(936) 写出**的(见 MCP_服务器工具.控制台输出 的注释),
# 我却一直按 UTF-8 读 —— 于是中文全是乱码, 按中文子串搜索必然 0 命中。
# 这是一个**测量侧编码 bug**(和它对应的实现一样, 都在"编码"这件事上踩过), 故此处两种编码都试。
raw = open(LOG, "rb").read()
for enc in ("gbk", "utf-8"):
    try:
        txt = raw.decode(enc, "replace")
    except Exception:
        continue
    hits = [l for l in txt.split("\n") if ("启动开关" in l or "AI浏览器" in l)]
    if hits:
        print("  [按 %s 解码] 命中 %d 行:" % (enc, len(hits)))
        for h in hits[:20]:
            print("    %s" % h.strip()[:160])
        break
else:
    txt = raw.decode("gbk", "replace")
    hits = []
print("  (日志共 %d 字节)" % len(raw))
if not hits:
    print("\n  按 GBK 解码后的全部内容:")
    print("  " + txt.replace("\n", "\n  ")[:900])
