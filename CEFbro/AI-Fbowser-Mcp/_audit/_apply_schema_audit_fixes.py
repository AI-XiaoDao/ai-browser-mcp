# -*- coding: utf-8 -*-
r"""第125轮(其四): 按"schema↔实现一致性审计"(只读子代理 `_audit/_schema_audit_B.md`)修正一批**可发现性/诚实性**缺陷。

为什么优先级高: 这类缺陷直接让"AI 代理配置好 MCP 后一次调用成功"落空 ——
  · `MISSING_IN_SCHEMA`: 实现会读的参数**没写进 schema**, 代理根本看不到 ⇒ 只能猜/反复试错
    (最典型: `browser_vip_enable_js_env` 实现读 `confirm`, 而它自己的描述偏偏要求传 confirm:true);
  · `REQUIRED_MISMATCH`: 必填与实现守卫不一致 ⇒ 代理照 schema 调用必被拒;
  · `DESC_PROMISE`: 描述写了与实现相反的事实(如"runtime_style 恒为 0"而实测为 1) ⇒ 误导推理;
  · `browser_vip_fingerprint_ssl` 属**静默假成功**: 未知 tls 值被回退成"不限制"却回 success。

本轮改动(全部在 `MCP_Server.wsv` 的注册行 + 一处 `MCP_Server_VIP.wsv` 实现):
  A browser_vip_enable_js_env      : schema 补 `confirm`(实现真读它) + 描述写清必须显式确认
  B browser_vip_touch_cancel       : schema 由空改为 x/y(实现真读它们; 原来只能按 0,0 取消还回成功)
  C browser_vip_touch_emulation    : 描述写清 enable 缺省=false 会**关闭**已开启的转换(避免静默反向操作)
  D browser_fill_attr_get          : required 去掉 attribute(描述本就写"省略则返回 textContent")
  E browser_fill_attr_set          : required 补 attribute/value(实现硬必填)
  F browser_fill_select            : required 补 value(实现硬必填)
  G browser_set_preference         : required 补 value(实现硬必填)
  H browser_vip_execute_js_context : required 补 code(实现唯一硬必填), 并写明 frame_index 条件必填
  I browser_fingerprint_languages  : 描述写明 languages|reset 二选一
  J browser_vip_mouse_wheel        : 描述写明 delta_x/delta_y 至少给一个(实现即如此)
  K browser_get_global_cache_dir   : 描述改为与实现一致的"真值来源"(类库该 getter 编译不过, 改为按启动开关推导)
  L browser_send_message           : 描述改为与实现一致(主进程路径恒失败, 实际是广播到渲染进程)
  M browser_get_run_style          : 描述去掉"runtime_style 恒为 0"(本机实测=1 谷歌)
  N browser_vip_fingerprint_ssl    : 实现改为**明确拒绝**未知 tls 值(不再静默回退成"不限制"却回成功) + 描述列出支持值

用法: py -3 _audit\_apply_schema_audit_fixes.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')

# (工具名, 旧子串, 新子串, 说明) —— 旧子串必须在**该工具的注册行内**且只出现一次
EDITS = [
    # A 补 confirm(实现真读)
    ("browser_vip_enable_js_env",
     '单参数Schema文本 ("enable", "boolean", "启用/关闭")',
     '多属性Schema文本 (属性项JSON ("enable", "boolean", "启用(true)/关闭(false)") + "," + 属性项JSON ("confirm", "boolean", "true=确认已知风险。**实现会读该参数**: 不传 confirm=true 会被明确拒绝(实测启用后会破坏本会话 CDP/JS 通道, 需重启恢复)"), "")',
     'A 补 confirm 到 schema'),
    ("browser_vip_enable_js_env",
     '"VIP: 启用JS执行环境"',
     '"VIP: 启用JS执行环境 | ⚠ 实测启用后会**破坏本会话的 CDP/JS 通道**(execute_js/dom_query 等退化为超时), 需重启进程恢复 ⇒ 故必须显式传 confirm=true 才执行(见 schema 的 confirm 参数); 不需要 VIP 环境的场景请直接用 browser_execute_js(走 CDP, 无副作用)"',
     'A 描述写清必须显式确认'),
    # B 补 x/y
    ("browser_vip_touch_cancel",
     ', 空Schema文本 ())',
     ', 双XY_Schema文本 ("x", "y", "X坐标(尽量给出; 省略按 0,0 取消, 可能取消到错误的点)", "Y坐标(同上)"))',
     'B 补 x/y 到 schema'),
    # C touch_emulation 的 enable 缺省语义
    ("browser_vip_touch_emulation",
     'enable=false 撤销)"',
     'enable=false 撤销) | ⚠ **enable 缺省视为 false**: 只传 mode(不给 enable)会**关闭**已经开启的鼠标转触摸并回 success —— 要开启请显式传 enable=true"',
     'C 写清 enable 缺省语义'),
    # D attr_get 的 required 去掉 attribute
    ("browser_fill_attr_get",
     '"\\"selector\\",\\"attribute\\""',
     '"\\"selector\\""',
     'D attr_get required 去掉 attribute'),
    # E attr_set 的 required 补 attribute/value
    ("browser_fill_attr_set",
     '"\\"selector\\""',
     '"\\"selector\\",\\"attribute\\",\\"value\\""',
     'E attr_set required 补 attribute/value'),
    # F fill_select 的 required 补 value
    ("browser_fill_select",
     '"\\"selector\\""',
     '"\\"selector\\",\\"value\\""',
     'F fill_select required 补 value'),
    # G set_preference 的 required 补 value
    ("browser_set_preference",
     '"\\"name\\""',
     '"\\"name\\",\\"value\\""',
     'G set_preference required 补 value'),
    # H execute_js_context 的 required 补 code
    ("browser_vip_execute_js_context",
     '属性项JSON ("frame_id", "text", "框架ID(缺省路径用, 与 target 互斥时以 target 优先)"), ""))',
     '属性项JSON ("frame_id", "text", "框架ID(缺省路径用, 与 target 互斥时以 target 优先)"), "\\"code\\""))',
     'H execute_js_context required 补 code'),
    # I languages 二选一
    ("browser_fingerprint_languages",
     '设置后需刷新页面生效"',
     '设置后需刷新页面生效 | ⚠ **languages 与 reset 必须给一个**(都不给会被拒绝; 二者同时给时以 reset 优先)"',
     'I languages 二选一'),
    # J mouse_wheel 至少一个滚动量
    ("browser_vip_mouse_wheel",
     'delta_y为滚动量(正值向下滚)。',
     'delta_y为滚动量(正值向下滚), 两者**至少给一个**(都不给会被明确拒绝, 不会静默滚 0 像素)。',
     'J wheel 至少一个滚动量'),
    # K cache_dir 描述与实现一致
    ("browser_get_global_cache_dir",
     '"获取全局缓存目录路径(CEF用户数据根目录)| 真值取自类库 FBrowser_取初始化缓存目录(); 目录随启动分支变化: --mcp-stdio/--stdio/--headless 下为 CacheData 下的 GlobalData_Stdio, 常驻HTTP下为 CacheData 下的 GlobalData(见 main.wsv 的 是否为Stdio模式 开关) | 旧实现硬编码 GlobalData, stdio 分支下会静默返回错值 | 注意 profile 级缓存(Cache/Cookies/Local Storage)位于该目录下的 Default 子目录"',
     '"获取全局缓存目录路径(CEF用户数据根目录)| **真值来源如实说明**: 本机类库的 FBrowser_取初始化缓存目录() **编译不过**(文档与安装版本不一致), 故实现改为按启动开关推导: --mcp-stdio/--stdio/--headless 下为 CacheData/GlobalData_Stdio, 常驻 HTTP 下为 CacheData/GlobalData(见 main.wsv 的 是否为Stdio模式) —— 回包里的 `cache_dir_source` 字段会说明本次用的哪条推导规则, 不要把它当成类库真值 | 注意 profile 级缓存(Cache/Cookies/Local Storage)位于该目录下的 Default 子目录"',
     'K cache_dir 描述改准'),
    # L send_message 描述与实现一致
    ("browser_send_message",
     '"向主进程发消息"',
     '"向浏览器进程广播消息 | **如实说明**: 主进程路径(类库 向主进程发消息)在本架构下恒失败(控制台程序, 浏览器窗口即程序窗口), 实际发送到**全部渲染进程**; 回包会说明实际送达情况"',
     'L send_message 描述改准'),
    # M run_style 描述去掉错误结论
    ("browser_get_run_style",
     '注意: 本项目创建浏览器时未设置 窗口信息.运行风格, 故 runtime_style 当前恒为 0")',
     '注意: 该值由类库默认给出, **本机实测为 1(谷歌)** —— 旧描述写"恒为 0"已被实测推翻, 请以回包为准")',
     'M run_style 描述改准'),
    # N ssl 描述列出支持值(注册行在 Server, 实现在 VIP —— 两处都要改)
    ("browser_vip_fingerprint_ssl",
     '"VIP: SSL加密套件指纹"',
     '"VIP: SSL加密套件指纹 | tls_min/tls_max 取 0(不限制)/769(TLS1.0)/790(TLS1.1)/791(TLS1.2)/792(TLS1.3), **未知值会被明确拒绝**(此前会被静默回退成不限制却回 success = 假成功); ciphers 为加密套件文本, 留空=不改"',
     'N ssl 描述列出支持值'),
]

VIP_OLD = '''                // 整数→TLS版本枚举映射 (使用 MCP_服务器工具 统一方法)
                tls_min_enum = MCP_服务器工具.整数到TLS版本 (tls_min_int)
                tls_max_enum = MCP_服务器工具.整数到TLS版本 (tls_max_int)'''
VIP_NEW = '''                // ★ 实测缺陷修正: 未知 tls 值原本被 MCP_服务器工具.整数到TLS版本 静默回退成"不限制(TLS版本.空)",
                //   而本工具照样回 success ⇒ 调用方以为"已按指定版本限制", 实际根本没限制(**静默假成功**)。
                //   故这里先做显式校验: 只接受 0(不限制) 与 769/790/791/792, 其它值**明确拒绝**并列出支持值。
                如果 (tls_min_int != 0 && tls_min_int != MCP_常量.TLS指纹_1_0 && tls_min_int != MCP_常量.TLS指纹_1_1 && tls_min_int != MCP_常量.TLS指纹_1_2 && tls_min_int != MCP_常量.TLS指纹_1_3)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "非法 tls_min: " + 到文本 (tls_min_int) + " | 支持: 0(不限制) / 769(TLS1.0) / 790(TLS1.1) / 791(TLS1.2) / 792(TLS1.3); 未知值不会被静默忽略 —— 否则会出现"回 success 但其实没限制"的假成功"))
                }
                如果 (tls_max_int != 0 && tls_max_int != MCP_常量.TLS指纹_1_0 && tls_max_int != MCP_常量.TLS指纹_1_1 && tls_max_int != MCP_常量.TLS指纹_1_2 && tls_max_int != MCP_常量.TLS指纹_1_3)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "非法 tls_max: " + 到文本 (tls_max_int) + " | 支持: 0(不限制) / 769(TLS1.0) / 790(TLS1.1) / 791(TLS1.2) / 792(TLS1.3); 未知值不会被静默忽略"))
                }
                // 整数→TLS版本枚举映射 (使用 MCP_服务器工具 统一方法)
                tls_min_enum = MCP_服务器工具.整数到TLS版本 (tls_min_int)
                tls_max_enum = MCP_服务器工具.整数到TLS版本 (tls_max_int)'''

SSL_DESC_OLD = '"VIP: SSL加密套件指纹"'
SSL_DESC_NEW = ('"VIP: SSL加密套件指纹 | tls_min/tls_max 取 0(不限制)/769(TLS1.0)/790(TLS1.1)/791(TLS1.2)/792(TLS1.3), '
                '**未知值会被明确拒绝**(此前会被静默回退成"不限制"却回 success = 假成功); ciphers 为加密套件文本, 留空=不改"')


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    b0 = balance(txt)
    done = []
    for tool, old, new, tag in EDITS:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d 条' % (tool, len(idx))
        i = idx[0]
        assert new not in lines[i], '%s 已是新文案(幂等)' % tool
        assert lines[i].count(old) == 1, '%s 旧子串出现 %d 次: %s' % (tool, lines[i].count(old), old[:40])
        lines[i] = lines[i].replace(old, new, 1)
        done.append(tag)
    out = '\n'.join(lines)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server.wsv: 行数不变 %d; 完成 %d 项:' % (len(lines), len(done)))
    for d in done:
        print('   · %s' % d)

    vtxt = io.open(VIP, encoding='utf-8').read()
    vb0 = balance(vtxt)
    assert vtxt.count(VIP_OLD) == 1, 'VIP ssl 实现锚点 %d' % vtxt.count(VIP_OLD)
    vout = vtxt.replace(VIP_OLD, VIP_NEW, 1)
    assert balance(vout) == vb0, 'VIP 括号净值变了 %s -> %s' % (vb0, balance(vout))
    print('MCP_Server_VIP.wsv: 已加 tls 值显式校验(未知值明确拒绝); 括号净值 %s 不变' % (vb0,))
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        io.open(VIP, 'w', encoding='utf-8', newline='\n').write(vout)
        c1 = io.open(SERVER, encoding='utf-8').read()
        c2 = io.open(VIP, encoding='utf-8').read()
        assert 'confirm", "boolean"' in c1 and '双XY_Schema文本 ("x", "y"' in c1
        assert '非法 tls_min' in c2
        assert '\r' not in c1
        print('已写入 Server + VIP 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
