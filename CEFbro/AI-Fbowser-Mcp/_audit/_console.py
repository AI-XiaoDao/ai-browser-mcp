# -*- coding: utf-8 -*-
"""控制台 UTF-8 兜底 —— 本会话已第四次栽在同一个坑上, 故抽成一份共用实现。

现象: 项目消息里含 ⚠(U+26A0) 等字符, 而 Windows 控制台默认 GBK 代码页 ->
      `print` 抛 UnicodeEncodeError, 脚本**在打印阶段崩掉**, 于是
      "断言明明跑完了, 结论却丢了"(两次害得"反向对照用例"没跑完,
      更早一次害得台账 `--status` 整个总览打不出来)。

用法(每个会打印中文/emoji 的诊断脚本, 第一件事就是):
    import _console   # noqa: F401  (导入即生效)

注意: 必须用 errors="replace" 兜底 —— 宁可少一个字符, 也不能因为一个 emoji
      把整轮结论吞掉(这是本会话反复吃亏的根因: 崩在打印, 而不是崩在测量)。
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # 极老解释器无 reconfigure: 保持原样, 不影响测量
