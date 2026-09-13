# -*- coding: utf-8 -*-
"""把两处不生效的「缺参拒绝」守卫换成**字符串优先**判据。

背景(实测): `参数JSON.是否为空()==假 且 取对象("enable").取类型() != YYJSON值类型.未知`
这个 idiom **拦不住缺参** —— 作者原有的 browser_vip_enable_devtools_observer 实测同样失效,
导致缺省走 else 分支把 CDP 监管者关掉。

新判据原理: `yyjson取文本` 对「键缺失」与「JSON 布尔」**都**返回 "" ——
所以只有**显式字符串** "false"/"0"/"off" 才算关闭意图;
缺省(及布尔 false, 两者协议层无法区分)一律**拒绝并给出可行动提示** → 永不产生破坏性动作。
"""
import io
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

P = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src\MCP_Server_VIP.wsv"
lines = io.open(P, encoding="utf-8").read().split("\n")

OLD_RE = re.compile(r'^\s*// 显式分两步判空')
END_RE = re.compile(r'^\s*返回 \(MCP_响应构建\.命令失败 \(命令ID, "缺少必填参数 enable')

NEW_GUARD = """            // 修复(第十九轮): 原「取对象→取类型→判未知」idiom **实测拦不住缺参**
            // (作者原有的 browser_vip_enable_devtools_observer 同样失效), schema required 也不校验。
            // 新判据: yyjson取文本 对「键缺失」与「JSON布尔」都返回 "", 故只有**显式字符串**
            // "false"/"0"/"off" 才算关闭意图; 缺省(与布尔 false, 协议层无法区分)一律拒绝。
            // 失败方向安全: 任何歧义都不会执行破坏性动作。
            变量 开关文本 <类型 = 文本型>
            开关文本 = MCP命令服务器.yyjson取文本 (参数JSON, "enable")
            变量 开关布尔 <类型 = 逻辑型>
            开关布尔 = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")
            变量 目标状态 <类型 = 逻辑型>
            目标状态 = 开关布尔
            如果 (开关文本 == "false" || 开关文本 == "0" || 开关文本 == "off")
            {
                目标状态 = 假
            }
            否则 (开关文本 == "true" || 开关文本 == "1" || 开关文本 == "on")
            {
                目标状态 = 真
            }
            如果 (开关文本 == "" && 开关布尔 == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "必须显式指定 enable | 启用: enable:true 或 enable:\\"true\\" | 关闭: enable:\\"false\\" | ⚠ 关闭会使全部 CDP 类工具(debugger_*/cdp_*/reverse CDP类)失效且需重启进程才能恢复, 故不接受缺省; 说明: 布尔 false 与'缺省'在协议层无法区分, 关闭请用字符串 \\"false\\""))
            }"""

out, i, hits = [], 0, 0
while i < len(lines):
    if OLD_RE.match(lines[i]):
        # 找到该守卫块结束(返回缺参错误那行)
        j = i
        while j < len(lines) and not END_RE.match(lines[j]):
            j += 1
        if j < len(lines):
            end = j
            while end + 1 < len(lines) and lines[end + 1].strip() != "}":
                end += 1
            out.extend(NEW_GUARD.split("\n"))
            hits += 1
            i = end + 1
            continue
    out.append(lines[i])
    i += 1

# 把下游的 取逻辑 判定改为使用 目标状态 (两处)
txt = "\n".join(out)
n1 = txt.count('                    如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "enable"))')
txt = txt.replace('                    如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "enable"))',
                  '                    如果 (目标状态)')
n2 = txt.count('            enableObs = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")')
txt = txt.replace('            enableObs = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")',
                  '            enableObs = 目标状态')

io.open(P, "wb").write(txt.encode("utf-8"))
print("替换守卫块: %d 处" % hits)
print("下游判定改写: 内联 %d 处, enableObs %d 处" % (n1, n2))
