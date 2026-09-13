# -*- coding: utf-8 -*-
"""验收"用户标识通路": browser_create{tag} -> browser_user_tags 列出 -> browser_find_by_tag 查到。

判据:
 ① 给 tag 创建浏览器 -> 成功
 ② browser_user_tags 必须列出该标识(在此之前本机只有空标识)
 ③ **核心**: browser_find_by_tag {tag} 必须**查到**(该工具此前在本 MCP 内不可能成功)
 ④ **对照(防假阳性)**: 查一个不存在的 tag 必须仍然失败 —— 否则③的"查到"可能只是工具恒返回成功
 ⑤ 不传 tag 创建 -> 新浏览器不应继承上一个标识(防泄漏)
 收尾: 关掉测试创建的浏览器
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
TAG = "mcpTagProbe"
res = []


def call(name, args, timeout=60):
    t0 = time.time()
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def unesc(t):
    return t.replace('\\"', '"')


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-48s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:82]))


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?tagprobe=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① 带 tag 创建后台浏览器 ==")
e, t, dt = call("browser_create",
                {"url": "https://example.com/?tagged=1", "background": True, "tag": TAG}, 90)
print("   isError=%s %s" % (e, t[:230]))
rec("带 tag 创建成功", not e, t[:86])

print("\n== ② browser_user_tags 必须列出该标识 ==")
e, t, _ = call("browser_user_tags", {}, 45)
print("   %s" % t[:300])
rec("列出该标识", TAG in t, t[:86])

print("\n== ③ 核心: browser_find_by_tag 必须查到(此前不可能成功) ==")
e, t, _ = call("browser_find_by_tag", {"tag": TAG}, 45)
print("   isError=%s %s" % (e, t[:300]))
u = unesc(t)
found_id = None
m = re.search(r'"id"\s*:\s*(\d+)', u)
if m:
    found_id = int(m.group(1))
rec("按标识查到了浏览器", not e, t[:86])
print("   查到的 browser_id = %s" % found_id)

print("\n== ④ 对照: 不存在的 tag 必须仍然失败 ==")
e2, t2, _ = call("browser_find_by_tag", {"tag": "mcpNoSuchTag_zzz"}, 45)
print("   isError=%s %s" % (e2, t2[:200]))
rec("不存在的 tag 仍失败(非假阳性)", e2, t2[:86])

print("\n== ⑤ 不传 tag 创建 -> 不应继承上一个标识 ==")
e3, t3, _ = call("browser_create", {"url": "https://example.com/?notag=1",
                                    "background": True}, 90)
print("   isError=%s %s" % (e3, t3[:180]))
e4, t4, _ = call("browser_user_tags", {}, 45)
print("   tags: %s" % t4[:220])
u4 = unesc(t4)
# 应有恰好一个带 TAG 的浏览器(第二次创建不该也叫 mcpTagProbe)
n_tag = u4.count(TAG)
rec("标识未泄漏给新浏览器(仍只有 1 个该标识)", n_tag == 1, "出现 %d 次" % n_tag)

print("\n== 收尾: 关掉测试用浏览器 ==")
e5, t5, _ = call("browser_list", {}, 45)
print("   列表: %s" % t5[:300])
for bid in re.findall(r'"id"\s*:\s*(\d+)', unesc(t5)):
    if int(bid) != 1:
        call("browser_close", {"browser_id": int(bid)}, 45)
        print("   已关闭 browser_id=%s" % bid)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
