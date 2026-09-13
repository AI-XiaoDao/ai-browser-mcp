# -*- coding: utf-8 -*-
"""`browser_codec` / `browser_time_convert` 验收(修正版)。

上一版 8 处失败**全是我的探针写错**(不是产品缺陷), 已按**实测 schema 与回包**改正:
  · 时间工具的动作名是 `ts_to_text`(我写成 `to_time`), 本地时间在 `data.local`;
  · B11 原来把整段回包里的十六进制字符都数了(连 `bytes`/`timestamp` 的数字也数进去),
    改为**只取 `data.output` 字段**再判长度;
  · `text_to_ts` 的 `chinese` 语义按类库: 中文顺序(年在前)=true(默认), 月/日在前才传 false。
A3/A4 保持原判据 —— 它们是**真缺陷**的判别点(编码方向原先忽略 input), 已修。
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


def call(n, a=None, to=90):
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


def data_of(txt):
    """把回包里的 data 对象取出来(字段都在 data.* 下)。"""
    try:
        j = json.loads(txt)
        d = j.get("data")
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {}


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:280]) if detail else ''))


EXP = {
    'hex_ab': binascii.hexlify(b'AB').decode(),
    'hex_cn': binascii.hexlify('中文'.encode('utf-8')).decode(),
    'hex_qw': binascii.hexlify(base64.b64decode('qw==')).decode(),
    'hex_dead': binascii.hexlify(base64.b64decode('3q2+7w==')).decode(),
    'gbk_cn': binascii.hexlify('中文'.encode('gbk')).decode(),
    'gbk_cntest': binascii.hexlify('中文测试'.encode('gbk')).decode(),
    'gbk_mix': binascii.hexlify('中文abc'.encode('gbk')).decode(),
}
print('独立算准的期望值: %s' % json.dumps(EXP, ensure_ascii=False))

print('\n== A. hex 组 ==')
for label, args, want in [
    ('A1 hex_encode text "AB" -> %s' % EXP['hex_ab'],
     {"action": "hex_encode", "input": "text", "data": "AB"}, EXP['hex_ab']),
    ('A2 hex_encode text "中文" -> %s' % EXP['hex_cn'],
     {"action": "hex_encode", "input": "text", "data": "中文"}, EXP['hex_cn']),
    ('A3 ★hex_encode base64 "qw==" -> %s(修前给的是原文 hex)' % EXP['hex_qw'],
     {"action": "hex_encode", "input": "base64", "data": "qw=="}, EXP['hex_qw']),
    ('A4 hex_encode base64 "3q2+7w==" -> %s' % EXP['hex_dead'],
     {"action": "hex_encode", "input": "base64", "data": "3q2+7w=="}, EXP['hex_dead']),
]:
    e, t = call("browser_codec", args)
    got = str(data_of(t).get("output", ""))
    rec(label, (not e) and got.lower() == want.lower(), 'output=%r | %s' % (got, t[:110]))

print('\n== A2b. hex 双向往返 ==')
e, t = call("browser_codec", {"action": "hex_decode", "input": "hex", "data": EXP['hex_cn']})
rec('hex_decode(%s) -> 中文' % EXP['hex_cn'], (not e) and data_of(t).get("output") == '中文',
    t[:160])

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
    got = str(data_of(t).get("output", ""))
    rec(label, (not e) and got.lower() == want.lower(), 'output=%r | %s' % (got, t[:110]))

print('\n== B11 \\0 陷阱: output 字段必须恰好 8 个十六进制字符 ==')
e, t = call("browser_codec", {"action": "gbk_encode", "data": "中文", "output": "hex"})
got = str(data_of(t).get("output", ""))
rec('B11 gbk_encode("中文") 无尾部 00', (not e) and got == 'd6d0cec4', 'output=%r' % got)

print('\n== C. 时间组(动作名 ts_to_text, 本地时间在 data.local) ==')
e, t = call("browser_time_convert", {"action": "now"})
d = data_of(t)
now_epoch = int(time.time())
rec('C1 action=now 秒级时间戳与本机真实时间差 <= 2s',
    (not e) and abs(int(d.get("timestamp_s", 0)) - now_epoch) <= 2,
    'timestamp_s=%s 本机=%d' % (d.get("timestamp_s"), now_epoch))
rec('C2 tz_offset_minutes = -480(UTC+8, 与独立实测一致)', d.get("tz_offset_minutes") == -480,
    'tz_offset_minutes=%s' % d.get("tz_offset_minutes"))

for label, ts, want in [
    ('C4 ts=0 -> 1970-01-01 08:00:00', 0, '1970-01-01 08:00:00'),
    ('C5 ts=1700000000 -> 2023-11-15 06:13:20', 1700000000, '2023-11-15 06:13:20'),
    ('C6 ts=1234567890 -> 2009-02-14 07:31:30', 1234567890, '2009-02-14 07:31:30'),
    ('C7 ts=2147483647 -> 2038-01-19 11:14:07', 2147483647, '2038-01-19 11:14:07'),
]:
    e, t = call("browser_time_convert", {"action": "ts_to_text", "timestamp": ts})
    rec(label, (not e) and data_of(t).get("local") == want,
        'local=%r | %s' % (data_of(t).get("local"), t[:110]))

e, t = call("browser_time_convert", {"action": "ts_to_text", "timestamp": 2147483648})
rec('C8 ts=2147483648(int32 上限外) 必须显式报错且可行动',
    e and ('2038' in t or 'unit=ms' in t), t[:200])

e, t = call("browser_time_convert", {"action": "text_to_ts", "time_text": "1970-01-01 08:00:00"})
rec('C9 text_to_ts 中文顺序解析 -> timestamp_s=0',
    (not e) and data_of(t).get("timestamp_s") == 0,
    'timestamp_s=%r | %s' % (data_of(t).get("timestamp_s"), t[:120]))

e, t = call("browser_time_convert", {"action": "ts_to_text", "timestamp": 1700000000,
                                     "format": "%Y/%m/%d %H:%M:%S"})
rec('C10 自定义 format 生效', (not e) and data_of(t).get("local") == '2023/11/15 06:13:20',
    'local=%r' % data_of(t).get("local"))

e, t = call("browser_time_convert", {"action": "text_to_ts", "time_text": "垃圾文本zzz"})
rec('C11 无法解析的文本必须报错(而不是给个错时间)', e and ('哨兵' in t or '解析' in t), t[:160])

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
