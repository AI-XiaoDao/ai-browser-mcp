# -*- coding: utf-8 -*-
import io, json, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
a = set(json.load(io.open(os.path.join(HERE, "_cg2_index_t0.json"), encoding="utf-8"))["tools"])
b = set(json.load(io.open(os.path.join(HERE, "_cg2_index.json"), encoding="utf-8"))["tools"])
print("t0 =", len(a), " now =", len(b))
print("新增:", sorted(b - a))
print("消失:", sorted(a - b))
