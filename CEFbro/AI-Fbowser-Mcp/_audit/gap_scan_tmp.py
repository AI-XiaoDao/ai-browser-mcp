# -*- coding: utf-8 -*-
# TEMP read-only audit helper. Does NOT modify any source file.
import os, re, sys, io, json
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp'
SRC = os.path.join(ROOT, 'src')
LIB = r'C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器\FBroLib.wsv'

def read(p):
    with open(p, 'rb') as f:
        b = f.read()
    if b[:2] == b'\xff\xfe':
        return b.decode('utf-16-le', 'replace')
    return b.decode('utf-8', 'replace')

srcfiles = [os.path.join(SRC, n) for n in os.listdir(SRC)
            if n.endswith('.wsv') and '~vbak' not in n]
srctext = {}
for p in srcfiles:
    srctext[os.path.basename(p)] = read(p)

lib = read(LIB)
liblines = lib.split('\n')

# ranges of the three target classes
RANGES = [('FBrowser初始化控制', 14, 266),
          ('FBrowser辅助功能', 377, 538),
          ('类_FBrowser_浏览器', 539, 1462)]

methods = {}
for cname, a, b in RANGES:
    lst = []
    for i in range(a, b + 1):
        line = liblines[i - 1]
        m = re.match(r'^(\s*)方法\s+(\S+)(.*)$', line)
        if m:
            indent = len(m.group(1))
            name = m.group(2)
            attrs = m.group(3)
            lst.append((i, indent, name, '公开' in attrs))
    methods[cname] = lst

print('=== method counts (indent, public) ===')
for c, lst in methods.items():
    print(c, len(lst), 'public=', sum(1 for x in lst if x[3]))

# per-method grep across src
def scan(name):
    pat_call = re.compile(re.escape(name) + r'\s*\(')
    pat_any = re.compile(re.escape(name))
    calls, anys = [], []
    for fn, txt in srctext.items():
        for ln, line in enumerate(txt.split('\n'), 1):
            if pat_call.search(line):
                calls.append((fn, ln, line.strip()))
            if pat_any.search(line):
                anys.append((fn, ln, line.strip()))
    return calls, anys

out = {}
for cname, lst in methods.items():
    for (ln, indent, name, pub) in lst:
        calls, anys = scan(name)
        out.setdefault(cname, []).append(
            dict(line=ln, name=name, public=pub, indent=indent,
                 calls=len(calls), anys=len(anys),
                 callsample=calls[:6], anysample=anys[:8]))

with open(os.path.join(ROOT, '_audit', 'gap_scan_out.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

for cname, lst in out.items():
    print('\n########', cname)
    for d in lst:
        flag = 'PUB' if d['public'] else '   '
        print('%-4d %s %-38s calls=%-4d any=%d' % (d['line'], flag, d['name'], d['calls'], d['anys']))
