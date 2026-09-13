# -*- coding: utf-8 -*-
"""修正上一轮补丁的 3 个编译错误(语法自检当场抓到, 未进入真机测试)。

错误1 (Core:5076) 没有找到"autoBp零命中":
   声明在 5102(循环前), 但赋值在 5076(断点处, 更早) -> 用了未声明的名字。
   修法: 把声明移到赋值之前。

错误2/3 (Core:5416/5437) 无法把"文本型"转换到"YYJSON只读对象类":
   `yyjson取对象成员_安全` 的第 1 参是 **YYJSON只读对象类**, 我误传了 JSON 文本。
   修法: 先把 body 文本 `创建自文本` 成对象, 再取成员; 并用创建成功作为守卫,
        避免把未创建的对象传进去。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '窗口能力编译修正-写入前')

# ---- 错误1: 声明前移 ----
DECL_AT_WRONG = '\n'.join([
    '            变量 auto停止原因 <类型 = 文本型>',
    '            auto停止原因 = "未知(循环提前结束)"',
    '            变量 autoBp零命中 <类型 = 逻辑型 值 = 假>',
])
DECL_FIXED = '\n'.join([
    '            变量 auto停止原因 <类型 = 文本型>',
    '            auto停止原因 = "未知(循环提前结束)"',
])

USE_AT = '            autoBp零命中 = MCP命令服务器.CDP断点是否零命中 (autoBpRaw)'
USE_AT_FIXED = '\n'.join([
    '            变量 autoBp零命中 <类型 = 逻辑型 值 = 假>',
    '            autoBp零命中 = MCP命令服务器.CDP断点是否零命中 (autoBpRaw)',
])

# ---- 错误2/3: 先解析成对象再取成员 ----
BEFORE_OLD = '\n'.join([
    '                变量 mw前色 <类型 = YYJSON只读对象类>',
    '                如果 (mw前体 != "")',
    '                {',
    '                    mw前色 = MCP命令服务器.yyjson取对象成员_安全 (mw前体, "bounds")',
    '                }',
])
BEFORE_NEW = '\n'.join([
    '                变量 mw前色 <类型 = YYJSON只读对象类>',
    '                如果 (mw前体 != "")',
    '                {',
    '                    变量 mw前JSON <类型 = YYJSON只读对象类>',
    '                    如果 (mw前JSON.创建自文本 (mw前体))',
    '                    {',
    '                        mw前色 = MCP命令服务器.yyjson取对象成员_安全 (mw前JSON, "bounds")',
    '                    }',
    '                }',
])

AFTER_OLD = '\n'.join([
    '                变量 mw后色 <类型 = YYJSON只读对象类>',
    '                如果 (mw后体 != "")',
    '                {',
    '                    mw后色 = MCP命令服务器.yyjson取对象成员_安全 (mw后体, "bounds")',
    '                }',
])
AFTER_NEW = '\n'.join([
    '                变量 mw后色 <类型 = YYJSON只读对象类>',
    '                如果 (mw后体 != "")',
    '                {',
    '                    变量 mw后JSON <类型 = YYJSON只读对象类>',
    '                    如果 (mw后JSON.创建自文本 (mw后体))',
    '                    {',
    '                        mw后色 = MCP命令服务器.yyjson取对象成员_安全 (mw后JSON, "bounds")',
    '                    }',
    '                }',
])


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    c = rd(CORE)
    edits = [("错误1a 去掉错位声明", DECL_AT_WRONG), ("错误1b 声明前移", USE_AT),
             ("错误2 前回读", BEFORE_OLD), ("错误3 后回读", AFTER_OLD)]
    for label, old in edits:
        n = c.count(old)
        print("[%s] 锚点 %d 次" % (label, n))
        if n != 1:
            print("!! 预期 1 次, 中止")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(CORE, os.path.join(BAK, os.path.basename(CORE)))
    print("已备份到 %s" % BAK)
    c = (c.replace(DECL_AT_WRONG, DECL_FIXED).replace(USE_AT, USE_AT_FIXED)
         .replace(BEFORE_OLD, BEFORE_NEW).replace(AFTER_OLD, AFTER_NEW))
    wr(CORE, c)
    print("OK: 3 个编译错误已修")
    with io.open(CORE, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
