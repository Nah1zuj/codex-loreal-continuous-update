# 会话命令契约

## 教学命令

`POST /api/makeup/command` 接收 `session_id`、`action`、`event_id`、`expected_plan_id`、`expected_revision` 和可选 `expected_step_id`。动作包括 start、advance、skip、previous、pause、resume 和 finish。相同的事件及预期输入可安全重试，响应带原事件结果和当前快照。相同 ID 的不同参数返回 `EVENT_MISMATCH`，过期计划或步骤返回 `STALE_PLAN`。两个错误都是 HTTP 409，附面向用户的说明。

兼容入口 `/api/chat`、`/api/chat/stream`、`/api/routine/start`、`/api/routine/advance` 和 `/api/recollection/finish` 支持同一事件字段。旧的无计划 routine 仍需迁移。文字入口原有的“下一步从草稿开始／从暂停恢复”兼容保留，严格命令显式指定 start 或 resume。

## 查询与恢复

- `GET /api/makeup/events/{session_id}/{event_id}` 仅当前浏览器身份可读。返回原事件是否已提交、提交时计划版本、步骤与最新会话快照。不存在或无权访问均返回 404。旧记录可确认已提交，历史详细版本可能缺失。
- `POST /api/session/{session_id}/restore` 恢复已有会话，撤销媒体授权，保留教学进度。普通 `GET /api/session/{session_id}` 仅查询。
- 流式业务提交发出 `committed`，随后可有 `delta`，终止于 `final` 或 `error`。生成失败不撤销已提交动作。前端中断后保留原事件标识用于查询，收到较旧教学版本时不覆盖当前快照。

## 小结

`POST /api/recollection/finish` 和已完成的 Reflect 会话返回 `summary` 供本次展示。兼容字段 `recollection` 为空。旧历史记录在读取时标记 `legacy_automatic`，不会作为 `latest` 候选复用。
