# -*- coding: utf-8 -*-
r"""第 170 轮 B2/B3/B5 受控验证:
B2: browser_id 非法(-1/abc/true) → 必须参数非法失败(绝不静默回退主浏览器)
B3: browser_close 主窗口无 confirm → 必须拒绝; 非主窗口(browser_id=2) 无 confirm → 允许
B5: browser_vip_enable_devtools_observer 开关仍可用(显式浏览器参数)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM

ok = []


def call(name, args, timeout=30):
    return CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                         'params': {'name': name, 'arguments': args}}, timeout)


def text_of(r):
    return ''.join((c.get('text') or '') for c in
                   ((r.get('result') or {}).get('content') or []))


def check(tag, cond, detail):
    ok.append(cond)
    print('%s [%s] %s' % ('PASS' if cond else 'FAIL', tag, detail[:130]))


# B2: 非法 browser_id
for bid in (-1, 'abc', True):
    r = call('browser_get_url', {'browser_id': bid})
    t = text_of(r)
    check('B2 browser_id=%s 拒绝' % bid, 'browser_id 参数非法' in t and 'browser_list' in t, t[:100])

# 合法 browser_id=1 仍可用(主浏览器当前URL是欢迎页 127.0.0.1:9222 或 example.com 均可)
r = call('browser_get_url', {'browser_id': 1})
t = text_of(r)
check('B2 browser_id=1 正常', '127.0.0.1' in t or 'example.com' in t, t[:80])

# B3: 主窗口无 confirm 必须拒绝
r = call('browser_close', {})
t = text_of(r)
check('B3 主窗口无confirm拒绝', 'confirm:true' in t and ('confirm' in t), t[:120])

# 建第二个浏览器, 无 confirm 关闭它必须允许
r = call('browser_create', {})
t = text_of(r)
check('B3 前置: 创建第二浏览器', '浏览器已创建' in t or '"success":true' in t, t[:80])
r = call('browser_list', {})
t = text_of(r)
ids = json.loads(t[t.index('['):t.rindex(']') + 1]) if ('[' in t) else []
ids = [b.get('id') for b in ids] if isinstance(ids, list) else []
non_main = [i for i in ids if i != 1]
check('B3 前置: 存在非主窗口', len(non_main) >= 1, 'ids=%s' % ids)
if non_main:
    r = call('browser_close', {'browser_id': non_main[0]})
    t = text_of(r)
    check('B3 非主窗口无confirm允许关闭', '浏览器已关闭' in t or '回读确认' in t, t[:110])

# B5: 观察者开关仍可用(工具设计: enable 需字符串 "false", 布尔 false 属"缺省"被拒以防误关闭)
r = call('browser_vip_enable_devtools_observer', {'enable': 'false'})
t = text_of(r)
check('B5 关闭观察者', '监管者事件已关闭' in t or '"success":true' in t, t[:90])
r = call('browser_vip_enable_devtools_observer', {'enable': True})
t = text_of(r)
check('B5 重新启用观察者', '监管者事件已启用' in t or '"success":true' in t, t[:90])

# 收尾健康
r = call('browser_execute_js', {'code': '1', 'max_ms': 4000})
t = text_of(r)
check('收尾 execute_js', '"message":"1"' in t or '1' in t, t[:60])

print('== 结果: %d/%d 通过 ==' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
