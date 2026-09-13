# -*- coding: utf-8 -*-
"""回归检测器: 异步结果库里是否存在**重复键**的 JSON。

为什么需要它(缺陷本质):
    YYJSON对象类.加入整数成员/加入文本成员  -> yyjson_mut_obj_add_*  (在尾部**追加**, 不覆盖)
    YYJSON对象类.取整数/取文本              -> yyjson_obj_get        (重复键返回**第一个**)
  于是本项目"解析已存 JSON -> 加入同名键 -> 再存回"的更新写法会产生重复键,
  读回永远是旧值 -> 状态机永久卡死。
  已实测后果: browser_scrape 永远停在 phase 2, 每轮轮询重提交一次提取子任务,
  直到超时报错(见报告第 61 节; db_async_results 每轮 +2)。

本检测器直接读应用自己的 SQLite(不经 MCP 协议、不经任何推断), 是这一缺陷类的
**独立事实来源**:
  * 任何一行出现重复键 -> 退出码 1 并打印该行(截断显示);
  * 额外统计每个键名在多少行里重复, 用于发现新的同类回归点。

用法:
  py -3 dupekey_scan.py                  # 全库扫描
  py -3 dupekey_scan.py --since 13500000 # 只看 start_time >= 该毫秒值的行
"""
import io
import json
import os
import re
import sqlite3
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, '..', '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                  'mcp_cache.db')
# 只统计"对象成员键"形态的键名, 避免把数组里的字符串值误当键
KEY = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:')

# 这些键天然允许在**嵌套子对象**里重复(例如每步都有自己的 status),
# 顶层重复才是状态机缺陷。这里用括号深度 1 限定。
STATE_KEYS = ('_phase', '_extract_task_id', '_check_task_id', '_poll_count',
              '_waiting', '_load_phase', '_browser_id', 'what')


def keys_at_depth1(js):
    """返回顶层(深度1)对象成员的键名列表。

    实现要点(上一版在这里写错了, 导致对任何输入都返回 [] 的假阴性):
    要在**字符串起始位置**判断"这是不是键名", 而不是在字符串结束位置 ——
    键名的特征是"该字符串后面紧跟冒号"。故: 遇到 '"' 记下 start, 扫描到闭合引号,
    再看其后第一个非空字符是否为 ':'。
    """
    out = []
    depth = 0
    i = 0
    n = len(js)
    while i < n:
        c = js[i]
        if c == '"':
            start = i
            i += 1
            esc = False
            while i < n:
                if esc:
                    esc = False
                elif js[i] == '\\':
                    esc = True
                elif js[i] == '"':
                    break
                i += 1
            end = i                      # 指向闭合引号
            j = end + 1
            while j < n and js[j] in ' \t\r\n':
                j += 1
            if j < n and js[j] == ':' and depth == 1:
                out.append(js[start + 1:end])
            i = end + 1
            continue
        if c == '{' or c == '[':
            depth += 1
        elif c == '}' or c == ']':
            depth -= 1
        i += 1
    return out


def main():
    since = 0
    if '--since' in sys.argv:
        since = int(sys.argv[sys.argv.index('--since') + 1])
    if not os.path.exists(DB):
        print('!! 数据库不存在: %s' % DB)
        print('   (需先运行过一次应用; 或路径已变)')
        return 2

    con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\', '/'), uri=True)
    cur = con.cursor()
    rows = cur.execute(
        'SELECT task_id, result_json FROM async_results').fetchall()
    total = len(rows)
    bad = []
    from collections import Counter
    dupkinds = Counter()
    for tid, js in rows:
        if not js:
            continue
        ks = keys_at_depth1(js)
        c = Counter(ks)
        dups = {k: v for k, v in c.items() if v > 1}
        if dups:
            bad.append((tid, dups, js[:260]))
            for k in dups:
                dupkinds[k] += 1

    print('扫描 %s' % os.path.relpath(DB, os.path.join(HERE, '..')))
    print('async_results 行数 = %d' % total)
    print('含顶层重复键的行数 = %d' % len(bad))
    if bad:
        for tid, dups, js in bad[:10]:
            print('  %s  重复键=%s' % (tid, dups))
            print('     %s' % js.replace('\n', ' '))
    if dupkinds:
        print('重复键统计(键名: 出现的行数) = %s' % dict(dupkinds))
    print()
    if bad:
        print('=> 检出重复键: 这些行的状态键读回的是**旧值**, 相关状态机会卡死/行为异常')
        return 1
    print('=> 未检出顶层重复键: 状态机写回路径正常')
    return 0


if __name__ == '__main__':
    sys.exit(main())
