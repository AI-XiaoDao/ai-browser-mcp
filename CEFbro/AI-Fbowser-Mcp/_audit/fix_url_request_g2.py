# -*- coding: utf-8 -*-
r"""G2: `browser_create_url_request` 补全(POST 体 / 自定义请求头 / HTTP 状态码回读)。

依据(上一轮只读缺口刷新 `_audit/_gap_refresh_r117.md` G2, 价值"高-中"):
  现实现只用 `请求.置地址` + `请求.置类型`, 于是 ——
    · **发不了 POST 体**(类库有 `类_FBrowser_POST数据`/`类_FBrowser_POST元素`, 见 FBroLib.wsv:2469/2556)
    · **设不了自定义请求头**(类库有 `请求.置协议头_名称 (名, 值, 覆盖)` FBroLib.wsv:2398)
    · **连 HTTP 状态码都不读**: 回调只回 success+body, 404 与 200 在回包里毫无区别
      (类库 `URL请求.取响应 ()` -> `类_FBrowser_响应.取状态/取状态文本/取MIME类型/取字符集`,
       FBroLib.wsv:3019/3031/3045/3059; 另有 `取请求错误码` :5585)

本补丁:
  ① Core 的 `browser_create_url_request` 分支: 新增 `headers`(每行 "名: 值")、`body`;
     有 body 且未显式给 method 时**自动用 POST**;
  ② `类_MCP_URL请求回调.即将完成`: 回包补 `status_code/status_text/mime/charset/http_ok/error_code`;
     `success` 仍表示"请求本身完成"(传输层语义), **另给 `http_ok`** 表示 2xx/3xx —— 不把 404 说成失败,
     但也绝不把 404 说成同 200 一样;
  ③ Server 的工具描述/schema 同步(新增 headers/body 与状态字段说明)。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'URL请求补全-写入前')
problems = []


def count_braces(lines):
    o = c = 0
    for ln in lines:
        if ln.lstrip().startswith(('@', '#', '//')):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        o += body.count('{')
        c += body.count('}')
    return o, c


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def save(p, text, name):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    open(p, 'wb').write(text.encode('utf-8'))


def rep(text, old, new, tag, nl='\n'):
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != 1:
        problems.append('%s: 命中 %d 次(应 1)' % (tag, c))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:90]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), 1)


# ── ① Core: 请求体/请求头 ──
c, nl2 = load(os.path.join(SRC, 'MCP_Server_Core.wsv'))
OLD = '''            变量 reqMethod <类型 = 文本型>
            reqMethod = MCP命令服务器.yyjson取文本 (参数JSON, "method")
            如果 (reqMethod == "")
            {
                reqMethod = "GET"
            }
            变量 请求 <类型 = 类_FBrowser_请求>
            请求.创建 ()
            请求.置地址 (reqURL)
            请求.置类型 (reqMethod)
'''
NEW = '''            变量 reqMethod <类型 = 文本型>
            reqMethod = MCP命令服务器.yyjson取文本 (参数JSON, "method")
            // 请求体与请求头(缺这些就只能发 GET): 有 body 且调用方没显式给 method -> 用 POST
            变量 reqBody <类型 = 文本型>
            reqBody = MCP命令服务器.yyjson取文本 (参数JSON, "body")
            如果 (reqBody != "" && MCP命令服务器.参数键存在 (参数JSON, "method") == 假)
            {
                reqMethod = "POST"
            }
            如果 (reqMethod == "")
            {
                reqMethod = "GET"
            }
            变量 请求 <类型 = 类_FBrowser_请求>
            请求.创建 ()
            请求.置地址 (reqURL)
            请求.置类型 (reqMethod)
            // 自定义请求头: 每行一条 "名: 值"(也接受 "名=值"); 覆盖=真 表示同名覆盖
            变量 reqHeaders <类型 = 文本型>
            reqHeaders = MCP命令服务器.yyjson取文本 (参数JSON, "headers")
            变量 头行数 <类型 = 整数>
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
            }
            // 请求体: 类库要求"数据编码必须是UTF8"(FBroLib.wsv:2610 注释原文), 故按 UTF-8 送
            变量 体字节数 <类型 = 整数>
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
            }
'''
c = rep(c, OLD, NEW, 'Core 请求体/请求头', nl2)
save(os.path.join(SRC, 'MCP_Server_Core.wsv'), c, 'MCP_Server_Core.wsv')

# ── ② Callbacks: 状态码回读 ──
cb, nl3 = load(os.path.join(SRC, 'MCP_Callbacks.wsv'))
OLD2 = '''        释放槽_一次 ()
        变量 包装对象 <类型 = YYJSON对象类>
        包装对象.创建自文本 ("{}")
        包装对象.加入逻辑值成员 ("success", 真)
        变量 结果文本 <类型 = 文本型>
'''
NEW2 = '''        释放槽_一次 ()
        变量 包装对象 <类型 = YYJSON对象类>
        包装对象.创建自文本 ("{}")
        包装对象.加入逻辑值成员 ("success", 真)
        // HTTP 层事实: 此前只回 success+body, **404 与 200 在回包里毫无区别**(实测缺口 G2)。
        // success 仍表示"请求本身完成"(传输层), 另给 http_ok 表示 2xx/3xx, 两者语义分开。
        变量 响应对象 <类型 = 类_FBrowser_响应>
        响应对象 = URL请求.取响应 ()
        如果 (响应对象.是否为空 () == 假)
        {
            变量 状态码 <类型 = 整数>
            状态码 = 响应对象.取状态 ()
            包装对象.加入整数成员 ("status_code", 状态码)
            包装对象.加入文本成员 ("status_text", 响应对象.取状态文本 ())
            包装对象.加入文本成员 ("mime", 响应对象.取MIME类型 ())
            包装对象.加入文本成员 ("charset", 响应对象.取字符集 ())
            包装对象.加入逻辑值成员 ("http_ok", 状态码 >= 200 && 状态码 < 400)
        }
        变量 错误码 <类型 = 整数>
        错误码 = URL请求.取请求错误码 ()
        如果 (错误码 != 0)
        {
            包装对象.加入整数成员 ("error_code", 错误码)
        }
        变量 结果文本 <类型 = 文本型>
'''
cb = rep(cb, OLD2, NEW2, 'Callbacks 状态码回读', nl3)
save(os.path.join(SRC, 'MCP_Callbacks.wsv'), cb, 'MCP_Callbacks.wsv')

# ── ③ Server: 描述与 schema ──
s, nl = load(os.path.join(SRC, 'MCP_Server.wsv'))
idx = [i for i, ln in enumerate(s.split('\n')) if '添加工具JSON ("browser_create_url_request"' in ln]
if len(idx) != 1:
    problems.append('Server 工具行定位 %d 行' % len(idx))
else:
    ls = s.split('\n')
    i = idx[0]
    ind = ' ' * (len(ls[i]) - len(ls[i].lstrip(' ')))
    DESC = ('独立 HTTP 请求(不经页面): 支持自定义请求头与 **POST 请求体**。'
            'headers 每行一条「名: 值」; 给了 body 且未显式给 method 时自动用 POST(类库要求请求体为 UTF-8)。'
            '结果经 mcp_result 取: 现在**会回 HTTP 状态码** —— status_code/status_text/mime/charset, '
            '以及 http_ok(2xx/3xx); success 只表示请求本身完成, 故 404 请以 http_ok/status_code 判断')
    SCHEMA = ('多属性Schema文本 (属性项JSON ("url", "text", "完整 URL(必填)") + "," + '
              '属性项JSON ("method", "text", "GET/POST/PUT/... (默认 GET; 给了 body 时默认 POST)") + "," + '
              '属性项JSON ("headers", "text", "自定义请求头, 每行一条 名: 值") + "," + '
              '属性项JSON ("body", "text", "请求体(UTF-8)")), "\\"url\\"")')
    # 保留原有其它参数(原实现可能只声明了 url/method): 只追加新参数, 不整行替换
    old_line = ls[i]
    if 'headers' not in old_line:
        if old_line.rstrip().endswith('单参数Schema文本 ("url", "text", "完整URL"))'):
            new_line = old_line.replace('单参数Schema文本 ("url", "text", "完整URL"))', SCHEMA + ')')
        else:
            new_line = (ind + '添加工具JSON ("browser_create_url_request", "%s", %s)' % (DESC, SCHEMA))
        ls[i] = new_line
        save(os.path.join(SRC, 'MCP_Server.wsv'), nl.join(ls), 'MCP_Server.wsv')
        print('   ok Server 工具描述/schema 已更新')
    else:
        print('   Server 已含 headers, 跳过')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
