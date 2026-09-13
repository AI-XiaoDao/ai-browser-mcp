# -*- coding: utf-8 -*-
"""注册 VIP 指纹三件套 + 给 6 个内核级输入工具补"会破坏 CDP 会话"的警告。

## 为什么要补警告(实测证据)
功能台账 `tool_ledger.py --next 15` 实测: `browser_vip_mouse_click/_move/_wheel` 与
`browser_vip_key_press/_release/_click` 这 6 个工具**每调用一次, 下一条 CDP 请求就不活了**
(台账里每一项后面都紧跟一行"实例不活, 先冷重启"), 而它们的返回文案却是光秃秃的
"VIP鼠标点击"/"VIP键盘按下: key_code=1" —— 对"整场会话的 CDP 通道已被打断"这件事**只字未提**。
用户随后用任何 CDP 优先工具都会白等超时, 只能反复换方法重试 —— 正是要消灭的那种体验。
这些工具本身是内核级注入(其存在意义就是过反爬), 无法改成 CDP 优先, 故正确做法是**如实告知代价**
并指出 CDP 版替代工具。

注意: 只给**实测会打断 CDP** 的那 6 个加警告。`browser_vip_mouse_press/_release` 与
`browser_vip_key_input/_key_type` 的说明写的是"CDP…"(非内核注入), 未实测其副作用, 不臆断。
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

WARN = (" | **警告: 本工具走内核级注入, 实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具"
        "都会超时/退化, 连 browser_status 都可能挂), 必须重启 AI-Fbowser-Mcp.exe 才能恢复;"
        "如后续还要用 CDP 类工具, 请改用 CDP 版: browser_mouse_click / browser_mouse_move / "
        "browser_mouse_wheel / browser_key_event")

WARN6 = ["browser_vip_mouse_click", "browser_vip_mouse_move", "browser_vip_mouse_wheel",
         "browser_vip_key_press", "browser_vip_key_release", "browser_vip_key_click"]

S = io.open(P, encoding="utf-8").read()
orig = S

# ---- 1) 给 6 个工具的描述补警告 ----
pat = re.compile(r'(添加工具JSON \("(?P<tool>[a-z_]+)", ")(?P<desc>(?:[^"\\]|\\.)*)(", (?:多属性Schema文本|双XY_Schema文本|单参数Schema文本) \()')
done = []
def add_warn(m):
    if m.group("tool") in WARN6 and "CDP 通道在本会话内失效" not in m.group("desc"):
        done.append(m.group("tool"))
        return m.group(1) + m.group("desc") + WARN + m.group(3)
    return m.group(0)

S = pat.sub(add_warn, S)
print("已补警告的工具: %s" % (", ".join(done) if done else "(无)"))
missing = [t for t in WARN6 if t not in done]
if missing:
    print("!! 以下工具未能匹配到描述(需人工检查): %s" % ", ".join(missing))
    sys.exit(2)

# ---- 2) 注册 VIP 指纹三件套(紧跟 browser_fingerprint_touch_enable) ----
ANCHOR = '        添加工具JSON ("browser_fingerprint_touch_enable", "VIP: 触摸事件指纹", 多属性Schema文本 (属性项JSON ("enable", "boolean", "启用") + "," + 属性项JSON ("points", "integer", "触摸点数"), ""))'
if S.count(ANCHOR) != 1:
    print("!! 注册锚点命中 %d 次(应 1) -> 中止" % S.count(ANCHOR))
    sys.exit(2)
NEW = ANCHOR + "\n" + "\n".join([
    '        添加工具JSON ("browser_fingerprint_languages", "VIP: navigator.languages 语言指纹。languages 传逗号分隔清单(如 zh-CN,zh,en); reset:true 恢复默认(类库无单项复位API, 以空文本交回库内部默认; 彻底复位用 browser_fingerprint action=clear)。设置后需刷新页面生效", 多属性Schema文本 (属性项JSON ("languages", "text", "语言清单, 逗号分隔, 例: zh-CN,zh,en") + "," + 属性项JSON ("reset", "boolean", "true=恢复默认(与 languages 二选一)"), ""))',
    '        添加工具JSON ("browser_fingerprint_webgl_vendor", "VIP: WebGL 厂商/渲染器字符串。默认渲染器字符串会把真实显卡与驱动暴露给指纹脚本, 故反指纹场景常需改写。vendor 例: Google Inc. (NVIDIA); renderer 可选(类库有独立API)。设置后需刷新页面生效", 多属性Schema文本 (属性项JSON ("vendor", "text", "厂商字符串, 例: Google Inc. (NVIDIA)") + "," + 属性项JSON ("renderer", "text", "渲染器字符串(可选; 省略则由库内部决定)"), "\\"vendor\\""))',
    '        添加工具JSON ("browser_font_randomize", "VIP: 字体枚举随机化(抗字体指纹)。action=random(默认) 从候选池随机挑 count 个字体并加宽/高偏移与 Canvas 字体度量噪点; seed 非0 时固定随机序列, 便于复现同一套指纹; action=reset 复位(清单置空+偏移归零)。设置后需刷新页面生效", 多属性Schema文本 (属性项JSON ("action", "text", "random(默认)/reset") + "," + 属性项JSON ("count", "integer", "随机挑选的字体个数(默认0=用库默认)") + "," + 属性项JSON ("seed", "integer", "随机种子(非0=可复现, 默认0)"), ""))',
])
if 'browser_fingerprint_languages' in orig:
    print("!! browser_fingerprint_languages 已注册 -> 中止(前提已变)")
    sys.exit(2)
S = S.replace(ANCHOR, NEW, 1)
print("已注册 3 个 VIP 指纹工具")

io.open(P, "w", encoding="utf-8", newline="\n").write(S)

# ---- 3) 写后自检 ----
chk = io.open(P, encoding="utf-8").read()
bad = 0
for t in WARN6:
    c = chk.count(WARN.strip())
    line = [l for l in chk.split("\n") if '添加工具JSON ("%s"' % t in l]
    ok = bool(line) and "CDP 通道在本会话内失效" in line[0]
    print("自检 %-28s 描述含警告: %s" % (t, "OK" if ok else "!! 缺失"))
    if not ok:
        bad += 1
for t in ("browser_fingerprint_languages", "browser_fingerprint_webgl_vendor", "browser_font_randomize"):
    n = chk.count('添加工具JSON ("%s"' % t)
    print("自检 %-30s 注册 %d 次 (应 1)" % (t, n))
    if n != 1:
        bad += 1
print("OK" if bad == 0 else "!! %d 项自检未通过" % bad)
sys.exit(1 if bad else 0)
