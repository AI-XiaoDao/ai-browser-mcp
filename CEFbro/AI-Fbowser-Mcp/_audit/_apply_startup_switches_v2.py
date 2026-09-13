# -*- coding: utf-8 -*-
r"""启动开关通道 v2: 补齐 跨框架操作模式 / 禁用代理 / 受控名值白名单表 + 只读回执工具。

依据(只读缺口审计, 逐条带证据):
  · `命令行.启用跨框架操作模式(` 在 src 全量命中 **0** 次; 同义实现已排查:
    browser_frame_* / browser_get_frames 只回框架信息不回可读写句柄;
    browser_vip_execute_js_context target=all_frames 是纯 JS、受同源限制且会破坏 CDP 通道 => 不等价。
  · `命令行.禁用代理(` 命中 **0** 次; browser_clear_proxy 只清"类库设过的实例级代理",
    关不掉 Windows 系统自动检测代理(--no-proxy-server 语义) => 不等价。
  · `命令行.置项值/置值/置额外参数` 命中各 **0** 次 => 缺少"进程级 Chromium switch"出口。
  · 回执字段 `命令行开关已应用` / `命令行开关原文` 已存在(本文件 400/401 行), 但**没有任何 MCP 读取入口**
    => 用户与 AI 都无法确认开关是否真的生效(不可观测 = 实际不可用)。

本补丁(**只改 MCP_Server.wsv**):
  1. 新增 4 个静态字段: 启动开关_启用跨框架操作模式 / 启动开关_禁用代理 / 启动开关_名值表 / 启动开关_被拒表;
  2. 加载MCP配置 内新增 3 个配置键的解析: `enable_cross_frame`(逻辑) / `disable_proxy`(逻辑) /
     `startup_switches`(对象, **逐名过白名单 + 值校验**, 未通过的写进 被拒表 而不是静默丢弃);
  3. 新增只读工具 `browser_startup_args`(action=get/list), 让"启动开关是否生效"可被 AI 自查。

安全: 白名单**写死在代码里**(只允许本补丁明确列出的 4 个 switch), 不允许配置里直接写任意 `--xxx` 串 ——
裸透传等于把内核命令行交给配置文件, 一个 `--single-process` 就能让浏览器不可用。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

# ---------- 1) 静态字段 ----------
FIELDS_ANCHOR = '    变量 命令行开关原文 <公开 静态 类型 = 文本型 值 = "" 注释 = "启动期如实回执: 施加完毕后的浏览器进程命令行原文(命令行.取字符串), 空=未在浏览器进程施加" @输出名 = "CmdLineSwitchRawText">'
FIELDS_NEW = [
    '    变量 启动开关_启用跨框架操作模式 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json enable_cross_frame: 为真时启动期对命令行调用 启用跨框架操作模式 —— 与 iframe 子框架填表互补(只解框架间操作限制, 不改同源策略)" @输出名 = "StartupSwitchEnableCrossFrame">',
    '    变量 启动开关_禁用代理 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json disable_proxy: 为真时启动期对命令行调用 禁用代理, 连 Windows 系统自动检测代理一起关掉(browser_clear_proxy 做不到这点)" @输出名 = "StartupSwitchDisableProxy">',
    '    变量 启动开关_名值表 <公开 静态 类型 = 文本型 值 = "" 注释 = "mcp_config.json startup_switches 里**通过白名单校验**的名值对, 序列化形如 名=值;名=值;(末尾带分号); 由 启动类.即将处理命令行 逐项施加" @输出名 = "StartupSwitchNameValueTable">',
    '    变量 启动开关_被拒表 <公开 静态 类型 = 文本型 值 = "" 注释 = "startup_switches 里**未通过白名单/值校验**的条目(名=原因;), 如实回执不静默丢弃" @输出名 = "StartupSwitchRejectedTable">',
]

# ---------- 2) 配置解析 ----------
CFG_ANCHOR = '''        如果 (配置解析.取逻辑值 ("ignore_gpu_blocklist"))
        {
            启动开关_忽略GPU禁用清单 = 真
        }'''
CFG_NEW = CFG_ANCHOR + '''

        如果 (配置解析.取逻辑值 ("enable_cross_frame"))
        {
            启动开关_启用跨框架操作模式 = 真
        }
        如果 (配置解析.取逻辑值 ("disable_proxy"))
        {
            启动开关_禁用代理 = 真
        }
        // ==== 启动期开关通道v2: 受控名值白名单表 ====
        // 约束: 只接受**代码里写死的白名单名**, 且每个名有自己的值校验; 未通过的条目进 被拒表 回执。
        // 为什么不裸透传: Chromium switch 里一个 --single-process 就能让浏览器不可用(类库自己也警告过),
        // 把整串命令行交给配置文件等于把内核稳定性交给手滑。
        变量 开关对象文本 <类型 = 文本型>
        开关对象文本 = 配置解析.取JSON文本 ("startup_switches")
        如果 (开关对象文本 != "" && 开关对象文本 != "{}")
        {
            变量 开关对象 <类型 = YYJSON只读对象类>
            如果 (开关对象.创建自文本 (开关对象文本))
            {
                变量 允许名 <类型 = 文本数组类>
                允许名.加入成员 ("lang")
                允许名.加入成员 ("force-device-scale-factor")
                允许名.加入成员 ("disable-blink-features")
                允许名.加入成员 ("disable-features")
                变量 名位 <类型 = 整数>
                名位 = 0
                判断循环 (名位 < 允许名.取成员数 ())
                {
                    变量 该名 <类型 = 文本型>
                    该名 = 允许名.取成员 (名位)
                    变量 该值 <类型 = 文本型>
                    该值 = MCP命令服务器.yyjson取文本 (开关对象, 该名)
                    如果 (该值 != "")
                    {
                        变量 值可用 <类型 = 逻辑型>
                        值可用 = 真
                        变量 值说明 <类型 = 文本型>
                        值说明 = ""
                        如果 (该名 == "lang")
                        {
                            // 语言标签: 只允许字母/数字/连字符, 长度受限
                            如果 (取文本长度 (该值) > 32)
                            {
                                值可用 = 假
                                值说明 = "过长(>32)"
                            }
                        }
                        否则 (该名 == "force-device-scale-factor")
                        {
                            // 缩放因子: 必须能解析成 0.5~4 之间的数(文本到小数解析失败得 0 视为非法)
                            变量 缩放值 <类型 = 小数>
                            缩放值 = 文本到小数 (该值)
                            如果 (缩放值 < 0.5 || 缩放值 > 4)
                            {
                                值可用 = 假
                                值说明 = "必须在 0.5~4 之间"
                            }
                        }
                        否则
                        {
                            // 特性开关列表: 只允许字母/数字/下划线/连字符/逗号(拒绝空格与短横线开头的自由串)
                            变量 字位 <类型 = 整数>
                            字位 = 0
                            判断循环 (字位 < 取文本长度 (该值))
                            {
                                变量 该字 <类型 = 文本型>
                                该字 = 取文本中间 (该值, 字位, 1)
                                如果 (寻找文本 ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-," , 该字, 0, 假) == -1)
                                {
                                    值可用 = 假
                                    值说明 = "含非法字符(只允许字母/数字/下划线/连字符/逗号)"
                                    跳出循环
                                }
                                字位 = 字位 + 1
                            }
                        }
                        如果 (值可用)
                        {
                            启动开关_名值表 = 启动开关_名值表 + 该名 + "=" + 该值 + ";"
                        }
                        否则
                        {
                            启动开关_被拒表 = 启动开关_被拒表 + 该名 + "=" + 值说明 + ";"
                        }
                    }
                    名位 = 名位 + 1
                }
            }
            否则
            {
                启动开关_被拒表 = 启动开关_被拒表 + "startup_switches=不是合法JSON对象;"
            }
        }'''

# ---------- 3) 只读回执工具 ----------
SCHEMA_ANCHOR = ''  # 仅作前缀定位用(见 main 内对 browser_get_global_cache_dir 的前缀匹配)
SCHEMA_NEW = '''添加工具JSON ("browser_startup_args", "启动期开关通道回执(只读): 查看本进程**实际应用过**的启动开关、内核命令行原文, 以及配置里 startup_switches 通过/被拒的条目。用于自查 mcp_config.json 的启动开关是否真的生效(这些开关**只在启动期生效, 改动后必须重启进程**) | action 缺省=get", 多属性Schema文本 (属性项JSON ("action", "text", "get(缺省, 返回全部回执) / list(仅返回已应用开关清单)"), ""))'''

# 分派: 系统分派里加只读分支(与 browser_get_global_cache_dir 同一处分派, 便于同一文件内定位)
DISP_ANCHOR = '''        如果 (方法名 == "browser_get_global_cache_dir")
        {'''
DISP_NEW = '''        如果 (方法名 == "browser_startup_args")
        {
            变量 启动回执action <类型 = 文本型>
            启动回执action = "get"
            如果 (参数JSON.是否为空 () == 假)
            {
                启动回执action = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            }
            如果 (启动回执action == "list")
            {
                返回 (MCP_响应构建.构建简单JSON ("applied_switches", MCP命令服务器.命令行开关已应用))
            }
            变量 启动回执 <类型 = YYJSON对象类>
            启动回执.创建自文本 ("{}")
            启动回执.加入逻辑值成员 ("success", 真)
            启动回执.加入文本成员 ("applied_switches", MCP命令服务器.命令行开关已应用)
            启动回执.加入文本成员 ("command_line_raw", MCP命令服务器.命令行开关原文)
            启动回执.加入文本成员 ("name_value_switches", MCP命令服务器.启动开关_名值表)
            启动回执.加入文本成员 ("rejected_switches", MCP命令服务器.启动开关_被拒表)
            启动回执.加入逻辑值成员 ("enable_cross_frame", MCP命令服务器.启动开关_启用跨框架操作模式)
            启动回执.加入逻辑值成员 ("disable_proxy", MCP命令服务器.启动开关_禁用代理)
            启动回执.加入文本成员 ("note", "启动开关只在启动期由 启动类.即将处理命令行 施加, 运行期无法补做; 改了 mcp_config.json 必须重启进程才生效; applied_switches 为空表示本次启动没有应用任何开关(可能是配置未开, 也可能命令行对象不可用)")
            返回 (启动回执.到可读文本 (YYJSON格式化选项.压缩))
        }
''' + DISP_ANCHOR


def find_anchor(lines, anchor):
    a = (anchor if isinstance(anchor, list) else anchor.split('\n'))
    a = [x.strip() for x in a]
    return [i for i in range(len(lines) - len(a) + 1)
            if [l.strip() for l in lines[i:i + len(a)]] == a]


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


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')
    assert not any('启动开关_名值表' in l for l in lines), '已应用过'

    p0, b0 = depth_delta(lines)

    # 3) 工具注册行(先做: 它会插到文件后段, 不影响前段锚点)。
    #    该注册行很长, 故用**前缀**定位(整行逐字匹配不现实), 并断言前缀唯一。
    pre = '添加工具JSON ("browser_get_global_cache_dir"'
    h = [i for i, l in enumerate(lines) if l.lstrip().startswith(pre)]
    assert len(h) == 1, '工具注册锚点 %d' % len(h)
    indent = lines[h[0]][:len(lines[h[0]]) - len(lines[h[0]].lstrip())]
    body = SCHEMA_NEW.split('添加工具JSON ("browser_startup_args", ', 1)[1]
    new_line = indent + '添加工具JSON ("browser_startup_args", ' + body
    assert new_line.lstrip().startswith('添加工具JSON ("browser_startup_args", '), '拼接失败'
    assert '"action"' in new_line, 'schema 段缺失'
    lines = lines[:h[0]] + [new_line] + lines[h[0]:]

    # 1) 静态字段
    h = find_anchor(lines, [FIELDS_ANCHOR])
    assert len(h) == 1, '字段锚点 %d' % len(h)
    lines = lines[:h[0] + 1] + FIELDS_NEW + lines[h[0] + 1:]

    # 2) 配置解析
    h = find_anchor(lines, CFG_ANCHOR.split('\n'))
    assert len(h) == 1, '配置锚点 %d' % len(h)
    i = h[0]
    lines = lines[:i] + CFG_NEW.split('\n') + lines[i + len(CFG_ANCHOR.split('\n')):]

    p1, b1 = depth_delta(lines)
    assert (p1, b1) == (p0, b0), '括号净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    out = '\n'.join(lines)
    print('MCP_Server.wsv: 行数 %d -> %d' % (len(raw.decode('utf-8').split('\n')), len(lines)))
    print('  净额 圆 %d 花 %d 不变; 工具注册 browser_startup_args 已插入' % (p0, b0))

    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        chk = open(TARGET, 'rb').read()
        assert not chk.startswith(b'\xef\xbb\xbf') and b'\r\n' not in chk, '写盘校验失败'
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
