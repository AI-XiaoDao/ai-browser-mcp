# -*- coding: utf-8 -*-
"""修正 event_add.py 生成的事件覆盖中与类库不一致之处 (由 event_sig_verify2.py 查出)。

问题 1: 13 个逻辑型事件漏写 `类型 = 逻辑型` -> 方法内 `返回 (假)` 在火山中会编译报错。
问题 2: 4 个事件的参数表与类库不符 (个数/类型)。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

BOOL_FIX = [
    "浏览器_从标签打开地址", "浏览器_光标被改变", "浏览器_即将运行快捷菜单命令",
    "浏览器_工具栏被改变", "浏览器_按下某键后", "浏览器_自动调整尺寸",
    "浏览器_菜单被点击", "浏览器_菜单被调用", "浏览器_请求焦点",
    "浏览器_选择客户端证书", "渲染_收到消息",
    "渲染_VIP_WebSocket客户端_接收数据", "渲染_VIP_WebSocket客户端_发送数据",
]

# 方法名 -> 正确的参数行列表(严格照抄类库)
PARAM_FIX = {
    "浏览器_即将创建主框架Document": [
        '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    ],
    "浏览器_即将连接框架": [
        '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
        '    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">',
        '    参数 是否为主框架 <类型 = 逻辑型 @输出名 = "IsMainFrame">',
    ],
    "渲染_VIP_WebSocket客户端_接收数据": [
        '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
        '    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">',
        '    参数 websocket客户端 <类型 = 类_FBrowserVIP_WebSocket客户端 @输出名 = "WSClient">',
        '    参数 数据长度 <类型 = 整数 @输出名 = "DataLength">',
        '    参数 数据 <类型 = 字节集类 @输出名 = "Data">',
    ],
    "渲染_VIP_WebSocket客户端_发送数据": [
        '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
        '    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">',
        '    参数 websocket客户端 <类型 = 类_FBrowserVIP_WebSocket客户端 @输出名 = "WSClient">',
        '    参数 数据长度 <类型 = 整数 @输出名 = "DataLength">',
        '    参数 数据 <类型 = 字节集类 @输出名 = "Data">',
    ],
}

files = {}
for f in ("MCP_BrowserEvents.wsv", "main.wsv"):
    p = os.path.join(SRC, f)
    files[f] = io.open(p, encoding="utf-8").read().split("\n")

stat = {"bool": 0, "param": 0}

for fname, lines in files.items():
    i = 0
    while i < len(lines):
        s = lines[i]
        m = re.match(r'\s*方法\s+([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*<(.*)$', s)
        if not m:
            i += 1
            continue
        name = m.group(1)
        # --- 修正 1: 补 类型 = 逻辑型 ---
        if name in BOOL_FIX:
            if "类型 = 逻辑型" not in s:
                lines[i] = re.sub(r'(方法\s+%s\s*<公开)\s+(@虚拟方法)' % re.escape(name),
                                  r'\1 类型 = 逻辑型 \2', s)
                stat["bool"] += 1
        # --- 修正 2: 重写参数行 ---
        if name in PARAM_FIX:
            j = i + 1
            # 跳过声明跨行的剩余部分
            buf = s
            while buf.count("<") > buf.count(">") and j < len(lines):
                buf += lines[j]
                j += 1
            # 收集并替换 参数 行
            k = j
            old_from = None
            old_to = None
            while k < len(lines) and lines[k].strip().startswith("参数"):
                if old_from is None:
                    old_from = k
                old_to = k
                k += 1
            if old_from is not None:
                lines[old_from:old_to + 1] = PARAM_FIX[name]
                stat["param"] += 1
        i += 1

for fname, lines in files.items():
    p = os.path.join(SRC, fname)
    raw = io.open(p, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    nl = "\r\n" if raw.count(b"\r\n") == raw.count(b"\n") and raw.count(b"\r\n") else "\n"
    out = nl.join(lines)
    io.open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))
    print("%s 写回完成" % fname)

print("补 类型 = 逻辑型: %d 处" % stat["bool"])
print("重写参数表: %d 处" % stat["param"])
