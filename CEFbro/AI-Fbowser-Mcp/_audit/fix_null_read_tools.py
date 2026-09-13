# -*- coding: utf-8 -*-
"""修复"主力读取工具静默返回 null"缺陷（L2 查出，根因已定位）。

根因: browser_get_text(选择器) / browser_dom_query / browser_fill_attr_get 都走
      填表框架.取元素内容 / 取元素属性 -> CEF JS 回调在本内核返回"空值" ->
      类_MCP_JS异步回调.回调(MCP_Callbacks.wsv:39-42) 把它写成**字面 "null"**,
      于是工具在元素存在时也返回 null 且 isError=false -> AI 误判"元素无文本"。

修法(优先+回退, 不删旧路):
  在原生填表框架调用**之前**先走 CDP JS(项目既有 CDP执行JS并等待, 其注释即写明
  "绕过不稳定的CEF JS回调"); 取到真值就直接返回, 取不到才落回原生路径。

本脚本只改 browser_get_text 与 browser_dom_query 两个分支(已逐行读过上下文);
browser_fill_attr_get 的同源问题留下轮(需先读其上下文, 不盲改)。
类_MCP_JS异步回调 的 "null" 分支**不改**: 它同时服务通用 JS 求值(JS 返回 null 是合法结果),
全局改写会改变 browser_execute_js 的语义 —— 风险高于收益, 改为在报告中记录。
"""
import io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv"
t = io.open(P, encoding="utf-8", newline="").read().replace("\\r\\n", "\\n")
CRLF = True

# ---------------- 1) browser_get_text 选择器分支 ----------------
old1 = """            如果 (selector != "")
            {
                // 原生: 用填表框架取元素内容, 非JS
                变量 填表框架 <类型 = 类_FBrowser_填表框架>"""
new1 = """            如果 (selector != "")
            {
                // 修复(逐功能测试发现): 原生"取元素内容"经 CEF JS 回调在本内核下恒返回空值,
                // 而 类_MCP_JS异步回调 把空值写成字面 "null" -> 本工具在元素**存在**时也返回
                // null 且 isError=false, AI 会误判"该元素没有文本"(静默错误答案)。
                // 改为**优先走 CDP JS**(项目既有 CDP执行JS并等待, 其注释即写明"绕过不稳定的CEF JS回调");
                // 取不到再回退下方的原生填表框架路径, 保留原有行为。
                变量 js取文码 <类型 = 文本型>
                js取文码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');return e?e.textContent:null})()"
                变量 js取文值 <类型 = 文本型>
                js取文值 = MCP命令服务器.CDP执行JS并等待 (js取文码, 10000, 真)
                如果 (js取文值 != "" && js取文值 != "null" && js取文值 != "undefined" && 是否以 (js取文值, "{\\"error\\"") == 假)
                {
                    返回 (MCP_响应构建.命令成功 (命令ID, js取文值))
                }
                // 原生: 用填表框架取元素内容, 非JS
                变量 填表框架 <类型 = 类_FBrowser_填表框架>"""

# ---------------- 2) browser_dom_query ----------------
old2 = """            变量 attribute <类型 = 文本型>
            attribute = MCP命令服务器.yyjson取文本 (参数JSON, "attribute")
            变量 填表框架 <类型 = 类_FBrowser_填表框架>"""
new2 = """            变量 attribute <类型 = 文本型>
            attribute = MCP命令服务器.yyjson取文本 (参数JSON, "attribute")
            // 修复(同上): 优先走 CDP JS 取内容/属性, 取不到再回退原生填表框架。
            变量 js查询码 <类型 = 文本型>
            如果 (attribute != "")
            {
                js查询码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');return e?e.getAttribute('" + MCP命令服务器.简单转义JS (attribute) + "'):null})()"
            }
            否则
            {
                js查询码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');return e?e.textContent:null})()"
            }
            变量 js查询值 <类型 = 文本型>
            js查询值 = MCP命令服务器.CDP执行JS并等待 (js查询码, 10000, 真)
            如果 (js查询值 != "" && js查询值 != "null" && js查询值 != "undefined" && 是否以 (js查询值, "{\\"error\\"") == 假)
            {
                返回 (MCP_响应构建.命令成功 (命令ID, js查询值))
            }
            变量 填表框架 <类型 = 类_FBrowser_填表框架>"""

for label, old, new in (("browser_get_text", old1, new1), ("browser_dom_query", old2, new2)):
    c = t.count(old)
    print("  %-20s 锚点命中 %d" % (label, c))
    if c == 1:
        t = t.replace(old, new, 1)
    else:
        print("      !! 锚点不唯一/未命中, 跳过该项")

io.open(P, "wb").write(t.replace("\\n", "\\r\\n").encode("utf-8"))
print("写回完成")
