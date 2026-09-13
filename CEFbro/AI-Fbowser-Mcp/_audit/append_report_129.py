# -*- coding: utf-8 -*-
"""追加报告第 129 节（第 112 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 129. 第112轮：`browser_vip_execute_js_context` 增加 `main`/`all_frames`/`frame_index` 三档目标（一次打穿全部 iframe）

### 129.1 缺口与价值

原实现只支持"按 `frame_id`（VIP 框架ID）"或"按 `context_id`（环境ID）"执行 JS。
类库另有三个方法：`高级_执行JS_主框架` / `高级_执行JS_全部框架` / `高级_执行JS_框架序号`
（`FBroVip.wsv:800/821/843`）。其中**全部框架**一次把 JS 跑遍**当前所有框架**，
免掉"枚举框架 → N 次注入"的往返 —— 对 iframe 多的站点，这是从 N 次调用降到 1 次。

### 129.2 ★两个必须处理的诚实性问题（否则新能力会变成"静默不可用"）

**问题一：多帧回调会互相覆盖。**
既有 `类_MCP_VIP通用回调.数据回调` 每次都 `存储异步结果(任务ID, …)` —— 属**覆盖式**。
而"全部框架"的回调**每帧调一次** ⇒ 调用方轮询 `mcp_result` **只会看到最后一帧**，
看起来"只执行了一个框架"。
→ 新增**累计式**回调类 `类_MCP_VIP多帧回调`：每次回调追加，并把
`frame_count` + `frames_text`（逐帧结果）**累计**写回，调用方能看到全部帧。

**问题二：未启用执行环境时回调可能永不触发。**
类库注释写明这些 VIP 方法需先`启用执行环境`才生效；若未启用，调用方会拿到一个
**永远不完成的异步任务**，白等到超时也看不出原因。
→ 给工具加**前置状态判断**：本会话未启用过就**明确失败并给指引**，而不是发一个注定不完成的回执。
状态由 `browser_vip_enable_js_env` 维护（新增静态标志 `VIP_JS环境已启用`），是**自有状态、不靠猜**。

> 顺带说明：类库的这些方法内部有 `if(!FBrowser初始化控制.是否为VIP …) return;` 的静默门控；
> 本项目在 `main.wsv:52-53` 已**强制把该标志置真**（"免VIP：成品对所有用户开放全部功能"），
> 所以门控不是问题；真正会让人白等的是"执行环境未启用"。

### 129.3 验收 **7/7**（`_audit/verify_vip_frame_targets.py`）

**【安全段】前置守卫与回归**

| 臂 | 期望 | 实测 |
|---|---|---|
| `target=main`（未启用环境） | 明确失败 + 指引 | `…需要先启用 VIP JS 执行环境: 请先调 browser_vip_enable_js_env {enable:true, confirm:true}…` ✔ |
| `target=all_frames`（未启用环境） | 同上 | ✔ |
| `target=frame_index`（未启用环境） | 同上 | ✔ |
| 缺省 target（原行为） | 不受影响 | 仍回 `JS已提交到指定环境` ✔ |

**【破坏段】启用执行环境后的真机验证**

| 臂 | 期望 | 实测 |
|---|---|---|
| `enable_js_env {enable:true, confirm:true}` | 成功且带破坏性告警 | ✔ |
| `target=main` + `code=document.title` | 拿到回调结果 | `{"result":{"type":"string","value":"Example Domain"}}` ✔ |
| **`target=all_frames`（页面内注入 iframe）** | **累计多帧** | **`frame_count:4`**，`frames_text` 含 4 帧：主框架 `https://example.com/?vipframe=1` + 3 个 `about:srcdoc` ✔ |

`all_frames` 那臂正是本项能力的意义所在：**一次调用覆盖了 4 个框架**（不是只有一个）。
结束时重启进程，`CDP 恢复检查: alive:…` ✔。

### 129.4 探针自坑（第 N 次）：又是**转义**

第一版把 `all_frames` 判成 FAIL —— 因为回包内层 JSON 是**转义过的**（`\\"frame_count\\":4`），
而我的正则按 `"frame_count":` 匹配。反转义后立刻 **7/7**。
（同类坑此前已出现多次：`call_fn` 的 `args/arguments`、`requestId` 的数字假设、
`browser_dom_rect` 的转义字段……）
**纪律：凡解析本项目的嵌套回包，先 `replace('\\\\"','"')` 再匹配。**

### 129.5 状态与下一步

工具总数 **316**（本轮是给既有工具加参数，未新增工具）；台账 **316/316**，通过 **309** / 失败 7，
**前置缺失 0、能力缺失 0、卡死 0**；编译 0 警告；fastcheck 41/41。

1. `类_FBrowser_菜单模式` 剩余未接线方法（该类 36 个，已接线约 15 个）。
2. A 组清单（92 条、含价值排序）里的下一项。
3. B 组 55 条"仅启动期生效"是否做启动参数通道。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 有 BOM, 中止')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 含 CR, 中止')
        return 1
    if '## 129. 第112轮' in text:
        print('!! §129 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 129. 第112轮') == 1
    print('已追加 §129; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
