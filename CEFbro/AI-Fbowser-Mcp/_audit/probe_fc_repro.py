# -*- coding: utf-8 -*-
r"""复现性对照: 「真·快检」与「截断前缀(同一前缀)」交替各跑两次, 并把被测进程的 stderr 落盘。

回答的问题: 既然截断前缀与真·快检在鼠标调用之前执行的代码**完全相同**, 为什么真·快检里
mouse_move ~5.1s、截断里 0.02s? 两种脚本交替跑两次可排除偶发, 并通过应用侧日志看出
慢的那几秒里应用在做什么。

用法: py -3 _audit\probe_fc_repro.py
"""
import io
import os
import re
import subprocess
import sys
import time
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401
import loop

EXE = loop.EXE
LOGF = os.path.join(HERE, '_fc_app_log.txt')
TRUNC = os.path.join(HERE, '_fc_trunc.py')

PROBE = '''
    print("\\n[截断] 前缀结束 → 立刻量 mouse_move")
    for _i in (1, 2, 3):
        _t0 = time.time()
        _e, _t = call("browser_mouse_move", {"x": 300 + _i * 3, "y": 200 + _i * 3})
        print("   [截断] mouse_move #%d %.2fs" % (_i, time.time() - _t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def start_with_log():
    loop.kill_app()
    log = io.open(LOGF, 'wb')
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE), stdout=log, stderr=log)
    for _ in range(60):
        time.sleep(1)
        try:
            h = json.loads(urllib.request.urlopen(loop.BASE + '/health', timeout=3).read())
            print('   [启动] tools=%s' % h.get('tool_count'))
            time.sleep(8)
            return True
        except Exception:
            pass
    return False


def build_trunc9():
    lines = io.open(os.path.join(HERE, 'fastcheck.py'), encoding='utf-8').read().split('\n')
    marks = [i for i, ln in enumerate(lines) if re.match(r'^    print\("\\n-- ', ln)]
    io.open(TRUNC, 'w', encoding='utf-8').write(
        '\n'.join(lines[:marks[8]]) + PROBE)


def run_script(path):
    t0 = time.time()
    p = subprocess.run([sys.executable, path], cwd=HERE, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    total = time.time() - t0
    got = []
    for ln in out.splitlines():
        if 'mouse_move #' in ln:
            m = re.search(r'([\d.]+)s', ln)
            print('      ' + ln.strip())
            if m:
                got.append(float(m.group(1)))
        if 'mouse_move 后 CDP 仍可用' in ln:
            print('      ' + ln.strip()[:130])
        if '结果:' in ln and '通过' in ln:
            print('      ' + ln.strip())
    return got, total, out


def applog_summary():
    try:
        raw = io.open(LOGF, 'rb').read().decode('gbk', 'replace')
    except Exception as ex:
        return '  (读日志失败 %r)' % ex
    lines = [l for l in raw.splitlines() if l.strip()]
    print('   应用日志行数=%d, 尾部 12 行:' % len(lines))
    for l in lines[-12:]:
        print('      ' + l.strip()[:140])
    return ''


def main():
    build_trunc9()
    print('   [构建] 截断脚本(保留前 8 小节)=%s' % os.path.basename(TRUNC))
    for i in (1, 2):
        for tag, path in (('真·快检', os.path.join(HERE, 'fastcheck.py')),
                          ('截断前缀', TRUNC)):
            print('\n=== 第%d轮 / %s ===' % (i, tag))
            if not start_with_log():
                print('   !! 启动失败')
                return 1
            got, total, _ = run_script(path)
            print('   => %s: mouse=%s 脚本总用时=%.1fs'
                  % (tag, [round(x, 2) for x in got], total))
            applog_summary()
    try:
        os.remove(TRUNC)
    except OSError:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
