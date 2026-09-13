# -*- coding: utf-8 -*-
r"""第135轮: 按**本轮受控实测**订正两个"不可逆副作用"工具的文案（旧文案有一处已被推翻）。

实测（`_audit/probe_three_gates.py`，每项之间自动重启，干净实例）:
  ① `browser_vip_mouse_wheel {x,y,delta_y}` → 调用成功 0.02s, 且**页面真的滚动**(scrollY 0→120, 页面侧预言机)
     ⇒ 台账里那条 GUARD 失败是**探针没给滚动量**造成的假目标, 能力本身是好的。
  ② `browser_vip_enable_js_env {enable:true, confirm:true}` → 调用成功 0.02s; 之后 execute_js **30.07s**、
     dom_query 10.10s; 再调 `{enable:false}`(返回"已关闭") 之后**仍然** 30.32s ⇒ **回滚无效, 必须重启进程**。
  ③ `browser_reverse_instrument_script {action:install, confirm:true}` → 调用成功 6.49s(带 auto_prepared: Debugger.enable);
     之后 execute_js **60s 超时报错**、dom_query 30.63s 报错; `{action:suppress}` 返回
     **`setSkipAllPauses 失败: timeout`**(15.09s), 且之后 execute_js 仍 35.11s 报错 ⇒ **suppress 已不能恢复**。
     ⚠ 这与本项目旧文案"suppress 可以恢复(约 45s)"**相矛盾**, 按实测订正(旧的恢复结论不再成立)。

用法: py -3 _audit\_apply_round135b.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

INST_OLD = ('**恢复办法(三条逐一实测)**: `action=suppress` **可以**恢复(约 45s, 走项目既有的卡死自救: 超时->自动 resume->重试一次; '
            '客户端请留足 60s 超时), 而 browser_debugger_resume 与 browser_debugger_disable **都不能**恢复; 重启也可以但没必要。')
INST_NEW = ('**恢复办法(第135轮受控复核更正)**: 实测 `action=suppress` **已不能恢复**(返回 `setSkipAllPauses 失败: timeout`, '
            '之后 execute_js 仍 35 秒超时报错), `browser_debugger_resume` / `disable` 同样无效 ⇒ **安装后请准备重启 '
            'AI-Fbowser-Mcp.exe**。旧文案称"suppress 可恢复(约45s)"已被本轮实测推翻, 不要再依赖它。')

ENV_OLD = ('"VIP: 启用JS执行环境 | ⚠ 实测启用后会**破坏本会话的 CDP/JS 通道**(execute_js/dom_query 等退化为超时), '
           '需重启进程恢复 ⇒ 故必须显式传 confirm=true 才执行(见 schema 的 confirm 参数); '
           '不需要 VIP 环境的场景请直接用 browser_execute_js(走 CDP, 无副作用)"')
ENV_NEW = ('"VIP: 启用JS执行环境 | ⚠ **不可逆副作用(第135轮受控实测)**: 启用后本会话 CDP/JS 通道退化'
           '(execute_js 30.07s、dom_query 10.10s), 且 enable:false **不会恢复**(实测关闭后仍 30.32s) —— '
           '**必须重启 AI-Fbowser-Mcp.exe**; 故必须显式传 confirm=true 才执行(见 schema 的 confirm 参数); '
           '不需要 VIP 环境的场景请直接用 browser_execute_js(走 CDP, 无副作用)"')


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    out = txt
    for tag, old, new in (('instrument_script 恢复办法订正', INST_OLD, INST_NEW),
                          ('enable_js_env 描述补不可逆事实', ENV_OLD, ENV_NEW)):
        cnt = out.count(old)
        assert cnt == 1, '%s 锚点 %d 次' % (tag, cnt)
        out = out.replace(old, new, 1)
        print('   · %s' % tag)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert 'setSkipAllPauses 失败: timeout' in c and '不会被恢复' not in c
        assert 'enable:false' in c and '必须重启 AI-Fbowser-Mcp.exe' in c
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
