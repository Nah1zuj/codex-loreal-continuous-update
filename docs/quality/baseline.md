# 阶段 0 源码与运行基线

2026-11-07 记录。工作目录是“codex欧莱雅持续更新版”的本机解压副本，原目录未包含 Git 元数据。代码起点为 `trace-baseline-20261107`（`9f64beac094827185ac7784e86e34bc31f1c6ddc`），整改分支为 `trace/spec-kit-remediation`。原压缩包是额外历史来源。现有密钥、用户库、工作日志、下载模型、外层媒体和历史备份留在本机，未纳入版本。回退时可独立检出上述标签并按当时脚本安装，数据保持原路径或由本人从一致性备份恢复。

- 采用已有 `specify-cli 1.2.3`。先在独立临时目录生成 Codex skills 与 Python 脚本，再迁入 `.specify` 和 `.agents/skills`。生成项经路径审查，未启用外部扩展或 issue 写操作。
- 现有入口为外层的安装与启动脚本 → `AccessibleBeautyAgent/launch-portable.py`。实际默认端口 5180 / 8012 / 8013。Mac arm64 环境使用 Python 3.12.15、Node 26.10.0、npm 11.19.1。
- 默认配置来自应用 `.env`。实际测试使用 mock 及隔离 SQLite，模型凭证未导出。匿名用户隔离由浏览器 Cookie 和 SQLite 支持。
- 知识库来自 `data/knowledge`，阶段 0 校验为 3 个 Look、3 个 Routine、2 个 Reference Case、12 个 Product、73 条无障碍指导、3 个 Source。
- 本地模型采用 Sherpa-ONNX 1.13.8、SenseVoice int8、双语唤醒模型和 MediaPipe Face Landmarker；记录的资源校验通过。
- 应用 README 仍提到缺失的根级 `setup.ps1` 等旧入口，旧脚本实在 `docs/旧入口归档`。历史报告、比赛模板与旧规格只用作历史，不作为当前运行或能力证明。当前副本未找到以白皮书命名的文件；产品边界采用本轮计划。
- 阶段 0 对照 [架构](architecture.md)、[能力矩阵](capability-matrix.md)、[缺陷与风险](bugs.md)、[需求追踪](traceability.md) 和 [测试证据](evidence/stage-0.md)。工程与真实试用均待后续验收。
