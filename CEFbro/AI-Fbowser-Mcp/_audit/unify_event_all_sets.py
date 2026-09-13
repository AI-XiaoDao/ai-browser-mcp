# -*- coding: utf-8 -*-
"""把三套"全开/全关事件"统一到**同一个 26 项集合**(以 MCP_Kernel 的 enable 分支为唯一来源)。

依据: 子代理 `_audit/_collect_events_fix_r115.md` 逐行计数 ——
  · 内核 `browser_kernel_events_all`: enable 26 / disable 26, 双向对称(基准);
  · `browser_collect event_all_enable`: 仅 11 项, 却回报"全部事件监控已启用";
  · `browser_collect event_all_disable`: 13 项, 比 enable 多关 资源事件/键盘焦点(静默破坏用户单独开的族);
  · 第三处 `关闭全部事件监控`: 14 项。
用户可见后果: 用 collect 开"全部"后, resource_*/key_focus_*/context_menu*/quick_menu*/nav_intent*/ui_*/
permission_*/offscreen_* 以及控制台/网络详细日志等 15 项仍关着; 用 collect 关"全部"后仍有 13 项为真。

做法: 从 MCP_Kernel.wsv 的 enable 分支**提取那 26 个字段名**(唯一来源), 生成三处赋值块;
同时修正四段与实际不符的文案。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '事件全开统一-写入前')
problems = []

# ── 唯一来源: 内核 enable 分支的字段清单 ──
k = open(os.path.join(SRC, 'MCP_Kernel.wsv'), 'rb').read().decode('utf-8')
start = k.find('如果 (动作 == "enable" || 动作 == "")')
end = k.find('全事件流已开启', start)
if start < 0 or end < 0:
    print('!! 内核 enable 分支定位失败')
    sys.exit(1)
FIELDS = re.findall(r'MCP命令服务器\.(是否\S+|是否记录\S+) = 真', k[start:end])
seen = []
for f in FIELDS:
    if f not in seen:
        seen.append(f)
FIELDS = seen
print('唯一来源字段数 = %d' % len(FIELDS))
for f in FIELDS:
    print('   %s' % f)
if len(FIELDS) != 26:
    print('!! 预期 26 项, 实得 %d —— 中止' % len(FIELDS))
    sys.exit(1)


def block(indent, val):
    return "\n".join('%sMCP命令服务器.%s = %s' % (indent, f, val) for f in FIELDS)


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


def save(name, text):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(SRC, name), dst)
    open(os.path.join(SRC, name), 'wb').write(text.encode('utf-8'))


IND = '                '   # Core 里 collect 分支的缩进(16 空格)
# ── Core: connect 两支统一 ──
c, nl2 = load(os.path.join(SRC, 'MCP_Server_Core.wsv'))
old_en = """            否则 (action == "event_all_enable")
            {
                MCP命令服务器.是否监控载入事件 = 真
                MCP命令服务器.是否监控标题改变 = 真
                MCP命令服务器.是否监控加载进度 = 真
                MCP命令服务器.是否监控对话框 = 真
                MCP命令服务器.是否监控全屏 = 真
                MCP命令服务器.是否监控图标 = 真
                MCP命令服务器.是否监控查找 = 真
                MCP命令服务器.是否监控框架 = 真
                MCP命令服务器.是否监控下载事件 = 真
                MCP命令服务器.是否监控生命周期 = 真
                MCP命令服务器.是否监控应用事件 = 真
                返回 (MCP_响应构建.命令成功 (命令ID, "全部事件监控已启用(含应用事件, 已排除 resource/keyboard 高频噪音) | event_log 上限 " + 到文本 (MCP_常量.事件日志最大条目) + " 条"))
            }
"""
new_en = ("""            否则 (action == "event_all_enable")
            {
""" + block(IND, '真') + """
                返回 (MCP_响应构建.命令成功 (命令ID, "全部事件监控已启用(26 项: 13 事件族 + 3 日志 + 10 扩展族, 与 browser_kernel_events_all 的集合**完全一致**) | event_log 上限 " + 到文本 (MCP_常量.事件日志最大条目) + " 条"))
            }
""")
c = rep(c, old_en, new_en, 'Core event_all_enable 统一为 26 项', nl2)

old_dis = """            否则 (action == "event_all_disable")
            {
                MCP命令服务器.是否监控载入事件 = 假
                MCP命令服务器.是否监控标题改变 = 假
                MCP命令服务器.是否监控加载进度 = 假
                MCP命令服务器.是否监控资源事件 = 假
                MCP命令服务器.是否监控对话框 = 假
                MCP命令服务器.是否监控全屏 = 假
                MCP命令服务器.是否监控图标 = 假
                MCP命令服务器.是否监控查找 = 假
                MCP命令服务器.是否监控框架 = 假
                MCP命令服务器.是否监控下载事件 = 假
                MCP命令服务器.是否监控键盘焦点 = 假
                MCP命令服务器.是否监控生命周期 = 假
                MCP命令服务器.是否监控应用事件 = 假
                返回 (MCP_响应构建.命令成功 (命令ID, "全部浏览器事件监控已禁用"))
            }
"""
new_dis = ("""            否则 (action == "event_all_disable")
            {
""" + block(IND, '假') + """
                返回 (MCP_响应构建.命令成功 (命令ID, "全部事件监控已禁用(26 项, 与 event_all_enable 逐项对称)"))
            }
""")
c = rep(c, old_dis, new_dis, 'Core event_all_disable 统一为 26 项', nl2)

# browser_event 报错文案补 6 个族名(此前会让人误以为不支持查)
c = rep(c, '下载_*/key_press/focus_* | 应用事件: app_*',
        '下载_*/key_press/focus_* | 菜单/快捷菜单/导航意图/界面细节: context_menu/quick_menu/nav_intent/ui_* | '
        '插件/启动/渲染: app_extension_*/app_startup_*/app_render_*/app_render_ws_* | 权限/离屏: permission_*/offscreen_* | '
        '应用事件: app_* | 族名可用通配(如 resource_*)',
        'Core browser_event 报错文案补族名', nl2)
save('MCP_Server_Core.wsv', c)

# ── Server: 第三处 关闭全部事件监控 ──
s, nl = load(os.path.join(SRC, 'MCP_Server.wsv'))
old_close = """    方法 关闭全部事件监控 <公开 静态 @输出名 = "CloseAllEventMonitor" @强制输出 = 真>
    {
        是否监控载入事件 = 假
        是否监控标题改变 = 假
        是否监控加载进度 = 假
        是否监控资源事件 = 假
        是否监控对话框 = 假
        是否监控全屏 = 假
        是否监控图标 = 假
        是否监控查找 = 假
        是否监控框架 = 假
        是否监控下载事件 = 假
        是否监控键盘焦点 = 假
        是否监控生命周期 = 假
        是否监控应用事件 = 假
        是否记录控制台 = 假
    }
"""
new_close = ("    方法 关闭全部事件监控 <公开 静态 @输出名 = \"CloseAllEventMonitor\" @强制输出 = 真>\n"
             "    {\n"
             "        // 与 browser_kernel_events_all 的 disable 分支保持同一 26 项集合(此前只有 14 项, 少 12 项),\n"
             "        // 否则关停路径会留下仍为真的监控开关。\n"
             + block('        ', '假') + "\n"
             "    }\n")
s = rep(s, old_close, new_close, 'Server 关闭全部事件监控 对齐为 26 项', nl)
save('MCP_Server.wsv', s)

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
