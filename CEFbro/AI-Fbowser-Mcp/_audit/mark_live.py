# -*- coding: utf-8 -*-
r"""mark_live.py —— 把台账里某个 OK_MANUAL(人工核对)项更新为真机实测 pass。

用法: py -3 _audit\mark_live.py --tool <工具名> --script <verify脚本名> [--note 补充说明]

规则(用户硬要求: 每轮只测一个, 逐条记录):
  · 只有该工具的专用受控 verify 脚本真机跑通后, 才能调用本脚本;
  · 台账 JSON 更新: status=pass, cls=OK_LIVE, manual 标记移除, note 记录脚本名与日期;
  · 人读台账 _tool_ledger.md 追加一行(与 tool_ledger.py 的 append_md 同格式)。
"""
import io
import json
import os
import sys
import time

base = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(base, '_tool_ledger.json')
MD = os.path.join(base, '_tool_ledger.md')


def main():
    tool = None
    script = None
    note = ''
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == '--tool' and i + 1 < len(argv):
            tool = argv[i + 1]; i += 2
        elif argv[i] == '--script' and i + 1 < len(argv):
            script = argv[i + 1]; i += 2
        elif argv[i] == '--note' and i + 1 < len(argv):
            note = argv[i + 1]; i += 2
        else:
            i += 1
    if not tool or not script:
        print('用法: py -3 _audit\\mark_live.py --tool <工具名> --script <verify脚本名> [--note 说明]')
        return 2
    with io.open(LEDGER, encoding='utf-8') as f:
        d = json.load(f)
    if tool not in d:
        print('!! 台账里没有该工具: %s' % tool)
        return 2
    old = d[tool]
    if not old.get('manual') and 'OK_MANUAL' not in str(old.get('cls', '')):
        print('!! 该工具不是 OK_MANUAL 人工核对项(当前 cls=%s), 无需 mark_live' % old.get('cls'))
        return 2
    ts = time.strftime('%m-%d %H:%M')
    # 轮次必须是整数(tool_ledger 用 max(round)+1 生成下一轮): 取现有最大整数轮次 +1
    try:
        rnd = max([int(r.get('round') or 0) for r in d.values()] or [0]) + 1
    except Exception:
        rnd = 150
    d[tool] = {
        'tool': tool, 'status': 'pass', 'cls': 'OK_LIVE',
        'elapsed': old.get('elapsed', 0),
        'args': old.get('args', {}),
        'note': ('真机实测: %s 通过 || %s' % (script, note)).strip(' |')[:300],
        'ts': ts, 'manual': False, 'round': rnd,
    }
    with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    # 人读台账追加一行(与 append_md 同格式)
    with io.open(MD, 'a', encoding='utf-8', newline='\n') as f:
        f.write(u'| %s | %s | `%s` | pass | - | OK_LIVE |  | %s |\n' % (
            ts, rnd, tool, d[tool]['note'].replace('|', '/')[:110]))
    print('已更新: %s -> OK_LIVE(真机实测 %s) | 台账进度不变(328/328), 但该项从"人工核对"变为"真机实测"' % (tool, script))
    return 0


if __name__ == '__main__':
    sys.exit(main())
