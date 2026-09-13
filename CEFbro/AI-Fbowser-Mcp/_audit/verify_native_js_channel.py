# -*- coding: utf-8 -*-
r"""对照量测: 原生"带返回值 JS"通道在主框架上是否也会退化(用于判定 G1b 的退化是否为本项目引入)。

三个对照臂, 各连续 12 次:
  A. browser_evaluate           —— 原生 提交异步JS任务 -> 异步执行JS -> 执行JS代码_带返回值(**主框架**)
  B. browser_execute_js(无frame) —— CDP 优先路径(主框架)
  C. browser_execute_js{frame_id} —— 本次新增: 原生 执行JS代码_带返回值(**子框架**)
判据: 若 A 也退化, 说明"原生带返回值 JS"通道本身有此性质(与子框架无关);
      若 A/B 稳定而 C 退化, 则是子框架原生执行的特有问题, 该路线不可用于交付。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
N = 12


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


call("browser_navigate", {"url": "https://example.com/?cmp=%d" % int(time.time()),
                          "wait_for_load": True})
time.sleep(0.8)
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"fr1\" name=\"cmpfr\" srcdoc=\"<b>x</b>\"></iframe>');'ok'"})
time.sleep(1.0)
e, t = call("browser_get_frames", {})
frames = json.loads(t).get("frames") or []
sub = next((f for f in frames if f.get('name') == 'cmpfr'), None)
print('子框架 id=%r' % ((sub or {}).get('id')))


def run(label, name, args_fn, expect):
    ok = 0
    slow = []
    for i in range(N):
        t0 = time.time()
        e, t = call(name, args_fn())
        dt = time.time() - t0
        got = val(t)
        good = (not e) and got == expect
        ok += 1 if good else 0
        if not good:
            slow.append(i + 1)
            print('      ✗ 第%d次 %.2fs: %s' % (i + 1, dt, t[:150]))
    print('   [%s] %-28s %2d/%d 通过%s'
          % ('PASS' if ok == N else 'FAIL', label, ok, N,
             ('  失败序号=%s' % slow) if slow else ''))


print('\n== A. browser_evaluate(原生带返回值, 主框架) 连续 %d 次 ==' % N)
run('A browser_evaluate', 'browser_evaluate', lambda: {"code": "1+1"}, '2')

print('\n== B. browser_execute_js(CDP, 主框架) 连续 %d 次 ==' % N)
run('B execute_js(CDP主框架)', 'browser_execute_js', lambda: {"code": "1+1"}, '2')

print('\n== C. browser_execute_js{frame_id}(原生带返回值, 子框架) 连续 %d 次 ==' % N)
if sub:
    run('C execute_js(子框架)', 'browser_execute_js',
        lambda: {"code": "1+1", "frame_id": sub.get('id')}, '2')
else:
    print('   [SKIP] 取不到子框架 id')

print('\n== D. A 之后再跑 B(看原生通道退化是否影响 CDP) ==')
run('D execute_js(CDP主框架) 复测', 'browser_execute_js', lambda: {"code": "1+1"}, '2')
