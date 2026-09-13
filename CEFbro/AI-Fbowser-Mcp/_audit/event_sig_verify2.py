# -*- coding: utf-8 -*-
"""签名一致性校验 v2 — 正确处理跨行的方法声明。

火山 方法声明可以是多行:
    方法 X <公开 注释 = "..."
    @虚拟方法 = 可覆盖>
    参数 A <类型 = T>
所以必须先消费到声明的 '>' 闭合, 再收集 参数 行, 直到 '{'。
"""
import io
import os
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SKILL = (r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming"
         r"\资料\类库\FBrowser浏览器\FBroEventControl.wsv")
SRC = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src"

CLASSES = {"类_FBrowser_应用事件": "APP", "类_FBrowser_浏览器事件": "BROWSER"}
MSTART = re.compile(r'方法\s+([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*)\s*<')
PARAM = re.compile(r'参数\s+([\u4e00-\u9fffA-Za-z_][\u4e00-\u9fffA-Za-z0-9_]*)\s*<类型\s*=\s*([^ >]+)')


def decl_of(lines, i):
    """从 lines[i] 的 '方法' 开始, 返回 (名称, 属性串, 参数类型表, 结束行号)。"""
    buf, j = "", i
    while j < len(lines):
        buf += lines[j] + "\n"
        if buf.count("<") <= buf.count(">"):
            break
        j += 1
    m = MSTART.search(lines[i])
    if not m:
        return None
    name = m.group(1)
    lt = buf.find("<")
    gt = buf.find(">", lt)
    attrs = buf[lt + 1:gt] if gt > 0 else ""
    is_bool = bool(re.search(r'类型\s*=\s*逻辑型', attrs))
    types, k, seen_brace = [], j + 1, False
    while k < len(lines):
        s = lines[k].strip()
        if s.startswith("{"):
            seen_brace = True
            break
        if s.startswith("参数"):
            pm = PARAM.search(lines[k])
            if pm:
                types.append(pm.group(2))
        elif s and not s.startswith(("注释", "返回值注释", "@", "<")):
            break
        k += 1
    return name, attrs, is_bool, types, seen_brace, k


def parse(path, only_classes=None):
    out = {}
    lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    cur = None
    i = 0
    while i < len(lines):
        m = re.match(r'\s*类\s+(\S+)', lines[i])
        if m:
            cur = m.group(1) if only_classes is None else CLASSES.get(m.group(1))
            i += 1
            continue
        if lines[i].lstrip().startswith("方法 ") and (only_classes is None or cur):
            r = decl_of(lines, i)
            if r:
                name, attrs, is_bool, types, ok, end = r
                if name not in ("类_初始化", "类_清理") and name not in out:
                    out[name] = (is_bool, types)
                # 注意: end 指向 '{' 或下一个 '方法' 行; 必须用 end(而非 end+1) 以免跳过紧邻的下一个方法
                i = end if end > i else i + 1
                continue
        i += 1
    return out


lib = parse(SKILL)
proj = {}
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".wsv") or ".~vbak" in f:
        continue
    proj.update({k: v for k, v in parse(os.path.join(SRC, f)).items() if k not in proj})

NEW = set("""浏览器_即将打开菜单 浏览器_菜单被调用 浏览器_菜单被点击 浏览器_菜单被关闭
浏览器_即将运行快捷菜单命令 浏览器_即将取消快捷菜单 浏览器_从标签打开地址 浏览器_处理协议请求
浏览器_即将创建主框架Document 浏览器_工具栏被改变 浏览器_光标被改变 浏览器_自动调整尺寸
浏览器_渲染视图 浏览器_拖拽区域改变 浏览器_选择客户端证书 浏览器_按下某键后 浏览器_请求焦点
浏览器_JS重置对话框 浏览器_JS对话框关闭 浏览器_即将连接框架
请求环境初始化完毕 即将处理命令行 浏览器_即将启动子进程 浏览器_即将启动消息调度
渲染_即将初始化WebKit 渲染_即将创建V8环境 渲染_收到消息 渲染_载入状态被改变 渲染_载入开始
渲染_载入结束 扩展插件_创建成功 扩展插件_创建失败 扩展插件_载入成功 扩展插件_卸载成功
渲染_VIP_WebSocket客户端_创建 渲染_VIP_WebSocket客户端_关闭 渲染_VIP_WebSocket客户端_连接服务器
渲染_VIP_WebSocket客户端_接收数据 渲染_VIP_WebSocket客户端_发送数据""".split())

print("类库事件 %d, 项目事件 %d, 本轮新增 %d" % (len(lib), len(proj), len(NEW)))
print()
print("=" * 100)
print("仅校验本轮新增事件的签名 (这是本轮改动引入风险的地方)")
print("=" * 100)
bad = 0
for n in sorted(NEW):
    if n not in lib:
        print("  ?? %-34s 类库中未找到 (名称拼写?)" % n)
        bad += 1
        continue
    if n not in proj:
        print("  !! %-34s 项目中未找到" % n)
        bad += 1
        continue
    lb, lt = lib[n]
    pb, pt = proj[n]
    errs = []
    if lb != pb:
        errs.append("返回类型 类库逻辑型=%s 项目=%s" % (lb, pb))
    if len(lt) != len(pt):
        errs.append("参数个数 类库%d 项目%d" % (len(lt), len(pt)))
    else:
        for k, (a, b) in enumerate(zip(lt, pt)):
            if a != b:
                errs.append("第%d参数 类库=%s 项目=%s" % (k + 1, a, b))
    if errs:
        bad += 1
        print("  !! %-34s %s" % (n, " | ".join(errs)))
        print("       类库参数: %s" % lt)
        print("       项目参数: %s" % pt)
    else:
        print("  OK %-34s 逻辑型=%-5s 参数 %d 个 全一致" % (n, lb, len(lt)))
print()
print("★ 不一致: %d / %d" % (bad, len(NEW)))
