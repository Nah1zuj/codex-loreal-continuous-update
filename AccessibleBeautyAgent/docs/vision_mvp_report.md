# TRACE Vision MVP 本轮工程报告

本轮完成现有UI上的功能衔接，保留Story、粒子／数字雕塑、Voice Agent、Full Look、Beauty Profile、Memory、路由和原API。没有训练或微调模型，也没有读取、输出或修改.env/API Key。

## 实现

- 本机单帧先运行官方预训练MediaPipe，再进行几何、亮度、清晰度、姿态和区域有效面积检查。浮点LAB椭圆ROI比较用户本人的左右脸颊；CSS镜像不改变原始像素或解剖方向。roll按实际像素宽高计算，yaw只是2D代理量。
- 腮红只报告未校准的区域颜色分量：相近、左侧更明显、右侧更明显。不能归因于腮红、确认覆盖面积、评价好坏或推断个体特征。唇部只定位区域和测量颜色，始终不确认完整覆盖。
- 复查要求新frame_id、时间戳和可比光线／位置／姿态。比较的是颜色变化，不能声称真实妆效改善。历史仅有数值，10条/会话、最多200会话，900秒有效期、30秒后台清理。关闭／撤回检查会使尚在运行的请求失效，避免晚到结果写回。
- 摄像头位于当前Voice会话内；检查不推进妆教，手动及授权自适应结果接回原会话。自适应至少3秒间隔、变化阈值2.5%，最多12秒重新取帧；不会录制视频。允许可选且明确授权的临时妆前数值基线。
- DeepSeek真实文本会话保留自然逐步辅导。视觉回复的事实由本地规则生成，DeepSeek仅在有限动作中选择后续问题，不生成新视觉事实。没有把模板事实说明称为自由视觉模型推理。模型上下文过滤掉图像和原始面部关键点，只保留新鲜且有范围说明的证据。
- analyze_makeup是受参数／用户意图约束的只读工具；无新证据时返回capture_required，不能自行获取权限或拍照。经审核知识检索保持真实审核门槛，目前没有已审核妆教可用。
- 原远程Mock检查功能保留在展开区，默认关闭；不冒充本地真实关键点。按钮在通话结束后也能发文字辅导请求；文字按钮打断／替换回复不会意外启动语音识别。进度条计已完成步骤，不把当前索引当完成数。状态提示和本地反馈遵循显示语言。

## 测试与验收

基线实际执行：后端158 PASS、前端134 PASS。最终回归：后端171 PASS；前端21文件142 PASS（25.04秒）；TypeScript/Vite构建106模块PASS（15.56秒）；知识库校验PASS（3Look、3Routine、2Reference、12Product、73Guidance、3Source）。没有剩余已知自动化测试失败。

本机摄像头PASS：真实640×480预览、两次原生本地检查、关闭后readyState0/width0/height0。两次均未检测到人脸，正确返回UNCERTAIN。真人正脸定位、化妆前后效果、真实准确率均NOT_TESTED，不能从这个结果给出“模型很好／妆效改善”的结论。真实DeepSeek已在浏览器提供准备、补水、底妆指导，下一步只推进一次。详见real_device_validation.md。

RED／FAIL历史：新观察模块尚不存在、缺少analyze_makeup、非方形角度14.04而应7.13、会话切换保留旧授权、结束通话后按钮无效、文本朗读替换意外启动识别、撤回期间检测晚到写回、900秒后会话残留数值。均经最小修复和GREEN回归。浏览器发现英文切换仍保留中文关闭提示，也已修复。首次离线评估CLI缺jsonschema；安装并声明可选依赖后，空数据评估正常返回NOT_EVALUATED，校准返回NOT_CALIBRATED。两次选择错误文件／目录的测试命令和错误语言选项名是执行错误，修正后运行正确命令；没有把这些错误命令当PASS。

## 评估与数据

MAKEUP_EVALUATION_SCHEMA.json和两个离线脚本已经实现同意／用途隔离、人工标签、版本、灯光／姿态、区域框、分类误报漏报、IoU、稳定性和前后变化一致性。脚本不打开图片、不调用远程服务、不训练。零份授权真人标注数据，当前不能计算准确率。校准至少要求30份明确允许校准的真人标注，排除非有限数和混合模型版本；候选阈值不会自动进入生产。详细标注／采样／误差分析流程在vision_evaluation_protocol.md。

## 剩余风险与未完成能力

- 原创课程仍待专业审核，不能称为经过专家验证的个体化妆教。尚无授权真人标注评估集、经验证的遮挡检测、肤色／光线公平性测试、真实彩妆分割／覆盖面积和妆效准确率。
- 本次没有真正见到人脸；MediaPipe的原生执行不代表在这台设备上已证明人脸定位准确。缺模型／运行库时仍可能退到历史face-box代理路径，其结果始终UNCERTAIN。
- 真实麦克风、ASR质量、本人听到的TTS、系统读屏、实际OS reduced-motion、设备权限拒绝和实机长时间自适应运行未验收。模拟媒体测试只能证明状态、隐私和清理接线。
- DeepSeek依赖网络且可能超时，文本回退保留；视觉跟进是有边界的规则事实＋模型动作选择。没有视觉API／训练支持的夸大承诺。
- 本地匿名浏览器隔离不是完整生产账号系统；只有确认后的摘要写日志，计划为恢复而保存。部署、手机HTTPS、模型资产和用户授权资料管理仍需生产设计。
- 保留现有lazy3D约682.49KB警告。未验证低端设备、长时GPU负荷、Lighthouse或60fps保证。浏览器工具曾有间歇输入超时，拍摄建议先暂停动态并确认实机响应。

准备拍摄请按filming_guide.md操作，特别是正脸和真实语音两项。当前本机验收没有保存任何摄像头照片、整段录像或本次体验日志。

独立功能提交：7dba0c0（本地证据）、3f65817（会话内摄像头）、1e55843（撤回及数值过期）、48e44d8（语言与帧范围说明）。最终离线评估基础设施、验收与账本在后续文档提交中收口。

## Camera consent and photo fallback (2026-10-12)
Local analysis has an explicit setup entry even with no previous voice session.
A private visual session is created without a provider call or implicit consent.
For camera use: enable preview, allow browser camera, then explicitly allow local
single-frame analysis. Adaptive sampling needs its own checkbox.
Photo fallback accepts JPEG/PNG/WebP up to15MB, reduces dimensions to1024 and
re-encodes locally before submission. Selecting a file sends nothing. Consent
and Check sends one image to this application backend; it is not saved or sent
to remote vision. Photo checks pause/revoke camera analysis first. Unknown photo
mirroring prevents anatomical-side recommendations or camera baseline reuse.
Current outputs cover quality and conservative region color observations, not a
validated cosmetic judgment, unrestricted image understanding or training.
Actual browser non-face fixture returned UNCERTAIN with recapture guidance;
actual camera preview/consent enabled successfully. Positive real-face results
and sustained adaptive sampling remain NOT_TESTED. Regression187/155 PASS.
