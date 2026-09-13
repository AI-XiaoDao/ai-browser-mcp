# -*- coding: utf-8 -*-
"""汇总分类: 决定 363 候选各自归属, 输出统计与明细表数据"""
import io, json, os, re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
HERE = os.path.dirname(os.path.abspath(__file__))
cands = json.load(io.open(os.path.join(HERE, "_cg2_cands.json"), encoding="utf-8"))
covmap = json.load(io.open(os.path.join(HERE, "_cg2_covmap.json"), encoding="utf-8"))

# 有直调但调用点不在工具分支内(covmap.tool 为空)的候选
notool = []
for k, v in covmap.items():
    if v and not any(x["tool"] for x in v):
        notool.append(k)
print("有直调但非工具分支的候选 =", len(notool))
for k in sorted(notool):
    print("   ", k)
