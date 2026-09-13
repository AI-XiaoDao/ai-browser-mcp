# -*- coding: utf-8 -*-
"""① 卫生扫描的"死代码备注"存在系统性误报: 正则 `\\s*(...|否则|...)` 会把**以"否则"开头的说明性注释**
   也算成"被注释掉的语句"(如 `// 否则后续 touch_move 会误以为…`), 实测 7/7 全是这类散文。
   改为要求 `否则` 后面紧跟代码形态的 `(` 或 `{`。
② 3 条"残注释(已移除/已废弃/已禁用)"按"叙述改契约"重写: 保留实测约束, 去掉开发过程叙述。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
SCAN = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
BAK = os.path.join(ROOT, '备份', '残注释改契约-写入前')
problems = []

# ── ① 扫描器: 收紧 DEAD_COMMENT ──
s = open(SCAN, 'rb').read().decode('utf-8')
OLD = 'r"^\\s*//\\s*(变量\\s|常量\\s|如果\\s*\\(|否则|判断循环|计次循环|循环\\s*\\(|返回\\s*\\(|"'
NEW = 'r"^\\s*//\\s*(变量\\s|常量\\s|如果\\s*\\(|否则\\s*[({]|判断循环|计次循环|循环\\s*\\(|返回\\s*\\(|"'
if s.count(OLD) != 1:
    problems.append('扫描器 DEAD_COMMENT 锚点命中 %d 次' % s.count(OLD))
else:
    s = s.replace(OLD, NEW, 1)
    s = s.replace('DEAD_COMMENT = re.compile(',
                  '# 注意: `否则` 必须后接 ( 或 { 才算"被注释掉的语句"; 单纯的"否则…"是说明性散文,\n'
                  '# 早期写成裸 `否则` 导致 7/7 全是误报(见 报告 §132)。\n'
                  'DEAD_COMMENT = re.compile(', 1)
    open(SCAN, 'wb').write(s.encode('utf-8'))
    print('   ok 扫描器 DEAD_COMMENT 已收紧')

# ── ② 三条残注释改写成约束 ──
EDITS = [
    ('MCP_Server_Core.wsv',
     '        // === 尝试关闭 (已禁用) ===',
     '        // 浏览器关闭入口: 本服务统一走 browser_close / browser_shutdown, 不经此段'),
    ('MCP_Server_System.wsv',
     '        // === v1.6 VIP 标签页 (已禁用) ===',
     '        // VIP 标签页入口: 本项目**不开放**远程建标签页(见 browser_create_tab 的守卫与替代方案)'),
    ('MCP_Server_Reverse.wsv',
     '        // 该命令只认 interval; 旧代码多传的 maxDepth 实测被忽略(属另一命令的字段), 已移除',
     '        // 约束: 本命令只认 interval; maxDepth 属另一命令的字段, 传了会被内核忽略, 故不传'),
]
for fn, old, new in EDITS:
    p = os.path.join(SRC, fn)
    text = open(p, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != 1:
        problems.append('%s: 锚点命中 %d 次' % (fn, c))
        continue
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, fn)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    open(p, 'wb').write(text.replace(o, new.replace('\n', nl), 1).encode('utf-8'))
    print('   ok %s 残注释改为约束' % fn)

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
