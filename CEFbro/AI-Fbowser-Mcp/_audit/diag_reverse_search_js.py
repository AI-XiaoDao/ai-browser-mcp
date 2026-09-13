# -*- coding: utf-8 -*-
"""定位 browser_reverse_search 的注入脚本为何抛 JS 异常。

背景(实测): 该工具稳定返回 `脚本搜索错误: JS异常:Uncaught` —— 只有 "Uncaught", 没有任何原因,
不可行动。两个可疑点:

 ① 注入 JS 里 `t.split('\\r\n')` (见 MCP_Server_Core.wsv 的 srCode)。
    该项目字符串转义惯例(有据): `\n` 在 .wsv 字面量里就是**真实换行**
    (例: MCP_Server.wsv 的 Prometheus 输出 "...已注册(1/0)\n" 依赖它产生真换行);
    `\\` 是**一个反斜杠** (例: 子文本替换 (安全词, "\\", "\\\\"))。
    于是 `'\\r\n'` 生成给 JS 的是: `'` + 反斜杠 + `r` + **真实换行** + `'`
    -> 单引号字符串里出现裸换行 = **未终止的字符串字面量 = 解析期 SyntaxError**。

 ② 异常格式化器 (MCP_Server.wsv 的 CDP执行JS并等待) 只读 exceptionDetails.text,
    而 CDP 的 text 字段固定就是 "Uncaught"; 真正原因在 exceptionDetails.exception.description。
    -> 所以任何走这条路的 JS 异常都只报 "Uncaught", 不可行动(横切可诊断性缺陷)。

本脚本用**判别性 A/B** 证实 ① 并直接读出 CDP 原始异常对象(绕过格式化器, 因此能看到真原因):
  臂A: split('\\r<LF>')  即现状(源码里的 '\\r\n')
  臂B: split('\\n')      即修法(源码里写 '\\n' -> JS 得到换行转义 "\n")
判据: 臂A 必须报 SyntaxError 类异常(证实 ①), 臂B 必须正常返回 JSON(证实修法可用)。
若臂A 不报错, 则 ① 被证伪, 需另找原因 —— 本脚本会如实打印, 不掩盖。
"""
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"

# 注入脚本模板, {} 处替换 split 的分隔符片段。
# 为忠实复现, 直接照抄 MCP_Server_Core.wsv 里 srCode 的结构(去掉 query/url 过滤的差异)。
TMPL = ("(function(){var q='sign';var ss=document.querySelectorAll('script');var R=[];"
        "ss.forEach(function(s,i){var src=s.src||'(inline)';var t=s.textContent||'';"
        "var lines=t.split({SPLIT});lines.forEach(function(l,li){if(l.indexOf(q)!==-1){"
        "R.push({script_index:i,src:src.substring(0,200),line:li+1,"
        "snippet:l.trim().substring(0,300)})}})});"
        "return JSON.stringify({query:q,found:R.length,results:R.slice(0,50)})})()")

# Python 里 "\\r\n" = 反斜杠 + r + 真实换行 -> 正是 .wsv 源码 '\\r\n' 生成给 JS 的字节
BROKEN = "'\\r\n'"
# Python 里 "\\n" = 反斜杠 + n -> JS 源码里的换行转义, 合法
FIXED = "'\\n'"


def call(name, args, timeout=30):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(BASE + "/mcp",
                                 data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def cdp_eval(expr):
    """经 browser_cdp_call 直接求值, 拿**原始** CDP 响应(不经项目的异常格式化器)。"""
    params = json.dumps({"expression": expr, "returnByValue": True}, ensure_ascii=False)
    resp = call("browser_cdp_call", {"method": "Runtime.evaluate", "params": params})
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


def show(tag, expr, split_desc):
    print("\n===== %s (split 片段: %s) =====" % (tag, split_desc))
    print("  JS 中该处的字节: %r" % split_desc)
    e, txt = cdp_eval(expr)
    print("  isError=%s" % e)
    print("  原始返回: %s" % txt[:700])
    # 原始 CDP 里应当能看到 exceptionDetails.exception.description
    has_syntax = ("SyntaxError" in txt) or ("Invalid or unexpected token" in txt) \
        or ("Unterminated" in txt)
    print("  含解析期错误标记: %s" % has_syntax)
    # 取 CDP result.value (Runtime.evaluate 在 returnByValue 下把 JS 返回值放在这里)
    val = None
    try:
        val = (json.loads(txt).get("result") or {}).get("value")
    except Exception:
        pass
    return has_syntax, txt, val


def main():
    # ★ 测量环境必须先证明干净。
    # 第一版没有这一步, 结果臂B 报 `RangeError: Maximum call stack size exceeded`,
    # 栈帧形如 `at __obj.<computed> (<anonymous>:1:544)` 反复自递归 —— 那不是本工具的问题,
    # 而是**同一批台账里先跑过的 browser_reverse_instrument 在页面上装了透明插装**
    # (包装 Function.prototype.apply/call、Array.prototype.push 等), 之后的 JS 都会被它拖崩。
    # 换句话说: 那一轮臂B 的结论是在**被污染的页面**上得出的, 不可信。
    call("browser_navigate", {"url": "https://example.com/?revsearch=clean",
                              "wait_for_load": True}, 45)
    e, probe = cdp_eval("JSON.stringify({instr:typeof window.__mcp_instrument_results,"
                        "hooks:typeof window.__mcp_initiator_log,"
                        "log:typeof window.__mcp_interpreter_logs,"
                        "scripts:document.querySelectorAll('script').length})")
    print("== 页面清洁度探针 ==")
    print("  %s" % probe[:300])
    # 只要三个插装标记里任一为 object(已定义), 就说明上轮插装还活着
    dirty = ('\"instr\\\":\\\"object' in probe or 'instr\\\":\\\"object' in probe
             or 'hooks\\\":\\\"object' in probe or 'log\\\":\\\"object' in probe)
    if dirty:
        print("  !! 页面仍带插装残留 -> 本脚本结论不可信, 先查为何重载没清掉")
        return 3
    print("  干净(三个插装标记均未定义)")

    a_syntax, a_txt, a_val = show("臂A: 现状(未终止字符串?)",
                                  TMPL.replace("{SPLIT}", BROKEN), BROKEN)
    b_syntax, b_txt, b_val = show("臂B: 修法(合法换行转义)",
                                  TMPL.replace("{SPLIT}", FIXED), FIXED)

    print("\n===== 判据 =====")
    ok = True
    if a_syntax:
        print("  [PASS] 臂A 证实: 现状注入脚本是解析期错误(未终止字符串) -> 这就是 browser_reverse_search 必失败的原因")
    else:
        print("  [FAIL] 臂A 未复现解析期错误 -> 假设①被证伪, 需要另找原因(不要照本脚本的结论改代码)")
        ok = False
    # 臂B 的判据: CDP result.value 应是一个**能解析出 found 键**的 JSON 字符串。
    # (第一版直接在外层信封里找 '"found"' 是错的 —— 该值嵌在 value 里且被 JSON 转义成 \"found\",
    #  于是修好了也报 FAIL。这正是"测试脚本自身缺陷会造成假失败"的老问题。)
    b_ok = False
    if isinstance(b_val, str):
        try:
            b_ok = "found" in json.loads(b_val)
        except Exception:
            b_ok = False
    if (not b_syntax) and b_ok:
        print("  [PASS] 臂B 证实: 换成 '\\n' 后脚本正常返回可解析 JSON(value=%s) -> 修法可用" % str(b_val)[:90])
    else:
        print("  [FAIL] 臂B 仍未正常返回 -> 修法不足 (value=%r, 解析期错误=%s)" % (b_val, b_syntax))
        ok = False

    # 额外: 证明格式化器丢掉了原因 —— 从臂A的原始响应里提取 CDP 真正给出的原因字段
    try:
        obj = json.loads(a_txt)
        ed = obj.get("exceptionDetails") or {}
        print("\n  CDP 原始异常字段(证明格式化器该读哪个):")
        print("    exceptionDetails.text                = %r   <- 现状只读这个, 所以永远只有 'Uncaught'" % ed.get("text"))
        print("    exceptionDetails.exception.description = %r" % ((ed.get("exception") or {}).get("description")))
        print("    exceptionDetails.exception.value       = %r" % ((ed.get("exception") or {}).get("value")))
    except Exception as ex:
        print("\n  (无法解析臂A原始响应为 JSON: %s)" % ex)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
