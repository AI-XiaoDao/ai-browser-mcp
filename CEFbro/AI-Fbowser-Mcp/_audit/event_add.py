# -*- coding: utf-8 -*-
"""为 类_MCP_浏览器事件 / 类_MCP_初始化事件 批量补齐缺失的 FBrowser 事件覆盖。

设计要点(全部来自技能内类库 FBroEventControl.wsv 的权威签名):
  1. 逻辑型事件 (返回真=阻止默认行为) 必须在末尾 返回 (假), 否则会拦截浏览器正常行为。
  2. 覆盖事件但不设置 out 参数 = 不改变默认行为, 因此对 允许操作系统执行 等出参一律不写。
  3. 每个事件族一个 是否监控* 开关, 默认 假, 由 browser_kernel_events_all enable 统一打开。
  4. 载荷只取简单可序列化字段; 复杂的值类参数 (FBrowser_文本/拖拽位置数组) 只记存在性。

跳过并说明理由的类库事件:
  - 获取默认事件 (OnGetDefaultClient): 它是"填充 用户额外配置"的**汇点**, 空覆盖会破坏
    谷歌模式下内置功能的默认事件装配 -> 故意不覆盖。
  - 离屏渲染_* (14 个): 本项目用**窗口内嵌渲染**, 离屏渲染事件永不触发, 覆盖即死代码 -> 不覆盖。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

# ----------------------------------------------------------------------------
# 新增监控开关 (加入 MCP命令服务器, 紧随 是否监控应用事件)
# ----------------------------------------------------------------------------
NEW_SWITCHES = [
    ("是否监控菜单事件", "IsMonitorContextMenu", "浏览器_即将打开菜单/菜单被调用/菜单被点击/菜单被关闭 → browser_event:context_menu*"),
    ("是否监控快捷菜单", "IsMonitorQuickMenu", "浏览器_即将运行快捷菜单命令/即将取消快捷菜单 → browser_event:quick_menu*"),
    ("是否监控导航意图", "IsMonitorNavIntent", "浏览器_从标签打开地址/处理协议请求/即将创建主框架Document → browser_event:nav_intent*"),
    ("是否监控界面细节", "IsMonitorUiDetail", "工具栏(提示)/光标/自动调整尺寸/渲染视图/拖拽区域/客户端证书 → browser_event:ui_*"),
    ("是否监控插件生命周期", "IsMonitorExtension", "扩展插件_创建成功/创建失败/载入成功/卸载成功 → app_event:extension_*"),
    ("是否监控启动流程", "IsMonitorStartup", "请求环境初始化完毕/即将处理命令行/即将启动子进程/消息调度/即将初始化WebKit → app_event:startup_*"),
    ("是否监控渲染细节", "IsMonitorRenderDetail", "渲染_即将创建V8环境/收到消息/载入状态被改变/载入开始/载入结束 → app_event:render_*"),
    ("是否监控WebSocket渲染", "IsMonitorRenderWS", "渲染_VIP_WebSocket客户端_创建/关闭/连接服务器/接收数据/发送数据 → app_event:render_ws_*"),
]

# ----------------------------------------------------------------------------
# 浏览器事件: (事件名, 开关, 事件类型, [(参数名,类型,输出名)], [(JSON键, 表达式)], 是否逻辑型)
# ----------------------------------------------------------------------------
BR = [
    ("浏览器_即将打开菜单", "是否监控菜单事件", "context_menu_opening",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("菜单环境", "类_FBrowser_菜单环境", "MenuParams"),
      ("菜单模式", "类_FBrowser_菜单模式", "MenuModel")], [], False),
    ("浏览器_菜单被调用", "是否监控菜单事件", "context_menu_run",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("菜单环境", "类_FBrowser_菜单环境", "MenuParams"),
      ("菜单模式", "类_FBrowser_菜单模式", "MenuModel"),
      ("运行命令菜单回调", "类_FBrowser_运行命令菜单回调", "RunMenuCallback")], [], True),
    ("浏览器_菜单被点击", "是否监控菜单事件", "context_menu_command",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("菜单环境", "类_FBrowser_菜单环境", "MenuParams"),
      ("命令ID", "整数", "CommandID"),
      ("事件标识", "整数", "EventFlags")],
     [("command_id", "命令ID"), ("event_flags", "事件标识")], True),
    ("浏览器_菜单被关闭", "是否监控菜单事件", "context_menu_dismissed",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame")], [], False),
    ("浏览器_即将运行快捷菜单命令", "是否监控快捷菜单", "quick_menu_command",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("命令ID", "整数", "CommandID"),
      ("事件标识", "整数", "EventFlags")],
     [("command_id", "命令ID"), ("event_flags", "事件标识")], True),
    ("浏览器_即将取消快捷菜单", "是否监控快捷菜单", "quick_menu_dismissed",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame")], [], False),
    ("浏览器_从标签打开地址", "是否监控导航意图", "open_url_from_tab",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("目的地址", "文本型", "TargetURL"),
      ("目的配置", "整数", "TargetDisposition"),
      ("用户行为", "逻辑型", "UserGesture")],
     [("url", "目的地址"), ("disposition", "目的配置"), ("user_gesture", "用户行为")], True),
    ("浏览器_处理协议请求", "是否监控导航意图", "protocol_execution",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("请求", "类_FBrowser_请求", "Request"),
      ("允许操作系统执行", "逻辑型类", "AllowOSExecution")],
     [("url", "请求.取地址 ()")], False),
    ("浏览器_即将创建主框架Document", "是否监控导航意图", "main_document_creating",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame")], [], False),
    ("浏览器_工具栏被改变", "是否监控界面细节", "tooltip",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("内容", "FBrowser_文本", "Content")], [], True),
    ("浏览器_光标被改变", "是否监控界面细节", "cursor_changed",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("光标句柄", "变整数", "CursorHandle"),
      ("类型", "整数", "CursorType"),
      ("光标信息", "FBrowser_光标信息", "CursorInfo")],
     [("cursor_type", "类型")], True),
    ("浏览器_自动调整尺寸", "是否监控界面细节", "auto_resize",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("高度", "整数", "Height"),
      ("宽度", "整数", "Width")],
     [("height", "高度"), ("width", "宽度")], True),
    ("浏览器_渲染视图", "是否监控界面细节", "render_view_ready",
     [("浏览器", "类_FBrowser_浏览器", "Browser")], [], False),
    ("浏览器_拖拽区域改变", "是否监控界面细节", "draggable_regions_changed",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("拖拽位置", "FBrowser_拖拽位置数组", "DraggableRegions")], [], False),
    ("浏览器_选择客户端证书", "是否监控界面细节", "client_cert_selected",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("是否为代理", "逻辑型", "IsProxy"),
      ("主机地址", "文本型", "Host"),
      ("端口", "整数", "Port"),
      ("X509证书清单", "类_FBrowser_X509证书数组", "CertList"),
      ("选择证书回调", "类_FBrowser_选择证书回调", "SelectCertCallback")],
     [("is_proxy", "是否为代理"), ("host", "主机地址"), ("port", "端口")], True),
    ("浏览器_按下某键后", "是否监控键盘焦点", "key_event",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("按键事件", "FBrowser_按键事件", "KeyEvent"),
      ("系统事件", "FBrowser_系统事件", "OsEvent")], [], True),
    ("浏览器_请求焦点", "是否监控键盘焦点", "set_focus",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("源类型", "整数", "Source")],
     [("source", "源类型")], True),
    ("浏览器_JS重置对话框", "是否监控对话框", "js_dialog_reset",
     [("浏览器", "类_FBrowser_浏览器", "Browser")], [], False),
    ("浏览器_JS对话框关闭", "是否监控对话框", "js_dialog_closed",
     [("浏览器", "类_FBrowser_浏览器", "Browser")], [], False),
    ("浏览器_即将连接框架", "是否监控框架", "frame_attached",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame")], [], False),
]

# ----------------------------------------------------------------------------
# 应用事件: (事件名, 开关, 事件类型, [(参数名,类型,输出名)], [(JSON键,表达式)], 是否逻辑型)
# ----------------------------------------------------------------------------
APP = [
    ("请求环境初始化完毕", "是否监控启动流程", "startup_request_context_ready",
     [("请求环境", "类_FBrowser_请求环境", "RequestContext")], [], False),
    ("即将处理命令行", "是否监控启动流程", "startup_cmdline",
     [("进程类型", "文本型", "ProcessType"),
      ("命令行", "类_FBrowser_命令行", "CommandLine")],
     [("process_type", "进程类型")], False),
    ("浏览器_即将启动子进程", "是否监控启动流程", "startup_child_process",
     [("命令行", "类_FBrowser_命令行", "CommandLine")], [], False),
    ("浏览器_即将启动消息调度", "是否监控启动流程", "startup_message_pump",
     [("延迟时间", "长整数", "DelayMs")],
     [("delay_ms", "延迟时间")], False),
    ("渲染_即将初始化WebKit", "是否监控启动流程", "startup_webkit_init", [], [], False),
    ("渲染_即将创建V8环境", "是否监控渲染细节", "render_v8_context_created",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("V8环境", "类_FBrowser_V8环境", "V8Context")], [], False),
    ("渲染_收到消息", "是否监控渲染细节", "render_message_received",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("源进程", "整数", "SourceProcess"),
      ("消息", "类_FBrowser_进程消息", "Message")],
     [("source_process", "源进程")], True),
    ("渲染_载入状态被改变", "是否监控渲染细节", "render_loading_state",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("是否读取中", "逻辑型", "IsLoading"),
      ("可后退", "逻辑型", "CanGoBack"),
      ("可前进", "逻辑型", "CanGoForward")],
     [("is_loading", "是否读取中"), ("can_go_back", "可后退"), ("can_go_forward", "可前进")], False),
    ("渲染_载入开始", "是否监控渲染细节", "render_load_start",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("过渡类型", "整数", "TransitionType")],
     [("transition_type", "过渡类型")], False),
    ("渲染_载入结束", "是否监控渲染细节", "render_load_end",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("状态码", "整数", "StatusCode")],
     [("status_code", "状态码")], False),
    ("扩展插件_创建成功", "是否监控插件生命周期", "extension_created",
     [("请求环境", "类_FBrowser_请求环境", "RequestContext"),
      ("插件ID", "文本型", "ExtensionID")],
     [("extension_id", "插件ID")], False),
    ("扩展插件_创建失败", "是否监控插件生命周期", "extension_create_failed",
     [("请求环境", "类_FBrowser_请求环境", "RequestContext"),
      ("插件ID", "文本型", "ExtensionID"),
      ("插件路径", "文本型", "ExtensionPath"),
      ("错误信息", "文本型", "ErrorMessage")],
     [("extension_id", "插件ID"), ("path", "插件路径"), ("error", "错误信息")], False),
    ("扩展插件_载入成功", "是否监控插件生命周期", "extension_loaded",
     [("请求环境", "类_FBrowser_请求环境", "RequestContext"),
      ("插件ID", "文本型", "ExtensionID")],
     [("extension_id", "插件ID")], False),
    ("扩展插件_卸载成功", "是否监控插件生命周期", "extension_unloaded",
     [("请求环境", "类_FBrowser_请求环境", "RequestContext"),
      ("插件ID", "文本型", "ExtensionID")],
     [("extension_id", "插件ID")], False),
    ("渲染_VIP_WebSocket客户端_创建", "是否监控WebSocket渲染", "render_ws_created",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("websocket客户端", "类_FBrowserVIP_WebSocket客户端", "WSClient")], [], False),
    ("渲染_VIP_WebSocket客户端_关闭", "是否监控WebSocket渲染", "render_ws_closed",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("websocket客户端", "类_FBrowserVIP_WebSocket客户端", "WSClient")], [], False),
    ("渲染_VIP_WebSocket客户端_连接服务器", "是否监控WebSocket渲染", "render_ws_connect",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("websocket客户端", "类_FBrowserVIP_WebSocket客户端", "WSClient"),
      ("url", "文本型", "URL"),
      ("protocols", "文本型", "Protocols")],
     [("url", "url"), ("protocols", "protocols")], False),
    ("渲染_VIP_WebSocket客户端_接收数据", "是否监控WebSocket渲染", "render_ws_recv",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("websocket客户端", "类_FBrowserVIP_WebSocket客户端", "WSClient")], [], True),
    ("渲染_VIP_WebSocket客户端_发送数据", "是否监控WebSocket渲染", "render_ws_send",
     [("浏览器", "类_FBrowser_浏览器", "Browser"),
      ("框架", "类_FBrowser_框架", "Frame"),
      ("websocket客户端", "类_FBrowserVIP_WebSocket客户端", "WSClient")], [], True),
]


def param_line(name, typ, outname):
    return "    参数 %s <类型 = %s @输出名 = \"%s\">" % (name, typ, outname)


def emit_browser(ev):
    name, sw, etype, params, payload, is_bool = ev
    L = []
    L.append("    方法 %s <公开 @虚拟方法 = 可覆盖>" % name)
    for p in params:
        L.append("    " + param_line(*p).strip())
    L.append("    {")
    L.append("        如果 (MCP命令服务器.%s)" % sw)
    L.append("        {")
    if payload:
        L.append("            变量 事件数据 <类型 = YYJSON对象类>")
        L.append("            事件数据.创建自文本 (\"{}\")")
        for k, expr in payload:
            L.append("            事件数据.加入文本成员 (\"%s\", 到文本 (%s))" % (k, expr))
        L.append("            记录监控事件 (真, \"%s\", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))" % etype)
    else:
        L.append("            记录监控事件 (真, \"%s\", 浏览器.取ID (), \"\")" % etype)
    L.append("        }")
    if is_bool:
        L.append("        // 逻辑型事件: 返回假 = 不阻止浏览器默认行为")
        L.append("        返回 (假)")
    L.append("    }")
    return "\n".join(L)


def emit_app(ev):
    name, sw, etype, params, payload, is_bool = ev
    L = []
    L.append("    方法 %s <公开 @虚拟方法 = 可覆盖>" % name)
    for p in params:
        L.append("    " + param_line(*p).strip())
    L.append("    {")
    L.append("        如果 (MCP命令服务器.%s == 假)" % sw)
    L.append("        {")
    if is_bool:
        L.append("            返回 (假)")
    else:
        L.append("            返回")
    L.append("        }")
    if payload:
        L.append("        变量 事件数据 <类型 = YYJSON对象类>")
        L.append("        事件数据.创建自文本 (\"{}\")")
        for k, expr in payload:
            L.append("        事件数据.加入文本成员 (\"%s\", 到文本 (%s))" % (k, expr))
        L.append("        记录应用监控事件 (\"%s\", 事件数据.到可读文本 (YYJSON格式化选项.压缩))" % etype)
    else:
        L.append("        记录应用监控事件 (\"%s\", \"\")" % etype)
    if is_bool:
        L.append("        // 逻辑型事件: 返回假 = 消息未被处理/不阻止默认行为")
        L.append("        返回 (假)")
    L.append("    }")
    return "\n".join(L)


def insert_before_last_brace(path, blocks, marker_comment):
    raw = io.open(path, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
    crlf = raw.count(b"\r\n") == raw.count(b"\n") and raw.count(b"\r\n") > 0
    nl = "\r\n" if crlf else "\n"
    lines = text.split("\n")
    # 找最后一个仅含 '}' 的行
    idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            idx = i
            break
    assert idx is not None, "未找到类结尾"
    body = []
    body.append("")
    body.append(marker_comment)
    for b in blocks:
        body.append("")
        body.append(b)
    body.append("")
    lines[idx:idx] = body
    out = nl.join(lines)
    data = (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8")
    io.open(path, "wb").write(data)
    return len(blocks)


def add_switches():
    p = os.path.join(SRC, "MCP_Server.wsv")
    raw = io.open(p, "rb").read()
    text = raw.decode("utf-8")
    anchor = None
    for i, l in enumerate(text.split("\n")):
        if "变量 是否监控应用事件 <" in l:
            anchor = i
    assert anchor is not None, "未找到 是否监控应用事件 锚点"
    lines = text.split("\n")
    add = []
    for cn, en, note in NEW_SWITCHES:
        add.append("    变量 %s <公开 静态 类型 = 逻辑型 值 = 假 注释 = \"%s\" @输出名 = \"%s\">"
                   % (cn, note, en))
    lines[anchor + 1:anchor + 1] = add
    io.open(p, "wb").write("\n".join(lines).encode("utf-8"))
    return len(NEW_SWITCHES)


if __name__ == "__main__":
    n = add_switches()
    print("已新增监控开关: %d" % n)
    nb = insert_before_last_brace(
        os.path.join(SRC, "MCP_BrowserEvents.wsv"),
        [emit_browser(e) for e in BR],
        "    # ================================================================")
    print("已写入浏览器事件覆盖: %d" % nb)
    na = insert_before_last_brace(
        os.path.join(SRC, "main.wsv"),
        [emit_app(e) for e in APP],
        "    # ================================================================")
    print("已写入应用事件覆盖: %d" % na)
