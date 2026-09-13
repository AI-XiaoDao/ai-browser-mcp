# -*- coding: utf-8 -*-
r"""第138轮补丁 C: 修 `browser_close_try` 的"主窗口"判定缺陷(实测踩到)。

## 实测现象(第138轮验收 `_audit/verify_close_try.py`)
传 `browser_id=2`(一个**后台**浏览器)时, 工具却返回了"关闭主窗口需 confirm:true" —— 判定错误。

## 根因
路由层会先把参数里的 `browser_id` 写入静态 `目标浏览器ID`; 而 `取主浏览器 ()` 在
`目标浏览器ID > 0` 时**返回的就是那个目标自己**。于是"目标 == 主窗口"恒成立, 永远走不到关闭分支。
⇒ 判"是不是主窗口"**不能**用 `取主浏览器 ()`。

## 修法
按 `FBrowser_浏览器_取ID清单 ()` 的**最小 id** 认定主窗口(主窗口最先创建; 枚举方式与 browser_list 一致),
并在判定期间持 `浏览器数组锁`(与 browser_list 同样的用法)。

用法: py -3 _audit\_apply_round138c.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
APPLY = '--apply' in sys.argv

OLD = '''            变量 ct主浏览器 <类型 = 类_FBrowser_浏览器>
            ct主浏览器 = MCP命令服务器.取主浏览器 ()
            变量 ct主ID <类型 = 整数 值 = 0>
            如果 (ct主浏览器.是否为空 () == 假 && ct主浏览器.是否已关闭 () == 假)
            {
                ct主ID = ct主浏览器.取ID ()
            }'''

NEW = '''            // ⚠ 判"是不是主窗口"**不能**用 取主浏览器 (): 路由层已把参数里的 browser_id 写进静态
            //   目标浏览器ID, 而 取主浏览器() 在该值 >0 时**返回的就是目标自己** ⇒ "目标==主窗口"恒成立,
            //   后台浏览器也会被当成主窗口(实测踩到)。改按 ID 清单的**最小 id** 认定主窗口
            //   (主窗口最先创建; 枚举方式与 browser_list 一致), 期间持数组锁。
            变量 ct主ID <类型 = 整数 值 = 0>
            MCP命令服务器.浏览器数组锁.加锁 ()
            变量 ct清单 <类型 = 类_FBrowser_列表值>
            ct清单 = FBrowser_浏览器_取ID清单 ()
            如果 (ct清单.是否为空 () == 假)
            {
                变量 ct数量 <类型 = 整数>
                ct数量 = ct清单.取大小 ()
                计次循环 (ct数量)
                {
                    变量 ct项 <类型 = 整数>
                    ct项 = ct清单.取整数值 (取循环索引 ())
                    如果 (ct主ID == 0 || ct项 < ct主ID)
                    {
                        ct主ID = ct项
                    }
                }
            }
            MCP命令服务器.浏览器数组锁.解锁 ()'''


def main():
    txt = io.open(CORE, encoding='utf-8', newline='').read()
    if OLD not in txt:
        if 'ct清单' in txt:
            print('· 已应用过, 跳过')
            return
        raise AssertionError('锚点未找到')
    assert txt.count(OLD) == 1, '锚点命中 %d 次' % txt.count(OLD)
    out = txt.replace(OLD, NEW, 1)
    print('MCP_Server_Core.wsv: 行数 %d -> %d' % (len(txt.split('\n')), len(out.split('\n'))))
    if APPLY:
        io.open(CORE, 'w', encoding='utf-8', newline='').write(out)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
