# -*- coding: utf-8 -*-
r"""第133轮收尾: 报告 ## 153 + `_gap_verified.md` 补第133轮进展（schema 一致性审计维度收官）。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 153. 第133轮：schema ↔ 实现一致性审计**收官**（323 个工具：MISSING=0、无 no-op 声明）

### 153.1 本轮清掉最后三个"声明了但实现从不读"的参数
用 `_audit/_show_branch_params.py --diff --closure` 复核后确认：
| 工具 | 被删的声明 | 为什么它是 no-op（源码核实） |
|------|-----------|------------------------------|
| `browser_debugger_last_paused` | `parse` | 全项目只有 `Core:5614` 在读 `parse`，而那属于 **evaluate** 的分支；`last_paused` 自己从不读 —— 是复制粘贴留下的残留（它的 schema 误抄了 evaluate 的参数） |
| `browser_reverse_scan_crypto` | `script_index` | 全项目只有 `Core:8019` 在读 `script_index`，属于 **reverse_extract 的 mode=download**；本工具是"扫描全部脚本"，传了会被**静默忽略** |
| `browser_reverse_detect_obfuscator` | `script_index` | 同上 |

处理：删除这三个 no-op 声明，并在描述里**给出真正能限定范围的路径**
（`browser_reverse_search_script` / `browser_reverse_extract mode=scan` 拿脚本 →
`browser_reverse_extract mode=download(script_index)` 取内容）—— 限制要说清楚，而不是留一个"看着能设其实无效"的参数。

### 153.2 收官判据（`_audit/verify_round133.py`，5/5）
- 全量 323 工具扫描：**MISSING = 0**（没有任何"实现读了却代理看不到"的参数）；
- **疑死参数 = 0**（没有任何"声明了却从不读"的参数）；
- 被改的三个工具真机回归可用；`last_paused` 还顺带展示了既有的零前置自愈
  （`auto_prepared: Debugger.pause(页面原本未暂停, 已自动启用调试器域并安排执行点制造暂停点…)`）。

唯一剩下的扫描差异是 `browser_evaluate.max_ms` —— 它是**入口公共参数**（由公共层读取，不是分支体），已在报告里标注为非缺陷。

### 153.3 本轮两次踩坑（都记进脚本注释，避免再犯）
1. **往描述里加文字，锚点不要包含结尾引号**：我按"…算法"（含引号）做替换，结果新文字落到**字符串外面**，
   编译直接报 `发现字符处于无效位置`（第11516/11518 行）。
2. **删 schema 实参时锚点要覆盖到该实参的全部**：`parse` 那处漏了 `, 假`，于是"锚点不存在、静默跳过"；
   而回读断言用"参数名是否出现在这一行"也不可靠 —— 新写的说明文字里同样会出现 `script_index`，会误判成功。
   已改为 `属性项JSON ("名"` 这种**声明形态**匹配。
   ⇒ 两处修法都是**整行重写**（而不是局部替换），一次改对；编译通过 + 扫描归零双重确认。

### 153.4 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
**schema 一致性维度至此收官**：`py -3 _audit\\_show_branch_params.py --brief --closure` 随时可复跑复核（期望：MISSING=0、疑死=0）。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 153.' in text:
        text = text[:text.index('## 153.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第133轮进展**'
    old = '> **第132轮进展**'
    add = (mark + '：**schema↔实现一致性审计收官** —— 清掉最后三个 no-op 声明'
           '（`debugger_last_paused.parse`、`reverse_scan_crypto.script_index`、`reverse_detect_obfuscator.script_index`，'
           '三者都是"声明了但实现从不读"，且已在描述里给出真正能限定范围的替代路径）。'
           '全量 323 工具扫描结果：**MISSING=0、疑死=0**（唯一剩余差异 `evaluate.max_ms` 属入口公共参数，非缺陷）。'
           '验收 5/5（含三个工具的真机回归）。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第133轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
