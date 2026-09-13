# -*- coding: utf-8 -*-
r"""新增 MCP命令服务器.解析框架对象 (原生 CEF 框架对象寻址) —— 供 browser_execute_js {frame_id} 用。

为什么需要它: 原生 类_FBrowser_框架 的 执行JS代码_带返回值 在**该框架自己的页面主世界**里求值,
而 CDP 只能给该框架建**隔离世界**(本机实测: 隔离世界读不到页面在子框架里挂的全局变量与函数)。
"在子框架里跑用户 JS" 必须用前者, 否则是静默换了世界。

寻址顺序: 空/main/主框架 -> 主框架; 再 CEF 框架ID; 再框架名; 最后纯数字序号(清单顺序, 0=主框架)。
契约: 找不到返回**空类**, 调用方必须守卫后报错 —— 绝不静默落到主框架。

安全: 插入区间必须是新方法自身(花括号净额 0), 且整文件净额保持 0。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
ANCHOR = '    方法 解析填表框架 <公开 静态 类型 = 类_FBrowser_填表框架 @输出名 = "ResolveFillFrame" @强制输出 = 真>'

HELPER = '''    # 解析"要操作哪个框架对象"(原生 CEF 框架对象, 用于在该框架**自己的页面主世界**执行 JS)。
    # 接受: 空/main/主框架 -> 主框架; CEF 框架ID(取框架ID 给出的 id); 框架名; 纯数字序号(清单顺序, 0=主框架)。
    # 契约: 找不到返回**空类**, 调用方必须用 是否为空()/是否有效() 守卫后报错 —— 不得静默落到主框架。
    # 依据: 类库 取框架_ID / 取框架_名称 对错误标识一律返回空类(类库原文: ID 错误返回空, 对空类执行操作会崩溃)。
    方法 解析框架对象 <公开 静态 类型 = 类_FBrowser_框架 @输出名 = "ResolveFrameObject" @强制输出 = 真>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 目标框架 <类型 = 文本型 @输出名 = "TargetFrame">
    {
        变量 空框架 <类型 = 类_FBrowser_框架>
        如果 (浏览器.是否为空 () || 浏览器.是否已关闭 ())
        {
            返回 (空框架)
        }
        如果 (目标框架 == "" || 目标框架 == "main" || 目标框架 == "主框架")
        {
            返回 (取安全主框架 (浏览器))
        }
        变量 候选 <类型 = 类_FBrowser_框架>
        // ① 按 CEF 框架ID
        候选 = 浏览器.取框架_ID (目标框架)
        如果 (候选.是否为空 () == 假 && 候选.是否有效 ())
        {
            返回 (候选)
        }
        // ② 按框架名
        候选 = 浏览器.取框架_名称 (目标框架)
        如果 (候选.是否为空 () == 假 && 候选.是否有效 ())
        {
            返回 (候选)
        }
        // ③ 纯数字才按序号解释: 否则 文本到整数("no-such") 得 0 会把"不存在"静默变成"主框架"
        变量 全是数字 <类型 = 逻辑型>
        全是数字 = 真
        变量 判位 <类型 = 整数>
        判位 = 0
        判断循环 (判位 < 取文本长度 (目标框架))
        {
            如果 (寻找文本 ("0123456789", 取文本中间 (目标框架, 判位, 1), 0, 假) == -1)
            {
                全是数字 = 假
                跳出循环
            }
            判位 = 判位 + 1
        }
        如果 (全是数字)
        {
            变量 id清单 <类型 = FBrowser_文本数组>
            id清单 = 浏览器.取框架ID ()
            变量 序号 <类型 = 整数>
            序号 = 文本到整数 (目标框架)
            如果 (序号 >= 0 && 序号 < id清单.取个数 ())
            {
                候选 = 浏览器.取框架_ID (id清单.取数据 (序号))
                如果 (候选.是否为空 () == 假 && 候选.是否有效 ())
                {
                    返回 (候选)
                }
            }
        }
        返回 (空框架)
    }

'''


def depth_delta(lines):
    bal = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
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
                elif c == '{':
                    bal += 1
                elif c == '}':
                    bal -= 1
            k += 1
    return bal


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '文件带 BOM'
    assert b'\r\n' not in raw, '文件含 CRLF'
    lines = raw.decode('utf-8').split('\n')

    hits = [i for i, l in enumerate(lines) if l == ANCHOR]
    assert len(hits) == 1, '锚点命中 %d 次' % len(hits)
    m = hits[0]
    # 回退到该方法自带注释块的首行(紧邻的连续 `    #` 行)
    ins = m
    while ins - 1 >= 0 and lines[ins - 1].startswith('    #'):
        ins -= 1
    print('锚点方法 @%d, 注释块首行 @%d: %s' % (m + 1, ins + 1, lines[ins].strip()[:70]))

    helper_lines = HELPER.rstrip('\n').split('\n')
    assert depth_delta(helper_lines) == 0, 'helper 不平衡: %d' % depth_delta(helper_lines)
    assert not any('解析框架对象' in l for l in lines), '已存在同名方法'

    out = lines[:ins] + helper_lines + lines[ins:]
    assert depth_delta(lines) == depth_delta(out) == 0, '整文件净额 %d -> %d' % (depth_delta(lines), depth_delta(out))
    new_hits = [i for i, l in enumerate(out) if l == ANCHOR]
    assert len(new_hits) == 1 and new_hits[0] == m + len(helper_lines), '插入后锚点漂移异常'

    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('已写入 %s (行数 %d -> %d)' % (TARGET, len(lines), len(out)))
    else:
        print('[dry-run] 在 %d 行前插入 %d 行; 行数 %d -> %d'
              % (ins + 1, len(helper_lines), len(lines), len(out)))
        print('花括号净额: helper %d, 整文件 %d -> %d' % (depth_delta(helper_lines), depth_delta(lines), depth_delta(out)))


main()
