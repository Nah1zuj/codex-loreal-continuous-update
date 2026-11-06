# TRACE 换账户开发交接

## 从哪里继续

工作目录：`D:\AccessibleBeautyAgent\.worktrees\realtime-beauty-call`

开发分支：`trace-v5-realtime`

完整设计：`docs/superpowers/specs/2026-10-11-realtime-beauty-companion-design.md`

Task 1–7 实施顺序：`docs/superpowers/plans/2026-10-11-realtime-beauty-companion.md`

执行账本：`.superpowers/sdd/2026-10-11-realtime-beauty-companion/progress.md`

## 当前真实状态

2026-10-12 最新 UI：Phase 4 完成后已接入 TRACE 2.0 感官视觉层，保留业务/API/路由，原创数字雕塑、暖红线框、粒子苹果与人脸转场、段落自有背景、实时区域预览、Full Look 半身标注、双语关键标题与三种语言显示。后端158／前端134／build106modules／KB PASS。请先读 docs/TRACE_SENSORY_UI_REPORT.md 与 docs/TRACE_SENSORY_UI.md。3D 懒加载块仍有500KB警告；旧临时测试目录曾出现SQLite损坏失败，隔离重跑通过，根因未确立。实机语音/摄像头/读屏、OS reduced-motion、真实妆效准确率、GLB替换和低端性能 NOT_TESTED。新视觉覆盖此前 Story，不要再按下面历史“Story不改”的说明回退。

2026-10-12 Phase 4 最新：本轮功能主链已修补，计划与事件 SQLite 持久化，17项工具、自然逐步辅导、真实 DeepSeek、TTS文字回退、本地关键点原型、结束摘要与确认日志保存。后端158／前端129／build／KB PASS。必须先读 `docs/PHASE4_ENGINEERING_REPORT.md` 与 `docs/PHASE4_PROGRESS.md`；不要再按旧130／127状态重做，也不要改Story粒子。真人视觉、实机ASR/TTS/读屏 NOT_TESTED，专业课程全部待审核。此前某次回归挂起，后续已连续通过但根因未完全确认。


最新：功能补修独立提交 0e307b8（旧会话404恢复、大字实际覆盖）；随后 Story 视觉已完成，范围是 `/story` 与共用原创苹果标识。最终后端130 / 前端127 PASS，构建94modules PASS，KB PASS。报告 docs/STORY_GENERATIVE_REPORT.md。不要将粒子艺术当训练或真人视觉准确率。现本地 DeepSeek 8002 是新版功能，真人图片服务仍Mock。用户新UI说明已执行，无需再次从Task1重做。

Story 实现提交 2a7abad；之后文档提交只记录完成状态与证据，不改变运行代码。

V2 增量功能 A–G 已完成可在本机验证的修补：SSE、多轮、六项受控工具、分句 TTS/取消、本地新帧 UNCERTAIN 原型、48 段原创待审核教程、匿名拥有者隔离、确认日志原文与语音保存门控。最终后端 130 / 前端 122 PASS，build 与 KB PASS。实施详情 docs/v2_progress.md、docs/implementation_report.md；外部生产目标未全部实现，严格参照 docs/remaining_limitations.md。新 Story 创意提示的 UI 工作排在这些功能修补之后，不能重做业务逻辑。

更新于 2026-10-12。Task 1–7 已依次完成并独立提交，详细 RED/GREEN、复审与浏览器证据见执行账本。不要再按旧交接中“Task 1 未提交”的状态重新开发。

后续用户要求也已实现：真实 DeepSeek 文本辅导、语音优先入口、私人日历与待确认日志、双苹果 GPU 粒子与红色幕布、无实色框的流体排版、故事优先对话、自动日志草稿、来源核对后的全品类灵感。最新实现提交：`6772c4b94e53ef7f5affacfe19ba76ea9a7029d4`。

最新回归：后端 115 PASS；前端 17 文件/118 PASS；构建 88 模块 PASS；KB PASS。真实文本模型/故事/草稿/自然下一步已在浏览器验证；媒体拒绝、清理和切换为明确标注的模拟验收，真实硬件和真人视觉准确率仍 NOT_TESTED。

先阅读 `docs/TRACE_FLUID_APPLE_REPORT.md`、`docs/TRACE_VOICE_FIRST_JOURNAL_REPORT.md` 和账本尾部。知识库仍小，未建立完整商品产业链、专家审核的树林眼妆课程、认证多用户日志存储或训练数据集。

## Task 1–7 顺序

1. Speech provider：连续识别、迟到事件、TTS 完成与中断安全。
2. Call state machine：聆听、思考、朗读、恢复、暂停和结束。
3. Camera stream：独立摄像头同意、预览、切换与轨道清理。
4. Frame analysis：2–3 秒节流、单飞抽帧、远程帧单独同意。
5. React call shells：Voice 一次点击通话、Video 主画面和推荐旁栏。
6. UI 与语言：soft luxury 后现代视觉、克制粒子、纯中文/纯英文、哲思陪伴语言 Policy。
7. 全量测试、浏览器验收、隐私审计、文档与最终代码审查。

严格按顺序执行，因为后一个 Task 消费前一个 Task 的接口。每个 Task 遵循 RED → GREEN → 回归测试 → 独立提交。

## 继续开发前检查

```powershell
cd D:\AccessibleBeautyAgent\.worktrees\realtime-beauty-call
git status --short
npm --prefix frontend test
npm --prefix frontend run build
```

后续改动继续遵循 RED → 最小实现 → GREEN → 回归 → 独立提交 → 更新账本；原 Task 1–7 的完成状态不应被覆盖。

运行中的新版前端为 `http://127.0.0.1:5174/`，代理新版文本后端 `127.0.0.1:8002`。用户已在本次对话明确授权正常加载原项目配置用于 DeepSeek 文本，未授权真人帧外发。可使用 `scripts/run_realtime_text.py` 启动正常文本配置加载，不能检查或打印密钥。不要干扰原项目 8000 服务。所有图像提供方保持 Mock。

自动日志仅生成待审阅草稿；保存仍需明确勾选确认。推荐长期记忆另需既有 consent action，不能将 AI 摘要或人格猜测直接写入长期记忆。桌面 GPU 实际 1,048,576 点，窄屏 131,072，暂停/减少动态 32,768，无 WebGL 回退 6,000；不能声称所有设备均百万点或保证帧率。麦克风 RMS 默认关闭，仅用户单独启用时本地测量；AI 朗读仍是状态脉动。

## 语言能力路线

当前优先做 Policy、审核示例、RAG 和评估，不立即微调模型。中文与英文必须分别编写并分别测试。哲思表达采用“明确动作 + 最多一句克制反思”的结构，吸收自然、时间、选择和自我呈现等主题，但不直接模仿黑塞或其他作家的句法，不让修辞覆盖操作与安全信息。

只有在拥有足够的授权对话、人工评分标准、训练/验证/独立测试拆分后，才评估微调。不得把 Prompt 修改称为模型训练。

## 妆效视觉路线

先定义有限任务，再建立有授权真人 Gold Set、双人标注规范和按人物隔离的数据拆分；对现有本地/远程模型测量误报、漏报与 UNCERTAIN。没有 Gold Set 前不得宣称妆效准确率，MediaPipe landmarks 也不等于妆效判断正确。

## 必须保留的边界

- 不修改或输出 `.env` 和 API Key。
- 不发送真人帧到远程服务，除非用户对当次目标和服务明确同意。
- 不上传或保存整段录像。
- 不从画面推断残障、健康、真实情绪、气味或衣物纤维。
- 原项目目录中的未提交知识库和两个用户脚本属于用户，继续留在原目录。


## Latest: Vision MVP / local camera follow-up — 2026-10-12

Worktree and branch unchanged. Phase4 and TRACE2 UI were completed before this follow-up; do not restart Task1 or replace the UI. Commits: 7dba0c0 local evidence;3f65817 contextual Voice camera;1e55843 generation/expiry privacy;48e44d8 localization/frame scope. Final backend171PASS90.46s, frontend142PASS25.04s, build106modulesPASS15.56s, KB3/3/2/12/73/3 PASS. Existing lazy3D682.49KB warning remains.

Real DeepSeek text, same-session local camera pipeline, official pretrained MediaPipe geometry and masked LAB appearance rules are connected. No calibrated blush/coverage/beauty verdict and no training. Images remain in RAM and are not remotely uploaded or stored. Numeric history is bounded900s with30s sweeping; DELETE/new generation prevents late writeback. Text-only button/interrupt does not start ASR. Expert-reviewed makeup knowledge remains unavailable.

User explicitly approved this turn's actual camera check. Actual640x480 preview, two native checks yielding no_face/UNCERTAIN, and close readyState0/width0/height0 verified. NO real-person accuracy or before/after result: no face was present. Real mic/ASR/audibleTTS/screenreader/OS reduced-motion/physical denial/long adaptive loop remain NOT_TESTED. No new per-session remote human-image consent is inherited. App may normally load original existing config for authorized DeepSeek text; never inspect/output/change keys or.env.

Runtime frontend5174 unchanged, backend8002 restarted with final code. Original main project untouched. Final Voice view retains functional step2 with motion paused, camera off, temporary viewport reset. Full truth and next filming checklist: docs/vision_mvp_report.md, docs/real_device_validation.md, docs/filming_guide.md. Optional evaluation dependency: backend/requirements-evaluation.txt. Empty evaluation/calibration CLI correctly returns NOT_EVALUATED/NOT_CALIBRATED; no real labeled samples supplied. Prefer authorized data/error analysis and calibration before specialized-model research. Never label synthetic fixtures, Mock or prompt changes as actual vision accuracy/training.

## 2026-10-12 Reference UI checkpoint
Four real-data editorial screens, MakeupPlan-to-FullLook bridge, native single-frame
RAM-only positioning overlay, review-before-save journal. Backend176/front147/build/KB
PASS. Hardware not started before UI checkpoint; acceptance limitations documented
in docs/reference_ui_integration.md. No secret files read or changed.

## 2026-10-12 Hardware reference continuation
UI checkpoint282edf7 (ledger0b9407e). Optional local hardware package installed
editable in existing venv; web still works if absent. /devices owner-controlled,
/mirror display-only, pairing120s/lease30min/tokenRAM. Simulator explicitly labeled;
no physical compatibility claims. Full backend184/front150/build/KB PASS, current
localhost runtime backend8002/frontend5174 restarted for fresh route cache. Mirror
browser sync/disconnect verified on fictional session. Real mic/TTS, positive face
analysis, screen reader, production auth/TLS and physical devices remain unverified.
Docs: hardware/README.md, docs/reference_ui_integration.md, docs/filming_guide.md.

## 2026-10-12 Camera/photo entry fix
c0bc192 unblocks local consent without requiring a prior voice conversation.
Open camera -> allow browser camera -> allow local single-frame checks -> check;
adaptive keyframes are a separate opt-in. Independent photo picker: selection
only prepares in browser, consent+Check submits to localhost local analyzer.
Photo checks stop camera analysis first; unknown orientation prevents physical
left/right advice and photos cannot become a pre-application baseline. Remote
Mock consent stays disabled and is clearly marked as no real analysis.
187 backend /155 frontend/build PASS. Actual camera authorization controls and
real non-face photo rejection verified, not positive makeup accuracy. Keep all
vision/privacy limitations in docs/vision_mvp_report.md. Camera closed at end.

## 2026-10-13 Visual reconstruction checkpoint
65460fa reconstructs reference visual layer only, keeping existing API paths unchanged.
Safety tagtrace-reference-before-20261012=6287a00. Read docs/reference-fidelity-audit.md
and README reconstruction section for exact model licence, frame-count tiers and
known differences. Default /models/human.glb is CC BY3.0 Lee Perry-Smith source,
with visible footer attribution, no photographed-skin texture. Never describe it
as original anatomy or as the actual user's scanned digital twin. Apple/particles
are original and shader-driven. High205000/medium88000/low16800; actual low-tier
IAB60fps, high tier failed stable60. Pause/reduced-motion stops scene, no global
fixed canvas. Backend187/frontend156/build/KB PASS. UI-only task: no new physical
camera/ASR/TTS/positive-face accuracy or hardware validation. Existing local photo
and explicit adaptive-camera checks kept, camera/remote off at end. No secrets
inspected, changed or output. Main checkout unaffected. No push/deployment.

## 2026-10-13 Apple-only refinement
Latest implementation a339c3e; human and all page/business logic preserved.
Three coordinated fruit forms, sliced flesh/seed/rim, outward powder bloom,
continuous idle shimmer/noise and champagne ribbons. high205000/medium88000/
low16800 totals retained by redistribution; low tier increases dot size slightly.
Short contiguous browser sample60fps at205000, not a sustained benchmark.
Pause and reduced-motion still honored; do not disable animation by default just
for final screenshot capture. Final screenshot uses active idle animation.
Frontend157/buildPASS. No new backend or physical-media validation this turn.
No secret files modified, no remote human media; latest browser has camera off.
