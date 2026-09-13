# -*- coding: utf-8 -*-
r"""第141轮补丁 L: `browser_screenshot` 补齐被写死的三个类库参数 —— **整页截图此前根本做不到**。

## 依据(逐字核对)
类库 `高级_网页截图`(FBroVip.wsv:717-736) 第 2/4/5 参:
  参数 截图质量 <整数>                "压缩质量 [0..100) (jpeg)"
  参数 是否表面 <逻辑型>              "fromSurface: 从表面而不是视图捕获截图"
  参数 是否包括视窗以外 <逻辑型>      "captureBeyondViewport: 捕获 viewport 之外的截图"
项目调用点(`MCP_Server_Core.wsv` 的 browser_screenshot)恒传 `80, 假, 假` ⇒
**整页截图做不到**(captureBeyondViewport 恒假), 且 jpeg 质量不可调。

## 补法
1. 新增 `quality`(默认 80, 钳 1..100)、`from_surface`(默认假)、`capture_beyond_viewport`(默认假);
2. 新增 `full_page`(默认假): 先量出文档真实尺寸(scrollHeight/scrollWidth, 含视口下限)再按它裁剪 +
   自动打开 `captureBeyondViewport` + 原点归零。**只开 captureBeyondViewport 而不给高度拿到的仍是视口大小**
   —— 类库的 rect 宽高不能为 0, 必须显式给"整页尺寸"。
3. 整页高度上限放宽到 20000(原 7680 是为"超大分辨率内存风险"设的通用钳制), 并在回执里如实说明按什么尺寸裁的。

用法: py -3 _audit\_apply_round141L.py [--apply]
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

CORE_OLD = '''                    // 全部异步: 生成task_id, 回调触发时存储结果
                    变量 异步截图ID <类型 = 文本型>
                    异步截图ID = MCP命令服务器.生成异步任务ID ()
                    变量 截图回调 <类型 = 类_FBrowser_事件智能指针>
                    截图回调.创建 (类_MCP_截图异步回调)
                    截图回调.取执行类 (类_MCP_截图异步回调).任务ID = 异步截图ID
                    截图回调.取执行类 (类_MCP_截图异步回调).图片格式 = fmt
                    vip_ctrl.高级_网页截图 (fmt, 80, 截图大小, 假, 假, 截图回调)
                    返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步截图ID, "截图已提交, 通过mcp_result查询", 800))'''

CORE_NEW = '''                    // 类库第 2/4/5 参此前被写死成 80/假/假 ⇒ **整页截图做不到**、jpeg 质量不可调。现全部开放:
                    变量 截图质量 <类型 = 整数>
                    截图质量 = MCP命令服务器.yyjson取整数 (参数JSON, "quality")
                    如果 (截图质量 <= 0)
                    {
                        截图质量 = 80
                    }
                    如果 (截图质量 > 100)
                    {
                        截图质量 = 100
                    }
                    变量 从表面截图 <类型 = 逻辑型>
                    从表面截图 = MCP命令服务器.yyjson取逻辑 (参数JSON, "from_surface")
                    变量 视窗之外 <类型 = 逻辑型>
                    视窗之外 = MCP命令服务器.yyjson取逻辑 (参数JSON, "capture_beyond_viewport")
                    变量 整页截图 <类型 = 逻辑型>
                    整页截图 = MCP命令服务器.yyjson取逻辑 (参数JSON, "full_page")
                    变量 整页测量说明 <类型 = 文本型>
                    整页测量说明 = ""
                    如果 (整页截图)
                    {
                        // 整页必须先**量出文档真实尺寸**再按它裁剪: 类库的 rect 宽高不能为 0,
                        // 只把 captureBeyondViewport 置真而高度仍传视口大小, 拿到的还是视口那一屏。
                        变量 页高文本 <类型 = 文本型>
                        页高文本 = MCP命令服务器.CDP执行JS并等待 ("(function(){var d=document.documentElement,b=document.body;return Math.max(d?d.scrollHeight:0,b?b.scrollHeight:0,window.innerHeight||0)})()", 8000, 真)
                        变量 页宽文本 <类型 = 文本型>
                        页宽文本 = MCP命令服务器.CDP执行JS并等待 ("(function(){var d=document.documentElement,b=document.body;return Math.max(d?d.scrollWidth:0,b?b.scrollWidth:0,window.innerWidth||0)})()", 8000, 真)
                        变量 页高 <类型 = 整数>
                        页高 = 文本到整数 (页高文本)
                        变量 页宽 <类型 = 整数>
                        页宽 = 文本到整数 (页宽文本)
                        如果 (页高 > 0)
                        {
                            截图大小.高度 = 页高
                            整页测量说明 = "按文档实际尺寸裁剪 height=" + 到文本 (页高)
                        }
                        如果 (页宽 > 0)
                        {
                            截图大小.宽度 = 页宽
                            如果 (整页测量说明 != "")
                            {
                                整页测量说明 = 整页测量说明 + ", "
                            }
                            整页测量说明 = 整页测量说明 + "width=" + 到文本 (页宽)
                        }
                        截图大小.横坐标 = 0
                        截图大小.纵坐标 = 0
                        视窗之外 = 真
                        // 整页高度另有天花板: 通用 7680 钳制是为"超大分辨率内存风险"设的, 整页需要更高上限
                        如果 (截图大小.高度 > 20000)
                        {
                            截图大小.高度 = 20000
                            整页测量说明 = 整页测量说明 + " (高度已按 20000 上限钳制)"
                        }
                        如果 (截图大小.宽度 > 7680)
                        {
                            截图大小.宽度 = 7680
                            整页测量说明 = 整页测量说明 + " (宽度已按 7680 上限钳制)"
                        }
                        如果 (整页测量说明 == "")
                        {
                            整页测量说明 = "未能量出文档尺寸(页面可能未就绪), 已按传入的 width/height 裁剪 + captureBeyondViewport"
                        }
                    }
                    // 全部异步: 生成task_id, 回调触发时存储结果
                    变量 异步截图ID <类型 = 文本型>
                    异步截图ID = MCP命令服务器.生成异步任务ID ()
                    变量 截图回调 <类型 = 类_FBrowser_事件智能指针>
                    截图回调.创建 (类_MCP_截图异步回调)
                    截图回调.取执行类 (类_MCP_截图异步回调).任务ID = 异步截图ID
                    截图回调.取执行类 (类_MCP_截图异步回调).图片格式 = fmt
                    vip_ctrl.高级_网页截图 (fmt, 截图质量, 截图大小, 从表面截图, 视窗之外, 截图回调)
                    返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步截图ID, "截图已提交(质量=" + 到文本 (截图质量) + ", 表面=" + 选择 (从表面截图, "真", "假") + ", 视窗之外=" + 选择 (视窗之外, "真", "假") + 选择 (整页测量说明 == "", "", " | 整页: " + 整页测量说明) + "), 通过mcp_result查询", 800))'''

DESC_OLD = '''"页面截图| 返回 base64 图片(data:image/...); format=png/jpeg/webp, 可指定 width/height/x/y/scale 裁剪缩放"'''
DESC_NEW = '''"页面截图| 返回 base64 图片(data:image/...); format=png/jpeg/webp, 可指定 width/height/x/y/scale 裁剪缩放 | **full_page:true = 整页截图**: 本工具先量出文档真实尺寸(scrollHeight/scrollWidth)再按它裁剪并自动打开 captureBeyondViewport —— 只开该开关而高度仍传视口大小, 拿到的还是视口那一屏(类库 rect 宽高不能为 0); 整页高度上限 20000 | quality(默认80, jpeg 压缩质量, 1..100) / from_surface(从表面而非视图捕获) / capture_beyond_viewport(手动开启捕获视窗之外) 三个类库参数原先被写死成 80/假/假, 现已开放 | 截图是**异步任务**: 回执带 task_id, 用 mcp_result 取回图片"'''

SCHEMA_OLD = '''属性项JSON ("scale", "integer", "缩放(默认1)"), ""))'''
SCHEMA_NEW = '''属性项JSON ("scale", "integer", "缩放(默认1)") + "," + 属性项JSON ("full_page", "boolean", "true=整页截图(自动量文档尺寸 + captureBeyondViewport; 高度上限20000)") + "," + 属性项JSON ("quality", "integer", "jpeg 压缩质量 1..100(默认80)") + "," + 属性项JSON ("from_surface", "boolean", "从表面而非视图捕获(fromSurface)") + "," + 属性项JSON ("capture_beyond_viewport", "boolean", "手动开启捕获视窗之外(整页请优先用 full_page)"), ""))'''

EDITS = [(CORE, 'L1 三个类库参数 + full_page', CORE_OLD, CORE_NEW),
         (SERVER, 'L2 截图描述(整页/质量)', DESC_OLD, DESC_NEW),
         (SERVER, 'L3 截图 schema 补四参数', SCHEMA_OLD, SCHEMA_NEW)]


def main():
    print('== 第141轮补丁 L (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-34s 锚点未找到(可能已应用)' % tag)
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
