# 运行基线验证

**版本** `5458f04` 及阶段 1 的锁定记录。**运行** 2026-11-07 · macOS arm64 · Python 3.12.15 · Node 26.10.0 · npm 11.19.1。知识库与阶段 0 的 Git 版本一致。模型版本与 SHA-256 见两份资产清单。

| 需求 | 状态 | 证据 |
|---|---|---|
| FR-101 干净安装 | PASS（Mac） | 从暂存源码导出干净副本，无 `.env`、个人 SQLite、模型和虚拟环境。执行 `./install-portable.sh`，Python 依赖安装、`pip check`、npm 依赖及构建通过。 |
| FR-101 Windows Python 依赖 | PASS（交叉解析） | `uv pip compile backend/requirements-runtime.txt --python-version 3.12 --python-platform x86_64-pc-windows-msvc --only-binary :all:` 解析 48 项，额外锁定 Windows 的 colorama。另从 Mac 下载了 CPython 3.12 Windows x64 的运行依赖轮包，未在 Windows 执行。 |
| FR-102 模型校验 | PASS | `voice/setup_local_voice_models.py`、`scripts/setup_local_landmarks.py --check`。语音模型通过真实本机加载；视觉资产摘要匹配，现有合成空白像素推理回归通过。 |
| FR-102 合成语音 | PASS | `voice/verify_stream.py voice/fixtures --port 61980` 通过 7 组真实本机 WebSocket 及模型样例，`unittest discover -s voice -p test_bounded.py` 通过 9 项。输入为合成音频。 |
| FR-102 缺模型降级 | PASS（Mac） | 干净副本中运行 `scripts/verify_runtime.py --missing-voice`，语音状态 `assets_missing_or_invalid`，真实 HTTP 文字会话与恢复通过。 |
| FR-103 / FR-106 启动与回退边界 | PASS（Mac） | `scripts/verify_runtime.py` 实际起三个服务，覆盖占用保护、同目录重复、诊断、停止及端口释放。中文空格副本首次安装后再次移动目录，确认重建缓存、重新启动和后续跳过重复安装。 |
| FR-104 后端 | PASS | `python -m pytest -ra`，194 通过、2 Windows 专用检查跳过。测试前后日常 SQLite 文件哈希一致。 |
| FR-104 前端 | PASS | `npm test -- --reporter=dot`，35 个文件、182 项，jsdom 不提供实际 WebGL。 |
| FR-104 构建与知识库 | PASS | `npm run build`，保留大分块警告；`scripts/validate_kb.py`，退出 0。 |
| FR-104 真实 HTTP 代理 | PASS（mock 业务） | `scripts/live_smoke.py --port 61980`，网页、检索、模拟视觉、保存拒绝、保存和删除通过，数据库为隔离库。 |
| FR-105 健康和诊断 | PASS | 启动冒烟及 `test_runtime_health.py`。诊断区分进程、SQLite、知识、资产和远程配置，不写浏览器身份、不输出测试凭据。 |
| FR-106 Windows PowerShell / 干净安装 / 实体 | BLOCKED | 当前环境为 Mac，需 Windows 机器执行实际入口与回归。 |

2026-11-12 初次在当时固定的 `main db485ed` 上补充 [Windows x64 净安装与启停验收包](windows-acceptance-packet.md)、合成记录和记录校验器；PR 分支随后同步共享 `main 53af597`。合成记录实际输出 `BLOCKED`。包核验函数另对 Issue #11 的固定 main 审计 ZIP 做全新解压，逐一通过 569 个 manifest 文件的大小与 SHA-256；这是跨平台包结构的软件检查，不是 Windows 安装或入口证据。这些材料只统一未来实机执行和证据格式，没有新增 Windows 实机结论。
| 真实设备与独立清单评审 | NOT RUN | 分别由阶段 4、5、8 和实际评审者完成。Mac 模型冷安装另见下方。 |

## 队友验收

从干净副本按 [运行说明](../../AccessibleBeautyAgent/README.md) 安装。在应用目录用本次安装的 Python 运行 `scripts/verify_runtime.py --missing-voice`，完成模型安装后去掉参数重跑。随后执行四项回归，提交系统、Python、Node、模型状态、结果及异常。Windows 还应双击一次实际启动入口，确认关闭窗口后端口可重新使用。

## 文字供应商诊断复核

`/api/health` 分别报告当前文字供应商配置就绪，以及本次后端运行中同一配置下是否已收到并完成一条远程流式答复。本地命令、mock、取消和缺少正常结束标记的流均不计入通过。按浏览器隔离的 `/api/diagnostics` 可查看每轮的服务来源及响应证据，凭据和回复正文不进入诊断。回环 HTTP 替身通过了配置与实际调用状态切换，真实供应商等待已批准配置。[联调步骤](../../docs/quality/release-runbook.md#真实文字与标签联调)

## Windows 入口静态复核

2026-11-07 在 macOS 使用 Microsoft 官方 PowerShell 7.6.8 arm64 归档，先核对发布页 SHA-256，再用语言解析器检查 `install-portable.ps1` 与 `start-portable.ps1`，两个文件均无语法错误。Windows PowerShell 5.1、真实安装和启停仍需 Windows 实机结果。[PowerShell 7.6.8 发布页](https://github.com/PowerShell/PowerShell/releases/tag/v7.6.8)

## Mac 模型冷安装复核

2026-11-07 在验收修订包的 Mac 净安装副本中，确认语音与视觉模型均缺失后，按发布说明下载固定版本并逐项核验 SHA-256。语音两套关键词和转写模型加载，健康报告为 `loaded`，九组合成音频 WebSocket 用例通过。实际 MediaPipe 对合成空白帧完成推理并返回无人脸。冷安装验证使用独立目录和 mock 文字配置，实际音视频采集另验。

## 收敛结论

Mac 软件链路和回归通过。Windows 运行与独立评审依然开放。阶段 2 先推进可独立验证的会话和隐私整改。原版本代码回退点为 `trace-baseline-20261107`，本阶段无数据库迁移。
