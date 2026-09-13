# -*- coding: utf-8 -*-
"""二分第二步: 保留两个助手方法, 只把**分支**还原成原来的一行调用, 看是否能通过。

上一步已知: 无助手 + 有分支 => 失败; 全还原 => 通过。
本步: 有助手 + 无分支改动 =>
  · 通过 => 助手本身没问题, 真因在分支体里(下一步在分支体内部二分);
  · 失败 => 助手本身有问题(单行if已改多行, 那就另有原因)。
无论结果都恢复原文件。
"""
import io
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

CORE = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
BAK = os.path.join(HERE, "_core_step2.bak")
shutil.copy2(CORE, BAK)
COMPILER = r"E:\HSPC\bin\x64\voldev_awp.exe"
VSLN = "AI-Fbowser-Mcp.vsln"

ORIG = ('        否则 (方法名 == "browser_clear_cache_browser")\n'
        '        {\n'
        '            变量 browser <类型 = 类_FBrowser_浏览器>\n'
        '            browser = MCP命令服务器.取主浏览器 ()\n'
        '            如果 (browser.是否为空 () == 假)\n'
        '            {\n'
        '                变量 异步清理ID2 <类型 = 文本型>\n'
        '                异步清理ID2 = MCP命令服务器.生成异步任务ID ()\n'
        '                变量 清理回调 <类型 = 类_FBrowser_事件智能指针>\n'
        '                清理回调.创建 (类_MCP_清理缓存回调)\n'
        '                清理回调.取执行类 (类_MCP_清理缓存回调).任务ID = 异步清理ID2\n'
        '                browser.清理缓存 (, , , 清理回调)\n'
        '                返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步清理ID2, "浏览器清理已提交"))\n'
        '            }\n'
        '            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))\n'
        '        }\n')

try:
    s = io.open(CORE, encoding="utf-8").read()
    i = s.find('        否则 (方法名 == "browser_clear_cache_browser")')
    j = s.find('        否则 (方法名 == "browser_cache_dir")')
    if i < 0 or j < 0:
        print("!! 找不到分支边界 -> 中止"); sys.exit(2)
    s2 = s[:i] + ORIG + s[j:]
    io.open(CORE, "w", encoding="utf-8", newline="\n").write(s2)
    print("[步骤] 已保留助手、只还原分支")
    p = subprocess.run([COMPILER, "@compile", VSLN, "/c"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    errs = [l.strip() for l in out.splitlines() if "错误:" in l]
    print("  退出码=%s 错误行=%d" % (p.returncode, len(errs)))
    for e in errs[:3]:
        print("      %s" % e[:150])
    print("\n结论: %s" % ("助手本身没问题 => 真因在**分支体**里"
                          if len(errs) == 0 else
                          "助手本身就有问题 => 需查助手"))
finally:
    shutil.copy2(BAK, CORE)
    print("已恢复 Core 原文件")
