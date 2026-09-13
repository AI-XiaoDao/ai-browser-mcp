# -*- coding: utf-8 -*-
r"""补能力: 鼠标事件转触摸事件(CDP 路线), 挂在 browser_vip_touch_emulation 上, 不新增工具。

依据(只读缺口审计): 类库 `高级_设置触发鼠标触摸事件 (启用, 配置 0=MOBILE/1=DESKTOP)`(FBroVip.wsv:623-628,
导出 FBroHsVIPControl_SetEmitTouchEventsForMouse = CEF Emulation.setEmitTouchEventsForMouse)在全项目**零调用**;
项目只有"触摸仿真开关", 没有"鼠标转触摸"这一档。
路线选择: 走 **CDP** `Emulation.setEmitTouchEventsForMouse`(与项目既有 Emulation.setFocusEmulationEnabled 同源),
**不走内核级注入** —— 项目已实测内核级注入会使本会话 CDP 通道失效, 而 CDP 路线不需要启用 JS 执行环境、也不需要刷新。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

ANCHOR = '''            变量 vipTouch <类型 = 类_FBrowserVIP_控制器>
            vipTouch = MCP命令服务器.取VIP控制器 ()'''
NEW = '''            // mode=mouse: 鼠标事件转触摸事件(**CDP 路线**)。
            // 实测结论: 内核级注入会让本会话 CDP 通道失效, 而 CDP 的 Emulation.setEmitTouchEventsForMouse
            // 不需要启用 JS 执行环境、不需要刷新页面, 也不会破坏 CDP 通道 —— 故优先提供这条。
            变量 触摸模式 <类型 = 文本型>
            触摸模式 = MCP命令服务器.yyjson取文本 (参数JSON, "mode")
            如果 (触摸模式 == "mouse")
            {
                变量 转触摸配置 <类型 = 文本型>
                转触摸配置 = MCP命令服务器.yyjson取文本 (参数JSON, "configuration")
                如果 (转触摸配置 == "")
                {
                    转触摸配置 = "mobile"
                }
                如果 (转触摸配置 != "mobile" && 转触摸配置 != "desktop")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "configuration 只支持 mobile / desktop | mobile=视口按移动端触摸布局, desktop=按桌面端"))
                }
                变量 转触摸启用 <类型 = 逻辑型>
                转触摸启用 = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")
                变量 转触摸参数 <类型 = 文本型>
                如果 (转触摸启用)
                {
                    转触摸参数 = "{\\"enabled\\":true,\\"configuration\\":\\"" + 转触摸配置 + "\\"}"
                }
                否则
                {
                    转触摸参数 = "{\\"enabled\\":false}"
                }
                变量 转触摸结果 <类型 = 文本型>
                转触摸结果 = MCP命令服务器.执行CDP并同步等待 ("mcp_emittouch_" + 到文本 (取启动时间 ()), "Emulation.setEmitTouchEventsForMouse", 转触摸参数, 8000)
                如果 (MCP命令服务器.CDP同步结果是否成功 (转触摸结果) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "CDP Emulation.setEmitTouchEventsForMouse 失败: " + MCP命令服务器.取CDP同步结果错误 (转触摸结果) + " | 可用替代: browser_vip_touch_emulation {enable:true, max_points:N}(内核级触摸仿真, 需刷新页面)"))
                }
                如果 (转触摸启用)
                {
                    返回 (MCP_响应构建.命令成功 (命令ID, "鼠标事件已转为触摸事件(CDP Emulation.setEmitTouchEventsForMouse): configuration=" + 转触摸配置 + " | 撤销: 同参数传 enable=false"))
                }
                返回 (MCP_响应构建.命令成功 (命令ID, "已关闭鼠标转触摸(CDP)"))
            }
            如果 (vipTouch.是否为空 () == 假)''' + '\n' + ANCHOR

DESC_OLD = '添加工具JSON ("browser_vip_touch_emulation", "VIP: 触摸事件模拟", 多属性Schema文本 (属性项JSON ("enable", "boolean", "启用") + "," + 属性项JSON ("max_points", "integer", "最大触摸点"), ""))'
DESC_NEW = ('添加工具JSON ("browser_vip_touch_emulation", "触摸/鼠标转触摸: 缺省或 mode 非 mouse 时走 VIP 内核级触摸仿真(需刷新页面); '
            'mode=mouse 时走 **CDP Emulation.setEmitTouchEventsForMouse**(把鼠标事件转成触摸事件, 不需刷新、不破坏 CDP 通道, 用 configuration 选 mobile/desktop, enable=false 撤销)", '
            '多属性Schema文本 (属性项JSON ("enable", "boolean", "启用(true)/撤销(false)") + "," + 属性项JSON ("max_points", "integer", "最大触摸点(仅内核级路径用)") '
            '+ "," + 属性项JSON ("mode", "text", "mouse=走 CDP 鼠标转触摸; 缺省=VIP 内核级触摸仿真") '
            '+ "," + 属性项JSON ("configuration", "text", "mode=mouse 时: mobile(默认)/desktop"), ""))')


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == [x.strip() for x in block]]


def nets(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@') or st.startswith('//') or st.startswith('#'):
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
                elif c == '(':
                    p += 1
                elif c == ')':
                    p -= 1
                elif c == '{':
                    b += 1
                elif c == '}':
                    b -= 1
            k += 1
    return p, b


def main():
    raw = open(VIP, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw, 'VIP 编码/行尾异常'
    vtxt = raw.decode('utf-8')
    assert 'setEmitTouchEventsForMouse' not in vtxt, '已应用过'
    vlines = vtxt.split('\n')
    hits = find_block(vlines, ANCHOR.split('\n'))
    assert len(hits) == 1, 'VIP 锚点命中 %d 次' % len(hits)
    s = hits[0]
    p0, b0 = nets(vlines)
    vout = vlines[:s] + NEW.split('\n') + vlines[s + len(ANCHOR.split('\n')):]
    p1, b1 = nets(vout)
    assert (p1, b1) == (p0, b0), 'VIP 净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)

    sraw = open(SRV, 'rb').read()
    assert not sraw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in sraw
    stxt = sraw.decode('utf-8')
    n = stxt.count(DESC_OLD)
    assert n == 1, '描述锚点命中 %d 次' % n
    sout = stxt.replace(DESC_OLD, DESC_NEW)
    print('VIP 分支 @%d (+%d 行); 描述已更新; 净额不变' % (s + 1, len(NEW.split('\n')) - len(ANCHOR.split('\n'))))
    if '--apply' in sys.argv:
        with io.open(VIP, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(vout))
        with io.open(SRV, 'w', encoding='utf-8', newline='\n') as f:
            f.write(sout)
        print('已写入两个文件')
    else:
        print('[dry-run] 未落盘')


main()
