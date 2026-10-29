# TRACE V2：修改前审计

日期：2026-10-12。分支：trace-v5-realtime；基线提交：959d68f。

## 现状与保留边界

前端为 React 19、TypeScript、Vite、GSAP。保留现有白红暖色、双苹果 WebGL 粒子、流体排版、导航、中文/英文单语言界面、暂停动效与 reduced-motion。入口与页面分别在 App.tsx、Entry、VoiceCall、VideoCall、FullLook、Journal、BeautyMemory、AdminApp。本次升级将状态和接口接到这些页面，不另建通用聊天仪表盘。

后端为 FastAPI/Pydantic，AgentHarness 负责明确步骤、相机和记忆同意的状态机。DeepSeek 已能真实回答故事与当前步骤，但采用同步 JSON 完整回复；缺少逐字流、完整多轮角色上下文、可取消请求和工具调度。Qwen/DeepSeek 为服务端配置；浏览器不持有密钥。Mock 仍是测试与开发默认，不能作为生产成功。

会话保存在 SessionStore 内存，重启丢失；前端仅保留 session_id 与近期 30 条文字。长期偏好和用户确认的日志为 SQLite JSON 表，没有版本化迁移、持久文字转录与留存机制。journal/profile/memory/session 的 user_id 来自请求，不能隔离不同浏览器用户，这是优先修复项。admin_enabled 只开关路由，不是管理员认证。生产部署需要真正账户认证，匿名浏览器身份只能作为本地私密模式。

浏览器 Web Speech 提供识别和朗读，已有手动打断、暂停、停止和迟到回调保护。识别可能由浏览器供应商远程处理，应明确披露；不是已部署的服务端 STT/VAD。真实设备、连续双工打断、断网、读屏体验尚未全面验收。Canvas/AudioContext 的音量读取仅本地处理，不保存或上传声音。

相机明确授权、本地预览、缩小 JPEG、2.5 秒节流、单请求与迟到结果拒绝已经实现。没有整段录像。当前视觉推理是 Mock；OpenCV Haar/眼框仅作人脸/光照/模糊门控，不能作为精确 landmark 或妆效识别。远程模型置信度也未经金标准校准。真实图片与帧本次没有上传授权，不能用真人帧验证。需要本地原型、fresh-frame 标识、观察与判断分离、校准缺失时明确 UNCERTAIN。

知识库有原有 JSON canonical schemas、版本检查、CSV/XLSX 草稿导入、人工审核与混合检索。当前 3 LOOK、3 ROUTINE、2 REFERENCE_CASE、12 PRODUCT、1 ACCESSIBILITY_GUIDANCE、1 SOURCE；多数为 demo。Mock embedding 为本地近似，不能称训练或真实语义模型。生产 verified-only 策略应保留。缺少带使用权约束的文本/视频片段导入与可追溯教程集合；公开可读不等于允许复制。不得自动抓取未知使用权资源或保存第三方整段视频。

API 还包括标签释读、产品比较、六领域 FullLook 规划与修订；这些工作接口和知识后台保留。所有外部依赖失败必须显式报错，不能换成未标识的假 AI 回复。

## 依赖、配置与部署

已安装依赖：FastAPI、uvicorn、httpx、numpy、OpenCV headless、Pillow、openpyxl、pytest；前端 React/GSAP/Vitest。尚无 MediaPipe 模型、人工标注授权数据集、可校准妆效金标准、生产账户供应商或服务器流式语音供应商。不要自动下载模型/真人数据。

配置名称来自 config.py，未读取配置值：MODEL_PROVIDER、VISION_PROVIDER、READING_PROVIDER、REFERENCE_PROVIDER、ALLOW_REMOTE_AI、RESEARCH_MODE、ADMIN_ENABLED、DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL、DEEPSEEK_MODEL、DEEPSEEK_VISION_MODEL、EMBEDDING_PROVIDER、RERANKER_PROVIDER、VOICE_PROVIDER、DEVELOPER_MODE、DASHSCOPE_API_KEY、QWEN_BASE_URL、QWEN_CHAT_MODEL、QWEN_VISION_MODEL、QWEN_EMBEDDING_MODEL、REMOTE_TIMEOUT、CONFIDENCE_HIGH、CONFIDENCE_MIN、MEMORY_PATH、PRODUCT_*_WEIGHT。实际 .env 和密钥均未查看、打印或修改。沿用原配置的 DeepSeek 文本调用已有用户授权。

本地前端 5174 通过代理访问后端 8002；仅 loopback 运行。生产还需 HTTPS、安全 cookie、反向代理不缓冲 SSE、备份、数据库访问保护、管理员外部认证与明确数据保留策略。没有本次上线授权。

## 顺序与验证

A 审计/基线 → B 流式会话/工具/上下文 → C 语音/转录 → D 本地视觉/新帧 → E 使用权约束知识导入/RAG → F 用户隔离/记忆/日志/日历 → G UI 联调/回归/部署文档。

基线前端：17 文件、118 测试通过。后端基线运行结果另记 testing_report。所有新增行为先失败测试，再最小实现与回归。接口测试不冒充真实麦克风、真人视觉准确率或模型训练。
