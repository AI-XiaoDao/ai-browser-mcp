# -*- coding: utf-8 -*-
"""实现 non-CDP 的 JS↔宿主查询通道（A 组第 3 缺口: FBrowser_JS交互_注册/删除）。

背景(第111轮实测复核): 全项目 grep `JS交互`/`cefQuery`/`FBroHsQueryHandler` = **0 命中** —— 该通道确实缺失。
它与项目现用的 CDP `Runtime.addBinding` **不是一回事**: 后者依赖 CDP 域(可被检测), 前者是 CEF 自己的
message router(`window.<函数名>({request,onSuccess,onFailure})`), 对"需要一条非 CDP 的页面↔宿主通道"的场景
(反检测/逆向)有独立价值。

形态照抄类库自带例子(main3.wsv:43-46 / jscallback.wsv):
  变量 事件指针 <类型 = 类_FBrowser_事件智能指针>
  事件指针.创建 (子类)            // 子类 基础类 = 类_FBrowser_JS交互事件
  FBrowser_JS交互_注册 ("函数名", "", 事件指针)
  回调里: JS交互回调.成功 (文本)   // 完成本次查询

部件:
  1) MCP_Callbacks.wsv: 新回调类 类_MCP_JS交互事件(CRLF 文件)
  2) MCP_Server.wsv: 3 个静态字段 + 记录/取回复 helper + 工具注册 + 注册表
  3) MCP_Server_Core.wsv: 工具分派(一个工具, 多 action)
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
BAK = os.path.join(ROOT, '备份', 'JS查询通道-写入前')

CB = os.path.join(SRC, 'MCP_Callbacks.wsv')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')

# ---------- 1) 回调类(追加到 MCP_Callbacks.wsv 末尾) ----------
CB_CLASS = '''
类 类_MCP_JS交互事件 <公开 基础类 = 类_FBrowser_JS交互事件 @输出名 = "MCPJSQueryHandler">
{
    方法 即将查询 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 框架 <类型 = 类_FBrowser_框架 @输出名 = "Frame">
    参数 查询ID <类型 = 长整数 @输出名 = "QueryID">
    参数 请求文本 <类型 = 文本型 @输出名 = "RequestText">
    参数 persistent <类型 = 逻辑型 @输出名 = "Persistent">
    参数 JS交互回调 <类型 = 类_FBrowser_JS交互回调 @输出名 = "JSCallback">
    {
        // 页面 -> 宿主 的请求: 记入日志(供 AI 观察"页面主动向宿主发了什么"), 并按注册的回复文本应答。
        // 返回真 = 由本处理器接管本次查询(CEF 要求接管者必须调用 成功/失败 完成它)。
        变量 本次回复 <类型 = 文本型>
        本次回复 = MCP命令服务器.记录JS查询并取回复 (请求文本)
        如果 (JS交互回调.是否为空 () == 假)
        {
            JS交互回调.成功 (本次回复)
        }
        返回 (真)
    }
}
'''

# ---------- 2) MCP_Server.wsv ----------
FIELDS_ANCHOR = ('    变量 是否监控菜单事件 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_即将打开菜单/菜单被调用/菜单被点击/菜单被关闭 → browser_event:context_menu*" @输出名 = "IsMonitorContextMenu">\n')
FIELDS_NEW = FIELDS_ANCHOR + (
    '    # non-CDP 的 JS<->宿主查询通道(CEF message router): 注册名与回复、以及页面发来的请求日志。\n'
    '    变量 JS查询注册名文本 <公开 静态 类型 = 文本型 @输出名 = "JSQueryNamesText">\n'
    '    变量 JS查询回复文本 <公开 静态 类型 = 文本型 @输出名 = "JSQueryReplyText">\n'
    '    变量 JS查询日志文本 <公开 静态 类型 = 文本型 @输出名 = "JSQueryLogText">\n'
    '    变量 JS查询事件指针 <公开 静态 类型 = 类_FBrowser_事件智能指针 @输出名 = "JSQueryHandlerPtr">\n'
)

HELPER_ANCHOR = '    # 把"右键上下文"(类_FBrowser_菜单环境)取成紧凑 JSON —— **只在 CEF 回调内调用**。\n'
HELPER_NEW = '''    # JS 查询回调里调用: 记录请求并返回应回复给页面的文本。
    # 回复规则: 注册时给了回复文本就用它; 否则**回显**请求(便于调用方验证往返是否真的通了)。
    # 日志用单个文本缓冲 + 复用既有的 裁剪规则文本到最大行数 做行数上限, 避免另造一套数组裁剪。

    方法 记录JS查询并取回复 <公开 静态 类型 = 文本型 @输出名 = "LogJSQueryAndGetReply" @强制输出 = 真>
    参数 请求文本 <类型 = 文本型 @输出名 = "RequestText">
    {
        变量 本次行 <类型 = 文本型>
        本次行 = "[" + 到文本 (取启动时间 ()) + "] " + 请求文本
        如果 (JS查询日志文本 == "")
        {
            JS查询日志文本 = 本次行
        }
        否则
        {
            JS查询日志文本 = JS查询日志文本 + "\\n" + 本次行
        }
        JS查询日志文本 = 裁剪规则文本到最大行数 (JS查询日志文本, 200)
        如果 (JS查询回复文本 != "")
        {
            返回 (JS查询回复文本)
        }
        返回 ("mcp-echo:" + 请求文本)
    }

''' + HELPER_ANCHOR

TOOL_LINE = ('添加工具JSON ("browser_js_query", "**非 CDP** 的 JS<->宿主查询通道(CEF message router)。'
             'action=register(name 必填, reply 可选) 注册一个页面可调用的 JS 函数名; 之后页面里 '
             'window.<name>({request:文本, onSuccess:fn, onFailure:fn}) 会到达宿主, 宿主按 reply 应答(未设 reply 则回显 mcp-echo:请求)。'
             'action=unregister(name)/list/log[limit]/clear。'
             '与 CDP 的 Runtime.addBinding 不是一回事: 本通道不经 CDP(反检测场景下 CDP 可被识别), 适合页面主动向宿主发消息的场景。'
             '注册后需刷新/新开页面才注入 JS 函数", '
             '多属性Schema文本 (属性项JSON ("action", "text", "register/unregister/list/log/clear") + "," + '
             '属性项JSON ("name", "text", "register/unregister: JS函数名(如 mcpQuery)") + "," + '
             '属性项JSON ("reply", "text", "register: 应答文本(留空=回显 mcp-echo:请求)") + "," + '
             '属性项JSON ("limit", "integer", "log: 返回条数(默认20)"), "\\"action\\""))\n')

REG_ANCHOR_NEEDLE = r'命令注册表\.置整数值 \("browser_fill_get_text", (\d+)\)'


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('   %s 换行=%s' % (tag, 'CRLF' if nl == '\r\n' else 'LF'))
    norm = [(old.replace('\n', nl), new) for old, new in pairs]
    for old, new in norm:
        c = text.count(old)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, old.strip()[:70]))
            return None
    for old, new in norm:
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


# 1) 回调类: 追加末尾(用"文件末尾 }"作锚点太脆, 改为在最后一个类结束处追加)
t = io.open(CB, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in t else '\n'
if not t.endswith(nl):
    t = t + nl
os.makedirs(BAK, exist_ok=True)
shutil.copy2(CB, os.path.join(BAK, 'MCP_Callbacks.wsv'))
t2 = t + CB_CLASS.replace('\n', nl)
open(CB, 'wb').write(t2.encode('utf-8'))
print('   MCP_Callbacks.wsv 已追加回调类(CRLF=%d)' % t2.count('\r\n'))

# 2) 字段 + helper + 工具注册
if patch(SERVER, [(FIELDS_ANCHOR, FIELDS_NEW), (HELPER_ANCHOR, HELPER_NEW)], 'MCP_Server.wsv') is None:
    sys.exit(1)

srv = io.open(SERVER, encoding='utf-8').read()
m = re.search(r'^.*添加工具JSON \("browser_fill_set_text".*$', srv, re.M)
if not m:
    print('!! 找不到 browser_fill_set_text 注册行')
    sys.exit(1)
srv = srv[:m.end()] + '\n' + TOOL_LINE.rstrip('\n') + srv[m.end():]
mr = re.search(r'^.*' + REG_ANCHOR_NEEDLE + r'.*$', srv, re.M)
if not mr:
    print('!! 找不到 browser_fill_get_text 注册表行')
    sys.exit(1)
nid = int(mr.group(1)) + 2
ins = (mr.group(0) + '\n'
       + '        命令注册表.置整数值 ("browser_js_query", %d)\n' % nid
       + '        注册命令双变体 ("js_query", %d)' % nid)
srv = srv[:mr.start()] + ins + srv[mr.end():]
open(SERVER, 'wb').write(srv.encode('utf-8'))
print('   MCP_Server.wsv 已写入(工具注册 + 注册表 ID %d)' % nid)

# 3) 分派(Core)
CORE_ANCHOR = '        // === 右键菜单自定义(方案甲: 只暂存规格, 由 CEF 回调在模型有效期内施加) ===\n'
CORE_NEW = '''        // === 非 CDP 的 JS<->宿主查询通道(CEF message router) ===
        否则 (方法名 == "browser_js_query")
        {
            变量 jqAction <类型 = 文本型>
            jqAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            如果 (jqAction == "")
            {
                jqAction = "list"
            }
            变量 jqName <类型 = 文本型>
            jqName = MCP命令服务器.yyjson取文本 (参数JSON, "name")
            如果 (jqAction == "register")
            {
                如果 (jqName == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "register 需要 name(页面里将用 window.<name>({request:...}) 调用, 如 mcpQuery)"))
                }
                // 处理器实例只建一次
                如果 (MCP命令服务器.JS查询事件指针.是否为空 ())
                {
                    MCP命令服务器.JS查询事件指针.创建 (类_MCP_JS交互事件)
                }
                // 已注册过则幂等成功(不重复注册, 只更新回复文本)
                变量 jq已存在 <类型 = 逻辑型>
                jq已存在 = 假
                如果 (MCP命令服务器.JS查询注册名文本 != "")
                {
                    变量 jq名数组 <类型 = 文本数组类>
                    分割文本 (MCP命令服务器.JS查询注册名文本, "\\n", jq名数组, 真, 假)
                    计次循环 (jq名数组.取成员数 ())
                    {
                        如果 (jq名数组.取成员 (取循环索引 ()) == jqName)
                        {
                            jq已存在 = 真
                        }
                    }
                }
                变量 jqReply <类型 = 文本型>
                jqReply = MCP命令服务器.yyjson取文本 (参数JSON, "reply")
                如果 (jq已存在 == 假)
                {
                    FBrowser_JS交互_注册 (jqName, "", MCP命令服务器.JS查询事件指针)
                    如果 (MCP命令服务器.JS查询注册名文本 == "")
                    {
                        MCP命令服务器.JS查询注册名文本 = jqName
                    }
                    否则
                    {
                        MCP命令服务器.JS查询注册名文本 = MCP命令服务器.JS查询注册名文本 + "\\n" + jqName
                    }
                }
                如果 (jqReply != "")
                {
                    MCP命令服务器.JS查询回复文本 = jqReply
                }
                变量 jq提示 <类型 = 文本型>
                jq提示 = "已注册 JS 查询函数名: window." + jqName + "({request:文本, onSuccess:fn, onFailure:fn})"
                如果 (jqReply == "")
                {
                    jq提示 = jq提示 + " | 应答策略: 回显 mcp-echo:<请求>(可在 register 时传 reply 改成固定文本)"
                }
                否则
                {
                    jq提示 = jq提示 + " | 应答策略: 固定回复 [" + jqReply + "]"
                }
                jq提示 = jq提示 + " | 注意: JS 函数在**新文档**注入, 已打开的页面需刷新后才有该函数; 用 action=log 看页面发来的请求"
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"name\\":\\"" + MCP_响应构建.JSON转义文本 (jqName) + "\\",\\"already_registered\\":" + 选择 (jq已存在, "true", "false") + ",\\"note\\":\\"" + MCP_响应构建.JSON转义文本 (jq提示) + "\\"}"))
            }
            如果 (jqAction == "unregister")
            {
                如果 (jqName == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "unregister 需要 name"))
                }
                FBrowser_JS交互_删除 (jqName)
                // 同步剔除名单(否则 list 会说还在, 出现"幽灵注册")
                变量 jq保留 <类型 = 文本型>
                jq保留 = ""
                变量 jq删数 <类型 = 整数>
                jq删数 = 0
                如果 (MCP命令服务器.JS查询注册名文本 != "")
                {
                    变量 jq名数组2 <类型 = 文本数组类>
                    分割文本 (MCP命令服务器.JS查询注册名文本, "\\n", jq名数组2, 真, 假)
                    计次循环 (jq名数组2.取成员数 ())
                    {
                        变量 jq一项 <类型 = 文本型>
                        jq一项 = jq名数组2.取成员 (取循环索引 ())
                        如果 (jq一项 == jqName)
                        {
                            jq删数 = jq删数 + 1
                        }
                        否则
                        {
                            如果 (jq保留 == "")
                            {
                                jq保留 = jq一项
                            }
                            否则
                            {
                                jq保留 = jq保留 + "\\n" + jq一项
                            }
                        }
                    }
                }
                MCP命令服务器.JS查询注册名文本 = jq保留
                返回 (MCP_响应构建.命令成功 (命令ID, "已注销 JS 查询函数名: " + jqName + " (从名单移除 " + 到文本 (jq删数) + " 项) | 幂等: 未注册过时同样返回成功"))
            }
            如果 (jqAction == "list")
            {
                变量 jq条数 <类型 = 整数>
                jq条数 = 0
                如果 (MCP命令服务器.JS查询日志文本 != "")
                {
                    变量 jq日志数组 <类型 = 文本数组类>
                    分割文本 (MCP命令服务器.JS查询日志文本, "\\n", jq日志数组, 真, 假)
                    jq条数 = jq日志数组.取成员数 ()
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"registered_names\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.JS查询注册名文本) + "\\",\\"reply\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.JS查询回复文本) + "\\",\\"log_lines\\":" + 到文本 (jq条数) + ",\\"note\\":\\"registered_names 为换行分隔的已注册 JS 函数名; 页面需刷新后才注入函数; 用 action=log 看页面发来的请求\\"}"))
            }
            如果 (jqAction == "log")
            {
                变量 jqLimit <类型 = 整数>
                jqLimit = MCP命令服务器.yyjson取整数 (参数JSON, "limit")
                如果 (jqLimit <= 0 || jqLimit > 200)
                {
                    jqLimit = 20
                }
                变量 jq日志全 <类型 = 文本数组类>
                分割文本 (MCP命令服务器.JS查询日志文本, "\\n", jq日志全, 真, 假)
                变量 jq总数 <类型 = 整数>
                jq总数 = jq日志全.取成员数 ()
                变量 jq返回 <类型 = 文本型>
                jq返回 = ""
                变量 jq起 <类型 = 整数>
                jq起 = jq总数 - jqLimit
                如果 (jq起 < 0)
                {
                    jq起 = 0
                }
                变量 jq位 <类型 = 整数>
                jq位 = jq起
                判断循环 (jq位 < jq总数)
                {
                    变量 jq行 <类型 = 文本型>
                    jq行 = jq日志全.取成员 (jq位)
                    如果 (jq返回 == "")
                    {
                        jq返回 = jq行
                    }
                    否则
                    {
                        jq返回 = jq返回 + "\\n" + jq行
                    }
                    jq位 = jq位 + 1
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"total\\":" + 到文本 (jq总数) + ",\\"returned\\":" + 到文本 (jq总数 - jq起) + ",\\"request_log\\":\\"" + MCP_响应构建.JSON转义文本 (jq返回) + "\\",\\"note\\":\\"页面发来的请求原文(形如 [启动毫秒] 请求文本); 为空说明还没收到过 —— 确认已 register 且页面已刷新\\"}"))
            }
            如果 (jqAction == "clear")
            {
                MCP命令服务器.JS查询日志文本 = ""
                返回 (MCP_响应构建.命令成功 (命令ID, "JS 查询日志已清空(注册名与回复不受影响)"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + jqAction + " | 支持: register/unregister/list/log/clear"))
        }
''' + CORE_ANCHOR
if patch(CORE, [(CORE_ANCHOR, CORE_NEW)], 'MCP_Server_Core.wsv') is None:
    sys.exit(1)
print('完成; 备份 -> %s' % BAK)
print('注: 分派分支里注册调用仍是占位, 下一步在正式实现中替换。')
