# -*- coding: utf-8 -*-
r"""第126轮: 给 browser_create_url_request 加 `body_file` —— 让"大请求体"绕开 MCP HTTP 通道的 ~1MB 请求体上限。

实测依据(本轮, `_audit/probe_arg_size_limit.py` + `verify_http_body_guard.py`):
  · arguments 1020KB 通过、1024KB(=1,048,576 字节)被**内核直接断连**(客户端只见 RemoteDisconnected, 无错误码);
  · 该墙在类库/CEF 侧、**早于**本项目的 `收到HTTP请求` 事件 —— 已实测"在处理器里按 Content-Length 提前拒绝"
    的守卫**根本进不来**, 且设 100 万字节安全线会误伤 1,000,001~1,048,575 这段**本来可用**的请求,
    故守卫已回退(见 `_revert_http_body_guard.py`);
  ⇒ 唯一有效的服务端缓解是**把大参数改成文件路径**。类库恰好提供 `类_FBrowser_POST元素.置数据_文件 (文件名)`
    (FBroLib.wsv:2602 → CEF `SetToFile`), 于是本工具新增 `body_file`: 请求体**直接从文件上传**(不把内容塞进 arguments,
    也不必读进内存)。

用法: py -3 _audit\_apply_body_file.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

# ① Core: 读取 body_file + 文件直传
CORE_READ_OLD = '''            变量 reqBody <类型 = 文本型>
            reqBody = MCP命令服务器.yyjson取文本 (参数JSON, "body")'''
CORE_READ_NEW = '''            变量 reqBody <类型 = 文本型>
            reqBody = MCP命令服务器.yyjson取文本 (参数JSON, "body")
            // ★ 大请求体走文件(第126轮实测的传输限制缓解手段):
            //   MCP HTTP 通道在 arguments ≥1MB 时会被内核直接断连(客户端只看到"无响应", 拿不到错误码);
            //   该墙早于本项目的事件处理, 服务端无法拦截, 故提供 body_file: 请求体从文件直传
            //   (类库 置数据_文件 → CEF SetToFile), 无需把内容塞进 arguments, 也不必读进内存。
            变量 reqBodyFile <类型 = 文本型>
            reqBodyFile = MCP命令服务器.yyjson取文本 (参数JSON, "body_file")
            变量 体来自文件 <类型 = 逻辑型>
            体来自文件 = 假
            如果 (reqBody == "" && reqBodyFile != "")
            {
                如果 (文件是否存在 (reqBodyFile) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "body_file 不存在: " + reqBodyFile + " | 请给**绝对路径**(相对路径按进程运行目录解析) | 提示: 大请求体请用 body_file 而不是 body —— 实测 MCP HTTP 通道在 arguments 约 1MB 处会被内核直接断连(客户端只看到无响应)"))
                }
                体来自文件 = 真
            }'''

CORE_BODY_OLD = '''            // 复用 应用请求体文本(同上; 返回的是 UTF-8 字节数)
            变量 体字节数 <类型 = 整数>
            体字节数 = MCP命令服务器.应用请求体文本 (请求, reqBody)'''
CORE_BODY_NEW = '''            // 复用 应用请求体文本(同上; 返回的是 UTF-8 字节数); body_file 走类库文件直传
            变量 体字节数 <类型 = 整数>
            如果 (体来自文件)
            {
                变量 文件元素 <类型 = 类_FBrowser_POST元素>
                文件元素.创建 ()
                文件元素.置数据_文件 (reqBodyFile)
                变量 文件体数据 <类型 = 类_FBrowser_POST数据>
                文件体数据.创建 ()
                文件体数据.增加元素 (文件元素)
                请求.置POST数据 (文件体数据)
                体字节数 = 0   // 文件直传不读入内存, 故不报字节数(避免为了报数把整个文件读一遍)
            }
            否则
            {
                体字节数 = MCP命令服务器.应用请求体文本 (请求, reqBody)
            }'''

CORE_FLAG_OLD = '''            如果 (reqBody != "")
            {
                变量 原标识 <类型 = 整数>
                原标识 = 请求.取标识 ()
                请求.设置标识 (位或 (原标识, 请求标识.上载进度报告))
                MCP_响应构建.记录自动处理 ("UR_FLAG_REPORT_UPLOAD_PROGRESS(请求体非空时自动置位; 上传进度事件 urlreq_upload 需要它)")
            }'''
CORE_FLAG_NEW = '''            如果 (reqBody != "" || 体来自文件)
            {
                变量 原标识 <类型 = 整数>
                原标识 = 请求.取标识 ()
                请求.设置标识 (位或 (原标识, 请求标识.上载进度报告))
                MCP_响应构建.记录自动处理 ("UR_FLAG_REPORT_UPLOAD_PROGRESS(请求体非空时自动置位; 上传进度事件 urlreq_upload 需要它)")
            }'''

# ② Server: schema + 描述
TOOL_OLD = '属性项JSON ("body", "text", "请求体(UTF-8)")'
TOOL_NEW = ('属性项JSON ("body", "text", "请求体(UTF-8); **大请求体请改用 body_file**(实测 MCP HTTP 通道在 arguments 约 1MB 处会被内核直接断连且无错误码)") + "," + '
            '属性项JSON ("body_file", "text", "请求体来自本地文件(绝对路径) —— 类库以 CEF SetToFile **从文件直传**, '
            '既不必把内容塞进 arguments, 也不必读进内存")')

DESC_OLD = '给了 body 且未显式给 method 时自动用 POST'
DESC_NEW = ('给了 body(或 body_file) 且未显式给 method 时自动用 POST(**大请求体请用 body_file**: '
            '实测 MCP HTTP 通道 arguments 约 1MB 处会被内核直接断连且无错误码)')


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


def patch(path, edits, name, check=()):
    raw = io.open(path, 'rb').read()
    has_cr = b'\r' in raw
    txt = raw.decode('utf-8')
    b0, n0 = balance(txt), len(txt.split('\n'))
    out = txt
    for old, new in edits:
        assert out.count(old) == 1, '%s 锚点 %d 次: %s' % (name, out.count(old), old.strip()[:50])
        out = out.replace(old, new, 1)
    assert balance(out) == b0, '%s 括号净值变了 %s -> %s' % (name, b0, balance(out))
    for m in check:
        assert m in out or m in txt, '%s 缺少 %s' % (name, m)
    print('%s: 行数 %d -> %d (CR=%s); 括号净值 %s 不变' % (name, n0, len(out.split('\n')), has_cr, balance(out)))
    return raw, out, has_cr


def main():
    c_raw, c_out, c_cr = patch(CORE, [(CORE_READ_OLD, CORE_READ_NEW),
                                      (CORE_BODY_OLD, CORE_BODY_NEW),
                                      (CORE_FLAG_OLD, CORE_FLAG_NEW)],
                               'MCP_Server_Core.wsv',
                               check=['体来自文件', '文件元素.置数据_文件 (reqBodyFile)'])
    # Server: 注册行里两处替换(同一行, 分两次替换)
    raw = io.open(SERVER, 'rb').read()
    txt = raw.decode('utf-8')
    sb0 = balance(txt)
    idx = [i for i, ln in enumerate(txt.split('\n')) if '添加工具JSON ("browser_create_url_request"' in ln]
    assert len(idx) == 1, 'create_url_request 注册行 %d' % len(idx)
    lines = txt.split('\n')
    ln = lines[idx[0]]
    assert ln.count(TOOL_OLD) == 1, 'body 属性锚点 %d' % ln.count(TOOL_OLD)
    ln = ln.replace(TOOL_OLD, TOOL_NEW, 1)
    assert ln.count(DESC_OLD) == 1, '描述锚点 %d' % ln.count(DESC_OLD)
    ln = ln.replace(DESC_OLD, DESC_NEW, 1)
    lines[idx[0]] = ln
    s_out = '\n'.join(lines)
    assert balance(s_out) == sb0, 'Server 括号净值变了'
    print('MCP_Server.wsv: 注册行已更新(body_file + 描述); 行数 %d 不变' % len(lines))

    if '--apply' in sys.argv:
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        c1 = io.open(CORE, encoding='utf-8').read()
        c2 = io.open(SERVER, encoding='utf-8').read()
        assert '置数据_文件 (reqBodyFile)' in c1 and ('\r' in c1) == c_cr
        assert '"body_file"' in c2 and '\r' not in c2
        print('已写入 Core + Server 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
