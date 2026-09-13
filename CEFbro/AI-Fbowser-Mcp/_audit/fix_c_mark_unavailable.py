# -*- coding: utf-8 -*-
"""按 objective 第(C)项允许的"明确标注不可用"处置渲染侧事件族。

依据(真机证伪两条候选修法):
  §39  既有 进程间消息_收到主进程消息 的页内注入也不生效
  §41  渲染进程由 SDK 自带 FBroSubprocess.exe 承载, 与承载本项目代码的浏览器进程分离
  §42  `获取默认事件` → 用户额外配置.置事件 实测也无法让渲染侧事件被派发
=> 渲染侧事件在本架构下不可达。objective 明确允许"明确标注不可用"作为处置。

只改**提示文案**, 不动任何逻辑。受影响的事件族(依类库"只能在渲染进程中使用"注解):
  event_render_enable    (渲染细节: app_render_*)
  event_renderws_enable  (渲染侧WebSocket: app_render_ws_*)
  event_startup_enable   (其中 渲染_即将初始化WebKit 一项)
不受影响因此不加标注: event_extension_enable(扩展插件_* 非渲染进程专属)。
"""
import io
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_Core.wsv"
t = io.open(P, encoding="utf-8").read()

REPS = [
    # 渲染细节
    ('"渲染细节监控已启用 (查询用 app_render_v8_context_created / app_render_message_received / app_render_loading_state / app_render_load_start / app_render_load_end)。注意: 本类事件由 CEF 渲染进程触发, 窗口内嵌渲染模式下是否回调以内核为准"',
     '"渲染细节监控开关已置真。⚠ 实测说明: 本族事件(渲染_*)由 CEF 渲染进程触发, 而渲染进程是 SDK 自带的 FBroSubprocess.exe, 与承载本项目代码的浏览器进程分离; 经真机验证, 这些事件**不会**被派发到本项目的事件覆盖上, 因此 app_render_* **不会产生任何记录**。开启本开关不会报错, 但请不要依赖其查询结果。需要页面侧信息请改用 browser_execute_js / browser_snapshot / browser_dom_query 等主进程侧工具"'),
    # 渲染侧 WebSocket
    ('"渲染侧WebSocket监控已启用 (查询用 app_render_ws_created / app_render_ws_closed / app_render_ws_connect / app_render_ws_recv / app_render_ws_send)"',
     '"渲染侧WebSocket监控开关已置真。⚠ 实测说明: 本族事件同属渲染进程事件(渲染_VIP_WebSocket客户端_*), 在本架构下不会被派发, app_render_ws_* **不会产生记录**。若要观察 WebSocket 流量, 请改用 browser_intercept(手写过滤器) 或 browser_reverse_websocket / browser_network 等主进程侧能力"'),
    # 启动流程(仅其中 WebKit 初始化一项属渲染进程)
    ('"启动流程监控已启用 (查询用 app_startup_request_context_ready / app_startup_cmdline / app_startup_child_process / app_startup_message_pump / app_startup_webkit_init)。注意: 该类事件在进程启动时触发, 开启监控**之后**的启动阶段才会被记录"',
     '"启动流程监控开关已置真 (可查 app_startup_request_context_ready / app_startup_cmdline / app_startup_child_process / app_startup_message_pump)。两点说明: ① 这些事件在进程启动阶段触发, 开启监控**之后**的启动流程才会被记录; ② app_startup_webkit_init 属渲染进程事件, 在本架构下不会被派发, 不会产生记录"'),
]

n = 0
for old, new in REPS:
    c = t.count(old)
    print("  命中 %d  <- %s" % (c, old[:52]))
    t = t.replace(old, new)
    n += c

io.open(P, "wb").write(t.encode("utf-8"))
print("合计改写提示文案: %d 处" % n)
