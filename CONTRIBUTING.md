# 贡献指南

感谢关注 **AI Browser MCP Server**。本仓库以火山视窗 `.wsv` 为权威源码。

## 你可以贡献什么

| 类型 | 路径 | 说明 |
|------|------|------|
| 核心逻辑 | `CEFbro/AI浏览器/src/*.wsv` | 请附测试说明或 `run_all_tests.js` 结果 |
| 文档 | `docs/`、`skills/`、`README.md` | 错别字、步骤、示例 |
| 桥接/测试 | `mcp_bridge.js`、`run_all_tests.js` | Node 脚本 |
| 工作流 | `CEFbro/AI浏览器/workflows/` | JSON 示例 |
| 发布脚本 | `release/pack-release.ps1` | 打包流程 |

**请勿修改** `generated-cpp/` 手改内容 — 该目录由编译同步，PR 会被要求改为改 `.wsv` 后重新生成。

## 开发环境

1. Windows x64 + [火山视窗 IDE](https://www.voldp.com/)（含 FBrowser CEF）
2. Node.js 18+（桥接与测试）
3. 打开 `CEFbro/AI浏览器/AI浏览器.vprj`，编译 Release x64

## 提 PR 前

```bash
# 1. 启动 AI浏览器.exe
# 2. 健康检查
curl http://127.0.0.1:9222/health

# 3. 桥接自检
node CEFbro/AI浏览器/mcp_bridge.js --check

# 4. 全量测试（可选，耗时）
node CEFbro/AI浏览器/run_all_tests.js
```

核心 `.wsv` 变更请在 PR 描述中说明：改了哪些 MCP 工具、是否向后兼容。

## 发布维护者（Release）

```powershell
# 编译 Release x64 后
.\release\pack-release.ps1 -Version 2.6.0
```

生成运行包 zip 与 cpp zip，上传 GitHub Releases。详见 `release/README.md`。

## 行为准则

- Issue 请提供：Windows 版本、MCP 版本（`/health`）、复现步骤
- 勿提交 token、cookie、`_int/linker/out/`、大二进制
- 许可证：贡献默认以 [MIT](LICENSE) 发布

## 联系

QQ 212577526 · 群 737680767 · [火山编程交流群](https://qm.qq.com/q/Hpv6qm8qUE)
