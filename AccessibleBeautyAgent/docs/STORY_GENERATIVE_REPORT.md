# TRACE Story：功能先修补，再做视觉

日期 2026-10-12，工作目录 D:/AccessibleBeautyAgent/.worktrees/realtime-beauty-call，分支 trace-v5-realtime。

## 顺序与范围

原 Task 1–7 早已依次完成，不重复从旧 Task1 开始。新的 Master 功能说明按 A→G 完成可本机验收的增量修补，G 独立提交 5c6557b；功能回归 GREEN 后才开始 Story。视觉联调发现后端重启后旧会话 404 的回退缺口，先补两项失败测试并修复，独立功能提交 0e307b8，再继续 UI。新 Story 不改后端、数据库、模型配置或知识库。

本次沿用 design-taste-frontend 进行现有页面审计与编辑排版；原生 React/WebGL 构建艺术系统、GSAP 负责文字容器的克制入场。没有声称安装了 React Bits / Product Design 工具。用户指定配色、章节编号、原创苹果身份与代码粒子优先于通用模板规范。

Story 视觉独立提交：2a7abad。之后更新执行账本与交接，工作分支保留。

## 视觉实现

- `/story` 单独使用象牙白 #F8F3EF、酒红 #651E2C / #872F40、柔红 #B34A59、铜粉 #BC8475 / 香槟 #D8BDA4，文字 #29201F / #453936。保持原有章节、模块入口、故事与用户决定权。
- 两行中文主标题、英文高反差 Prata、中文 Noto Serif SC 展示字子集；本地加载并携带 SIL OFL 授权，不请求第三方字体。未包含的中文字符使用本机宋体类回退，正文保持可读无衬线。
- 新 TRACE 标识为原创对称果实刻线、开口中缝、细果柄和偏心叶片；24px 级别可辨识。标识在原有导航/页脚共用，未复制 Apple 公司标识。其他页面保留原双苹果和红色粒子幕布。
- Story 背景为可分辨的点，不绘制三角面、流体块或实色大球；分层透视、深度淡化与粒子自己的大小/颜色/透明度。主阅读列通过粒子透明度保护，没有叠加遮挡正文的色框。
- 标题 GSAP 仅移动容器少量像素、微调字距与可见透明度，读屏文本从开始就完整存在。章节以 IntersectionObserver 触发一次小幅移动，保持自然纵向阅读，不锁滚动。

## 粒子数学与状态

每粒子拥有 typed-array position / velocity / acceleration / target / home / style；style 保存色彩采样、深度层、大小、透明度。逐点独立伪随机扰动，并用固定 seed 验证稳定性。

`v ← exp(-2.1 dt) v + F dt + σ sqrt(dt) ε`；`x ← x + v dt`。

dt 最大 1/30 秒，速度各轴限制 ±0.65，空间边界与回归 home 的弹簧约束避免漂走。鼠标力只作用于半径 0.42 场景单位内、二次衰减。没有用所有粒子共享正弦波伪装 Brownian。

显式 IDLE / HOVER / LISTENING / THINKING / SPEAKING / TRANSITIONING / REDUCED_MOTION。空闲分散云；聆听时约 80% 点渐聚苹果、其余仍分散；思考是小幅独立轨道；朗读保留雕塑并轻微随机漂移；结束后平滑散开。没有伪造输入音量。浏览器 TTS 无 PCM，SPEAKING 仅表示真实播放状态，不称实际声能；用户显式勾选后，仅在聆听时启用本地麦克风 RMS，音频不录制/上传。

Story 对话折页复用原 CallController / SSE，支持实际文字发送、语音开始/暂停/结束与音量测量的单独开关，不自动请求麦克风。Ended 后文本也能重新启动控制器，文字发送不先启动识别。真实英文虚构故事已通过该入口收到 DeepSeek 非预设回复，并显示 SPEAKING / speech-state-only；未把供应商状态当可听音质验收。

## 实际预算和性能

HIGH=12000、MEDIUM=6000、LOW=1800、REDUCED=1200；窄屏实际 LOW。DPR 封顶 1.5，移动 1。采用单 canvas、一次 GL POINTS draw / 帧，typed arrays，不按点更新 React。连续活动样本帧间隔超过 30ms 时降级；超过 250ms 的后台节流不当作 GPU 过载。不强制 Story 使用百万点；首页原百万绘制仍保留。

真实浏览器桌面活动采样：12000 点、约 60 FPS，平均帧间隔约 16.66ms，P95 16.8–16.9ms，CPU 更新/提交约 4.1–5.0ms。CPU typed-array 字节实际 912000；GL position/style 缓冲内容最低 336000 字节，不是完整 GPU 显存测量。背景标签曾被节流到约 1 FPS，报告明确区分；没有拿后台值宣称流畅。

键盘 Enter 暂停后：running=false、state=REDUCED_MOTION、1200 点、drawFrames=1；隔一段时间仍为 1，FPS=0，无持续 RAF。恢复可继续；visibility 隐藏停止，恢复 dt 限制；卸载清理 RAF、监听、观察器、GL 程序/缓冲和本地音量流；context lost 停绘制，恢复重建 GL。真实 WebGL context-loss 操作和长期低端设备测试仍未实施。

## PASS / FAIL / NOT_TESTED

PASS：最终后端 130 项（39.90s，全供应商 Mock / 无远程调用），前端 19 文件 / 127 项（9.92s），TypeScript/Vite 构建 94 modules（6.66s），KB 3 LOOK / 3 ROUTINE / 2 REFERENCE_CASE / 12 PRODUCT / 49 ACCESSIBILITY_GUIDANCE / 2 SOURCE。新增粒子 3 项稳定/局部鼠标/静止测试先 RED 再 GREEN。

PASS：真实 DeepSeek 8002 文本联调两轮虚构内容；最终首 delta 5345 / 8115ms，总 8390 / 11039ms，第二轮真实 search_knowledge/get_memory 调用成功；工具轮 usage 全量累计 5078 tokens（1879+3199），未配置费用，不编造价格。未开始妆容步骤，未保存虚构聊天为持久日志。前一次实测更快，不能承诺固定延迟。

PASS：实际 Story HOVER、真实文字/TTS 状态绑定、键盘暂停、中文/英文独立 UI，390 宽 viewport client/scroll 都为 375（桌面 1440 viewport client/scroll 都为1425），无横向溢出；窄屏大字正文实测24px、高对比生效；Voice/Video 入口仍在，视频页默认相机/远程检查关闭。历史原文保持写作时语言，不自动翻译用户原文。实际日志确认、单独原文勾选、刷新和原文读取此前已验收，虚构测试记录已精确清理。

FAIL（已处理的历史）：V2 B 阶段5个旧前端 fixture失败；G 首次 TS role推导失败；新增404恢复两项 RED；一次绕过 pytest 默认 basetemp 后，数据库路径保护拒绝系统 Temp（28 failed / 54 errors），恢复项目内 basetemp 后130 PASS，没有放宽保护。开发热更新出现一次重复 createRoot 警告，已完整重载；未做连续热更新压力验收。当前最终回归无未解决测试失败。

NOT_TESTED：真人视觉准确率、校准置信度、精确 landmarks、实体麦克风 ASR/可听 TTS/相机、OS reduced-motion、NVDA/JAWS、长期低端硬件/完整 GPU 显存、生产账户、多设备同步、其他兼容模型供应商。权限拒绝/媒体清理/模式切换的自动化 PASS 来自模拟，不能代替硬件验收。未做模型训练或真人图片上传，也没有全品类 SKU/库存/购买链接。

## 修改文件

前端：App.tsx（Story 接现有 controller / 条件背景）、pages/Story.tsx、components/StoryParticles.tsx、components/AppleMark.tsx、realtime/storyField.ts 与测试、styles/story.css、main.tsx 的 CSS 导入、public/fonts 与许可证。功能后续修补另包含 api/stream.ts / stream.test.ts、CallExperience.test.tsx 和 companion.css 阅读偏好覆盖。

功能后端及全部10项工程说明见 implementation_report.md / architecture_v2.md / api_reference.md / knowledge_sources.md / privacy_and_permissions.md / accessibility_checklist.md / testing_report.md / deployment_guide.md / remaining_limitations.md / architecture_audit.md。非秘密 config.example.toml 为说明文件，不读取实际 .env。

验收截图：trace-story-desktop-zh.png、trace-story-desktop-en.png、trace-story-mobile-zh.png、trace-story-mobile-en.png；实际日志证明 trace-v2-journal-proof.png 标明虚构验收。保留用户正在使用的页面，另留独立 Story 验收页，重置临时 viewport；开发文字后端 8002 与 Vite 5174 保持，临时测试8003关闭。
