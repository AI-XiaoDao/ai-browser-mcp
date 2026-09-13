# -*- coding: utf-8 -*-
"""在 fastcheck 序列内复现 highlight clear 超时:
隔离复现 5/5 通过(0.02s), 说明与"前序调用留下的状态"有关。
故连跑 fastcheck 直到失败, 打印失败点及其前若干行上下文, 以定位是哪个前序步骤造成的。"""
import io
import os
import subprocess
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    for i in range(1, 7):
        p = subprocess.run([sys.executable, os.path.join(HERE, "fastcheck.py")],
                           cwd=HERE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        out = (p.stdout or "") + (p.stderr or "")
        lines = out.splitlines()
        summary = [l for l in lines if "结果:" in l]
        print("--- 第 %d 次: 退出码=%s %s" % (i, p.returncode,
                                          summary[-1].strip() if summary else "(无汇总)"))
        if p.returncode != 0:
            print("    ★ 复现失败! 失败点前后上下文:")
            fail_idx = [k for k, l in enumerate(lines) if "[FAIL]" in l]
            if fail_idx:
                k = fail_idx[0]
                for l in lines[max(0, k - 18):k + 3]:
                    print("      " + l)
            else:
                print("      (未找到 [FAIL] 行, 末尾 20 行:)")
                for l in lines[-20:]:
                    print("      " + l)
            return 1
    print("   连跑 6 次均通过 —— 本轮未复现")
    return 0


if __name__ == "__main__":
    sys.exit(main())
