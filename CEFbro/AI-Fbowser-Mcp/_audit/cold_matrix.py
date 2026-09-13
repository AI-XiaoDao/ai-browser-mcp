# -*- coding: utf-8 -*-
"""冷启动"一次调用成功"矩阵 —— 用户最新目标的度量工具。

用户要求: "所有功能 MCP 在 AI 代理软件上配置好后, 只要加载 MCP 就能一次非常稳定地调用成功,
不要出现很多次调用失败等多次尝试其他方法"。

与 mass_probe.py 的关键区别:
  · mass_probe 会**先预置一个页面**再探测(等于给了前置), 无法度量"零前置"体验;
    本脚本**先冷重启程序**(全新会话: 无任何前置调用), 然后每个工具**只调一次**。
  · 增加**前置缺失分类**(PREREQ): 错误文本里出现"请先/需先/未启用/is not enabled/必须先"等,
    这一类的数量就是本目标的**核心指标, 目标为 0**。

用法: py -3 cold_matrix.py            # 全量(约60-120秒)
      py -3 cold_matrix.py --keep     # 不重启, 直接测当前会话
      py -3 cold_matrix.py --limit 30 # 冒烟
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mass_probe as MP   # 复用 build_args / classify / LETHAL / MUTATING_SKIP
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
import _app_launch  # 调试期: 可见控制台窗口 + 应用自写 mcp_console.log

BASE = MP.BASE
EXE = os.path.join(os.path.dirname(HERE), '_int', 'AI-Fbowser-Mcp', 'debug', 'x64',
                   'linker', 'AI-Fbowser-Mcp.exe')
OUT = os.path.join(HERE, '_cold_matrix.json')

# 前置缺失特征: 这类失败 = "用户被迫先调别的工具/反复试错", 是本目标要清零的对象
# 注意: 不能把 "先 browser_xxx" 这类**建议措辞**算进来 —— 元素不存在的错误里常附
# "建议: 先用 browser_snapshot 确认元素存在", 那是行动建议而非前置要求, 曾被误判为 PREREQ。
PREREQ_RE = re.compile(
    r"请先|需先|必须先|先调用|先执行|未启用|is not enabled|前置|"
    r"需启用|尚未启用|未被启用|先设置|先下载|先添加")
# 本机能力缺失(可接受, 但必须给出替代方案)
CAP_RE = re.compile(r"本机|不支持|未实现|不存在|wasn't found|not supported|已禁用")
# 目标不存在/页面无此元素(可接受: 参数本身指向的目标不存在)
# 补充(实测): 本项目写工具找不到元素时的文案是"该选择器在当前页面上匹配到 0 个元素"
# 与 "element not found", 旧正则只认"不存在/未找到", 于这类失败会漏到后面被 PREREQ 的
# "需先"命中(来自尾部提示) —— 故一并补上。
TARGET_RE = re.compile(r"不存在|未找到|找不到|没有找到|无此|元素.*空|querySelector|"
                       r"未匹配|匹配不到|匹配到 0 个元素|element not found|为空|"
                       # 补充(第98轮): 内核对"目标资源不在缓存/已失效"的原话就是这两句,
                       # 属**目标不存在**而不是"未分类"。browser_network_body 传真 requestId
                       # 但该请求已被回收时即回第一句; heap get_object 传失效 object_id 回第二句。
                       r"No resource with given identifier|Object is not available")
# 无浏览器/无页面 (冷启动时本不该出现)
NOBROWSER_RE = re.compile(r"无浏览器|没有浏览器|浏览器.*未|主框架无效|无可用")

# 失败文案尾部的"建议/注意/替代"段是**行动建议**, 不是失败原因。
# 实测教训: `browser_fill_*` 的目标不存在文案尾部有"注意 iframe 内元素需先切换框架",
# 其中的"需先"被 PREREQ 正则命中 → 7 个"目标不存在"失败被误记成"缺前置",
# 让本目标最核心的指标(前置缺失类失败数)虚高。故分类前先剥掉这些提示段。
_HINT_HEAD_RE = re.compile(r"^\s*(建议|注意|提示|替代|可用替代|如仍要|如后续|下一步)")


def strip_hints(text):
    """剥掉 '|' 分隔的尾部提示段(建议/注意/替代…), 只留失败原因本身。"""
    keep = []
    for seg in (text or "").split("|"):
        if _HINT_HEAD_RE.match(seg):
            break
        keep.append(seg)
    return "|".join(keep)



def http_get(path, timeout=15):
    return json.loads(urllib.request.urlopen(BASE + path, timeout=timeout).read().decode())


def http_post(payload, timeout=40):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def cold_restart():
    """冷重启: 关掉程序再启动, 保证是全新会话(无任何前置调用/无缓存状态)。"""
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    _app_launch.launch_visible()
    for _ in range(60):
        time.sleep(1)
        try:
            h = http_get("/health", timeout=3)
            if h.get("tool_count"):
                print("  冷启动就绪: tools=%s cdp=%s" % (h.get("tool_count"), h.get("cdp_ready")))
                time.sleep(2)
                return h
        except Exception:
            pass
    return None


def alive(timeout=6):
    """活性探针(2025-09-13 重构): 双段判据, 兼顾"不误杀"与"通道真坏要能恢复"。
    ① 基线: browser_status 秒回(不碰渲染器, 绝不阻塞) → 服务在线。
    ② CDP 短探: execute_js max_ms=1500 —— 预算短, 应用侧等待/自救有界(不会像 4000ms 那样
       把协议锁占死 30 秒、把 /health 拖超时 → 误判死亡)。暂停/渲染器重启等**瞬时**状态会
       被应用侧 resume 自救恢复, 两次(间隔2秒)都失败才判"CDP 通道真坏" → 返回假(触发修复性
       冷重启, 这是**恢复**手段: 通道真坏时每个工具都白等 15~40 秒, 重启一次即复原)。
    教训(实测): 只用 browser_status 判活 → 通道坏时全量工具逐个超时, 一轮 334 跑 10 分钟还卡死;
       只用 execute_js 判活 → 渲染器繁忙时把锁占死 → health 超时 → 误杀闪退。两段结合才平衡。"""
    # ① 基线: browser_status 成功即服务在线
    try:
        r = http_post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "browser_status", "arguments": {}}}, 8)
        res = r.get("result") or {}
        txt = "".join((c.get("text") or "") for c in (res.get("content") or []))
        if (not res.get("isError")) and '"success":true' in txt:
            base_ok = True
        else:
            base_ok = False
    except Exception:
        base_ok = False
    if not base_ok:
        # 连 browser_status 都异常: 只有 /health 在线才算活(可能只是执行队列繁忙)
        try:
            h = http_get("/health", timeout=8)
            if h.get("tool_count"):
                print('      ~ 探针异常但服务在线 => 存活(不冷重启)')
                return True
        except Exception:
            pass
        return False
    # ② CDP 短探(两次, 间隔 2 秒): 瞬时忙碌会被应用侧自救恢复; 两次都失败=通道真坏
    for _n in range(2):
        try:
            r = http_post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                           "params": {"name": "browser_execute_js",
                                      "arguments": {"code": "1", "max_ms": 1500}}}, 12)
            res = r.get("result") or {}
            if not res.get("isError"):
                txt = "".join((c.get("text") or "") for c in (res.get("content") or []))
                if '"success":true' in txt or '"message":"1"' in txt:
                    return True
        except Exception:
            pass
        time.sleep(2)
    print('      ~ CDP 通道两次短探均失败(真坏) => 判死, 触发修复性冷重启')
    return False


# 状态依赖: 工具本身要求"页面已在某状态"才有效(如从暂停态恢复、单步)。
# 不满足时拒绝执行是**正确行为**, 不是缺前置 —— 必须排在 PREREQ 之前判断,
# 否则其错误文案里的"请先 debugger_flow…"会被 PREREQ 正则吞掉, 污染核心指标。
STATE_RE = re.compile(r"页面未处于暂停状态|尚无 Debugger\.paused|未处于暂停|无需恢复")
# 故意加的"防误操作守卫": 传了 confirm/必须提供某参数才允许执行 —— 这是正确行为, 不是缺陷
GUARD_RE = re.compile(r"请设置|以确认|必须提供|必须同时提供|不能省略|请显式传")
# 参数本身非法/类型不对(测试侧或调用方给错)
PARAM_RE = re.compile(r"不是有效数字|必须为正整数|不能为0|非法|无效的|格式错误")


def prereq_of(text):
    """把一次失败归类。返回 (类别, 依据)

    先剥掉尾部提示段(建议/注意/替代) —— 它们是行动建议而非失败原因, 否则提示里的
    "需先/请先"会把"目标不存在"类失败误吞成 PREREQ(实测已发生, 见 strip_hints 注释)。
    """
    core = strip_hints(text)
    for name, rx in (("STATE", STATE_RE), ("PREREQ", PREREQ_RE), ("GUARD", GUARD_RE),
                     ("PARAM", PARAM_RE), ("TARGET", TARGET_RE),
                     ("NO_BROWSER", NOBROWSER_RE), ("CAPABILITY", CAP_RE)):
        m = rx.search(core or "")
        if m:
            return name, m.group(0)
    return "OTHER", (core or text or "")[:60]


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    keep = "--keep" in sys.argv

    print("== 冷启动一次调用矩阵 ==")
    if not keep:
        h = cold_restart()
        if not h:
            print("!! 冷启动失败")
            return 2

    tl = http_get("/tools/list", timeout=20)
    tools = tl.get("tools", [])
    print("工具总数 = %d" % len(tools))

    rows = []
    wedges = []
    auto_prep = 0
    skip = MP.LETHAL | MP.MUTATING_SKIP
    t0 = time.time()
    for t in tools:
        name = t.get("name")
        if name in skip:
            rows.append({"tool": name, "cls": "SKIP", "note": "致命/污染全局, 不探测"})
            continue
        if limit and len(rows) >= limit:
            break
        schema = t.get("inputSchema") or {}
        desc = t.get("description") or ""
        # 注意: build_args 返回的是元组 (args, notes) —— 曾漏解包导致每个工具都收到
        # 形如 [{...},[...]] 的 arguments(2元素数组而非对象), 使整轮矩阵的失败数字全部失真。
        args, _anotes = MP.build_args(schema, desc, t.get("name"))
        if name in MP.SPECIAL_ARGS:
            args = dict(MP.SPECIAL_ARGS[name])
        st = time.time()
        err = None
        try:
            resp = http_post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                              "params": {"name": name, "arguments": args}}, 45)
        except Exception as ex:
            resp, err = None, str(ex)
        el = time.time() - st
        cls, note = MP.classify(name, args, resp, el, err)
        row = {"tool": name, "cls": cls, "elapsed": round(el, 2),
               "args": args, "note": note}
        if "auto_prepared" in (note or ""):
            auto_prep += 1
            row["auto_prepared"] = True
        if cls.startswith("ERR") or cls in ("TIMEOUT", "TRANSPORT_ERR", "NO_RESPONSE", "RPC_ERR",
                                            "PROTO_ERR", "NOTFOUND"):
            sub, why = prereq_of(note)
            row["fail_kind"] = sub
            row["fail_why"] = why
        # 卡死检测: 仅对"失败或明显变慢"的调用做活性探针(便宜的 browser_status),
        # 一旦发现实例已被卡死就冷重启, 避免污染后续全部结果, 并记录是哪个工具搞卡的。
        if (cls in ("TIMEOUT", "TRANSPORT_ERR", "NO_RESPONSE") or el > 4.0):
            if not alive():
                row["wedge"] = True
                wedges.append(name)
                print("  [wedge] %s 把实例卡死了 -> 冷重启后继续" % name)
                if not cold_restart():
                    print("  !! 冷重启失败, 终止")
                    break
        rows.append(row)

    total = len(rows)
    def cnt(pred):
        return sum(1 for r in rows if pred(r))
    ok = cnt(lambda r: r["cls"] in ("OK", "OK_EMPTY_TEXT"))
    skipn = cnt(lambda r: r["cls"] == "SKIP")
    prereq = [r for r in rows if r.get("fail_kind") == "PREREQ"]
    nobr = [r for r in rows if r.get("fail_kind") == "NO_BROWSER"]
    cap = [r for r in rows if r.get("fail_kind") == "CAPABILITY"]
    tgt = [r for r in rows if r.get("fail_kind") == "TARGET"]
    other = [r for r in rows if r.get("fail_kind") == "OTHER"]
    slow = sorted([r for r in rows if r.get("elapsed", 0) > 3],
                  key=lambda r: -r["elapsed"])[:12]

    print("\n---- 汇总 (%.1fs) ----" % (time.time() - t0))
    print("总数 %d | 跳过 %d | 一次成功 %d (%.0f%%)" %
          (total, skipn, ok, 100.0 * ok / max(1, total - skipn)))
    print("【核心指标】前置缺失类失败 = %d  (目标 0)" % len(prereq))
    print("auto_prepared 生效(自动补前置) = %d" % auto_prep)
    print("把实例搞卡死(已自动冷重启)的工具 = %d  %s" % (len(wedges), wedges))
    print("无浏览器/无页面 = %d | 能力缺失 = %d | 目标不存在 = %d | 其它失败 = %d" %
          (len(nobr), len(cap), len(tgt), len(other)))
    if prereq:
        print("\n---- 前置缺失明细(必须清零) ----")
        for r in prereq[:40]:
            print("  %-42s %s" % (r["tool"], (r["note"] or "")[:100]))
    if wedges:
        print("\n---- 会把实例搞卡死的工具(真正的'连续失败'元凶) ----")
        for w in wedges:
            print("  %s" % w)
    if nobr:
        print("\n---- 无浏览器/无页面 ----")
        for r in nobr[:15]:
            print("  %-42s %s" % (r["tool"], (r["note"] or "")[:90]))
    if other:
        print("\n---- 其它失败 ----")
        for r in other[:25]:
            print("  %-42s %s" % (r["tool"], (r["note"] or "")[:100]))
    if slow:
        print("\n---- 最慢(>3s) ----")
        for r in slow:
            print("  %-42s %5.1fs %s" % (r["tool"], r["elapsed"], r["cls"]))

    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("\n明细已存 _cold_matrix.json")
    return 1 if prereq else 0


if __name__ == "__main__":
    sys.exit(main())
