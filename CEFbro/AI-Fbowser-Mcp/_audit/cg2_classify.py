# -*- coding: utf-8 -*-
"""把 363 候选逐条判定, 生成 _classlib_gap_confirmed2.md"""
import io, json, os, re, collections
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
cands = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
covmap = json.load(io.open(os.path.join(HERE, "_cg2_covmap.json"), encoding="utf-8"))
IDX = json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))
TOOLS = IDX["tools"]

def key(c):
    return "%s::%s" % (c["cls"], c["method"])

def tools_for(c):
    v = covmap.get(key(c), [])
    return sorted(set(x["tool"] for x in v if x["tool"]))

# ---------------- 手工判定表 ----------------
# (类, 方法) -> (判定, 途径, 覆盖者/证据, 备注)
D = {}

def put(cls, meth, verdict, route, who, note="", tool="", prio="", reuse=""):
    D["%s::%s" % (cls, meth)] = dict(v=verdict, route=route, who=who, note=note,
                                     tool=tool, prio=prio, reuse=reuse)

V = "类_FBrowserVIP_控制器"
MC = "类_FBrowser_菜单模式"
CL = "类_FBrowser_命令行"
BR = "类_FBrowser_浏览器"
EV = "类_FBrowser_应用事件"

# ===== A 确认缺口 =====
A_CMDLINE = [
    ("FBrowser_命令行_取全局", "P2", "需新写: 取 CEF 全局命令行对象的唯一入口; 无它则任何启动参数工具都无从下手"),
    ("FBrowser_命令行_创建", "P2", "需新写: 自建命令行对象(供测试/预演), 与 取全局 同族"),
    ("插入值", "P1", "复用 main.wsv:459 已覆盖的 `即将处理命令行` 空实现(注: 该事件在 FBrowser_初始化 前派发, 是插入开关的唯一天然落点) + 类_FBrowser_命令行::插入值"),
    ("启用无头模式", "P1", "同上; 现状: 全项目 `--headless` 只出现在 MCP_Stdio.wsv:225 的**服务端**参数判定, 与浏览器无头模式无关"),
    ("设置远程调试端口", "P1", "同上; 现状: src 全库 0 命中 `remote-debugging`"),
    ("启用自动播放", "P1", "同上(媒体自动化前置)"),
    ("启用摄像头", "P2", "同上"),
    ("启用录音", "P2", "同上"),
    ("启用单进程模式", "P2", "同上"),
    ("启用跨框架操作模式", "P2", "同上"),
    ("忽略GPU禁用清单", "P2", "同上"),
    ("禁用GPU", "P2", "同上(虚拟机/无GPU环境稳定性)"),
    ("禁用GPU缓存", "P2", "同上"),
]
for m, p, r in A_CMDLINE:
    put(CL, m, "A", "无", "类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法", r, "browser_kernel_cmdline", p, r)

put(BR, "FBrowser_创建后台浏览器", "A", "无",
    "src 全库 0 命中 `后台浏览器`/`FBroHsCreate`; 唯一创建入口 browser_create 描述明写「新建一个可见浏览器窗口」(MCP_Server.wsv:9490), 无 background/headless 参数",
    "批量取数核心: 无窗口、占用更低, 类库注释称优于无头模式", "browser_create_background", "P0",
    "main.wsv:202-212 已有一条 `FBrowser_创建浏览器` 的 UI 线程创建路径, 可原样改调 `FBrowser_创建后台浏览器`; 同步版需经 `FBrowser_任务运行器_投递任务`")
put(BR, "FBrowser_创建后台浏览器_同步", "A", "无",
    "同上; 且 `FBrowser_任务运行器_投递任务` 在 src 中 0 调用(对应工具位 browser_task_runner_post 被 MCP_Server_System.wsv:20-22 硬禁用)",
    "同步版返回 类_FBrowser_浏览器, 必须在 UI 线程调用", "browser_create_background", "P0",
    "复用 MCP_Server_System.wsv:9 系统分派器; 需先解禁/改造 task_runner 通道")
put(BR, "移动窗口", "A", "无(工具位恒失败)",
    "browser_move_window 已注册(MCP_Server.wsv:9538)但描述写「⛔ 本工具恒失败」, MCP_Server_Core.wsv:5369 分支直接返回失败; 无任何替代工具能改原生窗口位置/尺寸",
    "注: 需求侧可用 browser_vip_fingerprint_viewport / browser_screenshot(width,height) 做视口仿真, 但改的是视口不是窗口", "browser_move_window(解禁)", "P2",
    "类_FBrowser_浏览器::移动窗口 → FBroHsBrowserHost_MoveWindow, 一行即可接回; 当前被架构(嵌入式主窗口布局)主动禁用")
put(BR, "显示隐藏窗口", "A", "无",
    "src 全库 0 命中 `显示隐藏窗口`/`ShowWindows`; 无工具、无桩位, 也无 CDP 等价(CDP 无隐藏宿主窗口的方法)",
    "多浏览器轮换/降低干扰时常用", "browser_show_window", "P2",
    "类_FBrowser_浏览器::显示隐藏窗口(显示隐藏 逻辑型) → FBroHsBrowserHost_ShowWindows")

# A-3 宿主侧 URL 请求定制
UR = "类_FBrowser_URL请求事件"
put(UR, "开始创建", "A", "无",
    "类库回调 Start(flag, request) 的唯一落点; src 里 类_MCP_URL请求回调(MCP_Callbacks.wsv:723) 只 override 了 获取到数据/读取结束/即将完成, **未 override 开始创建**, 因此无法在发出请求前设置头/体/flag; CDP 无 CEF USRRequest 客户端的对应域",
    "宿主侧 HTTP 客户端(不经页面/CORS)的定制入口", "扩展 browser_create_url_request", "P1",
    "复用 MCP_Callbacks.wsv:723 类_MCP_URL请求回调, 加一个 `开始创建` override; 内部用 URL请求.取请求() 拿到 类_FBrowser_请求 后调用 设置/增加元素/读取流")
put(UR, "上传进度", "A", "无",
    "OnUploadProgress 需先置 UR_FLAG_REPORT_UPLOAD_PROGRESS(= 类_FBrowser_请求::设置标识), 该 flag 无入口; 且 类_MCP_URL请求回调 未 override 本方法",
    "类库注释明确「只有在请求上设置了 UR_FLAG_REPORT_UPLOAD_PROGRESS 标志时才会调用」", "扩展 browser_create_url_request", "P2",
    "同上回调类新增 override; 上传体用 FBrowser_读取流_从文件创建")
RQ = "类_FBrowser_请求"
put(RQ, "设置标识", "A", "无",
    "SetFlags(请求标识: 无/跳过缓存/只使用缓存); src 全库 0 命中; browser_create_url_request 的 schema 只有 url+method(MCP_Server.wsv:9601), 无法置 flag",
    "同时是 上传进度 事件生效的前置条件", "扩展 browser_create_url_request", "P2",
    "MCP_Server_Core.wsv:5505-5514 已构造 类_FBrowser_请求 并 置地址/置类型, 追加一行 设置标识 即可")
put(RQ, "获取地址_首件cookie", "A", "无",
    "GetFirstPartyForCookies; src 0 命中; 出站请求的 cookie 归属域不可读", "", "扩展 browser_create_url_request", "P2",
    "同 设置标识 路径")
put(RQ, "设置地址_首件cookie", "A", "无",
    "SetFirstPartyForCookies; src 0 命中; 无法为宿主侧请求指定 cookie 归属域(带登录态取数的关键)", "", "扩展 browser_create_url_request", "P1",
    "同 设置标识 路径")
PD = "类_FBrowser_POST数据"
put(PD, "增加元素", "A", "无",
    "类_FBrowser_POST数据/CefPostData 的元素数组; src 全库只**读**不写(MCP_Server.wsv:7410/10651 用 取POST数据/取元素), 0 命中 增加元素/移除元素",
    "与 类_FBrowser_请求::设置(…POST数据…) 组合即为「带自定义 body 的 POST」", "扩展 browser_create_url_request", "P1",
    "MCP_Server_Core.wsv:5505 处新建 类_FBrowser_POST数据 并 增加元素(元素含 读取流), 再传给 请求.设置")
put(PD, "移除元素", "A", "无", "同上, 元素数组维护的从属方法", "", "扩展 browser_create_url_request", "P2", "同 增加元素")
put(PD, "移除所有元素", "A", "无", "同上, 元素数组维护的从属方法", "", "扩展 browser_create_url_request", "P2", "同 增加元素")
RS = "类_FBrowser_读取流"
put(RS, "FBrowser_读取流_从数据创建", "A", "无",
    "CefStreamReader 构造; src 全库 0 命中; POST 上传体只能来自内存/文件流, 无流即无 body", "", "扩展 browser_create_url_request", "P1", "需新写(仅在 URL 请求拼装处使用)")
put(RS, "FBrowser_读取流_从文件创建", "A", "无",
    "同上; 从文件建流(上传本地文件作 body)", "", "扩展 browser_create_url_request", "P1", "需新写")

# A-4 原生 V8 扩展
V8E = "类_FBrowser_V8环境"
put(V8E, "FBrowser_V8_注册JS扩展", "B1", "工具名",
    "「页面脚本执行前注入自定义代码」这一能力已由三条现成路径覆盖: ① browser_reverse_preload(Page.addScriptToEvaluateOnNewDocument, 真·先于任何页面 JS); ② browser_inject persist=true —— 实现走 `持久V8扩展列表`(MCP_Server.wsv:1864 加入持久V8扩展) 并由 **浏览器_载入开始** 事件消费(MCP_BrowserEvents.wsv:1537 → MCP_Server.wsv:2088 应用持久V8到框架 → 框架.执行JS代码, 按标识去重); ③ browser_reverse_add_binding(Runtime.addBinding, 原生函数, fn.toString 查不出)",
    "⚠ 残余差异(非缺口但值得知道): 类库此法走 FBroHsRegisterExtension = **原生 V8 扩展**, 在上下文创建期注入且对页面 JS 完全不可见(比 ② 的 `执行JS代码` 更隐蔽); 该原生通道未暴露, 且 类_FBrowser_V8处理程序 的回调通路(给扩展挂原生函数)完全未用。要「不可检测」时请用 ①+③ 组合")
put(V8E, "FBrowser_V8环境_取当前环境", "B4", "非能力项",
    "类库注释「只能在渲染进程中使用」; 本项目渲染进程是 SDK 自带 FBroSubprocess.exe, 该静态方法取的是当前(渲染)进程的上下文", "")
put(V8E, "FBrowser_V8环境_取运行环境", "B4", "非能力项", "同上(GetEnteredContext)", "")

# A-5 菜单模式
MENU = [
    ("添加菜单", "AddItem(命令ID,标签名)"),
    ("添加分隔栏", "AddSeparator()"),
    ("添加Check菜单", "AddCheckItem(命令ID,标签名)"),
    ("添加Radio菜单", "AddRadioItem(命令ID,标签名,群ID)"),
    ("添加子菜单", "AddSubMenu(命令ID,标签名)"),
    ("选中状态", "SetCheck(命令ID,选中)"),
    ("选中状态_索引", "SetCheckedAt(索引ID,选中)"),
    ("存在快捷键", "HasAccelerator(命令ID)"),
    ("存在快捷键_索引", "HasAcceleratorAt(索引ID)"),
    ("设置快捷键", "SetAccelerator(命令ID,键代码,shift,ctrl,alt)"),
    ("设置快捷键_索引", "SetAcceleratorAt(索引ID,键代码,shift,ctrl,alt)"),
    ("移除快捷键", "RemoveAccelerator(命令ID)"),
    ("移除快捷键_索引", "RemoveAcceleratorAt(索引ID)"),
]
for m, sig in MENU:
    put(MC, m, "A", "无",
        "src 0 调用(见本节导语; 类库对应 %s)" % sig,
        "", "browser_context_menu", "P2",
        "复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490)")

# A-6 VIP 残留
put(V, "指纹_清空调用计数", "A", "无",
    "FBroHsVIPControl_ClearFingerCount(只清计数, 保留伪装); browser_fingerprint 只有 action=count(读) 与 action=clear(→ vip_ctrl.清理数据, 是**清掉全部伪装**的 ClearAllData, MCP_Server_Core.wsv:2000), 二者语义不同, 无法只清计数",
    "", "browser_fingerprint action=clear_count", "P2", "MCP_Server_Core.wsv:1986 分支内加一个 action 即可(一行 vip_ctrl.指纹_清空调用计数())")
VG = "FBrowserVIP全局功能"
put(VG, "FBrowser_VIP功能_启用插件高级功能", "A", "无",
    "类库注释: 「必须在加载插件前启用…默认 CEF 不支持插件 content_scripts.js 脚本执行, 启用高级功能后才能支持」; src 全库 0 命中。已有 browser_vip_load_extension / extension_info / unload_extension 三个工具管插件, 却无这个前置开关",
    "", "browser_vip_enable_extension_advanced", "P2", "复用 MCP_Server_VIP.wsv:1322 browser_vip_load_extension 分支, 加载前调用一次")
put(VG, "FBrowser_VIP过滤器_取消修改内容", "A", "无",
    "只支持全局 clear: browser_intercept 的 action=clear 把 资源替换规则/导航拦截规则 **整串清空**(MCP_Server_Core.wsv:2250-2253), 而 src 只有 `添加资源替换规则`(MCP_Server.wsv:6979)、**没有** 移除/删除单条规则的函数",
    "", "browser_intercept action=remove(url)", "P2", "复用 MCP_Server.wsv:6979 添加资源替换规则 的同款规则串(规则格式 `action|url|search|replace|file`), 新写一个按 url 过滤的 移除资源替换规则")
put(VG, "FBrowser_VIP过滤器_取消替换资源", "A", "无", "同上(取消单条替换资源规则, 而非全部)", "", "browser_intercept action=remove(url)", "P2", "同上")
put(VG, "FBrowser_VIP过滤器_修改内容", "B2", "action 枚举", "browser_intercept action=modify(MCP_Server_Core.wsv:2347 真调用 添加资源替换规则)")
put(VG, "FBrowser_VIP过滤器_取消全部修改内容", "B2", "action 枚举", "browser_intercept action=clear(MCP_Server_Core.wsv:2250 清空全部规则)")
put(VG, "FBrowser_VIP过滤器_取消全部替换资源", "B2", "action 枚举", "browser_intercept action=clear")
put(VG, "FBrowser_VIP过滤器_替换资源_数据", "B2", "action 枚举", "browser_intercept action=replace_data(MCP_Server_Core.wsv:2362)")
put(VG, "FBrowser_VIP过滤器_替换资源_文件", "B2", "action 枚举", "browser_intercept action=replace_file(MCP_Server_Core.wsv:2371)")

# A-7 初始化控制残留
IC = "FBrowser初始化控制"
put(IC, "FBrowser_初始化_设置V8环境默认堆栈大小", "A", "无",
    "FBroSetV8DefaultsHeapSize(初始尺寸,最大尺寸); src 全库 0 命中(仅类库自身文档提到); 必须在 FBrowser_初始化 前调用, main.wsv:98 之后无法补救",
    "渲染进程栈溢出崩溃的官方缓解手段", "(启动参数通道) browser_kernel_initsetting", "P2",
    "复用 main.wsv:75-98 的 设置 块, 在 FBrowser_初始化 之前根据启动参数/env 调用")
put(IC, "FBrowser_初始化_设置内存释放", "C", "存疑",
    "FBroSetReleaseMemoryCycleTime/FBroSetMaxReleaseMemory; src 0 命中。类库**自标弃用**「弃用, 用于设置系统内部内存释放线程」。卡在: 弃用后该 API 是否仍生效未知(需真机验证长驻进程内存曲线), 若已失效则应改判 B4。需证据: ① 一版带本调用与不带本调用的编译产物长时间运行的内存占用对比; ② 或向 SDK 作者确认弃用后的替代品(类库另有 FBrowser_内存_压缩清理, 已被 browser_compress_memory 暴露)")
put(IC, "FBrowser_初始化_设置守护", "C", "存疑",
    "FBroSetIsLiveMainProcessCycleTime; src 0 命中; 类库**自标弃用**「弃用, 设置系统内部守护线程」。卡在: 弃用 API 的实际效果未知; 且本项目已有自己的子进程残留治理(启动时检测上次渲染进程崩溃并清理缓存, main.wsv:67), 是否还需要守护线程需先确认。需证据: ① 强杀主进程后观察 FBroSubprocess.exe 是否残留(本项目已做过的类似真机验证); ② SDK 作者对弃用原因的说明")
put(IC, "FBrowser_设置程序DPI模式", "A", "无",
    "FBroHsSetProcessDPI(DPI模式); src 全库 0 命中 `DPI`; 类库注明「在程序入口初始化之前调用」, 是纯启动期设置",
    "CDP 无对应(Emulation.setDeviceMetricsOverride 只改页面视口 DPR, 不改进程 DPI 感知)", "(启动参数通道) browser_kernel_initsetting", "P2", "放在 main.wsv 启动方法最前(第 19 行 启动方法 内, FBrowser_初始化 之前)")
put(IC, "启用自带调试提示", "C", "存疑",
    "类库注释「**仅调试模式下有用**, 启用模块类调试输出提示」; src 0 命中; 无工具暴露 SDK 自身调试输出开关。卡在: 本项目是 release 编译时(编译产物/编译命令未见调试版标记), 该开关可能完全无效果。需证据: ① 确认本项目构建是 debug 还是 release(编译参数/generated-cpp 产物); ② 调试版下实测 启用自带调试提示(真) 是否真的多出 SDK 事件类初始化/销毁提示。若为 release 构建 → 改判 B4")

# ===== B1 工具名覆盖(手工) =====
B1_MANUAL = {
    (IC, "FBrowser_关闭"): "browser_shutdown(main.wsv:233 执行关闭序列 内调用, 由 browser_shutdown 触发)",
    (IC, "取初始化缓存目录".replace("取初始化", "FBrowser_取初始化") ) : "",
}
put(IC, "FBrowser_取初始化缓存目录", "B1", "工具名", "browser_cache_dir(browser.取请求环境.取缓存路径) + browser_get_global_cache_dir(MCP_Server_System.wsv:50)")
put(IC, "FBrowser_JS交互_注册", "B1", "工具名", "browser_kernel_ipc_queue/browser_ipc_send_to 构成的双工 IPC(页面 window.__mcp_ipc_queue ↔ 宿主), 覆盖「页面 JS 回调宿主」需求")
put(IC, "FBrowser_JS交互_删除", "B1", "工具名", "同上")
put("FBrowser辅助功能", "FBrowser_浏览器_通过序号取浏览器", "B1", "工具名", "browser_list(返回 id 清单) + browser_get_main_browser + browser_id 参数")
put("FBrowser辅助功能", "FBrowser_Parser_取数据URI", "B1", "工具名", "browser_base64_encode(mimetype 前缀由调用方拼接)")
put(BR, "尝试关闭浏览器", "B1", "工具名", "browser_close(MCP_Server_Core.wsv:440 调 关闭浏览器, 类库注释即明写会触发 onbeforeunload); 且 browser_close_try 描述明写「[已废弃] 已替换为 browser_close」")
put(BR, "FBrowser_创建浏览器_同步", "B1", "工具名", "browser_create + browser_list/browser_wait(异步创建→轮询取 id, 语义等价; 项目一律以 browser_id 寻址)")
put("类_FBrowser_框架", "载入地址", "B1", "工具名", "browser_navigate(MCP_Server_Core.wsv 多处直调 载入地址)")
put("类_FBrowser_方案注册", "添加自定义方案", "B1", "工具名", "browser_kernel_scheme(main.wsv:321-329 注册自定义方案 事件里调 添加自定义方案, 运行期由 browser_kernel_scheme 挂载资源处理器)")
put("类_FBrowser_服务器", "FBrowser_服务器_创建", "B1", "工具名", "MCP 自身的 HTTP/WS 传输层(MCP_Server.wsv:8121 调用), 不是浏览器能力")
put(V, "指纹_虚拟内核功能", "B1", "工具名", "已被 browser_vip_set_web_version/browser_vip_set_v8_version/browser_vip_set_css_version 三件套取代(同类库内 `内核开关_设置Web/V8/CSS内核`, 三个都已有专属工具且被直调); 且本方法类库标注**弃用**")
for m in ["即将处理命令行", "执行关闭完毕", "注册自定义方案", "渲染_即将创建V8环境", "渲染_即将初始化WebKit",
          "渲染_即将捕获异常", "渲染_即将释放V8环境", "渲染_即将销毁浏览器", "渲染_收到消息",
          "渲染_浏览器创建", "渲染_焦点节点改变", "渲染_载入开始", "渲染_载入状态被改变",
          "渲染_载入结束", "渲染_载入错误", "扩展插件_创建成功", "扩展插件_创建失败",
          "扩展插件_载入成功", "扩展插件_卸载成功", "渲染_VIP_WebSocket客户端_创建",
          "渲染_VIP_WebSocket客户端_关闭", "渲染_VIP_WebSocket客户端_连接服务器",
          "渲染_VIP_WebSocket客户端_接收数据", "渲染_VIP_WebSocket客户端_发送数据"]:
    put(EV, m, "B1", "工具名",
        "browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218)",
        "⚠ 注: 渲染进程侧(app_render_*)事件在本架构下不会真正派发(渲染进程是独立的 FBroSubprocess.exe), 项目已在 MCP_Server_Core.wsv:3341 自我声明; 页面侧等价能力请用 browser_event(load_start/load_end/…)、browser_reverse_websocket、browser_collect")
put(EV, "获取默认事件", "B1", "工具名", "main.wsv:779 已 override 获取默认事件(类_FBrowser_应用事件的虚方法)")
put("类_FBrowser_资源过滤器", "获取数据", "B1", "工具名", "browser_intercept(action=modify/replace_data/replace_file 的过滤器实现类_MCP_篡改过滤器, MCP_Callbacks.wsv:907)")
put("类_FBrowser_资源过滤器", "修改数据", "B1", "工具名", "同上(MCP_Callbacks.wsv:925)")
put("类_FBrowserVIP_通用回调", "数据回调", "B1", "工具名", "MCP_Callbacks.wsv:395/617 已 override(高级_执行JS 的异步结果回调)")
put("类_FBrowserVIP_通用回调", "列表数据回调", "B1", "工具名", "MCP_Callbacks.wsv:648 已 override(browser_vip_dom_search 结果回调)")
put(UR, "获取到数据", "B1", "工具名", "browser_create_url_request(MCP_Callbacks.wsv:739 已 override)")
put(UR, "读取结束", "B1", "工具名", "browser_create_url_request(MCP_Callbacks.wsv:766 已 override)")
put(UR, "即将完成", "B1", "工具名", "browser_create_url_request(MCP_Callbacks.wsv:779 已 override)")
put("类_FBrowser_下载图片回调", "图片下载完成", "B1", "工具名", "browser_download_image(MCP_Callbacks.wsv:857 已 override)")
put("类_FBrowser_打开文件对话框回调", "即将关闭文件对话框", "B1", "工具名", "browser_file_dialog(MCP_Callbacks.wsv:557 已 override)")
put("类_FBrowser_打印为PDF回调", "即将完成打印", "B1", "工具名", "browser_print_to_pdf(MCP_Callbacks.wsv:587 已 override)")
put("类_FBrowser_JS交互事件", "即将查询", "B1", "工具名", "browser_kernel_ipc_queue/browser_ipc_send_to(双工 IPC)")
put("类_FBrowser_JS交互事件", "即将取消查询", "B1", "工具名", "同上")
# V8值
for m in ["FBrowser_V8值_创建函数", "FBrowser_V8值_创建双精度小数型值", "FBrowser_V8值_创建数组值",
          "FBrowser_V8值_创建数组缓存值", "FBrowser_V8值_创建整型值", "FBrowser_V8值_创建文本值",
          "FBrowser_V8值_创建无符号整型值", "FBrowser_V8值_创建日期值", "FBrowser_V8值_创建未定义类",
          "FBrowser_V8值_创建空类", "FBrowser_V8值_创建类", "FBrowser_V8值_创建逻辑值"]:
    put("类_FBrowser_V8值", m, "B1", "工具名",
        "browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象",
        "注: 宿主侧原生 V8 值对象(含 创建函数)未暴露, 但等价的「宿主函数暴露给页面」由 browser_reverse_add_binding(Runtime.addBinding) 覆盖")
put("类_FBrowser_V8值", "执行函数", "B1", "工具名", "browser_reverse_call_fn(Runtime.callFunctionOn, 可传 object_id 或 function_name)")
put(CL, "设置全局代理", "B1", "工具名", "browser_set_proxy/browser_set_s5_proxy/browser_clear_proxy(实例级代理, MCP_Server_Core.wsv:1199 调 高级_设置代理); 差异仅在「全局 vs 实例级」, 单浏览器场景等价")
put(CL, "禁用代理", "B1", "工具名", "browser_clear_proxy(MCP_Server_Core.wsv:1232 调 高级_清空代理)")

# ===== B2 action 枚举 =====
put(V, "指纹_虚拟Webdriver", "B2", "action 枚举",
    "browser_fingerprint action=set_batch —— 批量指纹配置 JSON 的 `webdriver` 键(MCP_Server_Core.wsv:2194-2201 判键存在后调用); 同一 set_batch 块还吃下 ua/vendor/product/languages/webgl_vendor/hardware_concurrency/device_memory/width/height/avail_width/avail_height 等键",
    "注: webdriver 也由 browser_antidetect_presets preset=stealth 一并处理")
for m in ["指纹_取调用计数", "指纹_虚拟Canvas_随机", "指纹_虚拟WebGL_随机", "指纹_虚拟Audio_随机", "清理数据"]:
    act = {"指纹_取调用计数": "count", "指纹_虚拟Canvas_随机": "canvas_random", "指纹_虚拟WebGL_随机": "webgl_random",
           "指纹_虚拟Audio_随机": "audio_random", "清理数据": "clear"}[m]
    put(V, m, "B2", "action 枚举", "browser_fingerprint action=%s(MCP_Server_Core.wsv:1986 分支真调用, 行号见 covmap)" % act)

# ===== VIP 高级输入/执行 的等价覆盖(手工) =====
put(V, "高级_发送鼠标事件", "B1", "工具名",
    "browser_reverse_input_cdp(kind=mouse, 直发 CDP 原始输入) / browser_vip_mouse_press/release/move/wheel(内核注入) / browser_mouse_click 等工具的 kernel:true(内核级注入, MCP_Server_Core.wsv:643 确有执行)")
put(V, "高级_发送键盘事件", "B1", "工具名",
    "browser_key_event(MCP_Server_Core.wsv:704 分支 → 725/730 直调 高级键盘_按下/放开) / browser_reverse_input_cdp(kind=key, 13 项参数由 CDP Input.dispatchKeyEvent 表达)")
put(V, "高级_发送触摸事件", "B1", "工具名",
    "browser_reverse_input_cdp(kind=touch) / browser_touch_press+move+release(kernel:true 走内核注入) / browser_vip_touch_cancel 等")
put(V, "高级触摸_单击", "B1", "工具名", "browser_touch_press + browser_touch_release 组合(类库实现同为 按下→延时→放开 两步)")
put(V, "高级_执行JS_主框架", "B1", "工具名", "browser_vip_execute_js_context(context_id, 主框架 contextId=1) / browser_execute_js")
put(V, "高级_执行JS_全部框架", "B1", "工具名", "browser_get_frames + browser_vip_execute_js_context 逐个框架执行(等价, 需 AI 侧循环; 无「一次批量」工具)")
put(V, "高级_执行JS_框架序号", "B1", "工具名", "browser_vip_execute_js_context(frame_id, 由 browser_vip_get_js_env_ids 取) / browser_get_frames 提供序号→框架映射")
put(V, "逐字分割", "B4", "非能力项", "纯字符串工具函数(把文本按字符拆成文本数组), 被 高级键盘_输入文本 内部调用; 不是用户能力")
put(IC, "FBrowser_关闭", "B1", "工具名", "browser_shutdown(main.wsv:233 执行关闭序列 内调用 FBrowser_关闭 (真), 该序列由 browser_shutdown 触发)")
put(IC, "FBrowser_自定义方案_注册", "B1", "工具名", "browser_kernel_scheme action=register(MCP_Kernel.wsv:443 直调 FBrowser_自定义方案_注册(\"mcp\", 域名, 处理器))")
put(IC, "FBrowser_自定义方案_清理", "B1", "工具名", "browser_kernel_scheme action=clear(MCP_Kernel.wsv:480 直调 FBrowser_自定义方案_清理())")
put("FBrowser辅助功能", "FBrowser_Parser_解析JSON", "B4", "非能力项",
    "JSON 解析内部件(项目通篇使用 YYJSON, 该 API 仅用于 CDP params 解析 MCP_Server.wsv:1629); 对 AI 无独立价值 —— 传参本来就已是 JSON")
put(BR, "FBrowser_创建浏览器", "B1", "工具名", "browser_create(main.wsv:212 UI 线程创建路径直调, 由 browser_create 写入 待创建URL 触发)")

# ===== B3 CDP 直通 =====
DOMV = "类_FBrowserVIP_开发者DOM"
put(DOMV, "清除查找", "B3", "CDP 直通", "browser_cdp_call{method:\"DOM.discardSearchResults\"}(类库对应 CefDOMSearchId 释放; 搜索本身已由 browser_vip_dom_search 覆盖)")
put(DOMV, "移除节点", "B3", "CDP 直通", "browser_cdp_call{method:\"DOM.removeNode\",params:{nodeId}}(类库注释即「removeNode」; nodeId 可由 browser_vip_dom_get_document 的枚举结果取得)")
put(DOMV, "移除节点属性", "B3", "CDP 直通", "browser_cdp_call{method:\"DOM.removeAttribute\",params:{nodeId,name}}(类库注释即「removeAttribute」)")
put(V, "高级_设置触发鼠标触摸事件", "B3", "CDP 直通", "browser_cdp_call{method:\"Emulation.setEmitTouchEventsForMouse\"}(CDP Emulation 域原生方法, 与 FBroHsVIPControl_SetEmitTouchEventsForMouse 同义)")
put(BR, "清理缓存", "B3", "CDP 直通",
    "browser_cdp_call{method:\"Storage.clearDataForOrigin\",params:{origin,storageTypes}} —— 按源+存储类型清理(CDP Storage 域原生); 类库 清理缓存(源地址,清理对象位或,存储类型) 的粒度可由它完全表达",
    "⚠ 可用性差距: 现有 browser_clear_cache_browser 虽然直调 清理缓存, 但**四个参数全传空**(MCP_Server_Core.wsv:5578 `browser.清理缓存 (, , , 清理回调)`), 即「只清 localStorage/IndexedDB 而保留 Cookie」这类需求只能靠手写 CDP Storage.clearDataForOrigin")
put(BR, "打开对话框", "B3", "CDP 直通",
    "browser_cdp_call{method:\"Page.setInterceptFileChooserDialog\"} 拦下原生文件对话框 + {method:\"DOM.setFileInputFiles\"} 直接给 <input type=file> 塞文件 —— 自动化真正需要的语义(选文件)由此覆盖",
    "⚠ 可用性差距: 现有 browser_file_dialog 是**故意不弹窗**的桩(MCP_Server_Core.wsv:5380「不弹任何窗口…其会阻塞控制台」), 只校验 path 存在性; 原生 RunFileDialog 本身对 AI 无意义")
put("类_FBrowser_框架", "载入请求", "B3", "CDP 直通",
    "browser_cdp_call{method:\"Page.navigate\",params:{url,referrer,referrerPolicy,transitionType}} / {method:\"Network.setExtraHTTPHeaders\"} —— 带自定义 Referer/请求头的导航可表达",
    "⚠ 可用性差距: Page.navigate 的 referrer 与 setExtraHTTPHeaders 的语义与 CefRequest 不等价(setExtraHTTPHeaders 是浏览器级持续生效), 需用户自己知道方法名与参数")

# ===== B4 非能力项 =====
B4_REASON = {
    ("FBrowser初始化控制", "FBrowser_初始化"): "启动期一次性调用(main.wsv:98), 不构成运行期工具能力",
    ("FBrowser初始化控制", "FBrowser_消息循环_执行"): "本项目自建消息泵(main.wsv:112-118 PeekMessage 循环)+ 设置.启用系统消息循环=真(main.wsv:90), SDK 消息循环 API 不参与; 暴露为工具反而会与主循环冲突",
    ("FBrowser初始化控制", "FBrowser_消息循环_运行"): "同上",
    ("FBrowser初始化控制", "FBrowser_消息循环_退出"): "同上(退出由 browser_shutdown + 主循环标志位完成)",
    ("FBrowser初始化控制", "FBrowser_消息循环_设置系统模式"): "同上",
    ("FBrowser初始化控制", "启用自带调试提示"): "见 A 段",
    ("FBrowser辅助功能", "FBrowser_启用异常收集"): "类库自带注释「火山版本内置已经设置了, 所以这个没用」—— 官方明示无效",
    ("FBrowser辅助功能", "异常收集回调模板函数"): "同上, 是 启用异常收集 的 @匹配方法 模板, 无独立能力",
    ("FBrowser辅助功能", "FBrowser_Parser_写入JSON"): "JSON 序列化内部件; 项目统一使用 YYJSON(火山内置), 该 API 属 类_FBrowser_值 的附属",
    ("FBrowser辅助功能", "FBrowser_Parser_字节值解析为JSON"): "同上",
    ("类_FBrowser_框架", "访问DOM对象"): "类库注释「只能在渲染进程中调用」; 本项目渲染进程为独立 FBroSubprocess.exe, 主进程不可用; DOM 能力由 browser_dom_*/CDP DOM 域覆盖",
    ("类_FBrowser_服务器", "关闭连接"): "MCP 自身 HTTP/WS 服务的连接管理(生命周期由进程掌控), 非浏览器能力",
    ("类_FBrowser_事件智能指针", "FBrowser创建事件智能指针"): "全局函数形式的等价物已在项目内普遍使用: `事件智能指针变量.创建(执行类)`(如 MCP_Server.wsv:1720/3370/5295)",
    ("类_FBrowser_请求环境", "FBrowser_请求环境_取全局"): "宿主侧全局请求环境句柄, 项目经 browser.取请求环境() 获取(MCP_Server.wsv:7868 取请求环境_安全)",
    ("类_FBrowser_拖拽数据", "增加文件"): "仅离线渲染(OSR)拖拽事件路径使用; 本项目为窗口内嵌渲染, 该类只在 离屏渲染_开始拖拽 事件参数中出现(MCP_BrowserEvents.wsv:3074), 且项目已声明 OSR 事件不触发",
    ("类_FBrowser_同步辅助类", "停止等待"): "同步等待原语(供 SDK 内部阻塞式等待), 属线程/同步基础设施",
    ("类_FBrowser_同步辅助类", "添加字节集"): "字节集拼接内部实现(被多个回调用于累积响应体)",
    ("类_FBrowser_同步辅助类", "清理数据"): "内部状态复位",
    ("类_FBrowser_值转换", "FBrowser_字节集到字节集"): "类型转换内部件(字节集↔火山字节集), 无用户可见能力",
    ("类_FBrowser_值转换", "FBrowser_数据到字节集"): "同上",
    ("类_FBrowser_值转换", "FBrowser_文本到字节集"): "同上",
    ("类_FBrowser_V8值", "将重新抛出异常"): "V8 C++ 异常转发内部件",
    ("类_FBrowser_V8值", "清理异常"): "同上",
    ("类_FBrowser_V8值", "调整外部内存大小"): "V8 外部内存记账内部件",
    ("类_FBrowser_V8拦截器", "获取_名"): "V8 Handler 的 C++ 属性存取器",
    ("类_FBrowser_V8拦截器", "获取_索引"): "同上",
    ("类_FBrowser_V8拦截器", "设置_名"): "同上",
    ("类_FBrowser_V8拦截器", "设置_索引"): "同上",
    ("FBrowser类辅助", "FBrowser创建类指针"): "火山类与 C++ 指针互转的封装辅助(反射层), 每个包装类都自动生成",
    ("FBrowser类辅助", "FBrowser取执行类"): "同上",
    ("FBrowser类辅助", "FBrowser设置类"): "同上",
    ("FBrowser类辅助", "FBrowser释放当前类"): "同上",
    ("FBrowser类辅助", "FBrowser释放类"): "同上",
    ("类_FBrowser_任务运行器", "FBrowser_任务运行器_取当前"): "线程基础设施; 对应的唯一工具位 browser_task_runner_post 已被 MCP_Server_System.wsv:20-22 主动禁用(理由: GUI 窗口自动管理浏览器实例)。真正缺的是「后台浏览器创建」, 见 A 段",
    ("类_FBrowser_任务运行器", "FBrowser_任务运行器_取指定线程"): "同上",
    ("类_FBrowser_任务运行器", "FBrowser_任务运行器_投递任务"): "同上",
    ("类_FBrowser_任务运行器", "FBrowser_任务运行器_投递任务_延迟"): "同上",
    ("类_FBrowser_任务运行器", "FBrowser_任务运行器_是否指定线程上调用"): "同上",
    ("类_FBrowser_任务运行器", "投递任务"): "同上",
    ("类_FBrowser_任务运行器", "投递延时任务"): "同上",
    ("FBrowser_双文本数组", "查找数据"): "数组容器查找内部件",
    ("FBrowser_文本数组", "到火山文本数组"): "数组容器↔火山原生类型转换内部件",
}
# 事件类/回调类的 类_初始化/类_清理 与数组遍历
for k in list(covmap.keys()):
    cls, meth = k.split("::")
    if meth in ("类_初始化", "类_清理"):
        B4_REASON[(cls, meth)] = "框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力"
    if meth in ("到下一个", "到数组首"):
        B4_REASON[(cls, meth)] = "数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施"

# 服务器事件 6 个
for m in ["收到HTTP请求", "收到WebSocket消息", "收到WebSocket请求", "收到WebSocket连接", "收到客户端连接", "收到客户端断开连接"]:
    B4_REASON[("类_FBrowser_服务器事件", m)] = ("MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), "
                                            "事件即 MCP 协议入口本身, 不是待补的浏览器工具能力")

# ===== C 存疑 =====
C_UNSURE = {
    (V, "高级_创建标签浏览器"): "卡在「浏览器以什么 UI 模式创建」。类库注释限定「谷歌模式(Chrome UI)下才可以使用」; main.wsv:203-212 只用 FBrowser_窗口信息(父窗口句柄=0/坐标/宽高) 调 FBrowser_创建浏览器, 未见 CEF_RUNTIME_STYLE_CHROME(常量 谷歌=1, FBroConst.wsv:753) 的显式设定。需证据: ① 实测 browser_create 出来的浏览器是否有 Chrome 式 Tab 条; ② 或读 FBroConst.wsv 里 CEF_RUNTIME_STYLE_* 常量被哪个属性消费。若为普通窗口模式, 该项应改判为 B4(架构不适用)。",
}

report_c = 0
rows = []
for c in cands:
    k = key(c)
    if k in D:
        d = D[k]
        rows.append((c, d["v"], d["route"], d["who"], d.get("note", ""), d.get("tool", ""), d.get("prio", ""), d.get("reuse", "")))
    elif (c["cls"], c["method"]) in B4_REASON:
        rows.append((c, "B4", "非能力项", B4_REASON[(c["cls"], c["method"])], "", "", "", ""))
    elif (c["cls"], c["method"]) in C_UNSURE:
        rows.append((c, "C", "存疑", C_UNSURE[(c["cls"], c["method"])], "", "", "", ""))
    else:
        ts = tools_for(c)
        if ts:
            route = "action 枚举" if ts == ["browser_fingerprint"] else "工具名"
            rows.append((c, "B2" if ts == ["browser_fingerprint"] else "B1", route,
                         "%s(src 直调, covmap)" % ", ".join(ts), "", "", "", ""))
        else:
            rows.append((c, "?", "未判定", "", "", "", "", ""))

cnt = collections.Counter(r[1] for r in rows)
print("总数 =", len(rows))
for k in sorted(cnt):
    print("  %-4s %d" % (k, cnt[k]))
un = [r for r in rows if r[1] == "?"]
if un:
    print("\n!! 未判定:")
    for r in un:
        print("   ", r[0]["cls"], r[0]["method"])
json.dump([{"cls": r[0]["cls"], "method": r[0]["method"], "params": r[0]["params"],
            "file": r[0]["file"], "verdict": r[1], "route": r[2], "who": r[3],
            "note": r[4], "tool": r[5], "prio": r[6], "reuse": r[7]} for r in rows],
          io.open(os.path.join(HERE, "_cg2_verdict.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
