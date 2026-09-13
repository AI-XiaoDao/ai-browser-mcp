// 只读: 通过在 ; { } ) 之后插入换行, 让 V8 报告错误行号, 再映射回原始列
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');

// 生成 行 <-> 原索引 映射
let out = '';
const idxOfLineStart = [0];
for (let i = 0; i < src.length; i++) {
  const ch = src[i];
  out += ch;
  if (ch === ';' || ch === '{' || ch === '}' || ch === ')') {
    out += '\n';
    idxOfLineStart.push(i + 1);
  }
}
fs.writeFileSync('_audit/_revfunc_runtime_lines.js', out, 'utf8');

const lines = out.split('\n');
try {
  new vm.Script(out);
  console.log('PARSE OK (multi-line)');
} catch (e) {
  const m = String(e.stack).match(/evalmachine\.<anonymous>:(\d+)/);
  console.log('message:', e.message);
  console.log('stack head:', String(e.stack).split('\n').slice(0, 6).join(' | '));
  if (m) {
    const lineNo = parseInt(m[1], 10);
    console.log('error line:', lineNo, 'content:', JSON.stringify(lines[lineNo - 1]));
    console.log('orig index start:', idxOfLineStart[lineNo - 1], '->', idxOfLineStart[lineNo]);
    console.log('orig slice:', JSON.stringify(src.slice(idxOfLineStart[lineNo - 1] - 60, idxOfLineStart[lineNo] + 20)));
  }
}
console.log('--- first 40 generated lines ---');
lines.slice(0, 40).forEach((l, i) => console.log((i + 1) + ': ' + l));
