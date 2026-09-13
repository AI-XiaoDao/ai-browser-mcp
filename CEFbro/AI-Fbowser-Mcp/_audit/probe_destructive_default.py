# -*- coding: utf-8 -*-
"""验收: "遗漏必填参数 -> 执行了破坏性/状态改变的动作" 这一类是否已修。

背景(真机实测, 修复前全部 success:true):
  browser_mouse_click {}          -> 真的在页面 (0,0) 点了一下          (不可撤销)
  browser_mouse_wheel {}          -> 高级鼠标_滚轮滚动 (0,0,0,0) 空操作却报成功
  browser_set_zoom {}             -> "缩放(持久): 0", 缩放清 0 且持久作用于新窗口
  browser_antidetect_presets {}   -> 部署 stealth 预设, **持久生效于所有新浏览器**
  browser_network {}              -> 隐式打开全局网络日志
  browser_vip_enable_js_env {}    -> 关闭 JS 执行环境
  browser_fingerprint_online {}   -> navigator.onLine 伪造成 false
  browser_set_mute {}             -> 取消静音并写入持久配置
  browser_set_focus {}            -> 窗口失去焦点
  browser_set_window_style {type} -> style 缺省=0, 会把窗口样式位全部清掉(仅源码判定, 未真机执行)

修法: 新增共享方法 `MCP命令服务器.参数键存在`(未知/空值 均视为未提供),
在各工具执行前做"缺参即拒绝"守卫; 同时修掉 set_zoom 里"只判 未知"的存在性误判。

用例结构: **缺参必须报错** + **显式传值必须成功**(正对照, 防"一律报错"这种假修复)。

注意: 本脚本会临时改动缩放/静音/焦点/指纹等状态, 结束时统一还原。
"""
import importlib.util
import sys
import time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("v4", "verify_round4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

results = []


def call(name, args, timeout=45):
    return v4.call(name, args, timeout)


def rec(tag, ok, detail):
    results.append((tag, ok, detail))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:150]))


def must_err(tag, tool, args, needle=None):
    """缺参: 必须报错(isError=true), 且文案含 needle(若给)。"""
    e, t, _ = call(tool, args)
    if not e:
        rec(tag, False, "!! 预期报错却返回成功: " + t.replace("\n", " ")[:140])
        return
    if needle and needle not in t:
        rec(tag, False, "已报错但文案不含 %r: %s" % (needle, t[:130]))
        return
    rec(tag, True, t.replace("\n", " ")[:120])


def must_ok(tag, tool, args, needle=None):
    """显式传值: 必须成功(正对照)。"""
    e, t, _ = call(tool, args)
    if e:
        rec(tag, False, "预期成功却报错: " + t.replace("\n", " ")[:140])
        return
    if needle and needle not in t:
        rec(tag, False, "成功但内容不含 %r: %s" % (needle, t[:130]))
        return
    rec(tag, True, t.replace("\n", " ")[:120])


print("== 环境 ==")
call("browser_navigate", {"url": "about:blank", "wait_for_load": True}, 60)
time.sleep(1.0)
print("  已导航到 about:blank (避免真实点击产生副作用)")

print("\n== 1) 鼠标: 缺参必须拒绝; 显式坐标必须成功 ==")
must_err("mouse_click {} 应拒绝", "browser_mouse_click", {}, "必须同时提供 x 与 y")
must_ok("mouse_click {x,y} 正对照", "browser_mouse_click", {"x": 100, "y": 100}, "点击")
must_err("mouse_wheel {} 应拒绝", "browser_mouse_wheel", {}, "必须同时提供 x 与 y")
must_err("mouse_wheel {x,y} 无 delta 应拒绝", "browser_mouse_wheel",
         {"x": 100, "y": 100}, "delta_y 或 delta_x")
must_ok("mouse_wheel {x,y,delta_y} 正对照", "browser_mouse_wheel",
        {"x": 100, "y": 100, "delta_y": 120}, "滚轮")

print("\n== 2) 缩放: 缺参必须拒绝(原来会清 0 且持久) ==")
must_err("set_zoom {} 应拒绝", "browser_set_zoom", {}, "参数 level 不能为空")
must_err("set_zoom {level:'abc'} 应拒绝", "browser_set_zoom",
         {"level": "abc"}, "不是有效数字")
must_ok("set_zoom {level:1.5} 正对照", "browser_set_zoom", {"level": 1.5}, "1.5")
must_ok("set_zoom {level:0} 显式 0 应允许", "browser_set_zoom", {"level": 0}, "缩放")
must_ok("set_zoom {level:'1.50'} 合法写法", "browser_set_zoom", {"level": "1.50"}, "缩放")

print("\n== 3) 持久/开关类: 缺参必须拒绝 ==")
must_err("set_mute {} 应拒绝", "browser_set_mute", {}, "不能省略")
must_ok("set_mute {mute:false} 正对照", "browser_set_mute", {"mute": False}, "静音")
must_err("set_focus {} 应拒绝", "browser_set_focus", {}, "不能省略")
must_ok("set_focus {focus:true} 正对照", "browser_set_focus", {"focus": True}, "焦点")
must_err("fingerprint_online {} 应拒绝", "browser_fingerprint_online", {}, "不能省略")
must_ok("fingerprint_online {value:true} 正对照", "browser_fingerprint_online",
        {"value": True}, "OnLine")
must_err("vip_enable_js_env {} 应拒绝", "browser_vip_enable_js_env", {}, "不能省略")
# 注意: 启用 JS 执行环境已于本轮加确认门槛(它实测会破坏本会话 JS 通道),
# 故"正对照"必须带 confirm:true; 不带 confirm 的启用应被拒绝。
must_err("vip_enable_js_env {enable:true} 无 confirm 应拒绝", "browser_vip_enable_js_env",
         {"enable": True}, "需显式确认")
must_ok("vip_enable_js_env {enable:true,confirm:true} 正对照", "browser_vip_enable_js_env",
        {"enable": True, "confirm": True}, "JS执行环境")
must_err("network {} 应拒绝", "browser_network", {}, "不能省略")
must_ok("network {action:'list'} 正对照", "browser_network", {"action": "list"}, None)
must_err("antidetect_presets {} 应拒绝", "browser_antidetect_presets", {}, "不能省略")
# 用 GWL_ID(-12) 而不是 GWL_STYLE(-16) 做这条用例:
# 修复前 style 缺省=0 会真的执行 置窗口属性(type, 0), 用 GWL_STYLE 会把窗口样式位全部清掉
# (含 WS_VISIBLE, 可能使窗口不可见/不可用)。用 GWL_ID 则只是把控件ID置0, 无害,
# 而在修复后两者都会在调用前被守卫拦下 —— 既安全又能验证守卫生效。
must_err("set_window_style {type:GWL_ID} 缺 style 应拒绝", "browser_set_window_style",
         {"type": -12}, "style 不能省略")

print("\n== 4) 还原被改动的状态 ==")
for tag, tool, args in (("还原 mute", "browser_set_mute", {"mute": False}),
                        ("还原 focus", "browser_set_focus", {"focus": True}),
                        ("还原 online", "browser_fingerprint_online", {"value": True}),
                        ("还原 zoom", "browser_set_zoom", {"level": 1.0}),
                        ("还原 js_env", "browser_vip_enable_js_env", {"enable": True}),
                        ("还原 网络日志", "browser_network", {"action": "disable"})):
    e, t, _ = call(tool, args)
    print("  %-16s err=%s %s" % (tag, e, t.replace("\n", " ")[:80]))

print("\n== 汇总 ==")
bad = [x for x in results if not x[1]]
print("  通过 %d / %d" % (len(results) - len(bad), len(results)))
for tag, _, d in bad:
    print("  未通过: %s -> %s" % (tag, str(d)[:140]))
sys.exit(1 if bad else 0)
