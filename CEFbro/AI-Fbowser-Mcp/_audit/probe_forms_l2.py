# -*- coding: utf-8 -*-
"""L2 语义覆盖（目标 ≤15 秒）：表单工作流 + highlight clear 路径。

为什么要测这两块：
  · `browser_get_forms` + `browser_fill_form` 是 AI 填表的**主力组合**，此前只验证过
    "全字段失败会报错"，没有验证过**有表单时字段是否被正确识别、能否真的填进去**。
  · `browser_highlight` 的 `clear` 路径此前从未测过（只测了 duration_ms=0）。

预言机: 用 CDP 优先的读取工具 / browser_execute_js 读页面真值。
"""
import json
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
RUN = str(int(time.time()))[-6:]
F1, F2 = "fn" + RUN, "fe" + RUN
res = []


def call(name, args, timeout=30):
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


ENVELOPE_ONLY = {"id", "jsonrpc", "success", "data", "message", "result", "error",
                 "result_json", "poll_hint", "_hint", "needs_reload", "ok"}


def payload(t):
    """从任意深度的响应里取出**最有信息量的那个 JSON 对象**。

    本会话在此坑栽了四次(message / data / result_json / forms_json 各不相同,
    且 browser_get_forms 是 `data -> forms_json` **两层嵌套**; 之前"返回第一个能解析的
    dict"会停在中转层 `data` 上, 于是把 count=1 读成 count=0)。
    故不硬编码键名, 改为:
      1) 递归收集所有可达 dict(顺着 dict 值与"字符串形式的 JSON");
      2) 打分 = 非信封键数量 + 非空数组字段数量;
      3) 取分最高者。
    信封键(id/jsonrpc/success/data/message/result/error…)不计分, 不会被误当载荷。
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

    s = (t or "").strip()
    try:
        root = json.loads(s)
    except Exception:
        return s
    cands = []
    collect(root, cands)
    best = root if isinstance(root, dict) else s
    best_score = -1
    for d in cands:
        score = len([k for k in d.keys() if k not in ENVELOPE_ONLY])
        score += sum(1 for k, v in d.items()
                     if isinstance(v, list) and v and k not in ENVELOPE_ONLY)
        if score > best_score:
            best, best_score = d, score
    return best


def js(code):
    e, t = call("browser_execute_js", {"code": code})
    if e:
        return None
    s = t.strip()
    try:
        j = json.loads(s)
        if isinstance(j, dict) and "message" in j:
            return str(j["message"])
    except Exception:
        pass
    return s.strip('"')


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:100]))


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s" % (h.get("tool_count"), h.get("cdp_ready")))
except Exception as ex:
    print("  !! 服务未就绪(%s) -> 作废" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?form=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.5)
# 注入一个真实表单(带 name/type/required), 供 get_forms / fill_form 使用
js("document.body.insertAdjacentHTML('beforeend',"
   "'<form id=\"tform\"><input id=\"%s\" name=\"username\" type=\"text\">"
   "<input id=\"%s\" name=\"email\" type=\"email\">"
   "<button type=\"submit\">go</button></form>');'ok'" % (F1, F2))
time.sleep(0.3)

print("\n== 1) browser_get_forms 应识别到该表单与字段 ==")
e, t = call("browser_get_forms", {})
p = payload(t)
forms = (p or {}).get("forms") if isinstance(p, dict) else None
if forms is None:
    # 有些实现把 forms_json 包成字符串
    raw = json.dumps(p, ensure_ascii=False)
    rec("get_forms 返回可解析", False, raw[:110])
    forms = []
rec("get_forms 识别到 1 个表单", len(forms) == 1, "count=%s" % len(forms))
fields = []
if forms:
    f0 = forms[0]
    fields = f0.get("fields") or f0.get("inputs") or []
    rec("表单里识别到 2 个输入框", len(fields) >= 2,
        "fields=%d 明细=%s" % (len(fields), json.dumps(fields, ensure_ascii=False)[:90]))
print("     原始: %s" % json.dumps(p, ensure_ascii=False)[:220])

print("\n== 2) browser_fill_form 端到端填进去 ==")
fields_arg = json.dumps([{"selector": "#" + F1, "value": "alice"},
                         {"selector": "#" + F2, "value": "a@b.com"}],
                        ensure_ascii=False)
e2, t2 = call("browser_fill_form", {"fields": fields_arg}, 40)
p2 = payload(t2)
print("     工具回复: err=%s %s" % (e2, json.dumps(p2, ensure_ascii=False)[:150]))
if isinstance(p2, dict):
    rec("fill_form filled=2 failed=0",
        p2.get("filled") == 2 and p2.get("failed") == 0,
        "filled=%s failed=%s success=%s" % (p2.get("filled"), p2.get("failed"), p2.get("success")))
else:
    rec("fill_form 返回可解析", False, str(p2)[:90])
v1 = js("document.getElementById('%s').value" % F1)
v2 = js("document.getElementById('%s').value" % F2)
rec("预言机确认两个框真的被填", v1 == "alice" and v2 == "a@b.com", "%r / %r" % (v1, v2))

print("\n== 3) browser_highlight 显示 + clear 应还原样式 ==")
before = js("document.getElementById('%s').style.outline" % F1)
e3, t3 = call("browser_highlight", {"selector": "#" + F1, "duration_ms": 0})
mid = js("document.getElementById('%s').style.outline" % F1)
rec("highlight show 生效(有 outline)", bool(mid) and "dashed" in (mid or ""),
    "before=%r mid=%r" % (before, mid))
e4, t4 = call("browser_highlight", {"action": "clear"})
after = js("document.getElementById('%s').style.outline" % F1)
rec("highlight clear 还原样式", after == "" or after == before,
    "after=%r (期望空/与 before 相同)" % after)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
