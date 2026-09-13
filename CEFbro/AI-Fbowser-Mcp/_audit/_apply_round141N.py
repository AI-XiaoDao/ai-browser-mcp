# -*- coding: utf-8 -*-
r"""第141轮补丁 N: `browser_screenshot` 改走 **CDP `Page.captureScreenshot`**(默认), 类库路径降级为显式选项。

## 实测(本轮, 两臂对照)
| 路线 | 截图本身 | **截图后的 CDP 命令通道** |
|---|---|---|
| 类库 `高级_网页截图`(内核/VIP 路线) | 正常(0.05s) | **被打死**: 之后所有 CDP 命令(原始 `Runtime.evaluate`/`execute_js`/`debugger_enable`/`dom_query`)响应**永不到达**, 只能靠原生回退在 10~35s 后勉强返回或直接超时; **注销+重挂 CDP 观察者都救不回来** |
| CDP `Page.captureScreenshot` | 正常(0.04s, 整页 0.17s) | **完全健康**: 之后 `execute_js` 仍 0.03s(截图前后各测两次) |

⇒ 截图原本是"用一次就把会话搞残"的工具: 用户看到的正是"截完图之后每个工具都要等半分钟、甚至连续失败"。
修法(不重复造轮子 —— CDP 本就是项目主通道):
1. 新增 `CDP截图` 助手: 走 `Page.captureScreenshot`(支持 format/quality/fromSurface/captureBeyondViewport/clip),
   结果直接回包(同步, 无需 mcp_result);
2. `browser_screenshot` 默认走 CDP; CDP 不可用/失败时**明确失败**并给出可行动指引;
3. `via:"library"` 才走类库路线(并在回包里**如实警告**它会让本会话 CDP 命令通道失效);
4. 类库路线的质量/表面/视窗之外/整页参数保持不变(仍可显式选用)。

用法: py -3 _audit\_apply_round141N.py [--apply]
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

# ── N2: 在解析完参数之后、调用类库之前, 插入 CDP 优先尝试 ──
CDP_INSERT_ANCHOR = '''                    // 全部异步: 生成task_id, 回调触发时存储结果
                    变量 异步截图ID <类型 = 文本型>'''
CDP_INSERT_NEW = '''                    // ── 默认走 CDP(Page.captureScreenshot): 实测它**不破坏** CDP 命令通道 ──
                    变量 截图路线 <类型 = 文本型>
                    截图路线 = MCP命令服务器.yyjson取文本 (参数JSON, "via")
                    如果 (截图路线 == "")
                    {
                        截图路线 = "cdp"
                    }
                    如果 (截图路线 != "cdp" && 截图路线 != "library")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "via 只接受 cdp(默认)/library | library = 类库内核路线, **实测会让本会话 CDP 命令通道失效**, 仅在你确知后果时显式选用"))
                    }
                    如果 (截图路线 == "cdp")
                    {
                        变量 cdpClip <类型 = YYJSON对象类>
                        cdpClip.创建自文本 ("{}")
                        cdpClip.加入整数成员 ("x", 截图大小.横坐标)
                        cdpClip.加入整数成员 ("y", 截图大小.纵坐标)
                        cdpClip.加入整数成员 ("width", 截图大小.宽度)
                        cdpClip.加入整数成员 ("height", 截图大小.高度)
                        cdpClip.加入整数成员 ("scale", 截图大小.缩放)
                        变量 cdp截图参数 <类型 = YYJSON对象类>
                        cdp截图参数.创建自文本 ("{}")
                        cdp截图参数.加入文本成员 ("format", fmt)
                        如果 (fmt != "png")
                        {
                            cdp截图参数.加入整数成员 ("quality", 截图质量)
                        }
                        cdp截图参数.加入逻辑值成员 ("fromSurface", 从表面截图)
                        如果 (视窗之外)
                        {
                            cdp截图参数.加入逻辑值成员 ("captureBeyondViewport", 真)
                        }
                        cdp截图参数.加入文本成员 ("clip", cdpClip.到可读文本 (YYJSON格式化选项.压缩))
                        变量 cdp截图结果 <类型 = 文本型>
                        cdp截图结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_shot", "Page.captureScreenshot", cdp截图参数.到可读文本 (YYJSON格式化选项.压缩), 20000)
                        如果 (MCP命令服务器.CDP同步结果是否成功 (cdp截图结果))
                        {
                            变量 cdp结果文本 <类型 = 文本型>
                            cdp结果文本 = MCP命令服务器.yyjson取文本 (MCP命令服务器.取CDP结果对象 (cdp截图结果), "data")
                            如果 (cdp结果文本 != "")
                            {
                                变量 cdp截图回包 <类型 = YYJSON对象类>
                                cdp截图回包.创建自文本 ("{}")
                                cdp截图回包.加入逻辑值成员 ("success", 真)
                                cdp截图回包.加入文本成员 ("via", "cdp:Page.captureScreenshot")
                                cdp截图回包.加入文本成员 ("format", fmt)
                                cdp截图回包.加入整数成员 ("width", 截图大小.宽度)
                                cdp截图回包.加入整数成员 ("height", 截图大小.高度)
                                cdp截图回包.加入整数成员 ("image_base64_length", 取文本长度 (cdp结果文本))
                                cdp截图回包.加入文本成员 ("image", "data:image/" + fmt + ";base64," + cdp结果文本)
                                如果 (整页测量说明 != "")
                                {
                                    cdp截图回包.加入文本成员 ("full_page_note", 整页测量说明)
                                }
                                如果 (取文本长度 (cdp结果文本) > 700000)
                                {
                                    // 与项目既有实测一致: MCP 的 HTTP 通道在参数/回包约 1MB 处会被断连且无错误码
                                    cdp截图回包.加入文本成员 ("warning", "图片 base64 约 " + 到文本 (取文本长度 (cdp结果文本) / 1024) + "KB, 接近 MCP HTTP 通道约 1MB 的断连阈值; 建议 format=jpeg + quality 降一档, 或缩小 width/height/scale")
                                }
                                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, cdp截图回包.到可读文本 (YYJSON格式化选项.压缩)))
                            }
                            返回 (MCP_响应构建.命令失败 (命令ID, "CDP Page.captureScreenshot 返回成功但没有 data 字段 | 可显式改用 via:library(类库内核路线, **实测会让本会话 CDP 命令通道失效**)"))
                        }
                        返回 (MCP_响应构建.命令失败 (命令ID, "CDP 截图失败: " + MCP命令服务器.取CDP同步结果错误 (cdp截图结果) + " | 常见原因: CDP 通道不可用(可用 browser_cdp_status 看) | 替代: via:library 走类库内核路线(**实测会让本会话 CDP 命令通道失效**, 仅在确知后果时使用)"))
                    }
                    // via=library: 类库内核路线(功能等价但会打死 CDP 通道, 故只在显式选用时使用)
                    // 全部异步: 生成task_id, 回调触发时存储结果
                    变量 异步截图ID <类型 = 文本型>'''

# ── N3: 类库路线的回包加上"会打死 CDP"的如实警告 ──
LIB_RET_OLD = '''                    返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步截图ID, "截图已提交(质量=" + 到文本 (截图质量) + ", 表面=" + 选择 (从表面截图, "真", "假") + ", 视窗之外=" + 选择 (视窗之外, "真", "假") + 选择 (整页测量说明 == "", "", " | 整页: " + 整页测量说明) + "), 通过mcp_result查询", 800))'''
LIB_RET_NEW = '''                    返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步截图ID, "截图已提交(经类库内核路线; 质量=" + 到文本 (截图质量) + ", 表面=" + 选择 (从表面截图, "真", "假") + ", 视窗之外=" + 选择 (视窗之外, "真", "假") + 选择 (整页测量说明 == "", "", " | 整页: " + 整页测量说明) + "), 通过mcp_result查询 | ⚠ 实测: 该路线会让本会话的 CDP 命令通道失效(之后 CDP 类工具会退化为原生回退, 每次 10~35 秒且可能超时), 需重启进程恢复; 下次请用默认的 via:cdp)", 800))'''

# ── N4: 描述与 schema ──
DESC_ADD_OLD = '''"页面截图| 返回 base64 图片(data:image/...);'''
DESC_ADD_NEW = '''"页面截图| **默认走 CDP `Page.captureScreenshot`**(实测: 截图前后 CDP 命令通道都健康) | 备选 `via:\\"library\\"` 走类库内核路线 —— **实测会让本会话 CDP 命令通道失效**(之后 CDP 类工具退化为原生回退, 每次 10~35 秒且可能超时; 注销/重挂观察者都救不回, 需重启进程), 仅在确知后果时显式选用 | 返回 base64 图片(data:image/...);'''

VIA_PROP_ANCHOR = '''属性项JSON ("capture_beyond_viewport", "boolean", "手动开启捕获视窗之外(整页请优先用 full_page)")'''
VIA_PROP_NEW = '''属性项JSON ("capture_beyond_viewport", "boolean", "手动开启捕获视窗之外(整页请优先用 full_page)") + "," + 属性项JSON ("via", "text", "cdp(默认, 安全) / library(类库内核路线, 实测会让本会话 CDP 命令通道失效)")'''

# ── N5: 取CDP结果对象 助手(若无) ──
RESOBJ_ANCHOR = '''    # 类库 `值类型` 常量 → 可读名(browser_json 回包用; 常量定义见 FBroConst.wsv 的 值类型 类)'''
RESOBJ_NEW = '''    # 从 `执行CDP并同步等待` 的回包里取出 CDP 的 `result` 对象(CDP 原始结果在 result 字段里, 是一段 JSON 文本)
    方法 取CDP结果对象 <公开 静态 类型 = YYJSON只读对象类 @输出名 = "GetCDPResultObject" @强制输出 = 真>
    参数 同步结果JSON <类型 = 文本型 @输出名 = "SyncResultJSON">
    {
        变量 外层 <类型 = YYJSON只读对象类>
        变量 空对象 <类型 = YYJSON只读对象类>
        如果 (外层.创建自文本 (同步结果JSON) == 假)
        {
            返回 (空对象)
        }
        变量 内层文本 <类型 = 文本型>
        内层文本 = yyjson取文本 (外层, "result")
        变量 内层 <类型 = YYJSON只读对象类>
        如果 (内层文本 != "" && 内层.创建自文本 (内层文本))
        {
            返回 (内层)
        }
        返回 (空对象)
    }

''' + RESOBJ_ANCHOR

EDITS = [
    (CORE, 'N2 CDP 优先截图', CDP_INSERT_ANCHOR, CDP_INSERT_NEW),
    (CORE, 'N3 类库路线加"会打死CDP"警告', LIB_RET_OLD, LIB_RET_NEW),
    (SERVER, 'N4a 描述: CDP 默认 + library 警告', DESC_ADD_OLD, DESC_ADD_NEW),
    (SERVER, 'N4b schema: via', VIA_PROP_ANCHOR, VIA_PROP_NEW),
    (SERVER, 'N5 助手 取CDP结果对象', RESOBJ_ANCHOR, RESOBJ_NEW),
]


def main():
    print('== 第141轮补丁 N (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-40s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    for path, txt in cache.items():
        print('%s: 行数 %d' % (os.path.basename(path), len(txt.split('\n'))))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
