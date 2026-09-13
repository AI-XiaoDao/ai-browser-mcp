# -*- coding: utf-8 -*-
r"""第128轮: 修掉两处"静默假成功"（只读审计 `_schema_audit_C.md` 第 11、15 条，均已在源码核实）。

① `browser_kernel_scheme action=register`（MCP_Kernel.wsv:411-416）:
   原实现 `如果 (body == "" && 文件是否存在 (file))` —— **file 写错会被静默忽略**, 于是注册一个
   **空内容**方案却回 success; `data` 与 `file` 都不给同样如此。对代理而言"注册成功但页面是空的"
   极难排查。改为: file 给了但不存在 → 明确报错(附绝对路径要求); 读回为空 → 报错; data/file 都没给 → 拒绝。
② `browser_kernel_ipc_clear` / `browser_kernel_ipc_queue`（MCP_Kernel.wsv:544-554）:
   描述写"action 必填且只能为 clear", 但实现**不校验**: 不传 action(或拼错)会**静默退化为读取队列**并回
   success —— 调用方以为已清空, 实际什么都没清。改为: 工具名是 ipc_clear 且未给 action 时按 clear 处理;
   给了未知 action 时明确拒绝(列出支持值)。

用法: py -3 _audit\_apply_kernel_fake_success.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KERNEL = os.path.join(ROOT, 'src', 'MCP_Kernel.wsv')

SCHEME_OLD = '''            变量 body <类型 = 文本型>
            body = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (body == "" && 文件是否存在 (MCP命令服务器.yyjson取文本 (参数JSON, "file")))
            {
                body = 读入文本文件 (MCP命令服务器.yyjson取文本 (参数JSON, "file"))
            }'''
SCHEME_NEW = '''            变量 body <类型 = 文本型>
            body = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            // 实测缺陷修正: 原实现只写 "body 为空且文件存在才读", 于是 file 写错(或 data/file 都不给)会被
            //   **静默忽略**, 结果注册出一个空内容方案却回 success —— 调用方以为注册好了, 页面却是空的。
            变量 方案文件 <类型 = 文本型>
            方案文件 = MCP命令服务器.yyjson取文本 (参数JSON, "file")
            如果 (body == "")
            {
                如果 (方案文件 != "")
                {
                    如果 (文件是否存在 (方案文件) == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "file 不存在: " + 方案文件 + " | 请给**绝对路径**(相对路径按进程运行目录解析) | 如实说明: 此前 file 写错会被静默忽略并注册出一个**空内容**方案却回 success(假成功), 现已改为明确报错"))
                    }
                    body = 读入文本文件 (方案文件)
                    如果 (body == "")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "file 读取为空: " + 方案文件 + " | 页面只会拿到空文档, 无实际意义; 请确认文件内容"))
                    }
                }
                否则
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "必须提供 data(响应内容) 或 file(存在的文件绝对路径) | 二者都不给时此前会注册一个**空内容**方案并回 success(假成功), 现已拒绝"))
                }
            }'''

IPC_OLD = '''        变量 动作 <类型 = 文本型>
        动作 = MCP命令服务器.yyjson取文本 (参数JSON, "action")
        如果 (动作 == "clear")'''
IPC_NEW = '''        变量 动作 <类型 = 文本型>
        动作 = MCP命令服务器.yyjson取文本 (参数JSON, "action")
        // 工具名 browser_kernel_ipc_clear 自带"清空"语义: 未给 action 时应按 clear 处理,
        // 否则会**静默退化为读取队列**并回 success —— 调用方以为已清空, 实际什么都没清(实测缺陷)。
        如果 (动作 == "" && MCP命令服务器.当前命令方法名 == "browser_kernel_ipc_clear")
        {
            动作 = "clear"
        }
        如果 (动作 != "" && 动作 != "clear" && 动作 != "queue" && 动作 != "list" && 动作 != "get")
        {
            返回 (MCP_响应构建.命令失败 (命令ID, "未知 action: " + 动作 + " | 支持 clear(清空) / queue(读取, 缺省行为) | 如实说明: 此前未知 action 会**静默退化为读取**并回 success, 调用方会以为已清空"))
        }
        如果 (动作 == "clear")'''


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
    txt = io.open(KERNEL, encoding='utf-8').read()
    has_cr = '\r' in txt
    b0, n0 = balance(txt), len(txt.split('\n'))
    out = txt
    for tag, old, new in (('① 方案 register 空内容/文件不存在守卫', SCHEME_OLD, SCHEME_NEW),
                          ('② IPC 队列 action 校验 + 工具名默认 clear', IPC_OLD, IPC_NEW)):
        cnt = out.count(old)
        assert cnt == 1, '%s 锚点 %d 次' % (tag, cnt)
        out = out.replace(old, new, 1)
        print('   · %s' % tag)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Kernel.wsv: 行数 %d -> %d (CR=%s); 括号净值 %s 不变'
          % (n0, len(out.split('\n')), has_cr, balance(out)))
    if '--apply' in sys.argv:
        io.open(KERNEL, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(KERNEL, encoding='utf-8').read()
        assert '方案文件' in c and '未知 action: ' in c and ('\r' in c) == has_cr
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
