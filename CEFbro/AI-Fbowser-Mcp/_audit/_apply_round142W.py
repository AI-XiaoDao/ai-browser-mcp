# -*- coding: utf-8 -*-
r"""第142轮补丁 W(收尾): 去掉 node_edit 里的**全树预检** —— 实测它本身才是"拖死通道"的那一步。

## 实测(verify_round142e, 干净实例)
| 步骤 | 结果 |
|---|---|
| 只读 `get_document {depth:4}` ×3 | 全通, 每次之后 execute_js 0.03s |
| 只读 `get_document {depth:6, pierce:true/false}`(页面含影子树) | 全通, 之后 execute_js 0.03s |
| `browser_vip_dom_node_edit`(此时已是"纯拒绝路由", 不发任何 DOM 命令) | **15.21s 返回**, 且之后 execute_js **35s** ⇒ 通道被打死 |

⇒ 打死通道的不是编辑命令, 而是拒绝路径里的**全树预检** `DOM.getDocument {depth:-1, pierce:true}`
  (depth=-1 = 整棵文档树 + 穿透影子树; 在含影子树的页面上会挂住)。而该预检在本轮改成"路由"之后**已无必要**:
  工具不再提交任何命令, 自然不需要提前探测影子树。故整体删除, 并把它变成**给调用方的提示**(写在路由文案里)。

用法: py -3 _audit\_apply_round142W.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv


def main():
    vip = io.open(VIP, encoding='utf-8', newline='').read()
    lines = vip.split('\n')
    # 1) 删除全树预检块: 从含 "★ 安全闸门(实测): 若页面含" 的注释起, 到紧随其后的 `变量 ne结果 <类型 = 文本型>` 之前
    i0 = None
    for i, l in enumerate(lines):
        if '★ 安全闸门(实测): 若页面含' in l:
            i0 = i
            break
    i1 = None
    if i0 is not None:
        for j in range(i0, len(lines)):
            if lines[j].strip().startswith('变量 ne结果 <类型 = 文本型>'):
                i1 = j
                break
    if i0 is not None and i1 is not None:
        del lines[i0:i1]
        print('· 已删除全树预检块(%d 行)' % (i1 - i0))
    else:
        print('· 未找到全树预检块(可能已删)')
    vip = '\n'.join(lines)

    # 2) 路由文案里补影子树提示
    old_tail = '''| 只读枚举仍可用: browser_vip_dom_get_document(pierce=true 可见影子树)"))'''
    new_tail = '''| 只读枚举仍可用: browser_vip_dom_get_document(pierce=true 可见影子树) | ⚠ 另一条实测警告: 页面**含 shadow root** 时, 连只读的**全树**枚举(DOM.getDocument depth=-1 pierce=true)也会挂住并打死通道 —— 请用**有界 depth**(如 ≤8)的枚举; 这类页面的 DOM 改写建议直接用 browser_execute_js"(MCP_响应构建.记录自动处理 ("DOM 节点编辑: 已按实测改为可行动路由(分支内提交会打死 CDP 通道)")))'''
    if old_tail in vip:
        vip = vip.replace(old_tail, new_tail, 1)
        print('· 路由文案已补"影子树 + 全树枚举"警告')
    else:
        print('· 路由文案尾部未命中(跳过)')

    if APPLY:
        io.open(VIP, 'w', encoding='utf-8', newline='').write(vip)
        print('   ✔ 已写入 MCP_Server_VIP.wsv')

    # 3) 删除已无引用的 统计JSON键出现次数 助手(避免零引用方法)
    srv = io.open(SERVER, encoding='utf-8', newline='').read()
    i0 = srv.find('    # 统计一段文本里某个标记出现次数')
    if i0 >= 0:
        i1 = srv.find('    # 从 `执行CDP并同步等待` 的回包里取出 CDP 载荷**文本**', i0)
        if i1 > i0:
            srv = srv[:i0] + srv[i1:]
            print('· 已删除零引用助手 统计JSON键出现次数')
            # 同时它原本作为 node_edit 的调用点已被删, 这里再确认没有其它引用
            if '统计JSON键出现次数 (' in srv:
                print('   ⚠ 仍存在调用点, 请注意')
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(srv)
        print('   ✔ 已写入 MCP_Server.wsv')
    if not APPLY:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
