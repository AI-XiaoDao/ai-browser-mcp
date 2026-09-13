# -*- coding: utf-8 -*-
r"""第140轮补丁: ①修复"注册成功却永不执行"的 CDP 预注入 ②`inject handler` 诚实化 ③启动期事件可观测。

## 实测(三臂对照, 本机可复现)
| 臂 | 做法 | 导航后哨兵 `window.__plS` |
|---|---|---|
| A | 只 `browser_reverse_preload`(现状) | **`undefined`** —— CDP 回 success+identifier, 但脚本**永不执行** |
| B | 先 `Page.enable` 再注册 | **`C1`** ✅ |
| C | `Page.enable` + 连续注册两次 | **`C1`** ✅ |
⇒ `Page.addScriptToEvaluateOnNewDocument` 在本机**必须先启用 Page 域**; 现状是"注册成功但静默无效",
而多个工具描述还把 `browser_reverse_preload` 推荐成"拦打包器最稳"的路径 —— 属**假能力**, 必须修。
(另实测: 注册 preload **不会**拖慢 JS 通道: 注册前后 execute_js 都是 0.03s。)

## 另两项
· `browser_inject {persist:true, type:"handler"}`: 实测其代码被当成**普通页面 JS** 执行(哨兵可读),
  并不是它承诺的"原生 handler 桥"(那需要渲染进程内 `FBrowser_V8_注册JS扩展`, 而本项目渲染事件不派发到主进程;
  `FBrowser_JS交互_注册` 两轮实测在本项目不可用) ⇒ 改为**可行动拒绝** + 给出实测有效的替代。
· 启动期事件(`app_startup_cmdline` / `app_startup_request_context_ready` …): 原先**永久丢失** ——
  两个独立成因叠加: ①监控开关默认假(而"开开关"的工具只能在启动**之后**调用) ②`记录事件日志` 在
  SQLite 未就绪时直接 return。改为: 开关默认真 + 未就绪时进内存缓冲, DB 就绪后首次调用即 flush。

用法: py -3 _audit\_apply_round140.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
EVENTS = os.path.join(ROOT, 'src', 'MCP_BrowserEvents.wsv')
APPLY = '--apply' in sys.argv

# ── H1: 预注入: 先 Page.enable(零前置) ──
PL_OLD = '''            // 改同步: 内核会回 identifier(脚本句柄), 调用方需要它才能后续移除该预注入脚本'''
PL_NEW = '''            // ★ 零前置(实测强制): **必须先启用 Page 域**, 否则 `Page.addScriptToEvaluateOnNewDocument`
            //   在本机会返回 success + identifier, 但注册进去的脚本**永不执行** —— 三臂对照实测:
            //   只注册 → 导航后哨兵 undefined; 先 Page.enable 再注册 → 哨兵 C1。(注册本身不拖慢 JS 通道。)
            变量 pl域结果 <类型 = 文本型>
            pl域结果 = 执行V8CDP命令 (命令ID + "_pe", "Page.enable", "{}", "Page 域已启用")
            如果 (MCP命令服务器.CDP同步结果是否成功 (pl域结果) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "Page.enable 失败, 预注入无法生效: " + MCP命令服务器.取CDP同步结果错误 (pl域结果) + " | 实测: 不先启用 Page 域时注册会回 success 但脚本永不执行, 故此处直接失败而不是给你一个假成功"))
            }
            MCP_响应构建.记录自动补域 ("Page")
            // 改同步: 内核会回 identifier(脚本句柄), 调用方需要它才能后续移除该预注入脚本'''

PL_RET_OLD = '''            "预注入脚本已注册(每次新文档创建前执行); cdp_result.identifier 即脚本句柄, 可用 browser_cdp_call method=Page.removeScriptToEvaluateOnNewDocument 移除该脚本"'''
PL_RET_NEW = '''            "预注入脚本已注册(每次新文档创建前执行); 已自动启用 Page 域(auto_prepared) —— 实测不启用时脚本永不执行; cdp_result.identifier 即脚本句柄, 可用 browser_cdp_call method=Page.removeScriptToEvaluateOnNewDocument 移除该脚本"'''

PL_DESC_OLD = '''"CDP逆向: 预注入脚本。Page.addScriptToEvaluateOnNewDocument—在所有页面JS执行之前注入,先于任何反检测/混淆代码加载"'''
PL_DESC_NEW = '''"CDP逆向: 预注入脚本。Page.addScriptToEvaluateOnNewDocument—在每个新文档创建前执行(早于页面自身脚本), 是拦打包器/反检测的首选时机 | **零前置(实测强制)**: 本工具会先自动 Page.enable 并经 auto_prepared 上报 —— 实测不启用 Page 域时, 注册会返回 success + identifier 但脚本**永不执行**(三臂对照: 只注册→哨兵 undefined; 先 enable→哨兵 C1) | 多次注册各自返回 identifier, 可用 browser_cdp_call method=Page.removeScriptToEvaluateOnNewDocument 移除"'''

# ── H2: inject handler 诚实化 + js 分支注释订正 ──
INJ_H_OLD = '''                如果 (persist && injectType == "handler")
                {
                    // 持久handler模式: 存入持久V8扩展列表, 由 渲染_即将初始化WebKit → FBrowser_V8_注册JS扩展 自动注入
                    变量 注入标识 <类型 = 文本型>
                    注入标识 = MCP命令服务器.yyjson取文本 (参数JSON, "inject_id")
                    如果 (注入标识 == "")
                    {
                        注入标识 = "mcp_inject_handler_" + 到文本 (取启动时间 ())
                    }
                    // 转义code中的|防止分隔符冲突, 解析侧(MCP_BrowserEvents)会反向还原
                    变量 安全code_handler <类型 = 文本型>
                    安全code_handler = code
                    子文本替换 (安全code_handler, "{PIPE}", "{PIPE_ESC}", , , 假)
                    子文本替换 (安全code_handler, "|", "{PIPE}", , , 假)
                    MCP命令服务器.加入持久V8扩展 (注入标识, 安全code_handler, "handler")
                    返回 (MCP_响应构建.响应_需要刷新 (命令ID, "V8 Handler持久注入已排队 | 将在新页面时自动注册 | 需要刷新/browser_reload"))
                }'''
INJ_H_NEW = '''                如果 (persist && injectType == "handler")
                {
                    // ⚠ 诚实化: 该模式**做不到它承诺的事** —— 实测它的代码最终走 应用持久V8到框架 → 框架.执行JS代码,
                    //   即被当作**普通页面 JS** 执行(哨兵可读), 而不是"页面 JS 调原生、原生同步回值"的 handler 桥。
                    //   真实 handler 桥需要渲染进程内 FBrowser_V8_注册JS扩展(或 FBrowser_JS交互_注册), 而本项目的
                    //   渲染进程事件不派发到主进程, 后者也已被两轮实测判定不可用(_audit/remove_js_query_bridge.py)。
                    //   故这里**明确拒绝**并给出实测有效的替代, 而不是回一句"已排队"让人以为桥通了。
                    返回 (MCP_响应构建.命令失败 (命令ID, "type=handler 本机不支持: 它承诺的『页面 JS 调原生并同步回值』需要渲染进程内注册 JS 扩展(FBrowser_V8_注册JS扩展 / FBrowser_JS交互_注册), 而本项目渲染进程事件不派发到主进程、JS 交互桥也经实测不可用 | 实测现状: 传 handler 时你的代码会被当作**普通页面 JS** 执行(不是原生桥) | 替代: ①只想在页面里预置代码 → 用 type:js + persist:true(实测: 设置后导航/重载都生效) ②要在页面自身脚本**之前**注入 → browser_reverse_preload(已修: 会自动 Page.enable) ③只对当前页执行一次 → browser_execute_js"))
                }'''
INJ_J_OLD = '''                    // 持久js模式: 存入持久V8扩展列表, 由 渲染_即将创建V8环境 → V8环境.执行JS代码 自动注入'''
INJ_J_NEW = '''                    // 持久js模式: 存入持久V8扩展列表; 真正生效路径是 浏览器_载入开始 事件 → 应用持久V8到框架(框架)
                    //   → 框架.执行JS代码。实测有效: 设置后 reload 与 navigate 到新地址都能读到哨兵。
                    //   (旧注释写"由 渲染_即将创建V8环境 注入" —— 那是渲染进程事件, 在本项目不派发, 注释与实现不符, 已订正)'''

# ── H3a: 记录事件日志: DB 未就绪时进内存缓冲, 就绪后 flush ──
LOG_OLD = '''    方法 记录事件日志 <公开 静态 @输出名 = "RecordEventLog" @强制输出 = 真>
    参数 日志类型 <类型 = 文本型 @输出名 = "LogType">
    参数 事件名 <类型 = 文本型 @默认值 = "" @输出名 = "EventName">
    参数 浏览器ID <类型 = 整数 @默认值 = 0 @输出名 = "BrowserID">
    参数 数据JSON <类型 = 文本型 @输出名 = "DataJSON">
    {
        如果 (缓存数据库可用 () == 假)
        {
            返回
        }'''
LOG_NEW = '''    方法 记录事件日志 <公开 静态 @输出名 = "RecordEventLog" @强制输出 = 真>
    参数 日志类型 <类型 = 文本型 @输出名 = "LogType">
    参数 事件名 <类型 = 文本型 @默认值 = "" @输出名 = "EventName">
    参数 浏览器ID <类型 = 整数 @默认值 = 0 @输出名 = "BrowserID">
    参数 数据JSON <类型 = 文本型 @输出名 = "DataJSON">
    {
        如果 (缓存数据库可用 () == 假)
        {
            // ★ 启动期事件不能丢: `即将处理命令行`/`请求环境初始化完毕` 等在主进程**确实会触发**, 但都早于
            //   SQLite 打开(启动方法 里 FBrowser_初始化 先于 启动MCP服务器)。原先这里直接 return ⇒ 这些事件
            //   永久消失, 而文档还把"app_* 一族永不产生记录"写成了渲染进程归属问题(两个成因被混为一谈)。
            //   改为先进内存缓冲(每条 5 个成员: 类型/事件名/浏览器ID/数据/时间戳, 上限 启动期事件缓冲上限 条),
            //   DB 就绪后由本方法的首次成功调用按序 flush。
            启动期事件缓冲.加入成员 (日志类型)
            启动期事件缓冲.加入成员 (事件名)
            启动期事件缓冲.加入成员 (到文本 (浏览器ID))
            启动期事件缓冲.加入成员 (数据JSON)
            启动期事件缓冲.加入成员 (到文本 (取现行时间毫秒 ()))
            判断循环 (启动期事件缓冲.取成员数 () > 启动期事件缓冲上限 * 5)
            {
                启动期事件缓冲.删除成员 (0)
            }
            返回
        }
        如果 (启动期事件缓冲.取成员数 () >= 5)
        {
            // 先整体取出再逐条落库(避免在循环里持续操作同一数组); 顺序与产生顺序一致
            变量 待落库 <类型 = 文本数组类>
            异步缓存锁.加锁 ()
            计次循环 (启动期事件缓冲.取成员数 ())
            {
                待落库.加入成员 (启动期事件缓冲.取成员 (取循环索引 ()))
            }
            // 清空缓冲: 文本数组类没有"清空()", 项目既有做法是循环 删除成员(0) (见 清空持久V8扩展)
            判断循环 (启动期事件缓冲.取成员数 () > 0)
            {
                启动期事件缓冲.删除成员 (0)
            }
            异步缓存锁.解锁 ()
            变量 落库位 <类型 = 整数 值 = 0>
            判断循环 (落库位 + 4 < 待落库.取成员数 ())
            {
                写事件日志行 (待落库.取成员 (落库位), 待落库.取成员 (落库位 + 1), 文本到整数 (待落库.取成员 (落库位 + 2)), 待落库.取成员 (落库位 + 3), 文本到长整数 (待落库.取成员 (落库位 + 4)))
                落库位 = 落库位 + 5
            }
        }'''
# 抽出"写一行"的方法 + 静态缓冲字段
LOG_SPLIT_OLD = '''        异步缓存锁.加锁 ()
        变量 stmt <类型 = SQLite记录集类>
        stmt = 缓存数据库.取记录集 ("INSERT INTO event_log (log_type, event_name, browser_id, data_json, created_at) VALUES (?, ?, ?, ?, ?)", )'''
LOG_SPLIT_NEW = '''        写事件日志行 (日志类型, 事件名, 浏览器ID, 存储JSON, 取现行时间毫秒 ())
    }

    # 事件落库的唯一出口(供"实时写入"与"启动期缓冲 flush"共用, 不再各写一份 INSERT)
    方法 写事件日志行 <公开 静态 @输出名 = "WriteEventLogRow" @强制输出 = 真>
    参数 日志类型 <类型 = 文本型 @输出名 = "LogType">
    参数 事件名 <类型 = 文本型 @输出名 = "EventName">
    参数 浏览器ID <类型 = 整数 @输出名 = "BrowserID">
    参数 存储JSON <类型 = 文本型 @输出名 = "StoreJSON">
    参数 时间戳 <类型 = 长整数 @输出名 = "Timestamp">
    {
        异步缓存锁.加锁 ()
        变量 stmt <类型 = SQLite记录集类>
        stmt = 缓存数据库.取记录集 ("INSERT INTO event_log (log_type, event_name, browser_id, data_json, created_at) VALUES (?, ?, ?, ?, ?)", )'''
LOG_SPLIT2_OLD = '''        stmt.置长整数参数数据 (5, 取现行时间毫秒 ())
        stmt.执行语句 ()
        stmt.释放 ()'''
LOG_SPLIT2_NEW = '''        stmt.置长整数参数数据 (5, 时间戳)
        stmt.执行语句 ()
        stmt.释放 ()'''

BUFFER_ANCHOR = '''    变量 是否监控启动流程 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "请求环境初始化完毕/即将处理命令行/即将启动子进程/消息调度/即将初始化WebKit → app_event:startup_*" @输出名 = "IsMonitorStartup">'''
BUFFER_NEW = '''    # ★ 启动期事件开关**默认真**: 这些事件(命令行/请求环境/子进程/消息调度)每次进程只发生一次, 且都**早于**
    #   "开开关"的工具调用时刻(那时进程已经起来) ⇒ 默认假等于"永久看不见"。实测: 默认真 + 下面的内存缓冲后,
    #   `browser_event event_type=app_startup_cmdline` 与 `app_startup_request_context_ready` 都能查到。
    变量 是否监控启动流程 <公开 静态 类型 = 逻辑型 值 = 真 注释 = "请求环境初始化完毕/即将处理命令行/即将启动子进程/消息调度/即将初始化WebKit → app_event:startup_*(默认开: 这些事件早于任何工具调用时刻, 关着就等于永久看不见)" @输出名 = "IsMonitorStartup">
    # 启动期事件的内存缓冲(SQLite 就绪前): 每条占 5 个成员(类型/事件名/浏览器ID/数据JSON/时间戳), 上限 40 条
    变量 启动期事件缓冲 <公开 静态 类型 = 文本数组类 @输出名 = "StartupEventBuffer">
    变量 启动期事件缓冲上限 <公开 静态 类型 = 整数 值 = 40 @输出名 = "StartupEventBufferLimit">'''

EDITS = [
    (REV, 'H1a 预注入: 先 Page.enable', PL_OLD, PL_NEW),
    (REV, 'H1a2 预注入成功文案: 标注 auto_prepared', PL_RET_OLD, PL_RET_NEW),
    (SERVER, 'H1b 预注入描述(实测约束)', PL_DESC_OLD, PL_DESC_NEW),
    (CORE, 'H2a handler 诚实化', INJ_H_OLD, INJ_H_NEW),
    (CORE, 'H2b js 分支注释订正', INJ_J_OLD, INJ_J_NEW),
    (SERVER, 'H3a 事件日志: DB 未就绪进缓冲 + flush', LOG_OLD, LOG_NEW),
    (SERVER, 'H3b 抽出 写事件日志行', LOG_SPLIT_OLD, LOG_SPLIT_NEW),
    (SERVER, 'H3c 写行用传入时间戳', LOG_SPLIT2_OLD, LOG_SPLIT2_NEW),
    (SERVER, 'H3d 启动开关默认真 + 缓冲字段', BUFFER_ANCHOR, BUFFER_NEW),
]


def main():
    print('== 第140轮补丁 (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-40s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    for path, txt in cache.items():
        print('%s: 行数 %d' % (os.path.basename(path), len(txt.split('\n'))))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
