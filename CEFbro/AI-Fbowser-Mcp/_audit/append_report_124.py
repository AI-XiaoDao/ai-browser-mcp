# -*- coding: utf-8 -*-
"""追加报告第 124 节（第 107 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 124. 第107轮：★更正上一轮的误判——`back/forward` 纳入同步（3×5/5）；`navigate` 经实验排除；类库缺口刷新（A 92 / B 55 / C 31）

### 124.1 先做实验：`browser_navigate` 会不会被旧 `load_end` 假满足？→ **不会**（该线索关闭）

上一轮留下一个高危疑点：既然事件驱动那条等待路径不判序事件属于哪次导航，
那么**同在同步名单里**的 `browser_navigate` 是否也会被上一次导航遗留的 `load_end` 立刻满足？
区分性实验：正常导航到 A（确保已有 load_end 事件）→ 紧接着导航到**永远载入不了**的黑洞地址：

```
browser_navigate {url:"https://10.255.255.1/", wait_for_load:true, max_ms:8000}
  -> 用时 8.19s，isError=True，"⏱ 操作超时(8s)…"，实时 URL 仍是 A
```

即 **navigate 会如实等满预算并报超时**（假满足会表现为"几乎立刻成功"）⇒ **navigate 不受影响，线索关闭**。

### 124.2 ★更正：上一轮"旧事件假满足"是**我自己的误判**

上一轮我观察到：把 `back/forward` 纳入同步后，`back` 在 **0.03s** 返回
`等待条件满足: load_end → https://example.com/?navB=2`（URL 是**后退前**那一页），
据此判定"旧事件假满足"并撤回。**本轮证明该结论错了**：根因是**我的探针与程序自身的启动导航竞争**
（同一轮稍后才由 `history.length = 3` 定位）。

再看那条消息的本质：它来自**事件匹配器**（`MCP_Server.wsv:4732`），
而"事件数据里的 URL"是**事件发生瞬间**记录的地址 —— 历史导航时它**可能仍是导航前的地址**，
即**该 URL 只是文案，不构成"假满足"的证据**。

修好探针（开测前等页面稳定：连续两次用**实时值**读到同一地址）后，把 `back/forward` 重新纳入同步：
**连续三次 5/5 通过**（`_audit/verify_back_forward_wait.py`）：

| 臂 | 期望 | 实测 |
|---|---|---|
| back（默认等载入） | 成功且**回到 A** | ✔ |
| forward（默认等载入） | 成功且**回到 B** | ✔ |
| 显式 `wait_for_load:false` | 立刻返回（快速路径） | ✔ 0.0x s |
| 无历史 | 诚实报错 | `无法前进 — 无导航历史` ✔ |

台账证据也随之升级：`browser_back -> "等待条件满足: load_end → …"`（**真实结果**，不再是回执）。

**结论**：`back/forward` 现在**一次调用即等到载入完成**，与 `navigate/reload` 行为一致；
上一轮 §123.2 的"不纳入同步"决定与理由**均予更正**。

**这是第二次被自己的探针误导**（第一次是早期"冷启动欢迎页有问题"，实为在**已被冷矩阵搞卡的实例**上测量）。
共同特征都是**测量环境不干净**。纪律再强化一条：
**测导航类能力前，必须先确认没有与程序自身的启动导航竞争**（判据：连续两次实时读到同一目标地址）。

### 124.3 类库缺口清单按当前源码刷新（只读子代理，交付 `_audit/_classlib_gap_r106.md`）

| 项 | 值 |
|---|---|
| 当前工具总数 | **314**（全部注册在 `MCP_Server.wsv` 单文件；4 个时刻独立计数一致） |
| 类库基准 | 8 文件 / 188 个类 / **1360 个方法** / 978 个去重名 |
| 证据链 | 328 名有调用或 override 证据 → 零证据 650 → 扣 override → 扣基础设施类 → **239 个能力候选** |
| **A 真缺口（运行期可做）** | **92** 条 |
| **B 仅启动期生效（运行期不可达）** | **55** 条 |
| **C 已被覆盖（含误报消除）** | **31** 条 |
| **旧报告过时结论** | **24** 条 |

**A 组 Top 5（按价值）**：
1. **`类_FBrowser_菜单环境` 全 19 条**（`FBroLib.wsv:3163-3279`）—— 形参 `菜单环境` **已经在三个事件的函数表里**
   （`MCP_BrowserEvents.wsv:2661/2679/2694`）却**零消费点**：**零新增通道成本**，一次让 AI 从
   "某处右键了"升级到"link=… / 选中文本=… / 目标是编辑框"。**CDP 完全没有右键上下文域**，无替代路径。
2. 扩展 `browser_context_menu` 规格格式（`del`/`relabel`/`vis`/`check_at`/`accel_at`/`noaccel` 共 8 条写类方法）——
   工具与通道都已存在，只是规格行当前只认 5 种类型。
3. `FBrowser_JS交互_注册/删除`（`FBroLib.wsv:202/214`）—— 类库原生双向 JS↔宿主查询通道，
   与项目现用的 CDP `Runtime.addBinding` **不是一回事**。
4. `browser_vip_execute_js_context` 增加 `main`/`all_frames`/`frame_index` 三档 target——
   现只接 `框架ID`；`all_frames` 可一次打穿所有 iframe，省"枚举框架→N 次注入"往返。
5. `browser_fill_get_text`/`set_text`（innerText 读写）—— 填表族 13 个工具**唯独没有"取元素 innerText"**，
   而 innerText 与 innerHTML 语义不同、不能互替。

**最要紧的"旧结论过时"**：`显示隐藏窗口`/`移动窗口`/`置自动调整大小` 旧判"真缺口/恒失败桩" → **均已实现**；
菜单 13 条旧判全缺口 → 工具已存在且**已接线 8 条**（该类实有 36 方法，剩 26 条）；
`置Brands`/`置FullVersionList`/`置PlatformVersion`/`置FullVersion` 旧列 **VIP REAL GAP 前 4** → **全部已覆盖**
（**这是旧报告最大的一处过时**）。

**子代理自报的两类反向误报陷阱（值得复用）**：① **注释污染** —— 那些方法名在 src 里**大量只出现在注释与工具描述字符串中**，
不过滤注释会把"未覆盖"误判成"已覆盖"；② **链式调用漏检** —— `取全局 ().取地址Cookie (…)` 的 receiver 以 `()` 结尾，
`[\\w]+\\.` 式正则会漏；③ 泛用短名（`取类型`/`取地址`/`是否为空`）**不采信名称命中**，改按类级可达性重判
（`类_FBrowser_菜单环境` 19 条即由此从"疑似覆盖"翻回真缺口）。

### 124.4 状态与下一步

工具总数 **314**；台账 **314/314** 已测，通过 **307** / 失败 7
（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），**前置缺失 0、能力缺失 0、卡死 0**；
编译 0 警告；fastcheck 41/41。

1. **实现 `类_FBrowser_菜单环境` 消费**（A 组第 1，零新增通道成本）：把 `link`/`选中文本`/`是否可编辑`
   等右键上下文纳入 `context_menu_opening` 事件载荷。
2. 扩展 `browser_context_menu` 的规格类型（`del`/`relabel`/`vis`/`check_at` 等 8 条）。
3. 补 `browser_fill_get_text`（innerText 读）——填表族明显缺口。
4. B 组 55 条"仅启动期生效"需先决定是否做**启动参数通道**（否则整块不可达）。
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
    if '## 124. 第107轮' in text:
        print('!! §124 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 124. 第107轮') == 1
    print('已追加 §124; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
