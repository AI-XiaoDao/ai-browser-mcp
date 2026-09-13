# -*- coding: utf-8 -*-
r"""第140轮补丁 I: 让启动期事件**真的可查**(上一补丁只改对了一半)。

## 实测发现(补丁 H 之后仍查不到)
`main.wsv:304 记录应用监控事件` 内层还有一道总闸 `是否监控应用事件`(默认假, 且只能启动**之后**打开)
—— 各调用点虽然先判了 `是否监控启动流程`, 但内层这道闸把事件又拦掉了。
所以"把 启动流程 开关默认真"并不够: 事件在启动期**根本没被记录**。

## 修法
1. `main.wsv`: 5 处启动期记录点改为**直调** `MCP命令服务器.记录应用事件 (...)`(它们已各自判过
   `是否监控启动流程` 这个**本族**开关); 保留 `记录应用监控事件` 给运行期其他族(扩展/渲染/IPC)用。
2. `MCP_Server.wsv`: 把"落库启动期缓冲"抽成 `落库启动期事件缓冲 ()`, 并在**查询路径** `查询事件日志`
   开头也调用它 —— 否则缓冲要等"下一次事件"才会 flush, 而启动期事件之后再无同族事件时永远看不到。
3. `查询事件日志` 的 app_* 查询闸门: 启动族(`app_startup_*`)允许用**本族开关** `是否监控启动流程` 放行
   (现在是默认真), 不再强制要求先开总闸 —— 否则"事件已入库却查不出来"。

用法: py -3 _audit\_apply_round140i.py [--apply]
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
MAIN = os.path.join(ROOT, 'src', 'main.wsv')
APPLY = '--apply' in sys.argv

# ── I1: main.wsv 的 5 处启动期记录点改为直调 ──
MAIN_NAMES = ['app_startup_request_context_ready', 'app_startup_child_process', 'app_startup_webkit_init']
MAIN_JSON = ['app_startup_cmdline', 'app_startup_message_pump']
MAIN_NOTE = ('''        // 直调 记录应用事件(不经 记录应用监控事件): 那个包装里还有一道总闸 `是否监控应用事件`(默认假,\n'''
             '''        // 只能在启动**之后**打开) —— 用在这里会让启动期事件**永远记不下来**(本族开关判过也没用)。\n''')

# ── I2: 抽出"落库启动期缓冲"并让查询路径也 flush ──
FLUSH_ANCHOR_OLD = '''        如果 (启动期事件缓冲.取成员数 () >= 5)
        {
            // 先整体取出再逐条落库(避免在循环里持续操作同一数组); 顺序与产生顺序一致
            变量 待落库 <类型 = 文本数组类>
            异步缓存锁.加锁 ()
            计次循环 (启动期事件缓冲.取成员数 ())
            {
                待落库.加入成员 (启动期事件缓冲.取成员 (取循环索引 ()))
            }
            // 清空缓冲: 文本数组类没有"清空()", 项目既有做法是循环 删除成员(0) (见 清空持久V8扩展)
            判断循环 (启动期事件缓冲.取成员数 () > 0)
            {
                启动期事件缓冲.删除成员 (0)
            }
            异步缓存锁.解锁 ()
            变量 落库位 <类型 = 整数 值 = 0>
            判断循环 (落库位 + 4 < 待落库.取成员数 ())
            {
                写事件日志行 (待落库.取成员 (落库位), 待落库.取成员 (落库位 + 1), 文本到整数 (待落库.取成员 (落库位 + 2)), 待落库.取成员 (落库位 + 3), 文本到长整数 (待落库.取成员 (落库位 + 4)))
                落库位 = 落库位 + 5
            }
        }'''
FLUSH_ANCHOR_NEW = '''        落库启动期事件缓冲 ()
    }

    # 把启动期内存缓冲落库(供"实时写入"与"查询"两条路径共用 —— 只在写入路径 flush 的话,
    # 启动期事件会在"之后再无同族事件"时永远查不到)。
    方法 落库启动期事件缓冲 <公开 静态 @输出名 = "FlushStartupEventBuffer" @强制输出 = 真>
    {
        如果 (缓存数据库可用 () == 假 || 启动期事件缓冲.取成员数 () < 5)
        {
            返回
        }
        // 先整体取出再逐条落库(避免在循环里持续操作同一数组); 顺序与产生顺序一致
        变量 待落库 <类型 = 文本数组类>
        异步缓存锁.加锁 ()
        计次循环 (启动期事件缓冲.取成员数 ())
        {
            待落库.加入成员 (启动期事件缓冲.取成员 (取循环索引 ()))
        }
        判断循环 (启动期事件缓冲.取成员数 () > 0)
        {
            启动期事件缓冲.删除成员 (0)
        }
        异步缓存锁.解锁 ()
        变量 落库位 <类型 = 整数 值 = 0>
        判断循环 (落库位 + 4 < 待落库.取成员数 ())
        {
            写事件日志行 (待落库.取成员 (落库位), 待落库.取成员 (落库位 + 1), 文本到整数 (待落库.取成员 (落库位 + 2)), 待落库.取成员 (落库位 + 3), 文本到长整数 (待落库.取成员 (落库位 + 4)))
            落库位 = 落库位 + 5
        }'''

QUERY_ANCHOR = '''        如果 (缓存数据库可用 () == 假)
        {
            返回 ("[]")
        }'''
QUERY_NEW = '''        如果 (缓存数据库可用 () == 假)
        {
            返回 ("[]")
        }
        // 查询前先把启动期缓冲落库: 启动期事件只发生一次, 若只靠"下一次写入"触发 flush, 它们可能永远查不到
        落库启动期事件缓冲 ()'''

APP_GATE_OLD = '''            // 监控开关未开启'''
EDITS = [
    (SERVER, 'I2a 抽出 落库启动期事件缓冲', FLUSH_ANCHOR_OLD, FLUSH_ANCHOR_NEW),
    (SERVER, 'I2b 查询前 flush 缓冲', QUERY_ANCHOR, QUERY_NEW),
]
for nm in MAIN_NAMES:
    old = '        记录应用监控事件 ("%s", "")' % nm
    new = MAIN_NOTE + '        MCP命令服务器.记录应用事件 ("%s", "")' % nm
    EDITS.append((MAIN, 'I1 %s 改直调' % nm, old, new))
for nm in MAIN_JSON:
    old = '        记录应用监控事件 ("%s", 事件数据.到可读文本 (YYJSON格式化选项.压缩))' % nm
    new = MAIN_NOTE + '        MCP命令服务器.记录应用事件 ("%s", 事件数据.到可读文本 (YYJSON格式化选项.压缩))' % nm
    EDITS.append((MAIN, 'I1 %s 改直调(带数据)' % nm, old, new))


def main():
    print('== 第140轮补丁 I (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-42s 锚点未找到(可能已应用/写法不同)' % tag)
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
