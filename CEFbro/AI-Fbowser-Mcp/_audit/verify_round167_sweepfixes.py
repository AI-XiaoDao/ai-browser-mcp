# -*- coding: utf-8 -*-
r"""第 167 轮复测: 334 回合第一遍的 6 个失败项 + step 工具自动恢复验证。

① browser_console_eval / browser_kernel_ipc_queue / browser_kernel_ipc_clear /
   browser_dom_select —— 探针参数已修, 应真路径成功;
② browser_mouse_wheel —— 窗口可见时应 0.03s 级成功(失败会自动强显窗口重试一次);
③ browser_debugger_step_over/into/out —— 本会话无断点时单步后必须自动 Debugger.resume,
   紧随其后的 browser_execute_js 必须**快速**成功(<5s, 页面没有挂在暂停态);
④ 收尾健康。
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import cold_matrix as CM

TO = 40
results = []


def call(name, args, timeout=TO):
    t0 = time.time()
    try:
        r = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                          'params': {'name': name, 'arguments': args}}, timeout)
        el = time.time() - t0
        return r, el
    except Exception as ex:
        return {'exception': str(ex)}, time.time() - t0


def ok_of(r):
    res = r.get('result') or {}
    if res.get('isError'):
        return False
    txt = json.dumps(res, ensure_ascii=False)
    return ('"success":true' in txt or '"success": true' in txt or
            '"valid":true' in txt or '"found":1' in txt or
            'message' in txt)


def check(tag, cond, detail):
    results.append((tag, cond))
    print('%s [%s] %s' % ('PASS' if cond else 'FAIL', tag, (detail or '')[:120]))


# ① 探针参数修复后的四项
r, el = call('browser_console_eval', {'expression': '1+1'})
check('console_eval', ok_of(r) and el < 5, 'el=%.2f %s' % (el, str(r)[:80]))

r, el = call('browser_kernel_ipc_queue', {'action': 'queue'})
check('ipc_queue', ok_of(r) and el < 5, 'el=%.2f %s' % (el, str(r)[:80]))

r, el = call('browser_kernel_ipc_clear', {'action': 'clear'})
check('ipc_clear', ok_of(r) and el < 5, 'el=%.2f %s' % (el, str(r)[:80]))

r, el = call('browser_dom_select', {'selector': 'h1'})
check('dom_select', ok_of(r) and el < 5, 'el=%.2f %s' % (el, str(r)[:100]))

# ② 滚轮
r, el = call('browser_mouse_wheel', {'x': 100, 'y': 100, 'delta_y': 300})
check('mouse_wheel', ok_of(r) and el < 30, 'el=%.2f %s' % (el, str(r)[:100]))

# ③ step 自动恢复: 每个 step 后紧跟 execute_js 快速探针
for step in ('browser_debugger_step_over', 'browser_debugger_step_into', 'browser_debugger_step_out'):
    r, el = call(step, {})
    txt = json.dumps(r, ensure_ascii=False)
    step_ok = (('自动' in txt and 'resume' in txt) or '"success":true' in txt) and el < 30
    r2, el2 = call('browser_execute_js', {'code': '1', 'max_ms': 4000})
    alive = ok_of(r2) and el2 < 5
    check('%s 自动恢复+页面存活' % step, step_ok and alive,
          'step el=%.2f | 探针 el=%.2f | step回=%s | 探针回=%s' % (el, el2, txt[:60], str(r2)[:60]))

# ④ 收尾健康
r, el = call('browser_execute_js', {'code': 'document.title', 'max_ms': 5000})
check('execute_js 收尾', ok_of(r) and el < 5, 'el=%.2f %s' % (el, str(r)[:60]))
r, el = call('browser_status', {})
check('browser_status', ok_of(r) and el < 5, 'el=%.2f' % el)

n = sum(1 for _, c in results if c)
print('== 结果: %d/%d 通过 ==' % (n, len(results)))
sys.exit(0 if n == len(results) else 1)
