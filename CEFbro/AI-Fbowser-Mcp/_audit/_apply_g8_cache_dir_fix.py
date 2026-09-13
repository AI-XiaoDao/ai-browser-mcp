# -*- coding: utf-8 -*-
r"""G8 修正: 类库 FBrowser_取初始化缓存目录() 在**本机安装版类库里编译不过**, 改为按同一开关推导。

实测(编译证据): 调用该静态方法后, 本地 C++ 编译器报
    <E:\HSPC\...\FBrowser\FBroLib.v>, 155: 错误: error C3861: 'IsEmpty': 找不到标识符
—— 该类库方法体在静态上下文里用了非静态成员 IsEmpty(), 属**类库自身缺陷**(技能文档版 V4.0.0 与
安装版 5.36 的差异; 这正是"把类库方法接上并编译"这条冒烟测试要抓的东西)。
故改为: 与 main.wsv 启动分支**同一个开关** MCPStdio桥.是否为Stdio模式() 推导, 并在响应里如实标注来源
(cache_dir_source), 绝不把"猜出来的路径"当既成事实 —— 同时说明 stdio 分支下旧实现的硬编码值是错的。

行尾: 该文件是 CR CR LF(混合 1 处 CRLF), 本脚本按**原行尾**写回, 不做静默转码。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')

OLD = [
    '变量 全局缓存目录 <类型 = 文本型>',
    '全局缓存目录 = FBrowser_取初始化缓存目录 ()',
    '变量 缓存目录来源 <类型 = 文本型>',
    '如果 (全局缓存目录 != "")',
    '{',
    '缓存目录来源 = "classlib: FBrowser_取初始化缓存目录"',
    '}',
    '否则',
    '{',
    '缓存目录来源 = "derived: 与 main.wsv 同一开关(是否为Stdio模式)"',
    '如果 (MCPStdio桥.是否为Stdio模式 ())',
    '{',
    '全局缓存目录 = 取运行目录 () + "\\\\CacheData\\\\GlobalData_Stdio"',
    '}',
    '否则',
    '{',
    '全局缓存目录 = 取运行目录 () + "\\\\CacheData\\\\GlobalData"',
    '}',
    '}',
]

NEW = [
    '// 约束: 取路径只能按 main.wsv 启动分支的**同一个开关**推导, 不能硬编码 ——',
    '// stdio/headless 实例用的是 CacheData 下的 GlobalData_Stdio, 硬编码 GlobalData 会给出一个"真实存在',
    '// 但属于另一个实例"的路径(最难发现的一类错值: 连存在性校验都通不出问题)。',
    '// 注: 类库 FBrowser_取初始化缓存目录() 本机**编译不过**(FBroLib.v:155 error C3861 IsEmpty),',
    '// 故此处不做类库读取, 而是如实标注取值来源 cache_dir_source, 让调用方知道这是推导值而非内核回报值。',
    '变量 是否Stdio <类型 = 逻辑型>',
    '是否Stdio = MCPStdio桥.是否为Stdio模式 ()',
    '变量 全局缓存目录 <类型 = 文本型>',
    '如果 (是否Stdio)',
    '{',
    '全局缓存目录 = 取运行目录 () + "\\\\CacheData\\\\GlobalData_Stdio"',
    '}',
    '否则',
    '{',
    '全局缓存目录 = 取运行目录 () + "\\\\CacheData\\\\GlobalData"',
    '}',
    '变量 缓存目录来源 <类型 = 文本型>',
    '缓存目录来源 = "derived: 与 main.wsv 同一开关(是否为Stdio模式), 非内核回报值"',
]


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == block]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    txt = raw.decode('utf-8')
    # 保留原行尾: 按行切片(保留每行尾部空白/CR 序列)
    lines = txt.split('\n')
    hits = find_block(lines, OLD)
    assert len(hits) == 1, '锚点命中 %d 次(期望 1)' % len(hits)
    s = hits[0]
    # 该块每一行都带尾随 '\r'(CRCRLF 文件的中间行), 取锚点行的行尾前缀
    tail = '\r' if lines[s].endswith('\r') else ''
    print('锚点 @%d, 行尾 tail=%r, 块 %d 行' % (s + 1, tail, len(OLD)))
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    new = [indent + x + tail for x in NEW]
    out = lines[:s] + new + lines[s + len(OLD):]
    joined = '\n'.join(out)
    assert '全局缓存目录 = FBrowser_取初始化缓存目录 ()' not in joined, '仍残留类库调用(赋值形式)'
    assert 'FBrowser_取初始化缓存目录 ()' not in joined.replace(
        '类库 FBrowser_取初始化缓存目录() 本机**编译不过**', ''), '仍有可执行调用'
    assert joined.count('缓存目录来源 = "derived:') == 1, '来源标注缺失'
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(joined)
        back = open(TARGET, 'rb').read().decode('utf-8')
        assert back == joined and not back.startswith('\ufeff'), '写盘校验失败'
        print('已写入 %s (块 %d 行 -> %d 行)' % (TARGET, len(OLD), len(new)))
    else:
        print('[dry-run] 块 %d 行 -> %d 行; 不落盘' % (len(OLD), len(new)))


main()
