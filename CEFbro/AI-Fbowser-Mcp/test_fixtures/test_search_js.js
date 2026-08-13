// 字节精确复现 browser_reverse_search 的生成JS (q='sign'), 经 cdp_call 执行定位真实异常
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
  return postMcp({jsonrpc:'2.0',id:'y6_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,600); }
  catch(e){ return JSON.stringify(r).slice(0,600); }
}
(async () => {
  // 与 wsv srCode 完全一致的 JS (火山转义后): \\n → \n
  const js = "(function(){var q='sign';var uf='';var ss=document.querySelectorAll('script');var R=[];ss.forEach(function(s,i){var src=s.src||'(inline)';if(uf&&src.indexOf(uf)===-1)return;var t=s.textContent||'';var lines=t.split('\\n');lines.forEach(function(l,li){if(l.indexOf(q)!==-1){R.push({script_index:i,src:src.substring(0,200),line:li+1,snippet:l.trim().substring(0,300)})}})});return JSON.stringify({query:q,found:R.length,results:R.slice(0,50)});})()";
  console.log('JS长度:', js.length, '| 含真实换行:', js.includes('\n'));
  const r = txt(await call('browser_cdp_call', {method:'Runtime.evaluate', params:JSON.stringify({expression:js, returnByValue:true}), max_ms:15000}));
  console.log('结果:', r.slice(0, 800));
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
