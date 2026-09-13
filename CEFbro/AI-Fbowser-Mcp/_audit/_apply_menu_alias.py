# -*- coding: utf-8 -*-
r"""第125轮(其二): 新增 `browser_menu_alias` —— 菜单命令ID ⇄ 别名(菜单族里唯一可 100% 回读验证的能力)。

为什么补(依据 `_audit/_gap_menu.md` §A2 与源码核实):
  · 项目已有 `解析菜单命令ID` 的**正向**链(规格文本里写 back/copy → 100/113), 但**没有反向**;
  · 而菜单事件 `context_menu_command` 只给 `command_id` 数字 —— 调用方拿到事件后无从判断 113 是什么,
    即"记录得到、读不懂"(与 `browser_event` 漏列菜单事件名同类的可发现性缺口);
  · 菜单族其余未调用方法多为"按索引写"(需在 CEF 回调内对活模型操作), 只有这一项是**纯计算**、零风险、
    且可完全回读验证(往返自检)。

不重复造轮子: 反向查表**不新建第二份表** —— 候选别名清单逐个调用既有 `解析菜单命令ID` 求值,
正向链改动时这里自动跟随(项目已有"两份列表漂移"的教训, 见 browser_context_menu 内注释)。

落地: MCP_Server.wsv 新增 4 个复用件 + 工具注册 + 命令注册表号 1329; Core 新增分派分支。
路由走既有"未命中即核心分派"的默认路径(无需改路由链)。

用法: py -3 _audit\_apply_menu_alias.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

HELPERS = '''    # ==== 菜单命令ID ⇄ 别名(读 context_menu_command 事件时把数字认成"用户点了什么") ====
    # 为什么需要(源码核实 + _audit/_gap_menu.md §A2): 项目只有 解析菜单命令ID 的**正向**链
    #   (规格文本写 back/copy → 100/113), 没有反向; 而菜单事件 context_menu_command 只回 command_id
    #   数字 —— 调用方拿到事件后无从判断 113 是什么, 属"记录得到却读不懂"的可发现性缺口。
    # 不重复造轮子: 反向查表**不新建第二份表**, 而是拿候选别名逐个调用既有正向链求值, 正向链一变
    #   这里自动跟随(项目已有"两份列表漂移"的教训)。
    # 诚实边界(照抄项目自己的实测结论): 这些是 **CEF 标准菜单项ID**(注释记载取自本机 cef_types.h),
    #   不是本应用菜单的真实内容; 且实测"修改类指向默认菜单项不会生效"(见 browser_context_menu 描述),
    #   故本表只有标识/诊断价值 —— 回复里会带 caveat 说明。

    变量 菜单别名候选 <公开 静态 类型 = 文本数组类 注释 = "别名候选(顺序无关); 反向查表用" @输出名 = "MenuAliasCandidates">

    方法 确保菜单别名候选 <公开 静态 @输出名 = "EnsureMenuAliasCandidates" @强制输出 = 真>
    {
        如果 (菜单别名候选.取成员数 () > 0)
        {
            返回
        }
        菜单别名候选 = 取空文本数组 ()
        菜单别名候选.加入成员 ("back")
        菜单别名候选.加入成员 ("forward")
        菜单别名候选.加入成员 ("reload")
        菜单别名候选.加入成员 ("reload_nocache")
        菜单别名候选.加入成员 ("stop")
        菜单别名候选.加入成员 ("undo")
        菜单别名候选.加入成员 ("redo")
        菜单别名候选.加入成员 ("cut")
        菜单别名候选.加入成员 ("copy")
        菜单别名候选.加入成员 ("paste")
        菜单别名候选.加入成员 ("delete")
        菜单别名候选.加入成员 ("selectall")
        菜单别名候选.加入成员 ("find")
        菜单别名候选.加入成员 ("print")
        菜单别名候选.加入成员 ("viewsource")
        菜单别名候选.加入成员 ("nosuggestions")
        菜单别名候选.加入成员 ("addtodict")
    }

    方法 菜单命令ID到别名 <公开 静态 类型 = 文本型 @输出名 = "MenuCommandIDToAlias" @强制输出 = 真>
    参数 命令ID <类型 = 整数 @输出名 = "CommandID">
    {
        确保菜单别名候选 ()
        计次循环 (菜单别名候选.取成员数 ())
        {
            变量 候选 <类型 = 文本型>
            候选 = 菜单别名候选.取成员 (取循环索引 ())
            如果 (解析菜单命令ID (候选) == 命令ID)
            {
                返回 (候选)
            }
        }
        返回 ("")
    }

    方法 菜单命令ID所属区间 <公开 静态 类型 = 文本型 @输出名 = "MenuCommandIDRange" @强制输出 = 真>
    参数 命令ID <类型 = 整数 @输出名 = "CommandID">
    {
        // 区间取自项目既有约定: 自建项 26500..28500(见 browser_context_menu 描述), 标准项 100..206(正向链表)
        如果 (命令ID >= 26500 && 命令ID <= 28500)
        {
            返回 ("service_custom")
        }
        如果 (命令ID >= 100 && 命令ID <= 206)
        {
            返回 ("cef_standard")
        }
        返回 ("unknown")
    }

    方法 取菜单别名清单JSON <公开 静态 类型 = 文本型 @输出名 = "GetMenuAliasListJSON" @强制输出 = 真>
    {
        确保菜单别名候选 ()
        变量 结果 <类型 = 文本型>
        结果 = "["
        变量 首项 <类型 = 逻辑型 值 = 真>
        计次循环 (菜单别名候选.取成员数 ())
        {
            变量 别名 <类型 = 文本型>
            别名 = 菜单别名候选.取成员 (取循环索引 ())
            变量 编号 <类型 = 整数>
            编号 = 解析菜单命令ID (别名)
            // 正向链里查不到的候选不进清单(这就是往返自检: 清单里的每一项都必然可 reverse→forward 对上)
            如果 (编号 <= 0)
            {
                到循环尾
            }
            如果 (首项)
            {
                首项 = 假
            }
            否则
            {
                结果 = 结果 + ","
            }
            结果 = 结果 + "{\\"alias\\":\\"" + 别名 + "\\",\\"command_id\\":" + 到文本 (编号) + "}"
        }
        结果 = 结果 + "]"
        返回 (结果)
    }

'''

ANCHOR_HELPER = '    方法 解析菜单命令ID <公开 静态 类型 = 整数 @输出名 = "ParseMenuCommandID" @强制输出 = 真>'

REG_OLD = '        命令注册表.置整数值 ("browser_context_menu", 1322)'
REG_NEW = '''        命令注册表.置整数值 ("browser_context_menu", 1322)
        命令注册表.置整数值 ("browser_menu_alias", 1329)'''

TOOL_ANCHOR = '添加工具JSON ("browser_context_menu", '
TOOL_NEW = ('添加工具JSON ("browser_menu_alias", "菜单命令ID ⇄ 别名(读 context_menu_command 事件时把数字认成'
            '「用户点了什么」)| **零前置**: action 可省略 —— 给了 command_id → to_name, 给了 name → to_id, 都没给 → list '
            '| action=list 列出全部别名与ID; action=to_name {command_id} 反查别名; action=to_id {name} 正查ID '
            '| 纯计算不碰浏览器(可完全回读验证): 反向查表由既有正向链 解析菜单命令ID 求值而来, **不存在第二份表** '
            '| **诚实边界**: 这些是 CEF 标准菜单项ID(取自本机 cef_types.h), 不是本应用菜单的真实内容; 实测「修改类指向默认菜单项不会生效」(见 browser_context_menu 描述), 故本表只有标识/诊断价值", '
            '多属性Schema文本 (属性项JSON ("action", "text", "list/to_name/to_id(可省略, 按已给参数自动选)") + "," + 属性项JSON ("command_id", "integer", "to_name: 要反查的命令ID(如 113)") + "," + 属性项JSON ("name", "text", "to_id: 别名(如 copy)"), ""))\n')

CORE_ANCHOR = '        否则 (方法名 == "browser_context_menu")'
CORE_NEW = '''        否则 (方法名 == "browser_menu_alias")
         {
             // 菜单 command_id ⇄ 别名: 把 context_menu_command 事件里的数字认成"用户点了什么"。
             // 纯计算、不碰浏览器 ⇒ 零风险且可完全回读验证(反向查表由既有正向链求值, 不新建第二份表)。
            变量 ma动作 <类型 = 文本型>
            ma动作 = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            变量 ma别名 <类型 = 文本型>
            ma别名 = MCP命令服务器.yyjson取文本 (参数JSON, "name")
            变量 ma命令ID <类型 = 整数>
            ma命令ID = MCP命令服务器.yyjson取整数 (参数JSON, "command_id")
            // 零前置: action 可省略 —— 按已给参数自动选(与 browser_reverse_runtime 等既有做法一致)
            如果 (ma动作 == "")
            {
                如果 (MCP命令服务器.参数键存在 (参数JSON, "command_id"))
                {
                    ma动作 = "to_name"
                }
                否则 (ma别名 != "")
                {
                    ma动作 = "to_id"
                }
                否则
                {
                    ma动作 = "list"
                }
            }
            变量 ma说明 <类型 = 文本型>
            ma说明 = "本表是 CEF 标准菜单项ID(取自本机 cef_types.h), 不是本应用菜单的真实内容; 实测修改类指向默认菜单项不会生效(见 browser_context_menu), 故只有标识/诊断价值"
            如果 (ma动作 == "list")
            {
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"list\\",\\"count\\":" + 到文本 (MCP命令服务器.菜单别名候选.取成员数 ()) + ",\\"aliases\\":" + MCP命令服务器.取菜单别名清单JSON () + ",\\"caveat\\":\\"" + MCP_响应构建.JSON转义文本 (ma说明) + "\\"}"))
            }
            如果 (ma动作 == "to_name")
            {
                如果 (MCP命令服务器.参数键存在 (参数JSON, "command_id") == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "action=to_name 需要 command_id | 例: command_id=113 反查得 copy | 也可 action=list 看全部"))
                }
                变量 ma命中别名 <类型 = 文本型>
                ma命中别名 = MCP命令服务器.菜单命令ID到别名 (ma命令ID)
                变量 ma区间 <类型 = 文本型>
                ma区间 = MCP命令服务器.菜单命令ID所属区间 (ma命令ID)
                变量 ma已识别文本 <类型 = 文本型>
                如果 (ma命中别名 != "")
                {
                    ma已识别文本 = "true"
                }
                否则
                {
                    ma已识别文本 = "false"
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"to_name\\",\\"command_id\\":" + 到文本 (ma命令ID) + ",\\"alias\\":\\"" + MCP_响应构建.JSON转义文本 (ma命中别名) + "\\",\\"recognized\\":" + ma已识别文本 + ",\\"id_range\\":\\"" + ma区间 + "\\",\\"caveat\\":\\"" + MCP_响应构建.JSON转义文本 (ma说明) + "\\"}"))
            }
            如果 (ma动作 == "to_id")
            {
                如果 (ma别名 == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "action=to_id 需要 name(别名文本) | 例: name=copy | 也可 action=list 看全部"))
                }
                变量 ma解析ID <类型 = 整数>
                ma解析ID = MCP命令服务器.解析菜单命令ID (ma别名)
                如果 (ma解析ID <= 0)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "未知菜单命令别名: " + ma别名 + " | 已知别名见 action=list; 纯数字ID(如 113 或自建项 26501)可直接作为命令ID 使用"))
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"to_id\\",\\"name\\":\\"" + MCP_响应构建.JSON转义文本 (ma别名) + "\\",\\"command_id\\":" + 到文本 (ma解析ID) + ",\\"id_range\\":\\"" + MCP命令服务器.菜单命令ID所属区间 (ma解析ID) + "\\",\\"caveat\\":\\"" + MCP_响应构建.JSON转义文本 (ma说明) + "\\"}"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "未知 action: " + ma动作 + " | 支持 list/to_name/to_id; 省略 action 时按已给参数自动选"))
         }
'''


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def patch(path, edits, name, check=None):
    raw = io.open(path, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '%s 带 BOM' % name
    txt = raw.decode('utf-8')
    b0, n0 = balance(txt), len(txt.split('\n'))
    out = txt
    for old, new in edits:
        cnt = out.count(old)
        assert cnt == 1, '%s 锚点出现 %d 次: %s' % (name, cnt, old.strip()[:60])
        out = out.replace(old, new, 1)
    assert balance(out) == b0, '%s 括号净值变了 %s -> %s' % (name, b0, balance(out))
    if check:
        for must in check:
            assert must in out, '%s 缺少 %s' % (name, must)
    print('%s: 行数 %d -> %d; 括号净值 %s 不变' % (name, n0, len(out.split('\n')), balance(out)))
    return raw, out


def main():
    s_raw, s_out = patch(SERVER, [(ANCHOR_HELPER, HELPERS + ANCHOR_HELPER),
                                  (REG_OLD, REG_NEW),
                                  (TOOL_ANCHOR, TOOL_NEW + TOOL_ANCHOR)],
                         'MCP_Server.wsv',
                         check=['方法 菜单命令ID到别名', '方法 取菜单别名清单JSON',
                                '命令注册表.置整数值 ("browser_menu_alias", 1329)',
                                '添加工具JSON ("browser_menu_alias"'])
    c_raw, c_out = patch(CORE, [(CORE_ANCHOR, CORE_NEW + CORE_ANCHOR)],
                         'MCP_Server_Core.wsv',
                         check=['方法名 == "browser_menu_alias"',
                                'MCP命令服务器.菜单命令ID到别名 (ma命令ID)'])

    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        chk = io.open(SERVER, encoding='utf-8').read()
        assert '\r' not in chk
        assert (b'\r' in io.open(CORE, 'rb').read()) == (b'\r' in c_raw)
        print('已写入 Server + Core 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
