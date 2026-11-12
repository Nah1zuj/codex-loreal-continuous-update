# Issue #1 软件复核记录（2026-11-12）

关联任务：[#1 固定共享验收版本，复核内部演示](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1)

## 结论

本轮为 **进行中的内部软件复核**，不是 M1 完成证明。后端、前端、构建、知识库、正常语音模型运行时、缺语音模型文字路径及关键会话状态自动化检查通过；仍缺 GitHub 最新 `main` 的本地同提交独立检出、人工浏览器关键路径、拒绝媒体后继续使用的现场记录及正式清理证据。

不得将本页用于声称 Windows、实体音视频、VoiceOver／NVDA、真实供应商、专业课程或目标用户验收通过。

## 源码与环境

| 项目 | 实际值 |
|---|---|
| GitHub 最新 main | `db485ed098d433758358e8cc6280af5d4003afe1`，PR #13 文档合并提交 |
| 本轮本地源码 | `fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07`，分支 `trace/spec-kit-remediation` |
| 共享源码关系 | `747f994` 的提交说明记录其同步了本地源码 `fd6154a`；本轮未把该关系冒充为最新 main 的同提交检出 |
| 系统 | macOS |
| Python | 3.12.15 |
| Node | v26.10.0 |
| npm | 11.19.1 |
| 本机语音状态 | 正常工作副本为 `loaded`；Git 归档独立副本为 `assets_missing_or_invalid` |
| 数据与端口 | 运行时脚本使用临时目录、独立 SQLite 和动态空闲端口 |

执行前后本地 Git 工作区均无未提交修改。没有切换、重置、合并或覆盖现有分支。

## 实际检查

| 检查 | 实际结果 | 分类与边界 |
|---|---|---|
| `python -m pytest -ra` | PASS：269 passed，2 skipped，30.18s | 2 项为 Windows PowerShell 专用检查；不是 Windows 实机结果 |
| `npm test -- --run` | PASS：36 files，191 tests | jsdom 软件环境；Canvas 未安装提示不等于实体浏览器渲染 |
| `npm run build` | PASS | 保留大于 500 kB 的 Vite 分包警告，未把警告隐去或直接判为缺陷 |
| `scripts/validate_kb.py` | PASS：LOOK 3、ROUTINE 3、REFERENCE_CASE 2、PRODUCT 14、ACCESSIBILITY_GUIDANCE 73、SOURCE 5 | 知识库结构校验，不是专业内容审核 |
| `scripts/verify_runtime.py` | PASS | 本机模型已加载；独立 SQLite、文字交互、会话恢复、端口归属、诊断和释放通过 |
| Git 归档独立副本 `scripts/verify_runtime.py --missing-voice` | PASS | 无语音模型时正确报告 `assets_missing_or_invalid`，文字路径、恢复、诊断及清理通过 |
| 会话控制与确认式小结专项 | PASS：18 tests | 覆盖跳步、暂停、恢复、结束、小结拒绝、明确确认、防重放和删除的软件行为 |

曾在本机模型已加载的日常副本中误用 `--missing-voice`，断言按设计失败；改用与环境一致的正常模式后通过。该参数不匹配不记作产品缺陷。随后在真正不含模型资产的 Git 归档独立副本中执行 `--missing-voice` 并通过。

## 前端交互补充审查

依据现有代码检查了动效和状态反馈边界：

- 已存在 `prefers-reduced-motion` 处理，GSAP、粒子、Canvas 和 CSS 动画在减少动态效果时停用或静态展示。
- 关键控件有清晰的 `:focus-visible` 轮廓；重要异步状态使用 `role="status"` 或 `aria-live`。
- 移动端布局不依赖 Hover 才能完成任务；Hover 仅作增强反馈。
- 当前未发现需要仅凭术语手册新增装饰动效的依据。交互变更仍须服务任务、移动端和读屏，不以“更炫”作为验收标准。

这是源码和自动化层面的审查，不替代 Chrome、VoiceOver 或 NVDA 的人工操作记录。

## 未完成和下一步

1. 恢复本机 GitHub 认证，从最新 `main` 建独立检出并记录精确 `git rev-parse HEAD`。
2. 在该同提交副本上复跑后端、前端、构建、知识库和运行时检查。
3. 人工复核开始、推进、跳步、暂停／恢复、提前结束、小结拒绝保存、明确保存与删除。
4. 记录拒绝相机和麦克风后继续文字使用、刷新后的媒体关闭状态及清理结果。
5. 失败项另建缺陷；全部完成标准满足后，才把 #1 转为待验收或已完成。
