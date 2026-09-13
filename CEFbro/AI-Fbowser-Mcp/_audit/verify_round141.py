# -*- coding: utf-8 -*-
r"""第141轮验收: 新增三个工具(browser_json / browser_data_uri / browser_by_index)真机验证。

判据(每条都有独立预言机, 不只是"回包看着像"):
  ① tools/list: 三者都注册且必填参数声明正确;
  ② `browser_json validate`: 合法 JSON → valid=true + value_type=dict; 非法 → valid=false 且**仍是 success**(校验结论);
  ③ `allow_trailing_commas` 判别差: `{"a":1,}` 严格模式非法 / 宽容模式合法(证明选项真的透传);
  ④ `normalize`: 回包 normalized 再用 browser_json 校验一次(往返稳定), 且结构等价(键值一致);
  ⑤ `from_base64`: 用 base64 文本走字节入口, 结果与文本入口**一致**;
  ⑥ 非法输入走 normalize → **可行动失败**(不是成功);
  ⑦ `browser_data_uri`: 前缀/mime 正确, 且用浏览器 `fetch` 真读它(页面侧预言机!);
  ⑧ `browser_by_index {index:0}` 的 browser_id 与 browser_list 里的主浏览器一致; 越界 → 明确失败;
  ⑨ 收尾健康。

用法: py -3 _audit\verify_round141.py
"""
import base64 as b64
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def payload(txt):
    """data 可能是字符串(内嵌 JSON)或对象 —— 两种都要认(上一轮已因此栽过一次)。"""
    try:
        o = json.loads(txt)
    except Exception:
        return {}
    d = o.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return o if isinstance(o, dict) else {}


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


print('== ① tools/list ==')
try:
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode(),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    tools = ((o.get("result") or {}).get("tools") or [])
    names = {t.get("name") for t in tools}

    def props(n):
        t = [x for x in tools if x.get("name") == n]
        return (((t[0].get("inputSchema") or {}).get("properties") or {}) if t else {}), \
               (((t[0].get("inputSchema") or {}).get("required") or []) if t else [])

    rec("工具数 327 且三个新工具都在", len(tools) == 327 and {"browser_json", "browser_data_uri", "browser_by_index"} <= names,
        "tools=%d" % len(tools))
    p, req = props("browser_json")
    rec("browser_json schema(action/data/allow_trailing_commas; data 必填)",
        set(p) >= {"action", "data", "allow_trailing_commas"} and "data" in req, "props=%s req=%s" % (sorted(p), req))
    p2, req2 = props("browser_data_uri")
    rec("browser_data_uri schema(mime/data; data 必填)", set(p2) >= {"mime", "data"} and "data" in req2, sorted(p2))
    p3, req3 = props("browser_by_index")
    rec("browser_by_index schema(index 必填)", set(p3) >= {"index"} and "index" in req3, sorted(p3))
except Exception as ex:
    rec("tools/list 读取", False, repr(ex))

print('\n== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r141=%d" % int(time.time())})

print('\n== ② validate: 合法/非法都要给**确定结论** ==')
GOOD = '{"a":[1,2],"b":"中文","c":true,"d":null}'
e, t, d = call("browser_json", {"data": GOOD})
p = payload(t)
rec("合法 JSON → valid=true", (not e) and p.get("valid") is True, "%.2fs %s" % (d, json.dumps(p, ensure_ascii=False)[:90]))
rec("value_type_name=dict(type=%s)" % p.get("value_type"), p.get("value_type_name") == "dict", "")
BAD = '{"a":1,}'
e2, t2, d2 = call("browser_json", {"data": BAD})
p2 = payload(t2)
rec("尾逗号 JSON → valid=false 且回包仍是 success(校验结论)", (not e2) and p2.get("valid") is False, t2[:90])
e3, t3, d3 = call("browser_json", {"data": BAD, "allow_trailing_commas": True})
p3 = payload(t3)
rec("allow_trailing_commas=true → 同一串变合法(**选项真的透传**)", (not e3) and p3.get("valid") is True, t3[:90])

print('\n== ③ normalize 往返稳定 + 结构等价 ==')
e4, t4, d4 = call("browser_json", {"action": "normalize", "data": GOOD})
p4 = payload(t4)
norm = p4.get("normalized") or ""
rec("normalize 成功且回包有 normalized", (not e4) and norm != "", "%.2fs len=%s" % (d4, len(norm)))
if norm:
    try:
        rec("normalized 与原文结构等价", json.loads(norm) == json.loads(GOOD), norm[:80])
    except Exception as ex:
        rec("normalized 与原文结构等价", False, "解析失败 %r" % (ex,))
    e5, t5, _ = call("browser_json", {"data": norm})
    rec("再把 normalized 喂回 validate 仍合法(往返稳定)", payload(t5).get("valid") is True, t5[:70])

print('\n== ④ from_base64 与文本入口结果一致 ==')
b64txt = b64.b64encode(GOOD.encode("utf-8")).decode("ascii")
e6, t6, _ = call("browser_json", {"action": "from_base64", "data": b64txt})
p6 = payload(t6)
rec("from_base64 成功且 input=base64", (not e6) and p6.get("input") == "base64", json.dumps(p6, ensure_ascii=False)[:90])
rec("与文本入口结构等价", json.loads(p6.get("normalized") or "null") == json.loads(GOOD), (p6.get("normalized") or "")[:70])

print('\n== ⑤ 非法输入走 normalize 必须**可行动失败** ==')
e7, t7, _ = call("browser_json", {"action": "normalize", "data": "not json at all"})
rec("normalize 非法输入 → 失败且给出下一步", e7 and ("validate" in t7 or "allow_trailing_commas" in t7), t7[:110])

print('\n== ⑥ data URI: 前缀正确 + **页面侧真能读** + 载荷可独立解码 ==')
DU_TEXT = "hello 中文"
e8, t8, d8 = call("browser_data_uri", {"mime": "text/plain", "data": DU_TEXT})
p8 = payload(t8)
uri = p8.get("data_uri") or ""
rec("回包有 data_uri 且 mime 正确", (not e8) and uri.startswith("data:text/plain"), "%.2fs %s" % (d8, uri[:60]))
# 预言机 A(与浏览器无关): 自己解出 base64 载荷, 必须与输入逐字相同
try:
    head, b64part = uri.split(",", 1)
    rec("URI 载荷可独立 base64 解码且与输入一致", b64.b64decode(b64part).decode("utf-8") == DU_TEXT,
        "%s -> %r" % (head, b64.b64decode(b64part).decode("utf-8")))
except Exception as ex:
    rec("URI 载荷可独立 base64 解码且与输入一致", False, repr(ex))
# 预言机 B(页面侧): 页面 fetch 该 data URI, 把长度写进 document.title(用非 CDP 的 get_title 读回;
# 注意: 工具返回 Promise 对象本身不算结果 —— 上一版就这么误判过)
want = "DU:%d" % len(DU_TEXT)
js = ("fetch(%s).then(function(r){return r.text()}).then(function(x){document.title='DU:'+x.length})"
      ".catch(function(e){document.title='DUERR'})" % json.dumps(uri))
call("browser_execute_js", {"code": js, "max_ms": 15000})
time.sleep(0.8)
e9, t9, _ = call("browser_get_title", {})
rec("页面 fetch(data URI) 读到 %s(标题预言机)" % want, want in t9, t9[:80])

print('\n== ⑦ by_index: 与 browser_list 交叉核对 + 越界明确失败 ==')
e10, t10, _ = call("browser_by_index", {"index": 0})
p10 = payload(t10)
e11, t11, _ = call("browser_list", {})
p11 = payload(t11)
ids = []
for it in (p11.get("browsers") or p11.get("list") or []):
    if isinstance(it, dict) and isinstance(it.get("id"), int):
        ids.append(it["id"])
rec("by_index(0) 返回 browser_id", (not e10) and isinstance(p10.get("browser_id"), int), json.dumps(p10, ensure_ascii=False)[:90])
rec("该 id 在 browser_list 里存在", (not e10) and (p10.get("browser_id") in ids or not ids), "id=%s list=%s" % (p10.get("browser_id"), ids))
rec("回包附带 id_list_in_order(便于交叉核对)", isinstance(p10.get("id_list_in_order"), str), str(p10.get("id_list_in_order"))[:60])
e12, t12, _ = call("browser_by_index", {"index": 99})
rec("越界 index 明确失败且给替代", e12 and ("browser_list" in t12), t12[:110])

print('\n== ⑧ 收尾健康 ==')
e13, t13, d13 = call("browser_execute_js", {"code": "1+1"})
rec("execute_js 正常", (not e13) and d13 < 1.0, "%.2fs" % d13)
e14, t14, _ = call("browser_status", {})
rec("browser_status 可用", (not e14), "")

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
