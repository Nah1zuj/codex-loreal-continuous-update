# 本地视觉 API

- `POST /api/vision/local/permits` 传 `session_id` 与 `scope`（`camera`、`adaptive` 或 `photo`）。仅会话所有者可创建，返回 `permit_id` 和 `expires_at` 和 `baseline_version`。连续凭据需要已有有效相机凭据，照片凭据限一次使用。
- `POST /api/vision/local` 随帧提交 `permit_id`、`explicit_consent:true`、`capture_kind`、`adaptive`、`frame_id`、`captured_at` 和目标。仅手动相机可提交 `baseline_consent:true`。使用基线比较时，传 `compare_baseline:true`。保存或比较均校验 `baseline_version`。凭据需匹配范围；同一帧 ID 或超出 30 秒窗口的帧不重用。
- `GET /api/vision/local/{session_id}` 返回最近一次未过期的观测（数组），并说明临时基线是否存在。返回结果包含 `source`、`quality`、`assessment`、`comparison` 和画面元信息，`calibrated:false`；无图像、完整关键点或置信概率。
- `DELETE /api/vision/local/{session_id}` 清除全部本地范围。请求体中的 `permit_id` 仅撤销对应范围；撤销相机也撤销依赖的连续授权。请求体同时含 `baseline:true` 和有效相机 `permit_id` 时，仅撤销基线，并返回新基线版本。
- 权限拒绝返回 403，帧过期、重复、取消和无效图像返回 409，跨浏览器身份访问返回 404。

旧 `/api/vision/check` 仅兼容本机 mock。Qwen 和 DeepSeek 配置下，无论照片或抽样帧、是否携带旧远程开关，都在解码和供应商调用前返回 403。标签读取单独使用阶段 6 的接口。
