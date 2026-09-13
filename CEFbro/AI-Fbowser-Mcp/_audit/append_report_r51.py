# -*- coding: utf-8 -*-
import io, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
SEC = u'''
---

## 81. 第 47–51 轮：`browser_kernel_watch` 收尾、log_type 审计与五次自我纠正

### 81.1 `browser_kernel_watch` 的最终定位

| 结论 | 证据 |
|---|---|
| 采样器**确实在跑** | 副作用探针：`expression="(window.__w=(window.__w||0)+1)"` → `window.__w` 1→2→3 每秒递增 |
| 采样器**确实成功提交**页面求值 | 同上（副作用真实发生） |
| 已修一处**确凿判据错误** | `如果 (提交返回 == "")` 只在"提交返回空串"时登记任务ID，而 `提交异步JS任务` **成功时返回非空回执**（本项目统一以 `是否以 (提交返回, "{\\"error\\"")` 判失败）→ 语义反了，已改为按 error 前缀判失败 |
| "`置监视平行值` 不追加新键"的推断 | ❌ **已查证并推翻**：其 `已更新==假` 分支确实 `加入成员 (键 + "=" + 值)`，与 `取监视平行值`（按 `键=` 前缀匹配）配对正确 |
| 监视**必然变化**的表达式仍无产出 | `String(Date.now())` 跑 4 秒 → 时间线搜不到 `watch_changed` → 排除"我测试表达有误" |
| **输出通道不存在**（关键） | `browser_event {"event_type":"watch_changed"}` → "未找到事件: watch_changed"，且其**支持类型列表里根本没有 `watch_changed`** |

**即 `browser_kernel_watch` 的成功回执承诺"变更记录为 `watch_changed` 事件"，而唯一的读者不认这个类型。**
修法二选一（或都做）：① 把 `watch_changed` 加入 `browser_event` 的类型白名单；② 让该工具自带 `get` 返回
各 key 的最近值与变更历史（不依赖事件系统，更直接）。

**顺带得到的权威事件类型词表**（取自 `browser_event` 运行时提示，比从 58 个调用点反推更准）：
`load_start / load_end / load_error / crash / navigate / popup / popup_failed / loading_state_change /
url_changed / browser_created / browser_closing / do_close / title_changed / load_progress / js_dialog /
before_unload / file_dialog / fullscreen / favicon / find_result / key_press` + 通配族
`resource_* / frame_* / download_* / focus_*` + 应用事件 `app_*`。
**可发现性问题**：描述里写 `load_end/crash/...`，实际需按通配写法（如 `resource_*`）传，值得在描述里补明。

### 81.2 新增系统性审计：`_audit/logtype_audit.py`（"只写不读"）

把已复现三次的缺陷模式（`cdp_monitor` / `watch_changed` / 疑似的 `network_detail`）做成一次查全：
对比"写入 `event_log` 的 `log_type` 集合"与"被读取的 `log_type` 集合"。

首轮结果：写入 7 种、被显式读取 6 种；**写入但无显式读取方 = `network_detail`、`watch_changed`**。

**⚠️ 该审计的重要局限（已被本轮实测证伪一次）**：它**只识别字面量类型的读取点**
（`查询事件日志 ("TYPE", …)`），对**非字面量/其它读取路径**会漏判 → **只能产出候选，不能作为结论**。
这与类库缺口审计"字面量匹配 → 误报"的教训**完全同构**。

### 81.3 `network_detail` 经真机核验为**假阳性**（审计局限的实证）

```
browser_network {"action":"detail_enable"} → 网络日志已启用(详细模式)
browser_network {"action":"list"} → {"network_detail":true,"network_logs":[
   {"type":"res","url":"…","content_length":318,"mime":"text/html",
    "response_headers_json":"{\\"allow\\":\\"GET, HEAD\\",\\"cf-cache-status\\":\\"MISS\\",…}"}]}
```

详细模式**返回了完整响应头与内容长度** → **有读取方**，不是缺陷。审计的"无显式读取方"应准确理解为
"**没有字面量类型的专用读取通道**"。`watch_changed` 则是经**双重实测**（不在支持列表 + 全类型时间线也搜不到）
确认为真问题，与 `network_detail` 区分开。

### 81.4 本会话自我纠正累计 **5 次**（每次都由"验证优先"拦下）

| # | 当时的错误结论 | 真因 |
|---|---|---|
| 1 | 冷启动 `Debugger.enable` 超时 → 欢迎页有问题 | 测量跑在**已被搞卡的实例**上（前序工具杀的 CDP） |
| 2 | `browser_get_text` 全文模式搞挂 CDP | 同上（真凶是前序**内核级鼠标注入**） |
| 3 | 反应器"只有 `*` 生效、具体事件名对不上" | **观测量被覆盖**：只看最终标题，而页面自身标题赋值盖回了 |
| 4 | `browser_event` 忽略 `event` 过滤 | 参数名是 **`event_type`**，我传了不存在的 `event` |
| 5 | `network_detail` 只写不读 | 审计只匹配**字面量读取点**，漏了 `browser_network` 的读取路径 |

**方法论（已稳定成型，建议作为本项目长期纪律）**：
1. 下结论前先确认**测量环境干净**；
2. 用**不可被后续动作覆盖的副作用**作观测口径（事件时间线 / 页面侧标记 / 计数器）；
3. 尽量用**两条独立通道**同时取证；
4. **改代码前先查证假设**（第 4、5 两次都是"一查才发现是自己错"）；
5. 任何**字面量模式匹配**的审计（类库缺口、log_type）**只产出候选**，必须逐个真机核验；
6. 有效手法沉淀：**副作用探针**（自增表达式判定函数是否真被进入）、**同条件对比**（两条规则/两臂同时注册）、
   **含对照臂**（用一个不存在的名字作对照，证明测试能区分真伪）。

### 81.5 其余可复用结论

- **`browser_cdp_call` 是任意 CDP 方法的全量透传**（无域白名单）→ 第四类误报来源（详见 80.1）。
- 请求级公共参数 `browser_id` / `max_ms` / `sync_wait` / `async_only` / `wait_for_load`（详见 80.2）；
  **DSH 的 read/grep 在 `MCP_Server.wsv` 上少计 3 行**，引用该文件请用代码锚点。
- 回归护栏：`loop.py` 已加 **8 秒稳定期**（修掉"重启后立即跑快检"的偶发失败，4/4 验证通过）；
  `mass_probe.build_args` 返回**元组**必须解包（漏解包会让整轮数字失真）。
- 台账 `_audit/tool_ledger.py`：**60/301**，前置缺失 0、卡死 0；30 个功能一轮 0.9 秒。
'''
with io.open(P, 'a', encoding='utf-8') as f:
    f.write(SEC)
print('已追加, 行数=%d' % len(io.open(P, encoding='utf-8').read().splitlines()))
