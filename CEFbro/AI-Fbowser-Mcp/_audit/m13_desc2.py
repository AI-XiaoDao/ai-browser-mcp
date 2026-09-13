# -*- coding: utf-8 -*-
r"""M13 — 描述改写第二批

针对两类"会让 AI 白调一轮"的问题:
  A. 恒失败工具的描述没有警告(browser_move_window / set_auto_resize)
  B. 有硬约束却未写入描述(仅支持 http/https/about/data/ftp)
另补: mcp_help 的新深链用法、参数语义不清的几个交互工具
"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
APPLY = os.environ.get("APPLY", "0") == "1"

# A. 整条替换
REPLACE = {
    "browser_move_window":
        "⛔ 本工具恒失败: 嵌入式GUI浏览器的窗口由主窗口统一管理, 不支持移动/改尺寸| 需要不同视口请用 browser_screenshot 的 width/height 或 fingerprint viewport",
    "browser_set_auto_resize":
        "⛔ 本工具恒失败: 嵌入式GUI浏览器尺寸由主窗口布局管理, 不支持自动调整| 需要改视口请用 fingerprint viewport",
    "mcp_help":
        "帮助信息| 不带参数返回按功能域分类的工具清单; 传 tool 参数则返回该工具的完整描述与参数 schema, 例: mcp_help tool=browser_navigate",
    "browser_key_event":
        "发送键盘事件| key_code=虚拟键码(如 13=Enter, 65=A), type=keydown/keyup/char, modifiers=修饰键位掩码; 输入文本请用 vip_key_type",
    "browser_mouse_click":
        "在页面坐标 (x,y) 处点击鼠标| button=left/right/middle(默认left); 坐标是页面视口坐标, 可用 dom_rect 取元素坐标",
    "browser_mouse_move":
        "把鼠标移动到页面坐标 (x,y)| 常用于触发 hover 菜单; 移动后需 click 才生效",
    "browser_mouse_wheel":
        "在 (x,y) 处滚动鼠标滚轮| delta_y 为正向下滚; 单纯滚动页面也可用 scroll_by",
    "browser_fingerprint":
        "浏览器指纹总入口(按 action 分派)| 常用: canvas_random/webgl_random/audio_random/ua/webrtc/geolocation/timezone/ssl/set_batch | 多数改动需刷新页面生效",
    "browser_screenshot":
        "页面截图| 返回 base64 图片(data:image/...); format=png/jpeg/webp, 可指定 width/height/x/y/scale 裁剪缩放",
    "browser_print_to_pdf":
        "把当前页面打印为 PDF 文件| 异步执行, 用 mcp_result 取结果; 需给 path; 目标文件已存在时需 overwrite:true",
    "browser_touch_press":   "触摸按下(CDP级, 移动端仿真)| 需先 fingerprint touch_enable 开启触摸",
    "browser_touch_release": "触摸放开(CDP级)| 与 touch_press 配对",
    "browser_touch_move":    "触摸拖动(CDP级)| 用于滑动/长按拖动",
    "browser_ipc_send_all":
        "向所有渲染进程推送一条进程间消息| 页面侧由 window.__mcp_ipc_queue 接收(逆向时可作主进程→页面的指令通道)",
    "browser_ipc_send_to":
        "向指定渲染进程推送一条进程间消息| 渲染进程ID 用 ipc_renderer_ids 获取",
    "browser_view_source":
        "在新标签打开当前页面源码视图(view-source:)| 取源码字符串请用 get_source",
    "browser_refresh_cookies":
        "把内存中的 Cookie 刷写到磁盘| 用于持久化登录态, 一般无需手动调用",
    "browser_set_proxy":
        "设置浏览器代理并持久生效(新浏览器自动应用)| address 形如 ip:port; 设置后需刷新页面才作用于当前页",
}

# B. 追加约束后缀(保留原有描述)
APPEND = {
    "browser_navigate": " | 仅支持 http/https/about/data/ftp 协议",
    "browser_create":   " | 仅支持 http/https/about/data/ftp 协议",
    "browser_scrape":   " | 仅支持 http/https/about/data/ftp 协议",
    "browser_start_download": " | 仅支持 http/https 协议",
    "browser_create_url_request": " | 仅支持 http/https 协议",
    "browser_close_try": " | ⛔ 该工具恒失败, 请改用 browser_close",
}

lines = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
ok = miss = 0
missed = []

for tool, desc in REPLACE.items():
    pat = re.compile(r'(添加工具JSON\s*\(\s*"' + re.escape(tool) + r'"\s*,\s*)"[^"]*"')
    done = False
    for i, l in enumerate(lines):
        if pat.search(l):
            lines[i] = pat.sub(lambda m: m.group(1) + '"' + desc + '"', l, count=1)
            done = True; ok += 1; break
    if not done:
        miss += 1; missed.append(("REPLACE", tool))

for tool, suf in APPEND.items():
    pat = re.compile(r'(添加工具JSON\s*\(\s*"' + re.escape(tool) + r'"\s*,\s*")([^"]*)(")')
    done = False
    for i, l in enumerate(lines):
        m = pat.search(l)
        if m:
            if suf.strip() in m.group(2):
                done = True; ok += 1; break          # 幂等
            lines[i] = pat.sub(lambda mm: mm.group(1) + mm.group(2) + suf + mm.group(3), l, count=1)
            done = True; ok += 1; break
    if not done:
        miss += 1; missed.append(("APPEND", tool))

print("成功 %d, 未命中 %d" % (ok, miss))
if missed:
    print("未命中:", missed)
if APPLY:
    io.open(os.path.join(SRC, "MCP_Server.wsv"), "w", encoding="utf-8", newline="").write("\n".join(lines))
    print("已写入")
else:
    print("(dry-run)")

print()
print("--- 抽样 ---")
for t in ["browser_move_window", "browser_set_auto_resize", "mcp_help",
          "browser_navigate", "browser_close_try", "browser_screenshot"]:
    for l in lines:
        if ('添加工具JSON ("' + t + '"') in l:
            print("  %s" % l.strip()[:190]); break
