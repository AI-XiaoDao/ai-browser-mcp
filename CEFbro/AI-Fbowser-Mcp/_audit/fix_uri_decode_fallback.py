# -*- coding: utf-8 -*-
"""URI 解码: 撤掉我引入的回归, 并让工具在**一次调用内**给出正确结果。

实测结论(本机 CEF, 四组合全测):
  · 类库 `FBrowser_Parser_URI解码(text, to_utf8, unescape_rule)` 的第三参被声明为**逻辑型**;
  · 传 真: 只还原非 ASCII("%E4%B8%AD%E6%96%87"->中文), 但 %20/%26/%3D **原样返回**;
  · 传 假: 什么都不还原(比原来更差 —— 我上一版把默认改成假, 属回归, 现撤回);
  · to_utf8 真/假 对结果无影响;
  · 页面内 decodeURIComponent("a%20b%26c%3Dd") = "a b&c=d"(期望值本身没问题)。
所以: 默认改回 真(不回归); 当结果显示仍残留 %HH 且确有浏览器时, 用页面内 decodeURIComponent
补齐(一次调用完成, 符合"零前置/一次成功"), 并如实回报 data.via 说明结果来自哪条路径;
两条路都失败时给出 warning 与可行动的替代做法, 不再"静默返回原串"。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'URI解码兜底-写入前')
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


# ─────────── Server: 新工具方法 含百分号转义 + 描述 ───────────
s, nl = load(os.path.join(SRC, 'MCP_Server.wsv'))

s = rep(s, '''    # 菜单规格"修改类"类型的**唯一判定源**''',
        '''    # 文本里是否还残留未还原的百分号转义(%HH) —— 用于判断类库解码器是否真的解开了。
    # 不引入正则(项目里没统一的正则封装), 用逐字符 + 十六进制字符集判断。
    方法 含百分号转义 <公开 静态 类型 = 逻辑型 @输出名 = "HasPercentEscape" @强制输出 = 真>
    参数 待查文本 <类型 = 文本型 @输出名 = "Text">
    {
        变量 位置 <类型 = 整数>
        位置 = 0
        判断循环 (位置 + 2 < 取文本长度 (待查文本))
        {
            如果 (取文本中间 (待查文本, 位置, 1) == "%")
            {
                变量 高半字节 <类型 = 文本型>
                变量 低半字节 <类型 = 文本型>
                高半字节 = 取文本中间 (待查文本, 位置 + 1, 1)
                低半字节 = 取文本中间 (待查文本, 位置 + 2, 1)
                如果 (寻找文本 ("0123456789abcdefABCDEF", 高半字节, 0, 假) != -1 && 寻找文本 ("0123456789abcdefABCDEF", 低半字节, 0, 假) != -1)
                {
                    返回 (真)
                }
            }
            位置 = 位置 + 1
        }
        返回 (假)
    }

    # 菜单规格"修改类"类型的**唯一判定源**''',
        'Server 新增 含百分号转义', nl)

s = rep(s, '         添加工具JSON ("browser_uri_decode", "URI解码(百分号还原)。默认把 %20/%26/%3D 等全部还原成字符; keep_escaped:true 则保留 ASCII 特殊字符的转义(旧行为, 只还原非 ASCII)", ',
        '         添加工具JSON ("browser_uri_decode", "URI解码(百分号还原)。'
        '实测: 类库解码器在本机**无法还原 ASCII 特殊字符**的转义(%20/%26/%3D 原样返回, 只还原非 ASCII), '
        '故当结果仍残留 %HH 时本工具会自动改用页面内 decodeURIComponent 补齐 —— 一次调用即可拿到完整结果; '
        '回包 data.via 说明实际走的路径(lib:… 或 js:decodeURIComponent)。'
        'to_utf8/keep_escaped 直接透传给类库(keep_escaped:true 为类库原始行为); 注意 + 不会被当作空格", ',
        'Server uri_decode 描述改写', nl)
save(os.path.join(SRC, 'MCP_Server.wsv'), s, 'MCP_Server.wsv')

# ─────────── Core: 解码分支重写 ───────────
c, nl2 = load(os.path.join(SRC, 'MCP_Server_Core.wsv'))
c = rep(c, '''            变量 toUtf8 <类型 = 逻辑型>
            toUtf8 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "to_utf8", 真)
            // 类库把第三参声明为**逻辑型**(注释却说它是 "URI保留规则" 的位标识), 所以只能给两档。
            // 实测: 传 真 时 "a%20b%26c%3Dd" 原样返回(空格/&/= 的转义被"保留"), 只有非 ASCII 转义被还原;
            // 故默认取 假 = 不保留转义(全部还原)。需要旧行为可显式传 keep_escaped:true。
            变量 keepEscaped <类型 = 逻辑型>
            keepEscaped = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "keep_escaped", 假)
            变量 result <类型 = 文本型>
            result = FBrowser_Parser_URI解码 (data, toUtf8, keepEscaped)
            返回 (MCP_响应构建.构建简单JSON ("decoded", result))
''', '''            变量 toUtf8 <类型 = 逻辑型>
            toUtf8 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "to_utf8", 真)
            // 类库第三参声明为**逻辑型**(注释却说它是 "URI保留规则" 位标识), 只能给两档。四种组合实测:
            //   真 -> 只还原非 ASCII("%E4%B8%AD%E6%96%87"->中文), %20/%26/%3D 原样返回;
            //   假 -> 什么都不还原(更差)。故默认取 真(类库原始行为), 不制造回归。
            变量 keepEscaped <类型 = 逻辑型>
            keepEscaped = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "keep_escaped", 真)
            变量 result <类型 = 文本型>
            result = FBrowser_Parser_URI解码 (data, toUtf8, keepEscaped)
            变量 走页面兜底 <类型 = 逻辑型>
            走页面兜底 = 假
            // 类库解不开 ASCII 特殊字符的转义时, 用页面内 decodeURIComponent 补齐(一次调用完成)。
            如果 (MCP命令服务器.含百分号转义 (data) && MCP命令服务器.含百分号转义 (result))
            {
                变量 兜底浏览器 <类型 = 类_FBrowser_浏览器>
                兜底浏览器 = MCP命令服务器.取主浏览器 ()
                如果 (兜底浏览器.是否为空 () == 假 && 兜底浏览器.是否已关闭 () == 假)
                {
                    变量 兜底值 <类型 = 文本型>
                    兜底值 = MCP命令服务器.CDP执行JS并等待 ("(function(){try{return decodeURIComponent(\\"" + MCP_响应构建.JSON转义文本 (data) + "\\")}catch(e){return null}})()", 8000, 真)
                    如果 (兜底值 != "" && 兜底值 != "null" && MCP命令服务器.含百分号转义 (兜底值) == 假)
                    {
                        result = 兜底值
                        走页面兜底 = 真
                    }
                }
            }
            变量 uOut <类型 = YYJSON对象类>
            uOut.创建自文本 ("{}")
            uOut.加入文本成员 ("decoded", result)
            如果 (走页面兜底)
            {
                uOut.加入文本成员 ("via", "js:decodeURIComponent")
            }
            否则
            {
                uOut.加入文本成员 ("via", "lib:FBrowser_Parser_URI解码")
            }
            如果 (MCP命令服务器.含百分号转义 (result))
            {
                uOut.加入文本成员 ("warning", "结果里仍残留 %HH: 类库解码器在本机无法还原 ASCII 特殊字符的转义, 且当时无可用浏览器可走页面兜底; 可用 browser_execute_js code=decodeURIComponent(…), 或先 browser_navigate 建页后重试")
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, uOut.到可读文本 (YYJSON格式化选项.压缩)))
''', 'Core 解码分支 + 页面兜底', nl2)
save(os.path.join(SRC, 'MCP_Server_Core.wsv'), c, 'MCP_Server_Core.wsv')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
