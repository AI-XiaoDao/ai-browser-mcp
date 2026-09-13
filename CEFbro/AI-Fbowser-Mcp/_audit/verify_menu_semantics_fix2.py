# -*- coding: utf-8 -*-
"""本轮修复的最终验收(3 臂, 每臂都有判别力)。

臂1 正常用法(9 行, 列位正确):
    item|自建普通|0|1|0| / check|自建勾选|0|0|0| / dis||26501|1|0| / vis||26501|0|0|
    relabel|改名了|26502|1|0| / mark||26502|1|0| / accel||26502|1|0|70C|(行尾补|应被容忍)
    relabel|想改默认|reload|1|0|(默认项, 必失败) / relabel|不存在|27999|1|0|(不存在, 必失败)
  判据: applied=7 / verified=3 / verify_mismatch 空 / apply_failed 恰好 2 条且原因不同 / 项数 19
臂2 故意把"修改类新标签"写错列(7 段, 第5列变成 1):
  判据: set 能通过(行尾空段可容忍), 但施加时**必须**在 apply_failed 里报"跳过"+父ID+列位提示
臂3 列数超宽(8 段): 判据: set 阶段直接拒绝并讲清列位
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
R = []

MAIN = "\n".join([
    "item|自建普通|0|1|0|",
    "check|自建勾选|0|0|0|",
    "dis||26501|1|0|",
    "vis||26501|0|0|",
    "relabel|改名了|26502|1|0|",
    "mark||26502|1|0|",
    "accel||26502|1|0|70C|",
    "relabel|想改默认|reload|1|0|",
    "relabel|不存在|27999|1|0|",
])
MISPLACED = "\n".join([
    "item|自建跳过|0|1|0|",
    "relabel||26501|改名了|1|0|",
])
OVERWIDE = "item|自建X|0|1|0|1|1|1|"


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


def kill():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)


def boot(tag):
    kill()
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
    call("browser_navigate", {"url": "https://example.com/?%s" % tag,
                              "wait_for_load": True}, 90)
    time.sleep(1.0)


def rightclick():
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": 130, "y": 130,
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)
    time.sleep(2.0)


def num(js, key):
    m = re.search(r'"%s":(\d+)' % key, js)
    return int(m.group(1)) if m else None


def txt(js, key):
    m = re.search(r'"%s":"([^"]*)"' % key, js)
    return m.group(1) if m else None


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + detail[:340]) if detail else ''))


print('== 臂1: 正常用法 ==')
boot('fix1')
e, t = call("browser_context_menu", {"action": "set", "items": MAIN})
rec('set 接受 9 行(含行尾补 | 的 accel 行)', not e, flat(t)[:280])
if e:
    sys.exit(1)
rightclick()
_, g = call("browser_context_menu", {"action": "get"})
g = flat(g)
applied, verified = num(g, 'last_applied_items'), num(g, 'verified_items')
mism, fails = txt(g, 'verify_mismatch'), txt(g, 'apply_failed')
print('   applied=%s verified=%s items=%s' % (applied, verified, num(g, 'menu_item_count')))
print('   verify_mismatch=%r\n   apply_failed=%r' % (mism, fails))
rec('5 条自建项修改 + 2 条创建 全部计入(applied=7)', applied == 7, 'applied=%s' % applied)
rec('D1 回读方向已校正(dis/vis/mark 三条回读全过, 无不一致)',
    mism == '' and verified == 3, 'verified=%s mismatch=%r' % (verified, mism))
rec('D2 默认项失败如实报出(报告解析后的ID 102, 而非别名 reload)',
    bool(fails) and '102' in (fails or '') and '默认菜单项' in (fails or ''), fails)
rec('D2 不存在的ID如实报出(与上一条原因不同)',
    bool(fails) and '27999' in (fails or '') and '条目不存在' in (fails or ''), fails)
rec('创建 2 个自建项真实存在于菜单(17+2=19)', num(g, 'menu_item_count') == 19,
    'menu_item_count=%s' % num(g, 'menu_item_count'))

print('\n== 臂2: 故意把新标签写错列(第5列变成 1) ==')
boot('fix2')
e, t = call("browser_context_menu", {"action": "set", "items": MISPLACED})
print('   set isError=%s' % e)
rightclick()
_, g2 = call("browser_context_menu", {"action": "get"})
g2 = flat(g2)
f2 = txt(g2, 'apply_failed')
print('   applied=%s apply_failed=%r' % (num(g2, 'last_applied_items'), f2))
rec('错列位不再"静默" —— 跳过被记入 apply_failed 并给出父ID与列位',
    bool(f2) and ('跳过' in f2) and ('父命令ID=1' in f2) and ('列位' in f2), f2)
rec('同时只有创建那条生效(applied=1)', num(g2, 'last_applied_items') == 1,
    'applied=%s' % num(g2, 'last_applied_items'))

print('\n== 臂3: 列数超宽(8 段)应在 set 阶段拒绝 ==')
boot('fix3')
e, t = call("browser_context_menu", {"action": "set", "items": OVERWIDE})
tt = flat(t)
print('   isError=%s | %s' % (e, tt[:300]))
rec('超宽规格被 set 阶段拒绝且讲清列位',
    e and ('字段过多' in tt) and ('6 列' in tt) and ('第2列' in tt), tt[:300])

call("browser_context_menu", {"action": "clear"})
kill()
ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
