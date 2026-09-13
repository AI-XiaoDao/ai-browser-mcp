# -*- coding: utf-8 -*-
"""把 11 处"写回已存在的状态键"改为覆盖写(先删除该键的所有值再追加)。

根因见 MCP_Server.wsv 中 覆盖整数成员/覆盖文本成员 的注释:
  加入X成员 = yyjson_mut_obj_add_* (追加, 不覆盖) ; 取X = yyjson_obj_get (返回第一个)
  => 对象里出现重复键, 读回旧值, 状态机永远推进不了。

只改这 11 处(对象均来自 创建自文本(已存JSON)), 其余"新建对象首次写入"的地方不动。
按行号从后往前改, 避免行号漂移。只做精确整行替换, 不做正则。
"""
import io
import os
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
TARGET = os.path.join(SRC, 'MCP_Server_Core.wsv')

# 行号 -> (旧整行内容, 新整行内容)  行号为修改前文件中的 1-based 行号
PLAN = {
    3645: ('更新计数存储.加入整数成员 ("_poll_count", pollCount)',
           'MCP命令服务器.覆盖整数成员 (更新计数存储, "_poll_count", pollCount)'),
    3798: ('sUpd.加入整数成员 ("_phase", scrapePhase)',
           'MCP命令服务器.覆盖整数成员 (sUpd, "_phase", scrapePhase)'),
    3827: ('sUpd2.加入文本成员 ("_check_task_id", sCheckID)',
           'MCP命令服务器.覆盖文本成员 (sUpd2, "_check_task_id", sCheckID)'),
    3867: ('sUpd3.加入整数成员 ("_phase", 2)',
           'MCP命令服务器.覆盖整数成员 (sUpd3, "_phase", 2)'),
    3868: ('sUpd3.加入文本成员 ("_check_task_id", "")',
           'MCP命令服务器.覆盖文本成员 (sUpd3, "_check_task_id", "")'),
    3876: ('sUpd3b.加入文本成员 ("_check_task_id", "")',
           'MCP命令服务器.覆盖文本成员 (sUpd3b, "_check_task_id", "")'),
    3956: ('sUpd4.加入整数成员 ("_phase", 3)',
           'MCP命令服务器.覆盖整数成员 (sUpd4, "_phase", 3)'),
    3957: ('sUpd4.加入文本成员 ("_extract_task_id", sExtID)',
           'MCP命令服务器.覆盖文本成员 (sUpd4, "_extract_task_id", sExtID)'),
    4056: ('更新等待存储.加入文本成员 ("_check_task_id", checkTaskID)',
           'MCP命令服务器.覆盖文本成员 (更新等待存储, "_check_task_id", checkTaskID)'),
    4057: ('更新等待存储.加入整数成员 ("_poll_count", pollCount)',
           'MCP命令服务器.覆盖整数成员 (更新等待存储, "_poll_count", pollCount)'),
    4110: ('重置等待.加入整数成员 ("_poll_count", pollCount)',
           'MCP命令服务器.覆盖整数成员 (重置等待, "_poll_count", pollCount)'),
}


def main():
    with io.open(TARGET, encoding='utf-8-sig') as f:
        raw = f.read()
    lines = raw.split('\n')
    ok = bad = 0
    for ln in sorted(PLAN, reverse=True):
        old, new = PLAN[ln]
        r = lines[ln - 1]
        ind = r[:len(r) - len(r.lstrip())]
        if r.strip() != old:
            print('  !! 行 %d 内容不符, 跳过\n     实际: %r\n     期望: %r' % (ln, r.strip(), old))
            bad += 1
            continue
        lines[ln - 1] = ind + new
        ok += 1
    if bad:
        print('有 %d 处未匹配, 未写回(避免半成品)' % bad)
        return 1
    with io.open(TARGET, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('\n'.join(lines))
    print('已替换 %d 处' % ok)
    return 0


if __name__ == '__main__':
    sys.exit(main())
