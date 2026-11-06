# 阶段 0 基线证据

代码 `trace-baseline-20261107` · 2026-11-07 中国标准时间 · macOS arm64 · Python 3.12.15 · Node 26.10.0 · npm 11.19.1。后端使用 mock、合成输入及项目内独立临时数据库；前端使用 jsdom。模型核对使用本机已有文件。

| 测试 | 结果 | 命令及现象 |
|---|---|---|
| 测试库位于项目之外 | FAIL | `MEMORY_PATH` 指向系统临时目录，pytest 收集阶段 13 处 `MEMORY_PATH must stay inside project directory` |
| 后端回归 | PASS | `python -m pytest --basetemp=<项目内work临时目录> -ra`，193 通过、1 跳过 |
| Windows 旧启动测试 | NOT RUN | Windows 专用检查在 macOS 跳过 |
| 前端回归 | PASS | `npm test -- --reporter=dot`，35 个文件、182 项；jsdom 无 WebGL |
| 前端构建 | PASS | `npm run build`，有超过 500 kB 的分块警告 |
| 知识库检查 | PASS | `python scripts/validate_kb.py`，退出码 0 |
| 本地模型文件校验 | PASS | 语音清单中 9 个文件及视觉模型文件，大小与 SHA-256 均匹配 |
| 双平台真实媒体、远程文字/标签、读屏及目标用户 | NOT RUN | 需要各阶段实体设备、受控服务、人工审核或试用证据 |

可从原标签分别执行测试和构建。后端原始基线复现时应设置 `MODEL_PROVIDER=mock`、`ALLOW_REMOTE_AI=false`，并显式指定项目 `work` 内的新 `MEMORY_PATH`。
