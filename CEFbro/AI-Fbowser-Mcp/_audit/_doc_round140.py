# -*- coding: utf-8 -*-
r"""第140轮收尾: 把"CDP 预注入修复 / handler 诚实化 / 启动期事件可观测"写入两份文档(§160)。
用法: py -3 _audit\_doc_round140.py [--apply]
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

GAP_TEXT = '''

## 九、第140轮完成：修复"注册成功却永不执行"的 CDP 预注入 + 两处诚实化 + 启动期事件可观测

### §160.1 `browser_reverse_preload`：修前是**假能力**（注册成功，脚本永不执行）

三臂对照实测（同一实例、干净重启、导航到带时间戳的新地址、读双哨兵）：

| 臂 | 做法 | 导航后 `window.__plS` |
|---|---|---|
| A | 只调 `browser_reverse_preload`（**修前行为**） | **`undefined`** —— CDP 回 `success` + `identifier:1`，脚本从未执行 |
| B | 先 `Page.enable` 再注册 | **`C1`** ✅ |
| C | `Page.enable` + 连续注册两次 | **`C1`** ✅ |

⇒ 在本机 `Page.addScriptToEvaluateOnNewDocument` **必须先启用 Page 域**才生效。
而多个工具描述把 `browser_reverse_preload` 推荐为"在所有页面JS之前注入 / 拦打包器最稳"的路径 ——
**修前那条建议指向一个静默无效的通道**。

修法（零前置，遵循项目既有 `auto_prepared` 惯例）：`browser_reverse_preload` 内部先 `Page.enable`，
失败则**明确失败**（而不是回一个假成功），成功则 `记录自动补域 ("Page")` 让回包带 `auto_prepared: Page.enable`。
旁证：注册动作本身**不会**拖慢 JS 通道（注册前后 `execute_js` 均 0.03s）。

### §160.2 `browser_inject {persist:true, type:"handler"}`：从"静默改变语义"改为**可行动拒绝**

实测：传 `handler` 时其代码最终走 `浏览器_载入开始 → 应用持久V8到框架 → 框架.执行JS代码`，
即被当作**普通页面 JS** 执行（哨兵 `window.__mcpHandlerRan='H1'` 在重载后可读），
**不是**它承诺的"页面 JS 调原生并同步回值"的原生桥。真实 handler 桥需要渲染进程内
`FBrowser_V8_注册JS扩展` / `FBrowser_JS交互_注册`，而本项目渲染进程事件不派发到主进程、
JS 交互桥也已两轮实测判定不可用。

修法：`type=handler` 明确拒绝 + 给出三条**实测有效**的替代（`type:js + persist:true`、
`browser_reverse_preload`(已修)、`browser_execute_js`），并如实说明"现状会被当普通 JS 跑"。
同时订正了 `type:js` 分支的注释：真正生效路径是 `浏览器_载入开始`（旧注释写的 `渲染_即将创建V8环境`
是渲染进程事件、在本项目不派发）。

### §160.3 启动期事件：从"永久丢失"到**可查**（两个成因叠加，都已修）

| 成因 | 说明 | 修法 |
|---|---|---|
| ① `记录事件日志` 在 SQLite 未就绪时直接 `return` | 启动期事件都早于 `启动MCP服务器`（SQLite 打开） | 改为进**内存环形缓冲**（每条 5 成员，上限 40 条），DB 就绪后由写入路径**与查询路径**双向 flush（只靠写入路径 flush 会因"之后再无同族事件"而永远查不到） |
| ② 内层总闸 `是否监控应用事件` 默认假 | `记录应用监控事件` 包装里还有一道总闸，且只能在启动**之后**打开 ⇒ 本族开关判过也没用 | 5 处启动期记录点改为**直调** `记录应用事件`（它们已各自判过本族开关）；`是否监控启动流程` 改**默认真** |
| ③ 查询闸门漏算本族开关 | `app开关已开` 只算了总闸/渲染/WS 三族，漏了启动族与扩展族 ⇒ 事件已入库却报"开关未开启" | 补全五族开关 |

**实测（修后，同一实例）**：`app_startup_cmdline` **1 条**（data=`{"process_type":""}`）、
`app_startup_request_context_ready` **2 条**、`app_startup_child_process` 多条 —— 三者修前都是"查不到"。
同时把过宽文案按实测**收窄**：`app_render_*` / `app_v8_*` / `app_render_ws_*` 由渲染进程触发、本机不派发
（仍然不入库）；而**主进程族**（启动期 / 扩展生命周期）会入库。旧文案"整个 app_* 族永远不会入库"已更正
（`MCP_Server_Core.wsv` 两处 + `main.wsv` 注释）。

### §160.4 验收与状态

| 项 | 结果 |
|---|---|
| `_audit/verify_round140.py` | **12/12** |
| 台账 | **324/324 = 324 通过 / 0 未通过**（`browser_reverse_preload` 复测 pass 0.05s 且带 `auto_prepared: Page.enable`；`browser_inject` pass） |
| 快检 | **56/56** |
| 编译 | **0 警告** |
| 卫生扫描 | **全零** |

**流程教训（第二次同类）**：本轮又一次在**探针**上栽跟头 —— `event_count()` 只处理"`data` 是对象"，
遇到"`data` 是列表"就把**已有记录**读成 `-1`；另有断言把文案里的 `type:js` 写成 `type=js`。
结论：**探针解析器与断言字面量同样属于被测对象**，失败时必须打印原文（本轮已按此打印全文定位）。
'''

REPORT_TEXT = '''

## 160. 第140轮：修好一条"注册成功却永不执行"的预注入通道 + 两处诚实化 + 启动期事件终于可查

### 160.1 `browser_reverse_preload`：修前是**假能力**

三臂对照（干净实例、导航到新地址、读双哨兵 `window.__plS`）：

| 臂 | 做法 | 结果 |
|---|---|---|
| A | 只调 `browser_reverse_preload`（**修前行为**） | **`undefined`**（CDP 回 `success` + `identifier:1`，脚本从未执行） |
| B | 先 `Page.enable` 再注册 | **`C1`** ✅ |
| C | `Page.enable` + 连注册两次 | **`C1`** ✅ |

⇒ 本机 `Page.addScriptToEvaluateOnNewDocument` **必须先启用 Page 域**。而多处描述把它推荐成
"在所有页面JS之前注入 / 拦打包器最稳" —— 修前那条建议指向的是**静默无效**的通道。

修法：工具内部先 `Page.enable`（失败即明确失败，不返回假成功），成功则如实上报
`auto_prepared: Page.enable`。旁证：注册本身不拖慢 JS 通道（前后 `execute_js` 均 0.03s）。

### 160.2 `browser_inject {type:"handler"}`：不再"静默改变语义"

实测：传 `handler` 时它最终被当作**普通页面 JS** 执行（哨兵在重载后可读），并非承诺的"原生 handler 桥"
（那需要渲染进程内注册 JS 扩展，而本项目渲染事件不派发到主进程）。现改为**明确拒绝 + 三条实测有效替代**
（`type:js + persist:true` / `browser_reverse_preload`(已修) / `browser_execute_js`），并订正了
`type:js` 分支里写错机理的注释。

### 160.3 启动期事件：从"永久丢失"到**可查**

三个成因（都已修）：① `记录事件日志` 在 SQLite 未就绪时直接丢弃（启动期事件全都早于 SQLite 打开）
→ 改内存缓冲 + **写入/查询双向 flush**；② `记录应用监控事件` 包装里的总闸 `是否监控应用事件` 默认假、
且只能启动后打开 → 启动期 5 个记录点改直调 + 本族开关默认真；③ 查询闸门漏算启动/扩展族开关
→ 补全五族。

**修后实测**：`app_startup_cmdline` 1 条（`{"process_type":""}`）、`app_startup_request_context_ready` 2 条、
`app_startup_child_process` 多条 —— 修前全部查不到。并把过宽文案按实测收窄：
**渲染族**（`app_render_*`/`app_v8_*`/`app_render_ws_*`）仍不入库，但**主进程族**（启动期/扩展生命周期）
**会**入库。

### 160.4 验收与状态

| 项 | 结果 |
|---|---|
| `_audit/verify_round140.py` | **12/12** |
| 台账 | **324/324 = 324 通过 / 0 未通过** |
| 快检 | **56/56** |
| 编译 | **0 警告** |
| 卫生扫描 | **全零** |
'''


def main():
    for path, text, tag, mark in [(GAP, GAP_TEXT, '§160 技术记录', '## 九、第140轮完成'),
                                  (REPORT, REPORT_TEXT, '§160 报告章节', '## 160. 第140轮')]:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if mark in txt:
            print('· %s —— 已存在, 跳过' % tag)
            continue
        out = txt.rstrip('\n') + '\n' + text
        print('· %s: %d -> %d 字符' % (tag, len(txt), len(out)))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(out)
    print('   ✔ 已写入' if APPLY else '(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
