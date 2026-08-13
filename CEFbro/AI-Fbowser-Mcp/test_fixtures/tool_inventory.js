// 拉取 tools/list 并输出每个工具的 名称 + required 字段, 用于设计全量探测脚本
const http = require('http');
function get(path) {
  return new Promise((resolve, reject) => {
    http.get({hostname:'127.0.0.1',port:9222,path,timeout:10000}, res => {
      let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>resolve(JSON.parse(raw)));
    }).on('error', reject);
  });
}
(async () => {
  const j = await get('/tools/list');
  const tools = j.tools || [];
  console.log('总数:', tools.length);
  // 按前缀分类统计
  const cats = {};
  for (const t of tools) {
    const p = t.name.split('_').slice(0,2).join('_');
    cats[p] = (cats[p]||0)+1;
  }
  console.log('\n=== 前缀分类 ===');
  for (const [k,v] of Object.entries(cats).sort()) console.log(' ', k, v);
  console.log('\n=== 每个工具的 required 参数 ===');
  for (const t of tools) {
    const req = (t.inputSchema && t.inputSchema.required) ? t.inputSchema.required.join(',') : '-';
    console.log(t.name + '  [' + req + ']');
  }
})().catch(e => { console.error(e.message); process.exit(1); });
