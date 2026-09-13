# -*- coding: utf-8 -*-
# TEMP read-only audit helper #2: synonym sweep. Does NOT modify any source file.
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\src'
files = [os.path.join(SRC, n) for n in os.listdir(SRC)
         if n.endswith('.wsv') and '~vbak' not in n]

def read(p):
    b = open(p, 'rb').read()
    return b.decode('utf-16-le', 'replace') if b[:2] == b'\xff\xfe' else b.decode('utf-8', 'replace')

docs = {}
for p in files:
    docs[os.path.basename(p)] = read(p).split('\n')

GROUPS = {
 '1 DPI':                ['\\bDPI\\b', 'DpiAware', 'SetProcessDPI', '感知模式', '设置程序DPI'],
 '2 V8堆栈':             ['V8', '堆栈', 'HeapSize', 'FBroSetV8', '环境默认堆栈'],
 '3 尝试关闭':           ['尝试关闭', '询问关闭', '即将关闭', 'beforeunload', 'close_try', '能否关闭'],
 '4 运行风格':           ['RuntimeStyle', 'runtime_style', '运行风格', '设置运行风格'],
 '5 数据URI':            ['DataURI', 'datauri', '数据URI', '取数据URI', 'data:'],
 '6 JS交互/Query':       ['JS交互', 'cefQuery', 'doQuery', 'QueryFunctions', '查询函数'],
 '7 IPC到主进程':        ['到主进程', '发送数据到主', 'ipc_send', '收到主进程消息'],
 '8 打开对话框':         ['打开对话框', 'RunFileDialog', '文件对话框', 'file_dialog'],
 '9 触摸':               ['触摸', 'TouchEvent', 'dispatchTouchEvent'],
 '10 序号取浏览器':      ['序号', '下标', 'ordinal', '按序号'],
 '11 焦点填表框架':      ['焦点填表', 'GetFocusedFrame', '取焦点填表框架'],
 '12 离屏渲染':          ['离屏', '\\bOSR\\b', 'windowless', '离屏渲染'],
 '13 消息循环':          ['消息循环', 'DoMessageLoopWork', 'RunMessageLoop', 'ModalLoop'],
 '14 调试提示':          ['自带调试提示', '调试信息显示', '调试提示'],
 '15 守护/内存释放线程': ['设置守护', '设置内存释放', '守护线程', '内存释放线程'],
 '16 同步创建':          ['创建浏览器_同步', '创建后台浏览器_同步', '任务运行器', '投递任务'],
 '17 JSON写入':          ['写入JSON', '字节值解析为JSON', 'yyjson', 'YYJSON'],
 '18 异常收集':          ['启用异常收集', '异常收集', '异常回调'],
 '19 窗口句柄取浏览器':  ['通过窗口句柄取浏览器'],
 '20 清理全局缓存':      ['清理全局缓存', 'clear_global_cache'],
}

for gname, pats in GROUPS.items():
    print('\n########', gname)
    for pat in pats:
        rx = re.compile(pat)
        hits = []
        for fn, lines in docs.items():
            for i, L in enumerate(lines, 1):
                if rx.search(L):
                    hits.append((fn, i, L.strip()))
        print('  %-24s total=%-4d' % (pat, len(hits)))
        for fn, i, t in hits[:5]:
            print('        %s:%d  %s' % (fn, i, t[:130]))
        if len(hits) > 5:
            print('        ... (%d more)' % (len(hits) - 5))
