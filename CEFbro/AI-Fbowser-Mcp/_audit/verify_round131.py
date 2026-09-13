# -*- coding: utf-8 -*-
r"""验证第131轮: 全量扫描发现的 12 个工具 / 20 个"实现真读却未声明"的参数已补齐。

两层验证:
  ① **穷尽性**: 重跑 `_show_branch_params.py --brief`(全量 323 工具), **MISSING 必须为 0**
     —— 这条比逐条断言更有力: 它直接复用"发现问题的那把尺子"来证明问题消失;
  ② 行为层抽样: 挑三个新参数的**真实用途**各跑一次(能传、能生效):
     · `browser_navigate {async_only:true}` → 立刻回 task_id(不等载入);
     · `browser_console_eval {file:<临时 js>}` → 从文件读脚本执行(顺带规避 1MB 参数墙);
     · `mcp_help {name:"browser_navigate"}` → 单工具说明(此前该参数代理看不到)。

用法: py -3 _audit\verify_round131.py
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=90):
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


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


print('== ① 穷尽性: 重跑全量扫描, MISSING 必须为 0 ==')
p = subprocess.run([sys.executable, os.path.join(ROOT, '_audit', '_show_branch_params.py'), '--brief'],
                   cwd=os.path.join(ROOT, '_audit'), capture_output=True, text=True,
                   encoding='utf-8', errors='replace')
out = (p.stdout or '') + (p.stderr or '')
miss_lines = [ln for ln in out.splitlines() if 'MISSING=[' in ln]
tail = [ln for ln in out.splitlines() if ln.startswith('-- 扫描')]
print('   %s' % (tail[0] if tail else '(无汇总行)'))
for ln in miss_lines:
    print('   !! %s' % ln)
rec("全量 323 工具中已无 MISSING(实现读却未声明)", not miss_lines,
    "%d 条残留" % len(miss_lines))
rec("扫描确实覆盖了全部工具", bool(tail) and '323' in tail[0], tail[0] if tail else '-')

print('\n== ② 行为层抽样: 新参数的"真实用途"确实可用 ==')
e1, t1 = call("browser_navigate", {"url": "https://example.com/?asy=%d" % int(__import__('time').time()),
                                   "async_only": True})
# 注意: navigate 的 async_only 是"不等载入、立刻返回成功", **不返回 task_id**(第一版探针按异步工具想当然, 属探针错误)
rec("navigate async_only=true 立刻返回成功(且未等待载入)",
    (not e1) and ("已导航到" in t1) and ("load_end" not in t1), t1[:90])

fp = os.path.join(tempfile.gettempdir(), "mcp_ce_file_probe.js")
with open(fp, "w", encoding="utf-8") as f:
    f.write("'FILE_JS_OK'")
e2, t2 = call("browser_console_eval", {"file": fp})
rec("console_eval file= 从文件读脚本并执行", (not e2) and ("FILE_JS_OK" in t2), t2[:90])

e3, t3 = call("mcp_help", {"name": "browser_navigate"})
rec("mcp_help name= 返回单工具说明", (not e3) and len(t3) > 40, t3[:90])

TL = {t["name"]: t for t in json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())["tools"]}


def props(n):
    return set(((TL.get(n, {}).get("inputSchema") or {}).get("properties") or {}).keys())


rec("back/forward 声明了 wait_for_load 与 async_only",
    {"wait_for_load", "async_only"} <= props("browser_back") and {"wait_for_load", "async_only"} <= props("browser_forward"),
    sorted(props("browser_back")))
rec("intercept 声明了 width/height/x/y",
    {"width", "height", "x", "y"} <= props("browser_intercept"), sorted(props("browser_intercept")))
rec("file_dialog 声明了 file_path/path", {"file_path", "path"} <= props("browser_file_dialog"),
    sorted(props("browser_file_dialog")))
rec("instrument_script 声明了 verify", "verify" in props("browser_reverse_instrument_script"),
    sorted(props("browser_reverse_instrument_script")))

try:
    os.remove(fp)
except OSError:
    pass
bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
