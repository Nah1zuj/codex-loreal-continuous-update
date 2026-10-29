# V2 API 增量

同源请求；应用启动先 GET `/api/identity` 建立 HttpOnly cookie。不要把 token 放进模型上下文或浏览器脚本。非同源 Origin 被拒绝，访问其他浏览器拥有的资源返回 404。旧 `/api/chat` JSON 接口保持兼容。

| 方法 / 路径 | 内容 / 行为 |
| --- | --- |
| POST /api/chat/stream | ChatRequest：message、可选 session_id、locale、experience_mode、action。SSE session(完整会话)、delta(text)、tool(name/ok)、final(reply)、error(message)；断开可取消，无输出后自动重试 |
| GET /api/transcripts/{session_id} | 本浏览器的临时 RAM 转录，persisted=false |
| GET /api/diagnostics | 本浏览器最近完成/失败/取消请求首 token、总耗时、供应商 usage；多工具轮累计，保留 rounds，费用未配置为 null |
| POST /api/vision/local | session_id、image、frame_id、captured_at、explicit_consent=true；baseline_consent 默认 false。单帧最多 3MB，30 秒内新帧；返回 observation + 原有 reply |
| DELETE /api/vision/local/{session_id} | 删除本地数值基线 |
| POST /api/journal | 既有标题/日期/感受/反思字段；显式 consent=true，session_id 可选，save_transcript 默认 false；有原文时需另行明确勾选 |
| GET /api/transcript-records/{id} | 当前浏览器已确认且未过期的原文 |
| POST /api/admin/tutorials/import | segments + commit=false 默认 dry-run；仅开发 loopback 后台，生产无管理员认证时拒绝 |

原有日志列举/删除、profile、memory、session、full-look、知识后台接口保持，服务端重写 user_id 为拥有者前缀，调用者不能选择其他人的 principal。原文跟随日志删除，30 天到期访问/保存时清理。会话不存在时需创建新会话。
