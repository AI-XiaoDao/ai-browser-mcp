# -*- coding: utf-8 -*-
"""把回包里硬编码的 advanced_enabled=true 改成**读真实标志**, 避免"断言而非回报"。
(这正是本项目反复强调的"不静默假成功"纪律 —— 开关没开就该显示 false。)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
n = text.count('advanced_enabled=true')
print('硬编码处: %d' % n)
if n != 2:
    print('!! 预期 2 处')
    sys.exit(1)
text = text.replace(
    'advanced_enabled=true',
    'advanced_enabled=" + 选择 (MCP命令服务器.VIP_插件高级功能已启用, "true", "false") + "')
open(P, 'wb').write(text.encode('utf-8'))
print('已改为读真实标志')
# 校验拼接后的行引号奇偶
for i, ln in enumerate(text.split('\n'), 1):
    if 'advanced_enabled=' in ln:
        raw = ln.replace('\\"', '').count('"')
        print('   行 %d 裸引号 %d %s' % (i, raw, 'OK' if raw % 2 == 0 else '★奇数'))
