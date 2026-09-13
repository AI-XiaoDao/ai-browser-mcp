# -*- coding: utf-8 -*-
r"""收紧 MEDIUM 口径: 只认 `vX.Y` 版本标签与 `R\d+` 批次标签。

实测残留的 7 条 MEDIUM 全是**段标题**或**行为/理由描述**:
  `// CDP逆向增强` / `// ── 隐式前置自动补齐 ──` / `// 判据收在读取器里: 9 个调用点统一受益, 新增调用点不必各自处理。` …
`增强/新增/补齐/优化/补充` 这些动词在本项目里主要用于**描述能力与行为**, 不是开发过程叙述。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
src = open(P, 'rb').read().decode('utf-8')

OLD = 'NOTE_MEDIUM = re.compile(r"v2\\.\\d|v1\\.\\d|新增|增强|补齐|补上|补充|优化|重构|R\\d+[:：]")'
NEW = ('# 收紧(第118轮): 只认**版本/批次标签**; `新增|增强|补齐|补上|补充|优化|重构` 在本项目里\n'
       '# 多用于描述能力与行为(段标题/理由句), 实测 7/7 残留全是这类, 故移出。\n'
       'NOTE_MEDIUM = re.compile(r"v\\d+\\.\\d|R\\d+[:：]")')
if src.count(OLD) != 1:
    print('!! 锚点命中 %d 次, 实际定义: ' % src.count(OLD))
    for ln in src.split('\n'):
        if 'NOTE_MEDIUM' in ln:
            print('   %r' % ln)
    sys.exit(1)
open(P, 'wb').write(src.replace(OLD, NEW, 1).encode('utf-8'))
print('MEDIUM 口径已收紧')
