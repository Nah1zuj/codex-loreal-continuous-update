# 本地运行与生产差距

后端使用原项目 venv（包含 OpenCV）：`D:/AccessibleBeautyAgent/.venv/Scripts/python.exe`。从 worktree 运行 `scripts/run_realtime_text.py --config-path D:/AccessibleBeautyAgent/.env --port 8002` 仅在配置拥有者明确授权之后；脚本正常加载 DeepSeek 文本配置，图像/embedding/reranker 强制 Mock，只绑定 127.0.0.1。

前端 frontend 内 `npm run dev -- --host 127.0.0.1 --port 5174`，现有 Vite `/api` 代理指向本地后端。`npm test` / `npm run build`，仓库根目录设置 PYTHONPATH=backend、全部 provider=mock、ALLOW_REMOTE_AI=false 后 `python -m pytest -q`，再 `python scripts/validate_kb.py`。

兼容供应商可通过配置名 MODEL_PROVIDER=openai_compatible、COMPATIBLE_BASE_URL、COMPATIBLE_MODEL、COMPATIBLE_API_KEY 由应用加载；本次未启用该供应商。非秘密配置示例在 docs/config.example.toml，不含任何密钥值。

SQLite migration 为 additive，启动创建 schema_migrations / browser_identities / transcript_records，旧偏好与日志不删除；部署前停服务并受控备份数据库。旧 demo 拥有者不能自动归属新 cookie。重启会丢失未确认 RAM 会话，请先明确保存希望保留的日志。

生产前需要 HTTPS、安全 cookie、同源反向代理（SSE 禁止缓冲、适当超时）、账户认证与管理员身份、密钥管理、限流/配额/观测、备份与删除期限、专家审核知识及授权校准集。当前没有生产发布；匿名 cookie 隔离不是可承诺的云账户系统。不要直接把本地开发后台暴露公网。
