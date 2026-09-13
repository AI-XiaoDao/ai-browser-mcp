# -*- coding: utf-8 -*-
"""看有哪些可用的截图方案。"""
import importlib.util
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

for m in ('PIL', 'PIL.ImageGrab', 'mss', 'pyautogui', 'numpy', 'win32gui', 'ctypes'):
    try:
        print('%-16s %s' % (m, bool(importlib.util.find_spec(m))))
    except Exception as e:
        print('%-16s ? %s' % (m, e))
