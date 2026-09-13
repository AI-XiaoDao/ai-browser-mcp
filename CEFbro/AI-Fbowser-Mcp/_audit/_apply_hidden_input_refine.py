# -*- coding: utf-8 -*-
r"""第124轮(其三): 按**更细的实测**校正文案, 并给"隐藏态永不返回"的滚轮加上与触摸同款的快速失败。

本轮新增实测(_audit/probe_hidden_input_semantics.py 用页面侧计数器当预言机, probe_hidden_wheel_cost.py):
  可见(WS_VISIBLE=1): mouseMoved 0.03s / mousePressed·Released 0.03s / mouseWheel 0.03s / touch 0.03s
  隐藏(WS_VISIBLE=0): mouseMoved **5.08s 且成功, 页面计数器+1**(事件真实到达)
                      mousePressed·Released **0.03s 且成功, 页面 click 计数+1**(点击在隐藏态**照样可用**)
                      mouseWheel **30s 不返回**(直发三次全超时, 页面 scrollY 不动)
                      Input.dispatchTouchEvent **30s 不返回**
                      Runtime.evaluate 0.03s / Emulation.setTouchEmulationEnabled 0.01s ⇒ 通道健康
  恢复可见: 全部立即回到 0.03s(scrollY 也真的变了)
⇒ 三处校正:
  ① 慢因文案原写"每条 CDP Input 命令都固定约5秒" —— **不准**: 按下/抬起不受影响, 滚轮/触摸是"不返回";
  ② 失败文案需按三类事件分别给事实(并保留"通道本身健康"这一关键结论);
  ③ 滚轮与触摸同属"隐藏态永不返回", 但滚轮当时还要白等 8 秒 —— 补上与触摸同样的入口快速失败;
  ④ 各工具描述按各自实测事实分别措辞(点击那条尤其要写清"隐藏态照样可用", 否则调用方会先去显示窗口, 白做一步)。

用法: py -3 _audit\_apply_hidden_input_refine.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

# ── ① 滚轮快速失败守卫 ──
WHEEL_ANCHOR = '''        变量 派发起始毫秒 <类型 = 长整数>
        派发起始毫秒 = 取启动时间 ()
        变量 参 <类型 = YYJSON对象类>'''
WHEEL_ADD = '''        变量 派发起始毫秒 <类型 = 长整数>
        派发起始毫秒 = 取启动时间 ()
        // 实测(_audit/probe_hidden_wheel_cost.py): 窗口不可见时 mouseWheel **永不返回** ——
        //   直发 CDP 连续三次都在 30 秒预算上超时, 页面 scrollY 毫无变化; 而同一状态下
        //   mouseMoved 5.08 秒即返回、按下/抬起 0.03 秒、Runtime/Emulation 0.01~0.03 秒 ⇒ 通道健康。
        //   (触摸 与 滚轮 同属"永不返回", 触摸已加同款守卫, 此处补齐。)
        //   既然该状态在窗口恢复可见前不可能成功, 就立即失败, 由调用方给出真实成因与恢复手段。
        如果 (事件类型 == "mouseWheel" && 浏览器窗口可见 () == 假)
        {
            返回 (假)
        }
        变量 参 <类型 = YYJSON对象类>'''

# ── ② 慢因文案(隐藏分支)校正 ──
NOTE_OLD = '            MCP_响应构建.记录自动处理 (输入类别 + "本次派发耗时" + 耗时档 + ": 浏览器窗口当前**不可见**(GWL_STYLE 的 WS_VISIBLE=0) ⇒ 渲染器被后台化节流, 实测该状态下**每条** CDP Input 命令都固定约5秒(工具仍然成功, 不是通道损坏) | 立即恢复手段: browser_show_window {visible:true}, 之后回到 30ms 级")'
NOTE_NEW = '            MCP_响应构建.记录自动处理 (输入类别 + "本次派发耗时" + 耗时档 + ": 浏览器窗口当前**不可见**(WS_VISIBLE=0) ⇒ 渲染器被后台化节流。实测该状态下: mouseMoved 约5秒但**成功**(事件仍真实到达页面), 点击(按下/抬起)**不受影响**(0.03秒级且页面真实收到), 而滚轮与触摸**完全不返回**(工具会立即失败并提示成因) | 立即恢复手段: browser_show_window {visible:true}, 之后回到 30ms 级")'

# ── ③ 失败成因文案(隐藏分支)按三类事件校正 ──
CAUSE_OLD = '            返回 (动作名 + "失败: 浏览器窗口当前**不可见**(GWL_STYLE 的 WS_VISIBLE=0) —— 实测该状态下渲染器被后台化挂起: Input.dispatchMouseEvent 仍能返回(约5秒), 但 **Input.dispatchTouchEvent 根本不返回**(直发 CDP 连续三次均在 30 秒预算上超时), 而同一时刻 Runtime.evaluate 0.03 秒、Emulation.setTouchEmulationEnabled 0.01 秒 ⇒ 说明 CDP 通道本身是健康的 | 恢复: browser_show_window {visible:true} 后用同样参数重试即可成功(实测恢复后立即 0.03~0.04 秒)")'
CAUSE_NEW = '            返回 (动作名 + "失败: 浏览器窗口当前**不可见**(WS_VISIBLE=0) —— 实测隐藏态下渲染器被后台化挂起, 不同事件类型表现不同: ① mouseMoved 约5秒但**成功**(事件真实到达页面) ② 点击(mousePressed/Released)**不受影响**(0.03秒级且页面真实收到) ③ **滚轮与触摸永不返回**(直发 CDP 连续多次都在 30 秒预算上超时, 页面毫无反应, 本项目对该两类做入口快速失败) | 同一时刻 Runtime.evaluate 0.03 秒、Emulation.setTouchEmulationEnabled 0.01 秒 ⇒ **CDP 通道本身是健康的**, 这不是 kernel:true 那种损伤 | 恢复: browser_show_window {visible:true} 后用同样参数重试(实测恢复后立即 0.03 秒)")'

# ── ④ 工具描述按各自实测分别措辞 ──
MOVE_OLD = (' | 实测: 窗口不可见(或被完全遮挡)时渲染器被节流, 每条 CDP Input 命令约5秒才返回'
            '(工具仍成功), 恢复可见立即回到30ms级; 慢时成因与恢复手段经 auto_prepared 上报')
MOVE_NEW = (' | 实测: 窗口不可见(或被完全遮挡)时该派发约5秒才返回(**仍成功**, 事件真实到达页面), '
            '恢复 browser_show_window {visible:true} 立即回到30ms级; 慢时成因经 auto_prepared 上报')
CLICK_NEW = (' | 实测: 即使窗口不可见, 点击**仍然即时可用**(按下/抬起 0.03秒级且事件真实到达页面, '
             '已用页面侧 click 计数器验证) —— 无需先显示窗口')
WHEEL_NEW = (' | 实测: 窗口不可见时滚轮**立即失败并说明成因**(隐藏态直发 Input.dispatchMouseEvent(mouseWheel) '
             '连续三次 30 秒都不返回, 页面 scrollY 不动); 恢复 browser_show_window {visible:true} 后 0.03 秒成功')
TOUCH_NEW = (' | 实测: 窗口不可见时**立即失败并说明成因**(隐藏态直发 Input.dispatchTouchEvent 连续三次 30 秒都不返回, '
             '而 Runtime/Emulation 仍 0.01~0.03 秒 ⇒ 通道健康); 恢复 browser_show_window {visible:true} 后 0.03 秒成功')
SHORT_OLD = (' | 实测: 窗口不可见/被其它窗口完全遮挡时渲染器被节流, 每条 CDP Input 命令约5秒才返回'
             '(工具仍成功), 恢复可见立即回到30ms级; 慢时成因与恢复手段经 auto_prepared 上报')
REVERSE_NEW = (' | 实测: 窗口不可见时 mouseMoved 约5秒(**仍成功**)、点击不受影响、滚轮与触摸则**立即失败并说明成因**'
               '(成因经 auto_prepared/报错如实给出)')
SHOW_OLD = (' | 实测副作用(重要): 窗口不可见时渲染器被后台化节流, CDP Input 族(鼠标/触摸/键盘直发)'
            '**每条**命令固定约5秒 —— 工具仍成功但明显变慢, 恢复 visible:true 后立即回到30ms级')
SHOW_NEW = (' | 实测副作用(重要): 窗口不可见时渲染器被后台化节流 —— mouseMoved 约5秒(**仍成功**), '
            '滚轮与触摸**永不返回**(这两个工具会立即失败并提示成因), 而点击与 Runtime/Emulation 仍是 0.03 秒级'
            '(通道健康); 恢复 visible:true 后全部立即复原')

DESC_PLAN = [
    ("browser_mouse_move", '", 多属性Schema文本', MOVE_OLD, MOVE_NEW),
    ("browser_mouse_click", '", 多属性Schema文本', MOVE_OLD, CLICK_NEW),
    ("browser_mouse_wheel", '", 多属性Schema文本', SHORT_OLD, WHEEL_NEW),
    ("browser_show_window", '", 多属性Schema文本', SHOW_OLD, SHOW_NEW),
    ("browser_touch_press", '", 双XY_Schema文本', SHORT_OLD, TOUCH_NEW),
    ("browser_touch_release", '", 双XY_Schema文本', SHORT_OLD, TOUCH_NEW),
    ("browser_touch_move", '", 双XY_Schema文本', SHORT_OLD, TOUCH_NEW),
    ("browser_reverse_input_cdp", '", 多属性Schema文本', SHORT_OLD, REVERSE_NEW),
]


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
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw, 'Server 应无 BOM 且纯 LF'
    txt = raw.decode('utf-8')
    assert 'mouseWheel 快速守卫' not in txt, '已改过'
    b0 = balance(txt)

    assert txt.count(WHEEL_ANCHOR) == 1, '滚轮锚点 %d' % txt.count(WHEEL_ANCHOR)
    out = txt.replace(WHEEL_ANCHOR, WHEEL_ADD, 1)
    for old, new, tag in ((NOTE_OLD, NOTE_NEW, '慢因文案'),
                          (CAUSE_OLD, CAUSE_NEW, '失败成因文案')):
        assert out.count(old) == 1, '%s 锚点 %d' % (tag, out.count(old))
        out = out.replace(old, new, 1)

    lines = out.split('\n')
    for tool, marker, old, new in DESC_PLAN:
        head = '        添加工具JSON ("%s", ' % tool
        idx = [i for i, ln in enumerate(lines) if ln.startswith(head)]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        if new in lines[i]:
            print('   (跳过 %s: 已是新版文案)' % tool)
            continue
        assert lines[i].count(old) == 1, '%s 旧文案数=%d' % (tool, lines[i].count(old))
        lines[i] = lines[i].replace(old, new, 1)
    out = '\n'.join(lines)

    b1 = balance(out)
    assert b0 == b1, '括号净值变了 %s -> %s' % (b0, b1)
    print('MCP_Server.wsv: 行数 %d -> %d; 括号净值 %s 不变'
          % (len(txt.split('\n')), len(lines), b1))

    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        chk = io.open(SERVER, encoding='utf-8').read()
        assert '事件类型 == "mouseWheel" && 浏览器窗口可见 () == 假' in chk
        assert 'mouseMoved 约5秒但**成功**' in chk
        assert '点击(mousePressed/Released)**不受影响**' in chk
        assert '\r' not in chk
        for tool, _m, _o, new in DESC_PLAN:
            assert new in chk, '%s 新文案未写入' % tool
        print('已写入并回读校验通过(滚轮守卫 + 2 处文案 + %d 个工具描述)' % len(DESC_PLAN))
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
