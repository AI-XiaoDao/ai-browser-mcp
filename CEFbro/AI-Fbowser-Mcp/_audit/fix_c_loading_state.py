# -*- coding: utf-8 -*-
"""为 '渲染_载入状态被改变' 接入渲染侧通道。

该事件是渲染进程事件, 但参数里**只有浏览器、没有框架**。
既有代码 main.wsv:431-432 (`进程间消息_收到主进程消息`) 已证明可用
`浏览器.取主框架 ()` 兜底取框架 —— 本脚本复用同一写法。

另: 经类库注解核实, 其余无框架参数的事件属**主进程事件**
 (请求环境初始化完毕 / 浏览器_即将启动子进程 / 即将启动消息调度 / 扩展插件_*),
 走原有 SQLite 路径即可, **不需要**本通道, 故不接入。
"""
import io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\main.wsv"
t = io.open(P, encoding="utf-8").read()

HELPER2 = '''    方法 记录应用事件渲染侧_按浏览器 <类型 = 逻辑型>
    参数 浏览器 <类型 = 类_FBrowser_浏览器>
    参数 事件类型 <类型 = 文本型>
    参数 数据JSON <类型 = 文本型 @默认值 = "">
    {
        // 用于"渲染进程事件但参数只有浏览器、没有框架"的情况(如 渲染_载入状态被改变)。
        // 取主框架兜底 —— 与 main.wsv 进程间消息_收到主进程消息 的既有写法一致。
        如果 (浏览器.是否为空 ())
        {
            返回 (假)
        }
        变量 兜底框架 <类型 = 类_FBrowser_框架>
        兜底框架 = 浏览器.取主框架 ()
        返回 (记录应用事件渲染侧 (兜底框架, 事件类型, 数据JSON))
    }
'''

# 1) 插到「记录应用事件渲染侧」helper 之后
anchor = "        返回 (真)\n    }\n"
i = t.find("方法 记录应用事件渲染侧 <")
j = t.find("方法 记录应用事件渲染侧 <", i + 10)
# 在第一个 helper 结束处插入: 找到该 helper 里最后一个 "返回 (真)" 之后
k = t.find("返回 (真)", i)
k = t.find("\n", k)
t = t[:k + 1] + "\n" + HELPER2 + t[k + 1:]

# 2) 为 渲染_载入状态被改变 追加入队调用(用浏览器兜底)
target = '记录应用监控事件 ("app_render_loading_state", 事件数据.到可读文本 (YYJSON格式化选项.压缩))'
cnt = t.count(target)
add = '记录应用事件渲染侧_按浏览器 (浏览器, "app_render_loading_state", 事件数据.到可读文本 (YYJSON格式化选项.压缩))'
t = t.replace(target, target + "\n        " + add)

io.open(P, "wb").write(t.encode("utf-8"))
print("插入 helper2: %s" % ("是" if "记录应用事件渲染侧_按浏览器" in t else "否"))
print("接入 渲染_载入状态被改变 调用点: %d" % cnt)
