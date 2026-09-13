# -*- coding: utf-8 -*-
r"""第141轮补丁: 新增三个**零风险纯函数/单行封装**工具(并行只读分诊确认的真缺口)。

## 依据(逐条核对, 不是照抄粗报告)
| 类库方法 | 出处 | 现状 |
|---|---|---|
| `FBrowser_Parser_解析JSON (json_string, options)` → `类_FBrowser_值`(失败返回 NULL) | FBroLib.wsv:433-441 | **仅内部使用**: 全项目唯一活调用点是 CDP params 解析(`MCP_Server.wsv:1780`), 代理没有任何 JSON 校验/规范化入口 |
| `FBrowser_Parser_写入JSON (node, options)` → 文本型 | FBroLib.wsv:450-457 | 真缺口 |
| `FBrowser_Parser_字节值解析为JSON (字节值, options)` | FBroLib.wsv:443-448 | 真缺口(注释原文: 字节值空指针直接返回空值类, 调用方必须先判空) |
| `FBrowser_Parser_取数据URI (mimetype, 数据)` → 文本型 | FBroLib.wsv:394-402 | 真缺口(现在只能"base64 编码 + 手工拼 data: 前缀", 易漏 mime/编码声明) |
| `FBrowser_浏览器_通过序号取浏览器 (序号)` → `类_FBrowser_浏览器` | FBroLib.wsv:487-492 | 真缺口(注释原文: 获取失败返回**空浏览器**, 必须判空) |

## 三个工具
1. `browser_json`: `action=validate`(默认, 给**校验结论**: valid/value_type/长度) / `normalize`(合法则回规范化 JSON, 非法则失败) /
   `from_base64`(base64 → 字节 → JSON, 走类库 `字节值解析为JSON` 而不是猜编码); 支持 `allow_trailing_commas`。
2. `browser_data_uri`: `mime` + `data` → data URI(直接来自类库, 不用手工拼)。
3. `browser_by_index`: `index` → 该序号浏览器的 id/url/是否弹窗, **判空并给可行动失败**, 并附带与 `browser_list` 顺序的交叉说明。

用法: py -3 _audit\_apply_round141.py [--apply]
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

# ── Core: 三个分派分支(插在 browser_codec 之前, 与编解码族相邻) ──
BRANCH_ANCHOR = '''        // === 零前置编解码: hex / UTF-8 / GBK多字节 (全部走 视窗基本类 已有函数, 零新模块) ==='''
BRANCH_NEW = '''        // === JSON 校验 / 规范化 / base64 入口 (零风险纯函数: 类库 FBrowser_Parser_解析JSON / 写入JSON / 字节值解析为JSON) ===
        // 为什么需要: 代理拿到的常是 JSON 文本, 却没有"这串是不是合法 JSON"的可信判据, 只能自己猜;
        //   而类库解析失败会返回 NULL(注释原文), 正好可以给出**确定的结论**。
        否则 (方法名 == "browser_json")
        {
            变量 jsAction <类型 = 文本型>
            jsAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            如果 (jsAction == "")
            {
                jsAction = "validate"
            }
            如果 (jsAction != "validate" && jsAction != "normalize" && jsAction != "from_base64")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + jsAction + " | 支持: validate(默认, 只给校验结论) / normalize(合法则回规范化JSON) / from_base64(data 是 base64 文本)"))
            }
            变量 jsData <类型 = 文本型>
            jsData = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (jsData == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数))
            }
            // options: 类库 JSON解析.RFC(0)=严格; JSON解析.允许逗号(1)=容忍尾逗号。
            // 实测口径: 本参数**同时**作用于解析与写出(类库共用同一个 options 位)。
            变量 jsOptions <类型 = 整数>
            jsOptions = JSON解析.RFC
            如果 (MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "allow_trailing_commas", 假))
            {
                jsOptions = JSON解析.允许逗号
            }
            变量 js值 <类型 = 类_FBrowser_值>
            变量 js来源 <类型 = 文本型>
            js来源 = "text"
            如果 (jsAction == "from_base64")
            {
                // base64 → 字节集 → JSON: 走类库的字节入口, 不先把字节猜成某种编码再解析
                变量 jsBytes <类型 = 类_FBrowser_字节集>
                jsBytes = FBrowser_Parser_Base64解码 (jsData)
                如果 (jsBytes.是否为空 ())
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "base64 解码失败(空字节集): 请检查 data 是否为合法 base64 | 实测: 类库 字节值解析为JSON 对空字节值直接返回空值类, 故先判空"))
                }
                js值 = FBrowser_Parser_字节值解析为JSON (jsBytes, jsOptions)
                js来源 = "base64"
            }
            否则
            {
                js值 = FBrowser_Parser_解析JSON (jsData, jsOptions)
            }
            变量 js合法 <类型 = 逻辑型>
            js合法 = (js值.是否为空 () == 假)
            如果 (jsAction == "validate")
            {
                // validate 是**校验结论**: 非法输入也回 success(工具确实完成了校验), 用 valid=false 表达结果
                变量 jsOut <类型 = YYJSON对象类>
                jsOut.创建自文本 ("{}")
                jsOut.加入逻辑值成员 ("success", 真)
                jsOut.加入逻辑值成员 ("valid", js合法)
                jsOut.加入文本成员 ("input", js来源)
                jsOut.加入整数成员 ("input_length", 取文本长度 (jsData))
                jsOut.加入整数成员 ("options_used", jsOptions)
                如果 (js合法)
                {
                    变量 js类型值 <类型 = 整数>
                    js类型值 = js值.取类型 ()
                    jsOut.加入整数成员 ("value_type", js类型值)
                    jsOut.加入文本成员 ("value_type_name", MCP命令服务器.JSON值类型名 (js类型值))
                    变量 js规范化 <类型 = 文本型>
                    js规范化 = FBrowser_Parser_写入JSON (js值, jsOptions)
                    jsOut.加入整数成员 ("normalized_length", 取文本长度 (js规范化))
                }
                否则
                {
                    jsOut.加入文本成员 ("note", "不是合法 JSON —— 这是**校验结论**, 不是工具故障 | 常见原因: 尾逗号(可传 allow_trailing_commas:true) / 单引号 / 未加引号的键名 / 注释 / 截断 | 类库原文: 解析失败返回 NULL(本项目据此判定)")
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, jsOut.到可读文本 (YYJSON格式化选项.压缩)))
            }
            如果 (js合法 == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, jsAction + " 需要合法 JSON, 但解析失败(input=" + js来源 + ", 长度=" + 到文本 (取文本长度 (jsData)) + ") | 先用 action=validate 拿到校验结论; 若是尾逗号请传 allow_trailing_commas:true; 若是二进制请改用 action=from_base64"))
            }
            变量 js规范化2 <类型 = 文本型>
            js规范化2 = FBrowser_Parser_写入JSON (js值, jsOptions)
            变量 jsOut2 <类型 = YYJSON对象类>
            jsOut2.创建自文本 ("{}")
            jsOut2.加入逻辑值成员 ("success", 真)
            jsOut2.加入逻辑值成员 ("valid", 真)
            jsOut2.加入文本成员 ("input", js来源)
            jsOut2.加入整数成员 ("value_type", js值.取类型 ())
            jsOut2.加入文本成员 ("value_type_name", MCP命令服务器.JSON值类型名 (js值.取类型 ()))
            jsOut2.加入文本成员 ("normalized", js规范化2)
            jsOut2.加入整数成员 ("options_used", jsOptions)
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, jsOut2.到可读文本 (YYJSON格式化选项.压缩)))
        }
        // === data URI 构造(类库 FBrowser_Parser_取数据URI) ===
        否则 (方法名 == "browser_data_uri")
        {
            变量 duMime <类型 = 文本型>
            duMime = MCP命令服务器.yyjson取文本 (参数JSON, "mime")
            如果 (duMime == "")
            {
                duMime = "text/plain"
            }
            变量 duData <类型 = 文本型>
            duData = MCP命令服务器.yyjson取文本 (参数JSON, "data")
            如果 (duData == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "data " + MCP_常量.错误_缺少参数 + " | 用 browser_data_uri 可直接得到可内联的 data: URI(本地图片/绕过 CSP 取图/构造内联资源的最短路径)"))
            }
            变量 du结果 <类型 = 文本型>
            du结果 = FBrowser_Parser_取数据URI (duMime, duData)
            如果 (du结果 == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "类库未返回 data URI(输入为空或 mime 非法): mime=" + duMime))
            }
            变量 duOut <类型 = YYJSON对象类>
            duOut.创建自文本 ("{}")
            duOut.加入逻辑值成员 ("success", 真)
            duOut.加入文本成员 ("mime", duMime)
            duOut.加入整数成员 ("data_length", 取文本长度 (duData))
            duOut.加入整数成员 ("uri_length", 取文本长度 (du结果))
            duOut.加入文本成员 ("data_uri", du结果)
            duOut.加入文本成员 ("note", "data URI 长度约为输入文本的 4/3(含 base64 与前缀); MCP 的 HTTP 通道在参数/回包约 1MB 处会被断连且无错误码 —— 超大资源请改用 browser_kernel_scheme(mcp:// 方案)或落盘后用 file 参数")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, duOut.到可读文本 (YYJSON格式化选项.压缩)))
        }
        // === 按序号取浏览器(类库 FBrowser_浏览器_通过序号取浏览器) ===
        否则 (方法名 == "browser_by_index")
        {
            变量 biIndex <类型 = 整数>
            biIndex = MCP命令服务器.yyjson取整数 (参数JSON, "index")
            如果 (biIndex < 0)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "index 必须 >= 0(从0开始) | 用 browser_list 看当前全部浏览器"))
            }
            变量 biBrowser <类型 = 类_FBrowser_浏览器>
            biBrowser = FBrowser_浏览器_通过序号取浏览器 (biIndex)
            如果 (biBrowser.是否为空 () || biBrowser.是否已关闭 ())
            {
                // 类库注释原文: 获取失败将返回一个空浏览器, 注意判断 —— 故这里如实失败, 绝不回 success
                变量 bi数量 <类型 = 整数>
                bi数量 = FBrowser_浏览器_取数量 ()
                返回 (MCP_响应构建.命令失败 (命令ID, "序号 " + 到文本 (biIndex) + " 没有对应浏览器(当前共 " + 到文本 (bi数量) + " 个) | index 从 0 开始; 用 browser_list 看全部(它按 ID 清单枚举, **顺序不保证与序号一致**) | 想按 ID/标签/窗口句柄定位: browser_cdp_call? 不必 —— 用 browser_find_by_tag / browser_find_by_hwnd / browser_list"))
            }
            变量 biOut <类型 = YYJSON对象类>
            biOut.创建自文本 ("{}")
            biOut.加入逻辑值成员 ("success", 真)
            biOut.加入整数成员 ("index", biIndex)
            biOut.加入整数成员 ("browser_id", biBrowser.取ID ())
            biOut.加入逻辑值成员 ("is_popup", biBrowser.是否为弹窗 ())
            变量 bi框架 <类型 = 类_FBrowser_框架>
            bi框架 = MCP命令服务器.取安全主框架 (biBrowser)
            如果 (bi框架.是否为空 () == 假)
            {
                biOut.加入文本成员 ("url", bi框架.取地址 ())
            }
            变量 bi清单 <类型 = 类_FBrowser_列表值>
            bi清单 = FBrowser_浏览器_取ID清单 ()
            如果 (bi清单.是否为空 () == 假)
            {
                变量 biID串 <类型 = 文本型>
                biID串 = ""
                计次循环 (bi清单.取大小 ())
                {
                    如果 (取循环索引 () > 0)
                    {
                        biID串 = biID串 + ","
                    }
                    biID串 = biID串 + 到文本 (bi清单.取整数值 (取循环索引 ()))
                }
                biOut.加入文本成员 ("id_list_in_order", biID串)
            }
            biOut.加入文本成员 ("note", "序号来自类库内置浏览器清单(与 browser_list 的 ID 清单**不保证同序**); 需要稳定引用请用返回的 browser_id")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, biOut.到可读文本 (YYJSON格式化选项.压缩)))
        }
        // === 零前置编解码: hex / UTF-8 / GBK多字节 (全部走 视窗基本类 已有函数, 零新模块) ==='''

# ── Server: 值类型名助手(把类库 值类型 常量翻成可读名, 供 browser_json 用) ──
HELPER_ANCHOR = '''    # 菜单规格"修改类"类型的**唯一判定源**'''
HELPER_NEW = '''    # 类库 `值类型` 常量 → 可读名(browser_json 回包用; 常量定义见 FBroConst.wsv 的 值类型 类)
    方法 JSON值类型名 <公开 静态 类型 = 文本型 @输出名 = "JSONValueTypeName" @强制输出 = 真>
    参数 类型值 <类型 = 整数 @输出名 = "TypeValue">
    {
        如果 (类型值 == 值类型.空)
        {
            返回 ("null")
        }
        如果 (类型值 == 值类型.逻辑)
        {
            返回 ("bool")
        }
        如果 (类型值 == 值类型.整数型)
        {
            返回 ("int")
        }
        如果 (类型值 == 值类型.双精度小数型)
        {
            返回 ("double")
        }
        如果 (类型值 == 值类型.文本)
        {
            返回 ("string")
        }
        如果 (类型值 == 值类型.字节集型)
        {
            返回 ("binary")
        }
        如果 (类型值 == 值类型.字典值型)
        {
            返回 ("dict")
        }
        如果 (类型值 == 值类型.列表型)
        {
            返回 ("list")
        }
        返回 ("invalid")
    }

''' + HELPER_ANCHOR

# ── Server: 注册三个工具 + 命令注册表 id ──
REG_ANCHOR = '''        命令注册表.置整数值 ("browser_context_menu", 1322)'''
REG_NEW = '''        命令注册表.置整数值 ("browser_json", 1331)
        命令注册表.置整数值 ("browser_data_uri", 1332)
        命令注册表.置整数值 ("browser_by_index", 1333)
''' + REG_ANCHOR

TOOL_ANCHOR = '''添加工具JSON ("browser_menu_probe",'''
TOOL_NEW = '''添加工具JSON ("browser_json", "JSON 校验/规范化(**零风险纯函数**, 走类库 FBrowser_Parser_解析JSON / 写入JSON) | action=validate(默认): 给**校验结论** —— 非法输入也回 success, 用 `valid:false` 表达(这不是工具故障), 并给出 value_type/value_type_name/长度; action=normalize: 合法则回**规范化(压缩)JSON**, 非法则失败并说明怎么办; action=from_base64: data 是 base64 文本(例: 页面里 btoa 出来的), 走类库字节入口解析, **不猜编码** | allow_trailing_commas=true 容忍尾逗号(类库选项 JSON解析.允许逗号) | 用途: 代理拿到的常是 JSON 文本, 以前只能自己猜是否合法; 现在有确定判据。类库原文: 解析失败返回 NULL", 多属性Schema文本 (属性项JSON ("action", "text", "validate(默认)/normalize/from_base64") + "," + 属性项JSON ("data", "text", "待处理文本(或 base64 文本)") + "," + 属性项JSON ("allow_trailing_commas", "boolean", "true=容忍尾逗号(解析与写出共用该选项)"), "\\"data\\""))
添加工具JSON ("browser_data_uri", "构造 data: URI(走类库 FBrowser_Parser_取数据URI) —— 把本地图片/文本内联进页面、绕过 CSP 取图、构造内联资源的最短路径(以前只能手工拼 base64 前缀, 容易漏 mime/编码声明) | 返回 data_uri 与长度; 注意: MCP 的 HTTP 通道在参数/回包约 1MB 处会被断连且**无错误码**, 超大资源请改用 browser_kernel_scheme(mcp:// 方案)或落盘后用 file 参数", 多属性Schema文本 (属性项JSON ("mime", "text", "MIME 类型(默认 text/plain), 如 image/png") + "," + 属性项JSON ("data", "text", "要内联的数据(文本)"), "\\"data\\""))
添加工具JSON ("browser_by_index", "按**序号**取浏览器(走类库 FBrowser_浏览器_通过序号取浏览器) | 返回 browser_id / is_popup / url, 并附 ID 清单便于交叉核对 | **实测注意**: 序号来自类库内置清单, 与 browser_list 的 ID 清单**不保证同序**; 需要稳定引用请用返回的 browser_id(或 browser_find_by_tag / browser_find_by_hwnd) | 类库原文: 获取失败返回**空浏览器**, 故越界会**明确失败**而不是回空成功", 多属性Schema文本 (属性项JSON ("index", "integer", "序号, 从 0 开始"), "\\"index\\""))
''' + TOOL_ANCHOR

EDITS = [
    (CORE, 'K1 三个新分派分支', BRANCH_ANCHOR, BRANCH_NEW),
    (SERVER, 'K2 值类型名助手', HELPER_ANCHOR, HELPER_NEW),
    (SERVER, 'K3 命令注册表 id 1331/1332/1333', REG_ANCHOR, REG_NEW),
    (SERVER, 'K4 注册三个工具', TOOL_ANCHOR, TOOL_NEW),
]


def main():
    print('== 第141轮补丁 (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-32s 锚点未找到(可能已应用)' % tag)
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
