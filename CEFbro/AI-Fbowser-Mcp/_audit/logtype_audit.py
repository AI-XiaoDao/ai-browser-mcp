# -*- coding: utf-8 -*-
"""系统性审计"只写不读"的 log_type。

已复现三次的缺陷模式: 某功能把结果写入 event_log 的某个 log_type, 但**没有任何读者**支持该类型
-> 用户看到"成功"却永远拿不到结果(静默假成功):
  · cdp_monitor  : 写入后全项目无读取方(已修)
  · watch_changed: browser_event 的支持列表里根本没有该类型(已定位)
本脚本把这种模式一次性查全: 写出"写入的 log_type 集合"与"读取的 log_type 集合"的差集。

用法: py -3 logtype_audit.py
"""
import io
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")

WRITE_RE = re.compile(r'记录事件日志 \("([^"]+)"')
# 查询事件日志 (日志类型, 事件名, 浏览器ID, 条数)
READ_RE = re.compile(r'查询事件日志 \("([^"]*)"')

# browser_event 支持的事件类型(取自工具运行时的"未找到事件…支持:"提示)
BROWSER_EVENT_SUPPORT = set("""
load_start load_end load_error crash navigate popup popup_failed loading_state_change
url_changed browser_created browser_closing do_close title_changed load_progress
js_dialog before_unload file_dialog fullscreen favicon find_result key_press
""".split())
BROWSER_EVENT_PREFIX = ("resource_", "frame_", "download_", "focus_", "app_")


def main():
    writes = {}   # log_type -> [(file, line)]
    reads = {}    # log_type -> [(file, line)]
    dyn_reads = []  # 非字面量的读取点(如查询事件日志 ("", "", ...) 的时间线模式)
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".wsv"):
            continue
        for i, ln in enumerate(io.open(os.path.join(SRC, fn), encoding="utf-8",
                                       errors="replace"), 1):
            if ln.lstrip().startswith("//") or ln.lstrip().startswith("#"):
                continue
            for m in WRITE_RE.finditer(ln):
                writes.setdefault(m.group(1), []).append("%s:%d" % (fn, i))
            for m in READ_RE.finditer(ln):
                t = m.group(1)
                if t == "":
                    dyn_reads.append("%s:%d" % (fn, i))
                else:
                    reads.setdefault(t, []).append("%s:%d" % (fn, i))

    only_written = {k: v for k, v in writes.items() if k not in reads}
    print("== '只写不读' log_type 审计 ==")
    print("写入的 log_type 共 %d 种; 被显式读取的 %d 种" % (len(writes), len(reads)))
    print("全类型读取点(时间线模式, 会读到所有类型): %s" % (dyn_reads or "无"))
    print()
    print("---- 写入但**没有任何显式读取方**的 log_type (%d) ----" % len(only_written))
    for k in sorted(only_written):
        mark = ""
        if k in BROWSER_EVENT_SUPPORT or k.startswith(BROWSER_EVENT_PREFIX):
            mark = "  [browser_event 支持该类型, 可经 event_type 查询]"
        else:
            mark = "  ★ 不在 browser_event 支持列表里 -> 用户无从读取(疑似静默假成功)"
        print("   %-18s %s%s" % (k, only_written[k][:3], mark))
    print()
    print("---- 被读取的 log_type ----")
    for k in sorted(reads):
        print("   %-18s %s" % (k, reads[k][:2]))


if __name__ == "__main__":
    main()
