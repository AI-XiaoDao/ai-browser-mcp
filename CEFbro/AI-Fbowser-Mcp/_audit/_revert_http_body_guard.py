# -*- coding: utf-8 -*-
r"""回退 `_apply_http_body_guard.py` —— **实测证明该守卫无法生效**, 且会误伤可用请求。

为什么回退(本轮实测, 证据确凿):
  · 加守卫后重测 1.5MB 入参: 客户端**仍然**收到 `RemoteDisconnected`(无任何响应), 说明那道 1MB 墙在
    **类库/CEF 侧、早于 `收到HTTP请求` 事件** —— 处理器里的 Content-Length 检查根本不会被执行;
  · 而实测 1020KB(1,044,480 字节填充)是**能通过**的, 若按 1,000,000 字节安全上限拒绝, 就会把
    1,000,001~1,048,575 这一整段**本来可用**的请求误判为超限 ⇒ 净损失。
  ⇒ 结论: 超限请求"拿不到可行动错误"这一点**在服务端无解**(请求根本到不了我们的代码),
     只能靠**文档 + 能力替代**解决: ①把"大参数"改成**文件路径**类参数(本轮同时给
     `browser_execute_js.file` / `browser_create_url_request.body_file` 加支持) ②改用 WebSocket(50MB)/stdio 通道。
  本条回归说明: 守卫代码已删, 但**实测事实与替代方案**已写进 docs 与 help 文案。

用法: py -3 _audit\_revert_http_body_guard.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTTP = os.path.join(ROOT, 'src', 'MCP_Server_HTTP.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CONST = os.path.join(ROOT, 'src', 'MCP_Constants.wsv')


def cut(path, marker_start, marker_end, name, keep_end=True):
    """删掉 [marker_start 行 .. marker_end 行) 这一整段(按文本子串定位)。"""
    raw = io.open(path, 'rb').read()
    has_cr = b'\r' in raw
    txt = raw.decode('utf-8')
    i = txt.find(marker_start)
    assert i != -1, '%s: 找不到起点' % name
    j = txt.find(marker_end, i)
    assert j != -1, '%s: 找不到终点' % name
    out = txt[:i] + (marker_end if keep_end else '') + txt[j + len(marker_end):]
    io.open(path, 'w', encoding='utf-8', newline='\n').write(out)
    chk = io.open(path, 'rb').read()
    assert (b'\r' in chk) == has_cr, '%s 行尾风格被改变' % name
    print('%s: 已删除 %d 字节' % (name, len(txt) - len(out)))


def main():
    # ① HTTP 守卫块: 从注释头删到"读取HTTP_POST体"调用之前
    cut(HTTP,
        '                // ★ 前置守卫(第126轮实测)',
        '                变量 请求体JSON <类型 = 文本型>\n                请求体JSON = MCP命令服务器.读取HTTP_POST体 (请求)',
        'MCP_Server_HTTP.wsv 守卫',
        keep_end=True)
    # ② Server 里的取请求头整数值 辅助(含其注释头)
    cut(SERVER,
        '    # 取请求头里的整数值(用于在**读正文之前**按 Content-Length 做容量守卫)',
        '    方法 读取HTTP_POST体 <公开 静态 类型 = 文本型 @输出名 = "ReadHTTPPOSTBody" @强制输出 = 真>',
        'MCP_Server.wsv 取请求头整数值',
        keep_end=True)
    # ③ 常量(仅被守卫引用, 一并回退; 实测事实改由 docs/help 承载)
    raw = io.open(CONST, 'rb').read()
    txt = raw.decode('utf-8')
    i = txt.find('    // 第126轮实测: MCP **HTTP** 通道在请求体约 1MB')
    j = txt.find('    @输出名 = "HTTPBodySafeLimit">')
    assert i != -1 and j != -1, '常量定位失败'
    out = txt[:i] + txt[j + len('    @输出名 = "HTTPBodySafeLimit">') + 1:]
    io.open(CONST, 'w', encoding='utf-8', newline='\n').write(out)
    print('MCP_Constants.wsv: 已删除 HTTP请求体安全上限 常量')
    chk = io.open(SERVER, encoding='utf-8').read()
    assert '方法 取请求头整数值' not in chk
    ch2 = io.open(HTTP, encoding='utf-8').read()
    assert '前置守卫(第126轮实测)' not in ch2 and '读取HTTP_POST体 (请求)' in ch2
    print('回读校验通过(守卫/辅助/常量均已移除, 正文读取路径完好)')


main()
