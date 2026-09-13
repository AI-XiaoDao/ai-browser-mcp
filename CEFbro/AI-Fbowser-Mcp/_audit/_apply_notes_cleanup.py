# -*- coding: utf-8 -*-
"""按 _audit/_notes_cleanup_plan_r117.md 的判定表, 清理"操作备注"注释。

只做两类动作:
  del = 删行(纯过程叙述, 句内无可执行约束)
  rw  = 改写(叙述里含约束 -> 契约式, 保留数值/条件/后果)

安全性:
  * 每条都用**整行原文锚点**(含缩进)定位; 锚点在目标文件内命中数必须恰好 1,
    否则整批中止, 且**不写任何文件**。
  * 只写本判定表涉及的 8 个文件; 每个文件按自身编码/BOM/行尾原样写回,
    且只替换锚点覆盖的整行(全部是 `//` 注释行), 不碰任何代码行。
  * 写入前把原文件备份到 备份/备注清理-写入前/。
  * 断言: 每个文件改动后行数变化 == 该文件各条 delta 之和。
  * 任何异常打印 traceback 全文与相关片段。

用法:
  py -3 _audit/_apply_notes_cleanup.py --dry-run   # 只校验与预演, 不写文件
  py -3 _audit/_apply_notes_cleanup.py             # 实际写入
"""
import argparse
import os
import shutil
import sys
import traceback

ROOT = 'C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\CEFbro\\AI-Fbowser-Mcp'
SRC = os.path.join(ROOT, "src")
BACKUP_DIR = os.path.join(ROOT, "备份", "备注清理-写入前")

# (文件, [原文锚点(整行, 含缩进)], 处置, 依据, [改写后整行])
EDITS = [
    ('MCP_Callbacks.wsv',
     ['        // HTTP 层事实: 此前只回 success+body, **404 与 200 在回包里毫无区别**(实测缺口 G2)。\r'],
     'rw', "含 HTTP 层事实(只回 success+body 时 404 与 200 在回包里不可区分, 实测缺口 G2); 只剥掉 '此前' 这个时间对比口吻, 事实与缺口编号原样保留",
     ['        // HTTP 层事实: 只回 success+body 时 **404 与 200 在回包里毫无区别**(实测缺口 G2)。']),
    ('MCP_Kernel.wsv',
     ['        // 现按同族**已实测可用**的写法补上。两个易错点:'],
     'rw', "把'现按…补上'改成契约句",
     ['        // 契约: 按同族**已实测可用**的写法。两个易错点:']),
    ('MCP_Kernel.wsv',
     ['        //   ② 早前此处的尝试被回退, 归因是"该上下文不能调 查询事件日志"; 真因更可能是 查询事件日志 当时'],
     'rw', "把'早前此处的尝试被回退, 归因是…'改成排查警告, 保留真正的根因(缺 DB 可用性守卫)",
     ['        //   ② 若此处调用失败, 不要归因"该上下文不能调 查询事件日志"; 真因更可能是 查询事件日志 当时']),
    ('MCP_Server.wsv',
     ['        // v1.6 新增'],
     'del', "整行只有版本号与'新增'二字, 无可执行约束、无功能信息; 该行只是给下面一组命令贴时间标签",
     []),
    ('MCP_Server.wsv',
     ['        // JS逆向工具 (v2.8.0)'],
     'rw', '命令注册表分组标签; 版本号属开发过程, 分组名属结构信息',
     ['        // JS逆向工具']),
    ('MCP_Server.wsv',
     ['        // CDP逆向增强 (v2.6.2)'],
     'rw', '同上(注册表分组标签)',
     ['        // CDP逆向增强']),
    ('MCP_Server.wsv',
     ['        // 静态加密模块提取 (v2.6.3)'],
     'rw', '同上(注册表分组标签)',
     ['        // 静态加密模块提取']),
    ('MCP_Server.wsv',
     ['        命令注册表.置整数值 ("reverse_extract", 1319)',
      '        // v2.8 反检测预设 + 逆向增强'],
     'rw', '同上(注册表分组标签)',
     ['        命令注册表.置整数值 ("reverse_extract", 1319)',
      '        // 反检测预设 + 逆向工具']),
    ('MCP_Server.wsv',
     ['        // v2.8 网络导出 + 权限伪装 (使用注册命令双变体辅助方法)'],
     'rw', '同上(注册表分组标签)',
     ['        // 网络导出 + 权限伪装 (使用注册命令双变体辅助方法)']),
    ('MCP_Server.wsv',
     ['        // v2.8 自动化重试 + Canvas噪声'],
     'rw', '同上(注册表分组标签)',
     ['        // 自动化重试 + Canvas噪声']),
    ('MCP_Server.wsv',
     ['        注册命令双变体 ("canvas_noise", 1325)',
      '        // v2.8 逆向热补丁 + 字体随机化'],
     'rw', '同上(注册表分组标签)',
     ['        注册命令双变体 ("canvas_noise", 1325)',
      '        // 逆向热补丁 + 字体随机化']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强 R5: Debugger/Runtime/DOMDebugger/Network 未暴露API'],
     'rw', '同上(注册表分组标签), 去掉 v2.8 与 R5 两个轮次标签',
     ['        // CDP逆向: Debugger/Runtime/DOMDebugger/Network 未暴露API']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强 R6: Runtime.compileScript/Profiler.preciseCoverage/Page.setBypassCSP等'],
     'rw', '同上',
     ['        // CDP逆向: Runtime.compileScript/Profiler.preciseCoverage/Page.setBypassCSP等']),
    ('MCP_Server.wsv',
     ['        // v2.8 R7: Storage.getCookies / Network.emulateNetworkConditions / DOM.resolveNode / Emulation.setFocusEmulation / WebGL vendor'],
     'rw', '同上',
     ['        // CDP逆向: Storage.getCookies / Network.emulateNetworkConditions / DOM.resolveNode / Emulation.setFocusEmulation / WebGL vendor']),
    ('MCP_Server.wsv',
     ['        // v2.8 R8: Input.dispatchMouseEvent/KeyEvent / Tracing.start/end / Runtime.evaluate(silent+userGesture)'],
     'rw', '同上',
     ['        // CDP逆向: Input.dispatchMouseEvent/KeyEvent / Tracing.start/end / Runtime.evaluate(silent+userGesture)']),
    ('MCP_Server.wsv',
     ['        // v2.8 R9: navigator.languages / CSS.startRuleUsageTracking / LayerTree'],
     'rw', '同上',
     ['        // CDP逆向: navigator.languages / CSS.startRuleUsageTracking / LayerTree']),
    ('MCP_Server.wsv',
     ['        // v2.8.2 V8级Hook与插装 (新增3项; blackbox/async_stack/breakpoints_active/skip_pauses/',
      '        //               precise_coverage/patch/search_script 已在上方预留号, 本次补上实现)'],
     'rw', "两行都是'哪一批号、第几次补上'的批次记叙; 按本组实际登记的命令重写为内容标签",
     ['        // V8级Hook与插装: reverse_instrument_script / reverse_return_value / reverse_set_variable /',
      '        //   reverse_pause_on_exceptions / reverse_get_possible_breakpoints / reverse_add_binding']),
    ('MCP_Server.wsv',
     ['        // v2.8.1 UX: AI 交互增强 (快照/文本点击/表单枚举/高亮/批量填表)'],
     'rw', '注册表分组标签',
     ['        // AI 交互增强: 快照/文本点击/表单枚举/高亮/批量填表']),
    ('MCP_Server.wsv',
     ['        // v2.8.1 R: 逆向定位/解密能力'],
     'rw', '注册表分组标签',
     ['        // 逆向定位/解密能力']),
    ('MCP_Server.wsv',
     ['        // VIP补充: 短名别名 (让 refresh_cookies/get_all_cookies/set_preference 可用)'],
     'rw', "分组标签+含'让 xxx 可用'的语义说明; 保留说明, 去掉'补充'变更口吻",
     ['        // VIP 短名别名: 让 refresh_cookies/get_all_cookies/set_preference 可用']),
    ('MCP_Server.wsv',
     ['                // 修复: null/空成员显式计失败并写入结果, 保证 total == success_count + failure_count'],
     'rw', "叙述里含可执行约束(total == success_count + failure_count); 只剥掉'修复:'",
     ['                // null/空成员显式计失败并写入结果, 保证 total == success_count + failure_count']),
    ('MCP_Server.wsv',
     ['                // ★ 依据(本轮实测, 含应用自身日志): 观察者是**单个**全局对象, 切到另一个浏览器再切回来,'],
     'rw', "块内唯一实测证据(CDP观察者只在未注册时注册)。保留事实与数值, 只去掉'本轮'这个相对时间标签",
     ['                // ★ 依据(实测, 含应用自身日志): 观察者是**单个**全局对象, 切到另一个浏览器再切回来,']),
    ('MCP_Server.wsv',
     ['                // 修复: 观察者确实不在册时**快速失败**, 不再发出一条注定收不到响应的 CDP 命令'],
     'rw', '叙述里含契约(观察者不在册时必须快速失败、不得发注定无响应的命令); 改为契约句',
     ['                // 契约: 观察者确实不在册时**快速失败**, 不再发出一条注定收不到响应的 CDP 命令']),
    ('MCP_Server.wsv',
     ['        //    实测教训(第一次实现踩到): 只靠 执行CDP并同步等待 的**反应式**补域是不够的 ——',
      '        //    那次 pause 请求被接受, 但 5 秒内始终等不到 Debugger.paused, 直到**下一次**工具调用',
      '        //    才发现页面其实已经暂停(即本次 pause 白做、下次才生效)。原因是启用调试器域会重置',
      '        //    "下一语句暂停"标志: 先 pause 后 enable == pause 被清掉。故这里主动、显式地先 enable。'],
     'rw', "块内是'第一次实现踩到'的过程叙述, 但结论(先 pause 后 enable 会清掉暂停标志)是内核约束, 必须保留",
     ['        //    实测约束: 只靠 执行CDP并同步等待 的**反应式**补域是不够的 ——',
      '        //    先 pause 后 enable 时, pause 请求虽被接受, 但 5 秒内始终等不到 Debugger.paused, 直到**下一次**工具调用',
      '        //    才发现页面其实已经暂停(即该次 pause 被清掉、下次才生效):',
      '        //    "下一语句暂停"标志 —— 先 pause 后 enable 即被清掉。故这里主动、显式地先 enable。']),
    ('MCP_Server.wsv',
     ['            // 清掉可能残留的旧暂停事件, 否则会把上一次的暂停误当成本次制造出来的'],
     'rw', "含顺序契约(必须先清旧暂停事件); '本次'是运行期序数, 但句首暗示了先后实现的对比, 一并中性化",
     ['            // 清掉可能残留的旧暂停事件, 否则会把上一次的暂停误当成新制造出来的那一次']),
    ('MCP_Server.wsv',
     ['        // 修复: 反检测三字段同样纳入锁快照 (持久反检测_伪装UA 为CVolString, 与代理地址同模式的跨线程堆损坏风险)'],
     'rw', "含跨线程堆损坏风险这一硬约束; 只去掉'修复:'",
     ['        // 反检测三字段同样纳入锁快照 (持久反检测_伪装UA 为CVolString, 与代理地址同模式的跨线程堆损坏风险)']),
    ('MCP_Server.wsv',
     ['        // v2.6.2: 反检测预配置 — 浏览器创建时自动应用, 无需逐命令'],
     'rw', '配置说明; 去掉版本号',
     ['        // 反检测预配置: 浏览器创建时自动应用, 无需逐命令']),
    ('MCP_Server.wsv',
     ['        // v2.8.2 例外: Debugger.scriptParsed 每脚本只上报一次, 但单槽缓存只留最后一条,'],
     'rw', '说明 scriptParsed 单槽缓存为何不够; 去掉版本号',
     ['        // 例外: Debugger.scriptParsed 每脚本只上报一次, 但单槽缓存只留最后一条,']),
    ('MCP_Server.wsv',
     ['        // v2.8.2: 导航后旧文档的 scriptId 全部失效(检索会报 "No script for id"),'],
     'rw', '说明清表原因(导航后 scriptId 失效); 去掉版本号',
     ['        // 导航后旧文档的 scriptId 全部失效(检索会报 "No script for id"),']),
    ('MCP_Server.wsv',
     ['        // 修复: 改yyjson解析, 正确处理转义引号/冒号后空白 (原手写定位遇CDP事件含转义会截断错位)'],
     'rw', '含契约(必须用 yyjson 解析, 否则含转义会截断错位); 改为无时间性的说明',
     ['        // 用 yyjson 解析: 正确处理转义引号/冒号后空白 (手写定位遇 CDP 事件含转义会截断错位)']),
    ('MCP_Server.wsv',
     ['        //   实测(第 72 轮): 目标是第二个浏览器时, execute_js 白等 30 秒、get_text 白等 10 秒, 而且'],
     'rw', "块内唯一实测证据(第二个浏览器上白等 30s/10s); 只去掉'第 72 轮'这个轮次标签",
     ['        //   实测: 目标是第二个浏览器时, execute_js 白等 30 秒、get_text 白等 10 秒, 而且']),
    ('MCP_Server.wsv',
     ['        // ── v2.8.3 核心: 隐式前置自动补齐 ──'],
     'rw', '段标题; 去掉版本号',
     ['        // ── 隐式前置自动补齐 ──']),
    ('MCP_Server.wsv',
     ['                // 这是"明明没做错却连续失败、只能反复换方法试"的头号成因(实测: 一次断点命中未恢复后,',
      '                // execute_js / debugger_enable / 连 browser_status 都开始超时)。'],
     'rw', "含因果契约(断点未恢复会让之后每个工具都超时); 去掉'反复换方法'的抱怨口吻",
     ['                // 成因(实测): 一次断点命中未恢复后,',
      '                // execute_js / debugger_enable / 连 browser_status 都开始超时。']),
    ('MCP_Server.wsv',
     ['            // ★ 修(可诊断性, 实测): CDP 的 exceptionDetails.text **固定就是 "Uncaught"** ——'],
     'rw', "块内唯一实测结论(CDP exceptionDetails.text 固定为 Uncaught); 去掉'修(...)'的过程框",
     ['            // ★ 实测约束(可诊断性): CDP 的 exceptionDetails.text **固定就是 "Uncaught"** ——']),
    ('MCP_Server.wsv',
     ['            //   原实现优先读 text, 于是**所有**走这条路径的 JS 异常都只报 "JS异常:Uncaught",'],
     'rw', "把'原实现'改成条件式, 事实(只报 Uncaught)与后果都保留",
     ['            //   若优先读 text, 则**所有**走这条路径的 JS 异常都只报 "JS异常:Uncaught",']),
    ('MCP_Server.wsv',
     ['                // 现在先试原生同步 JS(实测该路径在 CDP 失效时仍可用), 拿到有效值就用它。'],
     'rw', "含实测依据(原生同步JS在 CDP 失效时仍可用); 去掉'现在'的变更口吻",
     ['                // 故先试原生同步 JS(实测该路径在 CDP 失效时仍可用), 拿到有效值就用它。']),
    ('MCP_Server.wsv',
     ['            // ★ 修(失败原因被吞): 原来只读包装里的 "message" —— 但写入失败原因的是 处理CDP响应,'],
     'rw', "含硬事实(处理CDP响应写的是 error/result, 从来没有 message); 去掉'原来…但'的更正口吻",
     ['            // ★ 关键(失败原因会被吞): 包装里只有 "message", 但写入失败原因的是 处理CDP响应,']),
    ('MCP_Server.wsv',
     ['        // 排查代价极高(曾据此误判为"某工具把响应写坏了")。故补上守卫。'],
     'rw', "含必须补守卫的因果链(DB 未就绪 -> 请求线程异常终止 -> 200+空体); 去掉'曾据此误判/故补上'的过程口吻",
     ['        // 缺此守卫时, DB 未就绪会让请求线程异常终止, 且现象极易被误判为"某工具把响应写坏了"。']),
    ('MCP_Server.wsv',
     ['            // (实测: urlreq_start 记录成功但 browser_event 查不到)。此前只有 crash 在调用侧特判,',
      '            // 现推广为通则。'],
     'rw', "含契约(无浏览器上下文的事件必须按通则查询); 把'此前只有 crash 特判/现推广'的过程叙述压成通则句",
     ['            // (实测: urlreq_start 记录成功但 browser_event 查不到)。此处按通则处理, 不再为单个事件特判。']),
    ('MCP_Server.wsv',
     ['        // v2.7: 预存pending占位 — 即使CEF回调因页面导航丢失, 任务也不会"消失"'],
     'rw', '含契约(pending 占位保证任务不消失); 去掉版本号',
     ['        // 预存 pending 占位: 即使 CEF 回调因页面导航丢失, 任务也不会"消失"']),
    ('MCP_Server.wsv',
     ['            // 修复: 原用 取文本 比较文本"false"/"0", 布尔节点取文本为空导致 wait_for_load:false 仍同步等待'],
     'rw', "含参数语义约束(wait_for_load 必须按布尔语义判定); 去掉'原用…导致'的更正口吻",
     ['            // wait_for_load 判定用布尔语义(不做文本比较): 布尔节点取文本为空, 按文本比较 "false"/"0" 会让 false 仍同步等待']),
    ('MCP_Server.wsv',
     ['        // browser_scrape 在第100轮曾因"同步后回空串"被撤回; 其根因(转换器不读工具专属键)已修,',
      '        // 且 取工具结果键名 已为它补上 text 映射, 故本轮重新纳入。'],
     'rw', "块内是'曾因…被撤回/已修/故本轮重新纳入'的完整过程记叙; 但结论(可纳入同步名单)有依据, 压缩为一句依据",
     ['        // browser_scrape 纳入同步的依据: 转换器按 取工具结果键名 读工具专属键 text, 不会再回空串。']),
    ('MCP_Server.wsv',
     ['        // 修复(探测发现): 原将 dom_query/dom_get_html 的 "null" 值判定为失败——'],
     'rw', "含语义约束(null 值不等于查询失败); 去掉'修复(探测发现): 原将…判定为失败'的更正框",
     ['        // 约束: dom_query/dom_get_html 的 "null" 值**不判失败** ——']),
    ('MCP_Server.wsv',
     ['            // 修复(参数类型容错): 底层 取整数 只认 JSON 数值节点 —— 文本节点("100")与布尔节点'],
     'rw', "含类型容错约束; 去掉'修复(参数类型容错):'的变更框",
     ['            // 参数类型容错: 底层 取整数 只认 JSON 数值节点 —— 文本节点("100")与布尔节点']),
    ('MCP_Server.wsv',
     ['            // 修复(同 yyjson取整数): 文本/布尔节点归一化, 否则 "1.5" 会读成 0。'],
     'rw', '含边界约束(否则 "1.5" 读成 0); 去掉\'修复(同…)\':',
     ['            // 文本/布尔节点归一化, 否则 "1.5" 会读成 0。']),
    ('MCP_Server.wsv',
     ['            // 修复(同 yyjson取整数): 文本/布尔节点归一化'],
     'rw', "同上, 更短的一条; 去掉'修复(同…):'",
     ['            // 文本/布尔节点归一化']),
    ('MCP_Server.wsv',
     ['        //   修在这里(而不是逐个调用点)是因为 9 个调用点都会受益, 且不会再有新调用点踩坑。'],
     'rw', "说明判据为何收在读取器里; 去掉'修在这里'的过程口吻",
     ['        //   判据收在读取器里: 9 个调用点统一受益, 新增调用点不必各自处理。']),
    ('MCP_Server.wsv',
     ['            // v2.8.1 体验优化: 框架未就绪时最多等待8秒(可中断轮询), 覆盖慢页面加载,'],
     'rw', '体验参数说明(8秒上限、可中断); 去掉版本号',
     ['            // 框架未就绪时最多等待8秒(可中断轮询), 覆盖慢页面加载,']),
    ('MCP_Server.wsv',
     ['                // 修复: 本方法可能在**未持有 MCP执行锁**的路径上被调用'],
     'rw', "含加锁约束; 去掉'修复:'",
     ['                // 本方法可能在**未持有 MCP执行锁**的路径上被调用']),
    ('MCP_Server.wsv',
     ['        // 修复(HTTP不启动): 原实现在 --mcp-stdio/--stdio/--headless 下完全跳过'],
     'rw', '含启动约束(stdio/headless 下也必须尝试建服务器); 改为约束句',
     ['        // 约束(HTTP不启动): 即使在 --mcp-stdio/--stdio/--headless 下也不能跳过']),
    ('MCP_Server.wsv',
     ['        // 调用处根本无法判断成败, 所以原实现只能"一刀切跳过"。'],
     'rw', "含'不能一刀切跳过'的结论; 去掉'原实现只能'",
     ['        // 调用处无从判断成败 —— 这正是不能"一刀切跳过"的原因。']),
    ('MCP_Server.wsv',
     ['        // === 构建命令注册表 (字典预查找优化) ==='],
     'rw', "段标题; '优化'是变更口吻, 改为手法本身",
     ['        // === 构建命令注册表 (字典预查找) ===']),
    ('MCP_Server.wsv',
     ['        // 崩溃计数复位: 浏览器存活且计数未达阈值时, 窗口随维护周期滚动 (修复: 原子写, 与UI线程崩溃计数竞争)'],
     'rw', "含并发约束(必须原子写); 去掉括号里的'修复:'",
     ['        // 崩溃计数复位: 浏览器存活且计数未达阈值时, 窗口随维护周期滚动 (原子写, 与UI线程崩溃计数竞争)']),
    ('MCP_Server.wsv',
     ['        // 修复: 原守卫用 MCP正在关闭 早退, 但关闭序列(main.wsv)先置位该标志再调本方法,'],
     'rw', "含关闭序列约束(不能用 MCP正在关闭 早退); 把'原守卫…导致'改成前置警告",
     ['        // 注意: 不能用 MCP正在关闭 早退 —— 关闭序列(main.wsv)先置位该标志再调本方法,']),
    ('MCP_Server.wsv',
     ['        // 修复(真机验证发现): 指标_进度通知数 此前只声明与自增, 却未导出到 Prometheus 文本,'],
     'rw', "含可观测性约束(必须导出到 Prometheus); 去掉'修复(真机验证发现): …此前'",
     ['        // 指标_进度通知数 必须导出到 Prometheus 文本, 否则 notifications/progress 推送完全不可观测,']),
    ('MCP_Server.wsv',
     ['        // 修复(标准): 提前提取请求ID(文本/数字), 后续错误响应统一回显真实id'],
     'rw', "含 JSON-RPC 契约(错误响应要回显真实 id); 去掉'修复(标准):'",
     ['        // 提前提取请求ID(文本/数字), 后续错误响应统一回显真实id']),
    ('MCP_Server.wsv',
     ['        // v2.8.1: 补全路由, batch/aliases/workflow_*/短名(如 get_url) 作为顶层方法调用不再落入 -32601'],
     'rw', '路由覆盖说明; 去掉版本号',
     ['        // 路由覆盖: batch/aliases/workflow_*/短名(如 get_url) 作为顶层方法调用不落入 -32601']),
    ('MCP_Server.wsv',
     ['        // v2.8: 声明 resources + prompts 能力'],
     'rw', '能力声明; 去掉版本号',
     ['        // 声明 resources + prompts 能力']),
    ('MCP_Server.wsv',
     ['        // v1.6'],
     'del', "整行只有版本号 'v1.6', 连'新增'都没有; 不含任何约束或语义",
     []),
    ('MCP_Server.wsv',
     ['        // ======== 能力补齐: 以下 14 个工具在源码中早已完整实现(分派分支齐全),'],
     'rw', "含事实(14 个工具早已实现但未登记); 把'能力补齐'这个变更口吻改成'补登记'",
     ['        // ======== 补登记工具: 以下 14 个工具在源码中已完整实现(分派分支齐全),']),
    ('MCP_Server.wsv',
     ['        // v1.8 CDP结果回传'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        // CDP结果回传']),
    ('MCP_Server.wsv',
     ['        // v1.7 VIP指纹补充'],
     'rw', "注册表分组标签; 去掉版本号与'补充'变更口吻",
     ['        // VIP 指纹工具']),
    ('MCP_Server.wsv',
     ['        // v1.7 VIP扩展插件'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        // VIP 插件管理']),
    ('MCP_Server.wsv',
     ['        // v2.8.0 JS逆向工具'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        // JS逆向工具']),
    ('MCP_Server.wsv',
     ['        // v2.6.2 JS逆向增强工具'],
     'rw', "注册表分组标签; '增强'是变更口吻, 改为本组内容清单",
     ['        // JS逆向: 归因/环境/插桩/搜索/溯源/预设']),
    ('MCP_Server.wsv',
     ['        // v2.6.2 CDP逆向增强 (原生CDP协议,非JS注入)'],
     'rw', '注册表分组标签',
     ['        // CDP逆向: 原生CDP协议, 非JS注入']),
    ('MCP_Server.wsv',
     ['        // v2.6.3 静态加密模块提取'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        // 静态加密模块提取']),
    ('MCP_Server.wsv',
     ['        添加工具JSON ("browser_reverse_extract", "JS逆向: 静态加密模块提取(CDP Runtime.evaluate同步)。mode=scan枚举页面<script>标签返回脚本列表+加密特征检测; mode=download按DOM索引取脚本textContent完整源码; mode=analyze按url_pattern一次扫描+源码分析提取算法(AES/RSA/MD5/SHA/HMAC)和可疑密钥常量", 多属性Schema文本 (属性项JSON ("mode", "text", "scan(默认)/download/analyze") + "," + 属性项JSON ("url_pattern", "text", "URL片段(analyze模式必填, 匹配脚本src)") + "," + 属性项JSON ("script_index", "text", "DOM脚本索引(download模式必填, 取自scan返回的index)") + "," + 属性项JSON ("keyword", "text", "关键词(scan模式可选, 过滤含关键词的脚本)"), ""))',
      '        // v2.8 反检测预设 + 逆向增强'],
     'rw', '注册表分组标签',
     ['        添加工具JSON ("browser_reverse_extract", "JS逆向: 静态加密模块提取(CDP Runtime.evaluate同步)。mode=scan枚举页面<script>标签返回脚本列表+加密特征检测; mode=download按DOM索引取脚本textContent完整源码; mode=analyze按url_pattern一次扫描+源码分析提取算法(AES/RSA/MD5/SHA/HMAC)和可疑密钥常量", 多属性Schema文本 (属性项JSON ("mode", "text", "scan(默认)/download/analyze") + "," + 属性项JSON ("url_pattern", "text", "URL片段(analyze模式必填, 匹配脚本src)") + "," + 属性项JSON ("script_index", "text", "DOM脚本索引(download模式必填, 取自scan返回的index)") + "," + 属性项JSON ("keyword", "text", "关键词(scan模式可选, 过滤含关键词的脚本)"), ""))',
      '        // 反检测预设 + 逆向工具']),
    ('MCP_Server.wsv',
     ['        // v2.8 网络导出 + 权限伪装'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        // 网络导出 + 权限伪装']),
    ('MCP_Server.wsv',
     ['        // v2.8 自动化重试 + Canvas噪声 (v2.8)'],
     'rw', '注册表分组标签; 去掉重复出现的版本号',
     ['        // 自动化重试 + Canvas噪声']),
    ('MCP_Server.wsv',
     ['        添加工具JSON ("browser_canvas_noise", "反检测: Canvas指纹噪点注入(JS层实现,不需VIP)。action=inject为Canvas toDataURL/toBlob/getImageData添加±level随机噪声,防Canvas指纹追踪; action=remove移除噪声。不依赖内核VIP API,纯JS Hook", 多属性Schema文本 (属性项JSON ("action", "text", "inject(默认)/enable/remove/disable") + "," + 属性项JSON ("level", "integer", "噪声级别1-5(默认1, 越大噪声越明显)"), ""))',
      '        // v2.8 逆向热补丁 + 字体随机化'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        添加工具JSON ("browser_canvas_noise", "反检测: Canvas指纹噪点注入(JS层实现,不需VIP)。action=inject为Canvas toDataURL/toBlob/getImageData添加±level随机噪声,防Canvas指纹追踪; action=remove移除噪声。不依赖内核VIP API,纯JS Hook", 多属性Schema文本 (属性项JSON ("action", "text", "inject(默认)/enable/remove/disable") + "," + 属性项JSON ("level", "integer", "噪声级别1-5(默认1, 越大噪声越明显)"), ""))',
      '        // 逆向热补丁 + 字体随机化']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强: 6个官方API封装'],
     'rw', '注册表分组标签',
     ['        // CDP逆向: 6个官方API封装']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强 R6: Runtime/Profiler/Page/Debugger 深度API'],
     'rw', '注册表分组标签',
     ['        // CDP逆向: Runtime/Profiler/Page/Debugger 深度API']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强 R7: Storage/Network/DOM/Emulation + VIP WebGL vendor'],
     'rw', '注册表分组标签',
     ['        // CDP逆向: Storage/Network/DOM/Emulation + VIP WebGL vendor']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强 R8: Input/Tracing/Runtime 收尾'],
     'rw', "注册表分组标签; 去掉'收尾'这个批次口吻",
     ['        // CDP逆向: Input/Tracing/Runtime']),
    ('MCP_Server.wsv',
     ['        // v2.8 CDP逆向增强 R9: fingerprint_languages + CSS/LayerTree 收尾'],
     'rw', "注册表分组标签; 去掉'收尾'",
     ['        // CDP逆向: fingerprint_languages + CSS/LayerTree']),
    ('MCP_Server.wsv',
     ['        // v1.8 浏览器事件查询'],
     'rw', '注册表分组标签; 去掉版本号',
     ['        // 浏览器事件查询']),
    ('MCP_Server.wsv',
     ['        // v2.8.1 UX2: 滚动控制 (AI翻页采集核心)'],
     'rw', '注册表分组标签; 去掉版本号与 UX2 批次号',
     ['        // 滚动控制 (AI翻页采集核心)']),
    ('MCP_Server.wsv',
     ['        // v2.8.1 DBG: 断点管理 + 批量Hook + 调用栈'],
     'rw', '注册表分组标签; 去掉版本号与 DBG 批次号',
     ['        // 断点管理 + 批量Hook + 调用栈']),
    ('MCP_Server.wsv',
     ['        // v2.8.1 UX3: 快照索引闭环'],
     'rw', '注册表分组标签; 去掉版本号与 UX3 批次号',
     ['        // 快照索引闭环']),
    ('MCP_Server.wsv',
     ['        // v1.7 新增'],
     'del', "整行只有'v1.7 新增', 上面两行已分别是 'CDP调试 (VIP)' 与 '网络抓包' 两个分组名; 本行本身不含任何信息",
     []),
    ('MCP_Server_Core.wsv',
     ['                // ★ 修(正确性+副作用安全, 实测): CDP 已**明确**报出"用户 JS 抛异常"时, 该结论是终局的。'],
     'rw', "含终局判据契约(CDP 明确报出用户 JS 抛异常时结论终局); 把'修(...)'换成'契约(...)'",
     ['                // ★ 契约(正确性+副作用安全, 实测): CDP 已**明确**报出"用户 JS 抛异常"时, 该结论是终局的。']),
    ('MCP_Server_Core.wsv',
     ['                //   原来它与"CDP 通道不可用"共用同一条判据(只要以 {"error" 开头就继续往下走原生回退),'],
     'rw', "把'原来它与…共用同一条判据'改成条件式, 保留副作用跑两遍的后果",
     ['                //   若与"CDP 通道不可用"共用同一条判据(只要以 {"error" 开头就继续往下走原生回退),']),
    ('MCP_Server_Core.wsv',
     ['                    // 这补上了"CDP 通道没附着到目标浏览器"时的取值能力 —— 实测第二个浏览器上'],
     'rw', "含能力说明与实测依据; 去掉'这补上了'的过程口吻",
     ['                    // 覆盖"CDP 通道没附着到目标浏览器"时的取值 —— 实测第二个浏览器上']),
    ('MCP_Server_Core.wsv',
     ['                    // 为什么必须换掉原来的"填表框架 取元素内容": 实测(第 73 轮)对**第二个浏览器**,'],
     'rw', "把'为什么必须换掉原来的 X'改成'为什么不用 X'; 实测事实与轮次标签处理",
     ['                    // 为什么不用"填表框架 取元素内容": 实测对**第二个浏览器**,']),
    ('MCP_Server_Core.wsv',
     ['                        // 第一版漏了这一项, 实测外层只等了 0ms 就报"等待超时(0ms)" —— 与 browser_execute_js'],
     'rw', "含契约(占位必须带 max_ms); 去掉'第一版漏了这一项'",
     ['                        // 漏写这一项时外层只等 0ms 就报"等待超时(0ms)" —— 必须与 browser_execute_js']),
    ('MCP_Server_Core.wsv',
     ['                        // 工具侧没有机会去掉前缀 —— 实测第一版就把 `__MCP_TEXT__Example Domain` 原样漏给了用户'],
     'rw', "含硬约束(内部哨兵绝不能出现在面向用户的返回里); 去掉'第一版'",
     ['                        // 工具侧没有机会去掉前缀(已见: `__MCP_TEXT__Example Domain` 会原样漏给用户)']),
    ('MCP_Server_Core.wsv',
     ['            // FBrowser_创建后台浏览器 —— 与 main.wsv 里既有的 `__SHUTDOWN__` 前缀同一惯例, 无需新增握手字段。'],
     'rw', "含握手约定; 去掉'新增'变更口吻",
     ['            // FBrowser_创建后台浏览器 —— 与 main.wsv 里 `__SHUTDOWN__` 前缀同一惯例, 无需额外握手字段。']),
    ('MCP_Server_Core.wsv',
     ['                    // 实测(第 71 轮, 三臂对照): 创建与使用第二个浏览器**不再影响主浏览器的 CDP 通道**'],
     'rw', "块内唯一实测证据(三臂对照); 去掉'第 71 轮'",
     ['                    // 实测(三臂对照): 创建与使用第二个浏览器**不影响主浏览器的 CDP 通道**']),
    ('MCP_Server_Core.wsv',
     ['                    // 实测(第 72-73 轮): 目标隔离正确、不影响主浏览器 CDP 工具、且在第二个浏览器上读取也正常'],
     'rw', '块内唯一实测证据(第 72-73 轮结论); 去掉轮次标签',
     ['                    // 实测: 目标隔离正确、不影响主浏览器 CDP 工具、且在第二个浏览器上读取也正常']),
    ('MCP_Server_Core.wsv',
     ['        // === 自动化重试机制 (v2.8) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 自动化重试机制 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === Canvas指纹噪点注入 (v2.8 反检测, JS实现, 不需VIP) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === Canvas指纹噪点注入 (反检测, JS实现, 不需VIP) ===']),
    ('MCP_Server_Core.wsv',
     ['        // === 网络日志 HAR 导出 (v2.8) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 网络日志 HAR 导出 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === 权限API伪装 (v2.8 反检测) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 权限API伪装 (反检测) ===']),
    ('MCP_Server_Core.wsv',
     ['            // === v2.2 浏览器事件监控 ==='],
     'rw', '段标题; 去掉版本号',
     ['            // === 浏览器事件监控 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v1.8 浏览器事件查询 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 浏览器事件查询 ===']),
    ('MCP_Server_Core.wsv',
     ['                //   不是错误。原来报失败会让调用方(尤其 AI)以为需要"先制造暂停再恢复" -> 无意义的多步调用,'],
     'rw', "把'原来报失败会让…'改成条件式, 契约(不得谎报做过事)由下一行承担",
     ['                //   不是错误。若报失败会让调用方(尤其 AI)以为需要"先制造暂停再恢复" -> 无意义的多步调用,']),
    ('MCP_Server_Core.wsv',
     ['        // === 断点管理 (v2.8.1 新增) ==='],
     'rw', "段标题; 去掉版本号与'新增'",
     ['        // === 断点管理 ===']),
    ('MCP_Server_Core.wsv',
     ['            // 修: 原实现把**工具自身的 MCP 参数**原样当 CDP 参数发给 Debugger.getStackTrace, 而 CDP 该方法'],
     'rw', "含 CDP 参数语义(要的是 error 对象上的 stackTraceId, 不是当前暂停栈); 把'原实现把…'改成参数语义陈述",
     ['            // 参数语义: Debugger.getStackTrace 要的不是**工具自身的 MCP 参数** —— CDP 该方法']),
    ('MCP_Server_Core.wsv',
     ['                //   原实现在缺帧 ID 时直接失败("call_frame_id和expression 参数不能为空"),'],
     'rw', "把'原实现在缺帧ID时直接失败'改成前置约束",
     ['                //   缺帧 ID 时不能直接失败("call_frame_id和expression 参数不能为空"):']),
    ('MCP_Server_Core.wsv',
     ['            // 故改回直接调用 —— 同一逻辑只保留一份实现, 不给后来人留两个真相。'],
     'rw', "含契约(同一逻辑只保留一份实现); 去掉'改回'",
     ['            // 故直接调用读取器 —— 同一逻辑只保留一份实现, 不留两个真相。']),
    ('MCP_Server_Core.wsv',
     ['                // ASCII "qw==" 的十六进制(71773d3d), 而不是解码后单字节 0xAB 的 "ab" —— 属实测缺陷。'],
     'rw', "含契约(必须按 input 取字节); 把'属实测缺陷'改成结论句",
     ['                // ASCII "qw==" 的十六进制(71773d3d), 而不是解码后单字节 0xAB 的 "ab" —— 故必须按 input 取字节。']),
    ('MCP_Server_Core.wsv',
     ['            // ★ 补能力 + 诚实性: 原来这里恒失败, 文案称"嵌入式GUI浏览器不支持…由主窗口自动管理"。'],
     'rw', "含诚实性契约(不得恒失败, 不得用误导文案); 把'补能力+原来这里恒失败'改成契约句",
     ['            // ★ 契约(诚实性): 本工具**不能**恒失败, 也不得用"嵌入式GUI浏览器不支持…由主窗口自动管理"这类文案 ——']),
    ('MCP_Server_Core.wsv',
     ['        // === v1.6 浏览器实例方法 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 浏览器实例方法 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v1.6 窗口管理 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 窗口管理 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v1.6 IPC 进程间通信 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === IPC 进程间通信 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v1.6 全局函数 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 全局函数 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v1.6 缓存/清理 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 缓存/清理 ===']),
    ('MCP_Server_Core.wsv',
     ['                // 补上 origin=https://example.com 后立刻变成 NONE(带不带结尾斜杠都可)。'],
     'rw', "块内唯一实测证据的第三行; 去掉'补上…后'的变更口吻",
     ['                // 带 origin=https://example.com 时立刻变成 NONE(带不带结尾斜杠都可)。']),
    ('MCP_Server_Core.wsv',
     ['                    // ★ 修(实测崩栈根因): 原实现在**日志路径**上使用了会被自己包装的内建方法 ——'],
     'rw', "块内唯一实测崩栈根因(日志路径用了会被自己包装的内建方法); 去掉'修(实测崩栈根因): 原实现'",
     ['                    // ★ 根因(实测崩栈): 日志路径上不能使用会被自己包装的内建方法 ——']),
    ('MCP_Server_Core.wsv',
     ['                    //   现改为: 安装前捕获原生 apply/call/toString/split/substring, 日志路径只用这些捕获量,'],
     'rw', "把'现改为:'改成'约束:'",
     ['                    //   约束: 安装前捕获原生 apply/call/toString/split/substring, 日志路径只用这些捕获量,']),
    ('MCP_Server_Core.wsv',
     ['                    //   (原来原函数只留在不可达的闭包里, 只能靠刷新页面恢复)。'],
     'rw', "含前提(必须留 __mcp_orig 才能卸载); 去掉'原来原函数只留在…'的对比口吻",
     ['                    //   若不留这个入口, 原函数只存在于不可达的闭包里, 只能靠刷新页面恢复。']),
    ('MCP_Server_Core.wsv',
     ['                    //   原实现用 forEach 回调(本身就是一次函数调用)天然每轮独立作用域, 所以没这个 bug。'],
     'rw', "把'原实现用 forEach…所以没这个 bug'改成中性对照",
     ['                    //   用 forEach 回调时天然每轮独立作用域(回调本身就是一次函数调用), 没有此问题。']),
    ('MCP_Server_Core.wsv',
     ['                    //   现改为: 安装前捕获 split/substring/toString, 一律用 Reflect.apply 调用,'],
     'rw', "把'现改为:'改成'约束:'",
     ['                    //   约束: 安装前捕获 split/substring/toString, 一律用 Reflect.apply 调用,']),
    ('MCP_Server_Core.wsv',
     ['        // === 反检测预设一键部署 (v2.8) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 反检测预设一键部署 ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v2.8.1 UX2: 滚动控制 (JS通道同步, AI翻页采集) ==='],
     'rw', '段标题; 去掉版本号与 UX2 批次号',
     ['        // === 滚动控制 (JS通道同步, AI翻页采集) ===']),
    ('MCP_Server_Core.wsv',
     ['        // === v2.8.1 UX3: 按快照索引操作 (snapshot的data-mcp-id闭环, 免手写选择器) ==='],
     'rw', '段标题; 去掉版本号与 UX3 批次号',
     ['        // === 按快照索引操作 (snapshot的data-mcp-id闭环, 免手写选择器) ===']),
    ('MCP_Server_Reverse.wsv',
     ['                // 改同步。附注: 本机实测 DOMDebugger 侧要的就是 eventName(Debugger 侧才用 instrumentation), 旧代码本就正确\r'],
     'rw', "含内核实测结论(DOMDebugger 侧要 eventName); 去掉'改同步。'开头与'旧代码本就正确'",
     ['                // 同步执行。附注: 本机实测 DOMDebugger 侧要的就是 eventName(Debugger 侧才用 instrumentation)。']),
    ('MCP_Server_Reverse.wsv',
     ['            // 纯算法调用增强: 支持 function_name 直调, 自动 Runtime.evaluate 解析 objectId (免手动取objectId)\r'],
     'rw', "能力说明; 去掉'增强'变更口吻",
     ['            // 纯算法直调: 支持 function_name, 自动 Runtime.evaluate 解析 objectId (免手动取 objectId)']),
    ('MCP_Server_Reverse.wsv',
     ['                //   现改为按调用方已给的关键参数**自动选一个可用的动作**, 并如实经 auto_prepared 上报。\r'],
     'rw', "含契约(自动选一个可用动作并如实上报); 去掉'现改为'",
     ['                //   契约: 按调用方已给的关键参数**自动选一个可用的动作**, 并如实经 auto_prepared 上报。']),
    ('MCP_Server_Reverse.wsv',
     ['                // 又因 touchPoints 同款教训(数组套对象用 yyjson 加入数组成员 会 0xC0000005),\r'],
     'rw', "把'同款教训'改成'同款约束', 保留 0xC0000005 这一硬事实",
     ['                // 又因 touchPoints 同款约束(数组套对象用 yyjson 加入数组成员 会 0xC0000005),']),
    ('MCP_Server_Reverse.wsv',
     ['        // === Hook逆向增强: 批量函数Hook + 调用栈快照 ===\r'],
     'rw', "段标题; 去掉'增强'变更口吻",
     ['        // === Hook逆向: 批量函数Hook + 调用栈快照 ===']),
    ('MCP_Server_Reverse.wsv',
     ['            // ⚠ 实测更正(本机CEF构建, 见 _audit/diag_instrument_script_wedge.py): 装上之后本会话的\r'],
     'rw', "块内唯一实测结论(装上之后本会话 JS 通道被阻塞, 只能重启); 去掉'更正'这个变更口吻",
     ['            // ⚠ 实测约束(本机CEF构建, 见 _audit/diag_instrument_script_wedge.py): 装上之后本会话的']),
    ('MCP_Server_Reverse.wsv',
     ['            //   只有重启进程才行。原注释"分析完必须 resume 即可"在本机不成立, 故已按实测更正。\r'],
     'rw', "把'原注释不成立, 故已按实测更正'改成对注释本身的否定",
     ['            //   只有重启进程才行 —— "分析完必须 resume 即可"在本机**不成立**。']),
    ('MCP_Server_Reverse.wsv',
     ['                //   "Precise coverage has not been started."。上一轮只把这句改写得更可行动, 但台账里\r'],
     'rw', "把'上一轮只把这句改写得更可行动'的过程叙述去掉, 保留'仅改写文案不够'的结论",
     ['                //   "Precise coverage has not been started."。仅改写文案不够 —— 台账里']),
    ('MCP_Server_Reverse.wsv',
     ['                //   现改为**自动补前置**: 未开启时自动 Profiler.enable + startPreciseCoverage 再取一次,\r'],
     'rw', "含契约(自动补前置并如实上报); 去掉'现改为'",
     ['                //   契约: **自动补前置** —— 未开启时自动 Profiler.enable + startPreciseCoverage 再取一次,']),
    ('MCP_Server_Reverse.wsv',
     ['            // ★ 修(实测): 本机内核绑定要求的是**旧协议参数名 newValue**, 不是新版 CDP 的 result。\r'],
     'rw', "块内唯一内核实测结论(绑定要 newValue 而非 result); 去掉'修(实测): '过程框",
     ['            // ★ 实测约束: 本机内核绑定要求的是**旧协议参数名 newValue**, 不是新版 CDP 的 result。']),
    ('MCP_Server_Reverse.wsv',
     ['            //   原实现发 {"result":{"value":…}} -> 内核恒定回\r'],
     'rw', "去掉'原实现'主语, 保留内核回包原文",
     ['            //   发 {"result":{"value":…}} -> 内核恒定回']),
    ('MCP_Server_Reverse.wsv',
     ['            //   即该工具此前**必然失败**。三者对照实测(原始 CDP, 同一暂停帧):\r'],
     'rw', "把'此前必然失败'改成'在此写法下必然失败'",
     ['            //   即该工具在此写法下**必然失败**。三者对照实测(原始 CDP, 同一暂停帧):']),
    ('MCP_Server_Reverse.wsv',
     ['            //     {"result":{"value":true}}   -> "mandatory field missing"(原实现)\r'],
     'rw', "括注由'原实现'改为'错误写法'",
     ['            //     {"result":{"value":true}}   -> "mandatory field missing"(错误写法)']),
    ('MCP_Server_Reverse.wsv',
     ['                // ★ 修(与其它调试器工具对齐, 也是"不重复造轮子"): 原来这里用的是\r'],
     'rw', "把'修(…): 原来这里用的是'改成契约句",
     ['                // ★ 契约(与其它调试器工具对齐, 也是"不重复造轮子"): 此处不能用']),
    ('MCP_Server_Reverse.wsv',
     ['                //   实测它们都能拿到 call_frame_id(evaluate 的零前置路径即依赖它)。故改用同一个主解析器。\r'],
     'rw', "去掉'故改用'的过程口吻",
     ['                //   实测它们都能拿到 call_frame_id(evaluate 的零前置路径即依赖它)。故统一用同一个主解析器。']),
    ('MCP_Server_Reverse.wsv',
     ['            // 反调试/风控陷阱检测(v2.8 技能书记载的"7类反调试陷阱: debugger语句/toString重写等"): **只检测布置了哪些陷阱, 不做绕过**。\r'],
     'rw', '去掉技能书引用里的版本号',
     ['            // 反调试/风控陷阱检测(技能书记载的"7类反调试陷阱: debugger语句/toString重写等"): **只检测布置了哪些陷阱, 不做绕过**。']),
    ('MCP_Server_System.wsv',
     ['        // === v1.6 其他 ===\r'],
     'rw', '段标题; 去掉版本号',
     ['        // === 其他工具 ===']),
    ('MCP_Server_VIP.wsv',
     ['        // === v1.6 快速连通性检查 ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 快速连通性检查 ===']),
    ('MCP_Server_VIP.wsv',
     ['            // ★ 修(安全性, 与 browser_vip_enable_devtools_observer 同一缺陷类): 原来只挡了"键缺失",'],
     'rw', "含安全契约(不能只挡键缺失, 否则最危险的取值成为兜底); 把'修(安全性…): 原来只挡了'改成约束陈述",
     ['            // ★ 安全性(与 browser_vip_enable_devtools_observer 同一缺陷类): 只挡"键缺失"不够 ——']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP 指纹补充 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP 指纹补充 ===']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP 插件管理 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP 插件管理 ===']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP 指定环境执行JS (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP 指定环境执行JS ===']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP CDP DOM文档获取 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP CDP DOM文档获取 ===']),
    ('MCP_Server_VIP.wsv',
     ['            // ★ 修(安全性, 实测): 原来只挡了"空文本"这一种情况, 于是**无法识别的取值会掉进破坏性分支** ——'],
     'rw', "含安全契约(白名单取值, 其余拒绝); 把'修(安全性, 实测): 原来只挡了'改成约束陈述",
     ['            // ★ 安全性(实测): 只挡"空文本"不够 —— **无法识别的取值会掉进破坏性分支**:']),
    ('MCP_Server_VIP.wsv',
     ['            //   实测传 enable:"mcp_probe" 时: 开关文本非空 -> 旧守卫不触发 -> 目标状态沿用 开关布尔(非布尔节点取逻辑=假)'],
     'rw', "把'旧守卫不触发'改成'该守卫不触发'",
     ['            //   实测传 enable:"mcp_probe" 时: 开关文本非空 -> 该守卫不触发 -> 目标状态沿用 开关布尔(非布尔节点取逻辑=假)']),
    ('MCP_Server_VIP.wsv',
     ['            //   即"最危险的分支成了兜底"。现改为: 只认显式白名单取值, 其余一律拒绝并说明。'],
     'rw', "含契约(只认显式白名单); 去掉'现改为:'",
     ['            //   即"最危险的分支成了兜底"。契约: 只认显式白名单取值, 其余一律拒绝并说明。']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP 触摸模拟 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP 触摸模拟 ===']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP UA完整指纹 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP UA完整指纹 ===']),
    ('MCP_Server_VIP.wsv',
     ['                // ★ 补能力(能力面反查确认的真缺口, VIP 审计排名第 1): 原来只设 8 个 UA 字段,'],
     'rw', "含契约(UA 字符串与 UA-CH 必须一起设, 否则更容易被识别); 把'补能力…原来只设 8 个'改成契约句",
     ['                // ★ 契约: UA 字符串与 UA-CH 必须一起设 —— 只设基础字段会']),
    ('MCP_Server_VIP.wsv',
     ['        // === VIP 屏幕方向 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === VIP 屏幕方向 ===']),
    ('MCP_Server_VIP.wsv',
     ['        // === 获取额外数据 (v1.7) ==='],
     'rw', '段标题; 去掉版本号',
     ['        // === 获取额外数据 ===']),
    ('main.wsv',
     ['        // (与上面 `__SHUTDOWN__` 同一惯例, 因此不需要新增任何握手字段)。'],
     'rw', "叙述里含唯一握手约定(复用 __SHUTDOWN__ 通道), 属实现契约; 只去掉'新增'这个变更口吻",
     ['        // (与上面 `__SHUTDOWN__` 同一惯例, 因此不需要额外的握手字段)。']),
]


def read_text(path):
    """返回 (行列表, 编码, 行尾, BOM)。按字节判 UTF-16LE / UTF-8。"""
    raw = open(path, "rb").read()
    if raw[:2] == b"\xff\xfe":
        text, enc, bom = raw.decode("utf-16-le"), "utf-16le", "\xff\xfe"
    elif raw[:3] == b"\xef\xbb\xbf":
        text, enc, bom = raw[3:].decode("utf-8"), "utf-8", "\xef\xbb\xbf"
    else:
        text, enc, bom = raw.decode("utf-8"), "utf-8", b""
    crlf, lf = raw.count(b"\r\n"), raw.count(b"\n")
    eol = "\r\n" if (lf and crlf == lf) else ("\n" if crlf == 0 else None)
    if eol is None:
        raise RuntimeError("%s 行尾混用(CRLF=%d, LF=%d), 本脚本不处理" % (path, crlf, lf))
    return text.split("\n"), enc, eol, bom


def find_all(lines, anchor):
    """返回 anchor 在 lines 中所有匹配的起始下标(0-based)。"""
    out, n, m = [], len(lines), len(anchor)
    if m == 0:
        return out
    for i in range(0, n - m + 1):
        if lines[i:i + m] == list(anchor):
            out.append(i)
    return out


def context_dump(lines, idx, radius=3):
    a = max(0, idx - radius)
    b = min(len(lines), idx + radius + 4)
    return "\n".join("  %6d| %s" % (k + 1, lines[k]) for k in range(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="只校验锚点与行数变化, 不写任何文件")
    args = ap.parse_args()

    files = sorted({e[0] for e in EDITS})
    print("== 操作备注清理 (判定表 %d 条) ==" % len(EDITS))
    print("模式: %s" % ("DRY-RUN (不写文件)" if args.dry_run else "写入"))
    print("涉及文件: %s" % ", ".join(files))
    print()

    orig, enc, eol, bom = {}, {}, {}, {}
    for f in files:
        p = os.path.join(SRC, f)
        if not os.path.exists(p):
            print("!! 源文件不存在: %s" % p)
            return 2
        orig[f], enc[f], eol[f], bom[f] = read_text(p)
    for f in files:
        print("  %-26s %6d 行  enc=%s  eol=%s  bom=%s"
              % (f, len(orig[f]), enc[f], "CRLF" if eol[f] == "\r\n" else "LF",
                 ("有" if bom[f] else "无")))

    # ---- 阶段1: 锚点定位 (全部命中数必须 == 1) ----
    placed, bad = [], []
    for k, (f, anchor, kind, why, repl) in enumerate(EDITS, 1):
        hits = find_all(orig[f], anchor)
        if len(hits) != 1:
            bad.append((k, f, len(hits), hits, anchor))
            continue
        placed.append((f, hits[0], anchor, repl, k))
    if bad:
        print()
        print("!! 有 %d 条锚点命中数 != 1, 整批中止, 未写任何文件:" % len(bad))
        for k, f, n, hits, anchor in bad:
            print("   #%d %s -> 命中 %d 次" % (k, f, n))
            for ln in anchor:
                print("      锚点行: %r" % ln)
            for h in hits[:3]:
                print("      命中于第 %d 行附近:" % (h + 1))
                print(context_dump(orig[f], h))
        return 3

    # ---- 阶段2: 同文件内锚点不得重叠 ----
    for f in files:
        rs = sorted([p for p in placed if p[0] == f], key=lambda x: x[1])
        for i in range(1, len(rs)):
            prev, cur = rs[i - 1], rs[i]
            if cur[1] < prev[1] + len(prev[2]):
                print("!! %s 锚点重叠: #%d(第%d行) 与 #%d(第%d行)"
                      % (f, prev[4], prev[1] + 1, cur[4], cur[1] + 1))
                print(context_dump(orig[f], prev[1]))
                return 4

    # ---- 阶段2b: 同一锚点是否也出现在别的源码 .wsv 里(仅提示, 不阻断) ----
    others = {}
    for nm in sorted(os.listdir(SRC)):
        if not nm.endswith(".wsv") or "~vbak" in nm:
            continue
        try:
            others[nm] = "\n".join(read_text(os.path.join(SRC, nm))[0])
        except Exception:
            continue
    cross = []
    for (f, idx, anchor, repl, k) in placed:
        key = "\n".join(anchor)
        for nm, body in others.items():
            if nm != f and key in body:
                cross.append((k, f, nm))
    if cross:
        print()
        print("!! 以下锚点也出现在另一个源码文件里 —— 本脚本只在该条声明的文件内替换:")
        for k, f, nm in cross:
            print("   #%d 声明于 %s, 同样出现在 %s" % (k, f, nm))

    # ---- 阶段3: 生成新内容 + 断言行数变化 ----
    new, want_delta, per_file = {}, {}, {}
    for f in files:
        lines = list(orig[f])
        rs = sorted([p for p in placed if p[0] == f], key=lambda x: x[1], reverse=True)
        for (_f, idx, anchor, repl, k) in rs:
            lines[idx:idx + len(anchor)] = list(repl)
        want = sum(len(p[3]) - len(p[2]) for p in placed if p[0] == f)
        got = len(lines) - len(orig[f])
        if got != want:
            print("!! %s 行数变化断言失败: 实际 %+d, 预期 %+d" % (f, got, want))
            return 5
        new[f], want_delta[f] = lines, want
        stat = dict((k, 0) for k in ("del", "del_lines", "rw", "rw_before",
                                    "rw_after", "absorbed"))
        for (f2, idx, anchor, repl, k) in placed:
            if f2 != f:
                continue
            if EDITS[k - 1][2] == "del":
                stat["del"] += 1
                stat["del_lines"] += len(anchor)
            else:
                stat["rw"] += 1
                stat["rw_before"] += len(anchor)
                stat["rw_after"] += len(repl)
                if len(repl) < len(anchor):
                    stat["absorbed"] += len(anchor) - len(repl)
        per_file[f] = stat

    # ---- 阶段4: 写回 (dry-run 跳过) ----
    if not args.dry_run:
        if not os.path.isdir(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        for f in files:
            shutil.copy2(os.path.join(SRC, f), os.path.join(BACKUP_DIR, f))
        for f in files:
            with open(os.path.join(SRC, f), "wb") as fh:
                fh.write(bom[f] + eol[f].join(new[f]).encode(enc[f]))

    # ---- 统计 ----
    print()
    print("-- 按文件统计 (条数 | 删条/删行 | 改条/改写前->后 | 净行数) --")
    keys = ("del", "del_lines", "rw", "rw_before", "rw_after", "absorbed")
    tot = dict((k, 0) for k in keys)
    for f in files:
        s = per_file[f]
        print("   %-26s %4d | %4d/%-4d | %4d/%d->%d | %+d"
              % (f, s["del"] + s["rw"], s["del"], s["del_lines"], s["rw"],
                 s["rw_before"], s["rw_after"], want_delta[f]))
        for k in keys:
            tot[k] += s[k]
    print("   %-26s %4d | %4d/%-4d | %4d/%d->%d | %+d"
          % ("合计", tot["del"] + tot["rw"], tot["del"], tot["del_lines"], tot["rw"],
             tot["rw_before"], tot["rw_after"], sum(want_delta.values())))
    print()
    print("共处理 %d 条: 删 %d 条(删 %d 行), 改 %d 条(改写前 %d 行 -> 改写后 %d 行), 净行数 %+d"
          % (tot["del"] + tot["rw"], tot["del"], tot["del_lines"], tot["rw"],
             tot["rw_before"], tot["rw_after"], sum(want_delta.values())))
    if tot["absorbed"]:
        print("  其中 %d 行被并入上一行(整块合并), 故实际消失的行数 = %d + %d = %d"
              % (tot["absorbed"], tot["del_lines"], tot["absorbed"],
                 tot["del_lines"] + tot["absorbed"]))
    if args.dry_run:
        print()
        print("DRY-RUN: 未写任何文件。去掉 --dry-run 即写入(写入前会备份到")
        print("  %s)" % BACKUP_DIR)
    else:
        print()
        print("备份目录: %s" % BACKUP_DIR)
        print("已写入: %s" % ", ".join(files))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        print("!! 未捕获异常, traceback 全文:")
        traceback.print_exc()
        sys.exit(1)
