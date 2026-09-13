// 只读: 判定 V8 是否认为 return 处于顶层 (即 IIFE 体是否提前闭合)
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');

function t(name, code) {
  try { new vm.Script(code); console.log('PASS  ', name); }
  catch (e) { console.log('FAIL  ', name, '=>', e.message); }
}
t('as-is', src);
t('wrapped in function body', "function __w(){" + src + "\n}");
t('tail only (from index 1000)', src.slice(1000));
t('head only (to index 1000, closed)', src.slice(0, 1000) + "})())");
t('head only (to index 1100, closed)', src.slice(0, 1100) + "})())");
t('head only (to index 1150, closed)', src.slice(0, 1150) + "})())");
t('head only (to index 1160, closed)', src.slice(0, 1160) + "})())");
t('head only (to index 1200, closed)', src.slice(0, 1200) + "})())");
t('head only (to index 1230, closed)', src.slice(0, 1230) + "})())");

// 受控重写: 把第二处 [ 前插入分号 -> 看是否变成运行期错误(语法通过)
const second = src.indexOf("}catch(e){}})['XMLHttpRequest'");
console.log('second boundary at', second);
if (second > 0) {
  const fixed = src.slice(0, second + "}catch(e){}})".length) + ";" + src.slice(second + "}catch(e){}})".length);
  t('after inserting ; at 2nd boundary', fixed);
  console.log('fixed head:', JSON.stringify(fixed.slice(second - 30, second + 50)));
}

// 找出所有 "<something>[" 边界
let idx = -1;
while ((idx = src.indexOf('[', idx + 1)) !== -1) {
  const prev = src[idx - 1];
  if (prev === ')' || prev === '}' || prev === "'" || /[A-Za-z0-9_$]/.test(prev) === false) {
    console.log('bracket at', idx, 'prev char', JSON.stringify(prev), 'ctx:', JSON.stringify(src.slice(Math.max(0, idx - 30), idx + 30)));
  }
}
