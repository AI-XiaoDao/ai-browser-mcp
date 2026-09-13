# -*- coding: utf-8 -*-
r"""334 个工具从第一个开始、一个回合一个、顺序真机测试(用户 2025-09-13 明确要求)。

用法:
  py -3 _audit\sweep334.py --status       # 进度总览
  py -3 _audit\sweep334.py --next         # 执行下一回合(游标处的 1 个工具)
  py -3 _audit\sweep334.py --all          # 从第一个开始顺序跑完全部 334 个
  py -3 _audit\sweep334.py --tool 名      # 复测指定工具(不动游标)
  py -3 _audit\sweep334.py --reset        # 游标归零(重新从第一个开始)

每回合: 调工具一次 → 分类(pass/fail+失败性质) → 读 mcp_console.log 里该工具的执行日志行
(双证据) → 写 `_sweep334.json` + `_sweep334.md`。
LETHAL/MUTATING_SKIP 打印跳过(它们已有受控 verify 证据在台账, 通用探针会污染/打死实例)。
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import mass_probe as MP
import cold_matrix as CM
import _app_launch

TOOL_TIMEOUT = 40
STATE = os.path.join(HERE, '_sweep334.json')
MD = os.path.join(HERE, '_sweep334.md')


def load_state():
    if os.path.exists(STATE):
        with io.open(STATE, encoding='utf-8') as f:
            return json.load(f)
    return {'cursor': 0, 'results': {}}


def save_state(st):
    with io.open(STATE, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def append_md(row):
    new = not os.path.exists(MD)
    with io.open(MD, 'a', encoding='utf-8', newline='\n') as f:
        if new:
            f.write(u'# 334 回合逐个测试台账\n\n'
                    u'> 由 `_audit/sweep334.py` 逐回合追加: 一个回合一个工具, 回包+控制台日志双证据。\n\n'
                    u'| 时间 | 回合 | 工具 | 状态 | 耗时 | 类别 | 说明 |\n'
                    u'|---|---|---|---|---|---|---|\n')
        f.write(u'| %s | %d | `%s` | %s | %.2fs | %s | %s |\n' % row)


def log_evidence(name):
    """mcp_console.log 里该工具的执行日志行(最多3条, 双证据用)。"""
    hits = []
    for ln in _app_launch.read_log(400):
        if name in ln and ('调用工具' in ln or '执行:' in ln or 'RPC方法' in ln):
            hits.append(ln.strip()[:100])
    return hits[-3:]


def test_one(name, schema, desc, round_no):
    args, _anotes = MP.build_args(schema, desc, name)
    props = (schema or {}).get('properties', {}) or {}
    for k, v in list(args.items()):
        t = ((props.get(k) or {}).get('type') or '').lower()
        if t in ('integer', 'number') and not isinstance(v, (int, float)):
            try:
                args[k] = int(str(v))
            except Exception:
                args[k] = 1
    if name in MP.SPECIAL_ARGS:
        args = dict(MP.SPECIAL_ARGS[name])
    if name in getattr(MP, 'DYNAMIC_ARGS', {}):
        try:
            extra = MP.DYNAMIC_ARGS[name](None)
            if extra and all(v not in (0, '', None) for v in extra.values()):
                args = dict(args)
                args.update(extra)
        except Exception:
            pass
    pre = []
    for pname, pargs in (MP.TOOL_PRE_CALLS.get(name) or []):
        try:
            presp = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                                  'params': {'name': pname, 'arguments': pargs}}, TOOL_TIMEOUT)
            pcls, _ = MP.classify(pname, pargs, presp, 0, None)
            pre.append('%s->%s' % (pname, pcls))
        except Exception as ex:
            pre.append('%s->EXC:%s' % (pname, ex))
    st = time.time()
    err = None
    try:
        resp = CM.http_post({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                             'params': {'name': name, 'arguments': args}}, TOOL_TIMEOUT)
    except Exception as ex:
        resp, err = None, str(ex)
    el = time.time() - st
    cls, note = MP.classify(name, args, resp, el, err)
    rec = {'tool': name, 'cls': cls, 'elapsed': round(el, 2), 'args': args,
           'note': (note or '')[:300], 'ts': time.strftime('%m-%d %H:%M'), 'round': round_no}
    if pre:
        rec['pre_calls'] = pre
        rec['note'] = (('[前置] ' + '; '.join(pre) + ' || ') + (note or ''))[:300]
    if cls in ('OK', 'OK_EMPTY_TEXT'):
        rec['status'] = 'pass'
    else:
        kind, why = CM.prereq_of(note)
        rec['kind'] = kind
        rec['why'] = why
        rec['status'] = 'fail'
    if cls != 'TIMEOUT' and (cls in ('TRANSPORT_ERR', 'NO_RESPONSE') or el > 4.0) and not CM.alive():
        rec['wedge'] = True
        rec['status'] = 'fail(wedge)'
        print('      !! 把实例卡死了 -> 冷重启')
        CM.cold_restart()
    ev = log_evidence(name)
    rec['log'] = ev
    return rec


def main():
    argv = sys.argv[1:]
    st = load_state()
    tools = CM.http_get('/tools/list', timeout=20).get('tools', [])
    names = [t.get('name') for t in tools]

    if '--status' in argv:
        res = st['results']
        total = len(tools)
        done = [k for k in names if k in res]
        ok = [k for k in done if res[k]['status'] == 'pass']
        bad = [k for k in done if res[k]['status'].startswith('fail')]
        skip = [k for k in done if res[k]['status'] == 'skip']
        print('== 334 回合进度 ==')
        print('工具总数 %d | 已测 %d | 游标 %d | 通过 %d | 跳过 %d | 失败 %d' %
              (total, len(done), st['cursor'], len(ok), len(skip), len(bad)))
        from collections import Counter
        for k, v in Counter(res[t].get('kind', '') for t in bad).most_common():
            print('   失败性质 %-12s %d' % (k or '(未分类)', v))
        if bad:
            print('失败明细:')
            for t in sorted(bad):
                print('   %-40s %-10s %s' % (t, res[t].get('kind', ''), (res[t].get('note') or '')[:80]))
        return 0

    if '--reset' in argv:
        st = {'cursor': 0, 'results': st['results']}
        save_state(st)
        print('游标已归零')
        return 0

    if '--tool' in argv:
        nm = argv[argv.index('--tool') + 1]
        t = next((x for x in tools if x.get('name') == nm), None)
        if not t:
            print('!! 没有该工具: %s' % nm)
            return 2
        todo = [(nm, t)]
        single = True
    elif '--all' in argv:
        st['cursor'] = 0
        todo = [(t.get('name'), t) for t in tools]
        single = False
    else:  # --next
        if st['cursor'] >= len(tools):
            print('已全部测完。--status 看结果; --reset 重新开始。')
            return 0
        todo = [(tools[st['cursor']].get('name'), tools[st['cursor']])]
        single = True

    rnd = st.get('max_round', 0) + 1
    t0 = time.time()
    last_name = None
    for name, t in todo:
        schema = t.get('inputSchema') or {}
        desc = t.get('description') or ''
        if name in MP.LETHAL or name in MP.MUTATING_SKIP:
            rec = {'tool': name, 'status': 'skip', 'cls': 'SKIP', 'elapsed': 0, 'args': {},
                   'note': '致命/污染全局, 通用探针不测; 受控 verify 证据见 _tool_ledger.json',
                   'ts': time.strftime('%m-%d %H:%M'), 'round': rnd}
            print('   %-40s 跳过(致命/污染全局, 受控证据见台账)' % name)
        else:
            restart_after = None
            if not CM.alive(5):
                # 记录"重启前最后一个工具": 用于定位是哪个工具把渲染器占用到探针超时(用户看到的闪退)
                restart_after = last_name
                print('   (实例不活, 先冷重启; 上一个工具=%s)' % last_name)
                CM.cold_restart()
            rec = test_one(name, schema, desc, rnd)
            if restart_after:
                rec['restart_after'] = restart_after
                rec['note'] = ('[冷重启触发者=%s] ' % restart_after) + (rec.get('note') or '')
                rec['note'] = rec['note'][:300]
            print('   %-40s %-12s %5.2fs %s' % (name, rec['status'], rec['elapsed'],
                                                (rec.get('note') or '')[:70]))
            for ln in rec.get('log', []):
                print('       日志| ' + ln)
        st['results'][name] = rec
        last_name = name
        st['max_round'] = rnd
        st['cursor'] += 1
        save_state(st)
        append_md((rec['ts'], rnd, name, rec['status'], rec['elapsed'],
                   rec.get('kind', ''), (rec.get('note') or '').replace('|', '/')[:110]))
        rnd += 1
    print('== 本轮 %.1fs, 已测 %d 个 | 游标 %d/%d ==' %
          (time.time() - t0, len(todo), st['cursor'], len(tools)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
