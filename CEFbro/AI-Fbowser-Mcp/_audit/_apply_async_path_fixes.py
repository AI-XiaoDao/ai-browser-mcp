# -*- coding: utf-8 -*-
r"""第126轮(其二): 两处"异步路径"缺陷(由本轮验收脚本真实踩到)。

F1 `命令成功_异步` **丢弃 auto_prepared** ⇒ 零前置的"如实上报"在**所有异步工具**上失效
   (实测: browser_create_url_request 自动置 UR_FLAG_REPORT_UPLOAD_PROGRESS + 自动开 urlreq 监控,
     但异步提交回包里看不到任何说明 —— 与项目"零前置必如实上报"的不变量不符)。
F2 异步工具在 **JSON 回包之后**追加裸文本 `\n\n[task_id: xxx]` ⇒ 整段内容不再是合法 JSON
   (实测: 客户端 json.loads 直接失败, 我的验收脚本因此把 task_id 解析成 None, 出现 3 条假失败)。
   JSON 回包里本来就有 `task_id` 字段, 故只在**非 JSON** 内容时才追加。

用法: py -3 _audit\_apply_async_path_fixes.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

F1_OLD = '        对象.加入文本成员 ("poll_hint", "用 mcp_result 轮询: mcp_result {request_id: \\"" + 任务ID + "\\", consume: true}")'
F1_NEW = '''        // 零前置"如实上报": 异步提交路径此前**丢弃**了 auto_prepared(自动补域/自动开监控/自动置标志…),
        // 与 命令成功/命令失败 不一致 —— 实测: browser_create_url_request 自动置上传进度标志并自动开
        // urlreq 监控, 但这些说明在异步回包里完全看不到。此处对齐消费一次并附上。
        变量 补域异步 <类型 = 文本型>
        补域异步 = MCP_响应构建.取并清除自动补域报告 ()
        如果 (补域异步 != "")
        {
            对象.加入文本成员 ("auto_prepared", 补域异步)
        }
        对象.加入文本成员 ("poll_hint", "用 mcp_result 轮询: mcp_result {request_id: \\"" + 任务ID + "\\", consume: true}")'''

F2_OLD = '''        如果 (是否异步 && 异步任务ID != "")
        {
            内容文本 = 内容文本 + "\\n\\n[task_id: " + 异步任务ID + "]"
        }'''
F2_NEW = '''        如果 (是否异步 && 异步任务ID != "")
        {
            // 仅在内容**不是 JSON** 时追加人类可读提示 —— JSON 回包里已有 task_id 字段,
            // 在 JSON 后追加裸文本会让整段内容不再可解析(实测: 客户端 json.loads 直接失败)。
            如果 (是否以 (删首尾空 (内容文本), "{") == 假)
            {
                内容文本 = 内容文本 + "\\n\\n[task_id: " + 异步任务ID + "]"
            }
        }'''


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
    n0, b0 = len(txt.split('\n')), balance(txt)
    out = txt
    for tag, old, new in (('F1 异步回包补 auto_prepared', F1_OLD, F1_NEW),
                          ('F2 只在非 JSON 内容后追加 task_id 提示', F2_OLD, F2_NEW)):
        if new.split('\n')[0] in out and tag.startswith('F1') and '补域异步' in out:
            print('   (%s 已存在, 跳过)' % tag)
            continue
        assert out.count(old) == 1, '%s 锚点 %d 次' % (tag, out.count(old))
        out = out.replace(old, new, 1)
        print('   · %s' % tag)
    # F2 的锚点在替换 F1 后仍在(不同位置), 已在上面的循环里处理
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server.wsv: 行数 %d -> %d; 括号净值 %s 不变' % (n0, len(out.split('\n')), balance(out)))
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert '补域异步' in c and '是否以 (删首尾空 (内容文本), "{") == 假' in c and '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
