# -*- coding: utf-8 -*-
r"""量"恢复可见后第一次滚轮是否会被吞掉": 隐藏→显示后连续发 3 次滚轮, 每次都用页面 scrollY 核对。

起因: 验收脚本 ⑦ 里"恢复可见后滚轮返回成功(0.02s)但 scrollY 没变", 而隐藏前同一操作 scrollY 120 生效。
需判定这是 ①首次被吞(之后正常) ②一直不生效(真缺陷) ③读取时机问题(合成器线程滚动, 主线程 pageYOffset 晚更新)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=120):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    t = "".join(i.get("text") or "" for i in (rr.get("content") or []) if i.get("type") == "text")
    return bool(rr.get("isError")), t, dt


def js(e):
    _e, t, _dt = call("browser_execute_js", {"code": e})
    try:
        return json.loads(t).get("message", "")
    except Exception:
        return t


def y():
    return js("String(Math.round(window.pageYOffset||0))")


def vis(v):
    call("browser_show_window", {"visible": v})


def wheel(tag, dy=60):
    e, t, dt = call("browser_mouse_wheel", {"x": 300, "y": 300, "delta_y": dy})
    before = y()
    time.sleep(0.6)
    after = y()
    print('   %-30s %6.2fs err=%-5s scrollY %s -> %s' % (tag, dt, e, before, after))
    return dt, e


vis(True)
time.sleep(1.0)
print('== 准备: 注入高内容并归零 ==')
js("(function(){var o=document.getElementById('occw_tall');if(o)o.remove();"
   "var d=document.createElement('div');d.id='occw_tall';d.style.height='4000px';"
   "d.textContent='tall';document.body.appendChild(d);window.scrollTo(0,0);return 'ok'})()")
time.sleep(0.5)
print('   scrollY =', y())

print('\n== A. 全程可见: 连续 3 次滚轮(对照) ==')
for i in (1, 2, 3):
    wheel('可见 #%d' % i)

print('\n== B. 隐藏 3 秒再显示, 立刻连续 3 次滚轮 ==')
vis(False)
time.sleep(3.0)
vis(True)
time.sleep(0.3)
for i in (1, 2, 3):
    wheel('恢复后 #%d' % i)

print('\n== C. 再隐藏→显示, 但先做一次 mouse_move 再滚(看是否与"解节流"有关) ==')
vis(False)
time.sleep(3.0)
vis(True)
time.sleep(0.3)
e, t, dt = call("browser_mouse_move", {"x": 300, "y": 300})
print('   恢复后先 mouse_move: %.2fs err=%s' % (dt, e))
for i in (1, 2):
    wheel('move 后 #%d' % i)

print('\n== 清理 ==')
js("(function(){var o=document.getElementById('occw_tall');if(o)o.remove();window.scrollTo(0,0);return 'cleanup'})()")
vis(True)
