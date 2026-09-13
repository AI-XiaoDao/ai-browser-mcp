# -*- coding: utf-8 -*-
"""导出 MCP tools/list 到 _audit/_tools_list.json, 供静态阅读各工具 schema。

用途: 写 TOOL_ARG_OVERRIDES 前必须知道**声明类型**(text/integer/boolean)与是否必填,
否则会把覆盖值写成"类型不符"从而仍被守卫拦下(该项目读取器是类型严格的:
yyjson取整数 对字符串节点拿不到、yyjson取文本 对数字节点拿不到)。
"""
import io
import json
import os
import sys
import urllib.request

BASE = "http://127.0.0.1:9222"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tools_list.json')


def rpc(method, params=None, _id=1):
    body = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(BASE + "/mcp",
                                 data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    resp = rpc("tools/list")
    tools = ((resp.get("result") or {}).get("tools")) or []
    if not tools:
        print("!! tools/list 未返回工具: %s" % json.dumps(resp, ensure_ascii=False)[:400])
        return 2
    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        json.dump({"count": len(tools), "tools": tools}, f, ensure_ascii=False, indent=1)
    print("已导出 %d 个工具 -> %s" % (len(tools), OUT))

    # 顺手打印本次关心的几个工具的 schema, 便于直接读
    want = ["browser_vip_set_css_version", "browser_set_window_style",
            "browser_fill_attr_set", "browser_dom_query", "browser_wait",
            "browser_intercept", "browser_kernel_watch", "browser_cdp_event",
            "browser_network_body", "browser_find_by_tag"]
    idx = {t.get("name"): t for t in tools}
    for w in want:
        t = idx.get(w)
        if not t:
            print("\n== %s: 不存在 ==" % w)
            continue
        props = (t.get("inputSchema") or {}).get("properties") or {}
        req = (t.get("inputSchema") or {}).get("required") or []
        print("\n== %s ==" % w)
        print("   required=%s" % (req or "[]"))
        for pn, ps in props.items():
            print("     %-16s type=%-8s %s" % (pn, (ps or {}).get("type"),
                                               ((ps or {}).get("description") or "")[:70]))
        if not props:
            print("     (无参数)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
