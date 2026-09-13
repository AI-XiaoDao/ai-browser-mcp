# -*- coding: utf-8 -*-
r"""第138轮: `browser_debugger_pause` 从"⛔ 恒失败守卫"变成**真正可用且安全有界**的暂停工具。

## 现状(实测)
`browser_debugger_pause` 在 tools/list 里可见、有注册项, 但分支**无条件返回失败**:
  `Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) | 请用 debugger_flow …`
用户的要求是"所有显示出来的 MCP 能力都能稳定正常执行功能" —— 一个只会失败的工具不算能力。
而项目里**早就有**安全的暂停机制 `确保调试器已暂停`(`MCP_Server.wsv:1814`):
先显式 `Debugger.enable` → 用页面自身的 `setTimeout(...,30)` 安排一个**必然很快执行**的语句给 pause 做落点
→ 再 `Debugger.pause` → 等 `Debugger.paused`(并带 `auto_prepared` 如实上报) ⇒ 暂停成为**有界**操作。
`step_over/step_into/step_out` 等 8 处已经在用它。

## 本补丁(复用, 不重复造轮子)
1. `MCP_Server_Core.wsv` 的 `browser_debugger_pause` 分支改为调用 `确保调试器已暂停`;
   并在调用前**武装既有的防呆网**: 记下 `暂停前事件指纹` 与 `待恢复暂停时间` ——
   主循环的 `检查暂停自动恢复`(`MCP_Server.wsv:9982`)会在"10 秒内没等到暂停事件"时自动 resume,
   防的就是"pause 发出后队列被永久堵住"。只在**调用前页面未暂停**时武装(页面本来就暂停时不武装, 免得误 resume)。
2. `MCP_Server.wsv` 的工具描述从"⛔ 已禁用(恒失败)"改写为真实行为 + 看现场/恢复方式 + 自动自救说明。

用法: py -3 _audit\_apply_round138.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

CORE_OLD = '''            // 安全设计: 原始Debugger.pause在无JS执行点的页面上永不返回, 且会堵塞CDP命令队列
            // (队列FIFO, 后续CDP命令与自动resume全部排在其后, 连锁超时)
            // 正确暂停流程: debugger_flow(一键) 或 enable → set_breakpoint → navigate → wait_paused
            返回 (MCP_响应构建.命令失败 (命令ID, "Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) | 请用 debugger_flow 一键断点 或 debugger_enable → set_breakpoint → navigate → wait_paused"))'''

CORE_NEW = '''            // 安全设计: 裸发 Debugger.pause 在没有 JS 执行点的页面上**永不返回**, 且会堵塞 CDP 命令队列
            // (队列 FIFO —— 后续 CDP 命令与自动 resume 全排在它后面, 连锁超时, 连 browser_status 都可能挂)。
            // 故这里**不裸发** pause, 而是复用既有的 确保调试器已暂停: 先显式启用 Debugger 域 → 用页面自身的
            // setTimeout 安排一个 30ms 后**必然执行**的语句给 pause 一个落点 → 再 pause 并等 Debugger.paused
            // ⇒ "暂停"变成**有界**操作(失败会明确说明原因与替代, 不会静默堵住队列)。
            变量 暂停前已有 <类型 = 文本型>
            暂停前已有 = MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")
            MCP命令服务器.暂停前事件指纹 = 取文本左边 (暂停前已有, 200)
            如果 (暂停前已有 == "")
            {
                // 只在"由本次调用制造暂停"时武装防呆网(主循环 10 秒没等到暂停事件就自动 resume)
                MCP命令服务器.待恢复暂停时间 = 取启动时间 ()
            }
            如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "无法制造暂停点(已安排执行点 + Debugger.pause 并等待约6秒仍未收到 Debugger.paused) | 可能原因: 页面没有可执行的JS(about:blank/纯静态页) 或 CDP 通道不可用 | 替代: 先 browser_navigate 到有脚本的页面再暂停, 或用 browser_debugger_flow 一键断点"))
            }
            变量 暂停成功对象 <类型 = YYJSON对象类>
            暂停成功对象.创建自文本 ("{}")
            暂停成功对象.加入逻辑值成员 ("success", 真)
            暂停成功对象.加入文本成员 ("paused", "true")
            暂停成功对象.加入文本成员 ("note", "页面已暂停(暂停点=自动安排的30ms执行点或既有断点) | 看现场: browser_debugger_last_paused / browser_debugger_stack / browser_debugger_evaluate | 恢复: browser_debugger_resume (即使忘了恢复, 后续任意 CDP 工具都会自动 resume 并续等原请求, 不会把实例卡死)")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, 暂停成功对象.到可读文本 (YYJSON格式化选项.压缩)))'''

DESC_OLD = '''"⛔ 已禁用(刻意保留的守卫, 恒失败): Debugger.pause 会**冻结没有 JS 执行点的页面并堵塞 CDP 命令队列**(队列 FIFO —— 后续所有 CDP 命令与自动 resume 都排在它后面, 连锁超时, 连 browser_status 都可能挂), 故本工具**不接受调用并直接给出替代流程** | 正确做法: ①一键断点用 browser_debugger_flow ②手动流程 browser_debugger_enable → browser_debugger_set_breakpoint → 触发页面 → browser_debugger_wait_paused ③要看某个函数被调用时的现场, 用 browser_debugger_flow 的 function 目标或 browser_reverse_* 系列 | 说明书更正(第128轮): 该工具此前**没有注册行**(不在 tools/list 里), 按名调用却真的有效, 属「看不见的守卫」; 现已如实注册, 使拒绝理由与替代方案可被发现"'''

DESC_NEW = '''"可靠暂停页面(随时可用) | 裸发 Debugger.pause 在**没有 JS 执行点的页面**上永不返回, 还会堵塞 CDP 命令队列(FIFO —— 后续命令与自动 resume 全排在它后面, 连锁超时), 故本工具**不裸发**: 先显式启用 Debugger 域 → 用页面自身的 setTimeout 安排一个 30ms 后**必然执行**的语句给 pause 一个落点 → 再 pause 并等 Debugger.paused, 让暂停成为**有界**操作(失败会给出原因与替代, 不会静默堵队列; 另有主循环 10 秒防呆, 未等到暂停事件会自动 resume)。看现场: browser_debugger_last_paused / browser_debugger_stack / browser_debugger_evaluate; 恢复: browser_debugger_resume —— 即使忘了恢复, 后续任意 CDP 工具都会自动 resume 并**续等原请求**, 不会把实例卡死 | 想看某个函数/URL 被调用时的现场, 用 browser_debugger_flow 一键断点更直接"'''


def patch(path, edits, name):
    txt = io.open(path, encoding='utf-8', newline='').read()
    n0 = len(txt.split('\n'))
    for tag, old, new in edits:
        if old in txt:
            assert txt.count(old) == 1, '%s / %s 锚点命中 %d 次' % (name, tag, txt.count(old))
            txt = txt.replace(old, new, 1)
            print('   · %s' % tag)
        else:
            print('   · %s —— 已应用过/未找到, 跳过' % tag)
    print('%s: 行数 %d -> %d' % (name, n0, len(txt.split('\n'))))
    if APPLY:
        io.open(path, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 %s' % os.path.basename(path))


def main():
    print('== 第138轮补丁 (%s) ==' % ('应用' if APPLY else '预演'))
    patch(CORE, [('browser_debugger_pause 改为复用安全暂停', CORE_OLD, CORE_NEW)], 'MCP_Server_Core.wsv')
    patch(SERVER, [('描述改为真实行为', DESC_OLD, DESC_NEW)], 'MCP_Server.wsv')
    if not APPLY:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
