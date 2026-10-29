# TRACE Phase 4 功能交付与真实验收

2026-10-12 · `trace-v5-realtime` · `D:\AccessibleBeautyAgent\.worktrees\realtime-beauty-call`

本轮修补了真实文字辅导主链。没有重做界面，也没有修改 Story 粒子、品牌或导航。完整的真人语音＋摄像头妆效验收仍未完成，不能把本轮称为全部生产就绪。

## 实际交付

- 自然命令优先识别否定、解释、重复、暂停和结束，支持中文与英文。同步 chat 和 SSE 共用同一计划控制器。
- 新 `MakeupPlan` / `MakeupStep` 验证模型。AI 可提出知识记录 ID，不能覆盖来源教学、拥有者或完成状态；无效提案回退至已有规范课程。
- 五个方案模板：自然日常、柔和暖调、简约通勤、柔和晚间、简单初学。自然日常十五分钟为准备／底妆／腮红／唇色／收尾；标准较长流程可加入可选妆前、遮瑕、眉眼。
- 控制器持久化当前步骤、完成／跳过状态、暂停、回看和事件幂等。回看不清除已经完成的记录；跳到腮红不把中间步骤伪记为完成。
- 主流程是草稿 READY → 激活当前 step → WAITING_FOR_USER → 下一步骤／暂停／重复／解释／新画面请求 → SESSION_COMPLETE。激活和等待在一次事务内提交。
- 真正的 DeepSeek 负责自然解释，SQLite 控制器负责状态。上下文含计划、当前步骤、历史、操作结果、确认偏好和视觉事实。普通话题不会重置步骤。
- SSE 先同步已提交步骤，再流式解释。模型失败或被打断也能恢复最新步骤；重复事件和旧步骤编号不能连续推进。
- TTS 失败只停止语音播放，保留完整文字流；ASR 仅最终结果触发请求，迟到回调被隔离。
- 新增语音可用的摄像头命令：开启摄像头／同意本地检查／帮我看看／关闭摄像头。摄像头授权、单帧分析授权和远程画面授权仍独立。浏览器权限需要用户自己处理。
- 结束后读出事实摘要，再经“保存到我的记录”写入已有 journal/calendar。保存返回实际数据库结果，去重检查真实记录。聊天原文、录音、视频和照片不随之保存。

## 数据与接口

SQLite 增量迁移 v2：`makeup_sessions(session_id,user_id,locale,payload,updated_at)`；`makeup_events(session_id,event_id,intent)`，后者复合主键去重。原 memory、journal、transcript 表保留。计划本地持久化用于恢复，30 天未更新的计划不可通过恢复读取；尚无后台物理清理任务。会话恢复不恢复摄像头、麦克风、原文历史或视觉画面。

`GET /api/makeup/{session_id}` 读取拥有者计划与当前步骤；`DELETE` 必须 `explicit_consent=true`，删除该计划进度与事件，保留独立确认的日志。拥有者由既有浏览器隔离中间件校验；这仍是匿名浏览器身份，不是认证账户体系。

计划 JSON Schema：`TRACE_PHASE4_SCHEMA.json`。17 项新增工具参数 Schema：`TRACE_PHASE4_TOOLS.json`。

| 工具 | 行为与约束 |
|---|---|
| create_makeup_plan | 验证 needs 与可选知识 ID 提案，禁止替换进行中的计划 |
| get_active_makeup_plan / get_current_step | 只读本会话的数据 |
| start_makeup_session | 用户明确开始，激活第一步 |
| explain_current_step / repeat_current_step | 保留步骤，提供解释依据 |
| complete_current_step / advance_makeup_step | 用户完成／下一步确认，事务推进，事件去重 |
| go_to_previous_step | 回看但保留完成记录 |
| pause_makeup_session / resume_makeup_session | 用户命令改变暂停状态 |
| request_visual_check | 请求新画面，清除旧观察；不隐式授权或拍摄 |
| get_visual_observation / compare_visual_observations | 仅新鲜、非模拟观察；无画面时 available=false |
| search_reviewed_makeup_knowledge | 只返回真实人审、非演示记录；目前不存在可用专业人审课程 |
| generate_session_summary | 已结束计划的事实摘要，未完成／未报告内容保持缺失 |
| save_confirmed_beauty_journal | 先呈现摘要，再要求明确保存；事务成功后确认 |

所有新增工具都验证参数，拒绝额外字段，使用服务端会话拥有者。模型无法通过工具设置 consent 或任意写数据库。状态拒绝返回受控错误，失败不能伪造成功。

## 知识库真实覆盖

沿用 canonical KB，没有另建系统。新增原创中英文草稿 24 条，覆盖十二主题：准备、补水、可选妆前、底妆、遮瑕、眉部、眼部、腮红、唇部、收尾、卸妆、常见问题。每条含用品／工具、准备、动作、触觉空间参照、常见错误、完成标准和可选视觉检查。

KB 总数：LOOK 3、ROUTINE 3、REFERENCE_CASE 2、PRODUCT 12、ACCESSIBILITY_GUIDANCE 73、SOURCE 3。五个新方案是控制器模板，不等同于新增五条已审核 LOOK。原有 48 段原创教程保留。

**专业课程审核：BLOCKED。** 新内容为原创工程草稿，全部 DRAFT、verified=false；没有伪造审核人，也没有将模型生成内容标成专家审核。生产模式在没有人审课程时拒绝生成专业计划；本机开发模式明确披露待审状态。没有微调、训练集、完整欧莱雅 SKU 库或购买数据。个人用品、产品类型和肤质没有被自动推断。

## 摄像头与视觉状态

本应用后端单帧分析使用真实像素、OpenCV 和可选 MediaPipe IMAGE 推理；没有第三方视觉推理请求。官方模型：3,758,596 字节，SHA256 `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`，下载至忽略的 `work/models/`，不是人像资产。

检测输出仅用于关键点位置和脸颊／唇部区域颜色数值；不启用表情或情绪推断。关键点缺失、光照／位置不合格或帧过期时保持未知。没有可校准的妆效测量时始终 UNCERTAIN。Haar face-box proxy 是明确命名的回退，不能当作真实关键点。

- PASS：官方模型实际对空白图片推理，返回零人脸；非法关键点拒绝；合成区域／左右方向测试；权限拒绝、新帧 ID、过期帧、重复帧、未校准输出和拥有者隔离自动测试。
- NOT_TESTED：真人摄像头帧、真人关键点召回、腮红左右判定、唇部越界识别准确率，以及真实调整后妆效改善。
- 临时基线仍需单独同意，仅数值在 RAM 保留最多十五分钟，不保存图片。无基线同意时不能声称完成前后数值比较。每次检查要求新帧；错误请求和关闭检查会清除旧观察，不能重复利用旧报告当新观察。

官方实现依据：[MediaPipe Python guide](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python)。官方模型输出关键点不等于妆效判定准确。可选依赖使用现有 OpenCV headless；MediaPipe 包元数据要求的 opencv-contrib-python 未额外安装，pip 因此有依赖声明警告。已验证当前运行时导入和空白推理，但没有宣称跨环境安装无风险。不要在生产部署中直接假设该环境组合完全兼容。

## 真实 DeepSeek 与页面验收

`TRACE_PHASE4_LIVE_TEXT.json` 保留真实 API 的十一轮结果和实际状态，不是 scripted UI 或 Mock。使用隔离的虚构测试 alias，不读取其他用户日志。步骤索引前七轮为 0→0→1→1→1→2→2；解释／重复保留底妆；结束仅记录明确完成的准备与底妆；明确保存后数据库有一条对应记录。

摄像头两轮回复明确“尚未取到画面”，没有用文本假装检查通过。因此 **文本＋数据库路径 PASS，完整包含真人视觉的场景 PARTIAL / NOT_TESTED**。真实文本往返约 4.3–11.6 秒，不能保证固定低延迟。

`TRACE_PHASE4_LIVE_ENGLISH.json` 为真实 DeepSeek 的初学方案／开始／重复三轮，全部英语；不是运输 Mock。独立浏览器页还执行了方案请求、开始、下一步、重复和重启后恢复；键盘 Enter 提交真实表单。刷新只恢复计划步骤，不恢复未授权持久化的完整聊天。

## 自动测试与异常

最终结果写于下方交付记录。基线后端130／前端127全部通过。新增 intent/controller/TTS 测试确实出现过 RED，再实现 GREEN；一次测试因 TestClient.delete 不接受 json 参数失败，改用 request 后通过。

有一轮全量回归挂起并被终止，没有得到失败断言。补充 native detector close 和 shutdown 后，连续全量后端 155／156／157 已通过；根因未被完全证明。不能抹去这次异常，也不能声称其根因已完全解决。

## 实机验收清单（全部仍需执行）

1. 在真实电脑／手机明确开启麦克风，用中文、英文依次完成开始、重复、解释、暂停、继续、下一步和结束；核对实际听见的 TTS，而非仅看 Speaking 状态。
2. 朗读中打断，确认旧音频停止，当前后端步骤保留，无自回声或重复 ASR 推进。
3. 拒绝麦克风权限、识别失败、TTS 缺失，确认文字仍完整可操作。
4. 以语音开启摄像头，拒绝／接受浏览器授权；随后单独确认本地单帧分析。未同意时不得分析或外发。
5. 以本人当次同意的画面执行腮红／唇部新帧检查、光照异常、无人脸、多脸和调整后重查。核对 UNCERTAIN，不把颜色差异直接解释成妆效。
6. 撤回检查、关闭／切换摄像头、切换模式、隐藏页面和结束通话，确认媒体轨道与临时观察清理；不录制整段视频。
7. NVDA／系统读屏、仅键盘、OS reduced-motion、大字和窄屏依次执行完整流程。
8. 完成后先听摘要，拒绝保存应无日志；同意后按正确日期查看日历；刷新和后端重启仍有确认记录。

## 剩余限制

专业审核课程、真人 Gold Set、标注与准确率评估缺失；真实硬件完整验收缺失；普通文字辅导已可用，专业真人妆效判断不能宣称完成。新计划的动态修订、个人产品自动结构化和复杂参考图解析仍有限；不会把未知的所有权或肤质补成事实。计划恢复保留状态而非全部对话历史。匿名浏览器隔离、第三方 Web Speech 可用性、模型延迟、可选原生依赖和挂起风险仍需生产工程验证。

修改文件清单：`TRACE_PHASE4_MODIFIED_FILES.txt`；仓库执行账本：`docs/PHASE4_PROGRESS.md`。SQLite 迁移、接口 Schema 和控制器均为实际代码提交，不是设计草图。


## 最终交付记录

- 后端完整回归：158 PASS（34.88s）；前端完整回归：19 文件／129 PASS；生产构建：94 模块 PASS；KB 与 diff whitespace 校验 PASS。最终没有剩余失败断言。早先一次挂起、一次测试调用形式失败和 RED 均保留在上文。
- 真实 DeepSeek 中文十一轮＋数据库确认保存 PASS；真实英文三轮 PASS。真人视觉／物理 ASR／可听见的扬声器／系统读屏：NOT_TESTED。
- 功能实现提交包括 50384cb、9e07690、f81fab1、159fdcf、cbc8302、f8948eb、4cece56、c655ea1；最后文档提交另记录结果。
- 修改文件、计划 Schema、工具 Schema 和真实 API 对话证据随本报告一起存放。
