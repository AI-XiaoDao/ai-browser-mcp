# -*- coding: utf-8 -*-
"""批量重测指定工具并汇总(替代在 PowerShell 里拼循环/正则 —— 那样写既易错又难读)。

用法: py -3 _audit/retest_batch.py 工具名 [工具名...]
      py -3 _audit/retest_batch.py --triage-a     # 跑失败分诊里那 30 个 A 类工具
"""
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, '_audit', 'tool_ledger.py')

# 失败分诊(_audit/_failure_triage.md)判为 A 类的 30 个
TRIAGE_A = [
    # A-1 selector=h1
    'browser_dom_query', 'browser_dom_rect', 'browser_dom_inner_html', 'browser_dom_click',
    'browser_fill_click', 'browser_fill_focus', 'browser_fill_scroll', 'browser_fill_trigger',
    # A-2 注入真实控件
    'browser_dom_checked', 'browser_dom_selected', 'browser_dom_set_value',
    'browser_fill_set_value', 'browser_fill_select',
    # A-3 真实属性
    'browser_fill_attr_get', 'browser_fill_attr_set',
    # A-4 语义必填
    'browser_wait', 'browser_intercept', 'browser_file_dialog', 'workflow_get',
    'browser_cdp_call', 'browser_kernel_auth', 'browser_kernel_scheme',
    'browser_kernel_reactor', 'browser_kernel_watch',
    'browser_vip_execute_js_context', 'browser_vip_dom_search',
    # A-5 先造状态
    'browser_cdp_event', 'browser_reverse_return_value', 'browser_reverse_set_variable',
    'browser_forward',
]


def run_one(tool):
    p = subprocess.run([sys.executable, LEDGER, '--tool', tool, '--retest'],
                       cwd=ROOT, capture_output=True)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    # 台账每行形如: "   browser_xxx   pass   0.02s  {...}"
    line = None
    for L in out.split('\n'):
        if L.strip().startswith(tool):
            line = L.strip()
            break
    if line is None:
        return tool, None, out.strip()[:200]
    m = re.search(r'\b(pass|fail|fail\(wedge\)|skip\S*)\b', line)
    verdict = m.group(1) if m else '?'
    return tool, verdict, line


def main(argv):
    tools = TRIAGE_A if (not argv or argv[0] == '--triage-a') else argv
    ok, bad, err = [], [], []
    for t in tools:
        tool, verdict, line = run_one(t)
        if verdict is None:
            err.append((tool, line))
            print("  [ ?? ] %-38s 无法解析: %s" % (tool, line[:110]))
        elif verdict == 'pass':
            ok.append(tool)
            print("  [PASS] %-38s %s" % (tool, line[len(tool):][:80].strip()))
        else:
            bad.append((tool, verdict, line))
            print("  [FAIL] %-38s %s" % (tool, line[len(tool):][:100].strip()))
    print("\n== 汇总: 通过 %d / %d ; 仍失败 %d ; 解析失败 %d =="
          % (len(ok), len(tools), len(bad), len(err)))
    if bad:
        print("\n--- 仍失败(原文) ---")
        for t, v, line in bad:
            print("  %-38s %-12s %s" % (t, v, line[len(t):][:150].strip()))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
