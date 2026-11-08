# 本机语音 WebSocket 契约

浏览器从本机页面连接 `/local-voice/stream`。输入为 16 kHz 单声道 PCM 或小型 JSON 控制帧。语音工作者先发送 `ready`，浏览器以 `mode` 和递增 `epoch` 建立当前代次，收到同一代次确认后才发送本段音频。页面刷新、关闭或离开语音工作区需重新由用户开启。

- `capture` 的 `start`、`end` 带当前代次，与关键词进入同一录音缓冲。重复 `end` 不再提交。
- `transcribing` 表示转写开始，`transcript` 只在当前段识别成功时带文本返回。前端在当前代次内处理事件。
- 录音超限返回 `capture`、`discarded=true` 和 `reason=duration_limit`，提示 120 秒限制。空音频和无法识别的段落分别返回 `no_audio`、`unrecognized`，均不发送对话。
- 丢弃切换到新代次，旧音频和迟到结果无效。关闭结束设备、音频处理、连接与启动期限。暂停语音保留明确说明的本地唤醒路径，暂停课程不等于暂停语音。
