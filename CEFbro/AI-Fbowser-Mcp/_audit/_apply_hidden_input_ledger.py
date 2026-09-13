# -*- coding: utf-8 -*-
r"""第124轮: 给"窗口隐藏 ⇒ 输入族表现"相关的工具台账补实测注记(保留原 status/note)。

实测依据: _audit/probe_input_occlusion.py(A/B/A/B)、probe_hidden_input_semantics.py(页面侧预言机)、
probe_hidden_wheel_cost.py、以及验收脚本 _audit/verify_input_occlusion.py(25/25)。
关键事实: 可见态全部 0.03s; 隐藏态 mouseMoved 5.08s 但**成功且真实到达页面**, click 仍 0.05s 且
页面 click 计数+1, wheel/touch **永不返回**(直发 30s 超时) ⇒ 已为 wheel/touch 加入口快速失败。

用法: py -3 _audit\_apply_hidden_input_ledger.py [--apply]
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, '_audit', '_tool_ledger.json')

TAIL = (' | [第124轮实测] 窗口隐藏(WS_VISIBLE=0)时: {行为} —— 恢复 browser_show_window '
        '{{visible:true}} 后立即回到 0.03 秒级; 可见性由 GWL_STYLE 的 WS_VISIBLE 位判定, '
        '慢因/失败成因会经 auto_prepared 或报错如实给出。验收: _audit/verify_input_occlusion.py 25/25。')

NOTES = {
    "browser_mouse_move": TAIL.format(行为='mouseMoved **5.08 秒才返回但仍成功**, 且事件真实到达页面(页面 mousemove 计数 +1)'),
    "browser_mouse_click": TAIL.format(行为='点击**不受影响**: 0.03~0.05 秒且页面真实收到 (页面 click 计数 +1) —— 无需先显示窗口'),
    "browser_mouse_wheel": TAIL.format(行为='mouseWheel **永不返回**(直发 CDP 连续多次 30 秒超时, 页面 scrollY 不变) ⇒ 已加入口快速失败, 不再白等 8 秒后误报通道不可用'),
    "browser_touch_press": TAIL.format(行为='Input.dispatchTouchEvent **永不返回**(直发三次 30 秒超时) ⇒ 已加入口快速失败并说明真实成因'),
    "browser_touch_release": TAIL.format(行为='同 touch_press: 隐藏态派发永不返回 ⇒ 入口快速失败并说明真实成因'),
    "browser_touch_move": TAIL.format(行为='同 touch_press: 隐藏态派发永不返回 ⇒ 入口快速失败并说明真实成因'),
    "browser_reverse_input_cdp": TAIL.format(行为='鼠标移动 5.08 秒(仍成功)、点击不受影响; kind=wheel/touch 永不返回(入口快速失败)'),
    "browser_show_window": TAIL.format(行为='隐藏窗口会让 mouseMoved 变慢至约 5 秒、滚轮与触摸不可用(另见各工具注记); 点击与 Runtime/Emulation 仍是 0.03 秒级 ⇒ 通道健康'),
}


def main():
    raw = io.open(LEDGER, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf')
    d = json.loads(raw.decode('utf-8'))
    touched, missing = 0, []
    for k, tail in NOTES.items():
        if k not in d:
            missing.append(k)
            continue
        if tail not in str(d[k].get('note', '')):
            d[k]['note'] = str(d[k].get('note', '')) + tail
            touched += 1
    print('台账条目 %d; 本次补注记 %d 条; 缺失工具 %s' % (len(d), touched, missing or '无'))
    if '--apply' in sys.argv:
        with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=2))
        chk = json.loads(io.open(LEDGER, encoding='utf-8').read())
        assert all(NOTES[k] in str(chk[k]['note']) for k in NOTES if k in chk)
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
