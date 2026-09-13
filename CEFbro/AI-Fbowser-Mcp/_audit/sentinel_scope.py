# -*- coding: utf-8 -*-
"""
校验 __MCP_NO_ATTR__ / __MCP_NO_ELEM__ 判定语句是否位于
   如果 (js值 != "" && js值 != "null" && ...)      <- 深度 d
   {
       ... 判定 ...                               <- 应为 d+1
       返回 (…命令成功…)
   }

若判定跑到成功块之外, 哨兵串会被当作正常值经 命令成功 返回给 AI,
即"把内部哨兵泄漏成用户可见结果", 属于真实缺陷(已在本项目真实发生过一次)。

不变式: 判定行深度 == 所属 如果(!=) 行深度 + 1。
@ 行(嵌入 C++)、字符串字面量、// 注释内的大括号不参与计数。
"""
import io, os, re, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'src')

OPEN_IF = re.compile(r'^\s*如果\s*\(')
OPEN_ELSE = re.compile(r'^\s*否则(\s*\(|\s*$)')
RET_OK = re.compile(r'^\s*返回\s*\(.*命令成功')
SENT = re.compile(r'==\s*"__MCP_NO_(ELEM|ATTR)__"')
SIGNATURE = re.compile(r'!=')


def is_signature(line):
    """是否"成功判定块"的块头: 如果 (... != ... "null" ...)"""
    return bool(OPEN_IF.match(line)) and '!=' in line and '"null"' in line


def strip_code(line):
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        if c == '"':
            i += 1
            while i < n:
                if line[i] == '\\':
                    i += 2
                    continue
                if line[i] == '"':
                    i += 1
                    break
                i += 1
            out.append('""')
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def depths(lines):
    d, res = 0, []
    for raw in lines:
        s = raw.strip()
        if s.startswith('@'):
            res.append(d)
            continue
        sk = strip_code(raw)
        res.append(d)
        d += sk.count('{') - sk.count('}')
    return res


def main():
    n_files = n_sent = n_bad = n_skip = 0
    for name in sorted(os.listdir(SRC)):
        if not name.endswith('.wsv'):
            continue
        n_files += 1
        with io.open(os.path.join(SRC, name), encoding='utf-8-sig') as f:
            lines = f.read().splitlines()
        D = depths(lines)
        for i, ln in enumerate(lines):
            if not SENT.search(ln):
                continue
            n_sent += 1
            dp = D[i]
            up = None
            for j in range(i - 1, -1, -1):
                if is_signature(lines[j]):
                    up = j
                    break
            # 本哨兵不属于" 如果(js值!="" && != "null" ...) { 返回(成功) }" 这一模式
            # (如 browser_scrape 提取路径用的是 __MCP_TEXT__ 前缀模式) -> 不适用, 不计缺陷
            if up is None or D[up] not in (dp - 1, dp):
                n_skip += 1
                print('SKIP %s:%d depth=%d %s' % (name, i + 1, dp, ln.strip()[:88]))
                print('        -> 非"成功判定块"模式, 本检查不适用')
                continue
            why = []
            在否则分支 = False
            if D[up] == dp:
                # 关键区分: 判定与判定块头同深度, 既可能是"跑到块外"(真缺陷),
                # 也可能是**判定位于同一 如果 的 否则 分支内**(合法结构)。
                # 后者特征: 判定所在块的块头(深度 dp-1 的最近 如果/否则)是 否则。
                enc = None
                for j in range(i - 1, -1, -1):
                    if D[j] == dp - 1 and (OPEN_IF.match(lines[j]) or OPEN_ELSE.match(lines[j])):
                        enc = j
                        break
                if enc is not None and OPEN_ELSE.match(lines[enc]):
                    # 否则 分支: 只要求本分支内存在成功返回, 否则视为非该模式
                    ret_after = [k for k in range(i + 1, len(lines))
                                 if RET_OK.match(lines[k]) and D[k] > D[enc]]
                    if not ret_after:
                        n_skip += 1
                        print('SKIP %s:%d depth=%d %s' % (name, i + 1, dp, ln.strip()[:88]))
                        print('        -> 位于 否则 分支内且该分支无 返回(命令成功), 不适用')
                        continue
                    在否则分支 = True
                else:
                    why.append('深度 %d == 上方判定块深度 %d 且不在 否则 分支内 -> 判定跑到成功块之外, '
                               '哨兵会经 命令成功 泄漏给调用方' % (dp, D[up]))
            # 找该 如果 块的收尾 '}' 行
            close = None
            for k in range(up + 1, len(lines)):
                if D[k] == D[up] and lines[k].strip().startswith('}'):
                    close = k
                    break
            # 否则 分支的判定不在 `up` 那个块里, 故不适用该块的死代码检查(已在上面单独校验过)
            if not 在否则分支:
                if close is None:
                    why.append('找不到所属判定块的收尾大括号')
                else:
                    inner = [k for k in range(up + 1, close) if RET_OK.match(lines[k])]
                    if not inner:
                        why.append('块内没有 返回(命令成功) -> 判定为死代码')
                    elif not any(k > i for k in inner):
                        why.append('所有 返回(命令成功) 都在判定之前 -> 判定为死代码')
            tag = 'OK  ' if not why else 'BUG '
            if why:
                n_bad += 1
            print('%-4s %s:%d depth=%d %s' % (tag, name, i + 1, dp, ln.strip()[:88]))
            for w in why:
                print('        -> %s' % w)
    print('\n扫描 %d 个源文件, 哨兵判定语句 %d 处; 越界/死代码 %d 处, 不适用 %d 处'
          % (n_files, n_sent, n_bad, n_skip))
    return 1 if n_bad else 0


if __name__ == '__main__':
    sys.exit(main())
