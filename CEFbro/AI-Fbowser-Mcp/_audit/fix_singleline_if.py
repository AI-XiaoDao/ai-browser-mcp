# -*- coding: utf-8 -*-
"""把两个掩码助手里的**单行 if 块**改写成火山视窗合法的多行形式。

## 为什么要改(这是一次代价很高的教训)
我写成 `如果 (名 == "appcache") { 返回 (清理缓存.Appcache) }` —— 单行 if + 花括号。
火山视窗**不接受**这种写法, 后果不是"这一行报错", 而是**整个类构建失败**:
编译器随后在**别的文件**里报 `没有找到所指定的常量/变量/参数名称"MCP_核心分派"`(3 条级联错误),
从报错位置完全看不出真因在另一个文件的语法细节上。
故本脚本改写成项目通行的多行形式, 并加注释把这条坑记在原地。

自带校验: 改前必须命中预期条数, 改后必须为 0, 否则中止。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
s = io.open(P, encoding="utf-8").read()

# 匹配形如:  如果 (条件) { 返回 (表达式) }
pat = re.compile(r'^(?P<ind>[ ]*)如果 \((?P<cond>.+?)\) \{ 返回 \((?P<val>.+?)\) \}$', re.M)
hits = pat.findall(s)
print("改前匹配到单行 if 块: %d 处" % len(hits))
if len(hits) == 0:
    print("没有需要改的")
    sys.exit(0)


def to_multiline(m):
    ind = m.group("ind")
    return ("%s如果 (%s)\n%s{\n%s    返回 (%s)\n%s}"
            % (ind, m.group("cond"), ind, ind, m.group("val"), ind))


s2 = pat.sub(to_multiline, s)
# 同时把"这条坑"写进注释(放在第一个助手方法之前)
marker = "    # === 清理缓存的对象/类型掩码: 单项名称 → 类库常量 ==="
note = ("    # ⚠ 方言坑(实测代价高): 这两个方法最初写成单行 `如果 (c) { 返回 (x) }`, 火山**不接受**;\n"
        "    #   症状不是本行报错, 而是**整个类构建失败** —— 编译器随后在别的文件里报\n"
        "    #   `没有找到\"MCP_核心分派\"` 之类的级联错误, 从报错位置根本看不出真因。\n"
        "    #   故本文件里所有 if 块一律写多行形式。\n")
if marker in s2 and "方言坑(实测代价高)" not in s2:
    s2 = s2.replace(marker, note + marker, 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s2)
left = len(pat.findall(io.open(P, encoding="utf-8").read()))
print("改后仍匹配到单行 if 块: %d 处" % left)
sys.exit(0 if left == 0 else 1)
