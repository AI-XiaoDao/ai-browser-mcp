# -*- coding: utf-8 -*-
r"""订正 try_close 的"否决"文案: 不要把成因一口咬定为"页面 beforeunload"。

实测(verify_close_try.py 第一版, 探针 bug 导致每次都打在主浏览器上):
  · 对**主浏览器**(本项目里=程序窗口, 非页面驱动窗口)调用 尝试关闭浏览器 恒返回**假**;
  · 而同一浏览器用不带 try_close 的强制关闭可以正常关掉。
=> 返回假有两种成因(页面否决 / 目标不是页面驱动窗口), 文案必须把两者都列出并给出区分手段,
   否则会把"主浏览器不适用"误报成"页面拒绝了" —— 那是把猜测写成事实。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

OLD = '返回 (MCP_响应构建.命令失败 (命令ID, "关闭被页面否决: 页面 beforeunload 处理器返回了内容且未确认 | 依据: 类库 尝试关闭浏览器(TryCloseBrowser) 返回假 = 未开始关闭 | 可用替代: ① 不带 try_close 的强制关闭(不询问页面) ② 用 browser_collect 查 js_dialog/before_unload 事件看页面提了什么 ③ 页面允许后再重试"))'
NEW = '返回 (MCP_响应构建.命令失败 (命令ID, "关闭未开始: 内核 TryCloseBrowser 返回假(类库 尝试关闭浏览器) —— 它只表示\\"没有任何关闭被发起\\", 成因有两种, 请按下述区分: ① 页面 beforeunload 未确认(页面驱动窗口) ② **目标不是页面驱动窗口** —— 实测对本项目**主浏览器**(=程序窗口)调用它恒返回假, 该情形它不适用 | 替代: 不带 try_close 的强制关闭(不询问页面) / browser_list 看该 id 是否仍在 / browser_collect 查 js_dialog、before_unload 事件看页面提了什么"))'


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    txt = raw.decode('utf-8')
    n = txt.count(OLD)
    assert n == 1, '锚点命中 %d 次' % n
    out = txt.replace(OLD, NEW)
    print('已替换"否决"文案(两种成因并列 + 区分手段)')
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
