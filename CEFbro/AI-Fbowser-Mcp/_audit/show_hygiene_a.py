# -*- coding: utf-8 -*-
"""打印 _hygiene_r98.md 的 (a) 小节原文, 以便按**内容**而不是行号定位待删注释。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
text = io.open(os.path.join(ROOT, '_audit', '_hygiene_r98.md'), encoding='utf-8').read()
secs = list(re.finditer(r'^#{2,4}.*$', text, re.M))
for i, m in enumerate(secs):
    if '(a)' not in m.group(0):
        continue
    end = secs[i + 1].start() if i + 1 < len(secs) else len(text)
    print(text[m.start():end])
    break
