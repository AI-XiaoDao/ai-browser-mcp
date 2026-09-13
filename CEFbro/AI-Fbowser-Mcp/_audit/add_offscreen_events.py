# -*- coding: utf-8 -*-
"""目标(1): 补齐 11 个 离屏渲染_* 事件覆盖 → 事件覆盖率 100%。

签名严格照抄类库 FBroEventControl.wsv（见 _audit/_event_sigs.txt L219-288）。
含 3 个 类型 = 逻辑型 的事件: 获取屏幕点 / 获取窗口信息 / 开始拖拽
  -> 与既有约定一致: 所有分支返回 假（不阻止/不改变默认行为）。
出参（整数类 / FBrowser_屏幕信息 / FBrowser_矩形位置数组）一律**不写**, 保持 CEF 默认。

配套:
  · 新增开关 是否监控离屏渲染
  · browser_collect 新增 action = event_offscreen_enable
  · browser_kernel_events_all enable/disable 同步该开关
文案如实说明: 窗口内嵌渲染模式下不触发, 仅切到离屏(OSR)模式才有意义。
"""
import io
import os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

# (事件名, 是否逻辑型, 事件类型串, [(参数名, 类型, 输出名)], [(JSON键, 表达式)])
EV = [
    ("离屏渲染_获取屏幕点", True, "offscreen_get_screen_point",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("视图横坐标", "整数", "ViewX"),
      ("视图纵坐标", "整数", "ViewY"), ("屏幕横坐标", "整数类", "ScreenX"),
      ("屏幕纵坐标", "整数类", "ScreenY")],
     [("view_x", "视图横坐标"), ("view_y", "视图纵坐标")]),
    ("离屏渲染_获取窗口信息", True, "offscreen_get_screen_info",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("屏幕信息", "FBrowser_屏幕信息", "ScreenInfo")], []),
    ("离屏渲染_即将显示弹窗", False, "offscreen_popup_show",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("显示", "逻辑型", "Show")],
     [("show", "显示")]),
    ("离屏渲染_将被绘制", False, "offscreen_paint",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("类型", "整数", "PaintType"),
      ("矩形清单", "FBrowser_矩形位置数组", "DirtyRects"), ("缓存指针", "变整数", "BufferPtr"),
      ("宽度", "整数", "Width"), ("高度", "整数", "Height")],
     [("paint_type", "类型"), ("width", "宽度"), ("height", "高度")]),
    ("离屏渲染_将被加速绘制", False, "offscreen_paint_accelerated",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("类型", "整数", "PaintType"),
      ("矩形清单", "FBrowser_矩形位置数组", "DirtyRects"),
      ("加速绘制信息", "FBrowser_加速绘制信息", "AccelInfo")],
     [("paint_type", "类型")]),
    ("离屏渲染_开始拖拽", True, "offscreen_start_dragging",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("拖拽数据", "类_FBrowser_拖拽数据", "DragData"),
      ("拖拽操作类型", "整数", "AllowedOps"), ("横坐标", "整数", "X"), ("纵坐标", "整数", "Y")],
     [("allowed_ops", "拖拽操作类型"), ("x", "横坐标"), ("y", "纵坐标")]),
    ("离屏渲染_更新拖动光标", False, "offscreen_update_drag_cursor",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("拖拽操作类型", "整数", "Operation")],
     [("operation", "拖拽操作类型")]),
    ("离屏渲染_滚动偏移量改变", False, "offscreen_scroll_offset",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("横坐标", "小数", "OffsetX"),
      ("纵坐标", "小数", "OffsetY")],
     [("offset_x", "横坐标"), ("offset_y", "纵坐标")]),
    ("离屏渲染_IME范围改变", False, "offscreen_ime_range",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("选择范围", "FBrowser_范围", "SelectedRange"),
      ("字符范围", "FBrowser_矩形位置数组", "CharacterBounds")], []),
    ("离屏渲染_文本选择改变", False, "offscreen_text_selection",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("选择文本", "文本型", "SelectedText"),
      ("选择范围", "FBrowser_范围", "SelectedRange")],
     [("text", "选择文本")]),
    ("离屏渲染_虚拟键盘请求", False, "offscreen_virtual_keyboard",
     [("浏览器", "类_FBrowser_浏览器", "Browser"), ("输入类型", "整数", "InputMode")],
     [("input_mode", "输入类型")]),
]


def emit(ev):
    name, is_bool, etype, params, payload = ev
    L = ["    方法 %s <公开%s @虚拟方法 = 可覆盖>" % (name, " 类型 = 逻辑型" if is_bool else "")]
    for pn, pt, po in params:
        L.append('    参数 %s <类型 = %s @输出名 = "%s">' % (pn, pt, po))
    L.append("    {")
    L.append("        如果 (MCP命令服务器.是否监控离屏渲染)")
    L.append("        {")
    if payload:
        L.append("            变量 事件数据 <类型 = YYJSON对象类>")
        L.append('            事件数据.创建自文本 ("{}")')
        for k, e in payload:
            L.append('            事件数据.加入文本成员 ("%s", 到文本 (%s))' % (k, e))
        L.append('            记录监控事件 (真, "%s", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))' % etype)
    else:
        L.append('            记录监控事件 (真, "%s", 浏览器.取ID (), "")' % etype)
    L.append("        }")
    if is_bool:
        L.append("        // 逻辑型事件: 返回假 = 不改变 CEF 默认行为(出参一律不写)")
        L.append("        返回 (假)")
    L.append("    }")
    return "\n".join(L)


def insert_before_last_brace(path, blocks, comment):
    raw = io.open(path, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
    nl = "\r\n" if raw.count(b"\r\n") and raw.count(b"\r\n") == raw.count(b"\n") else "\n"
    lines = text.split("\n")
    idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            idx = i
            break
    body = ["", comment]
    for b in blocks:
        body += ["", b]
    body.append("")
    lines[idx:idx] = body
    io.open(path, "wb").write((b"\xef\xbb\xbf" if bom else b"") + nl.join(lines).encode("utf-8"))
    return len(blocks), idx + 1, len(lines)


# ---- 1) 开关 ----
p = os.path.join(SRC, "MCP_Server.wsv")
t = io.open(p, encoding="utf-8").read()
anchor = None
for i, l in enumerate(t.split("\n")):
    if "变量 是否监控许可提示 <" in l:
        anchor = i
assert anchor is not None, "未找到开关锚点"
ls = t.split("\n")
ls[anchor + 1:anchor + 1] = [
    '    变量 是否监控离屏渲染 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "离屏渲染(OSR)事件族 → browser_event:offscreen_* (注: 窗口内嵌渲染模式下不触发, 仅切换到离屏渲染模式才有意义)" @输出名 = "IsMonitorOffscreen">'
]
io.open(p, "wb").write("\n".join(ls).encode("utf-8"))
print("1) 新增开关 是否监控离屏渲染")

# ---- 2) 事件覆盖 ----
n, ins, tot = insert_before_last_brace(
    os.path.join(SRC, "MCP_BrowserEvents.wsv"),
    [emit(e) for e in EV],
    "    # ================================================================\n"
    "    # v3.3 事件覆盖补全: 离屏渲染(OSR)事件族 (11 个) → 事件覆盖率 100%\n"
    "    # ⚠ 这些事件仅在**离屏渲染模式**下由 CEF 回调; 本项目采用窗口内嵌渲染,\n"
    "    #   因此它们不会触发。此处实现的意义是: ①覆盖率完整 ②将来若切换 OSR 模式即可用。\n"
    "    # ================================================================")
print("2) 写入离屏渲染事件覆盖: %d 个 (插入 L%d, 类闭合 L%d)" % (n, ins, tot))

# ---- 3) browser_collect 动作 ----
p3 = os.path.join(SRC, "MCP_Server_Core.wsv")
t3 = io.open(p3, encoding="utf-8").read()
anchor3 = '''            否则 (action == "event_permission_enable")
            {
                MCP命令服务器.是否监控许可提示 = 真
                返回 (MCP_响应构建.命令成功 (命令ID, "许可提示监控已启用 (permission_media_request/prompt_show/prompt_close) | 可感知页面索要摄像头/麦克风/定位等权限"))
            }
'''
add3 = anchor3 + '''            否则 (action == "event_offscreen_enable")
            {
                MCP命令服务器.是否监控离屏渲染 = 真
                返回 (MCP_响应构建.命令成功 (命令ID, "离屏渲染(OSR)事件族监控开关已置真 (可查 offscreen_get_screen_point / get_screen_info / popup_show / paint / paint_accelerated / start_dragging / update_drag_cursor / scroll_offset / ime_range / text_selection / virtual_keyboard)。⚠ 本族事件仅在离屏渲染模式下由 CEF 回调, 本项目采用窗口内嵌渲染, 因此**不会触发、不会产生记录**; 开启不会报错, 但请勿依赖其查询结果"))
            }
'''
print("3) 新增 action:", "已插入" if t3.count(anchor3) == 1 else "!! 锚点异常(%d)" % t3.count(anchor3))
t3 = t3.replace(anchor3, add3, 1)
io.open(p3, "wb").write(t3.encode("utf-8"))

# ---- 4) events_all 接线 ----
p4 = os.path.join(SRC, "MCP_Kernel.wsv")
t4 = io.open(p4, encoding="utf-8").read()
t4 = t4.replace("            MCP命令服务器.是否监控许可提示 = 真\n",
                "            MCP命令服务器.是否监控许可提示 = 真\n            MCP命令服务器.是否监控离屏渲染 = 真\n")
t4 = t4.replace("            MCP命令服务器.是否监控许可提示 = 假\n",
                "            MCP命令服务器.是否监控许可提示 = 假\n            MCP命令服务器.是否监控离屏渲染 = 假\n")
io.open(p4, "wb").write(t4.encode("utf-8"))
print("4) events_all enable/disable 接线完成")
