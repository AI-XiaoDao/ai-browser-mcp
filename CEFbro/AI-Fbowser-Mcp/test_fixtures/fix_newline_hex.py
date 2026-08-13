# 将篡改过滤器类内的换行字符比较 "\n" 替换为十六进制转义 "\x0A" (字节精确)
import io
p = 'C:/Users/cxzxc/Desktop/官方火山编PC视窗wsv源码/ai-browser-mcp/CEFbro/AI-Fbowser-Mcp/src/MCP_Callbacks.wsv'
txt = io.open(p, encoding='utf-8').read()
i = txt.find('类 类_MCP_篡改过滤器')
seg = txt[i:]
# 字节精确模式: == "\n"  (双引号 反斜杠 n 双引号)
old = '== "\\n"'
new = '== "\\x0A"'
n = seg.count(old)
seg = seg.replace(old, new)
txt = txt[:i] + seg
io.open(p, 'w', encoding='utf-8', newline='').write(txt)
print('替换数:', n)
