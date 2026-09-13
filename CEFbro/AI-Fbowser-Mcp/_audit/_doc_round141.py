# -*- coding: utf-8 -*-
r"""第141轮收尾: 把本轮三项成果写入两份文档(§161)。
用法: py -3 _audit\_doc_round141.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
APPLY = '--apply' in sys.argv

GAP_TEXT = '''

## 十、第141轮完成：三个纯函数工具 + 整页截图（此前做不到）+ **修掉"截图打死 CDP 通道"**

### §161.1 新增三个工具（327 = 324 + 3）

| 工具 | 类库依据 | 解决的问题 |
|---|---|---|
| `browser_json` | `FBrowser_Parser_解析JSON`(433) / `写入JSON`(450) / `字节值解析为JSON`(443) | 代理拿到的常是 JSON 文本却**没有可信的合法性判据**；`validate` 给确定结论（非法也回 success + `valid:false`，那是校验结论不是故障）、`normalize` 回规范化 JSON、`from_base64` 走类库字节入口（不猜编码）；`allow_trailing_commas` 透传类库选项 |
| `browser_data_uri` | `FBrowser_Parser_取数据URI`(394) | 以前只能"base64 编码 + 手工拼 `data:` 前缀"，容易漏 mime/编码声明 |
| `browser_by_index` | `FBrowser_浏览器_通过序号取浏览器`(487) | 补齐序号语义；类库原文"获取失败返回**空浏览器**" ⇒ 越界**明确失败**并附 ID 清单便于交叉核对（序号与 `browser_list` 不保证同序，已在描述里写明） |

验收 `_audit/verify_round141.py` **23/23**：合法/非法 JSON 判别、`allow_trailing_commas` **判别差**、
normalize 往返结构等价、`from_base64` 与文本入口一致、非法输入走 normalize 给可行动失败、
data URI 载荷**独立 base64 解码一致** + **页面 `fetch` 真读到**（标题预言机）、by_index 与 browser_list 交叉核对 + 越界可行动失败。

### §161.2 `browser_screenshot`：整页截图此前**根本做不到**，且 `width/height/scale` 一直被忽略

实测（三臂，判据 = **PNG 头解析出的像素尺寸**）：

| 臂 | 参数 | 结果 |
|---|---|---|
| A | 默认（`fromSurface` 写死假）+ 800×600 | **(984, 705)** —— 宽高被忽略，拿到的是窗口可见区 |
| B | `from_surface:true` + 800×600 | **(800, 600)** ✅ rect 生效 |
| C | `from_surface:true` + `full_page`（页面 scrollHeight=5350） | **(984, 5350)** ✅ 与 scrollHeight 完全一致 |

⇒ 第 4 参 `是否表面` 决定"截 view(窗口) 还是 surface(按 rect 区域)"；项目把它写死成假，
于是**对外宣称的 `width/height/x/y/scale` 一直静默无效**。已改默认真（想回到旧行为显式传 `false`）。

### §161.3 高影响缺陷：**类库截图路线会把本会话 CDP 命令通道打死**（已改走 CDP）

| 路线 | 截图本身 | 截图后的 CDP 命令通道 |
|---|---|---|
| 类库 `高级_网页截图`（VIP 内核路线） | 正常 0.05s | **被打死**：之后原始 `Runtime.evaluate` 30s 超时、`execute_js` 30~35s 才靠原生回退返回或直接失败、`debugger_enable` 20s 超时；`注销CDP观察者`+重挂**也救不回来** ⇒ 用户看到的正是"截完图之后每个工具都要等半分钟、还会连续失败" |
| CDP `Page.captureScreenshot` | 正常（视口 0.04s / 整页 0.17s） | **完全健康**：截图前后 `execute_js` 都是 0.03s（两臂各测两次） |

修法（不重复造轮子 —— CDP 本就是项目主通道）：
1. `browser_screenshot` **默认走 CDP** `Page.captureScreenshot`（支持 format/quality/fromSurface/captureBeyondViewport/clip），
   图片**同步回包**（无需 `mcp_result` 轮询）；
2. `via:"library"` 才走类库路线，且回包**如实警告**"该路线会让本会话 CDP 命令通道失效"；
3. 非法 `via` 明确拒绝。

途中踩到两个坑（都已修）：① CDP 载荷在同步结果的 **`message`**（裸通道实测形态）而非 `result`，需容错提取；
② 本项目 YYJSON 对象**不支持嵌套对象成员**，`clip` 用"文本成员"传会被 CDP 判 `Invalid parameters` ⇒ 参数整段拼接。

验收 `_audit/verify_round141N.py` **11/11**：整页高度 == scrollHeight、**截图后 `execute_js` 仍 0.03s**、
连截 3 张后仍 <1s、rect 生效（800×600）、jpeg 质量透传（q10 6968 字节 vs q95 23104 字节）、`via` 守卫。

### §161.4 状态

| 项 | 结果 |
|---|---|
| 工具数 | **327** |
| 台账 | **327/327 = 327 通过 / 0 未通过**（新工具均已测 pass；`browser_screenshot` 复测 pass 0.08s via=cdp） |
| 验收 | `verify_round141` **23/23**、`verify_round141N` **11/11** |
| 快检 / 编译 / 卫生扫描 | **56/56** / **0 警告** / **全零** |

**流程教训（第三次同源）**：`browser_by_index` 复测记 fail，根因是**探针造了越界序号**(通用整数兜底 10)
撞上工具守卫 ⇒ 已按 `mass_probe` 既有做法补 `index:0`。探针的"通用兜底值"必须落在**运行期合法域**内。
'''

REPORT_TEXT = '''

## 161. 第141轮：三个纯函数工具 + 整页截图（此前做不到）+ 修掉"截图打死 CDP 通道"

### 161.1 新增三个工具（工具数 324 → 327）

- **`browser_json`**：JSON 校验/规范化/base64 入口（类库 `解析JSON` / `写入JSON` / `字节值解析为JSON`）。
  `validate` 给**确定结论**（非法也回 success + `valid:false` —— 那是校验结论，不是工具故障）；
  `normalize` 回规范化 JSON；`from_base64` 走类库字节入口不猜编码；`allow_trailing_commas` 透传类库选项。
- **`browser_data_uri`**：构造 `data:` URI（类库 `取数据URI`），省掉"手工拼 base64 前缀、漏 mime/编码声明"。
- **`browser_by_index`**：按序号取浏览器（类库 `通过序号取浏览器`），越界**明确失败**并附 ID 清单
  （类库原文"获取失败返回空浏览器"⇒ 必须判空；序号与 `browser_list` **不保证同序**，描述里已写明）。

验收 `_audit/verify_round141.py` **23/23**，含"`allow_trailing_commas` 判别差"、normalize 往返结构等价、
data URI **独立解码 + 页面 `fetch` 标题预言机**、by_index 与 `browser_list` 交叉核对。

### 161.2 整页截图此前**做不到**，而且 `width/height/scale` 一直被忽略

| 臂 | 参数 | 得到的图片（解析 PNG 头） |
|---|---|---|
| A | 默认（`fromSurface` 写死假）+ 800×600 | **(984, 705)** —— 宽高被忽略，拿到的是窗口可见区 |
| B | `from_surface:true` + 800×600 | **(800, 600)** ✅ |
| C | `from_surface:true` + `full_page`（scrollHeight=5350） | **(984, 5350)** ✅ |

⇒ 已把 `from_surface` 默认改真（旧行为可显式传 `false`），并新增 `full_page`（自动量文档尺寸 + `captureBeyondViewport`）、
`quality`、`capture_beyond_viewport`。

### 161.3 高影响缺陷：类库截图路线会**打死本会话的 CDP 命令通道**

| 路线 | 截图本身 | 截图后的 CDP 命令通道 |
|---|---|---|
| 类库 `高级_网页截图`（内核/VIP 路线，修前默认） | 0.05s 正常 | **被打死** —— 原始 `Runtime.evaluate` 30s 超时、`execute_js` 30~35s 才靠原生回退返回或直接失败；注销+重挂 CDP 观察者**也救不回来** |
| CDP `Page.captureScreenshot`（修后默认） | 视口 0.04s / 整页 0.17s | **完全健康** —— 截图前后 `execute_js` 都是 0.03s |

这就是用户感知到的"截完图之后每个工具都要等半分钟、甚至连续失败"。现默认改走 CDP，
图片**同步回包**（不再需要 `mcp_result` 轮询），`via:"library"` 保留为显式选项并**如实警告**其副作用。

验收 `_audit/verify_round141N.py` **11/11**；`browser_screenshot` 台账复测 **pass（via=cdp）**。

### 161.4 状态

| 项 | 结果 |
|---|---|
| 工具数 / 台账 | **327** / **327/327 = 327 通过 / 0 未通过** |
| 快检 / 编译 / 卫生扫描 | **56/56** / **0 警告** / **全零** |

> 流程教训（第三次同源）：探针的"通用兜底值"必须落在**运行期合法域**内 —— `browser_by_index` 被兜底成
> `index:10` 而实例只有 1 个浏览器，于是复测记成"越界失败"。已按 `mass_probe` 既有做法补 `index:0`。
'''


def main():
    for path, text, tag, mark in [(GAP, GAP_TEXT, '§161 技术记录', '## 十、第141轮完成'),
                                  (REPORT, REPORT_TEXT, '§161 报告章节', '## 161. 第141轮')]:
        txt = io.open(path, encoding='utf-8', newline='').read()
        if mark in txt:
            print('· %s —— 已存在, 跳过' % tag)
            continue
        out = txt.rstrip('\n') + '\n' + text
        print('· %s: %d -> %d 字符' % (tag, len(txt), len(out)))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(out)
    print('   ✔ 已写入' if APPLY else '(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
