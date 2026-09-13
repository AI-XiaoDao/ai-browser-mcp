# -*- coding: utf-8 -*-
"""补齐两个"恒失败"的窗口能力(原为假前提导致的 CAPABILITY 拒绝)。

前提纠正(已由主代理独立确认): 本项目是 /SUBSYSTEM:CONSOLE 程序, 创建浏览器时
`窗口信息.父窗口句柄 = 0`(src/main.wsv, 以桌面为父窗口), 用户看到的窗口**就是浏览器窗口本身**。
故"嵌入式GUI浏览器不支持…由主窗口自动管理"的拒绝文案与代码事实不符。

类库确有对应 API(只读复核, 均不需 HWND —— 宿主经 CefBrowserHost 隐式定位窗口):
  · 移动窗口 (左边,顶边,宽度,高度,是否重画=假) -> FBroHsBrowserHost_MoveWindow
  · 置自动调整大小 (启用,最小高度,最小宽度,最大高度,最大宽度) -> FBroHsBrowserHost_SetAutoResizeEnabled
  且生成物证据显示这两个方法**从未被引用过**(generated-cpp 里 0 命中), 属真缺口。

本脚本:
  1) Core: browser_move_window 由"恒失败"改为真实调用 + CDP 回读验证(Browser.getWindowForTarget
     直接返回 bounds, 一次调用即可回读), 验证不到就如实报 verified=false;
  2) Core: browser_set_auto_resize 由"恒失败"改为真实调用(类库无返回值 -> 只能报"已调用", 不假装生效);
  3) MCP_Server: 修掉两条误导性描述; 并给 browser_set_auto_resize **补上 schema**(原来根本没有, 无法收参)。
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
BAK = os.path.join(ROOT, '备份', '窗口能力补齐-写入前')
B = chr(92)
Q = chr(34)

# ---------------- 1) browser_move_window 实现 ----------------
MW_OLD = '\n'.join([
    '        否则 (方法名 == "browser_move_window")',
    '        {',
    '            返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 嵌入式GUI浏览器不支持 move_window | 窗口尺寸由主窗口自动管理"))',
    '        }',
])
MW_NEW = '\n'.join([
    '        否则 (方法名 == "browser_move_window")',
    '        {',
    '            // ★ 补能力 + 诚实性: 原来这里恒失败, 文案称"嵌入式GUI浏览器不支持…由主窗口自动管理"。',
    '            //   该前提与代码事实不符 —— 本项目是控制台程序, 创建浏览器时 父窗口句柄=0(以桌面为父),',
    '            //   用户看到的窗口就是浏览器窗口本身(src/main.wsv 的窗口信息段)。',
    '            //   类库确有 移动窗口(左边,顶边,宽度,高度,是否重画) -> FBroHsBrowserHost_MoveWindow,',
    '            //   且**不需要 HWND**(宿主经 CefBrowserHost 隐式定位窗口)。',
    '            //   类库该方法**无返回值**, 故这里用 CDP Browser.getWindowForTarget 回读 bounds 做验证,',
    '            //   回读不到就如实报 verified=false —— 不假装成功(本项目的核心不变量)。',
    '            变量 mwBrowser <类型 = 类_FBrowser_浏览器>',
    '            mwBrowser = MCP命令服务器.取主浏览器 ()',
    '            如果 (mwBrowser.是否为空 () == 假 && mwBrowser.是否已关闭 () == 假)',
    '            {',
    '                变量 mwX <类型 = 整数>',
    '                mwX = MCP命令服务器.yyjson取整数 (参数JSON, "x")',
    '                变量 mwY <类型 = 整数>',
    '                mwY = MCP命令服务器.yyjson取整数 (参数JSON, "y")',
    '                变量 mwW <类型 = 整数>',
    '                mwW = MCP命令服务器.yyjson取整数 (参数JSON, "width")',
    '                变量 mwH <类型 = 整数>',
    '                mwH = MCP命令服务器.yyjson取整数 (参数JSON, "height")',
    '                变量 mwRepaint <类型 = 逻辑型>',
    '                mwRepaint = MCP命令服务器.yyjson取逻辑 (参数JSON, "repaint")',
    '                // 宽/高可省略 -> 保持当前尺寸: 先回读一次拿当前 bounds',
    '                变量 mw前 <类型 = 文本型>',
    '                mw前 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_w0", "Browser.getWindowForTarget", "{}", 5000)',
    '                变量 mw前体 <类型 = 文本型>',
    '                mw前体 = MCP命令服务器.取CDP同步结果体文本 (mw前)',
    '                变量 mw前色 <类型 = YYJSON只读对象类>',
    '                如果 (mw前体 != "")',
    '                {',
    '                    mw前色 = MCP命令服务器.yyjson取对象成员_安全 (mw前体, "bounds")',
    '                }',
    '                如果 (mwW <= 0)',
    '                {',
    '                    mwW = MCP命令服务器.yyjson取整数 (mw前色, "width")',
    '                }',
    '                如果 (mwH <= 0)',
    '                {',
    '                    mwH = MCP命令服务器.yyjson取整数 (mw前色, "height")',
    '                }',
    '                // 类库签名: 移动窗口(左边, 顶边, 宽度, 高度, 是否重画)',
    '                mwBrowser.移动窗口 (mwX, mwY, mwW, mwH, mwRepaint)',
    '                // 回读验证(类库无返回值, 只能靠读回): 稍等渲染线程应用后再读',
    '                MCP命令服务器.MCP可中断延时 (250)',
    '                变量 mw后 <类型 = 文本型>',
    '                mw后 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_w1", "Browser.getWindowForTarget", "{}", 5000)',
    '                变量 mw后体 <类型 = 文本型>',
    '                mw后体 = MCP命令服务器.取CDP同步结果体文本 (mw后)',
    '                变量 mw后色 <类型 = YYJSON只读对象类>',
    '                如果 (mw后体 != "")',
    '                {',
    '                    mw后色 = MCP命令服务器.yyjson取对象成员_安全 (mw后体, "bounds")',
    '                }',
    '                变量 mw实左 <类型 = 整数>',
    '                mw实左 = MCP命令服务器.yyjson取整数 (mw后色, "left")',
    '                变量 mw实顶 <类型 = 整数>',
    '                mw实顶 = MCP命令服务器.yyjson取整数 (mw后色, "top")',
    '                变量 mw实宽 <类型 = 整数>',
    '                mw实宽 = MCP命令服务器.yyjson取整数 (mw后色, "width")',
    '                变量 mw实高 <类型 = 整数>',
    '                mw实高 = MCP命令服务器.yyjson取整数 (mw后色, "height")',
    '                变量 mw结果 <类型 = YYJSON对象类>',
    '                mw结果.创建自文本 ("{}")',
    '                mw结果.加入整数成员 ("requested_x", mwX)',
    '                mw结果.加入整数成员 ("requested_y", mwY)',
    '                mw结果.加入整数成员 ("requested_width", mwW)',
    '                mw结果.加入整数成员 ("requested_height", mwH)',
    '                mw结果.加入整数成员 ("actual_left", mw实左)',
    '                mw结果.加入整数成员 ("actual_top", mw实顶)',
    '                mw结果.加入整数成员 ("actual_width", mw实宽)',
    '                mw结果.加入整数成员 ("actual_height", mw实高)',
    '                变量 mw已验 <类型 = 逻辑型>',
    '                mw已验 = (mw实宽 > 0 && mw实宽 == mwW && mw实高 == mwH)',
    '                mw结果.加入逻辑值成员 ("verified", mw已验)',
    '                如果 (mw已验)',
    '                {',
    '                    mw结果.加入文本成员 ("message", "窗口已移动并回读确认")',
    '                }',
    '                否则',
    '                {',
    '                    mw结果.加入文本成员 ("message", "已调用类库 移动窗口, 但回读未确认生效(可能被窗口管理器/宿主约束) | 请以 actual_* 为准 | 类库该方法无返回值, 故不谎报成功")',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, mw结果.到可读文本 (YYJSON格式化选项.压缩)))',
    '            }',
    '            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))',
    '        }',
])

# ---------------- 2) browser_set_auto_resize 实现 ----------------
AR_OLD = '\n'.join([
    '        否则 (方法名 == "browser_set_auto_resize")',
    '        {',
    '            返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 嵌入式GUI浏览器不支持 set_auto_resize | 尺寸由主窗口 adjust_layout 管理"))',
    '        }',
])
AR_NEW = '\n'.join([
    '        否则 (方法名 == "browser_set_auto_resize")',
    '        {',
    '            // ★ 补能力: 同 browser_move_window, 原"恒失败"的前提已被推翻。',
    '            //   类库: 置自动调整大小(启用,最小高度,最小宽度,最大高度,最大宽度) -> SetAutoResizeEnabled。',
    '            //   ⚠ 类库声明顺序是 最小**高度**、最小**宽度**(与 CEF CefSize 的 {width,height} 相反),',
    '            //     官方样例全用对称值故无法消歧 —— 这里按类库声明顺序传, 并在回复里如实标注该风险。',
    '            //   类库无返回值 -> 只能报"已调用", 不假装已生效(该类设置也没有可回读的查询接口)。',
    '            变量 arBrowser <类型 = 类_FBrowser_浏览器>',
    '            arBrowser = MCP命令服务器.取主浏览器 ()',
    '            如果 (arBrowser.是否为空 () == 假 && arBrowser.是否已关闭 () == 假)',
    '            {',
    '                如果 (MCP命令服务器.参数键存在 (参数JSON, "enable") == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "必须显式指定 enable | 例: enable:true(窗口可随内容增长) / enable:false(关闭) | 缺省语义不明故不接受缺省"))',
    '                }',
    '                变量 ar启用 <类型 = 逻辑型>',
    '                ar启用 = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")',
    '                变量 ar最小高 <类型 = 整数>',
    '                ar最小高 = MCP命令服务器.yyjson取整数 (参数JSON, "min_height")',
    '                变量 ar最小宽 <类型 = 整数>',
    '                ar最小宽 = MCP命令服务器.yyjson取整数 (参数JSON, "min_width")',
    '                变量 ar最大高 <类型 = 整数>',
    '                ar最大高 = MCP命令服务器.yyjson取整数 (参数JSON, "max_height")',
    '                变量 ar最大宽 <类型 = 整数>',
    '                ar最大宽 = MCP命令服务器.yyjson取整数 (参数JSON, "max_width")',
    '                arBrowser.置自动调整大小 (ar启用, ar最小高, ar最小宽, ar最大高, ar最大宽)',
    '                变量 ar结果 <类型 = YYJSON对象类>',
    '                ar结果.创建自文本 ("{}")',
    '                ar结果.加入逻辑值成员 ("enable", ar启用)',
    '                ar结果.加入整数成员 ("min_height", ar最小高)',
    '                ar结果.加入整数成员 ("min_width", ar最小宽)',
    '                ar结果.加入整数成员 ("max_height", ar最大高)',
    '                ar结果.加入整数成员 ("max_width", ar最大宽)',
    '                ar结果.加入逻辑值成员 ("verified", 假)',
    '                ar结果.加入文本成员 ("message", "已调用类库 置自动调整大小(SetAutoResizeEnabled) | 类库该设置无返回值、也没有可回读的查询接口, 故无法确认是否生效: 本工具不谎报 verified=true | 参数按类库声明顺序 最小高度/最小宽度 传入(与 CEF 的 {width,height} 顺序相反, 传非对称值请自行确认)")',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, ar结果.到可读文本 (YYJSON格式化选项.压缩)))',
    '            }',
    '            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))',
    '        }',
])

# ---------------- 3) MCP_Server 注册项 ----------------
REG_AR_OLD = ('        添加工具JSON (' + Q + 'browser_set_auto_resize' + Q
              + ', ' + Q + '⛔ 本工具恒失败: 嵌入式GUI浏览器尺寸由主窗口布局管理, 不支持自动调整'
              + '| 需要改视口请用 fingerprint viewport' + Q + ')')
REG_AR_NEW = ('        添加工具JSON (' + Q + 'browser_set_auto_resize' + Q
              + ', ' + Q + '启用/关闭窗口自动调整大小(CEF SetAutoResizeEnabled)。**已实现**: 经类库 置自动调整大小 '
              + '调用宿主 SetAutoResizeEnabled(不需 HWND)。类库无返回值、且该类设置没有可回读的查询接口, '
              + '故只报 verified=false 而不谎报生效。⚠ 类库声明顺序是 最小**高度**、最小**宽度**(与 CEF 的 '
              + '{width,height} 相反), 官方样例都用对称值无法消歧 —— 传非对称值时请自行确认顺序' + Q
              + ', 多属性Schema文本 (属性项JSON (' + Q + 'enable' + Q + ', ' + Q + 'boolean' + Q
              + ', ' + Q + 'true=启用(窗口可随内容增长) / false=关闭 | 必填' + Q + ') + '
              + Q + ',' + Q + ' + 属性项JSON (' + Q + 'min_height' + Q + ', ' + Q + 'integer' + Q + ', '
              + Q + '最小高度(0=该维不限)' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'min_width' + Q
              + ', ' + Q + 'integer' + Q + ', ' + Q + '最小宽度(0=该维不限)' + Q + ') + ' + Q + ',' + Q
              + ' + 属性项JSON (' + Q + 'max_height' + Q + ', ' + Q + 'integer' + Q + ', '
              + Q + '最大高度(0=该维不限)' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'max_width' + Q
              + ', ' + Q + 'integer' + Q + ', ' + Q + '最大宽度(0=该维不限)' + Q + '), '
              + Q + B + Q + 'enable' + B + Q + Q + '))')

REG_MW_OLD = ('        添加工具JSON (' + Q + 'browser_move_window' + Q + ', ' + Q
              + '⛔ 本工具恒失败: 嵌入式GUI浏览器的窗口由主窗口统一管理, 不支持移动/改尺寸'
              + '| 需要不同视口请用 browser_screenshot 的 width/height 或 fingerprint viewport' + Q
              + ', 多属性Schema文本 (属性项JSON (' + Q + 'x' + Q + ', ' + Q + 'integer' + Q + ', ' + Q + 'X' + Q
              + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'y' + Q + ', ' + Q + 'integer' + Q + ', '
              + Q + 'Y' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'width' + Q + ', ' + Q + 'integer'
              + Q + ', ' + Q + '宽' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'height' + Q + ', '
              + Q + 'integer' + Q + ', ' + Q + '高' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'repaint'
              + Q + ', ' + Q + 'boolean' + Q + ', ' + Q + '重绘' + Q + '), ' + Q + B + Q + 'x' + B + Q + ','
              + B + Q + 'y' + B + Q + Q + '))')
REG_MW_NEW = ('        添加工具JSON (' + Q + 'browser_move_window' + Q + ', ' + Q
              + '移动/缩放浏览器窗口。**已实现**: 经类库 移动窗口 -> 宿主 MoveWindow(不需 HWND), '
              + '并用 CDP Browser.getWindowForTarget 回读 bounds 验证, 回读不符则如实报 verified=false。'
              + 'width/height 省略时保持当前尺寸。注意: 用户看到的就是浏览器窗口本身(本项目为控制台程序, '
              + '浏览器以桌面为父窗口), 所以本工具会真的移动你眼前的窗口' + Q
              + ', 多属性Schema文本 (属性项JSON (' + Q + 'x' + Q + ', ' + Q + 'integer' + Q + ', ' + Q + 'X' + Q
              + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'y' + Q + ', ' + Q + 'integer' + Q + ', '
              + Q + 'Y' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q + 'width' + Q + ', ' + Q + 'integer'
              + Q + ', ' + Q + '宽(省略/<=0=保持当前)' + Q + ') + ' + Q + ',' + Q + ' + 属性项JSON (' + Q
              + 'height' + Q + ', ' + Q + 'integer' + Q + ', ' + Q + '高(省略/<=0=保持当前)' + Q + ') + '
              + Q + ',' + Q + ' + 属性项JSON (' + Q + 'repaint' + Q + ', ' + Q + 'boolean' + Q + ', '
              + Q + '是否重画(默认false)' + Q + '), ' + Q + B + Q + 'x' + B + Q + ',' + B + Q + 'y' + B + Q
              + Q + '))')


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    c = rd(CORE)
    s = rd(SRV)
    for label, txt, old in (("Core move_window", c, MW_OLD), ("Core auto_resize", c, AR_OLD),
                            ("SRV reg auto_resize", s, REG_AR_OLD), ("SRV reg move_window", s, REG_MW_OLD)):
        n = txt.count(old)
        print("[%s] 锚点出现 %d 次" % (label, n))
        if n != 1:
            print("!! 预期 1 次, 中止(不改任何文件)")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, CORE):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    wr(CORE, c.replace(MW_OLD, MW_NEW).replace(AR_OLD, AR_NEW))
    print("OK [Core] 两个窗口工具已由'恒失败'改为真实实现(含回读验证/诚实标注)")
    wr(SRV, s.replace(REG_AR_OLD, REG_AR_NEW).replace(REG_MW_OLD, REG_MW_NEW))
    print("OK [MCP_Server] 两条误导性描述已改; browser_set_auto_resize 已补 schema")
    for p in (SRV, CORE):
        with io.open(p, 'rb') as f:
            raw = f.read()
        print("复核 %s: BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
