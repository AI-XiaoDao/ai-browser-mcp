# -*- coding: utf-8 -*-
"""`browser_codec` / `browser_time_convert` 验收(期望值全部独立算准, 不凭印象)。

判据来源: `_audit/_codec_plan_r115.md` ③ 验收判据表(A/B/C 三组)。
本机时区已实测 UTC+08:00(Bias=-480), 故 UTC+8 列即本机期望值。

先打印两个工具的**实际 schema**, 便于在参数名与计划不一致时立刻看出来(而不是把参数名错误当成功能缺陷)。
"""
import base64
import binascii
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []


def rpc(method, params=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        b["params"] = params
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))


def call(n, a=None, to=90):
    o = rpc("tools/call", {"name": n, "arguments": a or {}}, to)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


# ── 先看 schema ──
o = rpc("tools/list")
tools = {t.get('name'): t for t in (o.get('result') or {}).get('tools') or []}
for nm in ('browser_codec', 'browser_time_convert'):
    t = tools.get(nm)
    if t:
        print('== %s schema ==\n   %s' % (nm, json.dumps(t.get('inputSchema'),
                                                         ensure_ascii=False)[:700]))
    else:
        print('== %s **不在工具清单里** ==' % nm)

# ── 期望值(独立算准) ──
EXP = {
    'hex_ab': binascii.hexlify(b'AB').decode(),
    'hex_cn': binascii.hexlify('中文'.encode('utf-8')).decode(),
    'hex_qw': binascii.hexlify(base64.b64decode('qw==')).decode(),
    'hex_dead': binascii.hexlify(base64.b64decode('3q2+7w==')).decode(),
    'gbk_cn': binascii.hexlify('中文'.encode('gbk')).decode(),
    'gbk_cntest': binascii.hexlify('中文测试'.encode('gbk')).decode(),
    'gbk_mix': binascii.hexlify('中文abc'.encode('gbk')).decode(),
}
print('\n期望值: %s' % json.dumps(EXP, ensure_ascii=False))

print('\n== A. hex 组 ==')
for label, args, want in [
    ('A1 hex_encode text "AB" -> %s' % EXP['hex_ab'],
     {"action": "hex_encode", "input": "text", "data": "AB"}, EXP['hex_ab']),
    ('A2 hex_encode text "中文" -> %s' % EXP['hex_cn'],
     {"action": "hex_encode", "input": "text", "data": "中文"}, EXP['hex_cn']),
    ('A3 ★大小写判别 hex_encode base64 "qw==" -> %s' % EXP['hex_qw'],
     {"action": "hex_encode", "input": "base64", "data": "qw=="}, EXP['hex_qw']),
    ('A4 hex_encode base64 "3q2+7w==" -> %s' % EXP['hex_dead'],
     {"action": "hex_encode", "input": "base64", "data": "3q2+7w=="}, EXP['hex_dead']),
]:
    e, t = call("browser_codec", args)
    rec(label, (not e) and (want in t.lower()), t[:220])

print('\n== B. GBK 组 ==')
for label, args, want in [
    ('B1 gbk_encode "中文" output=hex -> %s' % EXP['gbk_cn'],
     {"action": "gbk_encode", "data": "中文", "output": "hex"}, EXP['gbk_cn']),
    ('B2 gbk_decode input=hex "D6D0CEC4" -> 中文',
     {"action": "gbk_decode", "input": "hex", "data": "D6D0CEC4"}, '中文'),
    ('B3 gbk_encode "中文测试" -> %s' % EXP['gbk_cntest'],
     {"action": "gbk_encode", "data": "中文测试", "output": "hex"}, EXP['gbk_cntest']),
    ('B7 ★真实痛点 gbk_decode base64 -> <title>中文测试</title>',
     {"action": "gbk_decode", "input": "base64",
      "data": "PHRpdGxlPtbQzsSy4srUPC90aXRsZT4="}, '<title>中文测试</title>'),
    ('B9 gbk_encode "AB" -> 4142',
     {"action": "gbk_encode", "data": "AB", "output": "hex"}, '4142'),
    ('B10 gbk_encode "中文abc" -> %s' % EXP['gbk_mix'],
     {"action": "gbk_encode", "data": "中文abc", "output": "hex"}, EXP['gbk_mix']),
]:
    e, t = call("browser_codec", args)
    rec(label, (not e) and (want.lower() in t.lower()), t[:240])

print('\n== B11 \\0 陷阱: 输出长度必须恰好 8 个 hex 字符 ==')
e, t = call("browser_codec", {"action": "gbk_encode", "data": "中文", "output": "hex"})
hexs = ''.join(ch for ch in t if ch.lower() in '0123456789abcdef')
rec('B11 gbk_encode("中文") 无尾部 00(长度 8)', (not e) and (len(hexs) == 8), t[:200])

print('\n== C. 时间组 ==')
e, t = call("browser_time_convert", {"action": "now"})
print('   now: %s' % t[:240])
now_epoch = int(time.time())
if not e:
    import re
    m = re.search(r'(1[6-9]\d{8}|2\d{9})', t)
    rec('C1 action=now 的秒级时间戳与本机真实时间差 <= 2s',
        bool(m) and abs(int(m.group(1)) - now_epoch) <= 2,
        '工具=%s 本机=%d' % (m.group(1) if m else '?', now_epoch))
else:
    rec('C1 action=now', False, t[:200])

for label, args, want in [
    ('C4 ts=0 -> 1970-01-01 08:00:00(UTC+8)',
     {"action": "to_time", "timestamp": 0}, '1970-01-01 08:00:00'),
    ('C5 ts=1700000000 -> 2023-11-15 06:13:20',
     {"action": "to_time", "timestamp": 1700000000}, '2023-11-15 06:13:20'),
    ('C6 ts=1234567890 -> 2009-02-14 07:31:30',
     {"action": "to_time", "timestamp": 1234567890}, '2009-02-14 07:31:30'),
    ('C7 ts=2147483647 -> 2038-01-19 11:14:07',
     {"action": "to_time", "timestamp": 2147483647}, '2038-01-19 11:14:07'),
]:
    e, t = call("browser_time_convert", args)
    rec(label, (not e) and (want in t), t[:220])

e, t = call("browser_time_convert", {"action": "to_time", "timestamp": 2147483648})
rec('C8 ts=2147483648(int32 溢出) 必须显式报 2038 错而不是给错时间',
    e and ('2038' in t or '溢出' in t or '超出' in t), t[:240])

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
