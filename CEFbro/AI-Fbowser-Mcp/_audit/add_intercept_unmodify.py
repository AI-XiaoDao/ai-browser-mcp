# -*- coding: utf-8 -*-
"""实现 browser_intercept 的 unmodify / unreplace —— 按 URL 撤销单条规则。

背景(子代理只读分析 + 主代理复核): 现在只能 `clear` **整体清空**, 不能撤一条;
长会话里改错一条就得推倒重建全部规则。类库 `过滤器_取消修改内容/取消替换资源` 需要"完整目标地址"
且当前手写通道并未使用 VIP 过滤器(VIP 添加侧全树零调用), 故本实现只作用于**手写过滤器通道**,
并在返回文本里**显式声明作用域**, 避免调用方误以为连 VIP 过滤器一起撤了。

口径: 与"命中"完全一致 —— 请求URL **包含** 规则URL 即算该规则(见 匹配资源篡改规则 :7241)。
删除不存在的规则按**幂等成功**处理并如实回报删了几条(与 clear/popup_disable 惯例一致;
报失败会诱发 AI 反复重试, 而"该 URL 不再被改"这一目标状态本已达成)。

落点: ① 新helper 插在 添加资源替换规则 之后; ② 两个 action 插在 line_replace 之后、未知action 之前。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '拦截按URL撤销-写入前')

# ============ A. MCP_Server.wsv: 新增 helper ============
SERVER = os.path.join(SRC, 'MCP_Server.wsv')
A_OLD = ('        资源替换规则 = 裁剪规则文本到最大行数 (资源替换规则, MCP_常量.拦截规则最大行数)\n'
         '        规则锁.解锁 ()\n'
         '    }\n'
         '\n'
         '    # 手写篡改: 按URL匹配资源替换规则, 返回匹配JSON {action,search,replace,file} 或空文本\n')
A_NEW = ('        资源替换规则 = 裁剪规则文本到最大行数 (资源替换规则, MCP_常量.拦截规则最大行数)\n'
         '        规则锁.解锁 ()\n'
         '    }\n'
         '\n'
         '    # 按 URL 撤销资源替换规则(与 匹配资源篡改规则 同口径: 请求URL包含规则URL 即命中), 返回删除条数。\n'
         '    # 限定动作为空=删所有动作类; 传 "replace_file" 则只删文件替换类(供 unreplace 精确撤销)。\n'
         '\n'
         '    方法 删除资源替换规则 <公开 静态 类型 = 整数 @输出名 = "DeleteResourceReplaceRule" @强制输出 = 真>\n'
         '    参数 目标URL <类型 = 文本型 @输出名 = "TargetURL">\n'
         '    参数 限定动作 <类型 = 文本型 @输出名 = "LimitAction">\n'
         '    {\n'
         '        // 空 URL 直接返回 0: 防止"空串子串匹配到全部"把规则误删光\n'
         '        如果 (目标URL == "")\n'
         '        {\n'
         '            返回 (0)\n'
         '        }\n'
         '        变量 删除条数 <类型 = 整数>\n'
         '        删除条数 = 0\n'
         '        规则锁.加锁 ()\n'
         '        如果 (资源替换规则 != "")\n'
         '        {\n'
         '            变量 保留行 <类型 = 文本型>\n'
         '            保留行 = ""\n'
         '            变量 行数组 <类型 = 文本数组类>\n'
         '            分割文本 (资源替换规则, "\\n", 行数组, 真, 假)\n'
         '            计次循环 (行数组.取成员数 ())\n'
         '            {\n'
         '                变量 行文本 <类型 = 文本型>\n'
         '                行文本 = 行数组.取成员 (取循环索引 ())\n'
         '                变量 本行命中 <类型 = 逻辑型>\n'
         '                本行命中 = 假\n'
         '                如果 (行文本 != "")\n'
         '                {\n'
         '                    变量 段数组 <类型 = 文本数组类>\n'
         '                    分割文本 (行文本, "|", 段数组, 假, 假)\n'
         '                    如果 (段数组.取成员数 () >= 2)\n'
         '                    {\n'
         '                        变量 动作相符 <类型 = 逻辑型>\n'
         '                        动作相符 = 真\n'
         '                        如果 (限定动作 != "" && 段数组.取成员 (0) != 限定动作)\n'
         '                        {\n'
         '                            动作相符 = 假\n'
         '                        }\n'
         '                        如果 (动作相符)\n'
         '                        {\n'
         '                            // 存储时 URL 段是转义过的, 比较前必须反转义, 否则带 % | 的 URL 永远删不掉\n'
         '                            变量 规则URL <类型 = 文本型>\n'
         '                            规则URL = 规则字段反转义 (段数组.取成员 (1))\n'
         '                            如果 (规则URL != "" && 寻找文本 (目标URL, 规则URL, 0, 假) != -1)\n'
         '                            {\n'
         '                                本行命中 = 真\n'
         '                            }\n'
         '                        }\n'
         '                    }\n'
         '                }\n'
         '                如果 (本行命中)\n'
         '                {\n'
         '                    删除条数 = 删除条数 + 1\n'
         '                }\n'
         '                否则\n'
         '                {\n'
         '                    如果 (保留行 == "")\n'
         '                    {\n'
         '                        保留行 = 行文本\n'
         '                    }\n'
         '                    否则\n'
         '                    {\n'
         '                        保留行 = 保留行 + "\\n" + 行文本\n'
         '                    }\n'
         '                }\n'
         '            }\n'
         '            资源替换规则 = 保留行\n'
         '        }\n'
         '        规则锁.解锁 ()\n'
         '        返回 (删除条数)\n'
         '    }\n'
         '\n'
         '    # 手写篡改: 按URL匹配资源替换规则, 返回匹配JSON {action,search,replace,file} 或空文本\n')

# ============ B. MCP_Server_Core.wsv: 两个 action ============
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
B_OLD = ('                返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + action + " | 支持: modify/replace_data/replace_file/block/line_replace/navigate_block/navigate_redirect/popup_config/popup_disable/cache/uncache/clear/ws_hook"))\n')
B_NEW = ('                否则 (action == "unmodify")\n'
         '                {\n'
         '                    // 按 URL 撤销资源替换规则(与添加/命中同口径: 请求URL包含规则URL)\n'
         '                    变量 unmodify删数 <类型 = 整数>\n'
         '                    unmodify删数 = MCP命令服务器.删除资源替换规则 (url, "")\n'
         '                    返回 (MCP_响应构建.命令成功 (命令ID, "已按 URL 撤销资源替换规则 " + 到文本 (unmodify删数) + " 条 | 口径: 请求URL包含规则URL(与命中同口径) | url=" + url + " | 作用域: 手写过滤器通道(不含 VIP 过滤器) | 只影响后续请求, 刷新页面后生效"))\n'
         '                }\n'
         '                否则 (action == "unreplace")\n'
         '                {\n'
         '                    // 与 unmodify 同构, 但只撤销文件替换(replace_file)类规则\n'
         '                    变量 unreplace删数 <类型 = 整数>\n'
         '                    unreplace删数 = MCP命令服务器.删除资源替换规则 (url, "replace_file")\n'
         '                    返回 (MCP_响应构建.命令成功 (命令ID, "已按 URL 撤销文件替换规则 " + 到文本 (unreplace删数) + " 条 | 口径: 请求URL包含规则URL | url=" + url + " | 作用域: 手写过滤器通道(不含 VIP 过滤器) | 只刷新影响后续请求"))\n'
         '                }\n'
         '                返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + action + " | 支持: modify/replace_data/replace_file/block/line_replace/unmodify/unreplace/navigate_block/navigate_redirect/popup_config/popup_disable/cache/uncache/clear/ws_hook"))\n')


def patch(path, old, new, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    c = text.count(old)
    print('%s 换行=%s 锚点命中=%d (应为1)' % (tag, 'CRLF' if nl == '\r\n' else 'LF', c))
    if c != 1:
        return False
    body = new.replace('\n', nl)
    for ln in body.split(nl):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            print('!! 裸双引号奇数: %s' % ln.strip()[:100])
            return False
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.replace(old, body, 1).encode('utf-8'))
    print('   已写入 %s' % os.path.basename(path))
    return True


ok = patch(SERVER, A_OLD, A_NEW, 'MCP_Server.wsv')
if not ok:
    sys.exit(1)
ok = patch(CORE, B_OLD, B_NEW, 'MCP_Server_Core.wsv')
if not ok:
    sys.exit(1)
print('完成; 备份 -> %s' % BAK)
