# -*- coding: utf-8 -*-
"""追加报告第 128 节（第 111 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 128. 第111轮：★负结论——CEF message router（非 CDP 的 JS↔宿主通道）在**本应用不可用**；按纪律把工具撤掉

### 128.1 要做的能力（第107轮刷新的 A 组第 3）

`FBrowser_JS交互_注册/删除` —— CEF 自己的 message router：注册一个 JS 函数名后，
页面里 `window.<名字>({request, onSuccess, onFailure})` 会把消息送到宿主，宿主用
`JS交互回调.成功(文本)` 应答。它与项目现用的 CDP `Runtime.addBinding` **不是一回事**
（后者依赖 CDP 域，可被检测），对"需要一条非 CDP 的页面↔宿主通道"的场景有独立价值。

复核确认项目里**完全没有**该通道：全 src grep `JS交互` / `cefQuery` / `FBroHsQueryHandler` = **0 命中**。

### 128.2 实现（照抄类库自带例子的形态）

- `MCP_Callbacks.wsv` 新增回调类 `类_MCP_JS交互事件 <基础类 = 类_FBrowser_JS交互事件>`，
  重写 `即将查询 (浏览器, 框架, 查询ID, 请求文本, persistent, JS交互回调) → 逻辑型`：
  记录请求 → `JS交互回调.成功 (应答)` → `返回 (真)`。
- `MCP_Server.wsv` 存放注册名/回复/日志，工具 `browser_js_query`（`register`/`unregister`/`list`/`log`/`clear`）。
- 构建通过，工具数 316 → **317**，fastcheck 41/41 —— **编译与"能不能用"完全是两回事**。

### 128.3 ★两次实测：该通道在本应用**不可用**

**实验一（运行期注册，浏览器已存在）**：`register` 报成功，但页面里查一圈候选函数：

```
["cefQuery:undefined","cefQueryCancel:undefined","cefQuerytest:undefined",
 "cefQueryCanceltest:undefined","mcpQuery:undefined","_cefQuery:undefined"]
```

**刷新后依旧全部 undefined**，以默认名 `cefQuery` 注册同样如此 ⇒ **JS 函数从未注入页面**，
页面根本无从调用 ⇒ 工具会"报注册成功却无人能用"。

**实验二（启动期注册）**：类库自带例子是**先注册再创建浏览器**（`main3.wsv:45-46` 注册 → `:113` 创建），
故把注册挪到 `main.wsv` 的 `FBrowser_初始化` **之前**再试：

```
[启动] 就绪 tools=317 cdp=False      <- CDP 都没起来
fastcheck 0.1s 即失败
```

⇒ 启动期注册**直接破坏本应用的浏览器创建/CDP 通道**。

**结论**：CEF message router 在本应用不可用（运行期注册无效；启动期注册有破坏性）。
类库例子的形态**不能照搬到本应用**。

### 128.4 按纪律处置：**把工具撤掉**（不留"声明有、实际不可用"的能力）

两次实测都指向"这个能力做不出来"，于是**不是**把它留在那里显示"注册成功"，
而是把这一轮加的东西**全部撤回**：

| 撤回项 | 文件 |
|---|---|
| 启动期注册（从备份还原） | `main.wsv` |
| 回调类 `类_MCP_JS交互事件` | `MCP_Callbacks.wsv` |
| 4 个静态字段 + `记录JS查询并取回复` + 工具注册行 + 注册表两行 | `MCP_Server.wsv` |
| `browser_js_query` 分派分支 | `MCP_Server_Core.wsv` |

复核：四个文件中 `JS交互` / `cefQuery` / `browser_js_query` / `类_MCP_JS交互事件` **全部为 0**；
构建后 **tools 回到 316、cdp=True、fastcheck 41/41**，台账 **316/316** 通过 309 / 失败 7（无残留条目）。

**这条纪律值得单列**：我前几十轮主要在消灭"**静默假成功**"（做了却说没做）。
本节是它的**镜像**——"**声明有、实际不可用**"同样有害，而且这个实验里它差点以"注册成功"的形态留下。
处置原则一致：**不能用，就不要注册；并把这个负结论写进报告，避免后续重复投入。**

### 128.5 状态与下一步

工具总数 **316**（与实验前一致，无净增）；台账 **316/316**，通过 **309** / 失败 7
（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），**前置缺失 0、能力缺失 0、卡死 0**；
编译 0 警告；fastcheck 41/41。

1. A 组第 4 项：`browser_vip_execute_js_context` 加 `main`/`all_frames`/`frame_index` 三档 target
   （一次打穿所有 iframe，省"枚举框架→N 次注入"往返）。
2. `类_FBrowser_菜单模式` 剩余未接线方法（该类 36 个，已接线约 15 个）。
3. B 组 55 条"仅启动期生效"是否做启动参数通道。
4. 从第107轮 A 组清单里继续取下一项（清单已含 92 条，含价值排序）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 有 BOM, 中止')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 含 CR, 中止')
        return 1
    if '## 128. 第111轮' in text:
        print('!! §128 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 128. 第111轮') == 1
    print('已追加 §128; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
