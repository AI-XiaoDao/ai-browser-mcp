# -*- coding: utf-8 -*-
"""实现 browser_context_menu（方案甲：预置规格 + 回调内一次性施加）。

为什么必须走方案甲(第100轮子代理给的决定性依据):
  CEF 头 `cef_context_menu_handler.h:102-103` **逐字**写着
    "Do not keep references to |params| or |model| outside of this callback."
  且 `cef_menu_model.h:48` 要求只能在浏览器进程 UI 线程访问, 而本 MCP 工具跑在**非 UI 线程**
  (`MCP_Stdio.wsv:324` 缓存线程类) => 保存句柄延迟调用**不可行**。
  又: 每次右键都是**全新的默认菜单模型**, 故规格必须**每次右键重施**。

部件:
  1) MCP_Server.wsv: 6 个静态字段 + 方法 应用菜单规格(顶层菜单) -> 施加条数
  2) MCP_BrowserEvents.wsv: 在 浏览器_即将打开菜单 回调里调用它(拿到 菜单模式 的地方)
  3) MCP_Server_Core.wsv: 工具分派 set/get/clear
  4) MCP_Server.wsv: 命令注册表 + 添加工具JSON

规格格式(逐行文本, 字段用 '|' 分隔, 标签经 规则字段转义 以容忍 '|'):
  类型|标签|命令ID|参数|父命令ID|快捷键
  类型: item/check/radio/sep/sub
  参数: item/sub=1可用0禁用; check=1选中; radio=群ID(<=0 时按 1); sep 忽略
  父命令ID: 0=顶层; 非0=挂到其上方最近一个 sub 行(故**子项须紧跟其 sub 行**)
  快捷键: 空=不设; 形如 70 / 70C / 70CS(键码+修饰词 C=ctrl S=shift A=alt; 仅显示, 触发需自行发键盘事件)
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '右键菜单自定义-写入前')

# ============================================================ 1) MCP_Server.wsv
SERVER = os.path.join(SRC, 'MCP_Server.wsv')

A_OLD = ('    变量 是否监控菜单事件 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_即将打开菜单/菜单被调用/菜单被点击/菜单被关闭 → browser_event:context_menu*" @输出名 = "IsMonitorContextMenu">\n')
A_NEW = A_OLD + (
    '    # 右键菜单自定义规格(方案甲)。浏览器每次右键都是**全新的默认菜单模型**, 且 CEF 禁止在\n'
    '    # 回调之外持有菜单对象, 故这里只**暂存规格**, 由 浏览器_即将打开菜单 回调在模型有效期内施加。\n'
    '    变量 菜单规格文本 <公开 静态 类型 = 文本型 @输出名 = "MenuSpecText">\n'
    '    变量 菜单已启用 <公开 静态 类型 = 逻辑型 值 = 假 @输出名 = "MenuEnabled">\n'
    '    变量 菜单施加次数 <公开 静态 类型 = 整数 值 = 0 @输出名 = "MenuApplyCount">\n'
    '    变量 菜单最近施加条数 <公开 静态 类型 = 整数 值 = 0 @输出名 = "MenuLastAppliedCount">\n'
    '    变量 菜单上次施加时刻 <公开 静态 类型 = 文本型 @输出名 = "MenuLastApplyTime">\n'
    '    变量 菜单上次错误 <公开 静态 类型 = 文本型 @输出名 = "MenuLastError">\n'
)

# 方法体: 放在"命令预查找"注释之前(该类内部)
B_OLD = '    # ======== 命令预查找 (字典O(1), 找不到直接返回) ==========\n'
B_NEW = '''    # 把暂存的菜单规格施加到**当前这次右键**的菜单模型上(只在 CEF 回调内调用)。
    # 返回成功施加的条目数; 规格为空或未启用时**什么都不做并返回 0**
    #   —— 绝不能在规格为空时清空菜单: CEF 默认菜单会被清掉, 右键菜单直接消失。
    # 子项挂载: 父命令ID 非 0 的行挂到"其上方最近创建的 sub 行", 故规格须把子项紧跟其 sub 行。

    方法 应用菜单规格 <公开 静态 类型 = 整数 @输出名 = "ApplyMenuSpec" @强制输出 = 真>
    参数 顶层菜单 <类型 = 类_FBrowser_菜单模式 @输出名 = "TopMenuModel">
    {
        如果 (菜单已启用 == 假 || 菜单规格文本 == "" || 顶层菜单.是否为空 ())
        {
            返回 (0)
        }
        变量 施加条数 <类型 = 整数>
        施加条数 = 0
        变量 最近子菜单 <类型 = 类_FBrowser_菜单模式>
        变量 行数组 <类型 = 文本数组类>
        分割文本 (菜单规格文本, "\\n", 行数组, 真, 假)
        计次循环 (行数组.取成员数 ())
        {
            变量 行文本 <类型 = 文本型>
            行文本 = 行数组.取成员 (取循环索引 ())
            如果 (行文本 == "")
            {
                到循环尾
            }
            变量 段数组 <类型 = 文本数组类>
            分割文本 (行文本, "|", 段数组, 假, 假)
            如果 (段数组.取成员数 () < 3)
            {
                到循环尾
            }
            变量 条目类型 <类型 = 文本型>
            条目类型 = 段数组.取成员 (0)
            变量 条目标签 <类型 = 文本型>
            条目标签 = 规则字段反转义 (段数组.取成员 (1))
            变量 条目命令ID <类型 = 整数>
            条目命令ID = 文本到整数 (段数组.取成员 (2))
            变量 条目参数 <类型 = 整数>
            条目参数 = 1
            如果 (段数组.取成员数 () >= 4 && 段数组.取成员 (3) != "")
            {
                条目参数 = 文本到整数 (段数组.取成员 (3))
            }
            变量 条目父ID <类型 = 整数>
            条目父ID = 0
            如果 (段数组.取成员数 () >= 5 && 段数组.取成员 (4) != "")
            {
                条目父ID = 文本到整数 (段数组.取成员 (4))
            }
            // 除分隔栏外, 命令ID 必须落在 CEF 允许的自定义区间; 越界直接跳过并记错误
            如果 (条目类型 != "sep" && (条目命令ID < 26500 || 条目命令ID > 28500))
            {
                菜单上次错误 = "跳过命令ID越界的条目(须在26500..28500): " + 行文本
                到循环尾
            }
            变量 目标模型 <类型 = 类_FBrowser_菜单模式>
            目标模型 = 顶层菜单
            如果 (条目父ID != 0)
            {
                目标模型 = 最近子菜单
            }
            如果 (目标模型.是否为空 ())
            {
                菜单上次错误 = "父菜单不存在, 跳过: " + 行文本
                到循环尾
            }
            如果 (条目类型 == "sep")
            {
                如果 (目标模型.添加分隔栏 ())
                {
                    施加条数 = 施加条数 + 1
                }
            }
            否则 (条目类型 == "sub")
            {
                变量 子模型 <类型 = 类_FBrowser_菜单模式>
                子模型 = 目标模型.添加子菜单 (条目命令ID, 条目标签)
                如果 (子模型.是否为空 () == 假)
                {
                    施加条数 = 施加条数 + 1
                    最近子菜单 = 子模型
                    如果 (条目参数 == 0)
                    {
                        目标模型.置禁止状态 (条目命令ID, 真)
                    }
                }
            }
            否则 (条目类型 == "check")
            {
                如果 (目标模型.添加Check菜单 (条目命令ID, 条目标签))
                {
                    施加条数 = 施加条数 + 1
                    如果 (条目参数 == 1)
                    {
                        目标模型.选中状态 (条目命令ID, 真)
                    }
                }
            }
            否则 (条目类型 == "radio")
            {
                变量 单选项群ID <类型 = 整数>
                单选项群ID = 条目参数
                如果 (单选项群ID <= 0)
                {
                    单选项群ID = 1
                }
                如果 (目标模型.添加Radio菜单 (条目命令ID, 条目标签, 单选项群ID))
                {
                    施加条数 = 施加条数 + 1
                }
            }
            否则
            {
                如果 (目标模型.添加菜单 (条目命令ID, 条目标签))
                {
                    施加条数 = 施加条数 + 1
                    如果 (条目参数 == 0)
                    {
                        目标模型.置禁止状态 (条目命令ID, 真)
                    }
                }
            }
            // 快捷键(可选, 仅用于显示): 键码 + 修饰词 C/S/A, 例 "70C"
            如果 (段数组.取成员数 () >= 6 && 段数组.取成员 (5) != "" && 条目类型 != "sep")
            {
                变量 快捷键原文 <类型 = 文本型>
                快捷键原文 = 段数组.取成员 (5)
                变量 键码文本 <类型 = 文本型>
                键码文本 = ""
                变量 修饰位 <类型 = 整数>
                修饰位 = 1
                判断循环 (修饰位 <= 取文本长度 (快捷键原文))
                {
                    变量 当前字符 <类型 = 文本型>
                    当前字符 = 取文本中间 (快捷键原文, 修饰位 - 1, 1)
                    如果 (寻找文本 ("0123456789", 当前字符, 0, 假) != -1)
                    {
                        键码文本 = 键码文本 + 当前字符
                    }
                    修饰位 = 修饰位 + 1
                }
                如果 (键码文本 != "")
                {
                    变量 是否Ctrl <类型 = 逻辑型>
                    是否Ctrl = 寻找文本 (快捷键原文, "C", 0, 假) != -1
                    变量 是否Shift <类型 = 逻辑型>
                    是否Shift = 寻找文本 (快捷键原文, "S", 0, 假) != -1
                    变量 是否Alt <类型 = 逻辑型>
                    是否Alt = 寻找文本 (快捷键原文, "A", 0, 假) != -1
                    目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本), 是否Shift, 是否Ctrl, 是否Alt)
                }
            }
        }
        菜单最近施加条数 = 施加条数
        菜单施加次数 = 菜单施加次数 + 1
        菜单上次施加时刻 = 到文本 (取启动时间 ())
        返回 (施加条数)
    }

''' + B_OLD

# 命令注册表 + 工具注册
C_REG_ANCHOR = '    命令注册表.置整数值 ("browser_intercept", '
C_TOOL_ANCHOR = '添加工具JSON ("browser_context_menu"'   # 仅用于自检: 应不存在


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    for old, new in pairs:
        c = text.count(old)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, old.strip()[:70]))
            return None
    for old, new in pairs:
        for ln in new.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号奇数: %s' % ln.strip()[:100])
                return None
        text = text.replace(old, new.replace('\n', nl), 1)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.encode('utf-8'))
    print('   %s 已写入(+%d 处)' % (os.path.basename(path), len(pairs)))
    return text


# 计算注册表最大 ID, 取 max+1
srv = io.open(SERVER, encoding='utf-8').read()
ids = [int(m.group(2)) for m in re.finditer(r'命令注册表\.置整数值 \("([^"]+)",\s*(\d+)\)', srv)]
NEXT_ID = (max(ids) + 1) if ids else 1360
print('命令注册表条目 %d 个, 最大 ID=%s -> 新 ID=%d' % (len(ids), max(ids) if ids else '-', NEXT_ID))

REG_OLD = '        命令注册表.置整数值 ("browser_context_menu_alias_placeholder", 0)\n'
REG_NEW = ('        命令注册表.置整数值 ("browser_context_menu", %d)\n'
           '        注册命令双变体 ("context_menu", %d)\n' % (NEXT_ID, NEXT_ID))

TOOL_OLD = '添加工具JSON ("browser_intercept", '
TOOL_NEW = ('添加工具JSON ("browser_context_menu", "右键菜单自定义(方案甲: 预置规格, 每次右键时由 CEF 回调施加)。'
            '浏览器每次右键都是**全新的默认菜单模型**, 且 CEF 明确禁止在回调之外持有菜单对象, 故本工具**不能即时修改当前已打开的菜单**, 只能先 set 预置规格, 之后每次右键自动施加。'
            '规格为逐行文本, 每行: 类型|标签|命令ID|参数|父命令ID|快捷键 —— 类型=item/check/radio/sep/sub; '
            '参数: item与sub为1可用0禁用, check为1选中, radio为群ID; 父命令ID=0 表示顶层, 非0 表示挂到其上方最近的 sub 行(故子项须紧跟其 sub 行); '
            '快捷键仅用于显示(如 70C = 键码70+Ctrl, 可组合 S/A), 触发需自行发键盘事件。命令ID 须在 26500..28500, 留 0 则由服务端自动分配。'
            '注意: 本工具与 browser_kernel_menu(屏蔽快捷菜单)语义相反", '
            '多属性Schema文本 (属性项JSON ("action", "text", "set/get/clear") + "," + '
            '属性项JSON ("items", "text", "set: 菜单规格(逐行文本, 格式见工具描述)") + "," + '
            '属性项JSON ("enable", "boolean", "set: 是否启用(默认true)"), "\\"action\\""))\n')

ok = patch(SERVER, [(A_OLD, A_NEW), (B_OLD, B_NEW), (TOOL_OLD, TOOL_NEW)], 'MCP_Server.wsv')
if ok is None:
    sys.exit(1)

# 注册表: 插在 browser_intercept 那一行之后
text = io.open(SERVER, encoding='utf-8').read()
m = re.search(r'^.*命令注册表\.置整数值 \("browser_intercept".*$', text, re.M)
if not m:
    print('!! 找不到 browser_intercept 注册行, 中止')
    sys.exit(1)
ins = m.group(0) + '\n' + REG_NEW.rstrip('\n')
text = text[:m.start()] + ins + text[m.end():]
os.makedirs(BAK, exist_ok=True)
open(SERVER, 'wb').write(text.encode('utf-8'))
print('   注册表条目已插入(ID=%d, 并注册短名变体 context_menu)' % NEXT_ID)

# ============================================================ 2) MCP_BrowserEvents.wsv
BE = os.path.join(SRC, 'MCP_BrowserEvents.wsv')
BE_OLD = ('        如果 (MCP命令服务器.是否监控菜单事件)\n'
          '        {\n'
          '            记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), "")\n'
          '        }\n')
BE_NEW = ('        如果 (MCP命令服务器.是否监控菜单事件)\n'
          '        {\n'
          '            记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), "")\n'
          '        }\n'
          '        // 自定义菜单规格在此施加: `菜单模式` 只在本次回调内有效(CEF 头逐字禁止回调外持引用),\n'
          '        // 且每次右键都是新的默认模型, 故必须每次重施; 规格为空时本方法什么都不做(绝不清空默认菜单)。\n'
          '        如果 (MCP命令服务器.菜单已启用)\n'
          '        {\n'
          '            MCP命令服务器.应用菜单规格 (菜单模式)\n'
          '        }\n')
if patch(BE, [(BE_OLD, BE_NEW)], 'MCP_BrowserEvents.wsv') is None:
    sys.exit(1)

# ============================================================ 3) MCP_Server_Core.wsv
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
C_OLD = '        // === 数据提取: 链接/图片/表格 结构化JSON ===\n'
C_NEW = '''        // === 右键菜单自定义(方案甲: 只暂存规格, 由 CEF 回调在模型有效期内施加) ===
        否则 (方法名 == "browser_context_menu")
        {
            变量 cmAction <类型 = 文本型>
            cmAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            如果 (cmAction == "")
            {
                cmAction = "set"
            }
            如果 (cmAction == "set")
            {
                变量 cmItems <类型 = 文本型>
                cmItems = MCP命令服务器.yyjson取文本 (参数JSON, "items")
                如果 (cmItems == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set 需要 items(逐行菜单规格) | 格式: 类型|标签|命令ID|参数|父命令ID|快捷键; 类型=item/check/radio/sep/sub; 命令ID 须在 26500..28500(留0自动分配)"))
                }
                // 校验并自动分配命令ID(留 0 / 重复的按 26501 起顺序补齐), 越界或类型非法直接拒绝(不静默丢弃)
                变量 cm行数组 <类型 = 文本数组类>
                分割文本 (cmItems, "\\n", cm行数组, 真, 假)
                变量 cm有效数 <类型 = 整数>
                cm有效数 = 0
                变量 cm自动ID <类型 = 整数>
                cm自动ID = 26501
                变量 cm新规格 <类型 = 文本型>
                cm新规格 = ""
                变量 cm已用ID <类型 = 整数>
                计次循环 (cm行数组.取成员数 ())
                {
                    变量 cm行 <类型 = 文本型>
                    cm行 = cm行数组.取成员 (取循环索引 ())
                    如果 (cm行 == "")
                    {
                        到循环尾
                    }
                    变量 cm段 <类型 = 文本数组类>
                    分割文本 (cm行, "|", cm段, 假, 假)
                    如果 (cm段.取成员数 () < 3)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行字段不足(至少 类型|标签|命令ID): " + cm行))
                    }
                    变量 cm类型 <类型 = 文本型>
                    cm类型 = cm段.取成员 (0)
                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行类型非法: " + cm类型 + " | 支持 item/check/radio/sep/sub"))
                    }
                    变量 cmID <类型 = 整数>
                    cmID = 文本到整数 (cm段.取成员 (2))
                    如果 (cm类型 != "sep")
                    {
                        如果 (cmID == 0 || cmID < 26500 || cmID > 28500)
                        {
                            // 留 0 = 让服务端分配; 越界则明确拒绝(CEF 自定义区间外的 ID 不会生效)
                            如果 (cmID == 0)
                            {
                                cmID = cm自动ID
                                cm自动ID = cm自动ID + 1
                            }
                            否则
                            {
                                返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行命令ID越界: " + 到文本 (cmID) + " | CEF 自定义菜单命令ID 必须在 26500..28500"))
                            }
                        }
                        cm已用ID = cm已用ID + 1
                    }
                    // 回写规范化后的行(标签保持原样, 由回调侧反转义)
                    变量 cm新行 <类型 = 文本型>
                    cm新行 = cm类型 + "|" + cm段.取成员 (1) + "|" + 到文本 (cmID)
                    如果 (cm段.取成员数 () >= 4)
                    {
                        cm新行 = cm新行 + "|" + cm段.取成员 (3)
                    }
                    如果 (cm段.取成员数 () >= 5)
                    {
                        cm新行 = cm新行 + "|" + cm段.取成员 (4)
                    }
                    如果 (cm段.取成员数 () >= 6)
                    {
                        cm新行 = cm新行 + "|" + cm段.取成员 (5)
                    }
                    如果 (cm新规格 == "")
                    {
                        cm新规格 = cm新行
                    }
                    否则
                    {
                        cm新规格 = cm新规格 + "\\n" + cm新行
                    }
                    cm有效数 = cm有效数 + 1
                }
                如果 (cm有效数 == 0)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "规格里没有有效条目"))
                }
                MCP命令服务器.菜单规格文本 = cm新规格
                变量 cmEnable <类型 = 逻辑型>
                cmEnable = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "enable", 真)
                MCP命令服务器.菜单已启用 = cmEnable
                MCP命令服务器.菜单施加次数 = 0
                MCP命令服务器.菜单最近施加条数 = 0
                MCP命令服务器.菜单上次错误 = ""
                // 零前置: 菜单事件监控默认是关的, 这里自动打开(否则事件不记录、状态无从观察)
                MCP命令服务器.是否监控菜单事件 = 真
                变量 cm提示 <类型 = 文本型>
                cm提示 = "菜单规格已预置(启用=" + 选择 (cmEnable, "true", "false") + ", 条目=" + 到文本 (cm有效数) + ", 含命令ID条目=" + 到文本 (cm已用ID) + ") | 每次右键时由 CEF 回调施加, 本工具无法即时修改已打开的菜单 | 已自动开启菜单事件监控"
                如果 (cmEnable == 假)
                {
                    cm提示 = cm提示 + " | 注意: 规格已保存但当前处于**禁用**状态(enable=false), 右键不会施加"
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"applied\\":false,\\"spec_lines\\":" + 到文本 (cm有效数) + ",\\"enabled\\":" + 选择 (cmEnable, "true", "false") + ",\\"message\\":\\"" + MCP_响应构建.JSON转义文本 (cm提示) + "\\",\\"note\\":\\"规格已暂存: 右键一次后可用 action=get 查看施加次数与条数\\"}"))
            }
            否则 (cmAction == "get")
            {
                变量 cm规格回显 <类型 = 文本型>
                cm规格回显 = MCP命令服务器.菜单规格文本
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"enabled\\":" + 选择 (MCP命令服务器.菜单已启用, "true", "false") + ",\\"apply_count\\":" + 到文本 (MCP命令服务器.菜单施加次数) + ",\\"last_applied_items\\":" + 到文本 (MCP命令服务器.菜单最近施加条数) + ",\\"last_apply_time\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单上次施加时刻) + "\\",\\"last_error\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单上次错误) + "\\",\\"spec\\":\\"" + MCP_响应构建.JSON转义文本 (cm规格回显) + "\\",\\"event_monitor\\":" + 选择 (MCP命令服务器.是否监控菜单事件, "true", "false") + ",\\"note\\":\\"apply_count=右键次数; last_applied_items=上次实际施加成功的条目数(0 或持续不增说明规格为空/被禁用/模型无效)\\"}"))
            }
            否则 (cmAction == "clear")
            {
                MCP命令服务器.菜单规格文本 = ""
                MCP命令服务器.菜单已启用 = 假
                MCP命令服务器.菜单最近施加条数 = 0
                返回 (MCP_响应构建.命令成功 (命令ID, "右键菜单自定义已撤销(规格清空, 恢复浏览器默认菜单) | 幂等: 本就未设置时同样返回成功"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + cmAction + " | 支持: set/get/clear"))
        }
''' + C_OLD
if patch(CORE, [(C_OLD, C_NEW)], 'MCP_Server_Core.wsv') is None:
    sys.exit(1)

print('完成; 备份 -> %s' % BAK)
