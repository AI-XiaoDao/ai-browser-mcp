# -*- coding: utf-8 -*-
"""本轮(事件覆盖扩展)核对: 开关声明 / 事件方法落位 / 逻辑型返回 / 开关接线。"""
import io
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
NEWSW = ["是否监控菜单事件", "是否监控快捷菜单", "是否监控导航意图", "是否监控界面细节",
         "是否监控插件生命周期", "是否监控启动流程", "是否监控渲染细节", "是否监控WebSocket渲染"]
NEWEV = """浏览器_即将打开菜单 浏览器_菜单被调用 浏览器_菜单被点击 浏览器_菜单被关闭
浏览器_即将运行快捷菜单命令 浏览器_即将取消快捷菜单 浏览器_从标签打开地址 浏览器_处理协议请求
浏览器_即将创建主框架Document 浏览器_工具栏被改变 浏览器_光标被改变 浏览器_自动调整尺寸
浏览器_渲染视图 浏览器_拖拽区域改变 浏览器_选择客户端证书 浏览器_按下某键后 浏览器_请求焦点
浏览器_JS重置对话框 浏览器_JS对话框关闭 浏览器_即将连接框架
请求环境初始化完毕 即将处理命令行 浏览器_即将启动子进程 浏览器_即将启动消息调度
渲染_即将初始化WebKit 渲染_即将创建V8环境 渲染_收到消息 渲染_载入状态被改变 渲染_载入开始
渲染_载入结束 扩展插件_创建成功 扩展插件_创建失败 扩展插件_载入成功 扩展插件_卸载成功
渲染_VIP_WebSocket客户端_创建 渲染_VIP_WebSocket客户端_关闭 渲染_VIP_WebSocket客户端_连接服务器
渲染_VIP_WebSocket客户端_接收数据 渲染_VIP_WebSocket客户端_发送数据""".split()
BOOL_EV = """浏览器_从标签打开地址 浏览器_光标被改变 浏览器_即将运行快捷菜单命令 浏览器_工具栏被改变
浏览器_按下某键后 浏览器_自动调整尺寸 浏览器_菜单被点击 浏览器_菜单被调用 浏览器_请求焦点
浏览器_选择客户端证书 渲染_收到消息 渲染_VIP_WebSocket客户端_接收数据
渲染_VIP_WebSocket客户端_发送数据""".split()

TXT = {}
for f in os.listdir(SRC):
    if f.endswith(".wsv") and ".~vbak" not in f:
        TXT[f] = io.open(os.path.join(SRC, f), encoding="utf-8").read()

server = TXT["MCP_Server.wsv"]
browser = TXT["MCP_BrowserEvents.wsv"]
main = TXT["main.wsv"]
kernel = TXT["MCP_Kernel.wsv"]

ok = 0
tot = 0

print("=" * 100)
print("A. 8 个新监控开关")
print("=" * 100)
for s in NEWSW:
    tot += 1
    decl = ('变量 %s <公开 静态 类型 = 逻辑型' % s) in server
    used = (s in kernel) or (s in browser) or (s in main)
    if decl and used:
        ok += 1
    print("  %s %-24s 声明=%s 被引用=%s" % ("OK " if (decl and used) else "!! ", s, decl, used))

print()
print("=" * 100)
print("B. 39 个事件方法落位 + 逻辑型返回")
print("=" * 100)
miss = []
for n in NEWEV:
    tot += 1
    where = None
    for f, t in TXT.items():
        if re.search(r'方法\s+%s\s*<' % re.escape(n), t):
            where = f
            break
    if not where:
        miss.append(n)
        print("  !! %-34s 未找到" % n)
        continue
    ok += 1
print("  落位: %d / %d   (分布在 %s)" % (len(NEWEV) - len(miss), len(NEWEV), "MCP_BrowserEvents.wsv/main.wsv"))

print()
print("=" * 100)
print("C. 逻辑型事件必须 类型 = 逻辑型 且末尾 返回 (假)")
print("=" * 100)
def method_body(text, name):
    """用花括号配对取出方法体 (跳过 参数 行, 从第一个 '{' 起配对)。"""
    m = re.search(r'方法\s+%s\s*<[^>]*>' % re.escape(name), text)
    if not m:
        return None
    j = text.find("{", m.end())
    if j < 0:
        return None
    depth, i, in_str = 0, j, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[j:i + 1]
        i += 1
    return None


for n in BOOL_EV:
    tot += 1
    where = None
    for f, t in TXT.items():
        if re.search(r'方法\s+%s\s*<' % re.escape(n), t):
            where = (f, t)
            break
    if not where:
        print("  !! %-34s 未找到" % n)
        continue
    f, t = where
    attrs = re.search(r'方法\s+%s\s*<([^>]*)>' % re.escape(n), t).group(1)
    has_type = "类型 = 逻辑型" in attrs
    body = method_body(t, n)
    has_ret = bool(body and "返回 (假)" in body)
    good = has_type and has_ret
    if good:
        ok += 1
    print("  %s %-34s 类型=逻辑型:%s 返回假:%s (%s)"
          % ("OK " if good else "!! ", n, has_type, has_ret, f))

print()
print("=" * 100)
print("D. 全事件流开关已接线 (enable + disable 各 8 项)")
print("=" * 100)
tot += 1
en = all(("MCP命令服务器.%s = 真" % s) in kernel for s in NEWSW)
dis = all(("MCP命令服务器.%s = 假" % s) in kernel for s in NEWSW)
if en and dis:
    ok += 1
print("  %s browser_kernel_events_all: enable 全含=%s  disable 全含=%s" % ("OK " if (en and dis) else "!! ", en, dis))

print()
print("★ 通过 %d / %d" % (ok, tot))
