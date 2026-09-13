# -*- coding: utf-8 -*-
"""第四轮修复的在线验证: 同源(CEF JS 回调返空值 -> 字面 "null")缺陷的四处修复。

覆盖:
  A. browser_get_text  全文模式 CDP 优先 (原走 取文本_异步, 偶发 15s 超时)
  B. browser_get_text  selector 模式 (原有修复, 回归)
  C. browser_fill_attr_get  属性/元素双哨兵 (本轮新增)
  D. browser_dom_query / browser_dom_inner_html 哨兵 (回归)
  E. browser_scrape extract_selector 路径 CDP 优先 (本轮新增)
  F. browser_fill_attr_get 省略 attribute 的 textContent 路径 (回归)

判定纪律: 先断言响应成功/失败, 再做内容断言; 期望值来自页面事实或源码, 不凭记忆。
"""
import io
import json
import os
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
URL = "https://example.com/"
H1 = "Example Domain"

results = []


def post(payload, timeout=40):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def call(name, args, timeout=40):
    """返回 (isError, 文本, 原始响应)。"""
    try:
        resp = post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": name, "arguments": args}}, timeout)
    except Exception as ex:
        return True, "EXC: %s" % ex, None
    res = resp.get("result") or {}
    is_err = bool(res.get("isError"))
    txt = ""
    for item in res.get("content") or []:
        if item.get("type") == "text":
            txt += item.get("text") or ""
    if not txt:
        txt = json.dumps(res, ensure_ascii=False)
    return is_err, txt, resp


def rec(tag, ok, detail):
    results.append((tag, ok, detail))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, detail[:150]))


def expect_ok(tag, name, args, needle, timeout=40):
    """成功响应 + 内容含 needle。"""
    is_err, txt, _ = call(name, args, timeout)
    if is_err:
        rec(tag, False, "预期成功但返回错误: " + txt[:160])
        return None
    if needle is not None and needle not in txt:
        rec(tag, False, "成功但内容不含 %r: %s" % (needle, txt[:160]))
        return txt
    rec(tag, True, txt[:110].replace("\n", "\\n"))
    return txt


def expect_err(tag, name, args, needle, timeout=40):
    """失败响应 + 错误文本含 needle。"""
    is_err, txt, _ = call(name, args, timeout)
    if not is_err:
        rec(tag, False, "预期失败(isError=true)但返回成功: " + txt[:160])
        return
    if needle not in txt:
        rec(tag, False, "已报错但文案不含 %r: %s" % (needle, txt[:160]))
        return
    rec(tag, True, txt[:130].replace("\n", "\\n"))


def main():
    print("== 0. 环境准备 ==")
    try:
        h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=10).read())
        print("  health: cdp_ready=%s browsers=%s" % (h.get("cdp_ready"), h.get("browsers")))
        if not h.get("cdp_ready"):
            print("  !! CDP 未就绪, 先启用监管者")
            call("browser_vip_enable_inspector", {"enable": True})
            time.sleep(2)
    except Exception as ex:
        print("  !! health 取不到, 服务未启动? %s" % ex)
        return 2

    call("browser_navigate", {"url": URL, "wait_for_load": True}, timeout=60)
    time.sleep(0.6)

    print("\n== 1. 对照项(证明页面与链路正常) ==")
    expect_ok("对照 browser_execute_js 1+1", "browser_execute_js",
              {"code": "1+1"}, "2")

    print("\n== A. browser_get_text 全文模式(本轮 CDP 优先) ==")
    t = expect_ok("A1 全文含页面标题", "browser_get_text", {}, H1)
    if t:
        # 稳定性: 原缺陷为偶发 15s 超时, 连测 3 次
        for i in (2, 3):
            expect_ok("A%d 全文复测含标题" % i, "browser_get_text", {}, H1)

    print("\n== B. browser_get_text selector 模式(回归) ==")
    expect_ok("B1 h1 文本", "browser_get_text", {"selector": "h1"}, H1)
    expect_err("B2 不存在元素报错", "browser_get_text",
               {"selector": "#nonexistent-xyz"}, "元素不存在")

    print("\n== C. browser_fill_attr_get 双哨兵(本轮新增) ==")
    # a[href] 是真实 HTML 属性
    expect_ok("C1 真实属性 href", "browser_fill_attr_get",
              {"selector": "a", "attribute": "href"}, "iana.org")
    # textContent 是 DOM property 而非 HTML attribute -> 应为可操作的"属性不存在"
    expect_err("C2 property 当属性取 -> 属性不存在", "browser_fill_attr_get",
               {"selector": "h1", "attribute": "textContent"}, "属性不存在")
    expect_err("C3 元素不存在报错", "browser_fill_attr_get",
               {"selector": "#nonexistent-xyz", "attribute": "href"}, "元素不存在")
    # 省略 attribute -> textContent 回退路径
    expect_ok("C4 省略 attribute 取 textContent", "browser_fill_attr_get",
              {"selector": "h1"}, H1)

    print("\n== D. 其余读取工具哨兵(回归) ==")
    expect_err("D1 dom_query 不存在元素", "browser_dom_query",
               {"selector": "#nonexistent-xyz"}, "元素不存在")
    expect_ok("D2 dom_inner_html h1", "browser_dom_inner_html",
              {"selector": "h1"}, H1)
    expect_err("D3 dom_inner_html 不存在元素", "browser_dom_inner_html",
               {"selector": "#nonexistent-xyz"}, "元素不存在")

    print("\n== E. browser_scrape extract_selector(本轮 CDP 优先) ==")
    # browser_scrape 返回提交信封({"success":true,"_async":true,"task_id":...}), 需用 mcp_result 轮询推进
    # 阶段机(phase 0→2→3)。判据用 task_id 是否存在, 不能用 "爬虫中"/"_waiting" ——
    # 提交信封本身不含这两个标记(上一版即因此没轮询, 把信封误判成"未含期望文本")。
    import re as _re
    is_err, txt, resp = call("browser_scrape",
                             {"url": URL, "extract_selector": "h1",
                              "max_ms": 15000}, timeout=90)
    seen = txt
    m = _re.search(r"task_\d+_\d+_\d+", json.dumps(resp or {}, ensure_ascii=False) + txt)
    deadline = time.time() + 75
    polls = 0
    while (not is_err) and m and time.time() < deadline:
        if H1 in seen:                       # 已拿到真值
            break
        if "失败" in seen or '"error"' in seen:
            break
        time.sleep(2)
        polls += 1
        is_err, seen2, _ = call("mcp_result", {"request_id": m.group(0)}, timeout=40)
        if seen2:
            seen = seen2
        else:
            break
    print("     (轮询 %d 次, 最终响应 %d 字符)" % (polls, len(seen)))
    if is_err:
        rec("E1 scrape extract 提取 h1", False, "返回错误: " + seen[:160])
    elif H1 not in seen:
        rec("E1 scrape extract 提取 h1", False,
            "未含期望文本(旧缺陷为静默返回 null): " + seen[:170].replace("\n", "\\n"))
    else:
        rec("E1 scrape extract 提取 h1", True, seen[:110].replace("\n", "\\n"))

    print("\n== 汇总 ==")
    bad = [t for t, ok, _ in results if not ok]
    print("  通过 %d / %d" % (len(results) - len(bad), len(results)))
    for t in bad:
        print("  未通过: %s" % t)
    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "_verify_round4.json"), "w", encoding="utf-8") as f:
        json.dump([{"tag": t, "ok": o, "detail": d} for t, o, d in results],
                  f, ensure_ascii=False, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
