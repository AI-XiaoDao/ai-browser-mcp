# -*- coding: utf-8 -*-
r"""第132轮收尾: 报告 ## 152 + `_gap_verified.md` 补第132轮进展。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 152. 第132轮：schema 审计补上"闭包分析"（38 条差异 → 4 条）＋ 修掉 geolocation 的**参数名不一致导致静默忽略**

### 152.1 把最后一块拼图补上：委托给共享助手的参数读取
上一轮全量扫描报出 38 条"声明了但分支体没读到"（EXTRA）。本轮给 `_audit/_show_branch_params.py` 加了
`--closure`：**递归跟到被委托的共享助手方法里**（以 `参数JSON` 为实参的调用，深度上限 3、防环），
于是"参数其实是被助手读的"这一类被正确归位（如 `browser_evaluate` 的 `code/file`、`browser_debugger_flow` 的
`url/line/expressions`）⇒ 差异从 **38 条降到 4 条**，且 **MISSING 仍为 0**。

### 152.2 补齐读取件清单（两个假阳性类别，都已消除）
1. **漏了 `yyjson取小数/取长整数/取对象成员_安全`** ⇒ VIP 族一批参数（`geolocation.lat/lng/accuracy`、
   `battery.level/charging_time`、`pixel_ratio.value`、`canvas_font.value`…）被误判成"死参数"。
   补上后这些**全部回归正常**。
2. **对象式读取**（`参数JSON.取文本 ("x")`）一开始按"任意对象.取文本"匹配，把**读事件/响应对象**的调用
   （`事件数据.取文本 ("webdriver")`）也算成参数读取 ⇒ 反过来造出 4 条假 MISSING。
   已把接收者**限定为参数对象本身**（`参数JSON|参数|参数对象|params|paramJSON|JSON参数`）。
⇒ 教训：**测量件每加一条规则，都要用"已知真值"回测**；否则只是把一类假象换成另一类。

### 152.3 修掉一个真实的"静默不生效"：`browser_fingerprint` 的坐标参数名不一致
扫描（闭包开）报出 `browser_fingerprint MISSING=['latitude','longitude']`；源码核实
`MCP_Server_Core.wsv:2527/2529` 确实只读 `latitude/longitude`，而它的 **schema 与兄弟工具
`browser_vip_fingerprint_geolocation` 用的是 `lat/lng`** ⇒ 调用方照另一处文档传 `lat/lng` 会被
**静默忽略**（坐标保持 0，却回 success）。
处理（两手）：① 实现同时接受两种写法（专用名优先，`lat/lng` 回退）；② schema 把两组名字都声明出来并注明等价。
验收 `_audit/verify_round132.py` **4/4**：全量扫描 MISSING=0、`lat/lng` 与 `latitude/longitude` 两条路径都成功、
指纹族其他 action 无回归。

### 152.4 一条环境教训（值得每轮记住）
本轮快检第一次跑出 **55/56**（鼠标臂 5.1s）。排查发现：CDP 读类工具仍 0.03s，而 `mouse_move` 稳定 5.08s，
且**工具自己的慢因上报写着"窗口当前不可见(WS_VISIBLE=0)"** —— 可就在一分钟前 `browser_get_window_style`
读到的却是可见（style=382664704）。即：**同一实例在长时间连续探测后，窗口/渲染器状态会漂移**。
`loop.py --nobuild` 干净重启后立刻恢复 **56/56（4.4s）**。
⇒ 纪律：**延迟类断言失败之前必须先在干净实例上复现**，否则会把环境污染误判成产品回归（第124轮已有同类教训）。

### 152.5 遗留（下一轮）
扫描剩余 4 条"疑死参数"（闭包开、MISSING=0）：
`browser_debugger_last_paused.parse`、`browser_evaluate.max_ms`、`browser_reverse_detect_obfuscator.script_index`、
`browser_reverse_scan_crypto.script_index`。其中 `max_ms` 实为**入口公共参数**（由公共层读取，不是死参数）；
其余三条需逐条判断"实现没读 ⇒ 删声明，还是补实现"，判断依据同样用
`py -3 _audit\\_show_branch_params.py --diff --closure <工具名>`。

### 152.6 状态
工具 **323**；台账 **323/323 已测 = 320 通过 / 3 刻意设计**；快检 **56/56（干净实例 4.4s）**；编译 **0 警告**；卫生扫描**全零**。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 152.' in text:
        text = text[:text.index('## 152.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    mark = '> **第132轮进展**'
    old = '> **第131轮进展**'
    add = (mark + '：扫描器加 **闭包分析**（跟到共享助手，38 条差异 → 4 条）+ 补齐读取件清单'
           '（`yyjson取小数/取长整数/取对象成员_安全` 与限定接收者的对象式读取）—— 消除了两类假象；'
           '据此找出并修掉真实缺陷：`browser_fingerprint` 的 geolocation 只认 `latitude/longitude` 而 schema/兄弟工具用 '
           '`lat/lng` ⇒ **坐标被静默忽略**，现已两者都接受并都声明。验收 4/4。'
           '另记环境教训：长会话下窗口/渲染器状态会漂移（快检一次 55/56、鼠标 5.08s），干净重启即恢复 56/56，'
           '**延迟类断言失败前必须先干净复现**。\n')
    if mark not in g and old in g:
        g = g.replace(old, add + old, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第132轮进展')
    else:
        print('_gap_verified.md: 跳过')


main()
