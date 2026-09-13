# -*- coding: utf-8 -*-
r"""第139轮补丁 A: 修"schema 承诺了、实现却没生效"的静默缺陷 + 补两个被截断的参数。

## 缺陷(均由只读分诊子代理静态定位, 主代理逐条 grep 复核)
1. **`browser_key_event.modifiers` 是假能力**：schema 声明了 `modifiers`, 但 VIP 路径
   (`MCP_Server_Core.wsv` 的 `高级键盘_按下/放开/单击` 三处) **根本没传它** —— 只有当 VIP 不可用、
   掉到 CEF 退路时才写进 `按键事件.修饰位`。VIP 在本项目恒可用 ⇒ **按 schema 传 modifiers 时组合键静默失效**。
   修法: 在读 type 时一并读 `modifiers`, VIP 三处都传第 2 参(类库约定 Alt=1/Ctrl=2/Meta=4/Shift=8),
   CEF 退路按**语义换算**成 CEF 旗标(Shift=2/Ctrl=4/Alt=8/Command=16), 而不是把 VIP 掩码直接塞进去。
2. **`browser_context_menu action=set` 的载荷不是合法 JSON**：拼接处漏了一个逗号
   (`"warnings":""\"spec_lines"`), 任何按 JSON 解析 `data` 的调用方都会失败。
3. **`browser_fingerprint_pixel_ratio.value` 声明成 text**：实现按小数读(读取器已对文本节点归一化, 故能跑),
   但 schema 类型与语义不符 —— 改为 number 并在描述里注明文本也接受。

## 参数补齐(被包装器截断的类库能力)
4. `browser_vip_mouse_press/release`: 类库 `高级鼠标_按下/放开` 有第 3 参 `按键类型`(0左/1中/2右),
   项目一直只传 x,y ⇒ **永远左键**; 且缺 x/y 时会退化成在 (0,0) 按下。补 `button` + x/y 必填守卫。
5. `browser_vip_mouse_click`: 类库 `高级鼠标_单击` 第 4 参 `单击延时`(默认 50ms)被截断, 补 `delay_ms`。

用法: py -3 _audit\_apply_round139a.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

# ── A1 VIP 键盘: 把 modifiers 真正接上 ──
KB_OLD = '''                变量 类型文本 <类型 = 文本型>
                类型文本 = MCP命令服务器.yyjson取文本 (参数JSON, "type")
                // VIP优先: CDP高级键盘 (绕过反自动化检测)
                变量 vip_ctrl <类型 = 类_FBrowserVIP_控制器>
                vip_ctrl = browser.取VIP控制器 ()
                如果 (vip_ctrl.是否为空 () == 假 && key <= 255)
                {
                    如果 (类型文本 == "keydown")
                    {
                        vip_ctrl.高级键盘_按下 (key)
                        返回 (MCP_响应构建.命令成功 (命令ID, "VIP按下 key_code=" + 到文本 (key)))
                    }
                    否则 (类型文本 == "keyup")
                    {
                        vip_ctrl.高级键盘_放开 (key)
                        返回 (MCP_响应构建.命令成功 (命令ID, "VIP放开 key_code=" + 到文本 (key)))
                    }
                    否则 (类型文本 == "" || 类型文本 == "char" || 类型文本 == "click" || 类型文本 == "press")
                    {
                        vip_ctrl.高级键盘_单击 (key)
                        返回 (MCP_响应构建.命令成功 (命令ID, "VIP单击 key_code=" + 到文本 (key)))
                    }'''

KB_NEW = '''                变量 类型文本 <类型 = 文本型>
                类型文本 = MCP命令服务器.yyjson取文本 (参数JSON, "type")
                // 修饰键位掩码, 与类库 `高级键盘_按下/放开/单击` 第 2 参的约定一致:
                //   Alt=1, Ctrl=2, Meta/Command=4, Shift=8 (FBroVip.wsv 该参数注释原文)。
                // ⚠ 该值原先只在下面的 CEF 退路里被使用, VIP 三处调用**都没传** ⇒
                //   按 schema 传 modifiers 时组合键静默失效(schema 承诺了却没生效)。现三处都传。
                变量 修饰掩码 <类型 = 整数>
                修饰掩码 = MCP命令服务器.yyjson取整数 (参数JSON, "modifiers")
                // VIP优先: CDP高级键盘 (绕过反自动化检测)
                变量 vip_ctrl <类型 = 类_FBrowserVIP_控制器>
                vip_ctrl = browser.取VIP控制器 ()
                如果 (vip_ctrl.是否为空 () == 假 && key <= 255)
                {
                    如果 (类型文本 == "keydown")
                    {
                        vip_ctrl.高级键盘_按下 (key, 修饰掩码, 假)
                        返回 (MCP_响应构建.命令成功 (命令ID, "VIP按下 key_code=" + 到文本 (key) + " modifiers=" + 到文本 (修饰掩码)))
                    }
                    否则 (类型文本 == "keyup")
                    {
                        vip_ctrl.高级键盘_放开 (key, 修饰掩码, 假)
                        返回 (MCP_响应构建.命令成功 (命令ID, "VIP放开 key_code=" + 到文本 (key) + " modifiers=" + 到文本 (修饰掩码)))
                    }
                    否则 (类型文本 == "" || 类型文本 == "char" || 类型文本 == "click" || 类型文本 == "press")
                    {
                        vip_ctrl.高级键盘_单击 (key, 修饰掩码, 50, 假)
                        返回 (MCP_响应构建.命令成功 (命令ID, "VIP单击 key_code=" + 到文本 (key) + " modifiers=" + 到文本 (修饰掩码)))
                    }'''

# ── A2 CEF 退路: 语义换算 + 修正错误注释 ──
CEF_OLD = '''                按键事件.系统按键 = key
                // 修饰键: 位标志组合 (1=Ctrl, 2=Alt, 4=Shift), 默认0=无
                变量 修饰位 <类型 = 整数>
                修饰位 = MCP命令服务器.yyjson取整数 (参数JSON, "modifiers")
                按键事件.修饰位 = 修饰位'''
CEF_NEW = '''                按键事件.系统按键 = key
                // 修饰键换算: 对外统一用 VIP 约定(Alt=1/Ctrl=2/Meta=4/Shift=8), 而 CEF 事件旗标是另一套位序
                //   (SHIFT=2, CONTROL=4, ALT=8, COMMAND=16) —— 必须按**语义**换算, 直接把掩码塞进去会让
                //   Ctrl 变成 Shift 之类的错键(旧注释 "1=Ctrl,2=Alt,4=Shift" 与两边约定都不符, 已删)。
                变量 修饰位 <类型 = 整数 值 = 0>
                如果 (位与 (修饰掩码, 1) != 0)
                {
                    修饰位 = 修饰位 + 8
                }
                如果 (位与 (修饰掩码, 2) != 0)
                {
                    修饰位 = 修饰位 + 4
                }
                如果 (位与 (修饰掩码, 4) != 0)
                {
                    修饰位 = 修饰位 + 16
                }
                如果 (位与 (修饰掩码, 8) != 0)
                {
                    修饰位 = 修饰位 + 2
                }
                按键事件.修饰位 = 修饰位'''

# ── A3 右键菜单 set 载荷的非法 JSON ──
CM_OLD = '''+ "\\"\\"spec_lines\\":" +'''
CM_NEW = '''+ "\\",\\"spec_lines\\":" +'''

# ── A4 pixel_ratio schema 类型 ──
PR_OLD = '''单参数Schema文本 ("value", "text", "如1.5")'''
PR_NEW = '''单参数Schema文本 ("value", "number", "设备像素比, 如 1.5 / 2 / 0.8; 文本 \\"1.5\\" 也可(读取器对文本节点已归一化)")'''

# ── A5 vip_mouse_press/release: button + x/y 守卫 ──
PRESS_OLD = '''                    vip_ctrl.高级鼠标_按下 (MCP命令服务器.yyjson取整数 (参数JSON, "x"), MCP命令服务器.yyjson取整数 (参数JSON, "y"))
                    返回 (MCP_响应构建.命令成功 (命令ID, "VIP鼠标按下"))'''
PRESS_NEW = '''                    // x/y 必填: 缺参会退化成在 (0,0) 按下并报成功
                    如果 (MCP命令服务器.参数键存在 (参数JSON, "x") == 假 || MCP命令服务器.参数键存在 (参数JSON, "y") == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "必须同时提供 x 与 y (整数坐标) | 缺省会退化成在 (0,0) 按下, 故拒绝执行"))
                    }
                    // 按键类型(类库第3参): 0左/1中/2右 —— 原先不传 ⇒ 按下的**永远是左键**
                    变量 mp按钮 <类型 = 整数>
                    mp按钮 = MCP命令服务器.yyjson取整数 (参数JSON, "button")
                    如果 (mp按钮 < 0 || mp按钮 > 2)
                    {
                        mp按钮 = 0
                    }
                    vip_ctrl.高级鼠标_按下 (MCP命令服务器.yyjson取整数 (参数JSON, "x"), MCP命令服务器.yyjson取整数 (参数JSON, "y"), mp按钮)
                    返回 (MCP_响应构建.命令成功 (命令ID, "VIP鼠标按下 button=" + 到文本 (mp按钮)))'''

RELEASE_OLD = '''                    vip_ctrl.高级鼠标_放开 (MCP命令服务器.yyjson取整数 (参数JSON, "x"), MCP命令服务器.yyjson取整数 (参数JSON, "y"))
                    返回 (MCP_响应构建.命令成功 (命令ID, "VIP鼠标放开"))'''
RELEASE_NEW = '''                    如果 (MCP命令服务器.参数键存在 (参数JSON, "x") == 假 || MCP命令服务器.参数键存在 (参数JSON, "y") == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "必须同时提供 x 与 y (整数坐标) | 缺省会退化成在 (0,0) 放开, 故拒绝执行"))
                    }
                    变量 mr按钮 <类型 = 整数>
                    mr按钮 = MCP命令服务器.yyjson取整数 (参数JSON, "button")
                    如果 (mr按钮 < 0 || mr按钮 > 2)
                    {
                        mr按钮 = 0
                    }
                    vip_ctrl.高级鼠标_放开 (MCP命令服务器.yyjson取整数 (参数JSON, "x"), MCP命令服务器.yyjson取整数 (参数JSON, "y"), mr按钮)
                    返回 (MCP_响应构建.命令成功 (命令ID, "VIP鼠标放开 button=" + 到文本 (mr按钮)))'''

# ── A6 vip_mouse_click: delay_ms ──
CLICK_OLD = '''                    vip_ctrl.高级鼠标_单击 (vx, vy, MCP命令服务器.yyjson取整数 (参数JSON, "button"))
                    返回 (MCP_响应构建.命令成功 (命令ID, "VIP鼠标点击"))'''
CLICK_NEW = '''                    // 单击延时(类库第4参, 默认50ms): 反爬场景常需要更长的按压时长, 原先被截断只能吃默认值
                    变量 vclick延迟 <类型 = 整数>
                    vclick延迟 = MCP命令服务器.yyjson取整数 (参数JSON, "delay_ms")
                    如果 (vclick延迟 <= 0)
                    {
                        vclick延迟 = 50
                    }
                    如果 (vclick延迟 > 5000)
                    {
                        vclick延迟 = 5000
                    }
                    vip_ctrl.高级鼠标_单击 (vx, vy, MCP命令服务器.yyjson取整数 (参数JSON, "button"), vclick延迟)
                    返回 (MCP_响应构建.命令成功 (命令ID, "VIP鼠标点击 button=" + 到文本 (MCP命令服务器.yyjson取整数 (参数JSON, "button")) + " delay_ms=" + 到文本 (vclick延迟)))'''

# ── A7 描述/schema ──
KE_DESC_OLD = '''"发送键盘事件| key_code=虚拟键码(如 13=Enter, 65=A), type=keydown/keyup/char, modifiers=修饰键位掩码; 输入文本请用 vip_key_type"'''
KE_DESC_NEW = '''"发送键盘事件| key_code=虚拟键码(如 13=Enter, 65=A), type=keydown/keyup/char, modifiers=修饰键位掩码(**Alt=1 / Ctrl=2 / Meta=4 / Shift=8**, 与类库约定一致; 例 Ctrl+A = key_code:65, modifiers:2); 输入文本请用 vip_key_type"'''
KE_PROP_OLD = '''属性项JSON ("modifiers", "integer", "修饰键")'''
KE_PROP_NEW = '''属性项JSON ("modifiers", "integer", "修饰键位掩码: Alt=1 / Ctrl=2 / Meta=4 / Shift=8 (可相加, 如 Ctrl+Shift=10)")'''

PRESS_REG_OLD = '''添加工具JSON ("browser_vip_mouse_press", "VIP: CDP鼠标按下 | **警告: 本工具实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具都会超时/退化), 必须重启 AI-Fbowser-Mcp.exe 才能恢复; 如后续还要用 CDP 类工具, 请改用 browser_mouse_click / browser_mouse_move / browser_mouse_wheel / browser_key_event", 双XY_Schema文本 ("x", "y", "X", "Y"))'''
PRESS_REG_NEW = '''添加工具JSON ("browser_vip_mouse_press", "VIP: 内核级鼠标按下(可与 browser_vip_mouse_release 组成拖拽) | x,y=页面坐标(必填, 缺参会退化成在(0,0)按下故直接拒绝), button=按键(0左(默认)/1中/2右) | **警告: 本工具走内核级注入, 实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具都会超时/退化), 必须重启 AI-Fbowser-Mcp.exe 才能恢复; 如后续还要用 CDP 类工具, 请改用 browser_mouse_click / browser_mouse_move / browser_mouse_wheel / browser_key_event", 多属性Schema文本 (属性项JSON ("x", "integer", "X(必填)") + "," + 属性项JSON ("y", "integer", "Y(必填)") + "," + 属性项JSON ("button", "integer", "按键: 0左(默认)/1中/2右"), "\\"x\\",\\"y\\""))'''
RELEASE_REG_OLD = '''添加工具JSON ("browser_vip_mouse_release", "VIP: CDP鼠标放开 | **警告: 本工具实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具都会超时/退化), 必须重启 AI-Fbowser-Mcp.exe 才能恢复; 如后续还要用 CDP 类工具, 请改用 browser_mouse_click / browser_mouse_move / browser_mouse_wheel / browser_key_event", 双XY_Schema文本 ("x", "y", "X", "Y"))'''
RELEASE_REG_NEW = '''添加工具JSON ("browser_vip_mouse_release", "VIP: 内核级鼠标放开(与 browser_vip_mouse_press 配对) | x,y=页面坐标(必填), button=按键(0左(默认)/1中/2右, 应与按下时一致) | **警告: 本工具走内核级注入, 实测每次调用都会让 CDP 通道在本会话内失效**(之后所有 CDP 优先工具都会超时/退化), 必须重启 AI-Fbowser-Mcp.exe 才能恢复; 如后续还要用 CDP 类工具, 请改用 browser_mouse_click / browser_mouse_move / browser_mouse_wheel / browser_key_event", 多属性Schema文本 (属性项JSON ("x", "integer", "X(必填)") + "," + 属性项JSON ("y", "integer", "Y(必填)") + "," + 属性项JSON ("button", "integer", "按键: 0左(默认)/1中/2右, 与按下一致"), "\\"x\\",\\"y\\""))'''

CLICK_PROP_OLD = '''属性项JSON ("button", "integer", "按键: 0左/1中/2右 (默认0)"), "\\"x\\",\\"y\\""))'''
CLICK_PROP_NEW = '''属性项JSON ("button", "integer", "按键: 0左/1中/2右 (默认0)") + "," + 属性项JSON ("delay_ms", "integer", "按下到放开的延时毫秒(默认50, 上限5000; 反爬场景可用更长的按压时长)"), "\\"x\\",\\"y\\""))'''

EDITS = [
    (CORE, '键盘: VIP 三处真正透传 modifiers', KB_OLD, KB_NEW),
    (CORE, '键盘: CEF 退路按语义换算旗标', CEF_OLD, CEF_NEW),
    (CORE, '右键菜单 set 载荷补回逗号(非法 JSON)', CM_OLD, CM_NEW),
    (VIP, '鼠标按下: button + x/y 守卫', PRESS_OLD, PRESS_NEW),
    (VIP, '鼠标放开: button + x/y 守卫', RELEASE_OLD, RELEASE_NEW),
    (VIP, '鼠标单击: delay_ms', CLICK_OLD, CLICK_NEW),
    (SERVER, 'key_event 描述: modifiers 映射', KE_DESC_OLD, KE_DESC_NEW),
    (SERVER, 'key_event schema: modifiers 说明', KE_PROP_OLD, KE_PROP_NEW),
    (SERVER, 'pixel_ratio schema: text→number', PR_OLD, PR_NEW),
    (SERVER, 'vip_mouse_press 注册: 补 button', PRESS_REG_OLD, PRESS_REG_NEW),
    (SERVER, 'vip_mouse_release 注册: 补 button', RELEASE_REG_OLD, RELEASE_REG_NEW),
    (SERVER, 'vip_mouse_click: 补 delay_ms', CLICK_PROP_OLD, CLICK_PROP_NEW),
]


def main():
    print('== 第139轮补丁 A (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-42s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 锚点命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    for path, txt in cache.items():
        n = len(txt.split('\n'))
        print('%s: 行数 %d' % (os.path.basename(path), n))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
