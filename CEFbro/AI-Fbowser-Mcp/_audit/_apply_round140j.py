# -*- coding: utf-8 -*-
r"""第140轮补丁 J: 更正"整个 app_* 族永不入库"的过宽结论(本轮实测已推翻其中一半)。

## 本轮实测(改动 I 之后, 同一实例真机查询)
| 事件 | 结果 |
|---|---|
| `app_startup_cmdline` | ✅ 有记录, data=`{"process_type":""}` |
| `app_startup_request_context_ready` | ✅ 多条 |
| `app_startup_child_process` | ✅ 多条 |
| `app_startup_message_pump` | ❌ 查询闸门未放行(见下) |
| `app_render_*` / `app_v8_*` / `app_render_ws_*` | ❌ 仍是 0(渲染进程触发, 本机不派发 —— 这半边结论成立) |

## 两个缺陷
1. **查询闸门漏了本族开关**: `app开关已开 = (是否监控应用事件 || 是否监控渲染细节 || 是否监控WebSocket渲染)`
   —— 没算 `是否监控启动流程`(现在是默认真)与 `是否监控插件生命周期` ⇒ 事件**已入库却报"开关未开启"**。
2. **文案过宽**: "整个 app_* 族不产生任何记录…永远不会入库"已与实测不符 —— 必须收窄为
   "渲染族不派发 ⇒ 不入库; **主进程族(启动期/扩展生命周期)会入库**"。

用法: py -3 _audit\_apply_round140j.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
MAIN = os.path.join(ROOT, 'src', 'main.wsv')
APPLY = '--apply' in sys.argv

GATE_OLD = '''                    app开关已开 = (MCP命令服务器.是否监控应用事件 || MCP命令服务器.是否监控渲染细节 || MCP命令服务器.是否监控WebSocket渲染)'''
GATE_NEW = '''                    // 把**所有** app_* 族开关都算进来: 漏掉本族开关会让"事件已入库"却报"开关未开启"
                    // (实测: app_startup_* 已入库, 却因这里没算 是否监控启动流程 而被拒绝查询)
                    app开关已开 = (MCP命令服务器.是否监控应用事件 || MCP命令服务器.是否监控渲染细节 || MCP命令服务器.是否监控WebSocket渲染 || MCP命令服务器.是否监控启动流程 || MCP命令服务器.是否监控插件生命周期)'''

CLAIM_OLD = '''                       返回 (MCP_响应构建.命令失败 (命令ID, "未找到应用事件: " + evtType + " | 监控开关**已开启**, 但本机该族无记录 —— 实测: app_* 族(含 app_render_*/app_v8_*/app_startup_*)由渲染进程(FBroSubprocess.exe)触发, 不会被派发到本项目的事件覆盖上, 因此永远不会入库 | 可用替代: 页面侧事实请用 browser_event 的浏览器事件族(load_*/title_changed/url_changed/frame_* 等, 已实测有效) + browser_execute_js / browser_console_* / browser_network | 主进程侧等价能力请用 CDP 类工具(Emulation.* / Page.addScriptToEvaluateOnNewDocument / Debugger.setPauseOnExceptions)"))'''
CLAIM_NEW = '''                       // 文案按**实测**收窄(原写"整个 app_* 族永不入库"已被推翻一半):
                       //   · 渲染族(app_render_*/app_v8_*/app_render_ws_*)由渲染进程 FBroSubprocess.exe 触发,
                       //     本机不派发到主进程覆盖 ⇒ 确实永远不入库;
                       //   · 主进程族**会**入库: app_startup_cmdline / app_startup_request_context_ready /
                       //     app_startup_child_process(实测已可查)、扩展生命周期 app_extension_*(运行期触发, 同样可查)。
                       返回 (MCP_响应构建.命令失败 (命令ID, "未找到应用事件: " + evtType + " | 监控开关**已开启**, 但该事件无记录 | 实测分界: ①**主进程族会入库** —— app_startup_cmdline / app_startup_request_context_ready / app_startup_child_process(已实测可查)与 app_extension_*(运行期扩展生命周期); ②**渲染族不会入库** —— app_render_* / app_v8_* / app_render_ws_* 由渲染进程(FBroSubprocess.exe)触发, 不派发到主进程覆盖 | 若你查的是渲染族, 请用替代: 页面侧事实用浏览器事件族(load_*/title_changed/url_changed/frame_* 已验证有效) + browser_execute_js / browser_console_* / browser_network; 主进程侧等价能力用 CDP 类工具(Emulation.* / Page.addScriptToEvaluateOnNewDocument / Debugger.setPauseOnExceptions)"))'''

SWITCH_HINT_OLD = '''返回 (MCP_响应构建.命令失败 (命令ID, "未找到应用事件: " + evtType + " | 监控开关未开启, 请先 browser_collect action=event_app_enable(注意: 即使开启, 本机 app_* 族也未必会产生记录, 详见 browser_collect 说明)"))'''
SWITCH_HINT_NEW = '''返回 (MCP_响应构建.命令失败 (命令ID, "未找到应用事件: " + evtType + " | 相关监控开关未开启, 请先 browser_collect action=event_app_enable(总闸) 或本族开关 action=event_startup_enable(启动族)/action=event_extension_enable(扩展族) | 注意: 启动族开关当前**默认已开**, 若仍无记录说明该事件本次进程未触发"))'''

MAIN_CLAIM_OLD = '''# 实测(报告 141 节): 本机 app_* 族(含 app_render_*/app_v8_*/app_startup_*)不会入库 —— 渲染进程是 SDK 自带的 FBroSubprocess.exe,'''
MAIN_CLAIM_NEW = '''# 实测(第140轮更正): **渲染族**(app_render_*/app_v8_*/app_render_ws_*)不会入库 —— 渲染进程是 SDK 自带的 FBroSubprocess.exe,
# 而**主进程族**(app_startup_*/app_extension_*)会入库(已实测可查: app_startup_cmdline / request_context_ready / child_process);'''

EDITS = [(CORE, 'J1 查询闸门补全本族开关', GATE_OLD, GATE_NEW),
         (CORE, 'J2 过宽结论收窄为实测分界', CLAIM_OLD, CLAIM_NEW),
         (CORE, 'J3 未开启时的指引更准', SWITCH_HINT_OLD, SWITCH_HINT_NEW),
         (MAIN, 'J4 main.wsv 注释同上更正', MAIN_CLAIM_OLD, MAIN_CLAIM_NEW)]


def main():
    print('== 第140轮补丁 J (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-38s 锚点未找到(可能已应用)' % tag)
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
