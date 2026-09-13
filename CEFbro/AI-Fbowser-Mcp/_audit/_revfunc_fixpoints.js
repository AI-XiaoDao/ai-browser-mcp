// 只读: 输出两处修复点的精确字符位置, 并生成修复后的参考串(_audit/_revfunc_runtime_fixed.js)
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');

const iClass = src.indexOf("})['XMLHttpRequest'");
const iRet = src.indexOf(')return out.slice');
console.log('len(runtime) =', src.length);
console.log('[修复点1] 类名数组前, 需在 index ' + (iClass + 2) + ' 处插入 ";"');
console.log('  上下文:', JSON.stringify(src.slice(iClass - 40, iClass + 45)));
console.log('[修复点2] return 前, 需在 index ' + (iRet + 1) + ' 处插入 ";"');
console.log('  上下文:', JSON.stringify(src.slice(iRet - 40, iRet + 45)));

const fixed = src.slice(0, iClass + 2) + ';' + src.slice(iClass + 2, iRet + 1) + ';' + src.slice(iRet + 1);
fs.writeFileSync('_audit/_revfunc_runtime_fixed.js', fixed, 'utf8');
console.log('wrote _audit/_revfunc_runtime_fixed.js len=', fixed.length);

// 与 V4 等价性: 语法必须通过
try { new vm.Script(fixed); console.log('fixed parses OK'); } catch (e) { console.log('fixed PARSE FAIL', e.message); }

// 统计 catch(e){} 数量 (逐项兜底计数点)
console.log('catch(e){} count =', (src.match(/catch\(e\)\{\}/g) || []).length);
console.log('try{ count =', (src.match(/try\{/g) || []).length);

// 修复前后差异的长上下文(便于人工比对)
console.log('\n--- 修复点1 前 ---\n' + src.slice(iClass - 120, iClass + 60));
console.log('--- 修复点1 后 ---\n' + fixed.slice(iClass - 120, iClass + 60));
console.log('\n--- 修复点2 前 ---\n' + src.slice(iRet - 120, iRet + 40));
console.log('--- 修复点2 后 ---\n' + fixed.slice(iRet - 120, iRet + 40));
