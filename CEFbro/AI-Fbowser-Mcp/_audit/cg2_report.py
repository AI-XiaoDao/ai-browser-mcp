# -*- coding: utf-8 -*-
"""生成 _classlib_gap_confirmed2.md"""
import io, json, os, re, collections
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
V = json.load(io.open(os.path.join(HERE, "_cg2_verdict.json"), encoding="utf-8"))
IDX = json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))
DECL = json.load(io.open(os.path.join(HERE, "_cg2_adecl.json"), encoding="utf-8"))
TOOLS = IDX["tools"]
CAND = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
PARAM = {"%s::%s" % (c["cls"], c["method"]): c["params"] for c in CAND}
SRCFILE = {"%s::%s" % (c["cls"], c["method"]): c["file"] for c in CAND}

def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")

A = [r for r in V if r["verdict"] == "A"]
C = [r for r in V if r["verdict"] == "C"]
B1 = [r for r in V if r["verdict"] == "B1"]
B2 = [r for r in V if r["verdict"] == "B2"]
B3 = [r for r in V if r["verdict"] == "B3"]
B4 = [r for r in V if r["verdict"] == "B4"]
prio = collections.Counter(r["prio"] for r in A)

def decl_of(r):
    k = "%s::%s" % (r["cls"], r["method"])
    d = DECL.get(k)
    if d:
        return d["decl"]
    ps = PARAM.get(k) or []
    return "方法 %s " % r["method"] + " ".join("参数 %s" % p[0] for p in ps)

L = []
w = L.append

w("# 类库 API 面 → MCP 工具面: **确认缺口**第二轮收敛报告")
w("")
w("> 只读审计产物。**未修改任何 `.wsv`、未编译、未调用 MCP 接口**。")
w("> 输入 = `_audit/_classlib_gap.md` 的 363 个候选缺口; 判据 = 三向核对(工具名 / action 枚举 / `browser_cdp_call` 直通)。")
w("> 结论 = **确认缺口 %d 条**, 误报 %d 条(其中 %d 条属「非能力项」性质, 见 B4), 存疑 %d 条。"
  % (len(A), len(B1) + len(B2) + len(B3) + len(B4), len(B4), len(C)))
w("")
w("---")
w("")
w("## 0. 快照、口径与判据")
w("")
w("### 0.1 基准快照")
w("")
w("| 项 | 值 |")
w("|---|---|")
w("| 工具面 | `src/MCP_Server.wsv` 中 `添加工具JSON (...)` 注册 **%d** 个工具(逐条从源码正则提取, 与 `_cg2_index.json` 一致) |" % len(TOOLS))
w("| 分派器 | 7 个 `分类分派_*`(核心/填表/逆向/内核/VIP/系统/编排), 共 342 个 `方法名 == \"...\"` 分支 + 72 个 `action` 分支 + 21 个 `动作` 分支 |")
w("| 类库面 | `资料/类库/FBrowser浏览器/` 8 个 `.wsv`(FBroLib/FBroVip/FBroEventControl/FBroValue/FBroCallback/FBroDataType/FBroConst/FBroHelp), 100 个类, 1360 条 `方法` 声明 |")
w("| 候选 | `_audit/_classlib_gap.md` 的 **363** 条(本次逐条复核, 无遗漏) |")
w("")
w("**⚠ 重要: 分析期间 `src/` 正在被并发修改。** 本会话内实测: `MCP_Server.wsv` 626 099 → 631 054 字节, `MCP_Kernel.wsv` 101 246 → 101 905, `MCP_Server_Core.wsv` 446 449 → 450 079, `MCP_Server_Reverse.wsv` 133 094 → 151 667; 工具数 311 → **312**(新增 `browser_reverse_detect_traps`)。")
w("因此**所有「缺失」类结论都在最终快照上重跑过一遍**; 行号一律给出锚点文本, 请以文本而非行号引用。")
w("")
w("**审计方完整性声明**: 本轮只读。未修改 `src/` 下任何 `.wsv`(一行都没有)、未运行 `voldev_awp.exe`/任何 `.bat`/编译器、未发起任何 HTTP/JSON-RPC 请求、未启动或重启 `AI-Fbowser-Mcp.exe`。")
w("所有产物只写在 `_audit/`(脚本 `cg2_*.py`、中间数据 `_cg2_*.json/txt`、本报告)。`git status` 里 `src/*.wsv` 的 `M` 标记来自**并发工作的其它会话**, 与本报告无关。")
w("工具名清单是**静态提取**自 `添加工具JSON (...)` 源码, 不是 `tools/list` 的实际响应(未调用 MCP 接口)。")
w("")
w("最终快照 sha256 前16位:")
w("")
w("```")
w("MCP_Server.wsv        631054  804746663803d91f")
w("MCP_Server_Core.wsv   450079  954862728ba361e8")
w("MCP_Server_Reverse.wsv 151667 2be0773d02f901e2")
w("MCP_Server_VIP.wsv     98847  e9728214a022349c")
w("MCP_Kernel.wsv        101905  7cd3cb1dcb854081")
w("MCP_BrowserEvents.wsv  98920  24599cf1f642a5c1")
w("MCP_Callbacks.wsv      65744  c77f591c6d8f14c9")
w("main.wsv               38979  6fa1bccdab2c5df3")
w("类库 FBroLib.wsv      287774  0b34667326c6e3c4")
w("类库 FBroVip.wsv      137695  9370b87dcc3a9781")
w("类库 FBroEventControl 143472  b5835e60fc469bc7")
w("```")
w("")
w("### 0.2 三向核对怎么做才算「排除」")
w("")
w("| 途径 | 判据(必须读到实现, 不看描述) |")
w("|---|---|")
w("| ① 工具名覆盖 | 能指名一个工具, 且在 `src` 中 grep 到该工具分支**真的调用**了目标类库方法(`_cg2_covmap.py` 自动把每个直调点归属到最近的 `方法名==\"...\"` 分支) |")
w("| ② action/枚举覆盖 | 该工具的 `action`/`preset`/`动作` 分支里存在语义等价分支, 并已读到该分支真调用 |")
w("| ③ `browser_cdp_call` 直通 | 存在标准 CDP 方法可完全表达该能力。已读实现确认是**真直通**: `MCP_Server.wsv:1646 vip_ctrl.开发者消息_执行方法 (cdpMsgId, cdpMethod, params_dict)`, 只透传方法名与参数, **无域白名单**(仅 `Debugger.` 前缀触发一次自愈, 见 :1577) |")
w("")
w("**三条全部排除才记为确认缺口。** 途径③成立的条目一律标注「经 browser_cdp_call 可达(非缺口)」, 并单列**可用性差距**: 用户必须自己知道 CDP 方法名与参数形态。")
w("")
w("### 0.3 分类口径(含对任务书三分类的一处扩展)")
w("")
w("| 记号 | 含义 | 条数 |")
w("|---|---|---|")
w("| **A** | 确认缺口(三路皆不成立) | %d |" % len(A))
w("| **B1** | 误报 — 工具名覆盖 | %d |" % len(B1))
w("| **B2** | 误报 — action/preset 枚举覆盖 | %d |" % len(B2))
w("| **B3** | 误报 — `browser_cdp_call` 直通覆盖(附可用性差距) | %d |" % len(B3))
w("| **B4** | 误报 — **非能力项**(任务书三分类之外的扩展类, 见下) | %d |" % len(B4))
w("| **C** | 存疑 | %d |" % len(C))
w("| | **合计** | **%d** |" % len(V))
w("")
w("**关于 B4(必须说明, 因为它不是「被覆盖」):** 有 **%d** 条候选根本不是用户能力 —— 它们是类生命周期(`类_初始化`/`类_清理`)、" % len(B4))
w("数组遍历原语(`到下一个`/`到数组首`)、C++↔火山类型互转、V8/线程内部机制, 或**启动期一次性配置**(项目已在 `main.wsv` 里定死)。")
w("它们既不是缺口, 也谈不上「被某工具覆盖」。原脚本的 NOISE 过滤器只按「取/置/是否/加入…」前缀排除, 这类名字全部漏网。")
w("**B4 每一行都单独给了理由**, 便于你按自己的口径重新归类(若严格只认三类, 请把 B4 从「误报」中剔除, 则误报 = %d)。" % (len(B1) + len(B2) + len(B3)))
w("")
w("---")
w("")

# ============ A ============
w("## (A) 确认缺口 —— %d 条" % len(A))
w("")
w("优先级: **P0 = %d**(阻塞常规自动化的批量/无窗口场景) / **P1 = %d**(逆向与反检测常用) / **P2 = %d**(边缘或启动期)。"
  % (prio.get("P0", 0), prio.get("P1", 0), prio.get("P2", 0)))
w("")
w("**P0 / P1 速览(只列这两档, 共 %d 条):**" % (prio.get("P0", 0) + prio.get("P1", 0)))
w("")
w("| 优先 | 建议工具名 / 形态 | 一句话能力 | 复用路径 |")
w("|---|---|---|---|")
for r in A:
    if r["prio"] in ("P0", "P1"):
        w("| **%s** | `%s` | %s | %s |" % (r["prio"], esc(r["tool"] or "需新写"), esc(r["method"]), esc(r["reuse"] or "需新写")))
w("")


FAM = [
    ("A-1", "类_FBrowser_命令行 —— 启动参数族(15 条中 13 条)", "类_FBrowser_命令行",
     ["FBrowser_命令行_取全局", "FBrowser_命令行_创建", "插入值", "启用无头模式", "设置远程调试端口",
      "启用自动播放", "启用摄像头", "启用录音", "启用单进程模式", "启用跨框架操作模式",
      "忽略GPU禁用清单", "禁用GPU", "禁用GPU缓存"],
     "**这一族要单独看: 它们只能在 CEF 初始化之前生效, 因此不是「加个工具」而是「加一条启动通道」。**\n"
     "\n"
     "- 证据 1: `FBrowser_初始化` 在 `main.wsv:98` 被调用, 之后 `类_FBrowser_命令行` 的任何设置都来不及;\n"
     "- 证据 2: 全 `src` 中 `类_FBrowser_命令行` **只作为事件参数类型**出现(`main.wsv:461`/`main.wsv:474` 的 `即将处理命令行`、`浏览器_即将启动子进程`), **从未调用过它的任何方法**(`_cg2_direct.py`: 该族 13 条全部「无同名直调」);\n"
     "- 证据 3: `main.wsv:459` 的 `即将处理命令行` override **体是空的**(只在开启监控时记录 `app_startup_cmdline`), 也就是说插入开关的天然落点现成, 但没接线;\n"
     "- 反例排除: `--headless` 在项目里**已经存在**但语义完全不同 —— `MCP_Stdio.wsv:225` 用它判定 MCP **服务端**是否无控制台, 与浏览器无头模式无关;\n"
     "- 建议形态: 用 MCP 进程自身启动参数(或环境变量)承载, 在 `main.wsv` 的 `启动方法`/`即将处理命令行` 里 `插入值`/`启用X()`; 可另加一个只读工具(如 `browser_kernel_cmdline`)回显当前生效的开关集, 便于 AI 自检。"),
    ("A-2", "后台(无窗口)浏览器 —— 2 条", "类_FBrowser_浏览器",
     ["FBrowser_创建后台浏览器", "FBrowser_创建后台浏览器_同步"],
     "类库注释即卖点: 「创建一个完全后台没有窗口的浏览器…**不同于创建浏览器再隐藏窗口, 也非无头模式其优于无头模式**…可用于纯后台刷新取数等相关操作, 比前台浏览器占用更低, 其他操作和普通浏览器无异」。\n"
     "\n"
     "- 证据: 全 `src` grep `后台浏览器` / `FBroHsCreate` **0 命中**; 唯一创建入口 `browser_create` 的描述明写「新建一个**可见**浏览器窗口」(`MCP_Server.wsv`), 且只有 `main.wsv:212` 一条 `FBrowser_创建浏览器` 路径, 窗口信息写死 1000×800;\n"
     "- 反例排除: 现有 `browser_create` + `browser_id` 只解决「多个可见窗口」, 不解决「无窗口/低占用」; 无头模式(见 A-1)亦未接;\n"
     "- 注意: `_同步` 版**必须经 `FBrowser_任务运行器_投递任务` 到 UI 线程**(类库注释原文), 而该通道对应的工具位 `browser_task_runner_post` 被 `MCP_Server_System.wsv:20-22` 硬禁用 —— 实现时要么解禁、要么在 `main.wsv` 的 500ms 节拍里排程。"),
    ("A-3", "宿主侧 URL 请求定制(CEF URLRequest 客户端) —— 10 条", "类_FBrowser_URL请求事件 / 类_FBrowser_请求 / 类_FBrowser_POST数据 / 类_FBrowser_读取流",
     ["开始创建", "上传进度", "设置标识", "获取地址_首件cookie", "设置地址_首件cookie",
      "增加元素", "移除元素", "移除所有元素", "FBrowser_读取流_从数据创建", "FBrowser_读取流_从文件创建"],
     "`browser_create_url_request` 的 schema **只有 `url` + `method`**(`MCP_Server.wsv:9601`), 实现 `MCP_Server_Core.wsv:5505-5514` 只做 `请求.置地址/置类型` —— 无自定义头、无 cookie 归属域、无 body、无 flag。\n"
     "\n"
     "- 证据 1: `类_MCP_URL请求回调`(`MCP_Callbacks.wsv:723`) 只 override 了 `获取到数据`/`读取结束`/`即将完成`, **没有 override `开始创建`** —— 而 `开始创建` 是拿 `类_FBrowser_URL请求.取请求()` 后设置一切的**唯一时机**;\n"
     "- 证据 2: `类_FBrowser_POST数据` 在 `src` 里**只读不写**(`MCP_Server.wsv:7410`、`:10651` 用 `取POST数据`/`取元素` 读抓到的请求), `增加元素`/`移除元素`/`移除所有元素` 0 命中; `类_FBrowser_读取流` 0 命中;\n"
     "- 证据 3: `类_FBrowser_请求::设置(地址,类型,POST数据,协议头数据)` 是全套拼装入口, 全 `src` 未调用;\n"
     "- **为什么不算 CDP 可达**: 这不是页面请求, 而是**宿主侧的 CEF `CefURLRequest` 客户端** —— 不经 DOM、不受 CORS 约束、不依赖页面存在。CDP 没有对应域;\n"
     "- 可用的部分替代(不计入本缺口): 页面内 `browser_execute_js` + `fetch()`(受同源/CORS 限制)、`browser_cdp_call` 的 `Fetch.*`/`Network.setExtraHTTPHeaders`(只作用于浏览器自身的页面请求)。"),
    ("A-4", "右键菜单模型(CefMenuModel) —— 13 条", "类_FBrowser_菜单模式",
     None,
     "**这一族的共同证据(下面每一行都适用, 不再重复):**\n"
     "\n"
     "- `类_FBrowser_菜单模式` = `CefMenuModel` 包装(`FBroLib.wsv:3288`), 13 个方法在 `src` 中 **0 调用**(逐方法 grep, 见 `_cg2_zero.py`);\n"
     "- 该类在项目里**只作为事件参数类型**出现: `MCP_BrowserEvents.wsv:2662`(`浏览器_即将打开菜单`)、`:2674`(`浏览器_菜单被调用`), 两个 override **都只记录事件**(`context_menu_opening/run/command/dismissed`), 完全没碰传进来的 `Menumodel`;\n"
     "- 现有 `browser_kernel_menu` 的 action 只有 `disable/enable/status`(整块屏蔽右键菜单), 与「改菜单项」正交, 不构成覆盖;\n"
     "- **非 CDP 可达**: CEF 的右键菜单模型不属于任何 CDP 域, `browser_cdp_call` 无法增删原生菜单项(CDP 无 `Menu` 域);\n"
     "- 类库特性提示: `设置快捷键`/`设置快捷键_索引` 的注释写明「**只是用于显示快捷键, 触发需自行用键盘事件实现**」—— 它不产生行为, 这也是本族整体判 P2 的原因之一。"),
    ("A-5", "VIP 残留 —— 4 条", "类_FBrowserVIP_控制器 / FBrowserVIP全局功能",
     ["指纹_清空调用计数", "FBrowser_VIP功能_启用插件高级功能",
      "FBrowser_VIP过滤器_取消修改内容", "FBrowser_VIP过滤器_取消替换资源"], None),
    ("A-6", "初始化期设置残留 —— 3 条", "FBrowser初始化控制",
     ["FBrowser_初始化_设置V8环境默认堆栈大小", "FBrowser_设置程序DPI模式"], None),
    ("A-7", "窗口控制残留 —— 2 条", "类_FBrowser_浏览器",
     ["移动窗口", "显示隐藏窗口"], None),
]
seen = set()

def emit_rows(items, head=("类库来源", "类库方法(参数表)", "为何三路皆不成立", "建议工具名", "可复用的现成实现路径", "优先级")):
    w("| " + " | ".join(head) + " |")
    w("|" + "---|" * len(head))
    for r in items:
        key = "%s::%s" % (r["cls"], r["method"])
        if key in seen:
            continue
        seen.add(key)
        w("| %s | `%s` %s | %s | `%s` | %s | **%s** |" % (
            esc(r["file"]), esc(r["method"]), esc(decl_of(r)).replace("方法 %s " % r["method"], ""),
            esc(r["who"]), esc(r["tool"] or "需新写"), esc(r["reuse"] or "需新写"), esc(r["prio"])))

for code, title, cls, methods, blurb in FAM:
    if methods is None:
        items = [r for r in A if r["cls"] == cls]
    elif " / " in cls:
        want = set(methods)
        items = [r for r in A if r["method"] in want]
    else:
        items = [r for r in A if r["cls"] == cls and r["method"] in methods]
    items = [r for r in items if "%s::%s" % (r["cls"], r["method"]) not in seen]
    title = re.sub(r"——\s*\d+\s*条", "—— %d 条" % len(items), title)
    w("### %s %s" % (code, title))
    w("")
    if blurb:
        w(blurb)
        w("")
    w("| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |")
    w("|---|---|---|---|---|---|")
    for r in items:
        key = "%s::%s" % (r["cls"], r["method"])
        seen.add(key)
        ps = " ".join("`%s`" % p[0] for p in (PARAM.get(key) or []))
        w("| %s | `%s` %s | %s | `%s` | %s | **%s** |" % (
            esc(r["file"]), esc(r["method"]), ps,
            esc(r["who"]), esc(r["tool"] or "需新写"), esc(r["reuse"] or "需新写"), esc(r["prio"])))
    w("")

left = [r for r in A if "%s::%s" % (r["cls"], r["method"]) not in seen]
if left:
    w("### A-9 其余确认缺口 (%d 条)" % len(left))
    w("")
    w("| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |")
    w("|---|---|---|---|---|---|")
    for r in left:
        key = "%s::%s" % (r["cls"], r["method"])
        ps = " ".join("`%s`" % p[0] for p in (PARAM.get(key) or []))
        w("| %s | `%s` %s | %s | `%s` | %s | **%s** |" % (
            esc(r["file"]), esc(r["method"]), ps,
            esc(r["who"]), esc(r["tool"] or "需新写"), esc(r["reuse"] or "需新写"), esc(r["prio"])))
    w("")

# ============ B ============
w("---")
w("")
w("## (B) 误报 —— %d 条" % (len(B1) + len(B2) + len(B3) + len(B4)))
w("")
w("### B1 工具名覆盖 —— %d 条" % len(B1))
w("")
w("> 判据: `src` 中能 grep 到该工具分支**真的调用**了目标类库方法(由 `_cg2_covmap.py` 自动归属, 并非名字相似)。")
w("")
bycls = collections.OrderedDict()
for r in B1:
    bycls.setdefault(r["cls"], []).append(r)
for cls in sorted(bycls, key=lambda c: -len(bycls[c])):
    rows = bycls[cls]
    w("**%s (%d)**" % (cls, len(rows)))
    w("")
    w("| 类库方法 | 覆盖它的工具 / 证据 |")
    w("|---|---|")
    for r in rows:
        w("| `%s` | %s |" % (esc(r["method"]), esc(r["who"])))
    w("")

w("### B2 action / preset 枚举覆盖 —— %d 条" % len(B2))
w("")
w("| 类/来源 | 类库方法 | 被哪个工具的哪个 action 覆盖 |")
w("|---|---|---|")
for r in B2:
    w("| %s | `%s` | %s |" % (esc(r["cls"]), esc(r["method"]), esc(r["who"])))
w("")

w("### B3 `browser_cdp_call` 直通覆盖 —— %d 条(含可用性差距)" % len(B3))
w("")
w("| 类/来源 | 类库方法 | CDP 方法 | 可用性差距(必须由用户自己知道方法名与参数) |")
w("|---|---|---|---|")
for r in B3:
    w("| %s | `%s` | %s | %s |" % (esc(r["cls"]), esc(r["method"]), esc(r["who"]), esc(r["note"] or "无")))
w("")
w("> 这 **%d** 条按任务书口径**不算缺口**(CDP 完全兜住), 但它们暴露的是**可用性**问题而非能力问题: `browser_cdp_call` 的工具描述只有两个字「VIP: CDP命令(带结果回传)」, 参数是裸的 `method`/`params`, 没有任何域/方法清单或引导。同一能力「有没有工具」与「AI 能不能无提示地用出来」是两件事。" % len(B3))
w("")

w("### B4 非能力项 —— %d 条(对任务书三分类的扩展, 逐行给理由)" % len(B4))
w("")
bycls = collections.OrderedDict()
for r in B4:
    bycls.setdefault(r["cls"], []).append(r)
for cls in sorted(bycls, key=lambda c: -len(bycls[c])):
    rows = bycls[cls]
    w("**%s (%d)**" % (cls, len(rows)))
    w("")
    w("| 类库方法 | 为什么它不是用户能力 |")
    w("|---|---|")
    for r in rows:
        w("| `%s` | %s |" % (esc(r["method"]), esc(r["who"])))
    w("")

# ============ C ============
w("---")
w("")
w("## (C) 存疑 —— %d 条" % len(C))
w("")
w("宁缺勿错: 以下条目我**无法在只读条件下判定**, 写清卡点与所需证据。")
w("")
for r in C:
    w("### `%s` —— %s" % (r["method"], r["cls"]))
    w("")
    w("- 来源: `%s`" % r["file"])
    w("- 声明: `%s`" % decl_of(r))
    w("- **卡点与所需证据**: %s" % r["who"])
    w("")

# ============ 特别小节 ============
w("---")
w("")
w("## 特别小节: 四族单独结论(它们的「缺口」性质不同)")
w("")
w("### 1. `类_FBrowser_命令行`(启动参数类) —— 结论: **真缺口, 但必须做成启动通道而不是运行期工具**")
w("")
w("见 A-1。要点复述: ① 13/15 条确认缺口, 2 条(`设置全局代理`/`禁用代理`)算误报(被 `browser_set_proxy`/`browser_clear_proxy` 的实例级代理覆盖, 差异只是全局 vs 实例); ")
w("② **运行期调用无效**(CEF 已初始化), 所以「建议工具名」栏里我写的是通道而非工具位; ")
w("③ 落点现成: `main.wsv:459` 的 `即将处理命令行` override 是空的, 正是插入开关的位置; ")
w("④ `--headless` 在项目里已被 MCP 服务端占用(MCP_Stdio.wsv:225), 若新增浏览器无头开关**必须换名**, 否则语义冲突。")
w("")
w("### 2. `类_FBrowser_菜单模式`(菜单与快捷键) —— 结论: **13 条全是真缺口, 但都是 P2**")
w("")
w("- 该类是 `CefMenuModel` 包装(FBroLib.wsv:3288), 13 个方法在 `src` 中 **0 调用**; ")
w("- 项目里该类**只作为事件参数类型**出现在 `MCP_BrowserEvents.wsv:2662`/`:2674`(`浏览器_即将打开菜单`/`浏览器_菜单被调用`)—— 事件**收得到 MenuModel 却什么都不做**, 只记录 `context_menu_opening/run/command/dismissed`; ")
w("- 现有 `browser_kernel_menu` 的 action 只有 `disable/enable/status`(整块屏蔽右键菜单), 与「改菜单项」正交; ")
w("- 非 CDP 可达: CEF 右键菜单模型不属于任何 CDP 域(CDP 无法增删原生菜单项); ")
w("- 特性提示: `设置快捷键`/`设置快捷键_索引` 的类库注释写明「**只是用于显示快捷键, 触发需自行用键盘事件实现**」, 即它不产生行为, 只影响显示 —— 这也解释了为什么它是 P2。")
w("")
w("### 3. `类_FBrowserVIP_控制器`(102 条) —— 结论: **误报 100 条, 真缺口 1 条, 存疑 1 条**")
w("")
w("| 结果 | 条数 | 说明 |")
w("|---|---|---|")
w("| 误报·工具名覆盖 | 92 | 每条都能指名一个专属 VIP 工具(如 `内核开关_禁用Console*` 15 条 → `browser_vip_disable_console` 一个工具; `指纹_虚拟BatteryManager*` 4 条 → `browser_vip_fingerprint_battery`; `高级鼠标_*` 5 条 → `browser_vip_mouse_*`) |")
w("| 误报·action 枚举覆盖 | 6 | `browser_fingerprint` 的 `canvas_random/webgl_random/audio_random/count/clear` |")
w("| 误报·CDP 直通覆盖 | 1 | `高级_设置触发鼠标触摸事件` → `Emulation.setEmitTouchEventsForMouse` |")
w("| 误报·非能力项 | 1 | `逐字分割`(内部字符串工具函数, 被 高级键盘_输入文本 调用) |")
w("| **确认缺口** | **1** | `指纹_清空调用计数` |")
w("| 存疑 | 1 | `高级_创建标签浏览器` |")
w("| 合计 | 102 | |")
w("")
w("误报率 **98%**(100/102) —— 这一族是最典型的「一个英文工具吃掉 N 个中文类库方法」: 原脚本按方法名做字面匹配, 而 MCP 侧是 `browser_vip_*` + 指纹一键工具, 名字不可能相似。")
w("")
w("### 4. `类_FBrowser_应用事件`(27 条) —— 结论: **误报 27 条, 无缺口**")
w("")
w("逐条核对方式: 把 26 个候选方法名逐个到 `src/main.wsv` 里找 `方法 <名> <公开 @虚拟方法 = 可覆盖>` —— **24 个事件方法全部被 `类_MCP_初始化事件` override**(该类 `基础类 = 类_FBrowser_应用事件`, main.wsv:256), 并写入 `app_*` 记录; ")
w("第 25 条 `获取默认事件` 同样在 main.wsv:779 被 override; 余下 2 条是 `类_初始化`/`类_清理`(B4)。")
w("开关由 `browser_collect`(event_app_enable / event_extension_enable / event_startup_enable / event_render_enable / event_renderws_enable)与 `browser_kernel_events_all`(MCP_Kernel.wsv:1205-1218 一次开 21 族)控制; 查询用 `browser_event(event_type=\"app_*\")`。")
w("")
w("| 类库事件 | 落地的事件名 / 行号 |")
w("|---|---|")
for a, b in [("即将处理命令行", "app_startup_cmdline (main.wsv:470)"), ("执行关闭完毕", "override main.wsv:295"),
             ("注册自定义方案", "override main.wsv:321(内核层注册 mcp:// 方案)"),
             ("扩展插件_创建成功", "app_extension_created (:599)"), ("扩展插件_创建失败", "app_extension_create_failed (:617)"),
             ("扩展插件_载入成功", "app_extension_loaded (:631)"), ("扩展插件_卸载成功", "app_extension_unloaded (:645)"),
             ("渲染_即将捕获异常", "app_v8_exception (:317)"), ("渲染_即将释放V8环境", "app_v8_released (:381)"),
             ("渲染_焦点节点改变", "app_dom_focus_changed (:369)"), ("渲染_即将初始化WebKit", "app_startup_webkit_init (:502)"),
             ("渲染_即将创建V8环境", "app_render_v8_context_created (:514)"), ("渲染_浏览器创建", "app_render_browser_created (:407)"),
             ("渲染_即将销毁浏览器", "app_render_browser_destroyed (:416)"), ("渲染_载入错误", "app_render_load_error (:397)"),
             ("渲染_收到消息", "app_render_message_received (:531)"), ("渲染_载入状态被改变", "app_render_loading_state (:552)"),
             ("渲染_载入开始", "app_render_load_start (:568)"), ("渲染_载入结束", "app_render_load_end (:584)"),
             ("渲染_VIP_WebSocket客户端_创建", "app_render_ws_created (:657)"), ("渲染_VIP_WebSocket客户端_关闭", "app_render_ws_closed (:670)"),
             ("渲染_VIP_WebSocket客户端_连接服务器", "app_render_ws_connect (:689)"),
             ("渲染_VIP_WebSocket客户端_接收数据", "app_render_ws_recv (:704)"),
             ("渲染_VIP_WebSocket客户端_发送数据", "app_render_ws_send (:721)")]:
    w("| `%s` | %s |" % (a, b))
w("")
w("> ⚠ **但这 24 条「已覆盖」要打个折扣**: 其中 `渲染_*` 一族属**渲染进程事件**, 而本项目渲染进程是 SDK 自带的 `FBroSubprocess.exe`(独立进程), ")
w("> 项目自己在 `MCP_Server_Core.wsv` 的开关说明里写明: 「本族事件由 CEF 渲染进程触发…经真机验证, 这些事件**不会**被派发到本项目的事件覆盖上, 因此 app_render_* **不会产生任何记录**…需要页面侧信息请改用 browser_execute_js / browser_snapshot / browser_dom_query」; ")
w("> `渲染_VIP_WebSocket客户端_*` 同段亦有同款声明。**所以它们的「覆盖」是声明层的覆盖: 事件名注册了、override 写了, 但不会有数据。** ")
w("> 这类「名义覆盖」建议你单独按「能力是否真的可用」再筛一遍 —— 我按任务书的三向核对口径只能记它「非缺口」(事件族与查询工具都在), 但可观测性上它是空的。")
w("")
w("---")
w("")
w("## 附: 本次复核中「最容易误判」的三类候选(给后续审计的避坑记录)")
w("")
w("原脚本 `classlib_gap.py` 的匹配口径是「类库方法名(或其前 3 字)是否出现在任一工具的描述文本里」。这个口径的漏洞不是「不够聪明」, 而是**方向错了**: MCP 工具名是英文、类库方法名是中文, 覆盖关系往往既不相似也不同长。三类具体陷阱:")
w("")
w("### 陷阱 1: 一个英文工具吃掉一整族中文方法(批量覆盖)")
w("")
w("| 类库方法(候选) | 实际覆盖者 | 为什么字面匹配必然漏 |")
w("|---|---|---|")
w("| `内核开关_禁用ConsoleLog` / `ConsoleWarn` / `ConsoleError` / … 共 **15 条** | 一个工具 `browser_vip_disable_console`(`MCP_Server_VIP.wsv:1658-1672` 15 行连续直调) | 「ConsoleLog」与工具名、工具描述都不重合 |")
w("| `指纹_虚拟BatteryManagerLevel` / `Charging` / `ChargingTime` / `DischargingTime` **4 条** | 一个工具 `browser_vip_fingerprint_battery` | 同上 |")
w("| `渲染_载入结束` / `渲染_载入错误` / `渲染_浏览器创建` … **24 条** | 一个工具 `browser_event` 的 `app_*` 族(24 个 override 全在 `main.wsv`) | 工具描述里根本没有「渲染_载入结束」这种词 |")
w("")
w("### 陷阱 2: 覆盖藏在**工具的参数开关**里, 不在工具名里")
w("")
w("| 类库方法(候选) | 实际覆盖者 | 说明 |")
w("|---|---|---|")
w("| `停止载入` | `browser_stop` | (用户已举的反例)名字毫无字面关系, 但 `MCP_Server_Core.wsv:167` 直调 `browser.停止载入 ()` |")
w("| `高级_发送鼠标事件` / `高级鼠标_单击` / `高级鼠标_移动` / `高级鼠标_滚轮滚动` | `browser_mouse_click` 等工具的 **`kernel:true` 参数** + `browser_vip_mouse_*` 专属工具 | 内核实现在同一工具的另一条参数分支里(`MCP_Server_Core.wsv:643`), 按工具名匹配永远看不到 |")
w("| `指纹_虚拟Canvas_随机` | `browser_fingerprint` 的 **`action=canvas_random`** | 多合一工具的 action 分支不写进工具描述也能生效 |")
w("")
w("### 陷阱 3: 只看「第一个消费者」就断言「死路径」(我自己踩过)")
w("")
w("复核 `FBrowser_V8_注册JS扩展` 时, 我先看到 `browser_inject persist=true` 把代码存进 `持久V8扩展列表`(`MCP_Server.wsv:1864`), 而该列表在 `MCP_BrowserEvents.wsv:157` 的读取处**只打印条数**; 又看到真正「该」消费它的 `渲染_即将创建V8环境`(`main.wsv:505`)只记录事件不做注入 —— 于是写下「persist 是死路径, 这是确认缺口」。")
w("**这个结论是错的**: 换一个 grep 词(`应用持久V8到框架`)才发现真正的消费者在 `MCP_BrowserEvents.wsv:1537` 的 `浏览器_载入开始` 事件里, 一路走到 `MCP_Server.wsv:2088 应用持久V8到框架` → `框架.执行JS代码`, 而且做了标识去重、管道符转义还原等完整处理。所以 `FBrowser_V8_注册JS扩展` 最终判 **B1(非缺口)**, 报告里只保留「原生 V8 扩展通道未暴露」这条残余差异说明。")
w("**教训**: 断言「某能力缺失」前, 至少用 2~3 个不同关键词检索, 并追踪**数据结构的所有读者**; 只追踪函数名会漏掉经中间方法消费的路径。")
w("")
w("---")
w("")
w("## 统计")
w("")
w("| 项 | 数量 |")
w("|---|---|")
w("| 复核的候选总数 | **%d** |" % len(V))
w("| **(A) 确认缺口** | **%d**(P0 %d / P1 %d / P2 %d) |" % (len(A), prio.get("P0", 0), prio.get("P1", 0), prio.get("P2", 0)))
w("| (B) 误报合计 | **%d** |" % (len(B1) + len(B2) + len(B3) + len(B4)))
w("| &nbsp;&nbsp;B1 工具名覆盖 | %d |" % len(B1))
w("| &nbsp;&nbsp;B2 action 枚举覆盖 | %d |" % len(B2))
w("| &nbsp;&nbsp;B3 browser_cdp_call 直通覆盖 | %d |" % len(B3))
w("| &nbsp;&nbsp;B4 非能力项(口径扩展, 非「被覆盖」) | %d |" % len(B4))
w("| (C) 存疑 | **%d** |" % len(C))
w("| **误报率(含 B4)** | **%.1f%%** |" % (100.0 * (len(B1) + len(B2) + len(B3) + len(B4)) / len(V)))
w("| 误报率(严格三类, 不含 B4) | %.1f%% |" % (100.0 * (len(B1) + len(B2) + len(B3)) / len(V)))
w("| 确认缺口率 | %.1f%% |" % (100.0 * len(A) / len(V)))
w("")
w("对照上一轮 `_classlib_gap_confirmed.md` 的口径: 上轮只覆盖 7 个优先类的 210 条候选(得到 31 条「真缺口」, 误报率 72.4%); ")
w("本轮覆盖全部 363 条 + 全部 312 个工具 + 三向核对, 误报率 **%.1f%%** —— 说明原脚本(%s 的匹配口径)**本地几乎不可用于判断缺口**, 只能当候选生成器。"
  % (100.0 * (len(B1) + len(B2) + len(B3) + len(B4)) / len(V), "「方法名或其前 3 字出现在任一工具描述文本里」"))
w("")
w("---")
w("")
w("## 复现方式(全部只读)")
w("")
w("```")
w("py -3 _audit/cg2_extract.py     # 工具名全集 + 类库方法全集(含参数表) + 分派器分支 -> _cg2_data.json")
w("py -3 _audit/cg2_cands.py       # 从 _classlib_gap.md 解析 363 候选 -> _cg2_cands.json")
w("py -3 _audit/cg2_index.py       # 工具注册全文/schema/分支/字面量索引 -> _cg2_index.json")
w("py -3 _audit/cg2_direct.py      # 候选在 src 中的同名直调扫描")
w("py -3 _audit/cg2_covmap.py      # 把每个直调点归属到所属工具分支  -> _cg2_covmap.json")
w("py -3 _audit/cg2_classify.py    # 逐条判定 -> _cg2_verdict.json(363 行, 每行含 verdict/route/who)")
w("py -3 _audit/cg2_report.py      # 生成本报告")
w("```")
w("")
w("其它辅助: `cg2_zero.py`(无直调清单) `cg2_vipcalls.py`(VIP 控制器调用点) `cg2_vip102.py` `cg2_def.py`(类库声明速查) `cg2_adecl.py` `cg2_find.py`(定向 grep) `cg2_show.py`(工具定义速查) `cg2_toolcat.py`。")
w("")
w("> **本报告是候选清单 + 证据, 不是结论, 也未经真机验证。** 所有「缺失」判定均为静态源码证据; 「非缺口」判定基于读实现, 但**未逐个真机调用**。请对 A 段每一项按「先复现缺口, 再实现, 再验收」流程处理。")
w("")

p = os.path.join(HERE, "_classlib_gap_confirmed2.md")
io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("写出", p, len(L), "行")
print("A=%d (P0 %d / P1 %d / P2 %d)  B1=%d B2=%d B3=%d B4=%d  C=%d" %
      (len(A), prio.get("P0", 0), prio.get("P1", 0), prio.get("P2", 0),
       len(B1), len(B2), len(B3), len(B4), len(C)))
print("A 已输出:", len(seen), "/", len(A))
