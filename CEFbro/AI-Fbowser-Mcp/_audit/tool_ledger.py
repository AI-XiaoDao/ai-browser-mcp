# -*- coding: utf-8 -*-
"""功能台账 —— 逐个功能测试并逐条记录（用户要求：一次测一个，不做全量）。

设计要点:
  · 状态持久化在 _audit/_tool_ledger.json, **跨轮累积**, 已测过的默认不再重测。
  · 每轮只测"尚未测过"的若干项(--next N)或指定单项(--tool 名称)。
  · 复用 cold_matrix 的 build_args/classify/活性探针/冷重启 —— 不重复造轮子。
  · 只在**该功能确实把实例搞卡**时才冷重启(先做便宜的 browser_status 活性探针)。
  · 每条记录同步追加到 _tool_ledger.md(人读) 与 json(机读)。

用法:
  py -3 tool_ledger.py --status            # 看进度总览
  py -3 tool_ledger.py --next 6            # 测接下来 6 个未测的
  py -3 tool_ledger.py --tool browser_stop # 测指定单个
  py -3 tool_ledger.py --next 6 --retest   # 连已测过的也重测
"""
import io
import json
import os
import sys
import time

# 控制台是 GBK 代码页, 而台账里的备注含中文与 emoji(⛔/✅ 等) —— 实测 `--status`
# 打印失败明细时抛 UnicodeEncodeError, 导致"看进度总览"这个最基本的功能直接崩掉(exit 1),
# 于是明明有失败项却看不到。这里把 stdout/stderr 强制成 utf-8 且不可编码字符用 'replace' 兜底:
# 报告宁可少一个字符, 也不能因为一个 emoji 把整个总览吞掉。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mass_probe as MP
import cold_matrix as CM   # 复用: alive / cold_restart / prereq_of / http_post
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

LEDGER = os.path.join(HERE, "_tool_ledger.json")
MD = os.path.join(HERE, "_tool_ledger.md")
# 每工具超时上限: 有些工具自带长超时(browser_debugger_wait_paused 会等满自身 30s,
# browser_debugger_flow 40s+), 逐功能测时会把整轮预算吃光(实测那批 76s, 其他批次仅 1–12s)。
# 用户明确要求"不要每次测试都太耗时间", 故此处收紧; 超时的结论仍是"该工具在此参数下超时", 判定不受损。
TOOL_TIMEOUT = 15


def load():
    if os.path.exists(LEDGER):
        try:
            return json.load(io.open(LEDGER, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save(d):
    with io.open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def tool_list():
    tl = CM.http_get("/tools/list", timeout=20)
    return tl.get("tools", [])


def test_one(t, rec, round_no):
    """测单个工具, 返回记录 dict。"""
    name = t.get("name")
    schema = t.get("inputSchema") or {}
    desc = t.get("description") or ""
    # build_args 返回元组 (args, notes), 必须解包 —— 否则 arguments 会变成数组而全部失真
    # 传入工具名以启用"工具级入参覆盖"(补上那些被声明为可选、却是实现真正需要的入参)
    args, _anotes = MP.build_args(schema, desc, name)
    # 数值型参数必须给数字: mass_probe 的取值为通用文本, 会让 integer/number 参数拿到 "mcp_probe"
    # 而报"不是有效数字" —— 那是测试侧假失败, 会污染台账。此处按 schema 类型强制纠正。
    _props = (schema or {}).get("properties", {}) or {}
    for _k, _v in list(args.items()):
        _t = ((_props.get(_k) or {}).get("type") or "").lower()
        if _t in ("integer", "number") and not isinstance(_v, (int, float)):
            try:
                args[_k] = int(str(_v))
            except Exception:
                args[_k] = 1
    if name in MP.SPECIAL_ARGS:
        args = dict(MP.SPECIAL_ARGS[name])
    # 运行期取值(与 mass_probe 同一张表): 句柄/任务ID 之类**每次启动都不同**, 预置常量只会测到
    # "目标不存在"。实测 browser_find_by_hwnd 长期用假句柄 1 -> 台账记成"未找到窗口句柄为 1 的浏览器";
    # 换成真实句柄立刻成功, 属探针假目标。此处复用 MP.DYNAMIC_ARGS, 避免两处逻辑漂移。
    if name in getattr(MP, "DYNAMIC_ARGS", {}):
        try:
            _extra = MP.DYNAMIC_ARGS[name](None)
            if _extra and all(v not in (0, "", None) for v in _extra.values()):
                args = dict(args)
                args.update(_extra)
                _anotes = list(_anotes) + ["运行期取值: %s" % sorted(_extra.keys())]
        except Exception as _dex:
            _anotes = list(_anotes) + ["运行期取值失败: %r" % _dex]
    # 工具级前置调用: 有些工具语义上依赖某状态(如"页面上等暂停"), 单次探针构造不出来,
    # 于是只能记成"超时" —— 那等于把"这工具到底能不能用"答错了。这里按 MP.TOOL_PRE_CALLS
    # 执行最小前置序列, 并**把每条前置的结果写进备注**(透明, 不隐藏事实)。
    _pre = []
    for _pname, _pargs in (MP.TOOL_PRE_CALLS.get(name) or []):
        _pst = time.time()
        try:
            _presp = CM.http_post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                   "params": {"name": _pname, "arguments": _pargs}},
                                  TOOL_TIMEOUT)
            _pcls, _pnote = MP.classify(_pname, _pargs, _presp, time.time() - _pst, None)
            _pre.append("%s -> %s" % (_pname, _pcls))
        except Exception as _pex:
            _pre.append("%s -> EXC:%s" % (_pname, _pex))
    st = time.time()
    err = None
    try:
        resp = CM.http_post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": name, "arguments": args}}, TOOL_TIMEOUT)
    except Exception as ex:
        resp, err = None, str(ex)
    el = time.time() - st
    cls, note = MP.classify(name, args, resp, el, err)
    r = {"tool": name, "cls": cls, "elapsed": round(el, 2), "args": args,
         "note": (note or "")[:300], "ts": time.strftime("%m-%d %H:%M"), "round": round_no}
    if _pre:
        r["pre_calls"] = _pre
        r["note"] = (("[前置] " + "; ".join(_pre) + " || ") + (note or ""))[:300]
    if "auto_prepared" in (note or ""):
        r["auto_prepared"] = True
    if cls in ("OK", "OK_EMPTY_TEXT"):
        r["status"] = "pass"
    else:
        kind, why = CM.prereq_of(note)
        r["kind"] = kind
        r["why"] = why
        r["status"] = "fail"
    # 卡死检测(仅对失败或明显变慢的调用做活性探针)。
    # 注意: **客户端超时(TOOL_TIMEOUT)后不做探针** —— 服务端自身超时更长(30~40s), 此刻它仍持有
    # 协议锁, 探针必然失败, 会被误判成"把实例搞死了"。第 57 轮实测: 两个调试器工具因此各被误标
    # fail(wedge) 并多花一次冷重启(~11s), 收益被抵消。真正的活性判定交给下一轮循环前的 pre-check
    # (那里若实例真死了会冷重启), 两者不重复。
    if cls != "TIMEOUT" and (cls in ("TRANSPORT_ERR", "NO_RESPONSE") or el > 4.0) and not CM.alive():
        r["wedge"] = True
        r["status"] = "fail(wedge)"
        print("      !! 把实例卡死了 -> 冷重启")
        CM.cold_restart()
    return r


def append_md(rows):
    new = not os.path.exists(MD)
    with io.open(MD, "a", encoding="utf-8", newline="\n") as f:
        if new:
            f.write(u"# MCP 功能逐个测试台账\n\n"
                    u"> 由 `_audit/tool_ledger.py` 逐条追加。一次只测一个功能，跨轮累积，不重复测。\n\n"
                    u"| 时间 | 轮次 | 工具 | 状态 | 耗时 | 类别 | 失败性质 | 说明 |\n"
                    u"|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(u"| %s | %s | `%s` | %s | %.2fs | %s | %s | %s |\n" % (
                r["ts"], r.get("round", ""), r["tool"], r["status"], r["elapsed"], r["cls"],
                r.get("kind", ""), (r.get("note") or "").replace("|", "/")[:110]))


def main():
    d = load()
    tools = {t.get("name"): t for t in tool_list()}
    if "--status" in sys.argv:
        total = len(tools)
        done = [k for k in d if k in tools]
        ok = [k for k in done if d[k]["status"] == "pass"]
        bad = [k for k in done if d[k]["status"].startswith("fail")]
        wed = [k for k in done if d[k].get("wedge")]
        prep = [k for k in done if d[k].get("auto_prepared")]
        print("== 功能台账 ==")
        print("工具总数 %d | 已测 %d | 未测 %d" % (total, len(done), total - len(done)))
        print("通过 %d | 失败 %d | 其中把实例卡死 %d" % (len(ok), len(bad), len(wed)))
        print("auto_prepared 生效 %d" % len(prep))
        from collections import Counter
        c = Counter(d[k].get("kind", "") for k in bad)
        for k, v in c.most_common():
            print("   失败性质 %-12s %d" % (k or "(未分类)", v))
        if bad:
            print("\n未通过明细:")
            for k in sorted(bad):
                print("   %-40s %-10s %s" % (k, d[k].get("kind", ""), (d[k].get("note") or "")[:80]))
        return 0

    todo = None
    if "--tool" in sys.argv:
        nm = sys.argv[sys.argv.index("--tool") + 1]
        if nm not in tools:
            print("!! 没有该工具: %s" % nm)
            return 2
        todo = [tools[nm]]
    else:
        n = 6
        if "--next" in sys.argv:
            n = int(sys.argv[sys.argv.index("--next") + 1])
        retest = "--retest" in sys.argv
        names = [k for k in tools if retest or k not in d]
        todo = [tools[k] for k in names[:n]]
    if not todo:
        print("没有待测工具(全部已测过)。要看总览: --status")
        return 0

    rnd = (max([r.get("round", 0) for r in d.values()] or [0]) + 1)
    print("== 逐个测试 (第 %d 轮, %d 个) ==" % (rnd, len(todo)))
    rows = []
    t0 = time.time()
    for t in todo:
        name = t["name"]
        if name in MP.LETHAL or name in MP.MUTATING_SKIP:
            print("   %-40s 跳过(致命/污染全局)" % name)
            continue
        if not CM.alive(5):
            print("   (实例不活, 先冷重启)")
            CM.cold_restart()
        r = test_one(t, d, rnd)
        d[name] = r
        rows.append(r)
        print("   %-40s %-12s %5.2fs %s" % (name, r["status"], r["elapsed"],
                                            (r.get("note") or "")[:70]))
        save(d)
    append_md(rows)
    print("== 本轮 %.1fs, 已记录 %d 条; 总进度 %d/%d ==" %
          (time.time() - t0, len(rows), len([k for k in d if k in tools]), len(tools)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
