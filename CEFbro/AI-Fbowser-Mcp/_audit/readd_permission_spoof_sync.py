# -*- coding: utf-8 -*-
"""把 browser_permission_spoof 重新纳入同步名单(第100轮因"20s 超时"撤回)。

本轮复核结论:
  · 它的异步任务**立即完成**(首次 mcp_result 轮询即得真实内容 "Permissions API 已伪装: ... → granted")
  · 用请求级 `sync_wait:true` 强制同步 -> **0.05s 成功**, 无超时
  => 第100轮那次超时**不可复现**, 属当时环境(疑与前面 11 个工具的残留状态有关), 不是工具缺陷。
仍按流程: 重新纳入后**再走一遍名单路径**(不传 sync_wait)验证, 若复现超时则再次撤回。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsf')
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '重纳权限伪装同步-写入前')

text = io.open(SRC, encoding='utf-8').read()
PAIRS = [
    ('        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise")\n',
     '        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise" || 规范名 == "browser_permission_spoof")\n'),
    ('            返回 (20000)\n',
     '            返回 (20000)\n'),
]
# 预算表: 找到注入组那行并补上
BUDGET_OLD = '        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise")\n'
BUDGET_NEW = '        如果 (规范名 == "browser_inject" || 规范名 == "browser_dom_set_html" || 规范名 == "browser_canvas_noise" || 规范名 == "browser_permission_spoof")\n'
c = text.count(BUDGET_OLD)
print('注入组名单行 命中 %d 处(应为2: 应同步等待 + 取同步等待毫秒)' % c)
if c != 2:
    print('!! 中止')
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server.wsv'))
open(SRC, 'wb').write(text.replace(BUDGET_OLD, BUDGET_NEW).encode('utf-8'))
after = io.open(SRC, encoding='utf-8').read()
print('已写入; 备份 -> %s' % BAK)
print('复核 browser_permission_spoof 名单出现次数: %d (应为2)'
      % after.count('规范名 == "browser_permission_spoof"'))
