# -*- coding: utf-8 -*-
"""把 6 个"致命/污染全局"工具的人工受控实测**补记进台账**。

背景: tool_ledger.py 的 CLI 对 MP.LETHAL/MUTATING_SKIP 直接 `continue`(见其 main()),
所以这 6 个永远进不了台账, 长期被算成"未测" —— 实测其实早在报告 §103.1 做过并全部存活。
本脚本按台账同一 record schema 补记, 并把**测法**与**原文**一并写进 note(可审计)。

禁止事项: 本脚本不调用任何 MCP 工具(纯记账), 只读报告原文作为事实来源。
"""
import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import tool_ledger as TL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 事实来源: 报告 §103.1 的表格(测法 + 实测结果原文 + 存活)
FACTS = {
    "browser_set_preference": dict(
        args={"action": "set", "key": "webkit.webprefs.javascript_enabled", "value": "true"},
        why_safe="把 webkit 首选项设成它本来就是的值(不改变任何行为)",
        result="首选项 webkit.webprefs.javascript_enabled 已设置"),
    "browser_set_s5_proxy": dict(
        args={"host": "127.0.0.1", "port": 1, "needs_reload": True},
        why_safe="指向本机无效端口 127.0.0.1:1, 测完立刻重启清掉",
        result="S5代理已设置: 127.0.0.1:1 ... + 如实给出 needs_reload:true"),
    "browser_reverse_patch": dict(
        args={"dry_run": True},
        why_safe="用它自带的 dry_run:true (只验证编译不替换)",
        result="dryRun 通过(新源码可编译, 未实际替换)"),
    "browser_close": dict(
        args={"browser_id": 2},
        why_safe="先建第二个后台浏览器, 只关 browser_id=2, 不动主浏览器",
        result="浏览器已关闭: id=2"),
    "browser_close_try": dict(
        args={},
        why_safe="放靠后执行; 文档说它会关浏览器",
        result="⛔ 远程关闭浏览器已禁用…(如实拒绝, 未造成影响)"),
    "browser_shutdown": dict(
        args={"confirm": True},
        why_safe="最后一项, confirm:true + 2 秒延迟",
        result="AI浏览器将在2秒后安全关闭, 感谢使用 (重启后恢复)"),
}


def main():
    d = TL.load()
    tools = {t.get("name") for t in TL.tool_list()}

    # 校验: 报告里确实有这些记录(避免我凭记忆写台账)
    rep = io.open(os.path.join(ROOT, 'MCP工具可用性检测报告.md'),
                  encoding='utf-8').read()
    missing_doc = [n for n in FACTS if n not in rep]
    if missing_doc:
        print('!! 报告里找不到这些工具名, 中止: %s' % missing_doc)
        return 1
    missing_tool = [n for n in FACTS if n not in tools]
    if missing_tool:
        print('!! 工具列表里没有(名字不对, 中止): %s' % missing_tool)
        return 1

    rnd = (max([r.get("round", 0) for r in d.values()] or [0]) + 1)
    ts = time.strftime("%m-%d %H:%M")
    rows = []
    for name, f in FACTS.items():
        old = d.get(name)
        note = ("[人工受控实测·非探针] 测法: %s || 原文: %s || 当时实例存活; "
                "补记原因: 台账 CLI 对 LETHAL 工具直接跳过, 故长期被算作未测"
                % (f["why_safe"], f["result"]))
        r = {"tool": name, "cls": "OK_MANUAL", "elapsed": 0.0, "args": f["args"],
             "note": note[:300], "ts": ts, "round": rnd, "status": "pass",
             "manual": True}
        if old:
            r["prev"] = {"status": old.get("status"), "cls": old.get("cls")}
        d[name] = r
        rows.append(r)
        print('   %-32s -> pass (原状态: %s)' % (name, (old or {}).get('status', '未测')))

    TL.save(d)
    TL.append_md(rows)
    print('已补记 %d 条 (第 %d 轮); 总进度 %d/%d'
          % (len(rows), rnd, len([k for k in d if k in tools]), len(tools)))
    return 0


sys.exit(main())
