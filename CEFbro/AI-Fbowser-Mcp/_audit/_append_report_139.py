# -*- coding: utf-8 -*-
r"""追加报告章节: ## 139. 第121轮 —— iframe 框架寻址的三个真实缺陷 + G5/G6/G7/G8 四项功能落地。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 139. 第121轮：iframe 框架寻址的三个真实缺陷（都属"静默错答案"）+ G5/G6/G7/G8 四项功能落地

### 139.1 结论速览
| 项 | 结果 |
|---|---|
| `browser_execute_js {frame_id}`（G1b） | **17/17 通过**；缺省路径(CDP 隔离世界) 稳定性 **24/24 次全绿、单次约 0.06s** |
| DOM/填表族 `frame_id`（G1c，23 个工具） | **25/25 通过**（含嵌套 iframe、按名/按id/按序号、写操作双向、跨域 OOPIF 读取） |
| 交叉回归 | 快检 **56/56**；`browser_get_frames` 的 `is_main` 由"按位置猜"改为"问框架对象" |
| G5 下载终态信息 | `download_complete` 已产生，字段齐全（见 139.6） |
| G6 媒体设备指纹 | "假成功"改为**如实失败/如实回报**（3/3） |
| G7 `browser_fingerprint clear_count` | 已可用（旧版报未知 action） |
| G8 全局缓存目录 | 不再硬编码；标注取值来源，且与内核回报口径的关系已查清 |

### 139.2 ★缺陷一：CEF 的框架清单顺序**不保证主框架在前**（`browser_get_frames` 的 `is_main` 一直是猜的）
`browser_get_frames` 原先用 `is_main = (序号 == 0)` 推断。实测该清单顺序会出现 **[子框架, 主框架]**：
```
[0] name='orderfr' is_main=True(按位置推断)  href=about:srcdoc        ← 其实是**子框架**
[1] name=''        is_main=False            href=https://example.com/ ← 其实是**主框架**
```
后果：消费者按 `is_main` 选框架会**选反**。本轮 fastcheck 的"iframe 写入"臂就因此把值写进了主框架，
一度看起来像工具回归（实为清单标志位失真）。修正：改为问框架对象自身 `是否为主框架 ()`，并顺带输出 `url`
（跨域 OOPIF 不在 CDP 框架树里，地址是唯一可靠的对照键）。

### 139.3 ★缺陷二：跨域 iframe 是 OOPIF，**不在**页面级 `Page.getFrameTree` 里
实测同页面：CEF 清单 3 条 `[main, samefr, xofr(8-…)]` vs CDP 树 **2 条** `[main, srcdoc-samefr]`。
OOPIF 只在独立 target 里，页面级会话够不到。原实现"按序号对齐 CEF 与 CDP 清单"因此在**有 OOPIF 时错位**：
若 OOPIF 排在同源框架之前，按 id/按名传那个同源框架会落到**另一个框架**上（静默读写错对象）。
修正：`解析框架执行上下文` 改为**按框架键匹配**（见 139.4），OOPIF 找不到对应项时**如实失败**，
并在错误文案里写明原因与可用替代（`browser_execute_js {frame_id, world:main}` 走原生框架对象，跨域可达 ——
实测该路确实能读到跨域框架的 `document.title`）。

### 139.4 ★缺陷三：同名同址的 srcdoc 框架会被**对调**（只按地址匹配不够）
第一版修正按"地址 + 名次"匹配。实测外层(`mcpfr`)与内层(`mcpfr2`)都是 `about:srcdoc`，
而 **CEF 清单顺序与 CDP 树顺序并不一致**，结果 `frame_id=外层` 读到了内层的值、`frame_id=内层` 读到外层的值
—— 探针直接抓到 `预言机 = ['MAIN','IFRAME2','IFRAME1']`（外层/内层互换）。
最终实现 `CDP框架树找ID (树体, 目标名, 目标地址, 地址名次)`：
1. 目标名非空 → **只认同名项**（必要时用地址加固为强命中）；
2. 目标名为空（匿名框架）→ 退回"地址 + 名次"最佳努力；
3. 名字与地址都取不到 → 仅当两侧条数一致才按序号兜底，否则返回 -1（**失败，不猜**）。

### 139.5 守住"绝不在错误框架里执行"的几道闸
- `CDP执行JS并等待` 内部原有 **5 处** `原生执行JS并等待` 回退，而该原生路径**只在主框架**执行；
  调用方给了子框架上下文时回退 == 静默跑错框架。新增 `子框架原生回退` 闸门（上下文 > 0 直接返回空 = 无回退可用），
  5 处调用点全部改走它（脚本断言"恰好 5 处"）。
- `browser_get_text` 的两条回退链同样只认主框架 → 指定 `frame_id` 时**到此为止并如实报错**（新增守卫）。
- `前置存在校验` 原先恒在**主框架**探测元素，于是"Schema 有 frame_id 的写操作"在 iframe 里会被判"匹配到 0 个元素"直接失败
  —— 7 个写分支根本走不到原生执行。已改为框架感知（签名加 `浏览器/参数JSON`，7 个调用点同步补参）。

### 139.6 G5 下载终态信息（含"回调不出现"的实测补强）
- 已落地字段：`download_start` 增 `download_id/url/original_url/mime/content_disposition`；
  `download_progress` 增 `download_id/url/speed`；**新增** `download_complete` / `download_canceled`
  （`download_id/filename/url/original_url/total_bytes/received_bytes/mime/content_disposition/saved_path/start_time/end_time/completed/canceled/received_all`）。
- 实测补强：本机 CEF 回调里 `isComplete` 为真的那次**不出现**（真机下载 8199 字节后只有 start/progress），
  故终态判据加"**已收满**"（总长度 > 0 且 已下载 ≥ 总长度），并按 `download_id` 去重。
- 实测延迟：下载事件的**落库有明显延迟**（触发后数十秒到约 2 分钟才查得到），
  验证脚本因此做成两阶段（`--check-only` 复验）；已用落库记录确认字段齐全（download_id=23 那次）。
- 已知边界：完成瞬间 `取存储位置 ()` 可能为空串（实测 `saved_path:""`），调用方应结合 `received_all/completed` 判断。

### 139.7 G6/G7/G8
- **G6**：`browser_vip_fingerprint_media_devices` 此前**只有 type 被传给内核**（第二参默认空对象，类库实现按 `IsNullObject()`
  短路，内核收到 `"1;"` 零设备），却回"已设置"。现在：`type` 必填（省略即报错，避免"默认清空"这种静默破坏）、
  `devices` 逐条构造 `FBrowser_媒体硬件数组` 并**真正传下去**、`type=1/2` 缺清单**如实失败**，回报里带设备数。
  残留不确定性（类库侧）：`MapToString()` 末行结果被丢弃 → 清单串缺收尾 `}`；是否真生效需内核侧另测。
- **G7**：`browser_fingerprint` 新增 `action=clear_count`（类库 `指纹_清空调用计数`，此前 0 引用），
  回 `success/cleared/count`；`clear`（全清）与 `clear_count`（只清计数）语义区分写进描述，
  并订正了把 `count` 说成"当前生效项数"的旧文案（实为**指纹 API 调用计数**）。
- **G8**：`browser_get_global_cache_dir` 原先硬编码 `CacheData\\GlobalData`，**忽略 stdio 分支**
  （`--mcp-stdio/--stdio/--headless` 实例真实用的是 `GlobalData_Stdio`）—— 返回的路径真实存在却属于另一个实例，
  是最难发现的一类错值。现改为按 **main.wsv 的同一个开关**推导并写明 `cache_dir_source`；顺带规整了双分隔符。
  **编译实测拦下一个更深的坑**：类库 `FBrowser_取初始化缓存目录 ()`（静态）在本机安装版**编译不过**
  （`FBroLib.v:155 error C3861: 'IsEmpty' 找不到标识符`），故改用开关推导（"把类库方法接上并编译"这条冒烟测试的价值再次体现）。
  另查清：`browser_cache_dir`（内核回报）返回的是 **profile 目录** `<root>\\Default`，与全局根目录是**两个口径**，
  两者关系已在描述里写明。

### 139.8 本轮改动文件
`src/MCP_Server.wsv`（框架匹配/解析方法、23 个工具的 frame_id 说明、指纹与缓存目录描述、下载去重变量）、
`src/MCP_Server_Core.wsv`（`browser_get_frames` 的 is_main+url、DOM 族 8 处框架感知、`browser_get_text` 守卫、`clear_count`）、
`src/MCP_Server_Form.wsv`（`前置存在校验` 框架感知 + 7 调用点 + attr_get/get_text/set_text 框架感知）、
`src/MCP_BrowserEvents.wsv`（下载终态块重写）、`src/MCP_Server_VIP.wsv`（媒体设备清单真正传入）、
`src/MCP_Server_System.wsv`（缓存目录真值 + 来源标注）。编译 0 错误 0 警告；快检 56/56。
'''
# 注: 本字面量内不含三个连续双引号


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 139.' not in text, '章节 139 已存在'
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已追加: %d -> %d 字符' % (len(text), len(out)))
    else:
        print('[dry-run] 将追加 %d 字符' % len(SECTION))


main()
