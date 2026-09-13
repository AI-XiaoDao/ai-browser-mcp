# -*- coding: utf-8 -*-
r"""第135轮收尾: 报告 ## 155 + `_gap_verified.md` 补第135轮进展。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 155. 第135轮：把台账里 3 条"刻意设计失败"逐条做**受控实测**——全部按 schema 调用可成功，台账 323/323 通过

用户的诉求是"确保**所有显示出来的**能力都能稳定正常执行"。本轮的做法不是改判定口径，而是**逐项在干净实例上实测**
（`_audit/probe_three_gates.py`，每项之间自动重启，避免互相污染）：

| 工具 | 旧台账 | 受控实测结果 | 结论 |
|------|--------|--------------|------|
| `browser_vip_mouse_wheel` | GUARD 失败（缺 delta_y） | 传 `delta_y:120` → **成功 0.02s**，且**页面真的滚动**（注入 3000px 内容，页面侧预言机 `scrollY 0→120`） | 旧失败是**探针没给滚动量**的假目标；能力本身正常 |
| `browser_vip_enable_js_env` | OTHER 失败（缺 confirm） | 传 `{enable:true, confirm:true}` → **成功 0.02s**；之后 execute_js 30.07s、dom_query 10.10s；`enable:false` 后**仍 30.32s** | 按 schema 可成功；**副作用不可逆，必须重启**（已写进描述） |
| `browser_reverse_instrument_script` | OTHER 失败（缺 confirm） | 传 `{action:install, confirm:true}` → **成功 6.49s**（带 `auto_prepared: Debugger.enable`）；之后 execute_js 60s 超时报错、dom_query 30.63s 报错；`action=suppress` → **`setSkipAllPauses 失败: timeout`**，之后仍 35.11s 报错 | 按 schema 可成功；**suppress 已不能恢复**（旧文案被推翻，已订正），必须重启 |

### 155.1 因此产生的代码订正（不是"改口径"，是**改错话**）
- `browser_reverse_instrument_script` 的描述里原写"**suppress 可以恢复(约 45s)**" —— 本轮实测已推翻。
  已改为："suppress 返回 `setSkipAllPauses 失败: timeout`，之后仍 35 秒超时 ⇒ **安装后请准备重启进程**；
  旧文案的结论不要再依赖"。
- `browser_vip_enable_js_env` 的描述补上**实测数字**与"`enable:false` **不会**恢复（关闭后仍 30.32s）⇒ 必须重启"。
- 两个"确认闸门"在 `_audit/mass_probe.py` 里补了 `DYNAMIC_ARGS`（探针也按 schema 传 `confirm:true`），
  否则台账永远记一条"没传 confirm 被拒"的**假失败**——这与当初 `browser_find_by_hwnd` 用假句柄、
  `mcp_result` 用假 id 是同一类测量缺陷。

### 155.2 验收与状态
- `_audit/verify_round130/131/132/133/134.py` 等本轮既有验收全部保持通过；快检 **56/56**（干净实例）；
  编译 **0 警告**；卫生扫描**全零**；
- **台账 323/323 已测 = 323 通过 / 0 未通过**（3 条"刻意设计失败"改为**受控实测条目**：status=pass +
  实测证据 + "用后需重启"的硬约束，做法与 `browser_close_try` / `browser_debugger_pause` 一致）。

### 155.3 仍未解决的真实限制（如实记录，下一轮候选）
两个"闸门"的副作用**今天确实是不可逆的**：它们会打死本会话的 CDP/JS 通道，只有重启能恢复。
要让 `install` 从"用完即废"变成"可稳定连续使用"，需要给 CDP 暂停加**自动 resume 钩子**
（本项目已有"卡死自救"的先例：超时且存在未处理 `Debugger.paused` 时自动 resume 并重试；
把它前移到**事件到达时立即 resume** 即可让被自己的插装拦住的 `Runtime.evaluate` 顺利返回），
这是一处**真正的能力升级**，需要实现 + 独立验收，列入下一轮。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 155.' in text:
        text = text[:text.index('## 155.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第135轮进展**'
    old = '> **第134轮进展**'
    add = (mark + '：按要求把 3 条"刻意设计失败"逐条**受控实测**（干净实例、项间自动重启）：三个工具**按 schema 传参都能成功**'
           '（mouse_wheel 0.02s 且页面真的滚动 scrollY 0→120；enable_js_env 0.02s；instrument install 6.49s），'
           '旧失败全是**探针没传必填参**造成的假目标 ⇒ 已补 `DYNAMIC_ARGS`(confirm) 并改写为受控台账条目，'
           '**台账 323/323 通过 / 0 未通过**。同时实测推翻一处旧文案：`instrument_script` 的 `action=suppress` '
           '**已不能恢复**（`setSkipAllPauses 失败: timeout`，之后仍 35s 报错），描述已订正为"必须重启进程"；'
           '`enable_js_env` 描述补上"enable:false 不恢复(关闭后仍 30.32s)"。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第135轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
