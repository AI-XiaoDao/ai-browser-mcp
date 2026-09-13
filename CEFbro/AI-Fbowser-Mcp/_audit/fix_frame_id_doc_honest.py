# -*- coding: utf-8 -*-
r"""把注入到 21 个 schema 里的 `frame_id` 说明改成**如实版**: 写得到、读要绕 CDP。

实测(本轮):
  · 原生(填表)路径**支持子框架** —— `browser_fill_set_value {frame_id}` 确实写进了 iframe, 主框架不受影响;
  · 但**走 CDP JS 的读取类工具仍在主框架求值**(它们为绕开"CEF JS 回调恒返回 null"而改为 CDP 优先),
    故 `browser_fill_attr_get {frame_id}` 这类读取不会进 iframe;
  · 读 iframe 的可行路径**已在本机实测**: `Page.getFrameTree` 取 **CDP 侧 frameId**(与 browser_get_frames
    的 `6-…` **不是同一套**) -> `Page.createIsolatedWorld {frameId}` 取 executionContextId ->
    `Runtime.evaluate {contextId}`(实测读到 iframe 内部文本)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

OLD = ('iframe 的框架ID(取自 browser_get_frames 的 id 字段)或框架名; 省略=主框架')
NEW = ('iframe 的框架ID(取自 browser_get_frames 的 id)或框架名; 省略=主框架。'
       '实测边界: **原生填表路径支持子框架**(已在 iframe 内写入验证), '
       '但走 CDP JS 的**读取类**工具仍在主框架求值 —— 读 iframe 内容请走 CDP: '
       'Page.getFrameTree 取 CDP 侧 frameId(与 browser_get_frames 的 id **不是同一套**) '
       '-> Page.createIsolatedWorld {frameId} -> Runtime.evaluate {contextId}(本机已实测可行)')
n = text.count(OLD)
print('待替换的出现次数 = %d (应为 21)' % n)
if n != 21:
    print('!! 与预期不符, 未写文件')
    sys.exit(1)
if NEW.replace('\\"', '').count('"') % 2 != 0:
    print('!! 新文案引号奇数')
    sys.exit(1)
open(P, 'wb').write(text.replace(OLD, NEW).encode('utf-8'))
print('已把 21 处 frame_id 说明改为如实版')
