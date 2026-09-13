# -*- coding: utf-8 -*-
r"""按**本轮实测**给台账补两条: ①内核级注入族加入 SKIP_MUTATING(保护后续判定) ②保留它们"单次调用可成功"的历史证据。

实测数据(_audit/probe_kernel_mouse_cdp_impact.py, 干净实例上两次复现):
  注入前: execute_js 0.03s / dom_query(CDP) 0.03s / cdp_call 0.03s
  调 browser_vip_mouse_click 之后: execute_js **30.09s** / dom_query 10.12s / cdp_call **30.02s 报错**
  +3 秒复测: execute_js **35.15s 报错** / cdp_call 30.01s 报错  ⇒ 不是"延迟失效", 是**本会话内持续失效**, 重启才恢复。
=> 这类工具在**台账连测**里必须跳过: 它们的"pass"只代表自己那一次调用成功, 却会把**其后所有** CDP 优先工具的判定一起带坏
   (这正是"一次探测毁掉整轮"的成因)。历史 pass 条目**保留**(它证明工具本身可用), 但补上警示注记。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, '_audit', '_tool_ledger.json')

FAMILY = ["browser_vip_mouse_click", "browser_vip_mouse_press", "browser_vip_mouse_release",
          "browser_vip_mouse_move", "browser_vip_mouse_wheel",
          "browser_vip_touch_press", "browser_vip_touch_release", "browser_vip_touch_move",
          "browser_vip_touch_cancel",
          "browser_vip_key_click", "browser_vip_key_press", "browser_vip_key_release",
          "browser_vip_key_input", "browser_vip_key_type"]

WARN = (' | [第123轮实测] 内核级注入族: 单独调用可成功(本条目即证据), 但会让**本会话 CDP 通道失效**'
        '(实测 execute_js 0.03s→30s、cdp_call 报错、+3s 仍失效, 需重启恢复) '
        '=> 已加入台账 SKIP_MUTATING, 不再参与连测(否则一次探测会带坏其后全部判定); '
        '需要复验本族时请单开一轮并在其后立即重启。')


def main():
    # 1) mass_probe: 加入 SKIP_MUTATING
    mp = os.path.join(ROOT, '_audit', 'mass_probe.py')
    txt = open(mp, 'rb').read().decode('utf-8')
    assert 'browser_vip_mouse_click' not in txt, 'mass_probe 已改过'
    anchor = '''    "browser_reverse_patch",
}'''
    add = '''    "browser_reverse_patch",
    # ★ 第 123 轮**实测**新增: 内核级输入注入族(鼠标/触摸/键盘)。
    # 实测(干净实例, 两次复现): 注入前 execute_js 0.03s / cdp_call 0.03s;
    #   调 browser_vip_mouse_click 之后 execute_js 30.09s、cdp_call 30.02s 报错, +3 秒复测仍 35.15s 报错
    #   —— 不是"延迟失效", 而是**本会话内持续失效**, 只有重启进程能恢复。
    # 故这一族在连测里必须跳过: 它们自己那一次会 pass, 却把**其后所有** CDP 优先工具一起带坏。
    # (项目对 browser_vip_key_input 的工具文案也早已自述同一效果。) 需要复验请单开一轮并在其后立刻重启。
    "browser_vip_mouse_click", "browser_vip_mouse_press", "browser_vip_mouse_release",
    "browser_vip_mouse_move", "browser_vip_mouse_wheel",
    "browser_vip_touch_press", "browser_vip_touch_release", "browser_vip_touch_move",
    "browser_vip_touch_cancel",
    "browser_vip_key_click", "browser_vip_key_press", "browser_vip_key_release",
    "browser_vip_key_input", "browser_vip_key_type",
}'''
    assert txt.count(anchor) == 1, 'mass_probe 锚点 %d' % txt.count(anchor)
    out_mp = txt.replace(anchor, add)

    # 2) 台账: 给这一族的历史条目补警示注记(保留原 status/note)
    raw = open(LEDGER, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf')
    d = json.loads(raw.decode('utf-8'))
    touched = 0
    for k in FAMILY:
        if k in d and WARN not in str(d[k].get('note', '')):
            d[k]['note'] = str(d[k].get('note', '')) + WARN
            touched += 1
    print('mass_probe: SKIP_MUTATING += %d 个工具; 台账补注记 %d 条' % (len(FAMILY), touched))
    if '--apply' in sys.argv:
        with io.open(mp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out_mp)
        with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=2))
        print('已写入 mass_probe.py 与 _tool_ledger.json')
    else:
        print('[dry-run] 未落盘')


main()
