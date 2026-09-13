# -*- coding: utf-8 -*-
"""_apply_codec_patch.py — 落地 `browser_codec` 与 `browser_time_convert` 两个 action 制工具。

对应计划：`_audit/_codec_plan_r115.md`（r115 零前置编解码工具计划）。
本脚本只做**文本精确插桩**，不编译、不调用 MCP、不重启程序。

────────────────────────────────────────────────────────────────────────
一、改哪些文件、各插几处
────────────────────────────────────────────────────────────────────────
1) `src/MCP_Server.wsv`  —— 2 处插入
   a. 方法 `构建命令注册表`（`        // v1.6 新增` 之前）内、
      锚点行 `命令注册表.置整数值 ("browser_uri_decode", 643)` 之后插入 **4 行**：
        命令注册表.置整数值 ("browser.codec", <ID1>)
        命令注册表.置整数值 ("browser_codec", <ID1>)
        命令注册表.置整数值 ("browser.time_convert", <ID2>)
        命令注册表.置整数值 ("browser_time_convert", <ID2>)
   b. 方法 `填充工具列表` 内、锚点行 `添加工具JSON ("browser_uri_decode", ` 之后插入 **2 行**
      （两条 `添加工具JSON (...)` 工具登记，含完整 inputSchema）。
      注：锚点用**子串定位 + 在"该行行尾之后"插入**，不复制/改写锚点行本身
      —— 因为 `MCP_Server.wsv` 正被并发编辑，且任务点名 `browser_collect` 的描述行正在改。

2) `src/MCP_Server_Core.wsv` —— 1 处插入
   方法 `分类分派_核心操作` 内，在锚点行
        `        // === 触摸事件 (CDP 派发优先; 内核注入为显式 opt-in) ===`
   **之前**插入 **1 个代码块（含 2 个分派分支）**：`否则 (方法名 == "browser_codec") { ... }`
   与 `否则 (方法名 == "browser_time_convert") { ... }`。

   为什么放这里：`MCP_Server.wsv` 的 `处理_工具调用` 是"前缀直投 + 兜底核心分派"路由
   （前缀：browser_fill_ / browser_vip_ / browser_fingerprint_ / browser_font_ / workflow /
   browser_reverse_ / browser_kernel_ / 一组系统命令；**其余一律落到 `MCP_核心分派.分类分派_核心操作`**）。
   `browser_codec` / `browser_time_convert` 不匹配任何前缀 → 必然进入核心分派，
   与既有 `browser_base64_encode` / `browser_uri_decode` 同一个分派器，零额外路由改动。
   入口处有 `子文本替换 (方法名, "browser.", "browser_", , , 假)`，故双变体名都能命中本分支。

────────────────────────────────────────────────────────────────────────
二、新 ID
────────────────────────────────────────────────────────────────────────
脚本自己扫 `命令注册表.置整数值 ("...", N)` 的全部 N 取 max，新 ID = max+1 / max+2，
并在输出里打印实际用了哪两个号；同时断言这两个号在改动前**未被占用**。

────────────────────────────────────────────────────────────────────────
三、断言了什么（全部通过才写文件；先全部校验、再统一写）
────────────────────────────────────────────────────────────────────────
A. 定位：3 个锚点各自在目标文件中**恰好命中 1 行**；否则抛异常、**不写任何文件**。
B. 幂等：`browser_codec` / `browser_time_convert` / `browser.codec` / `browser.time_convert`
   在改动前**不得已存在**；否则判定"已打过补丁"，直接中止（保护并发编辑中的文件）。
C. 格式：目标文件必须是 **UTF-8 无 BOM、纯 LF（不得出现 `\\r`）**；否则中止。
D. 引号：每一插入行的"去掉 `\\"` 后的 `"` 计数必须为偶数"（防生成非法 .wsv 字符串）。
D2. 风格：插入行缩进必须是 4 空格倍数、不含 Tab / 行尾空白 / 空行。
D3. 作用域：**块内（花括号深度 > 0）声明的变量若在更浅深度被引用即中止**。
   —— 该检查在本脚本开发过程中**实际抓到过一个真 bug**（`codec实际字节数` 曾在 hex 子块内声明、
   却在子块外的回包处引用，火山会编译不过），已修正为在分支顶层声明。
D4. 令牌白名单：剥掉字符串字面量与 `//` 注释后，插入块里每个 `NAME (` 形式的被调用名
   必须命中 `ALLOWED_CALLS`（59 项，全部在 `_codec_plan_r115.md` 有原文出处），
   否则中止 —— 用来抓方法名拼写错误（例：把 `时间戳到时间` 写成别的）。
E. 花括号：每个文件改动前后 **balance(开 − 闭) 完全一致**，且插入块自身 balance == 0。
F. 自检：改动后的文本里
   `添加工具JSON ("browser_codec"` 恰好 1 次、`否则 (方法名 == "browser_codec")` 恰好 1 次；
   `browser_time_convert` 同理（登记 1 次 + 分派 1 次）；双变体注册各 1 次。
G. 备份：写文件前 `备份/编解码工具-写入前/<文件名>`（已存在则不覆盖）。
H. 写前复核：写每个文件之前**重新读一遍**，sha256 与校验阶段不一致即中止（并发编辑竞态的最后一道闸）。

────────────────────────────────────────────────────────────────────────
四、我**没有**验证什么（重要，别把本脚本当成已验证）
────────────────────────────────────────────────────────────────────────
* 未编译：火山语法正确性、类型匹配、方法重载解析**一律未验证**（本机无 voldev，且禁止编译）。
* 未运行：两个工具的**运行期行为**、返回值、异常路径全部未实测 —— 真机验收请按
  `_codec_plan_r115.md` §3 的 A/B/C 三张表逐条执行。
* 未确认的类库行为（原文未载明，工具层已做守卫/归一化，但**类库裸行为未知**）：
  `CVolMem::ToHexStr` 输出大小写、`CVolMem::sFromHexStr` 对奇数长度/非 hex/小写的处理、
  `多字节到文本` 对非法 GBK 字节的替换行为。
* 未确认 `删全部空`（`w_string_p.wsv:817`）与 `到大写`（`:775`）在本项目里**从未被调用过**
  （项目只用过它们的同类 `到小写`）。二者都在在册模块 `视窗基本类` 内、签名明确，
  但"本机从未跑过"这一点属实，属残余风险。
* 未确认 `/` 的整数除法在**长整数场景**下的取整方向（只在整数场景有项目内先例）。
* 未做 `data.*` 之外的回包字段路径确认：`命令成功_原始JSON` 会把内容包在 `"data"` 下
  （`MCP_ResponseBuilders.wsv:181-187` 的 `构建带数据字段JSON`），故字段路径是
  `data.timestamp_s` / `data.output` 等，**不是**顶层。
* 未提供 `utc` 字段：需要"小数天"运算（`(小数)`强转在本项目零先例），为不引入未验证写法而省略；
  这是相对 `_codec_plan_r115.md` §2.3 示例 JSON 的**已知偏差**。
* 未处理并发编辑的竞态：脚本"先校验后写"之间若文件被别的进程改动，`write` 前会做一次
  "锚点仍在 + 内容指纹未变"复核（同一进程内读到的内容会被重新读一遍比对），
  但两次读之间仍有理论窗口。

用法：
    py -3 _audit\\_apply_codec_patch.py --dry-run     # 只校验 + 预览，不写任何文件
    py -3 _audit\\_apply_codec_patch.py               # 校验通过后写文件（先备份）
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
import traceback

# ───────────────────────── 路径 ─────────────────────────

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'src')
BACKUP_DIR = os.path.join(ROOT, '备份', '编解码工具-写入前')

SERVER = 'MCP_Server.wsv'
CORE = 'MCP_Server_Core.wsv'

# ───────────────────────── 锚点（原文子串，绝不用行号） ─────────────────────────

ANCHOR_REGISTRY = '命令注册表.置整数值 ("browser_uri_decode", 643)'
ANCHOR_TOOLLIST = '添加工具JSON ("browser_uri_decode", '
ANCHOR_DISPATCH = '// === 触摸事件 (CDP 派发优先; 内核注入为显式 opt-in) ==='

# 期望锚点所在的方法（只用于报错时定位，不参与定位）
ANCHOR_METHOD = {
    ANCHOR_REGISTRY: '方法 构建命令注册表',
    ANCHOR_TOOLLIST: '方法 填充工具列表',
    ANCHOR_DISPATCH: '方法 分类分派_核心操作',
}

NEW_TOOLS = ['browser_codec', 'browser_time_convert']

# ───────────────────────── 插入内容 ─────────────────────────

REG_BLOCK_TEMPLATE = '''        命令注册表.置整数值 ("browser.codec", {id1})
        命令注册表.置整数值 ("browser_codec", {id1})
        命令注册表.置整数值 ("browser.time_convert", {id2})
        命令注册表.置整数值 ("browser_time_convert", {id2})'''

TOOL_BLOCK = r'''        添加工具JSON ("browser_codec", "零前置编解码(hex / UTF-8 / GBK多字节)。全部走【视窗基本类】已有函数, 无新模块、无新二进制。action: hex_encode(文本或base64字节 到 hex) / hex_decode(hex 到 文本或hex/base64) / utf8_encode(文本 到 UTF-8字节) / utf8_decode(UTF-8字节 到 文本) / gbk_encode(文本 到 GBK字节) / gbk_decode(GBK字节 到 文本, 中国站GBK响应体专治)。input=text|hex|base64 决定 data 怎么读(encode 方向一律按文本读, 字符集由 action 决定); output=hex|text|base64 决定结果怎么给(encode 默认 hex, decode 默认 text); uppercase(默认false)控制 hex 大小写; allow_spaces(默认true)允许 hex 里带空格/换行。工具层已做确定性处理: 内部固定传【假】给 文本到UTF8/文本到多字节 的第二参(其默认为真会在尾部多一个零字节)、hex 输入先校验偶数长度与合法字符并归一化成大写、解码后回验字节数。文本出口按类库的C字符串语义构造, 遇内嵌0x00会截断 —— 含NUL的二进制请用 output=hex|base64。", 多属性Schema文本 (属性项JSON ("action", "text", "hex_encode/hex_decode/utf8_encode/utf8_decode/gbk_encode/gbk_decode") + "," + 属性项JSON ("data", "text", "要处理的数据(文本, 或 input 指定的 hex/base64)") + "," + 属性项JSON ("input", "text", "data怎么读: text(默认) / hex / base64") + "," + 属性项JSON ("output", "text", "结果怎么给: encode默认hex, decode默认text; 可选 text/hex/base64") + "," + 属性项JSON ("uppercase", "boolean", "hex 输出是否大写(默认false=小写)") + "," + 属性项JSON ("allow_spaces", "boolean", "hex 输入是否允许空格与换行(默认true)"), "\"action\",\"data\""))
        添加工具JSON ("browser_time_convert", "时间戳换算与格式化(零前置, 走【视窗基本类】时间操作类)。action: now(当前时间) / ts_to_text(时间戳到时间) / text_to_ts(时间文本到时间戳) / verify_tz(时区自检锚点: 指定时间(1970,1,1,8,0,0) 的秒级时间戳在本机UTC+8下必须为 0)。action 可省略, 按已给参数自动选(timestamp则ts_to_text, time_text则text_to_ts, 都没给则now), 以免空参调用必然失败。unit=s|ms 指定秒或毫秒; format 为类库格式串(默认 %Y-%m-%d %H:%M:%S, 请避免 %a %A %b %B %c %p %x %X 这些随系统区域设置变化的替换符); chinese(默认true)指定时间文本是年月日顺序还是月日年顺序。返回 data.timestamp_s / data.timestamp_ms / data.local / data.friendly / data.tz_offset_minutes / data.ole / data.year。语义说明: 秒级/毫秒级时间戳都是【真 UTC】值(类库按当前时区 Bias 补偿, UTC+8 时 Bias=-480); local 按机器本地时区渲染; friendly 来自 时间到文本, 会省略为0的时分秒(午夜退化成日期), 故只作人读字段。上限: 秒级 2147483647(=2038-01-19 03:14:07Z), 越界会明确报错并指向 unit=ms(类库 取时间戳 返回 32 位整数)。", 多属性Schema文本 (属性项JSON ("action", "text", "now/ts_to_text/text_to_ts/verify_tz (可省略, 按已给参数自动选)") + "," + 属性项JSON ("timestamp", "integer", "UNIX 时间戳(秒或毫秒, 由 unit 决定)") + "," + 属性项JSON ("unit", "text", "s(秒, 默认) / ms(毫秒)") + "," + 属性项JSON ("time_text", "text", "时间文本, 例: 1973年11月15日12时30分25秒 或 1970-01-01 08:00:00") + "," + 属性项JSON ("format", "text", "格式化串(默认 %Y-%m-%d %H:%M:%S)") + "," + 属性项JSON ("chinese", "boolean", "time_text 是否年月日顺序(默认true)"), "\"action\""))'''

DISPATCH_BLOCK = r'''        // === 零前置编解码: hex / UTF-8 / GBK多字节 (全部走 视窗基本类 已有函数, 零新模块) ===
        // 陷阱1: 文本到UTF8 / 文本到多字节 的第二参"是否包括结束零字符"【默认为真】, 会在结果尾部多一个零字节,
        //        本分支一律显式传 假 (项目既有调用点亦如此), 并把这一点写进工具描述。
        // 陷阱2: 类库对 hex 输出的【大小写】、sFromHexStr 对奇数长度与非hex字符的行为, 原文均未载明,
        //        故本分支自己做: 偶数长度校验 + 逐字符合法性校验 + 统一归一化成大写送库 + 回验字节数 + 按 uppercase 归一化输出。
        // 陷阱3: UTF8到文本 / 多字节到文本 按 C 字符串构造(遇内嵌 0x00 截断); 工具描述里如实声明, 二进制出口走 hex/base64。
        否则 (方法名 == "browser_codec")
        {
            变量 codec动作 <类型 = 文本型>
            codec动作 = ""
            如果 (MCP命令服务器.参数键存在 (参数JSON, "action"))
            {
                codec动作 = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            }
            如果 (codec动作 != "hex_encode" && codec动作 != "hex_decode" && codec动作 != "utf8_encode" && codec动作 != "utf8_decode" && codec动作 != "gbk_encode" && codec动作 != "gbk_decode")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "action 必填且只能是: hex_encode | hex_decode | utf8_encode | utf8_decode | gbk_encode | gbk_decode | 实际: " + codec动作))
            }
            变量 codec数据 <类型 = 文本型>
            codec数据 = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (codec数据 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数))
            }
            变量 codec输入 <类型 = 文本型>
            codec输入 = "text"
            如果 (MCP命令服务器.参数键存在 (参数JSON, "input"))
            {
                codec输入 = MCP命令服务器.yyjson取文本 (参数JSON, "input")
            }
            变量 codec输出 <类型 = 文本型>
            codec输出 = ""
            如果 (MCP命令服务器.参数键存在 (参数JSON, "output"))
            {
                codec输出 = MCP命令服务器.yyjson取文本 (参数JSON, "output")
            }
            变量 codec大写 <类型 = 逻辑型>
            codec大写 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "uppercase", 假)
            变量 codec允许空格 <类型 = 逻辑型>
            codec允许空格 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "allow_spaces", 真)
            变量 codec是编码 <类型 = 逻辑型>
            codec是编码 = 假
            如果 (codec动作 == "hex_encode" || codec动作 == "utf8_encode" || codec动作 == "gbk_encode")
            {
                codec是编码 = 真
            }
            变量 codec是GBK <类型 = 逻辑型>
            codec是GBK = 假
            如果 (codec动作 == "gbk_encode" || codec动作 == "gbk_decode")
            {
                codec是GBK = 真
            }
            变量 codec字节 <类型 = 字节集类>
            变量 codec实际字节数 <类型 = 整数>
            codec实际字节数 = 0
            如果 (codec是编码)
            {
                // 编码方向: data 一律按文本理解, 目标字符集由 action 决定
                如果 (codec是GBK)
                {
                    codec字节 = 文本到多字节 (codec数据, 假)
                }
                否则
                {
                    codec字节 = 文本到UTF8 (codec数据, 假)
                }
            }
            否则
            {
                // 解码方向: data 是"字节的文本表示", 必须显式给 input
                如果 (codec输入 == "hex")
                {
                    变量 codec清洗 <类型 = 文本型>
                    codec清洗 = 删全部空 (codec数据)
                    如果 (codec允许空格 == 假 && codec清洗 != codec数据)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "hex 输入含空白字符(空格/Tab/换行), 但 allow_spaces=false; 如需忽略空白请传 allow_spaces=true"))
                    }
                    变量 codec位数 <类型 = 整数>
                    codec位数 = 取文本长度 (codec清洗)
                    如果 (codec位数 == 0)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "hex 输入为空(去掉空白后没有任何字符)"))
                    }
                    如果 (codec位数 % 2 != 0)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "hex 长度必须为偶数(每字节两位十六进制), 实际 " + 到文本 (codec位数) + " 位 | 类库对奇数长度的行为未载明, 故工具层直接拒绝而非猜测"))
                    }
                    变量 codec上表 <类型 = 文本型>
                    codec上表 = "0123456789ABCDEF"
                    变量 codec下表 <类型 = 文本型>
                    codec下表 = "0123456789abcdef"
                    变量 codec规范 <类型 = 文本型>
                    codec规范 = ""
                    变量 codec非法 <类型 = 文本型>
                    codec非法 = ""
                    变量 codec位 <类型 = 整数>
                    codec位 = 0
                    变量 codec单元 <类型 = 文本型>
                    codec单元 = ""
                    变量 codec命中 <类型 = 整数>
                    codec命中 = 0
                    判断循环 (codec位 < codec位数)
                    {
                        codec单元 = 取文本中间 (codec清洗, codec位, 1)
                        codec命中 = 寻找文本 (codec上表, codec单元, 0, 假)
                        如果 (codec命中 >= 0)
                        {
                            codec规范 = codec规范 + 取文本中间 (codec上表, codec命中, 1)
                        }
                        否则
                        {
                            codec命中 = 寻找文本 (codec下表, codec单元, 0, 假)
                            如果 (codec命中 >= 0)
                            {
                                codec规范 = codec规范 + 取文本中间 (codec上表, codec命中, 1)
                            }
                            否则
                            {
                                codec非法 = codec单元
                                跳出循环
                            }
                        }
                        codec位 = codec位 + 1
                    }
                    如果 (codec非法 != "")
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "hex 输入含非法字符: " + codec非法 + " (位置 " + 到文本 (codec位) + ", 0起) | 只接受 0-9 与 A-F/a-f(可带空格与换行)"))
                    }
                    codec字节 = 十六进制文本到字节集 (codec规范)
                    codec实际字节数 = 取字节集长度 (codec字节)
                    变量 codec期望字节数 <类型 = 整数>
                    codec期望字节数 = codec位数 / 2
                    如果 (codec实际字节数 != codec期望字节数)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "hex 解码字节数异常: 期望 " + 到文本 (codec期望字节数) + " 字节, 实际 " + 到文本 (codec实际字节数) + " 字节 | 类库 CVolMem::sFromHexStr 对异常输入的行为未载明, 原样上报以便实测判定"))
                    }
                }
                否则 (codec输入 == "base64")
                {
                    变量 codecB64 <类型 = 类_FBrowser_字节集>
                    codecB64 = FBrowser_Parser_Base64解码 (codec数据)
                    如果 (codecB64.是否为空 ())
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "base64 解码失败: 输入不是合法 base64 文本"))
                    }
                    codec字节 = codecB64.取字节集 ()
                }
                否则 (codec输入 == "text")
                {
                    // 文本入: 按 action 的字符集取字节(便于"文本到另一种编码的字节"直接自检)
                    如果 (codec是GBK)
                    {
                        codec字节 = 文本到多字节 (codec数据, 假)
                    }
                    否则
                    {
                        codec字节 = 文本到UTF8 (codec数据, 假)
                    }
                }
                否则
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "input 只能是 text | hex | base64, 实际: " + codec输入))
                }
            }
            变量 codec结果 <类型 = 文本型>
            codec结果 = ""
            变量 codec结果hex <类型 = 文本型>
            codec结果hex = ""
            如果 (codec是编码)
            {
                如果 (codec输出 == "" || codec输出 == "hex")
                {
                    codec结果hex = 字节集到十六进制文本 (codec字节)
                    如果 (codec大写)
                    {
                        codec结果 = 到大写 (codec结果hex)
                    }
                    否则
                    {
                        codec结果 = 到小写 (codec结果hex)
                    }
                }
                否则 (codec输出 == "base64")
                {
                    codec结果 = 字节集到Base64文本 (codec字节, , -1)
                }
                否则
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "编码方向(hex_encode/utf8_encode/gbk_encode)的 output 只能是 hex | base64 | 实际: " + codec输出 + " | 要拿文本请用对应的 _decode 动作"))
                }
            }
            否则
            {
                如果 (codec输出 == "" || codec输出 == "text")
                {
                    如果 (codec是GBK)
                    {
                        codec结果 = 多字节到文本 (codec字节)
                    }
                    否则
                    {
                        codec结果 = UTF8到文本 (codec字节)
                    }
                }
                否则 (codec输出 == "hex")
                {
                    codec结果hex = 字节集到十六进制文本 (codec字节)
                    如果 (codec大写)
                    {
                        codec结果 = 到大写 (codec结果hex)
                    }
                    否则
                    {
                        codec结果 = 到小写 (codec结果hex)
                    }
                }
                否则 (codec输出 == "base64")
                {
                    codec结果 = 字节集到Base64文本 (codec字节, , -1)
                }
                否则
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "解码方向的 output 只能是 text | hex | base64 | 实际: " + codec输出))
                }
            }
            变量 codec字符集 <类型 = 文本型>
            codec字符集 = "utf8"
            如果 (codec是GBK)
            {
                codec字符集 = "gbk"
            }
            codec实际字节数 = 取字节集长度 (codec字节)
            变量 codec回包 <类型 = YYJSON对象类>
            codec回包.创建自文本 ("{}")
            codec回包.加入逻辑值成员 ("success", 真)
            codec回包.加入文本成员 ("action", codec动作)
            codec回包.加入文本成员 ("charset", codec字符集)
            codec回包.加入文本成员 ("input", codec输入)
            codec回包.加入文本成员 ("output", codec结果)
            codec回包.加入整数成员 ("bytes", codec实际字节数)
            codec回包.加入整数成员 ("chars", 取文本长度 (codec结果))
            codec回包.加入文本成员 ("note", "hex 输出默认小写(uppercase=true 切大写); 文本出口按 action 的字符集解释(utf8 或 gbk); 文本出口按类库C字符串语义构造, 遇内嵌零字节会截断, 二进制请用 output=hex 或 output=base64")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, codec回包.到可读文本 (YYJSON格式化选项.压缩)))
        }
        // === 时间戳换算与格式化: 全部走 视窗基本类 时间操作类 (零前置) ===
        // 陷阱1: 取时间戳 返回【整数】(32位) —— 2038-01-19 03:14:07Z 之后溢出, 故越界入参直接报错, 且秒级值只在 1902..2037 年份区间内计算。
        // 陷阱2: 时间到文本 会"省略为 0 的时分秒"(午夜/整点退化成日期), 故只作 friendly 人读字段; 机器可解析一律用 时间到格式文本。
        // 陷阱3: 时间戳语义 = 真 UTC(类库按【当前】时区 Bias 补偿, UTC+8 时 Bias=-480), 不含历史/DST 偏移。
        // 陷阱4: 到时间 解析失败返回哨兵值 数值范围.最小日期时间值(100年1月1日), 必须用 为最小时间 判定, 不能与空文本混淆。
        否则 (方法名 == "browser_time_convert")
        {
            变量 时间有时间戳 <类型 = 逻辑型>
            时间有时间戳 = MCP命令服务器.参数键存在 (参数JSON, "timestamp")
            变量 时间有文本 <类型 = 逻辑型>
            时间有文本 = MCP命令服务器.参数键存在 (参数JSON, "time_text")
            变量 时间动作 <类型 = 文本型>
            时间动作 = ""
            如果 (MCP命令服务器.参数键存在 (参数JSON, "action"))
            {
                时间动作 = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            }
            如果 (时间动作 == "")
            {
                // action 可省略: 按已给参数自动选(与 browser_reverse_runtime 的既有约定一致)
                如果 (时间有时间戳)
                {
                    时间动作 = "ts_to_text"
                }
                否则 (时间有文本)
                {
                    时间动作 = "text_to_ts"
                }
                否则
                {
                    时间动作 = "now"
                }
            }
            如果 (时间动作 != "now" && 时间动作 != "ts_to_text" && 时间动作 != "text_to_ts" && 时间动作 != "verify_tz")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "action 只能是 now | ts_to_text | text_to_ts | verify_tz (省略时按已给参数自动选) | 实际: " + 时间动作))
            }
            变量 时间单位 <类型 = 文本型>
            时间单位 = "s"
            如果 (MCP命令服务器.参数键存在 (参数JSON, "unit"))
            {
                时间单位 = MCP命令服务器.yyjson取文本 (参数JSON, "unit")
            }
            如果 (时间单位 != "s" && 时间单位 != "ms")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "unit 只能是 s(秒) | ms(毫秒) | 实际: " + 时间单位))
            }
            变量 时间格式 <类型 = 文本型>
            时间格式 = MCP命令服务器.yyjson取文本 (参数JSON, "format")
            如果 (时间格式 == "")
            {
                时间格式 = "%Y-%m-%d %H:%M:%S"
            }
            变量 时间值 <类型 = 小数>
            时间值 = 0
            变量 时间戳输入 <类型 = 长整数>
            时间戳输入 = 0
            如果 (时间动作 == "now")
            {
                时间值 = 取现行时间 ()
            }
            否则 (时间动作 == "verify_tz")
            {
                // 免文本解析的时区自检锚点: UTC+8 机器上 指定时间(1970,1,1,8,0,0) 的 取时间戳 必须是 0
                时间值 = 指定时间 (1970, 1, 1, 8, 0, 0)
            }
            否则 (时间动作 == "ts_to_text")
            {
                如果 (时间有时间戳 == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "ts_to_text 需要 timestamp 参数(整数时间戳; 毫秒请同时传 unit=ms)"))
                }
                时间戳输入 = MCP命令服务器.yyjson取长整数 (参数JSON, "timestamp")
                变量 秒上界 <类型 = 长整数>
                秒上界 = 2147483647
                变量 秒下界 <类型 = 长整数>
                秒下界 = 0 - 秒上界 - 1
                如果 (时间单位 == "ms")
                {
                    时间值 = 毫秒时间戳到时间 (时间戳输入)
                }
                否则
                {
                    如果 (时间戳输入 > 秒上界 || 时间戳输入 < 秒下界)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "秒级时间戳超出类库可表示范围: 上限 2147483647 = 2038-01-19 03:14:07Z(类库 取时间戳 返回 32 位整数, 再往后会溢出) | 收到 " + 到文本 (时间戳输入) + " | 若你手上的数是毫秒, 请改传 unit=ms"))
                    }
                    时间值 = 时间戳到时间 (时间戳输入)
                }
                如果 (为有效时间 (时间值) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "时间戳无法转换为有效时间(超出 数值范围.最小/最大日期时间值): " + 到文本 (时间戳输入)))
                }
            }
            否则
            {
                如果 (时间有文本 == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "text_to_ts 需要 time_text 参数(时间文本)"))
                }
                变量 时间文本 <类型 = 文本型>
                时间文本 = MCP命令服务器.yyjson取文本 (参数JSON, "time_text")
                如果 (时间文本 == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "time_text 为空 | 空串不会被静默当作 1970-01-01, 请给出真实时间文本"))
                }
                变量 时间中文格式 <类型 = 逻辑型>
                时间中文格式 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "chinese", 真)
                时间值 = 到时间 (时间文本, 时间中文格式)
                如果 (为最小时间 (时间值))
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "无法解析时间文本(类库 到时间 返回哨兵值 数值范围.最小日期时间值 = 100年1月1日): " + 时间文本 + " | 中文格式例: 1973年11月15日12时30分25秒 / 1973-11-15 12:30:25 | 若为月日年顺序请传 chinese=false"))
                }
            }
            变量 时间年份 <类型 = 整数>
            时间年份 = 取年份 (时间值)
            变量 时间戳秒 <类型 = 整数>
            时间戳秒 = 0
            变量 时间戳毫秒 <类型 = 长整数>
            时间戳毫秒 = 0
            变量 时间安全区 <类型 = 逻辑型>
            时间安全区 = 假
            如果 (时间年份 >= 1902 && 时间年份 <= 2037)
            {
                时间安全区 = 真
            }
            如果 (时间安全区)
            {
                时间戳秒 = 取时间戳 (时间值)
                时间戳毫秒 = 取毫秒时间戳 (时间值)
            }
            如果 (时间动作 == "ts_to_text" && 时间单位 == "ms")
            {
                // 毫秒档: 原样回显入参, 避免安全区外回显 0 造成误解(安全区内二者本就一致)
                时间戳毫秒 = 时间戳输入
            }
            变量 时间偏移分 <类型 = 整数>
            时间偏移分 = 0
            如果 (时间安全区)
            {
                // 本地相对 UTC 的分钟数: 取时间戳 已含 -Bias*60 补偿, 与"朴素本地秒"相减即得偏移(UTC+8 = -480)
                时间偏移分 = (时间戳秒 - (整数)取时间间隔 (时间值, 25569, 时间字段类型.秒)) / 60
            }
            变量 时间回包 <类型 = YYJSON对象类>
            时间回包.创建自文本 ("{}")
            时间回包.加入逻辑值成员 ("success", 真)
            时间回包.加入文本成员 ("action", 时间动作)
            时间回包.加入文本成员 ("unit", 时间单位)
            时间回包.加入小数成员 ("ole", 时间值)
            时间回包.加入整数成员 ("year", 时间年份)
            时间回包.加入整数成员 ("timestamp_s", 时间戳秒)
            时间回包.加入长整数成员 ("timestamp_ms", 时间戳毫秒)
            时间回包.加入文本成员 ("local", 时间到格式文本 (时间值, 时间格式))
            时间回包.加入文本成员 ("friendly", 时间到文本 (时间值))
            时间回包.加入整数成员 ("tz_offset_minutes", 时间偏移分)
            时间回包.加入文本成员 ("format", 时间格式)
            如果 (时间安全区 == 假)
            {
                时间回包.加入文本成员 ("warning", "年份 " + 到文本 (时间年份) + " 超出 取时间戳 的 32 位整数安全区(1902..2037): 类库 取时间戳 返回整数, 2038-01-19 03:14:07Z 之后溢出, 故本次不给出秒级时间戳与 tz_offset_minutes")
            }
            时间回包.加入文本成员 ("note", "local 按机器本地时区渲染; tz_offset_minutes 是本地相对 UTC 的分钟数(UTC+8 = -480); timestamp_s/timestamp_ms 是真 UTC 值; friendly 会省略为0的时分秒, 只作人读")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, 时间回包.到可读文本 (YYJSON格式化选项.压缩)))
        }'''


# ───────────────────────── 基础设施 ─────────────────────────

class PatchError(Exception):
    """带上下文的补丁错误：抛出时打印 traceback 全文 + 相关文件片段。"""

    def __init__(self, msg, path=None, lines=None, needle=None):
        super().__init__(msg)
        self.msg = msg
        self.path = path
        self.lines = lines
        self.needle = needle

    def render(self):
        out = [self.msg]
        if self.path:
            out.append('  文件: %s' % self.path)
        if self.needle:
            out.append('  锚点/子串: %r' % self.needle)
        if self.lines and self.needle:
            hit = [i for i, ln in enumerate(self.lines) if self.needle in ln]
            for idx in hit[:5]:
                lo = max(0, idx - 4)
                hi = min(len(self.lines), idx + 5)
                out.append('  片段(物理行 %d..%d):' % (lo + 1, hi))
                for k in range(lo, hi):
                    mark = '>>' if k == idx else '  '
                    out.append('    %s %5d | %s' % (mark, k + 1, self.lines[k]))
        return '\n'.join(out)


def read_wsv(path):
    """读 .wsv：要求 UTF-8 无 BOM、纯 LF。返回 (lines, text)。"""
    with open(path, 'rb') as fh:
        raw = fh.read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raise PatchError('文件带 UTF-8 BOM，不符合本项目 .wsv 约定，中止', path=path)
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        raise PatchError('文件是 UTF-16 编码，本脚本只处理 UTF-8，中止', path=path)
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise PatchError('文件不是合法 UTF-8，中止（原文异常已在上方 traceback 中）', path=path)
    cr = text.count('\r')
    if cr:
        lines = text.split('\n')
        raise PatchError('文件含 %d 个 CR（非纯 LF），与实测风格不符，中止' % cr, path=path, lines=lines,
                         needle=text.split('\r')[0][:40] if '\r' in text else None)
    lines = text.split('\n')
    return lines, text


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def uniq_line_index(lines, needle, path, tag):
    """锚点必须在文件中恰好命中 1 行；否则抛 PatchError（不写任何文件）。"""
    hit = [i for i, ln in enumerate(lines) if needle in ln]
    if len(hit) != 1:
        raise PatchError('%s: 锚点命中 %d 次（要求恰好 1 次），中止且不写任何文件' % (tag, len(hit)),
                         path=path, lines=lines, needle=needle)
    return hit[0]


def brace_counts(text):
    return text.count('{'), text.count('}'), text.count('{') - text.count('}')


def check_quotes(lines, tag):
    """每行"去掉 \\" 后双引号计数必须为偶数"（沿用 r114 补丁脚本的校验方式）。"""
    bad = []
    for i, ln in enumerate(lines):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            bad.append((i + 1, ln))
    if bad:
        msg = ['%s: 插入内容含"裸双引号"（会生成非法 .wsv 字符串），中止:' % tag]
        for n, ln in bad[:10]:
            msg.append('    第 %d 行: %s' % (n, ln))
        raise PatchError('\n'.join(msg))


VAR_DECL_RE = re.compile(r'^变量 ([^ <]+) <')
IDENT_RE = re.compile(r'[A-Za-z\u4e00-\u9fff_][A-Za-z0-9\u4e00-\u9fff_]*')


def check_scope(lines, tag):
    """作用域自检：块内(花括号深度>0)声明的变量若在更浅深度被引用，火山会编译不过。

    做法：按 `{`/`}` 跟踪深度；对每个"变量 X <...>"的声明记录(行号, 深度)；
    若 X 在声明之后、深度更浅的行里再次出现，即判定越界引用 → 中止。
    （本检查在本轮开发中实际抓到过一个真 bug：codec实际字节数 在 hex 分支内声明、
      却在分支外的回包处引用。）
    """
    depths = []
    depth = 0
    for ln in lines:
        depths.append(depth)
        depth += ln.count('{') - ln.count('}')
    if depth != 0:
        raise PatchError('%s: 花括号在块内不平衡（结束深度=%d），中止' % (tag, depth))

    decls = []   # (line_idx, depth, name)
    uses = {}
    for i, ln in enumerate(lines):
        s = ln.strip()
        md = VAR_DECL_RE.match(s)
        if md:
            decls.append((i, depths[i], md.group(1)))
        for name in IDENT_RE.findall(s):
            uses.setdefault(name, []).append(i)

    bad = []
    for i, d, name in decls:
        if d == 0:
            continue
        for j in uses.get(name, []):
            if j > i and depths[j] < d:
                bad.append((name, i + 1, d, j + 1, depths[j]))
                break
    if bad:
        msg = ['%s: 变量作用域越界（块内声明、块外引用），火山会编译不过，中止:' % tag]
        for name, dl, dd, ul, ud in bad:
            msg.append('    %s: 在第 %d 行(深度 %d)声明，却在第 %d 行(深度 %d)被引用' % (name, dl, dd, ul, ud))
        raise PatchError('\n'.join(msg))

    # 未使用变量提示（不阻断，只提示）
    unused = []
    for i, d, name in decls:
        if len(uses.get(name, [])) <= 1:
            unused.append((name, i + 1))
    return unused


def check_style(lines, tag):
    """缩进/空白风格自检：4 空格倍数、无 Tab、无行尾空白、无空行。"""
    bad = []
    for i, ln in enumerate(lines):
        if ln.rstrip() != ln:
            bad.append((i + 1, '行尾空白', ln))
        if '\t' in ln:
            bad.append((i + 1, '含 Tab', ln))
        if ln.strip() == '':
            bad.append((i + 1, '含空行', ln))
        indent = len(ln) - len(ln.lstrip(' '))
        if indent % 4 != 0:
            bad.append((i + 1, '缩进非 4 的倍数(%d)' % indent, ln))
    if bad:
        msg = ['%s: 风格自检失败，中止:' % tag]
        for n, why, ln in bad[:10]:
            msg.append('    第 %d 行 [%s]: %s' % (n, why, ln[:120]))
        raise PatchError('\n'.join(msg))


# 调用令牌白名单：插入块里"允许出现的被调用名"。任何不在表内的 NAME( 调用一律中止，
# 用来抓方法名拼写错误（例：把 时间戳到时间 写成 时间戳转时间）。
# 来源分三档，全部在 _codec_plan_r115.md 里有原文出处：
#   [CL] 视窗基本类（在册模块，w_bin_p/w_string_p/w_misc_p/w_math_p）
#   [YY] yyJSON 模块的 YYJSON对象类
#   [PR] 本项目既有方法（MCP_Server.wsv / MCP_Server_Core.wsv / MCP_ResponseBuilders.wsv）
#   [KW] 火山关键字
ALLOWED_CALLS = set('''
如果 否则 判断循环 返回 跳出循环 变量
UTF8到文本 文本到UTF8 多字节到文本 文本到多字节
字节集到十六进制文本 十六进制文本到字节集 字节集到Base64文本
删全部空 到大写 到小写 到文本 取文本长度 取文本中间 寻找文本 取字节集长度
为有效时间 为最小时间 指定时间 取现行时间 取年份
取时间戳 时间戳到时间 取毫秒时间戳 毫秒时间戳到时间 取时间间隔
时间到文本 时间到格式文本 到时间
创建自文本 到可读文本 加入文本成员 加入整数成员 加入长整数成员 加入小数成员 加入逻辑值成员
MCP命令服务器.yyjson取文本 yyjson取文本 yyjson取逻辑_默认 yyjson取长整数 参数键存在
MCP_响应构建.命令失败 命令失败 MCP_响应构建.命令成功_原始JSON 命令成功_原始JSON
FBrowser_Parser_Base64解码 是否为空 取字节集
添加工具JSON 置整数值 属性项JSON 多属性Schema文本 单参数Schema文本 空Schema文本
'''.split())


def _strip_strings(ln):
    out = []
    ins = False
    i = 0
    while i < len(ln):
        c = ln[i]
        if ins:
            if c == '\\' and i + 1 < len(ln):
                i += 2
                continue
            if c == '"':
                ins = False
            i += 1
            continue
        if c == '"':
            ins = True
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def check_calls(lines, tag):
    """调用令牌白名单自检：先剥掉字符串字面量与 // 注释，再取 `NAME (` 形式的令牌。"""
    unknown = {}
    seen = set()
    for i, ln in enumerate(lines):
        s = _strip_strings(ln)
        p = s.find('//')
        if p >= 0:
            s = s[:p]
        for tok in re.findall(r'([A-Za-z\u4e00-\u9fff_][A-Za-z0-9\u4e00-\u9fff_]*)\s*\(', s):
            seen.add(tok)
            if tok not in ALLOWED_CALLS:
                unknown.setdefault(tok, []).append(i + 1)
    if unknown:
        msg = ['%s: 出现白名单外的被调用名（疑似拼写错误 / 未在计划中验证过的 API），中止:' % tag]
        for tok, where in sorted(unknown.items()):
            msg.append('    %s  @ 插入块第 %s 行' % (tok, ','.join(str(x) for x in where[:6])))
        raise PatchError('\n'.join(msg))
    return sorted(seen)


def scan_registry_ids(lines):
    ids = []
    for ln in lines:
        s = ln.strip()
        if s.startswith('命令注册表.置整数值 ("') and s.endswith(')'):
            tail = s[:-1].rsplit(',', 1)[-1].strip()
            if tail.lstrip('-').isdigit():
                ids.append(int(tail))
    return ids


def count_occurrences(lines, needle):
    return sum(1 for ln in lines if needle in ln)


def insert_after(lines, idx, block_lines):
    return lines[:idx + 1] + block_lines + lines[idx + 1:]


def insert_before(lines, idx, block_lines):
    return lines[:idx] + block_lines + lines[idx:]


def preview(lines, first, count, label, pad=6):
    lo = max(0, first - pad)
    hi = min(len(lines), first + count + pad)
    out = ['  ── %s ──' % label]
    for k in range(lo, hi):
        mark = '>>' if first <= k < first + count else '  '
        s = lines[k]
        if len(s) > 170:
            s = s[:170] + ' …'
        out.append('    %s %5d | %s' % (mark, k + 1, s))
    return '\n'.join(out)


# ───────────────────────── 主流程 ─────────────────────────

def build_plan():
    """读取 + 校验 + 生成改动后的内容。任何失败抛 PatchError（不写文件）。"""
    server_path = os.path.join(SRC, SERVER)
    core_path = os.path.join(SRC, CORE)

    report = []
    server_lines, server_text = read_wsv(server_path)
    core_lines, core_text = read_wsv(core_path)
    report.append('[读入] %s: %d 行 / %d 字节 / sha256=%s' % (SERVER, len(server_lines), len(server_text.encode('utf-8')), sha(server_text)[:16]))
    report.append('[读入] %s: %d 行 / %d 字节 / sha256=%s' % (CORE, len(core_lines), len(core_text.encode('utf-8')), sha(core_text)[:16]))

    # B. 幂等性检查
    for name in NEW_TOOLS + ['browser.codec', 'browser.time_convert']:
        n = count_occurrences(server_lines, name) + count_occurrences(core_lines, name)
        if n:
            raise PatchError('幂等检查失败: %r 在改动前已出现 %d 次 —— 疑似已打过本补丁，中止（不写任何文件）' % (name, n),
                             path=server_path, lines=server_lines, needle=name)
    report.append('[幂等] 两个新工具名（含双变体）在改动前均 0 命中 —— 可以打补丁')

    # 新 ID
    ids = scan_registry_ids(server_lines)
    if not ids:
        raise PatchError('注册表 ID 扫描结果为空 —— 无法安全分配新 ID，中止', path=server_path, lines=server_lines,
                         needle='命令注册表.置整数值 ("')
    id1 = max(ids) + 1
    id2 = max(ids) + 2
    for cand in (id1, id2):
        if cand in ids:
            raise PatchError('分配出的 ID %d 已被占用，中止' % cand, path=server_path, lines=server_lines,
                             needle='", %d)' % cand)
    report.append('[ID] 注册表现有 %d 条映射, min=%d max=%d → 本次使用 %d 与 %d（均已断言未被占用）'
                  % (len(ids), min(ids), max(ids), id1, id2))

    # A. 锚点唯一性
    i_reg = uniq_line_index(server_lines, ANCHOR_REGISTRY, server_path, '命令注册表插入点')
    i_tool = uniq_line_index(server_lines, ANCHOR_TOOLLIST, server_path, '工具登记插入点')
    i_disp = uniq_line_index(core_lines, ANCHOR_DISPATCH, core_path, '核心分派插入点')
    report.append('[锚点] %s:%d  <- %r  (期望所在方法: %s)' % (SERVER, i_reg + 1, ANCHOR_REGISTRY, ANCHOR_METHOD[ANCHOR_REGISTRY]))
    report.append('[锚点] %s:%d  <- %r  (期望所在方法: %s)' % (SERVER, i_tool + 1, ANCHOR_TOOLLIST, ANCHOR_METHOD[ANCHOR_TOOLLIST]))
    report.append('[锚点] %s:%d  <- %r  (期望所在方法: %s)' % (CORE, i_disp + 1, ANCHOR_DISPATCH, ANCHOR_METHOD[ANCHOR_DISPATCH]))

    # 锚点所在方法的存在性（把行号漂移的影响降到最低：只报告，不阻断）
    for tag, lines, idx, method in (('注册表', server_lines, i_reg, ANCHOR_METHOD[ANCHOR_REGISTRY]),
                                    ('工具列表', server_lines, i_tool, ANCHOR_METHOD[ANCHOR_TOOLLIST]),
                                    ('分派器', core_lines, i_disp, ANCHOR_METHOD[ANCHOR_DISPATCH])):
        if not any(method in ln for ln in lines[:idx]):
            report.append('[警告] %s 插入点之前找不到方法声明 %r —— 请人工确认锚点仍在目标方法内' % (tag, method))

    reg_block = REG_BLOCK_TEMPLATE.format(id1=id1, id2=id2).split('\n')
    tool_block = TOOL_BLOCK.split('\n')
    disp_block = DISPATCH_BLOCK.split('\n')

    # D. 引号校验
    check_quotes(reg_block, '注册表插入块')
    check_quotes(tool_block, '工具登记插入块')
    check_quotes(disp_block, '分派分支插入块')

    # D2. 风格校验（缩进/Tab/行尾空白/空行）
    check_style(reg_block, '注册表插入块')
    check_style(tool_block, '工具登记插入块')
    check_style(disp_block, '分派分支插入块')
    report.append('[风格] 三个插入块：缩进均为 4 空格倍数、无 Tab / 行尾空白 / 空行')

    # D3. 调用令牌白名单（抓方法名拼写错误）
    call_tokens = check_calls(disp_block, '分派分支插入块')
    check_calls(tool_block, '工具登记插入块')
    check_calls(reg_block, '注册表插入块')
    report.append('[令牌] 分派分支共 %d 个被调用名，全部命中白名单（%d 项）: %s'
                  % (len(call_tokens), len(ALLOWED_CALLS), ' '.join(call_tokens)))

    # D3. 作用域自检（块内声明必须在块内使用；否则火山编译不过）
    unused_note = []
    for name, blk in (('注册表插入块', reg_block), ('工具登记插入块', tool_block), ('分派分支插入块', disp_block)):
        unused_note += check_scope(blk, name)
    report.append('[作用域] 三个插入块通过"块内声明必须在块内使用"检查（本轮开发中该检查抓到过 1 个真 bug）')
    if unused_note:
        report.append('[提示] 以下声明在块内未再被引用（仅提示，不阻断）: '
                      + ', '.join('%s@%d' % u for u in unused_note))

    # E. 插入块自身括号平衡
    for name, blk in (('注册表插入块', reg_block), ('工具登记插入块', tool_block), ('分派分支插入块', disp_block)):
        o, c, b = brace_counts('\n'.join(blk))
        if b != 0:
            raise PatchError('%s 自身花括号不平衡: 开=%d 闭=%d 差=%d，中止' % (name, o, c, b))
    report.append('[括号] 三个插入块自身 balance 均为 0 '
                  '(注册表 %d 行, 工具登记 %d 行, 分派分支 %d 行)'
                  % (len(reg_block), len(tool_block), len(disp_block)))

    # 生成新内容
    so, sc, sb = brace_counts(server_text)
    co, cc, cb = brace_counts(core_text)

    # 先插工具登记（行号更大）再插注册表，避免互相影响索引
    new_server = insert_after(server_lines, i_tool, tool_block)
    new_server = insert_after(new_server, i_reg, reg_block)
    new_core = insert_before(core_lines, i_disp, disp_block)

    new_server_text = '\n'.join(new_server)
    new_core_text = '\n'.join(new_core)

    # E. 改动前后 balance 必须一致
    so2, sc2, sb2 = brace_counts(new_server_text)
    co2, cc2, cb2 = brace_counts(new_core_text)
    if sb != sb2:
        raise PatchError('%s 花括号 balance 变化: 改动前 %d → 改动后 %d，中止' % (SERVER, sb, sb2),
                         path=server_path, lines=new_server, needle='{')
    if cb != cb2:
        raise PatchError('%s 花括号 balance 变化: 改动前 %d → 改动后 %d，中止' % (CORE, cb, cb2),
                         path=core_path, lines=new_core, needle='{')
    report.append('[括号] %s: 开=%d 闭=%d balance=%d → 开=%d 闭=%d balance=%d（一致）' % (SERVER, so, sc, sb, so2, sc2, sb2))
    report.append('[括号] %s: 开=%d 闭=%d balance=%d → 开=%d 闭=%d balance=%d（一致）' % (CORE, co, cc, cb, co2, cc2, cb2))

    # F. 自检：每个新工具名恰好 1 次登记 + 1 次分派
    checks = []
    for name in NEW_TOOLS:
        n_reg = count_occurrences(new_server, '添加工具JSON ("%s"' % name)
        n_reg_old = count_occurrences(new_server, '添加工具JSON ("%s",' % name)
        if n_reg == 0:
            n_reg = n_reg_old
        n_disp = count_occurrences(new_core, '否则 (方法名 == "%s")' % name)
        checks.append((name, n_reg, n_disp))
        if n_reg != 1:
            raise PatchError('自检失败: %s 的工具登记行数为 %d（应为 1）' % (name, n_reg),
                             path=server_path, lines=new_server, needle='添加工具JSON ("%s"' % name)
        if n_disp != 1:
            raise PatchError('自检失败: %s 的分派分支数为 %d（应为 1）' % (name, n_disp),
                             path=core_path, lines=new_core, needle='方法名 == "%s"' % name)
    # 双变体注册
    for name, variant in (('browser_codec', 'browser.codec'), ('browser_time_convert', 'browser.time_convert')):
        n = count_occurrences(new_server, '命令注册表.置整数值 ("%s"' % variant)
        if n != 1:
            raise PatchError('自检失败: 注册表变体 %s 出现 %d 次（应为 1）' % (variant, n),
                             path=server_path, lines=new_server, needle=variant)
    report.append('[自检] 工具登记 1 次 + 分派分支 1 次: ' + ' | '.join('%s(登记=%d, 分派=%d)' % c for c in checks))
    report.append('[自检] 注册表双变体各 1 次: browser.codec/browser_codec=%d, browser.time_convert/browser_time_convert=%d'
                  % (id1, id2))

    plan = {
        'server_path': server_path,
        'core_path': core_path,
        'server_lines': server_lines, 'core_lines': core_lines,
        'new_server': new_server, 'new_core': new_core,
        'server_sha_before': sha(server_text), 'core_sha_before': sha(core_text),
        'i_reg': i_reg, 'i_tool': i_tool, 'i_disp': i_disp,
        'reg_block': reg_block, 'tool_block': tool_block, 'disp_block': disp_block,
        'id1': id1, 'id2': id2,
        'preview': '\n'.join([
            preview(new_server, i_reg, len(reg_block), '%s 注册表插入 (%d 行 @ 物理行 %d 之后)' % (SERVER, len(reg_block), i_reg + 1)),
            preview(new_server, i_tool + len(reg_block), len(tool_block), '%s 工具登记插入 (%d 行)' % (SERVER, len(tool_block))),
            preview(new_core, i_disp, len(disp_block), '%s 核心分派插入 (%d 行 @ 物理行 %d 之前)' % (CORE, len(disp_block), i_disp + 1)),
        ]),
        'report': report,
    }
    return plan


def write_files(plan):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    written = []
    for path, lines, sha_before, label in (
            (plan['server_path'], plan['new_server'], plan['server_sha_before'], SERVER),
            (plan['core_path'], plan['new_core'], plan['core_sha_before'], CORE)):
        # 写前复核：重新读一次，确认内容指纹未变（并发编辑竞态的最后一道闸）
        cur_lines, cur_text = read_wsv(path)
        if sha(cur_text) != sha_before:
            raise PatchError('写前复核失败: %s 在校验之后被其它进程改动（指纹已变），中止且未写入该文件' % label,
                             path=path, lines=cur_lines, needle=None)
        dst = os.path.join(BACKUP_DIR, label)
        if os.path.exists(dst):
            print('  [备份] 已存在，按约定不覆盖: %s' % dst)
        else:
            shutil.copy2(path, dst)
            print('  [备份] %s → %s' % (label, dst))
        data = '\n'.join(lines).encode('utf-8')
        with open(path, 'wb') as fh:
            fh.write(data)
        written.append((label, len(lines), len(data)))
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description='落地 browser_codec / browser_time_convert（先校验后写）')
    ap.add_argument('--dry-run', action='store_true', help='只校验 + 预览，不写任何文件（也不建备份）')
    args = ap.parse_args(argv)

    print('=' * 78)
    print(' 零前置编解码工具补丁  —— 对应 _audit/_codec_plan_r115.md')
    print(' 模式: %s' % ('DRY-RUN（只校验与预览，绝不写文件）' if args.dry_run else 'APPLY（校验通过后写文件）'))
    print('=' * 78)

    plan = build_plan()
    for ln in plan['report']:
        print(ln)
    print(plan['preview'])
    print('-' * 78)
    print('[计划] 将写入 %s: 注册表 %d 行 + 工具登记 %d 行' % (SERVER, len(plan['reg_block']), len(plan['tool_block'])))
    print('[计划] 将写入 %s: 分派分支 %d 行（含 browser_codec 与 browser_time_convert 两个分支）' % (CORE, len(plan['disp_block'])))
    print('[计划] 新命令 ID: browser_codec/browser.codec = %d, browser_time_convert/browser.time_convert = %d'
          % (plan['id1'], plan['id2']))

    if args.dry_run:
        print('DRY-RUN: 未写入任何文件、未创建任何备份。')
        print('复跑不带 --dry-run 即执行写入（会先备份到 备份/编解码工具-写入前/）。')
        return 0

    print('-' * 78)
    written = write_files(plan)
    for label, nlines, nbytes in written:
        print('  [写入] %s: %d 行 / %d 字节' % (label, nlines, nbytes))
    print('完成。注意：本脚本不编译、不调用 MCP、不重启程序；')
    print('      语法/类型/运行期行为均未验证 —— 请由主代理编译并串行执行 §3 验收表。')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except PatchError as exc:
        print('=' * 78, file=sys.stderr)
        print('补丁中止（未写入任何文件）', file=sys.stderr)
        print(exc.render(), file=sys.stderr)
        print('-' * 78, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)
    except Exception:
        print('=' * 78, file=sys.stderr)
        print('未预期异常（未写入任何文件）—— 原始 traceback 全文如下:', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(3)
