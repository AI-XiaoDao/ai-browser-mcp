// 验证 call_fn 内联参数方案的 JSON 合法性与 JS 可执行性 (字节精确模拟 wsv 构建逻辑)
function jsonEscape(s) {
  return s.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}
const objectId = 'abc-123';
const argsRaw = '["U0FMVF9hZG1pbjEyM0AxMjM0NQ==",42,true,null,{"k":"v"}]';
// 模拟 wsv: "{\"objectId\":\"" + JSON转义(objectId) + "\",\"functionDeclaration\":\"function(){return this.apply(this," + JSON转义(argsRaw) + ")}\",\"returnByValue\":true}"
const paramsText = '{"objectId":"' + jsonEscape(objectId) + '","functionDeclaration":"function(){return this.apply(this,' + jsonEscape(argsRaw) + ')}","returnByValue":true}';
console.log('参数JSON:', paramsText);
const parsed = JSON.parse(paramsText);
console.log('JSON解析: OK');
const decl = parsed.functionDeclaration;
console.log('functionDeclaration:', decl);
try { new Function('return ' + decl); console.log('decl 是合法JS: OK'); } catch (e) { console.log('JS错误:', e.message); }
// 沙箱执行: 模拟 CDP 以对象为this调用, 验证参数原样到达且类型保留
const fn = new Function('return ' + decl)();
const calls = [];
const target = {
  apply: function (thisArg, arr) {
    calls.push(arr);
    return 'RET_' + JSON.stringify(arr);
  }
};
console.log('执行结果:', fn.call(target));
const got = calls[0];
console.log('参数到达:', JSON.stringify(got));
console.log('类型检查: [0]字符串=' + (typeof got[0] === 'string') + ' [1]数字=' + (typeof got[1] === 'number') + ' [2]布尔=' + (typeof got[2] === 'boolean') + ' [3]null=' + (got[3] === null) + ' [4]对象=' + (typeof got[4] === 'object'));
