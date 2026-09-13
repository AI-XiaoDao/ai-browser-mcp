# -*- coding: utf-8 -*-
"""让 browser_network_body **一次调用就把响应体带回来**。

修复后的实测(工具已接受十六进制 id, 但回包仍是):
  {"success":true,"_async":true,"task_id":"1","message":"CDP已提交:Network.getResponseBody"}
=> 走了异步入口 执行CDP命令_带参数, **响应体被丢弃**; 调用方要再调 mcp_result 才可能拿到,
   与"一次调用就成功拿到数据"的目标不符 —— 与第 97 轮修的 7 个逆向取数调用点是同一缺陷类。

改用 Core 既有的同步惯用法(见 browser_move_window 的写法, MCP_Server_Core.wsf:5490-5501):
  执行CDP并同步等待 -> CDP同步结果是否成功 -> 取CDP同步结果体文本 -> 解析
并如实报告 base64 标志、长度与截断。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', 'network_body改同步-写入前')

OLD = r'            返回 (MCP命令服务器.执行CDP命令_带参数 (命令ID, "Network.getResponseBody", bodyParams.到可读文本 (YYJSON格式化选项.压缩)))'

NEW = r'''            变量 body同步 <类型 = 文本型>
            body同步 = MCP命令服务器.执行CDP并同步等待 (命令ID, "Network.getResponseBody", bodyParams.到可读文本 (YYJSON格式化选项.压缩), 15000)
            如果 (MCP命令服务器.CDP同步结果是否成功 (body同步) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "Network.getResponseBody 失败: " + MCP命令服务器.取CDP同步结果错误 (body同步) + " | 常见原因: 该请求的响应体已不在缓存中(要在请求发生后尽快取), 或 requestId 不属于当前页面 | 建议重新订阅并复现一次请求后立即取"))
            }
            变量 body体 <类型 = 文本型>
            body体 = MCP命令服务器.取CDP同步结果体文本 (body同步)
            变量 body内容 <类型 = 文本型>
            body内容 = ""
            变量 body是B64 <类型 = 逻辑型>
            body是B64 = 假
            如果 (body体 != "")
            {
                变量 body解析 <类型 = YYJSON只读对象类>
                如果 (body解析.创建自文本 (body体))
                {
                    body内容 = MCP命令服务器.yyjson取文本 (body解析, "body")
                    body是B64 = MCP命令服务器.yyjson取逻辑_默认 (body解析, "base64Encoded", 假)
                }
            }
            变量 body全长 <类型 = 整数>
            body全长 = 取文本长度 (body内容)
            变量 body上限 <类型 = 整数>
            body上限 = 200000
            变量 body已截 <类型 = 逻辑型>
            body已截 = 假
            如果 (body全长 > body上限)
            {
                body内容 = 取文本左边 (body内容, body上限)
                body已截 = 真
            }
            变量 body结果 <类型 = YYJSON对象类>
            body结果.创建自文本 ("{}")
            body结果.加入逻辑值成员 ("success", 真)
            body结果.加入文本成员 ("request_id", requestId)
            body结果.加入逻辑值成员 ("base64_encoded", body是B64)
            body结果.加入整数成员 ("body_length", body全长)
            body结果.加入逻辑值成员 ("body_truncated", body已截)
            如果 (body是B64)
            {
                body结果.加入文本成员 ("body", body内容)
                body结果.加入文本成员 ("note", "body 为 base64 编码(该响应体是二进制或以二进制判定), 解码后才是原文; 可用 browser_base64_decode 解码")
            }
            否则
            {
                body结果.加入文本成员 ("body", body内容)
                body结果.加入文本成员 ("note", "body 为原文(未编码)")
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, body结果.到可读文本 (YYJSON格式化选项.压缩)))'''


def main():
    data = open(SRC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '不应有BOM'
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s' % ('CRLF' if nl == '\r\n' else 'LF'))
    n = text.count(OLD)
    print('锚点命中: %d' % n)
    if n != 1:
        print('!! 锚点不唯一, 中止')
        return 1
    for ln in NEW.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            print('!! 裸双引号奇数: %s' % ln)
            return 1
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
    print('备份 -> %s' % BAK)
    open(SRC, 'wb').write(text.replace(OLD, NEW.replace('\n', nl)).encode('utf-8'))
    print('已写入; 该处 1 行 -> %d 行' % len(NEW.split('\n')))
    return 0


sys.exit(main())
