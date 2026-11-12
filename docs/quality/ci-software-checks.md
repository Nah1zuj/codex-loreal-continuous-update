# Pull Request 软件检查

本页记录 `.github/workflows/software-checks.yml` 的范围和证据边界。该工作流只是提交前的软件回归门禁，不是工程候选、真实试用或人工验收的替代品。

## 自动执行的检查

- Ubuntu＋Python 3.12：按 `backend/requirements-lock.txt` 安装并检查锁定依赖，运行后端回归、知识库校验和缺失可选语音资产时的运行时降级检查。
- Ubuntu＋Node.js 26.10.0：使用 `npm ci` 安装锁定依赖，拦截当前高危及以上的 npm 审计发现，运行前端测试和生产构建。
- GitHub Actions 引用固定到已查询的完整 commit，工作流权限只保留仓库内容读取。

## 不在自动检查范围内

- Windows 净安装、启停、PowerShell 入口和 NVDA；
- macOS VoiceOver，实体麦克风、扬声器、耳机和相机；
- 本地语音与视觉模型的真实资产加载；
- 真实文字或标签服务、私有凭据、真实供应商响应；
- 专业课程审核、产品资料审阅、独立验收和目标用户任务。

上述项目继续在对应 Issue 中按 PASS／FAIL／NOT RUN／BLOCKED 分开留证。CI 通过只证明该 commit 在 GitHub 托管的 Ubuntu 环境通过上述软件检查。

## 2026-11-12 引入前本地复核

复核基线：`db485ed098d433758358e8cc6280af5d4003afe1` 加本 PR 的依赖锁更新；macOS，Python 3.12，Node.js 26.10.0。

| 检查 | 结果 | 边界／5907注 |
|---|---|---|
| 全部后端测试 | PASS：268 passed，3 skipped | 2 项仅适用 Windows PowerShell；1 项需要未安装的官方 Face Landmarker 本地模型 |
| 知识库校验 | PASS | LOOK 3，ROUTINE 3，REFERENCE_CASE 2，PRODUCT 14，ACCESSIBILITY_GUIDANCE 73，SOURCE 5 |
| 缺语音资产运行时复核 | PASS | 使用隔离 SQLite、mock 设置和独立端口；语音结果为 `assets_missing_or_invalid` |
| 全部前端测试 | PASS：36 files，191 tests | jsdom 不提供 Canvas 实现的现有提示保留 |
| 前端构建 | PASS：137 modules | 现有大于 500 kB 分包提示保留 |
| npm 依赖审计 | PASS：0 vulnerabilities | 将测试工具链间接依赖 `undici` 由 7.30.0 更新至 7.30.2；更新前生产依赖审计也是 0 |

工作流只有进入 `main` 后，后续 PR 才能稳定继承这套检查。当前已开放 PR 不会因为本分支存在工作流而自动获得新结果。是否将状态检查设为分支保护的必需条件，也需要仓库管理者另行确认。
