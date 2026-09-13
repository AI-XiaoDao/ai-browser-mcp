# -*- coding: utf-8 -*-
"""C1 — 用真实编译产物做终局验证

验证项:
  1. 虚拟覆盖方法是否仍用原始拼音符号名 (覆盖链路完整)
  2. @强制输出 是否把"按需编译"漏掉的方法补上 (方法数对比旧快照)
  3. 输出名冲突/缺失
"""
import os, re, io, json, collections, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NEW = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\_int\AI-Fbowser-Mcp\debug\x64\project"
OLD = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\generated-cpp\release-x64"

print("=" * 100)
print("C1 真实编译产物终局验证")
print("=" * 100)

def methods(path):
    d = io.open(path, encoding="utf-8", errors="replace").read()
    return re.findall(r"\b(rg_[A-Za-z0-9_]+|MCP[A-Za-z0-9_]+|[A-Z][A-Za-z0-9_]*)\s*\(", d)

print()
print("--- 1. 虚拟覆盖方法是否保留原始符号名 ---")
p = os.path.join(NEW, "vcls_MCPBrowserEvent.h")
d = io.open(p, encoding="utf-8", errors="replace").read()
virt = re.findall(r"virtual\s+\S+\s+(rg_[A-Za-z0-9_]+)\s*\(", d)
print("   类 MCPBrowserEvent : virtual 方法 %d 个" % len(virt))
print("   前 6 个:", virt[:6])
pinyin_ok = all(v.startswith("rg_LiuLanQi_") or v.startswith("rg_") for v in virt)
print("   是否全部保留原始 rg_ 符号名:", "是 ✓" if pinyin_ok else "否 !!")
# 与基类对比
base = os.path.join(NEW, "vcls_rg_class_FBrowser_llqshj.h")
bd = io.open(base, encoding="utf-8", errors="replace").read()
bvirt = set(re.findall(r"virtual\s+\S+\s+(rg_[A-Za-z0-9_]+)\s*\(", bd))
overlap = [v for v in virt if v in bvirt]
print("   与基类 rg_class_FBrowser_llqshj 同名(即成功覆盖)的: %d / %d" % (len(overlap), len(virt)))

print()
print("--- 2. @强制输出 效果: 方法数对比 ---")
pairs = [
    ("vcls_MCPCommandServer.h", "vcls_rg_MCPMingLingFuWuQi.h", "MCP命令服务器"),
    ("vcls_MCPKernelDispatch.h", "vcls_rg_MCP_NeiHeFenPa.h", "MCP_内核分派"),
    ("vcls_MCPCoreDispatch.h", "vcls_rg_MCP_HeXinFenPa.h", "MCP_核心分派"),
    ("vcls_MCPWorkflowDispatch.h", "vcls_rg_MCP_BianPaiFenPa.h", "MCP_编排分派"),
    ("vcls_MCPResponseBuilder.h", "vcls_rg_MCP_XiangYingGouJian.h", "MCP_响应构建"),
]
print("   %-26s %8s %8s %8s" % ("类", "旧快照", "新编译", "增量"))
print("   " + "-" * 58)
for nf, of, cn in pairs:
    np_, op_ = os.path.join(NEW, nf), os.path.join(OLD, of)
    nm = len(re.findall(r"CALLBACK\s+\w+\s*\(", io.open(np_, encoding="utf-8", errors="replace").read())) if os.path.exists(np_) else -1
    om = len(re.findall(r"CALLBACK\s+\w+\s*\(", io.open(op_, encoding="utf-8", errors="replace").read())) if os.path.exists(op_) else -1
    print("   %-26s %8d %8d %8s" % (cn, om, nm, ("+%d" % (nm - om)) if om >= 0 and nm >= 0 else "-"))

print()
print("--- 3. 输出名是否全部为英文 (无残留拼音) ---")
bad = []
for f in os.listdir(NEW):
    if not (f.startswith("vcls_MCP") and f.endswith(".h")):
        continue
    d = io.open(os.path.join(NEW, f), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"(?:static\s+|virtual\s+)?[\w:<>&\s\*]+\s+(?:CALLBACK\s+)?(\w+)\s*\(", d):
        name = m.group(1)
        if name in ("DECLARE_EMPTY_VOL_CLASS", "inline_"):
            continue
        if re.match(r"^rg_", name):
            bad.append((f, name))
print("   残留 rg_ 前缀的方法名: %d 条" % len(bad))
for b in bad[:12]:
    print("      %s : %s" % b)

print()
print("--- 4. 英文类头文件清单 (共 %d 个) ---" %
      len([f for f in os.listdir(NEW) if f.startswith("vcls_MCP") and f.endswith(".h")]))
en = sorted(f for f in os.listdir(NEW) if f.startswith("vcls_MCP") and f.endswith(".h"))
for i in range(0, len(en), 3):
    print("   " + "".join("%-42s" % x for x in en[i:i + 3]))
