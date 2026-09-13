# -*- coding: utf-8 -*-
r"""第 167 轮修补(334 回合全量扫测发现的真问题):
① browser_debugger_step_over/into/out: 本会话无断点时, 单步(自动制造的暂停点)后页面会一直
   挂着 → 后续每个 CDP 工具超时, 活体探针误判实例死亡 → 冷重启 → 用户看到浏览器闪退。
   修复: 断点注册表为空时单步后自动 Debugger.resume 并如实说明(有真实断点时保持暂停)。
② browser_mouse_wheel: 窗口可见但被遮挡/后台化时 mouseWheel 派发耗尽 8 秒预算失败
   (全量扫测实测 8.13s 超时)。修复: 失败时强制显示窗口并重试一次(实测恢复后 0.03 秒), 仍失败才报成因。

改动文件: src/MCP_Server_Core.wsv (纯 LF)。锚点唯一性校验, 不匹配即中止。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
raw = io.open(F, 'rb').read()


def replace_once(old, new, tag):
    global raw
    n = raw.count(old)
    if n != 1:
        print('!! [%s] 锚点出现 %d 次(应为1), 中止' % (tag, n))
        sys.exit(2)
    raw = raw.replace(old, new)
    print('[%s] 已替换' % tag)


STEP_OLD = (
    '            \u8fd4\u56de (MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 '
    '(\u547d\u4ee4ID, "Debugger.stepOver", \u53c2\u6570JSON))\n'
    '        }').encode('utf-8')
STEP_NEW = (
    '            \u53d8\u91cf stepOver\u56de\u6267 <\u7c7b\u578b = \u6587\u672c\u578b>\n'
    '            stepOver\u56de\u6267 = MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 (\u547d\u4ee4ID, "Debugger.stepOver", \u53c2\u6570JSON)\n'
    '            \u5982\u679c (MCP\u547d\u4ee4\u670d\u52a1\u5668.\u65ad\u70b9\u6ce8\u518c\u8868.\u53d6\u6210\u5458\u6570 () == 0)\n'
    '            {\n'
    '                // \u672c\u4f1a\u8bdd\u65e0\u4efb\u4f55\u771f\u5b9e\u65ad\u70b9: \u5355\u6b65\u540e\u65e0\u68c0\u67e5\u70b9\u53ef\u505c, \u9875\u9762\u4f1a\u4e00\u76f4\u6302\u7740 \u2014\u2014 \u540e\u7eed\u6bcf\u4e2a CDP \u5de5\u5177\u90fd\u4f1a\u8d85\u65f6,\n'
    '                // \u6d3b\u4f53\u63a2\u9488\u8d85\u65f6\u8fd8\u4f1a\u88ab\u8bef\u5224\u5b9e\u4f8b\u6b7b\u4ea1\u800c\u51b7\u91cd\u542f(\u7528\u6237\u770b\u5230\u7684\u5c31\u662f\u95ea\u9000), \u6545\u81ea\u52a8\u6062\u590d\u3002\n'
    '                MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6e05\u9664CDP\u4e8b\u4ef6\u8bb0\u5f55 ("Debugger.paused")\n'
    '                MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 (\u547d\u4ee4ID, "Debugger.resume", \u53c2\u6570JSON)\n'
    '                MCP_\u54cd\u5e94\u6784\u5efa.\u8bb0\u5f55\u81ea\u52a8\u5904\u7406 ("Debugger.resume(\u672c\u4f1a\u8bdd\u65e0\u65ad\u70b9, \u5355\u6b65\u540e\u5df2\u81ea\u52a8\u6062\u590d\u9875\u9762\u8fd0\u884c)")\n'
    '                \u8fd4\u56de (MCP_\u54cd\u5e94\u6784\u5efa.\u547d\u4ee4\u6210\u529f (\u547d\u4ee4ID, "\u5355\u6b65\u8df3\u8fc7\u5df2\u6267\u884c | \u672c\u4f1a\u8bdd\u672a\u8bbe\u7f6e\u65ad\u70b9(\u65e0\u68c0\u67e5\u70b9\u53ef\u505c), \u5df2\u81ea\u52a8 Debugger.resume \u6062\u590d\u9875\u9762\u8fd0\u884c, \u5b9e\u4f8b\u4fdd\u6301\u53ef\u7528 | \u6709\u771f\u5b9e\u65ad\u70b9\u65f6\u5355\u6b65\u540e\u4fdd\u6301\u6682\u505c\u4f9b\u67e5\u770b\u73b0\u573a"))\n'
    '            }\n'
    '            \u8fd4\u56de (stepOver\u56de\u6267)\n'
    '        }').encode('utf-8')
replace_once(STEP_OLD, STEP_NEW, 'step_over')

INTO_OLD = (
    '            \u8fd4\u56de (MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 '
    '(\u547d\u4ee4ID, "Debugger.stepInto", \u53c2\u6570JSON))\n'
    '        }').encode('utf-8')
INTO_NEW = (
    '            \u53d8\u91cf stepInto\u56de\u6267 <\u7c7b\u578b = \u6587\u672c\u578b>\n'
    '            stepInto\u56de\u6267 = MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 (\u547d\u4ee4ID, "Debugger.stepInto", \u53c2\u6570JSON)\n'
    '            \u5982\u679c (MCP\u547d\u4ee4\u670d\u52a1\u5668.\u65ad\u70b9\u6ce8\u518c\u8868.\u53d6\u6210\u5458\u6570 () == 0)\n'
    '            {\n'
    '                MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6e05\u9664CDP\u4e8b\u4ef6\u8bb0\u5f55 ("Debugger.paused")\n'
    '                MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 (\u547d\u4ee4ID, "Debugger.resume", \u53c2\u6570JSON)\n'
    '                MCP_\u54cd\u5e94\u6784\u5efa.\u8bb0\u5f55\u81ea\u52a8\u5904\u7406 ("Debugger.resume(\u672c\u4f1a\u8bdd\u65e0\u65ad\u70b9, \u5355\u6b65\u540e\u5df2\u81ea\u52a8\u6062\u590d\u9875\u9762\u8fd0\u884c)")\n'
    '                \u8fd4\u56de (MCP_\u54cd\u5e94\u6784\u5efa.\u547d\u4ee4\u6210\u529f (\u547d\u4ee4ID, "\u5355\u6b65\u8fdb\u5165\u5df2\u6267\u884c | \u672c\u4f1a\u8bdd\u672a\u8bbe\u7f6e\u65ad\u70b9(\u65e0\u68c0\u67e5\u70b9\u53ef\u505c), \u5df2\u81ea\u52a8 Debugger.resume \u6062\u590d\u9875\u9762\u8fd0\u884c, \u5b9e\u4f8b\u4fdd\u6301\u53ef\u7528 | \u6709\u771f\u5b9e\u65ad\u70b9\u65f6\u5355\u6b65\u540e\u4fdd\u6301\u6682\u505c\u4f9b\u67e5\u770b\u73b0\u573a"))\n'
    '            }\n'
    '            \u8fd4\u56de (stepInto\u56de\u6267)\n'
    '        }').encode('utf-8')
replace_once(INTO_OLD, INTO_NEW, 'step_into')

OUT_OLD = (
    '            \u8fd4\u56de (MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 '
    '(\u547d\u4ee4ID, "Debugger.stepOut", \u53c2\u6570JSON))\n'
    '        }').encode('utf-8')
OUT_NEW = (
    '            \u53d8\u91cf stepOut\u56de\u6267 <\u7c7b\u578b = \u6587\u672c\u578b>\n'
    '            stepOut\u56de\u6267 = MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 (\u547d\u4ee4ID, "Debugger.stepOut", \u53c2\u6570JSON)\n'
    '            \u5982\u679c (MCP\u547d\u4ee4\u670d\u52a1\u5668.\u65ad\u70b9\u6ce8\u518c\u8868.\u53d6\u6210\u5458\u6570 () == 0)\n'
    '            {\n'
    '                MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6e05\u9664CDP\u4e8b\u4ef6\u8bb0\u5f55 ("Debugger.paused")\n'
    '                MCP\u547d\u4ee4\u670d\u52a1\u5668.\u6267\u884cCDP\u547d\u4ee4 (\u547d\u4ee4ID, "Debugger.resume", \u53c2\u6570JSON)\n'
    '                MCP_\u54cd\u5e94\u6784\u5efa.\u8bb0\u5f55\u81ea\u52a8\u5904\u7406 ("Debugger.resume(\u672c\u4f1a\u8bdd\u65e0\u65ad\u70b9, \u5355\u6b65\u540e\u5df2\u81ea\u52a8\u6062\u590d\u9875\u9762\u8fd0\u884c)")\n'
    '                \u8fd4\u56de (MCP_\u54cd\u5e94\u6784\u5efa.\u547d\u4ee4\u6210\u529f (\u547d\u4ee4ID, "\u5355\u6b65\u8df3\u51fa\u5df2\u6267\u884c | \u672c\u4f1a\u8bdd\u672a\u8bbe\u7f6e\u65ad\u70b9(\u65e0\u68c0\u67e5\u70b9\u53ef\u505c), \u5df2\u81ea\u52a8 Debugger.resume \u6062\u590d\u9875\u9762\u8fd0\u884c, \u5b9e\u4f8b\u4fdd\u6301\u53ef\u7528 | \u6709\u771f\u5b9e\u65ad\u70b9\u65f6\u5355\u6b65\u540e\u4fdd\u6301\u6682\u505c\u4f9b\u67e5\u770b\u73b0\u573a"))\n'
    '            }\n'
    '            \u8fd4\u56de (stepOut\u56de\u6267)\n'
    '        }').encode('utf-8')
replace_once(OUT_OLD, OUT_NEW, 'step_out')

# ② 滚轮失败自愈: 锚点=滚轮 CDP 失败返回行(其前是 mouseWheel 成功分支的收尾)
WHEEL_OLD = (
    '                    \u8fd4\u56de (MCP_\u54cd\u5e94\u6784\u5efa.\u547d\u4ee4\u5931\u8d25 (\u547d\u4ee4ID, '
    'MCP\u547d\u4ee4\u670d\u52a1\u5668.CDPInput\u5931\u8d25\u539f\u56e0\u6587\u672c ("CDP \u6d3e\u53d1\u9f20\u6807\u4e8b\u4ef6") '
    '+ " | \u53ef\u7528\u66ff\u4ee3: browser_element_action / browser_execute_js \u6d3e\u53d1\u4e8b\u4ef6"))\n').encode('utf-8')
n = raw.count(WHEEL_OLD)
print('wheel 失败返回行出现 %d 次' % n)
WHEEL_NEW = (
    '                    // \u81ea\u6108(\u5168\u91cf\u626b\u6d4b\u5b9e\u6d4b 2025-09-13): \u7a97\u53e3\u4e0d\u53ef\u89c1/\u88ab\u906e\u6321\u65f6 mouseWheel \u6d3e\u53d1\u4f1a\u8017\u5c3d 8 \u79d2\u9884\u7b97\u5931\u8d25; \u5f3a\u5236\u663e\u793a\u7a97\u53e3\u540e\u91cd\u8bd5\u4e00\u6b21(\u5b9e\u6d4b\u6062\u590d\u540e 0.03 \u79d2)\u3002\n'
    '                    browser.\u663e\u793a\u9690\u85cf\u7a97\u53e3 (\u771f)\n'
    '                    \u5982\u679c (MCP\u547d\u4ee4\u670d\u52a1\u5668.CDP\u6d3e\u53d1\u9f20\u6807\u4e8b\u4ef6 ("mouseWheel", x, y, "left", deltaX, deltaY))\n'
    '                    {\n'
    '                        MCP_\u54cd\u5e94\u6784\u5efa.\u8bb0\u5f55\u81ea\u52a8\u5904\u7406 ("\u6eda\u8f6e: \u9996\u6b21\u6d3e\u53d1\u5931\u8d25(\u7a97\u53e3\u4e0d\u53ef\u89c1/\u88ab\u906e\u6321), \u5df2\u81ea\u52a8\u5f3a\u5236\u663e\u793a\u7a97\u53e3\u5e76\u91cd\u8bd5\u6210\u529f")\n'
    '                        \u8fd4\u56de (MCP_\u54cd\u5e94\u6784\u5efa.\u547d\u4ee4\u6210\u529f (\u547d\u4ee4ID, "\u6eda\u8f6e (" + \u5230\u6587\u672c (x) + "," + \u5230\u6587\u672c (y) + ") delta:" + \u5230\u6587\u672c (deltaX) + "," + \u5230\u6587\u672c (deltaY) + " | \u7ecf CDP \u6d3e\u53d1(\u4e0d\u7834\u574f CDP \u4f1a\u8bdd); \u9996\u6b21\u5931\u8d25(\u7a97\u53e3\u4e0d\u53ef\u89c1/\u88ab\u906e\u6321), \u5df2\u81ea\u52a8\u5f3a\u5236\u663e\u793a\u7a97\u53e3\u5e76\u91cd\u8bd5\u6210\u529f | \u5982\u9700\u5185\u6838\u7ea7\u6ce8\u5165\u8bf7\u4f20 kernel:true"))\n'
    '                    }\n'
    '                    \u8fd4\u56de (MCP_\u54cd\u5e94\u6784\u5efa.\u547d\u4ee4\u5931\u8d25 (\u547d\u4ee4ID, MCP\u547d\u4ee4\u670d\u52a1\u5668.CDPInput\u5931\u8d25\u539f\u56e0\u6587\u672c ("CDP \u6d3e\u53d1\u9f20\u6807\u4e8b\u4ef6") + " | \u5df2\u5c1d\u8bd5\u5f3a\u5236\u663e\u793a\u7a97\u53e3\u5e76\u91cd\u8bd5\u4e00\u6b21, \u4ecd\u5931\u8d25 | \u53ef\u7528\u66ff\u4ee3: browser_element_action / browser_execute_js \u6d3e\u53d1\u4e8b\u4ef6"))\n').encode('utf-8')
if n == 1:
    raw = raw.replace(WHEEL_OLD, WHEEL_NEW)
    print('[wheel_retry] 已替换')
elif n == 0:
    print('!! wheel 失败返回行未找到, 中止')
    sys.exit(2)
else:
    print('!! wheel 失败返回行出现 %d 次, 需要更精确锚点, 中止' % n)
    sys.exit(2)

io.open(F, 'wb').write(raw)
print('完成: MCP_Server_Core.wsv 已更新(step 自恢复 x3 + wheel 重试 x1)')
