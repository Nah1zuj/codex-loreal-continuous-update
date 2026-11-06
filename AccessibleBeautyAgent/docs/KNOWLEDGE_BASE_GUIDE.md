# Beauty KB 规范输入指南（Phase 2）

详细操作见 [KNOWLEDGE_BASE_WORKFLOW.md](KNOWLEDGE_BASE_WORKFLOW.md)。规范模型唯一来源是 backend/app/schemas/knowledge.py，/api/admin/schemas 可查看完整字段；templates 提供可导入样例。旧 base 字符串/routine_id/眼部字段兼容读取，保存会规范化。

## 可编辑文件与校验

规范输入仅为 data/knowledge 六个文件：looks.json、routines.json、reference_cases.json、products.json、accessibility_guidance.json、sources.json。全部 UTF-8，形状 {"records":[...]}。推荐后台编辑，自动保护版本；直接改 JSON 需自行保留备份，不获得后台版本冲突保护。data/demo 是不可变测试样本，勿改。迁移前旧输入保存在 data/history/migration_phase2。

词表在 data/config：scenes、impressions、intensity_levels、saturation_levels、finishes、placements、makeup_areas、accessibility_categories、reference_status。添加场景同时填写 scenes.json 中的 aliases；无需更改 Intent 枚举。刷新页面读取新词表。

```powershell
.\.venv\Scripts\python.exe scripts/validate_kb.py
.\.venv\Scripts\python.exe scripts/rebuild_index.py
```
CLI 重建保存 data/index.json；已运行的服务请用后台重建按钮刷新内存，或重启。重建不会写规范知识，也不会删其他类型。--type / --look-id 只限定报告计数，实际完整原子重建，以保留父子关系。

生产规则：DEVELOPER_MODE=false、RESEARCH_MODE=false 时 Agent/RAG 仅使用 verified=true 且 demo_data=false，停用/拒绝始终排除。Look 与关联 Routine 都需审核才能指导。当前 SAMPLE 和合成验收图均排除于生产；没有真实审核数据时返回空结果是正常行为。

## 后续 DeepSeek

密钥只写本机 .env。保留当前 ALLOW_REMOTE_AI=false，直到你决定启用。届时设置 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL、DEEPSEEK_MODEL，并把 MODEL_PROVIDER 改为 deepseek；图像与参考单独设置 VISION_PROVIDER/REFERENCE_PROVIDER 和经确认支持图像的 DEEPSEEK_VISION_MODEL，最后显式启用 ALLOW_REMOTE_AI=true。重启服务。文字、视觉可独立切换；只启用文字不会启用图像。

DeepSeek 适配器已实现但未进行真实接口验证；模型名称与图像能力以账户和官方文档为准。现阶段没有自动分析准确率保证。远程 embedding/reranker 与 realtime 也未实测；本地检索/浏览器语音仍可使用。
