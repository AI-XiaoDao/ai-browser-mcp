# -*- coding: utf-8 -*-
"""恢复被我在"鼠标三分支重构"中误删的缺参守卫, 并给触摸三件套补上同样的守卫。

## 事故复盘(必须记录, 因为它正是本项目最怕的那类回归)
我替换 `browser_mouse_click` / `_wheel` 整个分支时, **从第 596 行开始读**, 而这两个分支的
缺参守卫在 **590-593 / 1136-1143 行**(即我读取区间之前), 于是守卫被整段抹掉:
  · click : "必须同时提供 x 与 y … 缺省会被当作 (0,0) 而在页面左上角误点" —— 直接导致
            `browser_mouse_click {}` 变成"在 (0,0) 真的点一下并报成功"(静默假成功 + 误点),
            fastcheck 用例 `mouse_click {} 应拒绝` 立刻变红。
  · wheel : 同上的 x/y 守卫 + "必须提供 delta_y 或 delta_x … 省略会造成滚动 0 像素却报成功"。
教训: **替换整个分支前必须读到该分支的第一行**(本轮 `read` 起点选错)。
本脚本以「分支名 + 紧随的 `{` + 首行语句」为锚点回插, 并在写前断言锚点唯一、守卫当前确实缺失。

## 同时补的守卫
触摸三件套(本轮新增)此前没有 x/y 守卫 -> `browser_touch_press {}` 会在 (0,0) 真的按下,
与 click 的既定策略不一致。按同一理由补上(触摸按下同样是"真实动作", 不该有静默缺省)。
"""
import io
import os
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
S = io.open(P, encoding="utf-8").read()

CLICK_GUARD = '''            如果 (MCP命令服务器.参数键存在 (参数JSON, "x") == 假 || MCP命令服务器.参数键存在 (参数JSON, "y") == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "必须同时提供 x 与 y (整数坐标) | 缺省会被当作 (0,0) 而在页面左上角误点, 故拒绝执行; 如需点左上角请显式传 x=0 y=0"))
            }
'''

WHEEL_GUARD = '''            如果 (MCP命令服务器.参数键存在 (参数JSON, "x") == 假 || MCP命令服务器.参数键存在 (参数JSON, "y") == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "必须同时提供 x 与 y (整数坐标) | 缺省会退化成在 (0,0) 滚动"))
            }
            如果 (MCP命令服务器.参数键存在 (参数JSON, "delta_y") == 假 && MCP命令服务器.参数键存在 (参数JSON, "delta_x") == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "必须提供 delta_y 或 delta_x (滚动量, 正数向下/向右) | 省略会造成滚动 0 像素却报成功"))
            }
'''

TOUCH_GUARD = '''            如果 (MCP命令服务器.参数键存在 (参数JSON, "x") == 假 || MCP命令服务器.参数键存在 (参数JSON, "y") == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "必须同时提供 x 与 y (整数坐标) | 缺省会被当作 (0,0) 而在页面左上角误触, 故拒绝执行; 如需触左上角请显式传 x=0 y=0"))
            }
'''

# (分支名, 守卫文本, 锚点首行, 说明)
JOBS = [
    ("browser_mouse_click", CLICK_GUARD,
     '        否则 (方法名 == "browser_mouse_click")\n        {\n            变量 browser <类型 = 类_FBrowser_浏览器>',
     "恢复 click 的 x/y 守卫"),
    ("browser_mouse_wheel", WHEEL_GUARD,
     '        否则 (方法名 == "browser_mouse_wheel")\n        {\n            变量 browser <类型 = 类_FBrowser_浏览器>',
     "恢复 wheel 的 x/y + delta 守卫"),
    ("browser_touch_press", TOUCH_GUARD,
     '        否则 (方法名 == "browser_touch_press")\n        {\n            变量 touchX <类型 = 整数>',
     "补 touch_press 的 x/y 守卫"),
    ("browser_touch_release", TOUCH_GUARD,
     '        否则 (方法名 == "browser_touch_release")\n        {\n            变量 touchX <类型 = 整数>',
     "补 touch_release 的 x/y 守卫"),
    ("browser_touch_move", TOUCH_GUARD,
     '        否则 (方法名 == "browser_touch_move")\n        {\n            变量 touchX <类型 = 整数>',
     "补 touch_move 的 x/y 守卫"),
]

for name, guard, anchor, why in JOBS:
    n = S.count(anchor)
    if n != 1:
        print("!! 锚点 %s 命中 %d 次(应 1) -> 中止" % (name, n))
        sys.exit(2)
    if "参数键存在 (参数JSON, \"x\")" in anchor:
        print("!! %s 守卫已存在, 无需回插 -> 中止(前提已变)" % name)
        sys.exit(2)
    S = S.replace(anchor, anchor.replace("        {\n", "        {\n" + guard), 1)
    print("已回插: %-22s %s" % (name, why))

io.open(P, "w", encoding="utf-8", newline="\n").write(S)

# 写后自检
chk = io.open(P, encoding="utf-8").read()
todo = [("click x/y 守卫", '而在页面左上角误点, 故拒绝执行; 如需点左上角请显式传 x=0 y=0'),
        ("wheel x/y 守卫", '缺省会退化成在 (0,0) 滚动'),
        ("wheel delta 守卫", '省略会造成滚动 0 像素却报成功'),
        ("touch x/y 守卫", '而在页面左上角误触, 故拒绝执行; 如需触左上角请显式传 x=0 y=0')]
bad = 0
for label, s in todo:
    c = chk.count(s)
    print("自检 %-18s 出现 %d 次 %s" % (label, c, "OK" if c >= 1 else "!! 缺失"))
    if c < 1:
        bad += 1
tc = chk.count('而在页面左上角误触, 故拒绝执行')
print("自检 触摸三件套守卫覆盖 %d 处 (应为 3)" % tc)
if tc != 3:
    bad += 1
print("OK" if bad == 0 else "!! 自检未通过")
sys.exit(1 if bad else 0)
