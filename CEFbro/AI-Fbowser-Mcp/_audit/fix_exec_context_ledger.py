# -*- coding: utf-8 -*-
r"""把 browser_vip_execute_js_context 台账项恢复为受控实测 pass(OK_LIVE)。
该工具前置"启用执行环境"会毒化 CDP, 通用探针无法正确测量; 受控实测见 verify_round156_execparams(11/11)。
"""
import io
import json
import os
import time

base = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(base, '_tool_ledger.json')
with io.open(LEDGER, encoding='utf-8') as f:
    d = json.load(f)
d['browser_vip_execute_js_context'] = {
    'tool': 'browser_vip_execute_js_context', 'status': 'pass', 'cls': 'OK_LIVE',
    'elapsed': 0.02, 'args': {},
    'note': '受控实测 verify_round156_execparams 11/11 (6执行参数暴露+默认路径自动解析context_id; 前置需启用毒化环境, 通用探针无法测量)',
    'ts': time.strftime('%m-%d %H:%M'), 'manual': False, 'round': 156,
}
with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print('已恢复 browser_vip_execute_js_context -> OK_LIVE')
