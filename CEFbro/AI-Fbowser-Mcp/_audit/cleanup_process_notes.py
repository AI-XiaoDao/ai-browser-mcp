# -*- coding: utf-8 -*-
"""清理"纯过程性操作备注"(按**内容锚点**定位, 不用会漂移的行号)。

取舍原则(逐条看过上下文后定的, 不是照单全删):
  · **删**: 自包含、零信息的改动史/进度簿记, 且删掉后上下文不残句。
  · **改写**: 该行承载了"为什么必须这么做"的语义, 只是用了"原来/修复"的历史口吻
            -> 改成约束/规则陈述, 保留知识。
  · **不动**: 报告里的片段在当前源码里已定位不到(说明期间已被改动) —— 定位不到就绝不盲删;
            以及"首行被后文'于是…'依赖"的块(删了会残句, 且改写属编辑加工, 收益不抵风险)。

每条都以**当前源码里的整行文本**为锚点, 要求在该文件中恰好命中一次, 否则中止(不写)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '过程性备注清理-写入前')

# ---------- 删除项: (文件, 该行去除首尾空白后的完整文本) ----------
DEL = [
    ('MCP_Server.wsv', '// v2.8.2 续: CDP逆向R5-R9 剩余预留号开始补齐实现 (get_possible_breakpoints/add_binding 为本次新分配)'),
    ('MCP_Server.wsv', '// 修复: 原实现丢弃返回值并无条件置 CDP观察者已注册=真 且打印"已自动注册"。'),
    ('MCP_Server.wsv', '// 原子递增并直接返回原子操作结果: 修复原实现丢弃返回值后二次非原子读回的竞态(重复ID/跳号)'),
    ('MCP_Server.wsv', '// 该钩子此前从未被调用 —— 于是工具能加规则却永不产生事件(假成功), 现按设计意图接上。'),
    ('MCP_Server.wsv', '// 修复: 改yyjson解析 (原手写逐字符读取不处理冒号后空白)'),
    ('MCP_Server.wsv', '// 修复(竞态): 调用方未持锁(如browser_create等待循环已显式解锁)时纯延时, 不做解锁/加锁'),
    ('MCP_Server.wsv', '// 修(失败不给原因): 原返回体只有 error:"timeout", 调用方看不出等了多久、为什么没等到。'),
    ('MCP_Server.wsv', '// 修复(竞态): 关闭前取异步缓存锁, 防止CEF回调线程/在途HTTP线程在关闭窗口内并发访问已关闭连接'),
    ('MCP_Server.wsv', '// 修复: 原 计数器+1 为非原子读改写, 多线程并发可产生重复task_id; 改Interlocked原子递增'),
    ('MCP_Server.wsv', '// 修复(数据): 等待态判定改 JSON 解析(与 存储异步结果 一致), 防结果文本含 _waiting:true 字面量误判'),
    ('MCP_Server.wsv', '// 修复(数据): REPLACE 覆盖前保留既有 browser_id/poll_count (原仅4列写入致其归零, 引发跨浏览器等待误触发)'),
    ('MCP_Server.wsv', '// 修复(数据): 强制删除排除 is_waiting=1, 防轮询中的等待任务被强删(客户端假"未找到任务结果")'),
    ('MCP_Server.wsv', '// 修复: 警告日志移出锁外, 不延长异步缓存锁持有时间'),
    ('MCP_Server.wsv', '// 修复(P0): 同步等待期间让出协议锁所需的请求级静态上下文暂存'),
    ('MCP_Server.wsv', '// 修复: 轮询参数原在循环内逐次重建(对象构建+序列化+再解析), 一次性构造复用'),
    ('MCP_Server.wsv', '// 修复: 空闲时不再误导性返回"信号已发送"'),
    ('MCP_Server.wsv', '// 本次仅补登记, 不改任何实现逻辑。'),
    ('MCP_Server_Core.wsv', '// ★ 修(不静默假成功): 原来这里**无条件**写 success:真 —— 于是"一次命中都没有"'),
    ('MCP_Server_Utils.wsv', '// 修复: 转换失败时丢弃, 不把NUL填充写入stderr'),
    ('MCP_Server_Utils.wsv', '// 修复: 正文+换行单次写出, 防多线程日志交错错位'),
]

# ---------- 改写项: (文件, 旧行, 新行) ----------
REW = [
    # 章节标题里的版本号+"核心修复"无信息量; 保留它真正说明的事(结果经 mcp_result 回传)
    ('MCP_Server_Core.wsv',
     '// === v1.8 CDP结果回传 (核心修复: 结果通过mcp_result返回) ===',
     '// === CDP 结果回传 (异步命令的结果经 mcp_result 取回) ==='),
    # 在 @ 注入的 C++ 里: 去掉历史口吻, 保留"为什么必须无条件消费"这一约束
    ('MCP_Stdio.wsv',
     '@         // 修复: 无条件等待并消费空行分隔符(轮询+退出检查), 防客户端分块写时漏消费导致帧体错位',
     '@         // 必须无条件等待并消费空行分隔符(轮询+退出检查): 客户端分块写时若漏消费, 帧体会错位'),
]


def main():
    touched = {}
    for fn, old in DEL:
        p = os.path.join(SRC, fn)
        text = touched.get(fn) or io.open(p, encoding='utf-8').read()
        if text.count(old) != 1:
            print('!! 删除锚点命中 %d 次(应为1), 中止: %s' % (text.count(old), old[:60]))
            return 1
        touched[fn] = text.replace(old + '\n', '', 1) if (old + '\n') in text else text.replace(old, '', 1)
    for fn, old, new in REW:
        p = os.path.join(SRC, fn)
        text = touched.get(fn)
        if text is None:
            text = io.open(p, encoding='utf-8').read()
        if text.count(old) != 1:
            print('!! 改写锚点命中 %d 次(应为1), 中止: %s' % (text.count(old), old[:60]))
            return 1
        touched[fn] = text.replace(old, new, 1)

    os.makedirs(BAK, exist_ok=True)
    total_del = 0
    for fn, text in touched.items():
        p = os.path.join(SRC, fn)
        before = io.open(p, encoding='utf-8').read()
        shutil.copy2(p, os.path.join(BAK, fn))
        nl = '\r\n' if '\r\n' in before else '\n'
        open(p, 'wb').write(text.encode('utf-8'))
        d = before.count('\n') - text.count('\n')
        total_del += d
        print('   %-24s 行数 %d -> %d (%+d)' % (fn, before.count('\n') + 1,
                                                text.count('\n') + 1, -d))
    print('\n已处理 %d 个文件; 净删 %d 行; 备份 -> %s' % (len(touched), total_del, BAK))
    return 0


sys.exit(main())
