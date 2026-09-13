# -*- coding: utf-8 -*-
"""修 browser_reverse_cdp_hook 的参数名: functionObjectId -> objectId。

A/B 实测(同一 objectId, 只换字段名):
  {"objectId": "-6037387049398756694.1.1"}         -> {"breakpointId":"7:1"}          ✔ 接受
  {"functionObjectId": "-6037387049398756694.1.1"} -> Failed to deserialize params.objectId
                                                      - BINDINGS: mandatory field missing at position 51
即源码注释"要求 functionObjectId, 非 objectId"**恰好写反了**。
该错误此前完全不可见: 工具走异步入口, 内核报错也被回成 success(第99轮去掉假成功后才暴露)。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '函数断点参数名-写入前')

OLD_A = '                // CDP Debugger.setBreakpointOnFunctionCall 要求参数名为 functionObjectId, 非 objectId'
NEW_A = ('                // 内核实测(本机 A/B, 只换字段名, 句柄相同):\n'
         '                //   {"objectId": ...}         -> {"breakpointId":"7:1"}                    接受\n'
         '                //   {"functionObjectId": ...} -> Failed to deserialize params.objectId\n'
         '                //                                 - mandatory field missing at position 51\n'
         '                // 即该命令要的就是 **objectId**(原注释"要求 functionObjectId, 非 objectId"恰好写反,\n'
         '                // 而这个参数名错误此前完全不可见 —— 因为工具走异步入口, 内核报错也被回成 success)')
OLD_B = '                chParams.加入文本成员 ("functionObjectId", chObjectId)'
NEW_B = '                chParams.加入文本成员 ("objectId", chObjectId)'


def main():
    data = open(SRC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '不应有BOM'
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s' % ('CRLF' if nl == '\r\n' else 'LF'))
    for sub in (OLD_A, OLD_B):
        c = text.count(sub)
        print('  命中 %d : %s' % (c, sub.strip()[:70]))
        if c != 1:
            print('!! 锚点不唯一, 中止')
            return 1
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Reverse.wsv'))
    text = text.replace(OLD_A, NEW_A.replace('\n', nl)).replace(OLD_B, NEW_B)
    open(SRC, 'wb').write(text.encode('utf-8'))
    print('已写入; 备份 -> %s' % BAK)
    print('复核: 文件里 functionObjectId 出现 %d 次(应为 0)' % text.count('functionObjectId'))
    return 0


sys.exit(main())
