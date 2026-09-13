# -*- coding: utf-8 -*-
r"""追加报告章节: ## 138. 第120轮: G1b 子框架内执行 JS (browser_execute_js {frame_id})。

约束: 报告文件必须无 BOM、LF 换行、章节号不得重复; 追加而非改写既有内容。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 138. 第120轮：G1b —— `browser_execute_js {frame_id}` 子框架内执行 JS（含"世界语义"实测与两条通道的稳定性对照）

### 138.1 目标与结论
- 目标：让"在指定 iframe 内执行 JS"成为**一次调用即成功**的能力（此前只有主框架求值）。
- 结论：`browser_execute_js {frame_id}` 已可用，支持 **CEF 框架ID / 框架名 / 序号** 三种寻址；**嵌套 iframe** 同样可寻址。
- 验收：`_audit/verify_frame_exec.py` **17/17 通过**；稳定性 `_audit/verify_frame_exec_stability.py` 缺省路径 **24/24 次全绿、单次约 0.06s**。

### 138.2 踩到的第一个坑（静态可证，实测吻合）：CDP 结果是**被转义的 JSON 字符串**
`MCP_Server.wsv` 的"收到CDP响应"存的是 `{"success":…,"messageId":…,"result":"<CDP 结果原文>"}`
—— `result` 是**文本成员**。于是按存储原文扫描 `"id":"` 时，实际字符是 `\\"id\\":\\"`，**永远扫不到**。
实测表现：按 id/名/序号三条路全部返回 `未找到框架`（框架清单本身完全正常，3 个框架、名字都对）。
- 修正：新增 `取CDP结果文本 (存储JSON)`，先 `yyJSON` 取 `result`（自动反转义），取不到再解一层转义兜底；
  `Page.getFrameTree` 的框架 id 抽取与 `Page.createIsolatedWorld` 的 `executionContextId` 读取都改走它（后者直接用 `yyjson取整数`）。

### 138.3 第二个坑（危险级）：`文本到整数` 把"框架不存在"静默变成"序号 0 = 主框架"
序号兜底原写成 `候选序号 = 文本到整数 (目标框架)`。垃圾文本（如 `no-such-frame-zzz`）会得 0，
于是"不存在的框架"被解析成序号 0 —— 代码照样执行、照样返回成功，只是**跑在了别的框架里**。
- 实测证据：该臂返回 `x`（成功）而不是错误；且因为序号 0 当时走的是隔离世界，连主框架的 `window` 标记都查不到，极难发现。
- 修正：只有**纯数字**文本才按序号解释（逐字符校验），并约定 **序号 0 = 主框架 → 直接返回 0 走默认上下文**（页面主世界）。

### 138.4 第三个坑（本机实测，决定了本功能的最终形态）：隔离世界 ≠ 页面主世界
CDP 只能对子框架建**隔离世界**（`Page.createIsolatedWorld`）。量测（`_audit/verify_frame_ctx_semantics.py`）：
- 隔离世界里 `String(window.<页面在子框架挂的全局>)` 恒为 `undefined`；
- 页面在子框架主世界定义的函数，`typeof window.<fn>` **不是** `function`；
- 但 DOM 完全可达（`document.querySelector('#tgt').value` 正常）。
反过来说，原生 `类_FBrowser_框架.执行JS代码_带返回值` 在**该框架自己的页面主世界**执行，没有这个问题。
- 故最终形态：`world` 参数显式二选一 ——
  - 缺省/`isolated`：CDP 隔离世界（稳定、同步、DOM 可达；页面全局不可见）；
  - `world=main`：原生框架对象（页面主世界可读写；走原生"带返回值 JS"通道，见 138.5）。
- 两个方向都在工具描述里写明，避免"看起来成功、其实换了个世界"。

### 138.5 第四个坑：原生"带返回值 JS"通道本身会丢回调（**非本功能引入**）
对照量测 `_audit/verify_native_js_channel.py`（每臂连续 12 次）：
| 臂 | 路径 | 结果 |
|---|---|---|
| A | `browser_evaluate`（原生带返回值，**主框架**，既有功能） | 11/12，1 次 5s 超时 |
| B | `browser_execute_js`（CDP，主框架） | **12/12** |
| C | `browser_execute_js {frame_id}`（原生带返回值，**子框架**，本轮新增） | 11/12 |
| D | A 之后再跑 B（CDP 是否被原生通道拖坏） | **12/12** |
- 判读：A 与 C 的失效率同量级，说明这是**原生通道固有性质**（约 8% 回调丢失 → 5s 超时），与"子框架"无关；
  B/D 全绿说明 CDP 通道不受影响。该结论已写进工具描述（"偶发时重试一次即可"）。
- 顺带实证：超时后通道会短暂连带失败，但**会自行恢复**（同一会话后续调用重新成功）。

### 138.6 新增的"禁止静默跑错框架"守卫（静态补齐）
`CDP执行JS并等待` 内部原有 **5 处** `原生执行JS并等待` 回退，而该原生路径**只在主框架执行**（实现第一句就是 `取安全主框架`）。
调用方一旦传了子框架的执行上下文，CDP 无回执时就会**静默落到主框架**跑同一段 JS。
- 修正：新增 `子框架原生回退 (JS代码, 最大等待毫秒, 执行上下文ID)`——上下文 > 0 时直接返回 `""`（语义"无回退可用"），
  否则原样转调原生路径（上下文 = 0 的行为**逐字不变**）；方法体内 5 处调用点全部改走它，脚本断言"恰好 5 处"。

### 138.7 本轮新增/改动的代码
- `src/MCP_Server.wsv`：新增 `取CDP结果文本`、`解析框架执行上下文`、`解析框架对象`、`子框架原生回退`、`CDP执行JS按框架`（后者供 G1c 的 DOM/填表族复用）；
  `CDP执行JS并等待` 增加可选第 4 参 `执行上下文ID` 并把 5 处回退改为受守卫；`browser_execute_js` 的 Schema 增加 `frame_id` / `world`。
- `src/MCP_Server_Core.wsv`：`browser_execute_js` 增加子框架分支（缺省 CDP 隔离世界 / `world=main` 原生主世界），
  未知框架**明确报错**、不求值、不回退主框架。
- 编译：0 错误 0 警告；快检 56/56。

### 138.8 待办（本轮识别，未做）
- `world=main` 的 8% 回调丢失属原生通道固有性质；若要"主世界 + 稳定"两者兼得，需要另找通道（例如
  `Page.addScriptToEvaluateOnNewDocument {runImmediately}` + `Runtime.addBinding` 的 binding 回调），已记入后续目标。
'''
# 注: 上面字符串里不含三个连续双引号, 满足 raw 报告字面量约束


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 138.' not in text, '章节 138 已存在'
    assert text.rstrip().endswith('---') or True
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已追加: %s (%d -> %d 字符)' % (REPORT, len(text), len(out)))
    else:
        print('[dry-run] 将追加 %d 字符; 章节头: %s' % (len(SECTION), SECTION.strip().split('\n')[0]))


main()
