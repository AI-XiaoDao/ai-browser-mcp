# -*- coding: utf-8 -*-
"""测量"更新已存 JSON 时键被重复追加"这一根因的影响半径。

根因(已由类库源码确认):
  加入整数成员/加入文本成员 -> yyjson_mut_obj_add_* , 语义是"在尾部加入**新的**成员",
  **不覆盖**同名键。而本项目大量使用
      obj.创建自文本(已存JSON);  obj.加入X成员("_phase", 新值);  存储(obj.到可读文本())
  于是对象里出现两个同名键, 读取时拿到**第一个(旧值)** -> 状态机永远推进不了。

browser_scrape 已实测: 每轮轮询 db_async_results +2, 阶段永远停在 phase=2, 最终超时报错。
本脚本用**同模式的其它工具**做交叉验证(若同因, 它们也应"立刻可满足却超时"):
  browser_wait    用 _check_task_id 更新(同模式)
"""
import importlib.util
import json
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("v4", "verify_round4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

BASE = "http://127.0.0.1:9222"
URL = "https://example.com/"


def health():
    return json.loads(urllib.request.urlopen(BASE + "/health", timeout=10).read())


def run(tag, tool, args, budget=30):
    h0 = health()["db_async_results"]
    t0 = time.time()
    e, t, _ = v4.call(tool, args, timeout=budget + 40)
    print("  %-26s err=%-5s %.1fs | %s" % (tag, e, time.time() - t0, t[:150].replace("\n", " ")))
    # 若返回的是异步信封, 轮询几轮看是否推进
    tid = None
    try:
        import re
        m = re.search(r"task_\d+_\d+_\d+", t)
        tid = m.group(0) if m else None
    except Exception:
        pass
    if tid and ("_waiting" in t or "_async" in t):
        for k in range(4):
            time.sleep(1.5)
            e2, t2, _ = v4.call("mcp_result", {"request_id": tid}, 40)
            print("      轮询%d: %s" % (k + 1, t2.replace("\n", " ")[:130]))
            if ("超时" in t2) or ("失败" in t2 and "_waiting" not in t2):
                break
    h1 = health()["db_async_results"]
    print("      db_async_results: %d -> %d (+%d)" % (h0, h1, h1 - h0))


v4.call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
time.sleep(1.0)
print("页面就绪, h1 存在 = %r" % v4.call("browser_fill_exists", {"selector": "h1"})[1][:20])
print()

print("== browser_wait: 等 h1(页面上立即存在), what=selector value=h1 max_ms=6000 ==")
run("browser_wait selector h1", "browser_wait",
    {"what": "selector", "value": "h1", "max_ms": 6000}, budget=30)

print("\n== browser_wait: 等一个永不存在(对照) ==")
run("browser_wait selector #nope", "browser_wait",
    {"what": "selector", "value": "#nope-xyz", "max_ms": 5000}, budget=30)

print("\n== browser_wait: timeout=3s (不做条件检查, 纯计时) ==")
run("browser_wait timeout 3000", "browser_wait",
    {"what": "timeout", "value": "3000", "max_ms": 8000}, budget=30)
