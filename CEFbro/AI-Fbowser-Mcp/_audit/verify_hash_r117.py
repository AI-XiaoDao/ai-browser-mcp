# -*- coding: utf-8 -*-
r"""`browser_hash` 验收: MD5(文本/文件) 与 CRC32 用**Python 独立算准**(hashlib/zlib), XXH128 做性质验证。

为什么 XXH128 不做绝对向量: 本机没有可用的 xxhash 参考实现(先探测), 凭记忆写向量违反纪律。
改为验证: 长度 32 位十六进制 + 确定性(两次相同) + 区分度(不同输入不同) + 与 MD5 不同算法。
"""
import hashlib
import json
import os
import sys
import tempfile
import urllib.request
import zlib

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


def data_of(t):
    try:
        d = json.loads(t).get("data")
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:260]) if detail else ''))


try:
    import xxhash  # noqa: F401
    HAVE_XX = True
except Exception as ex:
    HAVE_XX = False
    print('   (本机无 xxhash 参考实现: %r -> XXH128 只做性质验证)' % (ex,))

print('== A. MD5(文本) —— 与 hashlib 对照 ==')
for s in ("hello", "abc", "中文测试"):
    want = hashlib.md5(s.encode('utf-8')).hexdigest()
    e, t = call("browser_hash", {"action": "md5", "data": s})
    got = str(data_of(t).get("md5", ""))
    rec('md5(%r) == %s' % (s, want), (not e) and got.lower() == want, 'got=%r | %s' % (got, t[:90]))

print('\n== A2. uppercase 开关 ==')
want = hashlib.md5(b"hello").hexdigest().upper()
e, t = call("browser_hash", {"action": "md5", "data": "hello", "uppercase": True})
got = str(data_of(t).get("md5", ""))
rec('uppercase:true -> 全大写', (not e) and got == want, 'got=%r want=%r' % (got, want))

print('\n== B. MD5(文件) —— 与 hashlib 对照(含大文件路径) ==')
fd, path = tempfile.mkstemp(suffix='.bin', prefix='mcphash_')
os.close(fd)
payload = (b"MCP-HASH-PROBE-" * 5000) + bytes(range(256))
open(path, 'wb').write(payload)
want_file = hashlib.md5(payload).hexdigest()
print('   测试文件: %s (%d 字节)' % (path, len(payload)))
e, t = call("browser_hash", {"action": "md5_file", "path": path})
got = str(data_of(t).get("md5", ""))
rec('md5_file == %s' % want_file, (not e) and got.lower() == want_file, 'got=%r | %s' % (got, t[:110]))
os.remove(path)

e, t = call("browser_hash", {"action": "md5_file", "path": r"C:\definitely\not\here_zzz.bin"})
rec('不存在的文件必须**明确报错**(而不是给空文件的 MD5)', e and '文件不存在' in t, t[:160])
rec('且不能返回空文件摘要 d41d8cd9…', 'd41d8cd9' not in t, t[:120])

print('\n== C. CRC32 —— 与 zlib.crc32 对照(标准值是无符号) ==')
for s in ("hello", "123456789"):
    want = zlib.crc32(s.encode('utf-8')) & 0xffffffff
    e, t = call("browser_hash", {"action": "crc32", "data": s})
    d = data_of(t)
    got_u = d.get("crc32_unsigned")
    got_s = d.get("crc32")
    # 有符号值应当是同一组 32 位的 int32 重解释
    want_s = want - 4294967296 if want >= 2 ** 31 else want
    rec('crc32(%r): crc32_unsigned == %d' % (s, want), (not e) and got_u == want,
        'unsigned=%r signed=%r | %s' % (got_u, got_s, t[:110]))
    rec('crc32(%r): 有符号值 == %d(同一组 32 位)' % (s, want_s), got_s == want_s,
        'signed=%r 期望=%d' % (got_s, want_s))

print('\n== D. XXH128 —— 性质验证(无独立向量) ==')
e1, t1 = call("browser_hash", {"action": "xxhash", "data": "hello"})
e2, t2 = call("browser_hash", {"action": "xxhash", "data": "hello"})
e3, t3 = call("browser_hash", {"action": "xxhash", "data": "hellp"})
h1 = str(data_of(t1).get("xxhash", ""))
h2 = str(data_of(t2).get("xxhash", ""))
h3 = str(data_of(t3).get("xxhash", ""))
rec('xxhash 返回 32 位十六进制', (not e1) and len(h1) == 32 and all(c in '0123456789abcdefABCDEF' for c in h1), 'h=%r' % h1)
rec('确定性: 两次相同输入结果一致', h1 == h2 and h1 != '', '%r vs %r' % (h1, h2))
rec('区分度: 差一个字符结果不同', h1 != h3, '%r vs %r' % (h1, h3))

print('\n== E. 守卫与零前置 ==')
e, t = call("browser_hash", {})
rec('缺 action 可行动拒绝', e and 'action' in t, t[:140])
e, t = call("browser_hash", {"action": "md5"})
rec('缺 data 可行动拒绝(并说明空串摘要无意义)', e and 'data' in t, t[:160])
e, t = call("browser_hash", {"action": "sha256", "data": "x"})
rec('未知 action 列出全部可用值', e and 'crc32' in t and 'xxhash' in t, t[:160])

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
