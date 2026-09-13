# -*- coding: utf-8 -*-
"""查 URI 编解码的**真实语义**(不只看 success):
类库签名把 unescape_rule 声明成逻辑型, 注释却说它是"URI保留规则. 位标识操作"。
现实现固定传 真 —— 若 真 转换成正整数 -1(全位), 可能意味着"全部保留" => 解码根本不生效。
判据: encode("a b") 是否得 "a%20b"; decode("a%20b") 是否得 "a b"。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a, to=60):
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


CASES = [
    ("browser_uri_encode", {"data": "a b&c=d"}, "a%20b%26c%3Dd", "空格应编码为 %20"),
    ("browser_uri_encode", {"data": "中文 x"}, None, "非ASCII也编码"),
    ("browser_uri_decode", {"data": "a%20b%26c%3Dd"}, "a b&c=d", "应还原为空格与 & ="),
    ("browser_uri_decode", {"data": "%E4%B8%AD%E6%96%87"}, "中文", "UTF-8 百分号还原"),
    ("browser_uri_decode", {"data": "a+b"}, "a b", "+ 是否视为空格(取决于规则)"),
]

for name, args, expect, why in CASES:
    e, t = call(name, args)
    print('%-22s %-28s -> isError=%s %s' % (name, json.dumps(args, ensure_ascii=False),
                                            e, t.replace('\\"', '"')[:150]))
    print('      (%s; 期望 %r)' % (why, expect))
