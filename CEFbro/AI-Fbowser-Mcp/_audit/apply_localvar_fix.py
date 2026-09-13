# -*- coding: utf-8 -*-
"""把第三步确认的修复落到源文件里(并就地记下这条方言坑)。

真因(已由 _audit/bisect_step3.py 证实): **局部**文本变量不能写 `值 = ""` 初始化 ——
只有 `公开 静态` 成员变量可以。写了之后的症状不是本行报错, 而是整个类构建失败,
编译器在**别的文件**里报 "没有找到 MCP_核心分派" 之类级联错误, 报错位置毫无指向性。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
s = io.open(P, encoding="utf-8").read()

BAD1 = '变量 ccBad <类型 = 文本型 值 = ""'
BAD2 = '变量 ccTypeBad <类型 = 文本型 值 = ""'
a, b = s.count(BAD1), s.count(BAD2)
print("改前: ccBad=%d ccTypeBad=%d" % (a, b))
s = s.replace(BAD1, '变量 ccBad <类型 = 文本型>')
s = s.replace(BAD2, '变量 ccTypeBad <类型 = 文本型>')

ANCHOR = '                变量 ccTokens <类型 = 文本数组类>'
NOTE = ('                // ⚠ 方言坑(实测定位代价很高): **局部**文本变量不能写 `值 = ""` 初始化 ——\n'
        '                //   只有 `公开 静态` 的成员变量可以。写了之后症状不是本行报错, 而是**整个类构建失败**,\n'
        '                //   编译器会在**别的文件**里报"没有找到 MCP_核心分派"这类级联错误, 从报错位置看不出真因。\n'
        '                //   故此处两个"坏名字"变量声明不带 值。\n')
if "方言坑(实测定位代价很高)" not in s and ANCHOR in s:
    s = s.replace(ANCHOR, NOTE + ANCHOR, 1)
    print("已就地补上方言坑注释")

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
chk = io.open(P, encoding="utf-8").read()
print("改后残留: ccBad=%d ccTypeBad=%d (应为 0/0)"
      % (chk.count(BAD1), chk.count(BAD2)))
print("注释是否就位: %s" % ("方言坑(实测定位代价很高)" in chk))
