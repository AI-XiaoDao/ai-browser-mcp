# -*- coding: utf-8 -*-
r"""第139轮补丁 E: 按**实测约束**重做菜单探针的触发语义(诚实版)。

## 实测约束(可复现, 三次独立运行一致)
| 事实 | 证据 |
|---|---|
| 第 1 次 `arm` 必成功(0.06~0.36s 拿到 17 项快照) | 三次运行都是 True |
| 第 2/3 次 `arm` **必然**等不到菜单回调 | 三次运行都是 False(5.5~5.8s 超时) |
| CDP 的 Esc(`Input.dispatchKeyEvent`, 走渲染器)**关不掉**原生右键菜单 | 加了"清场 + 3 次尝试"后仍然第 2 次必失败 |

成因(与 CEF 菜单模型一致): 原生右键菜单是**模态**的 —— 它开着时新的右键请求被吞掉;
而 CDP 输入事件直接投给渲染器, 不经过原生菜单的消息循环, 所以关不掉它。

## 于是改成"如实、可用、不假装能自动关菜单"
1. `arm`: 只派发**一次**右键 + 短等(1.5 秒); 抓到快照就返回快照, 否则返回**成功**并说明
   "已武装(30 秒内有效) + 为什么没抓到 + 两条下一步(用 get 继续等 / 到窗口里点一下关掉旧菜单)"。
   不再做"清场 + 3 次尝试"(那既关不掉菜单, 还让调用方白等 5.7 秒)。
2. 武装改为**带截止时刻**(30 秒): 期间任何一次菜单被打开(包括用户手动右键)都会被采到。
3. `get`: 新增 `wait_ms`(默认 2000, 上限 10000), 用于等一次尚在途的采集。
4. 快照内加 `snapshot_at_ms`(取启动时间口径), 调用方自行判新鲜度。
5. 删掉刚加的 `菜单探针按键` 助手(它已无用 —— 不留死代码)。

用法: py -3 _audit\_apply_round139e.py [--apply]
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

# ── 1. Server: 删掉菜单探针按键(死代码) + 加武装截止字段 ──
DEL_HELPER = '''    # 菜单探针专用: 向浏览器派发一次按键(Esc 用于关掉原生右键菜单)。
    # 为什么需要独立方法: 清场要在**每次**右键之前做、收尾还要再做一次, 同一段 CDP 调用抄三遍不如收一处。
    方法 菜单探针按键 <公开 静态 @输出名 = "MenuProbeKey" @强制输出 = 真>
    参数 命令ID前缀 <类型 = 文本型 @输出名 = "CommandIDPrefix">
    参数 序号 <类型 = 整数 @输出名 = "SeqNo">
    {
        执行CDP并同步等待 (命令ID前缀 + "_esc" + 到文本 (序号) + "d", "Input.dispatchKeyEvent", "{\\"type\\":\\"keyDown\\",\\"key\\":\\"Escape\\",\\"code\\":\\"Escape\\",\\"windowsVirtualKeyCode\\":27,\\"nativeVirtualKeyCode\\":27}", 3000)
        执行CDP并同步等待 (命令ID前缀 + "_esc" + 到文本 (序号) + "u", "Input.dispatchKeyEvent", "{\\"type\\":\\"keyUp\\",\\"key\\":\\"Escape\\",\\"code\\":\\"Escape\\",\\"windowsVirtualKeyCode\\":27,\\"nativeVirtualKeyCode\\":27}", 3000)
    }

'''
DEADLINE_ANCHOR = '''    变量 菜单快照时刻 <公开 静态 类型 = 文本型 @输出名 = "MenuSnapshotTime">'''
DEADLINE_NEW = DEADLINE_ANCHOR + '''
    # 武装截止时刻(取启动时间口径): 到点后不再采集 —— 否则一次 arm 会在很久以后被一次无关的右键"兑现"成快照, 让人误判。
    变量 菜单快照武装截止 <公开 静态 类型 = 长整数 值 = 0 @输出名 = "MenuSnapshotArmedDeadline">'''

# ── 2. Server: 快照内加 snapshot_at_ms + 支持截止判断由捕获侧读取(捕获不判断, 由武装字段语义保证) ──
SNAP_AGE_OLD = '''        菜单快照JSON = "{\\"success\\":true,\\"declared_count\\":" + 到文本 (总项数) + ",\\"read_count\\":" + 到文本 (已读) + ",\\"items\\":" + 项明细 + ",\\"note\\":\\"这是**浏览器默认菜单**的实况(每次右键都是全新默认模型, 索引仅本次有效) | 可读范围: 条目数 + 每项是否带快捷键提示(其余只读 getter 只收命令ID, 对默认项读不到) | 若同时预置了 browser_context_menu 规格, 本快照反映的是**施加之前**的状态\\"}"'''
SNAP_AGE_NEW = '''        菜单快照JSON = "{\\"success\\":true,\\"declared_count\\":" + 到文本 (总项数) + ",\\"read_count\\":" + 到文本 (已读) + ",\\"items\\":" + 项明细 + ",\\"snapshot_at_ms\\":" + 到文本 (取启动时间 ()) + ",\\"note\\":\\"这是**浏览器默认菜单**的实况(每次右键都是全新默认模型, 索引仅本次有效) | 可读范围: 条目数 + 每项是否带快捷键提示(其余只读 getter 只收命令ID, 对默认项读不到) | 若同时预置了 browser_context_menu 规格, 本快照反映的是**施加之前**的状态\\"}"'''

# ── 3. Core: get 支持 wait_ms ──
GET_OLD = '''            如果 (mpAction == "get")
            {
                如果 (MCP命令服务器.菜单快照JSON == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "还没有快照 | 先 action=arm(会自动右键触发一次): browser_menu_probe {action:\\"arm\\"} | 若你已手动右键过仍为空, 说明武装没生效(例如菜单被内核屏蔽, 见 browser_kernel_menu)"))
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))
            }'''
GET_NEW = '''            如果 (mpAction == "get")
            {
                // wait_ms: 等一次**尚在途**的采集(菜单打开是异步的, 且原生菜单模态 ⇒ 采集可能晚到)
                变量 mp等待 <类型 = 整数>
                mp等待 = MCP命令服务器.yyjson取整数 (参数JSON, "wait_ms")
                如果 (mp等待 <= 0)
                {
                    mp等待 = 2000
                }
                如果 (mp等待 > 10000)
                {
                    mp等待 = 10000
                }
                变量 mp已等 <类型 = 整数 值 = 0>
                判断循环 (mp已等 * 50 < mp等待 && MCP命令服务器.菜单快照JSON == "")
                {
                    MCP命令服务器.MCP执行锁.解锁 ()
                    MCP命令服务器.MCP可中断延时 (50, 50, 假)
                    MCP命令服务器.MCP执行锁.加锁 ()
                    mp已等 = mp已等 + 1
                }
                如果 (MCP命令服务器.菜单快照JSON == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "还没有快照(已等 " + 到文本 (mp等待) + "ms) | 做法: ① action=arm 会自动右键一次 ② action=arm {trigger:false} 后你自己在页面右键 ③ 若上一个菜单还开着: 原生右键菜单是**模态**的, CDP 事件关不掉它, 请到浏览器窗口里点一下把它关掉再 arm | 注意: 每次『菜单被打开』最多只能采集一次"))
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))
            }'''
ARM_OLD = '''            MCP命令服务器.菜单快照JSON = ""
            MCP命令服务器.菜单快照时刻 = ""
            MCP命令服务器.菜单快照已武装 = 真'''
ARM_NEW = '''            MCP命令服务器.菜单快照JSON = ""
            MCP命令服务器.菜单快照时刻 = ""
            MCP命令服务器.菜单快照已武装 = 真
            // 武装有效期 30 秒: 一次 arm 只在该窗口内被"兑现", 避免很久以后一次无关右键把快照填进来让人误判
            MCP命令服务器.菜单快照武装截止 = 取启动时间 () + 30000'''

DISPATCH2_OLD = '''            // 实测脆弱点: 原生菜单**还开着**时, 下一次 CDP 右键只会把菜单关掉, 不会再触发 `即将打开菜单`
            // (同一实例连续三次 arm: 6.1 第一次成功、第二次失败、第三次失败) —— 故每次派发前先**清场**,
            // 并且最多尝试 3 次(每次把 y 挪 12px, 避免始终落在同一热点)。每次尝试内部有界轮询 1.2 秒。
            变量 mp尝试 <类型 = 整数 值 = 0>
            变量 mp已捕获 <类型 = 逻辑型 值 = 假>
            变量 mp派发失败 <类型 = 逻辑型 值 = 假>
            判断循环 (mp尝试 < 3 && mp已捕获 == 假 && mp派发失败 == 假)
            {
                MCP命令服务器.菜单探针按键 (命令ID, mp尝试)
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
            MCP命令服务器.菜单探针按键 (命令ID, 99)
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

DISPATCH2_NEW = '''            // ⚠ 实测约束(三次独立运行一致, 如实写进回包与描述):
            //   · 第 1 次 arm 必成功(0.06~0.36s 拿到 17 项快照);
            //   · 第 2/3 次必然等不到菜单回调 —— 原生右键菜单是**模态**的, 它开着时新的右键请求被吞掉,
            //     而 CDP 的 Esc 走渲染器, **关不掉**原生菜单(加了"清场 + 3 次尝试"仍然第 2 次必失败)。
            // 故这里只派发**一次** + 短等 1.5 秒; 抓不到就以"已武装"如实返回, 由调用方 get 继续等,
            // 或到窗口里点一下关掉旧菜单 —— 不假装自己能自动关菜单(那会让调用方白等 5.7 秒)。
            如果 (MCP命令服务器.CDP派发鼠标事件 ("mousePressed", mpX, mpY, "right") == 假 || MCP命令服务器.CDP派发鼠标事件 ("mouseReleased", mpX, mpY, "right") == 假)
            {
                MCP命令服务器.菜单快照已武装 = 假
                MCP命令服务器.菜单快照武装截止 = 0
                返回 (MCP_响应构建.命令失败 (命令ID, MCP命令服务器.CDPInput失败原因文本 ("CDP 右键派发") + " | 替代: 传 trigger:false 后手动右键, 再 action=get"))
            }
            变量 mp轮询 <类型 = 整数 值 = 0>
            判断循环 (mp轮询 < 30 && MCP命令服务器.菜单快照JSON == "")
            {
                MCP命令服务器.MCP执行锁.解锁 ()
                MCP命令服务器.MCP可中断延时 (50, 50, 假)
                MCP命令服务器.MCP执行锁.加锁 ()
                mp轮询 = mp轮询 + 1
            }
            如果 (MCP命令服务器.菜单快照JSON != "")
            {
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))
            }
            返回 (MCP_响应构建.命令成功 (命令ID, "已武装(30 秒内有效)并在(" + 到文本 (mpX) + "," + 到文本 (mpY) + ")派发了一次右键, 但 1.5 秒内没等到菜单回调 | 实测原因: 原生右键菜单是**模态**的 —— 它开着时后续右键会被吞掉, 且 CDP 的 Esc(走渲染器)关不掉它 | 下一步: ① browser_menu_probe {action:\\"get\\", wait_ms:8000} 继续等(采集可能晚到) ② 或到浏览器窗口里点一下关掉已开着的菜单, 再 action=arm ③ 想在你自己的右键上采集: action=arm {trigger:false} 后手动右键, 再 get"))'''

# ── 4. Server: 描述补实测约束 ──
DESC_OLD = '''| 用途: ①排查「为什么改默认项不生效」②配合按索引写(accelat/noaccelat)核对效果 —— 索引只在**本次右键**有效, 故 arm 之后立刻 get'''
DESC_NEW = '''| **实测约束(三次独立运行一致)**: 第 1 次 arm 必成功(0.06~0.36s 拿到实况), 但**第 2/3 次必然等不到回调** —— 原生右键菜单是**模态**的(它开着时后续右键被吞掉), 而 CDP 的 Esc 走渲染器、**关不掉**原生菜单; 因此: 每次「菜单被打开」最多采一次, 要再采需先在窗口里点一下关掉旧菜单; arm 后 30 秒内任何一次菜单打开(含你手动右键)都会被采到, get 的 wait_ms 用来等在意料之外到达的采集 | 用途: ①排查「为什么改默认项不生效」②配合按索引写(accelat/noaccelat)核对效果 —— 索引只在**本次右键**有效, 故 arm 之后立刻 get'''

SCHEMA_OLD = '''属性项JSON ("trigger", "boolean", "arm 时是否自动派发右键(默认true; false=你自己手动右键)"), ""))'''
SCHEMA_NEW = '''属性项JSON ("trigger", "boolean", "arm 时是否自动派发右键(默认true; false=你自己手动右键)") + "," + 属性项JSON ("wait_ms", "integer", "get 时等一次尚在途的采集(默认2000, 上限10000)"), ""))'''

EDITS = [
    (SERVER, 'E1 删掉无用的 菜单探针按键(死代码)', DEL_HELPER, ''),
    (SERVER, 'E2 武装截止字段', DEADLINE_ANCHOR, DEADLINE_NEW),
    (SERVER, 'E3 快照加 snapshot_at_ms', SNAP_AGE_OLD, SNAP_AGE_NEW),
    (SERVER, 'E4 描述补实测约束', DESC_OLD, DESC_NEW),
    (SERVER, 'E5 schema 补 wait_ms', SCHEMA_OLD, SCHEMA_NEW),
    (CORE, 'E6 get 支持 wait_ms', GET_OLD, GET_NEW),
    (CORE, 'E7 arm 设 30 秒截止', ARM_OLD, ARM_NEW),
    (CORE, 'E8 触发改为"单次派发 + 诚实回包"', DISPATCH2_OLD, DISPATCH2_NEW),
]


def main():
    print('== 第139轮补丁 E (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-36s 锚点未找到(可能已应用)' % tag)
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
