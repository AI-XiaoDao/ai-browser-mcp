JSON.stringify((function()
{
var out=[];
var seen={
}
;
var MAX=500;
var FIL='' ;
function add(p,f)
{
try{
if(typeof f!=='function')
return;
var src=f.toString()
;
if(FIL&&p.indexOf(FIL)
<0)
return;
var k=src.length+'|'+src.slice(0,40)
;
if(seen[k])
return;
seen[k]=1;
out.push({
p:p,n:f.name||'',l:f.length,s:src.slice(0,1500)
}
)
}
catch(e)
{
}
}
try{
Object.keys(window)
.forEach(function(k)
{
try{
if(typeof window[k]==='function')
add('window.'+k,window[k])
}
catch(e)
{
}
}
)
}
catch(e)
{
}
['location','navigator','document','history','crypto','performance','localStorage','sessionStorage','console'].forEach(function(o)
{
try{
var obj=window[o];
if(!obj)
return;
Object.keys(obj)
.forEach(function(k)
{
try{
if(typeof obj[k]==='function')
add(o+'.'+k,obj[k])
}
catch(e)
{
}
}
)
}
catch(e)
{
}
}
)
['XMLHttpRequest','WebSocket','Promise','Map','Set','Array','Object','String','Number','Date','RegExp','JSON','WebAssembly','URL','Blob','FileReader','FormData','Headers','Request','Response','AbortController','IntersectionObserver','MutationObserver','ResizeObserver'].forEach(function(c)
{
try{
var C=window[c];
if(!C||typeof C!=='function')
return;
add('window.'+c,C)
;
try{
Object.getOwnPropertyNames(C.prototype)
.forEach(function(k)
{
try{
add(c+'.prototype.'+k,C.prototype[k])
}
catch(e)
{
}
}
)
}
catch(e)
{
}
}
catch(e)
{
}
}
)
return out.slice(0,MAX)
}
)
()
)
