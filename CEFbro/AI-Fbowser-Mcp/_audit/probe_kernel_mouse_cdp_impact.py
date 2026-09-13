# -*- coding: utf-8 -*-
r"""判定一条**长期沿用的口径**: "内核级鼠标注入会让本会话 CDP 通道永久失效"。

背景: 项目多处注释/工具文案都这么写(`MCP_Server.wsv:3344/10734` 等), 而台账里
`browser_vip_mouse_click/_press/_release/_move` 却是 **pass** —— 两者矛盾(要么注释陈旧, 要么那些 pass 是假象)。
本脚本做**受控实验**: 先量 CDP 健康(execute_js 延迟 + 一次纯 CDP 工具), 再故意调用内核级 `browser_vip_mouse_click`,
然后立刻重测 —— 若 CDP 仍健康, 则该口径对"点击"这条路径**已被证伪**; 若真挂, 则如实记录并用重启恢复。

恢复手段: 若 CDP 真挂, 主代理随后跑 loop.py 重启实例(本脚本不重启)。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=45):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def health(tag):
    """CDP 健康三指标: execute_js 延迟 / 纯 CDP 工具(dom_query 走 CDP) / cdp_call。"""
    t0 = time.time()
    e1, t1 = call("browser_execute_js", {"code": "1+1"})
    d1 = time.time() - t0
    t0 = time.time()
    e2, t2 = call("browser_dom_query", {"selector": "h1", "attribute": "class"})
    d2 = time.time() - t0
    t0 = time.time()
    e3, t3 = call("browser_cdp_call", {"method": "Runtime.evaluate",
                                       "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"})
    d3 = time.time() - t0
    print('   [%s] execute_js %.2fs(err=%s) | dom_query(CDP) %.2fs(err=%s) | cdp_call %.2fs(err=%s)'
          % (tag, d1, e1, d2, e2, d3, e3))
    return d1, d2, d3, (e1 or e2 or e3)


call("browser_navigate", {"url": "https://example.com/?kernmouse=%d" % int(time.time()),
                          "wait_for_load": True})
print('== 1. 注入前基线 ==')
b = health('before')

print('\n== 2. 故意调用**内核级** VIP 鼠标点击 ==')
e, t = call("browser_vip_mouse_click", {"x": 100, "y": 100})
print('   browser_vip_mouse_click: isError=%s %s' % (e, t[:160]))
time.sleep(1.0)

print('\n== 3. 注入后立刻重测 ==')
a = health('after')

print('\n== 4. 再等 3 秒复测(排除"延迟失效") ==')
time.sleep(3.0)
c = health('after+3s')

print('\n判读:')
worst = max(a[0], a[1], a[2], c[0], c[1], c[2])
if worst < 6 and not (a[3] or c[3]):
    print('   CDP 通道**仍然健康**(最慢 %.2fs, 无错误) => "内核级鼠标注入使 CDP 永久失效" 对点击这条路径**已被本次实测证伪**;'
          '项目里那几处口径应改为"实测未复现"而不是断言失效。' % worst)
else:
    print('   CDP 出现退化/错误(最慢 %.2fs) => 该口径在本机仍然成立; 需要重启实例恢复(主代理执行 loop.py)。' % worst)
