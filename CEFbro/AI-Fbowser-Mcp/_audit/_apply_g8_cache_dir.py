# -*- coding: utf-8 -*-
r"""G8 补丁: 缓存目录两个工具 (browser_cache_dir / browser_get_global_cache_dir)

== 审计结论(只读审计, 未编译未运行) ==

1) browser_get_global_cache_dir 的实现(MCP_Server_System.wsv:47-52)把缓存根目录**硬编码**为
   `取运行目录 () + "\CacheData\GlobalData"`; 而 main.wsv:84-91 启动时按 `MCPStdio桥.是否为Stdio模式 ()`
   分流写入 `设置.缓存目录`: stdio 模式 = `CacheData\GlobalData_Stdio`, 常驻 HTTP = `CacheData\GlobalData`。
   => 在 --mcp-stdio / --stdio / --headless 分支下, 该工具返回的路径与真实缓存目录**必然不一致**
      (实证: 运行目录 \CacheData 下 GlobalData 与 GlobalData_Stdio 两个真实目录同时存在)。

2) 类库侧的真值读取器(无需拼路径): `FBrowser初始化控制.FBrowser_取初始化缓存目录 ()`
   (FBroLib.wsv:252, `方法 FBrowser_取初始化缓存目录 <公开 静态 类型 = 文本型 ...>`, 无参数)
   -> 内部调 `FBroHsGetSetCachePath()`。已从 FBrowserCEF3lib.dll 导出表确认该 C 函数**无参数**
   (`?FBroHsGetSetCachePath@@YA?AV?$scoped_refptr@VFBroString@@@@XZ`, 末尾 XZ = 无参), 故是纯读取器,
   返回的正是初始化时 `设置.缓存目录` 的真实值(自动覆盖两条分支)。
   本补丁用**不带类名前缀**的写法, 与 main.wsv:103 `FBrowser_初始化 (...)` 同款: 两者同属 FBroLib.wsv 的
   `类 FBrowser初始化控制`(行 14~266), 该项目已在用该写法。

3) browser_cache_dir 的**类库 API 用法无需改动**(主代理怀疑的"用错类库 API"未获证实):
   `browser.取请求环境 ().取缓存路径 ()` 走的正是 `类_FBrowser_请求环境.取缓存路径`(FBroLib.wsv:2045
   -> FBroHsRequestContext_GetCachePath -> CefRequestContext::GetCachePath), 语义正确; 且项目从不创建
   独立请求环境(main.wsv:233 创建浏览器时省略第 4 参数 请求环境, 即全局请求环境)。
   近名 API 有两个陷阱, 但代码都没踩: `FBrowser_请求环境_取全局`(FBroLib.wsv:1994, 静态取全局请求环境)、
   `FBrowser_取初始化缓存目录`(FBroLib.wsv:252, 取进程级缓存目录)。
   => 只改**说明文案**与实际语义对齐, 不动逻辑。

== 本补丁 3 处(每个锚点必须恰好命中 1 次) ==
   P1  src/MCP_Server_System.wsv  取类库真值 + 回传来源(不再把硬编码路径当事实)   行数 +24
   P2  src/MCP_Server.wsv         browser_get_global_cache_dir 描述               行数 0
   P3  src/MCP_Server.wsv         browser_cache_dir 描述                         行数 0

== 换行与编码(重要) ==
   本脚本**不假设 LF**: `src/MCP_Server_System.wsv` 实测行尾是异常的 `<CR><CR><LF>`(151 行) + 1 行
   `<CR><LF>`, 而 `src/MCP_Server.wsv` 是纯 LF。故本脚本按"行+原行尾"切片(正则 `(?<=\n)`),
   插入行沿用**锚点行自己的行尾**, 其余字节原样保留 —— 避免把 152 行搅成一次纯空白 diff(静默转码)。
   写盘仍用 `io.open(..., 'w', encoding='utf-8', newline='\n')`: newline='\n' 表示**不做换行翻译**,
   字符串里显式的 \r 会原样落盘, 因此既满足"无 BOM / 不注入 CRLF", 又不破坏原文件行尾。

== 校验 ==
   锚点用 strip() 后逐行比对(不依赖行号与缩进); 命中数 != 1 立即报错退出;
   断言 字符串字面量之外的花括号/圆括号净额不变、行数变化 == 预期、'\n' 计数变化 == 预期、首行未变。
   默认 dry-run, 只有传 --apply 才写盘。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BS = '\\'                 # 单个反斜杠
COMMENT_BS = BS + BS      # 火山 行注释标记: 两个反斜杠
TERM_RE = re.compile(r'[\r\n]+$')

# ---------------------------------------------------------------- 补丁定义
PATCHES = [
    {
        'file': os.path.join('src', 'MCP_Server_System.wsv'),
        'why': 'browser_get_global_cache_dir 硬编码 CacheData\\GlobalData, 忽略 stdio 分支; 改为取类库真值并回传来源',
        'anchor': [
            r'变量 全局缓存目录 <类型 = 文本型>',
            r'全局缓存目录 = 取运行目录 () + "\\CacheData\\GlobalData"',
            r'返回 (MCP_响应构建.构建简单JSON ("global_cache_dir", 全局缓存目录))',
        ],
        'repl': [
            r'// G8: 缓存目录真值取自类库(无参读取器), 不硬编码 —— stdio 分支用 GlobalData_Stdio, 硬编码会静默返回错值',
            r'// 依据: main.wsv 启动时按 是否为Stdio模式 分流, 写入 设置.缓存目录',
            r'变量 全局缓存目录 <类型 = 文本型>',
            r'全局缓存目录 = FBrowser_取初始化缓存目录 ()',
            r'变量 缓存目录来源 <类型 = 文本型>',
            r'如果 (全局缓存目录 != "")',
            r'{',
            r'    缓存目录来源 = "classlib: FBrowser_取初始化缓存目录"',
            r'}',
            r'否则',
            r'{',
            r'    缓存目录来源 = "derived: 与 main.wsv 同一开关(是否为Stdio模式)"',
            r'    如果 (MCPStdio桥.是否为Stdio模式 ())',
            r'    {',
            r'        全局缓存目录 = 取运行目录 () + "\\CacheData\\GlobalData_Stdio"',
            r'    }',
            r'    否则',
            r'    {',
            r'        全局缓存目录 = 取运行目录 () + "\\CacheData\\GlobalData"',
            r'    }',
            r'}',
            r'变量 缓存目录JSON <类型 = YYJSON对象类>',
            r'缓存目录JSON.创建自文本 ("{}")',
            r'缓存目录JSON.加入逻辑值成员 ("success", 真)',
            r'缓存目录JSON.加入文本成员 ("global_cache_dir", 全局缓存目录)',
            r'缓存目录JSON.加入文本成员 ("cache_dir_source", 缓存目录来源)',
            r'返回 (缓存目录JSON.到可读文本 (YYJSON格式化选项.压缩))',
        ],
        'delta': 24,   # 27 - 3
    },
    {
        'file': os.path.join('src', 'MCP_Server.wsv'),
        'why': 'browser_get_global_cache_dir 的 Schema 描述未说明"随启动分支变化", 调用方无从判断取值口径',
        'anchor': [
            r'添加工具JSON ("browser_get_global_cache_dir", "获取全局缓存目录路径")',
        ],
        'repl': [
            r'添加工具JSON ("browser_get_global_cache_dir", "获取全局缓存目录路径(CEF用户数据根目录)| 真值取自类库 FBrowser_取初始化缓存目录(); 目录随启动分支变化: --mcp-stdio/--stdio/--headless 下为 CacheData 下的 GlobalData_Stdio, 常驻HTTP下为 CacheData 下的 GlobalData(见 main.wsv 的 是否为Stdio模式 开关) | 旧实现硬编码 GlobalData, stdio 分支下会静默返回错值 | 注意 profile 级缓存(Cache/Cookies/Local Storage)位于该目录下的 Default 子目录")',
        ],
        'delta': 0,
    },
    {
        'file': os.path.join('src', 'MCP_Server.wsv'),
        'why': 'browser_cache_dir 的描述只说"获取缓存目录", 未区分"当前浏览器请求环境"与"全局"口径(逻辑本身正确, 不动)',
        'anchor': [
            r'添加工具JSON ("browser_cache_dir", "获取缓存目录")',
        ],
        'repl': [
            r'添加工具JSON ("browser_cache_dir", "获取当前浏览器请求环境的缓存路径(类库 取请求环境().取缓存路径() 的 cache_path)| 无浏览器时明确失败 | 要取进程级全局缓存目录(不受浏览器存活影响)请用 browser_get_global_cache_dir")',
        ],
        'delta': 0,
    },
]


# ---------------------------------------------------------------- 工具
def token_net(bodies):
    """返回 (花括号净额, 圆括号净额)。

    跳过 @ 开头的嵌入式 C++ 行、# 开头的注释/嵌入块标记行、整行注释(// 与 \\);
    字符串字面量内的字符不计数。
    """
    br = pr = 0
    for raw in bodies:
        s = raw.strip()
        if not s:
            continue
        if s[0] == '@' or s[0] == '#':
            continue
        if s.startswith('//') or s.startswith(COMMENT_BS):
            continue
        i = 0
        in_str = False
        while i < len(s):
            c = s[i]
            if in_str:
                if c == BS:
                    i += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif s[i:i + 2] == '//':
                    break
                elif s[i:i + 2] == COMMENT_BS:
                    break
                elif c == '{':
                    br += 1
                elif c == '}':
                    br -= 1
                elif c == '(':
                    pr += 1
                elif c == ')':
                    pr -= 1
            i += 1
    return br, pr


def load_segments(path):
    """读文件 -> (分段列表, 原文)。

    分段 = 每段"行内容 + 行尾", 用正则 (?<=\\n) 在 \\n 之后切开, 故 \\r\\r\\n / \\r\\n / \\n 都能原样保留。
    """
    raw = open(path, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '%s 带 UTF-8 BOM, 拒绝改写' % path
    text = raw.decode('utf-8')
    segs = re.split(r'(?<=\n)', text)
    return segs, text


def split_term(seg):
    """返回 (行内容, 行尾)。"""
    m = TERM_RE.search(seg)
    if m:
        return seg[:m.start()], m.group(0)
    return seg, ''


def bodies_of(segs):
    return [split_term(s)[0] for s in segs]


def find_unique(segs, anchor):
    flat = [split_term(s)[0].strip() for s in segs]
    n = len(anchor)
    return [i for i in range(len(segs) - n + 1) if flat[i:i + n] == anchor]


def main():
    apply_mode = '--apply' in sys.argv
    print('=' * 78)
    print('G8 缓存目录补丁  %s' % ('[APPLY 落盘]' if apply_mode else '[DRY-RUN 只打印]'))
    print('项目根: %s' % ROOT)
    print('=' * 78)

    by_file = {}
    for p in PATCHES:
        by_file.setdefault(p['file'], []).append(p)

    for rel, plist in by_file.items():
        path = os.path.join(ROOT, rel)
        print('\n### 文件: %s' % rel)
        segs, text0 = load_segments(path)
        segs_orig = list(segs)
        keep = list(range(len(segs)))   # keep[j] = 该段来自原始文件的行号, 新插入段为 None
        bodies = bodies_of(segs)
        before_br, before_pr = token_net(bodies)
        n0 = len(segs)
        nl0 = text0.count('\n')
        print('  原: %d 行, \\n 计数=%d, 花括号净额=%d, 圆括号净额=%d' % (n0, nl0, before_br, before_pr))
        styles = {}
        for s in segs:
            t = split_term(s)[1]
            if t == '':
                continue
            styles[t] = styles.get(t, 0) + 1
        print('  行尾分布: %s' % {repr(k): v for k, v in styles.items()})
        if set(styles) - {'\n'}:
            print('  !! 注意: 本文件行尾不是纯 LF(实测含 %s), 脚本按原行尾保留, 不做静默转码'
                  % ', '.join(repr(k) for k in styles if k != '\n'))
        head0 = segs[0]

        for k, p in enumerate(plist, 1):
            print('\n  --- 补丁 %d/%d: %s' % (k, len(plist), p['why']))
            print('  锚点(逐行 strip 比对, 共 %d 行):' % len(p['anchor']))
            for s in p['anchor']:
                print('      | %s' % s)
            hits = find_unique(segs, p['anchor'])
            print('  锚点命中数: %d%s' % (len(hits), '' if len(hits) == 1 else '   (必须 == 1)'))
            if len(hits) != 1:
                print('  !! 锚点命中 %d 次, 期望恰好 1 次 -> 中止, 未改动任何文件' % len(hits))
                for h in hits:
                    print('     命中行号: %d' % (h + 1))
                return 2
            i = hits[0]
            n = len(p['anchor'])
            first_body = split_term(segs[i])[0]
            base = first_body[:len(first_body) - len(first_body.lstrip())]
            terms = set(split_term(segs[i + j])[1] for j in range(n))
            assert len(terms) == 1, '锚点各行行尾不一致: %s' % terms
            term = terms.pop()
            assert term, '锚点末行没有行尾, 不能安全插入多行'
            new_block = [(base + s if s else '') + term for s in p['repl']]

            print('  匹配位置: 第 %d~%d 行, 缩进 %d 空格, 行尾 %s' % (i + 1, i + n, len(base), repr(term)))
            print('  [旧文本]')
            for j in range(n):
                print('      %5d | %s' % (i + 1 + j, bodies[i + j]))
            print('  [新文本]  (%d 行)' % len(new_block))
            for j, s in enumerate(new_block):
                print('      %5d | %s' % (i + 1 + j, split_term(s)[0]))

            for s in new_block:
                b = split_term(s)[0]
                assert b.count('"') % 2 == 0, '新文本双引号数为奇数(字符串未闭合): %s' % b

            cand = segs[:i] + new_block + segs[i + n:]
            keep = keep[:i] + [None] * len(new_block) + keep[i + n:]
            d = len(cand) - len(segs)
            print('  行数变化: %+d (预期 %+d) %s' % (d, p['delta'], 'OK' if d == p['delta'] else 'MISMATCH'))
            assert d == p['delta'], '行数变化 %+d != 预期 %+d' % (d, p['delta'])
            segs = cand

        final = ''.join(segs)
        after_br, after_pr = token_net(bodies_of(segs))
        exp_delta = sum(x['delta'] for x in plist)
        print('\n  校验(整文件):')
        print('    行数 %d -> %d (预期 %+d) %s'
              % (n0, len(segs), exp_delta, 'OK' if len(segs) - n0 == exp_delta else 'MISMATCH'))
        assert len(segs) - n0 == exp_delta
        nl1 = final.count('\n')
        print('    \\n 计数 %d -> %d (预期 %+d) %s'
              % (nl0, nl1, exp_delta, 'OK' if nl1 - nl0 == exp_delta else 'MISMATCH'))
        assert nl1 - nl0 == exp_delta, '\\n 计数变化 %+d != 预期 %+d' % (nl1 - nl0, exp_delta)
        print('    花括号净额(字符串外) %d -> %d  %s'
              % (before_br, after_br, 'OK' if before_br == after_br else 'MISMATCH'))
        print('    圆括号净额(字符串外) %d -> %d  %s'
              % (before_pr, after_pr, 'OK' if before_pr == after_pr else 'MISMATCH'))
        assert before_br == after_br, '花括号净额变了: %d -> %d' % (before_br, after_br)
        assert before_pr == after_pr, '圆括号净额变了: %d -> %d' % (before_pr, after_pr)
        assert segs[0] == head0, '文件首行被改动'
        print('    首行未变: %s' % split_term(head0)[0][:60])
        # 未被任何锚点覆盖的原始行必须逐字节不变(行尾含在内)
        survivors_now = [s for s, k in zip(segs, keep) if k is not None]
        survivors_orig = [segs_orig[k] for k in keep if k is not None]
        print('    未触碰行逐字节不变: %d 行  %s'
              % (len(survivors_now), 'OK' if survivors_now == survivors_orig else 'MISMATCH'))
        assert survivors_now == survivors_orig, '有非锚点行被改动'
        assert len(survivors_now) == n0 - sum(len(x['anchor']) for x in plist)

        if apply_mode:
            with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(final)
            print('  >>> 已写入 %s (UTF-8 无 BOM, 原行尾保留, 未做换行翻译)' % path)
        else:
            print('  >>> [dry-run] 未落盘')

    print('\n' + '=' * 78)
    if apply_mode:
        print('完成: 3 处补丁已落盘。编译与运行验证由主代理执行(本脚本不编译、不运行)。')
    else:
        print('dry-run 结束: 未修改任何文件。落盘请执行:')
        print('    py -3 _audit/_apply_g8_cache_dir.py --apply')
    print('=' * 78)
    return 0


if __name__ == '__main__':
    sys.exit(main())
