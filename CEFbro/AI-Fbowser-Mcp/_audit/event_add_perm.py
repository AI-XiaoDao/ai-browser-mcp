# -*- coding: utf-8 -*-
"""补齐 3 个许可提示事件 (媒体访问许可 / 显示许可提示 / 关闭许可提示)。
签名严格照抄类库 FBroEventControl.wsv L1725/L1740/L1754。
类库自身实现即为 `返回 (假)`, 故本覆盖同样返回假, 不改变默认行为。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

# 1) 新增开关
p = os.path.join(SRC, "MCP_Server.wsv")
txt = io.open(p, encoding="utf-8").read()
anchor = None
for i, l in enumerate(txt.split("\n")):
    if "变量 是否监控WebSocket渲染 <" in l:
        anchor = i
assert anchor is not None, "未找到锚点"
lines = txt.split("\n")
lines[anchor + 1:anchor + 1] = [
    '    变量 是否监控许可提示 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_即将请求媒体访问许可/即将显示许可提示/即将关闭许可提示 → browser_event:permission_* (摄像头/麦克风/定位等授权请求)" @输出名 = "IsMonitorPermissionPrompt">'
]
io.open(p, "wb").write("\n".join(lines).encode("utf-8"))
print("已新增开关 是否监控许可提示")

# 2) 事件方法
BLOCKS = []
BLOCKS.append("""    方法 浏览器_即将请求媒体访问许可 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">
    参数 请求源 <类型 = 文本型 @输出名 = "RequestingOrigin">
    参数 请求许可 <类型 = 整数 @输出名 = "RequestedPermissions">
    参数 回调 <类型 = 类_FBrowser_媒体接入回调 @输出名 = "Callback">
    {
        // 安全相关: 页面正在索要摄像头/麦克风等媒体权限, 让 AI 能感知并告警
        如果 (MCP命令服务器.是否监控许可提示)
        {
            变量 事件数据 <类型 = YYJSON对象类>
            事件数据.创建自文本 ("{}")
            事件数据.加入文本成员 ("origin", 请求源)
            事件数据.加入文本成员 ("permissions", 到文本 (请求许可))
            记录监控事件 (真, "permission_media_request", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))
        }
        // 逻辑型事件: 返回假 = 不阻止浏览器默认行为 (与类库自身默认实现一致)
        返回 (假)
    }""")
BLOCKS.append("""    方法 浏览器_即将显示许可提示 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 提示ID <类型 = 长整数 @输出名 = "PromptID">
    参数 请求源 <类型 = 文本型 @输出名 = "RequestingOrigin">
    参数 请求许可 <类型 = 整数 @输出名 = "RequestedPermissions">
    参数 回调 <类型 = 类_FBrowser_权限提示回调 @输出名 = "Callback">
    {
        如果 (MCP命令服务器.是否监控许可提示)
        {
            变量 事件数据 <类型 = YYJSON对象类>
            事件数据.创建自文本 ("{}")
            事件数据.加入文本成员 ("prompt_id", 到文本 (提示ID))
            事件数据.加入文本成员 ("origin", 请求源)
            事件数据.加入文本成员 ("permissions", 到文本 (请求许可))
            记录监控事件 (真, "permission_prompt_show", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))
        }
        返回 (假)
    }""")
BLOCKS.append("""    方法 浏览器_即将关闭许可提示 <公开 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 提示ID <类型 = 长整数 @输出名 = "PromptID">
    参数 结果标识 <类型 = 整数 @输出名 = "ResultFlag">
    {
        如果 (MCP命令服务器.是否监控许可提示)
        {
            变量 事件数据 <类型 = YYJSON对象类>
            事件数据.创建自文本 ("{}")
            事件数据.加入文本成员 ("prompt_id", 到文本 (提示ID))
            事件数据.加入文本成员 ("result", 到文本 (结果标识))
            记录监控事件 (真, "permission_prompt_close", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))
        }
    }""")

p2 = os.path.join(SRC, "MCP_BrowserEvents.wsv")
t2 = io.open(p2, encoding="utf-8").read()
ls = t2.split("\n")
idx = None
for i in range(len(ls) - 1, -1, -1):
    if ls[i].strip() == "}":
        idx = i
        break
body = ["", "    # ================================================================"]
for b in BLOCKS:
    body += ["", b]
body.append("")
ls[idx:idx] = body
io.open(p2, "wb").write("\n".join(ls).encode("utf-8"))
print("已写入许可提示事件: %d" % len(BLOCKS))

# 3) 接线到 events_all
p3 = os.path.join(SRC, "MCP_Kernel.wsv")
t3 = io.open(p3, encoding="utf-8").read()
t3 = t3.replace("            MCP命令服务器.是否监控WebSocket渲染 = 真\n",
                "            MCP命令服务器.是否监控WebSocket渲染 = 真\n            MCP命令服务器.是否监控许可提示 = 真\n")
t3 = t3.replace("            MCP命令服务器.是否监控WebSocket渲染 = 假\n",
                "            MCP命令服务器.是否监控WebSocket渲染 = 假\n            MCP命令服务器.是否监控许可提示 = 假\n")
io.open(p3, "wb").write(t3.encode("utf-8"))
print("已接线 events_all (enable/disable)")
