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

回退请从 `trace-baseline-20261107` 在另一目录检出源码。个人 SQLite、密钥和模型资源单独保存。备份 SQLite 时先关闭运行中的应用，使用 SQLite 一致性备份。阶段 1 未改变数据库结构。

## 历史资料

以下为旧版本记录，保留历史方案和测试说明。当前操作以上文为准。

<details>
<summary>查看历史 README</summary>

# TRACE · 让美的信息，在感官之间流动

Current `trace-v5-realtime`: Phase 4 coaching is followed by the TRACE sensory UI layer. The current interface preserves existing routes, voice, makeup, Full Look and confirmed memory while adding original Three.js sculpture, wireframe, points, apple/face morphs and section-owned backgrounds. See [visual implementation and repository comparison](docs/TRACE_SENSORY_UI.md), [visual acceptance](docs/TRACE_SENSORY_UI_REPORT.md), [Phase 4 report](docs/PHASE4_ENGINEERING_REPORT.md) and [current handoff](docs/ACCOUNT_SWITCH_HANDOFF.md). The historical Phase 3 notes below describe the earlier demo, not the current provider configuration. Selected repositories: [Three.js](https://github.com/mrdoob/three.js) for mature MIT geometry/rendering and the existing [GSAP](https://github.com/greensock/GSAP) for restrained motion; React Three Fiber/drei/Lenis were researched but not added.

Phase 3 redesign of Accessible Beauty Agent / 无界体验家. Open `/demo` for the Dinner workflow; `/story` for the concept. See [Demo guide](docs/TRACE_DEMO_GUIDE.md) and [Phase 3 report](docs/PHASE3_ACCEPTANCE.md). AI calls remain disabled; all image demonstrations are labeled simulations.

# Accessible Beauty Agent · 无界体验家

面向盲人及低视力用户的语音优先美妆 Hackathon MVP。通过场景意图选择 Look、逐步指导、经过同意的三帧检查、偏好反馈与长期记忆，演示完整流程。**不评价美丑，不评分，不保证妆容效果。**

实际项目路径：`D:\AccessibleBeautyAgent`。无需付费 API 即可运行。当前知识与产品全部是 **SAMPLE DATA**，产品品牌为虚构数据，不构成真实产品声明。

## 快速启动（Windows PowerShell）

需要 Python 3.11+（本机验证 3.13.11）、Node 22.12+（本机验证 24.13.0），网络仅用于第一次安装依赖。

```powershell
cd D:\AccessibleBeautyAgent
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-dev.ps1
```

启动脚本检查端口、隐藏启动两个服务、等待 health 和前端就绪，再打开浏览器。保留 PowerShell 窗口，Ctrl+C 会关闭它启动的两个进程。日志位于 `work/`。端口冲突时拒绝启动，不关闭其他程序。

- 前端：<http://127.0.0.1:5173>
- 后端 health：<http://127.0.0.1:8000/api/health>
- 自动 API 文档：<http://127.0.0.1:8000/docs>

本机已安装依赖，直接运行第二条启动命令即可。`-NoBrowser` 可禁止自动打开浏览器；`-Setup` 可在启动前执行安装。

## Mock 演示

`.env` 默认：

```dotenv
MODEL_PROVIDER=mock
VISION_PROVIDER=mock
EMBEDDING_PROVIDER=mock
RERANKER_PROVIDER=mock
REFERENCE_PROVIDER=mock
ALLOW_REMOTE_AI=false
VOICE_PROVIDER=browser
DEVELOPER_MODE=true
```

1. 点“开始对话”，输入“今晚有一个正式 dinner，我想精致一点但别太成熟”。
2. 匹配 `soft_formal`，点“开始步骤”，再“下一步”到腮红。
3. 点“用相机检查”，确认“同意本次检查”。
4. 无相机演示：选择 BOTH / LEFT_ONLY / UNCERTAIN 等状态，运行模拟三帧检查。**模拟不代表照片观察。**
5. 或打开真实相机、拍摄三帧。真实图像始终执行本地门控；mock 妆容结论仍明确标为模拟。
6. 继续唇妆与可选检查，输入偏好反馈。记忆候选展示后，点同意保存或不保存。
7. 在“美妆记忆”查看/删除记录。开发者面板可显示状态、工具、视觉结果、置信度、检索文档与错误，并可隐藏。

麦克风不是必需。浏览器支持时，可在阅读语音说明后点“按键语音输入”；依浏览器实现，识别可能调用浏览器厂商服务。TTS 使用浏览器 speechSynthesis；文本与手动按钮始终可用。

## 架构

```text
React / Camera / browser voice
       ↓ JSON HTTP (Vite /api proxy)
FastAPI → SessionStore → AgentHarness
                        ├ Look/Product tools → canonical JSON KB
                        ├ HybridRetriever → parent/child + filters + BM25/vector
                        ├ VisionService → local face gate → 3 provider results → consensus
                        └ MemoryStore → SQLite (only with explicit consent)
```

模型只提取意图；选定 Look、产品、流程、视觉结果、记忆操作都来自工具。模型不能授予相机/长期记忆同意。会话保存在进程内，重启会清空；长期记忆保存于 `data/users/beauty.sqlite`。不持久化相机图片或录音。

### 关键模块

- `backend/app/agent/`：可执行状态机、受限工具 Harness、mock/Qwen 意图适配器。
- `backend/app/rag/`：KB 校验、父子切分、本地向量与 BM25 类检索、可选 reranker。
- `backend/app/vision/`：OpenCV 本地人脸与眼部定位门控、视觉适配器、三帧多数投票、阈值语言策略。
- `backend/app/memory/`：SQLite 体验记忆与按记录重建的 Profile Memory。
- `frontend/src/`：语义 UI、单次相机同意、三帧 JPEG、浏览器语音抽象与文本回退。

## 单独运行

后端（从项目根目录）：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

前端（另一个窗口）：

```powershell
cd D:\AccessibleBeautyAgent\frontend
npm.cmd run dev
```

## 测试、构建、数据校验

```powershell
cd D:\AccessibleBeautyAgent
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\validate_kb.py
.\.venv\Scripts\python.exe scripts\rebuild_index.py
cd frontend
npm.cmd test
npm.cmd run build
npm.cmd audit
```

`pytest` 临时数据在项目 `work/pytest`，不写实际用户记忆。`backend/requirements-lock.txt` 与 `frontend/package-lock.json` 固定本机通过验证的版本。运行 `setup.ps1` 使用 Python 锁文件、npm ci。

## 远程模型（当前关闭）

当前 `ALLOW_REMOTE_AI=false`，禁止任何模型外部请求。优先接入 DeepSeek 的说明见 `docs/KNOWLEDGE_BASE_WORKFLOW.md`；以下 Qwen 配置仅保留兼容参考，启用还必须设置 `ALLOW_REMOTE_AI=true`。编辑根目录 `.env`（不要提交），设置 `DASHSCOPE_API_KEY`、对应地域的 `QWEN_BASE_URL` 与已开通的模型名，然后将所需 Provider 改为 `qwen`。可独立启用语言、视觉、embedding，其他部分继续 mock。语言和视觉走 `/chat/completions`，embedding 走 `/embeddings`。

```dotenv
DASHSCOPE_API_KEY=your-key-here
QWEN_BASE_URL=your-regional-openai-compatible-base-url
QWEN_CHAT_MODEL=qwen-plus
QWEN_VISION_MODEL=qwen-vl-plus
QWEN_EMBEDDING_MODEL=text-embedding-v3
MODEL_PROVIDER=qwen
VISION_PROVIDER=qwen
EMBEDDING_PROVIDER=mock
```

根据 [Model Studio 官方兼容接口文档](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope) 选择工作空间与地域 URL；key 与 endpoint 必须匹配。示例模型名需以你的控制台支持列表为准。密钥仅由后端读取。没有凭据时保留 mock；显式配置远程 provider 却缺少 key 时返回配置/服务错误，不伪造远程成功。

Qwen chat/vision/embedding HTTP 适配器已实现，**未用真实凭据验证**。远程 reranker 是注入式扩展接口；Qwen realtime/WebRTC 是 **PLACEHOLDER**，不是完整实时语音。现成浏览器 TTS/PTT 与文本可运行。

## 替换真实 Beauty KB

按 `docs/KNOWLEDGE_BASE_GUIDE.md` 准备下面规范 JSON 文件，保留同一结构即可替换内容：

- `data/knowledge/looks.json`：新 Look、场景、避免项与 routine_id。
- `data/knowledge/routines.json`：可朗读的单步指令、慢速/重复/原因、visual_task。
- `data/knowledge/reference_cases.json`：人工审核的结构化图片/视频帧记录。
- `data/knowledge/products.json`：可核对来源的产品属性/声明；缺失字段设 null/空列表。
- `data/knowledge/accessibility_guidance.json`：带来源的无障碍指引。

新增 Look 时同步加入 routine，并让产品/reference 的 look_id 指向已有 Look。修改后先 validate，再通过后台 Rebuild 即时刷新；CLI rebuild 后重启后端。正式展示可隐藏 Debug；`DEVELOPER_MODE=false` 禁用绕过真实门控的模拟场景。若仍使用 mock，所有结论依旧显示模拟标识。

## 已知限制

- OpenCV Haar 人脸/双眼代理门控不是 MediaPipe 精确姿态估计。光照、眼镜、遮挡、角度可能误拒绝；未用真实多样人脸数据校准。
- mock 向量是哈希词袋代理，不是学习型语义 embedding；可切到 RemoteEmbeddingProvider。向量线性扫描适用于小型 KB。
- 索引快照持久化在 `data/index.json`；启动从规范 KB 自动重建内存索引，避免快照陈旧。
- mock 意图是确定性关键词规则；复杂自然语言依赖远程模型。对细腻对称性、梯度、毫米边界、情绪不做判断。
- 本机单用户开发 API，无账号认证、生产授权、多实例会话、部署监控。只监听 loopback，不应直接对公网开放。
- 浏览器摄像头、麦克风和语音服务受硬件、权限、浏览器及网络影响；未实际开启本机相机/麦克风验证硬件。

更多细节见 `docs/ARCHITECTURE.md`、`docs/API.md`、`docs/RUNBOOK.md` 和 `docs/DEVELOPMENT_STATUS.md`。

## Phase 2 知识研究工作台

打开 [/admin/knowledge](http://127.0.0.1:5173/admin/knowledge)、[/admin/references](http://127.0.0.1:5173/admin/references)、[/admin/rag](http://127.0.0.1:5173/admin/rag)。已实现 CSV/XLSX 导入、人工审核与历史保护、图片草稿、视频选帧、可读父子 RAG、实时索引重建和多通道调试。生产只使用审核后的非演示数据。新增规范来源文件 `data/knowledge/sources.json`。

操作见 [知识研究流程](docs/KNOWLEDGE_BASE_WORKFLOW.md)、[审核清单](docs/KB_RESEARCH_CHECKLIST.md)、[UI 修改入口](docs/UI_CUSTOMIZATION.md)。


### Local Vision MVP (2026-10-12)

Voice can open a camera inside its existing session. Explicit local checks use the optional pretrained MediaPipe runtime before conservative quality gates and masked LAB appearance rules; image bytes are neither stored nor sent to third-party vision models. This does **not** establish blush coverage, cosmetic attribution or calibrated accuracy. Default remote image-provider functionality remains separate and requires its own consent.

Read [engineering report](docs/vision_mvp_report.md), [real-device evidence](docs/real_device_validation.md), [filming checklist](docs/filming_guide.md) and [evaluation protocol](docs/vision_evaluation_protocol.md). The latter includes consent-separated label schemas and offline metrics/calibration; no training or real labeled dataset was supplied. Install only the optional offline evaluator dependency with `python -m pip install -r backend/requirements-evaluation.txt`. Core local model setup remains `scripts/setup_local_landmarks.py`.

## Reference UI and optional hardware (2026-10-12)

Home, Voice, Makeup and Full Look now use the reference editorial composition with
actual session data. Original procedural digital sculpture and category illustrations
replace real portrait/product photography; they are explicitly labeled illustrations.
Read [UI acceptance](docs/reference_ui_integration.md) and [hardware setup, security
and unsupported adapters](hardware/README.md). Devices and browser mirror routes
are `/devices` and `/mirror`. Install the isolated local package with
`python -m pip install -e hardware`; existing web routes work without it.
No device SDK or physical lighting/camera integration has been validated.
Hardware architecture and simulator implemented; physical device integration not yet validated.

## Reference B reconstruction (2026-10-13)

The visual layer uses Three.js (MIT), BufferGeometry/ShaderMaterial particles,
GLTFLoader and MeshSurfaceSampler from https://github.com/mrdoob/three.js.
No additional rendering framework: the existing React/TypeScript stack and
local audio-energy lifecycle remain. Three.js already ships the mesh loader,
surface sampler, efficient points and wireframe necessary for this implementation;
adding React Three Fiber or postprocessing would duplicate the existing renderer.
Noto Serif SC is self-hosted via @fontsource/noto-serif-sc (SIL OFL1.1), alongside
existing Cormorant Garamond. Font licence: frontend/public/fonts/NotoSerifSC-OFL.txt.

Human asset: “Infinite, 3D Head Scan” by Lee Perry-Smith, CC BY3.0, distributed
in the Three.js examples. https://github.com/mrdoob/three.js/tree/dev/examples/models/gltf/LeePerrySmith
Source licence: https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/LeePerrySmith/LeePerrySmith_License.txt
404976-byte mesh copied to frontend/public/models/human.glb; SHA256
402b8a8ac9f03232e6d64b5962929703a069daf99d3c49ac8eb0e48bedc9c576.
Material/textures replaced by warm ivory; topology subdivided for wireframe only.
Body extension and apple/fields are original procedural work. Visible attribution
is in the footer. Replace /models/human.glb with an appropriately licensed mesh;
no external model fetch at runtime. This artwork is not the user's digital twin.

High hero:205000 points; medium:88000; low/mobile:16800. Voice/makeup only render
human points (35000 high,18000 medium,3500 low); invisible apple fields are not
allocated for them. Measured IAB low hero60fps/16.7ms, high density not stable60;
adaptive quality trades fidelity for performance. Every scene belongs to its
section and stops offscreen/hidden/reduced-motion. No skin photograph, full-page
raster substitute, remote human frame, fake confidence metric or training claim.

Reference measurements, iterations, real screenshots and remaining differences:
docs/reference-fidelity-audit.md. Existing API, voice/vision consent, makeup/RAG,
FullLook, memory/calendar and optional hardware remain. The generated target has
anatomy/thumbnail details different from this licensed mesh and original SVGs;
this implementation does not claim pixel-perfect equality.

## Living apple refinement — a339c3e
Current apple atmosphere replaces the former single isolated cutout with three
coordinated particle forms (main cut surface, smaller whole fruit, floating slice),
controlled outward bloom and warm luminous ribbons. Figure/layout/API unchanged.
Layer high/medium/low: apple34000/14000/2600; slice18000/8000/1600;
burst22000/9000/1400; plume28000/10000/1600; human35000/18000/3500;
ambient28000/12000/1800; orbit9000/4000/700; ribbon10000/4000/1600;
highlight3000/1000/400; satellite12000/5000/1000; fragment6000/3000/600.
Totals205000/88000/16800. Extra forms share the existing scene/typed buffers.
Noise, phase shimmer, fade-wrapped outward travel and local pointer fields animate
in idle; human shader behavior stays unchanged. Reduced-motion/pause remains.
157frontend/buildPASS. Browser time1.866->51.483 and contiguous60fps sample;
sparse rAF samples excluded with explicit insufficient-sample flag. Long-running
FPS and physical audio response not verified. No new dependencies or model asset.


## 2026-10-20 本机语音起止词更新

倾听与映照页保留麦克风连接，本地检测“开始”，说出需求后以“结束”提交。
等待时仅执行本地关键词检测，不调用普通语音转写，也不提交对话服务。
内容只在内存中暂存，听到结束后本地转写，剔除起止词及区间外文本，再提交现有对话服务。
进入播报/思考时不接受普通语音；完成回应后回到等待开始。
单段超过120秒而未结束会丢弃，不自动发送。切换页面、暂停或关闭麦克风会清空未提交内容。
首页的原有“可以开始”入口保留。文字与按钮操作不受此规则影响。

首次加载此更新必须停止原启动终端并重新双击第一层“启动正确版本.command”，然后刷新Chrome。
前端176项测试通过，TypeScript及生产构建通过；本地音频门控6项测试通过。
真人对“开始/结束”的识别准确率、噪声与扬声器回声尚待实际试用。
本机已核对Chrome网站许可和macOS摄像头许可均开启，并观察到页面显示摄像头已开启。
备份：项目根目录下“备份/20261020_语音起止词实施前”。

</details>
