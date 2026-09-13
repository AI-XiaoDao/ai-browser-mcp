# -*- coding: utf-8 -*-
"""最终交叉核对: 新代码引用的每个符号/类是否真的存在且可见。"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

print("=" * 100)
print("最终交叉核对 — 新代码引用的符号可见性")
print("=" * 100)
print()

allsrc = {}
for f in os.listdir(SRC):
    if f.endswith(".wsv") and ".~vbak" not in f:
        allsrc[f] = io.open(os.path.join(SRC, f), encoding="utf-8").read()

def declared(pat, files=None):
    hits = []
    for f, t in allsrc.items():
        if files and f not in files:
            continue
        for i, l in enumerate(t.split("\n")):
            if re.search(pat, l):
                hits.append((f, i + 1, l.strip()[:100]))
    return hits

CHECKS = [
    ("类 MCPStdio桥 存在", r'^类\s+MCPStdio桥\s'),
    ("MCPStdio桥.写日志 <公开 静态>", r'方法\s+写日志\s+<公开[^>]*静态'),
    ("MCPStdio桥.是否为Stdio模式 <公开 静态>", r'方法\s+是否为Stdio模式\s+<公开[^>]*静态'),
    ("变量 会话ID <公开 静态>", r'变量\s+会话ID\s+<公开[^>]*静态'),
    ("变量 服务器端口 <公开 静态>", r'变量\s+服务器端口\s+<公开[^>]*静态'),
    ("变量 服务器绑定地址 <公开 静态>", r'变量\s+服务器绑定地址\s+<公开[^>]*静态'),
    ("方法 绑定MCP服务器实例", r'方法\s+绑定MCP服务器实例\s+<公开'),
    ("方法 控制台输出", r'方法\s+控制台输出\s+<公开'),
    ("类 浏览器容器", r'^类\s+浏览器容器'),
    ("类 MCP命令服务器", r'^类\s+MCP命令服务器'),
    ("类 类_MCP_服务器事件", r'^类\s+类_MCP_服务器事件'),
    ("方法 取随机数 可用(已在本项目用过)", r'取随机数\s*\('),
    ("方法 到小写 可用", r'到小写\s*\('),
    ("方法 删首尾空 可用", r'删首尾空\s*\('),
    ("方法 读环境变量 可用", r'读环境变量\s*\('),
    ("方法 选择 可用", r'选择\s*\('),
    ("常量 HTTP_JSON内容类型", r'HTTP_JSON内容类型'),
    ("类 FBrowser_双文本数组", r'FBrowser_双文本数组'),
    ("类 FBrowser_双文本", r'FBrowser_双文本\b'),
    ("方法 加入文本成员(yyJSON)", r'\.加入文本成员\s*\('),
    ("方法 到可读文本(YYJSON格式化选项.压缩)", r'YYJSON格式化选项\.压缩'),
    ("方法 发送HttpResponse", r'\.发送HttpResponse\s*\('),
    ("方法 发送原始数据", r'\.发送原始数据\s*\('),
    ("方法 服务器.是否为空", r'服务器\.是否为空\s*\('),
]
ok = 0
for tag, pat in CHECKS:
    hits = declared(pat)
    if hits:
        ok += 1
        f, ln, txt = hits[0]
        print("  OK  %-40s %s:%d" % (tag, f, ln))
    else:
        print("  !!  %-40s 未找到" % tag)
print()
print("通过 %d / %d" % (ok, len(CHECKS)))
