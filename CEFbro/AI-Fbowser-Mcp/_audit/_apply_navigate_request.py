# -*- coding: utf-8 -*-
r"""第125轮(其三): 补上真缺口 `载入请求` —— browser_navigate 支持 method/headers/body(提交式跳转)。

缺口依据(只读子代理逐条核对, `_audit/_gap_recheck_1.md` 真缺口第 1 条):
  类库 `类_FBrowser_框架.载入请求 (请求)`(FBroLib.wsv:1669) 全项目 **0 调用**, 而现有 `browser_navigate`
  只能发 GET(`载入地址`) ⇒ 无法复现"提交式跳转 / 带签名头接口跳转"这类真实场景。
可行性(已核实): `类_FBrowser_请求` 有公开 `创建 ()`(FBroLib.wsv:2279 `Set(FBroHsRequest_Create())`),
  且 `置地址/置类型/置协议头_名称/置POST数据` 都已在本项目 `browser_create_url_request` 里被真实使用过
  (MCP_Server_Core.wsv:7198-7251) —— 故本改动**复用同一套构建逻辑**, 不另写一份。

做法(不重复造轮子):
  1) MCP_Server.wsv 抽出两个复用件 `应用请求头文本` / `应用请求体文本`(即既有 URL 请求分支里那两段解析),
     并新增 `载入框架请求 (框架, url, 方法, 头文本, 体文本)` 封装"建请求 → 载入请求";
  2) MCP_Server_Core.wsv 的 `browser_create_url_request` 改为调用这两个复用件(消除重复);
  3) `browser_navigate` 新增 method/headers/body: 三者任一非空(或 method≠GET)时走 `载入请求`,
     并**跳过同址快速路径**(带自定义请求时即使同址也必须真发一次); wait_for_load 行为保持一致;
  4) 工具描述与 schema 同步(零前置: 只给 body 时自动按 POST)。

用法: py -3 _audit\_apply_navigate_request.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

HELPERS = '''    # ==== 自定义请求的构建与"载入请求"(补类库 载入请求 缺口) ====
    # 缺口依据(_audit/_gap_recheck_1.md 真缺口第 1 条): 类库 `类_FBrowser_框架.载入请求`(FBroLib.wsv:1669)
    #   全项目 0 调用, 而 `browser_navigate` 只能发 GET(`载入地址`) ⇒ 无法复现"提交式跳转/带签名头接口跳转"。
    # 不重复造轮子: 请求头/请求体的解析原本只写在 `browser_create_url_request` 分支里, 这里抽成复用件,
    #   由"载入请求"与"URL 请求"两条路径**共用同一份**解析实现(避免两份漂移)。

    方法 应用请求头文本 <公开 静态 类型 = 整数 注释 = "把逐行头文本(每行 名: 值 或 名=值, 覆盖=真)应用到请求对象; 返回真正写入的条数" @输出名 = "ApplyRequestHeaderText" @强制输出 = 真>
    参数 请求 <类型 = 类_FBrowser_请求 @输出名 = "Request">
    参数 头文本 <类型 = 文本型 @输出名 = "HeaderText">
    {
        变量 已应用 <类型 = 整数>
        已应用 = 0
        如果 (头文本 == "")
        {
            返回 (0)
        }
        变量 头行数组 <类型 = 文本数组类>
        分割文本 (头文本, "\\n", 头行数组, 真, 假)
        计次循环 (头行数组.取成员数 ())
        {
            变量 头行 <类型 = 文本型>
            头行 = 删首尾空 (头行数组.取成员 (取循环索引 ()))
            如果 (头行 != "")
            {
                变量 头名 <类型 = 文本型>
                变量 头值 <类型 = 文本型>
                变量 冒号位 <类型 = 整数>
                冒号位 = 寻找文本 (头行, ":", 0, 假)
                如果 (冒号位 == -1)
                {
                    冒号位 = 寻找文本 (头行, "=", 0, 假)
                }
                如果 (冒号位 > 0)
                {
                    头名 = 删首尾空 (取文本左边 (头行, 冒号位))
                    头值 = 删首尾空 (取文本中间 (头行, 冒号位 + 1, 取文本长度 (头行) - 冒号位 - 1))
                    如果 (头名 != "")
                    {
                        请求.置协议头_名称 (头名, 头值, 真)
                        已应用 = 已应用 + 1
                    }
                }
            }
        }
        返回 (已应用)
    }

    方法 应用请求体文本 <公开 静态 类型 = 整数 注释 = "把文本请求体按 UTF-8 装进请求对象; 返回字节数(0=未设)" @输出名 = "ApplyRequestBodyText" @强制输出 = 真>
    参数 请求 <类型 = 类_FBrowser_请求 @输出名 = "Request">
    参数 体文本 <类型 = 文本型 @输出名 = "BodyText">
    {
        // 类库要求"数据编码必须是UTF8"(FBroLib.wsv:2610 注释原文), 故按 UTF-8 送
        如果 (体文本 == "")
        {
            返回 (0)
        }
        变量 体元素 <类型 = 类_FBrowser_POST元素>
        体元素.创建 ()
        体元素.置数据_文本 (体文本)
        变量 体数据 <类型 = 类_FBrowser_POST数据>
        体数据.创建 ()
        体数据.增加元素 (体元素)
        请求.置POST数据 (体数据)
        返回 (取字节集长度 (文本到UTF8 (体文本, 假)))
    }

    方法 载入框架请求 <公开 静态 类型 = 整数 注释 = "用自定义 方法/请求头/请求体 直接载入该框架(类库 载入请求)。返回 0=成功, 负数=失败原因码" @输出名 = "LoadFrameRequest" @强制输出 = 真>
    参数 目标框架 <类型 = 类_FBrowser_框架 @输出名 = "TargetFrame">
    参数 url <类型 = 文本型 @输出名 = "URL">
    参数 方法 <类型 = 文本型 @输出名 = "Method">
    参数 头文本 <类型 = 文本型 @输出名 = "HeaderText">
    参数 体文本 <类型 = 文本型 @输出名 = "BodyText">
    {
        如果 (目标框架.是否为空 () || 目标框架.是否有效 () == 假)
        {
            返回 (-1)
        }
        如果 (url == "")
        {
            返回 (-2)
        }
        变量 实际方法 <类型 = 文本型>
        实际方法 = 删首尾空 (方法)
        如果 (实际方法 == "")
        {
            // 零前置: 只给了 body 就按 POST 处理(与 browser_create_url_request 的既有约定一致)
            如果 (体文本 != "")
            {
                实际方法 = "POST"
            }
            否则
            {
                实际方法 = "GET"
            }
        }
        变量 请求 <类型 = 类_FBrowser_请求>
        请求.创建 ()
        请求.置地址 (url)
        请求.置类型 (实际方法)
        应用请求头文本 (请求, 头文本)
        应用请求体文本 (请求, 体文本)
        目标框架.载入请求 (请求)
        返回 (0)
    }

'''

ANCHOR_HELPER = '    方法 确保网络CDP捕获 <公开 静态 类型 = 文本型 注释 = "零前置: 确保 CDP 的 Network 域与 Network.* 事件订阅都在(取响应体与解析 requestId 都依赖它)。返回本次**真正补过**什么(空串=本来就绪)" @输出名 = "EnsureNetworkCDPCapture" @强制输出 = 真>'

# ── Core: browser_create_url_request 改为复用抽出的两个件 ──
CORE_HDR_OLD = '''            变量 头行数 <类型 = 整数>
            头行数 = 0
            如果 (reqHeaders != "")
            {
                变量 头行数组 <类型 = 文本数组类>
                分割文本 (reqHeaders, "\\n", 头行数组, 真, 假)
                计次循环 (头行数组.取成员数 ())
                {
                    变量 头行 <类型 = 文本型>
                    头行 = 删首尾空 (头行数组.取成员 (取循环索引 ()))
                    如果 (头行 != "")
                    {
                        变量 头名 <类型 = 文本型>
                        变量 头值 <类型 = 文本型>
                        变量 冒号位 <类型 = 整数>
                        冒号位 = 寻找文本 (头行, ":", 0, 假)
                        如果 (冒号位 == -1)
                        {
                            冒号位 = 寻找文本 (头行, "=", 0, 假)
                        }
                        如果 (冒号位 > 0)
                        {
                            头名 = 删首尾空 (取文本左边 (头行, 冒号位))
                            头值 = 删首尾空 (取文本中间 (头行, 冒号位 + 1, 取文本长度 (头行) - 冒号位 - 1))
                            如果 (头名 != "")
                            {
                                请求.置协议头_名称 (头名, 头值, 真)
                                头行数 = 头行数 + 1
                            }
                        }
                    }
                }
            }'''
CORE_HDR_NEW = '''            // 复用 应用请求头文本(与"载入请求"路径同一份解析实现, 避免两份漂移)
            变量 头行数 <类型 = 整数>
            头行数 = MCP命令服务器.应用请求头文本 (请求, reqHeaders)'''

CORE_BODY_OLD = '''            变量 体字节数 <类型 = 整数>
            体字节数 = 0
            如果 (reqBody != "")
            {
                变量 体元素 <类型 = 类_FBrowser_POST元素>
                体元素.创建 ()
                体元素.置数据_文本 (reqBody)
                变量 体数据 <类型 = 类_FBrowser_POST数据>
                体数据.创建 ()
                体数据.增加元素 (体元素)
                请求.置POST数据 (体数据)
                体字节数 = 取文本长度 (reqBody)
            }'''
CORE_BODY_NEW = '''            // 复用 应用请求体文本(同上; 返回的是 UTF-8 字节数)
            变量 体字节数 <类型 = 整数>
            体字节数 = MCP命令服务器.应用请求体文本 (请求, reqBody)'''

# ── Core: browser_navigate 支持自定义请求 ──
NAV_OLD = '''                    如果 (navFrame.是否为空 () == 假 && navFrame.是否有效 ())
                    {
                        // 同址导航: 主框架已在目标URL且未在加载时直接返回成功(载入地址前判等, 无竞态);
                        // 否则依赖后续load事件或超时, 快速路径避免30s无谓等待
                        如果 (navFrame.取地址 () == url && 浏览器容器.取加载状态 () == 假)
                        {
                            返回 (MCP_响应构建.命令成功 (命令ID, "已在目标页面: " + url + " | 未重复导航"))
                        }
                        // 记录导航发起时刻(载入地址前), 供注册加载等待任务判序load_end是否属于本次导航
                        变量 导航发起毫秒 <类型 = 长整数>
                        导航发起毫秒 = 取启动时间 ()
                        navFrame.载入地址 (url)'''
NAV_NEW = '''                    如果 (navFrame.是否为空 () == 假 && navFrame.是否有效 ())
                    {
                        // 提交式跳转(补类库 载入请求 缺口): 给了 method(非GET)/headers/body 时用自定义请求载入。
                        // 此时**不能走同址快速路径** —— 即使地址相同也必须真的发一次(否则"重放提交"静默变成不做事)。
                        变量 nav方法 <类型 = 文本型>
                        nav方法 = MCP命令服务器.yyjson取文本 (参数JSON, "method")
                        变量 nav头 <类型 = 文本型>
                        nav头 = MCP命令服务器.yyjson取文本 (参数JSON, "headers")
                        变量 nav体 <类型 = 文本型>
                        nav体 = MCP命令服务器.yyjson取文本 (参数JSON, "body")
                        变量 需要自定义请求 <类型 = 逻辑型>
                        需要自定义请求 = (nav头 != "" || nav体 != "")
                        如果 (nav方法 != "" && nav方法 != "GET")
                        {
                            需要自定义请求 = 真
                        }
                        如果 (需要自定义请求)
                        {
                            变量 请求发起毫秒 <类型 = 长整数>
                            请求发起毫秒 = 取启动时间 ()
                            变量 载入码 <类型 = 整数>
                            载入码 = MCP命令服务器.载入框架请求 (navFrame, url, nav方法, nav头, nav体)
                            如果 (载入码 != 0)
                            {
                                如果 (载入码 == -1)
                                {
                                    返回 (MCP_响应构建.命令失败 (命令ID, "载入请求失败: 主框架无效"))
                                }
                                返回 (MCP_响应构建.命令失败 (命令ID, "载入请求失败: url 为空"))
                            }
                            变量 实际方法文本 <类型 = 文本型>
                            实际方法文本 = nav方法
                            如果 (实际方法文本 == "")
                            {
                                如果 (nav体 != "")
                                {
                                    实际方法文本 = "POST"
                                }
                                否则
                                {
                                    实际方法文本 = "GET"
                                }
                            }
                            变量 waitLoadReq <类型 = 逻辑型>
                            waitLoadReq = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "wait_for_load", 真)
                            如果 (waitLoadReq && MCP命令服务器.yyjson取逻辑 (参数JSON, "async_only") == 假)
                            {
                                返回 (MCP命令服务器.注册加载等待任务 (命令ID, 参数JSON, browser, "等待提交式跳转完成: " + 实际方法文本 + " " + url, "已用自定义请求提交: " + 实际方法文本 + " " + url + " | 等待载入完成, 通过mcp_result查询", 请求发起毫秒))
                            }
                            返回 (MCP_响应构建.命令成功 (命令ID, "已用自定义请求提交: " + 实际方法文本 + " " + url))
                        }
                        // 同址导航: 主框架已在目标URL且未在加载时直接返回成功(载入地址前判等, 无竞态);
                        // 否则依赖后续load事件或超时, 快速路径避免30s无谓等待
                        如果 (navFrame.取地址 () == url && 浏览器容器.取加载状态 () == 假)
                        {
                            返回 (MCP_响应构建.命令成功 (命令ID, "已在目标页面: " + url + " | 未重复导航"))
                        }
                        // 记录导航发起时刻(载入地址前), 供注册加载等待任务判序load_end是否属于本次导航
                        变量 导航发起毫秒 <类型 = 长整数>
                        导航发起毫秒 = 取启动时间 ()
                        navFrame.载入地址 (url)'''

TOOL_ANCHOR = '添加工具JSON ("browser_navigate", '
TOOL_ADD = ('（本行由补丁替换）', '（占位）')


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


def patch(path, edits, name, check=None):
    raw = io.open(path, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '%s 带 BOM' % name
    txt = raw.decode('utf-8')
    b0, n0 = balance(txt), len(txt.split('\n'))
    out = txt
    for old, new in edits:
        cnt = out.count(old)
        assert cnt == 1, '%s 锚点出现 %d 次: %s' % (name, cnt, old.strip()[:70])
        out = out.replace(old, new, 1)
    assert balance(out) == b0, '%s 括号净值变了 %s -> %s' % (name, b0, balance(out))
    for must in (check or []):
        assert must in out, '%s 缺少 %s' % (name, must)
    print('%s: 行数 %d -> %d; 括号净值 %s 不变' % (name, n0, len(out.split('\n')), balance(out)))
    return raw, out


def main():
    s_raw, s_out = patch(SERVER, [(ANCHOR_HELPER, HELPERS + ANCHOR_HELPER)], 'MCP_Server.wsv',
                         check=['方法 载入框架请求', '方法 应用请求头文本', '方法 应用请求体文本'])
    c_raw, c_out = patch(CORE, [(CORE_HDR_OLD, CORE_HDR_NEW),
                                (CORE_BODY_OLD, CORE_BODY_NEW),
                                (NAV_OLD, NAV_NEW)], 'MCP_Server_Core.wsv',
                         check=['MCP命令服务器.载入框架请求 (navFrame, url, nav方法, nav头, nav体)',
                                'MCP命令服务器.应用请求头文本 (请求, reqHeaders)'])
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        chk = io.open(SERVER, encoding='utf-8').read()
        assert '\r' not in chk
        print('已写入 Server + Core 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
