# -*- coding: utf-8 -*-
r"""第139轮补丁 D: 让 `browser_menu_probe` 的右键触发**可靠**(实测脆弱点已定位)。

## 实测(同一实例, 连续三次 arm)
| 调用 | 结果 |
|---|---|
| `{action:"arm"}`(无 trigger 键) | **0.06s 拿到快照**(declared_count=17) |
| `{action:"arm", trigger:false}` | 0.02s 返回"已武装"(正确) |
| `{action:"arm", trigger:true}` | **3.97s 超时**(没等到菜单回调) |

归因: 原生右键菜单**还开着**时, 下一次 CDP 右键只会把菜单关掉, **不会再触发 `即将打开菜单`** ——
而上一次 arm 结束后我们虽然发了 Esc, 但菜单关闭是异步的/有时不生效, 于是"第二次 arm 必然失败"。
(这也解释了 `verify_menu_probe.py` 首轮为何时好时坏。)

## 修法(不引入新机制)
每次派发右键**之前先清场**(Esc + 250ms), 并且**最多尝试 3 次**(每次把 y 挪 12px, 避免落在同一热点);
每次尝试内部有界轮询 1.2 秒。收尾再发一次 Esc 关掉菜单。失败文案如实说明"已尝试 3 次"。

用法: py -3 _audit\_apply_round139d.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

# ── Server: 按键助手(供清场与收尾复用, 避免同一段 CDP 调用抄三遍) ──
HELPER_ANCHOR = '''    # 快捷键文本 → 键码(只取数字位); 与 应用菜单规格 里 accel 的既有解析口径一致。'''
HELPER_NEW = '''    # 菜单探针专用: 向浏览器派发一次按键(Esc 用于关掉原生右键菜单)。
    # 为什么需要独立方法: 清场要在**每次**右键之前做、收尾还要再做一次, 同一段 CDP 调用抄三遍不如收一处。
    方法 菜单探针按键 <公开 静态 @输出名 = "MenuProbeKey" @强制输出 = 真>
    参数 命令ID前缀 <类型 = 文本型 @输出名 = "CommandIDPrefix">
    参数 序号 <类型 = 整数 @输出名 = "SeqNo">
    {
        执行CDP并同步等待 (命令ID前缀 + "_esc" + 到文本 (序号) + "d", "Input.dispatchKeyEvent", "{\\"type\\":\\"keyDown\\",\\"key\\":\\"Escape\\",\\"code\\":\\"Escape\\",\\"windowsVirtualKeyCode\\":27,\\"nativeVirtualKeyCode\\":27}", 3000)
        执行CDP并同步等待 (命令ID前缀 + "_esc" + 到文本 (序号) + "u", "Input.dispatchKeyEvent", "{\\"type\\":\\"keyUp\\",\\"key\\":\\"Escape\\",\\"code\\":\\"Escape\\",\\"windowsVirtualKeyCode\\":27,\\"nativeVirtualKeyCode\\":27}", 3000)
    }

''' + HELPER_ANCHOR

# ── Core: 用"清场 + 最多 3 次尝试"替换原来的单次派发+3秒等待 ──
DISPATCH_OLD = '''            变量 mpX <类型 = 整数>
            mpX = MCP命令服务器.yyjson取整数 (参数JSON, "x")
            如果 (mpX <= 0)
            {
                mpX = 300
            }
            变量 mpY <类型 = 整数>
            mpY = MCP命令服务器.yyjson取整数 (参数JSON, "y")
            如果 (mpY <= 0)
            {
                mpY = 200
            }
            如果 (MCP命令服务器.CDP派发鼠标事件 ("mousePressed", mpX, mpY, "right") == 假 || MCP命令服务器.CDP派发鼠标事件 ("mouseReleased", mpX, mpY, "right") == 假)
            {
                MCP命令服务器.菜单快照已武装 = 假
                返回 (MCP_响应构建.命令失败 (命令ID, MCP命令服务器.CDPInput失败原因文本 ("CDP 右键派发") + " | 替代: 传 trigger:false 后手动右键, 再 action=get"))
            }
            // 有界等待(3 秒): 与 browser_create 的等待循环同写法 —— 显式解锁再延时, 避免持锁阻塞其它请求
            变量 mp等 <类型 = 整数 值 = 0>
            判断循环 (mp等 < 60 && MCP命令服务器.菜单快照JSON == "")
            {
                MCP命令服务器.MCP执行锁.解锁 ()
                MCP命令服务器.MCP可中断延时 (50, 50, 假)
                MCP命令服务器.MCP执行锁.加锁 ()
                mp等 = mp等 + 1
            }
            // 关掉菜单: 否则它会一直挡在页面上(后续点击/读取都会被它吃掉; 关不掉也不影响结果, 如实写在 note 里)
            MCP命令服务器.执行CDP并同步等待 (命令ID + "_esc1", "Input.dispatchKeyEvent", "{\\"type\\":\\"keyDown\\",\\"key\\":\\"Escape\\",\\"code\\":\\"Escape\\",\\"windowsVirtualKeyCode\\":27,\\"nativeVirtualKeyCode\\":27}", 5000)
            MCP命令服务器.执行CDP并同步等待 (命令ID + "_esc2", "Input.dispatchKeyEvent", "{\\"type\\":\\"keyUp\\",\\"key\\":\\"Escape\\",\\"code\\":\\"Escape\\",\\"windowsVirtualKeyCode\\":27,\\"nativeVirtualKeyCode\\":27}", 5000)
            如果 (MCP命令服务器.菜单快照JSON == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "已在(" + 到文本 (mpX) + "," + 到文本 (mpY) + ")派发右键, 但 3 秒内没等到菜单回调 | 可能: 该坐标没有可右键的内容 / 右键菜单被内核屏蔽(见 browser_kernel_menu) / 菜单监控被关 | 替代: trigger:false 手动右键后再 action=get"))
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))'''

DISPATCH_NEW = '''            变量 mpX <类型 = 整数>
            mpX = MCP命令服务器.yyjson取整数 (参数JSON, "x")
            如果 (mpX <= 0)
            {
                mpX = 300
            }
            变量 mpY <类型 = 整数>
            mpY = MCP命令服务器.yyjson取整数 (参数JSON, "y")
            如果 (mpY <= 0)
            {
                mpY = 200
            }
            // 实测脆弱点: 原生菜单**还开着**时, 下一次 CDP 右键只会把菜单关掉, 不会再触发 `即将打开菜单`
            // (同一实例连续三次 arm: 6.1 第一次成功、第二次失败、第三次失败) —— 故每次派发前先**清场**,
            // 并且最多尝试 3 次(每次把 y 挪 12px, 避免始终落在同一热点)。每次尝试内部有界轮询 1.2 秒。
            变量 mp尝试 <类型 = 整数 值 = 0>
            变量 mp已捕获 <类型 = 逻辑型 值 = 假>
            变量 mp派发失败 <类型 = 逻辑型 值 = 假>
            判断循环 (mp尝试 < 3 && mp已捕获 == 假 && mp派发失败 == 假)
            {
                MCP命令服务器.菜单探针按键 (命令ID, mp尝试, )
                MCP命令服务器.MCP执行锁.解锁 ()
                MCP命令服务器.MCP可中断延时 (250, 250, 假)
                MCP命令服务器.MCP执行锁.加锁 ()
                如果 (MCP命令服务器.CDP派发鼠标事件 ("mousePressed", mpX, mpY + mp尝试 * 12, "right") == 假 || MCP命令服务器.CDP派发鼠标事件 ("mouseReleased", mpX, mpY + mp尝试 * 12, "right") == 假)
                {
                    mp派发失败 = 真
                }
                否则
                {
                    变量 mp轮询 <类型 = 整数 值 = 0>
                    判断循环 (mp轮询 < 24 && MCP命令服务器.菜单快照JSON == "")
                    {
                        MCP命令服务器.MCP执行锁.解锁 ()
                        MCP命令服务器.MCP可中断延时 (50, 50, 假)
                        MCP命令服务器.MCP执行锁.加锁 ()
                        mp轮询 = mp轮询 + 1
                    }
                    如果 (MCP命令服务器.菜单快照JSON != "")
                    {
                        mp已捕获 = 真
                    }
                }
                mp尝试 = mp尝试 + 1
            }
            // 收尾: 无论成功失败都关掉菜单(否则它会一直挡在页面上, 后续点击/读取都被它吃掉)
            MCP命令服务器.菜单探针按键 (命令ID, 99, )
            如果 (mp派发失败)
            {
                MCP命令服务器.菜单快照已武装 = 假
                返回 (MCP_响应构建.命令失败 (命令ID, MCP命令服务器.CDPInput失败原因文本 ("CDP 右键派发") + " | 替代: 传 trigger:false 后手动右键, 再 action=get"))
            }
            如果 (mp已捕获 == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "已在(" + 到文本 (mpX) + "," + 到文本 (mpY) + ")附近尝试 " + 到文本 (mp尝试) + " 次右键, 都没等到菜单回调 | 可能: 该坐标没有可右键的内容 / 右键菜单被内核屏蔽(见 browser_kernel_menu) / 菜单监控被关 | 本工具仍处于**已武装**状态, 你手动右键一次后 action=get 也能取到"))
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))'''

EDITS = [(SERVER, 'D1 新增 菜单探针按键 助手', HELPER_ANCHOR, HELPER_NEW),
         (CORE, 'D2 清场 + 3 次尝试', DISPATCH_OLD, DISPATCH_NEW)]


def main():
    print('== 第139轮补丁 D (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-32s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    for path, txt in cache.items():
        print('%s: 行数 %d' % (os.path.basename(path), len(txt.split('\n'))))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
