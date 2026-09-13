# -*- coding: utf-8 -*-
r"""第 171 轮: 子代理审计修复定向验证(≤10 秒/项)。
① mcp_help 深链最后一个工具 → 详情必须是合法 JSON(尾不带 ']');
② browser_find_by_hwnd 大句柄(>2^31) 不再被截断(取长整数);
③ browser_network_export 的 HAR 条目 startedDateTime 非空(timestamp 已写)。
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM


def call(name, args, timeout=30):
    t0 = time.time()
    r = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                      'params': {'name': name, 'arguments': args}}, timeout)
    return r, time.time() - t0


def text_of(r):
    return ''.join((c.get('text') or '') for c in
                   ((r.get('result') or {}).get('content') or []))


ok = []


def check(tag, cond, detail):
    ok.append(cond)
    print('%s [%s] %s' % ('PASS' if cond else 'FAIL', tag, detail[:120]))


# ① mcp_help 深链: 找工具列表里最后一个工具名并请求其详情, 验证 JSON 可解析且结尾无 ']'
r, el = call('mcp_help', {})
t = text_of(r)
check('mcp_help 列表可用', '"tools"' in t or '工具' in t, t[:60])
tools = CM.http_get('/tools/list', timeout=15).get('tools', [])
last_tool = tools[-1]['name'] if tools else ''
r, el = call('mcp_help', {'tool': last_tool})
t = text_of(r)
parsed_ok = False
try:
    outer = json.loads(t)
    detail = outer.get('data') or {}
    if isinstance(detail, str):
        detail = json.loads(detail)
    parsed_ok = isinstance(detail, dict) and 'name' in detail
except Exception:
    parsed_ok = False
check('深链最后一个工具 %s 详情合法JSON' % last_tool, parsed_ok, t[:90])

# ② 大句柄不被截断: 传 3000000000 (>2^31), 期望"未找到窗口句柄为 3000000000"而不是 0/截断值
r, el = call('browser_find_by_hwnd', {'hwnd': 3000000000})
t = text_of(r)
check('hwnd 3000000000 未截断', '3000000000' in t, t[:100])

# ③ 网络记录 timestamp: 产生流量后导出, 记录项必须带非空 timestamp(HAR 的 startedDateTime 源)
call('browser_navigate', {'url': 'https://example.com/?harprobe=171'})
r, el = call('browser_network_export', {})
t = text_of(r)
ts_ok = False
try:
    obj = json.loads(t)
    logs = obj.get('network_logs') or []
    ts_ok = any((l.get('timestamp') or '') != '' for l in logs if isinstance(l, dict))
except Exception:
    ts_ok = False
check('网络记录含非空 timestamp', ts_ok, t[:110])

print('== 结果: %d/%d 通过 ==' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
