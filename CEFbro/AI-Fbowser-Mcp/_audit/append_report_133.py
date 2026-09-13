# -*- coding: utf-8 -*-
"""追加报告 §133(第116轮): 12 个事件补齐 + 全局事件可查缺陷 + 两个编解码工具。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

# 注意: 必须用**原始字符串** —— 正文里有 Windows 路径(`classlib\user\yw`), 普通三引号会把 `\u` 当转义
# 而报 "truncated \uXXXX escape"(本轮就踩了这个)。
SEC = r"""
---

## 133. 第116轮：事件覆盖 **135/150 → 147/150**，另修掉"记了却查不到"的可见性缺陷，并新增 2 个零前置编解码工具

### 133.1 十二个事件一次补齐（两个"照抄就编译不过"的签名陷阱都已避开）

按 `_audit/_events_patch_plan_r115.md` 落地（脚本 `_audit/_apply_events_patch.py`，由计划作者**只读产出**、
主代理运行）：

| 落点 | 数量 | 事件 |
|---|---|---|
| `MCP_BrowserEvents.wsv` | 7 | `即将打开开发者窗口` / `即将改变媒体访问` / `拖拽进入` / `进程间消息_收到渲染进程消息` / `离屏渲染_获取根屏幕矩形·获取视图矩形·移动调整弹窗` |
| `MCP_Callbacks.wsv` | 5 | `开发者消息_VIP_已附加·已分离` / `开始创建` / `下载进度` / `获得需授权证书` |

**两个签名陷阱（r114 描述有误，本轮按类库原文纠正）**：
1. `浏览器_即将打开开发者窗口`(`FBroEventControl.wsv:763`) 方法行里**没有** `类型 = 逻辑型` —— 那行
   `返回值注释 = "返回真阻止当前操作…"` 是从 `浏览器_即将打开新窗口`(:721) 抄来的**文案残留**；
   类库胶水(:750-760) 是 `void OnBeforeDevToolsPopup(..., bool* use_default_window, ...)` 且**无 return**。
   → 覆盖方法写成 void、体内**不得出现 `返回 (`**（写 `返回 (假)` 会编译失败）。
2. `离屏渲染_获取视图矩形`(:1437) / `移动调整弹窗`(:1501) 同样是 **void**；只有 `获取根屏幕矩形`(:1420) 是逻辑型。

**开关与入口按"新建立的不变式"做全**：两个新开关（`是否监控开发者窗口` / `是否监控自建URL请求`）需要
**9 处**同步（声明、关闭全部事件监控、新 action 分支、`event_all_enable`/`disable`、kernel 的
enable/disable、**上一轮新加的 `action:get`**、schema 枚举），总数文案 26 → **28**。
其中"`action:get` 也得上"与"`关闭全部事件监控` 也得上"，正是上一轮刚建立的对称性要求的延伸。

### 133.2 编译与离屏证据

- `/c` 语法自检：**0 错误 0 警告**；`/d` 完整构建：**0 警告**，`tools=319`，快检通过。
- **事件名 diff**（补丁前快照取自 `备份/事件覆盖补丁r115-写入前/`）：**新增 12 个名字、消失 0 个**，
  与 12 处改动**一一对应**：`devtools_popup` / `media_access_change` / `drag_enter` / `ipc_from_renderer_ext` /
  `offscreen_get_root_rect` / `offscreen_get_view_rect` / `offscreen_popup_size` /
  `devtools_attached` / `devtools_detached` / `urlreq_start` / `urlreq_download` / `urlreq_auth`。
- 独立测量工具（`_audit/event_gap.py`，类感知口径）**实测**：

| 事件类 | 前 | 后 |
|---|---|---|
| 应用事件 | 30/30 | 30/30 |
| **浏览器事件** | 81/88 | **88/88 = 100%** |
| 资源处理器 / 资源过滤器 / 服务器事件 | 6/6 · 4/4 · 8/8 | 同 |
| **开发者消息事件** | 3/5 | **5/5 = 100%** |
| **URL请求事件** | 3/7 | **6/7 = 85.7%** |
| JS交互事件 | 0/2 | 0/2（见 133.5） |
| **合计** | **135/150 = 90%** | **147/150 = 98%** |

### 133.3 ★真机触发结论：3 个已实证回调，9 个如实记为"本环境不可达"

只接线不等于会回调，所以逐个找**能真正触发它**的路径去碰：

| 事件 | 触发方式 | 结果 |
|---|---|---|
| `devtools_attached` | `browser_debugger_enable` | **有记录** ✔（这正是"CDP 会话丢失"的根因信号） |
| `urlreq_start` | `browser_create_url_request` | **有记录** ✔ |
| `urlreq_download` | 同上 | **有记录** ✔ |
| `devtools_detached` | 需要 CDP 会话**真分离**（`browser_vip_disable_debugger` 是内核指纹开关，不分离 CDP） | 本环境不可达（会话存活期间不触发） |
| `devtools_popup` | 需要真的弹出 DevTools 窗口（F12/菜单"检查"） | 本环境不可达（原生菜单项无法用 CDP 点） |
| `drag_enter` | 试过 `Input.dispatchDragEvent` | 未触发（CEF 的 OnDragEnter 走 OS 级拖拽） |
| `media_access_change` | 需要**真的拿到**摄像头/麦克风 | 不可达（需启动期 `--enable-media-stream`，尚未做） |
| `urlreq_auth` | 需要客户端证书质询的站点 | 不可达 |
| `offscreen_*` ×3 | 需要离屏渲染模式 | 不可达（本项目窗口内嵌渲染，代码里已注明不触发） |
| `ipc_from_renderer_ext` | 需要宿主主动向渲染进程发消息 | 不可达（本项目从不发） |

**纪律**：这 9 项记为"已接线 + 本环境不可达（附原因）"，**不声称已生效**。它们不引入风险：不回调就等于没有代码路径。

### 133.4 ★另一个真缺陷：事件**记了却永远查不到**（可见性）

现象：`urlreq_start` 记录成功，但 `browser_event` 查不到。根因：这三个事件由 `MCP_Callbacks` 用
`记录浏览器事件 ("urlreq_start", 0, …)` 写入 —— **URL 请求没有浏览器上下文，用 0 表示"与浏览器无关"**；
而 `查询事件日志` 是按**当前浏览器ID** 过滤（`browser_id=?`），于是这些行**永远查不出来**。
项目里本来只有 `crash` 在调用侧特判（把查询 ID 置 0），**本轮把它推广成通则**：
`AND (browser_id=? OR browser_id=0)`。修复后 `urlreq_start` / `urlreq_download` 立刻可查 ✔。
（这类"数据写进去了但读取路径永远筛掉"的缺陷，与"静默假成功"是同一族，靠**换一个观测器**才暴露出来。）

### 133.5 两个新工具：`browser_codec` + `browser_time_convert`（317 → **319**）

依据 `_audit/_codec_plan_r115.md`（作者只读产出 `_audit/_apply_codec_patch.py`，主代理运行）。
两者都只依赖**已在项目模块表里**的 `视窗基本类`（本轮亲自复核 `AI-Fbowser-Mcp.vprj`：`视窗基本类` ✔ 在册），
**零新模块、零既有工具改动**。

验收 **22/22**（`_audit/verify_codec_r116b.py`；期望值全部由 Python 独立算准，不是抄工具回包）：

- hex：`"AB"`→`4142`；`"中文"`→`e4b8ade69687`；`input=base64 "qw=="`→**`ab`**；`"3q2+7w=="`→**`deadbeef`**；往返回中文
- GBK：`"中文"`→`d6d0cec4`（**且无尾部 `00`**，证明内部写死了 `是否包括结束零字符=假`）、
  `"中文测试"`→`d6d0cec4b2e2cad4`、`"中文abc"`→`d6d0cec4616263`；
  **真实痛点**：`gbk_decode input=base64 "PHRpdGxlPtbQzsSy4srUPC90aXRsZT4="` → `<title>中文测试</title>` ✔
- 时间：`now` 与本机真实时间差 ≤2s；`tz_offset_minutes = **-480**`（UTC+8，与独立实测一致）；
  `0`→`1970-01-01 08:00:00`、`1700000000`→`2023-11-15 06:13:20`、`1234567890`→`2009-02-14 07:31:30`、
  `2147483647`→`2038-01-19 11:14:07`；`2147483648` **显式报错并提示改 `unit=ms`**；自定义 `format` 生效；
  无法解析的文本**如实报错**（类库哨兵值被识别）

**验收过程中抓到并修掉的两个真缺陷**：
1. **编码方向忽略了 `input`**（`browser_codec`）：`hex_encode input=base64 data="qw=="` 返回 `71773d3d`
   —— 那是 ASCII `"qw=="` 的十六进制，而 schema 明写 `input: data怎么读: text/hex/base64`。
   现编码方向也认 `input`（base64 先解码、hex 先解析），A3/A4 因此从 FAIL 转 **PASS**。
2. **类库方法名大小写**：补丁写了 `字节集到Base64文本`，实际是 `字节集到BASE64文本`
   （`w_bin_p.wsv:582`）→ `/c` 报 2 处"没有找到所指定的方法名称"，已改正并复检。

> 说明：上一版验收 9/17 的 8 处失败**全是我的探针写错**（动作名写成 `to_time`、把整段回包的十六进制字符
> 都数了进去）—— 已按实测 schema 与回包改正。这已是本会话第 N 次"先怀疑探针"。

### 133.6 并行协同：两份"补丁脚本"由计划作者产出，主代理只负责运行与验证

- 两个子代理各自产出 `_audit/_apply_events_patch.py`（62KB）/ `_audit/_apply_codec_patch.py`（59.5KB），
  **均未改 `src/`、未编译、未调 MCP**。
- 两者都自带强守卫：**只用原文锚点定位（绝不用行号）**、命中数必须为 1、**按文件实测行尾与空行风格**
  （`MCP_BrowserEvents.wsv` 是 LF + **双倍行距**、`MCP_Callbacks.wsv` 是 CRLF + 单倍）、花括号**增量配平**、
  写前 sha256 复核、`--dry-run`/`--verify-only`。
- 控制/进度自证：events 脚本作者事后**从磁盘反查**，用"行数增量 = 预测值"（+272/+96/+6/+14/+14）与
  格式指标证明补丁已落地，并确认重复运行会被冲突守卫**安全中止（exit 4）**；
  codec 脚本作者的自检**提前抓出自己的一处编译级错误**（变量在子块内声明、块外引用）。

### 133.7 顺带完成的测量与工具改进

- `_audit/fastcheck.py` 新增**本会话全部修复的回归钉**（URI 解码兜底/`use_plus`/`frame_by_id`/事件族名通配/
  内核 `action=get` 可观测/插件加载守卫/codec 的 base64-input/GBK/时间与时区/2038 报错）：
  **41 → 51 项，3.3 秒全绿**。
- `_audit/_hash_availability_r116.md`：更正了编解码计划的一条排除理由 —— MD5/SHA 的"缺头文件"说法**不成立**：
  本机 `E:\HSPC\plugins\vprj_win\classlib\user\yw` 里 `md5\md5_.h/.cpp`、`jjm\include\lz4.*`、`XxHash\xxhash.hpp`
  **全在**，且 `仰望模块` **已在 `.vprj` 模块表**里。类库导出 `MD5类_.取数据摘要_(字节集)` / `取数据摘要2_3_(文件)`
  / `取数据摘要_XxHash_*` / `取数据摘要_CRC32` / `取数据HMAC_MD5_字节集`。
  → 下一轮**一次 `/c` 探针**即可判定能否新增 `browser_hash`（本文件不含"已验证可用"结论）。

### 133.8 状态与待办

工具总数 **319**；台账 **319/319**；编译 **0 警告**；快检 **51/51**；事件覆盖 **147/150 = 98%**。

**待办（均未声称完成）**：
1. `类_FBrowser_JS交互事件` 2 个（`即将查询`/`即将取消查询`）：需要**新建第三个子类**且依赖页面侧
   `window.cefQuery`；而本会话已实测 CEF 消息路由器在本应用里**用不成**（报告 §128 的否定结论），
   故需先解决那条通路再谈覆盖。
2. `上传进度`：类库要求在请求上设 `UR_FLAG_REPORT_UPLOAD_PROGRESS`，而 `FBrowser_创建URL请求` 的形参表里
   **根本没有 flags 形参** ⇒ 与本项目**永不回调**，不接（计划 §4 已论证）。
3. 启动期开关通道（摄像头/录音/GPU 三连）：走 `main.wsv` 现成的 `即将处理命令行` 钩子 + `mcp_config.json`，
   **不要**走 `取全局命令行`（有历史失败原文证据）。
4. `browser_hash`（一次编译探针即可判定）。
5. 操作备注 242 条的"叙述改契约"清理（建议按文件分工并行）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 报告有 BOM')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 报告含 CR')
        return 1
    if '## 133. 第116轮' in text:
        print('!! §133 已存在')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 133. 第116轮') == 1
    print('已追加 §133; 行数 %d -> %d (无 BOM / 无 CR / 唯一)' % (text.count('\n') + 1, t2.count('\n') + 1))
    return 0


sys.exit(main())
