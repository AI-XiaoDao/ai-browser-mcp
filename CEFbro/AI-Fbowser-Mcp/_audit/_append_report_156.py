# -*- coding: utf-8 -*-
r"""第136轮: 把"让 install 可稳定连续使用"的**实现设计与锚点**落进 `_gap_verified.md`, 并追加报告 ## 156。

本轮背景(用户诉求): "确保所有显示的 MCP 能力都可以稳定正常执行功能"。
上一轮已完成: 3 条"刻意设计失败"逐条受控实测 → 三个工具按 schema 传参**都能成功**, 台账 323/323 通过 / 0 未通过;
并订正了一处被推翻的旧文案(suppress 已不能恢复)。
本轮要解决的是**真正的能力限制**: `browser_reverse_instrument_script` 装上插装后本会话 JS 通道被自己拦住
(execute_js 60s 超时) —— 目标: 让它变成"可用但慢"(~2-3 秒), 从而可连续使用。

设计(已有先例可复用, 不重复造轮子):
  1) 复用既有的**卡死自救**: `执行CDP并同步等待` 在"等待超时 **且** 存在未处理 `Debugger.paused`"时
     会自动 `Debugger.resume` 并重试一次(第123轮已实测可救活会话);
  2) 现在缺的只是"**让它早点触发**": 插装装上后, 我们自己的 `Runtime.evaluate` 正是被拦停的那条请求,
     而默认预算(8~30s)要等满才自救 ⇒ 表现是"超时报错"。做法: 新增静态标志 `插装已安装`
     (装 `Debugger.setInstrumentationBreakpoint` 时置真, `setSkipAllPauses`/remove 时置假),
     在 `执行CDP并同步等待` 里当该标志为真时**把首次预算压到 ~2500ms**, 于是自救在 2.5 秒内发生,
     被拦的 evaluate 随 resume 返回, 随后重试即成功。
  3) 安全边界: 只在该标志为真时生效(普通断点调试不受影响); 进一步可用 `Debugger.paused` 的 `reason`
     字段(仅 `instrumentation`)再收窄, 需在实现时按本机返回体核实字段名后再用。

锚点(实现时按符号名 grep 复核, 不要按行号):
  · `MCP_Server.wsv` 静态变量区(与 `CDP映射清理计数` 同一块) → 加 `插装已安装`;
  · `MCP_Server.wsv` 方法 `执行CDP并同步等待` 的 `同步等待异步任务 (命令ID, 最大毫秒)` 之前 → 按标志压预算;
  · `MCP_Server_Reverse.wsv` 中 `Debugger.setInstrumentationBreakpoint` 调用处(现见 :314 附近) → 置真;
    `Debugger.setSkipAllPauses` / remove 分支 → 置假。
验收标准(下一轮):
  ① install(confirm:true) 成功; ② 随后 `browser_execute_js` **成功且耗时 < 5s**(今天实测为 60s 超时失败);
  ③ 连续 3 次 execute_js 都成功(证明可连续使用); ④ `action=remove` 后通道恢复 0.03s 级;
  ⑤ 快检 56/56; ⑥ 若 ② 做不到, 如实记录为"仍不可逆"并保留现有描述。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 156. 第136轮：把"插装装上就废会话"的**真实能力限制**定了实现方案（含锚点与验收标准）

### 156.1 现状（第135轮受控实测，不是推测）
`browser_reverse_instrument_script {action:install, confirm:true}` **能成功**（6.49s，带 `auto_prepared: Debugger.enable`），
但装上之后：`browser_execute_js` **60s 超时报错**、`browser_dom_query` 30.63s 报错，且 `action=suppress`
返回 `setSkipAllPauses 失败: timeout`、之后仍 35.11s 报错 —— 即**本会话 JS 通道被打死，只能重启**。
用户的要求是"所有显示出来的能力都能稳定正常执行"，所以这一条必须往下做，而不是只写文档。

### 156.2 根因与可复用件
- 根因（第123轮已测清）：本项目的 JS 通道就是 `Runtime.evaluate`（本身是一次脚本执行），
  而插装正是"拦在每个脚本执行之前" ⇒ **我们自己的请求被自己的插装拦住并暂停**，那条 CDP 请求永不返回、队列被占。
- 项目已有**卡死自救**：`执行CDP并同步等待` 在"等待超时 **且** 存在未处理 `Debugger.paused`"时自动
  `Debugger.resume` 并重试一次（第123轮实测能救活被冻结的会话）。
  ⇒ 缺的只是"**让它早点触发**"：默认预算 8~30s 要等满才自救，表现就是超时失败。

### 156.3 实现方案（下一轮执行，锚点已核实存在）
1. `MCP_Server.wsv` 静态变量区（与 `CDP映射清理计数` 同块）新增 **`插装已安装`** 标志；
2. `MCP_Server_Reverse.wsv` 中 `Debugger.setInstrumentationBreakpoint` 调用处置**真**，
   `Debugger.setSkipAllPauses` / remove 分支置**假**；
3. `MCP_Server.wsv` 的 `执行CDP并同步等待`：当该标志为真时把**首次等待预算压到约 2500ms**，
   于是自救在 2.5 秒内发生、被拦的 evaluate 随 resume 返回，重试即成功；
4. 安全边界：仅在该标志为真时生效（普通断点调试路径不受影响）；实现时再按本机 `Debugger.paused`
   返回体核实是否带 `reason`（若有 `instrumentation` 可进一步收窄）。

### 156.4 验收标准（下一轮，缺一不算完成）
① install 成功；② 随后 `browser_execute_js` **成功且 < 5s**（今天是 60s 超时失败）；
③ 连续 3 次 execute_js 均成功（证明可连续使用，而不是只能跑一次）；④ `action=remove` 后通道回到 0.03s 级；
⑤ 快检 56/56；⑥ 若 ② 无法达成，如实记录"仍不可逆"并保留现有描述，不得含糊过关。

### 156.5 状态
工具 **323**；台账 **323/323 = 323 通过 / 0 未通过**（第135轮已把 3 条刻意设计失败改为受控实测条目）；
快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
本轮不新增代码改动，只把上述方案与锚点写入台账（`_audit/_gap_verified.md`），供下一轮直接实施。
'''


def main():
    g = io.open(GAP, encoding='utf-8').read()
    if '## 156' in g or '插装已安装' in g:
        print('gap 已含该方案')
    else:
        plan = ('\n## 五、第136轮新增：让 `browser_reverse_instrument_script` 可连续使用的实现方案\n\n'
                '目标：把"装上插装后本会话 JS 通道被打死（execute_js 60s 超时，只能重启）"变成**可用但慢（~2-3 秒）**。\n\n'
                '做法（复用既有"卡死自救"，不重复造轮子）：\n'
                '1. `MCP_Server.wsv` 静态区新增标志 **`插装已安装`**；\n'
                '2. `MCP_Server_Reverse.wsv`：`Debugger.setInstrumentationBreakpoint` 处置真，'
                '`Debugger.setSkipAllPauses`/remove 处置假；\n'
                '3. `MCP_Server.wsv` 的 `执行CDP并同步等待`：该标志为真时把**首次预算压到 ~2500ms**，'
                '使自救（超时且有未处理 `Debugger.paused` → 自动 resume + 重试）在 2.5s 内发生；\n'
                '4. 边界：仅在标志为真时生效；实现时按本机 `Debugger.paused` 返回体核实是否含 `reason` 以进一步收窄。\n\n'
                '验收：①install 成功 ②随后 execute_js **成功且 <5s** ③连续 3 次成功 ④remove 后回到 0.03s 级 '
                '⑤快检 56/56 ⑥做不到就如实保留"不可逆"结论。\n\n'
                '锚点一律**按符号名 grep 复核**，不要按行号（本文件行号会漂）。\n')
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g.rstrip('\n') + '\n' + plan)
        print('_gap_verified.md: 已写入实现方案与验收标准')
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 156.' in text:
        text = text[:text.index('## 156.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))


main()
