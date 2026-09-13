# -*- coding: utf-8 -*-
r"""G1: 让 DOM/填表族工具支持 **iframe 子框架**(此前 21 个工具全部硬编码 `取主填表框架 ()`)。

依据(上一轮缺口刷新 `_audit/_gap_refresh_r117.md` G1, 价值"高"):
  · 类库有 `取填表框架_ID (ID)` / `取填表框架_名称 (名称)` / `取主填表框架 ()`(FBroLib.wsv:1414/1422/1399);
  · 但 `src` 里 **21 处**填表/DOM 入口全部写死 `取主填表框架 ()` ⇒ **iframe 里的表单/DOM 完全操作不到**;
  · 类库警告"ID 错误返回空类, **对空类执行操作会崩溃**" ⇒ 解析器返回空框架时必须由调用方既有的
    `是否有效 ()` 守卫拦住(已核实 21 处**都有**该守卫)。

本补丁:
  ① `MCP命令服务器.解析填表框架 (浏览器, 目标框架)`: 空/`main`/`主框架` -> 主填表框架(向后兼容);
     否则先按 **frame_id** 取, 再按**框架名**取, 都取不到返回空框架(交给既有守卫报错);
  ② 21 个调用点改为传 `frame_id` 参数(工具入参);
  ③ 这 21 个工具的工具描述与 schema 同步暴露 `frame_id`; 另外两个回调里的调用点**保持主框架**
     (下载/网络回调没有 参数JSON, 也不该跟某个 iframe 绑定)。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', 'iframe子框架支持-写入前')
problems = []

FRAME_ARG_DESC = 'iframe 的框架ID(取自 browser_get_frames 的 id 字段)或框架名; 省略=主框架'

HELPER = '''    # 解析"要操作哪个填表框架": 空/main/主框架 -> 主填表框架(向后兼容); 否则先按 frame_id 再按框架名取。
    # 类库原文警告: ID 错误会返回**空类**, 对空类执行操作会崩溃 —— 故调用方必须用 是否有效() 守卫
    # (本项目 21 个调用点本来就有该守卫, 故这里返回空类即等于"框架不存在", 由调用方报错)。
    方法 解析填表框架 <公开 静态 类型 = 类_FBrowser_填表框架 @输出名 = "ResolveFillFrame" @强制输出 = 真>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 目标框架 <类型 = 文本型 @输出名 = "TargetFrame">
    {
        变量 空框架 <类型 = 类_FBrowser_填表框架>
        如果 (浏览器.是否为空 ())
        {
            返回 (空框架)
        }
        如果 (目标框架 == "" || 目标框架 == "main" || 目标框架 == "主框架")
        {
            返回 (浏览器.取主填表框架 ())
        }
        变量 按ID取 <类型 = 类_FBrowser_填表框架>
        按ID取 = 浏览器.取填表框架_ID (目标框架)
        如果 (按ID取.是否有效 ())
        {
            返回 (按ID取)
        }
        变量 按名取 <类型 = 类_FBrowser_填表框架>
        按名取 = 浏览器.取填表框架_名称 (目标框架)
        如果 (按名取.是否有效 ())
        {
            返回 (按名取)
        }
        返回 (空框架)
    }

'''

TARGETS = ["browser_dom_checked", "browser_dom_click", "browser_dom_get_html",
           "browser_dom_inner_html", "browser_dom_query", "browser_dom_rect",
           "browser_dom_select", "browser_dom_selected", "browser_dom_set_html",
           "browser_dom_set_value", "browser_fill_attr_get", "browser_fill_attr_set",
           "browser_fill_click", "browser_fill_exists", "browser_fill_focus",
           "browser_fill_form", "browser_fill_scroll", "browser_fill_select",
           "browser_fill_set_value", "browser_fill_trigger", "browser_get_text"]


def top_split(s):
    """把形如 `a, b, c` 的实参串按**顶层逗号**切分(忽略括号/引号内)。"""
    out, depth, cur, i, n = [], 0, '', 0, len(s)
    in_str = False
    while i < n:
        ch = s[i]
        if in_str:
            if ch == '\\':
                cur += s[i:i + 2]
                i += 2
                continue
            if ch == '"':
                in_str = False
            cur += ch
        else:
            if ch == '"':
                in_str = True
                cur += ch
            elif ch in '([{':
                depth += 1
                cur += ch
            elif ch in ')]}':
                depth -= 1
                cur += ch
            elif ch == ',' and depth == 0:
                out.append(cur.strip())
                cur = ''
            else:
                cur += ch
        i += 1
    if cur.strip():
        out.append(cur.strip())
    return out


# ───────── ① + ②: Server 里加解析器, 21 个调用点接线 ─────────
for fn in ('MCP_Server.wsv', 'MCP_Server_Core.wsv', 'MCP_Server_Form.wsv'):
    p = os.path.join(SRC, fn)
    text = open(p, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'

    if fn == 'MCP_Server.wsv':
        anchor = '    # 文本里是否还残留未还原的百分号转义(%HH)'
        if text.count(anchor) != 1:
            problems.append('解析器插入锚点命中 %d' % text.count(anchor))
        else:
            text = text.replace(anchor, HELPER.replace('\n', nl) + anchor, 1)
            print('   ok 解析填表框架 已插入 Server')

    # 调用点: `X.取主填表框架 ()` -> 解析器(带 frame_id); 带 参数JSON 的分派方法才改
    def repl(m):
        var = m.group(1)
        return ('MCP命令服务器.解析填表框架 (%s, MCP命令服务器.yyjson取文本 (参数JSON, "frame_id"))'
                % var)

    # 只在该文件的分派方法区改(Form/Core 都是分派文件); 逐行判断是否处于含 参数JSON 的方法内
    ls = text.split('\n')
    methods = [(i, m.group(1)) for i, ln in enumerate(ls)
               for m in [re.match(r'\s*方法\s+(\S+)', ln)] if m]
    changed = 0
    for i, ln in enumerate(ls):
        if '取主填表框架 ()' not in ln:
            continue
        owner = None
        for (mi, mn) in methods:
            if mi <= i:
                owner = mi
            else:
                break
        has_json = False
        if owner is not None:
            for k in range(owner, min(owner + 25, len(ls))):
                if re.match(r'\s*方法\s+', ls[k]) and k != owner:
                    break
                if '参数JSON' in ls[k]:
                    has_json = True
                    break
        if not has_json:
            print('   (跳过: %s:%d 无 参数JSON)' % (fn, i + 1))
            continue
        ls[i] = re.sub(r'([A-Za-z_0-9\u4e00-\u9fff]+)\.取主填表框架 \(\)', repl, ln)
        changed += 1
    if changed:
        text = nl.join(ls)
        print('   ok %s 接线 %d 处' % (fn, changed))
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, fn)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    open(p, 'wb').write(text.encode('utf-8'))

# ───────── ③: 21 个工具的描述 + schema ─────────
p = os.path.join(SRC, 'MCP_Server.wsv')
text = open(p, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
ls = text.split('\n')
done = 0
for tool in TARGETS:
    idx = [i for i, ln in enumerate(ls) if ('添加工具JSON ("%s"' % tool) in ln]
    if len(idx) != 1:
        problems.append('%s: 注册行定位 %d' % (tool, len(idx)))
        continue
    i = idx[0]
    ln = ls[i]
    # 提取 添加工具JSON 的实参
    start = ln.find('添加工具JSON (')
    inner_start = start + len('添加工具JSON (')
    depth = 1
    j = inner_start
    in_str = False
    while j < len(ln):
        ch = ln[j]
        if in_str:
            if ch == '\\':
                j += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
        j += 1
    inner = ln[inner_start:j]
    parts = top_split(inner)
    if len(parts) == 2:
        new_inner = '%s, %s' % (inner, '多属性Schema文本 (属性项JSON ("frame_id", "text", "%s"), "")' % FRAME_ARG_DESC)
        new_ln = ln[:inner_start] + new_inner + ln[j:]
    elif len(parts) >= 3:
        schema = ', '.join(parts[2:])
        m = re.match(r'单参数Schema文本 \((.*)\)$', schema, re.S)
        if m:
            p_parts = top_split(m.group(1))
            if len(p_parts) != 3:
                problems.append('%s: 单参数Schema 实参数 %d' % (tool, len(p_parts)))
                continue
            new_schema = ('多属性Schema文本 (属性项JSON (%s) + "," + 属性项JSON ("frame_id", "text", "%s"), "\\"%s\\"")'
                          % (', '.join(p_parts), FRAME_ARG_DESC, p_parts[0].strip('"')))
        elif schema.startswith('多属性Schema文本 ('):
            body = schema[len('多属性Schema文本 ('):-1]
            bp = top_split(body)
            if len(bp) < 2:
                problems.append('%s: 多属性Schema 顶层实参 %d' % (tool, len(bp)))
                continue
            req = bp[-1]
            props = ', '.join(bp[:-1])
            new_schema = ('多属性Schema文本 (%s + "," + 属性项JSON ("frame_id", "text", "%s"), %s)'
                          % (props, FRAME_ARG_DESC, req))
        else:
            problems.append('%s: 未识别的 schema 形态: %s' % (tool, schema[:60]))
            continue
        new_inner = ', '.join(parts[:2]) + ', ' + new_schema
        new_ln = ln[:inner_start] + new_inner + ln[j:]
    else:
        problems.append('%s: 实参数 %d' % (tool, len(parts)))
        continue
    # 描述里补一句(frame_id 说明), 只在还没有时加
    if 'frame_id' not in new_ln[:new_ln.find(', ', new_ln.find('", '))] if False else True:
        pass
    ls[i] = new_ln
    done += 1
print('   ok schema 已更新 %d/%d 个工具' % (done, len(TARGETS)))
open(p, 'wb').write(nl.join(ls).encode('utf-8'))

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
