# 偏好与日志契约

## 偏好

- `POST /api/memory/preview` 接收 `user_id` 与结构化 `candidate`。编辑时同时带 `memory_id` 与当前 `expected_version`。返回规范化内容、`candidate_id` 和 `candidate_version`，无写入。
- `POST /api/memory` 或 `POST /api/memory/{id}/edit` 带上述值及严格布尔同意。编辑带原记录版本。缺少候选版本或变更后的候选返回 409，明确拒绝返回 403。
- 课程反馈及 Full Look 偏好候选把版本随会话快照发出。 `/api/chat` 与流式兼容路径的 `memory_consent` 带 `memory_candidate_id` 和 `memory_candidate_version` 才能保存。
- 已确认回执可在重启后安全重复提交。进程重启后未提交的签名候选需重新预览。删除后原回执不能创建新偏好。

## 日志

- `POST /api/journal` 允许独立撰写，保存前明确同意。新界面传稳定的 `confirmation_id`，旧调用在相同内容下复用确认回执。
- `POST /api/journal/{id}/edit` 带 `expected_version` 和明确同意。读取后编辑、复制为新草稿均不自动保存。编辑不改变独立的聊天原文授权。
- `DELETE /api/journal/{id}` 明确删除后移除关联原文并失效回执。私人日志或总结不会自动转换为偏好。
