# -*- coding: utf-8 -*-
"""撤掉 JS 查询通道的两处改动 + **删除该工具**。

结论依据(本轮两次实测):
  ① 运行期注册(浏览器已存在): 注册报成功, 但页面里 window.mcpQuery / cefQuery 等**全部 undefined**,
     刷新后依旧 —— JS 函数从未注入。
  ② 启动期注册(挪到 main.wsv 的 FBrowser_初始化 之前): 构建通过, 但应用**起不来** ——
     `就绪 tools=317 cdp=False`, fastcheck 0.1s 即失败。
⇒ CEF message router 在本应用**不可用**。留着这个工具就等于"声明有、实际不可用"的幽灵能力,
   故连工具一起删掉(与"幽灵注册清零"一致), 并把这个负结论写进报告, 避免后续重复投入。
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
BAK = os.path.join(ROOT, '备份', '撤掉JS查询通道-写入前')
os.makedirs(BAK, exist_ok=True)


def rw(path, fn, tag):
    data = open(path, 'rb').read()
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    out = fn(text, nl)
    if out is None:
        print('!! %s 处理失败' % tag)
        return False
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(out.encode('utf-8'))
    print('   %s 已处理' % tag)
    return True


# 1) main.wsv: 按备份还原(最稳)
mainp = os.path.join(SRC, 'main.wsv')
bak_main = os.path.join(ROOT, '备份', 'JS查询启动期注册-写入前', 'main.wsv')
if os.path.exists(bak_main):
    shutil.copy2(mainp, os.path.join(BAK, 'main.wsv'))
    shutil.copy2(bak_main, mainp)
    print('   main.wsv 已从"启动期注册前"备份还原')
else:
    print('!! 找不到 main.wsv 备份')

# 2) MCP_Callbacks.wsv: 删掉追加的回调类
cb = os.path.join(SRC, 'MCP_Callbacks.wsv')


def strip_cb(text, nl):
    i = text.find('类 类_MCP_JS交互事件')
    if i < 0:
        print('   (MCP_Callbacks 未找到该类, 跳过)')
        return text
    return text[:i].rstrip('\r\n') + nl


rw(cb, strip_cb, 'MCP_Callbacks.wsv(删类)')

# 3) MCP_Server.wsv: 删字段块 / helper / 工具注册行 / 注册表两行
srv = os.path.join(SRC, 'MCP_Server.wsv')


def strip_srv(text, nl):
    # 3a 字段
    i = text.find('    # non-CDP 的 JS<->宿主查询通道(CEF message router)')
    j = text.find('    变量 JS查询事件指针')
    if i >= 0 and j > i:
        j = text.find(nl, j) + len(nl)
        text = text[:i] + text[j:]
    # 3b helper
    i = text.find('    # JS 查询回调里调用: 记录请求并返回应回复给页面的文本。')
    if i >= 0:
        k = text.find('    方法 记录JS查询并取回复', i)
        e = text.find('    # 把"右键上下文"(类_FBrowser_菜单环境)取成紧凑 JSON', k)
        if k > 0 and e > k:
            text = text[:i] + text[e:]
    # 3c 工具注册行
    text = re.sub(r'^.*添加工具JSON \("browser_js_query".*' + re.escape(nl), '', text, flags=re.M)
    # 3d 注册表两行
    text = re.sub(r'^.*命令注册表\.置整数值 \("browser_js_query".*' + re.escape(nl), '', text, flags=re.M)
    text = re.sub(r'^.*注册命令双变体 \("js_query".*' + re.escape(nl), '', text, flags=re.M)
    return text


rw(srv, strip_srv, 'MCP_Server.wsv(删字段/helper/注册)')

# 4) MCP_Server_Core.wsv: 删分派分支
core = os.path.join(SRC, 'MCP_Server_Core.wsv')


def strip_core(text, nl):
    i = text.find('        // === 非 CDP 的 JS<->宿主查询通道(CEF message router) ===')
    e = text.find('        // === 右键菜单自定义(方案甲: 只暂存规格, 由 CEF 回调在模型有效期内施加) ===', i)
    if i < 0 or e < 0:
        print('   (Core 未找到该分支, 跳过)')
        return text
    return text[:i] + text[e:]


rw(core, strip_core, 'MCP_Server_Core.wsv(删分派)')

# 复核
print('\n== 复核(应全为 0) ==')
for fn in ('main.wsv', 'MCP_Callbacks.wsv', 'MCP_Server.wsv', 'MCP_Server_Core.wsv'):
    t = io.open(os.path.join(SRC, fn), encoding='utf-8').read()
    print('   %-24s JS交互=%d cefQuery=%d browser_js_query=%d 类_MCP_JS交互事件=%d'
          % (fn, t.count('JS交互'), t.count('cefQuery'),
             t.count('browser_js_query'), t.count('类_MCP_JS交互事件')))
