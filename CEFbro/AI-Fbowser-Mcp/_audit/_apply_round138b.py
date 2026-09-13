# -*- coding: utf-8 -*-
r"""第138轮补丁 B: `browser_close_try` 从"恒失败(已废弃)"改成**真正可用且带安全闸门**的关闭入口。

## 现状(实测)
· 工具在 tools/list 里显示, 描述写着 `[已废弃] … ⛔ 该工具恒失败, 请改用 browser_close`;
· 实现分支无条件返回失败 —— 属"显示出来却永远做不到事"的 dead-end
  (静态扫描 `_audit/scan_deadends.py` 在 323 个已显示工具里只命中这 1 个)。
· 背景事实(见 `browser_close` 的描述): 类库的 `尝试关闭浏览器(TryCloseBrowser)` 在本项目**恒返回假**
  (没有类库要求的"顶层窗口关闭处理器"), 所以老实现注定失败 —— 这不是参数问题, 是路径不存在。

## 修法(转发复用, 不重复造轮子)
把 `browser_close_try` 变成**统一的关闭入口**, 两条路径都直接转发到既有实现:
1. 传了 `browser_id` 且**不是主浏览器** → 转发 `browser_close`(后台/其它浏览器会被真正关闭, 已实测可关);
2. 目标是主窗口(未传 id 或 id 就是主浏览器) → 关闭它等于退出整个 MCP 服务, 故需显式 `confirm:true`
   (此时转发 `browser_shutdown` 的安全关闭序列, 延迟钳制 1~3 秒); 不带 confirm 时**明确拒绝**并给替代 ——
   属目标允许的"需确认"类, 不再是 dead-end。

顺带更正 `browser_close` 描述里那句会误导的指引(`见 browser_close_try 的失败文案`)。

用法: py -3 _audit\_apply_round138b.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

CORE_OLD = '''        // 浏览器关闭入口: 本服务统一走 browser_close / browser_shutdown, 不经此段
        否则 (方法名 == "browser_close_try")
        {
            返回 (MCP_响应构建.命令失败 (命令ID, "⛔ 远程关闭浏览器已禁用(本工具刻意不实现) | 真实原因: 本项目是控制台程序, 浏览器窗口**就是**程序窗口, 关闭浏览器等于退出整个 MCP 服务(见 docs: 关闭浏览器窗口会退出整个程序), 因此不提供 API 关闭入口 —— 旧文案称'由GUI管理'与代码事实不符, 已按实测更正 | 想关闭请用 browser_close(可指定 browser_id 只关后台浏览器) 或 browser_shutdown(需 confirm:true)"))
        }'''

CORE_NEW = '''        // 浏览器关闭入口: 统一入口, 两条路径都**转发**到既有实现(不另写一份关闭逻辑)
        否则 (方法名 == "browser_close_try")
        {
            // 类库的 尝试关闭浏览器(TryCloseBrowser) 在本项目恒返回假(没有它要求的"顶层窗口关闭处理器"),
            // 故这里**不调用它**, 而是按目标分类转发:
            // · browser_id 指向非主浏览器 → browser_close(真正关闭, 实测可关后台浏览器)
            // · 指向主窗口(未传 id / id 就是主浏览器) → 关它等于退出整个 MCP 服务 ⇒ 需 confirm:true,
            //   转发 browser_shutdown 的安全关闭序列(响应先返回, 关闭经 UI 时钟延迟 1~3 秒执行)
            变量 ctID <类型 = 整数>
            ctID = MCP命令服务器.yyjson取整数 (参数JSON, "browser_id")
            变量 ct确认 <类型 = 逻辑型>
            ct确认 = MCP命令服务器.yyjson取逻辑 (参数JSON, "confirm")
            变量 ct主浏览器 <类型 = 类_FBrowser_浏览器>
            ct主浏览器 = MCP命令服务器.取主浏览器 ()
            变量 ct主ID <类型 = 整数 值 = 0>
            如果 (ct主浏览器.是否为空 () == 假 && ct主浏览器.是否已关闭 () == 假)
            {
                ct主ID = ct主浏览器.取ID ()
            }
            如果 (ctID > 0 && ctID != ct主ID)
            {
                返回 (MCP_核心分派.分类分派_核心操作 (命令ID, "browser_close", 参数JSON))
            }
            如果 (ct确认)
            {
                返回 (MCP_系统分派.分类分派_系统操作 (命令ID, "browser_shutdown", 参数JSON))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "关闭主浏览器窗口等于退出整个 AI-Fbowser-Mcp.exe 服务(MCP 连接会一起断开), 故需显式 confirm:true —— 加上 confirm:true 就会执行安全关闭(响应先返回, 1~3 秒后退出) | 只想关后台/其它浏览器: 传 browser_id=<browser_list 里的 id>, 本工具会直接关闭它 | 只想离开当前页面: browser_navigate 到其它地址"))
        }'''

DESC_OLD = '''添加工具JSON ("browser_close_try", "[已废弃] 关闭浏览器, 已替换为 browser_close | ⛔ 该工具恒失败, 请改用 browser_close")'''
DESC_NEW = '''添加工具JSON ("browser_close_try", "关闭浏览器(统一入口, 带安全闸门) | ①传 browser_id 且不是主浏览器 → 真正关闭它(与 browser_close 等价); ②目标是主窗口(未传 id / id 就是主浏览器) → 关闭它等于退出整个 AI-Fbowser-Mcp.exe 服务(MCP 连接一起断开), 故需 confirm:true, 此时执行与 browser_shutdown 相同的安全关闭(响应先返回, 1~3 秒后退出); 不带 confirm 会明确拒绝并给出替代 | 实测说明: 类库的 尝试关闭浏览器(TryCloseBrowser) 在本项目恒返回假(没有它要求的顶层窗口关闭处理器), 故本工具不再依赖它, 而是转发到 browser_close / browser_shutdown 两条可用路径", 多属性Schema文本 (属性项JSON ("browser_id", "integer", "要关闭的浏览器ID(省略=主窗口, 需 confirm:true)") + "," + 属性项JSON ("confirm", "boolean", "关闭**主窗口**(=退出整个程序)必须显式传 true; 关后台浏览器不需要") + "," + 属性项JSON ("delay_seconds", "integer", "confirm:true 时的关闭延迟秒数(1~3, 默认1)"), ""))'''

CLOSE_DESC_OLD = '''要关闭请直接用本工具(见 browser_close_try 的失败文案)"'''
CLOSE_DESC_NEW = '''要关闭请直接用本工具(browser_close_try 现在是它的别名入口: 传 browser_id 时两者等价)"'''


def patch(path, edits, name):
    txt = io.open(path, encoding='utf-8', newline='').read()
    n0 = len(txt.split('\n'))
    for tag, old, new in edits:
        if old in txt:
            assert txt.count(old) == 1, '%s / %s 锚点命中 %d 次' % (name, tag, txt.count(old))
            txt = txt.replace(old, new, 1)
            print('   · %s' % tag)
        else:
            print('   · %s —— 已应用过/未找到, 跳过' % tag)
    print('%s: 行数 %d -> %d' % (name, n0, len(txt.split('\n'))))
    if APPLY:
        io.open(path, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 %s' % os.path.basename(path))


def main():
    print('== 第138轮补丁 B (%s) ==' % ('应用' if APPLY else '预演'))
    patch(CORE, [('browser_close_try 改为转发复用', CORE_OLD, CORE_NEW)], 'MCP_Server_Core.wsv')
    patch(SERVER, [('描述: close_try 改为统一入口', DESC_OLD, DESC_NEW),
                   ('描述: close 里的过期指引更正', CLOSE_DESC_OLD, CLOSE_DESC_NEW)], 'MCP_Server.wsv')
    if not APPLY:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
