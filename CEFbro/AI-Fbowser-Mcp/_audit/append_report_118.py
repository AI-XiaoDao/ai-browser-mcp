# -*- coding: utf-8 -*-
"""追加报告第 118 节（第 101 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 118. 第101轮：★`browser_scrape` 冷启动**返回错误页面数据**（静默错数据）已修 + 转换器取键修复

### 118.1 起因：上一轮撤回 `browser_scrape` 的"空串"根因查清

第100轮把 `browser_scrape` 纳入同步后回**空串** `""`，当时只能撤回。本轮查清：
它的异步最终载荷是 **`{"success":true,"text":"Example Domain"}`** —— 数据放在**工具专属键 `text`** 下；
而中央转换器 `将异步结果转为命令响应`（`MCP_Server.wsv:6260`）取 `内容` 时只试
`message` → `result` → `error`，**从不读它自己已经收到的那个"结果键名"参数**（该参数只被用作**输出**键名）。
于是 `内容` 为空 → 响应里数据为空。

**两处修复（都很小且通用）**：
1. 转换器补上"按 `结果键名` 取值"的回退分支 ⇒ 任何"数据放在专属键下"的工具都能正确同步。
2. `取工具结果键名` 为 `browser_scrape` 补 `"text"` 映射（该方法原有 20 个分支，没有 scrape）。

修后 `browser_scrape` **重新纳入同步名单**，实测一次调用即得结果（台账改为带真实数据的 pass：`Example Domain`）。

### 118.2 ★真缺陷：冷启动后**第一次** scrape 返回的是**欢迎页**的数据

修好取键后立刻暴露一个更严重的问题（`_audit/diag_scrape_welcome_race.py`，全新进程）：

```
第1次 0.03s isError=False -> AI浏览器 MCP Server     ← 欢迎页的 h1（目标却是 example.com）
第2次 0.05s isError=False -> Example Domain
第3次 0.02s isError=False -> Example Domain
```

**这是"静默错数据"** —— 比报错危险得多：调用方拿到的是**另一个页面**的、看起来完全合理的内容。
而且 0.03s 根本不够完成"导航 + 提取"，说明它压根没等导航。

**根因**（`MCP_Server_Core.wsv` 爬虫状态机 Phase 0）：判据只有"未加载"这一半 ——

```
如果 (浏览器容器.取加载状态 () == 假)     // "不在加载中" 就认为加载完成
{
    scrapePhase = 1
}
```

而 `sFrame.载入地址 (sUrl)` 刚调用的那一瞬间，容器的加载状态**还没翻成"加载中"**，
于是 Phase 0 立刻判定"已完成" → 进 Phase 1/2 → 从**当前仍在显示的欢迎页**提取。
第二次调用之所以正确，只因为浏览器此时已经停在 example.com 上了 —— 也就是**首次调用必错**。

**修法**：给 Phase 0 补上"页面确实换了"这一半。提交任务时记下 `target_url` 与
`prev_url`（提交那一刻的页面地址）；Phase 0 只有在**当前地址已不再是 prev_url**（或目标本就等于
当前页，即"就是抓当前页"）时才允许前进：

```
如果 (sTargetUrl != "" && sPrevUrl2 != "" && sTargetUrl != sPrevUrl2 && sCurUrl == sPrevUrl2)
{
    sPageChanged = 假          // 页面还没换过去，继续等
}
如果 (sPageChanged && 浏览器容器.取加载状态 () == 假) { scrapePhase = 1 }
```

**双向验收**：

| 臂 | 修复前 | 修复后 |
|---|---|---|
| 冷启动第一次 scrape（目标 example.com） | `AI浏览器 MCP Server`（**错页面**） | `Example Domain` ✔（并连做 4 次均正确） |
| 目标不可达（黑洞地址 `10.255.255.1`，`max_ms=6000`） | 会立刻提取旧页面 → 返回**错数据** | **如实超时** `⏱ 操作超时(6s)`（用时 6.3s）✔ |

第二臂是这个修复的**安全性质**：宁可诚实超时，也绝不退回"拿上一个页面的数据充数"。

### 118.3 本轮两次自身失误（都由工具当场抓住）

- **作用域错误**：我把 `变量 sPrevUrl` 声明在 `如果 { … }` 块内部，却在块外使用 →
  编译报 `没有找到所指定的常量/变量/参数名称"sPrevUrl"`。火山里块内声明的变量作用域限于该块，
  **声明必须提到外层**。已修正并重编（0 警告）。
- **探针脚本自身的语法错**：`print("…" 上一个页面 "…")` —— 双引号字符串里嵌了 ASCII 双引号。
  与本项目 `.wsv` 里反复踩的坑是同一个；改用 `「」`。

### 118.4 状态

台账 **313/313** 已测，通过 306 / 失败 7（性质分布不变：TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），
**前置缺失 0、能力缺失 0、卡死 0**；编译 0 警告；fastcheck 41/41。

### 118.5 下一步

1. **`browser_intercept` 增 `unmodify`/`unreplace`**（子代理已给出精确落点与本机可验收的测试面）。
2. **`browser_context_menu`（方案甲）**：预置规格 + 回调内一次性施加（CEF 头逐字禁止回调外持引用）。
3. 复查其它"多阶段状态机"是否也有同类**判据缺失**：本轮证明"只看终态、不看起始态"的判据会漏掉竞态
   （`browser_scrape` 的 phase 0 即此类；建议对 `browser_wait`/`browser_print_to_pdf` 等含 `_phase`/
   `_load_phase` 的实现做一次同样的"起始态是否被确认"检查）。
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
    if '## 118. 第101轮' in text:
        print('!! §118 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 118. 第101轮') == 1
    print('已追加 §118; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
