# Issue #1 软件复核记录（2026-11-12）

关联任务：[#1 固定共享验收版本，复核内部演示](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1)

## 结论

本轮为 **进行中的内部软件复核**，不是 M1 完成证明。后端、前端、构建、知识库、正常语音模型运行时、缺语音模型文字路径及关键会话状态自动化检查通过；两轮独立本地实例的普通浏览器路径也已覆盖文字、暂停／继续、跳过、刷新恢复、提前结束、小结拒绝、修改后重新预览、明确保存和二次确认删除。另以独立 Chrome 156 将麦克风和摄像头站点权限显式设为 `denied`，确认两种请求均被拒绝、提示结束且文字回复正常。GitHub 最新 `main` 已在独立工作树按精确提交复跑；干净检出按仓库说明以缺语音模型模式通过，浏览器所用应用代码与该提交一致。真实权限弹窗键盘操作、读屏和实体设备证据另属后续验收。

不得将本页用于声称 Windows、实体音视频、VoiceOver／NVDA、真实供应商、专业课程或目标用户验收通过。

## 源码与环境

| 项目 | 实际值 |
|---|---|
| GitHub 最新 main | `db485ed098d433758358e8cc6280af5d4003afe1`，PR #13 文档合并提交 |
| 日常复核源码 | `fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07`，分支 `trace/spec-kit-remediation` |
| 最新 main 独立检出 | `db485ed098d433758358e8cc6280af5d4003afe1`，detached worktree `TRACE-main-20261112` |
| 应用代码差异 | `fd6154a..db485ed` 在 `AccessibleBeautyAgent` 下仅新增 57 个已跟踪语音模型／测试音频文件；浏览器、前后端和脚本源码无差异 |
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
| 最新 main `python -m pytest -ra` | PASS：268 passed，3 skipped，15.27s | 2 项为 Windows PowerShell 专用；1 项因干净检出未安装官方本地 Face Landmarker，未冒充实体视觉结果 |
| 最新 main `npm test -- --run` | PASS：36 files，191 tests | 与日常复核源码相同；jsdom Canvas 提示仍保留 |
| 最新 main `npm run build` | PASS：137 modules | 保留大于 500 kB 的分包警告 |
| 最新 main `scripts/validate_kb.py` | PASS：LOOK 3、ROUTINE 3、REFERENCE_CASE 2、PRODUCT 14、ACCESSIBILITY_GUIDANCE 73、SOURCE 5 | 知识库结构校验，不是专业内容审核 |
| 最新 main `scripts/verify_runtime.py --missing-voice` | PASS | README 对干净检出指定此模式；正确报告 `assets_missing_or_invalid`，文字路径、恢复、诊断及清理通过 |
| 最新 main 普通运行模式 | 预期不通过：`assets_missing_or_invalid` | 仓库包含 KWS 资产和模型来源清单，但未随 Git 分发完整 ASR `model.int8.onnx`；不能声称干净仓库语音开箱即用 |
| 会话控制与确认式小结专项 | PASS：18 tests | 覆盖跳步、暂停、恢复、结束、小结拒绝、明确确认、防重放和删除的软件行为 |
| 独立本地实例普通浏览器关键路径 | PASS（两轮） | 文字入口、提交、开始、暂停／继续、下一步、跳过、刷新、提前结束、小结拒绝、明确保存和二次确认删除可操作；浏览器无 warning/error |
| Chrome 显式媒体权限拒绝 | PASS（重复 2 次） | Chrome 156 / CDP 1.3 将 microphone、camera 权限设为 denied；两种请求均返回拒绝，提示结束，文字获得正常回复 |

曾在本机模型已加载的日常副本中误用 `--missing-voice`，断言按设计失败；改用与环境一致的正常模式后通过。该参数不匹配不记作产品缺陷。随后在真正不含模型资产的 Git 归档独立副本中执行 `--missing-voice` 并通过。

## 普通浏览器关键路径补充

在本地独立目录与 SQLite 上启动实例，固定使用前端 5191、后端 8021、语音 8022 端口。实际操作路径为：首页“书写·文字输入” → 输入晚宴需求 → 发送 → 接收“柔和正式”示例建议 → 开始步骤 → 暂停课程 → 继续课程 → 下一步。

- 发送前后按钮启用状态正确；建议和每一步均同时出现在对话记录与状态区域。
- 暂停后明确显示“已暂停，步骤保留”，控件变为“继续课程”；继续后恢复第 1 步，下一步进入“第 2 步，共 4 步”。
- 页面明确显示“麦克风已关闭”，文字入口仍可用；本轮没有申请或授予媒体权限。
- 浏览器控制台未发现 warning 或 error。
- 停止实例后 5191、8021、8022 均释放；Git 工作区仍干净。隔离目录中的 SQLite 和日志保留在忽略目录，供需要时复查。

这是普通浏览器与可访问语义层的操作证据，不是 VoiceOver／NVDA 实际播报。第一轮未覆盖的刷新、提前结束和小结保存／删除已在第二轮补做；浏览器／系统权限弹窗中的明确拒绝仍未覆盖。

## 普通浏览器关键路径补充（二）

第二个独立目录使用前端 5192、后端 8023、语音 8024 和独立 SQLite。实际结果：

- 点击语音输入后界面进入“正在连接麦克风与本地语音”；本轮没有授予权限，随即使用应用内“关闭麦克风”，状态变为“麦克风已关闭”，文字输入与发送继续可用。
- 开始课程后使用“跳过”从第 1 步进入第 2 步；刷新页面后仍为“第 2 步，共 4 步”，没有自动恢复录音。
- 提前停止后状态明确显示“会话已停止，相机已关闭”，教学和输入控件停止，出现“查看本次小结”。
- 选择“不保存这份摘要”后仍为“暂无已存摘要”，状态显示“已拒绝这份摘要”。
- 新会话生成第二份候选；修改标题和备注后，确认框按设计禁用，必须先“预览修改后的版本”。预览后才能勾选同意并保存。
- 保存后出现已确认摘要；点击删除先进入确认状态，只有再次点击“确认删除摘要”才删除。最终显示“暂无已存摘要”和“已删除摘要”。
- 全程浏览器未发现 warning 或 error。停止实例后 5192、8023、8024 均释放，Git 工作区干净；测试 SQLite 与日志保留在忽略目录供复查。

本轮先证明“未授予权限并主动关闭”后的文字退路；随后第三轮以 Chrome 站点权限显式 `denied` 补齐麦克风和摄像头拒绝路径。原生权限弹窗的键盘操作仍未在本轮复做。

## Chrome 显式媒体权限拒绝

在第三个独立目录与端口（前端 5193、后端 8025、语音 8026）启动 TRACE，并使用独立无头 Chrome 156.0.8078.81 配置。新增可复现脚本 `AccessibleBeautyAgent/scripts/verify_media_denial_browser.mjs`，通过 Chrome DevTools Protocol 1.3 把当前站点的 `microphone` 和 `camera` 权限显式设为 `denied`。

实际断言包括：

- `navigator.permissions` 对麦克风和摄像头均返回 `denied`。
- 点击语音输入后确实发起音频 `getUserMedia`，返回 `NotAllowedError`／`PermissionDeniedError`；等待连接提示结束并出现可继续文字的权限说明。
- 打开摄像头后确实发起视频 `getUserMedia`，返回拒绝；页面显示“摄像头权限被拒绝”。
- 返回文字页后输入“权限拒绝后继续文字”，用户消息进入记录且 TRACE 新增一条回复。
- 脚本连续执行两次均 PASS。停止后 5193、8025、8026 与 Chrome 调试端口 9334 全部释放；Git 工作区干净。

运行方式：

```bash
node scripts/verify_media_denial_browser.mjs http://127.0.0.1:5193 http://127.0.0.1:9334
```

这是 Chrome 中真实的站点权限拒绝与应用退路检查，但权限状态由 CDP 预设，未通过原生权限弹窗的键盘操作；不替代 #3 的键盘、VoiceOver／NVDA 或实体媒体验收。

## 前端交互补充审查

依据现有代码检查了动效和状态反馈边界：

- 已存在 `prefers-reduced-motion` 处理，GSAP、粒子、Canvas 和 CSS 动画在减少动态效果时停用或静态展示。
- 关键控件有清晰的 `:focus-visible` 轮廓；重要异步状态使用 `role="status"` 或 `aria-live`。
- 移动端布局不依赖 Hover 才能完成任务；Hover 仅作增强反馈。
- 当前未发现需要仅凭术语手册新增装饰动效的依据。交互变更仍须服务任务、移动端和读屏，不以“更炫”作为验收标准。

这是源码和自动化层面的审查，不替代 Chrome、VoiceOver 或 NVDA 的人工操作记录。

## 未完成和下一步

1. 审阅本 PR 中的证据、脚本和状态摘要；未经确认不合并。
2. PR 合并后在 `main` 同步证据入口，并再次确认合并提交的检查结果。
3. #1 可进入“待验收”，但 M1 是否完成仍取决于共享证据落入 `main`；真实权限弹窗、VoiceOver／NVDA、Windows 和实体设备继续由后续 Issues 验收。
