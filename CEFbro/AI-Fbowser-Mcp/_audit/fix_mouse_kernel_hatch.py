# -*- coding: utf-8 -*-
"""修复鼠标三件套的 kernel:true 逃生舱(此前形同虚设) + 删除随之产生的死代码。

## 实测/读码确认的缺陷
`browser_mouse_click` / `_move` / `_wheel` 三处在"CDP 派发失败"处加了**无条件** `返回 (命令失败 …)`,
但该失败文案里写着"如仍要内核注入请显式传 kernel:true" —— 而 `kernel:true` 只是**跳过 CDP 块**,
随即撞上同一个无条件失败返回, 于是:
  ① `kernel:true` 从不执行内核注入(逃生舱形同虚设, 且提示自相矛盾 —— 用户照提示重试必然再失败);
  ② 紧随其后的整段降级退路(VIP 内核注入 + CEF 事件派发)全部**永不可达**(死代码)。
`browser_mouse_click` 另有一处结构缺陷: CDP 路径被嵌在"VIP 控制器可用"分支内, 与 CDP 毫无关系,
导致 VIP 不可用时直接掉到 CEF 退路, 永远不试 CDP。

## 本次改动(三个分支统一为同一结构)
  参数校验 → 若 kernel≠true 走 CDP(成功即返回; 失败则**如实报错**, 不静默降级)
           → kernel=true 显示内核注入(真执行, 并如实告知会破坏 CDP 通道)
           → VIP 控制器不可用时退路: CEF 事件派发
顺带: 按钮文本→枚举映射只保留一份(原先 VIP 路径与退路各抄一份)。

## 自带校验: 分支定位靠花括号配对, 且改前逐条断言原文特征; 任一不符即中止不写入。
"""
import io
import os
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")

S = io.open(P, encoding="utf-8").read()
L = S.split("\n")


def is_code(line):
    s = line.strip()
    return not (s.startswith("//") or s.startswith("#") or s.startswith("@") or s == "")


def find_branch(name):
    """定位 `如果/否则 (方法名 == "name")` 分支: 返回 (start, end) 闭区间下标。

    注意: 分派链的**第一个**分支用 `如果`, 其余用 `否则`, 故两者都要认。
    """
    pat = '(方法名 == "%s")' % name
    hits = [i for i, l in enumerate(L)
            if (l.strip().startswith("否则 " + pat) or l.strip().startswith("如果 " + pat))]
    if len(hits) != 1:
        print("!! %s 分支预期 1 处, 实际 %d 处 -> 中止" % (name, len(hits)))
        sys.exit(2)
    i = hits[0]
    if L[i + 1].strip() != "{":
        print("!! %s: 分支头下一行不是 '{' -> 中止" % name)
        sys.exit(2)
    depth = 0
    j = i + 1
    while j < len(L):
        if is_code(L[j]):
            depth += L[j].count("{") - L[j].count("}")
        if depth == 0:
            break
        j += 1
    if L[j].strip() != "}":
        print("!! %s: 配平结束行不是 '}' -> 中止" % name)
        sys.exit(2)
    return i, j


CLICK = '''        否则 (方法名 == "browser_mouse_click")
        {
            变量 browser <类型 = 类_FBrowser_浏览器>
            browser = MCP命令服务器.取主浏览器 ()
            如果 (browser.是否为空 () == 假)
            {
                变量 x <类型 = 整数>
                变量 y <类型 = 整数>
                x = MCP命令服务器.yyjson取整数 (参数JSON, "x")
                y = MCP命令服务器.yyjson取整数 (参数JSON, "y")
                如果 (x < 0 || y < 0 || x > 32767 || y > 32767)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "坐标越界 | x,y 须在 0~32767 范围内"))
                }
                // 按钮文本→枚举只映射一份: 原先 VIP 路径与 CEF 退路各抄一份, 且字符串"right"当整数用会误按左键
                变量 按钮文本 <类型 = 文本型>
                按钮文本 = MCP命令服务器.yyjson取文本 (参数JSON, "button")
                变量 按钮类型 <类型 = 整数>
                如果 (按钮文本 == "right")
                {
                    按钮类型 = 鼠标按键类型.右键
                }
                否则 (按钮文本 == "middle")
                {
                    按钮类型 = 鼠标按键类型.中键
                }
                否则 (按钮文本 == "left" || 按钮文本 == "")
                {
                    按钮类型 = 鼠标按键类型.左键
                }
                否则
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "未知按钮类型: " + 按钮文本 + " | 支持: left/right/middle"))
                }
                变量 cdp按钮名 <类型 = 文本型>
                cdp按钮名 = 按钮文本
                如果 (cdp按钮名 == "")
                {
                    cdp按钮名 = "left"
                }
                // 缺省路径: CDP 派发(按下+抬起)。CDP 与 VIP 控制器无关, 故不再嵌在 VIP 分支内
                // (原先嵌在里面 -> VIP 不可用时永不尝试 CDP, 直接掉到 CEF 退路)
                如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "kernel") == 假)
                {
                    如果 (MCP命令服务器.CDP派发鼠标事件 ("mousePressed", x, y, cdp按钮名) && MCP命令服务器.CDP派发鼠标事件 ("mouseReleased", x, y, cdp按钮名))
                    {
                        返回 (MCP_响应构建.命令成功 (命令ID, "点击 (" + 到文本 (x) + "," + 到文本 (y) + ") 按钮:" + cdp按钮名 + " | 经 CDP 派发(不破坏 CDP 会话) | 如需内核级注入请传 kernel:true"))
                    }
                    // 失败不静默回退内核注入: 内核注入会让 CDP 通道在本会话内永久失效, 一次点击失败不该连累整场会话
                    返回 (MCP_响应构建.命令失败 (命令ID, "CDP 派发鼠标事件失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级注入 kernel:true; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe) | 可用替代: browser_element_action 点击元素 / browser_execute_js 派发事件"))
                }
                // kernel:true = 显式要求内核级注入(过反爬场景), 此处**确实执行**注入
                变量 vip_ctrl <类型 = 类_FBrowserVIP_控制器>
                vip_ctrl = browser.取VIP控制器 ()
                如果 (vip_ctrl.是否为空 () == 假)
                {
                    vip_ctrl.高级鼠标_单击 (x, y, 按钮类型)
                    返回 (MCP_响应构建.命令成功 (命令ID, "点击 (" + 到文本 (x) + "," + 到文本 (y) + ") 按钮:" + 按钮文本 + " | ⚠ 内核级鼠标注入: 实测会使 CDP 通道在本会话内失效(此后 CDP 优先工具退化), 需重启 AI-Fbowser-Mcp.exe 恢复"))
                }
                // VIP 控制器不可用时的退路: 普通 CEF 事件(不经内核, 也不破坏 CDP)
                变量 鼠标事件 <类型 = FBrowser_鼠标事件>
                鼠标事件.横坐标 = x
                鼠标事件.纵坐标 = y
                鼠标事件.修饰键 = 事件标识.无
                browser.发送鼠标点击事件 (按钮类型, 鼠标事件, 假, 1)
                browser.发送鼠标点击事件 (按钮类型, 鼠标事件, 真, 1)
                返回 (MCP_响应构建.命令成功 (命令ID, "点击 (" + 到文本 (x) + "," + 到文本 (y) + ") 按钮:" + 按钮文本 + " | 经 CEF 事件派发(VIP控制器不可用时的退路)"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
        }'''

MOVE = '''        否则 (方法名 == "browser_mouse_move")
        {
            变量 browser <类型 = 类_FBrowser_浏览器>
            browser = MCP命令服务器.取主浏览器 ()
            如果 (browser.是否为空 () == 假)
            {
                变量 x <类型 = 整数>
                变量 y <类型 = 整数>
                x = MCP命令服务器.yyjson取整数 (参数JSON, "x")
                y = MCP命令服务器.yyjson取整数 (参数JSON, "y")
                如果 (x < 0 || y < 0 || x > 32767 || y > 32767)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "坐标越界 | x,y 须在 0~32767 范围内"))
                }
                // 缺省路径: CDP Input.dispatchMouseEvent(真实输入事件, 不破坏 CDP 会话)
                如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "kernel") == 假)
                {
                    如果 (MCP命令服务器.CDP派发鼠标事件 ("mouseMoved", x, y))
                    {
                        返回 (MCP_响应构建.命令成功 (命令ID, "鼠标移动到 (" + 到文本 (x) + "," + 到文本 (y) + ") | 经 CDP Input.dispatchMouseEvent 派发(不破坏 CDP 会话) | 如需内核级注入请传 kernel:true"))
                    }
                    返回 (MCP_响应构建.命令失败 (命令ID, "CDP 派发鼠标事件失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级注入 kernel:true; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe) | 可用替代: browser_element_action / browser_execute_js 派发事件"))
                }
                // kernel:true = 显式要求内核级注入(过反爬场景), 此处**确实执行**注入
                变量 vip_ctrl <类型 = 类_FBrowserVIP_控制器>
                vip_ctrl = browser.取VIP控制器 ()
                如果 (vip_ctrl.是否为空 () == 假)
                {
                    vip_ctrl.高级鼠标_移动 (x, y)
                    返回 (MCP_响应构建.命令成功 (命令ID, "鼠标移动到 (" + 到文本 (x) + "," + 到文本 (y) + ") | ⚠ 内核级鼠标注入: 实测会使 CDP 通道在本会话内失效(此后 CDP 优先工具退化), 需重启 AI-Fbowser-Mcp.exe 恢复"))
                }
                // VIP 控制器不可用时的退路: 普通 CEF 鼠标移动事件
                变量 鼠标事件 <类型 = FBrowser_鼠标事件>
                鼠标事件.横坐标 = x
                鼠标事件.纵坐标 = y
                鼠标事件.修饰键 = 事件标识.无
                browser.发送鼠标移动事件 (鼠标事件, 假)
                返回 (MCP_响应构建.命令成功 (命令ID, "鼠标移动到 (" + 到文本 (x) + "," + 到文本 (y) + ") | 经 CEF 事件派发(VIP控制器不可用时的退路)"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
        }'''

WHEEL = '''        否则 (方法名 == "browser_mouse_wheel")
        {
            变量 browser <类型 = 类_FBrowser_浏览器>
            browser = MCP命令服务器.取主浏览器 ()
            如果 (browser.是否为空 () == 假)
            {
                变量 x <类型 = 整数>
                变量 y <类型 = 整数>
                变量 deltaX <类型 = 整数>
                变量 deltaY <类型 = 整数>
                x = MCP命令服务器.yyjson取整数 (参数JSON, "x")
                y = MCP命令服务器.yyjson取整数 (参数JSON, "y")
                deltaX = MCP命令服务器.yyjson取整数 (参数JSON, "delta_x")
                deltaY = MCP命令服务器.yyjson取整数 (参数JSON, "delta_y")
                如果 (x < 0 || y < 0 || x > 32767 || y > 32767)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "坐标越界 | x,y 须在 0~32767 范围内"))
                }
                如果 (deltaX < -10000 || deltaX > 10000 || deltaY < -10000 || deltaY > 10000)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "滚轮增量越界 | delta_x/delta_y 须在 ±10000 范围内"))
                }
                // 缺省路径: CDP 派发 mouseWheel
                如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "kernel") == 假)
                {
                    如果 (MCP命令服务器.CDP派发鼠标事件 ("mouseWheel", x, y, "left", deltaX, deltaY))
                    {
                        返回 (MCP_响应构建.命令成功 (命令ID, "滚轮 (" + 到文本 (x) + "," + 到文本 (y) + ") delta:" + 到文本 (deltaX) + "," + 到文本 (deltaY) + " | 经 CDP 派发(不破坏 CDP 会话) | 如需内核级注入请传 kernel:true"))
                    }
                    返回 (MCP_响应构建.命令失败 (命令ID, "CDP 派发鼠标事件失败: 本会话 CDP 通道已不可用(常见诱因是先前调用过内核级注入 kernel:true; 该失效在会话内不可恢复, 需重启 AI-Fbowser-Mcp.exe) | 可用替代: browser_element_action / browser_execute_js 派发事件"))
                }
                // kernel:true = 显式要求内核级注入(过反爬场景), 此处**确实执行**注入
                变量 vip_ctrl <类型 = 类_FBrowserVIP_控制器>
                vip_ctrl = browser.取VIP控制器 ()
                如果 (vip_ctrl.是否为空 () == 假)
                {
                    vip_ctrl.高级鼠标_滚轮滚动 (x, y, deltaX, deltaY)
                    返回 (MCP_响应构建.命令成功 (命令ID, "滚轮 (" + 到文本 (x) + "," + 到文本 (y) + ") delta:" + 到文本 (deltaX) + "," + 到文本 (deltaY) + " | ⚠ 内核级鼠标注入: 实测会使 CDP 通道在本会话内失效(此后 CDP 优先工具退化), 需重启 AI-Fbowser-Mcp.exe 恢复"))
                }
                // VIP 控制器不可用时的退路: 普通 CEF 鼠标滚轮事件
                变量 鼠标事件 <类型 = FBrowser_鼠标事件>
                鼠标事件.横坐标 = x
                鼠标事件.纵坐标 = y
                鼠标事件.修饰键 = 事件标识.无
                browser.发送鼠标滚轮事件 (鼠标事件, deltaX, deltaY)
                返回 (MCP_响应构建.命令成功 (命令ID, "滚轮 (" + 到文本 (x) + "," + 到文本 (y) + ") delta:" + 到文本 (deltaX) + "," + 到文本 (deltaY) + " | 经 CEF 事件派发(VIP控制器不可用时的退路)"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_无浏览器))
        }'''

JOBS = [("browser_mouse_click", CLICK, ["CDP派发鼠标事件", "发送鼠标点击事件"]),
        ("browser_mouse_move", MOVE, ["CDP派发鼠标事件", "高级鼠标_移动", "发送鼠标移动事件"]),
        ("browser_mouse_wheel", WHEEL, ["CDP派发鼠标事件", "高级鼠标_滚轮滚动", "发送鼠标滚轮事件"])]

# click 分支的缺陷特征: 内核注入调用**不存在**(上一轮已作为死代码删除), 因为该分支的
# kernel:true 路径被无条件失败返回挡死; 本脚本正是要把它补回成真正可用的 kernel:true 分支。
MUST_ABSENT = {"browser_mouse_click": "高级鼠标_单击"}

# ---- 1) 定位并逐条断言改前特征 ----
spans = []
for name, new, must in JOBS:
    a, b = find_branch(name)
    body = "\n".join(L[a:b + 1])
    for m in must:
        if m not in body:
            print("!! %s 分支内未找到特征串 %s -> 中止(源码可能已变)" % (name, m))
            sys.exit(2)
    absent = MUST_ABSENT.get(name)
    if absent and absent in body:
        print("!! %s 分支内意外出现 %s -> 中止(前提已变, 需重新读码)" % (name, absent))
        sys.exit(2)
    spans.append((a, b, name, new, body.count("\n") + 1))
    print("定位 %-22s 行 %d-%d (%d 行)" % (name, a + 1, b + 1, body.count("\n") + 1))

# ---- 2) 从后往前替换(避免行号位移) ----
new_lines = list(L)
for a, b, name, new, _ in sorted(spans, key=lambda x: -x[0]):
    new_lines[a:b + 1] = new.split("\n")
    print("已替换 %s" % name)

out = "\n".join(new_lines)
io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print("\n行数: %d -> %d" % (len(L), len(new_lines)))

# ---- 3) 写后自检: 死代码必须消失, kernel 分支必须真的注入 ----
chk = io.open(P, encoding="utf-8").read()
tail_fail = chk.count('如仍要内核注入请显式传 kernel:true(会确认 CDP 已失效)')
print("自检: 旧的自相矛盾失败文案残留 = %d (应为 0)" % tail_fail)
print("自检: 内核注入调用 高级鼠标_单击/移动/滚轮滚动 各 %d/%d/%d 次 (应各 1)"
      % (chk.count("高级鼠标_单击"), chk.count("高级鼠标_移动"), chk.count("高级鼠标_滚轮滚动")))
print("自检: kernel:true 说明注释 %d 处 (应为 3)" % chk.count("此处**确实执行**注入"))
if tail_fail != 0:
    print("!! 自检未通过")
    sys.exit(1)
print("OK")
