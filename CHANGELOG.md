# 更新日志

本文件记录面向用户的版本变更。发版流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [3.0.0] - 2026-08-17

### 修复（源码优化升级批次：P0×1 + P1×22 + P2×70+）

- **P0 stdio 传输失效**：`MCPStdio桥.读取一行` 内联 C++ 循环后残留的 `return CVolString()` 使火山返回代码不可达，stdio 模式恒空读后自断退出；已删除并理顺读取路径
- **P1 桥接层中文请求卡死（复审仿真发现）**：mcp_bridge.js 帧解析用 JS 字符串长度(UTF-16单元)对比 Content-Length(UTF-8字节数)，含中文/emoji 的请求体永远等不满帧；改为字节级缓冲解析（Buffer 累积 + ascii 头解析 + 字节切片 utf8 解码），113 项场景套件全部通过
- **全面复审批次（三个并行复审 + 场景套件 + 静态核验）**：修复 14 项确认问题，含 permission_spoof 转义顺序回归、安装代理配置空 mcpServers 插入错位（非法JSON）、stdio 空行分隔符条件消费（分块写帧体错位）、yyjson取逻辑_默认 布尔/数值节点失效、持久配置锁覆盖反检测字段、64MB帧拒绝后排空、字节截断切中文产生U+FFFD（新增 字节安全截断）、line_replace CRLF 行尾风格、preload 读前大小预检、set_zoom JSON数字0、task_ 片段长 1-based 补偿等
- **Stdio 加固**：Content-Length 64MB 上限；取消"帧尾换行消费"防下一帧错位；空闲不再误判断开（仅句柄关闭退出）；帧体不完整整帧丢弃；头部 Peek 轮询防停止死等；写入帧对齐 MCP 规范（去多余尾换行）
- **并发修复**：新增 `事件节流锁`（焦点回调 vs 定期维护的 CEF 字典无锁读写）；新增 `工作流状态锁`（工作流状态变量含 CVolString 跨线程读写）；`分配CDP消息ID` 返回原子操作结果；`生成异步任务ID` 改 InterlockedIncrement64；CDP 映射清理计数移入锁内；/tools 缓存重建纳入协议锁
- **正确性修复**：browser_create 比较-清除防抹掉 __SHUTDOWN__ 关闭标记；browser_set_cookie 子域名改结尾判断；browser_retry 拒绝重试自身；browser_fill_select 改用 select 选项 API；存在后填表回调 success 区分"已执行"；line_replace 补 UTF-8 边界处理；reverse_extract analyze 输出真对象数组；vip_get_js_env_ids ids 改真数组；工作流 task_id 提取按 1-based 截断；wait_for_load 布尔感知；主线程关闭延时改非阻塞
- **JSON/协议**：JSON转义补全全部控制字符；异步响应去除重复 result 键；持久V8管道符转义四层往返无损；/health db_stats 补扁平字段、uptime 改单调时钟；空 body 回 400 语义；workflow_stop 快速通道空闲返回真实语义
- **安全**：验证安全路径补尾分隔符防兄弟目录越界；replace_file 补路径白名单与缺字段提示
- **性能**：轮询参数循环外构造；日志 limit/max_ms/fields/functions 等全部钳制上限；截断按字节；js_bridge 帧解析重写+背压写队列+死代码清理
- **功能**：补 browser.create/browser.close 点号双路由；工作流汇总新增 delay_count（delay 不再计入 success_count）
- **并发加固（第二轮）**：新增 `持久配置锁`（持久代理/缩放/静音字段跨线程读写）；导航重定向链式保护（2秒内>10次放行，防互指规则死循环）
- **资源安全（第二轮）**：截图宽高上限7680/scale上限4；reverse_extract 取数组判空；下载进度回调对象判空；打开缓存数据库改列存在性检查
- **重构（第二轮）**：欢迎页三方法主体去重为 `导航欢迎页内部()`
- **持续找 bug（第五轮，静态扫描 15 维度 + 锁对象逐名核验）**：未知命令回退路径补静态上下文恢复；fingerprint webdriver 键存在性改 取类型()==未知；fill_select 改原生 value setter（React 受控兼容）；workflow delay 步骤补记录；崩溃防护计数改 Interlocked 原子接口；response_cache 警告日志移出锁；5 处失效行号注释与锁序注释修正
- **实机功能测试批次（32/32 全绿）— 发现并修复系统性 0-based 语义缺陷**：经火山 SDK `_vol_str_impl.cpp` 源码证实 `SearchText` 返回 0-based 索引（技能书文档误标 1-based），全库 14 处算术系统性差一——URL 安全拦截失效（javascript:/file:/data: 放行）、域名提取少末字符（同域 Cookie 被误拒）、前导点剥离连域名首字符、查询串剥离、DevTools WS 拒绝失效、CDP 日志去括号、task_id 提取四处、file: 前缀剥离等，全部修正并编译+实机复测通过
- **将异步结果转为命令响应 重复 result 键**（YYJSON对象分支）→ 排重
- **stdio 非管道 stdin 支持**：文件/控制台重定向原被 PeekNamedPipe 误判断开，改 GetFileType 判别 + 直读模式；stdio ping 冒烟通过
- **navigate/reload wait_for_load 同步等待真实生效（流畅与稳定性轮）**：原"防竞态补查"仅以 `取加载状态()==假` 判定页面已加载完，而 `载入地址()` 发出后 OnLoadStart 尚未到达时该标志仍为假 → 同步等待立即返回"已导航到…通过mcp_result查询"提交消息，页面实际还在导航中。修复：新增 `浏览器容器.最后载入结束毫秒`（OnLoadEnd 时记录），补查仅当"本次导航发起后确实发生过 load_end"（时间戳≥载入前发起毫秒）才即时完成；同址导航改由 browser_navigate 在载入地址()前判等直接返回"已在目标页面"（竞态安全）
- **自托管页面死锁防护（navigate/reload → 服务器自身页面）**：FBrowser 服务器事件循环单线程，同步等待期间无法服务自托管页面（MCP 服务自身 127.0.0.1:9222 的 docs/欢迎页等），wait_for_load 必然 20-30s 超时。新增 `是否本机自托管URL`/`URL主机端口匹配`（含端口边界校验防 9222 误匹配 92220），`应同步等待` 对目标/当前页为自托管 URL 时（含显式 sync_wait:true）自动降级为异步 task_id 轮询——load_end 后任务仍由事件驱动正常完成，实测 9ms 返回、mcp_result 秒级取到"等待条件满足: load_end"
- **渲染进程崩溃处置增强（实机 V8 OOM 崩溃验证）**：`浏览器_渲染意外终止` 新增 ①崩溃后立即将该浏览器上所有 `_waiting` 等待任务快速失败（原只能干等 max_ms 超时收到误导性"页面可能较慢"，实测 4 个等待任务均秒级收到"渲染进程崩溃"错误）②状态码语义化输出（0异常终止/1被杀死/2崩溃/3内存耗尽OOM）。`存储等待任务错误` 精确匹配浏览器ID（防误伤全局任务）。browser_event 的 crash 查询改为跨浏览器（崩溃浏览器已移出数组/重建后原按当前主浏览器ID过滤查不到历史崩溃记录）
- **关窗退出不再无限重启**：`浏览器_即将关闭` 原在最后一个窗口关闭时无条件标记重建 → 用户关掉 index 页窗口后新窗口立刻弹出、再关再弹、无限循环。修复：按关闭来源判别——用户手动关窗/browser_close（浏览器仍在数组中）→ 优雅退出整个 MCP 进程；崩溃清理路径（`渲染意外终止` 已先移出数组）→ 仍按崩溃恢复机制自动重建欢迎页。实测：browser_close 后进程约 1 秒内完整退出；Page.crash 后进程存活且 6 秒内重建新窗口

---

## [2.8.2] - 2026-08-14

### 新增（AI 交互增强 / v2.8.1 UX 批次）

- **5 个 AI 交互增强工具**（268 → 273）：`browser_snapshot`（页面交互元素快照，含文本/选择器/索引）、`browser_click_text`（按可见文本点击，模拟真实事件链）、`browser_get_forms`（表单字段枚举）、`browser_highlight`（元素高亮/自动清除）、`browser_fill_form`（一键批量填表，可自动提交）。全部走**内核执行JS代码_带返回值通道**（`框架.执行JS代码_带返回值` + JS回调 + sync-wait），非 CDP Runtime.evaluate 注入
- **browser_event 时间线模式**：event_type 为空时返回最近全部浏览器事件（跨类型、按时间倒序，limit 可调）；轻量事件监控（载入/生命周期/标题/框架/下载）**默认开启**，开箱即记录
- **运维指标**：`/health` 与 `mcp_status` 增加 tool_count / cdp_ready / db_stats（异步任务/事件日志/响应缓存行数）；新增 `取数据库统计JSON` 辅助
- **mcp_bridge.js --tools**：`node mcp_bridge.js --tools [关键字]` 列出全部工具名，支持过滤
- **mcp_help** 增加【AI交互-推荐】分类

### 修复（源码优化升级批次）

- **编译修复**：补回 `MCP_常量.同步等待_JS执行超时` 缺失定义；在 `MCP命令服务器` 上补回 11 个响应构建委托桩（`命令成功/命令失败/响应_需要刷新/命令成功_原始JSON/构建简单JSON/构建标准失败JSON/构建整数值JSON/构建Base64图片异步JSON/构建API元信息JSON/构建JSON版本响应/构建JSON列表响应`），修复 Form/Reverse/System/VIP/Workflow/Callbacks/HTTP 约 350 处调用点；依据发布版 generated-cpp 还原 `类_MCP_存在后填表回调`（8 种操作类型）
- **版本号**：`MCP_版本号` 2.6.1 → 2.8.0（与发布版 generated-cpp 及文档对齐，源码曾滞后于 Release）
- **数据安全**：缓存保留期改用墙钟时间（`取现行时间毫秒`），修复开机 14 天内每 60 秒清空全部日志/任务结果的严重数据丢失；"首次启动清理"改为仅在打开数据库时执行一次
- **锁修复**：`尝试同步跟随异步响应` 无主解锁破坏 MCP执行锁 → 新增 `需放锁等待` 参数按调用上下文区分；新增 `协议锁` 端到端串行化 JSON-RPC 请求，消除请求级静态上下文（追踪ID/紧凑模式）并发覆盖
- **并发正确性**：`待创建URL/待创建完成` 握手加锁（`待创建锁`）；`页面加载中/最新地址/当前页面标题` 跨线程读写改为加锁访问器；速率限制计数加锁；持久V8扩展列表加锁 + 存储侧管道符转义；CDP 映射时间戳改秒级存储防 32 位回绕
- **JSON-RPC 协议合规**：数字型 id 回退支持；通知（无 id）不再返回响应；直接 RPC 路由补全 batch/aliases/workflow_*/短名；initialize protocolVersion 按规范协商
- **下载修复**：`浏览器_可下载` 返回假会取消全部下载 → 返回真；`浏览器_即将下载` 对齐官方 demo（非自动保存分支调用 `继续("",真)`，返回假）
- **JS 安全**：`reverse_hook` xhr_fetch 模式串未转义（注入）→ 补 `简单转义JS`；`intercept navigate_redirect` 目标 URL 补安全校验；`验证URL安全` 补 \v\f 控制字符剥离与 file: 全量拦截
- **scrape 状态机**：phase 1 found 字段解析层级错误（wait_selector 永远超时）；phase 3 未检查 `_waiting` 占位与失败结果（垃圾结果提前完成）
- **其他**：canvas_noise remove 恢复原生 API（原 delete 原型永久破坏）；Workflow 任务 ID 提取 off-by-one 与死代码回退；URL 请求回调超限保留前缀+truncated 标记；Viewport 指纹宽高互换；CDP 断点 functionObjectId 参数名；存在后点击回调假成功；console_logs 数组特判；reverse_cdp_hook function_name 完整链路（两处处理器）

### 修复（对抗性验证批次）

- console_logs 数组特判拼接键名硬编码 network_logs → 改用键名变量（console_get 结果错挂键位）
- `类_MCP_存在后填表回调` 单引号 JS 字符串误用 JSON转义文本（不转义单引号）→ 7 处改 `简单转义JS`
- 限流拒绝响应缺 id 回显（客户端无法关联）→ 拒绝路径惰性解析请求 id；id:0 边缘注明按通知处理
- 执行关闭序列先置 `MCP正在关闭` 再停止 Stdio（原顺序退出冻结最长 10-15s）
- browser_create 超时路径改为比较-清除（协议锁下安全，防止"失败却创建"）
- 状态锁残留 2 处 `最新地址` 直写 → 改访问器
- 持久V8管道符转义补 `{PIPE_ESC_ESC}` 最长字面量保护（写入/读取镜像顺序，往返无损）
- **新增工具提交判定**：`提交异步JS任务` 成功返回 `{"_async":true,"task_id":...}` 包装 JSON 而非裸 taskID，5 个新工具/分支误以 `是否以(...,"task_")` 判定成功 → 全部误报主框架无效；改为 `是否以(...,"{\"error\"")` 失败判定 + 用自生成任务ID等待
### 新增（逆向定位/解密能力批次）

- **reverse_hook 扩展 3 类型**：`websocket`（消息send数据头Hook）、`eval_dynamic`（eval/Function构造器Hook，捕获动态生成/解密代码）、`cookie_set`（document.cookie setter Hook）——日志存 window.__MCP_*_LOG__
- **4 个逆向新工具**（272→276）：`browser_reverse_scan_crypto`（MD5/AES/SHA/自定义base64表/RSA 特征扫描）、`browser_reverse_string_refs`（密钥/常量引用定位：脚本/行号/上下文）、`browser_reverse_detect_obfuscator`（混淆器识别+置信度）、`browser_reverse_hook_logs`（Hook日志查询/清空）

### 新增（断点调试/CDP/Hook 逆向增强批次）

- **断点管理**：`browser_debugger_list_breakpoints`（列出全部已设断点+CDP断点ID）、`browser_debugger_clear_breakpoints`（逐个removeBreakpoint并清空）；`debugger_set_breakpoint` 改为同步等待CDP响应并记录断点注册表
- **CDP 自动就绪**：观察者未注册或附着其它浏览器时自动(重)注册；`browser_id` 参数支持多浏览器 CDP 操作（自动切换附着）
- **批量函数Hook**：`browser_reverse_hook_multi`（一次包装多个函数，支持obj.fn点路径，日志 __MCP_HOOK_LOG__）
- **调用栈快照**：`browser_reverse_stack_trace`（Error().stack 全量调用链，无需断点）
- **鸡肋清理**：禁用工具 browser_create_tab/browser_task_runner_post 从工具列表移除（分派保留友好错误）
- **滚动控制**：`browser_get_scroll`/`browser_scroll_by`（AI翻页采集闭环）

### 修复（全量审计批次: 3 P0 + 9 P1）

- **P0 事件驱动等待断链**：仓库源码缺失发布版已有的三处 `解析等待任务` 调用（load_end/navigate/load_start 事件）→ navigate/reload 默认等待必挂满 30 秒超时。已按 generated-cpp 还原三处接线 + 注册加载等待任务时补查"页面已加载完成"防事件先于注册竞态
- **P0 workflow_stop 不可打断**：workflow_run 持协议锁最长 30 分钟，stop 命令排队永远进不来 → 新增协议锁外快速通道（锁前惰性解析 method==workflow_stop 直接置停止标志）
- **P0 fill_form submit 条件反转**：错误分支误入等待白等 8 秒、成功反而报 failed → 补 `== 假`
- **P1**：shutdown 不再提前置 MCP正在关闭（响应存储不再被跳过）+ 延时钳制 60→3 秒；主循环节拍补消费 需要重建浏览器/需要恢复布局 标记（浏览器全崩后自动重建欢迎页）；定期维护双路径共享 上次维护毫秒 时间戳；window_topmost 改取逻辑值；监控默认开启方法化（配置文件缺失/为空分支也生效）；断点注册表关闭时清空（幽灵断点）；bridge --serve 声明移除；docs 死链替换

### 修复（三份审查报告批次: 新工具边界 + Core原有 + VIP/Stdio）

- **P0**：Reverse 分派链中被 `返回 ("")` 打断 → hook_multi/stack_trace 不可达(编译级)已删
- **高**：dom_select 误用勾选框 API → 改 `置元素选择项`（select_index 分支）；HAR 导出按行分割恒空 → 改数组解析；mouse_click VIP 路径 button 字符串映射缺失(右键变左键) → 补映射；navigate_redirect 自身重定向死循环 → 目标==重定向目标放行；Stdio 不解析 Content-Length 帧(每请求双帧/丢帧/父进程断开不退出) → 帧解析重写+残留保留+空读3次退出+写入循环写满；fill_form fields 真JSON数组回退；CDP 目标浏览器已关闭显式失败；断点空ID不登记；wait_for_load/include_links 布尔判定补 取逻辑
- **中**：batch 逗号按已追加数；MCP可中断延时检查工作流停止；js_env_ids 输出完整 ID 清单；vip_key_input 单字符截断；内核开关版本 116-135 校验；通知空 request_id 跳过存储；set_zoom 范围校验；wait max_ms 负数钳制

### 修复（最终清仓批次）

- intercept 事件Hook空壳诚实化：无 VIP 时明确提示"仅记录规则, 实际拦截需VIP授权"（3 处）
- workflow：delay_ms 上限 30 秒；步骤循环内每步检查 30 分钟超时（原实现仅下次运行时才重置）
- call_fn 支持 arguments 传参（文本成员规避 yyjson 嵌套崩溃）
- set_cookie 域名后缀匹配加点边界（xexample.com 不再匹配 example.com）
- key_event 未知 type 显式拒绝（原静默按单击）
- browser_list 不再持数组锁调用 8 秒等待的取安全主框架（改直接取主框架）
- schema 描述同步（wait_for_load 默认 true）；事件监控错误文案移除"框架"（实际默认关闭）

### 修复（工具覆盖审计批次）

- **发现 26 个工具只有注册/列表条目、分派实现缺失**（v2.8 源码回退的又一表现：fingerprint_languages/webgl_vendor/font_randomize + 23 个 reverse_* CDP 工具，发布版 generated-cpp 有实现、仓库源码没有）→ 已从工具列表移除（调用走"未知命令"诚实失败），待后续从 generated-cpp 还原实现
- 工具数修正：282 → **255**（全部有实现、可调用的真实工具数）

### 修复（运行时冲突批次）

- **反检测×断点调试冲突（渲染进程 illegal instruction 崩溃）**：`内核开关_禁用Debugger`（browser_reverse_setup disable_debugger 开启后浏览器创建时自动应用）与 CDP 断点工具根本冲突，debugger_flow 触发 V8 非法指令崩溃 → 新增 `确保Debugger可用` 自愈：debugger_flow/debugger_enable 入口自动恢复内核 Debugger 并复位持久标志（页面刷新后断点生效）

### 修复（编译调试批次）

- **全局方法重名**：火山规则=同包内全局类静态方法名必须唯一，委托桩方案（MCP命令服务器 与 MCP_响应构建 同名方法）违反该规则 → 删除 11 个委托桩，305 处调用点全部迁移为 `MCP_响应构建.*`（8 文件），9 处 `错误_无浏览器` 迁移至 `MCP_常量`
- **IDE 备份文件冲突**：`*.~vbak.wsv` 备份含同名全局类导致二次重名 → 已删除（编译前请清理）
- **常量补齐（与发布版对齐）**：`同步等待_即时毫秒`=1000、`同步等待_截图毫秒`=15000 缺失；`同步等待_JS执行超时` 15000→30000（发布版 generated-cpp 取证）
- **IsOSDirExist 未声明**：部分火山安装 win_base 头文件缺该声明（vol_functions.cpp 有实现）→ `目录是否存在` 三处调用改为 `MCP_服务器工具.检查目录是否存在`（内联 GetFileAttributesW 实现，环境自包含）
- size_t→整数 强转 2 处（C4267 警告清理）
- 编译+运行验证通过：272 工具（新增 5 工具全部注册），tools/list JSON 合法，snapshot/click_text(中文)/get_forms/highlight/fill_form/event时间线/mcp_status 全部实测正常

---

## [2.8.0] - 2026-06-28

### 新增

- **268 个 MCP 工具**（从 v2.6.1 的 243 增至 268）：43 个 CDP 逆向工具 + 7 反检测工具 + HAR 导出 + retry + workflow 条件变量 + resources/prompts 协议
- **mcp_bridge.js 全量工具模式**：移除 Cursor 白名单过滤限制，所有 268 工具动态展示

### 修复

- **browser_navigate / browser_reload `wait_for_load` 超时**：`注册加载等待任务` 缺少 `start_time` 导致 mcp_result 状态机立即判定超时（取启动时间() - 0 >= 30000 → true）。新增 `start_time` + `_event_driven` 标记，事件驱动任务由 `解析等待任务` 在 OnLoadEnd 回调中解析，避免轮询状态机假阳性

### 变更

- MCP 版本号 `MCP_版本号` → `"2.8.0"`
- 开源文档全量更新：版本号 2.6.x → 2.8.0，工具数 217/234/243 → 268

---

## [2.6.0] - 2026-06-21

### 新增

- **217 个 MCP 工具**：导航、填表、DOM、网络、工作流、CDP 调试等
- **双通道 JSON-RPC**：WebSocket + HTTP POST `/mcp`
- **sync-wait**：同步等待 DOM / 标题 / JS 结果
- **欢迎页控制台**：`http://127.0.0.1:9222/`
- **Cursor 桥接**：`mcp_bridge.js` stdio ↔ HTTP（自动修复 Cursor 协议版本 / JSON-RPC id / schema）
- **GitHub 开源**：`.wsv` 源码、`generated-cpp/` C++ 对照、完整文档与技能书
- **场景脚本**：`verify_cursor_tools.js`（Cursor 握手自检）、`baidu_search_params_analyze.js`

### 变更

- 同步 Release x64 编译产物至 `release/linker/`、`generated-cpp/release-x64/`
- 精简 MCP Stdio 模块；优化 Server/Core/Callbacks 分派与事件 Hook
- 移除冗余宣传/论坛文案文件（`FORUM_POSTS*`、`promo.*`、根目录 PDF/Word 等），保留 README 演示截图

### 发布包

| 文件 | 说明 |
|------|------|
| GitHub Release x64 | 运行成品 (exe + CEF，~157 MB) |
| GitHub Release win32 | 32 位运行成品 (exe + CEF，~136 MB) |
| GitHub Release cpp | 火山生成 C++ 对照（x64 / win32） |

### 说明

- 嵌入式 GUI 模式下 4 个窗口类工具（create/close/create_background/create_tab）已禁用
- **GitHub Release zip** 包含全部 217 个工具（截图、CDP、调试器、指纹、拦截等），解压即用

[2.6.0]: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
