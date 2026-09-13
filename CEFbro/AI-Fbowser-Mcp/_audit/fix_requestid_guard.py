# -*- coding: utf-8 -*-
"""修复 browser_network_body 的 request_id 格式守卫 —— 它按"数字串"假设硬拒**合法** id。

实测铁证:
  真实 requestId  = A6EE022756279359D6FE08AC76711D8D  (32 位十六进制)
  内核 Network.getResponseBody {requestId: 该值}
    -> {"body":"<!doctype html><html lang="en">...<title>Example Domain</title>..."}  内核**认**
  工具 browser_network_body {request_id: 同一值}
    -> 非法 CDP request_id: A6EE... | CDP 请求标识为数字串(形如 1000012345.5) | 如何取得有效值:
       ① cdp_monitor 订阅 ② cdp_event 取 requestId ③ 再调用本工具          <-- 自相矛盾

即: 守卫要求的格式在本机**根本不存在**, 而它给出的"如何取得有效值"路径拿到的正是被它拒绝的值。
=> 本工具 100% 不可用, 且报错文案会把调用方引向死循环。

修法: 保留"廉价前置校验"的本意(挡住明显畸形值, 避免持锁), 但**不假设具体格式** ——
改为长度上限 + 不含空白/双引号/花括号, 从而同时接受:
  · 本机 32 位十六进制          例: A6EE022756279359D6FE08AC76711D8D
  · 其它实现的数字串(含点)      例: 1000012345.5
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', 'network_body的id格式守卫-写入前')

OLD = [
    r'            // CDP 的 RequestId 为数字串(形如 1000012345.5), 按格式快速失败(非法 id 不会得到内核响应, 会持协议锁挂满 30s+ 拖累其它请求)',
    '            变量 首字符 <类型 = 文本型>',
    '            首字符 = 取文本左边 (requestId, 1)',
    r'            如果 (寻找文本 ("0123456789", 首字符, 0, 假) == -1)',
    '            {',
    r'                返回 (MCP_响应构建.命令失败 (命令ID, "非法 CDP request_id: " + requestId + " | CDP 请求标识为数字串(形如 1000012345.5) | 如何取得有效值: ① browser_kernel_cdp_monitor action=add methods=Network.* 订阅 ② browser_cdp_event event_name=Network.requestWillBeSent 取其中的 requestId ③ 再调用本工具 | 注意: browser_network list 的日志里没有 CDP request_id, 取不到"))',
    '            }',
]

NEW = [
    '            // 前置廉价校验(挡住明显畸形值, 避免拿畸形 id 去占 CDP 协议锁), 但**不假设具体格式**:',
    '            // 本机实测 requestId 是 **32 位十六进制**(如 A6EE022756279359D6FE08AC76711D8D),',
    '            // 而旧代码按"数字串(形如 1000012345.5)"硬判首字符 —— 于是把**合法** id 全部拒掉,',
    '            // 且它给出的"如何取得有效值"路径拿到的正是被它拒绝的那个值(自相矛盾, 必然死循环)。',
    '            // 现改为: 长度上限 + 不含空白/双引号/花括号, 因此两种格式都能通过。',
    '            变量 格式非法 <类型 = 逻辑型>',
    '            格式非法 = 假',
    '            如果 (取文本长度 (requestId) > 64)',
    '            {',
    '                格式非法 = 真',
    '            }',
    r'            如果 (寻找文本 (requestId, " ", 0, 假) != -1)',
    '            {',
    '                格式非法 = 真',
    '            }',
    r'            如果 (寻找文本 (requestId, "\"", 0, 假) != -1)',
    '            {',
    '                格式非法 = 真',
    '            }',
    r'            如果 (寻找文本 (requestId, "{", 0, 假) != -1 || 寻找文本 (requestId, "}", 0, 假) != -1)',
    '            {',
    '                格式非法 = 真',
    '            }',
    '            如果 (格式非法 == 真)',
    '            {',
    r'                返回 (MCP_响应构建.命令失败 (命令ID, "非法 CDP request_id: " + requestId + " | 合法形态: 本机为 32 位十六进制(如 A6EE022756279359D6FE08AC76711D8D), 其它实现可能是数字串(如 1000012345.5); 不能含空白/引号/花括号, 长度不超过 64 | 如何取得有效值: ① browser_kernel_cdp_monitor action=add methods=Network.* 订阅 ② browser_cdp_event event_name=Network.requestWillBeSent 取其中的 requestId ③ 尽快调用本工具(响应体可能被回收)"))',
    '            }',
]


def main():
    data = open(SRC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '不应有BOM'
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s' % ('CRLF' if nl == '\r\n' else 'LF'))
    old = nl.join(OLD)
    n = text.count(old)
    print('锚点命中: %d' % n)
    if n != 1:
        print('!! 锚点不唯一, 中止')
        return 1
    # 转义自查
    for ln in NEW:
        if ln.replace('\\"', '').count('"') % 2 != 0:
            print('!! 裸双引号奇数: %s' % ln)
            return 1
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
    print('备份 -> %s' % BAK)
    open(SRC, 'wb').write(text.replace(old, nl.join(NEW)).encode('utf-8'))
    print('已写入; 行数 %d -> %d' % (len(OLD), len(NEW)))
    return 0


sys.exit(main())
