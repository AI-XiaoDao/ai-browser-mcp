# -*- coding: utf-8 -*-
"""试验: 在 FBrowser_初始化 **之前** 注册 JS 查询函数名, 看 router 是否就会生效。

依据: 第111轮实测 —— 运行期(浏览器已建好)注册后, 页面里 `window.mcpQuery` 刷新后仍是 undefined,
连默认名 `cefQuery` 也不存在; 而类库自带例子是**先注册再创建浏览器**(main3.wsv:45-46 -> :113)。
故把注册挪到 main.wsv 启动流程的 FBrowser_初始化 之前试一次。
若仍不行 -> 该通道在本应用不可用, 应**撤掉工具**(不留"声明有、实际不可用"的能力)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'main.wsv')
BAK = os.path.join(ROOT, '备份', 'JS查询启动期注册-写入前')

text = io.open(SRC, encoding='utf-8').read()
nl = '\r\n' if '\r\n' in text else '\n'
print('main.wsv 换行=%s' % ('CRLF' if nl == '\r\n' else 'LF'))

OLD = ('        变量 初始化事件 <类型 = 类_FBrowser_事件智能指针>' + nl +
       '        初始化事件.创建 (类_MCP_初始化事件)' + nl)
NEW = ('        // 非 CDP 的 JS<->宿主查询通道(CEF message router): **必须**在 FBrowser_初始化/创建浏览器之前注册。' + nl +
       '        // 第111轮实测: 运行期(浏览器已存在)注册后, 页面里连默认名 cefQuery 都不存在, 刷新也没用;' + nl +
       '        // 而类库例子是先注册再创建浏览器 -> 故在此处注册默认函数名 mcpQuery。' + nl +
       '        MCP命令服务器.JS查询注册名文本 = "mcpQuery"' + nl +
       '        MCP命令服务器.JS查询事件指针.创建 (类_MCP_JS交互事件)' + nl +
       '        FBrowser_JS交互_注册 ("mcpQuery", "", MCP命令服务器.JS查询事件指针)' + nl +
       OLD)

c = text.count(OLD)
print('锚点命中 %d (应为1)' % c)
if c != 1:
    print('!! 中止')
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'main.wsv'))
open(SRC, 'wb').write(text.replace(OLD, NEW, 1).encode('utf-8'))
print('已写入; 备份 -> %s' % BAK)
