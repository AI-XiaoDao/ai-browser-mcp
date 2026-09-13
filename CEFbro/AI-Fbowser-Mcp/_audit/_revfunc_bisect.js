// 只读: 二分定位 "插入换行即能通过解析" 的边界类别与具体位置
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');

function parses(code) { try { new vm.Script(code); return true; } catch (e) { return false; } }

function build(only, positions) {
  let out = '';
  for (let i = 0; i < src.length; i++) {
    out += src[i];
    if (only.has(src[i]) && positions.has(i + 1)) out += '\n';
  }
  return out;
}

console.log('original parses:', parses(src));

for (const ch of [';', '{', '}', ')']) {
  const all = new Set();
  for (let i = 0; i < src.length; i++) if (src[i] === ch) all.add(i + 1);
  console.log('only after ' + JSON.stringify(ch) + ' :', parses(build(new Set([ch]), all)));
}

// 对每个类别逐个位置二分: 找出"单个换行"就能修复的位置
for (const ch of [')', '}', ';', '{']) {
  const pos = [];
  for (let i = 0; i < src.length; i++) if (src[i] === ch) pos.push(i + 1);
  const hits = [];
  for (const p of pos) {
    if (parses(build(new Set([ch]), new Set([p])))) hits.push(p);
  }
  console.log('single-newline fixes after ' + JSON.stringify(ch) + ' at:', hits.map(p => p + ' ctx=' + JSON.stringify(src.slice(p - 25, p + 25))));
}
