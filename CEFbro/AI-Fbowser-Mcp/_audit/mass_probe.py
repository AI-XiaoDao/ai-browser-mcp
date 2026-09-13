# -*- coding: utf-8 -*-
"""全工具真机批量探测 (objective 第1项: 逐个真实 tools/call)。

与上一轮 m1_probe.py 的区别:
  1) 参数不再硬编码 —— 从 /tools/list 的实时 inputSchema 推导, 覆盖全部注册工具
  2) 枚举型参数从 description 里抽取候选值 (如 "modify/replace_data/..." 取首个安全项)
  3) 致命工具拒探清单 (会杀掉服务进程, 探测中途断线)
  4) 布尔参数按语义择值 (enable 类取 true, 其余取 false), sync_wait 恒取 false 保持探测快
  5) 结果落盘 _probe_result.json, 便于反复分析而不必重探

用法: py -3 mass_probe.py            # 全量
      py -3 mass_probe.py --limit 20 # 冒烟
"""
import io
import json
import os
import re
import socket
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe_result.json")

# 探测这些工具会终止服务进程 (文档: "关闭浏览器窗口将退出程序"), 会导致后续全部断线
LETHAL = {
    "browser_shutdown", "browser_close", "browser_close_all", "browser_quit",
    "browser_exit", "browser_kill", "browser_close_try", "browser_destroy",
}
# 会改变网络/进程级全局状态, 探测后可能影响其余工具的判定
MUTATING_SKIP = {
    "browser_set_s5_proxy",     # 设了代理会影响后续所有导航
    "browser_set_preference",   # 改 Chromium 首选项, 需重启生效且影响全局
    # ★ 第 164 轮新增: 该工具把地址**持久化**(新浏览器自动应用), 通用探针的占位地址会污染整场后续会话;
    #   受控实测见 verify_round164_s5prompt(8/8, 测后立即 clear)。
    "browser_set_proxy",
    # ★ 第 165 轮新增: 真实创建**新标签浏览器**(browser_list 多一个 id), 通用探针空参会污染后续所有
    # 多浏览器判定。受控实测见 verify_round165_newtab(9/9, 测后即关闭新标签)。
    "browser_vip_new_tab",
    # ★ 第 70 轮新增: 该工具会**真的热替换页面里某个脚本的源码**(Debugger.setScriptSource)。
    # 通用探针给 source 的是占位串(如 "mcp_probe", 语法上恰好合法), 一旦真替换, 页面脚本被改成
    # 一个标识符表达式 —— 破坏页面并污染其后所有判定。
    # 值得记一笔的时序: 在第 69 轮修掉"缺键被当成真"的读取缺陷**之前**, 它的 dry_run 恒被读成真,
    # 所以探针其实一直在"只验证不替换"; 缺陷修好后默认值才真正生效(false=真替换),
    # 于是这个工具**从"安全的假测"变成了"危险的探测"** —— 修好一个缺陷会改变别处的风险面, 必须回头补防护。
    "browser_reverse_patch",
    # ★ 第 123 轮**实测**新增: 内核级输入注入族(鼠标/触摸/键盘)。
    # 实测(干净实例, 两次复现): 注入前 execute_js 0.03s / cdp_call 0.03s;
    #   调 browser_vip_mouse_click 之后 execute_js 30.09s、cdp_call 30.02s 报错, +3 秒复测仍 35.15s 报错
    #   —— 不是"延迟失效", 而是**本会话内持续失效**, 只有重启进程能恢复。
    # 故这一族在连测里必须跳过: 它们自己那一次会 pass, 却把**其后所有** CDP 优先工具一起带坏。
    # (项目对 browser_vip_key_input 的工具文案也早已自述同一效果。) 需要复验请单开一轮并在其后立刻重启。
    "browser_vip_mouse_click", "browser_vip_mouse_press", "browser_vip_mouse_release",
    "browser_vip_mouse_move", "browser_vip_mouse_wheel",
    "browser_vip_touch_press", "browser_vip_touch_release", "browser_vip_touch_move",
    "browser_vip_touch_cancel",
    "browser_vip_key_click", "browser_vip_key_press", "browser_vip_key_release",
    "browser_vip_key_input", "browser_vip_key_type",
    # ★ 第 156 轮新增: 这两者前置"启用执行环境"(毒化 CDP, 需重启恢复), 通用探针给不出该前置,
    # 且测完会污染其后所有判定。受控实测已落账(OK_LIVE), 连测必须跳过。
    "browser_vip_enable_js_env", "browser_vip_execute_js_context",
    # ★ 第 167 轮(334 回合全量扫测): 真改页面 DOM(innerHTML), 通用探针会污染其后所有
    # 页面内容断言(如 browser_scrape 期待 Example Domain 正文)。受控实测见 verify_round142f。
    "browser_dom_set_html",
    # ★ 第 170 轮(全量扫测实测): UA 指纹设置立即重启渲染器, 本会话 CDP 通道永久失效
    # (其后活体短探连败、每工具 15~40 秒白等, 只能重启恢复)。受控 verify 后再单独复测。
    "browser_fingerprint_ua",
}

# 必须显式指定参数的工具 (否则会因"缺省值具有破坏性"污染后续探测结果)
# 教训: 首轮全量探测时 browser_vip_enable_inspector 的 enable 非必填, 探测未传参,
# 于是它走 else 分支把 CDP 监管者关掉了 —— 此后所有 CDP 类工具的 TIMEOUT 都不可信。
SPECIAL_ARGS = {
    "browser_vip_enable_inspector": {"enable": True},
    # ★ 第 167 轮(334 回合全量扫测)新增: 这些工具的参数按语义补真实无害值, 否则通用探针
    # 要么缺必填(expression 为空 → 工具如实拒绝, 测不到真路径), 要么给非法枚举
    # (action="mcp_probe" → 如实拒绝), 要么选择器指向不存在元素(测不到成功路径)。
    "browser_console_eval": {"expression": "1+1"},
    "browser_kernel_ipc_queue": {"action": "queue"},
    "browser_kernel_ipc_clear": {"action": "clear"},
    "browser_dom_select": {"selector": "h1"},
    # ★ 第 170 轮(全量扫测实测): create 默认建**可见**窗口, 会盖住主窗口触发遮挡节流 →
    # 紧随其后的 browser_mouse_wheel 挂起(该工具在遮挡态下滚轮永不返回)。探针一律后台创建,
    # 不污染用户桌面可见布局; 后台浏览器与可见浏览器同享全部 MCP 能力(实测隔离正确)。
    "browser_create": {"background": True, "url": "https://example.com"},
}

# 参数名 -> 取值 (按语义给"合理且无害"的值)
NAME_HINTS = [
    (re.compile(r"selector|选择器"), "#mcp-probe-nonexistent"),
    (re.compile(r"^url$|url_|地址"), "https://example.com"),
    (re.compile(r"code|script|js|注入代码"), "void 0"),
    (re.compile(r"path|file|文件"), r"C:\Windows\win.ini"),
    (re.compile(r"domain"), "mcp-probe.local"),
    (re.compile(r"host"), "example.com"),
    (re.compile(r"expression|表达式"), "1"),
    (re.compile(r"text|文本|content"), "mcp-probe"),
    (re.compile(r"name|key|id$|_id"), "mcp_probe"),
    (re.compile(r"what|action|mode|type|target|state|level|format"), None),  # 走枚举抽取
    (re.compile(r"directory|dir|目录"), r"C:\Windows"),
]
BOOL_TRUE_HINT = re.compile(r"enable|on$|keep|persist|wait|found|include|force|allow|visible|disable")
# sync_wait 恒 false: 让工具走异步快路径, 单次探测才不会卡满超时
BOOL_FALSE_FORCE = re.compile(r"sync_wait|wait_for_load|async")

ENUM_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]{1,30}(?:/[A-Za-z_][A-Za-z0-9_.\-]{1,30})+")
DESTRUCTIVE_WORD = re.compile(r"clear|delete|remove|reset|stop|close|shutdown|disable|drop|kill|清空|删除|重置|停止|关闭")


def http_post(path, payload, timeout):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def enum_candidates(desc):
    """从描述里抽 a/b/c 形式的候选值。"""
    out = []
    for m in ENUM_RE.finditer(desc or ""):
        parts = m.group(0).split("/")
        for p in parts:
            p = p.strip()
            if p and p not in out:
                out.append(p)
    return out


def pick_value(pname, ptype, desc, tool_desc):
    """为一个参数挑一个合理无害的值。"""
    if pname == "sync_wait":
        return False, "强制异步快路径"
    if ptype == "boolean":
        if BOOL_FALSE_FORCE.search(pname):
            return False, "bool->false(快路径)"
        if BOOL_TRUE_HINT.search(pname):
            return True, "bool->true(语义为启用/保留)"
        return False, "bool->false"
    if ptype == "integer" or ptype == "number":
        if re.search(r"width|height|x$|^x|y$|^y", pname):
            return 10, "坐标/尺寸"
        if re.search(r"ms|timeout|time", pname):
            return 1000, "毫秒"
        if re.search(r"index", pname):
            return 1, "索引"
        if re.search(r"count|max|limit|len", pname):
            return 5, "数量"
        return 1, "integer"
    if ptype == "array":
        return [], "空数组"
    if ptype == "object":
        return {}, "空对象"
    # string
    for rx, val in NAME_HINTS:
        if rx.search(pname):
            if val is not None:
                return val, "名称语义"
            break
    # 枚举型: 从本参数描述优先, 其次工具描述里找 a/b/c
    for src, tag in ((desc, "参数描述枚举"), (tool_desc, "工具描述枚举")):
        cands = enum_candidates(src)
        safe = [c for c in cands if not DESTRUCTIVE_WORD.search(c)]
        if safe:
            return safe[0], tag + "->" + safe[0]
        if cands:
            return cands[0], tag + "(仅剩破坏性项)->" + cands[0]
    return "mcp_probe", "兜底字符串"


# ── 工具级入参覆盖 ──
# 为什么需要: build_args 只填**必填**参数(为减少副作用), 而下面这批工具把关键入参声明成了
# **可选**, 于是探针传空参调用, 撞上工具自己的"缺参守卫"就记成失败 —— 那测的是守卫, 不是实现。
# 这里为它们补上**真实且无害**的入参, 让测试真正打到实现本身。
# 原则: 只补"无副作用 / 副作用可忽略且可逆"的值; 有真实副作用的(下载文件、删除数据、改代理)一律不补。
TOOL_ARG_OVERRIDES = {
    # 需要真实路径的工具: 给一个不存在的 .crx 名(异步提交即回执, 无副作用)
    "browser_vip_load_extension": {"crx_path": "mcp_probe.crx"},
    # 读类: 给一个必然存在的表达式/数据
    "browser_execute_js": {"code": "document.title"},
    "browser_evaluate": {"code": "document.title"},
    "browser_base64_decode": {"data": "aGVsbG8="},   # 合法 base64("hello"); 探针原值 'mcp_probe' 不是合法 base64
    # 枚举型: 取该工具支持且**最无害**的那一项(action=disable 只关订阅, 可逆)
    "browser_kernel_events_all": {"action": "disable"},
    # 类型写错导致必被守卫拦下: set_zoom 的 level 在 schema 里是 text, 兜底值 'mcp_probe' 不是数字
    "browser_set_zoom": {"level": "1.0"},
    # 避免"文件已存在"这条与实现无关的守卫(改成允许覆盖)
    "browser_print_to_pdf": {"overwrite": True},
    # 工作流: 用最无害的一步(只读浏览器状态)
    "workflow_run": {"steps": '[{"tool":"browser_status","args":{}}]'},
    # 这些工具的正确行为是"缺关键入参就拒绝"(GUARD), 于是探针只测到守卫、测不到实现。
    # 补上**真实且无害**的值, 让测试打到实现:
    "browser_mouse_wheel": {"x": 100, "y": 100, "delta_y": 300},   # 页面滚动一次, 无副作用
    "browser_kernel_download": {"action": "list"},                 # 只列进行中的下载, 不发起下载
    # 读类 action(无副作用): 这两者把 action 声明成了可选, 但实现里"省略 action"是**刻意拒绝**
    # (browser_network 原文: 省略会隐式启用网络日志, 故拒绝) ⇒ 不补就只测到守卫。
    "browser_collect": {"action": "get"},        # 只读: 取当前各族监控开关状态
    # 序号类: 通用整数兜底给的是 10, 而测试实例通常只有 1 个浏览器 ⇒ 撞上工具自己的越界守卫。
    # 给 0(第一个浏览器)才是"打到实现"的调用; 越界行为另由 verify_round141.py 专门验证。
    "browser_by_index": {"index": 0},
    "browser_network": {"action": "list"},       # 只读: 列出已记录的网络请求, 不改开关
    "browser_delete_cookies": {"confirm": True},                   # 测试实例上清 cookie, 可接受且能验证实现
    # 通用整数取值 1 不在该工具的合法域内(它只认 -16/-20/-12); 这里**不覆盖** ——
    # 改窗口样式是对宿主窗口的真实副作用(可能把 GUI 窗口样式改坏), 宁可让它记 PARAM 失败。
    # 注意取值必须**符合 schema 类型**: 该参数在 schema 里是 text, 给整数会让工具侧
    # "yyjson取整数"类读取拿到空值(本项目已知: yyjson取文本/整数 对非本类型节点返回空),
    # 于是仍报"version 必须为正整数" —— 第一次写成整数 110 时就是这么失败的。
    "browser_vip_set_css_version": {"version": "120"},             # CSS 版本指纹, 无害
    # ↑ 原来写的是 "110": 该值**不在**工具真实域 116-135 内(见 MCP_Constants.wsv 内核版本最小/最大),
    #   于是即便类型写对(字符串)也会被第二道范围守卫拦下, 仍测不到实现。三个同族工具统一取域内值 120。
    # 同类: 这两个也是 text 型 version, 且工具自身把合法域限定为 116-135(官方API支持值),
    # 通用兜底值不是数字 -> 会被守卫拦下(测到的是守卫不是实现)。取域内值 120。
    "browser_vip_set_web_version": {"version": "120"},
    "browser_vip_set_v8_version": {"version": "120"},
    # 读取器修好后(缺键不再被当成真), 该工具在空参下会**正确地**要求 languages —— 那就测不到实现。
    # 补上真实入参(语言清单无害)以打到实现; 顺带记录: 修好前它空参"通过"其实是 reset 被误当真,
    # 静默复位的假成功。
    "browser_fingerprint_languages": {"languages": "zh-CN,zh,en"},
    # 这两个工具的 enable 是"开关"型: 通用兜底值 mcp_probe 现在会被**正确拒绝**
    # (本轮安全修复: 无法识别的取值不再落进"关闭观察者"分支), 于是探针只测到守卫、测不到实现。
    # 覆盖成**幂等且无害**的开启(只重新注册观察者, 不产生任何破坏性副作用)。
    # 注意: 关闭分支(enable:"false")故意**不**在这里测 —— 它会把 CDP 观察者注销,
    # 污染同批其它 CDP 工具的测量。那条路径由专门脚本覆盖:
    #   _audit/verify_vip_observer_whitelist.py (27/27, 含正对照)
    "browser_vip_enable_devtools_observer": {"enable": True},
    "browser_vip_enable_inspector": {"enable": True},
    # 这两个工具的参数都是"可选但有语义"的: 不给就只测到守卫("需要 object_id 或 function_name")。
    # 给一个**全局存在且完全无副作用**的函数名, 让探针打到实现。
    # 选 parseInt: 它是全局函数(描述里写"如window.sign", 即期望 window 上的名字),
    # 既不产生网络/写操作, 被调用时也只返回 NaN。
    "browser_reverse_cdp_hook": {"function_name": "parseInt"},
    "browser_reverse_call_fn": {"function_name": "parseInt"},
    # browser_reverse_websocket 的 action 只认 enable/query; 通用兜底 "send" 被守卫拦下,
    # 而 query 又需要 request_id -> 取它自己的文档默认动作 enable(在 example.com 上无 WS 流量, 无副作用)。
    "browser_reverse_websocket": {"action": "enable"},
    # browser_reverse_runtime 的**默认 action=properties 却必填 object_id**, 于是空参调用必然失败;
    # 探针改走 evaluate(给一个无副作用的表达式)才能打到实现。
    # 注: "默认动作在空参下永不可用"本身是可用性问题(违反零前置), 已单独记录待改(本轮先如实测量)。
    "browser_reverse_runtime": {"action": "evaluate", "expression": "1+1"},
    # hook_multi 的 functions 是 **JSON数组字符串**(text 型), 通用兜底值不是合法 JSON 数组 ->
    # 只测到守卫。给一个存在且无害的目标(包装 parseInt 不改变其语义), 让探针打到实现。
    "browser_reverse_hook_multi": {"functions": '["parseInt"]'},
    # 同类: 这三个的"关键参数"在 schema 里不是必填, 但缺了只测到守卫 -> 给真实且无害的值。
    # hook: 勾 parseInt(语义保持, 现在的包装器不改变被勾函数行为)
    "browser_reverse_hook": {"target": "parseInt"},
    # trace: 取只读的 get 分支(避免 start 在页面上留插装); targets 是 JSON 数组字符串
    "browser_kernel_reverse_trace": {"action": "get", "targets": '["parseInt"]'},
    # watch_global: names 是 JSON 数组字符串
    "browser_kernel_reverse_watch_global": {"names": '["token"]'},
    # retry: 通用兜底值 tool=mcp_probe 不存在 -> 必然"重试3次后仍失败"。换成一个必然成功的只读工具,
    # 才能真正测到"重试包装"这条实现; 次数压到 1。
    "browser_retry": {"tool": "browser_status", "max_retries": 1},
    # highlight: show 时必填 selector(但 schema 里 selector 不在必填列表) -> 给页面上真实存在的 h1,
    # 并让它 100ms 后自动清除, 不在页面上留高亮框。
    "browser_highlight": {"selector": "h1", "action": "show", "duration_ms": 100},
    # 这三个的"关键参数"不在 schema 必填列表里, 缺了就只测到守卫 -> 给只读、无害的值。
    "browser_reverse_search_script": {"action": "list"},
    "browser_reverse_listeners": {"selector": "document"},
    # dom_resolve: 它把 selector 拼成 document.querySelector(selector) 求 objectId,
    # 所以必须给**页面上真实存在的元素选择器**(给 "document" 会得到 querySelector('document') -> null)。
    "browser_reverse_dom_resolve": {"selector": "h1"},
    # query_objects: 需要原型表达式; example.com 上没有 CryptoJS, 但 Array.prototype 在**任何页面**都存在。
    "browser_reverse_query_objects": {"prototype_expression": "Array.prototype"},
    # await_promise: 需要一个返回 Promise 的表达式。
    "browser_reverse_await_promise": {"expression": "Promise.resolve(1)"},
}

# 需要"先造出目标元素"的工具: 用一行 JS 注入一个输入框, 再让探针去填它。
# 注意: 这条必须放在 TOOL_PRE_CALLS **定义之后** —— 第一版写在 TOOL_ARG_OVERRIDES 后面,
# 于是 import 时就 NameError, 直接把整个台账跑挂了(表现为所有命令都没有输出)。
TOOL_ARG_OVERRIDES["browser_fill_form"] = {
    "fields": '[{"selector":"#mcpProbeInput","value":"mcp-test"}]',
}

# ── 工具级"前置调用" ──
# 有些工具**语义上就依赖某个状态**(不是产品缺前置, 而是调用方必须先进入那个状态)。
# 单次探针无法构造该状态, 于是它们只能记成"超时"——那会把"工具是否可用"这个问题答错。
# 这里为它们声明**最小的前置调用序列**, 由台账在测该工具前按序执行, 并把执行结果写进备注,
# 保证透明(不隐藏任何事实)。
#
# 为什么前置用 browser_debugger_stack: 该项目已实现"零前置自动暂停"(页面未暂停时会自动
# 启用调试器域 + 安排执行点 + Debugger.pause 并等到暂停事件)。所以先调它一次, 页面就真的处于
# 暂停态, 于是 wait_paused 这类"等暂停"的工具立刻能拿到事件 —— 这同时**顺带验证了那条零前置链路**。
TOOL_PRE_CALLS = {
    "browser_debugger_wait_paused": [("browser_debugger_stack", {})],
    # fill_form 需要页面上**真实存在**的表单元素; example.com 没有输入框, 先注入一个。
    "browser_fill_form": [(
        "browser_execute_js",
        {"code": "(function(){if(document.getElementById('mcpProbeInput'))return 'exists';"
                 "var i=document.createElement('input');i.id='mcpProbeInput';i.type='text';"
                 "document.body.appendChild(i);return 'made'})()"})],
}


def build_args(schema, tool_desc, tool_name=None):
    props = (schema or {}).get("properties", {}) or {}
    required = set((schema or {}).get("required", []) or [])
    args, notes = {}, []
    for pname, spec in props.items():
        ptype = (spec or {}).get("type", "string")
        pdesc = (spec or {}).get("description", "")
        # 只填必填参数, 可选参数一律不填 (减少副作用, 且能验证"缺省路径"是否健壮)
        if pname not in required:
            continue
        v, why = pick_value(pname, ptype, pdesc, tool_desc)
        args[pname] = v
        notes.append("%s=%r(%s)" % (pname, v, why))
    # 工具级覆盖: 补上"可选但关键"的入参, 或**换掉**通用取值(让测试打到实现而非守卫)
    # 注意: 必须是"替换"而不是"仅在缺失时补" —— 第一版写成 `pname not in args` 时,
    # 那三个工具的入参恰好都是 required(通用取值已填), 于是覆盖被静默跳过,
    # 结果 base64_decode/kernel_events_all/set_zoom 仍在测"守卫"而不是实现(实测发现)。
    for pname, v in (TOOL_ARG_OVERRIDES.get(tool_name) or {}).items():
        # ★ 修(静默吞覆盖): 原来这里写的是 `if pname in props:` —— 参数不在 schema.properties 里时
        #   覆盖会被**悄悄丢掉**(不报错、不进 note, 台账上完全看不出来)。browser_file_dialog 与
        #   browser_forward 的 inputSchema 就是空 {"type":"object"}, 给它们写的覆盖因此永远无效。
        #   现改为无条件赋值, 并在 note 里点明该参数不在 schema 中(如实, 不隐藏事实)。
        old = args.get(pname, "<未填>")
        args[pname] = v
        extra = "" if pname in props else "(注意: 该参数不在 schema.properties 里)"
        notes.append("%s=%r(工具级覆盖, 原值 %r: 通用取值不适用于该工具)%s"
                     % (pname, v, old, extra))
    return args, notes


def classify(tool, args, resp, elapsed, err):
    if err:
        if "timed out" in err or "timeout" in err.lower():
            return "TIMEOUT", err[:200]
        return "TRANSPORT_ERR", err[:200]
    if resp is None:
        return "NO_RESPONSE", ""
    if "error" in resp:
        e = resp["error"]
        code = e.get("code")
        msg = e.get("message", "")
        if code == -32601:
            return "NOTFOUND", msg[:200]
        if code in (-32602, -32600, -32700):
            return "PROTO_ERR", "[%s] %s" % (code, msg[:180])
        return "RPC_ERR", "[%s] %s" % (code, msg[:180])
    res = resp.get("result", {})
    content = res.get("content", [])
    if not content:
        return "ERR_EMPTY", "result 无 content"
    text = ""
    for c in content:
        if isinstance(c, dict):
            text += c.get("text", "") or ""
    text = text.strip()
    is_err = bool(res.get("isError"))
    if is_err:
        # 是否"可行动": 含具体参数名/数值/范围/替代方案/枚举
        actionable = bool(re.search(r"不能为空|必填|需|请|范围|无效|支持|例:|默认|\d", text))
        return ("ERR_GOOD" if actionable else "ERR_WEAK"), text[:220]
    if text == "":
        return "OK_EMPTY_TEXT", "(成功但文本为空)"
    if '"success":false' in text or '"success": false' in text:
        return "ERR_WEAK", text[:220]
    return "OK", text[:160]


def probe_call(name, args, timeout=30, rid=0):
    """探测期调用另一个工具并把回包解成 dict(供"运行期取值"用; 失败返回 {})。

    rid: JSON-RPC 请求 id。**必须可指定** —— 实测(第125轮, _audit/probe_mcp_result_contract.py):
    命令结果按**命令ID**入库, 而 HTTP 客户端的命令ID就是这条 JSON-RPC 的 id, `mcp_result` 正是按它取值;
    故要造"一个真能取到的结果"就必须用可识别的 id 真调一次。
    """
    resp = http_post("/mcp", {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                              "params": {"name": name, "arguments": args}}, timeout)
    r = (resp or {}).get("result") or {}
    txt = "".join(it.get("text") or "" for it in (r.get("content") or [])
                  if it.get("type") == "text")
    try:
        return json.loads(txt)
    except Exception:
        return {}


# 运行期取值表: 参数的**真值每次启动都不同**, 预置任何常量都只会测到"目标不存在"。
def _network_body_args(_c):
    """为 browser_network_body 造一个**真能成功**的运行期目标。

    背景(第125轮实测): 该工具原先只收 request_id, 而项目里没有任何工具回传 CDP requestId
    —— 台账长期以 TARGET 失败记录("No resource with given identifier found"), 那是**前置缺失**,
    不是功能缺陷。工具现在支持按 url 自动解析 requestId(并自动开启 Network 捕获), 故这里如实
    模拟真实用法: ①订阅 Network.* ②发起一次**带时间戳**的请求(避免同址导航的"未重复导航"快路径
    导致不发请求) ③把该 URL 交给工具, 由它自己解析 requestId 并取响应体。
    """
    try:
        probe_call("browser_kernel_cdp_monitor", {"action": "add", "methods": "Network.*"})
    except Exception:
        pass
    u = "https://example.com/?nb_probe=%d" % int(time.time())
    try:
        probe_call("browser_navigate", {"url": u, "wait_for_load": True})
    except Exception:
        pass
    return {"url": u}


def _async_task_id():
    """造一个**已完成**的异步任务 id(供 mcp_result 用)。"""
    r = probe_call("browser_navigate", {"url": "https://example.com/?async_probe=%d" % int(time.time()),
                                        "async_only": True}, timeout=20)
    for key in ("task_id", "request_id", "id"):
        v = r.get(key)
        if isinstance(v, str) and v and v not in ("1", "0"):
            return v
    d = r.get("data") if isinstance(r.get("data"), dict) else {}
    for key in ("task_id", "request_id", "id"):
        v = (d or {}).get(key)
        if isinstance(v, str) and v:
            return v
    return ""


def _mcp_result_args(_c):
    """mcp_result 的真实契约(第125轮实测确认, _audit/probe_mcp_result_contract.py):
    结果按**命令ID**入库 —— 对 HTTP MCP 客户端而言就是那次调用的 JSON-RPC id(实测 id=4242 → 可取回;
    没调过的 id → 明确"未找到任务结果"); 异步/等待型工具还会额外回一个内部 `task_id`(如 task_xxx),
    两者都能取, 但语义分别是"那次调用的即时结果"与"该等待任务的实时/最终状态"。

    原先探针用假 id `mcp_probe` → 台账长期记成 TARGET 失败, 那是**探针假目标**, 不是功能缺陷。
    这里改成: 用一个独特 id 真调一次(留下可辨识结果) → 再按该 id 取。
    """
    rid = 990000 + int(time.time()) % 10000
    probe_call("browser_execute_js", {"code": "'MCPRESULT_PROBE_%d'" % rid}, rid=rid)
    return {"request_id": str(rid)}


def _window_style_args(_c):
    """browser_set_window_style 原先用 type=1 探测 -> 被白名单拒绝(探针假目标)。
    改为运行期**读回当前 GWL_STYLE 再原值写回**(等价于一次无副作用的真调用, 且可回读验证)。"""
    r = probe_call("browser_get_window_style", {})
    d = r.get("data") if isinstance(r.get("data"), dict) else {}
    raw = (d or {}).get("style", r.get("style"))
    try:
        style = int(str(raw))
    except Exception:
        return {}
    return {"type": -16, "style": style}


DYNAMIC_ARGS = {
    # 实测: 一直用假句柄 1 探测 -> 台账长期记"未找到窗口句柄为 1 的浏览器";
    # 换成 browser_get_window_handle 的真实句柄后立刻成功(返回 {id,url})。
    "browser_find_by_hwnd": lambda _c: {
        "hwnd": int((probe_call("browser_get_window_handle", {}) or {}).get("hwnd") or 0)},
    # 第135轮: 两个"确认闸门"也必须按 schema 传 confirm=true —— 不传会被**刻意**拒绝,
    # 台账若照旧只传默认参数, 就会永远记一条"未传 confirm"的假失败(与"探针假目标"同类)。
    # 注意: 这两条都有**不可逆副作用**(会打死本会话 JS 通道), 故**测完必须重启实例**。
    "browser_vip_enable_js_env": lambda _c: {"enable": True, "confirm": True},
    "browser_reverse_instrument_script": lambda _c: {"action": "install", "confirm": True},
    # 第135轮: 内核级滚轮**必须给滚动量**(缺它会被守卫拒绝 —— 台账因此长期记 GUARD 失败,
    # 那是"探针没给参数"而不是功能缺陷)。给一个真实滚动量后应能 pass; 注意本族会污染本会话 CDP 通道,
    # 故测完**必须重启实例**(已记录在案)。
    "browser_vip_mouse_wheel": lambda _c: {"x": 200, "y": 200, "delta_y": 120},
    # 第125轮: 把两个"探针假目标"改成运行期真值(工具本身没问题, 是探针没给真目标)
    "browser_network_body": _network_body_args,
    "mcp_result": _mcp_result_args,
    "browser_set_window_style": _window_style_args,
}


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    t0 = time.time()
    try:
        tl = http_get("/tools/list", timeout=20)
    except Exception as ex:
        print("!! 无法读取 /tools/list: %s" % ex)
        print("请先启动 AI-Fbowser-Mcp.exe")
        return
    tools = tl.get("tools", [])
    print("发现工具 %d 个" % len(tools))

    # 预置一个真实页面, 让依赖页面的工具能正常执行
    try:
        http_post("/mcp", {"jsonrpc": "2.0", "id": 0, "method": "tools/call",
                           "params": {"name": "browser_navigate",
                                      "arguments": {"url": "https://example.com",
                                                    "sync_wait": True}}}, 30)
        print("预置页面: https://example.com")
    except Exception as ex:
        print("预置页面失败(继续): %s" % ex)

    results = []
    for i, t in enumerate(tools):
        if limit and i >= limit:
            break
        name = t.get("name")
        desc = t.get("description", "")
        schema = t.get("inputSchema", {})
        # 必须把工具名传进去: build_args 用它查 TOOL_ARG_OVERRIDES。
        # (实测缺陷: 这里原先漏传 name, 于是**整张 TOOL_ARG_OVERRIDES 表在本入口完全失效**,
        #  工具仍收到通用兜底值 mcp_probe/1, 测到的只是守卫而不是实现。
        #  证据: 一次 probe 结果里 browser_vip_set_css_version 实际收到 "version":"mcp_probe"。)
        # tool_ledger.py 一直有传, 故台账不受此影响。
        args, notes = build_args(schema, desc, name)
        if name in SPECIAL_ARGS:
            args = dict(SPECIAL_ARGS[name])
            notes = ["显式指定(防破坏性缺省值污染后续探测)"]
        # 运行期取值: 有些参数**无法预置**(句柄/任务ID 之类每次启动都不同), 必须先真调一次再填。
        # 实测: browser_find_by_hwnd 一直用假句柄 1 探测, 于是台账长期把它记成"未找到窗口句柄为 1 的浏览器";
        # 改用真实句柄后立刻成功(返回 {id,url}), 说明那是**探针假目标**而非功能缺陷。
        if name in DYNAMIC_ARGS:
            try:
                extra = DYNAMIC_ARGS[name](None)
                if extra and all(v not in (0, "", None) for v in extra.values()):
                    args = dict(args)
                    args.update(extra)
                    notes = list(notes) + ["运行期取值: %s" % sorted(extra.keys())]
                else:
                    notes = list(notes) + ["运行期取值失败(保持通用值): %r" % (extra,)]
            except Exception as ex:
                notes = list(notes) + ["运行期取值失败: %r" % ex]
        row = {"name": name, "args": args, "arg_notes": notes,
               "required": (schema or {}).get("required", [])}
        if name in LETHAL:
            row.update({"verdict": "SKIP_LETHAL", "detail": "会终止服务进程", "elapsed": 0})
            results.append(row)
            print("[%3d/%d] %-42s SKIP_LETHAL" % (i + 1, len(tools), name))
            continue
        if name in MUTATING_SKIP:
            row.update({"verdict": "SKIP_MUTATING", "detail": "全局副作用", "elapsed": 0})
            results.append(row)
            print("[%3d/%d] %-42s SKIP_MUTATING" % (i + 1, len(tools), name))
            continue

        st = time.time()
        resp, err = None, None
        try:
            resp = http_post("/mcp", {"jsonrpc": "2.0", "id": 10000 + i,
                                      "method": "tools/call",
                                      "params": {"name": name, "arguments": args}}, 12)
        except Exception as ex:
            err = str(ex)
        el = time.time() - st
        verdict, detail = classify(name, args, resp, el, err)
        row.update({"verdict": verdict, "detail": detail, "elapsed": round(el, 2),
                    "raw": json.dumps(resp, ensure_ascii=False)[:1200] if resp else None})
        results.append(row)
        print("[%3d/%d] %-42s %-14s %5.2fs %s"
              % (i + 1, len(tools), name, verdict, el, detail[:70]))

    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(results, ensure_ascii=False, indent=1))

    print()
    print("=" * 100)
    print("汇总 (耗时 %.1fs, 结果已存 _probe_result.json)" % (time.time() - t0))
    print("=" * 100)
    tally = {}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("  %-18s %d" % (k, tally[k]))
    print("  总计               %d" % len(results))


if __name__ == "__main__":
    main()


# ============================================================================
# 失败分诊(_audit/_failure_triage.md)落地的 A 类覆盖 —— 追加在**文件末尾**,
# 用 .update() 保证不依赖上面两个表的定义顺序(曾因顺序问题把 import 弄崩过)。
# 依据逐条见分诊文档 §2; 这里只写"给什么值", 理由见文档。
# ============================================================================

# A-1 读/交互类: 分诊确认 h1 在页面上真实存在(browser_highlight{selector:h1}->highlighted:1,
# browser_reverse_dom_resolve{selector:h1}->object_id 非空); 点 h1 没有事件处理器,
# 不会导航(对比: 点 a 会跳 iana.org 污染后续测量, 故不用 a)。
TOOL_ARG_OVERRIDES.update({
    # 哈希工具: 探针必须同时给 action 与 data, 否则会被"空串摘要无意义"守卫正确拒绝
    "browser_hash": {"action": "md5", "data": "mcp_probe"},
    "browser_dom_query": {"selector": "h1"},
    "browser_dom_rect": {"selector": "h1"},
    "browser_dom_inner_html": {"selector": "h1"},
    "browser_dom_click": {"selector": "h1"},
    "browser_fill_click": {"selector": "h1"},
    "browser_fill_focus": {"selector": "h1"},
    "browser_fill_scroll": {"selector": "h1"},
    "browser_fill_trigger": {"selector": "h1"},
})

# A-2 需要"真实可写控件": example.com 现行版本没有 input/checkbox/select,
# 所以这几个工具**给什么 selector 都打不到实现** -> 先注入控件再指向它们。
_TOUCH_PROBE_JS = (
    "(function(){"
    "if(document.getElementById('mcpProbeSelect'))return 'exists';"
    "var i=document.createElement('input');i.id='mcpProbeInput';i.type='text';document.body.appendChild(i);"
    "var c=document.createElement('input');c.id='mcpProbeCheck';c.type='checkbox';document.body.appendChild(c);"
    "var s=document.createElement('select');s.id='mcpProbeSelect';"
    "var o1=document.createElement('option');o1.value='mcpA';o1.text='A';s.appendChild(o1);"
    "var o2=document.createElement('option');o2.value='mcpB';o2.text='B';s.appendChild(o2);"
    "document.body.appendChild(s);return 'made';})()"
)
_TOUCH_PRE = ("browser_execute_js", {"code": _TOUCH_PROBE_JS})
TOOL_PRE_CALLS.update({
    "browser_dom_checked": [_TOUCH_PRE],
    "browser_dom_selected": [_TOUCH_PRE],
    "browser_dom_set_value": [_TOUCH_PRE],
    "browser_fill_set_value": [_TOUCH_PRE],
    "browser_fill_select": [_TOUCH_PRE],
})
TOOL_ARG_OVERRIDES.update({
    "browser_dom_checked": {"selector": "#mcpProbeCheck"},
    "browser_dom_selected": {"selector": "#mcpProbeSelect"},
    "browser_dom_set_value": {"selector": "#mcpProbeInput", "value": "mcp-test"},
    "browser_fill_set_value": {"selector": "#mcpProbeInput", "value": "mcp-test"},
    "browser_fill_select": {"selector": "#mcpProbeSelect", "value": "mcpA"},
})

# A-3 真实 HTML 属性: 页面上的 <a href=...>Learn more</a> 必然带 href(双重佐证);
# attribute 在 schema 里是可选 -> 探针从不填。
TOOL_ARG_OVERRIDES.update({
    "browser_fill_attr_get": {"selector": "a", "attribute": "href"},
    "browser_fill_attr_set": {"selector": "a", "attribute": "data-mcp-probe", "value": "1"},
})

# A-4 缺"语义必填"入参的守卫类(值都取只读/无副作用的那个分支)。
TOOL_ARG_OVERRIDES.update({
    "browser_wait": {"what": "selector", "value": "h1"},
    "browser_intercept": {"action": "clear"},
    # file_dialog 的 schema 没有 properties -> 依赖上面的"无条件赋值"修复才生效。
    "browser_file_dialog": {"path": r"C:\Windows\win.ini"},
    "workflow_get": {"name": "hello"},
    "browser_cdp_call": {"method": "Runtime.evaluate",
                         "params": "{\"expression\":\"1\",\"returnByValue\":true}"},
    "browser_kernel_auth": {"action": "list"},
    "browser_kernel_scheme": {"action": "list"},
    # 这两个实现**已支持未写入文档的 list 只读分支**(信息更多、副作用更小) -> 用 list。
    "browser_kernel_reactor": {"action": "list"},
    "browser_kernel_watch": {"action": "list"},
    "browser_vip_execute_js_context": {"code": "document.title"},
    "browser_vip_dom_search": {"query": "Example Domain"},
    # 节点编辑: selector 路径(抗映射重建), 只给 h1 加一个探针属性(无害), 命中真实实现而非守卫
    "browser_vip_dom_node_edit": {"action": "set_attr", "selector": "h1",
                                  "attr_name": "data-mcp-probe", "value": "1", "confirm": True},
    # VIP 过滤器: 注册在**不存在资源**地址上的改写/替换(只登记, 不加载即无副作用), 命中真实实现而非守卫
    "browser_vip_filter_patch_text": {"url": "https://example.com/mcp-probe-patch.txt",
                                      "find": "x", "replace": "y"},
    "browser_vip_filter_replace_data": {"url": "https://example.com/mcp-probe-replace.txt",
                                        "body": "mcp-probe"},
    "browser_vip_filter_replace_file": {"url": "https://example.com/mcp-probe-replacefile.txt",
                                        "file": "mcp_config.json"},
})

# A-5 需要"先造状态"的 4 个。
TOOL_ARG_OVERRIDES.update({
    "browser_cdp_event": {"event_name": "Debugger.paused"},
})
TOOL_PRE_CALLS.update({
    # 与已通过的 browser_debugger_wait_paused 同款手法: stack 会触发零前置自动暂停,
    # 之后 Debugger.paused 会被写进 cdp_event:Debugger.paused 异步缓存。
    "browser_cdp_event": [("browser_debugger_stack", {})],
    # 这两个只在 Debugger.paused 时有效 -> 同样先自动暂停。
    "browser_reverse_return_value": [("browser_debugger_stack", {})],
    "browser_reverse_set_variable": [("browser_debugger_stack", {})],
    # find_by_tag: 先按探针的通用 tag 值("mcp_probe")建一个带标识的后台浏览器,
    # 这样它查得到 -> 台账能真正测到实现(此前该工具在本 MCP 内不可能成功; 详见报告 §106)。
    "browser_find_by_tag": [
        ("browser_create", {"url": "https://example.com/?tagprobe=1",
                            "background": True, "tag": "mcp_probe"}),
    ],
    # 前进历史: 连续两次导航再后退, 产生 forward 栈(wait_for_load=False 只为造历史, 不必等载入)。
    "browser_forward": [
        ("browser_navigate", {"url": "https://example.com", "wait_for_load": False}),
        ("browser_navigate", {"url": "https://example.com/?mcpForwardProbe=1", "wait_for_load": False}),
        ("browser_back", {}),
    ],
})


# ============================================================================
# 调试器族的真机测量前置 —— 用 `//# sourceURL` 让注入脚本带上**真实 URL**,
# 从而 setBreakpointByUrl 能匹配到(此前本页脚本 url 全为空串, urlRegex 永远 0 位置)。
# 依据: _audit/diag_sourceurl_breakpoint.py 实测(auto 用该正则命中 2 次, 对照臂 0 命中)。
# ============================================================================

# 幂等注入: 已有则直接返回。第 2 行声明变量 v, 第 3 行是 return —— 断在第 3 行可拿到
# **返回位置**的帧, 这正是 Debugger.setReturnValue / setVariableValue 需要的位置。
_BP_PROBE_LINES = [
    "window.mcpBpTick=0;",
    "window.mcpBpFn=function mcpBpFn(){",
    "  var v=1;",
    "  return v;",
    "};",
    "window.mcpBpTimer=setInterval(window.mcpBpFn,300);",
    "//# sourceURL=https://example.com/mcp-breakpoint-probe.js",
]
_BP_PROBE_SRC = "\n".join(_BP_PROBE_LINES)
_BP_INJECT = ("browser_execute_js", {
    "code": ("(function(){if(window.mcpBpTimer)return 'exists';"
             "var s=document.createElement('script');s.textContent=%s;"
             "document.body.appendChild(s);return 'ok'})()" % __import__('json').dumps(_BP_PROBE_SRC))})

# 停在探针脚本第 3 行(0 起算)的返回语句上, 且**不自动 resume** -> 后续工具能用到这个活帧
_BP_PAUSE = ("browser_debugger_flow", {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                                      "resume": False, "max_ms": 8000})

TOOL_PRE_CALLS.update({
    "browser_debugger_auto": [("browser_debugger_enable", {}), _BP_INJECT],
    "browser_debugger_flow": [("browser_debugger_enable", {}), _BP_INJECT],
    # 这两个需要"停在断点上的活帧", 故再加一步 flow(resume:false)
    "browser_reverse_return_value": [("browser_debugger_enable", {}), _BP_INJECT, _BP_PAUSE],
    "browser_reverse_set_variable": [("browser_debugger_enable", {}), _BP_INJECT, _BP_PAUSE],
})
TOOL_ARG_OVERRIDES.update({
    # 命中应很快(探针每 300ms 调一次该函数)
    "browser_debugger_auto": {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                              "max_ms": 8000, "max_hits": 2},
    "browser_debugger_flow": {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                              "max_ms": 8000},
    "browser_reverse_return_value": {"value": "true"},
    "browser_reverse_set_variable": {"variable_name": "v", "value": "42"},
})


# 修正上面的 _BP_INJECT: 幂等判据不可靠(clearInterval 后变量仍是真值 -> 跳过重装 -> 定时器已死),
# 改为**无条件重装**: 先清旧定时器, 再注入新脚本。放在定义之后重新赋值, 不依赖顺序。
_BP_INJECT = ("browser_execute_js", {
    "code": ("(function(){if(window.mcpBpTimer){try{clearInterval(window.mcpBpTimer)}catch(e){}}"
             "var s=document.createElement('script');s.textContent=%s;"
             "document.body.appendChild(s);return 'installed'})()"
             % __import__('json').dumps(_BP_PROBE_SRC))})
# 前置链里引用的是同一个名字, 重新注册一遍确保取到新值
for _t in ("browser_debugger_auto", "browser_debugger_flow",
           "browser_reverse_return_value", "browser_reverse_set_variable"):
    _chain = list(TOOL_PRE_CALLS.get(_t) or [])
    TOOL_PRE_CALLS[_t] = [(n, (_BP_INJECT[1] if n == "browser_execute_js" else a)) for n, a in _chain]

# ---------------------------------------------------------------------------
# 第 97 轮修复后补的覆盖值
# ---------------------------------------------------------------------------
TOOL_ARG_OVERRIDES.update({
    # 第121轮: 该工具改为**真契约** —— type 必填, 且 type=1/2 必须同时给 devices 设备清单
    # (旧版只传 type 时内核收到的是空清单却回"已设置"= 假成功)。探针必须按新契约给全套参数,
    # 否则打到的永远是"缺 devices"守卫而不是实现。
    "browser_vip_fingerprint_media_devices": {
        "target": "audio_input", "type": 1,
        "devices": "[{\"device_id\":\"default\",\"label\":\"MCP探针麦克风\",\"group_id\":\"mcp_probe\"}]"},
    # enable 现在**要求** url_pattern(刻意不默认"拦截全部": 无放行通道会把页面挂死),
    # 而 build_args 只填 required 参数, 于是探针打到的永远是守卫而不是实现。
    # 给一个**匹配不到任何真实流量**的模式: 既能验证 enable 真的被内核接受, 又不会挂住页面。
    "browser_reverse_network_intercept": {"url_pattern": "*mcp-probe-never-matches*"},
    # 显式给 profile 一个"取回数据"的完整动作(默认 start 只开采样)
    "browser_reverse_profile": {"action": "query"},
    # 第99轮: 这几个工具改成同步后, 通用填充值会打到"守卫/目标不存在"而非实现, 故补合法覆盖值
    "browser_reverse_cdp_hook": {"function_name": "parseInt"},
    "browser_reverse_dom_breakpoint": {"type": "xhr", "url": "*mcp-probe-never-matches*"},
    "browser_reverse_websocket": {"action": "enable"},
    "browser_reverse_preload": {"code": "void 0"},
    "browser_cdp": {"method": "Runtime.evaluate",
                    "params": "{\"expression\":\"document.title\",\"returnByValue\":true}"},
    # browser_intercept 原先只测到 action=clear(最平凡的分支); 改用 unmodify 指向一个
    # **永不匹配**的域名: 幂等成功(0 条)、不改变任何状态, 却能真正走一遍新实现的规则解析路径。
    "browser_intercept": {"action": "unmodify",
                          "url": "https://mcp-probe-never-matches.invalid/"},
    # browser_context_menu: 探针会填 action=set 但不给 items(被如实拒绝);
    # 改用只读的 get —— 真正走一遍状态汇总路径且**不改变任何状态**
    # (施加路径由 _audit/verify_context_menu.py 的 8/8 行为验收覆盖)。
    "browser_context_menu": {"action": "get"},
    # innerText 读写(第110轮新增): 通用填充值 "#mcp-probe-nonexistent" 会打到"元素不存在"守卫,
    # 改为读页面上真实存在的 h1(只读、无副作用)。
    "browser_fill_get_text": {"selector": "h1"},
    # set_text 是**写**操作: 先注入一个专用探针元素再写它, 避免改动页面既有内容而影响同轮其它用例。
    "browser_fill_set_text": {"selector": "#mcpProbeText", "text": "mcp-probe-text"},
})
# 写类工具的专用探针元素(与既有做法一致: 先 TOOL_PRE_CALLS 注入, 再对它操作)
TOOL_PRE_CALLS.setdefault("browser_fill_set_text", []).append(
    ("browser_execute_js",
     {"code": "document.body.insertAdjacentHTML('beforeend',"
              "'<div id=\"mcpProbeText\">probe</div>');'ok'"}))

