# -*- coding: utf-8 -*-
"""工具描述校正: 把"默认项可用别名修改"这类**与实测相反**的承诺改成如实说明。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
raw = open(p, 'rb').read()
text = raw.decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

EDITS = [
    # ① 删除"默认项用标准ID改"的错误承诺 -> 如实说明实测不可改
    ('**修改类**的 命令ID 指向已存在条目, 浏览器默认菜单项用其 CEF 标准ID(如 后退=100)',
     '**修改类**的 命令ID 指向**本服务自建的**条目(26500..28500)。实测: 指向浏览器默认菜单项(标准ID 100..130 或其别名 back/reload/copy 等)的修改类**不会生效** —— 右键后用 action=get 看 apply_failed 会逐条说明; 创建类不受影响'),
    # ② mark 的适用范围
    ('mark(勾选)',
     'mark(勾选, 仅对 check/radio 类条目有效)'),
    # ③ 回读语义提醒
    ('触发需自行发键盘事件。命令ID 须在 26500..28500, 留 0 则由服务端自动分配。',
     '触发需自行发键盘事件。命令ID 须在 26500..28500, 留 0 则由服务端自动分配。'
     '施加结果可读回核对: action=get 的 verified_items/verify_mismatch(注意类库只读 getter 是否禁止 语义与名字相反, 实测它返回的是"是否可用", 服务端已按此校正)与 apply_failed(哪条没生效及原因)。'),
]
lines = text.split('\n')
idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_context_menu"' in ln]
if len(idx) != 1:
    print('!! 定位 %d 行' % len(idx))
    sys.exit(1)
i = idx[0]
ln = lines[i]
for old, new in EDITS:
    c = ln.count(old)
    if c != 1:
        print('!! 片段命中 %d 次: %r' % (c, old[:50]))
        sys.exit(1)
    ln = ln.replace(old, new, 1)
if ln.replace('\\"', '').count('"') % 2 != 0:
    print('!! 新行引号奇数')
    sys.exit(1)
lines[i] = ln
open(p, 'wb').write(nl.join(lines).encode('utf-8'))
print('描述已校正(第 %d 行), 新长度 %d' % (i + 1, len(ln)))
for kw in ('apply_failed', '仅对 check/radio', '是否禁止'):
    k = ln.find(kw)
    print('  [%s] ...%s...' % (kw, ln[max(0, k - 60):k + 90]))
