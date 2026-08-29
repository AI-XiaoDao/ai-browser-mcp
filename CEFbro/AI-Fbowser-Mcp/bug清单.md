# AI浏览器 MCP Server — Bug 清单与修复记录

> 创建时间：全量分析后 · 修复方式：按《火山视窗技能书》规范（先备份 备份/ 目录 → 保持 UTF-8 无 BOM → 最小增量修改 → 逐项验证）
> 备份目录：CEFbro/AI-Fbowser-Mcp/备份/（10 个 .bak，可随时还原）

## 已修复（29 项）

### 第五轮：MFC 浏览器内核层面能力扩展（新增 5 工具 + 1 注册 + 4 事件接线）
### 第六轮：开发者事件组合 + 动态逆向能力套件（新增 13 工具，工具注册 260 -> 266）
### 第七轮：全量运行探测（部署版 v3.0.0/255 工具真机测试）
### 第八轮：编译错误修复（用户 IDE 编译反馈驱动）

### 第八轮补充：裸嵌套引号根因 + IDE 缓冲不同步

### 第九轮：C++ 编译阶段（火山解析全通过）

### 第十轮：附属文件缺失（workflows 目录）

- MCP_Server.wsv L233 `@视窗.附属文件 = "..\\workflows > workflows"` 声明编译期复制 workflows 目录，但源码目录缺失 → 编译报"未找到目录"
- ✅ 已创建源码 `workflows/` 目录并复制 6 个示例工作流（hello/ping_navigate/automation_form/debugger_breakpoint/debugger_full/reverse_analyze，取自部署目录）——附属文件全部齐备

- **C2562（我方代码）**：执行定期维护 void 方法内 `@ ... return CVolString();`（R15 原子占位）→ 已改 `return;` ✓；全 src 无其他 @ return 残留 ✓
- **17 个 C4244/C4715/C4005**：全部为 FBrowser 类库（E:\HSPC\...\FBroCallback/FBroValue/FBroLib）与 SDK 10.0.26100 环境警告提升（BOOL_P→逻辑型、变整数→int、_malloca 宏重定义）——非项目代码问题（类库/SDK 环境）；用户以前编译成功说明类库或 SDK 更新过
- **用户操作**：火山 IDE → 项目 → 本地编译选项 → 附加编译参数 `/wd4244 /wd4715 /wd4005`（或调低警告级别）；SDK 26100 与 VS2019(编译器16) 的 _malloca 冲突可考虑换 VS2022/匹配 SDK

**MCP_Server.wsv 5835"字符无效位置"根因确认**：工具注册行 6 处 `""action""`（4 引号裸嵌套）——TS 字符串转义在写入时被解码为裸引号，火山源码中 `""action""` = 空串+标识符+空串（语法错误），且解析错乱波及 5835 区域。已修复为 `"action"`（合法字符串）；全 16 文件裸嵌套扫描：全部干净 ✓。

**Kernel 240 类型错**：磁盘 Kernel 240 行 = `否则 (动作 == "clear")`（正常）；用户 IDE 缓冲为旧版（含 `包.加入逻辑值成员 ("note", 文本)` 误用行）——磁盘对应行已是 `加入文本成员`（362 行）✓。加入逻辑值成员 文本值误用全文扫描：无 ✓。

**用户操作**：IDE 关闭 Kernel/Server 标签页重新打开（或关闭项目重开）加载磁盘最新文件；或命令行编译绕过 IDE 缓冲：
`voldev_wp.exe @compile "...\AI-Fbowser-Mcp.vsln" /r`
若仍报 240：请提供 IDE 中该行内容。

**第一轮编译（14 错误）**：vprj 丢失 file16（IDE 重写）→ MCP_Kernel.wsv 未参与编译 → 8 处"未找到 MCP_内核分派"；vprj 已重新确认包含 file16 + num_files=16。

**第二轮编译（152 错误，Kernel 全面暴露）**：
- return 误用（火山关键字为 返回）：字符串外 return→返回 112 处（JS 注入串内保留 45 处）
- 置成员 方法不存在：改 数组置成员 辅助方法（重建保序）+ 6 处调用
- @输出参数 属性不存在：取方案内容 重构为返回 JSON 文本（打开 方法同步适配）

**第三轮编译（7 错误，均为连锁）**：MCP_Server.wsv 逻辑行 5835 区域（物理 6150 匹配文件 段）磁盘文件已验证干净——用户 IDE 缓冲为旧版本（物理 8384 vs 磁盘 9417）；Kernel 240 类型错为 MCP_Server 编译失败的连锁反应。

**用户行动**：IDE 中关闭项目重开（加载磁盘最新文件）或命令行编译（voldev_awsp.exe @compile vsln）绕过 IDE 缓冲。


**探测方法**：启动部署版 exe → HTTP 直连 → 轮1 全量 255 工具异步无参调用（分派可达性）+ 轮2 52 个代表性真实调用 + 聚焦复测 13 项 + CDP 通道状态探针。

**探测结果汇总**：直接可用 122 / 参数校验拦截 70 / 异步提交 24 / 预期状态错误 36（无历史后退、未暂停调试器、禁用项、confirm 确认等，全部为设计行为）/ 致命超时 3。

**发现并修复**：
- P1【高】browser_debugger_flow 无 breakpoint 校验 → 无参调用挂起持协议锁，堵塞整个 CDP 队列（FIFO），殃及 evaluate/reverse_*/dom_inner_html 等全部 CDP 依赖工具直至数分钟超时自愈（复测确认：debugger_enable/resume 等 6 个工具连锁超时）→ 源码已修：flow 入口 breakpoint 必填校验；debugger_script_source 无暂停上下文且无 script_id 时快速失败
- P2【中】browser_dom_query 同步返回 isError "null"（异步正常）→ 根因：JS消息是否表示失败 将 dom_query/dom_get_html 的 "null" 值判定为失败，但 取元素内容 对 body 等非输入元素返回 null 属正常语义 → 源码已修：移除该判定（element not found 独立拦截保留）

**确认非 bug（预期行为）**：snapshot/detect_obfuscator 偶发序列化错误=页面加载时序；reverse_strings 大页面 30s 超时=需 async_only/增大 max_ms；browser_find_by_tag 未找到=正常；click_text/snapshot/extract 等交互类正常。

**部署差异**：部署 exe 为旧版编译（tools/list 仍含已剔除的 browser_debugger_pause；不含新增 13 个内核工具）→ 需重新编译部署后生效。


**IPC 双向通道**（基于 进程间消息 系列官方签名）：
- 修复 browser_send_message 方向错误（原误用渲染进程专用 API 发送数据_到主进程，主进程调用恒失败 → 改 发送数据_到全部渲染进程）
- main.wsv 接线 进程间消息_收到主进程消息（渲染侧接收 → 注入 window.__mcp_ipc_queue 供页面 JS 消费）
- MCP_BrowserEvents.wsv 接线 浏览器_收到消息（OnProcessMessageReceived 记录 ipc_from_renderer 事件）

**事件组合能力**（5 工具）：
- browser_kernel_ipc_queue / ipc_clear — 渲染侧应答队列读取/清空（双工 IPC 上行）
- browser_kernel_cdp_monitor — CDP 事件订阅（methods 前缀模式 + 上限，命中写 event_log 供 browser_event 查询）
- browser_kernel_reactor — 事件反应器规则引擎（event 模式 + JS code + cooldown，记录监控事件入口触发异步执行）
- browser_kernel_watch — 定时监视（expression 周期求值 + 变更检测 → watch_changed 事件日志，主循环节拍驱动）
- browser_kernel_events_all — 一键全事件流（13 项浏览器/应用事件 + 控制台 + 网络详细）

**动态逆向能力套件**（6 工具，页面内 JS 插桩 + CDP Runtime.evaluate 注入/取回）：
- browser_kernel_reverse_probe — 五维 API 插桩（XHR/fetch/WebSocket/定时器/事件监听，URL/状态/响应/调用栈 → __MCP_PROBE__）
- browser_kernel_reverse_trace — 动态调用追踪（目标函数包装：调用栈+参数+返回值+耗时 → __MCP_TRACE__，targets 点路径解析）
- browser_kernel_reverse_algo — 动态算法 Hook（CryptoJS 全算法 + 全局哈希/base64 + WebCrypto subtle，算法名/参数/输出/调用栈 → __MCP_ALGO_LOG__）
- browser_kernel_reverse_functions — 动态函数提取（window/对象链/prototype 枚举，路径/函数名/参数个数/toString 源码，filter+max）
- browser_kernel_reverse_sources — 动态 JS 源码提取（document.scripts 全量含 inline，index 单脚本 + max_len 截断）
- browser_kernel_reverse_watch_global — 全局变量动态追踪（defineProperty setter 记录写入者调用栈+新值 → __MCP_GWATCH__）

**验证**：MCP_Kernel.wsv 结构花括号差 0（32 方法）；字符串内 11 处不平衡全部为错误前缀匹配串（预期）；全部 API 依据 FBrowser 官方签名。


**依据**：FBrowser浏览器 类库官方签名（FBroLib / FBroEventControl / FBroCallback / Scheme_callback 官方示例），全部 API 经技能库资料核验，无臆造。

| 新增 | 说明 | 内核依据 |
|---|---|---|
| `browser_kernel_cert` | 证书错误记录 list / ignore 忽略开关 / clear / status | 浏览器_请求证书错误 (FBroEventControl:621) + 类_FBrowser_SSL信息 |
| `browser_kernel_auth` | HTTP Basic/Digest 认证凭据注入 set/clear/list | 浏览器_获得需授权证书 (FBroEventControl:682) + 类_FBrowser_授权回调.继续(用户,密码) |
| `browser_kernel_download` | 下载 pause/resume/cancel（事件内即时执行队列）+ clear_queue | 浏览器_正在下载 (FBroEventControl:1225) + 正在下载回调.暂停/恢复/取消 (FBroCallback:349-362) |
| `browser_kernel_scheme` | 自定义协议 mcp://域名 动态内容 register/unregister/clear/list | FBrowser_自定义方案_注册 (FBroLib:146) + 类_FBrowser_资源处理器 (FBroEventControl:1828) + main.wsv 初始化期注册自定义方案 (CEF_SCHEME_OPTION_STANDARD=1) |
| `browser_kernel_menu` | 右键快捷菜单屏蔽 disable/enable/status | 浏览器_即将运行快捷菜单 (FBroEventControl:1153, 触发条件以实际内核为准) |

**接线**：src/MCP_Kernel.wsv 新建（16 方法：5 分派 + 5 事件侧辅助 + 资源处理器 6 事件）；MCP_BrowserEvents.wsv +3 事件（证书错误/认证/快捷菜单）+ 下载事件增强；main.wsv +注册自定义方案；MCP_Server.wsv 路由直投 + 回退链 + 工具注册；vprj +file16。

### 第四轮（全量稳定性扫描：竞态/数据错乱/失效功能/资源运行时）

### 第三轮（全量稳定性扫描修复）

### 第二轮（遗留问题逐项修复）

| # | 严重度 | 位置 | 问题描述 | 修复内容 | 状态 |
|---|--------|------|----------|----------|------|
| BUG-1 | 高 | src/MCP_Constants.wsv | MCP 协议版本声明为未来日期 "2026-08-14"，直连客户端（不经桥接）协商可能异常 | 改为已发布版本 "2025-06-18" | ✅ |
| BUG-2 | 中 | AI-Fbowser-Mcp.vprj | version_name "2.8.2" 与 MCP_常量.MCP_版本号 "3.0.0" 口径不一致 | vprj 版本统一为 "3.0.0" | ✅ |
| BUG-3 | 低 | mcp_bridge.js | 注释仍写"服务端为 2026-06-21"（与常量不符） | 更新为 2025-06-18 | ✅ |
| BUG-4 | 中 | README.md | "workflow 最多 200 步批量执行"与实现不符（实现无步数上限，仅 30 分钟总时限；200 是 batch 上限）| 修正两处描述（batch 单次最多 200 条；workflow 无步数上限）| ✅ |
| BUG-5 | 低 | 5 个 .wsv（Server 24 / BrowserEvents 19 / HTTP 4 / Workflow 2 / Callbacks 1）| **51 处**日志拼接缺陷：`到文本("前缀") + ", " + 到文本(x)` 输出形如 `[MCP] 浏览器创建完毕 [ID:, 1, ]` 的多余逗号 | 全部清理为 `"前缀" + 到文本(x)`（保留字面量内原有标点）| ✅ |
| BUG-6 | 低 | src/MCP_Server_HTTP.wsv | "WS消息长度"日志与"收到命令"日志重复输出 | 删除重复日志行 | ✅ |
| BUG-7 | 低 | src/MCP_Server.wsv | notifications/cancelled 日志两值直接拼接无分隔符 | 加 " 原因:" 分隔 | ✅ |
| BUG-8 | 中 | docs/MCP工具配置说明书.md | CURSOR_MODE 精简模式描述过期（v2.8.1 起桥接层已移除工具白名单过滤，全部工具动态显示）| 两处表格行更新为"已移除/已失效" | ✅ |
| BUG-9 | 低 | docs/index.html | 协议示例仍用旧版本 "2026-06-21"（与常量不一致）| 示例更新为 "2025-06-18" | ✅ |

| BUG-10 | 低 | src/MCP_Constants.wsv + MCP_Server_System.wsv | GWL 索引 -20/-12 硬编码散落（-16 已有常量）| 新增 窗口样式_GWL_EXSTYLE(-20)/窗口样式_GWL_ID(-12) 常量并替换引用，错误文案同步引用常量 | ✅ |
| BUG-11 | 低 | docs/QUICKSTART_ZH.md / QUICKSTART_EN.md | 工具数口径 "268" 与全项目 "255" 不一致（4 处）| 统一为 255 | ✅ |
| BUG-12 | 中 | 9 处文档（使用技能书/README/QUICKSTART×2/配置说明书/index.html×2/mcp_config.README）| 引用 skills/AI浏览器MCP.md 等文件，但 skills/ 目录未随仓库发布（悬空链接）| 全部改指实际存在的 docs/ 文档与 tools/list 动态接口 | ✅ |
| BUG-13 | 低 | mcp_config.README.md | 字段简表缺 vip_code/auto_install_agents/window_topmost/window_width,height | 补全 4 行 | ✅ |

| C1 | 高 | src/MCP_Server.wsv 读取HTTP_POST体 | HTTP POST 请求体无大小上限（整数累加），超大 body 可致内存膨胀/OOM（WS 侧已有 50MB 上限）| 总字节数改长整数，边累加边检查 50MB 上限（与 WS 一致），超限拒绝并记日志 | ✅ |

| R1 | 高 | MCP_BrowserEvents.wsv + MCP_Server.wsv | 导航拦截规则在 CEF 回调线程无锁直读（写侧持规则锁）→ 撕裂读风险 | 新增 取导航规则快照（持锁复制），读侧改基于局部副本 | ✅ |
| R2 | 高 | MCP_Server.wsv 关闭缓存数据库 | 关闭无锁，退出期 CEF/HTTP 线程可能并发访问已关闭连接 | 关闭前取异步缓存锁 | ✅ |
| R3 | 中 | MCP_Server.wsv 修剪异步结果表 | 超限强制删除会删 is_waiting=1 的轮询中任务 → 客户端假"未找到任务结果" | 强制删除排除等待任务（1小时滞留兜底回收）| ✅ |
| R4 | 中 | MCP_Server.wsv 存储任务结果 | REPLACE 仅 4 列 → 覆盖时 browser_id/poll_count 归零，跨浏览器等待误触发 | 保留既有 browser_id/poll_count + 等待态改 JSON 解析 | ✅ |
| R5 | 高 | MCP_Server.wsv 记录事件日志 | 超限任意截断切坏 JSON → 网络/事件/控制台日志整段不可解析 | 截断后 yyjson 重建合法对象（_truncated/_original_len/_preview）| ✅ |
| R7 | 低 | MCP_Server.wsv 清理过期下载 | 每 60 秒全目录扫描 | 每日首次触发（静态 OLE 日期）| ✅ |
| R8 | 低 | MCP_BrowserEvents.wsv | 崩溃恢复标记写入失败无告警 → 连环崩溃复现 | 写失败告警 | ✅ |
| R9 | 中 | MCP_Server.wsv + MCP_Server_HTTP.wsv | 取启动时间 32 位回绕（24.85天）：/health uptime 变负、IP 限流分钟桶错乱 | 分钟桶与 uptime 改墙钟基准 | ✅ |
| R10 | 中 | MCP_Stdio.wsv | 停止Stdio 无条件 停止() → 线程卡 CEF 长调用时主线程死等 | 置标志 + 3 秒超时轮询，超时放弃（进程退出强制终止）| ✅ |
| R11 | 低 | MCP_Callbacks.wsv | select_index 非法索引静默变 0 误选第 0 项 | 校验后明确报错 | ✅ |
| R12 | 高 | MCP_Server.wsv + MCP_Server_Core.wsv | MCP可中断延时 隐含"调用方持锁"契约，browser_create 先解锁再调 → 无主解锁破坏锁计数 | 加 是否持锁 参数，违约点传假 | ✅ |
| R13 | 高 | MCP_Server_Core.wsv | mcp_result stub-follow 只跟随非等待 stub → js_exec 轮询 stub 行假超时、真实结果丢弃 | 等待中 stub 也跟随，仅真实结果就绪时替换 | ✅ |
| R14 | 低 | MCP_Server.wsv | JSONRPC 信封快速通道不校验，非法 JSON 直通 | 先校验，失败走 _raw 包装 | ✅ |
| R15 | 中 | MCP_Server.wsv | 主循环节拍与请求入口双路径 check-then-set 非原子 → 并发维护 | Interlocked 原子占位防重入 | ✅ |
| F3 | 高 | MCP_Server.wsv + README.md | browser_debugger_pause 在 tools/list 广告但恒失败（会冻结页面堵塞 CDP 队列）| 从工具清单剔除，README 能力表同步（15 项），保留路由返回指导性错误 | ✅ |
| F2 | 低 | MCP_Callbacks.wsv | 类_MCP_任务回调 死代码（无实例化点）| 删除 | ✅ |
| D5 | 低 | MCP_Server_HTTP.wsv + MCP_Server.wsv + docs | /cursor-config 与自动安装仍输出已失效的 CURSOR_MODE | 4 处全部移除 | ✅ |
| D2/D3/D4/D6/D7/D8/D9 | 低 | 五份文档 | 环境变量表缺 WS/VERSION；code_base64 适用性错误；sync-wait 白名单边界缺失；字段表缺 4 字段；端点表缺 /api 等；event_all_enable 排除项与默认值未注明 | 全部修正/补全 | ✅ |

## 排查后确认非 Bug / 记录为已知限制（不动）
- 同步等待协议锁串行化（技能书承诺"单浏览器脚本顺序执行"，设计取舍）
- 静态上下文（当前命令方法名/目标浏览器ID）放锁窗口并发覆盖：需大面积固化重构，风险高，暂记录
- response_cache url 主键不含 method/mime：改表结构风险中，暂记录
- 聚合上限（条数×单条无总尺寸约束）：M3 已缓解（合法 JSON 包装），DB 尺寸上限暂记录
- 崩溃/重建标志位无锁：bool/长整数撕裂概率低，暂记录
- CDP 映射清理扫描上限 10 万：低概率，暂记录
- workflow.stop 畸形 JSON 快速通道：已确认解析失败立即返回，影响可忽略
- 截图 7680 尺寸上限：236MB 单帧理论峰值，低内存机器建议用户自控
- Core:5670 脚本索引：已有校验（确认无需修）

| 项 | 结论 |
|----|------|
| `寻找文本` 语义（MCP_Server_HTTP.wsv:223 DevTools WS 判定）| 0-based 索引已被 MCP_Server.wsv:6940 注释证实，判定正确 |
| 响应结构非 MCP 标准 content 数组（{id,success,message,data}）| 设计取舍（桥接层已兼容 Cursor），改动风险大，不动 |
| VIP 内置兜底授权码 "xsmzas1" | 产品设计（Release 全功能策略），非代码缺陷，不动 |
| vprj 冗余 MFC 模块（MFC界面基本类等 3 个）| 移除有编译风险（FBrowser 类库可能间接依赖），建议人工确认后处理 |

## 验证记录

- ✅ 修复后 `", " + 到文本` 残留：**0 处**
- ✅ 与备份逐行 diff：仅预期行变化（50 处逗号清理 + 1 处删行），结构/行数不变（Server 8954 / BrowserEvents 1112 / HTTP 287 / Callbacks 1284 / Workflow 844）
- ✅ 无语法异常模式（空拼接/多余括号）：0 处
- ✅ 全部文件保持 UTF-8 无 BOM
- ✅ "2026-08-14" / "2026-06-21" 已无残留


---

## 第十一轮：原生 MCP stdio 直连 + 全功能免VIP + 帧格式规范修复（2026-08-29）

### 1. Claude Code 30秒连接超时根因（MCP 标准合规）
- **根因**：原生 exe 与 node 桥的 stdio 输出均使用 Content-Length 帧；官方 MCP SDK（2025-06-18 规范）客户端按换行分隔 JSON 解析（JSON.parse(line)），收到 CL 头直接解析失败 → 握手无响应 → 30s CONNECT_TIMEOUT。
- **修复**（MCP_Stdio.wsv）：输出帧格式自适应——客户端发 Content-Length 帧→回 CL 帧；客户端换行分隔（官方 SDK）→回换行分隔 JSON。读取侧本就双格式兼容（字节级 ReadFile + PeekNamedPipe）。
- **修复**（mcp_bridge.js）：同步自适应（writeLine 按客户端输入帧格式回帧）。
- **验证**：新行分隔客户端 initialize / tools/list(265) / ping / tools-call 全通过；CL 帧客户端回 CL 帧通过；bogus/method 返回规范要求的 -32601。

### 2. 原生 stdio 模式落地（--mcp-stdio，零 Node 依赖）
- 复用既有 MCPStdio桥（MCP_Stdio.wsv）：AI-Fbowser-Mcp.exe --mcp-stdio 直接 stdin/stdout 讲 MCP 协议。
- main.wsv：stdio 模式跳过单实例互斥体（可与常驻 HTTP 实例并存）、跳过 auto_install_agents。
- MCP_Server.wsv：stdio 模式不创建 HTTP 服务器（避免端口冲突）；欢迎页改 about:blank。
- 实测：与常驻实例并存时原生 stdio 完整工作；父进程退出（stdin EOF）自动停止。
- ~/.claude.json 已切为原生模式：command = AI-Fbowser-Mcp.exe, args = [--mcp-stdio]。

### 3. 全功能免 VIP（成品所有用户可直接调用）
- 类库门控分析：FBrowserVIP 全部功能门控 = FBrowser初始化控制.是否为VIP（公开静态变量）；取VIP控制器 本身不检查授权；DLL 无逐调用校验。
- **修复**（main.wsv）：FBrowser初始化控制.是否为VIP = 真 无条件强制解锁（在 VIP注册_置授权码 之后、FBrowser_初始化 之前）。
- **实测验证**：假授权码（GARBAGE-INVALID-KEY-12345）+ 强制标志 → browser_fingerprint_ua 返回“UA完整指纹已设置”（VIP DLL 功能真实执行）、vip_* 工具全部进入功能逻辑，无“VIP控制器不可用”。
- 部署版验证：browser_fingerprint_ua → success。
- mcp_config.README：vip_code 字段标注“成品已免VIP，仅保留兼容”。
