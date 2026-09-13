// 只读: 取 V8 语法错误的确切列号, 并计算该列处的括号深度
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');
// 逐字符深度
let depth = 0, paren = 0, instr = null, esc = false;
const depAt = new Array(src.length);
for (let i = 0; i < src.length; i++) {
  const ch = src[i];
  if (instr) {
    if (esc) esc = false;
    else if (ch === '\\') esc = true;
    else if (ch === instr) instr = null;
    depAt[i] = depth;
    continue;
  }
  if (ch === "'" || ch === '"') { instr = ch; depAt[i] = depth; continue; }
  if (ch === '{') depth++;
  else if (ch === '}') depth--;
  else if (ch === '(') paren++;
  else if (ch === ')') paren--;
  depAt[i] = depth;
}
console.log('instr at end:', instr, 'final depth', depth, 'final paren', paren);
try { new vm.Script(src); console.log('PARSE OK'); }
catch (e) {
  console.log('message:', e.message);
  const lines = String(e.stack).split('\n');
  lines.forEach((l, i) => console.log('stack[' + i + '] len=' + l.length + ' :: ' + (l.length > 90 ? l.slice(0, 90) + '...' : l)));
  const caret = lines[2];
  const col = caret ? caret.indexOf('^') : -1;
  console.log('col of ^ :', col);
  if (col >= 0) {
    console.log('char at col:', JSON.stringify(src[col]));
    console.log('context:', JSON.stringify(src.slice(Math.max(0, col - 70), col + 40)));
    console.log('brace depth at col:', depAt[col]);
    for (let i = col - 1; i > 0 && i > col - 260; i--) {
      if (depAt[i] === 0 && src[i] === '}') console.log('  depth==0 right after index', i, JSON.stringify(src.slice(Math.max(0, i - 50), i + 8)));
    }
  }
}
