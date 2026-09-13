# -*- coding: utf-8 -*-
r"""控制台输出 双写补丁: ① 控制台窗口实时可见(用户调试期现场看) ② 同内容追加
exe 目录下 mcp_console.log 供审计脚本核对日志证据。

改动文件: src/MCP_Server_Utils.wsv (CRLF 主导, 字节级插入, 锚点唯一性校验)
锚点: 嵌入C++块尾部  @     fflush(stderr);\r\n 与  @ }\r\n 之间插入双写段。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'src', 'MCP_Server_Utils.wsv')

raw = io.open(F, 'rb').read()

ANCHOR = ('        @     fflush(stderr);\r\n'
          '        @ }\r\n').encode('utf-8')
n = raw.count(ANCHOR)
if n != 1:
    print('!! 锚点出现 %d 次(应为1), 中止' % n)
    sys.exit(2)

INSERT = (
    '        @     // 调试期双写: 控制台窗口实时可见(现场看日志), 同内容追加到 exe 目录下\r\n'
    '        @     // mcp_console.log 供审计脚本边写边读核对日志证据(发布成品可去掉此段)\r\n'
    '        @     static HANDLE s_log = INVALID_HANDLE_VALUE;\r\n'
    '        @     if (s_log == INVALID_HANDLE_VALUE) {\r\n'
    '        @         wchar_t path[300] = {0};\r\n'
    '        @         DWORD n2 = GetModuleFileNameW(NULL, path, 260);\r\n'
    '        @         if (n2 > 0 && n2 < 260) {\r\n'
    '        @             for (int i = (int)n2 - 1; i >= 0; i--) { if (path[i] == L\'\\\\\') { path[i + 1] = 0; break; } }\r\n'
    '        @             lstrcatW(path, L"mcp_console.log");\r\n'
    '        @             WIN32_FILE_ATTRIBUTE_DATA fa;\r\n'
    '        @             if (GetFileAttributesExW(path, GetFileExInfoStandard, &fa) && fa.nFileSizeHigh == 0 && fa.nFileSizeLow > 16 * 1024 * 1024) DeleteFileW(path);\r\n'
    '        @         }\r\n'
    '        @         s_log = CreateFileW(path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);\r\n'
    '        @     }\r\n'
    '        @     if (s_log != INVALID_HANDLE_VALUE) {\r\n'
    '        @         DWORD w2 = 0;\r\n'
    '        @         WriteFile(s_log, out.data(), (DWORD)out.size(), &w2, NULL);\r\n'
    '        @         FlushFileBuffers(s_log);\r\n'
    '        @     }\r\n'
).encode('utf-8')

head = ('        @     fflush(stderr);\r\n').encode('utf-8')
pos = raw.find(head)
if pos < 0:
    print('!! fflush 行未找到, 中止')
    sys.exit(2)
pos += len(head)

out = raw[:pos] + INSERT + raw[pos:]
io.open(F, 'wb').write(out)
print('已插入 %d 行双写段到 MCP_Server_Utils.wsv' % INSERT.count(b'\r\n'))
