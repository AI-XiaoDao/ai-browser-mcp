# -*- coding: utf-8 -*-
r"""第139轮补丁 G(收尾): ①把"按索引可改默认项"的**实测结论**写进 browser_context_menu 描述
②把本轮结论写入 `_audit/_gap_verified.md`(§159) 与 `MCP工具可用性检测报告.md`(§159)。
用法: py -3 _audit\_doc_round139.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
APPLY = '--apply' in sys.argv

DESC_OLD = '''实测: 指向浏览器默认菜单项(标准ID 100..130 或其别名 back/reload/copy 等)的修改类**不会生效**'''
DESC_NEW = '''实测: 指向浏览器默认菜单项(标准ID 100..130 或其别名 back/reload/copy 等)的**按命令ID**修改类**不会生效**(但**按索引**的 accelat 可以: 实测给默认菜单第 0 项按索引设快捷键, 存在快捷键_索引 回读为真、verified_items 计 1 ⇒ 「默认项改不动」只对按命令ID成立)'''

GAP_TEXT = '''

## 八、第139轮完成：菜单族补齐（只读实况快照 + 按索引写 + wipe）与 4 处"承诺了却没生效"的静默缺陷

### §159.1 静默缺陷（已修，编译 0 警告，逐条有实测/静态证据）

| # | 缺陷 | 证据（修前） | 修法 |
|---|------|--------------|------|
| 1 | `browser_key_event.modifiers` **声明了却在 VIP 路径被丢弃** ⇒ Ctrl/Shift/Alt 组合键静默失效 | `MCP_Server_Core.wsv` 的 VIP 三分支只传 `key`；只有 CEF 退路写 `按键事件.修饰位` | 三处都传第 2 参（类库约定 **Alt=1/Ctrl=2/Meta=4/Shift=8**）；CEF 退路按语义换算成 CEF 旗标（Shift=2/Ctrl=4/Alt=8/Command=16），不再把掩码直接塞进去 |
| 2 | `browser_context_menu action=set` 的载荷**不是合法 JSON**（拼接漏逗号：`"warnings":""spec_lines":`） | 实测 `json.loads(data)` 失败 | 补回逗号（`","spec_lines":`） |
| 3 | `browser_vip_mouse_press/release` **永远按左键**（类库第 3 参 `按键类型` 从未传）+ 缺 x/y 时退化成在 (0,0) 按下 | 无 `button` 参数、无 x/y 守卫 | 补 `button`(0/1/2) + x/y 必填守卫；`browser_vip_mouse_click` 补 `delay_ms`（类库第 4 参 `单击延时` 被截断） |
| 4 | `browser_fingerprint_pixel_ratio.value` 声明为 `text`（实现按小数读） | schema 类型与语义不符 | 改 `number` 并注明文本也接受（读取器已对文本节点归一化） |

### §159.2 菜单族补齐（`_gap_menu.md` §A1/§A3 两条"待做"落地）

- **只读实况快照**（新工具 `browser_menu_probe`，注册号 1330）：在 CEF 回调内、**施加规格之前**读。
  实测拿到 **declared_count=17 / read_count=17**，其中 **6 项带快捷键提示**；每次"菜单被打开"最多采一次；
  武装 30 秒内有效，`get` 支持 `wait_ms` 等一次晚到的采集。
- **按索引写**（并入既有 `browser_context_menu`，不新起第二个菜单状态机）：行类型
  `accelat` / `noaccelat`（可回读）/ `checkat` / `colorat` / `fontat`（后三者类库无 getter，记入 `verify_unavailable`），
  第 3 列是**索引**；另加 `wipe`（清空本次菜单，必须**唯一一行** + `confirm_wipe:true`）。
- **实测推翻一条旧结论**：规格 `item|…|26501|1|0|` + `accelat||17|1|0|70C` + `accelat||0|1|0|70C` 施加后
  **`verified_items=2` 且 `apply_failed` 为空** ⇒ **按索引可以改到浏览器默认菜单项**（第 0 项也成功，
  `存在快捷键_索引` 回读为真）。旧结论"默认项改不动"只对**按命令ID**的修改类成立。
- **另一个实测缺陷并已修**：索引类行会**重复落进**公共快捷键块（那段按命令ID设快捷键），
  于是"生效了却额外多出两条 `[accel N 未生效]`"污染 `apply_failed`；已加排除条件，修后 `apply_failed` 为空。
- **诚实边界（写进工具描述）**：原生右键菜单是**模态**的 ——
  第 1 次 `arm` 必成功（0.03~0.36s），第 2/3 次必然等不到回调，且 CDP 的 Esc（走渲染器）**关不掉**它
  （加了"清场 + 3 次尝试"后仍第 2 次必失败）。故 `arm` 只派发**一次** + 短等 1.5 秒，抓不到就**如实**返回
  "已武装 + 原因 + 两条下一步"，不再白等 5.7 秒。快照可读范围只有**条目数 + 每项是否带快捷键提示**
  （`是否可见/是否选中/取菜单类型/取分组ID/取子菜单` 全部收**命令ID**，对未知 ID 的默认项读不到 —— 不谎报）。

### §159.3 验收与状态

| 项 | 结果 |
|---|---|
| `_audit/verify_menu_probe.py` | **22/22 通过**（快照 / 索引写 / 诚实回包 / 守卫 / 收尾健康） |
| 台账 | **324/324 = 324 通过 / 0 未通过**（新工具 `browser_menu_probe` 已测 pass 1.94s） |
| 快检 | **56/56**（干净实例） |
| 编译 | **0 警告** |
| 卫生扫描 | **全零**（操作备注/死代码备注/残注释/零引用方法/零引用成员/重复分支/幽灵注册） |

**流程教训（写下来避免重犯）**：验证脚本自己的 `payload()` 只处理"`data` 是字符串"这一种形态，
遇到"`data` 直接是对象"就把 `apply_count` 读成 `None`，一度误判成"规格没施加" ——
**探针解析器也要当被测对象**（与 build_args 漏解包同一类问题）。
'''

REPORT_TEXT = '''

## 159. 第139轮：菜单族补齐（默认菜单**看得见**了 + 按索引**改得动**了）与 4 处静默缺陷

### 159.1 先修"承诺了却没生效"的静默缺陷（这类缺陷最伤人：调用方以为成功了）

| # | 缺陷 | 修前证据 | 修法 |
|---|---|---|---|
| 1 | `browser_key_event` 的 `modifiers` **schema 里声明、VIP 路径却丢弃** ⇒ **Ctrl/Shift/Alt 组合键静默失效** | VIP 三分支只传 `key_code` | 三处都传修饰键（类库约定 Alt=1/Ctrl=2/Meta=4/Shift=8），CEF 退路按语义换算成 CEF 旗标 |
| 2 | `browser_context_menu action=set` 的回包**不是合法 JSON**（少一个逗号：`"warnings":""spec_lines":`） | 实测 `json.loads` 抛错 | 补回逗号 |
| 3 | `browser_vip_mouse_press/release` **永远按左键**（类库第 3 参从未传），缺 x/y 时还会在 (0,0) 按下；`browser_vip_mouse_click` 的 `单击延时` 被截断 | 无 button / 无守卫 | 补 `button`、x/y 守卫、`delay_ms` |
| 4 | `browser_fingerprint_pixel_ratio.value` 类型声明与语义不符（声明 text、按小数读） | — | 改 number 并注明文本也接受 |

### 159.2 新增：`browser_menu_probe` —— 现在能**看见**浏览器默认右键菜单

右键菜单族以前只能"写"（规格类工具），而默认项按命令ID改不动 —— 于是"菜单里到底有什么"完全不可观测。
新工具在 CEF 回调内、**施加规格之前**把默认菜单读出来：

- 实测 **17 个条目**，其中 **6 项带快捷键提示**（`has_accel`），并带 `snapshot_at_ms` 便于判断新鲜度；
- 可读范围如实限定为"条目数 + 每项是否带快捷键提示"—— 标签文本与逐项可见/选中态**读不到**
  （类库那些 getter 只收命令ID，而默认项的命令ID无法反查）；
- `arm` 可自动右键触发，`get` 支持 `wait_ms` 等一次晚到的采集。

### 159.3 新增：**按索引**改菜单（`browser_context_menu` 的 5 种索引行 + `wipe`）

`accelat` / `noaccelat`（可回读核对）/ `checkat` / `colorat` / `fontat`（后三者类库无 getter ⇒ 记入 `verify_unavailable`，不谎报），
第 3 列填**索引**；另加 `wipe`（清空本次菜单，必须唯一一行 + `confirm_wipe:true`，避免"右键菜单直接消失"）。

**实测推翻旧结论**：`item|…|26501|…` + `accelat||17|…` + `accelat||0|…` 施加后
**`verified_items=2`、`apply_failed` 为空** ⇒ 按索引**可以**改到浏览器默认菜单项（含第 0 项，`存在快捷键_索引` 回读为真）。
旧结论"默认项改不动"只对**按命令ID**的修改类成立。

### 159.4 诚实边界（原生菜单是模态的）

第 1 次 `arm` 必成功（0.03~0.36s），但**第 2/3 次必然等不到回调**，且 CDP 的 Esc（走渲染器）**关不掉**原生菜单
（加"清场 + 3 次尝试"后仍第 2 次必失败）。故 `arm` 只派发一次 + 短等 1.5 秒，抓不到就如实返回
"已武装（30 秒内有效）+ 原因 + 两条下一步"，**不再白等 5.7 秒**；要再采一次需先在窗口里点一下关掉旧菜单。

### 159.5 验收与状态

| 项 | 结果 |
|---|---|
| `_audit/verify_menu_probe.py` | **22/22** |
| 台账 | **324/324 = 324 通过 / 0 未通过** |
| 工具数 | **324** |
| 快检 | **56/56** |
| 编译 | **0 警告** |
| 卫生扫描 | **全零** |

> 流程教训：验证脚本自己的 `payload()` 只处理"`data` 是字符串"，遇到"`data` 直接是对象"就把 `apply_count`
> 读成 `None`，一度误判成"规格没施加" —— **探针解析器也要当被测对象**（与当年 `build_args` 漏解包同一类问题）。
'''

EDITS = [(SERVER, 'G1 描述补"按索引可改默认项"实测结论', DESC_OLD, DESC_NEW)]


def main():
    print('== 第139轮收尾 (%s) ==' % ('应用' if APPLY else '预演'))
    for path, tag, old, new in EDITS:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if old not in txt:
            print('   · %-40s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        txt = txt.replace(old, new, 1)
        print('   · %s' % tag)
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    for path, text, tag, mark in [(GAP, GAP_TEXT, '§159 技术记录', '## 八、第139轮完成'),
                                  (REPORT, REPORT_TEXT, '§159 报告章节', '## 159. 第139轮')]:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if mark in txt:
            print('   · %s —— 已存在, 跳过' % tag)
            continue
        out = txt.rstrip('\n') + '\n' + text
        print('   · %s: %d -> %d 字符' % (tag, len(txt), len(out)))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(out)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
