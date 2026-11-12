# 本地视觉验证

## 证据范围

2026-11-07（北京时间），macOS 26.3，Python 3.12.15，Node 26.10.0，Chrome 156.0.8078.81。本次从阶段 2 基线 `a04b0ec` 继续验证阶段 5 工作区。真实本机浏览器联调用隔离启动器、独立 SQLite 与端口。模型是本机 MediaPipe Face Landmarker，SHA-256 为 `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`。输入为合成几何、照片和 Chrome 模拟摄像头。

| 需求 | 结果 | 证据 |
|---|---|---|
| FR-501 独立预览、手动、连续及照片授权 | PASS | `test_local_vision_permits.py`、`test_visual_entry.py`、相机和照片组件回归。真实浏览器预览不发送视觉请求；确认后只发本机单帧请求。 |
| FR-502 显式基线及可比性 | PASS | 单帧或连续帧默认无对比。基线授权版本阻断撤销后的在途结果与旧请求。相同目标/条件可比，变光或画面不合格时无变化结论。 |
| FR-503 撤销、过期、恢复和跨会话隔离 | PASS（软件） | 接口覆盖撤销处理中单帧、取消连续范围、基线撤销竞态、会话恢复与过期；组件覆盖卸载、会话变化。真实浏览器关闭释放视频流并清除后端证据，刷新后仍需授权。运行中的单帧原生推理可结束计算，但失效后不发表结果。 |
| FR-504 质量、来源、降级 | PASS（合成输入） | 合成无脸、多脸、暗光、模糊、过曝或遮挡代理、过期帧，以及缺模型 OpenCV 降级。原生模型在 Chrome 模拟相机输入上完成本机质量判断。 |
| FR-505 镜像、未知方向及本地约束 | PASS（软件） | 浏览器镜像前摄仅改变显示。照片接口只输出图像坐标。分析路由以启用远程文字的配置验证不会调用远程补充。隔离文字传输夹具确认上下文只暴露本地可用标记，未发送观测数值、帧标识或视觉工具。错误响应不回显原始图像。本地检查的说明保留在该次回复，未写入会话的最近对话回复。 |
| 旧远程人脸入口 | PASS（软件） | 对 Qwen、DeepSeek 分别尝试旧三帧照片和单帧视频。即使显式携带旧远程同意标记，仍在解码和推理前返回 403；模拟演示和正式本地观察回归通过。映照只提供本地检查。移除远程抽帧和三帧采集调用方后，47 项相关前端回归、TypeScript 检查和 Chrome 模拟媒体联调通过。 |
| 实体相机、遮挡实样及无障碍 | NOT RUN | 当前测试使用模拟输入。实体设备、光线和相机左右验证，以及 VoiceOver / NVDA 由阶段 8 对应设备记录。 |
| 实际妆效与颜色阈值校准 | 范围外 | 工程质量和数值代理不能据此判断妆效，另建研究规格。 |

## 可复验命令

- 后端：`.venv-portable/bin/python -m pytest tests/test_local_vision_permits.py tests/test_vision_session.py tests/test_v2_local_vision.py tests/test_v2_privacy.py tests/test_visual_entry.py tests/test_vision_mvp.py -ra`，27 项通过。
- 前端：在 `frontend` 运行 `npm test -- --reporter=dot src/components/LocalCameraCheck.test.tsx src/components/LocalPhotoCheck.test.tsx src/components/CallExperience.test.tsx`，42 项通过。 `npx tsc --noEmit` 通过。
- 浏览器：运行隔离本地启动器；打开单独 Chrome 临时配置，使用 `--headless --use-fake-device-for-media-stream --use-fake-ui-for-media-stream --remote-debugging-port`，再运行 `node scripts/verify_local_vision_browser.mjs APP_URL CHROME_DEBUG_URL`。本次 PASS。退出浏览器、服务后才复用端口。

## 2026-11-12 当前源码复跑

在本机源码 `fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07` 上使用 Chrome 156.0.8078.81、独立 SQLite、前端 5194、后端 8027、语音 8028 和调试端口 9335 重新执行：

```bash
node scripts/verify_local_vision_browser.mjs http://127.0.0.1:5194 http://127.0.0.1:9335 --media
```

首次冷启动时，本地请求已返回 200，MediaPipe 与字体缓存仍在初始化；观察最终进入 `quality`，但超过脚本原有约 10 秒等待而误报超时。模型热加载后原脚本立即通过。为避免把正常冷启动误记为产品失败，本轮把通用等待上限从约 10 秒放宽到约 30 秒；修改后脚本再次通过。

实际通过内容：

- 预览阶段零视觉请求；明确单帧授权后才向本机路由发送请求，结果来源为 `local_mediapipe`，没有调用旧 `/api/vision/check`。
- 关闭摄像头清除视频流和后端观察；模拟轨道结束会撤销授权、清除观察，重新开启后仍须重新同意。
- 刷新后没有残留视频流，检查按钮保持禁用直到重新授权。
- 合成麦克风连续三次启动和关闭；每轮轨道结束、本地语音连接回到零，窗口／文档监听数量不增长。
- Chrome、TRACE 和调试端口停止后全部释放，Git 工作区干净。

这仍是 Chrome 合成设备的软件验证，不是实体相机、真实光线／遮挡／镜像理解、扬声器或双平台辅助技术验收。

## 阶段结论

本地视觉的软件实现及上述回归通过。需要由独立需求评审者确认需求清单。真实相机质量、用户左右理解与辅助技术验收仍待实体设备。

媒体修订复核了 Chrome 中模拟摄像头轨道结束。当前预览脱离视频元素，本地检查授权撤销，已发起的检查取消，已返回的旧画面观察从服务端清除。重新打开预览须重新同意本地检查。组件回归另验证切换后旧轨道的迟到事件、已结束轨道缓存帧和结果竞态。浏览器和组件均使用合成媒体，实体设备断开另验。
