# 造型、标签与对比契约

- `POST /api/full-look/confirm` 支持 `select`、`confirm`、`skip`。选择时提交一个领域及该领域的 `suggestion_id`。确认单个建议的领域可直接确认。有多个建议时先选择。选择、局部修改、跳过和确认均按方案版本校验。冲突为 HTTP 409，`detail.code=FULL_LOOK_CONFLICT` 并带 `current_version`。
- `GET /api/reading/availability` 返回服务名称、目的地主机及配置状态。当前配置的 `remote_verification` 分为 `unverified`、`verified` 和 `failed`。`remote_verified` 仅在通过时为真。通过表示收到有效服务响应，低清晰度结果仍可为 `UNCERTAIN`。进程重启或配置变化后重新验证。
- 远程 `POST /api/reading/read` 同时要求 `explicit_consent:true`、`remote_upload_consent:true` 和相符的 `authorized_provider`。当前网页和联调脚本还提交已确认的 `authorized_destination_host`，传入后必须匹配。授权失败返回 403，配置不足返回 503。演示接收零张图片。
- `GET /api/products/catalog` 返回可比较的有来源目录项。`POST /api/products/compare` 保留 `description` 并返回来源状态、属性、出处、审核状态。无法验证的属性为空。样例明确标记为虚构。
