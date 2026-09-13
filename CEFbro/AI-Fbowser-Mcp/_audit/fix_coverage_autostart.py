# -*- coding: utf-8 -*-
"""把 browser_reverse_precise_coverage 的默认动作改成**自动补前置**(目标: 前置缺失类失败 = 0)。

现状: take 是**默认动作**, 但未 action=start 时内核只回一句英文
`Precise coverage has not been started.` —— 上一轮我把这句话改写成了可行动的
"请先调 action=start", 但那只是**把前置缺失说得更清楚**, 并没有消除它:
台账因此新出现 1 条 `PREREQ` 失败, 与本目标"前置缺失类失败=0"冲突。

修法(与项目既有的反应式补域同一思路, 也与 browser_reverse_runtime 的做法一致):
  未开启时**自动** Profiler.enable + startPreciseCoverage, 再重新 take 一次,
  并经 auto_prepared 如实上报"补过什么"。调用方一次调用即可拿到数据。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '覆盖率自动补前置-写入前')

OLD = ('            如果 (pcAction == "take")\n'
       '            {\n'
       '                返回 (执行V8CDP命令 (命令ID, "Profiler.takePreciseCoverage", "{}", '
       '"cdp_result 内按 scriptId/url/functions 给出执行情况: count>0 的函数即真实执行过 | '
       '与 browser_reverse_search_script action=list 对照 scriptId 定位脚本"))\n'
       '            }')

NEW = '''            如果 (pcAction == "take")
            {
                // ★ 零前置(实测驱动的改动): take 是**默认动作**, 而未 action=start 时内核只回一句英文
                //   "Precise coverage has not been started."。上一轮只把这句改写得更可行动, 但台账里
                //   它仍是一条**前置缺失类失败**(与"前置缺失类失败=0"的目标冲突)。
                //   现改为**自动补前置**: 未开启时自动 Profiler.enable + startPreciseCoverage 再取一次,
                //   并经 auto_prepared 如实上报补过什么 —— 与项目既有的"反应式补域"同一思路。
                变量 pcTake <类型 = 文本型>
                pcTake = MCP命令服务器.执行CDP并同步等待 (命令ID + "_tk", "Profiler.takePreciseCoverage", "{}", 15000)
                如果 (MCP命令服务器.CDP同步结果是否成功 (pcTake) == 假)
                {
                    变量 pcTakeErr <类型 = 文本型>
                    pcTakeErr = MCP命令服务器.取CDP同步结果错误 (pcTake)
                    如果 (寻找文本 (pcTakeErr, "has not been started", 0, 假) == -1)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "取精确覆盖率失败: " + pcTakeErr))
                    }
                    MCP_响应构建.记录自动处理 ("browser_reverse_precise_coverage: 精确覆盖率尚未开启, 已自动 Profiler.enable + startPreciseCoverage 并重新取数")
                    执行CDP并同步等待 (命令ID + "_en2", "Profiler.enable", "{}", 15000)
                    执行CDP并同步等待 (命令ID + "_st2", "Profiler.startPreciseCoverage", "{@Q@callCount@Q@:true,@Q@detailed@Q@:true,@Q@allowTriggeredUpdates@Q@:false}", 15000)
                    pcTake = MCP命令服务器.执行CDP并同步等待 (命令ID + "_tk2", "Profiler.takePreciseCoverage", "{}", 15000)
                    如果 (MCP命令服务器.CDP同步结果是否成功 (pcTake) == 假)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "已自动开启精确覆盖率但取数仍失败: " + MCP命令服务器.取CDP同步结果错误 (pcTake)))
                    }
                }
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, pcTake))
            }'''.replace('@Q@', chr(92) + chr(34))


def main():
    t = io.open(REV, encoding='utf-8', newline='').read()
    # ★ 本文件是 CRLF 行尾; 用 newline='' 读进来后必须按 \r\n 匹配多行锚点
    #   (第一次写成 \n 导致锚点 0 命中 —— 之前对该文件的改动都是单行片段, 所以没暴露这个问题)。
    crlf = '\r\n' in t
    old = OLD.replace('\n', '\r\n') if crlf else OLD
    new = NEW.replace('\n', '\r\n') if crlf else NEW
    n = t.count(old)
    print("[锚点] take 分支出现 %d 次 (文件 CRLF=%s)" % (n, crlf))
    if n != 1:
        print("  !! 预期 1 次, 中止")
        print("  锚点片段: %r" % old[:120])
        return 1
    if 'pcTakeErr' in t:
        print("  !! 似乎已改过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(REV, os.path.join(BAK, os.path.basename(REV)))
    print("已备份到 %s" % BAK)
    io.open(REV, 'w', encoding='utf-8', newline='').write(t.replace(old, new))
    print("OK: take 已改为自动补前置")
    raw = io.open(REV, 'rb').read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
