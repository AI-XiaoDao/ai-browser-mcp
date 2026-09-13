# -*- coding: utf-8 -*-
"""事件覆盖补齐 r115 —— 可执行补丁脚本 + 只读核对器（由主代理运行）。

用法
----
    py -3 _audit/_apply_events_patch.py --dry-run      # 只校验 + 预览，不写任何文件（**先跑这个**）
    py -3 _audit/_apply_events_patch.py --verify-only  # 只读核对当前 src/ 是否已正确落地（不改任何文件）
    py -3 _audit/_apply_events_patch.py                # 校验通过后备份 + 写入

⚠ 当前状态（2026-09-13 08:5x，脚本作者实测）
-------------------------------------------
**本补丁已被另一个并发 agent 应用过了。** 我在产出脚本过程中，用 `[0/5] 冲突守卫` 实测到
`变量 是否监控开发者窗口` / `event_devtoolspopup_enable` / `方法 下载进度 <公开` 等目标内容
**已存在于 `src/`**，于是脚本按设计**中止且未写入任何文件**。

因此现在应当：
  · **不要**再跑写入模式（会造出重复方法声明，火山里同名方法重复声明要么编译失败、要么静默覆盖）；
  · 先跑 `--verify-only` 只读核对已落地的结果（实测：**全部通过**，含 12 个事件的返回值类型断言
    与"void 方法体内无 `返回 (`"断言）。
  · 若将来需要重跑写入模式（例如回滚后重来），脚本的冲突守卫会在"目标内容已存在"时再次安全中止。

依据文档：`_audit/_events_patch_plan_r115.md`（同目录，r115 补丁计划）。

本脚本做什么
------------
1. **12 个事件覆盖方法**（类库原文签名逐字抄录，返回类型已按类库严格区分 void / 逻辑型）：
   - `src/MCP_BrowserEvents.wsv` +7：浏览器_即将打开开发者窗口 / 浏览器_即将改变媒体访问 /
     浏览器_拖拽进入 / 进程间消息_收到渲染进程消息 / 离屏渲染_获取根屏幕矩形 /
     离屏渲染_获取视图矩形 / 离屏渲染_移动调整弹窗
   - `src/MCP_Callbacks.wsv` +5：开发者消息_VIP_已附加 / 开发者消息_VIP_已分离（类_MCP_DevTools观察者）
     + 开始创建 / 下载进度 / 获得需授权证书（类_MCP_URL请求回调）
2. **新增 2 个监控开关 + 3 个节流字段声明**：
   - `是否监控开发者窗口`(IsMonitorDevToolsPopup) / `是否监控自建URL请求`(IsMonitorURLRequest) → `src/MCP_Server.wsv`
   - `上次拖拽进入毫秒` / `上次拖拽类型`（静态）→ `src/MCP_Server.wsv`；`上次进度字节`（实例，URL回调类内）→ `src/MCP_Callbacks.wsv`
3. **开关置真/置假入口同步 —— 9 处，不是计划里写的 6 处**（重要，见下"与计划的差异"）。
4. 5 处数字/注释文案 26 → 28。

⚠ 与计划的差异（必须知道）
--------------------------
计划 §3.2 写"6 处入口"，那是基于我早先读到的源码。**在我分析期间 `src/` 被并发 agent 改动过**
（实测 `MCP_Server.wsv` 11468→11482 行、`MCP_Server_Core.wsv` 7921→7949 行、`MCP_Kernel.wsv`
1800→1941 行），它新增了两个会"枚举全部开关"的地方，因此实际置真/置假入口是 **8 处 + 1 处 schema 枚举**：

  | # | 位置 | 锚点 |
  |---|---|---|
  | 1 | `MCP_Server.wsv` 声明 | `变量 是否监控离屏渲染 …` 之后 |
  | 2 | `MCP_Server.wsv` **关闭全部事件监控**(:8967) | `是否监控离屏渲染 = 假` 之后 |
  | 3 | `MCP_Server_Core.wsv` 新 action 分支 | `否则 (action == "event_title_enable")` 之前 |
  | 4 | `MCP_Server_Core.wsv` `event_all_enable` | `是否监控离屏渲染 = 真` 之后 |
  | 5 | `MCP_Server_Core.wsv` `event_all_disable` | `是否监控离屏渲染 = 假` 之后 |
  | 6 | `MCP_Kernel.wsv` `browser_kernel_events_all` enable | `是否监控离屏渲染 = 真` 之后 |
  | 7 | `MCP_Kernel.wsv` disable | `是否监控离屏渲染 = 假` 之后 |
  | 8 | `MCP_Kernel.wsv` **`action:get`**（并发 agent 新增） | 计数 `如果` 块之后 + `加入逻辑值成员` 之后 + `("total", 26)`→28 |
  | 9 | `MCP_Server.wsv` 工具 schema action 枚举 | 子串插入 2 个新 action |

**为什么必须做全 9 处而不是 6 处**：并发 agent 刚修复的缺陷注释原文是
「与 browser_kernel_events_all 的 disable 分支保持同一 26 项集合(此前只有 14 项, 少 12 项), 否则关停路径
会留下仍为真的监控开关」(MCP_Server.wsv:8969)。只做 6 处会**重新制造它刚修好的那个缺陷**；而漏掉
`action:get` 会让新开关在状态查询里不可见，漏掉 schema 枚举会让 AI 根本不知道这两个 action 存在。

断言（全部在写盘前完成；任一不满足即中止且**不写任何文件**）
----------------------------------------------------------
A. **定位一律用原文锚点文本，绝不用行号**；每个锚点在其文件内出现次数必须**恰好 1**。
B. **每文件的行尾/空行风格先实测再断言**：
   - `MCP_BrowserEvents.wsv` → 纯 LF、**双倍行距**（插入块逐行补空行）
   - `MCP_Callbacks.wsv` → CRLF、单倍行距
   - `MCP_Server/Server_Core/Kernel.wsv` → 纯 LF、单倍行距
   风格与预期不符 → 中止（不盲写）。
C. **花括号配平**：每文件写入后 `{` 增量 == `}` 增量（插入的都是完整方法块/完整分支，应配平）。
D. 写盘后自检：12 个事件名各恰好 1 次 `方法 <名> <公开` 声明；2 个新开关的
   `变量 声明`=1、`= 真`=3、`= 假`=3、`如果 (…)` 使用点=2、JSON 成员=1；2 个新 action 名各 2 次
   （分支 1 + schema 1）。

我没有验证什么（**不要把静态自检当成验证通过**）
-----------------------------------------------
- **未编译**：火山编译器是否接受这些覆盖方法、虚方法名/参数是否真正绑定到类库虚表，**全部未验证**。
- **未真机**：任何一个事件是否真的回调、`event_log` 是否真的写入、`browser_event` 是否能查到，**全部未验证**。
- **未调用 MCP、未访问 127.0.0.1:9222、未重启程序**。
- 本脚本的自检**只覆盖文本层面的插入正确性**（锚点唯一、风格一致、括号配平、出现次数），
  它**不能**替代编译与真机验证。
- 类库签名来自只读副本逐字抄录；若类库版本与项目中实际引用的版本不同，签名仍可能不匹配（未验证）。

失败时怎么办
------------
任何异常都会打印 **traceback 全文** + 出问题文件的相关片段（含行号与最接近的候选行）。
若已写入后自检失败，备份在 `备份/事件覆盖补丁r115-写入前/`，可直接覆盖回滚。
"""

import os
import shutil
import sys
import traceback

try:  # Windows 控制台默认 GBK，中文输出会炸；强制 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
BACKUP_DIR = os.path.join(ROOT, "备份", "事件覆盖补丁r115-写入前")


class ConflictError(Exception):
    """目标内容已存在（补丁已应用过 / 被别的 agent 应用）—— 不是脚本 bug，是设计上的守卫。"""


class PatchError(Exception):
    """带定位诊断的补丁错误。"""

    def __init__(self, filename, desc, needle, found, text=None):
        self.filename = filename
        self.desc = desc
        self.needle = needle
        self.found = found
        self.text = text
        super().__init__(
            "锚点未唯一: 文件=%s 用途=%s 期望=1 实际=%d 锚点首行=%r"
            % (filename, desc, found, needle.split("\n")[0])
        )


def key_token(line):
    """从一行里挑一个用于"找相似行"的关键词（取最长的连续非空白片段）。"""
    best = ""
    for tok in line.replace("\t", " ").split(" "):
        tok = tok.strip()
        if len(tok) > len(best):
            best = tok
    return best[:40] if best else line.strip()[:40]


def diagnose(text, needle):
    """锚点没命中时，打印该文件里最相似的若干行（原文），便于人工定位。"""
    out = []
    token = key_token(needle)
    lines = text.split("\n")
    if token:
        for i, l in enumerate(lines):
            if token in l:
                out.append("    L%-7d %s" % (i + 1, l.rstrip("\r")[:200]))
            if len(out) >= 8:
                break
    if not out:
        out.append("    (未找到含关键词 %r 的行；该文件共 %d 行)" % (token, len(lines)))
    return "\n".join(out)


class Patcher(object):
    """单文件补丁器：只做原文锚点定位 + 子串级插入/替换，并记录日志。"""

    def __init__(self, filename, text, eol):
        self.fn = filename
        self.text = text
        self.eol = eol
        self.log = []
        self.orig_text = text

    # --- 内部 ---
    def _require_unique(self, needle, desc):
        c = self.text.count(needle)
        if c != 1:
            raise PatchError(self.fn, desc, needle, c, self.text)

    def _new_block(self, new_lines):
        return self.eol.join(new_lines)

    # --- 公开操作 ---
    def insert_after(self, anchor_lines, new_lines, desc):
        """在锚点块之后插入。new_lines 里空字符串表示空行。"""
        block = self.eol.join(anchor_lines)
        self._require_unique(block, desc)
        i = self.text.index(block) + len(block)
        self.text = self.text[:i] + self.eol + self._new_block(new_lines) + self.text[i:]
        self.log.append(("insert_after", desc, len(new_lines), anchor_lines[0]))

    def insert_before(self, anchor_lines, new_lines, desc):
        """在锚点块之前插入。"""
        block = self.eol.join(anchor_lines)
        self._require_unique(block, desc)
        i = self.text.index(block)
        self.text = self.text[:i] + self._new_block(new_lines) + self.eol + self.text[i:]
        self.log.append(("insert_before", desc, len(new_lines), anchor_lines[0]))

    def insert_before_double_spaced(self, anchor_line, lines, desc):
        """双倍行距文件专用：把 lines 逐行补空行后插到 anchor_line 之前。"""
        if self.text.count(anchor_line) != 1:
            raise PatchError(self.fn, desc, anchor_line, self.text.count(anchor_line), self.text)
        block = "\n\n".join(lines) + "\n\n"
        i = self.text.index(anchor_line)
        self.text = self.text[:i] + block + self.text[i:]
        self.log.append(("insert_before(2x)", desc, len(lines), anchor_line))

    def replace(self, old, new, desc):
        """精确子串替换（原地替换，绝不整行重写）。"""
        self._require_unique(old, desc)
        self.text = self.text.replace(old, new, 1)
        self.log.append(("replace", desc, 0, old))


# =====================================================================
# 骨架内容（与 _events_patch_plan_r115.md §2 逐字一致；此处为单倍行距）
# =====================================================================

# ---- MCP_BrowserEvents.wsv：7 个方法（脚本会自动补空行成双倍行距）----

BE_DEVTOOLS_POPUP = [
    '    # 非用户命令打开的 DevTools(右键"检查"/内置F12) — 让 AI 能感知"DevTools 被意外打开"',
    '    # ⚠ 本事件在类库中**无返回值类型**(胶水 C++ 为 void OnBeforeDevToolsPopup)，禁止写 返回 (假)',
    '    # ⚠ 出参一律不写: 库注释把 使用默认窗口 标为"待验证", 写它可能改变 DevTools 窗口行为',
    '    方法 浏览器_即将打开开发者窗口 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 窗口信息 <类型 = FBrowser_窗口信息 @输出名 = "WindowInfo">',
    '    参数 浏览器设置 <类型 = FBrowser_浏览器配置 @输出名 = "BrowserSettings">',
    '    参数 使用默认窗口 <类型 = 逻辑型类 @输出名 = "UseDefaultWindow">',
    '    参数 用户额外配置 <类型 = 类_FBrowser_用户额外配置 @输出名 = "ExtraConfig">',
    '    {',
    '        如果 (MCP命令服务器.是否监控开发者窗口)',
    '        {',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入整数成员 ("devtools_win_width", 窗口信息.宽度)',
    '            事件数据.加入整数成员 ("devtools_win_height", 窗口信息.高度)',
    '            记录监控事件 (真, "devtools_popup", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '    }',
]

BE_MEDIA_ACCESS = [
    '    # 页面实际拿到/失去 摄像头/麦克风 访问权 (与 即将请求媒体访问许可 互补: 一个报请求, 一个报结果)',
    '    方法 浏览器_即将改变媒体访问 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 包含视频访问 <类型 = 逻辑型 @输出名 = "HasVideoAccess">',
    '    参数 包含音频访问 <类型 = 逻辑型 @输出名 = "HasAudioAccess">',
    '    {',
    '        如果 (MCP命令服务器.是否监控许可提示)',
    '        {',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入逻辑值成员 ("has_video_access", 包含视频访问)',
    '            事件数据.加入逻辑值成员 ("has_audio_access", 包含音频访问)',
    '            记录监控事件 (真, "media_access_change", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '    }',
]

BE_DRAG_ENTER = [
    '    # ⚠ 高频: 类库注释原文「连续拖动文件或链接后调用此事件…如果鼠标拖动动作未结束，返回真也还是会继续调用该事件」',
    '    #   → 500ms 节流 + 拖动类型变化时必记 (沿用 重定向链 的 取启动时间 节流写法)',
    '    方法 浏览器_拖拽进入 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 拖拽数据 <类型 = 类_FBrowser_拖拽数据 @输出名 = "DragData">',
    '    参数 拖动类型 <类型 = 整数 @输出名 = "DragOperationsMask">',
    '    {',
    '        变量 现在毫秒 <类型 = 长整数>',
    '        现在毫秒 = 取启动时间 ()',
    '        如果 (MCP命令服务器.是否监控界面细节 && (拖动类型 != MCP命令服务器.上次拖拽类型 || 现在毫秒 - MCP命令服务器.上次拖拽进入毫秒 > 500))',
    '        {',
    '            MCP命令服务器.上次拖拽类型 = 拖动类型',
    '            MCP命令服务器.上次拖拽进入毫秒 = 现在毫秒',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入整数成员 ("drag_ops", 拖动类型)',
    '            如果 (拖拽数据.是否为空 () == 假)',
    '            {',
    '                事件数据.加入逻辑值成员 ("is_file", 拖拽数据.是否为文件 ())',
    '                事件数据.加入逻辑值成员 ("is_link", 拖拽数据.是否为链接 ())',
    '                事件数据.加入文本成员 ("file_name", 拖拽数据.取文件名 ())',
    '                事件数据.加入文本成员 ("link_url", 拖拽数据.取链接地址 ())',
    '            }',
    '            记录监控事件 (真, "drag_enter", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '        // 逻辑型事件: 返回假 = 不取消 CEF 默认拖拽 (返回真会取消; 拖动未结束时仍会继续回调)',
    '        返回 (假)',
    '    }',
]

BE_IPC_FROM_RENDER_PROCESS = [
    '    # 类库扩展 IPC 通道 (非 CEF 原生): 页面/注入脚本调 进程间消息_发送数据_到主进程 后, 在此收到',
    '    方法 进程间消息_收到渲染进程消息 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 渲染进程ID <类型 = 变整数 @输出名 = "RenderProcessID">',
    '    参数 消息名 <类型 = 文本型 @输出名 = "MessageName">',
    '    参数 消息内容 <类型 = 字节集类 @输出名 = "MessageData">',
    '    {',
    '        变量 载荷长度 <类型 = 整数>',
    '        载荷长度 = 取字节集长度 (消息内容)',
    '        变量 事件数据 <类型 = YYJSON对象类>',
    '        事件数据.创建自文本 ("{}")',
    '        事件数据.加入文本成员 ("name", 消息名)',
    '        事件数据.加入文本成员 ("process_id", 到文本 (渲染进程ID))',
    '        事件数据.加入整数成员 ("size", 载荷长度)',
    '        如果 (载荷长度 > 0)',
    '        {',
    '            变量 载荷文本 <类型 = 文本型>',
    '            载荷文本 = UTF8到文本 (消息内容)',
    '            如果 (取文本长度 (载荷文本) > 4096)',
    '            {',
    '                载荷文本 = 取文本左边 (载荷文本, 4096) + "...[MCP截断]"',
    '            }',
    '            事件数据.加入文本成员 ("text", 载荷文本)',
    '        }',
    '        记录监控事件 (真, "ipc_from_renderer_ext", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '    }',
]

BE_OSR_ROOT_RECT = [
    '    # OSR 族补齐(第 12 项): 仅离屏渲染模式回调, 本项目窗口内嵌渲染下不会触发',
    '    方法 离屏渲染_获取根屏幕矩形 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 矩形 <类型 = FBrowser_矩形位置 @输出名 = "Rect">',
    '    {',
    '        如果 (MCP命令服务器.是否监控离屏渲染)',
    '        {',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入整数成员 ("x", 矩形.横坐标)',
    '            事件数据.加入整数成员 ("y", 矩形.纵坐标)',
    '            事件数据.加入整数成员 ("width", 矩形.宽度)',
    '            事件数据.加入整数成员 ("height", 矩形.高度)',
    '            记录监控事件 (真, "offscreen_get_root_rect", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '        // 逻辑型事件: 返回假 = 让 CEF 改用 离屏渲染_获取视图矩形 的矩形 (出参一律不写)',
    '        返回 (假)',
    '    }',
]

BE_OSR_VIEW_RECT = [
    '    方法 离屏渲染_获取视图矩形 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 矩形 <类型 = FBrowser_矩形位置 @输出名 = "Rect">',
    '    {',
    '        如果 (MCP命令服务器.是否监控离屏渲染)',
    '        {',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入整数成员 ("x", 矩形.横坐标)',
    '            事件数据.加入整数成员 ("y", 矩形.纵坐标)',
    '            事件数据.加入整数成员 ("width", 矩形.宽度)',
    '            事件数据.加入整数成员 ("height", 矩形.高度)',
    '            记录监控事件 (真, "offscreen_get_view_rect", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '    }',
]

BE_OSR_POPUP_SIZE = [
    '    方法 离屏渲染_移动调整弹窗 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    参数 矩形 <类型 = FBrowser_矩形位置 @输出名 = "Rect">',
    '    {',
    '        如果 (MCP命令服务器.是否监控离屏渲染)',
    '        {',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入整数成员 ("x", 矩形.横坐标)',
    '            事件数据.加入整数成员 ("y", 矩形.纵坐标)',
    '            事件数据.加入整数成员 ("width", 矩形.宽度)',
    '            事件数据.加入整数成员 ("height", 矩形.高度)',
    '            记录监控事件 (真, "offscreen_popup_size", 浏览器.取ID (), 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '    }',
]

# ---- MCP_Callbacks.wsv：1 个实例变量 + 5 个方法（CRLF / 单倍行距）----

CB_PROGRESS_VAR = [
    '    变量 上次进度字节 <类型 = 长整数 值 = -1 注释 = "OnDownloadProgress 节流游标(每数据块回调一次); -1=尚未记录" @输出名 = "LastProgressBytes">',
]

CB_DEVTOOLS_ATTACH = [
    '    方法 开发者消息_VIP_已附加 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    {',
    '        // CDP 会话建立 —— browser_cdp_* / browser_cdp_status 的权威"连上了"时刻',
    '        MCP命令服务器.记录浏览器事件 ("devtools_attached", 浏览器.取ID (), "")',
    '        MCP命令服务器.存储CDPDevTools事件 ("DevTools.agentAttached", "{}")',
    '    }',
    '',
    '    方法 开发者消息_VIP_已分离 <公开 @虚拟方法 = 可覆盖>',
    '    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">',
    '    {',
    '        // CDP 会话断开 —— "30s 黑洞/会话挂起"类缺陷的根因信号',
    '        MCP命令服务器.记录浏览器事件 ("devtools_detached", 浏览器.取ID (), "")',
    '        MCP命令服务器.存储CDPDevTools事件 ("DevTools.agentDetached", "{}")',
    '    }',
]

CB_URLREQ_START = [
    '    方法 开始创建 <公开 @虚拟方法 = 可覆盖>',
    '    参数 标识 <类型 = 长整数 @输出名 = "Key">',
    '    参数 URL请求 <类型 = 类_FBrowser_URL请求 @输出名 = "URLRequest">',
    '    {',
    '        // ⚠ 标识不可用于区分请求: 本项目 FBrowser_创建URL请求 的第 4 实参传的是',
    '        //   MCP_常量.URL请求默认超时(=60000), 而类库该形参语义是"传递给事件的标识"(FBroLib.wsv:234) —— 所有请求同值。',
    '        //   → 关联一律走本类自己的 任务ID(见 MCP_Server_Core.wsv)。',
    '        如果 (MCP命令服务器.是否监控自建URL请求)',
    '        {',
    '            变量 请求对象 <类型 = 类_FBrowser_请求>',
    '            请求对象 = URL请求.取请求 ()',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入文本成员 ("task_id", 任务ID)',
    '            事件数据.加入文本成员 ("url", 请求对象.取地址 ())',
    '            事件数据.加入文本成员 ("flag", 到文本 (标识))',
    '            MCP命令服务器.记录浏览器事件 ("urlreq_start", 0, 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '    }',
    '',
]

CB_URLREQ_DOWNLOAD = [
    '    方法 下载进度 <公开 @虚拟方法 = 可覆盖>',
    '    参数 标识 <类型 = 长整数 @输出名 = "Key">',
    '    参数 URL请求 <类型 = 类_FBrowser_URL请求 @输出名 = "URLRequest">',
    '    参数 当前大小 <类型 = 长整数 @输出名 = "Current">',
    '    参数 合计大小 <类型 = 长整数 @输出名 = "Total">',
    '    {',
    '        // ⚠ 高频: 类库注释「通知客户端下载进度|当前|表示呼叫前接收到的字节数, |total|是预期总大小(不确定为-1)」',
    '        //   → 每收一块就回调一次。用"绝对字节"节流(≥1MB 或 已收满), 刻意不做除法(规避整除/取整歧义)。',
    '        如果 (MCP命令服务器.是否监控自建URL请求 && (上次进度字节 < 0 || 当前大小 == 合计大小 || 当前大小 - 上次进度字节 >= 1048576))',
    '        {',
    '            上次进度字节 = 当前大小',
    '            变量 事件数据 <类型 = YYJSON对象类>',
    '            事件数据.创建自文本 ("{}")',
    '            事件数据.加入文本成员 ("task_id", 任务ID)',
    '            事件数据.加入长整数成员 ("current", 当前大小)',
    '            事件数据.加入长整数成员 ("total", 合计大小)',
    '            MCP命令服务器.记录浏览器事件 ("urlreq_download", 0, 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '        }',
    '    }',
    '',
]

CB_URLREQ_AUTH = [
    '    方法 获得需授权证书 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
    '    参数 标识 <类型 = 长整数 @输出名 = "Key">',
    '    参数 是否为代理 <类型 = 逻辑型 @输出名 = "IsProxy">',
    '    参数 主机 <类型 = 文本型 @输出名 = "Host">',
    '    参数 端口 <类型 = 整数 @输出名 = "Port">',
    '    参数 域名 <类型 = 文本型 @输出名 = "Domain">',
    '    参数 认证方案 <类型 = 文本型 @输出名 = "AuthScheme">',
    '    参数 授权回调 <类型 = 类_FBrowser_授权回调 @输出名 = "LicenseCallback">',
    '    {',
    '        // 与 浏览器_获得需授权证书(MCP_BrowserEvents.wsv) 共用同一凭据库,',
    '        // 返回格式 "user|pass"(见 MCP_Kernel.wsv 查询认证凭据 的注释与方法)',
    '        变量 凭据 <类型 = 文本型>',
    '        凭据 = MCP_内核分派.查询认证凭据 (主机, 端口, 域名)',
    '        如果 (凭据 != "")',
    '        {',
    '            变量 分隔位置 <类型 = 整数>',
    '            分隔位置 = 寻找文本 (凭据, "|", 0, 假)',
    '            如果 (分隔位置 > 0 && 授权回调.是否为空 () == 假)',
    '            {',
    '                授权回调.继续 (取文本左边 (凭据, 分隔位置), 取文本右边 (凭据, 取文本长度 (凭据) - 分隔位置 - 1))',
    '                如果 (MCP命令服务器.是否监控自建URL请求)',
    '                {',
    '                    变量 事件数据 <类型 = YYJSON对象类>',
    '                    事件数据.创建自文本 ("{}")',
    '                    事件数据.加入文本成员 ("task_id", 任务ID)',
    '                    事件数据.加入文本成员 ("host", 主机)',
    '                    事件数据.加入整数成员 ("port", 端口)',
    '                    事件数据.加入逻辑值成员 ("is_proxy", 是否为代理)',
    '                    事件数据.加入文本成员 ("auth_scheme", 认证方案)',
    '                    MCP命令服务器.记录浏览器事件 ("urlreq_auth", 0, 事件数据.到可读文本 (YYJSON格式化选项.压缩))',
    '                }',
    '            }',
    '            返回 (真)',
    '        }',
    '        返回 (假)',
    '    }',
]

# ---- MCP_Server.wsv 声明 ----

SERVER_THROTTLE_FIELDS = [
    '    变量 上次拖拽进入毫秒 <公开 静态 类型 = 长整数 值 = 0 注释 = "拖拽节流窗口起点(取启动时间毫秒): 浏览器_拖拽进入 在拖动未结束时会被反复回调" @输出名 = "LastDragEnterMs">',
    '    变量 上次拖拽类型 <公开 静态 类型 = 整数 值 = -1 注释 = "上一次记录的拖动操作掩码, 变化时必记一条" @输出名 = "LastDragEnterMask">',
]

SERVER_NEW_SWITCHES = [
    '    变量 是否监控开发者窗口 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "浏览器_即将打开开发者窗口 → browser_event:devtools_popup (非用户命令打开的 DevTools: 右键检查/内置F12)" @输出名 = "IsMonitorDevToolsPopup">',
    '    变量 是否监控自建URL请求 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "开始创建/下载进度/获得需授权证书 → browser_event:urlreq_start|urlreq_download|urlreq_auth (仅自建 FBrowser_创建URL请求)" @输出名 = "IsMonitorURLRequest">',
]

# 各入口的开关赋值行（缩进按各文件实测：Server 方法体 8 空格；Core 分支 16 空格；Kernel 分支 12 空格）
def sw_true(indent):
    return [
        indent + 'MCP命令服务器.是否监控开发者窗口 = 真',
        indent + 'MCP命令服务器.是否监控自建URL请求 = 真',
    ]


def sw_false(indent):
    return [
        indent + 'MCP命令服务器.是否监控开发者窗口 = 假',
        indent + 'MCP命令服务器.是否监控自建URL请求 = 假',
    ]


def sw_close_all(indent):
    """关闭全部事件监控（MCP_Server.wsv 内直接用类内字段名，无 MCP命令服务器. 前缀）。"""
    return [
        indent + '是否监控开发者窗口 = 假',
        indent + '是否监控自建URL请求 = 假',
    ]


CORE_NEW_ACTIONS = [
    '            否则 (action == "event_devtoolspopup_enable")',
    '            {',
    '                MCP命令服务器.是否监控开发者窗口 = 真',
    '                返回 (MCP_响应构建.命令成功 (命令ID, "开发者窗口(DevTools 弹窗)监控已启用 (devtools_popup) | 非用户命令打开 DevTools 时会记录; 该事件在类库中无返回值类型, 本覆盖不改变 CEF 行为"))',
    '            }',
    '            否则 (action == "event_urlreq_enable")',
    '            {',
    '                MCP命令服务器.是否监控自建URL请求 = 真',
    '                返回 (MCP_响应构建.命令成功 (命令ID, "自建URL请求监控已启用 (urlreq_start / urlreq_download / urlreq_auth) | 仅记录 browser_network_body 一类自建请求; 进度只写 event_log, 不写异步结果槽"))',
    '            }',
]

KERNEL_GET_COUNTERS = [
    '            如果 (MCP命令服务器.是否监控开发者窗口)',
    '            {',
    '                evt已开 = evt已开 + 1',
    '            }',
    '            如果 (MCP命令服务器.是否监控自建URL请求)',
    '            {',
    '                evt已开 = evt已开 + 1',
    '            }',
]

KERNEL_GET_MEMBERS = [
    '            evt状态.加入逻辑值成员 ("是否监控开发者窗口", MCP命令服务器.是否监控开发者窗口)',
    '            evt状态.加入逻辑值成员 ("是否监控自建URL请求", MCP命令服务器.是否监控自建URL请求)',
]

# 期望风格：(eol, 是否双倍行距)
EXPECTED_STYLE = {
    "MCP_BrowserEvents.wsv": ("\n", True),
    "MCP_Callbacks.wsv": ("\r\n", False),
    "MCP_Server.wsv": ("\n", False),
    "MCP_Server_Core.wsv": ("\n", False),
    "MCP_Kernel.wsv": ("\n", False),
}

TARGET_FILES = list(EXPECTED_STYLE.keys())


def read_file(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("文件带 UTF-8 BOM（预期无 BOM）: %s" % path)
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        raise RuntimeError("文件是 UTF-16LE/BE（预期 UTF-8）: %s" % path)
    return raw.decode("utf-8")


def detect_style(filename, text):
    lf = text.count("\n")
    crlf = text.count("\r\n")
    lone_lf = lf - crlf
    lines = text.split("\n")
    blank = sum(1 for l in lines if l.strip("\r") == "")
    ratio = float(blank) / max(1, len(lines))
    if crlf > 0 and lone_lf > 0:
        eol = "mixed"
    elif crlf > 0:
        eol = "\r\n"
    else:
        eol = "\n"
    double_spaced = ratio > 0.35
    return eol, double_spaced, ratio, len(lines)


def check_style(filename, text):
    exp_eol, exp_double = EXPECTED_STYLE[filename]
    eol, double_spaced, ratio, nlines = detect_style(filename, text)
    problems = []
    if eol != exp_eol:
        problems.append(
            "行尾不符: 实测=%r 预期=%r (CRLF=%d, LF总数=%d)"
            % (eol, exp_eol, text.count("\r\n"), text.count("\n"))
        )
    if double_spaced != exp_double:
        problems.append(
            "空行风格不符: 实测双倍行距=%s(空行占比%.3f) 预期=%s"
            % (double_spaced, ratio, exp_double)
        )
    return problems, eol, ratio, nlines


def build_patches(files):
    """在内存中构建全部改动。返回 {filename: Patcher}。"""
    P = {}

    # ---------------- src/MCP_BrowserEvents.wsv ----------------
    fn = "MCP_BrowserEvents.wsv"
    p = Patcher(fn, files[fn], "\n")
    p.insert_before_double_spaced(
        '    方法 浏览器_打开新窗口失败 <公开 @虚拟方法 = 可覆盖>',
        BE_DEVTOOLS_POPUP, "浏览器_即将打开开发者窗口 (插在 浏览器_打开新窗口失败 之前)")
    p.insert_before_double_spaced(
        '    方法 浏览器_收到消息 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
        BE_IPC_FROM_RENDER_PROCESS, "进程间消息_收到渲染进程消息 (插在 浏览器_收到消息 之前)")
    p.insert_before_double_spaced(
        '    方法 浏览器_拖拽区域改变 <公开 @虚拟方法 = 可覆盖>',
        BE_DRAG_ENTER, "浏览器_拖拽进入 (插在 浏览器_拖拽区域改变 之前)")
    p.insert_before_double_spaced(
        '    方法 浏览器_即将请求媒体访问许可 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
        BE_MEDIA_ACCESS, "浏览器_即将改变媒体访问 (插在 浏览器_即将请求媒体访问许可 之前)")
    p.insert_before_double_spaced(
        '    方法 离屏渲染_获取屏幕点 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
        BE_OSR_ROOT_RECT, "离屏渲染_获取根屏幕矩形 (插在 离屏渲染_获取屏幕点 之前)")
    p.insert_before_double_spaced(
        '    方法 离屏渲染_获取窗口信息 <公开 类型 = 逻辑型 @虚拟方法 = 可覆盖>',
        BE_OSR_VIEW_RECT, "离屏渲染_获取视图矩形 (插在 离屏渲染_获取窗口信息 之前)")
    p.insert_before_double_spaced(
        '    方法 离屏渲染_将被绘制 <公开 @虚拟方法 = 可覆盖>',
        BE_OSR_POPUP_SIZE, "离屏渲染_移动调整弹窗 (插在 离屏渲染_将被绘制 之前)")
    P[fn] = p

    # ---------------- src/MCP_Callbacks.wsv ----------------
    fn = "MCP_Callbacks.wsv"
    p = Patcher(fn, files[fn], "\r\n")
    p.insert_after(
        ['    变量 已释放槽 <类型 = 整数 值 = 0 注释 = "原子标志: 0=未释放, 1=已释放。使用InterlockedExchange确保多核安全" @输出名 = "ReleasedSlot">'],
        CB_PROGRESS_VAR, "上次进度字节 (插在 已释放槽 之后)")
    p.insert_after(
        ['        MCP命令服务器.存储CDPDevTools事件 (方法名, 事件文本)',
         '    }'],
        [""] + CB_DEVTOOLS_ATTACH + [""],
        "开发者消息_VIP_已附加/已分离 (插在 开发者消息_VIP_收到事件 方法体之后)")
    p.insert_after(
        ['                包装对象.加入文本成员 ("message", "请求完成(无响应体)")',
         '            }',
         '        }',
         '        MCP命令服务器.存储异步结果 (任务ID, 包装对象.到可读文本 (YYJSON格式化选项.压缩))',
         '    }'],
        [""] + CB_URLREQ_START + CB_URLREQ_DOWNLOAD + CB_URLREQ_AUTH + [""],
        "开始创建/下载进度/获得需授权证书 (插在 即将完成 方法体之后)")
    P[fn] = p

    # ---------------- src/MCP_Server.wsv ----------------
    fn = "MCP_Server.wsv"
    p = Patcher(fn, files[fn], "\n")
    p.insert_after(
        ['    变量 重定向链起始毫秒 <公开 静态 类型 = 长整数 值 = 0 注释 = "重定向链保护窗口起点(GetTickCount64毫秒)" @输出名 = "RedirectChainStartMs">'],
        SERVER_THROTTLE_FIELDS, "2 个拖拽节流字段 (插在 重定向链起始毫秒 之后)")
    p.insert_after(
        ['    变量 是否监控离屏渲染 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "离屏渲染(OSR)事件族 → browser_event:offscreen_* (注: 窗口内嵌渲染模式下不触发, 仅切换到离屏渲染模式才有意义)" @输出名 = "IsMonitorOffscreen">'],
        SERVER_NEW_SWITCHES, "2 个新监控开关声明 (插在 是否监控离屏渲染 之后)")
    p.insert_after(
        ['        MCP命令服务器.是否监控许可提示 = 假',
         '        MCP命令服务器.是否监控离屏渲染 = 假'],
        sw_close_all('        '), "关闭全部事件监控 补 2 项 (入口#2)")
    p.replace(
        'event_offscreen_enable/event_all_enable/event_all_disable',
        'event_offscreen_enable/event_devtoolspopup_enable/event_urlreq_enable/event_all_enable/event_all_disable',
        "工具 schema action 枚举加 2 个新 action (入口#9)")
    p.replace('**26** 个开关(13 事件族 + 3 日志 + 10 扩展族',
              '**28** 个开关(13 事件族 + 3 日志 + 12 扩展族',
              "browser_kernel_events_all 工具描述 26→28 / 10→12")
    p.replace('同一 26 项集合', '同一 28 项集合', "关闭全部事件监控 注释 26→28")
    P[fn] = p

    # ---------------- src/MCP_Server_Core.wsv ----------------
    fn = "MCP_Server_Core.wsv"
    p = Patcher(fn, files[fn], "\n")
    p.insert_before(
        ['            否则 (action == "event_title_enable")'],
        CORE_NEW_ACTIONS, "2 个新 action 分支 (入口#3)")
    p.insert_after(
        ['                MCP命令服务器.是否监控许可提示 = 真',
         '                MCP命令服务器.是否监控离屏渲染 = 真'],
        sw_true('                '), "event_all_enable 补 2 项 (入口#4)")
    p.insert_after(
        ['                MCP命令服务器.是否监控许可提示 = 假',
         '                MCP命令服务器.是否监控离屏渲染 = 假'],
        sw_false('                '), "event_all_disable 补 2 项 (入口#5)")
    p.replace('全部事件监控已启用(26 项: 13 事件族 + 3 日志 + 10 扩展族',
              '全部事件监控已启用(28 项: 13 事件族 + 3 日志 + 12 扩展族',
              "event_all_enable 文案 26→28 / 10→12")
    p.replace('全部事件监控已禁用(26 项, 与 event_all_enable 逐项对称)',
              '全部事件监控已禁用(28 项, 与 event_all_enable 逐项对称)',
              "event_all_disable 文案 26→28")
    P[fn] = p

    # ---------------- src/MCP_Kernel.wsv ----------------
    fn = "MCP_Kernel.wsv"
    p = Patcher(fn, files[fn], "\n")
    p.insert_after(
        ['            MCP命令服务器.是否监控许可提示 = 真',
         '            MCP命令服务器.是否监控离屏渲染 = 真'],
        sw_true('            '), "browser_kernel_events_all enable 补 2 项 (入口#6)")
    p.insert_after(
        ['            MCP命令服务器.是否监控许可提示 = 假',
         '            MCP命令服务器.是否监控离屏渲染 = 假'],
        sw_false('            '), "browser_kernel_events_all disable 补 2 项 (入口#7)")
    p.insert_after(
        ['            如果 (MCP命令服务器.是否监控离屏渲染)',
         '            {',
         '                evt已开 = evt已开 + 1',
         '            }'],
        KERNEL_GET_COUNTERS, "action:get 计数块补 2 项 (入口#8a)")
    p.insert_after(
        ['            evt状态.加入逻辑值成员 ("是否监控离屏渲染", MCP命令服务器.是否监控离屏渲染)'],
        KERNEL_GET_MEMBERS, "action:get 状态成员补 2 项 (入口#8b)")
    p.replace('evt状态.加入整数成员 ("total", 26)',
              'evt状态.加入整数成员 ("total", 28)',
              "action:get 的 total 26→28")
    p.replace('并使 26 个监控/记录开关立即生效',
              '并使 28 个监控/记录开关立即生效',
              "缺参拒绝文案 26→28")
    p.replace('// 浏览器/应用事件族 + 日志 全开(26 个开关, 与 disable 分支逐项对称)',
              '// 浏览器/应用事件族 + 日志 全开(28 个开关, 与 disable 分支逐项对称)',
              "enable 分支注释 26→28")
    p.replace('全事件流已开启: 26 个开关(13 核心事件族 + 3 日志 + 10 扩展事件族)',
              '全事件流已开启: 28 个开关(13 核心事件族 + 3 日志 + 12 扩展事件族)',
              "enable 成功文案 26→28 / 10→12")
    p.replace('// 只读: 回报 26 个开关的真值',
              '// 只读: 回报 28 个开关的真值',
              "action:get 注释 26→28")
    P[fn] = p

    return P


def preflight_conflict_check():
    """写盘前的**冲突/重复应用**守卫。

    本仓库同时有多个 agent 在改 `src/`（本会话已实测到多次并发写入），其中可能有 agent 正在做
    同样的事件补齐。若目标内容已存在，说明"已被应用过"或"与别人的改动冲突"——此时**必须中止**，
    否则会产生重复方法声明（火山里同名方法重复声明会编译失败，或静默覆盖，两种都难查）。

    检查范围：`src/` 下**全部** `*.wsv`（排除 `*.~vbak.wsv`），不只是 5 个目标文件。
    返回 (ok, 报告行列表)。
    """
    needles = [
        "变量 是否监控开发者窗口",
        "变量 是否监控自建URL请求",
        "event_devtoolspopup_enable",
        "event_urlreq_enable",
        "上次拖拽进入毫秒",
        "上次拖拽类型",
        "上次进度字节",
    ]
    for names in EVENT_DECL.values():
        for nm in names:
            needles.append("方法 " + nm + " <公开")

    report = []
    ok = True
    files = sorted(f for f in os.listdir(SRC)
                   if f.endswith(".wsv") and ".~vbak" not in f)
    for needle in needles:
        hits = []
        for fn in files:
            try:
                t = read_file(os.path.join(SRC, fn))
            except Exception as e:
                hits.append("%s(读取失败:%s)" % (fn, e))
                continue
            c = t.count(needle)
            if c:
                hits.append("%s x%d" % (fn, c))
        if hits:
            ok = False
            report.append("  [冲突] %-34s 已存在: %s" % (needle, ", ".join(hits)))
    if ok:
        report.append("  [OK ] 全部 %d 个冲突探针在 src/ 下均 0 命中（补丁尚未被应用过）" % len(needles))
    else:
        report.append("  → 中止：目标内容已存在，可能是别的 agent 已应用，或本脚本已跑过。")
        report.append("     请人工确认后再决定是否需要继续（本脚本不做增量/幂等补丁）。")
    return ok, report


def brace_counts(text):
    return text.count("{"), text.count("}")


def adjacent_nonblank_pairs(text):
    """相邻两条非空行的对数 —— 用于验证"双倍行距"没被插入块破坏。"""
    lines = text.replace("\r\n", "\n").split("\n")
    n = 0
    for a, b in zip(lines, lines[1:]):
        if a.strip() and b.strip():
            n += 1
    return n


def eol_purity(text):
    """返回 (lf总数, crlf数, 孤立LF数)。孤立LF>0 说明往 CRLF 文件里插了 LF。"""
    lf = text.count("\n")
    crlf = text.count("\r\n")
    return lf, crlf, lf - crlf


def preview_block(lines, limit=6):
    shown = lines[:limit]
    head = "\n".join("      | " + l for l in shown)
    if len(lines) > limit:
        head += "\n      | ... (共 %d 行)" % len(lines)
    return head


# ---- 写盘后的静态自检 ----

EVENT_DECL = {
    "MCP_BrowserEvents.wsv": [
        "浏览器_即将打开开发者窗口", "浏览器_即将改变媒体访问", "浏览器_拖拽进入",
        "进程间消息_收到渲染进程消息", "离屏渲染_获取根屏幕矩形",
        "离屏渲染_获取视图矩形", "离屏渲染_移动调整弹窗",
    ],
    "MCP_Callbacks.wsv": [
        "开发者消息_VIP_已附加", "开发者消息_VIP_已分离",
        "开始创建", "下载进度", "获得需授权证书",
    ],
}

# 每个事件的**返回值类型**期望（来自类库原文逐字抄录；True = 有 `类型 = 逻辑型`）
# 这是 r115 计划里两处"抄错就编译不过"的陷阱，故在自检里单独断言。
EXPECTED_RETURN_TYPE = {
    # 类库 FBroEventControl.wsv:763 —— 胶水 C++ 是 void OnBeforeDevToolsPopup，**无返回类型**
    "浏览器_即将打开开发者窗口": False,
    # :915 —— void
    "浏览器_即将改变媒体访问": False,
    # :1376 —— 类型 = 逻辑型
    "浏览器_拖拽进入": True,
    # :1401 —— void
    "进程间消息_收到渲染进程消息": False,
    # :1420 —— 类型 = 逻辑型
    "离屏渲染_获取根屏幕矩形": True,
    # :1437 —— void（类库此处确实无返回，注释在讲 return true/false 是残留）
    "离屏渲染_获取视图矩形": False,
    # :1501 —— void
    "离屏渲染_移动调整弹窗": False,
    # :2237 / :2243 —— void 且类库连 {} 都没写
    "开发者消息_VIP_已附加": False,
    "开发者消息_VIP_已分离": False,
    # :2282 / :2329 —— void
    "开始创建": False,
    "下载进度": False,
    # :2357 —— 类型 = 逻辑型
    "获得需授权证书": True,
}


def verify_only_main():
    """只读核对：不修改任何文件，核对当前 src/ 是否已正确落地 r115 计划。

    多做的两项检查（针对 r115 的两个"抄错就编译不过"陷阱）：
      · 每个事件的声明是否带 `类型 = 逻辑型`，与类库原文一致；
      · **void 方法体内不得出现 `返回 (`**（在无返回值的方法里写 `返回 (假)` 会编译失败）。
    """
    print("=" * 78)
    print("事件覆盖补齐 r115 —— 只读核对模式 [VERIFY-ONLY，不写任何文件]")
    print("项目根: %s" % ROOT)
    print("=" * 78)

    texts = {}
    for fn in TARGET_FILES:
        path = os.path.join(SRC, fn)
        if not os.path.isfile(path):
            print("  [FAIL] 目标文件不存在: %s" % path)
            return 2
        texts[fn] = read_file(path)

    ok, report = selfcheck_texts(texts, None)
    print("\n[1/3] 通用自检（声明计数 / 开关落点 / 行尾纯净度；花括号与双倍行距无基线时仅 info）")
    for line in report:
        print(line)

    print("\n[2/3] 返回值类型断言（r115 两个编译陷阱）")
    type_ok = True
    for fn, names in EVENT_DECL.items():
        t = texts[fn]
        eol = EXPECTED_STYLE[fn][0]
        for nm in names:
            prefix = "方法 " + nm + " <公开"
            idx = t.find(prefix)
            if idx < 0:
                type_ok = False
                ok = False
                print("     [FAIL] %-28s 未找到声明" % nm)
                continue
            line_end = t.find("\n", idx)
            decl_line = t[idx:line_end].rstrip("\r")
            has_ret = "类型 = 逻辑型" in decl_line
            exp_ret = EXPECTED_RETURN_TYPE[nm]
            good = (has_ret == exp_ret)
            if not good:
                type_ok = False
                ok = False
            print("     [%s] %-28s 声明含逻辑型=%s (期望 %s)"
                  % ("OK " if good else "FAIL", nm, has_ret, exp_ret))

            # void 方法体内不得有 返回 (
            if not exp_ret:
                nxt = t.find(eol + "    方法 ", idx)
                body = t[idx:nxt] if nxt > 0 else t[idx:]
                if "返回 (" in body:
                    ok = False
                    bad = [l.strip() for l in body.replace("\r\n", "\n").split("\n") if "返回 (" in l][:3]
                    print("     [FAIL] %-28s void 方法体内出现 `返回 (` —— 会编译失败: %s" % (nm, bad))
                else:
                    print("            └ void 方法体内无 `返回 (` ✓")

    print("\n[3/3] 风格复核")
    style_ok = True
    for fn in TARGET_FILES:
        problems, eol, ratio, nlines = check_style(fn, texts[fn])
        eolname = {"\n": "LF", "\r\n": "CRLF", "mixed": "MIXED"}[eol]
        if problems:
            style_ok = False
            ok = False
        print("     [%s] %-26s 行数=%-6d 行尾=%-5s 空行占比=%.3f %s"
              % ("OK " if not problems else "FAIL", fn, nlines, eolname, ratio,
                 "(双倍行距)" if ratio > 0.35 else "(单倍行距)"))
        for pr in problems:
            print("          !! %s" % pr)

    print("\n核对结论: %s" % ("全部通过" if ok else "存在 FAIL 项（见上方 [FAIL]）"))
    print("注意：这是**纯文本静态核对**，不等于编译通过，也不等于真机验证通过。")
    print("=" * 78)
    return 0 if ok else 2


# 期望出现次数（跨全项目 src）
EXPECTED_COUNTS = [
    # (字符串, {文件: 次数} 或 None 表示全项目合计, 期望总数, 说明)
    ("变量 是否监控开发者窗口", {"MCP_Server.wsv": 1}, 1, "开关声明恰好 1 处"),
    ("变量 是否监控自建URL请求", {"MCP_Server.wsv": 1}, 1, "开关声明恰好 1 处"),
    ("MCP命令服务器.是否监控开发者窗口 = 真", {"MCP_Server_Core.wsv": 2, "MCP_Kernel.wsv": 1}, 3,
     "置真入口 3 处 (Core: 分支+all_enable, Kernel: enable)"),
    ("MCP命令服务器.是否监控自建URL请求 = 真", {"MCP_Server_Core.wsv": 2, "MCP_Kernel.wsv": 1}, 3,
     "置真入口 3 处 (Core: 分支+all_enable, Kernel: enable)"),
    ("MCP命令服务器.是否监控开发者窗口 = 假", {"MCP_Server_Core.wsv": 1, "MCP_Kernel.wsv": 1}, 2,
     "置假入口 2 处 (Core: all_disable, Kernel: disable)"),
    ("MCP命令服务器.是否监控自建URL请求 = 假", {"MCP_Server_Core.wsv": 1, "MCP_Kernel.wsv": 1}, 2,
     "置假入口 2 处 (Core: all_disable, Kernel: disable)"),
    ("        是否监控开发者窗口 = 假", {"MCP_Server.wsv": 1}, 1,
     "关闭全部事件监控 补项(类内无前缀, 8空格缩进)"),
    ("        是否监控自建URL请求 = 假", {"MCP_Server.wsv": 1}, 1,
     "关闭全部事件监控 补项(类内无前缀, 8空格缩进)"),
    ("如果 (MCP命令服务器.是否监控开发者窗口)", {"MCP_BrowserEvents.wsv": 1, "MCP_Kernel.wsv": 1}, 2,
     "事件内使用 1 + action:get 计数 1"),
    ("如果 (MCP命令服务器.是否监控自建URL请求)", {"MCP_Callbacks.wsv": 2, "MCP_Kernel.wsv": 1}, 3,
     "URL 事件内使用 2(开始创建/获得需授权证书; 下载进度那行带 && 不匹配) + get 计数 1"),
    ('("是否监控开发者窗口", MCP命令服务器.是否监控开发者窗口)', {"MCP_Kernel.wsv": 1}, 1,
     "action:get 状态 JSON 成员 1"),
    ('("是否监控自建URL请求", MCP命令服务器.是否监控自建URL请求)', {"MCP_Kernel.wsv": 1}, 1,
     "action:get 状态 JSON 成员 1"),
    ("event_devtoolspopup_enable", {"MCP_Server_Core.wsv": 1, "MCP_Server.wsv": 1}, 2, "action 分支 1 + schema 1"),
    ("event_urlreq_enable", {"MCP_Server_Core.wsv": 1, "MCP_Server.wsv": 1}, 2, "action 分支 1 + schema 1"),
]


def selfcheck_texts(texts, baseline):
    """对给定文本集合做静态自检（不读盘）。返回 (ok, 报告行列表)。

    texts    : 打补丁**之后**的文本
    baseline : 打补丁**之前**的原始文本（用于花括号增量比对）

    写成接受 texts/baseline 而不是自己读盘，是为了让 --dry-run 能在**写入前**就预演写盘后的自检结果。

    关于花括号：**不能用绝对相等**判定 —— 这些 .wsv 里字符串字面量与注释本身就含 `{`/`}` 字符
    （例如 `创建自文本 ("{}")`、文案里的 `**完全一致**` 附近的大括号等），原始文件本来就不绝对配平
    （实测原始 MCP_Server.wsv `{`1838 / `}`1828）。真正的不变式是**增量配平**：Δ{ == Δ}。
    """
    report = []
    ok = True
    for fn in TARGET_FILES:
        if fn not in texts:
            ok = False
            report.append("  [FAIL] 缺少 %s 的文本（无法自检）" % fn)

    # ① 12 个事件名各恰好 1 次声明
    report.append("  ① 12 个事件声明计数（在各自目标文件内）")
    for fn, names in EVENT_DECL.items():
        for nm in names:
            pat = "方法 " + nm + " <公开"
            c = texts.get(fn, "").count(pat)
            flag = "OK " if c == 1 else "FAIL"
            if c != 1:
                ok = False
            report.append("     [%s] %-28s %s: %d 次" % (flag, nm, fn, c))

    # ② 开关/action 出现次数
    report.append("  ② 开关与 action 落点计数")
    for s, per_file, total, note in EXPECTED_COUNTS:
        if per_file is None:
            continue
        sum_all = sum(texts.get(f, "").count(s) for f in TARGET_FILES)
        per_ok = all(texts.get(f, "").count(s) == n for f, n in per_file.items())
        good = (sum_all == total) and per_ok
        if not good:
            ok = False
        detail = ", ".join("%s:%d(期望%d)" % (f, texts.get(f, "").count(s), n) for f, n in per_file.items())
        report.append("     [%s] %-46s 合计 %d(期望%d) | %s | %s"
                      % ("OK " if good else "FAIL", s, sum_all, total, detail, note))

    # ③ 花括号：增量必须配平（Δ{ == Δ}）
    report.append("  ③ 花括号增量配平（Δ{ 必须 == Δ}；绝对值本来就不配平，仅作 info）")
    for fn in TARGET_FILES:
        o, c = brace_counts(texts.get(fn, ""))
        if baseline and fn in baseline:
            o0, c0 = brace_counts(baseline[fn])
            do, dc = o - o0, c - c0
            good = (do == dc)
            if not good:
                ok = False
            report.append("     [%s] %-26s Δ{ = %+d, Δ} = %+d  (绝对值 { %d / } %d, 差 %d 为改动前既有)"
                          % ("OK " if good else "FAIL", fn, do, dc, o, c, o - c))
        else:
            report.append("     [info] %-26s { = %d, } = %d, 差 = %d（无基线，未判定）" % (fn, o, c, o - c))

    # ④ 双倍行距完整性：双倍行距文件里，插入块不得引入"相邻非空行"
    if baseline:
        report.append("  ④ 双倍行距完整性（仅对空行占比 >0.35 的文件判定：相邻非空行对数增量必须为 0）")
        for fn in TARGET_FILES:
            if fn not in baseline:
                continue
            a0 = adjacent_nonblank_pairs(baseline[fn])
            a1 = adjacent_nonblank_pairs(texts.get(fn, ""))
            is_double = detect_style(fn, baseline[fn])[1]
            if is_double:
                good = (a1 - a0) == 0
                if not good:
                    ok = False
                report.append("     [%s] %-26s 相邻非空行对 %d -> %d (增量 %+d)"
                              % ("OK " if good else "FAIL", fn, a0, a1, a1 - a0))
            else:
                report.append("     [info] %-26s 单倍行距文件, 相邻非空行对 %d -> %d (增量 %+d, 不判定)"
                              % (fn, a0, a1, a1 - a0))

    # ⑤ 行尾纯净度：CRLF 文件不得混入孤立 LF，LF 文件不得混入 CRLF
    report.append("  ⑤ 行尾纯净度（不能往 CRLF 文件插 LF，反之亦然）")
    for fn in TARGET_FILES:
        lf, crlf, lone = eol_purity(texts.get(fn, ""))
        exp_eol = EXPECTED_STYLE[fn][0]
        if exp_eol == "\r\n":
            good = (lone == 0)
            detail = "CRLF=%d, LF总数=%d, 孤立LF=%d (期望 0)" % (crlf, lf, lone)
        else:
            good = (crlf == 0)
            detail = "CRLF=%d (期望 0), LF总数=%d" % (crlf, lf)
        if not good:
            ok = False
        report.append("     [%s] %-26s %s" % ("OK " if good else "FAIL", fn, detail))
    return ok, report


def post_write_selfcheck(baseline):
    """写盘后重新读盘做静态自检。返回 (ok, 报告行列表)。"""
    texts = {}
    for fn in TARGET_FILES:
        try:
            texts[fn] = read_file(os.path.join(SRC, fn))
        except Exception:
            pass
    return selfcheck_texts(texts, baseline)


def main():
    if "--verify-only" in sys.argv or "--check" in sys.argv:
        return verify_only_main()

    dry_run = "--dry-run" in sys.argv
    print("=" * 78)
    print("事件覆盖补齐 r115 补丁脚本  %s" % ("[DRY-RUN 不写任何文件]" if dry_run else "[写入模式]"))
    print("项目根: %s" % ROOT)
    print("=" * 78)

    # 1) 读全部目标文件
    files = {}
    for fn in TARGET_FILES:
        path = os.path.join(SRC, fn)
        if not os.path.isfile(path):
            raise RuntimeError("目标文件不存在: %s" % path)
        files[fn] = read_file(path)

    # 1.5) 冲突/重复应用守卫
    print("\n[0/5] 冲突与重复应用守卫（扫描 src/ 全部 *.wsv）")
    cok, creport = preflight_conflict_check()
    for line in creport:
        print(line)
    if not cok:
        raise ConflictError(
            "冲突守卫未通过：r115 的目标内容已存在于 src/。\n"
            "  → 这通常意味着**补丁已被应用过**（本仓库有并发 agent，本脚本作者已实测到这种情况）。\n"
            "  → 本脚本不做增量/幂等补丁，为避免重复方法声明，这里**中止且未写入任何文件**。\n"
            "  → 现在应该做的是：py -3 _audit/_apply_events_patch.py --verify-only   # 只读核对已落地结果"
        )

    # 2) 风格断言
    print("\n[1/5] 行尾/空行风格实测与断言")
    for fn in TARGET_FILES:
        problems, eol, ratio, nlines = check_style(fn, files[fn])
        eolname = {"\n": "LF", "\r\n": "CRLF", "mixed": "MIXED"}[eol]
        status = "OK " if not problems else "FAIL"
        print("  [%s] %-26s 行数=%-6d 行尾=%-5s 空行占比=%.3f  %s"
              % (status, fn, nlines, eolname, ratio,
                 ("(双倍行距)" if ratio > 0.35 else "(单倍行距)")))
        for pr in problems:
            print("        !! %s" % pr)
        if problems:
            raise RuntimeError("风格断言失败: %s -> %s（不做任何写入）" % (fn, "; ".join(problems)))

    # 3) 构建全部改动（锚点唯一性在内部强制）
    print("\n[2/5] 锚点唯一性校验 + 内存构建改动")
    patchers = build_patches(files)
    total_ops = 0
    for fn in TARGET_FILES:
        p = patchers[fn]
        print("  %s：" % fn)
        for kind, desc, nlines, anchor in p.log:
            print("    - [%s] %s" % (kind, desc))
            print("        插入/替换 %d 行 | 锚点原文: %s" % (nlines, anchor))
        total_ops += len(p.log)

    # 4) 花括号配平增量校验
    print("\n[3/5] 花括号配平增量校验（{ 增量必须 == } 增量）")
    for fn in TARGET_FILES:
        o0, c0 = brace_counts(files[fn])
        o1, c1 = brace_counts(patchers[fn].text)
        do, dc = o1 - o0, c1 - c0
        status = "OK " if do == dc else "FAIL"
        print("  [%s] %-26s Δ{ = %+d, Δ} = %+d" % (status, fn, do, dc))
        if do != dc:
            raise RuntimeError("花括号增量不配平: %s (Δ{=%d, Δ}=%d) —— 不写任何文件" % (fn, do, dc))

    print("\n  共 %d 个操作（%d 个文件）" % (total_ops, len(TARGET_FILES)))

    # 5) dry-run 出口
    if dry_run:
        print("\n[4/5] DRY-RUN 内容预览（每个文件的前 2 个插入块）")
        for fn in TARGET_FILES:
            p = patchers[fn]
            ins = [e for e in p.log if e[1] and e[2] > 0]
            if not ins:
                continue
            print("\n  --- %s ---" % fn)
            for kind, desc, nlines, anchor in ins[:2]:
                print("    >> %s (%d 行, 锚点: %s)" % (desc, nlines, anchor))

        # 预演写盘后的自检（在内存结果上跑同一套检查，不写盘）
        print("\n[5/5] 预演：写盘后自检会对内存中这些文本输出以下结果")
        sim_ok, sim_report = selfcheck_texts(dict((fn, patchers[fn].text) for fn in TARGET_FILES), files)
        for line in sim_report:
            print(line)
        print("\n预演自检结论: %s" % ("全部通过" if sim_ok else "存在 FAIL 项 —— 请先修脚本/源码，不要落盘"))
        print("\nDRY-RUN 结束：未创建备份、未写入任何文件。")
        if sim_ok:
            print("      校验全部通过。去掉 --dry-run 即可落盘。")
        print("=" * 78)
        return 0 if sim_ok else 2

    # 6) 备份
    print("\n[4/5] 备份到 %s" % BACKUP_DIR)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for fn in TARGET_FILES:
        dst = os.path.join(BACKUP_DIR, fn)
        if os.path.exists(dst):
            print("  [skip] 备份已存在（保留不覆盖）: %s" % dst)
        else:
            shutil.copy2(os.path.join(SRC, fn), dst)
            print("  [ok  ] 已备份: %s" % dst)

    # 7) 写入（二进制写，保持 UTF-8 无 BOM 与原行尾）
    print("\n[5/5] 写入")
    for fn in TARGET_FILES:
        path = os.path.join(SRC, fn)
        data = patchers[fn].text.encode("utf-8")
        with open(path, "wb") as f:
            f.write(data)
        nlines = len(patchers[fn].log)
        print("  [ok  ] %-26s %d 处改动, %d 字节" % (fn, nlines, len(data)))
        for kind, desc, nl, anchor in patchers[fn].log:
            print("          - %s (%+d 行) 锚点: %s" % (desc, nl, anchor))

    # 8) 自检
    print("\n静态自检（写盘后重新读盘，基线=写入前内存原文）")
    ok, report = post_write_selfcheck(files)
    for line in report:
        print(line)
    print("\n" + ("自检全部通过（注意：这只是文本层面的静态检查，**不等于编译通过**，也更不等于真机验证通过）"
                  if ok else "自检存在 FAIL 项 —— 请查看上面 [FAIL] 行；备份在 %s" % BACKUP_DIR))
    print("=" * 78)
    return 0 if ok else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ConflictError as e:
        print("\n" + "=" * 78)
        print("安全中止：目标内容已存在，未写入任何文件。")
        print(str(e))
        print("=" * 78)
        sys.exit(4)
    except PatchError as e:
        print("\n" + "!" * 78, file=sys.stderr)
        print("锚点定位失败（未写入任何文件）", file=sys.stderr)
        print("  文件  : %s" % e.filename, file=sys.stderr)
        print("  用途  : %s" % e.desc, file=sys.stderr)
        print("  期望命中数: 1, 实际: %d" % e.found, file=sys.stderr)
        print("  锚点原文:\n%s" % "\n".join("      | " + x for x in e.needle.split("\n")), file=sys.stderr)
        if e.text:
            print("  该文件里最接近的候选行（原文，带行号）:", file=sys.stderr)
            print(diagnose(e.text, e.needle), file=sys.stderr)
        print("\n完整 traceback:", file=sys.stderr)
        traceback.print_exc()
        print("!" * 78, file=sys.stderr)
        sys.exit(3)
    except Exception:
        print("\n" + "!" * 78, file=sys.stderr)
        print("脚本异常（未写入任何文件，除非异常发生在写入阶段之后）", file=sys.stderr)
        traceback.print_exc()
        print("!" * 78, file=sys.stderr)
        sys.exit(1)
