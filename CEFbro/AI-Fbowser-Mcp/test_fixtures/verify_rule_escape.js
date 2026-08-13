// 规则转义往返模拟 (与 wsv 规则字段转义/反转义 逐行对应)
function esc(s) { return s.replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/\n/g, '\\n').replace(/\r/g, '\\r'); }
function unesc(s) { return s.replace(/\\r/g, '\r').replace(/\\n/g, '\n').replace(/\\\|/g, '|').replace(/\\\\/g, '\\'); }
const search = 'if (a|b) {';
const replace = 'console.log(1);\nconsole.log(2);';
const line = 'modify|' + esc('app.js') + '|' + esc(search) + '|' + esc(replace);
console.log('规则行:', line);
const segs = line.split('|');
const action = segs[0];
const url = unesc(segs[1]);
const s = unesc(segs[2]);
const r = unesc(segs.slice(3).join('|'));
console.log('解析: action=' + action + ' url=' + url);
console.log('搜索还原:', JSON.stringify(s), s === search ? 'OK' : 'FAIL');
console.log('替换还原:', JSON.stringify(r), r === replace ? 'OK' : 'FAIL');
const lines = ('block|x.com\n' + line).split('\n');
console.log('换行不破坏行结构:', lines.length === 2 ? 'OK' : 'FAIL');
// replace_data 空数据场景
const line2 = 'replace_data|' + esc('y.js');
const segs2 = line2.split('|');
console.log('replace_data空数据: 段数=' + segs2.length + ' action=' + segs2[0] + ' url=' + unesc(segs2[1]), segs2.length === 2 ? 'OK' : 'FAIL');
// modify 搜索以 file: 开头不被吞 (replace_file 才剥)
const line3 = 'modify|' + esc('z.js') + '|' + esc('file://x') + '|' + esc('rep');
const segs3 = line3.split('|');
const act3 = segs3[0];
const s3 = unesc(segs3[2]);
console.log('file:前缀保留(modify):', JSON.stringify(s3), act3 === 'modify' && s3 === 'file://x' ? 'OK' : 'FAIL');
const line4 = 'replace_file|' + esc('w.js') + '|file:' + esc('C:\\a\\b.js');
const segs4 = line4.split('|');
const act4 = segs4[0];
const f4 = act4 === 'replace_file' ? unesc(segs4[2].slice(5)) : 'N/A';
console.log('file:剥离(replace_file):', JSON.stringify(f4), f4 === 'C:\\a\\b.js' ? 'OK' : 'FAIL');
