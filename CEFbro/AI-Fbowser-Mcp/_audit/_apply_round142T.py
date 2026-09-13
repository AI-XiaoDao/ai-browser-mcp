# -*- coding: utf-8 -*-
r"""第142轮补丁 T: DOM 编辑命令改用**最小原语**(派发 + 直接同步等待), 不再经 `执行CDP并同步等待`。

## 实测对照(同一实例, 每步量 execute_js)
| 路线 | DOM.enable | getDocument | removeAttribute | removeNode | 之后 execute_js |
|---|---|---|---|---|---|
| **裸 `browser_cdp_call`**(= `执行CDP命令` 派发 + 外层同步等待) | 0.03s OK | 0.03s nodeId=20 | **0.03s, 页面侧回读 null** | **0.03s, 页面侧回读 true** | **全程 0.03s** |
| 工具路径 `执行CDP并同步等待` | — | 可(0.03s) | **15s 超时并拖死通道** | 同样 | 35s(坏) |

⇒ 差别只在**等待/派发这一层**: 引用 nodeId 的 DOM 命令经 `执行CDP并同步等待`(它自带"删旧结果 + 预算压缩 +
超时自救 + 反应式补域"等额外动作)会挂住; 而"`执行CDP命令_带参数` 派发 + `同步等待异步任务`"这一对最小原语
(即 `browser_cdp_call` 走的那条)完全正常。故本补丁把**节点编辑**换成这对最小原语。

用法: py -3 _audit\_apply_round142T.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
APPLY = '--apply' in sys.argv

OLD = '''            变量 ne结果 <类型 = 文本型>
            ne结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_ed", neCdp方法, neParams, 15000)'''
NEW = '''            // ★ 实测: 引用 nodeId 的 DOM 命令**不能**走 `执行CDP并同步等待`(它自带的"删旧结果/预算压缩/超时自救/
            //   反应式补域"等额外动作会让这条命令挂住 15s 并拖死整条通道); 而"派发 + 直接同步等待"这对最小原语
            //   (即 browser_cdp_call 走的那条路)实测完全正常 —— 故此处改用最小原语, 并保留同样可读的失败文案。
            变量 ne结果 <类型 = 文本型>
            MCP命令服务器.执行CDP命令_带参数 (命令ID + "_ed", neCdp方法, neParams)
            ne结果 = MCP命令服务器.同步等待异步任务 (命令ID + "_ed", 15000)'''

# 预检(不引用 nodeId 的 getDocument)也得换成同一对原语, 原因同上
PRE_OLD = '''            变量 ne预检 <类型 = 文本型>
            ne预检 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_pre", "DOM.getDocument", "{\\"depth\\":-1,\\"pierce\\":true}", 15000)'''
PRE_NEW = '''            变量 ne预检 <类型 = 文本型>
            MCP命令服务器.执行CDP命令_带参数 (命令ID + "_pre", "DOM.getDocument", "{\\"depth\\":-1,\\"pierce\\":true}")
            ne预检 = MCP命令服务器.同步等待异步任务 (命令ID + "_pre", 15000)'''

# DOM.enable 同样(doc 命令也是"引用状态"的隐式前置, 用最小原语更稳)
EN_OLD = '''            变量 neDom域 <类型 = 文本型>
            neDom域 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_neden", "DOM.enable", "{}", 5000)'''
EN_NEW = '''            变量 neDom域 <类型 = 文本型>
            MCP命令服务器.执行CDP命令_带参数 (命令ID + "_neden", "DOM.enable", "{}")
            neDom域 = MCP命令服务器.同步等待异步任务 (命令ID + "_neden", 5000)'''

# get_document 的 CDP 路径同样换最小原语(它也引用 DOM 域状态)
GD_OLD = '''                变量 dDom域 <类型 = 文本型>
                dDom域 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_den", "DOM.enable", "{}", 5000)'''
GD_NEW = '''                变量 dDom域 <类型 = 文本型>
                MCP命令服务器.执行CDP命令_带参数 (命令ID + "_den", "DOM.enable", "{}")
                dDom域 = MCP命令服务器.同步等待异步任务 (命令ID + "_den", 5000)'''
GD2_OLD = '''                变量 dCdp结果 <类型 = 文本型>
                dCdp结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_gd", "DOM.getDocument", dParams, 15000)'''
GD2_NEW = '''                变量 dCdp结果 <类型 = 文本型>
                MCP命令服务器.执行CDP命令_带参数 (命令ID + "_gd", "DOM.getDocument", dParams)
                dCdp结果 = MCP命令服务器.同步等待异步任务 (命令ID + "_gd", 15000)'''

EDITS = [('T1 编辑命令走最小原语', OLD, NEW),
         ('T2 预检走最小原语', PRE_OLD, PRE_NEW),
         ('T3 编辑前 DOM.enable 走最小原语', EN_OLD, EN_NEW),
         ('T4 get_document 的 DOM.enable 走最小原语', GD_OLD, GD_NEW),
         ('T5 get_document 走最小原语', GD2_OLD, GD2_NEW)]


def main():
    print('== 第142轮补丁 T (%s) ==' % ('应用' if APPLY else '预演'))
    txt = io.open(VIP, encoding='utf-8', newline='').read()
    for tag, old, new in EDITS:
        if old not in txt:
            print('   · %-38s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        txt = txt.replace(old, new, 1)
        print('   · %s' % tag)
    print('MCP_Server_VIP.wsv: 行数 %d' % len(txt.split('\n')))
    if APPLY:
        io.open(VIP, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
