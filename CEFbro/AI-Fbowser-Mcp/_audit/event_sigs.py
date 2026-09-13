# -*- coding: utf-8 -*-
"""抽取目标事件的完整声明(方法行 + 参数行 + 注释), 供编写可覆盖方法时照抄签名。
输出到 _event_sigs.txt, 避免整读 143KB 类库文件。"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SKILL = (r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming"
         r"\资料\类库\FBrowser浏览器\FBroEventControl.wsv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_event_sigs.txt")

CLASSES = {"类_FBrowser_应用事件": "APP", "类_FBrowser_浏览器事件": "BROWSER"}
EVENT_OK = re.compile(r'方法\s+([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*<公开(.*?)>')

# 本项目已覆盖的 (由 event_gap.py 得出, 这里再次计算以保证一致)
PROJ = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"
covered = set()
for f in os.listdir(PROJ):
    if not f.endswith(".wsv") or ".~vbak" in f:
        continue
    for l in io.open(os.path.join(PROJ, f), encoding="utf-8").read().split("\n"):
        m = EVENT_OK.search(l)
        if m and "虚拟方法 = 可覆盖" in m.group(2):
            covered.add(m.group(1))

lines = io.open(SKILL, encoding="utf-8", errors="replace").read().split("\n")
cur = None
blocks = {"APP": [], "BROWSER": []}
i = 0
while i < len(lines):
    l = lines[i]
    m = re.match(r'\s*类\s+(\S+)', l)
    if m:
        cur = CLASSES.get(m.group(1))
        i += 1
        continue
    m2 = EVENT_OK.search(l)
    if cur and m2 and "虚拟方法 = 可覆盖" in m2.group(2):
        name = m2.group(1)
        if name not in ("类_初始化", "类_清理"):
            # 收集方法行 + 紧随的 参数 行(到 '{' 或下一个 方法 为止)
            blk = [l.rstrip()]
            j = i + 1
            while j < len(lines) and j < i + 20:
                s = lines[j]
                st = s.strip()
                if st.startswith("参数") or st.startswith("返回值注释"):
                    blk.append(s.rstrip())
                    j += 1
                    continue
                if st.startswith("注释") or st.startswith("<"):
                    blk.append(s.rstrip())
                    j += 1
                    continue
                break
            if name not in covered:
                blocks[cur].append((name, i + 1, blk))
    i += 1

buf = []
for k, label in (("APP", "类_FBrowser_应用事件"), ("BROWSER", "类_FBrowser_浏览器事件")):
    buf.append("=" * 100)
    buf.append("%s  缺 %d 个事件" % (label, len(blocks[k])))
    buf.append("=" * 100)
    for name, ln, blk in blocks[k]:
        buf.append("")
        buf.append("---- %s   (类库 L%d) ----" % (name, ln))
        for b in blk:
            buf.append(b)

io.open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("已写出 %s" % OUT)
print("  APP 缺 %d, BROWSER 缺 %d" % (len(blocks["APP"]), len(blocks["BROWSER"])))
print("  项目已覆盖 %d 个事件" % len(covered))
