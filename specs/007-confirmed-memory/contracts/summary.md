# 摘要 API 契约

- `GET /api/recollection/candidate/{session_id}` 获取结束课程候选。若已保存或拒绝，返回 404。
- `POST /api/recollection/candidates/{candidate_id}/preview` 预览候选或编辑后的完整内容，返回新版本。
- `POST /api/recollection/candidates/{candidate_id}/confirm` 发送完整编辑字段、版本与明确同意。冲突返回 409，缺同意返回 403。
- `POST /api/recollection/candidates/{candidate_id}/reject` 拒绝当前版本；不新增个人记忆。
- `DELETE /api/recollection/{record_id}` 带明确同意删除单条。 `POST /api/recollection/{record_id}/reuse` 只允许显式选定已确认记录。
- `GET /api/recollection` 保留旧视图字段；显式 `user_id` 查询参数由浏览器所有者作用域校验，用于查看自己的其他命名空间。 `latest` 只返回本人显式选定可用于下次的记录。
