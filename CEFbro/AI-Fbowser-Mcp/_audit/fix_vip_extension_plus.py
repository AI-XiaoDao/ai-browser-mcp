# -*- coding: utf-8 -*-
"""VIP P0: 插件高级功能开关(默认 CEF **不执行**插件 content_scripts.js)。

依据(上一轮子代理审计 `_audit/_gap_vip_r114.md` P0 项 + 类库原文):
  `FBroVip.wsv:109` `FBrowser_VIP功能_启用插件高级功能` 注释原文 ——
  "必须在加载插件前启用，启用插件的高级功能，默认CEF不支持插件content_scripts.js脚本执行，
   启用高级功能后才能支持"；而全库该开关 **0 命中**，插件三件套(装载/卸载/查询)却已交付
  ⇒ 现状是"能装插件、但插件的 content scripts 不执行，且**没有任何报错**"。

本脚本:
 ① `main.wsv`: 在最早的可调用点(强制 VIP 标志之后、`FBrowser_初始化` 之前)调用一次;
 ② `MCP_Server.wsv`: 新增可观测静态标志 `VIP_插件高级功能已启用`; 工具描述更新, 并把
    `browser_vip_load_extension` 扩展为支持"已解压插件目录"(`VIP_高级_载入插件路径`, FBroLib.wsv:2075,
    类库原文: CRX 安装效率低于载入解压目录, 且概率性出现"页面已打开但插件未装完");
 ③ `MCP_Server_VIP.wsv`: 加载分支内再次幂等确保开关已开, 并如实回报 advanced_enabled / mode。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'VIP插件高级功能-写入前')
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


def save(name, text):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(SRC, name), dst)
    open(os.path.join(SRC, name), 'wb').write(text.encode('utf-8'))


# ─────────── ① main.wsv: 启动期启用 ───────────
m, nl = load(os.path.join(SRC, 'main.wsv'))
m = rep(m, '''        // 免VIP: 强制解锁类库VIP门控标志 (FBrowser初始化控制.是否为VIP 为类库公开静态变量, 成品对所有用户开放全部功能)
        FBrowser初始化控制.是否为VIP = 真
''', '''        // 免VIP: 强制解锁类库VIP门控标志 (FBrowser初始化控制.是否为VIP 为类库公开静态变量, 成品对所有用户开放全部功能)
        FBrowser初始化控制.是否为VIP = 真
        // 插件高级功能: 类库原文要求"必须在加载插件前启用", 否则插件的 content_scripts.js **不执行**
        // (默认 CEF 不支持), 且不会有任何报错 —— 属"已交付功能静默不工作"。此处是进程内最早的可调用点
        // (早于 FBrowser_初始化, 因此也早于任何请求环境/插件加载)。
        FBrowser_VIP功能_启用插件高级功能 ()
        MCP命令服务器.VIP_插件高级功能已启用 = 真
''', 'main.wsv 启动期启用插件高级功能', nl)
save('main.wsv', m)

# ─────────── ② Server: 可观测标志 + 描述/schema ───────────
s, nl2 = load(os.path.join(SRC, 'MCP_Server.wsv'))
s = rep(s, '    变量 VIP_JS环境已启用 <公开 静态 类型 = 逻辑型 值 = 假 @输出名 = "VipJSEnvEnabled">\n',
        '    变量 VIP_JS环境已启用 <公开 静态 类型 = 逻辑型 值 = 假 @输出名 = "VipJSEnvEnabled">\n'
        '    # 插件高级功能开关是否已启用(类库要求必须在加载插件前启用; 未启用时插件 content_scripts.js 不执行且无报错)\n'
        '    变量 VIP_插件高级功能已启用 <公开 静态 类型 = 逻辑型 值 = 假 @输出名 = "VipExtensionPlusEnabled">\n',
        'Server 新增 VIP_插件高级功能已启用', nl2)

s = rep(s, '         添加工具JSON ("browser_vip_load_extension", "VIP: 加载CRX插件包", 单参数Schema文本 ("crx_path", "text", "CRX文件路径"))\n',
        '         添加工具JSON ("browser_vip_load_extension", "VIP: 加载插件。'
        '两种形态: path=**已解压插件目录**(类库原文: 比 CRX 安装效率高, 推荐) 或 crx_path=.crx 插件包'
        '(类库原文: 概率性出现页面已打开但插件未装完, 装完刷新页面即生效)。'
        '两者给其一即可。回包 advanced_enabled 表示插件高级功能开关是否已开 —— '
        '类库原文: 默认 CEF **不支持**插件 content_scripts.js 执行, 必须在本开关启用后才支持, 且本开关必须在'
        '加载插件前启用(本服务已在进程启动时自动开启并幂等补开)", '
        '多属性Schema文本 (属性项JSON ("path", "text", "已解压插件目录(与 crx_path 二选一)") + "," + '
        '属性项JSON ("crx_path", "text", "CRX 插件包完整路径(与 path 二选一)"), ""))\n',
        'Server load_extension 描述与 schema', nl2)
save('MCP_Server.wsv', s)

# ─────────── ③ VIP: 加载分支 ───────────
v, nl3 = load(os.path.join(SRC, 'MCP_Server_VIP.wsv'))
v = rep(v, '''        否则 (方法名 == "browser_vip_load_extension")
        {
            变量 extCRX <类型 = 文本型>
            extCRX = MCP命令服务器.yyjson取文本 (参数JSON, "crx_path")
            如果 (extCRX != "")
            {
                如果 (MCP命令服务器.验证安全路径 (extCRX) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "路径不允许: " + extCRX + " | 仅允许运行目录内及无 .. 的路径"))
                }
                变量 reqEnv <类型 = 类_FBrowser_请求环境>
                reqEnv = MCP命令服务器.取请求环境_安全 ()
                如果 (reqEnv.是否为空 () == 假)
                {
                    reqEnv.VIP_高级_安装CRX插件包 (extCRX)
                    返回 (MCP_响应构建.命令成功 (命令ID, "CRX插件包已提交安装: " + extCRX))
                }
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_请求环境不可用))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "需要crx_path参数"))
        }
''', '''        否则 (方法名 == "browser_vip_load_extension")
        {
            变量 extCRX <类型 = 文本型>
            extCRX = MCP命令服务器.yyjson取文本 (参数JSON, "crx_path")
            变量 ext目录 <类型 = 文本型>
            ext目录 = MCP命令服务器.yyjson取文本 (参数JSON, "path")
            如果 (extCRX == "" && ext目录 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "需要 path(已解压插件目录) 或 crx_path(.crx 插件包) 之一 | 类库原文: 载入解压目录效率高于 CRX 安装, 且 CRX 会概率性出现「页面已打开但插件未装完」(装完刷新即生效)"))
            }
            // 插件高级功能: 类库要求"必须在加载插件前启用", 否则插件 content_scripts.js 不执行且**无任何报错**。
            // 进程启动时(main.wsv)已开启一次; 这里再幂等确保, 并如实回报开关状态。
            如果 (MCP命令服务器.VIP_插件高级功能已启用 == 假)
            {
                FBrowser_VIP功能_启用插件高级功能 ()
                MCP命令服务器.VIP_插件高级功能已启用 = 真
            }
            如果 (ext目录 != "")
            {
                如果 (MCP命令服务器.验证安全路径 (ext目录) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "路径不允许: " + ext目录 + " | 仅允许运行目录内及无 .. 的路径"))
                }
                变量 reqEnvU <类型 = 类_FBrowser_请求环境>
                reqEnvU = MCP命令服务器.取请求环境_安全 ()
                如果 (reqEnvU.是否为空 () == 真)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_请求环境不可用))
                }
                reqEnvU.VIP_高级_载入插件路径 (ext目录)
                返回 (MCP_响应构建.命令成功 (命令ID, "已提交载入插件目录: " + ext目录 + " | mode=unpacked | advanced_enabled=true | 类库为异步载入, 若页面已打开请 browser_reload 后再验证 content_scripts 是否生效"))
            }
            如果 (MCP命令服务器.验证安全路径 (extCRX) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "路径不允许: " + extCRX + " | 仅允许运行目录内及无 .. 的路径"))
            }
            变量 reqEnv <类型 = 类_FBrowser_请求环境>
            reqEnv = MCP命令服务器.取请求环境_安全 ()
            如果 (reqEnv.是否为空 () == 真)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_请求环境不可用))
            }
            reqEnv.VIP_高级_安装CRX插件包 (extCRX)
            返回 (MCP_响应构建.命令成功 (命令ID, "CRX插件包已提交安装: " + extCRX + " | mode=crx | advanced_enabled=true | 类库原文: CRX 安装较慢, 可能页面已打开而插件未装完, 装完 browser_reload 即生效"))
        }
''', 'VIP 加载分支: 幂等开关 + 解压目录', nl3)
save('MCP_Server_VIP.wsv', v)

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
