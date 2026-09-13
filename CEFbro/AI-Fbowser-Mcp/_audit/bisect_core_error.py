# -*- coding: utf-8 -*-
"""二分定位: 到底是"两个掩码助手"还是"分支改动"让 `类 MCP_核心分派` 构建失败。

做法: 把 Core 备份到 _audit(不在 src 里, 不会被编译), 然后**移除两个助手方法**,
跑一次语法检查看错误是否消失; 无论结果如何都恢复原文件。

已知现象: 编译器只在 MCP_Server.wsv 报 3 条 `没有找到"MCP_核心分派"` —— 即**这个类没构建出来**,
真因在 Core 里但没被直接报出来, 故必须二分。
"""
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

CORE = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
BAK = os.path.join(HERE, "_core_bisect.bak")
shutil.copy2(CORE, BAK)
print("已备份 Core 到 _audit/_core_bisect.bak")

COMPILER = r"E:\HSPC\bin\x64\voldev_awp.exe"
VSLN = "AI-Fbowser-Mcp.vsln"


def syntax_check(tag):
    p = subprocess.run([COMPILER, "@compile", VSLN, "/c"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    errs = [l.strip() for l in out.splitlines() if "错误:" in l]
    print("  [%s] 退出码=%s 错误行=%d" % (tag, p.returncode, len(errs)))
    for e in errs[:4]:
        print("      %s" % e[:150])
    return len(errs)


try:
    # 步骤 1: 移除两个助手方法, 保留分支改动
    s = io.open(CORE, encoding="utf-8").read()
    start = s.find("    方法 取清理对象掩码")
    end = s.find("    # === 分类分派: 核心操作")
    if start < 0 or end < 0 or end < start:
        print("!! 找不到助手方法的边界 -> 中止")
        sys.exit(2)
    removed = s[start:end]
    s2 = s[:start] + s[end:]
    io.open(CORE, "w", encoding="utf-8", newline="\n").write(s2)
    print("\n[步骤1] 已移除助手方法(共 %d 字符), 保留分支改动" % len(removed))
    n1 = syntax_check("无助手/有分支")

    # 步骤 2: 再把分支改动也还原成原来的一行调用
    s3 = io.open(CORE, encoding="utf-8").read()
    i = s3.find('否则 (方法名 == "browser_clear_cache_browser")')
    j = s3.find('否则 (方法名 == "browser_cache_dir")')
    if i < 0 or j < 0:
        print("!! 找不到分支边界 -> 中止")
        sys.exit(2)
    orig = ('        否则 (方法名 == "browser_clear_cache_browser")\n'
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
            '                返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步清理ID2, "浏览器缓存清理已提交, 通过mcp_result查询"))\n'
            '            }\n'
            '            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))\n'
            '        }\n')
    s4 = s3[:i] + orig + s3[j:]
    io.open(CORE, "w", encoding="utf-8", newline="\n").write(s4)
    print("\n[步骤2] 已把分支也还原为原实现(无助手/无分支改动)")
    n2 = syntax_check("全还原")

    print("\n结论: 无助手时错误 %d 条; 全还原时错误 %d 条" % (n1, n2))
    if n2 == 0 and n1 > 0:
        print("  => 真因在**分支改动**(与助手方法无关)")
    elif n1 == 0:
        print("  => 真因在**两个助手方法**")
    else:
        print("  => 两者都不是(或还有第三处改动); 需要继续查")
finally:
    shutil.copy2(BAK, CORE)
    print("\n已恢复 Core 原文件")
