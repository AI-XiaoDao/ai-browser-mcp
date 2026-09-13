# -*- coding: utf-8 -*-
r"""第138轮收尾: 更新台账条目 + 把两处"显示出来却做不到事"的修复写入台账/报告。

1. `_audit/_tool_ledger.json` 的 `browser_close_try`: 按本轮受控实测(12/12)改写 note
   (它是 LETHAL 工具, 台账 CLI 会跳过, 故仍以 `manual: true` 记录)。
2. `_audit/_gap_verified.md` + `MCP工具可用性检测报告.md`: 追加 §158。

用法: py -3 _audit\_doc_round138.py [--apply]
"""
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, '_audit', '_tool_ledger.json')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
APPLY = '--apply' in sys.argv

NOTE = ('[人工受控实测·非探针·第138轮] 测法: _audit/verify_close_try.py 12/12 通过 || '
        '①不带 confirm 关主窗口 → 可行动拒绝(明确告知需 confirm:true 与替代) || '
        '②传后台浏览器 id → **真的关掉**(browser_list 回读 [1,2]→[1], 不是只看回执) || '
        '③无效 id → 明确失败「浏览器不可用或已关闭」 || '
        '④confirm:true → **程序真的退出**(browser_status 3.5s 内不再可用) || '
        '⑤重启后 browser_status/execute_js 正常; tools/list 复核 schema 三参数(browser_id/confirm/delay_seconds)齐备 || '
        '实现已由「⛔ 恒失败(已废弃)」改为统一入口: 传 browser_id 转发 browser_close、关主窗口需 confirm:true 并转发 browser_shutdown || '
        '台账 CLI 对 LETHAL 工具直接跳过, 故以人工受控条目记录')

GAP_TEXT = '''

## 七、第138轮完成：把"显示出来却做不到事"的工具清零（dead-end = 0）

### §158.1 系统性扫描（不再靠"被点名才修"）

新增 `_audit/scan_deadends.py` → `_audit/_deadend_scan.md`：从 `添加工具JSON` 取**全部 323 个已显示工具**，
在 `分类分派_*` 里定位其分支，若分支**第一条可执行语句**就是无条件的 `命令失败` 返回，则判定为 dead-end
（"显示出来却永远做不到事"）。扫描结果：

| 阶段 | dead-end 命中 |
|---|---|
| 扫描前 | **1** —— `browser_close_try`（`browser_debugger_pause` 已于本轮稍早修好） |
| 修复后 | **0** |

### §158.2 `browser_debugger_pause`：从"⛔ 恒失败守卫"变成**真正可用的安全暂停**

- 原实现无条件返回"已禁用"；而项目里**早就有**安全机制 `确保调试器已暂停`
  （先显式 `Debugger.enable` → 用页面自身 `setTimeout(...,30)` 安排一个**必然很快执行**的语句给 pause 做落点
  → 再 `Debugger.pause` → 等 `Debugger.paused`），`step_over/step_into/step_out` 等 8 处已在用。
- 现改为复用它，并在调用前**武装既有的防呆网**（`暂停前事件指纹` + `待恢复暂停时间` ⇒ 主循环 `检查暂停自动恢复`
  10 秒没等到暂停事件就自动 resume，防队列被堵）；只在"调用前页面未暂停"时武装，避免误 resume。
- 实测（`_audit/verify_pause_tool.py` **11/11**）：pause **0.06s 成功**并带 `auto_prepared`；
  暂停态 `browser_debugger_last_paused` 能读到现场（`reason:other` + call_frame_id）；暂停态 `execute_js` 仍 0.03s
  （**不卡死实例**）；重复 pause 幂等成功 0.02s；`about:blank` 上也有界返回 0.17s（不挂起）。
  台账复测：**pass 0.06s**（原为人工受控条目，现已变成真测）。

### §158.3 `browser_close_try`：从"⛔ 恒失败(已废弃)"变成**统一关闭入口**

- 背景事实：类库 `尝试关闭浏览器(TryCloseBrowser)` 在本项目**恒返回假**（缺它要求的"顶层窗口关闭处理器"），
  所以老实现注定失败 —— 不是参数问题，是路径不存在。
- 修法（**转发复用，不另写关闭逻辑**）：
  · 传 `browser_id` 且**不是主窗口** → 转发 `browser_close`（真正关闭）；
  · 目标为主窗口 → 关闭它等于退出整个 MCP 服务，故需 `confirm:true`（转发 `browser_shutdown` 的安全关闭序列），
    不带 confirm 时明确拒绝并给替代。
- 归属判定踩坑并修掉：**不能用 `取主浏览器 ()`** —— 路由层已把参数里的 `browser_id` 写进静态 `目标浏览器ID`，
  而 `取主浏览器()` 在该值 >0 时返回的**就是目标自己**，于是"目标==主窗口"恒成立（实测现象：传后台浏览器 id 却报
  "需 confirm:true"）。改按 `FBrowser_浏览器_取ID清单 ()` 的**最小 id** 认定主窗口（枚举方式与 `browser_list` 一致）。
- 实测（`_audit/verify_close_try.py` **12/12**）：后台浏览器 `browser_id=2` → `browser_close_try` 成功关闭，
  `browser_list` 回读 `[1,2]→[1]`；无效 id → 明确失败；不带 confirm 关主窗口 → 可行动拒绝；
  `confirm:true` → **程序真的退出**（`browser_status` 3.5s 内不再可用）；重启后一切正常；
  `tools/list` 复核 schema 三参数齐备（改 schema 必须运行期复核）。

### §158.4 状态

| 指标 | 值 |
|---|---|
| 工具数 | **323** |
| dead-end（已显示却只会失败） | **0** |
| 台账 | **323/323 = 323 通过 / 0 未通过** |
| 快检 | **56/56**（干净实例） |
| 编译 | **0 警告** |
| 卫生扫描 | **全零**（操作备注/死代码备注/残注释/零引用方法/零引用成员/重复分支/幽灵注册） |
| 剩余"刻意的守卫" | 2 个：`browser_create_tab`、`browser_task_runner_post` —— 二者**不在 tools/list 里**（未显示），
且被调用时给出明确原因与替代，不影响"已显示能力必须可用"这一条 |

复核锚点（按符号名 grep）：`scan_deadends.py` / `ct清单` / `确保调试器已暂停` / `检查暂停自动恢复`。
'''

REPORT_TEXT = '''

## 158. 第138轮：把"显示出来却做不到事"的工具清零（dead-end = 0）

### 158.1 先做**系统性扫描**，不再"被点名才修"

用户的要求是"**确保所有显示的 MCP 能力都可以稳定正常执行功能**"。只修被点到的几个不够，
于是新增 `_audit/scan_deadends.py`（→ `_audit/_deadend_scan.md`）：取 `添加工具JSON` 里的**全部 323 个已显示工具**，
在 `分类分派_*` 中定位各自分支，若**第一条可执行语句**就是无条件 `命令失败` 返回，即判定为 dead-end。

| 阶段 | dead-end |
|---|---|
| 扫描前 | **1**（`browser_close_try`） |
| 修复后 | **0** |

### 158.2 `browser_debugger_pause`：现在**真的能暂停**（原先只会返回"已禁用"）

它以前被当成"刻意守卫"：裸发 `Debugger.pause` 在**没有 JS 执行点**的页面上永不返回，还会把 CDP 命令队列堵死。
但项目里早就有安全机制 —— `确保调试器已暂停`（先显式 `Debugger.enable` → 用页面自身的 `setTimeout(…,30)`
安排一个**必然很快执行**的语句给 pause 做落点 → 再 `Debugger.pause` → 等 `Debugger.paused`），
`step_over / step_into / step_out` 等 8 处一直在用它。本轮把 pause 也接到这条路上，并**武装既有的防呆网**
（主循环 `检查暂停自动恢复`：10 秒没等到暂停事件就自动 resume，防队列被堵）。

实测（`_audit/verify_pause_tool.py` **11/11**）：

| 项 | 结果 |
|---|---|
| `browser_debugger_pause` 调用 | ✅ **0.06s 成功**（带 `auto_prepared` 说明） |
| 暂停是真的 | ✅ 暂停态 `browser_debugger_last_paused` 读到现场（`reason:other` + call_frame_id） |
| 不卡死实例 | ✅ 暂停态 `execute_js` 仍 0.03s |
| 幂等 / 恢复 | ✅ 再次 pause 0.02s 成功；`resume` 后 execute_js 0.03s |
| 无 JS 执行点页面（about:blank） | ✅ 0.17s 有界返回（不挂起） |

### 158.3 `browser_close_try`：从"⛔ 恒失败(已废弃)"变成**统一关闭入口**

老实现失败的**真实原因**（`browser_close` 的描述里已记录）：类库的 `尝试关闭浏览器(TryCloseBrowser)`
在本项目**恒返回假** —— 本项目是控制台程序，没有类库要求的"顶层窗口关闭处理器"，**这条路径不存在**。
本轮不再依赖它，改为**转发复用**既有实现：

- 传 `browser_id` 且**不是主窗口** → 转发 `browser_close`（真正关闭）；
- 目标为主窗口 → 关闭它等于退出整个 MCP 服务，故需 `confirm:true`（转发 `browser_shutdown` 的安全关闭序列，
  响应先返回、1~3 秒后退出）；不带 confirm 时明确拒绝并给出替代。

实现时踩到并修掉一个**归属判定缺陷**：不能用 `取主浏览器 ()` 判"是不是主窗口"—— 路由层已把参数里的
`browser_id` 写进静态 `目标浏览器ID`，而 `取主浏览器()` 在该值 >0 时返回的**就是目标自己**，
于是"目标==主窗口"恒成立（实测现象：传后台浏览器 id 却回"需 confirm:true"）。
改按 `FBrowser_浏览器_取ID清单 ()` 的最小 id 认定主窗口（枚举方式与 `browser_list` 一致）。

实测（`_audit/verify_close_try.py` **12/12**）：

| 场景 | 结果 |
|---|---|
| 后台浏览器 `browser_id=2` | ✅ 成功关闭，`browser_list` 回读 `[1,2]→[1]`（**看回读，不看回执**） |
| 不存在的 id | ✅ 明确失败「浏览器不可用或已关闭」 |
| 不带 confirm 关主窗口 | ✅ 可行动拒绝（告知需 confirm:true 与替代） |
| `confirm:true` | ✅ **程序真的退出**（`browser_status` 3.5 秒内不再可用） |
| `tools/list` schema | ✅ 三参数齐备（`browser_id` / `confirm` / `delay_seconds`） |

### 158.4 当前状态

| 指标 | 值 |
|---|---|
| 工具数 | **323** |
| dead-end（已显示却只会失败） | **0** |
| 台账 | **323/323 = 323 通过 / 0 未通过** |
| 快检 | **56/56** |
| 编译 | **0 警告** |
| 卫生扫描 | **全零** |

仍保留的 2 个"刻意守卫"（`browser_create_tab` / `browser_task_runner_post`）**不在 tools/list 里**（不显示给代理），
被调用时也会给出明确原因与替代 —— 因此不影响"已显示能力必须可用"这条硬要求。
'''


def main():
    # ① 台账条目
    d = json.load(io.open(LEDGER, encoding='utf-8'))
    e = d.get('browser_close_try') or {}
    e.update({'cls': 'OK_MANUAL', 'status': 'pass', 'manual': True,
              'note': NOTE, 'ts': time.strftime('%m-%d %H:%M'), 'round': 138})
    d['browser_close_try'] = e
    print('· 台账 browser_close_try 已更新 (manual/pass)')
    # ② 文档
    docs = []
    for path, text, tag, mark in [(GAP, GAP_TEXT, '§158 技术记录', '## 七、第138轮完成'),
                                  (REPORT, REPORT_TEXT, '§158 报告章节', '## 158. 第138轮')]:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if mark in txt:
            print('· %s —— 已存在, 跳过' % tag)
            continue
        docs.append((path, txt.rstrip('\n') + '\n' + text))
        print('· %s: %d -> %d 字符' % (tag, len(txt), len(docs[-1][1])))
    if APPLY:
        io.open(LEDGER, 'w', encoding='utf-8', newline='').write(json.dumps(d, ensure_ascii=False, indent=1))
        for path, out in docs:
            io.open(path, 'w', encoding='utf-8', newline='').write(out)
        print('   ✔ 已写入台账与两份文档')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
