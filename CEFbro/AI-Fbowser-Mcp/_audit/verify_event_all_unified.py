# -*- coding: utf-8 -*-
"""验收"三套全开/全关统一为同一 26 项集合"。

判据(用**另一个工具**的只读状态作为观测器, 避免自证):
  · browser_kernel_events_all action=get 会回报各开关真值(它读的是同一批静态字段);
  · 臂1: browser_collect action=event_all_enable  -> 观测器里 26 项应**全部为真**
  · 臂2: browser_collect action=event_all_disable -> 观测器里 26 项应**全部为假**
  · 臂3: browser_kernel_events_all action=enable  -> 再全真(与臂1 等价, 证明两套一致)
先取一次基线, 便于对照。
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

FIELDS = [
    "是否监控载入事件", "是否监控标题改变", "是否监控加载进度", "是否监控资源事件",
    "是否监控对话框", "是否监控全屏", "是否监控图标", "是否监控查找", "是否监控框架",
    "是否监控下载事件", "是否监控键盘焦点", "是否监控生命周期", "是否监控应用事件",
    "是否记录控制台", "是否记录网络", "是否详细记录网络",
    "是否监控菜单事件", "是否监控快捷菜单", "是否监控导航意图", "是否监控界面细节",
    "是否监控插件生命周期", "是否监控启动流程", "是否监控渲染细节", "是否监控WebSocket渲染",
    "是否监控许可提示", "是否监控离屏渲染",
]


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


def snapshot():
    """用 kernel 的 action=get 取开关状态(只读)。"""
    e, t = call("browser_kernel_events_all", {"action": "get"})
    if e:
        return None, t
    return t, None


print('== 基线 ==')
t, err = snapshot()
print('   %s' % (t or err)[:400])

print('\n== 臂1: browser_collect action=event_all_enable ==')
e, t = call("browser_collect", {"action": "event_all_enable"})
print('   回包: %s' % t[:260])
rec('回包声明 26 项且与内核一致', (not e) and ('26' in t), t[:260])
time.sleep(0.4)
t, err = snapshot()
print('   get: %s' % (t or err)[:400])
if t:
    off = [f for f in FIELDS if ('"%s":false' % f) in t or ('"%s": 0' % f) in t]
    on = [f for f in FIELDS if ('"%s":true' % f) in t]
    print('   观测: 真 %d / 假 %d' % (len(on), len(off)))
    rec('★collect 全开后 26 项全部为真(修前只有 11 项)', len(on) == 26, '假项: %s' % (off or '无'))

print('\n== 臂2: browser_collect action=event_all_disable ==')
e, t = call("browser_collect", {"action": "event_all_disable"})
print('   回包: %s' % t[:240])
rec('回包声明与 enable 逐项对称', (not e) and ('26' in t or '对称' in t), t[:240])
time.sleep(0.4)
t, err = snapshot()
print('   get: %s' % (t or err)[:400])
if t:
    on = [f for f in FIELDS if ('"%s":true' % f) in t]
    rec('★collect 全关后 26 项全部为假(修前会残留 13 项为真)', len(on) == 0, '仍为真的项: %s' % (on or '无'))

print('\n== 臂3: browser_kernel_events_all action=enable(与臂1 等价) ==')
e, t = call("browser_kernel_events_all", {"action": "enable"})
print('   回包: %s' % t[:240])
time.sleep(0.4)
t, err = snapshot()
if t:
    on = [f for f in FIELDS if ('"%s":true' % f) in t]
    rec('内核全开同样 26 项为真(两套集合一致)', len(on) == 26, '真项数=%d' % len(on))

# 收尾: 关掉, 免得多余事件入库
call("browser_collect", {"action": "event_all_disable"})

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
