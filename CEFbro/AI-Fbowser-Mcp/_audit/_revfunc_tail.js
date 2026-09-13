// 只读: 打印注入 JS 尾部的逐字符深度, 并对若干结构做微解析测试
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');

let depth = 0, paren = 0, instr = null, esc = false;
const rows = [];
for (let i = 0; i < src.length; i++) {
  const ch = src[i];
  let mark = '';
  if (instr) {
    if (esc) esc = false;
    else if (ch === '\\') esc = true;
    else if (ch === instr) instr = null;
  } else if (ch === "'" || ch === '"') { instr = ch; }
  else if (ch === '{') { depth++; mark = ' <brace+'; }
  else if (ch === '}') { depth--; mark = ' <brace- depth=' + depth; }
  else if (ch === '(') { paren++; mark = ' <paren+'; }
  else if (ch === ')') { paren--; mark = ' <paren-'; }
  rows.push(i + '\t' + JSON.stringify(ch) + '\td' + depth + '\tp' + paren + mark);
}
console.log('--- tail from index 1020 ---');
console.log(rows.slice(1020).join('\n'));

function test(name, code) {
  try { new vm.Script(code); console.log('PASS  ', name); }
  catch (e) { console.log('FAIL  ', name, '=>', e.message); }
}
console.log('--- micro parse tests ---');
test('A forEach then array-literal-continuation',
  "var r=['a'].forEach(function(o){})['X','Y'];");
test('B try-catch then array statement',
  "try{1}catch(e){}['a','b'].forEach(function(o){try{}catch(e){}});");
test('C full skeleton',
  "JSON.stringify((function(){var out=[];try{Object.keys(window).forEach(function(k){try{}catch(e){}})}catch(e){}['a','b'].forEach(function(o){try{}catch(e){}})['X','Y'].forEach(function(c){try{}catch(e){}})return out.slice(0,3)})())");
test('D skeleton with braces only (no strings)',
  "JSON.stringify((function(){function add(p,f){try{}catch(e){}}try{1}catch(e){}['a'].forEach(function(o){try{}catch(e){}})['X'].forEach(function(c){try{}catch(e){}})return 1})())");
