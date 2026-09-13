# -*- coding: utf-8 -*-
"""追加报告第 121 节（第 104 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 121. 第104轮：`browser_permission_spoof` 复核后**重新纳入同步**（第100轮那次超时不可复现）

### 121.1 先查"到底哪里卡住了"：任务本身是好的

第100轮把它纳入同步后出现 **20s 超时**，当时只能撤回。本轮先把它的异步任务拆开看：

```
异步调用 -> {"_async":true,"task_id":"task_45147250_62307_2",
             "message":"权限API伪装已注入 | 权限:… → granted"}
第 1 次 mcp_result 轮询 -> {"success":true,
             "message":"Permissions API 已伪装: geolocation,notifications,…,clipboard-write → granted",
             "data":"…"}
```

即 **任务立即完成**（首次轮询就拿到真实内容，不是 `_waiting`）——
所以"超时"不在任务侧，也不在 `查询异步结果` 侧（两者都正常返回）。

### 121.2 用请求级 `sync_wait` 强制走同步路径复现 —— 复现不出来

`应同步等待` 的第一条判据就是请求里的 `sync_wait`，因此**不改源码**就能走同步路径：

```
browser_permission_spoof {action:"apply", sync_wait:true, max_ms:15000}
  -> 用时 0.05s isError=False
     "Permissions API 已伪装: geolocation,…,clipboard-write → granted"     ← 无超时
```

⇒ 第100轮那次 20s 超时**属当时环境**（那轮脚本在同一进程里连续跑了 12 个工具，
它排在第 12 位；疑似前序工具的残留状态所致），**不是工具缺陷**。

### 121.3 重新纳入名单 + 走**真实名单路径**再验（3/3）

按流程：重新加进 `应同步等待` 与 `取同步等待毫秒` 两张表（注入组，预算 20000），
然后**不传 `sync_wait`**、只用 `{action:"apply"}`（第100轮正是这一形态超时的）复验：

| 臂 | 期望 | 实测 |
|---|---|---|
| A 纯 `{action:"apply"}` | 一次调用即得结果 | **0.04s** `Permissions API 已伪装: … → granted`，无 `_async`、无超时 ✔ |
| B 连续 5 次 | 不劣化 | 0.02–0.03s × 5，全部成功 ✔ |
| C 先跑 `canvas_noise` + `inject` 后再调（**复刻第100轮上下文**） | 仍成功 | 0.04s 成功 ✔ |

台账该条已重测为带**真实数据**的 pass（原先只是异步回执）。

### 121.4 纪律补充（本轮的做法本身值得记）

「一次超时 → 撤回」在当时是正确处置（宁可退回已知可用状态），但**不能让结论停在撤回**：
本轮补了三步——① 查清任务侧是否正常；② 用 `sync_wait` 在不改源码的前提下复现；
③ 复现失败后带**压力臂**与**原上下文复刻臂**重新纳入。
若将来这个 20s 超时**再现**，处置办法已写死在源码注释与本节：再次撤回该名单项，
并按报告记录继续定位（届时优先怀疑"前序工具残留状态"，而非该工具本身）。

### 121.5 状态与下一步

台账 **313/313** 已测，通过 306 / 失败 7（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），
**前置缺失 0、能力缺失 0、卡死 0**；编译 0 警告；fastcheck 41/41。
至此**取数据/需落地确认类工具已有 11 个**实现"一次调用即得结果"
（10 个见 §117，本轮 +权限伪装）。

1. **`browser_context_menu`（方案甲）**：CEF 头逐字禁止回调外持引用 → 预置规格 +
   在 `浏览器_即将打开菜单` 回调内一次性施加；注意"规格为空必须跳过而非清空""每次右键都要重施"
   "命令ID 必须落在 26500..28500"。
2. 复查 `browser_back`/`browser_forward` 是否补 `wait_for_load`（现只回"已后退/已前进"，不声称已加载）。
3. 类库 `类_FBrowser_命令行` 14 项属"仅启动期生效"，需先决定是否做启动参数通道。
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
    if '## 121. 第104轮' in text:
        print('!! §121 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 121. 第104轮') == 1
    print('已追加 §121; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
