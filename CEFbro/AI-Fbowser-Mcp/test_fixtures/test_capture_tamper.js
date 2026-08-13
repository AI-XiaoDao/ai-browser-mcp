// 抓包/资源篡改功能完备性实测
// 流程: detail_enable → 抓取 → POST捕获 → block篡改 → modify篡改 → 清理
const http = require('http');
function postMcp(body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({hostname:'127.0.0.1',port:9222,path:'/mcp',method:'POST',
      headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},
      res => { let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{ try { resolve(JSON.parse(raw)); } catch(e){ resolve({_raw:raw.slice(0,120)}); } }); });
    req.on('error', e => reject(e));
    req.setTimeout(timeoutMs || 20000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
    req.write(data); req.end();
  });
}
function call(name, args, t) {
  return postMcp({jsonrpc:'2.0',id:'t_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,150); }
  catch(e){ return JSON.stringify(r).slice(0,150); }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  console.log('【1】开启详细抓包');
  console.log(' ', txt(await call('browser_network', {action:'detail_enable'})));

  console.log('【2】导航 example.com 并抓取');
  console.log(' ', txt(await call('browser_navigate', {url:'https://example.com', max_ms:15000}), 30000));

  console.log('【3】POST 捕获测试 (页面内 fetch POST)');
  await call('browser_evaluate', {code:"(function(){fetch('/nonexist_post_test',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'user=test123&action=login'}).catch(function(){});return JSON.stringify({submitted:true});})()"});
  await sleep(2500);

  console.log('【4】网络日志列表');
  const list = await call('browser_network', {action:'list', limit:20});
  const lt = txt(list);
  console.log(' ', lt.slice(0, 400));
  // 检查日志中是否含 POST 记录与 body
  if (/POST/i.test(lt) && /test123/.test(lt)) console.log('  ✓ POST+body 已捕获');
  else console.log('  ✗ POST 未在日志中看到 (可能事件未触发或需检查)');

  console.log('【5】资源篡改: block 测试 (屏蔽 example.com 主文档)');
  console.log(' ', txt(await call('browser_intercept', {action:'block', url:'example.com'})));
  await sleep(500);
  console.log(' ', txt(await call('browser_navigate', {url:'https://example.com', max_ms:10000}), 20000));
  console.log('  当前URL:', txt(await call('browser_get_url', {})), '| 标题:', txt(await call('browser_get_title', {})));

  console.log('【6】资源篡改: modify 测试 (内容替换)');
  console.log(' ', txt(await call('browser_intercept', {action:'clear'})));
  console.log(' ', txt(await call('browser_intercept', {action:'modify', url:'example.com', search_text:'Example Domain', replace_text:'★篡改成功标记★'})));
  await sleep(500);
  console.log(' ', txt(await call('browser_navigate', {url:'https://example.com', max_ms:15000}), 25000));
  const bodyText = txt(await call('browser_get_text', {selector:'body'}));
  console.log('  页面文本片段:', bodyText.slice(0, 200));
  if (bodyText.indexOf('★篡改成功标记★') !== -1) console.log('  ✓ modify 内容替换生效');
  else console.log('  ✗ modify 未生效 (页面可能被缓存, 需刷新或检查规则)');

  console.log('【7】清理所有拦截规则');
  console.log(' ', txt(await call('browser_intercept', {action:'clear'})));
  console.log(' ', txt(await call('browser_network', {action:'disable'})));
  console.log('【8】恢复导航 example.com');
  console.log(' ', txt(await call('browser_navigate', {url:'https://example.com', max_ms:15000}), 25000));
  console.log('DONE');
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
