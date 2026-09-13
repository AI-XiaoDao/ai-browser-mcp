# -*- coding: utf-8 -*-
"""删除 MCP_Server_Core.wsv 里 6 个**永不可达**的重复分支。

可达性证明（已核实源码）:
  MCP_Server.wsv 路由器是 如果/否则 链: `否则 (是否以 (方法名,"browser_reverse_"))`
  → `result = MCP_逆向分派.分类分派_逆向操作(...)`; 只有 `result == ""` 时才进回退链
  (回退链依次试 核心/填表/VIP/系统/编排/内核, **不含逆向分派**)。
  而 MCP_Server_Reverse.wsv 对这 6 个工具**都有分支**, 必返回非空响应
  → Core 里那 6 份永远不会被执行, 属死代码, 且其中多份内容已与 Reverse 不一致(维护隐患)。

安全措施: 先备份; 用 vlib 的括号配对定位 `否则 (...) { ... }` 块的闭括号; 删除后立即语法自检。
用法: py -3 del_dead_branches.py           # 演练(只报告)
      py -3 del_dead_branches.py --apply   # 实际删除
"""
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vlib
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

TARGET = "MCP_Server_Core.wsv"
TOOLS = ["browser_reverse_call_fn", "browser_reverse_cdp_hook", "browser_reverse_dom_breakpoint",
         "browser_reverse_heap", "browser_reverse_preload", "browser_reverse_websocket"]


def find_block(ls, db, da, tool):
    """返回 (起始行idx, 结束行idx) —— 即 `否则 (方法名 == "tool")` 到其块闭括号, 含两端。"""
    pat = '否则 (方法名 == "%s")' % tool
    for i, ln in enumerate(ls):
        if pat in ln:
            base = db[i]
            for j in range(i + 1, len(ls)):
                if da[j] == base:
                    return i, j
            return i, len(ls) - 1
    return None


def main():
    apply = "--apply" in sys.argv
    ls, (enc, eol, bom, raw) = vlib.lines_of(TARGET)
    _, db, da = vlib.brace_map(TARGET)

    # 前置校验: Reverse 里必须有这 6 个分支(否则不能删 Core 的)
    rev, _ = vlib.lines_of("MCP_Server_Reverse.wsv")
    missing = [t for t in TOOLS if not any('否则 (方法名 == "%s")' % t in l for l in rev)]
    if missing:
        print("!! 中止: 逆向分派缺少分支 %s —— 删 Core 会让这些工具失效" % missing)
        return 2

    ranges = []
    for t in TOOLS:
        r = find_block(ls, db, da, t)
        if r:
            ranges.append((t, r[0], r[1]))
        else:
            print("   (未找到) %s" % t)
    ranges.sort(key=lambda x: -x[1])   # 从后往前删, 避免行号错位
    total = 0
    for t, a, b in ranges:
        n = b - a + 1
        total += n
        print("   %-32s 行 %d-%d (%d 行)" % (t, a + 1, b + 1, n))
    print("共删除 %d 个分支 / %d 行" % (len(ranges), total))

    if not apply:
        print("\n(演练模式, 未改动。加 --apply 实际执行)")
        return 0

    bk = os.path.join(os.path.dirname(HERE), "备份", "死代码清理-删除Core重复分支-写入前")
    os.makedirs(bk, exist_ok=True)
    shutil.copy2(os.path.join(vlib.SRC, TARGET), os.path.join(bk, TARGET))
    print("已备份 -> %s" % bk)

    out = list(ls)
    for t, a, b in ranges:
        for k in range(a, b + 1):
            out[k] = None
    out = [l for l in out if l is not None]
    text = "\n".join(out)
    if bom == "FFFE":
        data = text.encode("utf-16-le")
        data = b"\xff\xfe" + data
    elif bom == "EFBBBF":
        data = b"\xef\xbb\xbf" + text.encode("utf-8")
    else:
        data = text.encode("utf-8")
    if eol == "CRLF":
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    with open(os.path.join(vlib.SRC, TARGET), "wb") as f:
        f.write(data)
    print("已写入 %s (编码=%s eol=%s bom=%s)" % (TARGET, enc, eol, bom or "无"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
