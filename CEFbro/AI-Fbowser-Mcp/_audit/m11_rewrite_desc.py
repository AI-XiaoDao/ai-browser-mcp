# -*- coding: utf-8 -*-
r"""M11 — 改写高频工具的短描述

原则(面向 AI 代理):
  1. 说清"做什么 + 前置条件"(AI 才知道何时能用)
  2. 说清"返回什么/失败什么样"(AI 才知道怎么判读)
  3. 去掉无信息量的 "(VIP)" —— 成品已全功能解锁, 该标记只会误导
  4. 控制在 ~70 字内 —— /tools/brief 已存在, 富描述不再直接压垮上下文, 但仍不宜冗长
"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
APPLY = os.environ.get("APPLY", "0") == "1"

NEW = {
    # ---- debugger 家族: 补前置条件与判读方式 ----
    "browser_debugger_enable":
        "启用CDP调试器(Debugger.enable)| 断点类工具的前置步骤; 调用会自动清除与之冲突的反检测项(禁用Debugger检测)",
    "browser_debugger_resume":
        "从断点继续执行(Debugger.resume)| 需页面处于暂停态, 否则返回 页面未处于暂停状态",
    "browser_debugger_stack":
        "取当前暂停点的JS调用栈| 需先 wait_paused 或 flow 让页面暂停",
    "browser_debugger_step_over":
        "单步跳过(执行当前行但不进入被调函数)| 需页面处于暂停态",
    "browser_debugger_step_into":
        "单步进入(进入被调函数内部)| 需页面处于暂停态",
    "browser_debugger_step_out":
        "单步跳出(执行完当前函数并返回调用处)| 需页面处于暂停态",
    "browser_debugger_set_breakpoint":
        "在URL匹配正则的脚本上设行断点(Debugger.setBreakpointByUrl)| 设完需导航或触发脚本才会命中, 再用 wait_paused 等待",
    "browser_debugger_evaluate":
        "在指定调用帧内求值(Debugger.evaluateOnCallFrame)| 断点处查看变量的主力工具; parse:true 走同步解析",
    "browser_debugger_flow":
        "断点一键流程: enable→设断点→导航→等暂停→帧内求值→resume| 逆向调试首选, 免手工编排6步",
    "browser_debugger_script_source":
        "取断点处脚本源码与上下文行| 无暂停上下文时需显式给 script_id",
    # ---- edit 家族: 说明作用对象; redo 原写"恢复"极易与 resume 混淆 ----
    "browser_edit_undo":  "撤销上一次编辑(原生编辑命令)| 作用于当前焦点元素",
    "browser_edit_redo":  "重做(撤销的逆操作, redo)| 注意不是 resume",
    "browser_edit_cut":   "剪切选中内容到剪贴板| 作用于当前焦点元素",
    "browser_edit_copy":  "复制选中内容到剪贴板| 作用于当前焦点元素",
    "browser_edit_paste": "把剪贴板内容粘贴到当前焦点元素",
    "browser_edit_delete": "删除选中内容| 作用于当前焦点元素",
    "browser_edit_select_all": "全选当前页面/焦点元素内容",
    # ---- fill 家族: 声明是原生CEF通道 + 返回形态 + 已知陷阱 ----
    "browser_fill_set_value": "填表(原生CEF, 非JS注入): 设置输入元素的值| selector 未命中时仍返回成功, 建议先用 fill_exists 校验",
    "browser_fill_click":     "填表(原生CEF, 非JS注入): 点击元素| selector 未命中时仍返回成功",
    "browser_fill_focus":     "填表(原生CEF): 让元素获得焦点",
    "browser_fill_scroll":    "填表(原生CEF): 滚动到元素所在位置",
    "browser_fill_exists":    "填表(原生CEF): 判断元素是否存在| 异步返回, 用 mcp_result 取 exists 布尔值",
    "browser_fill_attr_set":  "填表(原生CEF): 设置元素属性| 已禁用 href/src/action/formaction 与 on* 事件属性",
    "browser_fill_attr_get":  "填表(原生CEF): 取元素属性值| 异步返回, 用 mcp_result 取 value",
    "browser_fill_trigger":   "填表(原生CEF): 触发元素事件(默认 click)| 可绕过部分前端的手势/可信事件校验",
    "browser_fill_select":    "填表: 设置 <select> 选中项| 优先按 value 走原生 setter 并冒泡 input/change(兼容 React 受控组件)",
    # ---- 其余高频 ----
    "browser_back":    "后退一页| 无导航历史时返回失败",
    "browser_forward": "前进一页| 无导航历史时返回失败",
    "browser_find":    "页面内查找文本并高亮| 返回匹配总数/当前序号; 用 stop_find 停止",
    "browser_download_image": "下载图片到 Downloads 目录| 异步, 用 mcp_result 取保存路径",
    "browser_is_loading": "查询页面是否正在加载| 取自 CEF OnLoadStart/End 状态, 比读 JS readyState 更可靠",
    "browser_get_url": "取当前页面URL| 即时同步返回(读 CEF 缓存值, 不执行JS)",
    "browser_get_id":  "取当前操作目标浏览器的ID| 未显式指定 browser_id 时即为已有网页的主浏览器",
    "browser_get_zoom": "取当前缩放级别(如 1.0)",
    "browser_clear_cache": "清理CEF全局缓存| 异步; 影响所有浏览器实例, 不只当前页",
    "browser_delete_cookies": "删除所有域名下全部Cookie| 破坏性操作, 必须传 confirm:true",
    "browser_create": "新建一个可见浏览器窗口(默认 about:blank)| 需要浏览器级隔离时使用, 常规自动化无需手动创建",
}

lines = io.open(os.path.join(SRC, "MCP_Server.wsv"), encoding="utf-8").read().split("\n")
stat = {"ok": 0, "miss": 0, "skip": 0}
missed = []
for tool, desc in NEW.items():
    pat = re.compile(r'(添加工具JSON\s*\(\s*"' + re.escape(tool) + r'"\s*,\s*)"[^"]*"')
    hit = False
    for i, l in enumerate(lines):
        if pat.search(l):
            if "\r" in l:
                pass
            lines[i] = pat.sub(lambda m: m.group(1) + '"' + desc + '"', l, count=1)
            hit = True
            stat["ok"] += 1
            break
    if not hit:
        stat["miss"] += 1
        missed.append(tool)

print("改写: 成功 %d, 未命中 %d" % (stat["ok"], stat["miss"]))
if missed:
    print("未命中:", missed)

if APPLY:
    io.open(os.path.join(SRC, "MCP_Server.wsv"), "w", encoding="utf-8",
            newline="").write("\n".join(lines))
    print("已写入")
else:
    print("(dry-run, 加 APPLY=1 才写入)")

# 抽样展示
print()
print("--- 抽样 ---")
for t in ["browser_debugger_flow", "browser_edit_redo", "browser_fill_set_value",
          "browser_back", "browser_delete_cookies"]:
    for l in lines:
        if ('添加工具JSON ("' + t + '"') in l:
            print("  %s" % l.strip()[:170])
            break
