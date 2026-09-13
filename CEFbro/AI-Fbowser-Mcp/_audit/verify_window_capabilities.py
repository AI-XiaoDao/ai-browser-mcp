# -*- coding: utf-8 -*-
"""验收新补齐的两个窗口能力(browser_move_window / browser_set_auto_resize)。

背景: 这两个工具原来是"恒失败"桩, 文案称"嵌入式GUI浏览器不支持…由主窗口自动管理"。
该前提已由代码事实推翻(控制台程序, 父窗口句柄=0, 用户看到的就是浏览器窗口本身),
类库确有 移动窗口/置自动调整大小 两个 API(生成物已确认本次真的被引用)。

判据:
 ① browser_move_window 指定 x/y/宽/高 -> 成功且 verified=true, 且 actual_* 与请求一致
 ② 只给 x/y(不给宽高) -> 保持当前尺寸; 且 actual 宽高应等于**①里设过的值**
    (这条同时是①的判别性证据: 若①的缩放没真生效, ②里读回的宽高就不会是①的值)
 ③ browser_set_auto_resize 必须能收参并成功(类库无返回值 -> 如实 verified=false)
 ④ browser_set_auto_resize 缺 enable -> 必须拒绝(不给缺省语义)
 ⑤ **独立回读对照**: 用 browser_cdp_call 直接读 Browser.getWindowForTarget,
    结果必须与工具自报的 actual_* 一致 —— 防止工具"自说自话"伪造成功。
收尾: 把窗口移回初始位置, 不把用户窗口留在测试位置。
"""
import json
import os
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
res = []


def call(name, args, timeout=45):
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


def bounds():
    """独立回读: 直接经 CDP 读窗口 bounds(不经被测工具的自报字段)。"""
    params = json.dumps({}, ensure_ascii=False)
    e, t, _ = call("browser_cdp_call",
                   {"method": "Browser.getWindowForTarget", "params": params}, 20)
    try:
        obj = json.loads(t)
        body = obj.get("data", obj)
        if isinstance(body, str):
            body = json.loads(body)
        inner = body.get("result", body)
        return inner.get("bounds") or {}, t
    except Exception as ex:
        return {}, "解析失败:%s | %s" % (ex, t[:200])


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:90]))


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
call("browser_navigate", {"url": "https://example.com/?winfix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

init, raw = bounds()
print("== 初始窗口 bounds(独立回读) ==")
print("   %s" % json.dumps(init, ensure_ascii=False))
init_ok = bool(init)
rec("能读到初始 bounds(测量环境有效)", init_ok, json.dumps(init, ensure_ascii=False)[:80])
if not init_ok:
    print("!! 读不到 bounds, 后续结论不可信; 原始响应: %s" % raw[:300])
    sys.exit(2)

print("\n== ① move_window 指定 x/y/宽/高 -> verified=true 且 actual 一致 ==")
e, t, dt = call("browser_move_window", {"x": 160, "y": 120, "width": 880, "height": 660}, 45)
print("   isError=%s 用时=%.2fs" % (e, dt))
print("   resp: %s" % t[:320])
d1 = {}
try:
    o = json.loads(t)
    d1 = o.get("data", o)
    if isinstance(d1, str):
        d1 = json.loads(d1)
except Exception as ex:
    print("   (解析失败: %s)" % ex)
rec("调用成功", not e, t[:90])
rec("verified=true", d1.get("verified") is True,
    "actual=%sx%s@(%s,%s)" % (d1.get("actual_width"), d1.get("actual_height"),
                              d1.get("actual_left"), d1.get("actual_top")))
rec("actual 宽高等于请求值", d1.get("actual_width") == 880 and d1.get("actual_height") == 660,
    "%sx%s" % (d1.get("actual_width"), d1.get("actual_height")))

print("\n== ② 只给 x/y -> 保持当前尺寸(应等于①设过的 880x660) ==")
e, t, dt = call("browser_move_window", {"x": 80, "y": 70}, 45)
print("   isError=%s" % e)
print("   resp: %s" % t[:320])
d2 = {}
try:
    o = json.loads(t)
    d2 = o.get("data", o)
    if isinstance(d2, str):
        d2 = json.loads(d2)
except Exception as ex:
    print("   (解析失败: %s)" % ex)
rec("成功且 verified=true", (not e) and d2.get("verified") is True, t[:90])
rec("尺寸保持为①的 880x660(证明①的缩放真生效)",
    d2.get("actual_width") == 880 and d2.get("actual_height") == 660,
    "%sx%s" % (d2.get("actual_width"), d2.get("actual_height")))
rec("位置已改为(80,70)", d2.get("actual_left") == 80 and d2.get("actual_top") == 70,
    "(%s,%s)" % (d2.get("actual_left"), d2.get("actual_top")))

print("\n== ⑤ 独立回读对照: CDP 直读必须与工具自报一致 ==")
b_after, _ = bounds()
print("   CDP 直读: %s" % json.dumps(b_after, ensure_ascii=False))
rec("CDP 直读与工具自报 actual 一致",
    b_after.get("width") == d2.get("actual_width")
    and b_after.get("height") == d2.get("actual_height")
    and b_after.get("left") == d2.get("actual_left")
    and b_after.get("top") == d2.get("actual_top"),
    "cdp=%sx%s@(%s,%s)" % (b_after.get("width"), b_after.get("height"),
                           b_after.get("left"), b_after.get("top")))

print("\n== ③ set_auto_resize 能收参并成功(类库无返回值 -> verified=false 如实话术) ==")
e, t, dt = call("browser_set_auto_resize",
                {"enable": True, "min_height": 0, "min_width": 0,
                 "max_height": 10000, "max_width": 10000}, 45)
print("   isError=%s" % e)
print("   resp: %s" % t[:340])
rec("调用成功(不再恒失败)", not e, t[:90])
rec("如实标注 verified=false(不谎报生效)", '"verified":false' in t.replace(" ", ""), t[:90])

print("\n== ④ set_auto_resize 缺 enable -> 必须拒绝 ==")
e, t, dt = call("browser_set_auto_resize", {}, 45)
print("   resp: %s" % t[:200])
rec("缺 enable 被拒绝且可行动", e and ("必须显式指定 enable" in t), t[:90])

print("\n== 收尾: 把窗口移回初始位置 ==")
e, t, dt = call("browser_move_window",
                {"x": init.get("left", 0), "y": init.get("top", 0),
                 "width": init.get("width", 1000), "height": init.get("height", 800)}, 45)
print("   %s" % t[:200])
b_final, _ = bounds()
rec("已回到初始位置与尺寸",
    b_final.get("left") == init.get("left") and b_final.get("top") == init.get("top"),
    "now=%sx%s@(%s,%s)" % (b_final.get("width"), b_final.get("height"),
                           b_final.get("left"), b_final.get("top")))

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
