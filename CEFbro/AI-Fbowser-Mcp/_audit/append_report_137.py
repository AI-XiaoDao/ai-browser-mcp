# -*- coding: utf-8 -*-
r"""追加报告 §137(第119轮): iframe 子框架支持(G1)落地并实证 + 读取侧的边界与已实测的 CDP 配方。

SEC 必须原始字符串(正文含 Windows 路径/反斜杠), 且正文里不得出现连续三个双引号。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = r"""
---

## 137. 第119轮：iframe 子框架支持（G1）——21 个 DOM/填表工具不再只会操作主框架

### 137.1 缺口与修法

上一轮缺口刷新（`_audit/_gap_refresh_r117.md` G1）指出：`src` 里 **21 处**填表/DOM 入口
**全部硬编码** `browser.取主填表框架 ()` ⇒ **iframe 里的表单与 DOM 完全操作不到**，而类库其实提供了
`取填表框架_ID (ID)` / `取填表框架_名称 (名称)`（`FBroLib.wsv:1414/1422`）。

修法：
1. 新增中央解析器 `MCP命令服务器.解析填表框架 (浏览器, 目标框架)`：空 / `main` / `主框架` → 主填表框架（向后兼容）；
   否则**先按 frame_id 取，再按框架名取**；都取不到返回**空框架**。
   类库原文警告"ID 错误返回空类，**对空类执行操作会崩溃**" ⇒ 安全性依据是：这 21 个调用点**本来就有**
   `填表框架.是否有效 ()` 守卫（已逐一核实），故返回空类等于"框架不存在"，由调用方既有逻辑报错。
2. 21 个调用点改为传工具入参 `frame_id`（`MCP_Server_Core.wsv` 11 处 + `MCP_Server_Form.wsv` 10 处）。
   另外 `MCP_Callbacks.wsv` 里的 **2 处保持主框架**：那是下载/网络回调，没有 `参数JSON`，也不该绑定某个 iframe。
3. 21 个工具的描述与 schema 都加上 `frame_id`（`browser_dom_*` / `browser_fill_*` / `browser_get_text`）。

### 137.2 验收：**写路径已实证**（判别式设计）

`_audit/verify_iframe_support.py`：主框架与 iframe **放同一个选择器 `#tgt` 但值不同**（MAIN / IFRAME），
再用**主框架 JS 穿透 `contentDocument`** 当预言机（不依赖被测工具自证）：

| 臂 | 期望 | 实测 |
|---|---|---|
| 基线 | 两边各自可读且值不同 ⇒ 判别有效 | 主=`MAIN` / iframe=`IFRAME` ✔ |
| 不带 `frame_id` 写 | 只改主框架（向后兼容） | 主=`WRITTEN_IN_MAIN`，iframe 不受影响 ✔ |
| **带 `frame_id` 写** | 只改 iframe，**主框架不受串扰** | iframe=`WRITTEN_IN_IFRAME`，**主仍 `MAIN`** ✔★ |
| 未知 `frame_id` | **可行动失败**，绝不静默改主框架 | `isError=True 填表框架无效`，主框架值未变 ✔ |
| 按**框架名**定位 | 也应可用 | 用 `name=mcpfr` 的 iframe 验证 ✔ |

⇒ 真机确认：**填表/写入类工具现在能进 iframe**，且与主框架互不串扰。

### 137.3 ★诚实的边界：**读取类工具仍在主框架求值**（已在 21 个 schema 里写明）

验收时发现 `browser_fill_attr_get {frame_id}` **读到的还是主框架的值**。根因（读源码）：
这类读取工具是 **CDP JS 优先**——因为本内核下"原生 `填表框架.取元素属性` 恒返回空值并被写成字面 null"，
所以作者改走 `CDP执行JS并等待`；而那条路径**始终在主框架求值**，不认 `frame_id`。
⇒ 于是：**写（原生路径）进得了 iframe，读（CDP 路径）进不去**。

处置：**不假装**。把这 21 处 `frame_id` 说明改成如实版（写明"原生填表路径支持子框架；走 CDP JS 的读取类
工具仍在主框架求值"），并给出**已实测的绕行配方**（见 137.4）。这是"未完成"，不是"已支持"。

### 137.4 读取侧的正解已找到并**实测可行**（下一轮 G1b 的配方）

两个探针（`_audit/probe_cdp_frame_context.py` / `probe_cdp_frame_id_map.py`）给出决定性事实：

1. **CEF 的框架标识与 CDP 的 frameId 不是同一套**：
   `browser_get_frames` 给 `6-C5C7BC5DC8C76C073FED19F45D743039`，而 CDP `Page.getFrameTree` 给
   `CCDA0BFD9190678F1A0582CBDEC01966`，两侧**无交集**；拿 CEF 的 id 调 `Page.createIsolatedWorld`
   直接回 `-32602 No frame for given id found`（**第一次探针就是这么失败的**）。
2. 换成 **CDP 侧 frameId** 后全通（原始回包）：
   `Page.createIsolatedWorld {frameId: "CCDA0BFD…", worldName: "mcp_probe2", grantUniversalAccess: true}`
   → `{"executionContextId":11}` →
   `Runtime.evaluate {expression: "…document.getElementById('inner')…", contextId: 11, returnByValue: true}`
   → `{"result":{"type":"string","value":"CTX3:FROM_IFRAME3"}}` ✔（读到了 iframe 内部文本）

⇒ 下一轮 `browser_execute_js {frame_id}`（以及读取类工具）的实现路径：**先 `Page.getFrameTree` 把 CDP 框架树
按树序展平**，与 `browser_get_frames` 的清单**按序对应**（有名字时优先按 `name` 匹配），拿到 CDP frameId →
`createIsolatedWorld` 取 contextId → `Runtime.evaluate {contextId}`。

### 137.5 本轮我自己的两处探针失误（都不是产品缺陷）

1. **读输入框的值不能只给 selector**：`browser_fill_attr_get` 不给 `attribute` 时读的是**元素文本**
   （`<input>` 为空）⇒ A/B 两臂都"读到空"，被我误判成产品问题；补 `attribute:"value"` 后正常。
2. **匿名 iframe 的名字是 CEF 占位符**（`<!--dynamicFrame…-->`）⇒ 按名字定位那一臂得用**带 `name` 的 iframe**
   才有意义（改页面后即通过）。

### 137.6 状态

工具总数 **320**；台账 **320/320**；编译 **0 警告**；快检 **55 → 56**（新增"iframe 写入：`frame_id`
只改 iframe、主框架不受影响"这条回归钉）；卫生扫描仍**全部归零**（操作备注 0 / 死代码备注 0 / 残注释 0 /
零引用方法 0 / 零引用成员 0 / 重复分支 0 / 幽灵注册 0）。

**下一轮**：G1b（`browser_execute_js {frame_id}` + 读取类工具走 CDP 上下文，配方已实测）；
其余待办：G4 VIP 二进制资源替换、G5 下载完成信息、G6 `media_devices` 假成功、G7 `clear_count`、
G8 `browser_get_global_cache_dir` 不认 `_Stdio` 分支（静态即可判定）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 报告有 BOM')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 报告含 CR')
        return 1
    if '## 137. 第119轮' in text:
        print('!! §137 已存在')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 137. 第119轮') == 1
    print('已追加 §137; 行数 %d -> %d (无 BOM / 无 CR / 唯一)' % (text.count('\n') + 1, t2.count('\n') + 1))
    return 0


sys.exit(main())
