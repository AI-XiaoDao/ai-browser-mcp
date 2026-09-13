# -*- coding: utf-8 -*-
r"""M1 — MCP 工具真机调用探针

对 127.0.0.1:9222 的每个注册工具真实发起 tools/call，分类结果：
  OK            成功返回且 content 非空
  GUARD         失败但信息可行动(缺参数/需确认等) —— 属**正确行为**
  BAD_ERR       失败且信息不可行动(空/未知命令/内部错误)
  NOTFOUND      JSON-RPC -32601 工具不存在
  TIMEOUT       客户端超时
  TRANSPORT     连接/协议层错误

安全: 破坏性工具(shutdown/close/delete/clear/proxy/navigate 等)只做"缺参数校验"，
      不带真实参数, 并在报告中标注为 SKIP_MUTATE。
"""
import json, sys, os, time, io, urllib.request, urllib.error
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
OUT = os.path.dirname(os.path.abspath(__file__))

# 破坏性 / 会改变会话状态 -> 只验证路由与参数校验, 不传真实参数
MUTATE = {
    "browser_shutdown", "browser_close", "browser_delete_cookies",
    "browser_clear_cache", "browser_clear_cache_browser", "browser_navigate",
    "browser_reload", "browser_back", "browser_forward", "browser_stop",
    "browser_set_proxy", "browser_clear_proxy", "browser_restore_gui",
    "browser_intercept", "browser_kernel_download", "browser_kernel_scheme",
    "browser_kernel_auth", "browser_kernel_cert", "browser_kernel_menu",
    "browser_vip_load_extension", "browser_vip_unload_extension",
    "browser_create", "browser_move_window", "browser_set_zoom",
    "browser_set_mute", "browser_set_parent", "browser_set_focus",
    "browser_set_auto_resize", "browser_edit_paste", "browser_print",
    "browser_print_to_pdf", "browser_start_download", "browser_download_image",
    "browser_debugger_pause", "browser_debugger_resume",
    "browser_debugger_step_over", "browser_debugger_step_into",
    "browser_debugger_step_out", "browser_debugger_set_breakpoint",
    "browser_debugger_enable", "browser_debugger_auto", "browser_debugger_flow",
    "browser_reverse_*", "workflow_run",
}

# 需要真实参数的"只读"工具 -> 给一组最小可用参数, 验证内容正确性
READONLY_ARGS = {
    "browser_get_url": {},
    "browser_get_title": {},
    "browser_get_id": {},
    "browser_status": {},
    "browser_is_loading": {},
    "browser_is_muted": {},
    "browser_can_navigate": {},
    "browser_get_zoom": {},
    "browser_loading_info": {},
    "browser_window_info": {},
    "browser_popup_info": {},
    "browser_list": {},
    "browser_get_window_handle": {},
    "browser_fbro_version": {},
    "browser_get_frames": {},
    "browser_frame_names": {},
    "browser_get_focused_frame": {},
    "browser_get_window_title": {},
    "browser_cache_dir": {},
    "browser_request_context": {},
    "browser_user_tags": {},
    "browser_get_global_cache_dir": {},
    "browser_get_process_type": {},
    "browser_ipc_renderer_count": {},
    "browser_ipc_renderer_ids": {},
    "mcp_status": {},
    "aliases": {},
    "browser_network": {"action": "list", "limit": 3},
    "browser_event": {},
    "browser_get_source": {"max_chars": 200, "sync_wait": True, "max_ms": 3000},
    "browser_get_text": {"selector": "body", "max_chars": 200},
    "browser_evaluate": {"code": "1+1", "max_ms": 3000},
    "browser_execute_js": {"code": "1+1"},
    "browser_console_eval": {"expression": "1+1"},
    "browser_get_cookies": {"limit": 3},
    "browser_base64_encode": {"data": "hi"},
    "browser_base64_decode": {"data": "aGk="},
    "browser_uri_encode": {"data": "a b"},
    "browser_uri_decode": {"data": "a%20b"},
    "browser_dom_query": {"selector": "body"},
    "browser_dom_get_html": {"selector": "body", "max_chars": 200},
    "browser_dom_rect": {"selector": "body"},
    "browser_dom_inner_html": {"selector": "body"},
    "browser_dom_checked": {"selector": "body"},
    "browser_dom_selected": {"selector": "body"},
    "browser_extract": {"type": "links", "limit": 3},
    "browser_snapshot": {"limit": 5},
    "browser_get_forms": {},
    "browser_find": {"text": "MCP"},
    "browser_reverse_env": {},
    "browser_fingerprint": {"action": "count"},
    "browser_collect": {"action": "console_get", "limit": 3},
    "browser_cdp_event": {"event": "Debugger.paused"},
    "mcp_result": {"request_id": "nonexistent_probe"},
    "mcp_help": {},
    "ping": {},
}


def rpc(method, params, rid, timeout=6.0):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                       "params": params}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_tools():
    req = urllib.request.Request(BASE + "/tools/list")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))["tools"]


def classify(resp):
    if resp is None:
        return "TRANSPORT", ""
    if "error" in resp:
        code = resp["error"].get("code")
        msg = resp["error"].get("message", "")
        if code == -32601:
            return "NOTFOUND", msg
        return "BAD_ERR", "[%s] %s" % (code, msg)
    res = resp.get("result") or {}
    txt = ""
    try:
        txt = res["content"][0]["text"]
    except Exception:
        txt = json.dumps(res, ensure_ascii=False)[:400]
    if res.get("isError"):
        # 失败但信息是否有用
        if len(txt) < 12 or "未知命令" in txt or "结果解析失败" in txt:
            return "BAD_ERR", txt[:200]
        return "GUARD", txt[:200]
    if not txt.strip():
        return "BAD_ERR", "(成功但 content 为空)"
    return "OK", txt[:200]


GUIDANCE = ("不能为空", "缺少", "请", "需要", "必须先", "不支持", "无效",
            "不在", "超时", "未找到", "requires", "confirm")


def main():
    tools = get_tools()
    print("注册工具数: %d" % len(tools))
    rows = []
    t0 = time.time()
    for i, t in enumerate(tools, 1):
        name = t["name"]
        mut = name in MUTATE or any(
            name.startswith(m.rstrip("*")) for m in MUTATE if m.endswith("*"))
        args = {} if mut else READONLY_ARGS.get(name, {})
        cat, detail = "?", ""
        try:
            resp = rpc("tools/call", {"name": name, "arguments": args}, 1000 + i)
            cat, detail = classify(resp)
        except urllib.error.URLError as e:
            cat, detail = "TRANSPORT", str(e)[:120]
        except Exception as e:
            cat = "TIMEOUT" if "timed out" in str(e).lower() else "TRANSPORT"
            detail = str(e)[:120]
        rows.append({"name": name, "cat": cat, "detail": detail,
                     "mutate_only": mut, "has_args": bool(args),
                     "desc": (t.get("description") or "")[:160],
                     "schema": t.get("inputSchema") or {}})
        flag = "" if cat in ("OK", "GUARD") else "  <<<"
        print("[%3d/%3d] %-46s %-10s %s%s" % (i, len(tools), name, cat,
                                              detail[:70].replace("\n", " "), flag))
    dt = time.time() - t0
    json.dump(rows, open(os.path.join(OUT, "probe_raw.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print()
    print("耗时 %.1fs" % dt)
    from collections import Counter
    c = Counter(r["cat"] for r in rows)
    for k, v in c.most_common():
        print("  %-10s %d" % (k, v))


if __name__ == "__main__":
    main()
