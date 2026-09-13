# -*- coding: utf-8 -*-
r"""第142轮补丁 Y(关键更正): **去掉每次调用前的 `DOM.enable`** —— 实测它才是"编辑挂住"的元凶。

## 实测线索(复盘本轮全部数据)
1. 裸 `browser_cdp_call` 序列(**只在开头 enable 一次**): getDocument → nodeId → removeAttribute → removeNode
   全程 0.03s, 页面侧回读一致, 收尾 execute_js 0.03s ⇒ **可用**;
2. 本轮 `verify_round142b` **未加 DOM.enable 之前的第一次运行**: `remove_attr 成功 0.02s`(通过!), 只是随后的**回读枚举**失败;
3. 加了"每次调用前 DOM.enable"(补丁 R)之后: **`remove_attr` 开始恒定挂住 15s**, 通道随之被打死;
4. 只读枚举 `get_document {depth:4}` ×3(该路径也带 DOM.enable)之后一切正常, 但三次拿到的 nodeId 各不相同
   (18 → 40 → 62) —— 说明 `DOM.getDocument` **每次都重建节点映射**, 旧 nodeId 立即失效。

⇒ 结论: **`DOM.enable` 会重置/重建节点映射, 于是"刚枚举拿到的 nodeId"在下一条命令里已失效**;
   而本机对失效 nodeId 的 DOM 命令不是报错, 而是**挂住**(并拖死整条通道)。
   正确用法 = **只 enable 一次**(或根本不 enable) + **枚举后立刻编辑, 编辑前不要再 enable**。

用法: py -3 _audit\_apply_round142Y.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
APPLY = '--apply' in sys.argv

# Y1: get_document 路径去掉逐次 DOM.enable
GD_OLD = '''                // ★ 隐式前置(实测): 必须先 `DOM.enable` —— 域未启用时首条命令能过, 但 CEF 不维护节点映射,
                //   之后引用 nodeId 的命令会挂住, 并把整条 CDP 通道拖死(实测: 第 2 次 getDocument 起全部超时,
                //   收尾 execute_js 35s)。与 Page.enable / Runtime.enable 同一类前置, 故此处补齐并经 auto_prepared 上报。
                变量 dDom域 <类型 = 文本型>
                MCP命令服务器.执行CDP命令_带参数 (命令ID + "_den", "DOM.enable", "{}")
                dDom域 = MCP命令服务器.同步等待异步任务 (命令ID + "_den", 5000)
                如果 (MCP命令服务器.CDP同步结果是否成功 (dDom域) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "DOM.enable 失败, DOM 族无法安全使用: " + MCP命令服务器.取CDP同步结果错误 (dDom域) + " | 可显式改用 via:library(类库开发者DOM 路线; **实测会让本会话 CDP 命令通道失效**)"))
                }
                MCP_响应构建.记录自动补域 ("DOM")
'''
# Y2: node_edit 路径(已删, 只留注释确认)

EDITS = [('Y1 get_document 去掉逐次 DOM.enable', GD_OLD, '')]


def main():
    print('== 第142轮补丁 Y (%s) ==' % ('应用' if APPLY else '预演'))
    txt = io.open(VIP, encoding='utf-8', newline='').read()
    for tag, old, new in EDITS:
        if old not in txt:
            print('   · %-40s 锚点未找到(可能已删/已改)' % tag)
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
