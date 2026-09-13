# -*- coding: utf-8 -*-
"""按 browser_get_frames 的真实输出形态对齐参数名。

实测 browser_get_frames 回包是:
  {"success":true,"frames":[{"id":"6-FEB5…","name":"","is_main":true}, …]}
标识字段叫 **id**, 而新工具要的是 **frame_id** —— 调用方要"猜"字段名, 属零前置摩擦。
故: `frame_id` 优先, 兼容 `id`; 描述里点明取值来自 browser_get_frames 的 id 字段。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '按ID取框架参数对齐-写入前')
problems = []


def rep(text, old, new, tag, nl='\n'):
    o = old.replace('\n', nl)
    if text.count(o) != 1:
        problems.append('%s: 命中 %d 次' % (tag, text.count(o)))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号' % tag)
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), 1)


c = open(os.path.join(SRC, 'MCP_Server_Core.wsv'), 'rb').read().decode('utf-8')
nl2 = '\r\n' if '\r\n' in c else '\n'
c = rep(c, '''                变量 frameId <类型 = 文本型>
                frameId = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                如果 (frameId == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "frame_id " + MCP_常量.错误_缺少参数 + " | 框架ID 可从 browser_get_frames 取得"))
                }
''', '''                变量 frameId <类型 = 文本型>
                frameId = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                如果 (frameId == "")
                {
                    // browser_get_frames 回包里的字段名是 id(不是 frame_id), 这里兼容, 免得调用方还要猜
                    frameId = MCP命令服务器.yyjson取文本 (参数JSON, "id")
                }
                如果 (frameId == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "frame_id " + MCP_常量.错误_缺少参数 + " | 框架ID 取自 browser_get_frames 回包里的 id 字段(两处都接受 frame_id 与 id)"))
                }
''', 'Core frame_by_id 兼容 id', nl2)
os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, 'MCP_Server_Core.wsv')
if not os.path.exists(dst):
    shutil.copy2(os.path.join(SRC, 'MCP_Server_Core.wsv'), dst)
open(os.path.join(SRC, 'MCP_Server_Core.wsv'), 'wb').write(c.encode('utf-8'))

s = open(os.path.join(SRC, 'MCP_Server.wsv'), 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in s else '\n'
s = rep(s, '单参数Schema文本 ("frame_id", "text", "框架ID(取自 browser_get_frames)"))',
        '多属性Schema文本 (属性项JSON ("frame_id", "text", "框架ID(browser_get_frames 回包里的 id 字段)") + "," + '
        '属性项JSON ("id", "text", "同上, 兼容 browser_get_frames 的字段名"), "\\"frame_id\\""))',
        'Server frame_by_id schema 兼容 id', nl)
open(os.path.join(SRC, 'MCP_Server.wsv'), 'wb').write(s.encode('utf-8'))

print('问题: %r' % problems)
sys.exit(1 if problems else 0)
