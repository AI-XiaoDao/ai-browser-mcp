# -*- coding: utf-8 -*-
"""VIP P0 决定性验收: 插件 content_scripts.js 到底会不会执行?

判据(与命名无关, 只看页面真值):
  ① 负对照: 装插件**之前**导航 -> 页面无插件标记(否则说明测量方式本身就错)
  ② `browser_vip_load_extension {path: <已解压目录>}` -> 回包 mode=unpacked 且 advanced_enabled 如实
  ③ 装完 reload -> `document.documentElement.dataset.mcpExt` 出现 => content script **真的执行了**
     (类库原文: 默认 CEF **不支持** content_scripts, 必须启用插件高级功能后才支持 ——
      所以这一条同时验证了 P0 开关与新工具)
  ④ 反证: 用 browser_execute_js 读标记, 读不到就给原文, 不猜
"""
import json
import os
import shutil
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, '_audit', 'test_extension')
R = []


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
                                            if i.get("type") == "text").replace('\\"', '"')


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:340]) if detail else ''))


# ── 造一个最小解压插件: content script 给 <html> 打标记并改标题 ──
shutil.rmtree(EXT, ignore_errors=True)
os.makedirs(EXT, exist_ok=True)
manifest = {
    "manifest_version": 3,
    "name": "MCP Content Script Probe",
    "version": "1.0",
    "content_scripts": [{
        "matches": ["<all_urls>"],
        "js": ["content.js"],
        "run_at": "document_idle",
        "all_frames": True,
    }],
}
open(os.path.join(EXT, 'manifest.json'), 'w', encoding='utf-8').write(
    json.dumps(manifest, ensure_ascii=False, indent=2))
open(os.path.join(EXT, 'content.js'), 'w', encoding='utf-8').write(
    "document.documentElement.setAttribute('data-mcp-ext','yes');\n"
    "document.title = 'MCP-EXT-CONTENT-SCRIPT-RAN';\n")
print('测试插件已生成: %s' % EXT)
print('   manifest.json / content.js -> 给 <html> 打 data-mcp-ext=yes 并改标题')

MARK = "(document.documentElement.getAttribute('data-mcp-ext')||'__NONE__')"

# ① 负对照
call("browser_navigate", {"url": "https://example.com/?extprobe=before", "wait_for_load": True})
time.sleep(0.6)
e, t = call("browser_execute_js", {"code": MARK})
print('   装插件前标记: %s' % t[:160])
rec('负对照: 装插件前页面无标记(证明测量有效)', (not e) and '__NONE__' in t, t[:200])

# ② 加载解压插件
e, t = call("browser_vip_load_extension", {"path": EXT}, 60)
print('   load_extension 回包: isError=%s %s' % (e, t[:300]))
rec('解压目录加载被接受(mode=unpacked)', (not e) and 'mode=unpacked' in t, t[:300])
rec('回包如实回报 advanced_enabled=true', 'advanced_enabled=true' in t, t[:300])

# ③ 装完刷新 -> content script 应当执行
time.sleep(2.0)
call("browser_reload", {"ignore_cache": True}, 60)
time.sleep(2.5)
e, t = call("browser_execute_js", {"code": MARK}, 60)
print('   装插件后标记: %s' % t[:200])
rec('★content script 真的执行了(data-mcp-ext=yes)', (not e) and 'yes' in t, t[:200])
e2, t2 = call("browser_execute_js", {"code": "document.title"}, 60)
print('   标题: %s' % t2[:200])
rec('标题被内容脚本改写', (not e2) and 'MCP-EXT-CONTENT-SCRIPT-RAN' in t2, t2[:200])

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
