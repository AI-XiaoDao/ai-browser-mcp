# -*- coding: utf-8 -*-
"""系统性扫描: 还有多少"取数据"的 CDP 调用走了**异步**入口(结果被丢弃)?

背景: 已实证两处同类缺陷 ——
  · 逆向侧 7 处(第 97 轮修): Runtime.evaluate/getProperties/callFunctionOn/getResponseBody/
    globalLexicalScopeNames/stopSampling/getObjectByHeapObjectId 走 执行逆向CDP命令 -> 只回"CDP已提交"
  · browser_network_body(第 98 轮修): Network.getResponseBody 走 执行CDP命令_带参数 -> 只回"CDP已提交"
本脚本把**全部** 执行CDP命令 / 执行CDP命令_带参数 调用点列出来, 标出其中方法名属于"取数据"语义的,
即"调用方拿不到本该拿到的东西"的嫌疑点。

判定只用方法名语义(读操作前缀), 不做"它到底有没有返回数据"的断言 —— 后者要真机实测。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

# 数据返回型方法名特征(读操作 / 取快照 / 求值 / 查询)
DATA_PAT = re.compile(
    r'\.(get|take|query|read|collect|evaluate|callFunctionOn|compileScript|'
    r'getResponseBody|getProperties|getEventListeners|getPossibleBreakpoints|'
    r'getScriptSource|getBestEffortCoverage|getHeapObjectId|getObjectByHeapObjectId|'
    r'getTargets|getWindowForTarget|getVersion|getBrowserCommandLine|'
    r'captureScreenshot|snapshot|searchInContent|dom|resolveNode|describeNode)',
    re.I)
# 明显是"设置/触发"类, 返回空或无意义 -> 异步可接受
SET_PAT = re.compile(r'\.(enable|disable|set|add|remove|clear|reset|start|stop|override|'
                     r'emulate|delete|insert|insertText|dispatch|navigate|reload|'
                     r'continue|intercept|fulfill|block|fail|activate|attach|detach)',
                     re.I)

CALL_PAT = re.compile(r'(执行CDP命令_带参数|执行CDP命令|执行逆向CDP命令|执行V8CDP命令)\s*\(([^)]*?)"([A-Za-z]+\.[A-Za-z]+)"')

rows = []
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith('.wsv') or '~vbak' in fn:
        continue
    p = os.path.join(SRC, fn)
    lines = io.open(p, encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines, 1):
        for m in CALL_PAT.finditer(l):
            rows.append((fn, i, m.group(1), m.group(3), l.strip()[:110]))

print("== 异步/同步入口调用点总览 ==")
from collections import Counter
print("   共 %d 处" % len(rows))
for k, v in Counter(r[2] for r in rows).most_common():
    print("      %-22s %d" % (k, v))

ASYNC = ('执行CDP命令_带参数', '执行CDP命令', '执行逆向CDP命令')
sus = [r for r in rows if r[2] in ASYNC and DATA_PAT.search(r[3]) and not SET_PAT.match('.' + r[3].split('.', 1)[1])]
ok = [r for r in rows if r[2] == '执行V8CDP命令']

print("\n== 嫌疑点: 走异步入口 + 方法名属'取数据'语义 (%d 处) ==" % len(sus))
for fn, i, entry, meth, txt in sus:
    print("   %-24s:%-5d %-20s %-38s %s" % (fn, i, entry, meth, txt[:60]))

print("\n== 对照组: 已走同步入口 执行V8CDP命令 (%d 处) ==" % len(ok))
for fn, i, entry, meth, txt in ok:
    print("   %-24s:%-5d %-38s" % (fn, i, meth))

print("\n== 异步入口的全部调用点(供逐个判断) ==")
for fn, i, entry, meth, txt in rows:
    if entry in ASYNC:
        tag = 'DATA?' if DATA_PAT.search(meth) else ('set  ' if SET_PAT.match('.' + meth.split('.', 1)[1]) else '?????')
        print("   [%s] %-24s:%-5d %-20s %s" % (tag, fn, i, entry, meth))
