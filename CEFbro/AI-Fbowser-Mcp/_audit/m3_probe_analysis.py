# -*- coding: utf-8 -*-
r"""M3 — 探针结果深度分析

对 m1_probe.py 的原始结果重新分级（M1 的分类器把"需要code参数"这类
虽短但可行动的信息误判为 BAD_ERR），并逐项定性。
"""
import json, os, re, collections
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

OUT = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(OUT, "probe_raw.json"), encoding="utf-8"))

W = []
def w(s=""):
    W.append(s)

# ---- 重新分级 ----
GENERIC = "请查看工具描述补全必填参数"
def regrade(r):
    if r["cat"] in ("TIMEOUT", "TRANSPORT", "NOTFOUND"):
        return r["cat"]
    t = r["detail"]
    if r["cat"] == "OK":
        return "OK"
    # 失败 -> 看信息质量
    if not t.strip():
        return "ERR_EMPTY"
    if "未知命令" in t or "结果解析失败" in t or "内部错误" in t:
        return "ERR_INTERNAL"
    if GENERIC in t and len(t) < 40:
        return "ERR_WEAK"          # 泛化提示, 未指出具体参数
    if re.search(r"(不能为空|需要|缺少|必须|请先|无效|不支持|超时|未找到|失败|格式)", t):
        return "ERR_GOOD"          # 指出了具体缺失/原因
    return "ERR_WEAK"

for r in rows:
    r["grade"] = regrade(r)

c = collections.Counter(r["grade"] for r in rows)
w("=" * 104)
w("M3 探针结果深度分析  (265 个工具真机调用)")
w("=" * 104)
w()
w("%-14s %4s  %s" % ("分级", "数量", "含义"))
w("-" * 104)
MEAN = {
    "OK": "成功返回且 content 非空",
    "ERR_GOOD": "失败，但信息指出了具体参数/原因/下一步 —— **正确行为**",
    "ERR_WEAK": "失败，但只有泛化提示(未指出哪个参数) —— 可优化",
    "ERR_EMPTY": "失败且信息为空 —— 缺陷",
    "ERR_INTERNAL": "失败且为内部错误/未知命令 —— 缺陷",
    "TIMEOUT": "客户端 6s 超时 —— 需判定是设计如此还是缺陷",
    "TRANSPORT": "连接/协议层错误",
    "NOTFOUND": "JSON-RPC -32601 工具不存在",
}
for k, v in c.most_common():
    w("%-14s %4d  %s" % (k, v, MEAN.get(k, "")))
w()

# ---- TIMEOUT 逐项 ----
w("=" * 104)
w("【重点 1】17 个 TIMEOUT —— 逐项判定")
w("=" * 104)
w()
timeouts = [r for r in rows if r["grade"] == "TIMEOUT"]
w("%-42s %-6s %s" % ("工具", "仅校验", "描述"))
w("-" * 104)
for r in timeouts:
    w("%-42s %-6s %s" % (r["name"], "是" if r["mutate_only"] else "否",
                         (r["desc"] or "")[:56]))
w()

# ---- 错误信息质量 ----
w("=" * 104)
w("【重点 2】错误信息质量 (影响 AI 能否自我纠正)")
w("=" * 104)
w()
weak = [r for r in rows if r["grade"] in ("ERR_WEAK", "ERR_EMPTY", "ERR_INTERNAL")]
w("需要改进的失败信息: %d 个" % len(weak))
for r in weak:
    w("   %-42s [%s]" % (r["name"], r["grade"]))
    w("        %s" % (r["detail"][:110] or "(空)"))
w()

# ---- 成功但返回结构可疑 ----
w("=" * 104)
w("【重点 3】成功返回的结构形态 (AI 解析友好度)")
w("=" * 104)
w()
shapes = collections.Counter()
samples = collections.defaultdict(list)
for r in rows:
    if r["grade"] != "OK":
        continue
    t = r["detail"].strip()
    if t.startswith("{"):
        try:
            j = json.loads(t)
            if isinstance(j, dict):
                if j.get("_async"):
                    k = "异步 stub (需 mcp_result 轮询)"
                elif "data" in j:
                    k = "succ,msg,data 三层包裹"
                elif "result" in j:
                    k = "含 result 字段"
                else:
                    k = "succ+msg 扁平"
                if j.get("_async"):
                    shapes["异步 stub (需 mcp_result 轮询)"] += 1
                    samples["异步 stub (需 mcp_result 轮询)"].append(r["name"])
                    continue
            else:
                k = "JSON 数组"
        except Exception:
            k = "文本(形似JSON但解析失败)"
    elif t.startswith("["):
        k = "JSON 数组"
    else:
        k = "纯文本"
    shapes[k] += 1
    if len(samples[k]) < 8:
        samples[k].append(r["name"])
for k, v in shapes.most_common():
    w("   %-34s %3d   例: %s" % (k, v, ", ".join(samples[k][:5])))
w()

# ---- 参数校验覆盖 ----
w("=" * 104)
w("【重点 4】无参数工具 (74 个) 是否真的都无需参数")
w("=" * 104)
w()
nop = [r for r in rows if not (r["schema"] or {}).get("properties")]
ok_nop = [r for r in nop if r["grade"] == "OK"]
bad_nop = [r for r in nop if r["grade"] not in ("OK", "TRANSPORT")]
w("   无参数 schema 的工具: %d  (其中无参调用成功 %d, 其余 %d)" % (len(nop), len(ok_nop), len(bad_nop)))
for r in bad_nop[:25]:
    w("      %-42s %-12s %s" % (r["name"], r["grade"], r["detail"][:70]))
w()

# ---- 异步工具清单 (需轮询, 对 AI 是负担) ----
w("=" * 104)
w("【重点 5】返回异步 stub、需要 mcp_result 轮询的工具")
w("=" * 104)
w()
asy = samples.get("异步 stub (需 mcp_result 轮询)", [])
w("   共 %d 个（探针用空参数调用即返回 stub，说明这些工具**默认异步**）" % len(asy))
for n in asy:
    w("      %s" % n)

p = os.path.join(OUT, "report_M3_probe.txt")
open(p, "w", encoding="utf-8", newline="\n").write("\n".join(W))
json.dump(rows, open(os.path.join(OUT, "probe_graded.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("written", p)
print(dict(c))
