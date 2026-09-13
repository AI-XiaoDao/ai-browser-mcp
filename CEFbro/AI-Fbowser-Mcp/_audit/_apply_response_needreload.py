# -*- coding: utf-8 -*-
r"""第 170 轮: 响应_需要刷新 加"渲染器自愈等待"(CRLF 文件, 字节级插入)。
指纹/代理/内核变更可能立即重启渲染器, 紧随其后的 CDP 调用全部超时 → 活体短探连败 → 误判冷重启。
有界等待恢复(最多约 12 秒), 通道已健康时首探 0.03s 即回。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'src', 'MCP_ResponseBuilders.wsv')
raw = io.open(F, 'rb').read()

ANCHOR = ('    {\r\n'
          '        \u53d8\u91cf \u5bf9\u8c61 <\u7c7b\u578b = YYJSON\u5bf9\u8c61\u7c7b>\r\n'
          '        \u5bf9\u8c61.\u521b\u5efa\u81ea\u6587\u672c ("{}")\r\n').encode('utf-8')
n = raw.count(ANCHOR)
if n != 1:
    print('!! 锚点出现 %d 次(应为1), 中止' % n)
    sys.exit(2)

INSERT = (
    '        // \u6e32\u67d3\u5668\u81ea\u6108\u7b49\u5f85: \u6307\u7eb9/\u4ee3\u7406/\u5185\u6838\u53d8\u66f4\u53ef\u80fd\u7acb\u5373\u91cd\u542f\u6e32\u67d3\u5668, \u7d27\u968f\u5176\u540e\u7684 CDP \u8c03\u7528\u4f1a\u5168\u90e8\u8d85\u65f6\r\n'
    '        // (2025-09-13 \u5168\u91cf\u626b\u6d4b\u5b9e\u6d4b: fingerprint_ua \u540e\u6d3b\u4f53\u77ed\u63a2\u8fde\u8d25, \u88ab\u8bef\u5224\u51b7\u91cd\u542f)\u3002\u6709\u754c\u7b49\u5f85\u6062\u590d(\u6700\u591a\u7ea6 12 \u79d2),\r\n'
    '        // \u8ba9\u4e0b\u4e00\u4e2a\u5de5\u5177\u62ff\u5230\u5065\u5eb7\u901a\u9053; \u901a\u9053\u672c\u5df2\u5065\u5eb7\u65f6\u9996\u4e2a 3 \u79d2\u63a2\u9488 0.03s \u5373\u56de\u3002\r\n'
    '        \u8ba1\u6b21\u5faa\u73af (4)\r\n'
    '        {\r\n'
    '            \u53d8\u91cf \u81ea\u6108\u503c <\u7c7b\u578b = \u6587\u672c\u578b>\r\n'
    '            \u81ea\u6108\u503c = MCP\u547d\u4ee4\u670d\u52a1\u5668.CDP\u6267\u884cJS\u5e76\u7b49\u5f85 ("1", 3000, \u771f)\r\n'
    '            \u5982\u679c (\u81ea\u6108\u503c == "1")\r\n'
    '            {\r\n'
    '                \u8df3\u51fa\u5faa\u73af\r\n'
    '            }\r\n'
    '        }\r\n').encode('utf-8')

pos = raw.find(ANCHOR)
raw = raw[:pos] + INSERT + raw[pos:]
io.open(F, 'wb').write(raw)
print('已插入渲染器自愈等待到 响应_需要刷新')
