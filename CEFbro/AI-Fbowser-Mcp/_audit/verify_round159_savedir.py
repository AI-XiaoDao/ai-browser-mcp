# -*- coding: utf-8 -*-
r"""第159轮: browser_start_download save_dir 联动验收(文件落地回读 oracle)。

判据:
  ① 基线健康; 建自定义保存目录
  ② start_download {url, save_dir} → 成功且回执含该目录
  ③ 轮询 ≤15s: 自定义目录出现文件(事件侧消费覆盖的证据; 默认目录是 运行目录\Downloads)
  ④ 守卫: save_dir 路径遍历 → 拒绝; url 协议非法 → 拒绝
  ⑤ 全程 CDP 健康; 收尾 status
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []
TS = int(time.time())
DL_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "_tmp_dl_%d" % TS))
os.makedirs(DL_DIR, exist_ok=True)


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-58s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r159dl=%d" % TS})
health('①execute_js 快')

print('\n== ② 触发下载(自定义目录) ==')
e, t, d = call("browser_start_download",
               {"url": "https://example.com/", "save_dir": DL_DIR}, to=60)
# 回包文本里反斜杠被 JSON 转义成 \\ (所有消息同此行为), 断言前归一
rec('②start_download 成功且回执含自定义目录', (not e) and (DL_DIR.replace("\\", "\\\\") in t), "%.2fs %s" % (d, t[:90]))

print('\n== ③ 事件侧消费: 文件落进自定义目录 ==')
landed = []
for _ in range(15):
    landed = [f for f in os.listdir(DL_DIR) if not f.endswith('.crdownload') and not f.endswith('.tmp')]
    if landed:
        break
    time.sleep(1.0)
rec('③自定义目录出现文件(联动生效)', len(landed) > 0, landed[:3])
health('③之后 execute_js 仍快')

print('\n== ④ 守卫 ==')
e, t, d = call("browser_start_download",
               {"url": "https://example.com/", "save_dir": "..\\..\\Windows"}, to=60)
rec('④save_dir 路径遍历 → 拒绝', e and ("save_dir" in t), t[:80])
e, t, d = call("browser_start_download", {"url": "ftp://example.com/x"}, to=60)
rec('④ftp 协议 → 拒绝', e and ("http" in t), t[:80])

print('\n== ⑤ 收尾 ==')
health('⑤收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑤browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
