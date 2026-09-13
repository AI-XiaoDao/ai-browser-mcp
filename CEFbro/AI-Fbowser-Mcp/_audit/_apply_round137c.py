# -*- coding: utf-8 -*-
r"""第137轮补丁 v3: 重复 install 改为**幂等成功**(实测卡点)。

## 实测(第137轮, 台账复测)
在插装已装上的实例里再调 `action=install`, 工具返回:
  `该插装已处于启用状态(重复install) | 停止拦截用 action=suppress; 彻底清除用 browser_debugger_disable`
—— 即**把幂等的重复调用报成了失败**。对 AI 代理而言这正是"同一功能反复换方法试错"的触发点
(本目标要消灭的体验): 第二次 install 拿到失败, 代理会以为工具坏了。

## 修法(不重复造轮子)
`already enabled` 是 CDP 的**幂等信号**: 插装本来就在生效, 没有任何状态需要改。故改为
返回 `success:true + already_installed:true + note(下一步怎么停/恢复)`, 并**置位** `插装已安装`
(它确实已装上), 让自救预算继续生效。

用法: py -3 _audit\_apply_round137c.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
APPLY = '--apply' in sys.argv

OLD = '                        返回 (MCP_响应构建.命令失败 (命令ID, "该插装已处于启用状态(重复install) | 停止拦截用 action=suppress; 彻底清除用 browser_debugger_disable"))'
NEW = [
    '                        // 幂等: 重复 install **不是失败** —— 插装本来就已生效, 报失败只会逼调用方"换别的方法反复试错"',
    '',
    '                        // (正是本目标要消灭的体验)。如实回报 already_installed 并置位标志, 附上停止/恢复的下一步。',
    '',
    '                        MCP命令服务器.插装已安装 = 真',
    '',
    '                        变量 ivIdemOut <类型 = YYJSON对象类>',
    '',
    '                        ivIdemOut.创建自文本 ("{}")',
    '',
    '                        ivIdemOut.加入逻辑值成员 ("success", 真)',
    '',
    '                        ivIdemOut.加入逻辑值成员 ("already_installed", 真)',
    '',
    '                        ivIdemOut.加入文本成员 ("cdp_method", "Debugger.setInstrumentationBreakpoint")',
    '',
    '                        ivIdemOut.加入文本成员 ("note", "该插装本会话已装过(重复 install 无副作用, 不会叠加) | 停止拦截: action=suppress 或 browser_reverse_skip_pauses skip=true (若之前用过它们, 先 skip=false 恢复拦截) | 彻底清除: action=remove (本机未实现单独卸载时会自动兜底为 setSkipAllPauses) 或重启进程")',
    '',
    '                        返回 (MCP_响应构建.命令成功_原始JSON (命令ID, ivIdemOut.到可读文本 (YYJSON格式化选项.压缩)))',
]


def main():
    txt = io.open(REV, encoding='utf-8', newline='').read()
    if OLD not in txt:
        if NEW[4] in txt or 'already_installed' in txt:
            print('· 已应用过, 跳过')
            return
        raise AssertionError('锚点未找到')
    assert txt.count(OLD) == 1, '锚点命中 %d 次' % txt.count(OLD)
    out = txt.replace(OLD, '\n'.join(NEW), 1)
    print('MCP_Server_Reverse.wsv: 行数 %d -> %d' % (len(txt.split('\n')), len(out.split('\n'))))
    if APPLY:
        io.open(REV, 'w', encoding='utf-8', newline='').write(out)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
