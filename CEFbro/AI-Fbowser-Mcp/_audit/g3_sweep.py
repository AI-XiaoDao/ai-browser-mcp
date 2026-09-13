# -*- coding: utf-8 -*-
"""g3_sweep.py — 全量幽灵扫描 + 复用路径实现状态核查 (基于冻结快照, 只读)"""
import json, os, re

ROOT = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
SNAP = os.path.join(ROOT, "_audit", "_ghost_snapshot")
OUT = os.path.join(ROOT, "_audit")

import importlib.util
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
spec = importlib.util.spec_from_file_location("g2", os.path.join(OUT, "g2_ghost_audit.py"))
g2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g2)

# 复用路径候选 (工具名)
REUSE = [
    "browser_fingerprint", "browser_fingerprint_ua", "browser_vip_fingerprint_font",
    "browser_vip_fingerprint_canvas_font", "browser_vip_fingerprint_webgl",
    "browser_vip_fingerprint_languages",
    "browser_get_all_cookies", "browser_reverse_cookie_sources", "browser_get_cookies",
    "browser_vip_mouse_press", "browser_vip_mouse_release", "browser_vip_mouse_click",
    "browser_vip_key_type", "browser_vip_key_input", "browser_mouse_click", "browser_key_event",
    "browser_kernel_reverse_trace", "browser_kernel_reverse_probe",
    "browser_reverse_precise_coverage", "browser_reverse_profile",
    "browser_reverse_skip_pauses", "browser_reverse_blackbox", "browser_reverse_bypass_csp",
    "browser_reverse_async_stack", "browser_reverse_cache_disable",
    "browser_reverse_heap", "browser_reverse_runtime", "browser_reverse_cdp_hook",
    "browser_reverse_instrument", "browser_reverse_setup", "browser_reverse_extract",
    "browser_antidetect_presets", "browser_reverse_detect_obfuscator",
    "browser_permission_spoof", "browser_canvas_noise", "browser_retry",
    "browser_reverse_hook", "browser_reverse_search", "browser_reverse_dom_breakpoint",
    "browser_reverse_network_intercept", "browser_reverse_websocket",
    "browser_reverse_patch", "browser_reverse_evaluate_silent", "browser_reverse_compile_script",
    "browser_network_export", "browser_reverse_add_binding", "browser_reverse_listeners",
    "browser_reverse_dom_resolve",
]
# 特殊自带处理 (不经7个分派器, 由 JSON-RPC 层直接处理)
SPECIAL = {"mcp_status", "mcp_help", "mcp_result", "mcp_hello", "notifications_initialized"}


def main():
    tool_names, dict_names = g2.build_registry()
    disp = g2.dispatcher_bodies()
    branches = {}
    for dname, info in disp.items():
        if info is None:
            branches[dname] = []
            continue
        dfn, d, end, lines, text = info
        branches[dname] = g2.branches_of(text, d, end, lines)

    def hits_for(name):
        # 入口规范化: browser. → browser_ (执行浏览器命令 L10314)
        if name.startswith("browser."):
            name = "browser_" + name[len("browser."):]
        # 短名: 取短名映射 会补 browser_ 前缀后再分派
        elif not name.startswith("browser_") and name not in SPECIAL:
            name = "browser_" + name
        base = name[len("browser_"):] if name.startswith("browser_") else name
        out = []
        for dname, brs in branches.items():
            for (ln, kind, val, code) in brs:
                if val == name or val == base:
                    out.append({"d": dname, "line": ln, "kind": kind, "value": val, "code": code})
                elif kind == "前缀(是否以)" and val and name.startswith(val):
                    out.append({"d": dname, "line": ln, "kind": "前缀路由" + val, "value": val, "code": code})
        return out

    # --- 全量扫描 ---
    ghost_dict = []   # 在命令注册表但无任何分派分支
    ghost_tool = []   # 在 tools/list 但无任何分派分支
    for n in sorted(dict_names):
        if n in SPECIAL:
            continue
        if not hits_for(n):
            ghost_dict.append(n)
    for n in sorted(tool_names):
        if n in SPECIAL:
            continue
        if not hits_for(n):
            ghost_tool.append(n)

    L = []
    L.append("# 全量幽灵扫描 (快照 %s)" % SNAP)
    L.append("")
    L.append("## tools/list 已登记(301) 但分派链无分支  => 工具在列表里可见却不可用 (严重)")
    for n in ghost_tool:
        A = tool_names[n][0]
        B = dict_names.get(n, [])
        L.append("  %-42s tools/list %s:%d(%s) | 命令注册表: %s"
                 % (n, A["file"], A["line"], A.get("owner"),
                    ("%s:%d" % (B[0]["file"], B[0]["line"])) if B else "无"))
    L.append("  小计 = %d" % len(ghost_tool))
    L.append("")
    L.append("## 仅命令注册表有(camel/短名/遗留) 且分派链无分支 => 死注册项")
    for n in ghost_dict:
        if n in tool_names:
            continue
        B = dict_names[n][0]
        L.append("  %-42s 命令注册表 %s:%d %s" % (n, B["file"], B["line"], B["how"]))
    L.append("")
    L.append("## 复用路径候选实现状态")
    for n in REUSE:
        h = hits_for(n)
        L.append("  %-40s tools/list=%-3s 分派分支=%s"
                 % (n, "Y" if n in tool_names else "N",
                    ("; ".join("%s L%d %s" % (x["d"], x["line"], x["value"]) for x in h) if h else "无")))
    txt = "\n".join(L)
    open(os.path.join(OUT, "g3_sweep.txt"), "w", encoding="utf-8").write(txt)
    json.dump({"ghost_tool": ghost_tool, "ghost_dict_only": [n for n in ghost_dict if n not in tool_names]},
              open(os.path.join(OUT, "g3_sweep.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ghost_tool =", len(ghost_tool), " ghost_dict_only =", len([n for n in ghost_dict if n not in tool_names]))


if __name__ == "__main__":
    main()
