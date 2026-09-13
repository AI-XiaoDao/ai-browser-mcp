# -*- coding: utf-8 -*-
"""静态审计: **schema 声明的参数类型** 与 **代码实际使用的读取器** 是否矛盾。

动机(真实案例): browser_vip_fingerprint_geolocation 的 lat/lng 在 schema 里声明为 text,
代码却用 yyjson取小数 读 —— 于是**按 schema 正确传参**("39.9")也会被读成 0,
定位被静默置成 (0,0) 还报成功。这类"类型倒挂"会让**正确调用方受罚**。

方法:
  1) 解析 添加工具JSON ("工具名", "描述", schema) 里的 属性项JSON ("参数", "类型", "说明")
     -> 工具 -> {参数: 声明类型}
  2) 按 `方法名 == "工具名"` 切出分派分支, 收集分支内 yyjson取X (参数JSON, "参数") 用到的读取器
  3) 报告矛盾:
       · 声明 text   却用 取整数/取小数/取长整数/取逻辑  -> 传字符串会读成 0/假 (高危)
       · 声明 integer/number 却用 取文本 作为**唯一**读取 -> 传数字会读成 ""
       · 声明 boolean 却用 取文本 作为唯一读取
  4) 顺带列出"同一参数被多种读取器读"的情况(schema 与代码都不一致时常见)

只读源码, 不调用服务, 可与正在运行的真机测试并行。
"""
import io
import os
import re
import sys
from collections import defaultdict
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'src')

PROP = re.compile(r'属性项JSON\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,')
TOOL = re.compile(r'添加工具JSON\s*\(\s*"([^"]+)"\s*,')
BRANCH = re.compile(r'^\s*(?:如果|否则)\s*\(\s*方法名\s*==\s*"([^"]+)"')
READ = re.compile(r'yyjson取(文本|整数|小数|长整数|逻辑)\s*\(\s*([A-Za-z_\u4e00-\u9fff]+)\s*,\s*"([^"]+)"')

READER_KIND = {
    '文本': 'text', '整数': 'number', '小数': 'number',
    '长整数': 'number', '逻辑': 'boolean',
}
DECL_KIND = {'text': 'text', 'integer': 'number', 'number': 'number',
             'boolean': 'boolean', 'string': 'text'}


def read_lines(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return f.read().splitlines()


def strip_code(s):
    """去掉 // 注释(简化版, 足够本审计用)。"""
    i = s.find('//')
    return s[:i] if i != -1 else s


def scan_schemas():
    """工具 -> {参数: 声明类型}"""
    out = defaultdict(dict)
    reg = os.path.join(SRC, 'MCP_Server.wsv')
    for ln in read_lines(reg):
        if '添加工具JSON' not in ln:
            continue
        m = TOOL.search(ln)
        if not m:
            continue
        tool = m.group(1)
        for pm in PROP.finditer(ln):
            out[tool][pm.group(1)] = pm.group(2)
    return out


def scan_readers():
    """工具 -> {参数: set(读取器)}"""
    out = defaultdict(lambda: defaultdict(set))
    for name in sorted(os.listdir(SRC)):
        if not name.endswith('.wsv') or '~vbak' in name:
            continue
        lines = read_lines(os.path.join(SRC, name))
        cur = None
        for ln in lines:
            b = BRANCH.match(ln)
            if b:
                cur = b.group(1)
                continue
            if cur is None:
                continue
            for rm in READ.finditer(strip_code(ln)):
                out[cur][rm.group(3)].add(rm.group(1))
    return out


def main():
    decl = scan_schemas()
    uses = scan_readers()
    print('解析到工具 %d 个, 其中有参数读取记录的工具 %d 个' % (len(decl), len(uses)))

    high, mid, weird = [], [], []
    for tool, params in sorted(decl.items()):
        for p, dt in sorted(params.items()):
            dk = DECL_KIND.get(dt)
            rs = uses.get(tool, {}).get(p)
            if not rs:
                continue
            kinds = {READER_KIND[r] for r in rs if r in READER_KIND}
            if dk == 'text' and ('number' in kinds or 'boolean' in kinds):
                high.append((tool, p, dt, '/'.join(sorted(rs))))
            elif dk in ('number', 'boolean') and kinds == {'text'}:
                mid.append((tool, p, dt, '/'.join(sorted(rs))))
            elif len(kinds) > 1:
                weird.append((tool, p, dt, '/'.join(sorted(rs))))

    def dump(title, rows, note):
        print('\n=== %s (%d) ===' % (title, len(rows)))
        print('  %s' % note)
        for tool, p, dt, rs in rows:
            print('  %-40s %-16s 声明=%-8s 实际读取=%s' % (tool, p, dt, rs))

    dump('高危: 声明 text 却用数值/逻辑读取器', high,
         '按 schema 传字符串会被读成 0/假 -> 静默错误值(geolocation 案即此类)')
    dump('中危: 声明 数值/逻辑 却只用 取文本 读', mid,
         '按 schema 传数字/布尔会被读成空串')
    dump('可疑: 同一参数被多种类型的读取器读', weird,
         '通常说明 schema 与代码都没对齐, 需人工确认哪个才是对的')

    print('\n合计: 高危 %d, 中危 %d, 可疑 %d' % (len(high), len(mid), len(weird)))
    with io.open(os.path.join(HERE, 'report_typemismatch.txt'), 'w',
                 encoding='utf-8') as f:
        for title, rows in (('HIGH', high), ('MID', mid), ('WEIRD', weird)):
            for tool, p, dt, rs in rows:
                f.write('%s\t%s\t%s\tdecl=%s\tread=%s\n' % (title, tool, p, dt, rs))
    print('明细已写 report_typemismatch.txt')
    return 0


if __name__ == '__main__':
    sys.exit(main())
