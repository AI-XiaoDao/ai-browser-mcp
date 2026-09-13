# -*- coding: utf-8 -*-
r"""第124轮: 把"CDP Input 族慢 5 秒"的**实测归因**做进产品代码(复用既有 auto_prepared 机制)。

本轮受控实验结论(_audit/probe_input_visibility.py, A/B/A/B 可复现):
  · 窗口可见:      browser_mouse_move 0.02 / 0.01s, Runtime.evaluate 0.03s
  · 隐藏窗口后:    browser_mouse_move **5.12 / 5.11s**, Runtime.evaluate 仍 0.03s
  · 显示回来:      立即 0.03 / 0.03s
  · 再隐藏/再恢复: 5.12 / 5.08s → 0.03 / 0.03s
⇒ 快检那条臂的偶发 5s 不是派发代码缺陷、更不是 CDP 通道损坏, 而是"窗口不可见(渲染器被后台化节流)"的实例状态。
  这条 5 秒最容易被误判成"工具坏了", 于是换别的方法反复试错 —— 正是本目标要消灭的体验, 故由工具**自己说清成因**。

改动(全部落在两个 CDP 派发汇聚点, 不碰任何工具分支):
  1) MCP_Server.wsv 新增 浏览器窗口可见() 与 记CDP输入慢因(起始毫秒, 输入类别) —— 只在真慢(>2s)时回读一次
     GWL_STYLE 的 WS_VISIBLE 位, 并经既有 MCP_响应构建.记录自动处理 上报(auto_prepared), 零常态开销;
  2) CDP派发鼠标事件 / CDP派发触摸点一次 各加一行计时与上报(鼠标点击=两次派发, 故耗时按档位取整以便自动去重);
  3) 相关工具描述补一句实测事实与恢复手段(鼠标三件套 / 触摸三件套 / reverse_input_cdp / show_window)。

用法: py -3 _audit\_apply_input_slow_note.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
REVERSE = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')

# ── 新增代码块 ──
HELPER = '''    # ==== CDP Input 族"慢"的自诊断(第124轮实测归因) ====
    # 实测(受控 A/B/A/B, 可复现): browser_show_window visible:false 隐藏窗口后, **每一条** CDP Input 命令
    #   (Input.dispatchMouseEvent / dispatchTouchEvent / dispatchKeyEvent)都要 ~5.1s 才返回;
    #   同一实例里 Runtime.evaluate 仍 0.03s; 显示回来(visible:true)后**立即**回到 0.03s。
    #   成因: 窗口不可见时 Chromium 把渲染器后台化(节流), 输入事件要等渲染器唤醒 —— 属浏览器行为,
    #   不是本项目派发代码缺陷, 也不是 CDP 通道损坏。工具此时**仍然成功**, 只是慢。
    # 为什么要上报: 慢 5 秒最容易被误判成"工具坏了", 于是换别的方法反复试错 —— 正是本目标要消灭的体验。
    #   故只在真慢(>2s)时才回读一次窗口可见性, 并经既有的 auto_prepared 机制如实上报成因与恢复手段。

    方法 浏览器窗口可见 <公开 静态 类型 = 逻辑型 注释 = "回读主浏览器窗口 GWL_STYLE 的 WS_VISIBLE 位(0x10000000); 无浏览器时返回真(不把它当成慢的原因)" @输出名 = "BrowserWindowVisible" @强制输出 = 真>
    {
        变量 可见性浏览器 <类型 = 类_FBrowser_浏览器>
        可见性浏览器 = 取主浏览器 ()
        如果 (可见性浏览器.是否为空 () || 可见性浏览器.是否已关闭 ())
        {
            返回 (真)
        }
        返回 (位与 (可见性浏览器.取窗口属性 (MCP_常量.窗口样式_GWL_STYLE), 268435456) != 0)
    }

    方法 记CDP输入慢因 <公开 静态 @输出名 = "NoteCDPInputSlowReason" @强制输出 = 真>
    参数 起始毫秒 <类型 = 长整数 @输出名 = "StartMs">
    参数 输入类别 <类型 = 文本型 @输出名 = "InputKind">
    {
        变量 耗时 <类型 = 整数>
        耗时 = (整数)(取启动时间 () - 起始毫秒)
        如果 (耗时 < 2000)
        {
            返回
        }
        // 耗时按档位取整: 鼠标点击要连发 mousePressed+mouseReleased 两次, 档位化后可自动去重成一条上报
        变量 耗时档 <类型 = 文本型>
        如果 (耗时 >= 4000)
        {
            耗时档 = "约5秒"
        }
        否则
        {
            耗时档 = "2~4秒"
        }
        如果 (浏览器窗口可见 () == 假)
        {
            MCP_响应构建.记录自动处理 (输入类别 + "本次派发耗时" + 耗时档 + ": 浏览器窗口当前**不可见**(GWL_STYLE 的 WS_VISIBLE=0) ⇒ 渲染器被后台化节流, 实测该状态下**每条** CDP Input 命令都固定约5秒(工具仍然成功, 不是通道损坏) | 立即恢复手段: browser_show_window {visible:true}, 之后回到 30ms 级")
        }
        否则
        {
            MCP_响应构建.记录自动处理 (输入类别 + "本次派发耗时" + 耗时档 + ": 窗口可见但仍慢 ⇒ 常见成因: ①窗口被其它窗口完全遮挡(Windows 遮挡检测同样会节流渲染器) ②本会话先前调用过 kernel:true 内核级输入注入(该损伤需重启进程恢复) | 对照: 正常该命令 30ms 级; 可用 browser_show_window {visible:true} 或 browser_element_action(JS 事件派发) 规避")
        }
    }

'''

ANCHOR_COMMENT = '    # ==== 用 CDP 派发鼠标事件(不破坏 CDP 通道) ===='
MOUSE_VAR_OLD = '''        变量 参 <类型 = YYJSON对象类>
        参.创建自文本 ("{}")'''
MOUSE_VAR_NEW = '''        变量 派发起始毫秒 <类型 = 长整数>
        派发起始毫秒 = 取启动时间 ()
        变量 参 <类型 = YYJSON对象类>
        参.创建自文本 ("{}")'''

MOUSE_WAIT_OLD = '''        原始结果 = 执行CDP并同步等待 (临时ID, "Input.dispatchMouseEvent", 参.到可读文本 (YYJSON格式化选项.压缩), 8000)
        如果 (原始结果 == "")'''
MOUSE_WAIT_NEW = '''        原始结果 = 执行CDP并同步等待 (临时ID, "Input.dispatchMouseEvent", 参.到可读文本 (YYJSON格式化选项.压缩), 8000)
        记CDP输入慢因 (派发起始毫秒, "鼠标输入")
        如果 (原始结果 == "")'''

TOUCH_VAR_OLD = '''        // touchPoints 是"数组套对象"的嵌套结构'''
TOUCH_VAR_NEW = '''        变量 派发起始毫秒 <类型 = 长整数>
        派发起始毫秒 = 取启动时间 ()
        // touchPoints 是"数组套对象"的嵌套结构'''

TOUCH_WAIT_OLD = '''        原始结果 = 执行CDP并同步等待 (临时ID, "Input.dispatchTouchEvent", 参文本, 8000)
        返回 (CDP同步结果是否成功 (原始结果))'''
TOUCH_WAIT_NEW = '''        原始结果 = 执行CDP并同步等待 (临时ID, "Input.dispatchTouchEvent", 参文本, 8000)
        记CDP输入慢因 (派发起始毫秒, "触摸输入")
        返回 (CDP同步结果是否成功 (原始结果))'''

SHORT_SUFFIX = (' | 实测: 窗口不可见/被其它窗口完全遮挡时渲染器被节流, 每条 CDP Input 命令约5秒才返回'
                '(工具仍成功), 恢复可见立即回到30ms级; 慢时成因与恢复手段经 auto_prepared 上报')
MOVE_SUFFIX = (' | 实测: 窗口不可见(或被完全遮挡)时渲染器被节流, 每条 CDP Input 命令约5秒才返回'
               '(工具仍成功), 恢复可见立即回到30ms级; 慢时成因与恢复手段经 auto_prepared 上报')
SHOW_SUFFIX = (' | 实测副作用(重要): 窗口不可见时渲染器被后台化节流, CDP Input 族(鼠标/触摸/键盘直发)'
               '**每条**命令固定约5秒 —— 工具仍成功但明显变慢, 恢复 visible:true 后立即回到30ms级')

# 工具名 → (描述后缀, 该行里 schema 辅助方法前的标记)
DESC_EDITS = [
    ("browser_mouse_click", MOVE_SUFFIX, '", 多属性Schema文本'),
    ("browser_mouse_move", MOVE_SUFFIX, '", 多属性Schema文本'),
    ("browser_mouse_wheel", SHORT_SUFFIX, '", 多属性Schema文本'),
    ("browser_show_window", SHOW_SUFFIX, '", 多属性Schema文本'),
    ("browser_touch_press", SHORT_SUFFIX, '", 双XY_Schema文本'),
    ("browser_touch_release", SHORT_SUFFIX, '", 双XY_Schema文本'),
    ("browser_touch_move", SHORT_SUFFIX, '", 双XY_Schema文本'),
    # 逆向输入直发复用同一套 CDP 派发, 故同样补一句(它注册在 MCP_Server.wsv, 不在 Reverse.wsv)
    ("browser_reverse_input_cdp", SHORT_SUFFIX, '", 多属性Schema文本'),
]


def balance(text):
    """字符串字面量感知的 {} 与 () 净计数(跳过 @ 行与 // 、# 注释)。"""
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i = 0
        instr = False
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
    return ob, cb, op, cp


def edit_desc(lines, tool, suffix, marker):
    head = '        添加工具JSON ("%s", ' % tool
    idx = [i for i, ln in enumerate(lines) if ln.startswith(head)]
    assert len(idx) == 1, '%s 注册行数=%d' % (tool, len(idx))
    i = idx[0]
    assert lines[i].count(marker) == 1, '%s 里标记数=%d' % (tool, lines[i].count(marker))
    assert suffix.strip() not in lines[i], '%s 已改过' % tool
    lines[i] = lines[i].replace(marker, suffix + marker, 1)


def main():
    raw = io.open(SERVER, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '有 BOM'
    txt = raw.decode('utf-8')
    assert '\r' not in txt, 'MCP_Server.wsv 应为纯 LF'
    lines = txt.split('\n')
    n0 = len(lines)
    b0 = balance(txt)

    # 1) 插入自诊断代码块
    ci = [i for i, ln in enumerate(lines) if ln == ANCHOR_COMMENT]
    assert len(ci) == 1, '锚点注释数=%d' % len(ci)
    lines[ci[0]:ci[0]] = HELPER.split('\n')[:-1]

    # 2) 鼠标/触摸汇聚点: 计时 + 上报
    joined = '\n'.join(lines)
    for old, new, tag in ((MOUSE_VAR_OLD, MOUSE_VAR_NEW, '鼠标计时变量'),
                          (MOUSE_WAIT_OLD, MOUSE_WAIT_NEW, '鼠标慢因上报'),
                          (TOUCH_VAR_OLD, TOUCH_VAR_NEW, '触摸计时变量'),
                          (TOUCH_WAIT_OLD, TOUCH_WAIT_NEW, '触摸慢因上报')):
        assert joined.count(old) == 1, '%s 锚点出现 %d 次' % (tag, joined.count(old))
        joined = joined.replace(old, new, 1)
    lines = joined.split('\n')

    # 3) 工具描述
    for tool, suffix, marker in DESC_EDITS:
        edit_desc(lines, tool, suffix, marker)

    out = '\n'.join(lines)
    b1 = balance(out)
    # 新增代码块自身带成对括号, 故只比**净值**(开-闭), 它变化就说明有括号没配平
    assert (b0[0] - b0[1], b0[2] - b0[3]) == (b1[0] - b1[1], b1[2] - b1[3]), \
        '括号净值变了: %s -> %s' % (b0, b1)
    for must in ('方法 记CDP输入慢因', '方法 浏览器窗口可见',
                 '记CDP输入慢因 (派发起始毫秒, "鼠标输入")',
                 '记CDP输入慢因 (派发起始毫秒, "触摸输入")'):
        assert must in out, '缺少 %s' % must
    print('MCP_Server.wsv: 行数 %d -> %d (+%d); 括号净计数 %s (不变)'
          % (n0, len(lines), len(lines) - n0, b1))

    # 4) Reverse: 本文件无需改动(其工具注册在 MCP_Server.wsv), 保留读取以免将来误判
    rtxt = io.open(REVERSE, encoding='utf-8').read()
    assert '添加工具JSON ("browser_reverse_input_cdp"' not in rtxt, 'Reverse 里出现了该工具注册, 需改回此处处理'
    print('MCP_Server_Reverse.wsv: 无需改动(该工具注册在 MCP_Server.wsv), 已断言')

    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        # 回读校验
        chk = io.open(SERVER, encoding='utf-8').read()
        assert '方法 记CDP输入慢因' in chk and '方法 浏览器窗口可见' in chk
        assert chk.count('记CDP输入慢因 (派发起始毫秒') == 2
        assert '\r' not in chk
        for tool, suffix, _m in DESC_EDITS:
            assert suffix.strip() in chk, '%s 描述未写入' % tool
        print('已写入 MCP_Server.wsv 并回读校验通过(%d 个工具描述已补)' % len(DESC_EDITS))
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
