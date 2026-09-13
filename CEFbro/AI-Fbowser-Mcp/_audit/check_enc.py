import io,os
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
src=r"src"; bk=r"备份\并行子代理清理-写入前"
print("%-28s %-14s %-14s %-10s %-10s %s"%("文件","备份BOM","现BOM","备份EOL","现EOL","判定"))
bad=0
for n in sorted(os.listdir(src)):
    if not n.endswith(".wsv"): continue
    p1=os.path.join(src,n); p2=os.path.join(bk,n)
    if not os.path.exists(p2):
        print("%-28s (备份缺失)"%n); continue
    a=open(p2,"rb").read(); b=open(p1,"rb").read()
    def bom(x): return "UTF16LE" if x[:2]==b"\xff\xfe" else ("UTF8BOM" if x[:3]==b"\xef\xbb\xbf" else "无")
    def eol(x):
        crlf=x.count(b"\r\n"); lf=x.count(b"\n")
        return "CRLF" if lf and crlf==lf else ("LF" if crlf==0 else "MIXED")
    ba,bb=bom(a),bom(b); ea,eb=eol(a),eol(b)
    ok = (ba==bb and ea==eb)
    if not ok: bad+=1
    print("%-28s %-14s %-14s %-10s %-10s %s"%(n,ba,bb,ea,eb,"OK" if ok else "★不一致"))
print("\n不一致文件数 =",bad)
