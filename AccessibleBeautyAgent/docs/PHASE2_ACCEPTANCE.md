# Phase 2 交付与验收报告（2026-10-07）

A. 新增文件：backend/app/schemas/knowledge.py；backend/app/knowledge/（repository、validation、vocabulary、importer、admin_service、policy）；rag/document_builder.py；routes/admin.py；services/model_client.py；frontend/src/admin/；data/config/；sources.json；七份 CSV 与 beauty_kb_template.xlsx；import_kb.py、create_kb_templates.py、extract_video_frames.py；Phase2 回归测试；研究流程/清单/UI 修改指南。

B. 修改文件：原 KnowledgeStore/检索器、Agent/Look/Product 服务、视觉/参考适配器、配置/环境示例/API、前端 main 懒加载、规范示例数据、Python 依赖锁和项目文档。主产品界面保持原结构。

C. 已实现：规范数据与来源、扩展词表、行级导入报告、编辑/审核/停用、版本冲突与历史、图片上传/草稿/修订保护、批量图片草稿、视频选帧、可读父子文档、生产审核过滤、后台三页面、多通道检索调试和原子实时重建。

D. Mock：语言意图、视觉/参考分析、哈希向量、重排。参考 mock 返回未知属性，无实际图像观察。现有示例与合成验收图明确 demo_data=true。

E. 外部依赖：DeepSeek 文字/图像适配器准备完成，但尚未真实验证；Qwen 兼容保留。ALLOW_REMOTE_AI=false，未调用任何外部模型。远程 reranker/realtime 仍是扩展接口/占位。真实自动图像理解需要后续配置支持该能力的模型并验证。

F. 启动：PowerShell 进入 D:\AccessibleBeautyAgent，运行 powershell -ExecutionPolicy Bypass -File .\start-dev.ps1。当前服务器已启动。首次重装依赖时先停止服务再 setup.ps1。

G. 第一张真实图片：http://127.0.0.1:5173/admin/references，选择 Look 与 JPEG/PNG/WebP，真实研究不要勾选演示数据，点击上传到本机。

H. 审核：Analyze → 人工检查并编辑字段（未知留空）→ 填来源/备注 → 勾选确认并署名 → Verify & Save。重复分析不覆盖已审核记录，只生成修订建议。

I. 导入：编辑 templates/beauty_kb_template.xlsx 或对应 CSV，在 /admin/knowledge 预览报告，修正行/字段错误，导入接受的草稿。输入 verified 不会跳过人工审核；已有编号不覆盖。

J. 索引：后台 Validate → Rebuild。后台即时替换当前内存索引；scripts/rebuild_index.py 只保存快照，运行中服务需后台重建或重启。重建不修改规范文件，作用域参数只限定报告计数。

K. 检索：/admin/rag 输入“Dinner，想正式一点但不要太成熟”，查看 scene=dinner 与五个阶段结果；look_id=soft_formal、verified=true 可查看审核参考。默认开发模式可看 SAMPLE；生产模式排除所有演示和草稿。

L. 下一步维护文件：data/knowledge/looks.json、routines.json、reference_cases.json、products.json、accessibility_guidance.json、sources.json；标签维护 data/config/*.json。不要修改 data/demo 测试样本。参阅 KNOWLEDGE_BASE_WORKFLOW.md 和 KB_RESEARCH_CHECKLIST.md。

M. 验证与限制：59 项后端测试、7 项前端测试通过，生产构建和 pip check 通过，规范校验 PASS。Excel 7 行 roundtrip 全部接受；无来源的模板记录有明确 WARNING。视频测试按0/1秒提取2帧，越界9秒明确报告。浏览器完整上传→mock→人工改 light_medium→审核v3→保护重分析→重建42文档→Dinner检索已通过；审核过滤正确；桌面1280×900/移动390×844无横向溢出。服务重启后 health、审核参考检索与原 Dinner 流程启动正常。三项独立审查问题均以失败→通过回归修复，并完成复核。

未发现当前阻断错误。真实研究数据/模型准确率、真实硬件语音/相机和外部 DeepSeek API 尚未验收。原 sample reference 是图片路径占位，选择它会明确提示缺少图片；上传真实图片即可继续。验收 synthetic reference 已署名为“自动化验收（模拟人工审核）”，人工备注说明属性只是测试值，绝不视为真实研究结论；生产模式不会使用它。研究上传、报告、历史不进入 Git；只保留这一明确合成的演示图片供复现。

UI 可以继续改：fields.ts 管表单，admin.css 管后台样式，主产品 pages/style.css 独立，模型只在后端适配层。详细入口见 UI_CUSTOMIZATION.md。
