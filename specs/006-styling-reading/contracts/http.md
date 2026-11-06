# 造型、标签与对比契约

- `POST /api/full-look/confirm` 支持 `select`、`confirm`、`skip`。选择时提交一个领域及该领域的 `suggestion_id`。确认单个建议的领域可直接确认。有多个建议时先选择。选择、局部修改、跳过和确认均按方案版本校验。冲突为 HTTP 409，`detail.code=FULL_LOOK_CONFLICT` 并带 `current_version`。
- `GET /api/reading/availability` 返回当前服务名称、目的地主机和状态。配置就绪与真实网络通过分开。远程 `POST /api/reading/read` 同时要求 `explicit_consent:true`、`remote_upload_consent:true` 和相符的 `authorized_provider`。授权失败返回 403，配置不足返回 503。演示接收零张图片。
- `GET /api/products/catalog` 返回可比较的有来源目录项。`POST /api/products/compare` 保留 `description` 并返回来源状态、属性、出处、审核状态。无法验证的属性为空。样例明确标记为虚构。
