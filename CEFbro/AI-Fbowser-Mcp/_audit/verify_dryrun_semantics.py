# -*- coding: utf-8 -*-
"""验证 `browser_reverse_patch` 的 dry_run 语义在第 69 轮读取器修好后是否**真的按文档生效**。

## 为什么要专门验证
`dry_run = yyjson取逻辑_默认 (参数JSON, "dry_run", 假)`。读取器缺键被当成真时, 该工具恒走"只验证不替换",
即**用户以为改了、其实没改**(文档默认 false=真替换)。这是"静默假成功"的反向版本, 危害同样大。
修好后默认值才生效, 所以必须**两个方向都测**:
  ① `dry_run:true`  → 期望提示 "dryRun 通过(新源码可编译, 未实际替换)";
  ② 省略 dry_run    → 期望提示 "脚本已热替换(对后续调用生效)"。
判定依据是**工具自己的提示文本**(它由 选择(ptDry,...) 生成), 因此这条正好验证读取器到默认值的整条链路。

## 安全措施(为什么这样不会搞坏环境)
- 全程在一个**一次性页面**(about:blank + document.write 注入的小脚本)上做, 用完冷重启;
- 替换用的源码是**合法且极简**的 `var mcpPatchProbe=1;`, 不是占位垃圾串 —— 即便替换成功, 也不会
  把页面脚本改成语法残缺的东西(CDP 对非法源码会拒绝并返回编译错误, 但没必要去踩);
- 该工具已加入 `mass_probe.MUTATING_SKIP`, 避免将来被批量探针用占位源码误触发。
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
res = []


def call(name, args, timeout=30):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:95]))


def restart():
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
            return True
        except Exception:
            pass
    return False


if not restart():
    print("启动失败"); sys.exit(2)

# 一次性页面: 注入一个可被注册的小脚本
call("browser_navigate", {"url": "about:blank", "wait_for_load": True}, 30)
time.sleep(0.4)
call("browser_debugger_enable", {})
WRITE = ("document.write('<html><body><script>window.__patchA=1;</script>"
         "<script>window.__patchB=2;</script></body></html>');document.close();'wrote'")
e, t, _ = call("browser_execute_js", {"code": WRITE}, 30)
rec("一次性页面注入两个小脚本", not e, t.replace("\n", " ")[:60])
time.sleep(0.6)

e, t, _ = call("browser_reverse_search_script", {"action": "list"}, 30)
ids = re.findall(r'\\"scriptId\\":\\"(\d+)\\"', t) or re.findall(r'"scriptId":"(\d+)"', t)
print("  已注册 scriptId: %s" % ids)
sid = ids[-1] if ids else ""
if not sid:
    print("  !! 没拿到 scriptId, 无法继续(如实记录)"); restart(); sys.exit(0)

GOOD_SRC = "var mcpPatchProbe=1;"

print("\n== (1) dry_run:true 应「只验证不替换」 ==")
e, t, dt = call("browser_reverse_patch",
                {"source": GOOD_SRC, "script_id": sid, "dry_run": True}, 30)
rec("dry_run:true 调用成功", not e, t.replace("\n", " ")[:110])
rec("提示语为 未实际替换", "未实际替换" in t, t.replace("\n", " ")[:110])

print("\n== (2) 省略 dry_run(文档默认 false) 应「真替换」 ==")
e, t, dt = call("browser_reverse_patch", {"source": GOOD_SRC, "script_id": sid}, 30)
rec("省略 dry_run 调用成功(源码合法)", not e, t.replace("\n", " ")[:110])
rec("提示语为 已热替换(证明默认值不再是真)", "已热替换" in t, t.replace("\n", " ")[:110])

print("\n== ③ 对照: 显式 dry_run:false 应与省略时一致 ==")
e, t, dt = call("browser_reverse_patch",
                {"source": GOOD_SRC, "script_id": sid, "dry_run": False}, 30)
rec("dry_run:false 提示语亦为 已热替换", "已热替换" in t, t.replace("\n", " ")[:110])

print("\n== ④ 副作用核对: 页面与 CDP 通道仍健康 ==")
e, t, dt = call("browser_execute_js", {"code": "String(typeof mcpPatchProbe)"}, 30)
rec("execute_js 仍可用", (not e) and dt < 3.0, "%.2fs | %s" % (dt, t.replace("\n", " ")[:60]))

print("\n== 收尾: 冷重启(丢弃一次性页面) ==")
restart()
e, t, dt = call("browser_execute_js", {"code": "1+1"})
rec("收尾重启后可用", not e, "%.2fs" % dt)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
