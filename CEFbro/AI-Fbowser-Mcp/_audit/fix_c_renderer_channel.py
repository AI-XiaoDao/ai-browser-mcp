# -*- coding: utf-8 -*-
"""实现 (C) 的推荐方案①: 让渲染侧应用事件写入页面 window.__mcp_ipc_queue。

依据:
  - 多进程模型下渲染进程的 `缓存数据库已打开` 为假 -> `记录事件日志` 自身早退, 写不进 event_log
  - 项目既有成熟通道: 渲染侧用 `框架.执行JS代码` 往 window.__mcp_ipc_queue push,
    主进程经 CDP 读回(`browser_kernel_ipc_queue` 工具即为此)
  - 参照 main.wsv:424-444 `进程间消息_收到主进程消息` 的已验证写法

策略: **纯增量** —— 保留原有 `记录应用监控事件` 调用(若主进程侧能记录则照旧),
      仅对**带 框架 参数**的事件追加一次渲染侧入队调用。不改动既有行。
"""
import io
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\main.wsv"
t = io.open(P, encoding="utf-8").read()

HELPER = '''
    # ================================================================
    # v3.2 (C) 渲染侧事件通道: 渲染进程无法访问主进程 SQLite 句柄
    # (缓存数据库已打开 在主进程为真、渲染进程为假 -> 记录事件日志 自身早退),
    # 故带框架的渲染侧事件额外写入页面 window.__mcp_ipc_queue,
    # 由主进程经 browser_kernel_ipc_queue 读回。该通道为项目既有且已验证的机制。
    # ================================================================
    方法 记录应用事件渲染侧 <类型 = 逻辑型>
    参数 框架 <类型 = 类_FBrowser_框架>
    参数 事件类型 <类型 = 文本型>
    参数 数据JSON <类型 = 文本型 @默认值 = "">
    {
        如果 (框架.是否为空 () || 框架.是否有效 () == 假)
        {
            返回 (假)
        }
        变量 参数字段 <类型 = 文本型>
        参数字段 = MCP命令服务器.简单转义JS (数据JSON)
        变量 注入代码 <类型 = 文本型>
        注入代码 = "(function(){var q=window.__mcp_ipc_queue;if(!q){q=[];window.__mcp_ipc_queue=q}q.push({name:'" + MCP命令服务器.简单转义JS (事件类型) + "',data:'" + 参数字段 + "',ts:Date.now()});if(q.length>600){q.splice(0,q.length-600)}})()"
        框架.执行JS代码 (注入代码, "", 0)
        返回 (真)
    }
'''

# 需要追加渲染侧入队的 (事件类型, 该事件的框架参数名)
TARGETS = [
    ("app_render_v8_context_created", "框架"),
    ("app_render_message_received", "框架"),
    ("app_render_load_start", "框架"),
    ("app_render_load_end", "框架"),
    ("app_render_ws_created", "框架"),
    ("app_render_ws_closed", "框架"),
    ("app_render_ws_connect", "框架"),
    ("app_render_ws_recv", "框架"),
    ("app_render_ws_send", "框架"),
]

# 1) 插入 helper：放在类内最后一个 '}' 之前
lines = t.split("\n")
idx = None
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == "}":
        idx = i
        break
lines[idx:idx] = HELPER.split("\n")
t = "\n".join(lines)

# 2) 为每个目标事件的记录调用后追加渲染侧入队
applied, missed = [], []
for etype, frame in TARGETS:
    # 找到该事件方法体内 "记录应用监控事件 ("app_xxx"" 那一行，在其后插入
    pat = re.compile(r'( *)记录应用监控事件 \("' + re.escape(etype) + r'", (.*?)\)\n')
    m = pat.search(t)
    if not m:
        missed.append(etype)
        continue
    indent = m.group(1)
    arg = m.group(2)
    add = "%s记录应用事件渲染侧 (%s, \"%s\", %s)\n" % (indent, frame, etype, arg)
    t = t[:m.end()] + add + t[m.end():]
    applied.append(etype)

io.open(P, "wb").write(t.encode("utf-8"))
print("插入 helper: 1 个")
print("追加渲染侧入队: %d / %d" % (len(applied), len(TARGETS)))
for x in applied:
    print("   + %s" % x)
for x in missed:
    print("   ! 未匹配: %s" % x)
