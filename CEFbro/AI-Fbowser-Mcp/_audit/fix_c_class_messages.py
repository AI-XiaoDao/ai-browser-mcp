# -*- coding: utf-8 -*-
"""收口 C 类缺陷的其余部分 + 又两处"GUI管理"错误前提(诚实性)。

 ① browser_reverse_precise_coverage: 默认动作 take 落在未开启的前置上, 而 `has not been started`
    **不匹配** 执行V8CDP命令 的改写分支(只认 not enabled / Agent is not / Debugger is not)
    -> 英文原文裸透传, 调用方看不到"先 action=start"的指引。本轮补一个专门分支。
 ② browser_find_by_tag 的消息: 它说"该标识未被 browser_user_tags **设置过**"—— 把**只读**工具当写工具。
    本轮已把"创建时设置标识"的通路补齐(browser_create 的 tag 参数), 消息改为指向真正的设置方式。
 ③ browser_find_by_hwnd 的消息: 只有一句"未找到窗口句柄为 N 的浏览器", 零提示;
    而项目明明有 browser_get_window_handle。补上取得方式与替代。
 ④ MCP_Server_System.wsv 里还有**两处**"GUI窗口自动管理浏览器实例"——与 §96.2 已推翻的前提同源
    (本项目是控制台程序、无 GUI)。改为如实说明"本工具刻意不实现", 不再拿不存在的东西当理由。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
SYS = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')
BAK = os.path.join(ROOT, '备份', 'C类缺陷收口-写入前')

EDITS = [
    # ① precise_coverage: 给 "has not been started" 专门的可行动分支
    ('REV 覆盖率前置指引', REV,
     '            如果 (寻找文本 (v8Err, "not enabled", 0, 假) != -1 || 寻找文本 (v8Err, "Agent is not", 0, 假) != -1 || 寻找文本 (v8Err, "Debugger is not", 0, 假) != -1)',
     '\n'.join([
         '            // ★ 加: "精确覆盖率尚未开启" 原先落到下面的裸透传(英文原文, 调用方看不出下一步)。',
         '            //   它与 "域未启用" 是同一类"缺前置", 故给同样风格的可行动分支。',
         '            如果 (寻找文本 (v8Err, "has not been started", 0, 假) != -1)',
         '            {',
         '                返回 (MCP_响应构建.命令失败 (命令ID, CDP方法名 + " 失败: " + v8Err + " | 该能力需要先开启: 请先调 browser_reverse_precise_coverage action=start, 触发目标逻辑后再 action=take 取数"))',
         '            }',
         '            如果 (寻找文本 (v8Err, "not enabled", 0, 假) != -1 || 寻找文本 (v8Err, "Agent is not", 0, 假) != -1 || 寻找文本 (v8Err, "Debugger is not", 0, 假) != -1)',
     ])),

    # ② find_by_tag: 指向真正的设置方式(本轮新加的创建时 tag 参数)
    ('CORE find_by_tag 消息', CORE,
     '返回 (MCP_响应构建.命令失败 (命令ID, "未找到标识为: " + tag + " 的浏览器 | 可能原因: 该标识未被 browser_user_tags 设置过, 或浏览器已关闭 | 建议: 先用 browser_list 查看现有浏览器及其 id"))',
     '返回 (MCP_响应构建.命令失败 (命令ID, "未找到标识为: " + tag + " 的浏览器 | 设置方式: 用户标识**只能在创建浏览器时**指定(类库不支持运行期设置), 即 browser_create {url:…, tag:\"你的标识\"} | browser_user_tags 是**只读**的标识清单(旧文案说它「设置」标识, 与事实不符, 已更正) | 也可能该浏览器已关闭 | 可行动: 先 browser_user_tags 看现有标识, 或 browser_list 按 id 定位"))'),

    # ③ find_by_hwnd: 补取得方式与替代
    ('CORE find_by_hwnd 消息', CORE,
     '返回 (MCP_响应构建.命令失败 (命令ID, "未找到窗口句柄为 " + 到文本 (hwnd) + " 的浏览器"))',
     '返回 (MCP_响应构建.命令失败 (命令ID, "未找到窗口句柄为 " + 到文本 (hwnd) + " 的浏览器 | 如何取得有效句柄: 调 browser_get_window_handle(返回当前浏览器窗口句柄) 或 browser_window_info 看 hwnd 字段; 句柄是**运行时值**(每次启动不同), 无法预先写死 | 也可改用 browser_list(列 id) 或 browser_find_by_tag(按标识) 定位"))'),

    # ④ 两处"GUI管理"错误前提
    ('SYS create_tab 理由', SYS,
     '原因: GUI窗口自动管理浏览器实例, 无需手动创建标签页',
     '原因: 本工具**刻意不实现**(项目未开放远程建标签页入口) —— 旧文案称"GUI窗口自动管理浏览器实例", 而本项目是控制台程序、并无 GUI 管理窗口(该前提已按代码事实推翻), 故不再拿不存在的东西当理由'),
    ('SYS task_runner 理由', SYS,
     '原因: GUI窗口自动管理浏览器实例 |',
     '原因: 本工具**刻意不实现**(项目未开放该入口; 旧文案称"GUI窗口自动管理浏览器实例"与代码事实不符, 已更正) |'),
]


def main():
    texts = {p: io.open(p, encoding='utf-8', newline='').read() for p in (CORE, REV, SYS)}
    for label, path, old, new in EDITS:
        n = texts[path].count(old)
        print("[%-20s] %s 出现 %d 次" % (label, os.path.basename(path), n))
        if n != 1:
            print("   !! 预期 1 次, 中止(不改任何文件)")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (CORE, REV, SYS):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    for label, path, old, new in EDITS:
        texts[path] = texts[path].replace(old, new)
    for p, t in texts.items():
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print("OK: %d 处替换完成" % len(EDITS))
    for p in (CORE, REV, SYS):
        raw = io.open(p, 'rb').read()
        print("复核 %-24s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
