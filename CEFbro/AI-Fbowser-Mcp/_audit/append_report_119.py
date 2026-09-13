# -*- coding: utf-8 -*-
"""追加报告第 119 节（第 102 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 119. 第102轮：把"导航完成判据"这一类**系统性查完**（scrape 是唯一漏网者）+ 删死字段

### 119.1 起点：上一轮修 scrape 竞态时发现，项目里**早就存在正确判据**

`browser_navigate`（`MCP_Server_Core.wsv:130-147`）的做法是对的，而且比 scrape 原来那套更强：

```
// 同址导航: 主框架已在目标URL且未在加载时直接返回成功(载入地址前判等, 无竞态);
如果 (navFrame.取地址 () == url && 浏览器容器.取加载状态 () == 假) { …已在目标页面… }
// 记录导航发起时刻(载入地址前), 供注册加载等待任务判序load_end是否属于本次导航
导航发起毫秒 = 取启动时间 ()
navFrame.载入地址 (url)
→ 注册加载等待任务 (…, 导航发起毫秒)
```

而 `注册加载等待任务` 的判据（`MCP_Server.wsv:6612`）是：

```
如果 (浏览器容器.取加载状态 () == 假 && 导航发起毫秒 > 0 && 浏览器容器.取最后载入结束毫秒 () >= 导航发起毫秒)
```

即**"本次导航发起之后确实发生过一次 load_end"**。该处注释（:6607）还写明了它修的就是同一类问题：
> 导致wait_for_load立即返回未完成的提交消息; 现仅当本次导航发起后确实发生过load_end(时间戳>=导航发起毫秒)

⇒ **`browser_scrape` 当时是自己手写了一个更弱的 Phase 0**（只看"未加载"），才漏掉这个竞态。
这正是"不重复造轮子"被违反时会发生的事。

### 119.2 本轮改动：让 scrape 复用**同一信号**（不另造第三套）

上一轮我用"页面地址变了"判定；本轮补上项目既有的时间戳信号，两者取**或** —— 任一证据成立即认为导航已发生：

| 证据 | 覆盖的情形 |
|---|---|
| 地址已变（上一轮加的） | 正常导航、跳转/重定向 |
| `取最后载入结束毫秒 () >= nav_start_ms`（本轮加，与 navigate 同款） | **目标就是当前页 / 原地重载，地址不变** |

提交任务时把 `nav_start_ms` 一并存下（在 `载入地址` **之前**取时刻，与 navigate 一致）。

**三臂验收**（`_audit/verify_scrape_dual_evidence.py`，**3/3**）：

| 臂 | 期望 | 实测 |
|---|---|---|
| 1 冷启动第一次调用（地址会变） | 拿到**目标页**数据 | `Example Domain` ✔ 0.09s |
| 2 目标==当前页（地址不变，靠时间戳证据） | **不误判也不死等** | `Example Domain` ✔ 0.04s |
| 3 目标不可达（两个证据都等不到） | **如实超时**，绝不返回上一个页面的数据 | `⏱ 操作超时(6s)` ✔ 6.2s |

臂 2 是上一轮单靠地址判据时**会死等**的情形，本轮被时间戳证据救回；臂 3 则由两者共同保证安全。

### 119.3 ★系统性排查结论：这一类只有 scrape 一个漏网者

把全库**所有"发起导航"的调用点**逐一核对（`_audit/scan_nav_judgements.py`）：

| 调用点 | 完成判据 | 判定 |
|---|---|---|
| `Core:139` `browser_navigate` | 记录发起时刻 + `注册加载等待任务`（load_end≥发起时刻） | **正确** |
| `Core:236/240` `browser_reload` | 同上（该方法注释即"供 navigate/reload 的 wait_for_load 共用"） | **正确** |
| `MCP_Server.wsv:198` 欢迎页导航 | 自带 `欢迎页导航发起毫秒` 时间戳（:88-115） | **正确** |
| `Core:2815` `browser_scrape` | 原为"只看未加载" | **缺陷 → 本轮已修** |
| `Core:199/214` `browser_back/forward` | **不等待**，只回"已后退/已前进" | **非缺陷**：不声称"已加载"，也不消费页面数据 |
| `Core:5244` 自动导航（断点自动流程） | 固定 `延时(1000)` 后进"等断点命中"循环 | **非缺陷**：不声称已加载 |
| `BrowserEvents:1285` 重定向处理 | 只是执行重定向 | **非缺陷** |

⇒ **"发起导航后用裸'未加载'判据决定是否读数据"这一类，全库仅 scrape 一处**，现已消除。

**顺带澄清一个"看起来像、其实不是"的点**：`browser_wait {what:"load_end"}` 在页面空闲时会**立即成功**。
这**不是**同类缺陷 —— 该工具**只观察、不发起**任何导航；"等待'不在加载中'"在已经空闲时**本就已满足**。
（`load_start` 同理走"当前加载==期望加载"或事件驱动 `解析等待任务`。）真正的坑只在**自己发起了导航却不去确认它**。

### 119.4 删死字段 `_load_phase`（写而不读）

全库扫描：`_load_phase` **仅 1 处出现** —— `MCP_Server_Core.wsv:2776` 的写入，**无任何读取点**。
它写入的是常量 `0` 且从不更新，却暗示存在一个并不存在的阶段机（属**误导性死字段**）。
已删除（`_audit/del_dead_load_phase.py` 自带"全库仅此一处、否则中止"的前置校验）；
删后全库出现 0 次，编译 0 警告、fastcheck 41/41。

### 119.5 本轮自身失误（编译当场抓住，已修）

把 `浏览器容器.取最后载入结束毫秒 ()` 误写成 `MCP命令服务器.取最后载入结束毫秒 ()` →
`错误: 没有找到所指定的常量/变量/参数名称"MCP命令服务器"`。
根因：**该访问器属于类 `浏览器容器`**（`MCP_Server.wsv:5` 起的类），不是 `MCP命令服务器`；
而紧邻的下一行本来就写着 `浏览器容器.取加载状态 ()` —— 抄近邻的限定名就不会错。

### 119.6 状态与下一步

台账 **313/313** 已测，通过 306 / 失败 7（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），
**前置缺失 0、能力缺失 0、卡死 0**；编译 0 警告；fastcheck 41/41。

1. **`browser_intercept` 增 `unmodify`/`unreplace`**（子代理已给精确落点，本机可验收）。
2. **`browser_context_menu`（方案甲）**：CEF 头逐字禁止回调外持引用，只能"预置规格 + 回调内施加"。
3. 可考虑：`browser_back`/`forward` 是否补 `wait_for_load`（现在只回"已后退"，调用方需自行等页面）——
   属**能力增强**而非缺陷，取决于真实调用频率。
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
    if '## 119. 第102轮' in text:
        print('!! §119 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 119. 第102轮') == 1
    print('已追加 §119; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
