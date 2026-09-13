# -*- coding: utf-8 -*-
"""能力覆盖审计: 找出 FBrowser 类库中「有公开方法、但本项目源码从未调用」的浏览器能力。

权威来源: 技能书 资料/类库/FBrowser浏览器/{FBroLib,FBroVip,FBroDataType}.wsv
判据: 类库公开方法名在项目 src/*.wsv 中**作为调用出现 0 次** -> 该能力未被 MCP 暴露。
排除项: 事件覆盖(虚拟方法)、类_初始化/类_清理、后缀文本/属性包装、纯取值器噪音另行归类。

注: 只做局部解析, 不整读 287KB 类库文件。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SKILLDIR = (r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming"
            r"\资料\类库\FBrowser浏览器")
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

MSTART = re.compile(r'方法\s+([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*<([^>]*)>')
CLS = re.compile(r'^\s*类\s+(\S+)')

TARGET = {
    "类_FBrowser_浏览器": "浏览器控制",
    "类_FBrowserVIP_控制器": "VIP控制器",
    "类_FBrowser_请求环境": "请求环境",
    "类_FBrowser_框架": "框架",
    "类_FBrowser_V8环境": "V8环境",
    "类_FBrowser_DOM节点": "DOM节点",
    "类_FBrowser_字典值": "字典值",
    "类_FBrowser_命令行": "命令行",
}

SKIP = re.compile(r'^(类_初始化|类_清理|_?销毁|后缀文本)')


def lib_methods():
    out = {}
    for fn in ("FBroLib.wsv", "FBroVip.wsv", "FBroDataType.wsv"):
        path = os.path.join(SKILLDIR, fn)
        if not os.path.exists(path):
            continue
        cur = None
        for i, l in enumerate(io.open(path, encoding="utf-8", errors="replace").read().split("\n")):
            m = CLS.match(l)
            if m:
                cur = m.group(1)
                continue
            m2 = MSTART.search(l)
            if m2 and cur in TARGET:
                name, attrs = m2.group(1), m2.group(2)
                if "虚拟方法" in attrs:           # 事件覆盖, 不属于"能力"
                    continue
                if SKIP.match(name):
                    continue
                if "@嵌入式方法" in attrs or "输入" in attrs:
                    continue
                # 只收公开方法
                if "公开" not in attrs and "静态" not in attrs:
                    continue
                if name not in out:
                    is_static = "静态" in attrs
                    out[name] = (cur, fn, i + 1, is_static)
    return out


lib = lib_methods()
print("类库公开方法(目标类): %d 个" % len(lib))

# 项目全文
proj_text = ""
for f in sorted(os.listdir(SRC)):
    if f.endswith(".wsv") and ".~vbak" not in f:
        proj_text += io.open(os.path.join(SRC, f), encoding="utf-8").read() + "\n"
print("项目源码总长: %d 字符" % len(proj_text))

uncalled = []
for name, (cls, fn, ln, is_static) in sorted(lib.items()):
    # 作为调用: 名字后跟 '(' (允许 MCP命令服务器. 之类前缀)
    if re.search(re.escape(name) + r'\s*\(', proj_text):
        continue
    uncalled.append((name, cls, fn, ln, is_static))

print()
print("=" * 100)
print("类库有公开方法、项目从未调用: %d 个" % len(uncalled))
print("=" * 100)
by_cls = {}
for r in uncalled:
    by_cls.setdefault(r[1], []).append(r)
for cls in sorted(by_cls, key=lambda c: -len(by_cls[c])):
    rows = by_cls[cls]
    print()
    print("── %s  (%d 个) ──" % (cls, len(rows)))
    for name, _c, fn, ln, st in rows:
        print("   %-44s %s%s:%d" % (name, "静态 " if st else "", fn, ln))
