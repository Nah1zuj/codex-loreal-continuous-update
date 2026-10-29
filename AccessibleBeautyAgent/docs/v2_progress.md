# V2 执行账本

- A：已完整读取新工程说明并审计仓库，基线后端 115 / 前端 118 PASS。架构审计独立提交 0d08e4b。
- B RED：流式路由 404、工具模块缺失、SSE parser 缺失，3 个后端测试失败；前端 stream 模块缺失，测试收集失败。
- B GREEN：3 个后端测试和 2 个前端流式测试通过。新增真实兼容接口 SSE、多轮角色上下文、四项 allowlist 工具、错误与取消处理、实际首 token/总耗时/供应商 usage 记录。现有 UI 接流式文字，不重做视觉。后端完整回归 118 PASS，构建 PASS。完整前端回归待当前运行结果。
- B 限制：Mock 明确演示；尚未做真实流式供应商与工具调用实测；上下文采用有界裁剪，未实现压缩摘要；实际价格未配置时不生成费用估计。
- B 回归纠正：首次完整前端回归 115 PASS / 5 FAIL，原 App 测试只 mock 旧 JSON API，遗漏新 streaming transport。已为既有页面行为测试注入 streaming transport fixture；流式协议本身由独立测试覆盖。提交 d1509b2 时回归尚未全部 GREEN，记录这个实际流程偏差，后续修复完成后才继续。
- C RED → GREEN：首句测试失败后新增分句播放队列、请求 AbortSignal、迟到语音保护；43 项定向测试 PASS，完整前端 121 PASS、构建 PASS；提交 c0e09bf。浏览器识别不是服务端 VAD，自动全双工打断仍待设备方案。
- D RED → GREEN：本地区域模块缺失导致收集失败；新增 OpenCV 区域代理、质量门控、临时数值基线、新帧 ID/时间拒绝和 RAM 清理。2 个合成几何测试 PASS；完整后端 120 PASS、前端 121 PASS、构建 PASS。现有视频页新增独立本地授权按钮与“现在呢”新帧检查。未授权真人远程图片、未保存整段视频。代理不是精确 landmark；没有校准集，始终 UNCERTAIN。
- E RED → GREEN：教程模块缺失后实现既有 canonical KB 的使用权 allowlist、文本和带时间戳字幕段导入、内容去重、草稿/人工审核边界、CLI 和后台 API。2 个定向测试 PASS，完整后端 122 PASS。导入 48 个项目原创中英文草稿段，未复制外部教程；官方来源仅 citation-only 登记。没有权利确认的图片/整段视频不导入，没有自动爬虫或训练。
- F RED → GREEN：跨浏览器可读会话、未提供原文接口、恶意 Origin 未拒绝，3 个测试失败。增加服务端随机 HttpOnly/SameSite 身份 cookie、所有会话/偏好/日志访问隔离、Origin 检查、生产禁用无认证后台、增量 SQLite migration、30 天确认原文与级联删除。7 个定向测试 PASS；完整后端 125 PASS、前端 121 PASS、构建 PASS。现有日历记录可读取确认原文。旧 demo 数据不自动归属新浏览器；保留原数据等待授权迁移。匿名浏览器身份不是账户登录。
- G RED → GREEN：纯文字协议仍含 JSON 指令、身体左右映射、未先朗读的语音保存、工具轮 usage 只记录最后一轮，分别由新增失败测试定位并修复。最终完整后端 130 PASS；前端 18 文件 / 122 PASS；构建 91 modules PASS（首次 TS role 推导失败已修复重跑）；KB 3/3/2/12/49/2 PASS。导入/隐私/新帧定向 14 PASS。匿名 cookie 滑动续期、会话闲置 TTL/数量限制、兼容 provider、六项工具、低频本地检查和阅读控制完善，功能文档已补齐。
- G 实测：真实 DeepSeek 两轮虚构文字 SSE 完成，首 delta 2978/4271ms，总 4195/6046ms，实际 search_knowledge/get_memory 成功且未自动开始步骤。浏览器确认日志、独立原文同意、刷新读取 PASS；仅测试虚构记录，已清理。实际硬件、读屏、视觉准确率 NOT_TESTED。模型训练、生产账户、精确 landmarks、专家审核大规模 KB、完整 SKU 目录尚未实施，见 remaining_limitations.md。
- 顺序：功能修补已通过上述回归，用户新 Story 视觉说明接下来独立执行；不提前跳到视觉，不宣称 Master Prompt 全部生产目标完成。
- Story 联调功能补修 RED→GREEN：旧会话 HTTP404 不能从流式文字恢复，两项失败测试后实现仅未开始 SSE 的普通文字安全重建；不重试授权/单帧/部分输出。大字被页面固定像素覆盖的问题修复，实测24px。独立功能提交 0e307b8。
- Story 视觉 RED→GREEN：storyField 模块不存在，3项测试无法收集；实现独立阻尼随机粒子后3 PASS。保持后端与数据库不变，Story-only 酒红象牙白、当地合法字体、原创刻线苹果、鼠标局部力、真实controller状态、RMS单独授权、暂停静止和自适应预算。最终后端130 PASS39.90s，前端127 PASS9.92s，build94modules PASS6.66s，KB PASS。实际浏览器与限制见 docs/STORY_GENERATIVE_REPORT.md。
- Story 独立实现提交 2a7abad 后更新执行账本与交接；最终源码/测试已提交，后端8002正常使用已授权DeepSeek文本配置，临时8003关闭。
