# -*- coding: utf-8 -*-
"""删除 browser_wait 里**只写不读**的死字段 `_load_phase`。

证据(全 src 扫描, 含所有 .wsv, 排除备份):
  `_load_phase` 全库仅 1 处出现 —— MCP_Server_Core.wsv:2776 的**写入**;
  没有任何读取点(既无 yyjson取整数(...,"_load_phase") 也无别处引用)。
它写入的是常量 0 且从不更新, 却暗示存在一个并不存在的阶段机 -> 属误导性死字段。
load_start 的实际判定走 poll 侧 `当前加载 == 期望加载` 或事件驱动的 解析等待任务, 与本字段无关。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '删除死字段_load_phase-写入前')

text = io.open(SRC, encoding='utf-8').read()
OLD = ('                如果 (what == "load_start")\n'
       '                {\n'
       '                    等待存储.加入整数成员 ("_load_phase", 0)\n'
       '                }\n')
n = text.count(OLD)
print('锚点命中 %d 次(应为1)' % n)
if n != 1:
    print('!! 中止')
    sys.exit(1)

# 删除前再次确认全库无读取点
files = {}
for fn in sorted(os.listdir(os.path.join(ROOT, 'src'))):
    if fn.endswith('.wsv') and '~vbak' not in fn:
        files[fn] = io.open(os.path.join(ROOT, 'src', fn), encoding='utf-8').read()
total = sum(t.count('load_phase') for t in files.values())
print('全库 load_phase 出现 %d 次(删前)' % total)
if total != 1:
    print('!! 存在其它出现处, 中止(先人工确认是否有读取点)')
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
open(SRC, 'wb').write(text.replace(OLD, '', 1).encode('utf-8'))
after = io.open(SRC, encoding='utf-8').read()
print('已删除; 备份 -> %s' % BAK)
print('删后 load_phase 出现 %d 次(应为0)' % after.count('load_phase'))
