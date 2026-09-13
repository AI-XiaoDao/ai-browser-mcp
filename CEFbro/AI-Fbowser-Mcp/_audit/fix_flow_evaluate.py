# -*- coding: utf-8 -*-
"""实施 flow/evaluate 改动清单(F2 + F3 + E1 + E2 + E3a)。全部锚点先断言唯一, 再写。

来源: _audit/_flow_evaluate_fix_plan.md（只读复核, 逐字锚点, 已由我复核行号与内容）。

包含:
  F2  flow 默认等待 45000 -> 12000 (+ schema 文案)
  F3  flow 超时失败体: 保留 step/error, **追加** waited_ms/reason/hint
  E1  evaluate 缺 call_frame_id 时复用 inspect 的活帧获取(不新增方法, 与仓库"不新增导出符号"一致)
  E2  evaluate schema: call_frame_id 不再必填 + 文案同步(否则严格客户端永不发出空帧调用)
  E3a 解析Debugger求值结果: 失败原因 key 从 "message" 改为回退链 message->error->result
      (原来读的键根本不存在 -> 任何失败都被吞成 {"ok":false,"error":""}), 并给帧失效加行动指引

约定: 脚本内用 `@Q@` 代表两字符 `\\"`(反斜杠+引号), 避免转义歧义。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', 'flow与evaluate修复-写入前')
B = chr(92)
Q = chr(34)
ESC = B + Q          # \" 两个字符
PLACE = '@Q@'

# ---------------- F2: flow 默认等待 45000 -> 12000 ----------------
F2_OLD = '\n'.join([
    '        变量 maxMs <类型 = 整数>',
    '        maxMs = yyjson取整数 (参数JSON, "max_ms")',
    '        如果 (maxMs == 0)',
    '        {',
    '            maxMs = 45000',
    '        }',
])
F2_NEW = '\n'.join([
    '        变量 maxMs <类型 = 整数>',
    '        maxMs = yyjson取整数 (参数JSON, "max_ms")',
    '        如果 (maxMs == 0)',
    '        {',
    '            // 原默认 45000ms 远超常见客户端耐心(台账实测客户端 15s 就放弃), 结果是',
    '            // "客户端先超时 + 服务端还在等" —— 调用方只看到 timed out, 看不到任何原因。',
    '            // 压到 12000ms(与 browser_debugger_auto 的同类决定一致): 让服务端在客户端放弃之前',
    '            // 给出明确结论。需要更久请显式传 max_ms。',
    '            maxMs = 12000',
    '        }',
])

# ---------------- F2b: flow schema 文案 ----------------
F2B_OLD = '属性项JSON ("max_ms", "integer", "等待暂停毫秒")'
F2B_NEW = '属性项JSON ("max_ms", "integer", "等待暂停毫秒(默认12000; 客户端自身超时更短时请调低)")'

# ---------------- F3: flow 超时失败体 ----------------
F3_OLD = '\n'.join([
    '        如果 (pausedRaw == "")',
    '        {',
    '            返回 (DebuggerFlow失败返回 (命令ID, "{@Q@ok@Q@:false,@Q@step@Q@:@Q@wait_paused@Q@,@Q@error@Q@:@Q@timeout@Q@,@Q@breakpoint@Q@:@Q@" + MCP_响应构建.JSON转义文本 (bpRegex) + "@Q@}"))',
    '        }',
]).replace(PLACE, ESC)
F3_NEW = '\n'.join([
    '        如果 (pausedRaw == "")',
    '        {',
    '            // 修(失败不给原因): 原返回体只有 error:"timeout", 调用方看不出等了多久、为什么没等到。',
    '            // 保留 step/error 两个既有键值不动(分派层按键值前缀分类), 只**追加**原因与可行动提示。',
    '            变量 flow等待说明 <类型 = 文本型>',
    '            flow等待说明 = "等待 Debugger.paused 超时(" + 到文本 (maxMs) + "ms)"',
    '            如果 (navUrl == "")',
    '            {',
    '                flow等待说明 = flow等待说明 + " | 未传 url: 本工具不会导航, 只有当前页面自己执行到断点位置才可能命中"',
    '            }',
    '            否则',
    '            {',
    '                flow等待说明 = flow等待说明 + " | 已导航到 " + navUrl + ", 但该窗口内脚本未执行到断点位置"',
    '            }',
    '            返回 (DebuggerFlow失败返回 (命令ID, "{@Q@ok@Q@:false,@Q@step@Q@:@Q@wait_paused@Q@,@Q@error@Q@:@Q@timeout@Q@,@Q@breakpoint@Q@:@Q@" + MCP_响应构建.JSON转义文本 (bpRegex) + "@Q@,@Q@waited_ms@Q@:" + 到文本 (maxMs) + ",@Q@reason@Q@:@Q@" + MCP_响应构建.JSON转义文本 (flow等待说明) + "@Q@,@Q@hint@Q@:@Q@可行动: ①用 browser_reverse_get_possible_breakpoints 确认该脚本真正可下断的行列(混淆脚本常整包压成一行, 按行下断必然 0 位置) ②确认 url_regex 能匹配到目标脚本 ③需要更久请显式传 max_ms@Q@}"))',
    '        }',
]).replace(PLACE, ESC)

# ---------------- E1: evaluate 缺帧 ID 时自动取活帧 ----------------
E1_OLD = '\n'.join([
    '            变量 frameId <类型 = 文本型>',
    '            frameId = MCP命令服务器.yyjson取文本 (参数JSON, "call_frame_id")',
    '            变量 expr <类型 = 文本型>',
    '            expr = MCP命令服务器.yyjson取文本 (参数JSON, "expression")',
    '            如果 (frameId == "" || expr == "")',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "call_frame_id和expression " + MCP_常量.错误_缺少参数))',
    '            }',
])
E1_NEW = '\n'.join([
    '            变量 frameId <类型 = 文本型>',
    '            frameId = MCP命令服务器.yyjson取文本 (参数JSON, "call_frame_id")',
    '            变量 expr <类型 = 文本型>',
    '            expr = MCP命令服务器.yyjson取文本 (参数JSON, "expression")',
    '            如果 (expr == "")',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "expression " + MCP_常量.错误_缺少参数))',
    '            }',
    '            如果 (frameId == "")',
    '            {',
    '                // ★ 零前置(与 browser_debugger_inspect 同源逻辑): 未给帧ID 时自动取"当前活帧" ——',
    '                //   已暂停则直接复用, 未暂停则先制造暂停点(经 auto_prepared 如实上报),',
    '                //   再从最近一次 Debugger.paused 读 call_frame_id。',
    '                //   原实现在缺帧 ID 时直接失败("call_frame_id和expression 参数不能为空"),',
    '                //   而 AI 调用方最自然的用法就是"给个表达式让我看看" —— 于是第一次调用必失败。',
    '                如果 (MCP命令服务器.确保调试器已暂停 (命令ID) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "未给 call_frame_id 且无法自动制造暂停点(已安排执行点 + Debugger.pause 并等待5秒仍未收到 Debugger.paused) | 可能原因: 页面没有可执行的JS(纯静态页/about:blank) 或 CDP 通道不可用 | 可行动: browser_debugger_wait_paused / browser_debugger_last_paused 取帧后立即重试, 或用 browser_debugger_inspect"))',
    '                }',
    '                变量 rawEvPaused <类型 = 文本型>',
    '                rawEvPaused = MCP命令服务器.取CDP事件数据JSON ("Debugger.paused")',
    '                如果 (rawEvPaused != "")',
    '                {',
    '                    变量 evPauseSummary <类型 = 文本型>',
    '                    evPauseSummary = MCP命令服务器.解析Debugger暂停摘要 (rawEvPaused)',
    '                    变量 evPauseObj <类型 = YYJSON只读对象类>',
    '                    如果 (evPauseObj.创建自文本 (evPauseSummary))',
    '                    {',
    '                        frameId = MCP命令服务器.yyjson取文本 (evPauseObj, "call_frame_id")',
    '                    }',
    '                }',
    '            }',
    '            如果 (frameId == "")',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "无法取得活帧 call_frame_id | 可行动: browser_debugger_wait_paused 或 browser_debugger_last_paused 取帧后立即重试"))',
    '            }',
])

# ---------------- E2: evaluate schema ----------------
E2A_OLD = '属性项JSON ("call_frame_id", "text", "帧ID")'
E2A_NEW = '属性项JSON ("call_frame_id", "text", "帧ID(空=自动取最近暂停的活帧, 会自动制造暂停点)")'
E2B_OLD = ('"@Q@call_frame_id@Q@,@Q@expression@Q@"').replace(PLACE, ESC)
E2B_NEW = ('"@Q@expression@Q@"').replace(PLACE, ESC)

# ---------------- E3a: 求值失败原因不再被吞成空串 ----------------
E3_OLD = '\n'.join([
    '        如果 (yyjson取逻辑 (包装, "success") == 假)',
    '        {',
    '            返回 ("{@Q@ok@Q@:false,@Q@error@Q@:@Q@" + MCP_响应构建.JSON转义文本 (yyjson取文本 (包装, "message")) + "@Q@}")',
    '        }',
]).replace(PLACE, ESC)
E3_NEW = '\n'.join([
    '        如果 (yyjson取逻辑 (包装, "success") == 假)',
    '        {',
    '            // ★ 修(失败原因被吞): 原来只读包装里的 "message" —— 但写入失败原因的是 处理CDP响应,',
    '            //   它写的键是 "error"(失败) / "result"(成功), **从来没有 "message"**;',
    '            //   于是任何真实失败都被翻译成 {"ok":false,"error":""}, 调用方看不到原因。',
    '            变量 求值失败原因 <类型 = 文本型>',
    '            求值失败原因 = yyjson取文本 (包装, "message")',
    '            如果 (求值失败原因 == "")',
    '            {',
    '                求值失败原因 = yyjson取文本 (包装, "error")',
    '            }',
    '            如果 (求值失败原因 == "")',
    '            {',
    '                求值失败原因 = yyjson取文本 (包装, "result")',
    '            }',
    '            // 把"帧 ID 失效"翻译成可行动提示(帧 ID 是 CDP 的不透明句柄, 工具无法修复调用方给的旧帧,',
    '            // 只能说明它从哪来、为什么失效 —— 这是"让失败可行动", 不是"让它成功")。',
    '            如果 (寻找文本 (求值失败原因, "Invalid call frame id", 0, 假) != -1)',
    '            {',
    '                求值失败原因 = 求值失败原因 + " | call_frame_id 与当前暂停点绑定: 页面 resume 之后立即失效 —— 而 browser_debugger_flow / browser_debugger_auto 默认 resume:true, 它们返回体里的 paused.call_frame_id 在返回时通常已失效 | 取活帧: browser_debugger_wait_paused 或 browser_debugger_last_paused, 拿到后立即 evaluate; 也可以不传 call_frame_id(本工具会自动取活帧)"',
    '            }',
    '            如果 (求值失败原因 == "")',
    '            {',
    '                求值失败原因 = "cdp_failed"',
    '            }',
    '            返回 ("{@Q@ok@Q@:false,@Q@error@Q@:@Q@" + MCP_响应构建.JSON转义文本 (求值失败原因) + "@Q@}")',
    '        }',
]).replace(PLACE, ESC)

EDITS = [
    ('F2  flow 默认等待', SRV, F2_OLD, F2_NEW),
    ('F2b flow schema', SRV, F2B_OLD, F2B_NEW),
    ('F3  flow 超时原因', SRV, F3_OLD, F3_NEW),
    ('E1  evaluate 活帧', CORE, E1_OLD, E1_NEW),
    ('E2a schema 文案', SRV, E2A_OLD, E2A_NEW),
    ('E2b schema 必填', SRV, E2B_OLD, E2B_NEW),
    ('E3a 求值失败原因', SRV, E3_OLD, E3_NEW),
]


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    texts = {SRV: rd(SRV), CORE: rd(CORE)}
    for label, path, old, new in EDITS:
        n = texts[path].count(old)
        print("[%-18s] %s 中出现 %d 次" % (label, os.path.basename(path), n))
        if n != 1:
            print("   !! 预期 1 次, 中止(不改任何文件)")
            print("   锚点前 120 字符: %r" % old[:120])
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, CORE):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    for label, path, old, new in EDITS:
        texts[path] = texts[path].replace(old, new)
    for p, t in texts.items():
        wr(p, t)
    print("OK: 7 处替换完成")
    for p in (SRV, CORE):
        with io.open(p, 'rb') as f:
            raw = f.read()
        print("复核 %-22s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    print("残留检查: maxMs = 45000 -> %s ; 读 message 的旧写法 -> %s"
          % ('maxMs = 45000' in texts[SRV],
             'MCP_响应构建.JSON转义文本 (yyjson取文本 (包装, ' + Q + 'message' + Q + '))' in texts[SRV]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
