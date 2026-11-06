# 本机真实设备验收 · 2026-10-12

环境：Windows，Codex 内置浏览器，前端127.0.0.1:5174、后端127.0.0.1:8002。用户当次明确授权：请求本机摄像头，单帧仅由localhost处理，不保存照片、不向第三方视觉服务发图；DeepSeek只接收有限测量摘要。没有使用模拟摄像头替代本次设备验证。未读取设备型号、配置内容或密钥。

| 项目 | 状态 | 实际证据与边界 |
|---|---|---|
| 摄像头权限与预览 | PASS | 浏览器取得实际视频，readyState4、640×480，currentTime持续推进；不代表已识别人脸 |
| 真实单帧进入本地检测 | PASS | 两次手动新帧请求都有实际返回；首次frame_id bf3d5e32-0ab6-49ec-be08-d158295c618d，captured_at1791808568.482 |
| 原生MediaPipe执行 | PASS | method=mediapipe_masked_lab、landmark_status=ready、simulated=false；两次均face_count0、no_face |
| 看不清时不编造妆效 | PASS | UNCERTAIN、confidence=null、gate_pass=false、regions为空；提示调整位置／光线，不给左右补色结论 |
| DeepSeek受限视觉后续提问 | PASS | feedback_source=local_evidence_deepseek_bounded_followup；事实来自本地检测，文本模型只选允许的后续动作 |
| 摄像头关闭 | PASS | 关闭按钮后状态off，video readyState0、width0、height0；本地检查禁用并清除面板结果 |
| 真人正脸关键点／腮红／唇妆与涂前涂后 | NOT_TESTED | 当前两帧没有人脸，未满足前提；没有正向定位和真实妆效证据，不能宣称准确率或改善 |
| 实际麦克风／ASR／可听TTS | NOT_TESTED | 浏览器呈现过朗读状态，不证明本人能听到或识别质量；没有用合成麦克风冒充物理验收 |
| 实际浏览器拒绝权限／系统reduced-motion／屏幕阅读器 | NOT_TESTED | 拒绝、停止及晚到事件在模拟单元测试中通过；未做本次真实系统拒绝或辅助设备测试 |
| 实机自适应关键帧长期运行 | NOT_TESTED | 合成媒体测试验证至少3秒间隔、变化阈值、停止／卸载中止；不等于实机长时稳定性 |
| 当次真实日志保存 | NOT_TESTED | 未点击保存本机体验；确认门禁、幂等保存和隔离由实际TestClient/SQLite回归测试覆盖 |

浏览器另行实测了真实DeepSeek的“开始步骤”→准备与补水、“下一步”→轻薄底妆。计划从第1步推进到第2步，仅推进一次；摄像头检查时仍停留第1步。Voice→Video保留第2步。中文／英文检查控件、关闭状态和375px测试（滚动条后clientWidth360、scrollWidth360）通过。旧状态在语言切换时未更新的缺陷已修复。

工具自动化出现过CDP输入超时；随后读取DOM确认部分操作已执行，不能只凭点击调用成功或失败判定产品状态。未捕获、输出或保存含真人摄像头画面的截图。拍摄前仍需本人面对镜头，按filming_guide完成正脸、实际语音和妆前／妆后验证。
