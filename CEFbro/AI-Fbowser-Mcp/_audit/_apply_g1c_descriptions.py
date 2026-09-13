# -*- coding: utf-8 -*-
r"""G1c 收尾: 把 21 个 DOM/填表工具的 frame_id 说明改成**与实现一致**的版本。

背景: 这些工具的 frame_id 说明此前写着"原生填表路径支持子框架, 但走 CDP JS 的**读取类**工具仍在主框架求值 ——
读 iframe 内容请走 CDP: Page.getFrameTree -> createIsolatedWorld -> Runtime.evaluate"。
G1c 落地后读取类工具**已经**支持 frame_id(走 CDP 隔离世界), 该说明既过时又误导(会把 AI 引向手写 CDP 三步)。
新说明必须同时讲清两件事: ①现在支持 frame_id; ②隔离世界的边界(页面在该框架挂的全局变量不可见)与替代入口
(browser_execute_js {frame_id, world:main})。

安全: 只改 `添加工具JSON (` 行内 `属性项JSON ("frame_id", "text", "…")` 的第三段; 断言行数/括号净额不变。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

PAT = re.compile(r'属性项JSON \("frame_id", "text", "([^"]*)"\)')
NEW_DESC = ('iframe 的框架ID(取自 browser_get_frames 的 id, 形如 6-XXXX) / 框架名 / 序号(0=主框架); '
            '省略=主框架。给 frame_id 时本工具在该 **iframe 内**定位(走 CDP 隔离世界: DOM 可达, '
            '但**页面在该框架里挂的全局变量/函数不可见** —— 需要它们请用 browser_execute_js {frame_id, world:main}); '
            '框架不存在会**明确报错**, 不会静默改到主框架操作')


def bal(lines, ch_open, ch_close):
    n = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
            continue
        k = 0
        in_str = False
        while k < len(ln):
            c = ln[k]
            if in_str:
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == ch_open:
                    n += 1
                elif c == ch_close:
                    n -= 1
            k += 1
    return n


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')

    hits = []
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('添加工具JSON (') and '属性项JSON ("frame_id", "text"' in ln:
            hits.append(i)
    names = [re.search(r'添加工具JSON \("([^"]+)"', lines[i]).group(1) for i in hits]
    print('命中 %d 行带 frame_id 的注册行: %s' % (len(hits), ', '.join(names)))
    # 排除三类**语义不同**的 frame_id(不能套用 DOM/填表族的措辞, 否则是另一种误导):
    #   browser_execute_js          —— 它讲的是 world(隔离世界/页面主世界)语义
    #   browser_frame_by_id         —— frame_id 就是它要查的那个键本身, 不是"在框架内定位"
    #   browser_vip_execute_js_context —— 它有自己的 target/frame_index/context_id 选择语义
    SKIP = ('browser_execute_js', 'browser_frame_by_id', 'browser_vip_execute_js_context')
    hits = [i for i in hits if re.search(r'添加工具JSON \("([^"]+)"', lines[i]).group(1) not in SKIP]
    print('排除 %s 后, 本次要改 %d 行' % ('/'.join(SKIP), len(hits)))
    # 23 = 21 个 DOM/填表工具 + 本次新收 frame_id 的 browser_fill_get_text / browser_fill_set_text
    assert len(hits) == 23, '期望 23 行, 实得 %d' % len(hits)

    for i in hits:
        m = PAT.search(lines[i])
        assert m, '第 %d 行未匹配到 frame_id 属性段' % (i + 1)
        old, new = m.group(1), NEW_DESC
        tool = re.search(r'添加工具JSON \("([^"]+)"', lines[i]).group(1)
        print('   %-34s %5d  旧 %d 字 -> 新 %d 字' % (tool, i + 1, len(old), len(new)))
        lines[i] = PAT.sub(lambda _m: '属性项JSON ("frame_id", "text", "%s")' % new, lines[i], count=1)

    after = [re.search(r'添加工具JSON \("([^"]+)"', lines[i]).group(1) for i in hits]
    assert len(set(after)) == len(hits), '工具名有重复: %s' % after
    assert all(NEW_DESC in lines[i] for i in hits), '有行未替换成功'

    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines))
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘; 行数不变=%s, 花括号净额不变=%s'
              % (len(lines), bal(lines, '{', '}') == 0))
        print('提示: 加 --apply 落盘')


main()
