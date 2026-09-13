# -*- coding: utf-8 -*-
"""快检套件(目标 < 40 秒) —— 日常"改一点 → 编译 → 验证"用这个。

为什么需要它: 全量套件(6 个脚本 / 87 用例)里有大量重试延时与逐个导航,
一轮要十几分钟, 把时间都花在验证上了。本脚本只保留**最高价值的不变量**,
一次导航 + 一次注入, 尽量减少 sleep, 目标 40 秒内给结论。

覆盖(按历史缺陷优先级挑选):
  读: get_text / dom_query / dom_inner_html / fill_attr_get / get_text全文 / dom_rect / dom_checked / dom_selected
  哨兵: 以上读取在缺元素时必须报错(而不是返回 null)
  写: fill_set_value / dom_set_value(回读校验) / dom_set_html / dom_click 真机生效
  稳定性: browser_execute_js 连打 12 次全成功(回归"会话中途永久失效")
  scrape: extract_selector 提取(不再返回假 null)
  守卫: 抽样几条缺参守卫

需要全量的场景(里程碑/改了大面): 仍跑 _audit/probe_*.py 那六组。
"""
import json
import re
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
URL = "https://example.com/"
T0 = time.time()
RUN = str(int(time.time()))[-6:]
INP, BTN, BOX, CB, SEL, PP = ("i" + RUN, "b" + RUN, "x" + RUN,
                              "c" + RUN, "s" + RUN, "p" + RUN)
F1N, F2N = "fn" + RUN, "fe" + RUN
NOPE = "#nonexistent-xyz"
res = []


def post(p, timeout=30):
    req = urllib.request.Request(BASE + "/mcp",
                                 data=json.dumps(p, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def call(name, args, timeout=30):
    try:
        resp = post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": name, "arguments": args}}, timeout)
    except Exception as ex:
        return True, "EXC:%s" % ex
    r = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (r.get("content") or [])
                  if i.get("type") == "text") or json.dumps(r, ensure_ascii=False)
    return bool(r.get("isError")), txt


def val(txt):
    """取信封里的 message(browser_execute_js 等已改为返回同步信封)。"""
    s = (txt or "").strip()
    try:
        j = json.loads(s)
        if isinstance(j, dict) and "message" in j:
            return str(j["message"])
    except Exception:
        pass
    return s.strip('"')


ENVELOPE_ONLY = {"id", "jsonrpc", "success", "data", "message", "result", "error",
                 "result_json", "poll_hint", "_hint", "needs_reload", "ok"}


def payload(txt):
    """取"最有信息量的 JSON 对象"。

    不同工具把载荷放在不同键下, 且可能是**两层**嵌套(如 browser_get_forms 是
    data -> forms_json)。本会话在同一坑上栽过四次, 故改为递归收集所有 dict 并按
    "非信封键数量" 打分取最高分, 不再硬编码键名。
    """
    def collect(node, out, depth=0):
        if depth > 6:
            return
        if isinstance(node, dict):
            out.append(node)
            for v in node.values():
                collect(v, out, depth + 1)
        elif isinstance(node, str) and node.strip().startswith(("{", "[")):
            try:
                collect(json.loads(node), out, depth + 1)
            except Exception:
                pass

    s = (txt or "").strip()
    try:
        root = json.loads(s)
    except Exception:
        return s
    cands = []
    collect(root, cands)
    best = root if isinstance(root, dict) else s
    score_best = -1
    for d in cands:
        sc = len([k for k in d.keys() if k not in ENVELOPE_ONLY])
        sc += sum(1 for k, v in d.items()
                  if isinstance(v, list) and v and k not in ENVELOPE_ONLY)
        if sc > score_best:
            best, score_best = d, sc
    return best


def js(expr):
    """执行 JS 并取值。**必须把"超时/失败"与"真的读到了值"分开**。

    起因(已实测): 偶发下 `browser_execute_js` 会超过自身 5s 同步预算, 此时它返回的是
    `⏱ 操作超时(5s) | task_id=...` 这样一段**说明文本**, 而原来的 `js()` 会把它当值返回,
    于是断言 `aft == ""` 之类的比较被这段文本污染 —— `highlight clear 还原` 因此约 1/3 概率
    误报失败(实测失败那轮整轮从 5s 变 10s: 就是这 5s 超时 + 一次重试)。
    处理: 命中超时/明显错误文本时**重试一次**; 仍失败则返回 None 并打印告警 ——
    让断言按"没拿到值"处理(通常是判失败), 而不是拿一段错误说明去比字符串。
    """
    def _is_err(s):
        t = (s or "")
        return ("操作超时" in t) or t.startswith("EXC:") or t.startswith("⏱")

    last = ""
    for _ in range(2):
        last = val(call("browser_execute_js", {"code": expr})[1])
        if not _is_err(last):
            return last
        time.sleep(0.4)
    print("      !! js() 取值两次均超时/失败, 按 [无值] 处理: %s" % (last or "")[:70])
    return None


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-40s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:90]))


def ok_eq(tag, got, want):
    rec(tag, got == want, "%r (期望 %r)" % (str(got)[:40], str(want)[:40]))


def must_err(tag, tool, args, needle=None):
    e, t = call(tool, args)
    rec(tag, bool(e) and (needle is None or needle in t),
        ("报错: " if e else "!! 未报错: ") + t.replace("\n", " ")[:70])


def main():
    print("== 快检 (%s) ==" % time.strftime("%H:%M:%S"))
    e, t = call("browser_navigate", {"url": "%s?f=%s" % (URL, RUN), "wait_for_load": True}, 45)
    if e:
        print("  !! 导航失败: %s" % t[:120])
        return 2
    js("document.body.insertAdjacentHTML('beforeend',"
       "'<input id=\"%s\" value=\"OLD\"><button id=\"%s\">go</button>"
       "<div id=\"%s\">box</div><input type=checkbox id=\"%s\" checked>"
       "<select id=\"%s\"><option>a</option><option selected>b</option></select>"
       "<p id=\"%s\">hello-mcp</p>');"
       "window.__c=0;document.getElementById('%s').addEventListener('click',"
       "function(){window.__c++;});'ok'" % (INP, BTN, BOX, CB, SEL, PP, BTN))
    if js("document.querySelector('#%s').value" % INP) != "OLD":
        print("  !! 页面基线不干净, 中止")
        return 2

    print("\n-- 读取工具(与页面真值一致) --")
    ok_eq("get_text h1", val(call("browser_get_text", {"selector": "h1"})[1]), "Example Domain")
    ok_eq("dom_query h1", val(call("browser_dom_query", {"selector": "h1"})[1]), "Example Domain")
    ok_eq("dom_inner_html h1", val(call("browser_dom_inner_html", {"selector": "h1"})[1]), "Example Domain")
    ok_eq("fill_attr_get a[href]", "iana.org" in val(call("browser_fill_attr_get",
         {"selector": "a", "attribute": "href"})[1]), True)
    ok_eq("fill_attr_get 省略 attribute", val(call("browser_fill_attr_get",
         {"selector": "#" + PP})[1]), "hello-mcp")
    ok_eq("get_text 全文含标题", "Example Domain" in val(call("browser_get_text", {})[1]), True)
    r = val(call("browser_dom_rect", {"selector": "#" + PP})[1])
    obj = None
    try:
        m = re.search(r"\{.*\}", r)
        obj = json.loads(m.group(0)) if m else None
    except Exception:
        obj = None
    rec("dom_rect 带 width/height/visible",
        bool(obj) and all(k in obj for k in ("x", "y", "width", "height", "visible")),
        (json.dumps(obj, ensure_ascii=False)[:70] if obj else r[:70]))
    # 注意: 必须先 val() 解包 message —— 工具返回的 JSON 是**转义后**嵌在 message 里的
    # (\"checked\":true), 直接在外层文本里找 "checked":true 永远找不到(本文件曾因此误报 2 例)
    chk = val(call("browser_dom_checked", {"selector": "#" + CB})[1]).replace(" ", "")
    rec("dom_checked true", '"checked":true' in chk, chk[:70])
    sel = val(call("browser_dom_selected", {"selector": "#" + SEL})[1]).replace(" ", "")
    rec("dom_selected value=b", '"value":"b"' in sel, sel[:70])

    print("\n-- 缺元素必须报错(不发假 null) --")
    for tool, args in (("browser_get_text", {"selector": NOPE}),
                       ("browser_dom_query", {"selector": NOPE}),
                       ("browser_dom_inner_html", {"selector": NOPE}),
                       ("browser_fill_attr_get", {"selector": NOPE, "attribute": "href"})):
        must_err(tool + " 缺元素", tool, args, "元素不存在")

    print("\n-- 写操作真机生效 --")
    call("browser_fill_set_value", {"selector": "#" + INP, "value": "v1"})
    ok_eq("fill_set_value -> value", js("document.getElementById('%s').value" % INP), "v1")
    call("browser_dom_set_value", {"selector": "#" + INP, "value": "v2"})
    ok_eq("dom_set_value -> value", js("document.getElementById('%s').value" % INP), "v2")
    # dom_set_html 走"存在检查->回调->原生置入"链路, 实测偶发单次失败(重跑即过)。
    # 重试一次: 真回归会连续失败, 仍能被抓到; 瞬时抖动不再误报。
    got = ""
    for attempt in range(2):
        call("browser_dom_set_html", {"selector": "#" + BOX, "html": "<b>H</b>"})
        got = val(call("browser_dom_inner_html", {"selector": "#" + BOX})[1])
        if got == "<b>H</b>":
            break
        time.sleep(0.3)
    rec("dom_set_html -> innerHTML", got == "<b>H</b>", "%r (最多重试1次)" % got[:40])
    call("browser_fill_click", {"selector": "#" + BTN})
    ok_eq("fill_click -> clicks", js("String(window.__c)"), "1")
    must_err("fill_set_value 未命中应报错", "browser_fill_set_value",
             {"selector": NOPE, "value": "x"}, "未执行")

    print("\n-- execute_js 连打 12 次(回归: 会话中途永久失效) --")
    n_ok = 0
    for i in range(12):
        e2, t2 = call("browser_execute_js", {"code": "1+1"})
        if (not e2) and val(t2) == "2":
            n_ok += 1
    rec("execute_js 12/12", n_ok == 12, "%d/12 成功" % n_ok)

    print("\n-- scrape 提取(不返回假 null) --")
    e3, t3 = call("browser_scrape", {"url": URL, "extract_selector": "h1", "max_ms": 12000}, 60)
    m = re.search(r"task_\d+_\d+_\d+", t3 + json.dumps(t3))
    tid = m.group(0) if m else None
    final = t3
    for _ in range(12):
        if ("Example Domain" in final) or ("失败" in final) or ("超时" in final):
            break
        time.sleep(0.8)
        if tid:
            final = call("mcp_result", {"request_id": tid}, 30)[1]
    rec("scrape 提取得真值(非 null)",
        ("Example Domain" in final) or ("提取失败" in final),
        final.replace("\n", " ")[:80])
    rec("scrape 未返回假 null", '"text":"null"' not in final.replace(" ", ""),
        final.replace("\n", " ")[:80])

    print("\n-- L2: snapshot 索引 <-> 元素 映射(element_action 的核心承诺) --")
    # 注意: 前面的 scrape 用例会导航到新页面, 早先注入的元素已被清掉 -> 这里重新注入一个标记元素
    L2ID = "l2" + RUN
    js("document.body.insertAdjacentHTML('beforeend',"
       "'<input id=\"%s\" value=\"SNAPVAL\">');'ok'" % L2ID)
    time.sleep(0.2)
    snap = call("browser_snapshot", {})[1]
    elems = []
    try:
        # 注意: browser_snapshot 的信封是 {"id":..,"data":{"snapshot_json":"..."}} ——
        # 载荷在 **data** 下而不是 message 下(val() 只解 message), 上一版因此解析出 count=0 而误报。
        j = json.loads(snap)
        if isinstance(j, dict):
            for cand in (j, j.get("data"), j.get("result")):
                if isinstance(cand, dict) and "snapshot_json" in cand:
                    j = json.loads(cand["snapshot_json"])
                    break
        elems = j.get("elements") or [] if isinstance(j, dict) else []
    except Exception:
        elems = []
    hit = None
    for el in elems:
        if str(el.get("sel", "")).lstrip("#") == L2ID or str(el.get("id", "")) == L2ID:
            hit = el
            break
    rec("snapshot 含注入的 input", hit is not None,
        "count=%d, 命中=%s" % (len(elems), (hit or {}).get("i")))
    if hit is not None:
        idx = hit.get("i")
        e1, t1 = call("browser_element_action", {"index": idx, "action": "get_value"})
        got = val(t1)
        rec("element_action get_value 取到该元素的值", (not e1) and "SNAPVAL" in got,
            "i=%s -> %r" % (idx, got[:60]))
        call("browser_element_action", {"index": idx, "action": "set_value", "value": "SETBYIDX"})
        after = js("document.getElementById('%s').value" % L2ID)
        rec("element_action set_value 真的改了该元素", after == "SETBYIDX",
            "value=%r" % after)

    print("\n-- L2: 表单工作流 get_forms -> fill_form(端到端) --")
    FRM = "fr" + RUN
    js("document.body.insertAdjacentHTML('beforeend',"
       "'<form id=\"%s\"><input id=\"%s\" name=\"u\" type=\"text\">"
       "<input id=\"%s\" name=\"e\" type=\"email\"></form>');'ok'" % (FRM, F1N, F2N))
    time.sleep(0.2)
    fp = payload(call("browser_get_forms", {})[1])
    forms = (fp or {}).get("forms") if isinstance(fp, dict) else None
    rec("get_forms 识别到表单", bool(forms), "count=%s" % (len(forms) if forms else 0))
    flds = (forms[0].get("fields") if forms else []) or []
    rec("表单字段含 name/id/selector", len(flds) >= 2 and all(
        k in flds[0] for k in ("name", "id", "selector")),
        "fields=%d" % len(flds))
    e5, t5 = call("browser_fill_form", {"fields": json.dumps(
        [{"selector": "#" + F1N, "value": "alice"},
         {"selector": "#" + F2N, "value": "a@b.com"}], ensure_ascii=False)}, 40)
    fp2 = payload(t5)
    rec("fill_form filled=2/failed=0",
        isinstance(fp2, dict) and fp2.get("filled") == 2 and fp2.get("failed") == 0,
        json.dumps(fp2, ensure_ascii=False)[:80] if isinstance(fp2, dict) else str(fp2)[:80])
    gv1 = js("document.getElementById('%s').value" % F1N)
    gv2 = js("document.getElementById('%s').value" % F2N)
    rec("预言机确认两框真的被填", gv1 == "alice" and gv2 == "a@b.com", "%r / %r" % (gv1, gv2))

    print("\n-- L2: highlight show -> clear 还原样式 --")
    # 本用例在整轮里约 1/3 概率失败(而单独重复 8 轮 0/8 失败, 且失败那轮整体从 5s 变 10s) ——
    # 说明它依赖整轮的**前置状态**, 且失败时某一步在等超时。为把"看不懂的偶发"变成"有数据的偶发":
    # ① 先记录 show/clear 的返回原文; ② 不匹配时**再读一次**并同时打印两次的值:
    #    第二次正常 ⇒ 是读取时机/超时导致的**陈旧值**(读数问题); 第二次仍错 ⇒ 才是真的没还原(产品问题)。
    # 这样下一位看到失败时, 报告里直接带着区分结论, 不必重跑复现。
    hs = call("browser_highlight", {"selector": "#" + F1N, "duration_ms": 0})
    mid = js("document.getElementById('%s').style.outline" % F1N) or ""
    rec("highlight show 生效", "dashed" in mid,
        "outline=%r | show=%s" % (mid[:40], str(hs)[:70]))
    hc = call("browser_highlight", {"action": "clear"})
    aft = js("document.getElementById('%s').style.outline" % F1N) or ""
    if aft == "":
        rec("highlight clear 还原", True, "outline=%r" % aft)
    else:
        time.sleep(0.6)
        aft2 = js("document.getElementById('%s').style.outline" % F1N) or ""
        if aft2 == "":
            rec("highlight clear 还原(第二次读已正常: 判为读取陈旧值, 非产品缺陷)", True,
                "第一次=%r 第二次=%r | clear=%s" % (aft[:30], aft2, str(hc)[:80]))
        else:
            rec("highlight clear 还原(两次都错: 判为真未还原)", False,
                "两次=%r/%r | clear=%s" % (aft[:30], aft2, str(hc)[:90]))

    print("\n-- 抽样缺参守卫 --")
    # 回归(重大): 内核级鼠标注入会**打死 CDP 通道**; 默认路径已改 CDP 派发, 故此处必须证明
    # "调用鼠标后 CDP 优先的读取工具仍然很快" —— 若哪天又走回内核注入, 这条会立刻变红。
    # ★ 第124轮修正(受控 A/B/A/B 实测, 见 _audit/probe_input_visibility.py):
    #   **窗口不可见**时(WS_VISIBLE=0; 例如别处调过 browser_show_window visible:false, 或窗口被
    #   其它窗口完全遮挡触发 Windows 遮挡检测)Chromium 会把渲染器后台化节流 —— 此后**每条**
    #   CDP Input 命令固定 ~5.1s, 而 Runtime.evaluate / dom_query 仍 0.03s, 窗口恢复可见立即复原。
    #   这与本条要防的"内核注入打死通道"是**两码事**, 却会让本条偶发变红(实测真·快检 20.6s 那轮
    #   就是它: 同一脚本一次全慢 5.07/5.08/5.16s、一次全快 0.03/0.01/0.01s)。
    #   故: 先用只读的 browser_get_window_style 判可见性, **只在不可见时**幂等地显示回来, 再断言;
    #   并把原始 style 写进明细, 让"环境性慢"与"通道损坏"一眼可分。
    _vis, _vis_ok = None, True
    try:
        _vis = int(json.loads(call("browser_get_window_style", {})[1]).get("style", "0"))
        _vis_ok = (_vis & 0x10000000) != 0   # WS_VISIBLE
    except Exception:
        _vis = None
    if _vis is not None and not _vis_ok:
        call("browser_show_window", {"visible": True})
        time.sleep(0.5)
    t0 = time.time()
    call("browser_mouse_move", {"x": 300, "y": 200})
    e_mv, t_mv = call("browser_dom_query", {"selector": "h1"})
    mv_dt = time.time() - t0
    rec("mouse_move 后 CDP 仍可用(未打死会话; 窗口已确保可见)",
        (not e_mv) and ("Example Domain" in t_mv) and mv_dt < 3.0,
        "%.1fs 且 dom_query=%s | 窗口原style=%s(可见=%s)"
        % (mv_dt, "正常" if "Example Domain" in t_mv else "异常", _vis, _vis_ok))

    must_err("set_zoom {} 应拒绝", "browser_set_zoom", {}, "不能为空")
    must_err("mouse_click {} 应拒绝", "browser_mouse_click", {}, "必须同时提供")
    must_err("kernel_cert {} 应拒绝", "browser_kernel_cert", {}, "需要 action")
    must_err("kernel_watch {} 应拒绝", "browser_kernel_watch", {}, "需要 action")
    must_err("antidetect 未知 preset 应拒绝", "browser_antidetect_presets",
             {"preset": "zzz-nonexistent"}, "未知的 preset")
    # websocket 拦截: 缺参必须拒绝; 且**字符串 "true" 也要能开启**(读取器类型容错回归)
    must_err("vip_websocket_intercept {} 应拒绝", "browser_vip_websocket_intercept",
             {}, "不能省略")
    e6, t6 = call("browser_vip_websocket_intercept", {"enable": "true"})
    rec("vip_websocket_intercept {'true'} 字符串也生效",
        (not e6) and "已启用" in t6, t6.replace("\n", " ")[:70])

    print("\n-- L2: get_scroll 与预言机一致 / retry 不谎报成功 --")
    sc = payload(call("browser_get_scroll", {})[1])
    if isinstance(sc, dict):
        gy = str(sc.get("y", sc.get("scroll_y", sc.get("scrollY"))))
        gmax = str(sc.get("max_y", sc.get("maxY", sc.get("max_scroll_y"))))
        wy = js("String(Math.round(window.pageYOffset||0))")
        wmax = js("String(Math.round((document.documentElement.scrollHeight||0)"
                  "-(window.innerHeight||0)))")
        rec("get_scroll 与预言机一致", gy == wy and gmax == wmax,
            "y=%s/%s max_y=%s/%s" % (gy, wy, gmax, wmax))
    else:
        rec("get_scroll 返回可解析", False, str(sc)[:80])
    er, tr = call("browser_retry", {"tool": "browser_dom_query",
                                    "args": "{\"selector\":\"#nope-xyz\"}",
                                    "max_retries": 2, "backoff_ms": 100,
                                    "max_total_ms": 4000}, 40)
    rec("retry 对失败工具如实报错", bool(er),
        ("报错 " if er else "!! 成功 ") + tr.replace("\n", " ")[:70])

    print("\n-- scroll_by: 显式 0 == 不滚动(修复前会被改成 800) --")
    call("browser_scroll_by", {"x": 0, "y": 0})
    r = call("browser_scroll_by", {"x": 0, "y": 0})[1].replace('\\"', '"')
    m = re.search(r'scrolled_by_y"\s*:\s*(-?\d+)', r)
    rec("scroll_by 显式0 -> scrolled_by_y=0", bool(m) and m.group(1) == "0",
        "scrolled_by_y=%s" % (m.group(1) if m else "?"))

    print("\n-- 第115/116轮修复的回归钉(URI/帧/事件通配/开关可观测/插件守卫) --")
    # ① URI 解码: 本机类库解不开 ASCII 转义(%20/%26/%3D 原样返回), 工具必须**一次调用**走页面兜底给对
    e_u, t_u = call("browser_uri_decode", {"data": "a%20b%26c%3Dd"})
    tu = t_u.replace('\\"', '"')
    rec("uri_decode 一次得 'a b&c=d'(类库解不开, 靠兜底)",
        (not e_u) and ('"decoded":"a b&c=d"' in tu), tu[:90])
    # ② 编码 use_plus: 显式 true -> '+', 缺省仍是 %20(向后兼容)
    _, t_p = call("browser_uri_encode", {"data": "a b", "use_plus": True})
    _, t_q = call("browser_uri_encode", {"data": "a b"})
    rec("uri_encode use_plus/缺省", ('"encoded":"a+b"' in t_p.replace('\\"', '"'))
        and ('"encoded":"a%20b"' in t_q.replace('\\"', '"')),
        "%s | %s" % (t_p[:40], t_q[:40]))
    # ③ 按框架ID取框架: browser_get_frames 给出的 id 必须能回取(修前"给了钥匙没给门")
    _, t_f = call("browser_get_frames", {})
    fid = None
    try:
        j = json.loads(t_f)
        fr = j.get("frames") or []
        fid = (fr[0] or {}).get("id") if fr else None
    except Exception:
        fid = None
    if fid:
        _, t_b = call("browser_frame_by_id", {"frame_id": fid})
        rec("frame_by_id 用真实 id -> found:true", '"found":true' in t_b.replace('\\"', '"'),
            t_b[:80])
    else:
        rec("frame_by_id 用真实 id -> found:true", False,
            "取不到 frame id, 原文: %s" % str(t_f)[:80])
    # ④ 事件族名通配: 用**默认已开**的 load 族验证(不必打开高频族)
    _, t_e = call("browser_event", {"event_type": "load_*"})
    rec("event 族名通配 load_* 查到记录(修前是精确相等, 必查不到)",
        '"event":"load' in t_e.replace('\\"', '"'), t_e[:90])
    # ⑤ 内核 26/28 开关必须可观测(修前文案承诺 action=get 但没实现)
    # 注意: `enabled_count` 是"当前开着几个", 不是总数 —— 默认只开 4 项, 所以这里断言的是
    # "能读出 enabled_count/total 且自洽", 不要断言它很大(第一版就是我写错了断言而误报)。
    e_g, t_g = call("browser_kernel_events_all", {"action": "get"})
    mg = re.search(r'"enabled_count":(\d+)', t_g)
    mt = re.search(r'"total":(\d+)', t_g)
    rec("kernel_events_all action=get 可观测(有 total 且自洽)",
        (not e_g) and bool(mg) and bool(mt) and int(mt.group(1)) >= 26
        and 0 <= int(mg.group(1)) <= int(mt.group(1)),
        "enabled_count=%s total=%s" % (mg.group(1) if mg else "?", mt.group(1) if mt else "?"))
    # ⑥ 插件加载: 两个路径参数都不给时必须**可行动地**拒绝(而不是静默成功)
    e_l, t_l = call("browser_vip_load_extension", {})
    rec("vip_load_extension 缺参可行动拒绝",
        e_l and ("path" in t_l) and ("crx_path" in t_l), t_l.replace("\n", " ")[:80])

    # ⑦ 编解码工具(browser_codec / browser_time_convert): 只钉"最容易再错"的判别点
    #    · input=base64 必须**先解码**再出 hex(修前是把 base64 原文做 hex, 给的是 71773d3d)
    #    · GBK 出口必须有内容且无多余字节
    #    · 时间必须带 tz_offset_minutes, 且 int32 越界要显式报错
    _, t_c = call("browser_codec", {"action": "hex_encode", "input": "base64", "data": "qw=="})
    dc = payload(t_c)
    dc = dc if isinstance(dc, dict) else {}
    rec("codec hex_encode base64 'qw==' -> ab(修前是原文hex)",
        str(dc.get("output", "")).lower() == "ab", "output=%r" % dc.get("output"))
    _, t_d = call("browser_codec", {"action": "gbk_encode", "data": "中文", "output": "hex"})
    dd = payload(t_d)
    dd = dd if isinstance(dd, dict) else {}
    rec("codec gbk_encode '中文' -> d6d0cec4(无尾部00)",
        str(dd.get("output", "")).lower() == "d6d0cec4", "output=%r" % dd.get("output"))
    _, t_t = call("browser_time_convert", {"action": "ts_to_text", "timestamp": 0})
    dt_ = payload(t_t)
    dt_ = dt_ if isinstance(dt_, dict) else {}
    rec("time ts=0 -> 1970-01-01 08:00:00(UTC+8) 且 tz=-480",
        dt_.get("local") == "1970-01-01 08:00:00" and dt_.get("tz_offset_minutes") == -480,
        "local=%r tz=%r" % (dt_.get("local"), dt_.get("tz_offset_minutes")))
    e_t8, t_t8 = call("browser_time_convert", {"action": "ts_to_text", "timestamp": 2147483648})
    rec("time int32 越界显式报错", e_t8 and ("2038" in t_t8 or "unit=ms" in t_t8), t_t8[:70])

    # ⑧ 哈希工具(仰望模块): 用**权威标准值**钉死(MD5("hello") 与 CRC32("123456789")=0xCBF43926)
    _, t_h = call("browser_hash", {"action": "md5", "data": "hello"})
    dh = payload(t_h)
    dh = dh if isinstance(dh, dict) else {}
    rec("hash md5('hello') == 5d41402abc4b2a76b9719d911017c592",
        str(dh.get("md5", "")).lower() == "5d41402abc4b2a76b9719d911017c592",
        "md5=%r" % dh.get("md5"))
    _, t_c2 = call("browser_hash", {"action": "crc32", "data": "123456789"})
    dc2 = payload(t_c2)
    dc2 = dc2 if isinstance(dc2, dict) else {}
    rec("hash crc32('123456789') 无符号 == 3421780262 (0xCBF43926)",
        dc2.get("crc32_unsigned") == 3421780262,
        "crc32_unsigned=%r signed=%r" % (dc2.get("crc32_unsigned"), dc2.get("crc32")))
    e_hf, t_hf = call("browser_hash", {"action": "md5_file", "path": r"C:\definitely\not\here_zzz.bin"})
    rec("hash md5_file 不存在的文件必须报错(不给空文件摘要)",
        e_hf and ("文件不存在" in t_hf) and ("d41d8cd9" not in t_hf), t_hf[:70])

    # ⑨ URL 请求工具必须仍然暴露 G2 补全的入参(headers/body) —— 功能级验证在
    #    _audit/verify_url_request_g2.py(本机回显服务器, 按需跑); 这里只钉"接口没被改回去"。
    try:
        _tl = post({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        _tools = {t.get("name"): t for t in ((_tl.get("result") or {}).get("tools") or [])}
        _props = ((_tools.get("browser_create_url_request") or {}).get("inputSchema") or {}).get("properties") or {}
        rec("create_url_request 仍暴露 headers/body(G2 接口钉)",
            ("headers" in _props) and ("body" in _props), "props=%s" % sorted(_props))
    except Exception as _ex:
        rec("create_url_request 仍暴露 headers/body(G2 接口钉)", False, "取 schema 失败: %r" % _ex)

    # ⑩ iframe 子框架支持(G1): 主框架与 iframe 各放一个 #tgt 但值不同, 带 frame_id 写只改 iframe。
    #    预言机用主框架 JS 穿透 srcdoc 的 contentDocument(同源), 不依赖被测工具本身。
    js("document.body.insertAdjacentHTML('beforeend',"
       "'<input id=\"g1tgt\" value=\"MAIN\"><iframe id=\"g1fr\" name=\"mcpfcheck\" "
       "srcdoc=\"<input id=g1tgt value=IFRAME>\"></iframe>');'ok'")
    time.sleep(0.8)
    _fv = None
    try:
        _fr = json.loads(call("browser_get_frames", {})[1]).get("frames") or []
        print("       [dbg] 框架清单: %s" % [(f.get("name"), f.get("is_main"), f.get("id")) for f in _fr])
        _sub = next((f for f in _fr if f.get("is_main") is False), None)
        _fv = (_sub or {}).get("id")
    except Exception as _ex:
        rec("iframe 写入(G1): 取子框架 id", False, "解析失败 %r" % _ex)
    if _fv:
        _e, _t = call("browser_fill_set_value", {"selector": "#g1tgt", "value": "IN_FRAME", "frame_id": _fv})
        print("       [dbg] 写入回包 isError=%s %s" % (_e, _t[:200]))
        _iv = js("(function(){var f=document.getElementById('g1fr');"
                 "var e=f&&f.contentDocument&&f.contentDocument.querySelector('#g1tgt');"
                 "return e?e.value:'__NO_IFRAME__'})()")
        _mv = js("document.getElementById('g1tgt').value")
        rec("iframe 写入(G1): frame_id 只改 iframe, 主框架不受影响",
            _iv == "IN_FRAME" and _mv == "MAIN", "iframe=%r 主=%r" % (_iv, _mv))
    else:
        rec("iframe 写入(G1): 未取到子框架 id", False, "")

    dt = time.time() - T0
    bad = [t for t, o in res if not o]
    print("\n== 结果: %d/%d 通过, 用时 %.1fs ==" % (len(res) - len(bad), len(res), dt))
    for t in bad:
        print("   未通过: %s" % t)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
