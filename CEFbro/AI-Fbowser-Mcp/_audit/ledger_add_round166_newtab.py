# -*- coding: utf-8 -*-
r"""ledger_add_round166_newtab.py —— 第 165/166 轮新工具 browser_vip_new_tab 落账(一次性)。

该工具为 MUTATING_SKIP(真实创建新标签浏览器, 通用探针空参会污染后续所有多浏览器判定),
tool_ledger 对跳过项不落账, 故按 _apply_round135_ledger.py 先例直接写台账:
受控实测脚本 _audit/verify_round165_newtab.py 真机 9/9 通过(本机为谷歌模式 运行时风格=1)。
"""
import io
import json
import os
import time

base = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(base, '_tool_ledger.json')
MD = os.path.join(base, '_tool_ledger.md')
TOOL = 'browser_vip_new_tab'

with io.open(LEDGER, encoding='utf-8') as f:
    d = json.load(f)

if TOOL in d:
    print('!! 台账已有该工具, 无需重复落账: %s' % TOOL)
    raise SystemExit(2)

rnd = max([int(r.get('round') or 0) for r in d.values()] or [0]) + 1
ts = time.strftime('%m-%d %H:%M')
note = ('真机实测: verify_round165_newtab 通过 (9/9) || 空url→高级_创建标签浏览器(browser_list'
        '新增id=2, 真实验证)并browser_close readback确认移除; ftp://被http/https窄化拦截; '
        '非谷歌模式(运行时风格≠1)报可行动错误并给browser_create/browser_navigate替代; '
        '通用探针污染全局→MUTATING_SKIP, 本条目为受控落账')
d[TOOL] = {
    'tool': TOOL, 'status': 'pass', 'cls': 'OK_LIVE',
    'elapsed': 0.0, 'args': {}, 'note': note, 'ts': ts, 'manual': False, 'round': rnd,
}
with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
with io.open(MD, 'a', encoding='utf-8', newline='\n') as f:
    f.write(u'| %s | %d | `%s` | pass | - | OK_LIVE |  | %s |\n' % (
        ts, rnd, TOOL, note.replace('|', '/')[:110]))
print('已落账: %s -> OK_LIVE(受控实测 verify_round165_newtab 9/9) | 轮次 %d' % (TOOL, rnd))
