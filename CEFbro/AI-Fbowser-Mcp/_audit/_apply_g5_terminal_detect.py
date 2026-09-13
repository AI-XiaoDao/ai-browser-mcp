# -*- coding: utf-8 -*-
r"""G5b: 让"下载终态"在本机 CEF 回调序列里**确实能触发**(整块替换, 不做嵌套插入)。

实测(真机下载 8199 字节到本地后查事件): download_start / download_progress 已有新字段,
但 **download_complete 一条都没有** —— 本机 CEF 回调里 isComplete 为真的那次(或该类库方法)不出现,
只按 是否已下载完成()/是否已取消() 判定终态 == 该功能在本机永不生效。

替换后的终态块:
  · 判据 = 是否已下载完成() **或** 是否已取消() **或** (总长度>0 且 已下载长度>=总长度);
  · 去重: 同一 download_id 只上报一次(避免 100% 里程碑与 isComplete 重复命中);
  · 字段保持与原来一致(download_id/filename/url/original_url/total_bytes/received_bytes/mime/
    content_disposition/saved_path/start_time/end_time/completed/canceled)。

本文件是**双倍行距**风格(每条语句后跟一个空行), 插入时严格保持一致。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_BrowserEvents.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

VAR_ANCHOR = '    变量 是否监控下载事件 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_可下载/下载进度 → browser_event:download_*" @输出名 = "IsMonitorDownloadEvent">'
VAR_NEW = ['',
           '    变量 下载终态已报ID <公开 静态 类型 = 文本型 值 = "" 注释 = "最近一次已上报终态的下载ID(去重: 100%完成里程碑与 isComplete 回调可能重复命中)" @输出名 = "LastDownloadTerminalID">']

BLOCK_START = '            // G5: 下载终态上报 —— 此前仅按里程碑百分比写 download_progress, 完成后客户端拿不到落盘路径'
BLOCK_END_ANCHOR = '            // 内核层: 消费 browser_kernel_download 待执行操作 (pause/resume/cancel), 事件内即时执行'

NEW_BLOCK = '''            // G5: 下载终态上报 —— 此前仅按里程碑百分比写 download_progress, 完成后客户端拿不到落盘路径。
            // 判据补强(实测): 本机 CEF 回调里 isComplete 为真的那次**不出现**(真机下载 8199 字节后只有
            // start/progress 事件, complete 一条都没有), 故"已收满"同样视为终态, 否则本功能在本机永不生效。
            变量 终态已传字节 <类型 = 长整数>
            终态已传字节 = 下载.取已下载长度 ()
            变量 终态总字节 <类型 = 长整数>
            终态总字节 = 下载.取总长度 ()
            变量 终态收满 <类型 = 逻辑型>
            终态收满 = (终态总字节 > 0 && 终态已传字节 >= 终态总字节)
            变量 终态ID <类型 = 文本型>
            终态ID = 到文本 (下载.取关联标识符 ())
            如果 ((下载.是否已下载完成 () || 下载.是否已取消 () || 终态收满) && 终态ID != 下载终态已报ID)
            {
                下载终态已报ID = 终态ID
                变量 终态数据 <类型 = YYJSON对象类>
                终态数据.创建自文本 ("{}")
                终态数据.加入整数成员 ("download_id", 下载.取关联标识符 ())
                终态数据.加入文本成员 ("filename", 下载.取推荐文件名 ())
                终态数据.加入文本成员 ("url", 下载.取地址 ())
                终态数据.加入文本成员 ("original_url", 下载.取原始地址 ())
                终态数据.加入长整数成员 ("total_bytes", 终态总字节)
                终态数据.加入长整数成员 ("received_bytes", 终态已传字节)
                终态数据.加入文本成员 ("mime", 下载.取MIME类型 ())
                终态数据.加入文本成员 ("content_disposition", 下载.取内容描述 ())
                终态数据.加入文本成员 ("saved_path", 下载.取存储位置 ())
                终态数据.加入文本成员 ("start_time", 下载.取开始时间 ())
                终态数据.加入文本成员 ("end_time", 下载.取结束时间 ())
                变量 终态类型 <类型 = 文本型>
                终态类型 = "download_complete"
                如果 (下载.是否已取消 ())
                {
                    终态类型 = "download_canceled"
                }
                终态数据.加入逻辑值成员 ("completed", 下载.是否已下载完成 ())
                终态数据.加入逻辑值成员 ("canceled", 下载.是否已取消 ())
                终态数据.加入逻辑值成员 ("received_all", 终态收满)
                控制台输出 (到文本 ("[MCP] 下载终态:") + 终态类型 + " " + 下载.取存储位置 ())
                记录监控事件 (MCP命令服务器.是否监控下载事件, 终态类型, 浏览器.取ID (), 终态数据.到可读文本 (YYJSON格式化选项.压缩))
            }'''


def depth_delta(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@') or st.startswith('//') or st.startswith('#'):
            continue
        k = 0
        in_str = False
        while k < len(ln):
            c = ln[k]
            if in_str:
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '(':
                    p += 1
                elif c == ')':
                    p -= 1
                elif c == '{':
                    b += 1
                elif c == '}':
                    b -= 1
            k += 1
    return p, b


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == block]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    txt = raw.decode('utf-8')
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    lines = txt.replace(term, '\n').split('\n')
    print('行尾=%r 行数=%d' % (term, len(lines)))

    assert not any('下载终态已报ID' in l for l in lines), '已应用过'
    hs = [i for i, l in enumerate(lines) if l == BLOCK_START]
    ha = [i for i, l in enumerate(lines) if l == BLOCK_END_ANCHOR]
    assert len(hs) == 1, '块起始锚点 %d' % len(hs)
    assert len(ha) == 1, '块后锚点 %d' % len(ha)
    s, a = hs[0], ha[0]
    # 块尾 = 锚点之前最近的一个 '}'
    e = None
    for i in range(a - 1, s, -1):
        if lines[i].strip() == '}':
            e = i
            break
    assert e is not None and e > s, '未定位到块尾'
    old = lines[s:e + 1]
    assert any('是否已下载完成' in l for l in old), '旧块内容不符'
    po, bo = depth_delta(old)

    new = [l.strip() for l in NEW_BLOCK.split('\n')]
    # 双倍行距: 每条语句后补空行(注释与其后语句之间也保持一行空行)
    styled = []
    for l in new:
        styled.append('            ' + l if l else '')
        styled.append('')
    styled = styled[:-1]
    pn, bn = depth_delta(styled)
    assert (po, bo) == (pn, bn), '块净额 %s/%s -> %s/%s' % (po, bo, pn, bn)
    out = lines[:s] + styled + lines[e + 1:]
    # 去重变量属于 MCP命令服务器 类(MCP_Server.wsv) —— 事件类里用限定名访问
    out = [l.replace('下载终态已报ID', 'MCP命令服务器.下载终态已报ID') for l in out]

    sraw = open(SERVER, 'rb').read()
    assert not sraw.startswith(b'\xef\xbb\xbf'), 'MCP_Server.wsv 带 BOM'
    stxt = sraw.decode('utf-8').replace('\r\n', '\n')
    assert '下载终态已报ID' not in stxt, '变量已存在'
    slines = stxt.split('\n')
    hv = find_block(slines, [VAR_ANCHOR.strip()])
    assert len(hv) == 1, '变量锚点 %d' % len(hv)
    sout = slines[:hv[0] + 1] + VAR_NEW + slines[hv[0] + 1:]
    assert depth_delta(sout) == depth_delta(slines), 'MCP_Server.wsv 净额变化'
    assert depth_delta(out) == depth_delta(lines), '事件文件净额变化'

    print('块 %d..%d: %d 行 -> %d 行; 变量区 +%d 行; 事件文件 %d -> %d 行; MCP_Server %d -> %d 行'
          % (s + 1, e + 1, len(old), len(styled), len(VAR_NEW), len(lines), len(out),
             len(slines), len(sout)))
    if '--apply' in sys.argv:
        outw = '\n'.join(out).replace('\n', term)
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(outw)
        with io.open(SERVER, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sout))
        back = open(TARGET, 'rb').read().decode('utf-8')
        back2 = open(SERVER, 'rb').read().decode('utf-8')
        assert back == outw and back2 == '\n'.join(sout), '写盘校验失败'
        print('已写入 %s 与 %s' % (TARGET, SERVER))
    else:
        print('[dry-run] 未落盘')


main()
