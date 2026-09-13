# -*- coding: utf-8 -*-
r"""第139轮补丁 C(Core 侧): `browser_context_menu` 支持索引类/wipe/experimental + 新增 `browser_menu_probe` 分派。
配套补丁 B 落 Server/Events 侧(快照字段与方法、索引写分支、注册)。用法: py -3 _audit\_apply_round139c.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
APPLY = '--apply' in sys.argv

# C1 类型白名单: 加 索引类 + wipe
T1_OLD = '''                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub" && MCP命令服务器.是菜单修改类 (cm类型) == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行类型非法: " + cm类型 + " | 创建类: item/check/radio/sep/sub; 修改类: del/relabel/vis/dis/mark/accel/noaccel"))
                    }'''
T1_NEW = '''                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub" && cm类型 != "wipe" && MCP命令服务器.是菜单修改类 (cm类型) == 假 && MCP命令服务器.是菜单索引类 (cm类型) == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行类型非法: " + cm类型 + " | 创建类(按命令ID新建): item/check/radio/sep/sub | 修改类(按命令ID改已有项): del/relabel/vis/dis/mark/accel/noaccel | 索引类(按位置改, **唯一能作用于浏览器默认菜单项的通道**): accelat/noaccelat/colorat/checkat/fontat | 清空本次菜单: wipe(需 confirm_wipe:true 且必须唯一一行)"))
                    }'''

# C2 索引类: 第3列是索引(不是命令ID) —— 范围守卫 + 规范化回写 + 到循环尾
T2_OLD = '''                    变量 cm是修改类 <类型 = 逻辑型>
                    cm是修改类 = MCP命令服务器.是菜单修改类 (cm类型)
                    变量 cmID <类型 = 整数>'''
T2_NEW = '''                    变量 cm是修改类 <类型 = 逻辑型>
                    cm是修改类 = MCP命令服务器.是菜单修改类 (cm类型)
                    变量 cm是索引类 <类型 = 逻辑型>
                    cm是索引类 = MCP命令服务器.是菜单索引类 (cm类型)
                    // 索引类: 第3列是**索引**(纯位置寻址) —— 浏览器默认菜单项的命令ID无法反查, 只有位置寻址能改到它们。
                    // 故这里既不要求ID存在, 也不做 26500..28500 区间校验; 但要挡住"把索引列填成命令ID"这种错位。
                    如果 (cm是索引类)
                    {
                        变量 cm索引 <类型 = 整数>
                        cm索引 = 文本到整数 (cm段.取成员 (2))
                        如果 (cm索引 >= 100 && cm索引 <= 28500)
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是索引类(" + cm类型 + ")但第3列填的像**命令ID**(" + 到文本 (cm索引) + ") | 索引类第3列是**索引**(从0开始的位置号; 用 browser_menu_probe 可读到实际条目数) | 想按命令ID改请用 accel/noaccel/del/relabel/vis/dis/mark"))
                        }
                        如果 (cm索引 < 0 || cm索引 > 500)
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行索引越界: " + 到文本 (cm索引) + " | 索引从0开始, 上限500"))
                        }
                        变量 cm索引行 <类型 = 文本型>
                        cm索引行 = cm类型 + "|" + cm段.取成员 (1) + "|" + 到文本 (cm索引)
                        如果 (cm段.取成员数 () >= 4)
                        {
                            cm索引行 = cm索引行 + "|" + cm段.取成员 (3)
                        }
                        如果 (cm段.取成员数 () >= 5)
                        {
                            cm索引行 = cm索引行 + "|" + cm段.取成员 (4)
                        }
                        如果 (cm段.取成员数 () >= 6)
                        {
                            cm索引行 = cm索引行 + "|" + cm段.取成员 (5)
                        }
                        如果 (cm新规格 == "")
                        {
                            cm新规格 = cm索引行
                        }
                        否则
                        {
                            cm新规格 = cm新规格 + "\\n" + cm索引行
                        }
                        cm有效数 = cm有效数 + 1
                        到循环尾
                    }
                    变量 cmID <类型 = 整数>'''

# C3 wipe 检测 + 守卫
T3A_OLD = '''                cm警告 = ""'''
T3A_NEW = '''                cm警告 = ""
                变量 cm含wipe <类型 = 逻辑型 值 = 假>'''
T3B_OLD = '''                    cm有效数 = cm有效数 + 1
                }
                如果 (cm有效数 == 0)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "规格里没有有效条目"))
                }'''
T3B_NEW = '''                    如果 (cm类型 == "wipe")
                    {
                        cm含wipe = 真
                    }
                    cm有效数 = cm有效数 + 1
                }
                // wipe 是**破坏性**动作: 必须唯一一行 + 显式确认。理由(项目既有禁令的延伸):
                // 规格为空时清空菜单会把 CEF 默认菜单整片抹掉 —— 用户会以为右键坏了; 且每次右键都是新模型,
                // 所以"清空"只影响本次。要的是"屏蔽右键"应当用 browser_kernel_menu action=disable。
                如果 (cm含wipe)
                {
                    如果 (cm有效数 > 1)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "wipe 必须是规格里**唯一**的一行(当前共 " + 到文本 (cm有效数) + " 行) | 清空与其它行混用语义不明"))
                    }
                    如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "confirm_wipe") == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "wipe 会清空**本次右键**的整个菜单: 右键后一个条目都没有(用户会以为右键坏了); 下一次右键会恢复默认菜单 | 想要的是屏蔽右键请用 browser_kernel_menu action=disable | 确认清空请显式传 confirm_wipe:true"))
                    }
                }
                如果 (cm有效数 == 0)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "规格里没有有效条目"))
                }'''
T3C_OLD = '''                MCP命令服务器.菜单规格文本 = cm新规格
                变量 cmEnable <类型 = 逻辑型>'''
T3C_NEW = '''                MCP命令服务器.菜单规格文本 = cm新规格
                // 实验性动作(fontat)默认拒绝, 只在本行规格显式 experimental:true 时放行(单次生效, 下次 set 自动复位)
                MCP命令服务器.菜单允许实验字体 = MCP命令服务器.yyjson取逻辑 (参数JSON, "experimental")
                变量 cmEnable <类型 = 逻辑型>'''

# C4 set 回执补一句"本次含索引类/wipe"提示
T4_OLD = '''                cm提示 = "菜单规格已预置(启用=" + 选择 (cmEnable, "true", "false") + ", 条目=" + 到文本 (cm有效数) + ", 含命令ID条目=" + 到文本 (cm已用ID) + ") | 每次右键时由 CEF 回调施加, 本工具无法即时修改已打开的菜单 | 已自动开启菜单事件监控"'''
T4_NEW = '''                cm提示 = "菜单规格已预置(启用=" + 选择 (cmEnable, "true", "false") + ", 条目=" + 到文本 (cm有效数) + ", 含命令ID条目=" + 到文本 (cm已用ID) + ") | 每次右键时由 CEF 回调施加, 本工具无法即时修改已打开的菜单 | 已自动开启菜单事件监控"
                如果 (cm含wipe)
                {
                    cm提示 = cm提示 + " | ⚠ 含 wipe: 右键后菜单会被清空(仅本次)"
                }'''

# C5 get 载荷补 verify_unavailable
T5_OLD = '''+ ",\\"verify_mismatch\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\\",\\"apply_failed\\":\\""'''
T5_NEW = '''+ ",\\"verify_mismatch\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\\",\\"verify_unavailable\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单未验证说明) + "\\",\\"apply_failed\\":\\""'''

# C6 新增 browser_menu_probe 分派(紧接 context_menu 分支之后)
T6_OLD = '''        // === 数据提取: 链接/图片/表格 结构化JSON ===
        否则 (方法名 == "browser_extract")'''
T6_NEW = '''        // === 右键菜单**只读实况探针** ===
        // 为什么需要: 规格类工具只能"写", 而默认菜单项改不动 —— 代理看不见菜单里到底有什么, 只能靠猜。
        // 本工具在 CEF 回调内(模型有效期内)、**施加规格之前**读: 条目数 + 每项是否带快捷键提示。
        // 可读范围是类库能力边界(`是否可见/是否选中/取菜单类型` 只收命令ID, 对默认项读不到), 故不谎报更多。
        否则 (方法名 == "browser_menu_probe")
        {
            变量 mpAction <类型 = 文本型>
            mpAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            如果 (mpAction == "")
            {
                mpAction = "arm"
            }
            如果 (mpAction == "clear")
            {
                MCP命令服务器.菜单快照JSON = ""
                MCP命令服务器.菜单快照时刻 = ""
                MCP命令服务器.菜单快照已武装 = 假
                返回 (MCP_响应构建.命令成功 (命令ID, "菜单快照已清空(幂等)"))
            }
            如果 (mpAction == "get")
            {
                如果 (MCP命令服务器.菜单快照JSON == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "还没有快照 | 先 action=arm(会自动右键触发一次): browser_menu_probe {action:\\"arm\\"} | 若你已手动右键过仍为空, 说明武装没生效(例如菜单被内核屏蔽, 见 browser_kernel_menu)"))
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))
            }
            如果 (mpAction != "arm")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + mpAction + " | 支持: arm(默认)/get/clear"))
            }
            变量 mpBrowser <类型 = 类_FBrowser_浏览器>
            mpBrowser = MCP命令服务器.取主浏览器 ()
            如果 (mpBrowser.是否为空 () || mpBrowser.是否已关闭 ())
            {
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
            }
            MCP命令服务器.菜单快照JSON = ""
            MCP命令服务器.菜单快照时刻 = ""
            MCP命令服务器.菜单快照已武装 = 真
            变量 mpTrigger <类型 = 逻辑型>
            mpTrigger = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "trigger", 真)
            如果 (mpTrigger == 假)
            {
                返回 (MCP_响应构建.命令成功 (命令ID, "已武装: 请现在手动右键一次(或改用 trigger:true 自动右键), 然后 action=get 取快照"))
            }
            变量 mpX <类型 = 整数>
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
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, MCP命令服务器.菜单快照JSON))
        }
        // === 数据提取: 链接/图片/表格 结构化JSON ===
        否则 (方法名 == "browser_extract")'''

EDITS = [('C1 类型白名单: 索引类/wipe', T1_OLD, T1_NEW),
         ('C2 索引类: 第3列=索引守卫+回写', T2_OLD, T2_NEW),
         ('C3a wipe 检测变量', T3A_OLD, T3A_NEW),
         ('C3b wipe 唯一行+confirm 守卫', T3B_OLD, T3B_NEW),
         ('C3c experimental 单次放行', T3C_OLD, T3C_NEW),
         ('C4 set 回执提示', T4_OLD, T4_NEW),
         ('C5 get 载荷补 verify_unavailable', T5_OLD, T5_NEW),
         ('C6 新增 browser_menu_probe 分派', T6_OLD, T6_NEW)]


def main():
    print('== 第139轮补丁 C (%s) ==' % ('应用' if APPLY else '预演'))
    txt = io.open(CORE, encoding='utf-8', newline='').read()
    n0 = len(txt.split('\n'))
    for tag, old, new in EDITS:
        if old not in txt:
            print('   · %-36s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        txt = txt.replace(old, new, 1)
        print('   · %s' % tag)
    print('MCP_Server_Core.wsv: 行数 %d -> %d' % (n0, len(txt.split('\n'))))
    if APPLY:
        io.open(CORE, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
