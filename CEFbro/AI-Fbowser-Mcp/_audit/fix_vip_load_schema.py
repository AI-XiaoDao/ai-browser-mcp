# -*- coding: utf-8 -*-
"""补做: browser_vip_load_extension 的工具描述与 schema(整行替换, 缩进自取)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')
idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_vip_load_extension"' in ln]
if len(idx) != 1:
    print('!! 定位 %d 行' % len(idx))
    sys.exit(1)
i = idx[0]
ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
new = (ind + '添加工具JSON ("browser_vip_load_extension", "VIP: 加载插件。'
       '两种形态: path=**已解压插件目录**(类库原文: 比 CRX 安装效率高, 推荐) 或 crx_path=.crx 插件包'
       '(类库原文: 概率性出现页面已打开但插件未装完, 装完刷新页面即生效)。两者给其一即可。'
       '回包 advanced_enabled 表示插件高级功能开关是否已开 —— 类库原文: 默认 CEF **不支持**插件 '
       'content_scripts.js 执行, 必须在该开关启用后才支持, 且**必须在加载插件前启用**'
       '(本服务已在进程启动时自动开启, 加载前再幂等补开)", '
       '多属性Schema文本 (属性项JSON ("path", "text", "已解压插件目录(与 crx_path 二选一)") + "," + '
       '属性项JSON ("crx_path", "text", "CRX 插件包完整路径(与 path 二选一)"), ""))')
if new.replace('\\"', '').count('"') % 2 != 0:
    print('!! 新行引号奇数')
    sys.exit(1)
lines[i] = new
open(P, 'wb').write(nl.join(lines).encode('utf-8'))
print('已改第 %d 行 (长度 %d)' % (i + 1, len(new)))
print('   %s' % new[:200])
