// 统计 example.com 响应文本的换行符
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
  return postMcp({jsonrpc:'2.0',id:'nl2_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,400); }
  catch(e){ return JSON.stringify(r).slice(0,400); }
}
(async () => {
  const js = "(async function(){try{var r=await fetch('https://example.com/?nl='+Date.now());var t=await r.text();var n=(t.match(/\\n/g)||[]).length;var rn=(t.match(/\\r/g)||[]).length;return JSON.stringify({len:t.length,nl:n,cr:rn,head:t.substring(0,60)})}catch(e){return JSON.stringify({error:String(e)})}})()";
  const r = txt(await call('browser_cdp_call', {method:'Runtime.evaluate', params:JSON.stringify({expression:js, awaitPromise:true, returnByValue:true}), max_ms:15000}));
  console.log('响应文本统计:', r.slice(0, 400));
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
