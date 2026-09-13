# -*- coding: utf-8 -*-
r"""第137轮收尾: 把"插装装上后 JS 通道继续可用"的实测结论与更正写入两份台账/报告。

- `_audit/_gap_verified.md`         → 追加 §157(技术记录: 归因/改动/验收/残留 + 锚点)
- `MCP工具可用性检测报告.md`         → 追加 §157(人读版: 同一批实测数据 + 对 §155/§156 结论的更正)

用法: py -3 _audit\_doc_round137.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
APPLY = '--apply' in sys.argv

TABLE = '''| 环节 | 实测 |
|---|---|
| A 未装插装: 原始 `Runtime.evaluate` | 结果 **0.02s** 到达 |
| B 装插装后**不 resume** | 派发被拦(HTTP 侧 30s 超时), 结果**永不到达** |
| C 同一任务ID: resume 之后**继续等** | resume 本身 0.04s, **原任务ID 的结果 0.00s 就到** |
| D 对照: resume 之后**重新派发**一条 | 20s 仍拿不到结果 |'''

GAP_TEXT = '''

## 六、第137轮完成：插装装上后本会话 JS 通道**继续可用**（含归因更正）

### §157.1 归因（原始 CDP 通道量测，`_audit/probe_iv_timing.py`，可复现）

''' + TABLE + '''

结论：暂停发生在**渲染器**里 —— 被拦的那条 CDP 请求**一直挂在渲染器队列上**，resume 一发出就**立刻**完成。
故正确做法是「**resume 后继续等原来那条请求**」；而「resume 后重新派发」会**再次命中同一条插装**
（插装拦在脚本执行前），于是又要再 resume 一次，形成 6~20s 的死循环 —— 这正是"把首轮预算压到 2500ms"
仍然失败的成因（§156.2 里"重试一次即可"的假设只对了一半）。

### §157.2 落地改动（3 处 + 1 处幂等，均复用既有件，未新造轮子）

1. `执行CDP并同步等待`（`MCP_Server.wsv`）：记下 `原始预算`；插装态把**首轮**预算压到 **900ms**；
   自救改为 `Debugger.resume`（3000ms 预算）→ **续等原任务ID**（剩余预算，下限 2000ms）→
   只有续等仍失败才退回原有的"重新派发"兜底；
2. 同一处新增**"无暂停记录 → 把压缩掉的预算补等回来"**：压缩绝不会把"慢命令"变成"提前失败"（总等待上限不变）；
3. `MCP_Server_Reverse.wsv`：install **在自检之前**置位 `插装已安装`；`suppress` 的 note 按实测更正；
   `remove` 改为**确认拦停解除后**才清标志，且本机未实现 `Debugger.removeInstrumentationBreakpoint` 时
   **自动兜底**为 `setSkipAllPauses(true)`（复用既有 `执行V8CDP命令`，不另写实现）；
4. `action=install` 重复调用改为**幂等成功**（`already_installed:true`）——旧实现把重复调用报成失败，
   正是"代理换别的方法反复试错"的触发点。

### §157.3 验收（全部运行期实测，非静态推断）

- `_audit/verify_round137.py` **8/8**：install **1.01s**；execute_js ×3 = **0.99 / 0.96 / 0.97s**（修前 60s 超时失败）；
  dom_query 0.96s；remove 0.05s；remove 后 execute_js 0.02s；`browser_status` 健康。
- `_audit/verify_round137b.py` **19/19**：①自救方式确为"续等原请求"（`auto_prepared` 原文）；
  ①b 重复 install 幂等（0.03s）；②`skip=true` 后 **2 秒忙等脚本仍成功（2.10s）** ← 证明"补等"分支确实存在；
  ③恢复拦截后 0.96s；④`remove` 走兜底成功（0.05s）；⑥remove 后再 install 成功、通道 0.03s。
- 快检 **56/56**（干净实例）；编译 **0 警告**；卫生扫描**全零**；
  台账 **323/323 = 323 通过 / 0 未通过**（`browser_reverse_instrument_script` 复测 pass 1.04s）。

### §157.4 更正与残留（如实）

- §155.3 / §156.1 的"安装后只能重启"**已不成立**，描述与报告同步更正；
  "重启可彻底清掉插装定义"仍成立（本机没有可用的单独卸载方法）。
- 本机 Chromium **未实现** `Debugger.removeInstrumentationBreakpoint`（实测 `wasn't found`），
  故 `remove` 的真实语义是"解除拦停（兜底 `setSkipAllPauses(true)`）"，而不是"抹掉定义"——描述与 note 均如实写明。
- 插装态下每条 CDP 脚本请求仍有 **~0.95s** 的固定开销（一次暂停 + 一次 resume），属机制性成本，已在工具描述里给出数字。

复核锚点（按**符号名** grep，不按行号）：`原始预算` / `救活预算` / `补等结果` / `already_installed` / `插装已安装`。
'''

REPORT_TEXT = '''

## 157. 第137轮：插装装上后本会话 JS 通道**继续可用**（§156 方案落地；同时更正 §155/§156 的结论）

### 157.1 先更正结论：**"装上插装后本会话只能重启"已经不成立**

第135轮测到的现象是真的（`install` 成功后 `execute_js` 60s 超时、`suppress` 返回 `setSkipAllPauses 失败: timeout`），
但当时把它归因为"不可逆"是**结论下早了**。本轮用**原始 CDP 通道**把耗时构成量出来之后，真相是：

''' + TABLE + '''

解读：暂停发生在**渲染器**里，我们那条被拦的 CDP 请求**一直挂在渲染器队列上**；`resume` 一发出它就**立刻**完成。
所以正确修法是「**resume 后继续等原来那条请求**」，而不是第135/136轮设想的「resume 后重试一次」——
后者会**再次命中同一条插装**（插装拦在「脚本执行前」），于是又要再 resume 一次，实测 20 秒都拿不到结果。

### 157.2 这一轮改了什么

1. `执行CDP并同步等待`：记下**原始预算**；插装态把**首轮**预算压到 **900ms**（让自救立刻触发）；
   自救改为 resume → **续等原任务 ID**（用剩余预算，下限 2000ms）→ 只有续等仍失败才退回"重新派发"兜底；
2. 同一处新增**"没有暂停记录时，把压缩掉的预算补等回来"** ⇒ 压缩只是"把等待拆成两段"，
   **不会**把"慢命令"变成"提前失败"（总等待上限与压缩前完全一致）；
3. `browser_reverse_instrument_script`：install **在自检之前**置位标志；`suppress` 的说明按实测改写；
   `remove` 改成**确认拦停解除后**才清标志，且本机 Chromium **未实现**单独卸载方法时**自动兜底**为
   `setSkipAllPauses(true)`（复用既有的 `执行V8CDP命令`，不另写一份实现），并在 `note` 里如实说明
   "效果等价、差别只是插装定义仍在内核、重启进程后彻底消失"；
4. `action=install` 重复调用改为**幂等成功**（回执带 `already_installed:true`）。

### 157.3 实测验收（第156.4 的六条验收标准）

| 验收项 | 结果 |
|---|---|
| ① install 成功 | ✅ 1.01s（带 `auto_prepared: Debugger.enable`） |
| ② 随后 execute_js **成功且 <5s** | ✅ 0.99s（修前：60s 超时失败） |
| ③ 连续 3 次 execute_js 均成功 | ✅ 0.99 / 0.96 / 0.97s |
| ④ `remove` 后通道回到 0.03s 级 | ✅ remove 0.05s → execute_js 0.02s |
| ⑤ 快检 | ✅ **56/56**（干净实例） |
| ⑥ 做不到就如实记录 | 已做到，故按实测更新描述 |

补充分支验证（`_audit/verify_round137b.py`，**19/19 通过**）：

- 自救方式确为"续等原请求"（回执 `auto_prepared` 原文：`Debugger.resume(页面原卡在断点/插装, 已自动恢复并续等原请求成功)`）；
- **重复 install 幂等**（0.03s，`already_installed:true`），不再报"已处于启用状态"失败；
- `browser_reverse_skip_pauses skip=true` 之后跑**2 秒忙等脚本仍成功（2.10s）** ⇒ 证明"补等"分支真实存在；
- `skip=false` 恢复拦截后 execute_js 仍 0.96s ⇒ 拦截态可反复进入/退出；
- `remove` → 再 `install` → 通道 0.03s ⇒ **装/停循环不出现任何失败**。

状态：工具 **323**；台账 **323/323 = 323 通过 / 0 未通过**；编译 **0 警告**；卫生扫描**全零**。

### 157.4 残留（如实）

- `remove` 的真实语义是"**解除拦停**"而不是"抹掉定义"：本机 Chromium 未实现
  `Debugger.removeInstrumentationBreakpoint`（实测 `wasn't found`），工具会自动兜底并说明；
  要**彻底**消失仍需重启进程。
- 插装态下每条 CDP 脚本请求有 **~0.95s** 固定开销（一次暂停 + 一次 resume），属机制性成本，
  已写进工具描述，避免被误判成"工具坏了"。
- 若之前用过 `suppress`/`remove`（跳过全部暂停），再次 `install` 会如实回 `already_installed:true`；
  想恢复拦截用 `browser_reverse_skip_pauses skip=false`（回执里已给出这条下一步）。
'''

TARGETS = [(GAP, GAP_TEXT, '§157 技术记录'), (REPORT, REPORT_TEXT, '§157 报告章节')]


def main():
    for path, text, tag in TARGETS:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if '## 157.' in txt or '## 六、第137轮完成' in txt:
            print('· %s —— 已存在, 跳过' % tag)
            continue
        out = txt.rstrip('\n') + '\n' + text
        print('· %s: %d -> %d 字符' % (tag, len(txt), len(out)))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(out)
            print('   ✔ 已写入 %s' % os.path.basename(path))
    if not APPLY:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
