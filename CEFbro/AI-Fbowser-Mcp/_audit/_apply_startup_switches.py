# -*- coding: utf-8 -*-
"""启动期 Chromium 开关通道 (v1) —— 补丁施加脚本

由主代理运行; 本脚本**不编译、不调用 MCP、不重启程序**, 只改源码文本与配置文本。

================================================================================
改了哪些文件 / 各插几条
================================================================================
[P1] src/MCP_Server.wsv  (类 MCP命令服务器, 类级变量区) ---- 插 1 条 (共 12 行, 含 1 行前导空行)
     6 个配置位静态字段 + 2 个回执静态字段:
       启动开关_启用摄像头 / 启动开关_启用录音 / 启动开关_启用自动播放 /
       启动开关_禁用GPU / 启动开关_禁用GPU缓存 / 启动开关_忽略GPU禁用清单
       命令行开关已应用 (文本, 回执) / 命令行开关原文 (文本, 回执)
     位置: 紧接 `变量 是否自动关闭JS对话框 ...` 之后。

[P2] src/MCP_Server.wsv  (方法 加载MCP配置 体内) ---- 插 1 条 (共 27 行)
     读 mcp_config.json 的 6 个独立布尔键 -> 上述 6 个静态字段。
     键名: enable_media_stream / enable_speech_input / enable_autoplay /
           disable_gpu / disable_gpu_cache / ignore_gpu_blocklist  (缺键即假)
     位置: 紧接 `如果 (配置解析.取逻辑值 ("auto_dismiss_js_dialog")) {...}` 块之后。

[P3] src/main.wsv  (方法 即将处理命令行 体内, 方法体第一段) ---- 插 1 条 (共 56 行)
     白名单施加 (只在为真时调用, 无任何自由文本透传):
       启用摄像头 / 启用录音 / 启用自动播放 / 禁用GPU / 禁用GPU缓存 / 忽略GPU禁用清单
     门控: 只在 `进程类型 == ""` (浏览器进程) 时施加。
     回执: 写 命令行开关已应用 / 命令行开关原文, 并用 控制台输出 打印一行。
     位置: 方法体 `{` 之后、原有 `如果 (MCP命令服务器.是否监控启动流程 == 假) { 返回 }`
           之前 —— 否则默认关掉启动流程监控时该守卫会提前 return, 开关永不生效。

[P1R] src/MCP_Server.wsv  (锚点行尾) ---- 条件性 1 条: 修复 v1 首版 P1 的"落地粘连"
     首版 P1_INSERT 首行前少一个换行, 落地后块首行被粘在锚点行尾:
       <锚点><4空格># ==== 启动期开关通道v1: ...
     后果: 类级变量声明行尾挂上一段 '#' 注释文本 (火山解析敏感)。本补丁就地补一个换行修复;
     仅在检测到粘连形态时才会动作, 健康形态/未落地时判为"无需修复"。

[P4] mcp_config.json (+ 存在时的同内容副本 src/mcp_config.json 与
     _int/AI-Fbowser-Mcp/debug/x64/linker/mcp_config.json) ---- 插 1 条 (6 个键)
     把 6 个键以 false 写进配置, 便于后续按需翻转; 全假 = 行为与改动前完全一致。

================================================================================
断言了什么 (全部通过才允许写文件; 任一失败即中止且不写任何文件)
================================================================================
A1  只用原文锚点定位, 绝不用行号; 每个锚点/签名在文件中的命中数必须**恰好 1**,
    否则中止 (命中 0 或 >1 都会打印该文件的相关片段)。
A2  花括号增量配平: 每个被改文件的整体花括号末深度与改前**完全一致**(增量 0),
    最小深度 >= 0, 末深度 == 0 (扫描器规则与 _audit/brace_check.py 一致:
    跳过 @ / // / # 起始行, 剥掉行尾注释, 字符串内括号不计数)。
A3  插入块自身配平 (块内花括号增量 == 0, 且中途不低于 0)。
A4  作用域自检: 插入块里每一条 `变量 ...` 声明都必须位于该块的**相对深度 0**
    (即不在任何内层 `如果 { }` 里) —— 火山里分支内声明的变量块外不可见。
    P3 需要跨块使用的 启动开关清单 / 启动开关命令行 均声明在方法体顶层。
A5  P1: 8 个新变量名与 8 个 @输出名 在 MCP_Server.wsv 中各出现**恰好 1 次**。
A6  P3 白名单封闭: 插入块内所有 `命令行.X (...)` 调用只能来自 6 个白名单方法
    (启用摄像头/启用录音/启用自动播放/禁用GPU/禁用GPU缓存/忽略GPU禁用清单) 或只读访问器
    (取字符串 —— 仅用于回执核对);
    禁止方法 (置值/置项值/置程序/置额外参数/插入值/设置全局代理/设置远程调试端口/
    启用无头模式/启用单进程模式/启用跨框架操作模式) 在插入块内出现即失败;
    另外全 main.wsv 内 `命令行.置值` 与 `命令行.置项值` 必须为 0 次
    (即: 不存在"传任意 switch 字符串"的口子)。
A7  P2: 读取的键名集合恰为约定的 6 个。
A8  P4: 新文本必须是合法 JSON; 解析后与旧解析结果相比, **原有键值逐一不变**,
    只多出这 6 个键且值均为 false。
A9  写后复核: 重新读回字节, 编码 (UTF-8 无 BOM / UTF-16LE) 与行尾 (LF / CRLF)
    与改前一致; 文本与原文本的差异**恰为插入块本身**(new == old 注入点替换结果);
    标记 [启动期开关通道v1] 计数恰好 +1。
A10 幂等: 每个补丁有独立签名 + 块标记 (启动期开关通道v1); 已落地的补丁跳过 (不重复插入);
    签名与标记不自洽 (签名在而标记不在, 或标记数 != 该文件已落地补丁数) 时中止。
A11 未接线项核对: main.wsv 里 `命令行.启用无头模式` 调用 0 次 (类库 启用无头模式 的方法体
    实为 FBroHsCommandLine_EnableAutoplayPoliey, 是复制粘贴 Bug, 名实不符, 禁止接线)。
A12 插入块必须以换行开头 (否则块首行会粘在锚点行尾 —— v1 首版就是这样粘上去的);
    修复后不得存在"声明行尾挂 # 注释"的行; P1R 修复后块标记数不得变化。
A13 同文件多补丁**链式累计**: P2 的新文本建立在 P1 的新文本之上。首版没做链式, P2 以"改前原文"
    重写整文件, 把 P1 刚插入的块静默抹掉 (每个补丁的写后复核却各自自洽) —— 沙箱自测抓到的真实事故。

================================================================================
本脚本**没有验证什么** (编译与真机验证由主代理串行执行, 不得据本脚本声称已验证)
================================================================================
1. 未编译。火山编译器是否接受插入文本、8 个新字段与调用点是否 0 错 0 警, 全部未知。
2. 未运行。开关是否真的进了 CEF 命令行、navigator.mediaDevices/autoplay 是否真的可用、
   GPU 是否真的被禁用, 全部未知; 唯一可自证的中间证据是运行期
   `MCP命令服务器.命令行开关原文` (由 控制台输出 打到 stdout) 与启动日志一行回执。
3. 未验证 "Chromium 子进程命令行由浏览器进程命令行复制而来" 这一继承性假设 ——
   它正是 P3 只门控在浏览器进程的理由; 若该假设不成立, 渲染进程侧开关
   (enable-media-stream / autoplay 等) 可能只落在浏览器进程。
4. 未验证 `即将处理命令行` 在本项目架构下是否真的会在渲染子进程被派发
   (类库注释说"都会执行"; 但本项目 启动方法 首段的单实例互斥体会让子进程立刻退出,
   故子进程侧静态字段是否/何时可见未测)。门控使该不确定性不影响浏览器进程的行为。
5. 未验证 `禁用GPU缓存` / `忽略GPU禁用清单` 对应的真实 Chromium switch 名
   (类库注释只写了 启用摄像头/启用录音/启用自动播放/禁用代理 的名字, 其余未写),
   故回执只如实记录"调用过哪个方法", 不声称具体 switch 串。
6. 未验证 `启用自动播放` 实际写入的是 --autoplay-policy 还是类库注释里那个拼错的
   autoplay-poliey; 未验证 `忽略GPU禁用清单` 与 `禁用GPU` 同时为真时的内核行为。
7. 未改 mcp_config.README.md 与 docs 里的配置字段表 (新增 6 个键未写进文档)。
8. 未验证 6 个键全为真时是否引入新的启动崩溃/兼容问题 (本脚本只按需接线, 默认全假)。
9. 未加"MCP 工具可查询这些回执字段"的读取入口 (本次不改工具清单/分发表);
   回执目前只能从进程内静态字段与启动期 stdout 看到。

用法:
    py -3 _audit/_apply_startup_switches.py --dry-run        # 只校验 + 预览, 不写文件
    py -3 _audit/_apply_startup_switches.py                  # 校验通过后落盘 (写前自动备份; 幂等)
    py -3 _audit/_apply_startup_switches.py --verify-only    # 只读核对已落地结果
退出码: 0 = 成功/核对通过; 1 = 断言或核对失败; 2 = 环境/锚点异常(已打印 traceback 与片段)

配套说明见 `_audit/_startup_switches_plan.md` (设计依据 / 门控理由 / 回滚配方 / 验收手册)。
"""

import argparse
import io
import json
import os
import re
import shutil
import sys
import traceback
from datetime import datetime

# ---------------------------------------------------------------- 控制台 UTF-8 兜底
# (Windows 控制台默认 GBK, 中文 print 会抛 UnicodeEncodeError 把结论吞掉; 见 _audit/_console.py)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
BACKUP_DIR = os.path.join(ROOT, "备份", "启动开关通道-写入前")

MAIN = os.path.join(SRC, "main.wsv")
SERVER = os.path.join(SRC, "MCP_Server.wsv")
CONFIG = os.path.join(ROOT, "mcp_config.json")
# 与根配置同内容的副本(编译产物目录/m 源码目录各一份); 存在则一并加键, 让运行中的 exe 也能读到
CONFIG_MIRRORS = [
    os.path.join(SRC, "mcp_config.json"),
    os.path.join(ROOT, "_int", "AI-Fbowser-Mcp", "debug", "x64", "linker", "mcp_config.json"),
]

MARK = "启动期开关通道v1"   # 每个插入块内恰好出现 1 次 (块注释里的标记, 用于幂等与结构核对)

CONFIG_KEYS = [
    "enable_media_stream",
    "enable_speech_input",
    "enable_autoplay",
    "disable_gpu",
    "disable_gpu_cache",
    "ignore_gpu_blocklist",
]

NEW_VARS = [
    ("启动开关_启用摄像头", "StartupSwitchEnableMediaStream", "逻辑型",
     "逻辑型 值 = 假", "mcp_config.json enable_media_stream: 为真时启动期对命令行调用 启用摄像头(enable-media-stream)"),
    ("启动开关_启用录音", "StartupSwitchEnableSpeechInput", "逻辑型",
     "逻辑型 值 = 假", "mcp_config.json enable_speech_input: 为真时启动期对命令行调用 启用录音(enable-speech-input)"),
    ("启动开关_启用自动播放", "StartupSwitchEnableAutoplay", "逻辑型",
     "逻辑型 值 = 假", "mcp_config.json enable_autoplay: 为真时启动期对命令行调用 启用自动播放"),
    ("启动开关_禁用GPU", "StartupSwitchDisableGpu", "逻辑型",
     "逻辑型 值 = 假", "mcp_config.json disable_gpu: 为真时启动期对命令行调用 禁用GPU"),
    ("启动开关_禁用GPU缓存", "StartupSwitchDisableGpuCache", "逻辑型",
     "逻辑型 值 = 假", "mcp_config.json disable_gpu_cache: 为真时启动期对命令行调用 禁用GPU缓存"),
    ("启动开关_忽略GPU禁用清单", "StartupSwitchIgnoreGpuBlocklist", "逻辑型",
     "逻辑型 值 = 假", "mcp_config.json ignore_gpu_blocklist: 为真时启动期对命令行调用 忽略GPU禁用清单"),
]

ALLOWED_CMDLINE_CALLS = [
    "启用摄像头", "启用录音", "启用自动播放", "禁用GPU", "禁用GPU缓存", "忽略GPU禁用清单",
]
# 只读访问器: 只允许"读命令行"用于如实回执, 不允许任何带参写入器
ALLOWED_CMDLINE_READERS = ["取字符串", "是否存在某项", "取项值", "取程序", "取额外参数",
                           "是否有效", "是否为空"]
# 禁止出现在插入块里的调用 (自由文本透传口 / 参数化口 / 类库已知名实不符的口)
FORBIDDEN_CMDLINE_CALLS = [
    "置值", "置项值", "置程序", "置额外参数", "插入值",
    "设置全局代理", "VIP_高级_设置全局代理", "设置远程调试端口",
    "启用无头模式", "启用单进程模式", "启用跨框架操作模式", "禁用代理",
]

# ================================================================ 插入文本 (LF; 写盘时按文件行尾转换)

P1_INSERT = """
    # ==== 启动期开关通道v1: 启动期 Chromium 开关的配置字段 (由 _audit/_apply_startup_switches.py 插入) ====
    # 白名单布尔键来源: mcp_config.json (加载MCP配置 在 FBrowser_初始化 之前调用, 时机天然合适);
    # 消费点: 启动类.即将处理命令行; 全部默认假 => 不写配置时行为与改动前完全一致。
    变量 启动开关_启用摄像头 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json enable_media_stream: 为真时启动期对命令行调用 启用摄像头(enable-media-stream)" @输出名 = "StartupSwitchEnableMediaStream">
    变量 启动开关_启用录音 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json enable_speech_input: 为真时启动期对命令行调用 启用录音(enable-speech-input)" @输出名 = "StartupSwitchEnableSpeechInput">
    变量 启动开关_启用自动播放 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json enable_autoplay: 为真时启动期对命令行调用 启用自动播放" @输出名 = "StartupSwitchEnableAutoplay">
    变量 启动开关_禁用GPU <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json disable_gpu: 为真时启动期对命令行调用 禁用GPU" @输出名 = "StartupSwitchDisableGpu">
    变量 启动开关_禁用GPU缓存 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json disable_gpu_cache: 为真时启动期对命令行调用 禁用GPU缓存" @输出名 = "StartupSwitchDisableGpuCache">
    变量 启动开关_忽略GPU禁用清单 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json ignore_gpu_blocklist: 为真时启动期对命令行调用 忽略GPU禁用清单" @输出名 = "StartupSwitchIgnoreGpuBlocklist">
    变量 命令行开关已应用 <公开 静态 类型 = 文本型 值 = "" 注释 = "启动期如实回执: 实际调用过的开关(半角分号分隔, 末尾带分号; 空=一个都没应用), 由 启动类.即将处理命令行 写入" @输出名 = "CmdLineSwitchesApplied">
    变量 命令行开关原文 <公开 静态 类型 = 文本型 值 = "" 注释 = "启动期如实回执: 施加完毕后的浏览器进程命令行原文(命令行.取字符串), 空=未在浏览器进程施加" @输出名 = "CmdLineSwitchRawText">
"""

P2_INSERT = """
        // ==== 启动期开关通道v1: 6 个独立布尔键(默认假, 缺键即假) ====
        // 只读配置写静态字段; 真正施加在 启动类.即将处理命令行 里完成(FBrowser_初始化 之前)
        如果 (配置解析.取逻辑值 ("enable_media_stream"))
        {
            启动开关_启用摄像头 = 真
        }
        如果 (配置解析.取逻辑值 ("enable_speech_input"))
        {
            启动开关_启用录音 = 真
        }
        如果 (配置解析.取逻辑值 ("enable_autoplay"))
        {
            启动开关_启用自动播放 = 真
        }
        如果 (配置解析.取逻辑值 ("disable_gpu"))
        {
            启动开关_禁用GPU = 真
        }
        如果 (配置解析.取逻辑值 ("disable_gpu_cache"))
        {
            启动开关_禁用GPU缓存 = 真
        }
        如果 (配置解析.取逻辑值 ("ignore_gpu_blocklist"))
        {
            启动开关_忽略GPU禁用清单 = 真
        }
"""

P3_INSERT = """
        // ==== 启动期开关通道v1: Chromium 启动期开关 (只在此处接线, 白名单, 无自由文本透传) ====
        // 依据(类库原文): FBroEventControl.wsv:290 "浏览器进程和渲染进程都会执行, 在此次可以对命令行参数进行操作";
        //   同文件 :291 "The |process_type| value will be empty for the browser process, 此参数只会在子进程中才会有值"。
        // 门控在 `进程类型 == ""` (浏览器进程) 才施加, 理由:
        //   ① 本项目的 mcp_config.json 只在主进程 启动方法 里经 MCP命令服务器.加载MCP配置 读取;
        //      渲染子进程不执行 启动方法(启动方法 首段的单实例互斥体会在子进程里立刻 ERROR_ALREADY_EXISTS
        //      并 return 0 —— 若子进程真跑它, 渲染进程会自杀, 而实际渲染正常), 故子进程里这些静态字段恒为默认假,
        //      不加门控只会读到假值/记下"什么都没应用", 让回执失真;
        //   ② Chromium 子进程命令行由浏览器进程命令行复制而来(本项目未真机验证该继承性), 故在浏览器进程施加即覆盖全部进程。
        // ⚠ 禁用类库的 启用无头模式: 它的方法体实为 FBroHsCommandLine_EnableAutoplayPoliey(与 启用自动播放 同一函数),
        //   是类库复制粘贴 Bug, 名实不符, 禁止接线。
        变量 启动开关清单 <类型 = 文本型>
        启动开关清单 = ""
        变量 启动开关命令行 <类型 = 文本型>
        启动开关命令行 = ""
        如果 (进程类型 == "")
        {
            如果 (MCP命令服务器.启动开关_启用摄像头)
            {
                命令行.启用摄像头 ()
                启动开关清单 = 启动开关清单 + "enable_media_stream;"
            }
            如果 (MCP命令服务器.启动开关_启用录音)
            {
                命令行.启用录音 ()
                启动开关清单 = 启动开关清单 + "enable_speech_input;"
            }
            如果 (MCP命令服务器.启动开关_启用自动播放)
            {
                命令行.启用自动播放 ()
                启动开关清单 = 启动开关清单 + "enable_autoplay;"
            }
            如果 (MCP命令服务器.启动开关_禁用GPU)
            {
                命令行.禁用GPU ()
                启动开关清单 = 启动开关清单 + "disable_gpu;"
            }
            如果 (MCP命令服务器.启动开关_禁用GPU缓存)
            {
                命令行.禁用GPU缓存 ()
                启动开关清单 = 启动开关清单 + "disable_gpu_cache;"
            }
            如果 (MCP命令服务器.启动开关_忽略GPU禁用清单)
            {
                命令行.忽略GPU禁用清单 ()
                启动开关清单 = 启动开关清单 + "ignore_gpu_blocklist;"
            }
            启动开关命令行 = 命令行.取字符串 ()
        }
        MCP命令服务器.命令行开关已应用 = 启动开关清单
        MCP命令服务器.命令行开关原文 = 启动开关命令行
        如果 (启动开关清单 != "")
        {
            控制台输出 ("[AI浏览器] 启动期命令行开关已应用: " + 启动开关清单)
        }
"""

# ================================================================ 补丁定义 (锚点 = 原文, 绝不用行号)

ANCHOR_P1 = '    变量 是否自动关闭JS对话框 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "自动化模式下自动确认alert/confirm/prompt" @输出名 = "IsAutoCloseJSDialog">'

ANCHOR_P2 = """        如果 (配置解析.取逻辑值 ("auto_dismiss_js_dialog"))
        {
            是否自动关闭JS对话框 = 真
        }"""

ANCHOR_P3 = """    方法 即将处理命令行 <公开 @虚拟方法 = 可覆盖>
    参数 进程类型 <类型 = 文本型 @输出名 = "ProcessType">
    参数 命令行 <类型 = 类_FBrowser_命令行 @输出名 = "CommandLine">
    {"""

# P1 的历史落地缺陷: v1 脚本早期版本里 P1_INSERT 首行前少一个换行, 于是块首行被粘在锚点行尾
#   <锚点><4空格># ==== 启动期开关通道v1: ...
# 该形态会让类级变量声明行尾挂上一段 '#' 注释文本 (火山解析敏感), 必须就地补一个换行修复。
P1_FIRST_LINE = P1_INSERT.split("\n")[1]
GLUE_P1 = ANCHOR_P1 + P1_FIRST_LINE
FIXED_P1 = ANCHOR_P1 + "\n" + P1_FIRST_LINE


class PatchError(Exception):
    pass


class Report(object):
    def __init__(self):
        self.fail = []
        self.warn = []
        self.ok = []
        self.lines = []

    def p(self, s=""):
        print(s)
        self.lines.append(s)

    def ok_(self, tag, msg=""):
        self.ok.append(tag)
        self.p("  [OK]   %-34s %s" % (tag, msg))

    def warn_(self, tag, msg=""):
        self.warn.append(tag)
        self.p("  [WARN] %-34s %s" % (tag, msg))

    def fail_(self, tag, msg=""):
        self.fail.append(tag)
        self.p("  [FAIL] %-34s %s" % (tag, msg))


R = Report()


# ================================================================ 文件 IO (编码/行尾保真)

def read_text(path):
    """返回 (text, encoding, bom, newline)。

    约定: 返回的 **text 一律是 LF 归一化文本**(内部一律用 \\n 拼接/比较),
    文件真实行尾由 newline 单独保存, 写回时由 write_text 统一转换 ——
    这样锚点、插入块、反注入还原三项比较都在同一空间里做, 不会出现 CRLF 双重转换。
    本项目 .wsv = UTF-8 无 BOM + LF; mcp_config.json = UTF-8 无 BOM + CRLF。
    """
    raw = open(path, "rb").read()
    if raw[:2] == b"\xff\xfe":
        enc, bom, body = "utf-16-le", b"\xff\xfe", raw[2:]
    elif raw[:3] == b"\xef\xbb\xbf":
        enc, bom, body = "utf-8", b"\xef\xbb\xbf", raw[3:]
    else:
        enc, bom, body = "utf-8", b"", raw
    text = body.decode(enc)
    crlf = text.count("\r\n")
    lf = text.count("\n")
    if lf and crlf == lf:
        nl = "\r\n"
    elif crlf == 0:
        nl = "\n"
    else:
        raise PatchError("%s 行尾混用 (LF=%d CRLF=%d), 拒绝改写" % (path, lf, crlf))
    return text.replace("\r\n", "\n"), enc, bom, nl


def encode_text(text, enc, bom, nl):
    out = text.replace("\n", nl) if nl != "\n" else text
    return bom + out.encode(enc)


def write_text(path, text, enc, bom, nl):
    data = encode_text(text, enc, bom, nl)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def lineno_of(text, needle):
    idx = text.find(needle)
    return text.count("\n", 0, idx) + 1 if idx >= 0 else -1


def dump_context(path, needles, before=5, after=5, limit=4):
    """打印相关文件片段: 定位 needle (或其中最接近的片段), 输出带行号的上下文。"""
    try:
        text, _, _, _ = read_text(path)
    except Exception as ex:
        print("      (片段读取失败: %s)" % ex)
        return
    lines = text.split("\n")
    hits = []
    for nd in needles:
        for m in re.finditer(re.escape(nd), text):
            hits.append(text.count("\n", 0, m.start()))
            if len(hits) >= limit:
                break
    if not hits:
        # 退化: 用 needle 里最长的中文片段做模糊定位
        for nd in needles:
            for frag in sorted(re.split(r"[\s<>=()\"]+", nd), key=len, reverse=True)[:3]:
                if len(frag) < 4:
                    continue
                for m in re.finditer(re.escape(frag), text):
                    hits.append(text.count("\n", 0, m.start()))
                    break
            if hits:
                break
    if not hits:
        print("      (在 %s 中定位不到任何相关片段)" % path)
        return
    for h in sorted(set(hits))[:limit]:
        print("      --- %s 第 %d 行附近 ---" % (os.path.relpath(path, ROOT), h + 1))
        for i in range(max(0, h - before), min(len(lines), h + after + 1)):
            print("      %5d | %s" % (i + 1, lines[i]))
    print("      (%s 共 %d 行)" % (os.path.relpath(path, ROOT), len(lines)))


# ================================================================ 花括号扫描 (规则同 _audit/brace_check.py)

def brace_scan(text):
    """返回 (末深度, 最小深度, [首次转负行号...])。跳过 @///# 起始行, 剥行尾注释, 字符串内不计数。"""
    depth = 0
    mn = 0
    bad = []
    for i, raw in enumerate(text.split("\n")):
        s = raw.strip()
        if s.startswith("@") or s.startswith("//") or s.startswith("#"):
            continue
        keep = []
        inq = False
        j = 0
        while j < len(s):
            c = s[j]
            if inq:
                if c == "\\":
                    j += 2
                    continue
                if c == '"':
                    inq = False
            else:
                if c == "/" and j + 1 < len(s) and s[j + 1] == "/":
                    break
                if c == '"':
                    inq = True
                elif c in "{}":
                    keep.append(c)
            j += 1
        depth += keep.count("{") - keep.count("}")
        if depth < mn:
            mn = depth
            bad.append(i + 1)
    return depth, mn, bad


def scope_audit(block, label):
    """作用域自检: 插入块里每条 `变量` 声明都必须在块内相对深度 0 (分支内声明块外不可见)。"""
    issues = []
    depth = 0
    for i, raw in enumerate(block.split("\n")):
        s = raw.strip()
        if s.startswith("//") or s.startswith("#") or s.startswith("@"):
            continue
        if re.match(r"^变量\s+\S", s) and depth != 0:
            issues.append("%s 第 %d 行 `%s` 声明在相对深度 %d (分支内 -> 块外不可见)"
                          % (label, i + 1, s.split("<")[0].strip(), depth))
        keep = []
        inq = False
        j = 0
        while j < len(s):
            c = s[j]
            if inq:
                if c == "\\":
                    j += 2
                    continue
                if c == '"':
                    inq = False
            else:
                if c == "/" and j + 1 < len(s) and s[j + 1] == "/":
                    break
                if c == '"':
                    inq = True
                elif c in "{}":
                    keep.append(c)
            j += 1
        depth += keep.count("{") - keep.count("}")
        if depth < 0:
            issues.append("%s 第 %d 行 相对深度转负" % (label, i + 1))
            break
    if depth != 0:
        issues.append("%s 块末相对深度 = %d (要求 0)" % (label, depth))
    return issues


# ================================================================ 补丁解析 / 校验

def build_patches():
    return [
        {
            "id": "P1", "kind": "text", "path": SERVER, "anchor": ANCHOR_P1, "insert": P1_INSERT,
            "mode": "after", "sig": "变量 启动开关_启用摄像头 ",
            "doc": "类 MCP命令服务器 追加 8 个启动期开关静态字段",
            "hints": ['变量 是否自动关闭JS对话框', 'IsAutoCloseJSDialog'],
        },
        {
            "id": "P1R", "kind": "glue", "path": SERVER, "glued": GLUE_P1, "fixed": FIXED_P1,
            "doc": "修复 P1 落地粘连(块首行被粘在锚点行尾, 少一个换行)",
            "hints": ['IsAutoCloseJSDialog', '启动期开关通道v1'],
            "sig": None,
        },
        {
            "id": "P2", "kind": "text", "path": SERVER, "anchor": ANCHOR_P2, "insert": P2_INSERT,
            "mode": "after", "sig": '如果 (配置解析.取逻辑值 ("enable_media_stream"))',
            "doc": "加载MCP配置 读 6 个布尔键写静态字段",
            "hints": ['auto_dismiss_js_dialog', '配置解析.取逻辑值'],
        },
        {
            "id": "P3", "kind": "text", "path": MAIN, "anchor": ANCHOR_P3, "insert": P3_INSERT,
            "mode": "after", "sig": "MCP命令服务器.命令行开关已应用 = 启动开关清单",
            "doc": "即将处理命令行 白名单施加 + 回执",
            "hints": ['方法 即将处理命令行', '记录应用监控事件 ("app_startup_cmdline"'],
        },
        {
            "id": "P4", "kind": "json", "path": CONFIG, "keys": CONFIG_KEYS,
            "sig": '"enable_media_stream"',
            "doc": "mcp_config.json 预置 6 个开关键(全 false)",
            "hints": ['"window_topmost"'],
        },
    ]


def json_plan(text):
    """返回 (new_text, insert_text)。文本一律 LF 空间; 锚点 = 唯一一行 "window_topmost": <bool>[,]。

    兼容两种形态: (甲) 该行是最后一个键(无逗号) -> 需补一个逗号; (乙) 该行后面还有别的键(带逗号)
    -> 直接续接, 不再补逗号, 否则会产生 ",," 这种非法 JSON (会被下游 json.loads 断言当场拦下)。
    """
    pat = re.compile(r'(?m)^([ \t]*)"window_topmost"[ \t]*:[ \t]*(true|false)[ \t]*(,?)[ \t]*$')
    ms = list(pat.finditer(text))
    if len(ms) != 1:
        raise PatchError('mcp_config.json 锚点 `"window_topmost": <bool>` 命中 %d 次 (要求恰好 1)' % len(ms))
    m = ms[0]
    has_comma = bool(m.group(3))
    keys_text = (",\n").join('  "%s": false' % k for k in CONFIG_KEYS)
    insert = ("" if has_comma else ",") + "\n" + keys_text
    new = text[:m.end()] + insert + text[m.end():]
    return new, insert


def resolve(patches):
    """阶段一: 读文件、定位锚点、判定已落地/待插入。任何异常 -> PatchError。"""
    for p in patches:
        path = p["path"]
        if not os.path.exists(path):
            raise PatchError("[%s] 目标文件不存在: %s" % (p["id"], path))
        text, enc, bom, nl = read_text(path)
        p["text"], p["enc"], p["bom"], p["nl"] = text, enc, bom, nl
        p["_enc_desc"] = ("%s%s" % (enc, "+BOM" if bom else "")).ljust(16) + \
                         ("CRLF" if nl == "\r\n" else "LF")
        if p["kind"] == "glue":
            # 粘连修复补丁: 只有"健康形态没有 + 粘连形态恰好 1 次"时才需要修
            n_glue = text.count(p["glued"])
            n_fixed = text.count(p["fixed"])
            if n_fixed == 1 and n_glue == 0:
                p["state"] = "healthy"
            elif n_glue == 1 and n_fixed == 0:
                p["state"] = "pending"
            elif n_glue == 0 and n_fixed == 0:
                p["state"] = "na"       # P1 尚未落地 -> 不存在粘连, 无需修复
            else:
                p["state"] = "blocked"
                raise PatchError("[%s] 粘连形态 %d 次 / 健康形态 %d 次 —— 无法判定 (要求 粘连=1且健康=0, "
                                 "或 健康=1且粘连=0, 或两者皆 0)" % (p["id"], n_glue, n_fixed))
        elif p["kind"] == "text":
            n_anchor = text.count(p["anchor"])
            n_sig = text.count(p["sig"])
            if n_sig >= 1:
                # 已落地: 必须自洽 (签名恰好 1 次, 且块标记已被引入)
                p["state"] = "applied"
                p["n_anchor"] = n_anchor
                p["n_sig"] = n_sig
                if n_sig != 1:
                    raise PatchError("[%s] 签名在 %s 命中 %d 次 (要求恰好 1) —— 疑似重复插入"
                                     % (p["id"], os.path.relpath(path, ROOT), n_sig))
                if text.count(MARK) < 1:
                    raise PatchError("[%s] 签名已存在但块标记 %s 缺失 —— 文件状态不自洽"
                                     % (p["id"], MARK))
            elif n_anchor == 1:
                p["state"] = "pending"
                p["n_anchor"] = 1
            else:
                p["state"] = "blocked"
                raise PatchError("[%s] 锚点在 %s 命中 %d 次 (要求恰好 1)" %
                                 (p["id"], os.path.relpath(path, ROOT), n_anchor))
        else:
            present = [k for k in p["keys"] if ('"%s"' % k) in text]
            if len(present) == len(p["keys"]):
                p["state"] = "applied"
                p["new_text"], p["insert"], p["insert_final"] = text, "", ""
                p["base_text"] = text
            elif present:
                raise PatchError("[%s] %s 只含部分新键 %s —— 拒绝在中间状态上叠加"
                                 % (p["id"], os.path.relpath(path, ROOT), present))
            else:
                p["state"] = "pending"
                p["new_text"], p["insert"] = json_plan(text)
                p["insert_final"] = p["insert"]
                p["base_text"] = text
    # A10 结构核对: 每个文件里的块标记数必须等于"该文件已落地的文本补丁数"
    text_patches = [p for p in patches if p["kind"] in ("text", "glue")]
    for path in sorted(set(p["path"] for p in text_patches)):
        text = next(p["text"] for p in text_patches if p["path"] == path)
        # 注意: 只统计 kind=="text" 的已落地补丁 —— 粘连修复补丁 (P1R) 不引入新标记,
        #       把它算进来会把期望值抬高 1, 导致在健康树上误报"状态不自洽"(沙箱自测抓到)。
        n_applied = sum(1 for p in text_patches
                        if p["path"] == path and p["kind"] == "text" and p["state"] == "applied")
        n_mark = text.count(MARK)
        if n_mark != n_applied:
            raise PatchError("%s 块标记 `%s` 出现 %d 次, 但该文件已落地文本补丁 %d 个 —— 状态不自洽"
                             " (疑似手工改动或部分落地)" % (os.path.relpath(path, ROOT), MARK,
                                                     n_mark, n_applied))
        R.ok_("A10 标记自洽 %s" % os.path.basename(path),
              "块标记 %d 次 == 已落地文本补丁 %d 个" % (n_mark, n_applied))
    return patches


def check_insert_blocks(patches):
    """阶段二: 对每个待插入块做 配平 / 作用域 / 白名单 / 键名 断言。"""
    by_id = {p["id"]: p for p in patches}

    for pid in ("P1", "P2", "P3"):
        p = by_id[pid]
        if p["state"] != "pending":
            continue
        blk = p["insert"]
        d, mn, bad = brace_scan(blk)
        if d != 0 or mn < 0:
            R.fail_("A3 块配平 %s" % pid, "末深度=%d 最小深度=%d 行=%s" % (d, mn, bad[:5]))
        else:
            R.ok_("A3 块配平 %s" % pid, "末深度=0 最小深度=0 (%d 行)" % len(blk.split("\n")))
        issues = scope_audit(blk, pid)
        if issues:
            for it in issues:
                R.fail_("A4 作用域 %s" % pid, it)
        else:
            nv = len([l for l in blk.split("\n") if re.match(r"^\s*变量\s+\S", l)])
            R.ok_("A4 作用域 %s" % pid, "%d 条 变量 声明均位于块内相对深度 0" % nv)
        if pid == "P3":
            calls = re.findall(r"命令行\.([^\s(]+)\s*\(", blk)
            allow = set(ALLOWED_CMDLINE_CALLS) | set(ALLOWED_CMDLINE_READERS)
            bad_allowed = [c for c in calls if c not in allow]
            bad_forbid = [c for c in FORBIDDEN_CMDLINE_CALLS if ("命令行.%s" % c) in blk]
            if bad_allowed or bad_forbid:
                R.fail_("A6 白名单 P3", "越界调用=%s 禁止调用=%s" % (bad_allowed, bad_forbid))
            else:
                nw = [c for c in calls if c in ALLOWED_CMDLINE_CALLS]
                nr = sorted(set(c for c in calls if c in ALLOWED_CMDLINE_READERS))
                R.ok_("A6 白名单 P3", "%d 次调用全命中白名单: 施加 %d 次(%s) / 只读回执 %s"
                      % (len(calls), len(nw), ",".join(sorted(set(nw))), nr))
            main_text = by_id["P3"]["text"]
            free = [c for c in ("置值", "置项值", "置程序", "置额外参数", "插入值")
                    if ("命令行.%s" % c) in main_text]
            if free:
                R.fail_("A6 无自由文本口", "main.wsv 出现 命令行.%s" % free)
            else:
                R.ok_("A6 无自由文本口", "main.wsv 内 命令行.置值/置项值/置程序/置额外参数/插入值 = 0 次")
            if re.search(r"命令行\.\s*启用无头模式", main_text):
                R.fail_("A11 未接无头模式", "main.wsv 出现 命令行.启用无头模式 调用 (类库该方法体是自动播放的复制粘贴 Bug)")
            else:
                R.ok_("A11 未接无头模式", "main.wsv 内 命令行.启用无头模式 调用 = 0 次 (注释提及类库 Bug 不算接线)")
        if pid == "P2":
            keys = re.findall(r'配置解析\.取逻辑值 \("([^"]+)"\)', blk)
            if keys != CONFIG_KEYS:
                R.fail_("A7 P2 键名", "读到 %s (期望 %s)" % (keys, CONFIG_KEYS))
            else:
                R.ok_("A7 P2 键名", "6 个键逐一对应: " + ",".join(keys))
        if pid == "P1":
            dup = [cn for cn, _e, _t, _d, _c in NEW_VARS if ("变量 " + cn + " ") in p["text"]]
            dup_en = [en for _cn, en, _t, _d, _c in NEW_VARS if ('@输出名 = "%s"' % en) in p["text"]]
            if dup or dup_en:
                R.fail_("A5 变量名唯一", "改前已存在: 变量=%s 输出名=%s" % (dup, dup_en))
            else:
                R.ok_("A5 变量名唯一", "8 个新变量名与 8 个 @输出名 在改前文件中均为 0 次")


def check_json(patches):
    for p in patches:
        if p["kind"] != "json" or p["state"] != "pending":
            continue
        old = json.loads(p["text"])
        new = json.loads(p["new_text"])
        if set(new) - set(old) != set(p["keys"]):
            R.fail_("A8 JSON 新键", "新增键集合=%s" % sorted(set(new) - set(old)))
            continue
        if any(new[k] is not False for k in p["keys"]):
            R.fail_("A8 JSON 新键默认", "新键并非全 false")
            continue
        same = all(new[k] == v for k, v in old.items())
        if not same:
            R.fail_("A8 JSON 原文不变", "原有键值发生变化")
        else:
            R.ok_("A8 JSON 合法且原键不变", "新增 %d 键全 false, 原 %d 键逐一不变"
                  % (len(p["keys"]), len(old)))


def check_whole_files(patches, stage):
    """整文件花括号: 改前/改后(或当前) 末深度一致且为 0。"""
    for path in (MAIN, SERVER):
        p = next((x for x in patches if x["path"] == path), None)
        if p is None:
            continue
        before_d, before_mn, _ = brace_scan(p["text"])
        if stage == "pre":
            tgt = p["text"]
        else:
            tgt = p.get("final_text", p.get("new_text", p["text"]))
        d, mn, bad = brace_scan(tgt)
        tag = "A2 整文件配平 %s(%s)" % (os.path.basename(path), stage)
        if d != before_d or d != 0 or mn < 0:
            R.fail_(tag, "改前末深度=%d 最小=%d / 改后末深度=%d 最小=%d 转负行=%s"
                    % (before_d, before_mn, d, mn, bad[:5]))
        else:
            R.ok_(tag, "末深度 0 -> 0, 增量 0, 最小深度 >= 0")


# ================================================================ 施加 / 核对

def plan(patches):
    """把 pending 补丁算出 new_text, 并跑全部断言。

    ⚠ 同一文件上的多个补丁必须**链式**累计: P2 的新文本要建立在 P1 的新文本之上。
      否则 P2 会以"改前原文"为基准重写整个文件, 把 P1 刚插入的块静默抹掉
      (沙箱自测抓到的真实事故: 第二次写盘后 P1 的块消失, 而每个补丁的"写后复核"却各自自洽)。
    """
    for path in sorted(set(p["path"] for p in patches if p["kind"] in ("text", "glue"))):
        group = [p for p in patches if p["path"] == path and p["kind"] in ("text", "glue")]
        base = group[0]["text"]
        for p in group:
            if p["state"] != "pending":
                continue
            p["base_text"] = base
            if p["kind"] == "glue":
                p["new_text"] = base.replace(p["glued"], p["fixed"], 1)
                p["insert_final"] = ""
            else:
                ins = p["insert"].replace("\n", p["nl"]) if p["nl"] != "\n" else p["insert"]
                p["insert_final"] = ins
                if MARK in ins and ins.count(MARK) != 1:
                    raise PatchError("[%s] 插入块内标记 %s 出现 %d 次" % (p["id"], MARK, ins.count(MARK)))
                # A12: 插入块必须以换行开头 —— 否则块首行会粘在锚点行尾
                # (v1 早期版本的 P1 就是这么粘上去的, 已由 P1R 修复; 新补丁一律不许再犯)
                if not ins.startswith("\n"):
                    raise PatchError("[%s] 插入块未以换行开头, 会粘在锚点行尾 (insert=%r...)"
                                     % (p["id"], ins[:40]))
                if p["mode"] == "after":
                    p["new_text"] = base.replace(p["anchor"], p["anchor"] + ins, 1)
                else:
                    p["new_text"] = base.replace(p["anchor"], ins + p["anchor"], 1)
            if p["new_text"] == base:
                raise PatchError("[%s] 替换后文本无变化" % p["id"])
            base = p["new_text"]
        for p in group:
            p["final_text"] = base      # 该文件的最终形态(链式结果), 供整文件断言用
    check_insert_blocks(patches)
    check_glue(patches)
    check_json(patches)
    check_whole_files(patches, "post")
    return [p for p in patches if p["state"] == "pending"]


def check_glue(patches):
    """A12 二次核对: 修复后不得再有"声明行尾挂 # 注释"的粘连形态。"""
    for p in patches:
        if p["kind"] == "glue" and p["state"] == "pending":
            tgt = p["new_text"]
            bad = [i + 1 for i, l in enumerate(tgt.split("\n"))
                   if ("@输出名" in l and "#" in l) or (l.count("启动期开关通道v1") and l.count("@输出名"))]
            if p["new_text"].count(p["fixed"]) != 1 or p["new_text"].count(p["glued"]) != 0:
                R.fail_("A12 粘连修复", "修复后 健康形态=%d 粘连形态=%d (期望 1 / 0)"
                        % (p["new_text"].count(p["fixed"]), p["new_text"].count(p["glued"])))
            elif bad:
                R.fail_("A12 粘连修复", "仍有声明行尾挂注释的行: %s" % bad[:5])
            elif p["new_text"].count(MARK) != p["text"].count(MARK):
                R.fail_("A12 粘连修复", "块标记数变化 %d -> %d"
                        % (p["text"].count(MARK), p["new_text"].count(MARK)))
            else:
                R.ok_("A12 粘连修复", "锚点行尾的粘连块首行断开为新行; 块标记数不变; 无声明尾部挂注释")


def backup_name(path, primary_paths):
    """备份文件名: 主目标用基名; 配置镜像带上其父目录, 避免同名互撞。"""
    base = os.path.basename(path)
    if path in primary_paths:
        return base
    rel = os.path.relpath(os.path.dirname(path), ROOT)
    tag = re.sub(r"[^0-9A-Za-z_.-]+", "_", rel) or "root"
    return "%s@%s" % (base, tag)


def backup(items):
    """items: [(path, backup_name)]。已存在的备份不覆盖; 内容不同则另存时间戳副本。"""
    made = []
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for path, name in items:
        dst = os.path.join(BACKUP_DIR, name)
        cur = open(path, "rb").read()
        if os.path.exists(dst):
            old = open(dst, "rb").read()
            if old == cur:
                made.append((dst, "已存在且与现文件一致, 未覆盖"))
                continue
            alt = os.path.join(BACKUP_DIR, "%s.%s.bak" % (name, stamp))
            open(alt, "wb").write(cur)
            made.append((dst, "已存在但与现文件不同 -> 另存 %s, 未覆盖原备份" % os.path.basename(alt)))
            continue
        shutil.copy2(path, dst)
        made.append((dst, "新建"))
    return made


def apply_all(patches, pending):
    print("\n" + "=" * 100)
    print("阶段 6: 写前备份 -> 落盘 -> 写后复核")
    print("=" * 100)
    files = []
    for p in pending:
        if p["path"] not in [x for x, _n in files]:
            files.append((p["path"], os.path.basename(p["path"])))
    prim0 = next((p for p in patches if p["kind"] == "json"), None)
    if prim0 is not None and prim0["state"] == "pending":
        for mirror in CONFIG_MIRRORS:
            if os.path.exists(mirror) and mirror not in [x for x, _n in files]:
                files.append((mirror, backup_name(mirror, [prim0["path"]])))
    for dst, note in backup(files):
        print("  备份: %-60s %s" % (os.path.relpath(dst, ROOT), note))

    for p in pending:
        old_len = len(open(p["path"], "rb").read())
        new_len = write_text(p["path"], p["new_text"], p["enc"], p["bom"], p["nl"])
        back, enc, bom, nl = read_text(p["path"])
        tag = "A9 写后复核 %s %s" % (p["id"], os.path.basename(p["path"]))
        if back != p["new_text"]:
            R.fail_(tag, "读回文本与预期不符")
            continue
        if (enc, bom, nl) != (p["enc"], p["bom"], p["nl"]):
            R.fail_(tag, "编码/行尾漂移: %s%s/%r -> %s%s/%r"
                    % (p["enc"], "+BOM" if p["bom"] else "", p["nl"],
                       enc, "+BOM" if bom else "", nl))
            continue
        delta_mark = back.count(MARK) - p["base_text"].count(MARK)
        exp_delta_mark = 1 if (p["kind"] == "text" and MARK in p["insert_final"]) else 0
        if delta_mark != exp_delta_mark:
            R.fail_(tag, "块标记增量 = %d (期望 %d)" % (delta_mark, exp_delta_mark))
            continue
        restored = back
        if p["kind"] == "text":
            restored = back.replace(p["insert_final"], "", 1)
        elif p["kind"] == "glue":
            restored = back.replace(p["fixed"], p["glued"], 1)
        if p["kind"] in ("text", "glue") and restored != p["base_text"]:
            R.fail_(tag, "反注入还原 != 该补丁的施加基准文本 (差异不止插入块)")
            continue
        R.ok_(tag, "编码/行尾不变; 字节 %d -> %d; 差异恰为插入块" % (old_len, new_len))

    # 配置镜像副本: 同内容则一并加键, 保证运行中的 exe 目录也能读到
    prim = next((p for p in patches if p["kind"] == "json"), None)
    if prim is not None and prim["state"] == "pending":
        for mirror in CONFIG_MIRRORS:
            if not os.path.exists(mirror):
                continue
            text, enc, bom, nl = read_text(mirror)
            if text == prim["text"]:
                new_text, _ = json_plan(text)
                write_text(mirror, new_text, enc, bom, nl)
                print("  镜像同步: %-58s 已加入 6 键" % os.path.relpath(mirror, ROOT))
            elif text == prim["new_text"]:
                print("  镜像同步: %-58s 已是新内容, 跳过" % os.path.relpath(mirror, ROOT))
            else:
                R.warn_("配置镜像不一致", "%s 与根 mcp_config.json 内容不同, 未改动"
                        % os.path.relpath(mirror, ROOT))


def verify_only(patches):
    print("\n" + "=" * 100)
    print("只读核对 (--verify-only): 检查已落地结果, 不写任何文件")
    print("=" * 100)
    for p in patches:
        path = p["path"]
        rel = os.path.relpath(path, ROOT)
        if p["kind"] == "glue":
            if p["state"] == "healthy":
                R.ok_("V %s 无粘连" % p["id"], "%s 锚点行尾未粘连块首行 (健康形态 1 次)" % rel)
            elif p["state"] == "pending":
                R.fail_("V %s 需修复" % p["id"],
                        "%s 存在 P1 落地粘连(块首行粘在锚点行尾, 少一个换行): 运行 `py -3 "
                        "_audit/_apply_startup_switches.py` 可**就地修复**, 或先从 "
                        "备份\\启动开关通道-写入前\\ 还原该文件再整体重跑" % rel)
                dump_context(path, p["hints"])
            else:
                R.ok_("V %s 不适用" % p["id"], "%s 无粘连形态 (P1 尚未落地)" % rel)
            continue
        if p["kind"] == "json":
            keys = [k for k in p["keys"] if ('"%s"' % k) in p["text"]]
            if len(keys) == len(p["keys"]):
                R.ok_("V %s 配置键" % p["id"], "%s 已含 6 键" % rel)
            else:
                R.fail_("V %s 配置键" % p["id"], "%s 缺少 %s" % (rel, sorted(set(p["keys"]) - set(keys))))
            continue
        n_sig = p["text"].count(p["sig"])
        n_mark = p["text"].count(MARK)
        if n_sig == 1:
            R.ok_("V %s 已落地" % p["id"], "%s 签名 1 次 (第 %d 行附近), 块标记 %d 次"
                  % (rel, lineno_of(p["text"], p["sig"]), n_mark))
        elif n_sig == 0:
            R.fail_("V %s 未落地" % p["id"], "%s 找不到签名 `%s`" % (rel, p["sig"][:40]))
            dump_context(path, p["hints"])
        else:
            R.fail_("V %s 重复" % p["id"], "%s 签名 %d 次" % (rel, n_sig))
    # 结构一致性
    server_text = next(p["text"] for p in patches if p["path"] == SERVER)
    main_text = next(p["text"] for p in patches if p["path"] == MAIN)
    for cn, en, _t, _d, _c in NEW_VARS:
        n = server_text.count("变量 " + cn + " ")
        if n != 1:
            R.fail_("V 变量 %s" % cn, "MCP_Server.wsv 中声明 %d 次 (要求 1)" % n)
        if server_text.count('@输出名 = "%s"' % en) != 1:
            R.fail_("V 输出名 %s" % en, "命中 != 1")
    if not R.fail:
        R.ok_("V 8 个字段", "8 个变量名与 8 个 @输出名 在 MCP_Server.wsv 中各恰好 1 次")
    n_mon = main_text.count('记录应用监控事件 ("app_startup_cmdline"')
    if n_mon == 1:
        R.ok_("V 既有监控块保留", "app_startup_cmdline 记录仍在 (1 次)")
    else:
        R.fail_("V 既有监控块", "app_startup_cmdline 记录 %d 次 (要求 1)" % n_mon)
    if re.search(r"命令行\.\s*启用无头模式", main_text):
        R.fail_("V 无头模式未接", "main.wsv 出现 命令行.启用无头模式 调用")
    else:
        R.ok_("V 无头模式未接", "main.wsv 内 命令行.启用无头模式 调用 = 0 次 (门控注释虽提到该 Bug, 但未接线)")
    if "FBrowser初始化控制.是否为VIP = 真" in main_text:
        R.ok_("V VIP 前提保持", "FBrowser初始化控制.是否为VIP = 真 (本补丁不改它)")
    else:
        R.warn_("V VIP 前提", "未在 main.wsv 找到 `FBrowser初始化控制.是否为VIP = 真` —— 开关是否生效取决于该前提")
    check_whole_files(patches, "pre")


# ================================================================ 预览

def preview(patches, pending):
    print("\n" + "=" * 100)
    print("预览 (待插入内容)")
    print("=" * 100)
    for p in patches:
        rel = os.path.relpath(p["path"], ROOT)
        if p["state"] == "applied":
            print("\n--- [%s] %s : 已落地, 跳过 (%s)" % (p["id"], rel, p["doc"]))
            continue
        if p not in pending:
            continue
        print("\n--- [%s] %s : %s" % (p["id"], rel, p["doc"]))
        if p["kind"] == "glue":
            print("    修复前(粘连, 块首行粘在锚点行尾):")
            print("      - %s" % p["glued"][-120:])
            print("    修复后(块首行独立成行):")
            print("      + %s" % p["fixed"][-120:].replace("\n", "\n      + "))
            print("    改后行数: %d -> %d" % (len(p["base_text"].split("\n")), len(p["new_text"].split("\n"))))
            continue
        if p["kind"] == "text":
            print("    锚点(命中 1 次, 现第 %d 行):" % lineno_of(p["text"], p["anchor"]))
            for l in p["anchor"].split("\n"):
                print("      | %s" % l)
            print("    插入 (%d 行, 位置: %s):" % (len(p["insert_final"].rstrip("\n").split("\n")),
                                                "锚点之后" if p["mode"] == "after" else "锚点之前"))
            for l in p["insert_final"].rstrip("\n").split("\n"):
                print("      + %s" % l)
        else:
            print("    插入 %d 个键 (%s):" % (len(p["keys"]), ", ".join(p["keys"])))
            for l in p["insert"].split(p["nl"]):
                print("      + %s" % l)
        print("    改后行数: %d -> %d" % (len(p["base_text"].split("\n")), len(p["new_text"].split("\n"))))


# ================================================================ main

def main():
    ap = argparse.ArgumentParser(description="启动期 Chromium 开关通道 (v1) 补丁施加脚本")
    ap.add_argument("--dry-run", action="store_true", help="只校验 + 预览, 不写任何文件")
    ap.add_argument("--verify-only", action="store_true", help="只读核对已落地结果")
    args = ap.parse_args()
    if args.dry_run and args.verify_only:
        print("--dry-run 与 --verify-only 不能同时使用")
        return 2
    mode = "VERIFY-ONLY" if args.verify_only else ("DRY-RUN" if args.dry_run else "APPLY")
    print("=" * 100)
    print("启动期 Chromium 开关通道 (v1) —— MODE = %s" % mode)
    print("项目根: %s" % ROOT)
    print("备份目录: %s" % os.path.relpath(BACKUP_DIR, ROOT))
    print("=" * 100)

    patches = build_patches()
    resolve(patches)                      # 阶段一: 锚点定位 (失败即抛, 已读文件, 未写)
    print("\n阶段 1: 锚点定位 (只用原文锚点, 无行号)")
    for p in patches:
        rel = os.path.relpath(p["path"], ROOT)
        if p["kind"] == "json":
            print("  [OK]   %-3s %-26s %-16s 配置键: %s" % (p["id"], rel, p["_enc_desc"],
                                                        "已存在" if p["state"] == "applied" else "待写入"))
        elif p["kind"] == "glue":
            if p["state"] == "pending":
                R.ok_("A1 粘连修复 %s" % p["id"], "%s 粘连形态恰好 1 次 (锚点行第 %d 行), 待就地修复"
                      % (rel, lineno_of(p["text"], p["glued"])))
            else:
                R.ok_("%s %s" % ("A10 已健康" if p["state"] == "healthy" else "A10 无需修复", p["id"]),
                      "%s 无粘连形态 (P1 %s)"
                      % (rel, "已正确落地" if p["state"] == "healthy" else "尚未落地"))
        elif p["state"] == "pending":
            R.ok_("A1 锚点 %s" % p["id"], "%s 锚点恰好 1 次 (现第 %d 行), 编码/行尾 %s"
                  % (rel, lineno_of(p["text"], p["anchor"]), p["_enc_desc"]))
        else:
            R.ok_("A10 已落地 %s" % p["id"], "%s 签名 1 次, 跳过重复插入" % rel)

    if args.verify_only:
        verify_only(patches)
        print("\n" + "=" * 100)
        print("核对结果: OK=%d WARN=%d FAIL=%d" % (len(R.ok), len(R.warn), len(R.fail)))
        for f in R.fail:
            print("  FAIL: %s" % f)
        print("提示: 落地后仍需主代理串行执行 (1) 火山编译 (2) 真机重启验证 (3) 检查启动日志")
        print("      `[AI浏览器] 启动期命令行开关已应用: ...` 与 静态字段 命令行开关原文")
        print("=" * 100)
        return 1 if R.fail else 0

    print("\n阶段 2-4: 块配平 / 作用域 / 白名单 / 键名 / 整文件配平 断言")
    pending = plan(patches)

    if not pending:
        print("\n所有补丁均已落地, 无需改动 (幂等)。")
        print("结果: OK=%d WARN=%d FAIL=%d" % (len(R.ok), len(R.warn), len(R.fail)))
        return 1 if R.fail else 0

    preview(patches, pending)

    if args.dry_run:
        print("\n" + "=" * 100)
        print("DRY-RUN 结束: 未写任何文件 (含未创建备份目录)。")
        print("结果: OK=%d WARN=%d FAIL=%d" % (len(R.ok), len(R.warn), len(R.fail)))
        for f in R.fail:
            print("  FAIL: %s" % f)
        print("=" * 100)
        return 1 if R.fail else 0

    if R.fail:
        print("\n存在 FAIL 断言, 拒绝落盘。")
        for f in R.fail:
            print("  FAIL: %s" % f)
        return 1

    apply_all(patches, pending)

    print("\n" + "=" * 100)
    print("结果: OK=%d WARN=%d FAIL=%d" % (len(R.ok), len(R.warn), len(R.fail)))
    for f in R.fail:
        print("  FAIL: %s" % f)
    if not R.fail:
        print("落盘完成。下一步(主代理串行执行, 本脚本不代劳):")
        print("  1) 编译: 火山编译器 (本脚本未编译, 语法是否通过未知)")
        print("  2) 重启程序, 抓 stdout, 确认出现一行: [AI浏览器] 启动期命令行开关已应用: <清单> (仅当有开关为真)")
        print("     并把启动日志里 控制台输出 的原文与 命令行开关原文 记进台账; 全假时该行不出现 = 符合预期")
        print("  3) 逐个翻转 mcp_config.json 的键做真机对照 (一次只翻一个): ")
        print("     disable_gpu -> 观察渲染是否退化为 CPU 渲染; ignore_gpu_blocklist/disable_gpu_cache 同理需可判别观测")
        print("     enable_media_stream/enable_speech_input/enable_autoplay -> 需页面侧 getuserMedia/自动播放对照")
        print("  4) 注意: 运行中 exe 读的是输出目录 mcp_config.json (linker 副本), 本脚本已尽力同步已有副本")
        print("  5) 未完成的文档: mcp_config.README.md 的字段简表未加这 6 个键 (本脚本不改文档)")
    print("=" * 100)
    return 1 if R.fail else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:
        print("\n" + "!" * 100)
        print("异常中止 —— traceback 全文如下 (未写任何文件; 若已进入落盘阶段则仅可能部分文件已写):")
        print("!" * 100)
        print(traceback.format_exc())
        print("-" * 100)
        print("相关文件片段:")
        for path, hints in ((MAIN, ['方法 即将处理命令行', 'app_startup_cmdline', '是否监控启动流程']),
                            (SERVER, ['变量 是否自动关闭JS对话框', 'auto_dismiss_js_dialog',
                                      '应用默认事件监控 ()', '配置已加载 = 真']),
                            (CONFIG, ['"window_topmost"'])):
            print("  · %s" % os.path.relpath(path, ROOT))
            dump_context(path, hints, before=4, after=4, limit=2)
        print("-" * 100)
        print("结果: OK=%d WARN=%d FAIL=%d" % (len(R.ok), len(R.warn), len(R.fail)))
        sys.exit(2)
