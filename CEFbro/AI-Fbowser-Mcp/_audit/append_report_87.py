# -*- coding: utf-8 -*-
"""把第 87 节(测试基建事故与修复)追加到 MCP工具可用性检测报告.md。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "MCP工具可用性检测报告.md")

SECTION = """
---

## 87. 测试基建事故：批量给脚本打补丁时"插入不自洽代码"，把快检弄坏了

### 87.1 经过
"控制台 GBK 打印崩溃"这个坑本会话已踩第 5 次(台账 `--status`、两个验证脚本、brace 工具、本轮 `fastcheck`)。
最危险的一次是**本轮 `fastcheck`**: 它在打印统计时崩掉 -> 只留下"退出码 1 + 没有结果",
**看起来像"快检失败", 实际是打印崩了**。这种"崩在打印、吞掉结论"的形态会直接误导判断,
所以决定一次性给 `_audit` 下所有会 `print` 的脚本补上 `import _console`。

### 87.2 我犯的两个错（都是批量改写他人代码时的典型错误）
1. **插入了不自洽的代码**：当目标脚本已 `import sys` 时, 我插入的是
   `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` —— 它**假设 `os` 已被 import**。
   而 `fastcheck.py` 恰好没有 `import os`, 于是插入后立刻
   `NameError: name 'os' is not defined`, **把项目的主力回归测试直接弄坏**。
   更糟的是我当时写的那句三元表达式**两个分支是同一个字符串** —— 看着像做了判断, 实际什么都没判断。
   → **教训: 批量改写时, 插入的代码必须完全自洽, 不假设目标文件里任何既有名字存在。**
2. **漏掉带 BOM 的脚本**：我用 `^(import |from )` 定位 import 区, 而这些老脚本首行是
   `\\ufeffimport io,os`(UTF-8 BOM 就在行首), 正则匹配不到 -> 37 个脚本被记成"找不到 import 区"
   (报错信息本身是准确的, 但我第一版没去追为什么"会 print 却没有 import")。
   → 正确处理: 读用 `utf-8-sig`、写回时按原样保留 BOM(本项目对编码一直很敏感, 见既有纪律)。

### 87.3 修复与结果
`_audit/_repair_console_patch.py` 一次性做三件事, 且**每个文件改前先 py_compile 校验、失败就不改**:
- 把 138 处不自洽片段替换为**自洽片段**(统一用 `_os`/`_sys` 别名, 不依赖目标文件既有名字);
- 给 36 个带 BOM 的脚本补上(保 BOM 写回);
- 自检: 全目录"残留不自洽片段 = 0"。

**验证(关键)**: `fastcheck` 恢复为 **41/41 通过(5.0s)**。
唯一未处理的是 `decode_lost.py`(39 行的一次性数据还原脚本, **整个文件没有任何 import 语句**),
不影响任何测度路径, 如实留档而不强行改。

### 87.4 为什么把这段事故写进报告
前几轮反复强调"**测试脚本自身也会污染环境**", 本轮补上另一半:
**"为了让测试脚本更健壮而做的批量改写, 本身也会污染测试基建"**。
对策与既有纪律一致: ① 插入片段必须自洽; ② 改前先做语法/加载校验, 失败即不改;
③ 改完必须**跑一次真实回归**(本案就是 `fastcheck`)确认基建没被弄坏, 而不是只看"补了多少个文件"。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf" and b.count(b"\r\n") == 0
txt = b.decode("utf-8")
assert "## 87." not in txt
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1))
