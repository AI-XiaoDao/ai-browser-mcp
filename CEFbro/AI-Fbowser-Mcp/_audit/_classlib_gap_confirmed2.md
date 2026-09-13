# 类库 API 面 → MCP 工具面: **确认缺口**第二轮收敛报告

> 只读审计产物。**未修改任何 `.wsv`、未编译、未调用 MCP 接口**。
> 输入 = `_audit/_classlib_gap.md` 的 363 个候选缺口; 判据 = 三向核对(工具名 / action 枚举 / `browser_cdp_call` 直通)。
> 结论 = **确认缺口 46 条**, 误报 313 条(其中 111 条属「非能力项」性质, 见 B4), 存疑 4 条。

---

## 0. 快照、口径与判据

### 0.1 基准快照

| 项 | 值 |
|---|---|
| 工具面 | `src/MCP_Server.wsv` 中 `添加工具JSON (...)` 注册 **312** 个工具(逐条从源码正则提取, 与 `_cg2_index.json` 一致) |
| 分派器 | 7 个 `分类分派_*`(核心/填表/逆向/内核/VIP/系统/编排), 共 342 个 `方法名 == "..."` 分支 + 72 个 `action` 分支 + 21 个 `动作` 分支 |
| 类库面 | `资料/类库/FBrowser浏览器/` 8 个 `.wsv`(FBroLib/FBroVip/FBroEventControl/FBroValue/FBroCallback/FBroDataType/FBroConst/FBroHelp), 100 个类, 1360 条 `方法` 声明 |
| 候选 | `_audit/_classlib_gap.md` 的 **363** 条(本次逐条复核, 无遗漏) |

**⚠ 重要: 分析期间 `src/` 正在被并发修改。** 本会话内实测: `MCP_Server.wsv` 626 099 → 631 054 字节, `MCP_Kernel.wsv` 101 246 → 101 905, `MCP_Server_Core.wsv` 446 449 → 450 079, `MCP_Server_Reverse.wsv` 133 094 → 151 667; 工具数 311 → **312**(新增 `browser_reverse_detect_traps`)。
因此**所有「缺失」类结论都在最终快照上重跑过一遍**; 行号一律给出锚点文本, 请以文本而非行号引用。

**审计方完整性声明**: 本轮只读。未修改 `src/` 下任何 `.wsv`(一行都没有)、未运行 `voldev_awp.exe`/任何 `.bat`/编译器、未发起任何 HTTP/JSON-RPC 请求、未启动或重启 `AI-Fbowser-Mcp.exe`。
所有产物只写在 `_audit/`(脚本 `cg2_*.py`、中间数据 `_cg2_*.json/txt`、本报告)。`git status` 里 `src/*.wsv` 的 `M` 标记来自**并发工作的其它会话**, 与本报告无关。
工具名清单是**静态提取**自 `添加工具JSON (...)` 源码, 不是 `tools/list` 的实际响应(未调用 MCP 接口)。

最终快照 sha256 前16位:

```
MCP_Server.wsv        631054  804746663803d91f
MCP_Server_Core.wsv   450079  954862728ba361e8
MCP_Server_Reverse.wsv 151667 2be0773d02f901e2
MCP_Server_VIP.wsv     98847  e9728214a022349c
MCP_Kernel.wsv        101905  7cd3cb1dcb854081
MCP_BrowserEvents.wsv  98920  24599cf1f642a5c1
MCP_Callbacks.wsv      65744  c77f591c6d8f14c9
main.wsv               38979  6fa1bccdab2c5df3
类库 FBroLib.wsv      287774  0b34667326c6e3c4
类库 FBroVip.wsv      137695  9370b87dcc3a9781
类库 FBroEventControl 143472  b5835e60fc469bc7
```

### 0.2 三向核对怎么做才算「排除」

| 途径 | 判据(必须读到实现, 不看描述) |
|---|---|
| ① 工具名覆盖 | 能指名一个工具, 且在 `src` 中 grep 到该工具分支**真的调用**了目标类库方法(`_cg2_covmap.py` 自动把每个直调点归属到最近的 `方法名=="..."` 分支) |
| ② action/枚举覆盖 | 该工具的 `action`/`preset`/`动作` 分支里存在语义等价分支, 并已读到该分支真调用 |
| ③ `browser_cdp_call` 直通 | 存在标准 CDP 方法可完全表达该能力。已读实现确认是**真直通**: `MCP_Server.wsv:1646 vip_ctrl.开发者消息_执行方法 (cdpMsgId, cdpMethod, params_dict)`, 只透传方法名与参数, **无域白名单**(仅 `Debugger.` 前缀触发一次自愈, 见 :1577) |

**三条全部排除才记为确认缺口。** 途径③成立的条目一律标注「经 browser_cdp_call 可达(非缺口)」, 并单列**可用性差距**: 用户必须自己知道 CDP 方法名与参数形态。

### 0.3 分类口径(含对任务书三分类的一处扩展)

| 记号 | 含义 | 条数 |
|---|---|---|
| **A** | 确认缺口(三路皆不成立) | 46 |
| **B1** | 误报 — 工具名覆盖 | 184 |
| **B2** | 误报 — action/preset 枚举覆盖 | 11 |
| **B3** | 误报 — `browser_cdp_call` 直通覆盖(附可用性差距) | 7 |
| **B4** | 误报 — **非能力项**(任务书三分类之外的扩展类, 见下) | 111 |
| **C** | 存疑 | 4 |
| | **合计** | **363** |

**关于 B4(必须说明, 因为它不是「被覆盖」):** 有 **111** 条候选根本不是用户能力 —— 它们是类生命周期(`类_初始化`/`类_清理`)、
数组遍历原语(`到下一个`/`到数组首`)、C++↔火山类型互转、V8/线程内部机制, 或**启动期一次性配置**(项目已在 `main.wsv` 里定死)。
它们既不是缺口, 也谈不上「被某工具覆盖」。原脚本的 NOISE 过滤器只按「取/置/是否/加入…」前缀排除, 这类名字全部漏网。
**B4 每一行都单独给了理由**, 便于你按自己的口径重新归类(若严格只认三类, 请把 B4 从「误报」中剔除, 则误报 = 202)。

---

## (A) 确认缺口 —— 46 条

优先级: **P0 = 2**(阻塞常规自动化的批量/无窗口场景) / **P1 = 9**(逆向与反检测常用) / **P2 = 35**(边缘或启动期)。

**P0 / P1 速览(只列这两档, 共 11 条):**

| 优先 | 建议工具名 / 形态 | 一句话能力 | 复用路径 |
|---|---|---|---|
| **P0** | `browser_create_background` | FBrowser_创建后台浏览器 | main.wsv:202-212 已有一条 `FBrowser_创建浏览器` 的 UI 线程创建路径, 可原样改调 `FBrowser_创建后台浏览器`; 同步版需经 `FBrowser_任务运行器_投递任务` |
| **P0** | `browser_create_background` | FBrowser_创建后台浏览器_同步 | 复用 MCP_Server_System.wsv:9 系统分派器; 需先解禁/改造 task_runner 通道 |
| **P1** | `browser_kernel_cmdline` | 启用无头模式 | 同上; 现状: 全项目 `--headless` 只出现在 MCP_Stdio.wsv:225 的**服务端**参数判定, 与浏览器无头模式无关 |
| **P1** | `browser_kernel_cmdline` | 启用自动播放 | 同上(媒体自动化前置) |
| **P1** | `browser_kernel_cmdline` | 插入值 | 复用 main.wsv:459 已覆盖的 `即将处理命令行` 空实现(注: 该事件在 FBrowser_初始化 前派发, 是插入开关的唯一天然落点) + 类_FBrowser_命令行::插入值 |
| **P1** | `browser_kernel_cmdline` | 设置远程调试端口 | 同上; 现状: src 全库 0 命中 `remote-debugging` |
| **P1** | `扩展 browser_create_url_request` | 开始创建 | 复用 MCP_Callbacks.wsv:723 类_MCP_URL请求回调, 加一个 `开始创建` override; 内部用 URL请求.取请求() 拿到 类_FBrowser_请求 后调用 设置/增加元素/读取流 |
| **P1** | `扩展 browser_create_url_request` | 设置地址_首件cookie | 同 设置标识 路径 |
| **P1** | `扩展 browser_create_url_request` | 增加元素 | MCP_Server_Core.wsv:5505 处新建 类_FBrowser_POST数据 并 增加元素(元素含 读取流), 再传给 请求.设置 |
| **P1** | `扩展 browser_create_url_request` | FBrowser_读取流_从数据创建 | 需新写(仅在 URL 请求拼装处使用) |
| **P1** | `扩展 browser_create_url_request` | FBrowser_读取流_从文件创建 | 需新写 |

### A-1 类_FBrowser_命令行 —— 启动参数族(15 条中 13 条)

**这一族要单独看: 它们只能在 CEF 初始化之前生效, 因此不是「加个工具」而是「加一条启动通道」。**

- 证据 1: `FBrowser_初始化` 在 `main.wsv:98` 被调用, 之后 `类_FBrowser_命令行` 的任何设置都来不及;
- 证据 2: 全 `src` 中 `类_FBrowser_命令行` **只作为事件参数类型**出现(`main.wsv:461`/`main.wsv:474` 的 `即将处理命令行`、`浏览器_即将启动子进程`), **从未调用过它的任何方法**(`_cg2_direct.py`: 该族 13 条全部「无同名直调」);
- 证据 3: `main.wsv:459` 的 `即将处理命令行` override **体是空的**(只在开启监控时记录 `app_startup_cmdline`), 也就是说插入开关的天然落点现成, 但没接线;
- 反例排除: `--headless` 在项目里**已经存在**但语义完全不同 —— `MCP_Stdio.wsv:225` 用它判定 MCP **服务端**是否无控制台, 与浏览器无头模式无关;
- 建议形态: 用 MCP 进程自身启动参数(或环境变量)承载, 在 `main.wsv` 的 `启动方法`/`即将处理命令行` 里 `插入值`/`启用X()`; 可另加一个只读工具(如 `browser_kernel_cmdline`)回显当前生效的开关集, 便于 AI 自检。

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroLib.wsv | `FBrowser_命令行_创建`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 需新写: 自建命令行对象(供测试/预演), 与 取全局 同族 | **P2** |
| FBroLib.wsv | `FBrowser_命令行_取全局`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 需新写: 取 CEF 全局命令行对象的唯一入口; 无它则任何启动参数工具都无从下手 | **P2** |
| FBroLib.wsv | `启用单进程模式`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上 | **P2** |
| FBroLib.wsv | `启用录音`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上 | **P2** |
| FBroLib.wsv | `启用摄像头`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上 | **P2** |
| FBroLib.wsv | `启用无头模式`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上; 现状: 全项目 `--headless` 只出现在 MCP_Stdio.wsv:225 的**服务端**参数判定, 与浏览器无头模式无关 | **P1** |
| FBroLib.wsv | `启用自动播放`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上(媒体自动化前置) | **P1** |
| FBroLib.wsv | `启用跨框架操作模式`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上 | **P2** |
| FBroLib.wsv | `忽略GPU禁用清单`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上 | **P2** |
| FBroLib.wsv | `插入值`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 复用 main.wsv:459 已覆盖的 `即将处理命令行` 空实现(注: 该事件在 FBrowser_初始化 前派发, 是插入开关的唯一天然落点) + 类_FBrowser_命令行::插入值 | **P1** |
| FBroLib.wsv | `禁用GPU`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上(虚拟机/无GPU环境稳定性) | **P2** |
| FBroLib.wsv | `禁用GPU缓存`  | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上 | **P2** |
| FBroLib.wsv | `设置远程调试端口` `端口号` | 类库 FBroLib.wsv 定义; src 全库仅把 `类_FBrowser_命令行` 用作事件参数类型(main.wsv:461/474), 未调用任何方法 | `browser_kernel_cmdline` | 同上; 现状: src 全库 0 命中 `remote-debugging` | **P1** |

### A-2 后台(无窗口)浏览器 —— 2 条

类库注释即卖点: 「创建一个完全后台没有窗口的浏览器…**不同于创建浏览器再隐藏窗口, 也非无头模式其优于无头模式**…可用于纯后台刷新取数等相关操作, 比前台浏览器占用更低, 其他操作和普通浏览器无异」。

- 证据: 全 `src` grep `后台浏览器` / `FBroHsCreate` **0 命中**; 唯一创建入口 `browser_create` 的描述明写「新建一个**可见**浏览器窗口」(`MCP_Server.wsv`), 且只有 `main.wsv:212` 一条 `FBrowser_创建浏览器` 路径, 窗口信息写死 1000×800;
- 反例排除: 现有 `browser_create` + `browser_id` 只解决「多个可见窗口」, 不解决「无窗口/低占用」; 无头模式(见 A-1)亦未接;
- 注意: `_同步` 版**必须经 `FBrowser_任务运行器_投递任务` 到 UI 线程**(类库注释原文), 而该通道对应的工具位 `browser_task_runner_post` 被 `MCP_Server_System.wsv:20-22` 硬禁用 —— 实现时要么解禁、要么在 `main.wsv` 的 500ms 节拍里排程。

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroLib.wsv | `FBrowser_创建后台浏览器`  | src 全库 0 命中 `后台浏览器`/`FBroHsCreate`; 唯一创建入口 browser_create 描述明写「新建一个可见浏览器窗口」(MCP_Server.wsv:9490), 无 background/headless 参数 | `browser_create_background` | main.wsv:202-212 已有一条 `FBrowser_创建浏览器` 的 UI 线程创建路径, 可原样改调 `FBrowser_创建后台浏览器`; 同步版需经 `FBrowser_任务运行器_投递任务` | **P0** |
| FBroLib.wsv | `FBrowser_创建后台浏览器_同步`  | 同上; 且 `FBrowser_任务运行器_投递任务` 在 src 中 0 调用(对应工具位 browser_task_runner_post 被 MCP_Server_System.wsv:20-22 硬禁用) | `browser_create_background` | 复用 MCP_Server_System.wsv:9 系统分派器; 需先解禁/改造 task_runner 通道 | **P0** |

### A-3 宿主侧 URL 请求定制(CEF URLRequest 客户端) —— 10 条

`browser_create_url_request` 的 schema **只有 `url` + `method`**(`MCP_Server.wsv:9601`), 实现 `MCP_Server_Core.wsv:5505-5514` 只做 `请求.置地址/置类型` —— 无自定义头、无 cookie 归属域、无 body、无 flag。

- 证据 1: `类_MCP_URL请求回调`(`MCP_Callbacks.wsv:723`) 只 override 了 `获取到数据`/`读取结束`/`即将完成`, **没有 override `开始创建`** —— 而 `开始创建` 是拿 `类_FBrowser_URL请求.取请求()` 后设置一切的**唯一时机**;
- 证据 2: `类_FBrowser_POST数据` 在 `src` 里**只读不写**(`MCP_Server.wsv:7410`、`:10651` 用 `取POST数据`/`取元素` 读抓到的请求), `增加元素`/`移除元素`/`移除所有元素` 0 命中; `类_FBrowser_读取流` 0 命中;
- 证据 3: `类_FBrowser_请求::设置(地址,类型,POST数据,协议头数据)` 是全套拼装入口, 全 `src` 未调用;
- **为什么不算 CDP 可达**: 这不是页面请求, 而是**宿主侧的 CEF `CefURLRequest` 客户端** —— 不经 DOM、不受 CORS 约束、不依赖页面存在。CDP 没有对应域;
- 可用的部分替代(不计入本缺口): 页面内 `browser_execute_js` + `fetch()`(受同源/CORS 限制)、`browser_cdp_call` 的 `Fetch.*`/`Network.setExtraHTTPHeaders`(只作用于浏览器自身的页面请求)。

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroEventControl.wsv | `上传进度`  | OnUploadProgress 需先置 UR_FLAG_REPORT_UPLOAD_PROGRESS(= 类_FBrowser_请求::设置标识), 该 flag 无入口; 且 类_MCP_URL请求回调 未 override 本方法 | `扩展 browser_create_url_request` | 同上回调类新增 override; 上传体用 FBrowser_读取流_从文件创建 | **P2** |
| FBroEventControl.wsv | `开始创建` `标识` `URL请求` | 类库回调 Start(flag, request) 的唯一落点; src 里 类_MCP_URL请求回调(MCP_Callbacks.wsv:723) 只 override 了 获取到数据/读取结束/即将完成, **未 override 开始创建**, 因此无法在发出请求前设置头/体/flag; CDP 无 CEF USRRequest 客户端的对应域 | `扩展 browser_create_url_request` | 复用 MCP_Callbacks.wsv:723 类_MCP_URL请求回调, 加一个 `开始创建` override; 内部用 URL请求.取请求() 拿到 类_FBrowser_请求 后调用 设置/增加元素/读取流 | **P1** |
| FBroLib.wsv | `获取地址_首件cookie`  | GetFirstPartyForCookies; src 0 命中; 出站请求的 cookie 归属域不可读 | `扩展 browser_create_url_request` | 同 设置标识 路径 | **P2** |
| FBroLib.wsv | `设置地址_首件cookie` `地址` | SetFirstPartyForCookies; src 0 命中; 无法为宿主侧请求指定 cookie 归属域(带登录态取数的关键) | `扩展 browser_create_url_request` | 同 设置标识 路径 | **P1** |
| FBroLib.wsv | `设置标识` `标识` | SetFlags(请求标识: 无/跳过缓存/只使用缓存); src 全库 0 命中; browser_create_url_request 的 schema 只有 url+method(MCP_Server.wsv:9601), 无法置 flag | `扩展 browser_create_url_request` | MCP_Server_Core.wsv:5505-5514 已构造 类_FBrowser_请求 并 置地址/置类型, 追加一行 设置标识 即可 | **P2** |
| FBroLib.wsv | `增加元素` `POST元素` | 类_FBrowser_POST数据/CefPostData 的元素数组; src 全库只**读**不写(MCP_Server.wsv:7410/10651 用 取POST数据/取元素), 0 命中 增加元素/移除元素 | `扩展 browser_create_url_request` | MCP_Server_Core.wsv:5505 处新建 类_FBrowser_POST数据 并 增加元素(元素含 读取流), 再传给 请求.设置 | **P1** |
| FBroLib.wsv | `移除元素` `POST元素` | 同上, 元素数组维护的从属方法 | `扩展 browser_create_url_request` | 同 增加元素 | **P2** |
| FBroLib.wsv | `移除所有元素`  | 同上, 元素数组维护的从属方法 | `扩展 browser_create_url_request` | 同 增加元素 | **P2** |
| FBroLib.wsv | `FBrowser_读取流_从数据创建` `数据指针` `数据大小` | CefStreamReader 构造; src 全库 0 命中; POST 上传体只能来自内存/文件流, 无流即无 body | `扩展 browser_create_url_request` | 需新写(仅在 URL 请求拼装处使用) | **P1** |
| FBroLib.wsv | `FBrowser_读取流_从文件创建` `文件名` | 同上; 从文件建流(上传本地文件作 body) | `扩展 browser_create_url_request` | 需新写 | **P1** |

### A-4 右键菜单模型(CefMenuModel) —— 13 条

**这一族的共同证据(下面每一行都适用, 不再重复):**

- `类_FBrowser_菜单模式` = `CefMenuModel` 包装(`FBroLib.wsv:3288`), 13 个方法在 `src` 中 **0 调用**(逐方法 grep, 见 `_cg2_zero.py`);
- 该类在项目里**只作为事件参数类型**出现: `MCP_BrowserEvents.wsv:2662`(`浏览器_即将打开菜单`)、`:2674`(`浏览器_菜单被调用`), 两个 override **都只记录事件**(`context_menu_opening/run/command/dismissed`), 完全没碰传进来的 `Menumodel`;
- 现有 `browser_kernel_menu` 的 action 只有 `disable/enable/status`(整块屏蔽右键菜单), 与「改菜单项」正交, 不构成覆盖;
- **非 CDP 可达**: CEF 的右键菜单模型不属于任何 CDP 域, `browser_cdp_call` 无法增删原生菜单项(CDP 无 `Menu` 域);
- 类库特性提示: `设置快捷键`/`设置快捷键_索引` 的注释写明「**只是用于显示快捷键, 触发需自行用键盘事件实现**」—— 它不产生行为, 这也是本族整体判 P2 的原因之一。

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroLib.wsv | `存在快捷键` `命令ID` | src 0 调用(见本节导语; 类库对应 HasAccelerator(命令ID)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `存在快捷键_索引` `索引ID` | src 0 调用(见本节导语; 类库对应 HasAcceleratorAt(索引ID)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `添加Check菜单` `命令ID` `标签名` | src 0 调用(见本节导语; 类库对应 AddCheckItem(命令ID,标签名)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `添加Radio菜单` `命令ID` `标签名` `群ID` | src 0 调用(见本节导语; 类库对应 AddRadioItem(命令ID,标签名,群ID)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `添加分隔栏`  | src 0 调用(见本节导语; 类库对应 AddSeparator()) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `添加子菜单` `命令ID` `标签名` | src 0 调用(见本节导语; 类库对应 AddSubMenu(命令ID,标签名)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `添加菜单` `命令ID` `标签名` | src 0 调用(见本节导语; 类库对应 AddItem(命令ID,标签名)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `移除快捷键` `命令ID` | src 0 调用(见本节导语; 类库对应 RemoveAccelerator(命令ID)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `移除快捷键_索引` `索引ID` | src 0 调用(见本节导语; 类库对应 RemoveAcceleratorAt(索引ID)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `设置快捷键` `命令ID` `键代码` `是否按下shift` `是否按下ctrl` `是否按下alt` | src 0 调用(见本节导语; 类库对应 SetAccelerator(命令ID,键代码,shift,ctrl,alt)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `设置快捷键_索引` `索引ID` `键代码` `是否按下shift` `是否按下ctrl` `是否按下alt` | src 0 调用(见本节导语; 类库对应 SetAcceleratorAt(索引ID,键代码,shift,ctrl,alt)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `选中状态` `命令ID` `选中` | src 0 调用(见本节导语; 类库对应 SetCheck(命令ID,选中)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |
| FBroLib.wsv | `选中状态_索引` `索引ID` `选中` | src 0 调用(见本节导语; 类库对应 SetCheckedAt(索引ID,选中)) | `browser_context_menu` | 复用 MCP_BrowserEvents.wsv:2658 `浏览器_即将打开菜单` 已在手的 菜单模式 参数, 按 action 调 添加菜单/添加分隔栏/置可见状态/置禁止状态/选中状态; 规则表仿 browser_kernel_scheme(MCP_Kernel.wsv:391-490) | **P2** |

### A-5 VIP 残留 —— 4 条

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroVip.wsv | `指纹_清空调用计数`  | FBroHsVIPControl_ClearFingerCount(只清计数, 保留伪装); browser_fingerprint 只有 action=count(读) 与 action=clear(→ vip_ctrl.清理数据, 是**清掉全部伪装**的 ClearAllData, MCP_Server_Core.wsv:2000), 二者语义不同, 无法只清计数 | `browser_fingerprint action=clear_count` | MCP_Server_Core.wsv:1986 分支内加一个 action 即可(一行 vip_ctrl.指纹_清空调用计数()) | **P2** |
| FBroVip.wsv | `FBrowser_VIP功能_启用插件高级功能`  | 类库注释: 「必须在加载插件前启用…默认 CEF 不支持插件 content_scripts.js 脚本执行, 启用高级功能后才能支持」; src 全库 0 命中。已有 browser_vip_load_extension / extension_info / unload_extension 三个工具管插件, 却无这个前置开关 | `browser_vip_enable_extension_advanced` | 复用 MCP_Server_VIP.wsv:1322 browser_vip_load_extension 分支, 加载前调用一次 | **P2** |
| FBroVip.wsv | `FBrowser_VIP过滤器_取消修改内容` `目标地址` | 只支持全局 clear: browser_intercept 的 action=clear 把 资源替换规则/导航拦截规则 **整串清空**(MCP_Server_Core.wsv:2250-2253), 而 src 只有 `添加资源替换规则`(MCP_Server.wsv:6979)、**没有** 移除/删除单条规则的函数 | `browser_intercept action=remove(url)` | 复用 MCP_Server.wsv:6979 添加资源替换规则 的同款规则串(规则格式 `action\|url\|search\|replace\|file`), 新写一个按 url 过滤的 移除资源替换规则 | **P2** |
| FBroVip.wsv | `FBrowser_VIP过滤器_取消替换资源` `目标地址` | 同上(取消单条替换资源规则, 而非全部) | `browser_intercept action=remove(url)` | 同上 | **P2** |

### A-6 初始化期设置残留 —— 2 条

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroLib.wsv | `FBrowser_初始化_设置V8环境默认堆栈大小`  | FBroSetV8DefaultsHeapSize(初始尺寸,最大尺寸); src 全库 0 命中(仅类库自身文档提到); 必须在 FBrowser_初始化 前调用, main.wsv:98 之后无法补救 | `(启动参数通道) browser_kernel_initsetting` | 复用 main.wsv:75-98 的 设置 块, 在 FBrowser_初始化 之前根据启动参数/env 调用 | **P2** |
| FBroLib.wsv | `FBrowser_设置程序DPI模式` `DPI模式` | FBroHsSetProcessDPI(DPI模式); src 全库 0 命中 `DPI`; 类库注明「在程序入口初始化之前调用」, 是纯启动期设置 | `(启动参数通道) browser_kernel_initsetting` | 放在 main.wsv 启动方法最前(第 19 行 启动方法 内, FBrowser_初始化 之前) | **P2** |

### A-7 窗口控制残留 —— 2 条

| 类库来源 | 类库方法(参数表) | 为何三路皆不成立 | 建议工具名 | 可复用的现成实现路径 | 优先级 |
|---|---|---|---|---|---|
| FBroLib.wsv | `显示隐藏窗口` `显示隐藏` | src 全库 0 命中 `显示隐藏窗口`/`ShowWindows`; 无工具、无桩位, 也无 CDP 等价(CDP 无隐藏宿主窗口的方法) | `browser_show_window` | 类_FBrowser_浏览器::显示隐藏窗口(显示隐藏 逻辑型) → FBroHsBrowserHost_ShowWindows | **P2** |
| FBroLib.wsv | `移动窗口` `左边` `顶边` `宽度` `高度` `是否重画` | browser_move_window 已注册(MCP_Server.wsv:9538)但描述写「⛔ 本工具恒失败」, MCP_Server_Core.wsv:5369 分支直接返回失败; 无任何替代工具能改原生窗口位置/尺寸 | `browser_move_window(解禁)` | 类_FBrowser_浏览器::移动窗口 → FBroHsBrowserHost_MoveWindow, 一行即可接回; 当前被架构(嵌入式主窗口布局)主动禁用 | **P2** |

---

## (B) 误报 —— 313 条

### B1 工具名覆盖 —— 184 条

> 判据: `src` 中能 grep 到该工具分支**真的调用**了目标类库方法(由 `_cg2_covmap.py` 自动归属, 并非名字相似)。

**类_FBrowserVIP_控制器 (92)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `内核开关_禁用ConsoleAssert` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleClear` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleCount` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleDebug` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleDir` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleError` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleGroup` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleInfo` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleLog` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleProfile` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleTable` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleTime` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleTrace` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用ConsoleWarn` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_禁用Debugger` | browser_antidetect_presets, browser_vip_disable_debugger(src 直调, covmap) |
| `内核开关_禁用Performance检测` | browser_vip_disable_console(src 直调, covmap) |
| `内核开关_设置CSS内核` | browser_vip_set_css_version(src 直调, covmap) |
| `内核开关_设置EventIsTrusted` | browser_vip_set_is_trusted(src 直调, covmap) |
| `内核开关_设置V8内核` | browser_vip_set_v8_version(src 直调, covmap) |
| `内核开关_设置Web内核` | browser_vip_set_web_version(src 直调, covmap) |
| `指纹_启用触摸事件` | browser_antidetect_presets, browser_fingerprint_touch_enable, browser_vip_touch_emulation(src 直调, covmap) |
| `指纹_虚拟AppCodeName` | browser_fingerprint_appcodename(src 直调, covmap) |
| `指纹_虚拟AppName` | browser_fingerprint_appname(src 直调, covmap) |
| `指纹_虚拟AppVersion` | browser_fingerprint_appversion(src 直调, covmap) |
| `指纹_虚拟AudioInput设备` | browser_vip_fingerprint_media_devices(src 直调, covmap) |
| `指纹_虚拟AudioOutput设备` | browser_vip_fingerprint_media_devices(src 直调, covmap) |
| `指纹_虚拟Audio_定值` | browser_vip_fingerprint_audio_fixed(src 直调, covmap) |
| `指纹_虚拟BatteryManagerCharging` | browser_vip_fingerprint_battery(src 直调, covmap) |
| `指纹_虚拟BatteryManagerChargingTime` | browser_vip_fingerprint_battery(src 直调, covmap) |
| `指纹_虚拟BatteryManagerDischargingTime` | browser_vip_fingerprint_battery(src 直调, covmap) |
| `指纹_虚拟BatteryManagerLevel` | browser_vip_fingerprint_battery(src 直调, covmap) |
| `指纹_虚拟CSS字体指纹` | browser_font_randomize, browser_vip_fingerprint_font(src 直调, covmap) |
| `指纹_虚拟Canvas_定值` | browser_vip_fingerprint_canvas_fixed(src 直调, covmap) |
| `指纹_虚拟Canvas字体指纹` | browser_font_randomize, browser_vip_fingerprint_canvas_font(src 直调, covmap) |
| `指纹_虚拟CookieEnabled` | browser_fingerprint_cookie_enabled(src 直调, covmap) |
| `指纹_虚拟Date时区` | browser_antidetect_presets, browser_fingerprint, browser_vip_fingerprint_timezone(src 直调, covmap) |
| `指纹_虚拟DeviceMemory` | browser_antidetect_presets, browser_fingerprint, browser_vip_fingerprint_hardware(src 直调, covmap) |
| `指纹_虚拟DevicePixelRatio` | browser_antidetect_presets, browser_fingerprint_pixel_ratio(src 直调, covmap) |
| `指纹_虚拟HardwareConcurrency` | browser_antidetect_presets, browser_fingerprint, browser_vip_fingerprint_hardware(src 直调, covmap) |
| `指纹_虚拟JavaEnabled` | browser_fingerprint_java_enabled(src 直调, covmap) |
| `指纹_虚拟Languages` | browser_fingerprint, browser_fingerprint_languages(src 直调, covmap) |
| `指纹_虚拟OnLine` | browser_fingerprint_online(src 直调, covmap) |
| `指纹_虚拟Plugins` | browser_fingerprint_plugins(src 直调, covmap) |
| `指纹_虚拟Product` | browser_fingerprint, browser_vip_fingerprint_product(src 直调, covmap) |
| `指纹_虚拟ProductSub` | browser_fingerprint_product_sub, browser_vip_fingerprint_product(src 直调, covmap) |
| `指纹_虚拟Rect` | browser_antidetect_presets, browser_vip_fingerprint_rect(src 直调, covmap) |
| `指纹_虚拟UserAgent` | browser_antidetect_presets, browser_fingerprint, browser_fingerprint_ua(src 直调, covmap) |
| `指纹_虚拟Vendor` | browser_fingerprint, browser_vip_fingerprint_product(src 直调, covmap) |
| `指纹_虚拟VendorSub` | browser_fingerprint_vendor_sub, browser_vip_fingerprint_product(src 直调, covmap) |
| `指纹_虚拟VideoInput设备` | browser_vip_fingerprint_media_devices(src 直调, covmap) |
| `指纹_虚拟Viewport` | browser_vip_fingerprint_viewport(src 直调, covmap) |
| `指纹_虚拟WebGL_定值` | browser_vip_fingerprint_webgl_fixed(src 直调, covmap) |
| `指纹_虚拟Webglrenderer` | browser_fingerprint, browser_fingerprint_webgl_vendor(src 直调, covmap) |
| `指纹_虚拟Webglvendor` | browser_fingerprint, browser_fingerprint_webgl_vendor(src 直调, covmap) |
| `指纹_虚拟WebrtcIP` | browser_antidetect_presets, browser_fingerprint, browser_vip_fingerprint_webrtc(src 直调, covmap) |
| `指纹_虚拟内核功能` | 已被 browser_vip_set_web_version/browser_vip_set_v8_version/browser_vip_set_css_version 三件套取代(同类库内 `内核开关_设置Web/V8/CSS内核`, 三个都已有专属工具且被直调); 且本方法类库标注**弃用** |
| `指纹_虚拟定位` | browser_antidetect_presets, browser_fingerprint, browser_vip_fingerprint_geolocation(src 直调, covmap) |
| `指纹_虚拟屏幕XY` | browser_antidetect_presets, browser_fingerprint_screen_xy(src 直调, covmap) |
| `指纹_虚拟屏幕colorDepth` | browser_vip_fingerprint_screen(src 直调, covmap) |
| `指纹_虚拟屏幕pixelDepth` | browser_vip_fingerprint_screen(src 直调, covmap) |
| `指纹_虚拟屏幕分辨率` | browser_fingerprint, browser_vip_fingerprint_screen(src 直调, covmap) |
| `指纹_虚拟屏幕可用高度和宽度` | browser_fingerprint, browser_vip_fingerprint_screen(src 直调, covmap) |
| `指纹_虚拟屏幕方向` | browser_vip_orientation(src 直调, covmap) |
| `指纹_设置SSL加密套件` | browser_fingerprint, browser_vip_fingerprint_ssl(src 直调, covmap) |
| `高级_发送触摸事件` | browser_reverse_input_cdp(kind=touch) / browser_touch_press+move+release(kernel:true 走内核注入) / browser_vip_touch_cancel 等 |
| `高级_发送键盘事件` | browser_key_event(MCP_Server_Core.wsv:704 分支 → 725/730 直调 高级键盘_按下/放开) / browser_reverse_input_cdp(kind=key, 13 项参数由 CDP Input.dispatchKeyEvent 表达) |
| `高级_发送鼠标事件` | browser_reverse_input_cdp(kind=mouse, 直发 CDP 原始输入) / browser_vip_mouse_press/release/move/wheel(内核注入) / browser_mouse_click 等工具的 kernel:true(内核级注入, MCP_Server_Core.wsv:643 确有执行) |
| `高级_取当前环境ID清单` | browser_vip_get_js_env_ids(src 直调, covmap) |
| `高级_启用执行环境` | browser_vip_enable_js_env(src 直调, covmap) |
| `高级_执行JS` | browser_vip_execute_js_context(src 直调, covmap) |
| `高级_执行JS_主框架` | browser_vip_execute_js_context(context_id, 主框架 contextId=1) / browser_execute_js |
| `高级_执行JS_全部框架` | browser_get_frames + browser_vip_execute_js_context 逐个框架执行(等价, 需 AI 侧循环; 无「一次批量」工具) |
| `高级_执行JS_框架ID` | browser_vip_execute_js_context(src 直调, covmap) |
| `高级_执行JS_框架序号` | browser_vip_execute_js_context(frame_id, 由 browser_vip_get_js_env_ids 取) / browser_get_frames 提供序号→框架映射 |
| `高级_清空代理` | browser_clear_proxy, browser_vip_clear_s5_proxy(src 直调, covmap) |
| `高级_网页截图` | browser_screenshot(src 直调, covmap) |
| `高级_设置代理` | browser_set_proxy, browser_set_s5_proxy(src 直调, covmap) |
| `高级触摸_单击` | browser_touch_press + browser_touch_release 组合(类库实现同为 按下→延时→放开 两步) |
| `高级触摸_取消` | browser_vip_touch_cancel(src 直调, covmap) |
| `高级触摸_按下` | browser_touch_press(src 直调, covmap) |
| `高级触摸_放开` | browser_touch_release(src 直调, covmap) |
| `高级触摸_移动` | browser_touch_move(src 直调, covmap) |
| `高级键盘_单击` | browser_key_event, browser_vip_key_click(src 直调, covmap) |
| `高级键盘_按下` | browser_key_event, browser_vip_key_press(src 直调, covmap) |
| `高级键盘_放开` | browser_key_event, browser_vip_key_release(src 直调, covmap) |
| `高级键盘_输入字符` | browser_vip_key_input(src 直调, covmap) |
| `高级键盘_输入文本` | browser_vip_key_type(src 直调, covmap) |
| `高级鼠标_单击` | browser_mouse_click, browser_vip_mouse_click(src 直调, covmap) |
| `高级鼠标_按下` | browser_vip_mouse_press(src 直调, covmap) |
| `高级鼠标_放开` | browser_vip_mouse_release(src 直调, covmap) |
| `高级鼠标_滚轮滚动` | browser_mouse_wheel, browser_vip_mouse_wheel(src 直调, covmap) |
| `高级鼠标_移动` | browser_mouse_move, browser_vip_mouse_move(src 直调, covmap) |

**类_FBrowser_应用事件 (25)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `即将处理命令行` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `执行关闭完毕` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `扩展插件_创建失败` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `扩展插件_创建成功` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `扩展插件_卸载成功` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `扩展插件_载入成功` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `注册自定义方案` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_VIP_WebSocket客户端_关闭` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_VIP_WebSocket客户端_创建` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_VIP_WebSocket客户端_发送数据` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_VIP_WebSocket客户端_接收数据` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_VIP_WebSocket客户端_连接服务器` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_即将创建V8环境` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_即将初始化WebKit` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_即将捕获异常` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_即将释放V8环境` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_即将销毁浏览器` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_收到消息` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_浏览器创建` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_焦点节点改变` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_载入开始` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_载入状态被改变` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_载入结束` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `渲染_载入错误` | browser_event(app_* 族) —— main.wsv 的 类_MCP_初始化事件 已 **override 本方法** 并写入 app_* 记录; 开关由 browser_collect(event_app_enable 等)/browser_kernel_events_all 控制(MCP_Kernel.wsv:1205-1218) |
| `获取默认事件` | main.wsv:779 已 override 获取默认事件(类_FBrowser_应用事件的虚方法) |

**FBrowser辅助功能 (13)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_Parser_Base64编码` | browser_base64_encode(src 直调, covmap) |
| `FBrowser_Parser_Base64解码` | browser_base64_decode(src 直调, covmap) |
| `FBrowser_Parser_URI编码` | browser_uri_encode(src 直调, covmap) |
| `FBrowser_Parser_URI解码` | browser_uri_decode(src 直调, covmap) |
| `FBrowser_Parser_取数据URI` | browser_base64_encode(mimetype 前缀由调用方拼接) |
| `FBrowser_浏览器_取ID清单` | browser_list(src 直调, covmap) |
| `FBrowser_浏览器_取数量` | browser_create, browser_meta, mcp_status, ping(src 直调, covmap) |
| `FBrowser_浏览器_取用户标识清单` | browser_user_tags(src 直调, covmap) |
| `FBrowser_浏览器_通过ID取浏览器` | browser_close, browser_is_same, browser_list(src 直调, covmap) |
| `FBrowser_浏览器_通过序号取浏览器` | browser_list(返回 id 清单) + browser_get_main_browser + browser_id 参数 |
| `FBrowser_浏览器_通过用户标识取浏览器` | browser_find_by_tag(src 直调, covmap) |
| `FBrowser_浏览器_通过窗口句柄取浏览器` | browser_find_by_hwnd(src 直调, covmap) |
| `FBrowser_清理全局缓存` | browser_clear_cache(src 直调, covmap) |

**类_FBrowser_V8值 (13)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_V8值_创建函数` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建双精度小数型值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建数组值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建数组缓存值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建整型值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建文本值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建无符号整型值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建日期值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建未定义类` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建空类` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建类` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `FBrowser_V8值_创建逻辑值` | browser_reverse_call_fn(arguments 传 JSON 数组, 类型原样保留, MCP_Server.wsv:9752) / browser_reverse_set_variable(value 传 JSON 字面量) —— JS 值构造已下移到 CDP/JSON 层, 无需宿主侧 V8 值对象 |
| `执行函数` | browser_reverse_call_fn(Runtime.callFunctionOn, 可传 object_id 或 function_name) |

**FBrowser初始化控制 (10)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_JS交互_删除` | 同上 |
| `FBrowser_JS交互_注册` | browser_kernel_ipc_queue/browser_ipc_send_to 构成的双工 IPC(页面 window.__mcp_ipc_queue ↔ 宿主), 覆盖「页面 JS 回调宿主」需求 |
| `FBrowser_关闭` | browser_shutdown(main.wsv:233 执行关闭序列 内调用 FBrowser_关闭 (真), 该序列由 browser_shutdown 触发) |
| `FBrowser_内存_压缩清理` | browser_compress_memory(src 直调, covmap) |
| `FBrowser_创建URL请求` | browser_create_url_request(src 直调, covmap) |
| `FBrowser_取初始化缓存目录` | browser_cache_dir(browser.取请求环境.取缓存路径) + browser_get_global_cache_dir(MCP_Server_System.wsv:50) |
| `FBrowser_取版本号` | browser_fbro_version, browser_meta, browser_reverse_env(src 直调, covmap) |
| `FBrowser_自定义方案_注册` | browser_kernel_scheme action=register(MCP_Kernel.wsv:443 直调 FBrowser_自定义方案_注册("mcp", 域名, 处理器)) |
| `FBrowser_自定义方案_清理` | browser_kernel_scheme action=clear(MCP_Kernel.wsv:480 直调 FBrowser_自定义方案_清理()) |
| `FBrowser_进程_取当前进程类型` | browser_get_process_type(src 直调, covmap) |

**类_FBrowser_浏览器 (9)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_创建浏览器` | browser_create(main.wsv:212 UI 线程创建路径直调, 由 browser_create 写入 待创建URL 触发) |
| `FBrowser_创建浏览器_同步` | browser_create + browser_list/browser_wait(异步创建→轮询取 id, 语义等价; 项目一律以 browser_id 寻址) |
| `停止载入` | browser_stop(src 直调, covmap) |
| `可否前进` | browser_can_navigate, browser_forward, browser_loading_info, browser_reverse_env, browser_status(src 直调, covmap) |
| `尝试关闭浏览器` | browser_close(MCP_Server_Core.wsv:440 调 关闭浏览器, 类库注释即明写会触发 onbeforeunload); 且 browser_close_try 描述明写「[已废弃] 已替换为 browser_close」 |
| `开始下载` | browser_start_download(src 直调, covmap) |
| `设置代理` | browser_set_proxy, browser_set_s5_proxy(src 直调, covmap) |
| `重新载入` | browser_reload(src 直调, covmap) |
| `重新载入_忽略缓存` | browser_reload(src 直调, covmap) |

**类_FBrowser_URL请求事件 (3)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `即将完成` | browser_create_url_request(MCP_Callbacks.wsv:779 已 override) |
| `获取到数据` | browser_create_url_request(MCP_Callbacks.wsv:739 已 override) |
| `读取结束` | browser_create_url_request(MCP_Callbacks.wsv:766 已 override) |

**类_FBrowser_命令行 (2)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `禁用代理` | browser_clear_proxy(MCP_Server_Core.wsv:1232 调 高级_清空代理) |
| `设置全局代理` | browser_set_proxy/browser_set_s5_proxy/browser_clear_proxy(实例级代理, MCP_Server_Core.wsv:1199 调 高级_设置代理); 差异仅在「全局 vs 实例级」, 单浏览器场景等价 |

**类_FBrowserVIP_开发者DOM (2)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `枚举DOM` | browser_vip_dom_get_document(src 直调, covmap) |
| `预查找文本` | browser_vip_dom_search(src 直调, covmap) |

**类_FBrowserVIP_通用回调 (2)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `列表数据回调` | MCP_Callbacks.wsv:648 已 override(browser_vip_dom_search 结果回调) |
| `数据回调` | MCP_Callbacks.wsv:395/617 已 override(高级_执行JS 的异步结果回调) |

**类_FBrowser_JS交互事件 (2)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `即将取消查询` | 同上 |
| `即将查询` | browser_kernel_ipc_queue/browser_ipc_send_to(双工 IPC) |

**类_FBrowser_资源过滤器 (2)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `修改数据` | 同上(MCP_Callbacks.wsv:925) |
| `获取数据` | browser_intercept(action=modify/replace_data/replace_file 的过滤器实现类_MCP_篡改过滤器, MCP_Callbacks.wsv:907) |

**类_FBrowser_Cookie管理器 (2)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_Cookie管理器_取全局` | browser_delete_cookies, browser_get_all_cookies, browser_get_cookies, browser_refresh_cookies, browser_reverse_cookie_sources, browser_set_cookie(src 直调, covmap) |
| `刷新Cookie` | browser_refresh_cookies(src 直调, covmap) |

**类_FBrowser_下载图片回调 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `图片下载完成` | browser_download_image(MCP_Callbacks.wsv:857 已 override) |

**类_FBrowser_打开文件对话框回调 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `即将关闭文件对话框` | browser_file_dialog(MCP_Callbacks.wsv:557 已 override) |

**类_FBrowser_打印为PDF回调 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `即将完成打印` | browser_print_to_pdf(MCP_Callbacks.wsv:587 已 override) |

**类_FBrowser_框架 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `载入地址` | browser_navigate(MCP_Server_Core.wsv 多处直调 载入地址) |

**类_FBrowser_V8环境 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_V8_注册JS扩展` | 「页面脚本执行前注入自定义代码」这一能力已由三条现成路径覆盖: ① browser_reverse_preload(Page.addScriptToEvaluateOnNewDocument, 真·先于任何页面 JS); ② browser_inject persist=true —— 实现走 `持久V8扩展列表`(MCP_Server.wsv:1864 加入持久V8扩展) 并由 **浏览器_载入开始** 事件消费(MCP_BrowserEvents.wsv:1537 → MCP_Server.wsv:2088 应用持久V8到框架 → 框架.执行JS代码, 按标识去重); ③ browser_reverse_add_binding(Runtime.addBinding, 原生函数, fn.toString 查不出) |

**类_FBrowser_服务器 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `FBrowser_服务器_创建` | MCP 自身的 HTTP/WS 传输层(MCP_Server.wsv:8121 调用), 不是浏览器能力 |

**类_FBrowser_方案注册 (1)**

| 类库方法 | 覆盖它的工具 / 证据 |
|---|---|
| `添加自定义方案` | browser_kernel_scheme(main.wsv:321-329 注册自定义方案 事件里调 添加自定义方案, 运行期由 browser_kernel_scheme 挂载资源处理器) |

### B2 action / preset 枚举覆盖 —— 11 条

| 类/来源 | 类库方法 | 被哪个工具的哪个 action 覆盖 |
|---|---|---|
| 类_FBrowserVIP_控制器 | `指纹_取调用计数` | browser_fingerprint action=count(MCP_Server_Core.wsv:1986 分支真调用, 行号见 covmap) |
| 类_FBrowserVIP_控制器 | `指纹_虚拟Audio_随机` | browser_fingerprint action=audio_random(MCP_Server_Core.wsv:1986 分支真调用, 行号见 covmap) |
| 类_FBrowserVIP_控制器 | `指纹_虚拟Canvas_随机` | browser_fingerprint action=canvas_random(MCP_Server_Core.wsv:1986 分支真调用, 行号见 covmap) |
| 类_FBrowserVIP_控制器 | `指纹_虚拟WebGL_随机` | browser_fingerprint action=webgl_random(MCP_Server_Core.wsv:1986 分支真调用, 行号见 covmap) |
| 类_FBrowserVIP_控制器 | `指纹_虚拟Webdriver` | browser_fingerprint action=set_batch —— 批量指纹配置 JSON 的 `webdriver` 键(MCP_Server_Core.wsv:2194-2201 判键存在后调用); 同一 set_batch 块还吃下 ua/vendor/product/languages/webgl_vendor/hardware_concurrency/device_memory/width/height/avail_width/avail_height 等键 |
| 类_FBrowserVIP_控制器 | `清理数据` | browser_fingerprint action=clear(MCP_Server_Core.wsv:1986 分支真调用, 行号见 covmap) |
| FBrowserVIP全局功能 | `FBrowser_VIP过滤器_修改内容` | browser_intercept action=modify(MCP_Server_Core.wsv:2347 真调用 添加资源替换规则) |
| FBrowserVIP全局功能 | `FBrowser_VIP过滤器_取消全部修改内容` | browser_intercept action=clear(MCP_Server_Core.wsv:2250 清空全部规则) |
| FBrowserVIP全局功能 | `FBrowser_VIP过滤器_取消全部替换资源` | browser_intercept action=clear |
| FBrowserVIP全局功能 | `FBrowser_VIP过滤器_替换资源_数据` | browser_intercept action=replace_data(MCP_Server_Core.wsv:2362) |
| FBrowserVIP全局功能 | `FBrowser_VIP过滤器_替换资源_文件` | browser_intercept action=replace_file(MCP_Server_Core.wsv:2371) |

### B3 `browser_cdp_call` 直通覆盖 —— 7 条(含可用性差距)

| 类/来源 | 类库方法 | CDP 方法 | 可用性差距(必须由用户自己知道方法名与参数) |
|---|---|---|---|
| 类_FBrowserVIP_控制器 | `高级_设置触发鼠标触摸事件` | browser_cdp_call{method:"Emulation.setEmitTouchEventsForMouse"}(CDP Emulation 域原生方法, 与 FBroHsVIPControl_SetEmitTouchEventsForMouse 同义) | 无 |
| 类_FBrowser_浏览器 | `打开对话框` | browser_cdp_call{method:"Page.setInterceptFileChooserDialog"} 拦下原生文件对话框 + {method:"DOM.setFileInputFiles"} 直接给 <input type=file> 塞文件 —— 自动化真正需要的语义(选文件)由此覆盖 | ⚠ 可用性差距: 现有 browser_file_dialog 是**故意不弹窗**的桩(MCP_Server_Core.wsv:5380「不弹任何窗口…其会阻塞控制台」), 只校验 path 存在性; 原生 RunFileDialog 本身对 AI 无意义 |
| 类_FBrowser_浏览器 | `清理缓存` | browser_cdp_call{method:"Storage.clearDataForOrigin",params:{origin,storageTypes}} —— 按源+存储类型清理(CDP Storage 域原生); 类库 清理缓存(源地址,清理对象位或,存储类型) 的粒度可由它完全表达 | ⚠ 可用性差距: 现有 browser_clear_cache_browser 虽然直调 清理缓存, 但**四个参数全传空**(MCP_Server_Core.wsv:5578 `browser.清理缓存 (, , , 清理回调)`), 即「只清 localStorage/IndexedDB 而保留 Cookie」这类需求只能靠手写 CDP Storage.clearDataForOrigin |
| 类_FBrowserVIP_开发者DOM | `清除查找` | browser_cdp_call{method:"DOM.discardSearchResults"}(类库对应 CefDOMSearchId 释放; 搜索本身已由 browser_vip_dom_search 覆盖) | 无 |
| 类_FBrowserVIP_开发者DOM | `移除节点` | browser_cdp_call{method:"DOM.removeNode",params:{nodeId}}(类库注释即「removeNode」; nodeId 可由 browser_vip_dom_get_document 的枚举结果取得) | 无 |
| 类_FBrowserVIP_开发者DOM | `移除节点属性` | browser_cdp_call{method:"DOM.removeAttribute",params:{nodeId,name}}(类库注释即「removeAttribute」) | 无 |
| 类_FBrowser_框架 | `载入请求` | browser_cdp_call{method:"Page.navigate",params:{url,referrer,referrerPolicy,transitionType}} / {method:"Network.setExtraHTTPHeaders"} —— 带自定义 Referer/请求头的导航可表达 | ⚠ 可用性差距: Page.navigate 的 referrer 与 setExtraHTTPHeaders 的语义与 CefRequest 不等价(setExtraHTTPHeaders 是浏览器级持续生效), 需用户自己知道方法名与参数 |

> 这 **7** 条按任务书口径**不算缺口**(CDP 完全兜住), 但它们暴露的是**可用性**问题而非能力问题: `browser_cdp_call` 的工具描述只有两个字「VIP: CDP命令(带结果回传)」, 参数是裸的 `method`/`params`, 没有任何域/方法清单或引导。同一能力「有没有工具」与「AI 能不能无提示地用出来」是两件事。

### B4 非能力项 —— 111 条(对任务书三分类的扩展, 逐行给理由)

**类_FBrowser_服务器事件 (8)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `收到HTTP请求` | MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), 事件即 MCP 协议入口本身, 不是待补的浏览器工具能力 |
| `收到WebSocket消息` | MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), 事件即 MCP 协议入口本身, 不是待补的浏览器工具能力 |
| `收到WebSocket请求` | MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), 事件即 MCP 协议入口本身, 不是待补的浏览器工具能力 |
| `收到WebSocket连接` | MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), 事件即 MCP 协议入口本身, 不是待补的浏览器工具能力 |
| `收到客户端断开连接` | MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), 事件即 MCP 协议入口本身, 不是待补的浏览器工具能力 |
| `收到客户端连接` | MCP 自身 HTTP/WS 传输层已全部 override 实现(MCP_Server_HTTP.wsv:33/36/40/296/319/325), 事件即 MCP 协议入口本身, 不是待补的浏览器工具能力 |
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_任务运行器 (7)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser_任务运行器_取当前` | 线程基础设施; 对应的唯一工具位 browser_task_runner_post 已被 MCP_Server_System.wsv:20-22 主动禁用(理由: GUI 窗口自动管理浏览器实例)。真正缺的是「后台浏览器创建」, 见 A 段 |
| `FBrowser_任务运行器_取指定线程` | 同上 |
| `FBrowser_任务运行器_投递任务` | 同上 |
| `FBrowser_任务运行器_投递任务_延迟` | 同上 |
| `FBrowser_任务运行器_是否指定线程上调用` | 同上 |
| `投递任务` | 同上 |
| `投递延时任务` | 同上 |

**类_FBrowser_V8拦截器 (6)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `获取_名` | V8 Handler 的 C++ 属性存取器 |
| `获取_索引` | 同上 |
| `设置_名` | 同上 |
| `设置_索引` | 同上 |

**FBrowser初始化控制 (5)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser_初始化` | 启动期一次性调用(main.wsv:98), 不构成运行期工具能力 |
| `FBrowser_消息循环_执行` | 本项目自建消息泵(main.wsv:112-118 PeekMessage 循环)+ 设置.启用系统消息循环=真(main.wsv:90), SDK 消息循环 API 不参与; 暴露为工具反而会与主循环冲突 |
| `FBrowser_消息循环_设置系统模式` | 同上 |
| `FBrowser_消息循环_运行` | 同上 |
| `FBrowser_消息循环_退出` | 同上(退出由 browser_shutdown + 主循环标志位完成) |

**FBrowser辅助功能 (5)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser_Parser_写入JSON` | JSON 序列化内部件; 项目统一使用 YYJSON(火山内置), 该 API 属 类_FBrowser_值 的附属 |
| `FBrowser_Parser_字节值解析为JSON` | 同上 |
| `FBrowser_Parser_解析JSON` | JSON 解析内部件(项目通篇使用 YYJSON, 该 API 仅用于 CDP params 解析 MCP_Server.wsv:1629); 对 AI 无独立价值 —— 传参本来就已是 JSON |
| `FBrowser_启用异常收集` | 类库自带注释「火山版本内置已经设置了, 所以这个没用」—— 官方明示无效 |
| `异常收集回调模板函数` | 同上, 是 启用异常收集 的 @匹配方法 模板, 无独立能力 |

**FBrowser类辅助 (5)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser创建类指针` | 火山类与 C++ 指针互转的封装辅助(反射层), 每个包装类都自动生成 |
| `FBrowser取执行类` | 同上 |
| `FBrowser设置类` | 同上 |
| `FBrowser释放当前类` | 同上 |
| `FBrowser释放类` | 同上 |

**类_FBrowser_V8值 (3)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `将重新抛出异常` | V8 C++ 异常转发内部件 |
| `清理异常` | 同上 |
| `调整外部内存大小` | V8 外部内存记账内部件 |

**FBrowser_双文本数组 (3)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `查找数据` | 数组容器查找内部件 |

**FBrowser_文本数组 (3)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到火山文本数组` | 数组容器↔火山原生类型转换内部件 |

**类_FBrowser_同步辅助类 (3)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `停止等待` | 同步等待原语(供 SDK 内部阻塞式等待), 属线程/同步基础设施 |
| `添加字节集` | 字节集拼接内部实现(被多个回调用于累积响应体) |
| `清理数据` | 内部状态复位 |

**类_FBrowser_值转换 (3)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser_字节集到字节集` | 类型转换内部件(字节集↔火山字节集), 无用户可见能力 |
| `FBrowser_数据到字节集` | 同上 |
| `FBrowser_文本到字节集` | 同上 |

**类_FBrowser_应用事件 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_URL请求事件 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowserVIP_通用回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_JS交互事件 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_资源过滤器 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_下载图片回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_打开文件对话框回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_打印为PDF回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_V8环境 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser_V8环境_取当前环境` | 类库注释「只能在渲染进程中使用」; 本项目渲染进程是 SDK 自带 FBroSubprocess.exe, 该静态方法取的是当前(渲染)进程的上下文 |
| `FBrowser_V8环境_取运行环境` | 同上(GetEnteredContext) |

**类_FBrowser_字符串回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_JS回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_DOM回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_任务回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_Cookie回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_V8处理程序 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_V8存取器 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_清理缓存回调 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**FBrowser_矩形位置数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**FBrowser_拖拽位置数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**FBrowser_下划线组成数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**类_FBrowser_浏览器事件 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_资源处理器 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_开发者消息事件 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `类_初始化` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |
| `类_清理` | 框架生命周期方法(每个事件/回调基类都有), 由 SDK 在对象创建/销毁时自动调用, 不是可调用的用户能力 |

**类_FBrowser_字节集数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**类_FBrowser_POST元素数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**类_FBrowser_X509证书数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**类_FBrowser_V8值数组 (2)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `到下一个` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |
| `到数组首` | 数组容器的迭代原语(遍历 CEF 数组用), 属数据类型基础设施 |

**类_FBrowserVIP_控制器 (1)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `逐字分割` | 纯字符串工具函数(把文本按字符拆成文本数组), 被 高级键盘_输入文本 内部调用; 不是用户能力 |

**类_FBrowser_框架 (1)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `访问DOM对象` | 类库注释「只能在渲染进程中调用」; 本项目渲染进程为独立 FBroSubprocess.exe, 主进程不可用; DOM 能力由 browser_dom_*/CDP DOM 域覆盖 |

**类_FBrowser_服务器 (1)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `关闭连接` | MCP 自身 HTTP/WS 服务的连接管理(生命周期由进程掌控), 非浏览器能力 |

**类_FBrowser_事件智能指针 (1)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser创建事件智能指针` | 全局函数形式的等价物已在项目内普遍使用: `事件智能指针变量.创建(执行类)`(如 MCP_Server.wsv:1720/3370/5295) |

**类_FBrowser_请求环境 (1)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `FBrowser_请求环境_取全局` | 宿主侧全局请求环境句柄, 项目经 browser.取请求环境() 获取(MCP_Server.wsv:7868 取请求环境_安全) |

**类_FBrowser_拖拽数据 (1)**

| 类库方法 | 为什么它不是用户能力 |
|---|---|
| `增加文件` | 仅离线渲染(OSR)拖拽事件路径使用; 本项目为窗口内嵌渲染, 该类只在 离屏渲染_开始拖拽 事件参数中出现(MCP_BrowserEvents.wsv:3074), 且项目已声明 OSR 事件不触发 |

---

## (C) 存疑 —— 4 条

宁缺勿错: 以下条目我**无法在只读条件下判定**, 写清卡点与所需证据。

### `高级_创建标签浏览器` —— 类_FBrowserVIP_控制器

- 来源: `FBroVip.wsv`
- 声明: `方法 高级_创建标签浏览器 <公开 注释 = "VIP高级功能，需赞助后才能使用，谷歌模式下才可以使用，" 注释 = "在当前谷歌UI界面创建一个新的Tab标签浏览器，" 注释 = "设置了浏览器事件后即可和创建浏览器一样控制该标签浏览器"> 参数 地址 <类型 = 文本型 注释 = "可以为空，为空会获取当前浏览器的地址"> 参数 序号 <类型 = 整数 注释 = "UI上需要插入的序号位置，设置为-1为在末尾添加" @默认值 = -1> 参数 是否激活 <类型 = 逻辑型 注释 = "为真会激活并跳转标签，为假为不激活" @默认值 = 假> 参数 额外信息 <类型 = 类_FBrowser_字典值 注释 = "传递给事件的额外数据，可不设置，和创建浏览器不同的事这里不会传递给渲染进程" @默认值 = 空对象> 参数 浏览器事件 <类型 = 类_FBrowser_事件智能指针 注释 = "使用“FBrowser创建事件智能指针”全局方法或者在设置之前用该类型参数中的“创建”方法来创建一个继承于“类_FBrowser_浏览器事件”的自定义类事件；" 参数 禁用事件 <类型 = FBrowser_禁用事件 注释 = "当前浏览器器事件开关，可关闭某些不必要的事件加载，合理设置可提高加载速度" @默认值 = 空对象> 参数 标识 <类型 = 文本型 注释 = "设置创建后的浏览器的用户标识，设置后可通过用户标识获取到对应的浏览器，注意用户标识不要重复" @默认值 = "">`
- **卡点与所需证据**: 卡在「浏览器以什么 UI 模式创建」。类库注释限定「谷歌模式(Chrome UI)下才可以使用」; main.wsv:203-212 只用 FBrowser_窗口信息(父窗口句柄=0/坐标/宽高) 调 FBrowser_创建浏览器, 未见 CEF_RUNTIME_STYLE_CHROME(常量 谷歌=1, FBroConst.wsv:753) 的显式设定。需证据: ① 实测 browser_create 出来的浏览器是否有 Chrome 式 Tab 条; ② 或读 FBroConst.wsv 里 CEF_RUNTIME_STYLE_* 常量被哪个属性消费。若为普通窗口模式, 该项应改判为 B4(架构不适用)。

### `FBrowser_初始化_设置内存释放` —— FBrowser初始化控制

- 来源: `FBroLib.wsv`
- 声明: `方法 FBrowser_初始化_设置内存释放 <静态 注释 = "弃用，用于设置系统内部内存释放线程，必须在初始化之前设置，主进程设置后子进程不需要再设置，" 参数 循环周期 <类型 = 整数 注释 = "单位：毫秒；设置为-1使用默认值，默认值为1秒；0为不开启守护进程，大于0则为释放内存判断周期时间"> 参数 内存阈值 <类型 = 整数 注释 = "当内存超过多少时，执行内存释放，注意不要设置太小，不然老是在压缩内存反而降低效率">`
- **卡点与所需证据**: FBroSetReleaseMemoryCycleTime/FBroSetMaxReleaseMemory; src 0 命中。类库**自标弃用**「弃用, 用于设置系统内部内存释放线程」。卡在: 弃用后该 API 是否仍生效未知(需真机验证长驻进程内存曲线), 若已失效则应改判 B4。需证据: ① 一版带本调用与不带本调用的编译产物长时间运行的内存占用对比; ② 或向 SDK 作者确认弃用后的替代品(类库另有 FBrowser_内存_压缩清理, 已被 browser_compress_memory 暴露)

### `FBrowser_初始化_设置守护` —— FBrowser初始化控制

- 来源: `FBroLib.wsv`
- 声明: `方法 FBrowser_初始化_设置守护 <静态 注释 = "弃用，设置系统内部守护线程，必须在初始化之前设置，主进程设置后子进程不需要再设置，用于子进程判断主进程异常退出，子进程自动结束，避免进程残留，" 参数 循环周期 <类型 = 整数 注释 = "单位：毫秒；设置为-1使用默认值，默认值为10秒；0为不开启守护进程，大于0则为守护进程判断周期时间">`
- **卡点与所需证据**: FBroSetIsLiveMainProcessCycleTime; src 0 命中; 类库**自标弃用**「弃用, 设置系统内部守护线程」。卡在: 弃用 API 的实际效果未知; 且本项目已有自己的子进程残留治理(启动时检测上次渲染进程崩溃并清理缓存, main.wsv:67), 是否还需要守护线程需先确认。需证据: ① 强杀主进程后观察 FBroSubprocess.exe 是否残留(本项目已做过的类似真机验证); ② SDK 作者对弃用原因的说明

### `启用自带调试提示` —— FBrowser初始化控制

- 来源: `FBroLib.wsv`
- 声明: `方法 启用自带调试提示 <公开 静态 注释 = "仅调试模式下有用，启用模块类调试输出提示，一般指事件类初始化和销毁内部的只在调试模式下显示的提示信息；" 注释 = "全部类初始化在全局所以该设置屏蔽不到已经初始化的事件类，只能屏蔽设置后的；" 参数 是否启用 <类型 = 逻辑型>`
- **卡点与所需证据**: 类库注释「**仅调试模式下有用**, 启用模块类调试输出提示」; src 0 命中; 无工具暴露 SDK 自身调试输出开关。卡在: 本项目是 release 编译时(编译产物/编译命令未见调试版标记), 该开关可能完全无效果。需证据: ① 确认本项目构建是 debug 还是 release(编译参数/generated-cpp 产物); ② 调试版下实测 启用自带调试提示(真) 是否真的多出 SDK 事件类初始化/销毁提示。若为 release 构建 → 改判 B4

---

## 特别小节: 四族单独结论(它们的「缺口」性质不同)

### 1. `类_FBrowser_命令行`(启动参数类) —— 结论: **真缺口, 但必须做成启动通道而不是运行期工具**

见 A-1。要点复述: ① 13/15 条确认缺口, 2 条(`设置全局代理`/`禁用代理`)算误报(被 `browser_set_proxy`/`browser_clear_proxy` 的实例级代理覆盖, 差异只是全局 vs 实例); 
② **运行期调用无效**(CEF 已初始化), 所以「建议工具名」栏里我写的是通道而非工具位; 
③ 落点现成: `main.wsv:459` 的 `即将处理命令行` override 是空的, 正是插入开关的位置; 
④ `--headless` 在项目里已被 MCP 服务端占用(MCP_Stdio.wsv:225), 若新增浏览器无头开关**必须换名**, 否则语义冲突。

### 2. `类_FBrowser_菜单模式`(菜单与快捷键) —— 结论: **13 条全是真缺口, 但都是 P2**

- 该类是 `CefMenuModel` 包装(FBroLib.wsv:3288), 13 个方法在 `src` 中 **0 调用**; 
- 项目里该类**只作为事件参数类型**出现在 `MCP_BrowserEvents.wsv:2662`/`:2674`(`浏览器_即将打开菜单`/`浏览器_菜单被调用`)—— 事件**收得到 MenuModel 却什么都不做**, 只记录 `context_menu_opening/run/command/dismissed`; 
- 现有 `browser_kernel_menu` 的 action 只有 `disable/enable/status`(整块屏蔽右键菜单), 与「改菜单项」正交; 
- 非 CDP 可达: CEF 右键菜单模型不属于任何 CDP 域(CDP 无法增删原生菜单项); 
- 特性提示: `设置快捷键`/`设置快捷键_索引` 的类库注释写明「**只是用于显示快捷键, 触发需自行用键盘事件实现**」, 即它不产生行为, 只影响显示 —— 这也解释了为什么它是 P2。

### 3. `类_FBrowserVIP_控制器`(102 条) —— 结论: **误报 100 条, 真缺口 1 条, 存疑 1 条**

| 结果 | 条数 | 说明 |
|---|---|---|
| 误报·工具名覆盖 | 92 | 每条都能指名一个专属 VIP 工具(如 `内核开关_禁用Console*` 15 条 → `browser_vip_disable_console` 一个工具; `指纹_虚拟BatteryManager*` 4 条 → `browser_vip_fingerprint_battery`; `高级鼠标_*` 5 条 → `browser_vip_mouse_*`) |
| 误报·action 枚举覆盖 | 6 | `browser_fingerprint` 的 `canvas_random/webgl_random/audio_random/count/clear` |
| 误报·CDP 直通覆盖 | 1 | `高级_设置触发鼠标触摸事件` → `Emulation.setEmitTouchEventsForMouse` |
| 误报·非能力项 | 1 | `逐字分割`(内部字符串工具函数, 被 高级键盘_输入文本 调用) |
| **确认缺口** | **1** | `指纹_清空调用计数` |
| 存疑 | 1 | `高级_创建标签浏览器` |
| 合计 | 102 | |

误报率 **98%**(100/102) —— 这一族是最典型的「一个英文工具吃掉 N 个中文类库方法」: 原脚本按方法名做字面匹配, 而 MCP 侧是 `browser_vip_*` + 指纹一键工具, 名字不可能相似。

### 4. `类_FBrowser_应用事件`(27 条) —— 结论: **误报 27 条, 无缺口**

逐条核对方式: 把 26 个候选方法名逐个到 `src/main.wsv` 里找 `方法 <名> <公开 @虚拟方法 = 可覆盖>` —— **24 个事件方法全部被 `类_MCP_初始化事件` override**(该类 `基础类 = 类_FBrowser_应用事件`, main.wsv:256), 并写入 `app_*` 记录; 
第 25 条 `获取默认事件` 同样在 main.wsv:779 被 override; 余下 2 条是 `类_初始化`/`类_清理`(B4)。
开关由 `browser_collect`(event_app_enable / event_extension_enable / event_startup_enable / event_render_enable / event_renderws_enable)与 `browser_kernel_events_all`(MCP_Kernel.wsv:1205-1218 一次开 21 族)控制; 查询用 `browser_event(event_type="app_*")`。

| 类库事件 | 落地的事件名 / 行号 |
|---|---|
| `即将处理命令行` | app_startup_cmdline (main.wsv:470) |
| `执行关闭完毕` | override main.wsv:295 |
| `注册自定义方案` | override main.wsv:321(内核层注册 mcp:// 方案) |
| `扩展插件_创建成功` | app_extension_created (:599) |
| `扩展插件_创建失败` | app_extension_create_failed (:617) |
| `扩展插件_载入成功` | app_extension_loaded (:631) |
| `扩展插件_卸载成功` | app_extension_unloaded (:645) |
| `渲染_即将捕获异常` | app_v8_exception (:317) |
| `渲染_即将释放V8环境` | app_v8_released (:381) |
| `渲染_焦点节点改变` | app_dom_focus_changed (:369) |
| `渲染_即将初始化WebKit` | app_startup_webkit_init (:502) |
| `渲染_即将创建V8环境` | app_render_v8_context_created (:514) |
| `渲染_浏览器创建` | app_render_browser_created (:407) |
| `渲染_即将销毁浏览器` | app_render_browser_destroyed (:416) |
| `渲染_载入错误` | app_render_load_error (:397) |
| `渲染_收到消息` | app_render_message_received (:531) |
| `渲染_载入状态被改变` | app_render_loading_state (:552) |
| `渲染_载入开始` | app_render_load_start (:568) |
| `渲染_载入结束` | app_render_load_end (:584) |
| `渲染_VIP_WebSocket客户端_创建` | app_render_ws_created (:657) |
| `渲染_VIP_WebSocket客户端_关闭` | app_render_ws_closed (:670) |
| `渲染_VIP_WebSocket客户端_连接服务器` | app_render_ws_connect (:689) |
| `渲染_VIP_WebSocket客户端_接收数据` | app_render_ws_recv (:704) |
| `渲染_VIP_WebSocket客户端_发送数据` | app_render_ws_send (:721) |

> ⚠ **但这 24 条「已覆盖」要打个折扣**: 其中 `渲染_*` 一族属**渲染进程事件**, 而本项目渲染进程是 SDK 自带的 `FBroSubprocess.exe`(独立进程), 
> 项目自己在 `MCP_Server_Core.wsv` 的开关说明里写明: 「本族事件由 CEF 渲染进程触发…经真机验证, 这些事件**不会**被派发到本项目的事件覆盖上, 因此 app_render_* **不会产生任何记录**…需要页面侧信息请改用 browser_execute_js / browser_snapshot / browser_dom_query」; 
> `渲染_VIP_WebSocket客户端_*` 同段亦有同款声明。**所以它们的「覆盖」是声明层的覆盖: 事件名注册了、override 写了, 但不会有数据。** 
> 这类「名义覆盖」建议你单独按「能力是否真的可用」再筛一遍 —— 我按任务书的三向核对口径只能记它「非缺口」(事件族与查询工具都在), 但可观测性上它是空的。

---

## 附: 本次复核中「最容易误判」的三类候选(给后续审计的避坑记录)

原脚本 `classlib_gap.py` 的匹配口径是「类库方法名(或其前 3 字)是否出现在任一工具的描述文本里」。这个口径的漏洞不是「不够聪明」, 而是**方向错了**: MCP 工具名是英文、类库方法名是中文, 覆盖关系往往既不相似也不同长。三类具体陷阱:

### 陷阱 1: 一个英文工具吃掉一整族中文方法(批量覆盖)

| 类库方法(候选) | 实际覆盖者 | 为什么字面匹配必然漏 |
|---|---|---|
| `内核开关_禁用ConsoleLog` / `ConsoleWarn` / `ConsoleError` / … 共 **15 条** | 一个工具 `browser_vip_disable_console`(`MCP_Server_VIP.wsv:1658-1672` 15 行连续直调) | 「ConsoleLog」与工具名、工具描述都不重合 |
| `指纹_虚拟BatteryManagerLevel` / `Charging` / `ChargingTime` / `DischargingTime` **4 条** | 一个工具 `browser_vip_fingerprint_battery` | 同上 |
| `渲染_载入结束` / `渲染_载入错误` / `渲染_浏览器创建` … **24 条** | 一个工具 `browser_event` 的 `app_*` 族(24 个 override 全在 `main.wsv`) | 工具描述里根本没有「渲染_载入结束」这种词 |

### 陷阱 2: 覆盖藏在**工具的参数开关**里, 不在工具名里

| 类库方法(候选) | 实际覆盖者 | 说明 |
|---|---|---|
| `停止载入` | `browser_stop` | (用户已举的反例)名字毫无字面关系, 但 `MCP_Server_Core.wsv:167` 直调 `browser.停止载入 ()` |
| `高级_发送鼠标事件` / `高级鼠标_单击` / `高级鼠标_移动` / `高级鼠标_滚轮滚动` | `browser_mouse_click` 等工具的 **`kernel:true` 参数** + `browser_vip_mouse_*` 专属工具 | 内核实现在同一工具的另一条参数分支里(`MCP_Server_Core.wsv:643`), 按工具名匹配永远看不到 |
| `指纹_虚拟Canvas_随机` | `browser_fingerprint` 的 **`action=canvas_random`** | 多合一工具的 action 分支不写进工具描述也能生效 |

### 陷阱 3: 只看「第一个消费者」就断言「死路径」(我自己踩过)

复核 `FBrowser_V8_注册JS扩展` 时, 我先看到 `browser_inject persist=true` 把代码存进 `持久V8扩展列表`(`MCP_Server.wsv:1864`), 而该列表在 `MCP_BrowserEvents.wsv:157` 的读取处**只打印条数**; 又看到真正「该」消费它的 `渲染_即将创建V8环境`(`main.wsv:505`)只记录事件不做注入 —— 于是写下「persist 是死路径, 这是确认缺口」。
**这个结论是错的**: 换一个 grep 词(`应用持久V8到框架`)才发现真正的消费者在 `MCP_BrowserEvents.wsv:1537` 的 `浏览器_载入开始` 事件里, 一路走到 `MCP_Server.wsv:2088 应用持久V8到框架` → `框架.执行JS代码`, 而且做了标识去重、管道符转义还原等完整处理。所以 `FBrowser_V8_注册JS扩展` 最终判 **B1(非缺口)**, 报告里只保留「原生 V8 扩展通道未暴露」这条残余差异说明。
**教训**: 断言「某能力缺失」前, 至少用 2~3 个不同关键词检索, 并追踪**数据结构的所有读者**; 只追踪函数名会漏掉经中间方法消费的路径。

---

## 统计

| 项 | 数量 |
|---|---|
| 复核的候选总数 | **363** |
| **(A) 确认缺口** | **46**(P0 2 / P1 9 / P2 35) |
| (B) 误报合计 | **313** |
| &nbsp;&nbsp;B1 工具名覆盖 | 184 |
| &nbsp;&nbsp;B2 action 枚举覆盖 | 11 |
| &nbsp;&nbsp;B3 browser_cdp_call 直通覆盖 | 7 |
| &nbsp;&nbsp;B4 非能力项(口径扩展, 非「被覆盖」) | 111 |
| (C) 存疑 | **4** |
| **误报率(含 B4)** | **86.2%** |
| 误报率(严格三类, 不含 B4) | 55.6% |
| 确认缺口率 | 12.7% |

对照上一轮 `_classlib_gap_confirmed.md` 的口径: 上轮只覆盖 7 个优先类的 210 条候选(得到 31 条「真缺口」, 误报率 72.4%); 
本轮覆盖全部 363 条 + 全部 312 个工具 + 三向核对, 误报率 **86.2%** —— 说明原脚本(「方法名或其前 3 字出现在任一工具描述文本里」 的匹配口径)**本地几乎不可用于判断缺口**, 只能当候选生成器。

---

## 复现方式(全部只读)

```
py -3 _audit/cg2_extract.py     # 工具名全集 + 类库方法全集(含参数表) + 分派器分支 -> _cg2_data.json
py -3 _audit/cg2_cands.py       # 从 _classlib_gap.md 解析 363 候选 -> _cg2_cands.json
py -3 _audit/cg2_index.py       # 工具注册全文/schema/分支/字面量索引 -> _cg2_index.json
py -3 _audit/cg2_direct.py      # 候选在 src 中的同名直调扫描
py -3 _audit/cg2_covmap.py      # 把每个直调点归属到所属工具分支  -> _cg2_covmap.json
py -3 _audit/cg2_classify.py    # 逐条判定 -> _cg2_verdict.json(363 行, 每行含 verdict/route/who)
py -3 _audit/cg2_report.py      # 生成本报告
```

其它辅助: `cg2_zero.py`(无直调清单) `cg2_vipcalls.py`(VIP 控制器调用点) `cg2_vip102.py` `cg2_def.py`(类库声明速查) `cg2_adecl.py` `cg2_find.py`(定向 grep) `cg2_show.py`(工具定义速查) `cg2_toolcat.py`。

> **本报告是候选清单 + 证据, 不是结论, 也未经真机验证。** 所有「缺失」判定均为静态源码证据; 「非缺口」判定基于读实现, 但**未逐个真机调用**。请对 A 段每一项按「先复现缺口, 再实现, 再验收」流程处理。
