# -*- coding: utf-8 -*-
"""修掉与实现不符的文案(docs 与工具描述), 让"照文档做"与"实际行为"一致。

依据: 子代理 `_audit/_collect_events_fix_r115.md` §4 配套清单 + 本脚本前面打印的**真实原文**。
注意上一轮我把锚点写成 `下载_*`(中文)导致反复不中 —— 真实文本是英文 `download_*`, 这里按实测字符串改。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '文案与实现对齐-写入前')
problems = []


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def rep(text, old, new, tag, nl='\n', n=1):
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != n:
        problems.append('%s: 命中 %d 次(应 %d)' % (tag, c, n))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:90]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), n)


def save(src, text, name):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    open(src, 'wb').write(text.encode('utf-8'))


# ── Core: browser_event 报错文案补 6 个族名(真实锚点用英文 download_*) ──
c, nl2 = load(os.path.join(SRC, 'MCP_Server_Core.wsv'))
c = rep(c, 'download_*/key_press/focus_* | 应用事件: app_*',
        'download_*/key_press/focus_* | 菜单/快捷菜单/导航意图/界面细节: context_menu*/quick_menu*/nav_intent*/ui_* | '
        '插件/启动/渲染/WS: app_extension_*/app_startup_*/app_render_*/app_render_ws_* | 权限/离屏: permission_*/offscreen_* | '
        '应用事件: app_* | 族名可用通配(如 resource_*)',
        'Core browser_event 报错文案补族名', nl2)
save(os.path.join(SRC, 'MCP_Server_Core.wsv'), c, 'MCP_Server_Core.wsv')

# ── Server: 两处过期数字 ──
s, nl = load(os.path.join(SRC, 'MCP_Server.wsv'))
s = rep(s, '一次性打开13项浏览器/应用事件监控(载入/标题/进度/资源/对话框/全屏/图标/查找/框架/下载/焦点/生命周期/应用)并开启控制台与网络详细记录',
        '一次性打开 **26** 个开关(13 事件族 + 3 日志 + 10 扩展族: 含菜单/快捷菜单/导航意图/界面细节/插件/启动/渲染/渲染WS/权限/离屏), '
        '与 browser_collect action=event_all_enable 的集合**完全一致**',
        'Server kernel 工具描述 13->26', nl)
s = rep(s, 'app_enable(原有12族)',
        'app_enable(原有13族)',
        'Server collect 描述 12族->13族', nl)
save(os.path.join(SRC, 'MCP_Server.wsv'), s, 'MCP_Server.wsv')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
