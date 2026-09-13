# -*- coding: utf-8 -*-
r"""第124轮(其二): 让"CDP Input 派发失败"的报错说出**真实成因**, 并避免触摸族白等 8 秒。

本轮受控实测(_audit/probe_input_occlusion.py + probe_touch_hidden_cost.py):
  · 窗口可见:    mouse_move 0.04s / touchStart 0.03s / execute_js 0.03s
  · 隐藏窗口:    mouseMoved **5.09s 返回且成功**; touchStart **30s 不返回(直发三次全部超时)**;
                 Runtime.evaluate 0.03s、Emulation.setTouchEmulationEnabled 0.01s ⇒ **CDP 通道本身健康**
  · 恢复可见:    touchStart 立即 0.04s
⇒ 两个真实缺陷:
  ① 触摸族在"窗口不可见"时报的是"本会话 CDP 通道已不可用(常见诱因是 kernel:true)", **成因完全指错**,
     调用方会去换方法反复试错(正是本目标要消灭的体验);
  ② 它还要先白等 8 秒(派发预算)才失败 —— 而该状态在可见性恢复前**不可能成功**。
改动:
  1) MCP_Server.wsv 新增 CDPInput失败原因文本(动作名): 可见性不可见 ⇒ 给出实测事实与恢复手段; 否则保留原提示;
  2) CDP派发触摸事件 入口加"窗口不可见 ⇒ 立即返回假"(不再白等), 由调用方输出上述真实成因;
  3) Core 的 6 处鼠标/触摸派发失败文案改为调用该复用件(鼠标 3 处 + 触摸 3 处), 尾部替代方案原样保留。

用法: py -3 _audit\_apply_touch_hidden_cause.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

HELPER = '''    方法 CDPInput失败原因文本 <公开 静态 类型 = 文本型 注释 = "CDP Input 派发失败时的真实成因文案: 窗口不可见时给出实测事实与恢复手段, 否则保留通道/内核注入提示" @输出名 = "CDPInputFailureReasonText" @强制输出 = 真>
    参数 动作名 <类型 = 文本型 @输出名 = "ActionName">
    {
        如果 (浏览器窗口可见 () == 假)
        {
            返回 (动作名 + "失败: 浏览器窗口当前**不可见**(GWL_STYLE 的 WS_VISIBLE=0) —— 实测该状态下渲染器被后台化挂起: Input.dispatchMouseEvent 仍能返回(约5秒), 但 **Input.dispatchTouchEvent 根本不返回**(直发 CDP 连续三次均在 30 秒预算上超时), 而同一时刻 Runtime.evaluate 0.03 秒、Emulation.setTouchEmulationEnabled 0.01 秒 ⇒ 说明 CDP 通道本身是健康的 | 恢复: browser_show_window {visible:true} 后用同样参数重试即可成功(实测恢复后立即 0.03~0.04 秒)")
        }
        返回 (动作名 + "失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级注入 kernel:true 或关闭过 DevTools 观察者; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe)")
    }

'''

ANCHOR_HELPER = '    # ==== 用 CDP 派发鼠标事件(不破坏 CDP 通道) ===='

TOUCH_ANCHOR = '''        如果 (实际类型 != "touchStart" && 实际类型 != "touchMove" && 实际类型 != "touchEnd" && 实际类型 != "touchCancel")
        {
            返回 (假)
        }'''
TOUCH_ADD = TOUCH_ANCHOR + '''
        // 实测(受控 A/B, 见 _audit/probe_touch_hidden_cost.py): 窗口不可见时 Input.dispatchTouchEvent
        //   **永不返回** —— 直发 CDP 连续三次都在 30 秒预算上超时; 而同状态下鼠标 5.09 秒返回、
        //   Runtime 0.03 秒、Emulation.* 0.01 秒(通道健康)。既然该状态在窗口恢复可见前不可能成功,
        //   就**不要白等 8 秒再报一个指错成因的错**, 直接立即失败, 由调用方输出真实成因与恢复手段。
        如果 (浏览器窗口可见 () == 假)
        {
            返回 (假)
        }'''

MOUSE_OLD = '"CDP 派发鼠标事件失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级注入 kernel:true; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe) | 可用替代:'
MOUSE_NEW = 'MCP命令服务器.CDPInput失败原因文本 ("CDP 派发鼠标事件") + " | 可用替代:'
TOUCH_OLD = '"CDP 派发触摸失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级注入 kernel:true; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe) | 可用替代:'
TOUCH_NEW = 'MCP命令服务器.CDPInput失败原因文本 ("CDP 派发触摸") + " | 可用替代:'


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def main():
    raw = io.open(SERVER, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw, 'Server 应无 BOM 且为纯 LF'
    txt = raw.decode('utf-8')
    b0 = balance(txt)
    assert txt.count(ANCHOR_HELPER) == 1, '辅助锚点 %d' % txt.count(ANCHOR_HELPER)
    assert txt.count(TOUCH_ANCHOR) == 1, '触摸锚点 %d' % txt.count(TOUCH_ANCHOR)
    assert 'CDPInput失败原因文本' not in txt, '已改过'
    out = txt.replace(ANCHOR_HELPER, HELPER + ANCHOR_HELPER, 1)
    out = out.replace(TOUCH_ANCHOR, TOUCH_ADD, 1)
    assert balance(out) == b0, 'Server 括号净值变了: %s -> %s' % (b0, balance(out))
    assert 'CDPInput失败原因文本 ("CDP 派发触摸")' not in out  # 由 Core 调用

    craw = io.open(CORE, 'rb').read()
    crlf = b'\r' in craw
    ctxt = craw.decode('utf-8')
    c0 = balance(ctxt)
    assert ctxt.count(MOUSE_OLD) == 3, 'Core 鼠标文案 %d 处(应为3)' % ctxt.count(MOUSE_OLD)
    assert ctxt.count(TOUCH_OLD) == 3, 'Core 触摸文案 %d 处(应为3)' % ctxt.count(TOUCH_OLD)
    cout = ctxt.replace(MOUSE_OLD, MOUSE_NEW).replace(TOUCH_OLD, TOUCH_NEW)
    assert balance(cout) == c0, 'Core 括号净值变了: %s -> %s' % (c0, balance(cout))

    print('Server: 行数 %d -> %d; 括号净值 %s 不变'
          % (len(txt.split('\n')), len(out.split('\n')), b0))
    print('Core  : 行数 %d -> %d (行尾=%s); 括号净值 %s 不变'
          % (len(ctxt.split('\n')), len(cout.split('\n')), 'CRLF/CR' if crlf else 'LF', c0))
    print('       鼠标文案替换 3 处, 触摸文案替换 3 处')

    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        # Core 用字节写回, 原样保留其行尾风格
        io.open(CORE, 'wb').write(cout.encode('utf-8'))
        chk = io.open(SERVER, encoding='utf-8').read()
        assert '方法 CDPInput失败原因文本' in chk and '浏览器窗口可见 () == 假' in chk
        assert chk.count('如果 (浏览器窗口可见 () == 假)') == 2, \
            'Server 里可见性判断应恰有 2 处(慢因上报 + 触摸快速失败)'
        cchk = io.open(CORE, encoding='utf-8').read()
        assert cchk.count('CDPInput失败原因文本 ("CDP 派发鼠标事件")') == 3
        assert cchk.count('CDPInput失败原因文本 ("CDP 派发触摸")') == 3
        assert (b'\r' in io.open(CORE, 'rb').read()) == crlf
        print('已写入 Server + Core 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
