# -*- coding: utf-8 -*-
"""补 innerText 读写（A 组第 5 缺口，且**不与既有工具重复**）。

先核对是否重复(第107轮子代理说"填表族唯独没有取元素 innerText", 本轮复核发现更精确):
  · `browser_fill_attr_get` 省略 attribute 时返回的是 **textContent**(原始文本)
  · `browser_dom_inner_html` 返回 **innerHTML**(含标签)
  · `browser_dom_set_html` 写 **innerHTML**; `browser_dom_set_value` 写 **.value**
  ⇒ 真正缺的是 **innerText(渲染后可见文本, 受 CSS 影响)** 的**读**与**写** —— 两者都没有等价物。
故只加这两个能力, 不复制已有的 textContent/innerHTML 路径(避免"重复造轮子")。

实现沿用本项目既有先例(`browser_fill_attr_get`, MCP_Server_Form.wsv:206):
  **CDP JS 优先 + 哨兵值区分"元素不存在/文本为空/CDP 取不到"**;
  写操作额外做**回读验证**(项目横切不变量: 不静默假成功)。
  原生回调式读 API(`取元素内文本` 需 结果回调)在注释里已记载"本内核恒返回空值并被写成字面 null",
  故不实现该回退, 而是在 CDP 不可用时给出可行动失败(不谎报)。
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'innerText读写-写入前')

FORM = os.path.join(SRC, 'MCP_Server_Form.wsv')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')

# ---------- A) MCP_Server_Form.wsv: 两个分支 ----------
F_ANCHOR = '        否则 (方法名 == "browser.fill_trigger" || 方法名 == "browser_fill_trigger")\n'
F_NEW = '''        否则 (方法名 == "browser.fill_get_text" || 方法名 == "browser_fill_get_text")
        {
            变量 selector <类型 = 文本型>
            selector = MCP命令服务器.yyjson取文本 (参数JSON, "selector")
            如果 (selector == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "selector 不能为空 | CSS选择器示例: #id / .class / h1"))
            }
            变量 browser <类型 = 类_FBrowser_浏览器>
            browser = MCP命令服务器.取主浏览器 ()
            如果 (browser.是否为空 ())
            {
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
            }
            // 与 browser_fill_attr_get 同款: 哨兵区分"元素不存在"与"文本为空"(CDP 对空串返回 "")
            变量 js码 <类型 = 文本型>
            js码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');if(!e)return '__MCP_NO_ELEM__';return '__MCP_TEXT__'+String(e.innerText==null?'':e.innerText)})()"
            变量 js值 <类型 = 文本型>
            js值 = MCP命令服务器.CDP执行JS并等待 (js码, 10000, 真)
            如果 (js值 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "取 innerText 失败: CDP 通道无返回 | 该工具走 CDP(原生回调式读 API 在本内核恒返回空值) | 可先用 browser_fill_exists 确认元素存在, 或改用 browser_fill_attr_get(不传 attribute 取 textContent)"))
            }
            如果 (js值 == "__MCP_NO_ELEM__")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "元素不存在: " + selector + " | 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在/选择器正确"))
            }
            如果 (是否以 (js值, "__MCP_TEXT__"))
            {
                返回 (MCP_响应构建.命令成功 (命令ID, 取文本右边 (js值, 取文本长度 (js值) - 取文本长度 ("__MCP_TEXT__"))))
            }
            // 未命中哨兵: 原样返回(不吞掉内容)
            返回 (MCP_响应构建.命令成功 (命令ID, js值))
        }
        否则 (方法名 == "browser.fill_set_text" || 方法名 == "browser_fill_set_text")
        {
            变量 selector <类型 = 文本型>
            selector = MCP命令服务器.yyjson取文本 (参数JSON, "selector")
            变量 新文本 <类型 = 文本型>
            新文本 = MCP命令服务器.yyjson取文本 (参数JSON, "text")
            如果 (selector == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "selector 不能为空"))
            }
            如果 (MCP命令服务器.参数键存在 (参数JSON, "text") == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "text 不能省略 | 省略会被当作空串而清空元素文本; 确实要清空请显式传 text: \\"\\""))
            }
            变量 browser2 <类型 = 类_FBrowser_浏览器>
            browser2 = MCP命令服务器.取主浏览器 ()
            如果 (browser2.是否为空 ())
            {
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
            }
            // text 必须嵌入**单引号** JS 字符串 -> 用 简单转义JS(双引号上下文请用 JSON转义文本)
            变量 设码 <类型 = 文本型>
            设码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');if(!e)return '__MCP_NO_ELEM__';e.innerText='" + MCP命令服务器.简单转义JS (新文本) + "';return '__MCP_OK__'})()"
            变量 设值 <类型 = 文本型>
            设值 = MCP命令服务器.CDP执行JS并等待 (设码, 10000, 真)
            如果 (设值 == "__MCP_NO_ELEM__")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "元素不存在: " + selector))
            }
            如果 (设值 != "__MCP_OK__")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "设置 innerText 失败: " + 设值 + " | CDP 未确认写入"))
            }
            // 回读验证(项目横切不变量: 写操作要回读, 不静默假成功)
            变量 读码 <类型 = 文本型>
            读码 = "(function(){var e=document.querySelector('" + MCP命令服务器.简单转义JS (selector) + "');if(!e)return '__MCP_NO_ELEM__';return '__MCP_TEXT__'+String(e.innerText==null?'':e.innerText)})()"
            变量 读值 <类型 = 文本型>
            读值 = MCP命令服务器.CDP执行JS并等待 (读码, 10000, 真)
            变量 回读文本 <类型 = 文本型>
            回读文本 = ""
            如果 (是否以 (读值, "__MCP_TEXT__"))
            {
                回读文本 = 取文本右边 (读值, 取文本长度 (读值) - 取文本长度 ("__MCP_TEXT__"))
            }
            如果 (回读文本 != 新文本)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "写入未被回读确认: 期望 [" + 新文本 + "] 实际 [" + 回读文本 + "] | 元素可能不可编辑或文本被页面脚本改写"))
            }
            返回 (MCP_响应构建.命令成功 (命令ID, "innerText 已设置并回读确认: " + 回读文本))
        }
''' + F_ANCHOR

# ---------- B) MCP_Server.wsv: 注册两行 ----------
GET_LINE = ('添加工具JSON ("browser_fill_get_text", "填表(原生CEF/CDP): 取元素 **innerText**(渲染后可见文本, 受 CSS 影响) | '
            '与既有工具的区别: browser_fill_attr_get(不传 attribute) 取的是 **textContent**(原始文本, 含隐藏元素), '
            'browser_dom_inner_html 取的是 **innerHTML**(含标签) —— 三者语义不同不可互替 | '
            '元素不存在会明确报错(不返回空串冒充)", 单参数Schema文本 ("selector", "text", "CSS选择器"))\n')
SET_LINE = ('添加工具JSON ("browser_fill_set_text", "填表(原生CEF/CDP): 设置元素 **innerText**(渲染后文本; 会按纯文本处理, 不解析 HTML) | '
            '与既有工具的区别: browser_dom_set_html 写 innerHTML(解析HTML), browser_dom_set_value 写 .value(表单控件) —— '
            '设置普通元素的可见文本请用本工具 | 写后**回读验证**, 未确认会如实报失败", '
            '多属性Schema文本 (属性项JSON ("selector", "text", "CSS选择器") + "," + 属性项JSON ("text", "text", "要设置的文本(显式传空串表示清空)"), "\\"selector\\",\\"text\\""))\n')

REG_ANCHOR = '        命令注册表.置整数值 ("browser_context_menu", '


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('   %s 换行=%s' % (tag, 'CRLF' if nl == '\r\n' else 'LF'))
    # ★锚点必须按该文件的换行归一化: 多行锚点在 CRLF 文件里用 \n 去 count 会 0 命中
    norm = [(old.replace('\n', nl), new) for old, new in pairs]
    for old, new in norm:
        c = text.count(old)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, old.strip()[:70]))
            return False
    for old, new in norm:
        for ln in new.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号奇数: %s' % ln.strip()[:100])
                return False
        text = text.replace(old, new.replace('\n', nl), 1)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.encode('utf-8'))
    print('   %s 已写入(+%d 处)' % (os.path.basename(path), len(pairs)))
    return True


if not patch(FORM, [(F_ANCHOR, F_NEW)], 'MCP_Server_Form.wsv'):
    sys.exit(1)

# 注册: 紧跟 browser_fill_attr_get 的注册行之后(同族相邻)
srv = io.open(SERVER, encoding='utf-8').read()
m = re.search(r'^.*添加工具JSON \("browser_fill_attr_get".*$', srv, re.M)
if not m:
    print('!! 找不到 browser_fill_attr_get 注册行, 中止')
    sys.exit(1)
srv2 = srv[:m.end()] + '\n' + GET_LINE.rstrip('\n') + '\n' + SET_LINE.rstrip('\n') + srv[m.end():]
# 注册表 ID
ids = [int(x.group(1)) for x in re.finditer(r'命令注册表\.置整数值 \("[^"]+",\s*(\d+)\)', srv2)]
nid = max(ids) + 1
mr = re.search(r'^.*命令注册表\.置整数值 \("browser_context_menu".*$', srv2, re.M)
if not mr:
    print('!! 找不到 browser_context_menu 注册行, 中止')
    sys.exit(1)
ins = (mr.group(0) + '\n'
       + '        命令注册表.置整数值 ("browser_fill_get_text", %d)\n' % nid
       + '        注册命令双变体 ("fill_get_text", %d)\n' % nid
       + '        命令注册表.置整数值 ("browser_fill_set_text", %d)\n' % (nid + 1)
       + '        注册命令双变体 ("fill_set_text", %d)' % (nid + 1))
srv2 = srv2[:mr.start()] + ins + srv2[mr.end():]
os.makedirs(BAK, exist_ok=True)
shutil.copy2(SERVER, os.path.join(BAK, 'MCP_Server.wsv'))
open(SERVER, 'wb').write(srv2.encode('utf-8'))
print('   MCP_Server.wsv 已写入(2 条注册 + 注册表 ID %d/%d)' % (nid, nid + 1))
print('完成; 备份 -> %s' % BAK)
