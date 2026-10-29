# TRACE V2 架构

2026-10-12，trace-v5-realtime。沿用 React/TypeScript/Vite/GSAP 与 FastAPI/SQLite，未改为另一个产品。

浏览器 → 同源 `/api` 代理 → BrowserIdentityMiddleware → ConversationService → 允许的本地工具 / 服务端模型 transport → SSE。AgentHarness 仍掌管步骤与授权状态；模型不能授予相机、保存或分享同意。六个工具为 search_knowledge、get_look、create_plan、current_step、get_memory、advance_step；参数严格校验、最多两轮工具处理和一轮最终回复。推进步骤需要明确用户指令。

普通对话不必选择妆容。当前步骤、来源审核状态、已确认偏好加入上下文；最多 30 条 / 16000 字符，采用裁剪而非摘要压缩。会话与未确认转录在 RAM，最多 200 个会话，闲置两小时过期；重启失去未确认上下文。确认偏好、私人日志及单独授权保存的原文使用增量 SQLite schema migrations。

浏览器 Web Speech 识别 → 文字 → SSE → 完整句子队列 → 浏览器 TTS。手动打断会 abort 网络、识别和语音，迟到回调失效。识别可能由浏览器供应商处理，不是自建 STT；尚无全双工 VAD。浏览器 TTS 不提供 PCM，朗读动效只表达状态。

本地视觉单独请求授权，单帧发送至本应用后端 OpenCV；不调用第三方视觉模型，不保存照片。新帧 ID / 时间戳检查、3 秒低频检查、单请求丢弃忙帧、退出 abort 与基线清理。人脸质量门控及矩形区域 Lab 统计是未校准原型，始终 UNCERTAIN，不是妆效准确判断或精确 landmarks。

现有 canonical JSON 知识库及版本、人工审核、verified-only 生产检索保留。新的原创文本导入器先检查使用权、去重，再生成待审核草稿；不下载视频或未知权利图片。已有 full-look、标签、比较、记忆与日历接口继续使用。
