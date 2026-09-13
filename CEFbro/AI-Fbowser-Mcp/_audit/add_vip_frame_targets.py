# -*- coding: utf-8 -*-
"""给 browser_vip_execute_js_context 补 main/all_frames/frame_index 三档目标（A 组第 4 项）。

价值: `高级_执行JS_全部框架` 一次打穿**所有 iframe**, 省掉"枚举框架→N 次注入"的往返。

★两个必须处理好的诚实性问题:
  1. **多帧回调会覆盖**: 既有 `类_MCP_VIP通用回调` 每次回调都 `存储异步结果(任务ID, ...)` ——
     而"全部框架"的回调**每帧调一次**, 于是调用方轮询只会看到**最后一帧**。
     故新增**累计式**回调类: 每次回调追加并更新汇总(count + frames_text), 让调用方能看全。
  2. **未启用执行环境时会静默无回调**: 类库注释写明这些 VIP 方法需先"启用执行环境"才生效;
     若未启用, 回调可能永不触发 ⇒ 调用方轮询到超时也看不出原因。
     故给工具加**前置状态判断**: 本会话没启用过就**明确失败并给指引**(而不是发一个永远不完成的异步任务)。
     状态由 browser_vip_enable_js_env 维护(新增一个静态标志), 属自有状态、不靠猜。
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'VIP多帧目标-写入前')

CB = os.path.join(SRC, 'MCP_Callbacks.wsv')
VIP = os.path.join(SRC, 'MCP_Server_VIP.wsv')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')

MULTI_CLASS = '''
类 类_MCP_VIP多帧回调 <公开 基础类 = 类_FBrowserVIP_通用回调 @输出名 = "MCPVIPMultiFrameCallback">
{
    变量 任务ID <公开 类型 = 文本型 @输出名 = "TaskID">
    变量 帧计数 <公开 类型 = 整数 @输出名 = "FrameCount">
    变量 累计文本 <公开 类型 = 文本型 @输出名 = "AccumulatedText">

    方法 数据回调 <公开 @虚拟方法 = 可覆盖>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 标识ID <类型 = 整数 @输出名 = "KeyID">
    参数 成功 <类型 = 逻辑型 @输出名 = "Success">
    参数 数据指针 <类型 = 变整数 @输出名 = "DataPtr">
    参数 数据大小 <类型 = 整数 @输出名 = "DataSize">
    {
        // 每帧回调一次: **累计**而不是覆盖(既有的 类_MCP_VIP通用回调 是覆盖式, 用在这里只会留最后一帧)
        帧计数 = 帧计数 + 1
        变量 本条文本 <类型 = 文本型>
        本条文本 = ""
        如果 (成功 && 数据指针 != 0 && 数据大小 > 0)
        {
            变量 结果UTF8 <类型 = 字节集类>
            结果UTF8 = 指针到字节集 (数据指针, 数据大小)
            本条文本 = UTF8到文本 (结果UTF8)
            如果 (取字节集长度 (结果UTF8) > MCP_常量.截断_VIP数据最大字节)
            {
                本条文本 = MCP命令服务器.字节安全截断 (本条文本, MCP_常量.截断_VIP数据最大字节) + "...[MCP截断]"
            }
        }
        如果 (累计文本 == "")
        {
            累计文本 = "[帧1] " + 本条文本
        }
        否则
        {
            累计文本 = 累计文本 + "\\n[帧" + 到文本 (帧计数) + "] " + 本条文本
        }
        变量 汇总 <类型 = YYJSON对象类>
        汇总.创建自文本 ("{}")
        汇总.加入逻辑值成员 ("success", 真)
        汇总.加入整数成员 ("frame_count", 帧计数)
        汇总.加入文本成员 ("frames_text", 累计文本)
        汇总.加入文本成员 ("note", "多帧执行: 每个框架回调一次, 本结果为**累计**; 是否已跑完请自行判断(可用 browser_get_frames 取预期帧数对比 frame_count)")
        MCP命令服务器.存储异步结果 (任务ID, 汇总.到可读文本 (YYJSON格式化选项.压缩))
    }
}
'''

# VIP: 启用环境时维护自有状态标志
ENV_ANCHOR = '                    vip_ctrl.高级_启用执行环境 (MCP命令服务器.yyjson取逻辑 (参数JSON, "enable"))\n'
ENV_NEW = (ENV_ANCHOR +
           '                    // 维护自有状态: 供 browser_vip_execute_js_context 做**前置判断**,\n'
           '                    // 避免"未启用执行环境 -> 回调永不触发 -> 调用方白等到超时"。\n'
           '                    MCP命令服务器.VIP_JS环境已启用 = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")\n')

# VIP: 分派分支整体替换(加入 target/frame_index 与环境前置判断)
EXEC_OLD = '''            如果 (jsCode != "")
            {
                变量 vipCtrl <类型 = 类_FBrowserVIP_控制器>
                vipCtrl = MCP命令服务器.取VIP控制器 ()
                如果 (vipCtrl.是否为空 () == 假)
                {
                    变量 ctxID <类型 = 整数>
                    ctxID = MCP命令服务器.yyjson取整数 (参数JSON, "context_id")
                    变量 frmID <类型 = 文本型>
                    frmID = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                    变量 异步VIPJSID <类型 = 文本型>
                    异步VIPJSID = MCP命令服务器.生成异步任务ID ()
                    变量 VIPJS回调 <类型 = 类_FBrowser_事件智能指针>
                    VIPJS回调.创建 (类_MCP_VIP通用回调)
                    VIPJS回调.取执行类 (类_MCP_VIP通用回调).任务ID = 异步VIPJSID
                    如果 (frmID != "")
                    {
                        vipCtrl.高级_执行JS_框架ID (jsCode, frmID, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)
                    }
                    否则
                    {
                        vipCtrl.高级_执行JS (jsCode, ctxID, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)
                    }
                    返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步VIPJSID, "JS已提交到指定环境"))
                }
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_VIP不可用))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "需要code参数"))
'''
EXEC_NEW = '''            如果 (jsCode != "")
            {
                变量 vipCtrl <类型 = 类_FBrowserVIP_控制器>
                vipCtrl = MCP命令服务器.取VIP控制器 ()
                如果 (vipCtrl.是否为空 () == 假)
                {
                    变量 vipTarget <类型 = 文本型>
                    vipTarget = MCP命令服务器.yyjson取文本 (参数JSON, "target")
                    变量 ctxID <类型 = 整数>
                    ctxID = MCP命令服务器.yyjson取整数 (参数JSON, "context_id")
                    变量 frmID <类型 = 文本型>
                    frmID = MCP命令服务器.yyjson取文本 (参数JSON, "frame_id")
                    变量 frmIndex <类型 = 整数>
                    frmIndex = MCP命令服务器.yyjson取整数 (参数JSON, "frame_index")
                    // 前置判断: 这些 VIP 方法需先"启用执行环境"才生效; 未启用时回调可能永不触发,
                    // 调用方只会白等到超时且看不出原因 —— 故此处**明确失败并给指引**(可行动, 不静默)。
                    如果 (vipTarget == "main" || vipTarget == "all_frames" || vipTarget == "frame_index")
                    {
                        如果 (MCP命令服务器.VIP_JS环境已启用 == 假)
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "target=" + vipTarget + " 需要先启用 VIP JS 执行环境: 请先调 browser_vip_enable_js_env {enable:true, confirm:true} | ⚠ 实测启用后会破坏本会话 CDP 通道(CDP 优先工具会退化), 且需重启进程才能恢复 —— 建议只在确实需要时使用 | 另: browser_execute_js 走 CDP, 不需要该环境"))
                        }
                    }
                    变量 异步VIPJSID <类型 = 文本型>
                    异步VIPJSID = MCP命令服务器.生成异步任务ID ()
                    如果 (vipTarget == "all_frames")
                    {
                        // 多帧: 用**累计式**回调(每帧一次, 覆盖式回调只会留最后一帧)
                        变量 多帧回调 <类型 = 类_FBrowser_事件智能指针>
                        多帧回调.创建 (类_MCP_VIP多帧回调)
                        多帧回调.取执行类 (类_MCP_VIP多帧回调).任务ID = 异步VIPJSID
                        多帧回调.取执行类 (类_MCP_VIP多帧回调).帧计数 = 0
                        多帧回调.取执行类 (类_MCP_VIP多帧回调).累计文本 = ""
                        vipCtrl.高级_执行JS_全部框架 (jsCode, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, 多帧回调)
                        返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步VIPJSID, "JS已提交到**全部框架** | 每个框架回调一次, 结果为累计(frame_count/frames_text) | 是否跑完请对比 browser_get_frames 的帧数"))
                    }
                    变量 VIPJS回调 <类型 = 类_FBrowser_事件智能指针>
                    VIPJS回调.创建 (类_MCP_VIP通用回调)
                    VIPJS回调.取执行类 (类_MCP_VIP通用回调).任务ID = 异步VIPJSID
                    如果 (vipTarget == "main")
                    {
                        vipCtrl.高级_执行JS_主框架 (jsCode, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)
                        返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步VIPJSID, "JS已提交到**主框架**(顶级框架)"))
                    }
                    如果 (vipTarget == "frame_index")
                    {
                        如果 (frmIndex < 0)
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "target=frame_index 需要 frame_index(从0开始, 0 一般为主框架)"))
                        }
                        vipCtrl.高级_执行JS_框架序号 (jsCode, frmIndex, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)
                        返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步VIPJSID, "JS已提交到框架序号 " + 到文本 (frmIndex)))
                    }
                    如果 (frmID != "")
                    {
                        vipCtrl.高级_执行JS_框架ID (jsCode, frmID, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)
                    }
                    否则
                    {
                        vipCtrl.高级_执行JS (jsCode, ctxID, 真, 假, 真, MCP_常量.URL请求默认超时, 假, 假, VIPJS回调)
                    }
                    返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步VIPJSID, "JS已提交到指定环境"))
                }
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_VIP不可用))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "需要code参数"))
'''

# Server: 状态标志 + schema
FIELD_ANCHOR = '    变量 JS查询注册名文本 <公开 静态 类型 = 文本型 @输出名 = "JSQueryNamesText">\n'
FIELD_NEW = ''  # 该字段在第111轮已撤回, 故改用别的锚点
FIELD_ANCHOR2 = '    变量 菜单已启用 <公开 静态 类型 = 逻辑型 值 = 假 @输出名 = "MenuEnabled">\n'
FIELD_NEW2 = FIELD_ANCHOR2 + (
    '    # VIP JS 执行环境是否已启用(由 browser_vip_enable_js_env 维护):\n'
    '    # 供 browser_vip_execute_js_context 的 main/all_frames/frame_index 做前置判断, 避免静默等到超时。\n'
    '    变量 VIP_JS环境已启用 <公开 静态 类型 = 逻辑型 值 = 假 @输出名 = "VipJSEnvEnabled">\n'
)

SCHEMA_OLD = ('添加工具JSON ("browser_vip_execute_js_context", "VIP: 指定环境执行JS", 多属性Schema文本 (属性项JSON ("code", "text", "JS代码") + "," + 属性项JSON ("context_id", "integer", "环境ID") + "," + 属性项JSON ("frame_id", "text", "框架ID"), ""))')
SCHEMA_NEW = ('添加工具JSON ("browser_vip_execute_js_context", "VIP: 在指定环境/框架执行JS。target 缺省=按 context_id/frame_id 走原行为; '
              'target=main(主框架/顶级框架) / all_frames(**当前所有框架各执行一遍**, 一次打穿全部 iframe, 回调逐帧返回且结果为累计) / frame_index(按浏览器加载框架的序号执行, 需 frame_index, 0 一般为主框架)。'
              '⚠ 这三个 target 属 VIP 高级功能, **需先 browser_vip_enable_js_env {enable:true, confirm:true}**(未启用会明确失败而不是静默等待); '
              '该开关会破坏本会话 CDP 通道且需重启恢复 | 不需要 VIP 环境时请用 browser_execute_js(走 CDP)", '
              '多属性Schema文本 (属性项JSON ("code", "text", "JS代码") + "," + '
              '属性项JSON ("target", "text", "缺省/main/all_frames/frame_index") + "," + '
              '属性项JSON ("frame_index", "integer", "target=frame_index: 框架序号(从0开始, 0 一般为主框架)") + "," + '
              '属性项JSON ("context_id", "integer", "环境ID(缺省路径用)") + "," + '
              '属性项JSON ("frame_id", "text", "框架ID(缺省路径用, 与 target 互斥时以 target 优先)"), ""))')


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('   %s 换行=%s' % (tag, 'CRLF' if nl == '\r\n' else 'LF'))
    norm = [(old.replace('\n', nl), new) for old, new in pairs]
    for old, new in norm:
        c = text.count(old)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, old.strip()[:70]))
            return None
    for old, new in norm:
        for ln in new.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号奇数: %s' % ln.strip()[:100])
                return None
        text = text.replace(old, new.replace('\n', nl), 1)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.encode('utf-8'))
    print('   %s 已写入(+%d 处)' % (os.path.basename(path), len(pairs)))
    return text


# 1) 回调类追加(CRLF)
t = io.open(CB, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in t else '\n'
if not t.endswith(nl):
    t += nl
os.makedirs(BAK, exist_ok=True)
shutil.copy2(CB, os.path.join(BAK, 'MCP_Callbacks.wsv'))
open(CB, 'wb').write((t + MULTI_CLASS.replace('\n', nl)).encode('utf-8'))
print('   MCP_Callbacks.wsv 已追加 类_MCP_VIP多帧回调')

# 2) VIP 文件
if patch(VIP, [(ENV_ANCHOR, ENV_NEW), (EXEC_OLD, EXEC_NEW)], 'MCP_Server_VIP.wsv') is None:
    sys.exit(1)

# 3) Server: 字段 + schema
if patch(SERVER, [(FIELD_ANCHOR2, FIELD_NEW2), (SCHEMA_OLD, SCHEMA_NEW)], 'MCP_Server.wsv') is None:
    sys.exit(1)
print('完成; 备份 -> %s' % BAK)
