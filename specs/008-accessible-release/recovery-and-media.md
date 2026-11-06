# 长会话、异常重启与媒体资源验证

**对应** FR-803、T802 的软件部分。2026-11-07（北京时间），macOS 26.3，Python 3.12.15，Node 26.10.0，Chrome 156.0.8078.81。测试使用本轮集成工作区、回环地址、独立端口与临时 SQLite。文字为 mock 模式，视觉和语音使用本机实际加载的模型。输入为合成图像、静音 PCM 或 Chrome 模拟媒体流。

| 检查 | 结果 | 证据 |
|---|---|---|
| 较长教学会话 | PASS | 对真实本机 SSE 接口发送 120 条不推进课程的消息，每次均成功完成，计划 ID、版本和步骤保持不变。临时对话窗口为 30 条、未超过 16,000 字符，未持久化。 |
| 后端进程崩溃与资源释放 | PASS | 脚本校验后台进程是隔离启动器的子进程后模拟 SIGKILL。启动器报告异常，前后端及语音三个端口释放，打开的语音连接关闭。 |
| 同库重启恢复 | PASS | 重启同一隔离 SQLite 后恢复计划步骤、版本与已提交事件。重放原事件不推进。临时对话、视觉结果和旧媒体授权均未恢复，语音连接数为零。 |
| 本机语音服务连接清理 | PASS | 真实回环 WebSocket 连通、发送静音 PCM 并关闭，重复三次后连接计数均回到零。 |
| 浏览器相机及麦克风清理 | PASS（模拟媒体） | Chrome 连接实际本机服务。关闭相机释放视频流、清除后端观察，刷新后必须再授权。麦克风重复开启和关闭三次，所有跟踪音轨结束，语音服务连接回到零。监测的 `pagehide`、`visibilitychange`、`online`、`offline` 和 `beforeunload` 监听数量稳定。 |
| 空闲会话的流锁 | PASS | 空闲锁改为弱引用。同一浏览器身份下 20 个独立会话请求完成后，滚动上下文仍可用，锁表无空闲项。 |
| 物理设备与长期性能 | NOT RUN | 以上覆盖指定流程与连接回收。物理麦克风、摄像头、Windows、VoiceOver/NVDA 和长时间负载下的资源趋势需要另测。 |

## 复验

1. 在应用目录运行 `.venv-portable/bin/python scripts/verify_recovery.py`。脚本只启动和中断自己创建的隔离服务。当前崩溃注入命令使用 Unix `ps` 和 SIGKILL。
2. 用隔离启动器及 Chrome 临时配置，按 [阶段 5 验证步骤](../005-local-vision/verification.md) 运行 `node scripts/verify_local_vision_browser.mjs APP_URL CHROME_DEBUG_URL --media`。
3. 运行 `.venv-portable/bin/python -m pytest tests/test_conversation_lifetime.py -ra`。

目录移动与缺模型的真实本机证据见 [运行基线](../001-runtime-baseline/verification.md)。浏览器断线后查询原命令并继续使用的证据见 [会话验证](../002-session-control/verification.md)。本记录仅关闭 T802 的对应软件检查。
