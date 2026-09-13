# -*- coding: utf-8 -*-
"""实现 获取默认事件 (OnGetDefaultClient) —— 让 CEF 内部/渲染进程创建的浏览器
也能把事件派发到本项目的 类_MCP_浏览器事件。

依据(全部来自技能书类库, 未臆造):
  FBroEventControl.wsv:272  方法 获取默认事件 <公开 注释 = "OnGetDefaultClient…" @虚拟方法 = 可覆盖>
                            参数 浏览器 / 地址 / 用户额外配置 <类型 = 类_FBrowser_用户额外配置>
  FBroLib.wsv:5503          方法 置事件 <公开>
                            参数 浏览器事件 <类型 = 类_FBrowser_事件智能指针>
                            参数 禁用事件  <类型 = FBrowser_禁用事件 @默认值 = 空对象>
  FBroLib.wsv:5504 注释     「…创建一个继承于类_FBrowser_浏览器事件的自定义类事件;
                            即可实现事件触发到你所自定义的类事件方法中…如不设置将不会触发」
  FBroEventControl.wsv:275  「这里面不单独设置事件即为使用内置默认不控制, 要控制就需要自行设置浏览器事件」

调用形态依据: main.wsv 既有 `服务器事件.创建 (类_MCP_服务器事件)` (事件智能指针的创建用法)。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\main.wsv"

METHOD = '''
    # ================================================================
    # v3.2 (C) 关键补齐: 获取默认事件 (OnGetDefaultClient)
    # 背景: 实测发现 类_MCP_初始化事件 里所有 渲染_* 覆盖, 以及既有的
    #   进程间消息_收到主进程消息, 都从未被回调(应用事件因此一条也记不下来)。
    # 类库 类_FBrowser_用户额外配置.置事件 的注释写明:
    #   「…创建一个继承于"类_FBrowser_浏览器事件"的自定义类事件;
    #     即可实现事件触发到你所自定义的类事件方法中…如不设置将不会触发」
    # 而 获取默认事件 的参数说明是:
    #   「这里面不单独设置事件即为使用内置默认不控制, 要控制就需要自行设置浏览器事件」
    # 故此处把本项目的事件类装上, 使内部/渲染进程创建的浏览器也派发事件到我们。
    # ================================================================
    方法 获取默认事件 <公开 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 地址 <类型 = 文本型 @输出名 = "URL">
    参数 用户额外配置 <类型 = 类_FBrowser_用户额外配置 @输出名 = "ExtraConfig">
    {
        如果 (用户额外配置.是否为空 ())
        {
            返回
        }
        变量 默认事件指针 <类型 = 类_FBrowser_事件智能指针>
        默认事件指针.创建 (类_MCP_浏览器事件)
        用户额外配置.置事件 (默认事件指针)
    }
'''

lines = io.open(P, encoding="utf-8").read().split("\n")

# 插到类体内最后一个 '}' 之前
idx = None
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == "}":
        idx = i
        break
lines[idx:idx] = METHOD.split("\n")
io.open(P, "wb").write("\n".join(lines).encode("utf-8"))
print("已插入 获取默认事件 覆盖; 插入位置 L%d (类闭合 L%d)" % (idx + 1, len(lines)))
