# -*- coding: utf-8 -*-
r"""第137轮补丁(v2): 让 `browser_reverse_instrument_script` 装上插装后**本会话 JS 通道继续可用**。

## 归因(第137轮 `_audit/probe_iv_timing.py` 走**原始 CDP 通道**量测, 受控可复现)
| 环节 | 实测 |
|---|---|
| A 未装插装: 原始 Runtime.evaluate | 结果 **0.02s** 到达 |
| B 装插装后不 resume | 派发被拦(HTTP 30s 超时), 结果**永不到达** |
| C 同一任务ID: resume 之后**继续等** | resume 本身 0.04s, **原任务ID 的结果 0.00s 就到** |
| D 对照: resume 后**重新派发**一条 | 20s 仍拿不到结果 |

⇒ 暂停发生在渲染器里, 被拦的那条请求**一直挂着**, resume 一发出就立刻完成。故正确修法是
「**resume 后继续等原来那条请求**」, 而不是旧实现的「resume 后重新派发」—— 重派发会**再次**命中同一条
插装/断点(都拦在脚本执行前), 于是又要再 resume 一次, 形成 6~20s 的死循环。

## 补丁内容
1. `MCP_Server.wsv` `执行CDP并同步等待`:
   · 记下**原始预算**(`原始预算`); 装插装时把**首轮**预算压到 900ms(让自救立刻触发);
   · 自救改为: resume → **续等原任务ID**(用剩余预算, 下限 2000ms) → 失败才退回原有的"重派发"兜底;
   · 新增"无暂停记录时把压缩掉的预算**补等**回来" ⇒ 压缩**不会**把"慢命令"变成"提前失败", 总上限不变。
2. `MCP_Server_Reverse.wsv`:
   · install: **在自检之前**置位 `插装已安装`(自检自己就会被这条插装拦停, 否则白等满 3000ms);
   · suppress: 更新被实测推翻的旧 note(「耗时约 45s」「resume/disable 都无法恢复」);
   · remove: **不再提前清标志**(清早了自救预算回到正常值 ⇒ 下一次 execute_js 白等 15s);
     卸载成功才清; 本机未实现该方法时**自动兜底**为 setSkipAllPauses(true)(复用既有 `执行V8CDP命令`)。
3. `MCP_Server.wsv` 工具描述: 第135轮"装上即阻塞、需重启进程"按第137轮实测更正为
   "装上后约 1s/次正常可用", 并写明 suppress / remove 的真实行为。

用法: py -3 _audit\_apply_round137.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
APPLY = '--apply' in sys.argv

# ════════════════════════ MCP_Server.wsv (单倍行距, 用整段文本锚点) ════════════════════════

A1_OLD = '''        // ★ 装了插装时: 把**首次预算**压到 2500ms, 让下面的"卡死自救"(超时且有未处理 Debugger.paused
        //   → 自动 resume + 重试)在 2.5 秒内触发 —— 实测不改这里, 插装装完后 execute_js 要 60s 才超时失败;
        //   改了之后同一条请求会走"早超时 → 自救 resume → 重试成功"的路。(普通断点调试不受影响: 本标志仅由插装工具置位)
        如果 (插装已安装 && 最大毫秒 > 900)
        {
            最大毫秒 = 900
        }'''
A1_NEW = '''        变量 原始预算 <类型 = 整数>
        原始预算 = 最大毫秒
        // ★ 装了插装(Debugger.setInstrumentationBreakpoint)时: 我们自己的 Runtime.evaluate 会被**自己的插装**
        //   拦停 ⇒ 按正常预算只会等到超时失败。故把**首轮**预算压到 900ms, 让下面的"卡死自救"立刻触发。
        //   实测依据(第137轮, _audit/probe_iv_timing.py 走原始 CDP 通道量测):
        //   · 不压预算: 装完插装后 execute_js 要 60s 才超时失败(通道被自己的插装拦住);
        //   · 压到 2500ms: "等 2.5s → resume → 重新派发"总耗时 ~10s, 超过工具层 5s 同步预算 ⇒ 调用方仍是"操作超时(5s)";
        //   · 压到 900ms 且自救改为"resume 后**续等原请求**": 整条请求约 1s 返回**成功**。
        //   注意: 压缩只是"把等待拆成两段" —— 下面在无暂停记录时会把剩余预算**补等**回来, 故总上限不变。
        如果 (插装已安装 && 最大毫秒 > 900)
        {
            最大毫秒 = 900
        }'''

A2_OLD = '''                    执行CDP命令_带参数 (命令ID + "_rsq", "Debugger.resume", "{}")
                    同步等待异步任务 (命令ID + "_rsq", 5000)
                    清除CDP事件记录 ("Debugger.paused")
                    执行CDP命令_带参数 (命令ID + "_rt2", cdpMethod, paramsJSON文本)
                    变量 解卡结果 <类型 = 文本型>
                    解卡结果 = 同步等待异步任务 (命令ID + "_rt2", 最大毫秒)
                    如果 (CDP同步结果是否成功 (解卡结果))
                    {
                        MCP_响应构建.记录自动处理 ("Debugger.resume(页面原卡在断点, 已自动恢复并重试成功)")
                        返回 (解卡结果)
                    }
                    返回 (解卡结果)
                }'''
A2_NEW = '''                    执行CDP命令_带参数 (命令ID + "_rsq", "Debugger.resume", "{}")
                    同步等待异步任务 (命令ID + "_rsq", 3000)
                    清除CDP事件记录 ("Debugger.paused")
                    // ★ resume 之后要**继续等原来那条请求**, 而不是重新派发(第137轮原始 CDP 通道实测):
                    //   暂停发生在渲染器里 —— 我们那条 CDP 请求一直挂在渲染器队列上, resume 一发出它就**立刻**完成
                    //   (实测: resume 0.04s, 原任务ID 的结果 0.00s 就到); 而"重新派发"会**再次命中同一条**
                    //   插装/断点(都拦在脚本执行前), 于是又要再 resume 一次 —— 实测重派发路径 20s 都拿不到结果。
                    变量 救活预算 <类型 = 整数>
                    救活预算 = 原始预算 - 最大毫秒
                    如果 (救活预算 < 2000)
                    {
                        救活预算 = 2000
                    }
                    变量 救活结果 <类型 = 文本型>
                    救活结果 = 同步等待异步任务 (命令ID, 救活预算)
                    如果 (CDP同步结果是否成功 (救活结果))
                    {
                        MCP_响应构建.记录自动处理 ("Debugger.resume(页面原卡在断点/插装, 已自动恢复并续等原请求成功)")
                        返回 (救活结果)
                    }
                    // 续等仍未果(该请求确实已丢失)才退回"重新派发"兜底
                    执行CDP命令_带参数 (命令ID + "_rt2", cdpMethod, paramsJSON文本)
                    变量 解卡结果 <类型 = 文本型>
                    解卡结果 = 同步等待异步任务 (命令ID + "_rt2", 最大毫秒)
                    如果 (CDP同步结果是否成功 (解卡结果))
                    {
                        MCP_响应构建.记录自动处理 ("Debugger.resume(页面原卡在断点, 已自动恢复并重试成功)")
                        返回 (解卡结果)
                    }
                    返回 (解卡结果)
                }
                // ── 无暂停记录: 说明这条命令只是**慢** —— 把压缩掉的预算补回来 ──
                // 判据: 首轮 900ms 超时但页面并未暂停 ⇒ 压缩绝不能变成"提前失败"。
                // 补等剩余预算后, 总等待上限与压缩前**完全一致**(对未被拦停的慢命令零行为变化)。
                如果 (最大毫秒 < 原始预算)
                {
                    变量 补等结果 <类型 = 文本型>
                    补等结果 = 同步等待异步任务 (命令ID, 原始预算 - 最大毫秒)
                    如果 (CDP同步结果是否成功 (补等结果))
                    {
                        返回 (补等结果)
                    }
                }'''

A3_OLD = '''⚠ 实测更正(本机CEF构建): 装上后本会话的 **JS 通道即被阻塞** —— browser_execute_js / browser_debugger_last_paused 等会 30s 超时(browser_status 仍正常, 它走原生不经 CDP)。**根因已测清**: 本项目的 JS 通道就是 Runtime.evaluate(它本身就是一次脚本执行), 而被装上的插装正是拦「执行脚本」的 -> 请求被自己的插装拦住并暂停, 那条 CDP 请求永不返回, 单条队列随之被占。**注意: 这不是自检探针造成的** —— 实测把自检关掉(verify:false)装入后**同样卡死**, 卡死来自「装上插装」本身。**恢复办法(第135轮受控复核更正)**: 实测 `action=suppress` **已不能恢复**(返回 `setSkipAllPauses 失败: timeout`, 之后 execute_js 仍 35 秒超时报错), `browser_debugger_resume` / `disable` 同样无效 ⇒ **安装后请准备重启 AI-Fbowser-Mcp.exe**。旧文案称「suppress 可恢复(约45s)」已被本轮实测推翻, 不要再依赖它。原来的「分析完务必 resume」在本机不成立, 已按实测更正。故使用本工具时请**准备好随后重启进程**(旧文案说的 action=suppress 止血已不再有效); 只是读取源码请改用 browser_reverse_search_script / browser_reverse_detect_traps'''
A3_NEW = '''**装上后本会话 JS 通道仍可继续用(第137轮实测, 已推翻第135轮"装上即阻塞需重启"的结论)**: 插装拦的是「执行脚本」, 而本项目的 JS 通道就是 Runtime.evaluate(它本身就是一次脚本执行) —— 故每条请求会先被自己的插装暂停一次。第137轮把项目既有的「卡死自救」改成 **resume 后继续等原来那条请求**(不再重新派发: 重派发会**再次**命中同一条插装, 实测 20s 都拿不到结果; 续等原请求则实测 resume 0.04s、结果 0.00s 就返回)。装上后 browser_execute_js / browser_dom_query 实测约 1s 正常返回, **不需要重启进程**。action=suppress 走 Debugger.setSkipAllPauses(实测 0.04s 级返回, 页面不再被任何暂停拦停) | action=remove 先试原生卸载, 本机 Chromium **未实现** Debugger.removeInstrumentationBreakpoint(实测报 wasn't found), 会自动**兜底**成 setSkipAllPauses(true) 并在 note 里如实说明: 对使用者效果等价(页面不再卡住), 差别只是插装定义仍留在内核、重启进程后彻底消失。只是读取源码请改用 browser_reverse_search_script / browser_reverse_detect_traps'''

A4_OLD = '''属性项JSON ("confirm", "boolean", "**install 的硬前置**: 不传 confirm=true 会被明确拒绝(实测装上后本会话 JS 通道即被阻塞, 需随后 action=suppress 止血)")'''
A4_NEW = '''属性项JSON ("confirm", "boolean", "**install 的硬前置**: 不传 confirm=true 会被明确拒绝(装上后本会话 JS 通道经卡死自救继续可用, 实测约 1s/次, 无需重启进程)")'''

# ════════════════ MCP_Server_Reverse.wsv (双倍行距: 内容行之间夹空行 ⇒ 用**整行**锚点) ════════════════


def read_lines(path):
    txt = io.open(path, encoding='utf-8', newline='').read()
    has_cr = '\r' in txt
    return txt.split('\n'), has_cr


def find1(lines, sub, tag):
    hits = [i for i, l in enumerate(lines) if sub in l]
    assert len(hits) == 1, '%s: 锚点命中 %d 次 %r' % (tag, len(hits), sub)
    return hits[0]


def insert_block(lines, after_idx, block):
    """在 after_idx 之后插入 block(内容行 + 空行交替), 且不制造连续空行。"""
    out = []
    for c in block:
        out.append(c)
        out.append('')
    if out and out[-1] == '' and after_idx + 1 < len(lines) and lines[after_idx + 1] == '':
        out.pop()
    lines[after_idx + 1:after_idx + 1] = out
    return lines


def main():
    print('== 第137轮补丁 v2 (%s) ==' % ('应用' if APPLY else '预演'))

    # ── ① MCP_Server.wsv ──
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    n0 = len(txt.split('\n'))
    for tag, old, new in [('预算: 记原始预算 + 压到 900ms', A1_OLD, A1_NEW),
                          ('自救: resume 后**续等原请求**', A2_OLD, A2_NEW),
                          ('描述: 第137轮实测更正', A3_OLD, A3_NEW),
                          ('描述: confirm 参数更正', A4_OLD, A4_NEW)]:
        if old in txt:
            assert txt.count(old) == 1, '%s 锚点命中 %d 次' % (tag, txt.count(old))
            txt = txt.replace(old, new, 1)
            print('   · %s' % tag)
        elif new in txt:
            print('   · %s —— 已应用过, 跳过' % tag)
        else:
            raise AssertionError('MCP_Server.wsv / %s 锚点未找到' % tag)
    print('MCP_Server.wsv: 行数 %d -> %d' % (n0, len(txt.split('\n'))))
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 MCP_Server.wsv')

    # ── ② MCP_Server_Reverse.wsv ──
    lines, has_cr = read_lines(REV)
    n0 = len(lines)

    # R1: 把 install 的置位从"自检之后"挪到"自检之前"
    i_ins = find1(lines, 'ivInsRes = MCP命令服务器.执行CDP并同步等待 (命令ID + "_iv", "Debugger.setInstrumentationBreakpoint"', 'R1 装入调用')
    i_flag_late = find1(lines, 'MCP命令服务器.插装已安装 = 真', 'R1 旧置位')
    assert i_flag_late > i_ins, 'R1: 旧置位应在装入调用之后'
    # 先删旧置位(连同它带来的多余空行: 若下一行已是空行则一并删)
    del lines[i_flag_late]
    if i_flag_late < len(lines) and lines[i_flag_late] == '' and lines[i_flag_late - 1] == '':
        del lines[i_flag_late]
    if i_ins > i_flag_late:
        i_ins -= 1
        if i_ins < len(lines) and lines[i_ins] == '':
            pass
    insert_block(lines, i_ins, ['                // 立刻置位(必须在下面的**自检之前**): 自检本身就是一条会被这条插装拦停的 evaluate,',
                                '                // 置位后"首轮预算压缩 + resume 后续等"才生效, 自检才不会白等满 3000ms。',
                                '                MCP命令服务器.插装已安装 = 真'])
    print('   · R1 install: 置位提前到自检之前')

    # R2: suppress note 更正
    i_sup = find1(lines, '已跳过全部暂停: 插装仍在但不再拦截页面', 'R2 suppress note')
    lines[i_sup] = ('                ivSupOut.加入文本成员 ("note", "已跳过全部暂停: 插装仍在但不再拦截页面, '
                    '本会话的 JS 通道已恢复(实测 setSkipAllPauses 本身 0.04s 级返回) | '
                    '恢复拦截: browser_reverse_skip_pauses skip=false")')
    print('   · R2 suppress: note 按实测更正')

    # R3: remove 分支: 改注释 + 删掉"提前清标志"
    i_rm0 = find1(lines, '// remove: 先尝试原生卸载(为兼容其它Chromium版本)', 'R3 remove 首行注释')
    lines[i_rm0] = ('            // remove: 先尝试原生卸载(为兼容其它Chromium版本), 本机**未实现**该方法时自动兜底为 '
                    'setSkipAllPauses(true) ——')
    i_rm = find1(lines, '// remove 是卸载/清理路径: 先清标志', 'R3 remove 注释')
    lines[i_rm] = ('            // ★ 标志只在**确认拦停已解除**之后才清零(第137轮修正): 卸载与兜底都失败时插装依然拦着页面,')
    insert_block(lines, i_rm, ['            //   提前清零会让自救预算回到正常值 ⇒ 下一次 execute_js 又要白等满 15s。'])
    i_flag_rm = None
    for j in range(i_rm, min(i_rm + 6, len(lines))):
        if lines[j].strip() == 'MCP命令服务器.插装已安装 = 假':
            i_flag_rm = j
            break
    assert i_flag_rm is not None, 'R3: 未找到 remove 分支里被提前清掉的标志行'
    del lines[i_flag_rm]
    print('   · R3 remove: 不再提前清标志')

    # R4: remove 成功路径补上清标志
    i_rmsuc = find1(lines, 'ivRmOut.加入文本成员 ("note", "已卸载[', 'R4 remove 成功 note')
    insert_block(lines, i_rmsuc - 1, ['                MCP命令服务器.插装已安装 = 假'])
    print('   · R4 remove: 成功路径清标志')

    # R5: remove 失败 → 复用 setSkipAllPauses 兜底
    i_rmfail = find1(lines, '本机Chromium无法单独卸载插装断点(', 'R5 remove 失败返回')
    lines[i_rmfail:i_rmfail + 1] = [
        '            // 本机绑定的 Chromium **没有实现** Debugger.removeInstrumentationBreakpoint',
        '',
        '            // (实测错误原文: "Debugger.removeInstrumentationBreakpoint wasn\'t found"), 故做**等价兜底**:',
        '',
        '            // 复用既有的 setSkipAllPauses 出口(与 browser_reverse_skip_pauses 同一个 `执行V8CDP命令`, 不另写一份实现),',
        '',
        '            // 让页面不再被任何暂停(含本插装)拦停 —— 对使用者效果等价: JS 通道恢复、页面不再被卡住;',
        '',
        '            // 差别只是插装定义仍留在内核(不影响使用, 重启进程后彻底消失), 这一点由 note 如实说明。',
        '',
        '            变量 ivRmFbRes <类型 = 文本型>',
        '',
        '            ivRmFbRes = 执行V8CDP命令 (命令ID, "Debugger.setSkipAllPauses", "{\\"skip\\":true}", "本机 Chromium 未实现单独卸载插装断点(removeInstrumentationBreakpoint wasn\'t found), 已自动兜底为 setSkipAllPauses(true): 页面不再被任何暂停拦停, 本会话 JS 通道恢复 | 差别: 插装定义仍留在内核(不影响使用, 重启进程后彻底消失) | 恢复拦截: browser_reverse_skip_pauses skip=false")',
        '',
        '            如果 (MCP命令服务器.CDP同步结果是否成功 (ivRmFbRes))',
        '',
        '            {',
        '',
        '                MCP命令服务器.插装已安装 = 假',
        '',
        '                返回 (ivRmFbRes)',
        '',
        '            }',
        '',
        '            返回 (MCP_响应构建.命令失败 (命令ID, "插装无法解除: 本机 Chromium 未实现单独卸载(" + MCP命令服务器.取CDP同步结果错误 (ivRmRes) + "), 且兜底 setSkipAllPauses 也失败 | 立刻止血: action=suppress | 彻底清除: 重启 AI-FBowser-Mcp.exe"))',
    ]
    print('   · R5 remove: 失败 → setSkipAllPauses 兜底')

    print('MCP_Server_Reverse.wsv: 行数 %d -> %d (CR=%s)' % (n0, len(lines), has_cr))
    # ── 回读校验: 把改动点原样打出来(整行断言, 不靠"名字出现过"这种弱判据) ──
    for tag, sub in [('R1 自检前置位', '立刻置位(必须在下面的**自检之前**)'),
                     ('R2 suppress note', '实测 setSkipAllPauses 本身 0.04s 级返回'),
                     ('R3 remove 不提前清标志', '提前清零会让自救预算回到正常值'),
                     ('R4 remove 成功清标志', 'ivRmOut.加入文本成员 ("note", "已卸载['),
                     ('R5 remove 兜底', 'ivRmFbRes = 执行V8CDP命令 (命令ID, "Debugger.setSkipAllPauses"')]:
        i = find1(lines, sub, '回读 ' + tag)
        print('   · 回读 %s @ 第%d行' % (tag, i + 1))
        for j in range(max(0, i - 1), min(len(lines), i + 2)):
            print('        %s' % lines[j][:150])
    if APPLY:
        io.open(REV, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
        print('   ✔ 已写入 MCP_Server_Reverse.wsv')
    else:
        print('\n(预演完成; 加 --apply 写入)')


if __name__ == '__main__':
    main()
