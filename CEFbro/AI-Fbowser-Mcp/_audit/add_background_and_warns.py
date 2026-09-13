# -*- coding: utf-8 -*-
"""① 给 browser_create 注册 background 参数; ② 给实测同样会打断 CDP 的 4 个 VIP 输入工具补警告;
③ 给两个 version 参数补符合 schema 类型的测试取值。

## ② 的依据(本轮台账实测)
`browser_vip_mouse_press` / `_release` / `browser_vip_key_input` / `_key_type` 每一项**之后**都紧跟
"实例不活, 先冷重启" —— 即它们与其余 VIP 内核输入工具一样,**每次调用都会让 CDP 通道在本会话内失效**。
上一轮我**故意没给它们加警告**, 因为它们的描述写的是"CDP鼠标按下"/"CDP输入字符"(看起来走 CDP),
而当时没有实测证据 —— 现在有了, 属于"以证据为准修订文案", 而不是猜。
保持既有措辞风格, 只追加警告与 CDP 版替代工具指引。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "src", "MCP_Server.wsv")
S = io.open(P, encoding="utf-8").read()

WARN = (" | **警告: 本工具实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具都会超时/退化), "
        "必须重启 AI-Fbowser-Mcp.exe 才能恢复; 如后续还要用 CDP 类工具, 请改用 browser_mouse_click / "
        "browser_mouse_move / browser_mouse_wheel / browser_key_event")

VIPS = ["browser_vip_mouse_press", "browser_vip_mouse_release",
        "browser_vip_key_input", "browser_vip_key_type"]

added = []
for t in VIPS:
    # 这四个工具的 schema 构造器不同(mouse_press/_release 用 双XY_Schema文本, key_* 用 单参数Schema文本),
    # 故按"任意 schema 构造器名"匹配, 只要求紧跟描述字符串结尾
    pat = re.compile(r'(添加工具JSON \("%s", "[^"]*)(", (?:单参数Schema文本|双XY_Schema文本|多属性Schema文本) \()' % re.escape(t))

    def rep(m):
        if "CDP 通道在本会话内失效" in m.group(1):
            return m.group(0)
        added.append(t)
        return m.group(1) + WARN + m.group(2)
    S = pat.sub(rep, S)
missing = [t for t in VIPS if t not in added]
if missing:
    print("!! 未匹配到描述的工具: %s -> 中止" % ", ".join(missing))
    sys.exit(2)
print("已补警告: %s" % ", ".join(added))

# ① browser_create 注册 background 参数(替换整条注册行)
OLD_CREATE = ('添加工具JSON ("browser_create", "新建一个可见浏览器窗口(默认 about:blank)')
NEW_CREATE = ('添加工具JSON ("browser_create", "新建浏览器窗口(默认 about:blank) | background:true 时创建**完全无窗口的后台浏览器**'
              '(类库注明: 无窗口无窗口句柄、只能后台不能显示, 与先创建再隐藏窗口不同、也非无头模式, 适合纯后台刷新取数, 占用比前台更低)')
n = S.count(OLD_CREATE)
if n != 1:
    print("!! browser_create 注册锚点命中 %d 次(应 1) -> 中止" % n)
    sys.exit(2)
S = S.replace(OLD_CREATE, NEW_CREATE)
# 描述里原有的"新建一个可见浏览器窗口"整句替换为准确表述
S = S.replace('需要浏览器级隔离时使用, 常规自动化无需手动创建 | 仅支持 http/https/about/ftp 协议; data: 仅图片类型(image/png|jpeg|gif|webp|bmp|x-icon), 为防脚本注入 data:text/html 被拒 | 新建后用 browser_list 取它的 id',
              '需要浏览器级隔离或纯后台取数时使用, 常规自动化无需手动创建 | 允许 http/https/about/ftp; data: 仅图片类型(image/png|jpeg|gif|webp|bmp|x-icon), 为防脚本注入 data:text/html 被拒 | 新建后用 browser_list 取它的 id')
# 追加 background 参数项到该工具的 schema
OLD_SCHEMA = '单参数Schema文本 ("url", "text", "初始URL(默认about:blank)", 假))'
NEW_SCHEMA = ('多属性Schema文本 (属性项JSON ("url", "text", "初始URL(默认about:blank)") + "," + '
              '属性项JSON ("background", "boolean", "true=创建完全无窗口的后台浏览器(不显示、占用更低, 适合纯后台刷新取数); 默认false=可见窗口"), ""))')
n2 = S.count(OLD_SCHEMA)
if n2 < 1:
    print("!! browser_create schema 锚点未命中 -> 中止")
    sys.exit(2)
S = S.replace(OLD_SCHEMA, NEW_SCHEMA, 1)
print("已给 browser_create 注册 background 参数(schema 锚点原有 %d 处, 只改第 1 处)" % n2)

io.open(P, "w", encoding="utf-8", newline="\n").write(S)

# 写后自检
chk = io.open(P, encoding="utf-8").read()
bad = 0
for t in VIPS:
    line = [l for l in chk.split("\n") if '添加工具JSON ("%s"' % t in l]
    ok = bool(line) and "CDP 通道在本会话内失效" in line[0]
    print("自检 %-30s 描述含警告: %s" % (t, "OK" if ok else "!! 缺失"))
    if not ok:
        bad += 1
line = [l for l in chk.split("\n") if '添加工具JSON ("browser_create"' in l]
ok = bool(line) and '"background"' in line[0] and "background:true" in line[0]
print("自检 browser_create 含 background: %s" % ("OK" if ok else "!! 缺失"))
if not ok:
    bad += 1
print("OK" if bad == 0 else "!! %d 项未通过" % bad)
sys.exit(1 if bad else 0)
