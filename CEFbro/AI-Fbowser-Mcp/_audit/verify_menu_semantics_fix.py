# -*- coding: utf-8 -*-
"""验收本轮 4 项修复(每条都有判别力, 不是"看着对")。

主臂规格(2 个自建项 + 5 条能干成的修改 + 2 条注定干不成的):
    item|自建普通|0|1|0|           -> 26501
    check|自建勾选|0|0|0|          -> 26502
    dis||26501|1|0|                A 禁用自建项     : 回读方向校正后应 verified
    vis||26501|0|0|                B 隐藏自建项     : 应 verified
    relabel||26502|改名了|1|0|      C 改自建项标签   : 应 applied
    mark||26502|1|0|               D 勾选自建勾选项 : 应 verified
    accel||26502|70C|1|0|          E 自建项加 Ctrl+R : 应 applied(读回确认后计数)
    relabel||reload|试图改默认|1|0|  F 改**默认项**   : 应进 apply_failed 且写明"默认菜单项"
    relabel||27999|不存在的项|1|0|   G 改不存在的ID   : 应进 apply_failed 且写明"条目不存在"
判据: applied=7 / verified_items>=3 / verify_mismatch 为空 / apply_failed 同时含两种原因。
另两臂验 accel、noaccel 的计数是否真的按读回确认走(旧代码是无条件 +1)。
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


def arm(label, spec, tag):
    """重启 -> 下单 -> 右键 -> 取状态。返回 (set 回包, get 回包)。"""
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
    e, t = call("browser_context_menu", {"action": "set", "items": spec})
    if e:
        print('   !! set 失败: %s' % flat(t)[:300])
        return None, None
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": 130, "y": 130,
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)
    time.sleep(2.0)
    _, g = call("browser_context_menu", {"action": "get"})
    return flat(t), flat(g)


def rec(label, ok, detail):
    R.append((label, ok))
    print('   [%s] %s' % ('PASS' if ok else 'FAIL', label))
    print('        %s' % detail[:320])


def num(js, key):
    m = re.search(r'"%s":(\d+)' % key, js)
    return int(m.group(1)) if m else None


def txt(js, key):
    m = re.search(r'"%s":"([^"]*)"' % key, js)
    return m.group(1) if m else None


MAIN = "\n".join([
    "item|自建普通|0|1|0|",
    "check|自建勾选|0|0|0|",
    "dis||26501|1|0|",
    "vis||26501|0|0|",
    "relabel||26502|改名了|1|0|",
    "mark||26502|1|0|",
    "accel||26502|70C|1|0|",
    "relabel||reload|试图改默认|1|0|",
    "relabel||27999|不存在的项|1|0|",
])

print('== 主臂: 7 条能成 + 2 条注定不成 ==')
st, gt = arm('main', MAIN, 'fixmain')
if gt is None:
    sys.exit(1)
warn = txt(st, 'warnings')
print('   set.warnings = %r' % warn)
applied = num(gt, 'last_applied_items')
verified = num(gt, 'verified_items')
mism = txt(gt, 'verify_mismatch')
fails = txt(gt, 'apply_failed')
print('   applied=%s verified=%s items=%s' % (applied, verified,
                                              num(gt, 'menu_item_count')))
print('   verify_mismatch=%r' % mism)
print('   apply_failed=%r' % fails)

rec('A/B/C/D/E 五条自建项修改全部计入 applied(=7)',
    applied == 7, 'applied=%s (item+check 2 条创建 + dis/vis/relabel/mark/accel 5 条)' % applied)
rec('★D1 dis 回读方向已校正: 不再误报不一致, 且 verified>=3',
    (mism == '') and (verified is not None) and verified >= 3,
    'verify_mismatch=%r verified_items=%s' % (mism, verified))
rec('★D2 默认项失败被如实报出(含"默认菜单项"字样)',
    bool(fails) and ('reload' in fails) and ('默认菜单项' in fails), 'apply_failed=%r' % fails)
rec('★D2 不存在的ID也被如实报出(含"条目不存在"字样)',
    bool(fails) and ('27999' in fails) and ('条目不存在' in fails), 'apply_failed=%r' % fails)
rec('★D2 set 阶段就提前警告(指向默认项ID的修改类)',
    bool(warn) and ('reload' in warn) and ('不会生效' in warn), 'warnings=%r' % warn)
rec('创建的两个自建项都真在菜单里(真实项数 17+2=19)',
    num(gt, 'menu_item_count') == 19, 'menu_item_count=%s' % num(gt, 'menu_item_count'))

print('\n== 臂2: accel 后接 noaccel(同一自建项) -> 两条都应计数, applied=3 ==')
st2, gt2 = arm('chain', "item|自建计时|0|1|0|\naccel||26501|70C|1|0|\nnoaccel||26501|1|0|", 'fixchain')
if gt2:
    a2 = num(gt2, 'last_applied_items')
    print('   applied=%s apply_failed=%r' % (a2, txt(gt2, 'apply_failed')))
    rec('★E accel/noaccel 按"读回确认"计数(创建+加+删=3)',
        a2 == 3 and txt(gt2, 'apply_failed') == '', 'applied=%s' % a2)

print('\n== 臂3: 对**本来就没有快捷键**的自建项做 noaccel -> 幂等成功, 不算失败, applied=2 ==')
st3, gt3 = arm('idem', "item|自建无键|0|1|0|\nnoaccel||26501|1|0|", 'fixidem')
if gt3:
    a3 = num(gt3, 'last_applied_items')
    print('   applied=%s apply_failed=%r' % (a3, txt(gt3, 'apply_failed')))
    rec('幂等 noaccel 计为已施加而不是失败', a3 == 2 and txt(gt3, 'apply_failed') == '',
        'applied=%s' % a3)

call("browser_context_menu", {"action": "clear"})
kill()
ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
