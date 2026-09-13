# -*- coding: utf-8 -*-
"""修 C 类缺陷①: browser_find_by_tag 在本 MCP 内**永远不可能成功** —— 补上"设置用户标识"的通路。

根因(本轮查清):
  · 类库里**用户标识只能在创建浏览器时设置**: FBrowser_创建浏览器 的最后一个参数是 `标识`
    (FBroLib.wsv:563, 签名第 8 参), FBrowser_创建后台浏览器 亦然(:604, 第 7 参);
    `取用户标识` 的注释也写"浏览器创建的时候传递设置的值"。全库**没有**运行期设置标识的接口。
  · 而本项目 browser_create 只暴露 url/background, 两个创建调用都把 `标识` 那个位置**留空**
    (main.wsv:228 可见 / :221 后台) -> 标识恒为空 -> browser_find_by_tag 永远查不到东西,
    而它的失败文案还建议调用方去用**只读的** browser_user_tags "设置"标识(把读工具当写工具)。

修法(顺着项目**既有**的"待创建"握手惯例, 不发明新机制):
  1. 新增静态握手字段 待创建标识(与 待创建URL 并列);
  2. browser_create 支持 tag 参数 -> 写入 待创建标识(未传则写空串, 防止上一个标签泄漏到新浏览器);
  3. main.wsv 的两个创建调用把该字段放回类库签名里**本来就有的** `标识` 位置。
之后: browser_create{tag:"x"} -> browser_user_tags 能列出 -> browser_find_by_tag{tag:"x"} 能查到。

为什么不选"只改文案": 那是把"功能缺失"伪装成"参数不对"。本目标要求能力真正可用,
而这条例外链路的修复成本很小(5 处改动、复用现有握手字段、类库槽位现成)。
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
MAIN = os.path.join(ROOT, 'src', 'main.wsv')
BAK = os.path.join(ROOT, '备份', '用户标识通路-写入前')

# ---- 1) 新增握手字段 ----
DECL_OLD = '    变量 待创建URL <公开 静态 类型 = 文本型 值 = "" @输出名 = "PendingCreateURL">'
DECL_NEW = '\n'.join([
    DECL_OLD,
    '    // 用户标识: 类库里"标识"只能在创建浏览器时传入(FBroLib 创建函数的最后一个参数), 且没有运行期设置接口。',
    '    // 该字段与 待创建URL 同一套"待创建"握手, 由 browser_create 写入、main.wsv 在创建时取用。',
    '    变量 待创建标识 <公开 静态 类型 = 文本型 值 = "" @输出名 = "PendingCreateTag">',
])

# ---- 2) schema 增加 tag ----
SCHEMA_OLD = ('适合纯后台刷新取数); 默认false=可见窗口。实测: browser_id 目标隔离正确、'
              '不影响主浏览器的 CDP 工具, 且读取(execute_js/get_text)均正常"), ""))')
SCHEMA_NEW = ('适合纯后台刷新取数); 默认false=可见窗口。实测: browser_id 目标隔离正确、'
              '不影响主浏览器的 CDP 工具, 且读取(execute_js/get_text)均正常") + "," + '
              '属性项JSON ("tag", "text", "可选: 用户标识(类库只支持**创建时**设置, 无运行期设置接口)。'
              '设置后可用 browser_find_by_tag {tag} 找到该浏览器, browser_user_tags 可列出全部标识; '
              '标识需唯一(重复时会取到既有那个)。不传则新浏览器没有标识"), ""))')

# ---- 3) browser_create 写入握手字段 ----
SET_OLD = '\n'.join([
    '            MCP命令服务器.待创建锁.加锁 ()',
    '            MCP命令服务器.待创建完成 = 假',
    '            MCP命令服务器.待创建URL = 握手URL',
    '            MCP命令服务器.待创建锁.解锁 ()',
])
SET_NEW = '\n'.join([
    '            MCP命令服务器.待创建锁.加锁 ()',
    '            MCP命令服务器.待创建完成 = 假',
    '            变量 标识参数 <类型 = 文本型>',
    '            标识参数 = MCP命令服务器.yyjson取文本 (参数JSON, "tag")',
    '            // 未传 tag 时写空串: 否则上一次创建的标识会泄漏给这个新浏览器(标识重复会取到既有那个)。',
    '            MCP命令服务器.待创建标识 = 标识参数',
    '            MCP命令服务器.待创建URL = 握手URL',
    '            MCP命令服务器.待创建锁.解锁 ()',
])

# ---- 4/5) main.wsv 两个创建调用补上类库签名里本来就有的"标识"槽位 ----
MAIN_BG_OLD = 'FBrowser_创建后台浏览器 (bgUrl, 浏览器配置, , , 浏览器事件, , )'
MAIN_BG_NEW = ('FBrowser_创建后台浏览器 (bgUrl, 浏览器配置, , , 浏览器事件, , '
               'MCP命令服务器.待创建标识)')
MAIN_VIS_OLD = 'FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, , , 浏览器事件, , )'
MAIN_VIS_NEW = ('FBrowser_创建浏览器 (url, 窗口信息, 浏览器配置, , , 浏览器事件, , '
                'MCP命令服务器.待创建标识)')

EDITS = [
    ('SRV 握手字段', SRV, DECL_OLD, DECL_NEW),
    ('SRV schema tag', SRV, SCHEMA_OLD, SCHEMA_NEW),
    ('CORE 写入标识', CORE, SET_OLD, SET_NEW),
    ('MAIN 后台创建', MAIN, MAIN_BG_OLD, MAIN_BG_NEW),
    ('MAIN 可见创建', MAIN, MAIN_VIS_OLD, MAIN_VIS_NEW),
]


def main():
    texts = {p: io.open(p, encoding='utf-8', newline='').read() for p in (SRV, CORE, MAIN)}
    for label, path, old, new in EDITS:
        n = texts[path].count(old)
        print("[%-14s] %s 出现 %d 次" % (label, os.path.basename(path), n))
        if n != 1:
            print("   !! 预期 1 次, 中止(不改任何文件)")
            return 1
    if '待创建标识' in texts[SRV]:
        print("!! 似乎已添加过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, CORE, MAIN):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    for label, path, old, new in EDITS:
        texts[path] = texts[path].replace(old, new)
    for p, t in texts.items():
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print("OK: 5 处替换完成")
    for p in (SRV, CORE, MAIN):
        raw = io.open(p, 'rb').read()
        print("复核 %-22s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
