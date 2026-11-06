# TRACE 本机演示与拍摄指南

## 当前可以真实演示什么

DeepSeek 文本对话与服务器保存的逐步妆教计划、本机摄像头预览、单帧 MediaPipe 检测、条件合适时的区域颜色测量、新帧复查、明确确认后的私人日志。数字雕塑是通用示意，不是用户真实扫描。课程仍待专家审核。当前视觉规则未校准；不要把颜色观察称为“真实妆效准确率”或训练成果。

## 演示顺序

1. 打开 `http://127.0.0.1:5174/voice`。先选择中文优先或英语优先；根据需要暂停动态、调整阅读设置。保留本地后端8002和前端5174运行。
2. 可以先用文字说一个场景和感受，例如“这是演示情境：我要去咖啡馆见朋友，想自然一点”。想实际语音时点击“开始通话”，自行确认麦克风权限。浏览器识别可能使用供应商服务；文字发送给 DeepSeek。此次开发验收没有验证物理麦克风或可听音量。
3. 说“我想化自然日常妆，大约十五分钟，先给我计划”。检查计划是否还处于草稿；不要自动把它当成已审核专家课程。
4. 说或点击“开始步骤”。一次只做当前动作。“慢一点”“重复”“为什么”应保留当前进度。完成并准备继续时再说“下一步”。即使通话已结束，步骤按钮也可以继续文字请求，无需自动重开麦克风。
5. 到腮红步骤时，点击“在当前会话开启摄像头”或说“开启摄像头”，自行确认权限。预览不等于分析；远程图片检查保持关闭。
6. 点击“同意本地单帧检查”，再点击“检查新画面”或说“帮我看看”。人脸正对镜头、无遮挡、避免逆光、两侧光线均匀。图片只由 localhost 后端处理，不保存照片，不送第三方视觉模型。
7. 读真实结果。没有人脸、偏侧、模糊或不合适光线应得到“不确定”，这也是有效演示。条件合适时只读“哪一侧红色分量更明显／相近”，不能声称差异一定来自腮红，更不能据此评价好坏。
8. 调整后说“再看一次”或点“检查新画面”。需要新帧；只有光线、位置、尺寸和姿态相近才比较前后颜色。颜色差距变小不等于妆效改善。唇部目前只提供区域颜色，不能确认口红覆盖完整。
9. 自适应关键帧是单独的可选授权：至少3秒间隔，只在变化时分析，最长12秒复查。没有录像保存／上传。勾选妆前基线只用于确实未上妆的画面，数值在 RAM 中最多约15分钟。
10. 检查结束后继续原步骤。最后说“今天完成了”，听或读真实完成项总结。未完成的步骤不能声称已经完成。先确认内容，再明确说“保存到我的记录”；未经确认不会把整段谈话或照片存成日志。
11. 拍摄结束，点“关闭摄像头”和“结束通话”。确认摄像头关闭、检查按钮禁用。离开页面、隐藏页面和新会话会清理媒体或撤回当前检查；新会话需要重新同意。

## 开拍前检查

- 本机 MediaPipe 模型和清单存在于 `work/models/face_landmarker.task` 及 `.manifest.json`；下载工具为已有 `scripts/setup_local_landmarks.py`。不要把缺模型后的代理测量说成关键点识别成功。
- 必须事先实测真人正脸、实际光线和涂前／涂后；本次两帧没有检测到人脸，尚不能证明这些条件下的定位或妆效判断能力。
- TTS 是否真正听得到、ASR 中文／英文是否可用，需要本人在设备上确认。文字回退始终保留。
- 不使用预设画面冒充真人检查，不朗读编造的“已经改善”，不把 Mock、提示词或数学单元测试称为训练或准确率。
- 手机远程地址／HTTPS、生产账号体系、专业课程审核、经授权标注的视觉评估均未完成。明日优先拍本机功能过程与明确的能力边界。

## Reference UI / hardware filming extension

Open home, voice, makeup, Full Look in that order. Show actual conversation,
canonical step and paused/not-finished behavior. Full Look annotations are original
category illustrations plus real curated draft data, not verified commodity photos.
Review text and explicit save consent before recording to the calendar.

For hardware, open Devices, demonstrate explicitly labeled SIMULATOR and bounded
lighting confirmation. With your authorized local display, create a 120-second
code, enter in /mirror; show actual current step and progress. Disconnect/revoke
at end. Read-only mirror never gets camera, microphone, full chat, saved memory or
API credentials. Do not film pairing codes or tokens. No physical mirror/light/BLE
claim. Remote hardware needs HTTPS and deployment authentication first.
