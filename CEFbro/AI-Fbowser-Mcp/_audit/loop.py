# -*- coding: utf-8 -*-
"""一条命令跑完"改动 -> 编译 -> 重启 -> 验证"。

用法:
  py -3 loop.py            # 默认: 源码变了才编译 + 快检(约 40 秒)
  py -3 loop.py --nobuild  # 完全不编译, 只重启+快检
  py -3 loop.py --full     # 编译(如需) + 全量六组套件(里程碑用, 十几分钟)
  py -3 loop.py --buildonly
  py -3 loop.py --checkonly

为什么要有它: 之前每轮都手动"编译 → 重启 → 跑全部套件", 一轮十几分钟,
时间都花在验证而不是修问题上。现在:
  · 源码未变 -> 跳过编译(省 30–50 秒);
  · 日常用快检(40 秒内);
  · 全量套件只在里程碑跑。
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
import _app_launch  # 调试期: 可见控制台窗口 + 应用自写 mcp_console.log

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'src')
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
VSLN = 'AI-Fbowser-Mcp.vsln'
COMPILER = r'E:\HSPC\bin\x64\voldev_awp.exe'   # 必须 awp(加密狗=视窗+安卓个人)
STAMP = os.path.join(HERE, '_last_build.json')
BASE = 'http://127.0.0.1:9222'

FULL_SUITES = ['verify_round4.py', 'probe_native_reads.py', 'probe_writes.py',
               'probe_coercion.py', 'verify_scrape_fix.py',
               'probe_destructive_default.py']


def src_hash():
    h = hashlib.sha256()
    for n in sorted(os.listdir(SRC)):
        if n.endswith('.wsv') and '~vbak' not in n:
            with io.open(os.path.join(SRC, n), 'rb') as f:
                h.update(n.encode('utf-8'))
                h.update(f.read())
    return h.hexdigest()[:16]


def kill_app():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)


def build(force=False):
    cur = src_hash()
    prev = None
    if os.path.exists(STAMP):
        try:
            prev = json.load(io.open(STAMP, encoding='utf-8')).get('hash')
        except Exception:
            prev = None
    if not force and prev == cur and os.path.exists(EXE):
        print('  [编译] 源码未变(哈希 %s), 跳过' % cur)
        return True
    kill_app()
    print('  [编译] 源码哈希 %s -> 开始 (voldev_awp.exe /d)' % cur)
    t0 = time.time()
    p = subprocess.run([COMPILER, '@compile', VSLN, '/d'], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    warn = [ln for ln in out.splitlines() if ('警告' in ln or '错误' in ln)]
    print('  [编译] 退出码=%s 用时=%.1fs' % (p.returncode, time.time() - t0))
    for ln in warn:
        print('         ' + ln.strip()[:150])
    if p.returncode != 0:
        print('  [编译] !! 失败, 完整输出:')
        print('\n'.join(out.splitlines()[-25:]))
        return False
    json.dump({'hash': cur, 'time': time.strftime('%H:%M:%S')},
              io.open(STAMP, 'w', encoding='utf-8'))
    return True


def start_app():
    kill_app()
    _app_launch.launch_visible()
    for _ in range(60):
        time.sleep(1)
        try:
            h = json.loads(urllib.request.urlopen(BASE + '/health', timeout=3).read())
            print('  [启动] 就绪 tools=%s cdp=%s' % (h.get('tool_count'), h.get('cdp_ready')))
            # 稳定期: 实测"紧接着重启就跑快检"会让首个重 CDP 用例偶发超时(browser_highlight clear 5s);
            # 而对已运行一段时间的实例连跑 6 次则 41/41 稳定(4.2~4.3s)。
            # 两次"用探针预热"的实现均失败(请求本身返回错误, 21 次尝试全未成功), 故改用最朴素、
            # 可验证的手段: 给出足够长的稳定期。若日后仍偶发, 应改去排查 highlight clear 本身。
            time.sleep(8)
            return True
        except Exception:
            pass
    print('  [启动] !! 未就绪')
    return False


def run(script):
    t0 = time.time()
    p = subprocess.run([sys.executable, script], cwd=HERE,
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    line = ''
    for ln in out.splitlines():
        s = ln.strip()
        # 兼容两种汇总格式: "通过 14 / 14"(六组套件) 与 "结果: 23/23 通过"(fastcheck)
        if ('通过 ' in s and ' / ' in s) or ('通过' in s and '/' in s):
            line = s
    print('  %-30s %-30s %5.1fs' % (script, line, time.time() - t0))
    if p.returncode != 0:
        for ln in out.splitlines():
            if '未通过' in ln:
                print('        ' + ln.strip()[:140])
    return p.returncode == 0


def syntax_check():
    """仅生成C++自检(/c): 约6秒, 不链接 → 不需要先关程序, 适合"改完立刻验语法"的快循环。"""
    print('  [语法] voldev_awp.exe /c (不链接)')
    t0 = time.time()
    p = subprocess.run([COMPILER, '@compile', VSLN, '/c'], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    bad = [ln for ln in out.splitlines() if ('警告' in ln or '错误' in ln)]
    print('  [语法] 退出码=%s 用时=%.1fs 诊断行=%d' % (p.returncode, time.time() - t0,
                                                    len(bad)))
    for ln in bad[:30]:
        print('         ' + ln.strip()[:180])
    if p.returncode != 0:
        print('  [语法] !! 失败, 完整输出尾部:')
        print('\n'.join(out.splitlines()[-30:]))
        return False
    return True


def main():
    full = '--full' in sys.argv
    nobuild = '--nobuild' in sys.argv
    buildonly = '--buildonly' in sys.argv
    checkonly = '--checkonly' in sys.argv
    syntax = '--syntax' in sys.argv

    print('== loop %s ==' % time.strftime('%H:%M:%S'))
    if syntax:
        ok = syntax_check()
        print('== loop 结束: %s ==' % ('语法通过' if ok else '语法有错'))
        return 0 if ok else 1
    if not checkonly:
        if not build(force=False) and not nobuild:
            return 1
    if buildonly:
        return 0
    if not start_app():
        return 1
    scripts = FULL_SUITES if full else ['fastcheck.py']
    print('  -- %s --' % ('全量套件' if full else '快检'))
    allok = True
    for s in scripts:
        allok = run(s) and allok
    print('== loop 结束: %s ==' % ('全部通过' if allok else '有失败项'))
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
