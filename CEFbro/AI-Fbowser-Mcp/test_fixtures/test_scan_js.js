// 判别: browser_reverse_extract scan 的完整JS 经 cdp_call 执行 (与工具路径隔离)
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
  return postMcp({jsonrpc:'2.0',id:'y8_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,700); }
  catch(e){ return JSON.stringify(r).slice(0,700); }
}
(async () => {
  const js = "(function(){var R=[];var ss=document.querySelectorAll('script');ss.forEach(function(s,i){var src=s.src||'(inline:'+i+')';var type=s.type||'text/javascript';var txt=(s.textContent||'').substring(0,500);var hasCrypto=/sign|encrypt|decrypt|token|md5|sha|aes|rsa|hmac|base64|btoa|cipher|key|salt|nonce|x-/.test(txt.toLowerCase());R.push({index:i,src:src,type:type,size:s.textContent?s.textContent.length:0,preview:txt.substring(0,200),has_crypto_patterns:hasCrypto,inline:!s.src})});return JSON.stringify({total_scripts:R.length,scripts:R})})()";
  const r = txt(await call('browser_cdp_call', {method:'Runtime.evaluate', params:JSON.stringify({expression:js, returnByValue:true}), max_ms:15000}));
  console.log('cdp_call 执行scan JS:', r.slice(0, 900));
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
