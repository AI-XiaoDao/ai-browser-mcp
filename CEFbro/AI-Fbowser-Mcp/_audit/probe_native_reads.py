# -*- coding: utf-8 -*-
"""探测 3 个从未测试过的"原生API"读取工具 + browser_get_source。

动机: 已证实本内核下 填表框架 的 CEF JS 取值回调会返回空值, 被 类_MCP_JS异步回调
写成字面 "null" -> 工具静默返回 null(success=真)。同一根因家族里还有 3 个读取工具
从未被测过:
    browser_dom_rect      -> 填表框架.取元素坐标
    browser_dom_checked   -> 填表框架.取元素选择框
    browser_dom_selected  -> 填表框架.取元素选择项
    browser_get_source    -> 框架.取源码_异步

方法: 先注入可控表单元素, 再用 browser_execute_js(CDP, 已知可用) 取**预言机真值**,
再调被测工具比对。这样"预期值"来自页面事实而非我的记忆。

本文件已修掉三类**自身测试缺陷**(每一类都曾造成误判):
  1) 响应解包: 工具返回的 JSON 被转义嵌在 message 字段里, 直接取第一个 '{...}'
     拿到的是外层信封 -> 正确结果被误判为 FAIL。见 extract_obj。
  2) 元素残留: browser_navigate 到**同一 URL** 会被实现视为"已在目标地址"而跳过重载,
     上一轮注入的 #cb/#pp 仍在且 querySelector 命中旧元素 -> 基准错误。
     故本轮所有元素 ID 加唯一后缀, 并在开始时做基线自检。
  3) 测量污染: 前序重负载用例占用协议锁, 使后续工具偶发 15s 超时。
     故 get_source 用例带重试, 且单独复测已证 5/5 稳定 0.0s。
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

RUN = str(int(time.time()))[-6:]
CB, SEL, PP, HID = "#cb" + RUN, "#sel" + RUN, "#pp" + RUN, "#hid" + RUN
NOPE = "#nonexistent-xyz"

INJECT = ("document.body.insertAdjacentHTML('beforeend',"
          "'<div><input type=\"checkbox\" id=\"cb%s\" checked>"
          "<select id=\"sel%s\"><option>a</option><option selected>b</option></select>"
          "<p id=\"pp%s\">hello-mcp</p></div>');'injected'"
          % (RUN, RUN, RUN))

HIDE_JS = ("var d=document.createElement('div');d.id='hid%s';"
           "d.style.display='none';document.body.appendChild(d);'ok'" % RUN)

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
    """调用并自动跟随异步任务 (task_id -> mcp_result), 返回最终文本。"""
    is_err, txt = call(name, args, timeout)
    deadline = time.time() + 30
    seen, err = txt, is_err
    m = re.search(r"task_\d+_\d+_\d+", txt)
    while (not err) and m and time.time() < deadline:
        if "爬虫中" not in seen and "_waiting" not in seen and "已提交" not in seen \
                and "执行中" not in seen:
            break
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": m.group(0)}, 30)
        if not t2:
            break
        seen, err = t2, e2
    return err, seen


def oracle(expr):
    import json as _json
    def _unwrap(s):
        s = (s or "").strip()
        try:
            j = _json.loads(s)
            if isinstance(j, dict) and "message" in j:
                return str(j["message"])
        except Exception:
            pass
        return s.strip('"')
    """读页面真实状态(CDP, 已知可靠)。"""
    e, t = call("browser_execute_js", {"code": expr}, 30)
    if e:
        return "<ORACLE-ERR:%s>" % t[:60]
    return _unwrap(t)


def rec(tag, ok, detail):
    results.append((tag, ok, detail))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:160]))


def extract_obj(txt):
    """取出**最内层** JSON 对象。

    MCP 响应形如 {"id":"1","success":true,"message":"{\\"selector\\":...}"},
    工具返回的 JSON 被转义后嵌在 message 里; 只取第一个 '{...}' 会拿到外层信封。
    """
    def first_obj(s):
        t = (s or "").strip()
        try:
            v = json.loads(t)
            if isinstance(v, dict):
                return v
        except Exception:
            pass
        i = t.find("{")
        while i != -1:
            depth, j = 0, i
            while j < len(t):
                if t[j] == "{":
                    depth += 1
                elif t[j] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(t[i:j + 1])
                        except Exception:
                            break
                j += 1
            i = t.find("{", i + 1)
        return None

    node = first_obj(txt)
    for _ in range(5):
        if not isinstance(node, dict):
            break
        nxt = None
        for k in ("message", "data", "result_json"):
            v = node.get(k)
            if isinstance(v, str) and v.strip().startswith("{"):
                cand = first_obj(v)
                if isinstance(cand, dict):
                    nxt = cand
                    break
        if nxt is None:
            break
        node = nxt
    return node


def main():
    print("== 准备 (唯一ID后缀=%s) ==" % RUN)
    call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
    time.sleep(1.0)
    print("  注入: %s" % oracle(INJECT))
    time.sleep(0.4)

    print("\n== 预言机(CDP JS) ==")
    o_rect = oracle("(function(){var r=document.querySelector('%s')"
                    ".getBoundingClientRect();return JSON.stringify({x:Math.round(r.x),"
                    "y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)})})()" % PP)
    o_chk = oracle("String(document.querySelector('%s').checked)" % CB)
    o_sel = oracle("document.querySelector('%s').value" % SEL)
    print("  rect = %s   checked = %s   selected = %s" % (o_rect, o_chk, o_sel))
    try:
        oj = json.loads(o_rect)
    except Exception:
        rec("预言机可用", False, "rect 预言机不可解析: %s" % o_rect)
        return 1
    if o_chk != "true":
        rec("基线自检 checkbox 应为 true", False,
            "基线不干净(旧元素残留?) checked=%r -> 本轮读数不可信" % o_chk)
        return 2

    print("\n== browser_dom_rect ==")
    e, t = resolve("browser_dom_rect", {"selector": PP})
    obj = extract_obj(t)
    need = ("x", "y", "width", "height", "visible")
    missing = [k for k in need if not isinstance(obj, dict) or k not in obj]
    if e:
        rec("dom_rect (#pp)", False, "报错: " + t[:140])
    elif obj is None:
        rec("dom_rect (#pp)", False, "返回不是 JSON 对象: " + t[:140])
    elif missing:
        rec("dom_rect (#pp)", False, "缺字段 %s: %s"
            % (missing, json.dumps(obj, ensure_ascii=False)[:140]))
    elif abs(float(obj["x"]) - oj["x"]) > 2 or abs(float(obj["y"]) - oj["y"]) > 2:
        rec("dom_rect (#pp)", False, "坐标与预言机不符: 工具=%s,%s 预言机=%s,%s"
            % (obj["x"], obj["y"], oj["x"], oj["y"]))
    elif abs(float(obj["width"]) - oj["w"]) > 2 or abs(float(obj["height"]) - oj["h"]) > 2:
        rec("dom_rect (#pp)", False, "宽高与预言机不符: %sx%s vs %sx%s"
            % (obj["width"], obj["height"], oj["w"], oj["h"]))
    else:
        rec("dom_rect (#pp)", True, json.dumps(obj, ensure_ascii=False)[:150])

    oracle(HIDE_JS)
    time.sleep(0.3)
    e, t = resolve("browser_dom_rect", {"selector": HID})
    obj = extract_obj(t)
    if (not e) and obj and obj.get("visible") is False:
        rec("dom_rect (display:none 应 visible=false)", True,
            json.dumps(obj, ensure_ascii=False)[:140])
    else:
        rec("dom_rect (display:none 应 visible=false)", False,
            "非 false(可能恒 true): " + t[:140])

    e, t = resolve("browser_dom_rect", {"selector": NOPE})
    rec("dom_rect (元素不存在应报错)", bool(e and "元素不存在" in t), t[:140])

    print("\n== browser_dom_checked ==")
    e, t = resolve("browser_dom_checked", {"selector": CB})
    obj = extract_obj(t)
    if e:
        rec("dom_checked (应 checked=true)", False, "报错: " + t[:140])
    elif not obj or "checked" not in obj:
        rec("dom_checked (应 checked=true)", False, "无 checked 字段: " + t[:140])
    elif obj["checked"] is True:
        rec("dom_checked (应 checked=true)", True, json.dumps(obj, ensure_ascii=False)[:140])
    else:
        rec("dom_checked (应 checked=true)", False, "非 true: " + t[:140])

    oracle("document.querySelector('%s').checked=false" % CB)
    time.sleep(0.3)
    e, t = resolve("browser_dom_checked", {"selector": CB})
    obj = extract_obj(t)
    if (not e) and obj and obj.get("checked") is False:
        rec("dom_checked (取消勾选应 false)", True, json.dumps(obj, ensure_ascii=False)[:140])
    else:
        rec("dom_checked (取消勾选应 false)", False, "非 false: " + t[:140])

    e, t = resolve("browser_dom_checked", {"selector": PP})
    rec("dom_checked (非勾选元素应报错)", bool(e and "没有勾选状态" in t), t[:140])
    e, t = resolve("browser_dom_checked", {"selector": NOPE})
    rec("dom_checked (元素不存在应报错)", bool(e and "元素不存在" in t), t[:140])

    print("\n== browser_dom_selected ==")
    e, t = resolve("browser_dom_selected", {"selector": SEL})
    obj = extract_obj(t)
    if e:
        rec("dom_selected", False, "报错: " + t[:140])
    elif not obj or "value" not in obj:
        rec("dom_selected", False, "无 value 字段(旧格式裸索引?): " + t[:140])
    elif obj.get("value") != o_sel:
        rec("dom_selected", False, "value=%r 与预言机 %r 不符" % (obj.get("value"), o_sel))
    elif obj.get("index") != 1:
        rec("dom_selected", False, "index=%r 应为 1" % obj.get("index"))
    else:
        rec("dom_selected", True, json.dumps(obj, ensure_ascii=False)[:150])

    e, t = resolve("browser_dom_selected", {"selector": PP})
    rec("dom_selected (非select应报错)", bool(e and "不是 select" in t), t[:140])
    e, t = resolve("browser_dom_selected", {"selector": NOPE})
    rec("dom_selected (元素不存在应报错)", bool(e and "元素不存在" in t), t[:140])

    print("\n== browser_get_source (带重试; 单独复测已知 5/5 稳定 0.0s) ==")
    ok = False
    detail = ""
    for attempt in range(2):
        e, t = resolve("browser_get_source", {"max_chars": 200000, "sync_wait": True}, 60)
        if (not e) and "Example Domain" in t:
            ok, detail = True, "含 Example Domain, 长度=%d (第%d次)" % (len(t), attempt + 1)
            break
        detail = "第%d次失败: %s" % (attempt + 1, t[:110])
        time.sleep(2)
    rec("get_source 同步(最多3次)", ok, detail)

    print("\n== 汇总 ==")
    bad = [x for x in results if not x[1]]
    print("  通过 %d / %d" % (len(results) - len(bad), len(results)))
    for tag, _, d in bad:
        print("  未通过: %s -> %s" % (tag, str(d)[:130]))
    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "_probe_native_reads.json"), "w", encoding="utf-8") as f:
        json.dump([{"tag": t, "ok": o, "detail": d} for t, o, d in results],
                  f, ensure_ascii=False, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
