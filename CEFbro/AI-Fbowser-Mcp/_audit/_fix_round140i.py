# -*- coding: utf-8 -*-
r"""修: 补丁 I2a 插入位置把 `记录事件日志` 的尾部(截断 + 写行)切到了新方法里, 导致
  `数据JSON` / `日志类型` 越界(编译报错原文: 没有找到所指定的常量/变量/参数名称)。

修法: 把这段尾部搬回 `记录事件日志`(紧跟 `落库启动期事件缓冲 ()` 之后)。
用法: py -3 _audit\_fix_round140i.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

TAIL_START = '        变量 存储JSON <类型 = 文本型>'
TAIL_END = '        写事件日志行 (日志类型, 事件名, 浏览器ID, 存储JSON, 取现行时间毫秒 ())'
HOOK = '        落库启动期事件缓冲 ()'


def main():
    lines = io.open(SERVER, encoding='utf-8', newline='').read().split('\n')
    # 0) 先定位 `方法 落库启动期事件缓冲` 声明行: 尾部块的搜索必须**从它之后**开始
    #    (同名 `变量 存储JSON` 在文件里还有另外两处, 从文件头搜会抓错)
    im = None
    for i, l in enumerate(lines):
        if l.strip().startswith('方法 落库启动期事件缓冲'):
            im = i
            break
    assert im is not None, '未找到 方法 落库启动期事件缓冲 声明'
    # 1) 定位尾部块(在 `落库启动期事件缓冲` 方法体内, 即错误位置)
    i0 = None
    for i in range(im, len(lines)):
        if lines[i] == TAIL_START:
            i0 = i
            break
    assert i0 is not None, '未找到尾部块起点'
    i1 = None
    for j in range(i0, len(lines)):
        if lines[j] == TAIL_END:
            i1 = j
            break
    assert i1 is not None, '未找到尾部块终点'
    tail = lines[i0:i1 + 1]
    # 2) 定位 `落库启动期事件缓冲 ()`(在 记录事件日志 内), 把尾部插到它后面
    ih = None
    for i, l in enumerate(lines):
        if l == HOOK and i < i0:
            ih = i
            break
    assert ih is not None, '未找到插入点 落库启动期事件缓冲 ()'
    out = lines[:i0] + lines[i1 + 1:]
    # 删除后 ih 位置不变(ih < i0)
    out = out[:ih + 1] + tail + out[ih + 1:]
    print('· 尾部块 %d 行已从方法体内搬回 `记录事件日志` (插入到第 %d 行之后)' % (len(tail), ih + 1))
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write('\n'.join(out))
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
