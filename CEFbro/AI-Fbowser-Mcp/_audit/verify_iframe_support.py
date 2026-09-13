# -*- coding: utf-8 -*-
r"""[已被取代 — 保留仅作历史] G1 最早期的 iframe 验收脚本。

取代者(更严格, 请用这两个):
  · verify_frame_dom_read.py  —— 25 臂: 三层判别值(MAIN/IFRAME1/IFRAME2) + 按名/按id/按序号 +
    写操作双向验证 + 未知 frame_id 不得回落到主框架 + **跨域(OOPIF)** 框架读取
  · verify_frame_exec.py      —— 17 臂: browser_execute_js {frame_id} + world 语义 + 稳定性
本脚本的 F 臂曾因"同名框架跨探针残留"与"硬编码历史值"产生误报(框架是跨脚本复用的),
其判别力已被上述两个脚本完全覆盖, 故不再作为验收依据。
"""

判别设计: 主框架与 iframe **放同一个选择器 `#tgt`、但值不同**(MAIN vs IFRAME), 于是
  · 不给 frame_id 读到 MAIN、给了 frame_id 读到 IFRAME -> 证明定位真的生效(而不是"碰巧改到了同一个元素");
  · 写操作也做双向验证: 带 frame_id 只改 iframe(主框架不受影响), 不带则只改主框架(回归)。
预言机用 browser_execute_js 直接读 DOM(srcdoc 同源, 主框架可穿透 contentDocument), 不依赖被测工具本身。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


def js(expr):
    return val(call("browser_execute_js", {"code": expr})[1])


MAIN_VALUE = "document.querySelector('#tgt')?document.querySelector('#tgt').value:'__NO_MAIN__'"
IFRAME_VALUE = ("(function(){var f=document.querySelector('iframe');"
                "if(!f||!f.contentDocument)return '__NO_IFRAME__';"
                "var e=f.contentDocument.querySelector('#tgt');return e?e.value:'__NO_ELEM__'})()")

print('== 造页面: 主框架与 iframe 各有一个 #tgt(值不同), 且 iframe **带名字** ==')
call("browser_navigate", {"url": "https://example.com/?iframe117=%d" % int(time.time()),
                          "wait_for_load": True})
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<input id=\"tgt\" value=\"MAIN\"><iframe id=\"fr\" name=\"mcpfr\" "
     "srcdoc=\"<input id=tgt value=IFRAME>\"></iframe>');'ok'"})
time.sleep(1.0)
print('   主框架 #tgt = %r' % js(MAIN_VALUE))
print('   iframe  #tgt = %r' % js(IFRAME_VALUE))
rec('基线: 两边各自可读且值不同(判别有效)',
    js(MAIN_VALUE) == 'MAIN' and js(IFRAME_VALUE) == 'IFRAME',
    '主=%r iframe=%r' % (js(MAIN_VALUE), js(IFRAME_VALUE)))

e, t = call("browser_get_frames", {})
frames = []
try:
    frames = json.loads(t).get("frames") or []
except Exception as ex:
    print('   解析 frames 失败: %r / 原文 %s' % (ex, t[:200]))
sub = next((f for f in frames if f.get('is_main') is False), None)
fid = (sub or {}).get('id')
print('   子框架 id = %r (name=%r)' % (fid, (sub or {}).get('name')))

print('\n== A. 不带 frame_id: 读主框架(回归) ==')
# 注意: fill_attr_get 不给 attribute 时读的是**元素文本**(input 为空), 故此臂必须显式要 value 属性
e1, t1 = call("browser_fill_attr_get", {"selector": "#tgt", "attribute": "value"})
print('   %s' % val(t1)[:120])
rec('无 frame_id 时读到主框架的 MAIN', (not e1) and 'MAIN' in val(t1), val(t1)[:120])

print('\n== B. ★带 frame_id: 必须读到 iframe 里的 IFRAME ==')
if fid:
    e2, t2 = call("browser_fill_attr_get", {"selector": "#tgt", "attribute": "value",
                                            "frame_id": fid})
    print('   %s' % val(t2)[:140])
    rec('★带 frame_id 读到 IFRAME(证明能进 iframe)', (not e2) and 'IFRAME' in val(t2), val(t2)[:160])
else:
    rec('★带 frame_id 读到 IFRAME', False, '取不到子框架 id')

print('\n== C. ★带 frame_id 写: 只改 iframe, 主框架不动 ==')
if fid:
    e3, t3 = call("browser_fill_set_value", {"selector": "#tgt", "value": "WRITTEN_IN_IFRAME",
                                             "frame_id": fid})
    print('   回包: %s' % val(t3)[:140])
    time.sleep(0.4)
    mv, iv = js(MAIN_VALUE), js(IFRAME_VALUE)
    print('   写后: 主=%r iframe=%r' % (mv, iv))
    rec('★iframe 内被写入', iv == 'WRITTEN_IN_IFRAME', 'iframe=%r' % iv)
    rec('★主框架**未**被误改(无串扰)', mv == 'MAIN', '主=%r' % mv)
else:
    rec('★iframe 内被写入', False, '取不到子框架 id')

print('\n== D. 不带 frame_id 写: 改的是主框架(回归) ==')
e4, t4 = call("browser_fill_set_value", {"selector": "#tgt", "value": "WRITTEN_IN_MAIN"})
time.sleep(0.4)
mv, iv = js(MAIN_VALUE), js(IFRAME_VALUE)
print('   写后: 主=%r iframe=%r' % (mv, iv))
rec('无 frame_id 时改主框架(向后兼容)', mv == 'WRITTEN_IN_MAIN', '主=%r' % mv)
rec('且 iframe 仍是上一次的值(互不影响)', iv == 'WRITTEN_IN_IFRAME', 'iframe=%r' % iv)

print('\n== E. 传不存在的 frame_id: 必须可行动地失败(而不是静默改主框架) ==')
e5, t5 = call("browser_fill_set_value", {"selector": "#tgt", "value": "X",
                                         "frame_id": "no-such-frame-zzz"})
mv = js(MAIN_VALUE)
print('   回包: isError=%s %s' % (e5, t5[:160]))
print('   主框架值: %r' % mv)
rec('未知 frame_id 不静默改主框架(主框架仍是 WRITTEN_IN_MAIN)', mv == 'WRITTEN_IN_MAIN', '主=%r' % mv)

print('\n== F. 按框架**名**定位也可用(本页 iframe 有 name=mcpfr) ==')
# 约束: 断言必须拿**当前**预言机值比, 不能硬编码历史值 —— 浏览器是跨探针复用的, 同名框架可能残留,
# 硬编码会让本臂读出别的框架的旧值而误报失败(实测: 读到 'IFRAME' 而非写入值)。
_iv_now = js(IFRAME_VALUE)
_mv_now = js(MAIN_VALUE)
print('   当前预言机: iframe=%r 主=%r' % (_iv_now, _mv_now))
e7, t7 = call("browser_fill_attr_get", {"selector": "#tgt", "attribute": "value",
                                        "frame_id": "mcpfr"})
_got7 = val(t7)
print('   frame_id="mcpfr" -> %s' % _got7[:140])
rec('按框架名也能定位到 iframe(读到 iframe 当前值, 非主框架值)',
    (not e7) and (str(_iv_now) in _got7) and (str(_mv_now) not in _got7 or _iv_now == _mv_now),
    'tool=%r iframe=%r 主=%r' % (_got7[:60], _iv_now, _mv_now))

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
