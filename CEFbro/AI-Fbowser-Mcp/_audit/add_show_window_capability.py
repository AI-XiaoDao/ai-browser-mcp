# -*- coding: utf-8 -*-
"""补齐能力面反查确认的真缺口: 显示/隐藏窗口 (类库 `显示隐藏窗口`)。

依据:
  · 只读复核(报告 §95.7/§96.2 已独立确认): 本项目是控制台程序, 创建浏览器时 父窗口句柄=0,
    用户看到的窗口**就是浏览器窗口本身** —— 故"窗口由主窗口统一管理/嵌入式GUI不支持"的前提不成立。
  · 类库确有 `显示隐藏窗口 (显示隐藏)` (FBroLib.wsv:1071) -> FBroHsBrowserHost_ShowWindows, 不需要 HWND。
  · 窗口能力复核把它列为 **REAL GAP**(全 src 0 命中、台账无 show/hide 类工具)。
  · 可验证: 项目**已经在用** `browser.取窗口属性 (窗口样式_GWL_STYLE)`(MCP_Server_System.wsv:67/104),
    而 WS_VISIBLE 就是这个位掩码里的一位(0x10000000 = 268435456) —— 于是"隐藏/显示"能**回读验证**,
    不必靠猜(这符合本项目"写操作要有回读验证"的不变量)。

三处改动: 工具注册 + 命令注册表 + 派发分支。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '显示隐藏窗口能力-写入前')

REG_ANCHOR = '        命令注册表.置整数值 ("browser_move_window", 1030)'
TOOL_ANCHOR = '        添加工具JSON ("browser_move_window"'
CORE_ANCHOR = '        否则 (方法名 == "browser_set_auto_resize")'

REG_NEW = '\n'.join([
    REG_ANCHOR,
    '        命令注册表.置整数值 ("browser_show_window", 1031)',
])

TOOL_NEW = '\n'.join([
    '        添加工具JSON ("browser_show_window", "显示/隐藏浏览器窗口。**已实现**: 经类库 显示隐藏窗口 '
    '调用宿主 ShowWindows(不需 HWND), 并用 GWL_STYLE 的 WS_VISIBLE 位**回读验证**; 位没变成请求的状态就如实报 '
    'verified=false, 不谎报成功。说明: 用户看到的窗口就是浏览器窗口本身(本项目为控制台程序, 浏览器以桌面为父窗口), '
    '所以隐藏后**你需要再调一次 visible:true 把它显示回来**", '
    '多属性Schema文本 (属性项JSON ("visible", "boolean", "true=显示窗口 / false=隐藏窗口 | 必填(缺省语义不明, 不接受缺省)"), "\\"visible\\""))',
    TOOL_ANCHOR,
])

BRANCH = '\n'.join([
    '        否则 (方法名 == "browser_show_window")',
    '        {',
    '            // ★ 补能力(能力面反查确认的真缺口): 类库 显示隐藏窗口(显示隐藏) -> FBroHsBrowserHost_ShowWindows。',
    '            //   原"嵌入式GUI浏览器窗口由主窗口统一管理"的前提已被推翻(控制台程序, 父窗口句柄=0,',
    '            //   用户看到的窗口就是浏览器窗口本身), 故该能力可做到。',
    '            //   验证: 回读 GWL_STYLE 的 WS_VISIBLE 位(0x10000000)前后对比 —— 项目已在用 取窗口属性。',
    '            如果 (MCP命令服务器.参数键存在 (参数JSON, "visible") == 假)',
    '            {',
    '                返回 (MCP_响应构建.命令失败 (命令ID, "visible 不能省略 | true=显示窗口 / false=隐藏窗口 | 缺省语义不明, 故不接受缺省"))',
    '            }',
    '            变量 swBrowser <类型 = 类_FBrowser_浏览器>',
    '            swBrowser = MCP命令服务器.取主浏览器 ()',
    '            如果 (swBrowser.是否为空 () == 假 && swBrowser.是否已关闭 () == 假)',
    '            {',
    '                变量 sw目标 <类型 = 逻辑型>',
    '                sw目标 = MCP命令服务器.yyjson取逻辑 (参数JSON, "visible")',
    '                变量 sw前 <类型 = 整数>',
    '                sw前 = swBrowser.取窗口属性 (MCP_常量.窗口样式_GWL_STYLE)',
    '                swBrowser.显示隐藏窗口 (sw目标)',
    '                MCP命令服务器.MCP可中断延时 (250)',
    '                变量 sw后 <类型 = 整数>',
    '                sw后 = swBrowser.取窗口属性 (MCP_常量.窗口样式_GWL_STYLE)',
    '                变量 sw可见前 <类型 = 逻辑型>',
    '                sw可见前 = (位与 (sw前, 268435456) != 0)',
    '                变量 sw可见后 <类型 = 逻辑型>',
    '                sw可见后 = (位与 (sw后, 268435456) != 0)',
    '                变量 sw结果 <类型 = YYJSON对象类>',
    '                sw结果.创建自文本 ("{}")',
    '                sw结果.加入逻辑值成员 ("requested_visible", sw目标)',
    '                sw结果.加入逻辑值成员 ("visible_before", sw可见前)',
    '                sw结果.加入逻辑值成员 ("visible_after", sw可见后)',
    '                sw结果.加入整数成员 ("style_before", sw前)',
    '                sw结果.加入整数成员 ("style_after", sw后)',
    '                如果 (sw可见后 == sw目标)',
    '                {',
    '                    sw结果.加入逻辑值成员 ("verified", 真)',
    '                    sw结果.加入文本成员 ("message", "窗口可见性已按请求设置(回读 GWL_STYLE 的 WS_VISIBLE 位确认)")',
    '                }',
    '                否则',
    '                {',
    '                    sw结果.加入逻辑值成员 ("verified", 假)',
    '                    sw结果.加入文本成员 ("message", "已调用类库 显示隐藏窗口, 但回读 GWL_STYLE 的 WS_VISIBLE 位未变成请求的状态 | 可能被宿主/桌面环境约束 | 以 style_before/style_after 为准, 不谎报成功")',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, sw结果.到可读文本 (YYJSON格式化选项.压缩)))',
    '            }',
    '            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))',
    '        }',
    CORE_ANCHOR,
])


def main():
    srv = io.open(SRV, encoding='utf-8', newline='').read()
    core = io.open(CORE, encoding='utf-8', newline='').read()
    checks = [("SRV 命令注册表锚点", srv, REG_ANCHOR),
              ("SRV 工具注册锚点", srv, TOOL_ANCHOR),
              ("CORE 派发锚点", core, CORE_ANCHOR)]
    for label, txt, a in checks:
        n = txt.count(a)
        print("[%-18s] 出现 %d 次" % (label, n))
        if n != 1:
            print("  !! 预期 1 次, 中止")
            return 1
    if 'browser_show_window' in srv or 'browser_show_window' in core:
        print("!! 似乎已添加过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, CORE):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    srv = srv.replace(REG_ANCHOR, REG_NEW).replace(TOOL_ANCHOR, TOOL_NEW)
    core = core.replace(CORE_ANCHOR, BRANCH)
    io.open(SRV, 'w', encoding='utf-8', newline='').write(srv)
    io.open(CORE, 'w', encoding='utf-8', newline='').write(core)
    print("OK: 已加入 browser_show_window (注册 + 命令注册表 + 派发分支)")
    for p in (SRV, CORE):
        raw = io.open(p, 'rb').read()
        print("复核 %-22s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
