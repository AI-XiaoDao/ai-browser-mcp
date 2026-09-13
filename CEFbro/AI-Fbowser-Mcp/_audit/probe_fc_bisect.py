# -*- coding: utf-8 -*-
r"""二分定位: 快检前缀里哪一段让"之后第一次 mouse_move 变慢 ~5s"。

做法: 按快检的**小节边界**把 fastcheck.py 截断成临时脚本, 截断处追一段"立刻量两次 mouse_move";
每轮都自动重启实例(保证干净起点), 依次跑 k=9(整段前缀) → k=5 → k=3, 谁开始慢就往下二分。

用法: py -3 _audit\probe_fc_bisect.py [k1 k2 ...]    (默认 9 5 3)
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _console  # noqa: F401
import loop

FC = os.path.join(HERE, 'fastcheck.py')
TMP = os.path.join(HERE, '_fc_trunc.py')

PROBE = '''
    print("\\n[截断] 前缀结束 → 立刻量 mouse_move")
    for _i in (1, 2, 3):
        _t0 = time.time()
        call("browser_mouse_move", {"x": 300 + _i * 3, "y": 200 + _i * 3})
        print("   [截断] mouse_move #%d %.2fs" % (_i, time.time() - _t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def build(k):
    """截断到第 k 个小节之前(1-based: 1=读取工具 ... 9=抽样缺参守卫)。"""
    lines = io.open(FC, encoding='utf-8').read().split('\n')
    marks = [i for i, ln in enumerate(lines) if re.match(r'^    print\("\\n-- ', ln)]
    if k > len(marks):
        print('!! 小节数只有 %d' % len(marks))
        return False
    cut = marks[k - 1]
    head = lines[:cut]
    io.open(TMP, 'w', encoding='utf-8').write('\n'.join(head) + PROBE)
    print('   [截断] 保留前 %d 个小节, 截断行=%d, 生成 %s'
          % (k - 1, cut + 1, os.path.basename(TMP)))
    return True


def run_trunc(tag):
    print('   -- 重启实例 --')
    loop.kill_app()
    if not loop.start_app():
        print('   !! 启动失败')
        return None
    p = subprocess.run([sys.executable, TMP], cwd=HERE, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    times = []
    for ln in out.splitlines():
        if '[截断] mouse_move #' in ln:
            print('      ' + ln.strip())
            m = re.search(r'([\d.]+)s', ln)
            if m:
                times.append(float(m.group(1)))
    if not times:
        print('      !! 没拿到测量, 输出尾部:')
        print('\n'.join(out.splitlines()[-8:]))
    print('   => %s: mouse_move=%s' % (tag, [round(x, 2) for x in times]))
    return times


def main():
    ks = [int(x) for x in sys.argv[1:]] or [9, 5, 3]
    for k in ks:
        print('\n===== 截断点 k=%d (保留前 %d 个小节) =====' % (k, k - 1))
        if not build(k):
            continue
        t = run_trunc('k=%d' % k)
        if t and t[0] >= 3.0:
            print('   ** k=%d 已复现慢态(第一次 mouse_move %.2fs) **' % (k, t[0]))
        elif t:
            print('   k=%d 未复现(第一次 %.2fs)' % (k, t[0]))
    try:
        os.remove(TMP)
    except OSError:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
