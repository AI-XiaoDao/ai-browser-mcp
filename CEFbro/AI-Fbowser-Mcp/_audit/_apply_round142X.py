# -*- coding: utf-8 -*-
r"""第142轮补丁 X(定稿): `pierce=true` 加**影子树安全闸门** —— 实测它会**延迟**打死 CDP 通道。

## 实测(三次独立运行一致)
| 步骤(页面含 author shadow root) | 结果 |
|---|---|
| `get_document {depth:6, pierce:true}` | 回包正常(0.03s) |
| **紧随其后的** `execute_js` | **35s / 30s(通道已死)** |
| 对照: 只读 `get_document {depth:4, pierce:false}` ×3 | 每次之后 `execute_js` 都 0.03s ⇒ 安全 |

⇒ `pierce=true` 在**含影子树的页面**上会先正常返回、再让下一条 CDP 命令挂住(通道被打死)。既然闸门的目的
  就是看影子树, 这个参数在**这类页面**上不能放开用。故:
  · 用**页面侧廉价探测**(`Array.from(document.querySelectorAll('*')).some(e=>e.shadowRoot)`)**先查有没有影子树**;
  · 有 → `pierce=true` **明确拒绝**(可行动: 改用页面侧 JS 读影子树, 或 browser_execute_js);
  · 无 → 放行(实测安全)。

用法: py -3 _audit\_apply_round142X.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
APPLY = '--apply' in sys.argv
ANS = '            dPierce0 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "pierce", 假)'

OLD = '''            dPierce0 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "pierce", 假)'''
NEW = '''            dPierce0 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "pierce", 假)
            如果 (dPierce0)
            {
                // ★ 安全闸门(第142轮三次独立运行实测): pierce=true 在**含 author shadow root 的页面**上会
                //   "先正常返回、再让下一条 CDP 命令挂住" —— 也就是**延迟打死本会话的 CDP 命令通道**
                //   (之后所有 CDP 类工具 30s 才靠原生回退返回, 需重启进程恢复)。
                //   故先用**页面侧廉价探测**(不走 DOM 域, 因此安全)判断有没有影子树: 有就拒绝并给替代。
                变量 d影子探测 <类型 = 文本型>
                d影子探测 = MCP命令服务器.CDP执行JS并等待 ("(function(){try{var all=document.querySelectorAll('*');var n=Math.min(all.length,3000);for(var i=0;i<n;i++){if(all[i].shadowRoot)return 'YES'}return 'NO'}catch(e){return 'ERR'}})()", 8000, 真)
                如果 (d影子探测 == "YES")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "pierce=true 在本页**被拒绝**: 页面含 author shadow root | 实测(三次一致): 本机对这种页面枚举影子树会**先正常返回、再让下一条 CDP 命令挂住**, 即**延迟打死本会话的 CDP 命令通道**(之后所有 CDP 类工具 30s 才返回, 需重启进程恢复) | 替代(安全): 用页面侧 JS 直接读影子树 —— browser_execute_js code=\\"document.getElementById('宿主id').shadowRoot.querySelectorAll('*')\\" 或对具体元素取 shadowRoot.innerHTML | 只读普通 DOM 仍可用: 本工具不带 pierce 的枚举实测安全(可重复 3 次)"))
                }
                如果 (d影子探测 == "ERR")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "pierce=true 的影子树探测失败(页面可能未就绪): 无法确认安全性故拒绝 | 先 browser_navigate / browser_wait what=load_end 让页面就绪, 或改用 browser_execute_js 读影子树"))
                }
            }'''

EDITS = [('X1 pierce 影子树安全闸门', OLD, NEW)]


def main():
    print('== 第142轮补丁 X (%s) ==' % ('应用' if APPLY else '预演'))
    txt = io.open(VIP, encoding='utf-8', newline='').read()
    for tag, old, new in EDITS:
        if old not in txt:
            print('   · %-30s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        txt = txt.replace(old, new, 1)
        print('   · %s' % tag)
    print('MCP_Server_VIP.wsv: 行数 %d' % len(txt.split('\n')))
    if APPLY:
        io.open(VIP, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
