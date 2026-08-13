// 手写篡改过滤器专项验证 (缓存破坏URL, 确保请求真正到达过滤器)
const http = require('http');
function postMcp(body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({hostname:'127.0.0.1',port:9222,path:'/mcp',method:'POST',
      headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},
      res => { let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{ try { resolve(JSON.parse(raw)); } catch(e){ resolve({_raw:raw.slice(0,120)}); } }); });
    req.on('error', e => reject(e));
    req.setTimeout(timeoutMs || 25000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
    req.write(data); req.end();
  });
}
function call(name, args, t) {
  return postMcp({jsonrpc:'2.0',id:'v_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,200); }
  catch(e){ return JSON.stringify(r).slice(0,200); }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const ts = Date.now();
  const BUST = 'https://example.com/?nocache=' + ts;

  console.log('【A】block 测试 (缓存破坏URL)');
  await call('browser_intercept', {action:'clear'});
  console.log('  设置block:', txt(await call('browser_intercept', {action:'block', url:'example.com'})));
  await call('browser_navigate', {url: BUST, max_ms:15000}, 25000);
  await sleep(1000);
  const t1 = txt(await call('browser_get_title', {}));
  const u1 = txt(await call('browser_get_url', {}));
  console.log('  URL:', u1, '| 标题:', t1);
  const body1 = txt(await call('browser_get_text', {selector:'body'}));
  console.log('  正文:', body1.slice(0, 120));
  if (body1.indexOf('资源已屏蔽') !== -1) console.log('  ✓ block 生效 (手写过滤器输出屏蔽页)');
  else console.log('  ✗ block 未生效 (过滤器未挂载或未命中)');

  console.log('【B】modify 测试 (缓存破坏URL)');
  await call('browser_intercept', {action:'clear'});
  console.log('  设置modify:', txt(await call('browser_intercept', {action:'modify', url:'example.com', search_text:'Example Domain', replace_text:'★篡改生效★'})));
  const BUST2 = BUST + 'x';
  await call('browser_navigate', {url: BUST2, max_ms:15000}, 25000);
  await sleep(1200);
  const body2 = txt(await call('browser_get_text', {selector:'body'}));
  console.log('  正文:', body2.slice(0, 160));
  if (body2.indexOf('★篡改生效★') !== -1) console.log('  ✓ modify 生效 (流式搜索替换)');
  else console.log('  ✗ modify 未生效');

  console.log('【C】replace_data 测试');
  await call('browser_intercept', {action:'clear'});
  console.log('  设置replace_data:', txt(await call('browser_intercept', {action:'replace_data', url:'example.com', replace_text:'<html><body>REPLACED_DATA_OK</body></html>'})));
  const BUST3 = BUST + 'y';
  await call('browser_navigate', {url: BUST3, max_ms:15000}, 25000);
  await sleep(1200);
  const body3 = txt(await call('browser_get_text', {selector:'body'}));
  console.log('  正文:', body3.slice(0, 120));
  if (body3.indexOf('REPLACED_DATA_OK') !== -1) console.log('  ✓ replace_data 生效');
  else console.log('  ✗ replace_data 未生效');

  console.log('【D】清理');
  await call('browser_intercept', {action:'clear'});
  console.log('DONE');
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
