# TRACE 本地运行

面向盲人和低视力用户的语音优先美妆体验。产品范围与整改进度见 [工程质量目录](../docs/quality/traceability.md)。这里是当前运行入口的说明。

## 安装与启动

安装 Python 3.12.x 和 Node.js 26.10.0。Windows 使用 x64 Python、附带的 Python Launcher 与 Node.js 安装包。保持外层目录与 `AccessibleBeautyAgent` 的相对位置。

| 平台 | 安装入口 | 启动入口 | 应用 Python |
|---|---|---|---|
| macOS | 双击外层 `首次安装_Mac.command`，或运行 `./install-portable.sh` | 双击外层 `启动Demo_Mac.command` | `.venv-portable/bin/python` |
| Windows | 双击外层 `首次安装_Windows.bat`，或执行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\install-portable.ps1` | 双击外层 `启动Demo_Windows.bat` | `.venv-portable\Scripts\python.exe` |

安装使用锁定的 Python 依赖和 `npm ci`。启动入口检查安装状态，移动后按需重建环境。默认打开 [TRACE](http://127.0.0.1:5180/)。本机端口由 `runtime.json` 定义。保留启动窗口，按 Control+C 停止它启动的服务。端口冲突时在原应用释放端口，或用 `launch-portable.py --frontend-port … --backend-port … --voice-port …` 指定一组空闲端口。使用 `--no-browser` 可手动打开页面。

## 本机模型与配置

在应用目录中，用上表的应用 Python 运行：

- `voice/setup_local_voice_models.py` 校验本地语音文件；加 `--download` 下载缺失或校验失败的固定文件。文件和来源在 `voice/MODEL-SOURCES.json`。
- `scripts/setup_local_landmarks.py --check` 校验本地视觉模型；移除 `--check` 安装固定模型。文件与来源在 `backend/app/vision/face-landmarker.json`。
- 无语音模型时可继续文字体验。没有有效的视觉模型时，应用按现有本地观察能力降级。

应用读取本目录的 `.env`。干净检出使用 mock 默认配置。需要远程文字时，从 `.env.example` 创建私有 `.env`，按供应商设置模型、凭据与 `ALLOW_REMOTE_AI`。本地语音工作进程无需 API 凭据。SQLite 默认位于 `data/users/beauty.sqlite`，日志位于 `work/portable-*.log`。启动后可运行 `launch-portable.py --doctor`，查看前端、API、模型加载和远程配置状态。

## 回归与回退

用应用 Python 运行 `-m pytest -ra`、`scripts/validate_kb.py`、`scripts/verify_runtime.py`。无语音模型的干净检出用 `scripts/verify_runtime.py --missing-voice`。在 `frontend` 下运行 `npm test` 和 `npm run build`。自测使用临时 SQLite、mock 设置和独立端口。

回退请从 `trace-baseline-20261107` 在另一目录检出源码。个人 SQLite、密钥和模型资源单独保存。备份 SQLite 时先关闭运行中的应用，使用 SQLite 一致性备份。阶段 2 及之后的计划与记忆格式可能无法由旧代码读取。使用升级前的库副本，并查阅各阶段的迁移与回退说明。

## 演示、验收与历史资料

本地演示、真实设备检查和交付包说明见 [交付复核手册](../docs/quality/release-runbook.md)。旧 README 可从 Git 标签 `trace-baseline-20261107` 查看。应用内 `docs/旧入口归档/` 只用于追溯旧版。
