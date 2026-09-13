# -*- coding: utf-8 -*-
"""决定性诊断: CEF 到底有没有调用那两个资源回调?

做法: 用**捕获 stderr** 的方式启动进程(控制台输出走 stderr), 然后:
  1) 加一个 block 规则 -> 触发若干次导航
  2) 读 stderr 日志, 找这些标志行:
       "[MCP] 资源Hook已激活, 规则:"    <- 浏览器_获取资源处理器 被调用
       "[MCP] 手写篡改已挂载: ..."      <- 浏览器_获取资源过滤器 命中并挂上了过滤器
  三种可能的结论:
      两个都没有          -> CEF 根本没调用回调(重写未生效/未绑定)
      只有"已激活"        -> 回调被调用但规则没匹配上(匹配/存储侧问题)
      出现"已挂载"        -> 回调与匹配都正常, 问题在**过滤器实现**没真正改写响应体
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
LOG = os.path.join(ROOT, '_audit', '_stderr_diag.log')
URL = "https://example.com/?diag=1"


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
if os.path.exists(LOG):
    os.remove(LOG)
logf = open(LOG, 'wb')
p = subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=logf, stderr=subprocess.STDOUT)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass

call("browser_navigate", {"url": URL, "wait_for_load": True})
call("browser_intercept", {"action": "clear"})
print("== 加 block 规则 ==")
print("   %s" % call("browser_intercept", {"action": "block", "url": "example.com"})[1][:140])
call("browser_navigate", {"url": URL, "wait_for_load": True})
time.sleep(0.5)
call("browser_reload", {})
time.sleep(1.5)

e, t = call("browser_evaluate",
            {"code": "(document.body?document.body.innerText:'').slice(0,80)"}, 40)
print("== 页面正文 ==")
print("   %r" % t.strip()[:100])

time.sleep(0.5)
logf.close()
time.sleep(0.3)
raw = open(LOG, 'rb').read()
try:
    txt = raw.decode('gbk', errors='replace')
except Exception:
    txt = raw.decode('utf-8', errors='replace')

print("\n== stderr 日志中的关键标志 ==")
for key in ('资源Hook已激活', '手写篡改已挂载', '资源拦截Hook已预加载', '浏览器创建完毕'):
    n = txt.count(key)
    print("   %-26s 出现 %d 次" % (key, n))
print("\n== 日志里含 'Hook' 或 '篡改' 的行(最多 20 行) ==")
shown = 0
for l in txt.split('\n'):
    if ('Hook' in l or '篡改' in l or 'hook' in l) and shown < 20:
        print("   %s" % l.strip()[:160])
        shown += 1
if shown == 0:
    print("   (无)")
print("\n日志总长度 %d 字符; 文件: %s" % (len(txt), LOG))
try:
    p.terminate()
except Exception:
    pass
