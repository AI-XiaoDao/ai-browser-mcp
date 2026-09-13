# -*- coding: utf-8 -*-
"""把 7 个"需要页面已暂停"的调试工具的守卫改成"先自动制造暂停点"(零前置)。

## 依据(台账实测)
这 7 项在台账里全是 `fail/PREREQ`, 文案统一为
"页面未处于暂停状态 | 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused" ——
即调用方(AI)必须先手工编排一串断点流程才能用, 正是最高目标 A 线要清零的"前置缺失类失败"。

## 为什么现在可以安全地自己制造暂停
原 `browser_debugger_pause` 被禁用的原因是"无JS执行点的页面上 Debugger.pause 永不返回,
且冻结渲染器后堵塞后续CDP命令"。根因是**没有可暂停的执行点**, 而非 pause 不能用 ——
新增的 `MCP命令服务器.确保调试器已暂停` 先安排一个 30ms 后必然执行的语句再 pause,
等到暂停事件(5s 上限), 且 `执行CDP并同步等待` 的"卡死自救"会在超时时自动 resume 兜底;
补过什么经 `auto_prepared` 如实上报。

## 注意
守卫的缩进是 **12 空格**(在 `否则(方法名…)` 分支 + `如果(browser…)` 之内),
第一版脚本按 8 空格写导致一处都没匹配上 —— 本版按实测缩进(12/12/16/12)重写。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")

FAIL = ("无法自动制造暂停点(已安排执行点 + Debugger.pause 并等待5秒仍未收到 Debugger.paused) | "
        "可能原因: 页面没有可执行的JS(纯静态页/about:blank) 或 CDP 通道不可用 | "
        "替代: browser_debugger_flow 一键断点流程")

S = io.open(P, encoding="utf-8").read()
orig = S

# ---- 1) 同构守卫(step_over / step_into / step_out / stack): 12 空格缩进 ----
SAME = ('            如果 (MCP命令服务器.取CDP事件数据JSON ("Debugger.paused") == "")\n'
        '            {\n'
        '                返回 (MCP_响应构建.命令失败 (命令ID, "页面未处于暂停状态 | 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused"))\n'
        '            }')
NEW_SAME = ('            如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)\n'
            '            {\n'
            '                返回 (MCP_响应构建.命令失败 (命令ID, "' + FAIL + '"))\n'
            '            }')
n = S.count(SAME)
if n != 4:
    print("!! 同构守卫命中 %d 处(期望 4: step_over/into/out/stack) -> 中止" % n)
    sys.exit(2)
S = S.replace(SAME, NEW_SAME)
print("同构守卫已替换 %d 处" % n)

# ---- 2) inspect: 未给 call_frame_id 且未暂停时先制造暂停 ----
OLD = ('            如果 (frameId2 == "")\n'
       '            {\n'
       '                变量 rawInspect <类型 = 文本型>')
NEW = ('            如果 (frameId2 == "")\n'
       '            {\n'
       '                // 零前置: 未给帧ID 且页面未暂停时, 先自动制造暂停点(已暂停则立即返回真)\n'
       '                如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)\n'
       '                {\n'
       '                    返回 (MCP_响应构建.命令失败 (命令ID, "' + FAIL + '"))\n'
       '                }\n'
       '                变量 rawInspect <类型 = 文本型>')
if S.count(OLD) != 1:
    print("!! inspect 锚点命中 %d 次(应 1) -> 中止" % S.count(OLD))
    sys.exit(2)
S = S.replace(OLD, NEW)
print("inspect 守卫已替换")

# ---- 3) last_paused: 无暂停事件时先制造再重取 ----
OLD = ('                返回 (MCP_响应构建.命令失败 (命令ID, "尚无 Debugger.paused 事件 | 请先 enable + 断点 + 触发暂停"))\n'
       '            }')
NEW = ('                // 零前置: 没有暂停事件时自动制造一个, 再重取(而不是让调用方先去编排断点)\n'
       '                如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)\n'
       '                {\n'
       '                    返回 (MCP_响应构建.命令失败 (命令ID, "' + FAIL + '"))\n'
       '                }\n'
       '                rawLast = MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")\n'
       '            }')
if S.count(OLD) != 1:
    print("!! last_paused 锚点命中 %d 次(应 1) -> 中止" % S.count(OLD))
    sys.exit(2)
S = S.replace(OLD, NEW)
print("last_paused 守卫已替换")

# ---- 4) script_source: 既未暂停又未给 script_id 时先制造暂停 ----
OLD = ('            如果 (srcCtx == "" && srcCtx2 == "")\n'
       '            {\n'
       '                返回 (MCP_响应构建.命令失败 (命令ID, "未处于暂停状态且未指定 script_id | 请先 debugger_flow / debugger_enable + 断点 + wait_paused"))\n'
       '            }')
NEW = ('            如果 (srcCtx == "" && srcCtx2 == "")\n'
       '            {\n'
       '                // 零前置: 既未暂停又没给 script_id 时, 先自动制造暂停点再继续\n'
       '                // (给了 script_id 的调用方无需暂停, 故不动那条路径)\n'
       '                如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)\n'
       '                {\n'
       '                    返回 (MCP_响应构建.命令失败 (命令ID, "' + FAIL + '"))\n'
       '                }\n'
       '            }')
if S.count(OLD) != 1:
    print("!! script_source 锚点命中 %d 次(应 1) -> 中止" % S.count(OLD))
    sys.exit(2)
S = S.replace(OLD, NEW)
print("script_source 守卫已替换")

io.open(P, "w", encoding="utf-8", newline="\n").write(S)

# ---- 5) 写后自检 ----
chk = io.open(P, encoding="utf-8").read()
calls = chk.count("MCP命令服务器.确保调试器已暂停 (命令ID)")
left = chk.count('"页面未处于暂停状态 | 请先 debugger_flow')
left2 = chk.count("未处于暂停状态且未指定 script_id")
left3 = chk.count("尚无 Debugger.paused 事件")
print("自检 调用数 %d (期望 7)" % calls)
print("自检 残留旧文案: 页面未暂停=%d 脚本源=%d 无暂停事件=%d (三者应均 0)" % (left, left2, left3))
bad = 0
for label, v, want in (("调用数", calls, 7), ("残留 页面未暂停", left, 0),
                       ("残留 脚本源", left2, 0), ("残留 无暂停事件", left3, 0)):
    if v != want:
        print("!! %s = %d, 期望 %d" % (label, v, want))
        bad += 1
# resume 的"无需恢复"必须保留(它不是前置缺失, 而是幂等提示)
if chk.count("页面未处于暂停状态, 无需恢复") != 1:
    print("!! resume 的'无需恢复'提示被误改")
    bad += 1
print("OK" if bad == 0 else "!! %d 项自检未通过" % bad)
sys.exit(1 if bad else 0)
