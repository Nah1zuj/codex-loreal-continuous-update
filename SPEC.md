# TRACE-Next 必须保留的行为规格

版本：2026-11-09。基线 fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07。本规格约束独立项目必须保留的行为，不绑定公司、支付平台或比赛。

## 范围与对应验收

| ID | 必须保留的行为 | 可验证输入/输出及边界 | 证据入口（AccessibleBeautyAgent/tests/） |
|---|---|---|---|
| B01 | 健康报告区分服务可达、配置、真实验证 | GET /api/health 返回 mock；不能宣称远程已调用 | test_runtime_health.py、test_remote_verifier.py；对照 health |
| B02 | 首次文字意图与造型检索 | “今晚有一个正式 dinner，我想精致一点但别太成熟”→ dinner、soft_formal、too_mature | regression/test_acceptance.py；对照 catalogue_journey |
| B03 | 自由对话不擅自推进教学 | 问“下一步呢？”保留 active_index；推进由确定性命令控制 | test_session_commands.py、test_dialogue_knowledge.py |
| B04 | 幂等与乐观版本控制 | 同 event_id 同内容只推进一次；同事件改动作409；过期 revision409 | test_session_commands.py；对照 command_journey |
| B05 | 停止、暂停、跳过、恢复分开 | skip 标记 skipped；pause 不完成；finish 不伪造全部完成；恢复撤销相机授权 | test_session_commands.py、test_phase4_controller.py |
| B06 | 重启保留已提交进度与命令回执 | 同隔离 DB、同 Cookie 重建应用后查询事件/步骤；陌生身份404 | test_session_commands.py；对照 restart |
| B07 | 流式输出保持事件契约 | POST /api/chat/stream 返回 SSE session/committed等终态；断流不重复推进 | test_v2_conversation.py、test_conversation_lifetime.py；对照 stream |
| B08 | 相机预览和分析分别许可 | 未同意403；撤销/刷新/轨道结束清除许可；非法图片422 | test_local_vision_permits.py、test_v2_local_vision.py；前端 cameraStream.test.ts |
| B09 | 视觉结果不超证据 | 不清晰/低置信不指导补妆；demo带模拟标识；真实效果未验 | test_vision_mvp.py、test_vision_session.py、vision/test_consensus.py |
| B10 | 长期偏好明确同意与版本绑定 | false→403；字符串true→422；先preview再save；重放不重复，改候选409 | test_confirmed_memory.py、test_v2_privacy.py；对照 memory |
| B11 | 删除不可被旧确认请求复活 | 旧保存回执失效；其他浏览器读写404；日志及转录按级联规则删除 | test_private_journal.py、test_recollection_v2.py、regression/test_review.py |
| B12 | 六域造型局部修订和版本冲突 | 旧版本confirm/revise→409；确认本次不保存长期记忆 | test_styling_reading.py、test_v4_full_look.py |
| B13 | 标签单张授权和目的地绑定 | 无同意403；目的地主机/供应商变化零外传；结构错误不冒充读取 | test_styling_reading.py、test_reference_full_look.py；对照 reading |
| B14 | 有来源、审核状态及本地管理限制 | 未审核课程在试用模式不开放；产品无字段不编造；远程管理403 | test_dialogue_knowledge.py、test_v2_ingestion.py、regression/test_edge_cases.py |
| B15 | 语音资源与文字退路 | 缺模型报告missing仍可文字；暂停语音时不主动播报；界面可键盘操作 | voice/test_bounded.py；frontend/src/realtime/*test.ts、components/*test.tsx |
| B16 | 可选硬件降级 | 不装硬件包时列表available=false，不影响核心；模拟器明确标识 | test_hardware.py |
| B17 | 默认隔离运行与路径约束 | 无旧.env和用户DB；端口5280/8112/8113；安装锁与冲突保护保留 | regression/test_windows_setup.py、scripts/verify_runtime.py |
| B18 | 扩展不能覆盖核心契约 | 工厂可不创建默认应用；扩展只挂/api/extensions/{name}；重复名/无效名拒绝 | tests/test_application_factory.py（本次新增） |

## 自动对照场景与样本

验收程序在两个独立进程中加载固定旧提交和新代码。同场景使用相同输入、mock配置和各自临时SQLite；动态标识、签名、时间戳作保持引用关系的归一化（不删除业务状态或错误）。比较每次响应码、完整JSON/SSE、状态快照和场景末数据库内容；另比较完整OpenAPI及SQLite建表SQL。样本保存 migration/evidence/compatibility-samples.json，报告记录对照是否实际通过。不能只比较新旧“都通过测试”。

场景至少包括：health与未知会话；正式晚餐旧课程；新课程推进/重放/冲突/暂停/继续/恢复/提前结束；两个浏览器所有者隔离及五种JSON Content-Type；偏好审阅/严格同意/篡改/重复/删除；标签demo及未同意；Full Look旧版本冲突；流式推进及结束；应用重建后的事件与进度。全量旧回归另外覆盖更细分媒体/异常。

## 验收层级与切换

软件通过意味着本机 mock/模拟输入下行为兼容。真实远程模型、真实视觉准确性、Windows 实机、实体音视频、读屏和目标用户试用尚未验收。新目录作为独立项目继续发展，旧项目不自动替换；任何未来平台接入都必须作为可选扩展单独授权和验收，不能改变基础无障碍能力。
