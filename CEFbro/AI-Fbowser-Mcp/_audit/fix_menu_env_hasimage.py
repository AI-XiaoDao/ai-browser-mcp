# -*- coding: utf-8 -*-
"""移除对 类_FBrowser_菜单环境.是否存在图片 () 的调用 —— 该类库方法在本机**编译不过**。

实测(构建原文):
  <E:\\HSPC\\plugins\\vprj_win\\classlib\\sys\\FBrowser\\FBroLib.v>, 1895:
    错误: error C3861: 'FBroHSContextMenuParams_HasImageContents': 找不到标识符

含义: 技能书类库**声明**了 `是否存在图片` (FBroLib.wsv: 类_FBrowser_菜单环境 内), 但它生成的 C++ 调用了
**本机 CEF 封装里不存在的原生函数** —— 属"**文档/类库有、本机实际不可用**"的缺口。
而且这类缺口**只在有人真正调用它时才会暴露**(类库方法体是按需编译的), 所以在此之前一直不可见。

处置: 不再调用它。图片/媒体信息由**同类的两个可用getter**覆盖:
  `取媒体类型 () -> 整数`(参考 媒体类型.***) 与 `取媒体类型标识 () -> 整数`(位标志, 参考 媒体标识.***)。
不再自行推断 has_image —— 没有枚举值依据时硬猜等于编造语义。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '移除不可用类库调用-写入前')

text = io.open(SRC, encoding='utf-8').read()
OLD = '        菜单摘要.加入逻辑值成员 ("has_image", 菜单环境.是否存在图片 ())\n'
NEW = ('        // 注: 类库 是否存在图片() 在本机**编译不过**(FBroLib.v:1895 引用了不存在的原生函数\n'
       '        // FBroHSContextMenuParams_HasImageContents), 故不调用; 图片/媒体信息由下面两个 getter 覆盖。\n')
c = text.count(OLD)
print('锚点命中 %d (应为1)' % c)
if c != 1:
    print('!! 中止')
    sys.exit(1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server.wsv'))
open(SRC, 'wb').write(text.replace(OLD, NEW, 1).encode('utf-8'))
after = io.open(SRC, encoding='utf-8').read()
print('已移除; 备份 -> %s' % BAK)
print('复核 是否存在图片 出现次数: %d (应为0)' % after.count('是否存在图片'))
