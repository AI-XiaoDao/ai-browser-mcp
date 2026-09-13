# -*- coding: utf-8 -*-
"""消费 类_FBrowser_菜单环境 —— 把"右键上下文"纳入事件载荷（A 组第 1 缺口，零新增通道成本）。

为什么这是明确的缺口:
  `菜单环境` 形参**已经**出现在三个 CEF 事件签名的函数表里
  (`MCP_BrowserEvents.wsv:2661/2679/2694`), 但**零消费点**(方法体里从不使用) ——
  于是 AI 只能知道"某处右键了", 不知道**右键在什么上面**(链接/选中文本/编辑框/图片…)。
  而 **CDP 完全没有右键上下文域**, 没有替代路径。

生命周期: 与 `菜单模式` 同规 —— CEF 头说明该回调的参数**不得在回调之外持有**,
故本实现**只在回调内**把需要的值**取成文本**(不是保存对象), 再把文本交给事件记录。

落点: ① MCP_Server.wsv 新增 构建菜单环境摘要; ② MCP_BrowserEvents.wsv 三个 override 里调用。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '右键菜单环境消费-写入前')

SERVER = os.path.join(SRC, 'MCP_Server.wsv')
BE = os.path.join(SRC, 'MCP_BrowserEvents.wsv')

# ---------- A) MCP_Server.wsv: 新 helper（插在 应用菜单规格 之前，紧邻菜单相关代码） ----------
A_ANCHOR = '    # 把暂存的菜单规格施加到**当前这次右键**的菜单模型上(只在 CEF 回调内调用)。\n'
A_NEW = '''    # 把"右键上下文"(类_FBrowser_菜单环境)取成紧凑 JSON —— **只在 CEF 回调内调用**。
    # 该对象与 菜单模式 同受 CEF 生命周期约束(禁止在回调之外持有), 故这里只**取值成文本**, 不保存对象。

    方法 构建菜单环境摘要 <公开 静态 类型 = 文本型 @输出名 = "BuildMenuEnvSummary" @强制输出 = 真>
    参数 菜单环境 <类型 = 类_FBrowser_菜单环境 @输出名 = "MenuParams">
    {
        变量 菜单摘要 <类型 = YYJSON对象类>
        菜单摘要.创建自文本 ("{}")
        如果 (菜单环境.是否为空 ())
        {
            菜单摘要.加入逻辑值成员 ("available", 假)
            返回 (菜单摘要.到可读文本 (YYJSON格式化选项.压缩))
        }
        菜单摘要.加入逻辑值成员 ("available", 真)
        菜单摘要.加入整数成员 ("x", 菜单环境.取横向位置 ())
        菜单摘要.加入整数成员 ("y", 菜单环境.取纵向位置 ())
        菜单摘要.加入整数成员 ("type_flags", 菜单环境.取类型 ())
        菜单摘要.加入文本成员 ("link", 菜单环境.取地址 ())
        菜单摘要.加入文本成员 ("link_unfiltered", 菜单环境.取完整地址 ())
        菜单摘要.加入文本成员 ("source_url", 菜单环境.取源地址 ())
        菜单摘要.加入文本成员 ("page_url", 菜单环境.取页地址 ())
        菜单摘要.加入文本成员 ("frame_url", 菜单环境.取框架页地址 ())
        菜单摘要.加入文本成员 ("frame_charset", 菜单环境.取框架网页编码 ())
        菜单摘要.加入逻辑值成员 ("has_image", 菜单环境.是否存在图片 ())
        菜单摘要.加入整数成员 ("media_type", 菜单环境.取媒体类型 ())
        菜单摘要.加入整数成员 ("media_type_flags", 菜单环境.取媒体类型标识 ())
        菜单摘要.加入文本成员 ("selection_text", 菜单环境.取选择文本 ())
        菜单摘要.加入文本成员 ("misspelled_word", 菜单环境.取错误单词 ())
        菜单摘要.加入逻辑值成员 ("editable", 菜单环境.是否为编辑框 ())
        菜单摘要.加入逻辑值成员 ("spellcheck_enabled", 菜单环境.是否为选择框 ())
        菜单摘要.加入整数成员 ("edit_state_flags", 菜单环境.取编辑框类型标识 ())
        菜单摘要.加入逻辑值成员 ("is_custom_menu", 菜单环境.是否为Custom菜单 ())
        返回 (菜单摘要.到可读文本 (YYJSON格式化选项.压缩))
    }

''' + A_ANCHOR

# ---------- B) MCP_BrowserEvents.wsv: 三个 override 使用它 ----------
B1_OLD = ('        如果 (MCP命令服务器.是否监控菜单事件)\n'
          '        {\n'
          '            记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), "")\n'
          '        }\n')
B1_NEW = ('        如果 (MCP命令服务器.是否监控菜单事件)\n'
          '        {\n'
          '            // 右键上下文(链接/选中文本/是否编辑框/坐标/媒体类型…): 该对象只在本次回调内有效,\n'
          '            // 故在此**取成文本**再交给事件记录(不保存对象本身)。\n'
          '            记录监控事件 (真, "context_menu_opening", 浏览器.取ID (), MCP命令服务器.构建菜单环境摘要 (菜单环境))\n'
          '        }\n')

B2_OLD = ('        如果 (MCP命令服务器.是否监控菜单事件)\n'
          '        {\n'
          '            记录监控事件 (真, "context_menu_run", 浏览器.取ID (), "")\n'
          '        }\n')
B2_NEW = ('        如果 (MCP命令服务器.是否监控菜单事件)\n'
          '        {\n'
          '            记录监控事件 (真, "context_menu_run", 浏览器.取ID (), MCP命令服务器.构建菜单环境摘要 (菜单环境))\n'
          '        }\n')

B3_OLD = ('            事件数据.加入文本成员 ("command_id", 到文本 (命令ID))\n'
          '            事件数据.加入文本成员 ("event_flags", 到文本 (事件标识))\n'
          '            记录监控事件 (真, "context_menu_command", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))\n')
B3_NEW = ('            事件数据.加入文本成员 ("command_id", 到文本 (命令ID))\n'
          '            事件数据.加入文本成员 ("event_flags", 到文本 (事件标识))\n'
          '            // 同时带上右键上下文: 调用方据此判断"这此点击发生在链接/编辑框/选中文本上"\n'
          '            事件数据.加入文本成员 ("menu_env", MCP命令服务器.构建菜单环境摘要 (菜单环境))\n'
          '            记录监控事件 (真, "context_menu_command", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))\n')


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    for old, new in pairs:
        c = text.count(old)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, old.strip()[:70]))
            return False
    for old, new in pairs:
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


if not patch(SERVER, [(A_ANCHOR, A_NEW)], 'MCP_Server.wsv'):
    sys.exit(1)
if not patch(BE, [(B1_OLD, B1_NEW), (B2_OLD, B2_NEW), (B3_OLD, B3_NEW)], 'MCP_BrowserEvents.wsv'):
    sys.exit(1)
print('完成; 备份 -> %s' % BAK)
