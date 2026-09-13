# -*- coding: utf-8 -*-
"""校验: 项目内新覆盖事件的**参数签名**与类库权威定义逐项一致。
不一致 = 编译错误或虚函数未正确绑定, 必须为零。
比对项: 方法名 / 返回类型(是否逻辑型) / 参数个数 / 每个参数的类型。
"""
import io
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SKILL = (r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming"
         r"\资料\类库\FBrowser浏览器\FBroEventControl.wsv")
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

CLASSES = {"类_FBrowser_应用事件": "APP", "类_FBrowser_浏览器事件": "BROWSER"}
EV = re.compile(r'方法\s+([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*<公开(.*?)>')
PARAM = re.compile(r'(?:参数|局部变量)\s+([\u4e00-\u9fffA-Za-z_][\u4e00-\u9fffA-Za-z0-9_]*)\s*<类型\s*=\s*([^ >]+)')


def parse(path, want_classes=None):
    """返回 {方法名: (是否逻辑型, [参数类型...])} — 取首次出现。"""
    out = {}
    cur = None
    lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r'\s*类\s+(\S+)', lines[i])
        if m:
            cur = m.group(1) if want_classes is None else CLASSES.get(m.group(1))
            i += 1
            continue
        m2 = EV.search(lines[i])
        if m2 and (want_classes is None or cur):
            name, attrs = m2.group(1), m2.group(2)
            if name in ("类_初始化", "类_清理"):
                i += 1
                continue
            is_bool = "类型 = 逻辑型" in ("类型" + attrs if "类型" in attrs else attrs)
            # 更稳妥: 直接从属性串判断
            is_bool = bool(re.search(r'类型\s*=\s*逻辑型', attrs))
            types = []
            j = i + 1
            while j < len(lines) and j < i + 25:
                s = lines[j].strip()
                if s.startswith("参数"):
                    pm = PARAM.search(lines[j])
                    if pm:
                        types.append(pm.group(2))
                    j += 1
                    continue
                break
            if name not in out:
                out[name] = (is_bool, types)
        i += 1
    return out


lib = parse(SKILL)
print("类库事件解析: %d 个" % len(lib))

proj = {}
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".wsv") or ".~vbak" in f:
        continue
    proj.update(parse(os.path.join(SRC, f), want_classes=None))

print("项目已覆盖: %d 个" % len(proj))

# 只比对项目里覆盖的、且类库也存在的事件
common = sorted(set(proj) & set(lib))
print("可比对: %d 个" % len(common))
print()
print("=" * 100)
print("签名一致性")
print("=" * 100)

bad_n, bad_ret, bad_cnt, bad_type = [], [], [], []
for name in common:
    lb, lt = lib[name]
    pb, pt = proj[name]
    ok = True
    if lb != pb:
        bad_ret.append((name, lb, pb))
        ok = False
    if len(lt) != len(pt):
        bad_cnt.append((name, lt, pt))
        ok = False
    else:
        for k, (a, b) in enumerate(zip(lt, pt)):
            if a != b:
                bad_type.append((name, k, a, b))
                ok = False
    if not ok:
        pass

print("  返回类型不符: %d" % len(bad_ret))
for n, a, b in bad_ret:
    print("      %-34s 类库逻辑型=%s 项目=%s" % (n, a, b))
print("  参数个数不符: %d" % len(bad_cnt))
for n, a, b in bad_cnt:
    print("      %-34s 类库 %d 个 %s" % (n, len(a), a))
    print("      %-34s 项目 %d 个 %s" % ("", len(b), b))
print("  参数类型不符: %d" % len(bad_type))
for n, k, a, b in bad_type:
    print("      %-34s 第%d个: 类库=%s 项目=%s" % (n, k + 1, a, b))

total_bad = len(bad_ret) + len(bad_cnt) + len(bad_type)
print()
print("  ★ 合计不一致: %d" % total_bad)
if total_bad == 0:
    print("  ✅ 全部 %d 个事件的签名与类库权威定义完全一致" % len(common))
