# -*- coding: utf-8 -*-
"""修正上一次改动的作用域错误(编译报 2855 行找不到 sPrevUrl)。

火山里"块内声明的变量"作用域限于该块; 我把 sPrevUrl 声明在了 如果{...} 内部,
却在块外(2824 附近的存储语句)使用 -> 编译不过。
修法: 把**声明**提到外层(紧接 sFrame 之后), 块内只保留赋值。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '爬虫错页竞态作用域修正-写入前')

text = io.open(SRC, encoding='utf-8').read()
nl = '\n'

OLD = ('            变量 sFrame <类型 = 类_FBrowser_框架>\n'
       '            sFrame = MCP命令服务器.取安全主框架 (browser)\n'
       '            如果 (sFrame.是否为空 () == 假 && sFrame.是否有效 ())\n'
       '            {\n'
       '                // 记录提交前的页面地址: Phase 0 用它判断"页面是否真的换了"(见下方爬虫状态机)\n'
       '                变量 sPrevUrl <类型 = 文本型>\n'
       '                sPrevUrl = sFrame.取地址 ()\n'
       '                sFrame.载入地址 (sUrl)\n')

NEW = ('            变量 sFrame <类型 = 类_FBrowser_框架>\n'
       '            sFrame = MCP命令服务器.取安全主框架 (browser)\n'
       '            // 声明在外层: 该值后面(存储任务时)还要用, 块内声明会因作用域不可见而编译不过\n'
       '            变量 sPrevUrl <类型 = 文本型>\n'
       '            sPrevUrl = ""\n'
       '            如果 (sFrame.是否为空 () == 假 && sFrame.是否有效 ())\n'
       '            {\n'
       '                // 记录提交前的页面地址: Phase 0 用它判断"页面是否真的换了"(见下方爬虫状态机)\n'
       '                sPrevUrl = sFrame.取地址 ()\n'
       '                sFrame.载入地址 (sUrl)\n')

c = text.count(OLD)
print('锚点命中 %d 次(应为1)' % c)
if c != 1:
    print('!! 中止')
    sys.exit(1)
os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
open(SRC, 'wb').write(text.replace(OLD, NEW, 1).encode('utf-8'))
print('已修正作用域; 备份 -> %s' % BAK)
