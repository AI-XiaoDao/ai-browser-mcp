# -*- coding: utf-8 -*-
r"""第135轮(其二): 让台账里那 3 条"刻意设计失败"如实反映**本轮受控实测**的结果。

实测结论(`_audit/probe_three_gates.py`, 每项之间自动重启):
  ① `browser_vip_mouse_wheel {x,y,delta_y}` → **成功 0.02s, 且页面真的滚动**(scrollY 0→120, 页面侧预言机)
     ⇒ 旧台账那条 GUARD 失败是**探针没给滚动量**造成的假目标;
  ② `browser_vip_enable_js_env {enable:true,confirm:true}` → **成功 0.02s**; 副作用不可逆(见描述);
  ③ `browser_reverse_instrument_script {action:install,confirm:true}` → **成功 6.49s**; 副作用不可逆(见描述)。
本脚本做两件事:
  · 给两个"确认闸门"补 `DYNAMIC_ARGS`(探针也按 schema 传 confirm:true) —— 否则台账永远记"未传参被拒"这种假失败;
  · 给三个工具写**人工受控**台账条目(status=pass, 附实测证据与"用后需重启"的硬约束),
    与既有 `browser_close_try` / `browser_debugger_pause` 同一做法。

用法: py -3 _audit\_apply_round135_ledger.py [--apply]
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP = os.path.join(ROOT, '_audit', 'mass_probe.py')
LEDGER = os.path.join(ROOT, '_audit', '_tool_ledger.json')

MP_OLD = '''    # 第135轮: 内核级滚轮**必须给滚动量**(缺它会被守卫拒绝'''
MP_NEW = '''    # 第135轮: 两个"确认闸门"也必须按 schema 传 confirm=true —— 不传会被**刻意**拒绝,
    # 台账若照旧只传默认参数, 就会永远记一条"未传 confirm"的假失败(与"探针假目标"同类)。
    # 注意: 这两条都有**不可逆副作用**(会打死本会话 JS 通道), 故**测完必须重启实例**。
    "browser_vip_enable_js_env": lambda _c: {"enable": True, "confirm": True},
    "browser_reverse_instrument_script": lambda _c: {"action": "install", "confirm": True},
    # 第135轮: 内核级滚轮**必须给滚动量**(缺它会被守卫拒绝'''

NOTES = {
    "browser_vip_mouse_wheel":
        " | [第135轮受控实测] 按 schema 传 delta_y 后**调用成功(0.02s)且页面真的滚动**"
        "(干净实例上注入 3000px 高内容, 页面侧预言机 scrollY 0→120) —— 旧条目记的 GUARD 失败是"
        "**探针没给滚动量**的假目标。硬约束(同族实测): 内核级注入会让本会话 CDP 通道退化(execute_js 30s), "
        "**测完需重启**; 需要不破坏 CDP 的滚动请用 browser_mouse_wheel(CDP 版)。",
    "browser_vip_enable_js_env":
        " | [第135轮受控实测] 显式传 confirm=true 后**调用成功(0.02s)**; 之后 execute_js 30.07s、dom_query 10.10s, "
        "且 enable:false **不恢复**(关闭后仍 30.32s) ⇒ **不可逆, 必须重启进程**。"
        "旧条目记的 OTHER 失败是**探针没传 confirm**的假失败(工具本身按 schema 调用可成功)。",
    "browser_reverse_instrument_script":
        " | [第135轮受控实测] 显式传 confirm=true 后 **install 成功(6.49s, 带 auto_prepared: Debugger.enable)**; "
        "之后 execute_js 60s 超时报错、dom_query 30.63s 报错; `action=suppress` 返回 `setSkipAllPauses 失败: timeout`, "
        "且之后仍 35.11s 报错 ⇒ **suppress 已不能恢复, 必须重启** (旧文案称 suppress 可恢复约45s, 已被本轮推翻, "
        "工具描述已同步订正)。旧条目记的 OTHER 失败是**探针没传 confirm**的假失败。",
}


def main():
    mp = io.open(MP, encoding='utf-8').read()
    if 'browser_vip_enable_js_env' in mp:
        print('mass_probe: 已有闸门 DYNAMIC_ARGS(幂等)')
    else:
        assert mp.count(MP_OLD) == 1, 'mass_probe 锚点 %d' % mp.count(MP_OLD)
        mp_out = mp.replace(MP_OLD, MP_NEW, 1)
        print('mass_probe: 已为两个确认闸门补 DYNAMIC_ARGS')
    d = json.loads(io.open(LEDGER, encoding='utf-8').read())
    touched = 0
    for k, note in NOTES.items():
        cur = d[k].get('note', '') if k in d else ''
        if '[第135轮受控实测]' in str(cur):
            continue
        d.setdefault(k, {})['tool'] = k
        d[k]['cls'] = 'OK_MANUAL'
        d[k]['status'] = 'pass'
        d[k]['manual'] = True
        d[k]['args'] = {}
        d[k]['elapsed'] = 0.0
        d[k]['ts'] = '13:35 13:35'
        d[k]['round'] = 135
        d[k]['note'] = '[人工受控实测·非探针]' + str(note)
        touched += 1
    print('台账: 更新 %d 条(其余已是最新)' % touched)
    if '--apply' in sys.argv:
        if 'browser_vip_enable_js_env' not in io.open(MP, encoding='utf-8').read():
            io.open(MP, 'w', encoding='utf-8', newline='\n').write(mp_out)
        with io.open(LEDGER, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=2))
        print('已写入 mass_probe.py + _tool_ledger.json')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
