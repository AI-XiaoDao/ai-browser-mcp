# -*- coding: utf-8 -*-
r"""G5「下载完成信息缺失」静态补丁脚本 —— 只改 src/MCP_BrowserEvents.wsv 一个文件。

== 事实基础 (纯静态核对; 本脚本不编译、不运行 exe、不调 MCP 接口) ==
类库 `类_FBrowser_下载` (FBroLib.wsv:3626, 注释 CefDownloadItem, 输出名 FBroDownloadItem) 共 18 个方法,
其中下列方法在本项目 src/*.wsv 里 **0 引用** (grep 实证):
  是否已下载完成 (IsComplete)         FBroLib.wsv:3658   0 引用
  是否已取消     (IsCanceled)         FBroLib.wsv:3663   0 引用
  取现行下载速度 (GetCurrentSpeed)    FBroLib.wsv:3668   0 引用
  取存储位置     (GetFullPath)        FBroLib.wsv:3710   0 引用
  取原始地址     (GetOriginalUrl)     FBroLib.wsv:3729   0 引用
  取内容描述     (GetContentDisposition) FBroLib.wsv:3743 0 引用
  取MIME类型     (GetDownloadMimeType)   FBroLib.wsv:3750 0 引用
  取开始时间 / 取结束时间              FBroLib.wsv:3688 / 3699  0 引用
  (注: 任务书里猜的「取总字节/取已接收字节/取当前速度/取建议文件名/取下载ID/是否可继续」在类库中
   实际叫 取总长度(3678) / 取已下载长度(3683) / 取现行下载速度(3668) / 取推荐文件名(3736) /
   取关联标识符(3717); 类库**没有**「是否可继续」, 只有 是否仍在下载中(3653)。)
后果 (G5): CEF OnDownloadUpdated 的**终态** (is_complete / is_canceled) 从未被消费 ——
`下载进度` 只在 0/25/50/75/100 里程碑写一条 {filename,percent,received_bytes,total_bytes},
既无 download_id / url / speed, 更**永远没有落盘路径**; 客户端无法回答"下完了没有、文件存到哪"。

== 本补丁 (复用既有事件通道, 不新增工具、不新增事件族、不动 AddTool 注册) ==
  E1 `浏览器_正在下载` → download_progress 载荷 += download_id / url / speed
  E2 `浏览器_正在下载` → 新增终态分支 → download_complete | download_canceled
     (载荷含 saved_path = 取存储位置, 及 total/received/mime/content_disposition/start_time/end_time)
  E3 `浏览器_即将下载` → download_start 载荷 += download_id / url / original_url / mime / content_disposition
download_* 族已由 browser_collect action=event_download_enable 控制 (默认开: MCP_Server.wsv:513),
且 browser_event 查 event_log 时含 * 的族名走 LIKE (MCP_Server.wsv:5045-5059), 因此新事件名
download_complete / download_canceled 无需任何注册即可被 `browser_event {event_type:"download_*"}` 查到。

== 安全 ==
  * 唯一锚点子串定位 (不含行尾空白, 免疫行号漂移), 每处替换前断言锚点恰好出现 1 次, 否则报错退出。
  * 默认 dry-run, 只有 --apply 才落盘; 写盘 UTF-8 无 BOM + LF (io.open newline='\n')。
  * 断言: 行数增量 == 预期; 字符串/注释之外的 { } 净额不变、( ) 净额不变 (且开/闭增量成对);
    代码区花括号深度在锚点处前后一致; 新增行缩进与插入点同级语句一致; 结构锚计数不变; 原有非空行零丢失。
  * 幂等: 检测到本次新增的哨兵文本 → 直接报错退出, 绝不重复插入。
"""
import io
import os
import sys
import difflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401  导入即把 stdout/stderr 切成 UTF-8(errors=replace)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_REL = os.path.join('src', 'MCP_BrowserEvents.wsv')
TARGET = os.path.join(ROOT, TARGET_REL)

# ---------------------------------------------------------------- 锚点与新增代码
A1 = '                进度数据.加入长整数成员 ("total_bytes", 下载.取总长度 ())'
A2 = '            // 内核层: 消费 browser_kernel_download 待执行操作 (pause/resume/cancel), 事件内即时执行'
A3 = '            下载数据.加入长整数成员 ("total_bytes", 下载.取总长度 ())'

E1_LINES = [
    '                进度数据.加入整数成员 ("download_id", 下载.取关联标识符 ())',
    '                进度数据.加入文本成员 ("url", 下载.取地址 ())',
    '                进度数据.加入长整数成员 ("speed", 下载.取现行下载速度 ())',
]

E2_LINES = [
    '            // G5: 下载终态上报 —— 此前仅按里程碑百分比写 download_progress, 完成后客户端拿不到落盘路径',
    '            如果 (下载.是否已下载完成 () || 下载.是否已取消 ())',
    '            {',
    '                变量 终态数据 <类型 = YYJSON对象类>',
    '                终态数据.创建自文本 ("{}")',
    '                终态数据.加入整数成员 ("download_id", 下载.取关联标识符 ())',
    '                终态数据.加入文本成员 ("filename", 下载.取推荐文件名 ())',
    '                终态数据.加入文本成员 ("url", 下载.取地址 ())',
    '                终态数据.加入文本成员 ("original_url", 下载.取原始地址 ())',
    '                终态数据.加入长整数成员 ("total_bytes", 下载.取总长度 ())',
    '                终态数据.加入长整数成员 ("received_bytes", 下载.取已下载长度 ())',
    '                终态数据.加入文本成员 ("mime", 下载.取MIME类型 ())',
    '                终态数据.加入文本成员 ("content_disposition", 下载.取内容描述 ())',
    '                终态数据.加入文本成员 ("saved_path", 下载.取存储位置 ())',
    '                终态数据.加入文本成员 ("start_time", 下载.取开始时间 ())',
    '                终态数据.加入文本成员 ("end_time", 下载.取结束时间 ())',
    '                变量 终态类型 <类型 = 文本型>',
    '                终态类型 = "download_complete"',
    '                如果 (下载.是否已取消 ())',
    '                {',
    '                    终态类型 = "download_canceled"',
    '                }',
    '                终态数据.加入逻辑值成员 ("completed", 下载.是否已下载完成 ())',
    '                终态数据.加入逻辑值成员 ("canceled", 下载.是否已取消 ())',
    '                控制台输出 (到文本 ("[MCP] 下载终态:") + 终态类型 + " " + 下载.取存储位置 ())',
    '                记录监控事件 (MCP命令服务器.是否监控下载事件, 终态类型, 浏览器.取ID (), 终态数据.到可读文本 (YYJSON格式化选项.压缩))',
    '            }',
]

E3_LINES = [
    '            下载数据.加入整数成员 ("download_id", 下载.取关联标识符 ())',
    '            下载数据.加入文本成员 ("url", 下载.取地址 ())',
    '            下载数据.加入文本成员 ("original_url", 下载.取原始地址 ())',
    '            下载数据.加入文本成员 ("mime", 下载.取MIME类型 ())',
    '            下载数据.加入文本成员 ("content_disposition", 下载.取内容描述 ())',
]

# mode='after' → 锚点之后插入; mode='before' → 锚点之前插入 (两种都保持"语句间空一行"的既有排版)
# probe: 用于核对"花括号深度没被这段插入改动"的**代码行**(锚点本身是代码行就直接用它;
#        E2 的锚点是一条 // 注释(不计深度), 故改用紧随其后的同级代码行 变量 内核下载动作)。
EDITS = [
    dict(tag='E1', mode='after', anchor=A1, lines=E1_LINES, probe=A1,
         why='download_progress 载荷增补 download_id/url/speed'),
    dict(tag='E2', mode='before', anchor=A2, lines=E2_LINES,
         probe='            变量 内核下载动作 <类型 = 文本型>',
         why='新增下载终态分支 download_complete/download_canceled (含 saved_path 落盘路径)'),
    dict(tag='E3', mode='after', anchor=A3, lines=E3_LINES, probe=A3,
         why='download_start 载荷增补 download_id/url/original_url/mime/content_disposition'),
]

# 幂等哨兵: 这些文本只在"本次补丁已落盘"之后才存在于文件里
SENTINELS = [
    '"speed", 下载.取现行下载速度',
    '终态数据.加入文本成员 ("saved_path"',
    '"content_disposition", 下载.取内容描述 ()',
]

OB, CB, OP, CP = '{', '}', '(', ')'


def code_chars(text):
    """逐行产出 (行号, 代码字符及其列号): 跳过 '@'/'#'/'//' 整行, 跳过字符串字面量与行尾 // 注释。

    火山 .wsv 里 '@' 开头是嵌入式 C++、'#' 开头是文档/包含块注释、'//' 是代码注释,
    而字符串字面量里也可能出现 {}() (例如 创建自文本 ("{}")) —— 三者都不能计入。
    """
    for idx, line in enumerate(text.split('\n')):
        st = line.lstrip()
        if st.startswith('@') or st.startswith('#') or st.startswith('//'):
            continue
        in_str = False
        k = 0
        n = len(line)
        while k < n:
            c = line[k]
            if in_str:
                if c == '\\':          # 火山源码里的 \" 转义: 跳过两个字符
                    k += 2
                    continue
                if c == '"':
                    in_str = False
                k += 1
                continue
            if c == '"':
                in_str = True
                k += 1
                continue
            if c == '/' and k + 1 < n and line[k + 1] == '/':
                break                  # 行尾注释, 本行到此为止
            yield idx, k, c
            k += 1


def count_symbols(text):
    counts = {OB: 0, CB: 0, OP: 0, CP: 0}
    for _idx, _col, c in code_chars(text):
        if c in counts:
            counts[c] += 1
    return counts


def line_depths(text, ch_open=OB, ch_close=CB):
    """返回"每行行首的花括号深度"(只看代码区)。"""
    depths = []
    depth = 0
    per_line = {}
    for idx, _col, c in code_chars(text):
        per_line.setdefault(idx, depth)
        if c == ch_open:
            depth += 1
        elif c == ch_close:
            depth -= 1
    for idx in range(len(text.split('\n'))):
        depths.append(per_line.get(idx))
    return depths


def line_of(text, needle):
    for i, ln in enumerate(text.split('\n')):
        if needle in ln:
            return i
    return -1


def show_region(text, needle, ins_set, before=2, after=3, width=112):
    lines = text.split('\n')
    i = line_of(text, needle)
    if i < 0:
        print('      (结果中未找到 %r)' % needle)
        return
    for no in range(max(0, i - before), min(len(lines), i + after + 1)):
        ln = lines[no]
        mark = '>>' if needle in ln else ('++' if ln in ins_set else '  ')
        print('      %s %5d| %s' % (mark, no + 1, ln if len(ln) <= width else ln[:width] + ' …'))


def build_insert(spec):
    """返回 (拼进文件的字面量, 预期新增换行数)。"""
    body = '\n\n'.join(spec['lines'])
    blk = ('\n\n' + body) if spec['mode'] == 'after' else (body + '\n\n')
    return blk, blk.count('\n')


def main():
    apply = '--apply' in sys.argv
    ok = True

    raw = open(TARGET, 'rb').read()
    print('目标文件 : %s' % TARGET_REL)
    print('原始大小 : %d 字节' % len(raw))
    if raw.startswith(b'\xef\xbb\xbf'):
        print('!! 文件带 UTF-8 BOM, 本脚本拒绝处理 (避免静默转码)')
        return 2
    if b'\r' in raw:
        print('!! 文件含 CR 字符 %d 个 (非纯 LF), 按 newline=\'\\n\' 落盘会静默改换行符 —— 拒绝处理'
              % raw.count(b'\r'))
        return 2

    text = raw.decode('utf-8')
    old_lines = text.split('\n')
    print('原始行数 : %d  (LF=%d, CR=0, 末尾有换行=%s)'
          % (len(old_lines), text.count('\n'), text.endswith('\n')))
    print('原始代码区符号计数 : %s' % count_symbols(text))
    _depths = line_depths(text)
    _code_depths = [d for d in _depths if d is not None]
    print('原始代码区花括号深度 : 首行代码深度=%d, 末行代码深度=%d (全文件 {} 净额=%d)'
          % (_code_depths[0], _code_depths[-1], count_symbols(text)[OB] - count_symbols(text)[CB]))

    # ---- 幂等闸门
    for s in SENTINELS:
        if s in text:
            print('!! 已检测到本次补丁的哨兵文本 %r —— 疑似已落盘, 拒绝重复插入' % s)
            return 3

    # ---- 锚点唯一性 (全部先校验, 任一处 != 1 立即退出, 绝不"尽量替换")
    print('\n=== 锚点唯一性校验 (必须每处恰好 1 次) ===')
    for spec in EDITS:
        cnt = text.count(spec['anchor'])
        good = (cnt == 1)
        print('  [%s] 出现 %d 次  %s' % (spec['tag'], cnt, 'OK' if good else '<<< 不合格'))
        print('        锚点 = %r' % spec['anchor'])
        ok &= good
    if not ok:
        print('!! 有锚点匹配数 != 1, 立即退出 (不做任何替换)')
        return 4

    # ---- 统一替换
    print('\n=== 逐处改动 ===')
    new_text = text
    expected_delta = 0
    for spec in EDITS:
        blk, add_nl = build_insert(spec)
        expected_delta += add_nl
        if spec['mode'] == 'after':
            new_text = new_text.replace(spec['anchor'], spec['anchor'] + blk, 1)
        else:
            new_text = new_text.replace(spec['anchor'], blk + spec['anchor'], 1)
        print('\n  [%s] %s' % (spec['tag'], spec['why']))
        print('      文件   : %s' % TARGET_REL)
        print('      锚点   : %r' % spec['anchor'])
        print('      旧文本 : 锚点所在行原样保留; 仅在其%s插入 %d 行 (语句间空一行, 与原排版一致)'
              % ('之后' if spec['mode'] == 'after' else '之前', len(spec['lines'])))
        print('      新文本 : 在锚点%s插入 ↓' % ('之后' if spec['mode'] == 'after' else '之前'))
        for ln in spec['lines']:
            print('               + %s' % ln)
        print('      预期行数增量: +%d (= 新增 %d 个换行)' % (add_nl, add_nl))

    # ================= 断言 =================
    print('\n=== 断言 ===')
    new_lines = new_text.split('\n')

    delta = len(new_lines) - len(old_lines)
    a_ok = (delta == expected_delta)
    print('  [%s] 整文件行数增量 实际 %+d == 预期 %+d' % ('OK' if a_ok else 'FAIL', delta, expected_delta))
    ok &= a_ok

    cs_old, cs_new = count_symbols(text), count_symbols(new_text)
    print('  [信息] 代码区符号计数 旧 %s -> 新 %s' % (cs_old, cs_new))
    for name, o, c in (('花括号', OB, CB), ('圆括号', OP, CP)):
        pair = (cs_new[o] - cs_old[o]) == (cs_new[c] - cs_old[c])
        print('  [%s] 代码区%s开/闭增量成对: %+d / %+d'
              % ('OK' if pair else 'FAIL', name, cs_new[o] - cs_old[o], cs_new[c] - cs_old[c]))
        ok &= pair
        no, nn = cs_old[o] - cs_old[c], cs_new[o] - cs_new[c]
        same = (no == nn)
        print('  [%s] 代码区%s净额不变: %d -> %d' % ('OK' if same else 'FAIL', name, no, nn))
        ok &= same

    d_old, d_new = line_depths(text), line_depths(new_text)
    for spec in EDITS:
        i_old, i_new = line_of(text, spec['probe']), line_of(new_text, spec['probe'])
        same = (i_old >= 0 and i_new >= 0 and d_old[i_old] == d_new[i_new])
        print('  [%s] [%s] 深度探针行首花括号深度不变: 旧行%d=%s -> 新行%d=%s (%r)'
              % ('OK' if same else 'FAIL', spec['tag'], i_old + 1, d_old[i_old], i_new + 1,
                 d_new[i_new], spec['probe'].strip()))
        ok &= same

    for spec in EDITS:
        ind_anchor = len(spec['anchor']) - len(spec['anchor'].lstrip(' '))
        inds = [len(ln) - len(ln.lstrip(' ')) for ln in spec['lines']]
        if spec['mode'] == 'after':
            # 锚点之后插入: 全部新增行都应是与锚点同级的**语句**, 缩进必须与锚点一致
            same = all(b == ind_anchor for b in inds)
        else:
            # 锚点之前插入: 注释行 / 首条语句 / 语句的 {  / 收口的 } 必须与锚点同级, 块体必须更深
            same = (inds[0] == ind_anchor and inds[1] == ind_anchor and inds[2] == ind_anchor
                    and inds[-1] == ind_anchor and all(b > ind_anchor for b in inds[3:-1]))
        print('  [%s] [%s] 新增行缩进合规 (锚点同级缩进=%d 空格): %s'
              % ('OK' if same else 'FAIL', spec['tag'], ind_anchor, inds))
        ok &= same

    for needle, want in (('方法 浏览器_正在下载', 1), ('方法 浏览器_即将下载', 1),
                         ('类 类_MCP_浏览器事件', 1), ('方法 记录监控事件', 1),
                         ('记录监控事件 (真, "download_progress"', 1)):
        got = new_text.count(needle)
        same = (got == want)
        print('  [%s] 结构锚 %r 计数 %d (期望 %d)' % ('OK' if same else 'FAIL', needle, got, want))
        ok &= same

    lost = [ln for ln in old_lines if ln.strip() and ln not in new_lines]
    print('  [%s] 原有非空行丢失数 %d' % ('OK' if not lost else 'FAIL', len(lost)))
    ok &= (not lost)
    for spec in EDITS:
        for ln in spec['lines']:
            if ln not in new_text:
                print('  [FAIL] 新行未落入结果: %r' % ln)
                ok = False

    # ---- 落点实况 + diff
    print('\n=== 改动落点实况 (结果文件真实行号; >> = 锚点行, ++ = 本次新增) ===')
    for spec in EDITS:
        print('\n  [%s] %s' % (spec['tag'], spec['why']))
        show_region(new_text, spec['anchor'], set(spec['lines']))

    print('\n=== 变更预览 (unified diff 上下文 2 行; difflib 可能把重复的 } 对齐到别处, 以上面实况为准) ===')
    for ln in list(difflib.unified_diff(old_lines, new_lines, fromfile=TARGET_REL + ' (旧)',
                                        tofile=TARGET_REL + ' (新)', n=2, lineterm=''))[:400]:
        print('  ' + ln)

    if not ok:
        print('\n!! 断言未全过, 不落盘')
        return 5

    if apply:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_text)
        raw2 = open(TARGET, 'rb').read()
        print('\n已写入 %s' % TARGET_REL)
        print('落盘 %d 字节 | 末尾有换行=%s | 含 BOM=%s | 含 CR=%s'
              % (len(raw2), raw2.endswith(b'\n'), raw2.startswith(b'\xef\xbb\xbf'), b'\r' in raw2))
        print('落盘后行数 %d' % len(raw2.decode('utf-8').split('\n')))
    else:
        print('\n[dry-run] 未落盘 —— %d 处锚点均唯一, 断言全过' % len(EDITS))
        print('提示: 加 --apply 落盘')
    return 0


sys.exit(main())
