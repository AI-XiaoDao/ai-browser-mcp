# -*- coding: utf-8 -*-
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

print("=" * 100)
print("1. 欢迎页 HTML 里是否有 自动跳转/刷新 (解释两次 load_end)")
print("=" * 100)
srv = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
in_html = 0
for i, l in enumerate(srv):
    for pat, tag in [(r"location\.reload", "location.reload"), (r"http-equiv", "meta refresh"),
                     (r"location\.href\s*=", "location.href 赋值"), (r"window\.location", "window.location"),
                     (r"setInterval", "setInterval"), (r"setTimeout", "setTimeout")]:
        if re.search(pat, l):
            print("   %6d| [%s] %s" % (i + 1, tag, l.strip()[:130]))
            in_html += 1
print("   命中 %d 处" % in_html)

print()
print("=" * 100)
print("2. 取欢迎页HTML 的结构 (是否读文件/index.html)")
print("=" * 100)
start = next(k for k, l in enumerate(srv) if "方法 取欢迎页HTML" in l)
for k in range(start, min(start + 36, len(srv))):
    print("%6d| %s" % (k + 1, srv[k][:150]))

print()
print("=" * 100)
print("3. 浏览器_创建完毕 里是否还有一次导航")
print("=" * 100)
ev = io.open(os.path.join(SRC, "MCP_BrowserEvents.wsv"), encoding="utf-8").read().split("\n")
s = next(k for k, l in enumerate(ev) if "方法 浏览器_创建完毕" in l)
for k in range(s, min(s + 60, len(ev))):
    t = ev[k]
    if re.search(r"载入地址|导航|欢迎|待创建|恢复", t):
        print("%6d| %s" % (k + 1, t.strip()[:150]))

print()
print("=" * 100)
print("4. 欢迎页地址 取的是什么")
print("=" * 100)
for k in range(150, 205):
    print("%6d| %s" % (k + 1, srv[k][:150]))
