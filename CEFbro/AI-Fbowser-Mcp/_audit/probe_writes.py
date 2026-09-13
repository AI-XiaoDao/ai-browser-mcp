# -*- coding: utf-8 -*-
"""L4 写操作层: browser_fill_* / browser_dom_* 是否**真的改变了页面状态**。

背景(静态发现): 工具描述自己写着 ——
  browser_fill_set_value: "selector 未命中时仍返回成功, 建议先用 fill_exists 校验"
  browser_fill_click:     "selector 未命中时仍返回成功"
"返回成功但什么都没做"对 AI 代理是最危险的失败模式: 它会以为已点击/已填写并继续推进。

方法: 每个写操作都配一个**预言机**(browser_execute_js 读页面真实状态),
正例验"确实生效", 反例验"未命中时必须报错而不是报成功"。
"""
import io
import json
import os
import re
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
URL = "https://example.com/"

SETUP = """
document.body.insertAdjacentHTML('beforeend',
 '<div id="wrap"><input id="inp" type="text"><button id="btn">go</button>' +
 '<select id="sel"><option value="a">a</option>' +
 '<option value="b" selected>b</option></select><div id="box">box</div></div>');
window.__clicks = 0;
document.querySelector('#btn').addEventListener('click', function(){ window.__clicks++; });
'injected'
"""

results = []


def post(payload, timeout=45):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def call(name, args, timeout=45):
    try:
        resp = post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": name, "arguments": args}}, timeout)
    except Exception as ex:
        return True, "EXC: %s" % ex
    res = resp.get("result") or {}
    txt = ""
    for item in res.get("content") or []:
        if item.get("type") == "text":
            txt += item.get("text") or ""
    if not txt:
        txt = json.dumps(res, ensure_ascii=False)
    return bool(res.get("isError")), txt


def resolve(name, args, timeout=45):
    is_err, txt = call(name, args, timeout)
    deadline = time.time() + 30
    seen, err = txt, is_err
    m = re.search(r"task_\d+_\d+_\d+", txt)
    while (not err) and m and time.time() < deadline:
        if "已提交" not in seen and "_waiting" not in seen:
            break
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": m.group(0)}, 30)
        if not t2:
            break
        seen, err = t2, e2
    return err, seen


def oracle(expr, tries=2):
    """读页面真实状态(CDP, 已知可靠)。

    带重试: 预言机自身也会 5s 超时(尤其紧跟重负载用例之后), 不重试就会把
    "预言机超时"误判成"工具成功但页面状态未变" —— 本套件曾因此误报 1 例。

    另外必须**解包 message 信封**: browser_execute_js 已改为 CDP 优先, 返回
    {"id":..,"success":true,"message":"<值>"}(与兄弟工具一致); 不解包就会把整串信封当值。
    """
    import json as _json

    def unwrap(s):
        s = (s or "").strip()
        try:
            j = _json.loads(s)
            if isinstance(j, dict) and "message" in j:
                return str(j["message"])
        except Exception:
            pass
        return s.strip('"')

    last = ""
    for _ in range(tries):
        e, t = call("browser_execute_js", {"code": expr}, 30)
        if not e:
            v = unwrap(t)
            # 只排除"真的没读到"的情况: 空字符串 / null / 超时文案。
            # 注意**不能**用 startswith("<") 当判据 —— 合法的 HTML 值(如 <b>hi</b>)也以 < 开头。
            if v != "" and v not in ("null", "undefined") and "操作超时" not in v:
                return v
            last = v
        else:
            last = t[:60]
        time.sleep(0.6)
    return "<ORACLE-FAIL:%s>" % last


def rec(tag, ok, detail):
    results.append((tag, ok, detail))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:150]))


def positive(tag, tool, args, oracle_expr, want):
    """正例: 操作生效 + 预言机读到期望值。

    oracle_expr 可以是:
      · 字符串      -> 用 browser_execute_js 求值(原生 JS 回调通道)
      · (工具名, 参数字典) -> 用该工具作为预言机(优先用于 DOM 状态读取)
    为什么要支持第二种: 实测**原生 JS 回调通道会在会话中途失效**(browser_execute_js 连 1+1 都 5s 超时),
    而同期 CDP 通道仍然正常。此时用 browser_execute_js 当预言机会把"预言机坏了"误报成"工具没生效"。
    DOM 状态优先用 CDP 优先的工具读取(browser_dom_inner_html / browser_dom_query), 更稳。
    """
    e, t = resolve(tool, args)
    if isinstance(oracle_expr, tuple):
        oe, ot = resolve(oracle_expr[0], oracle_expr[1])
        if oe:
            got = "<ORACLE-FAIL:%s>" % ot[:60]
        else:
            # 工具返回的是信封 {"id":..,"success":true,"message":"<值>"}, 需要取出 message
            # (上一版直接用原始信封当预言机, 于是 "<b>hi</b>" 被比成整个 JSON 串而误报)
            got = ot.strip()
            try:
                j = json.loads(got)
                if isinstance(j, dict) and "message" in j:
                    got = str(j["message"])
            except Exception:
                got = got.strip('"')
    else:
        got = oracle(oracle_expr)
    if e:
        rec(tag, False, "工具报错(预期成功): " + t[:110])
    elif got != want:
        rec(tag, False, "工具称成功但页面状态未变: 预言机=%r 期望=%r | resp=%s"
            % (got, want, t[:80]))
    else:
        rec(tag, True, "生效, 预言机=%r" % (got,))


def negative(tag, tool, args):
    """反例: selector 未命中时必须报错, 而不是报成功。"""
    e, t = resolve(tool, args)
    if e:
        rec(tag, True, "如实报错: " + t[:110])
    elif "not found" in t.lower() or "不存在" in t or "未命中" in t:
        rec(tag, True, "如实报未命中: " + t[:110])
    else:
        rec(tag, False, "!! 静默假成功(未命中却报成功): " + t[:130])


def main():
    print("== 准备 ==")
    call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
    time.sleep(1.0)
    print("  " + oracle(SETUP))
    time.sleep(0.4)
    print("  基线: inp=%r clicks=%r sel=%r"
          % (oracle("document.querySelector('#inp').value"),
             oracle("String(window.__clicks)"),
             oracle("String(document.querySelector('#sel').selectedIndex)")))

    print("\n== 正例: 写操作必须真的改变页面状态 ==")
    positive("fill_set_value (#inp)", "browser_fill_set_value",
             {"selector": "#inp", "value": "hello-mcp"},
             "document.querySelector('#inp').value", "hello-mcp")
    positive("fill_click (#btn -> clicks=1)", "browser_fill_click",
             {"selector": "#btn"}, "String(window.__clicks)", "1")
    positive("fill_focus (#inp)", "browser_fill_focus",
             {"selector": "#inp"}, "document.activeElement.id", "inp")
    positive("fill_attr_set (#box data-x=42)", "browser_fill_attr_set",
             {"selector": "#box", "attribute": "data-x", "value": "42"},
             "document.querySelector('#box').getAttribute('data-x')", "42")
    positive("dom_set_value (#inp)", "browser_dom_set_value",
             {"selector": "#inp", "value": "dom-val"},
             "document.querySelector('#inp').value", "dom-val")
    positive("dom_set_html (#box)", "browser_dom_set_html",
             {"selector": "#box", "html": "<b>hi</b>"},
             ("browser_dom_inner_html", {"selector": "#box"}), "<b>hi</b>")
    positive("dom_click (#btn -> clicks=2)", "browser_dom_click",
             {"selector": "#btn"}, "String(window.__clicks)", "2")
    positive("dom_select (#sel index=0)", "browser_dom_select",
             {"selector": "#sel", "index": 0},
             "String(document.querySelector('#sel').selectedIndex)", "0")

    print("\n== 反例: selector 未命中时**不得**报成功 ==")
    negative("fill_set_value 未命中", "browser_fill_set_value",
             {"selector": "#nonexistent-xyz", "value": "x"})
    negative("fill_click 未命中", "browser_fill_click",
             {"selector": "#nonexistent-xyz"})
    negative("fill_focus 未命中", "browser_fill_focus",
             {"selector": "#nonexistent-xyz"})
    negative("fill_attr_set 未命中", "browser_fill_attr_set",
             {"selector": "#nonexistent-xyz", "attribute": "data-x", "value": "1"})
    negative("fill_trigger 未命中", "browser_fill_trigger",
             {"selector": "#nonexistent-xyz", "event": "click"})
    negative("fill_scroll 未命中", "browser_fill_scroll",
             {"selector": "#nonexistent-xyz"})
    negative("fill_select 未命中", "browser_fill_select",
             {"selector": "#nonexistent-xyz", "value": "a"})
    negative("dom_set_value 未命中", "browser_dom_set_value",
             {"selector": "#nonexistent-xyz", "value": "x"})
    negative("dom_set_html 未命中", "browser_dom_set_html",
             {"selector": "#nonexistent-xyz", "html": "<i>x</i>"})
    negative("dom_click 未命中", "browser_dom_click",
             {"selector": "#nonexistent-xyz"})
    negative("dom_select 未命中", "browser_dom_select",
             {"selector": "#nonexistent-xyz", "index": 0})

    print("\n== 汇总 ==")
    bad = [x for x in results if not x[1]]
    print("  通过 %d / %d" % (len(results) - len(bad), len(results)))
    for tag, _, d in bad:
        print("  未通过: %s -> %s" % (tag, str(d)[:130]))
    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "_probe_writes.json"), "w", encoding="utf-8") as f:
        json.dump([{"tag": t, "ok": o, "detail": d} for t, o, d in results],
                  f, ensure_ascii=False, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
