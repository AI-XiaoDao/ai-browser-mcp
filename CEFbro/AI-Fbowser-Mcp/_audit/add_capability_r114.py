# -*- coding: utf-8 -*-
"""本轮能力修补(3 项, 每项都有实测依据):

① `browser_uri_decode` **真 bug**: 现实现固定传 `unescape_rule=真`, 实测 "a%20b%26c%3Dd" 原样返回
   (只有非 ASCII 转义被还原) —— 因为类库该参语义是"保留这些转义"。改为默认 假(全部还原), 并把它
   与 `to_utf8` 暴露成参数(类库把该参声明为**逻辑型**, 所以只能给两档, 不能给 0/1/2/3/8/16)。
② `browser_uri_encode` 的 `use_plus` 原被写死 `假`, 暴露成参数(表单语义需要 + 表空格)。
③ 新增 `browser_frame_by_id`(类库 `取框架_ID`, FBroLib.wsv:757): `browser_get_frames` 已把 frame_id
   交给调用方, 却没有"按 ID 取回"的入口 —— 名字版 `browser_frame_by_name` 早就有了, 这是对称缺口。
   守卫: 类库注释明确"ID错误返回空, 类为空而执行操作会导致崩溃", 故先判空再取字段。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'URI解码与按ID取框架-写入前')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
problems = []


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def rep(text, old, new, tag, nl='\n', n=1):
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != n:
        problems.append('%s: 命中 %d 次(应 %d)' % (tag, c, n))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:90]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), n)


def save(src, text, name):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    open(src, 'wb').write(text.encode('utf-8'))


# ══════════════════════ Core: 编码/解码 + 新分支 ══════════════════════
c, nl2 = load(CORE)

c = rep(c, '''        否则 (方法名 == "browser_uri_encode")
        {
            变量 data <类型 = 文本型>
            data = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (data == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数))
            }
            变量 result <类型 = 文本型>
            result = FBrowser_Parser_URI编码 (data, 假)
            返回 (MCP_响应构建.构建简单JSON ("encoded", result))
        }
        否则 (方法名 == "browser_uri_decode")
        {
            变量 data <类型 = 文本型>
            data = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (data == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数))
            }
            变量 result <类型 = 文本型>
            result = FBrowser_Parser_URI解码 (data, 真, 真)
            返回 (MCP_响应构建.构建简单JSON ("decoded", result))
        }
''', '''        否则 (方法名 == "browser_uri_encode")
        {
            变量 data <类型 = 文本型>
            data = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (data == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数))
            }
            // use_plus: 类库注释 "If |use_plus| is true spaces will change to \\"+\\"" —— 表单语义
            变量 usePlus <类型 = 逻辑型>
            usePlus = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "use_plus", 假)
            变量 result <类型 = 文本型>
            result = FBrowser_Parser_URI编码 (data, usePlus)
            返回 (MCP_响应构建.构建简单JSON ("encoded", result))
        }
        否则 (方法名 == "browser_uri_decode")
        {
            变量 data <类型 = 文本型>
            data = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (data == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数))
            }
            变量 toUtf8 <类型 = 逻辑型>
            toUtf8 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "to_utf8", 真)
            // 类库把第三参声明为**逻辑型**(注释却说它是 "URI保留规则" 的位标识), 所以只能给两档。
            // 实测: 传 真 时 "a%20b%26c%3Dd" 原样返回(空格/&/= 的转义被"保留"), 只有非 ASCII 转义被还原;
            // 故默认取 假 = 不保留转义(全部还原)。需要旧行为可显式传 keep_escaped:true。
            变量 keepEscaped <类型 = 逻辑型>
            keepEscaped = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "keep_escaped", 假)
            变量 result <类型 = 文本型>
            result = FBrowser_Parser_URI解码 (data, toUtf8, keepEscaped)
            返回 (MCP_响应构建.构建简单JSON ("decoded", result))
        }
''', 'Core URI 编码/解码参数化 + 解码默认修正', nl2)

c = rep(c, '''            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
        }
        // === 浏览器查找(按标识) ===
''', '''            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
        }
        // === 按框架ID取框架信息(与 browser_frame_by_name 对称) ===
        // browser_get_frames 已经把 frame_id 交给调用方, 这里给出"按 ID 取回"的入口。
        // 类库注释警告: ID 错误会返回空类, 对空类执行操作会崩溃 —— 故先判空/判有效再取字段。
        否则 (方法名 == "browser_frame_by_id")
        {
            变量 browser <类型 = 类_FBrowser_浏览器>
            browser = MCP命令服务器.取主浏览器 ()
            如果 (browser.是否为空 () == 假)
            {
                变量 frameId <类型 = 文本型>
                frameId = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                如果 (frameId == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "frame_id " + MCP_常量.错误_缺少参数 + " | 框架ID 可从 browser_get_frames 取得"))
                }
                变量 frame <类型 = 类_FBrowser_框架>
                frame = browser.取框架_ID (frameId)
                变量 f对象 <类型 = YYJSON对象类>
                f对象.创建自文本 ("{}")
                如果 (frame.是否为空 () == 假 && frame.是否有效 ())
                {
                    f对象.加入逻辑值成员 ("found", 真)
                    f对象.加入文本成员 ("frame_id", frame.取框架ID ())
                    f对象.加入文本成员 ("url", frame.取地址 ())
                    f对象.加入逻辑值成员 ("is_main", frame.是否为主框架 ())
                    f对象.加入逻辑值成员 ("is_focused", frame.是否为焦点框架 ())
                }
                否则
                {
                    f对象.加入逻辑值成员 ("found", 假)
                    f对象.加入文本成员 ("frame_id", frameId)
                    f对象.加入文本成员 ("hint", "该 frame_id 不存在或框架已销毁(导航/刷新后 ID 会变): 请用 browser_get_frames 重新取")
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, f对象.到可读文本 (YYJSON格式化选项.压缩)))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
        }
        // === 浏览器查找(按标识) ===
''', 'Core 新增 browser_frame_by_id 分支', nl2)
save(CORE, c, 'MCP_Server_Core.wsv')

# ══════════════════════ Server: 注册 + 工具 schema ══════════════════════
s, nl = load(SERVER)

s = rep(s, '         命令注册表.置整数值 ("browser_frame_by_name", 1024)\n',
        '         命令注册表.置整数值 ("browser_frame_by_name", 1024)\n'
        '         命令注册表.置整数值 ("browser_frame_by_id", 1325)\n',
        'Server 注册表 browser_frame_by_id=1325', nl)

s = rep(s, '         添加工具JSON ("browser_frame_by_name", "按名查框架", 单参数Schema文本 ("name", "text", "框架名"))\n',
        '         添加工具JSON ("browser_frame_by_name", "按名查框架", 单参数Schema文本 ("name", "text", "框架名"))\n'
        '         添加工具JSON ("browser_frame_by_id", "按框架ID取框架信息(与 browser_frame_by_name 对称)。'
        'browser_get_frames 给出的 frame_id 可直接用; 找不到框架不算错误, 会回 found:false + hint(导航/刷新后旧 ID 失效, 请重新取)", '
        '单参数Schema文本 ("frame_id", "text", "框架ID(取自 browser_get_frames)"))\n',
        'Server 注册 browser_frame_by_id 工具', nl)

s = rep(s, '         添加工具JSON ("browser_uri_encode", "URI编码", 单参数Schema文本 ("data", "text", "数据"))\n',
        '         添加工具JSON ("browser_uri_encode", "URI编码(百分号编码, 与 JS encodeURIComponent 基本一致)。'
        '字母数字与 -_.!~* 等少数字符之外都会变成 %XX; 空格默认 %20, use_plus:true 时变成 + (表单语义)", '
        '多属性Schema文本 (属性项JSON ("data", "text", "要编码的文本") + "," + 属性项JSON ("use_plus", "boolean", "true=空格编码为 + / false(默认)=空格编码为 %20"), "\\"data\\""))\n',
        'Server uri_encode schema', nl)

s = rep(s, '         添加工具JSON ("browser_uri_decode", "URI解码", 单参数Schema文本 ("data", "text", "数据"))\n',
        '         添加工具JSON ("browser_uri_decode", "URI解码(百分号还原)。默认把 %20/%26/%3D 等全部还原成字符; '
        'keep_escaped:true 则保留 ASCII 特殊字符的转义(旧行为, 只还原非 ASCII)", '
        '多属性Schema文本 (属性项JSON ("data", "text", "要解码的文本") + "," + 属性项JSON ("to_utf8", "boolean", "true(默认)=把解码结果按 UTF-8 解释") + "," + 属性项JSON ("keep_escaped", "boolean", "true=保留 ASCII 特殊字符转义 / false(默认)=全部还原"), "\\"data\\""))\n',
        'Server uri_decode schema', nl)

save(SERVER, s, 'MCP_Server.wsv')
print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
