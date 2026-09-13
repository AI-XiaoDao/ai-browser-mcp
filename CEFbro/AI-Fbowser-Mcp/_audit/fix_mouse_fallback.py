# -*- coding: utf-8 -*-
"""把鼠标三件套的"CDP 派发失败 → 静默回退内核注入"改为: 如实报错, 不再静默走会毁掉会话的路径。

背景(实测因果链): 内核级鼠标注入会让 CDP 通道在**整个会话内**永久失效(需重启进程), 此后每个
CDP 优先工具都白等超时(连 browser_status 都挂)。原实现里 CDP 派发失败会**静默落到**内核注入分支,
于是一次点击失败就连累整场会话 —— 这正是用户说的"连续调用失败、反复换方法"。

定位方式与空白无关: 按锚点子串找行 → 找其后第 2 个 `}` (即内层 if 与外层 if 的闭合) → 在其后插入。
插入行缩进取自同处 `如果 (MCP命令服务器.CDP派发鼠标事件` 行的缩进。

用法: py -3 fix_mouse_fallback.py [--apply]
"""
import io
import os
import shutil
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
T = "MCP_Server_Core.wsv"

ANCHORS = [
    u') 按钮:" + cdp按钮名 + " | 经 CDP 派发',                       # browser_mouse_click
    u'"鼠标移动到 (" + 到文本 (x) + "," + 到文本 (y) + ") | 经 CDP',      # browser_mouse_move
    u'delta:" + 到文本 (deltaX) + "," + 到文本 (deltaY) + " | 经 CDP 派发',  # browser_mouse_wheel
]
MSG = (u"CDP 派发鼠标事件失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级鼠标注入 "
       u"kernel:true; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe) | 可用替代: "
       u"browser_element_action 点击元素 / browser_execute_js 派发事件 | "
       u"如仍要内核注入请显式传 kernel:true(会确认 CDP 已失效)")


def main():
    apply = "--apply" in sys.argv
    p = os.path.join(SRC, T)
    raw = open(p, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig" if bom else "utf-8")
    crlf = text.count("\r\n") > 0 and text.count("\r\n") == text.count("\n")
    lines = text.split("\n")

    hits = []
    for a in ANCHORS:
        idx = [i for i, l in enumerate(lines) if a in l]
        if len(idx) != 1:
            print("!! 锚点命中 %d 次(应为1): %s" % (len(idx), a[:40]))
            return 2
        i = idx[0]
        # 同行以内层的 CDP 派发 if 为准取缩进
        ind = None
        for j in range(i, max(0, i - 12), -1):
            if "CDP派发鼠标事件" in lines[j] and "如果" in lines[j]:
                ind = len(lines[j]) - len(lines[j].lstrip())
                break
        if ind is None:
            print("!! 未找到内层 if 缩进, 锚点: %s" % a[:40])
            return 2
        # 其后第 2 个纯 '}' 行 = 内层 if 与外层 if 的闭合
        cnt, k = 0, None
        for j in range(i + 1, min(len(lines), i + 30)):
            if lines[j].strip() == "}":
                cnt += 1
                if cnt == 2:
                    k = j
                    break
        if k is None:
            print("!! 未找到第 2 个闭合括号, 锚点: %s" % a[:40])
            return 2
        hits.append((i, k, ind))

    print("命中 %d 处, 每处插入 3 行:" % len(hits))
    for i, k, ind in hits:
        print("   锚点行 %d -> 插入于第 %d 行之后 (缩进 %d)" % (i + 1, k + 1, ind))

    if not apply:
        print("\n(演练模式, 未改动。加 --apply 实际执行)")
        return 0

    bk = os.path.join(os.path.dirname(HERE), "备份", "鼠标回退改诚实报错-写入前")
    os.makedirs(bk, exist_ok=True)
    shutil.copy2(p, os.path.join(bk, T))
    print("已备份 -> %s" % bk)

    sp = " " * ind
    block = [
        sp + u"// CDP 派发失败时不再静默回退内核注入: 内核注入会让 CDP 通道在本会话内永久失效",
        sp + u"// (此后每个 CDP 优先工具都白等超时, 连 browser_status 都会挂, 只能重启进程恢复);",
        sp + u"// 一次鼠标操作失败不该连累整场会话, 故如实报错并给出可用替代。",
        sp + u'返回 (MCP_响应构建.命令失败 (命令ID, "' + MSG + u'"))',
    ]
    for i, k, ind in sorted(hits, key=lambda x: -x[1]):   # 从后往前插入, 避免下标错位
        lines[k + 1:k + 1] = block

    out = "\n".join(lines)
    data = out.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    if crlf:
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    with open(p, "wb") as f:
        f.write(data)
    print("已写入 %s (BOM=%s CRLF=%s)" % (T, bom, crlf))
    return 0


if __name__ == "__main__":
    sys.exit(main())
