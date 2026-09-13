# -*- coding: utf-8 -*-
"""① docs/index.html: 修掉与实现不符的"开启 10 项", 并去掉指向**不存在文件**的死链;
② `_audit/mass_probe.py`: 给 browser_vip_load_extension 加探针参数(它现在必须给 path 或 crx_path,
   否则台账每次都会记一条 fail —— 那是探针缺参, 不是功能缺陷)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = []

# ── ① docs/index.html ──
D = os.path.join(ROOT, 'docs', 'index.html')
raw = open(D, 'rb').read()
text = raw.decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
DEAD = '使用技能书.md'
n_dead = text.count('/docs/' + DEAD)
print('死链引用处 = %d' % n_dead)
EDITS = [
    # 数字修正: collect 的 event_all_enable 现在是 26 项且与内核一致
    ('<code>event_all_enable</code> 开启 10 项（<strong>不含</strong> 资源与键盘焦点两类高频噪音，需单独 <code>event_resource_enable</code> / <code>event_focus_enable</code>）。',
     '<code>event_all_enable</code> 开启 <strong>26 项</strong>（13 事件族 + 3 日志 + 10 扩展族），与 '
     '<code>browser_kernel_events_all</code> 的集合完全一致；<code>event_all_disable</code> 逐项对称关闭。'
     '如需精细控制，仍可用单项 <code>event_resource_enable</code> / <code>event_focus_enable</code> 等。'),
    # 死链 1: 按钮
    ('<a class="btn" href="/docs/使用技能书.md" target="_blank">使用技能书.md</a>',
     '<span class="btn" title="该文档未随包发布，请以 tools/list 与 docs/ 目录下的其它文档为准">使用技能书.md（未随包发布）</span>'),
    # 死链 2/3: 表格两处
    ('<td><a href="/docs/使用技能书.md">使用技能书.md</a></td>',
     '<td>使用技能书.md（未随包发布）</td>'),
    # 死链 4: 正文
    ('详见 <a href="/docs/使用技能书.md">使用技能书</a> 与 <code>tools/list</code> 动态清单。',
     '详见 <code>tools/list</code> 动态清单与 <code>docs/</code> 目录下的既有文档。'),
]
for old, new in EDITS:
    o = old.replace('\n', nl)
    c = text.count(o)
    if c == 0:
        problems.append('docs: 锚点未命中 %r' % old[:60])
        continue
    text = text.replace(o, new)
    print('   ok docs 替换 %d 处: %s' % (c, old[:48]))
open(D, 'wb').write(text.encode('utf-8'))

# ── ② mass_probe 探针参数 ──
P = os.path.join(ROOT, '_audit', 'mass_probe.py')
src = open(P, 'rb').read().decode('utf-8')
if 'browser_vip_load_extension' in src:
    print('   mass_probe 已有该工具条目, 跳过')
else:
    anchor = 'TOOL_ARG_OVERRIDES = {'
    if src.count(anchor) != 1:
        problems.append('mass_probe: 找不到 TOOL_ARG_OVERRIDES')
    else:
        src = src.replace(anchor,
                          anchor + '\n    # 需要真实路径的工具: 给一个不存在的 .crx 名(异步提交即回执, 无副作用)\n'
                                   '    "browser_vip_load_extension": {"crx_path": "mcp_probe.crx"},', 1)
        open(P, 'wb').write(src.encode('utf-8'))
        print('   ok mass_probe 已加 browser_vip_load_extension 探针参数')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
