// 精确定位 MCP_Server_Core.wsv 中单/双反斜杠 \s 的出现位置
const fs = require('fs');
const txt = fs.readFileSync('C:/Users/cxzxc/Desktop/官方火山编PC视窗wsv源码/ai-browser-mcp/CEFbro/AI-Fbowser-Mcp/src/MCP_Server_Core.wsv', 'utf8');
const SINGLE = /\\(?!\\)s/g;      // 单反斜杠+s (后无第二反斜杠)
const DOUBLE = /\\\\s/g;          // 双反斜杠+s
let m;
while ((m = SINGLE.exec(txt)) !== null) {
  const line = txt.slice(0, m.index).split('\n').length;
  console.log('单反斜杠 \\s → 行', line, JSON.stringify(txt.slice(m.index - 20, m.index + 8)));
}
while ((m = DOUBLE.exec(txt)) !== null) {
  const line = txt.slice(0, m.index).split('\n').length;
  console.log('双反斜杠 \\\\s → 行', line);
}
