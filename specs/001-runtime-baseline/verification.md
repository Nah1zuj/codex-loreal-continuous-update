# 运行基线验证

**版本** `5458f04` 及阶段 1 的锁定记录。**运行** 2026-11-07 · macOS arm64 · Python 3.12.15 · Node 26.10.0 · npm 11.19.1。知识库与阶段 0 的 Git 版本一致。模型版本与 SHA-256 见两份资产清单。

| 需求 | 状态 | 证据 |
|---|---|---|
| FR-101 干净安装 | PASS（Mac） | 从暂存源码导出干净副本，无 `.env`、个人 SQLite、模型和虚拟环境。执行 `./install-portable.sh`，Python 依赖安装、`pip check`、npm 依赖及构建通过。 |
| FR-101 Windows Python 依赖 | PASS（交叉解析） | `uv pip compile backend/requirements-runtime.txt --python-version 3.12 --python-platform x86_64-pc-windows-msvc --only-binary :all:` 解析 48 项，额外锁定 Windows 的 colorama。 |
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
| 真实设备与独立清单评审 | NOT RUN | 分别由阶段 4、5、8 和实际评审者完成。下载语音资产的冷启动未作为通过项。 |

## 队友验收

从干净副本按 [运行说明](../../AccessibleBeautyAgent/README.md) 安装。在应用目录用本次安装的 Python 运行 `scripts/verify_runtime.py --missing-voice`，完成模型安装后去掉参数重跑。随后执行四项回归，提交系统、Python、Node、模型状态、结果及异常。Windows 还应双击一次实际启动入口，确认关闭窗口后端口可重新使用。

## 收敛结论

Mac 软件链路和回归通过。Windows 运行与独立评审依然开放。阶段 2 先推进可独立验证的会话和隐私整改。原版本代码回退点为 `trace-baseline-20261107`，本阶段无数据库迁移。
