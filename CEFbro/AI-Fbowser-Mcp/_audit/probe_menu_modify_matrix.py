# -*- coding: utf-8 -*-
"""真值矩阵实验: 修改类 setter 在**默认项 / 自建普通项 / 自建勾选项**上的返回值与回读。

规格:
    item|自建项|0|1|0|       -> 26501 (普通项)
    check|自建勾选|0|1|0|    -> 26502 (勾选项, 创建时即选中)
    diag||102|1|0|           -> 浏览器默认项(重新加载)
    diag||26501|1|0|         -> 自建普通项
    diag||26502|1|0|         -> 自建勾选项

每个 diag 会依次做:
    relabel / visT+rdVisT / visF+rdVisF / (恢复可见) / disT+rdDisT / disF+rdDisF
    / markT+rdMarkT / markF+rdMarkF / hasAccel / accel / hasAccel2 / noaccel
`T`=真 `F`=假。一次右键一次(原生菜单无法用 CDP 关闭)。
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
SPEC = "\n".join([
    "item|自建项|0|1|0|",
    "check|自建勾选|0|1|0|",
    "diag||102|1|0|",
    "diag||26501|1|0|",
    "diag||26502|1|0|",
])


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def flat(t):
    return t.replace('\\"', '"')


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?matrix=1", "wait_for_load": True}, 90)
time.sleep(1.0)

print('== 下发布置真值矩阵规格 ==')
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print('   isError=%s | %s' % (e, flat(t)[:200]))
if e:
    sys.exit(1)

print('\n== 右键一次 ==')
for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
    call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                             "params": {"type": typ, "x": 130, "y": 130,
                                        "button": "right", "clickCount": 1,
                                        "buttons": btn}}, 40)
time.sleep(2.0)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
for k in ('apply_count', 'last_applied_items', 'menu_item_count', 'verified_items',
          'last_error'):
    m = re.search(r'"%s":("[^"]*"|\d+|true|false)' % k, f)
    print('   %-18s %s' % (k, m.group(1) if m else '(缺)'))

blocks = re.findall(r'\[diag (\d+) ([^\]]*)\]', f)
print('\n== 真值矩阵 ==')
if not blocks:
    print('   !! 没有 diag 记录')
LABELS = {102: '默认项 重新加载', 26501: '自建普通项', 26502: '自建勾选项'}
for cid, body in blocks:
    print('\n   ID %s (%s)' % (cid, LABELS.get(int(cid), '?')))
    for kv in re.findall(r'(\w+)=([TF])', body):
        print('      %-10s %s' % kv)

print('\n== 自动判读 ==')
for cid, body in blocks:
    d = dict(re.findall(r'(\w+)=([TF])', body))
    name = LABELS.get(int(cid), cid)
    if 'rdVisT' in d:
        if d.get('visT') == 'F':
            print('   %-14s 置可见(真)本身就返回 F -> 该 ID 不可改可见性' % name)
        else:
            print('   %-14s 置可见(真)=%s 且 读回=%s / 置可见(假)=%s 且 读回=%s -> %s'
                  % (name, d['visT'], d['rdVisT'], d.get('visF'), d.get('rdVisF'),
                     '可见链正常' if (d['rdVisT'] == 'T' and d.get('rdVisF') == 'F')
                     else '可见链与期望不符'))
    if 'rdDisT' in d:
        if d.get('disT') == 'F':
            print('   %-14s 置禁止(真)返回 F -> 该 ID 不可改禁用状态' % name)
        else:
            inv = (d.get('rdDisT') == 'F' and d.get('rdDisF') == 'T')
            print('   %-14s 置禁止(真)=%s 读回=%s / 置禁止(假)=%s 读回=%s -> %s'
                  % (name, d['disT'], d.get('rdDisT'), d.get('disF'), d.get('rdDisF'),
                     '★两者互为反义(命名有问题)' if inv else
                     ('正向一致' if (d.get('rdDisT') == 'T' and d.get('rdDisF') == 'F')
                      else '无变化')))
    if 'rdMarkT' in d:
        print('   %-14s 选中(真)=%s 读回=%s / 选中(假)=%s 读回=%s hasAccel=%s accel=%s hasAccel2=%s noaccel=%s'
              % (name, d.get('markT'), d.get('rdMarkT'), d.get('markF'),
                 d.get('rdMarkF'), d.get('hasAccel'), d.get('accel'),
                 d.get('hasAccel2'), d.get('noaccel')))

call("browser_context_menu", {"action": "clear"})
print('\n== 完 ==')
