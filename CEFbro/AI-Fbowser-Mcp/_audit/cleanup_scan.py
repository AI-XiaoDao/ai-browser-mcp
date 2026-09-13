# -*- coding: utf-8 -*-
"""代码卫生扫描: 操作备注 / 死代码备注 / 死代码 / 幽灵注册 / 重复分支。

对应用户目标三。**只读不写**, 产出报表供人工/后续脚本清理。
纯静态分析(不调 MCP), 可与真机测试并行跑而不互相污染。

用法: py -3 cleanup_scan.py
输出: _cleanup_report.md (明细) + 控制台摘要
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vlib
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

# ── 操作备注(开发过程叙述)特征 ──
# 口径修正(见 报告 §136 与 _audit/_notes_cleanup_plan_r117.md §六):
#   · 移出 `静默|之前|本次|回退` —— 实测它们在代码里多为**运行期语义**
#     (`回退`=运行期回退分支, `静默`=描述内核/被调用方行为, `之前`=时序先后, `本次`=运行期序数),
#     旧口径把 95/247 条契约注释误判成"操作备注"。
#   · 补 `第\d+轮|上一版`(实测漏报真实叙述)。
# 口径(第117/118轮定稿): **只把"开发过程叙述"算作操作备注**。
#   · 移出 `实测|原实现|原返回|原来|先前` —— 它们是"为什么存在这条约束"的**依据**, 且项目里
#     这些注释常常是唯一记录实测结论的地方(清掉=把踩过的坑重新埋回去)。
#   · 移出 `静默|之前|本次|回退` —— 多为运行期语义(见 §136)。
#   · 保留真正带过程口吻的词。
NOTE_STRONG = re.compile(
    r"修复[:：(]|已修|曾因|曾经|踩坑|踩过|教训|本轮|上一轮|上一版|第\d+轮|"
    r"现改为|改回|纠正|笔误|漏了")
# 说明: `误判`/`假成功` 曾列在 STRONG, 但实测它们在本项目里是**领域术语** ——
#   · `不静默假成功` 是项目自己的横切不变量名;
#   · `误判` 用于描述运行期判据(如"会被误判为已加载完成"), 属约束而非过程叙述。
# 故移出; 若将来出现"我误判过…"这类过程句, 由人工复核处理。
# 收紧(第118轮): 只认**版本/批次标签**; `新增|增强|补齐|补上|补充|优化|重构` 在本项目里
# 多用于描述能力与行为(段标题/理由句), 实测 7/7 残留全是这类, 故移出。
NOTE_MEDIUM = re.compile(r"v\d+\.\d|R\d+[:：]")
# 行为契约类(应保留): 参数语义/边界/默认值/返回值/单位
NOTE_KEEP = re.compile(r"默认|上限|下限|范围|单位|毫秒|字符|越界|为空则|缺省|可选|必填|返回|禁止|不得|防|避免|兼容")

# ── 死代码备注: 被注释掉的可执行语句 ──
# 注意: `否则` 必须后接 ( 或 { 才算"被注释掉的语句"; 单纯的"否则…"是说明性散文,
# 早期写成裸 `否则` 导致 7/7 全是误报(见 报告 §132)。
DEAD_COMMENT = re.compile(
    r"^\s*//\s*(变量\s|常量\s|如果\s*\(|否则\s*[({]|判断循环|计次循环|循环\s*\(|返回\s*\(|"
    r"调用\s|执行\s|加入成员|\.加入|\.删除|\.创建|方法\s|参数\s|类\s|@)")

# ── "已移除/已禁用"残注释 ──
RESIDUAL = re.compile(r"已移除|已删除|已废弃|已禁用|不再使用|废弃|unused|deprecated|注释掉")

# ── 刻意的守卫分支(可路由 + 有分支 + 故意不实现 + 给了原因与替代方案) ──
# 判定依据: 真机回包原文, 见 _audit/probe_ghost_names.py 实测输出。新增项必须先实测再登记。
DUPLICATE_OK = {'ping': '协议层 ping 与工具层 ping 两条真实入口'}

DELIBERATE_GATES = {
    "browser_create_tab":
        "刻意不实现: 项目未开放远程建标签页; 回包给替代方案(browser_navigate / browser_create)",
    "browser_task_runner_post":
        "刻意不实现: 项目未开放远程 task_runner 建浏览器; 回包给替代方案(browser_id / browser_create)",
    "browser_debugger_pause":
        "刻意禁用: 会冻结无JS执行页面并堵塞CDP队列; 回包给替代方案(debugger_flow / set_breakpoint+wait_paused)",
}


def scan():
    files = {f: vlib.lines_of(f)[0] for f in vlib.FILES if os.path.exists(os.path.join(vlib.SRC, f))}
    all_text = "\n".join("\n".join(v) for v in files.values())

    notes, deadc, resid = [], [], []
    for f, ls in files.items():
        for i, ln in enumerate(ls, 1):
            s = ln.strip()
            if s.startswith("//"):
                if DEAD_COMMENT.match(ln):
                    deadc.append((f, i, s[:120]))
                if RESIDUAL.search(s):
                    resid.append((f, i, s[:120]))
                # `=== … ===` 是段标题, 不是备注(旧口径被 MEDIUM 的"新增/补充"等词误判)
                是段标题 = bool(re.match(r"//\s*[=＝\-—_]{2,}", s)) or ("===" in s and s.count("=") >= 6)
                if 是段标题:
                    pass
                elif NOTE_STRONG.search(s):
                    # STRONG 一律报: 旧口径"KEEP 整行排除"会反向漏报
                    # (实测漏掉 `已修复` 因含"返回"、`原实现靠…回落到默认值` 因含"默认")
                    notes.append((f, i, "STRONG", s[:150]))
                elif NOTE_MEDIUM.search(s) and not NOTE_KEEP.search(s):
                    notes.append((f, i, "MEDIUM", s[:150]))

    # ── 方法引用计数 ──
    # 重要: 必须排除"由框架按符号调用"的方法, 否则会误删:
    #   · `@虚拟方法 = 可覆盖` = 覆盖 C++ 基类虚函数(事件/回调), 源码里不出现方法名
    #   · 分派器入口由路由以字符串形式调用
    # 注意不能拿 `@输出名` 当依据 —— 本项目所有方法都带英文输出名, 那样会把全部方法都排除掉。
    zero_ref, virt_m, sym_m = [], 0, 0
    for f in files:
        for (i0, mname, sig, b0, b1) in vlib.find_methods(f):
            if mname in ("分类分派_核心操作", "分类分派_逆向操作", "分类分派_VIP操作",
                         "分类分派_填表操作", "分类分派_系统操作", "分类分派_编排操作"):
                continue
            # 框架按符号绑定、源码必然零引用的两类, 不能当死代码:
            #   · `@虚拟方法 = 可覆盖` 覆盖 C++ 基类虚函数
            #   · `<接收事件>` 事件接收方法(属性块常跨行, 必须连签名区一起看)
            #   · 应用入口 `启动方法`(由框架调用)
            head = "\n".join(files[f][i0:b0]) if b0 else sig
            if ("@虚拟方法" in head) or ("<接收事件" in head) or (mname == "启动方法"):
                virt_m += 1
                continue
            if "@输出名" in sig:
                sym_m += 1
            n = all_text.count(mname)
            if n <= 1:
                zero_ref.append((f, i0 + 1, mname, sig.strip()[:70]))

    # ── 成员(变量)引用计数 ──
    zero_member = []
    for f in files:
        for (i, l) in vlib.member_lines(f):
            m = re.match(r"\s*变量\s+(\S+)", l)
            if not m:
                continue
            nm = m.group(1)
            if all_text.count(nm) <= 1:
                zero_member.append((f, i + 1, nm))

    # ── 重复分支(同名工具在两个分派器各一份) ──
    branch_re = re.compile(r'否则 \(方法名 == "([a-z0-9_]+)"\)')
    per_tool = {}
    for f, ls in files.items():
        for i, ln in enumerate(ls, 1):
            m = branch_re.search(ln)
            if m:
                per_tool.setdefault(m.group(1), []).append((f, i))
    dup = {k: v for k, v in per_tool.items() if len(v) > 1}
    # 跨层同名分支不是死代码: 协议层(处理MCP请求_内部 里的 ping 回应 JSON-RPC ping)
    # 与 工具层(分类分派_系统操作 里的 ping)是两条真实入口, 各自可达。
    # 依据: _audit/diag_ping_dup.py 实测(执行浏览器命令 → MCP_系统分派.分类分派_系统操作)。
    dup = {k: v for k, v in dup.items() if k not in DUPLICATE_OK}

    # ── 幽灵注册(注册表有 / 无工具定义) ──
    # 注意: 本项目的 `注册命令双变体 ("xxx")` 让 `xxx` 与 `browser_xxx` **都能路由**,
    # 但只把其中一个放进 MCP 工具清单 —— 所以"注册表里有、清单里没有"**不等于**没有实现。
    # 实测(2026年, _audit/probe_ghost_names.py): 名字形如 browser_<已广告名> 的, 全部都能正常回包;
    # 其余几个是**刻意不实现**的守卫分支(有明确原因与替代方案), 也不是缺口。
    # 因此这里把两者分开: alias=路由别名(非缺口) / ghost=需人工核实的名字。
    reg = set()
    for m in re.finditer(r'注册命令双变体 \("([a-z0-9_]+)"', all_text):
        reg.add("browser_" + m.group(1))
    for m in re.finditer(r'置整数值 \("(browser_[a-z0-9_]+)"', all_text):
        reg.add(m.group(1))
    tools = set(re.findall(r'添加工具JSON \("([a-z0-9_]+)"', all_text))
    not_advertised = sorted(reg - tools)
    alias = [g for g in not_advertised if g.startswith("browser_")
             and g[len("browser_"):] in tools]
    # 刻意的守卫分支: 名字可路由、分支存在、但**故意不实现**, 并给出原因与替代方案。
    # 依据 = 真机回包原文(_audit/probe_ghost_names.py 实测), 不是猜测。
    deliberate = [g for g in not_advertised
                  if g not in alias and g in DELIBERATE_GATES]
    ghost = [g for g in not_advertised if g not in alias and g not in deliberate]

    return dict(files=files, notes=notes, deadc=deadc, resid=resid,
                zero_ref=zero_ref, zero_member=zero_member, dup=dup, ghost=ghost,
                ghost_alias=alias, ghost_gate=deliberate,
                tool_count=len(tools), event_m=virt_m, sym_m=sym_m)


def main():
    r = scan()
    print("== 代码卫生扫描 ==")
    print("源文件 %d 个, 工具定义 %d 个" % (len(r["files"]), r["tool_count"]))
    strong = [x for x in r["notes"] if x[2] == "STRONG"]
    medium = [x for x in r["notes"] if x[2] == "MEDIUM"]
    print("操作备注(开发过程叙述) = %d  (强特征 %d / 版本变更类 %d)" %
          (len(r["notes"]), len(strong), len(medium)))
    print("死代码备注(注释掉的语句) = %d" % len(r["deadc"]))
    print("残注释(已移除/已废弃…)   = %d" % len(r["resid"]))
    print("零引用方法              = %d  (已排除事件接收方法 %d 个 / 带@输出名可被嵌入C++调用 %d 个)" %
          (len(r["zero_ref"]), r["event_m"], r["sym_m"]))
    print("零引用成员              = %d" % len(r["zero_member"]))
    print("重复分支工具            = %d  %s" % (len(r["dup"]), sorted(r["dup"])[:12]))
    print("未广告的路由别名        = %d  %s  (browser_ 前缀可省略, 实测均能正常回包, 非缺口)"
          % (len(r["ghost_alias"]), r["ghost_alias"]))
    print("刻意的守卫分支          = %d  %s  (实测有明确原因+替代方案, 非缺口)"
          % (len(r["ghost_gate"]), r["ghost_gate"]))
    print("幽灵注册(待核实)        = %d  %s" % (len(r["ghost"]), r["ghost"]))

    def by_file(items, idx=0):
        d = {}
        for it in items:
            d[it[0]] = d.get(it[0], 0) + 1
        return sorted(d.items(), key=lambda x: -x[1])

    print("\n-- 操作备注按文件 --")
    for f, n in by_file(r["notes"]):
        print("   %-30s %d" % (f, n))

    md = ["# 代码卫生扫描报告\n",
          "> 由 `_audit/cleanup_scan.py` 生成（只读扫描，不改代码）\n",
          "\n## 摘要\n",
          "| 项目 | 数量 |", "|---|---|",
          "| 源文件 | %d |" % len(r["files"]),
          "| 工具定义 | %d |" % r["tool_count"],
          "| 操作备注(STRONG) | %d |" % len(strong),
          "| 操作备注(版本变更类) | %d |" % len(medium),
          "| 死代码备注 | %d |" % len(r["deadc"]),
          "| 残注释 | %d |" % len(r["resid"]),
          "| 零引用方法 | %d |" % len(r["zero_ref"]),
          "| 零引用成员 | %d |" % len(r["zero_member"]),
          "| 重复分支工具 | %d |" % len(r["dup"]),
          "| 未广告的路由别名（非缺口） | %d |" % len(r["ghost_alias"]),
          "| 刻意的守卫分支（非缺口） | %d |" % len(r["ghost_gate"]),
          "| 幽灵注册（待核实） | %d |" % len(r["ghost"]),
          "\n## 操作备注（STRONG，建议清理）\n"]
    for f, i, k, s in strong[:200]:
        md.append("- `%s:%d` %s" % (f, i, s))
    md.append("\n## 死代码备注（注释掉的语句）\n")
    for f, i, s in r["deadc"][:200]:
        md.append("- `%s:%d` %s" % (f, i, s))
    md.append("\n## 残注释\n")
    for f, i, s in r["resid"][:120]:
        md.append("- `%s:%d` %s" % (f, i, s))
    md.append("\n## 零引用方法（需人工确认后再删）\n")
    for it in r["zero_ref"][:200]:
        md.append("- `%s:%d` %s   %s" % (it[0], it[1], it[2], it[3] if len(it) > 3 else ""))
    md.append("\n## 零引用成员\n")
    for f, i, nm in r["zero_member"][:200]:
        md.append("- `%s:%d` %s" % (f, i, nm))
    md.append("\n## 重复分支\n")
    for k, v in sorted(r["dup"].items()):
        md.append("- `%s` → %s" % (k, "; ".join("%s:%d" % (a, b) for a, b in v)))
    md.append("\n## 未广告的路由别名（`browser_` 前缀可省略；实测均能正常回包，**不是缺口**）\n")
    for g in r["ghost_alias"]:
        md.append("- %s" % g)
    md.append("\n## 刻意的守卫分支（可路由、故意不实现、回包给了原因与替代方案；**不是缺口**）\n")
    for g in r["ghost_gate"]:
        md.append("- %s —— %s" % (g, DELIBERATE_GATES.get(g, "")))
    md.append("\n## 幽灵注册（待人工核实：可能没实现，也可能是刻意的守卫分支）\n")
    for g in r["ghost"]:
        md.append("- %s" % g)

    p = os.path.join(HERE, "_cleanup_report.md")
    with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))
    print("\n明细已写 _cleanup_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
