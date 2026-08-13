// line_replace 新功能实测: 在 example.com 上做行号区间替换
const http = require('http');
function postMcp(body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({hostname:'127.0.0.1',port:9222,path:'/mcp',method:'POST',
      headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},
      res => { let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{ try { resolve(JSON.parse(raw)); } catch(e){ resolve({_raw:raw.slice(0,200)}); } }); });
    req.on('error', e => reject(e));
    req.setTimeout(timeoutMs || 30000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
    req.write(data); req.end();
  });
}
function call(name, args, t) {
  return postMcp({jsonrpc:'2.0',id:'lr_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,400); }
  catch(e){ return JSON.stringify(r).slice(0,400); }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function body() {
  for (let i = 0; i < 4; i++) {
    const r = txt(await call('browser_evaluate', {code:"(function(){return JSON.stringify({t:document.body?(document.body.innerText||''):''})})()", max_ms: 10000}));
    if (r.indexOf('超时') === -1) { const m = r.match(/"t":"([^"]*)"/); return m ? m[1].substring(0, 150) : r.slice(0, 120); }
    await sleep(1500);
  }
  return '(超时)';
}
(async () => {
  await call('browser_intercept', {action:'clear'});
  console.log('设置line_replace (example.com 第1-3行):', txt(await call('browser_intercept', {action:'line_replace', url:'example.com', line_start:1, line_end:3, replace_text:'LINE_RANGE_REPLACED'})));
  const url = 'https://example.com/?lr=' + Date.now();
  await call('browser_navigate', {url: url, max_ms:15000}, 30000);
  await sleep(2000);
  const b = await body();
  console.log('页面正文:', b);
  if (b.indexOf('LINE_RANGE_REPLACED') !== -1) console.log('✓✓✓ line_replace 生效 (行1-3被替换)');
  else console.log('✗ 未生效');
  await call('browser_intercept', {action:'clear'});
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
