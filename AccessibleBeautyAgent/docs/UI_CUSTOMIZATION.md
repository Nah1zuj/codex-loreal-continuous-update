# 功能与 UI 后续修改

可以继续修改；页面、样式、数据和模型调用各自有入口。

| 目标 | 修改入口 |
|---|---|
| 主产品布局/按钮/样式 | frontend/src/App.tsx、frontend/src/components、frontend/src/style.css、frontend/src/pages |
| 后台表单字段/中文文案 | frontend/src/admin/fields.ts |
| 通用编辑与审核交互 | frontend/src/admin/RecordEditor.tsx |
| 三个后台页面/导航 | frontend/src/admin/KnowledgePage.tsx、ReferencePage.tsx、RagPage.tsx、AdminApp.tsx |
| 后台视觉样式 | frontend/src/admin/admin.css（kb-admin 范围，不影响主页面） |
| 可选标签与场景 | data/config/*.json |
| 新数据字段/校验 | backend/app/schemas/knowledge.py、backend/app/knowledge/validation.py，同时更新表单/模板 |
| 功能接口 | backend/app/routes/admin.py、backend/app/knowledge/admin_service.py |
| DeepSeek/其他模型 | backend/app/services/model_client.py、agent/providers.py、vision/reference.py、vision/providers.py、.env |

后台由 main.tsx 按 /admin 路径懒加载；主产品保持原流程。调整视觉无需重建知识库或换模型。新增业务字段需要同时更新 schema/表单/模板/文档生成器，再跑针对性测试与构建。审核、来源、版本和明确同意等业务约束应保留。

## Phase 3 TRACE customization

Edit `frontend/src/content/traceBrand.ts` for Chinese/English interface copy and the five module descriptions. `content/errors.ts` gives normal users short recovery language while the developer panel retains diagnostic detail. `styles/traceTokens.css` controls color, typography, spacing, dot size and motion; `styles/trace.css` handles layout. ModuleHeader, TraceMark, TraceDotGrid, ThreadProgress and MemoryFacts are reusable. Changes here do not require replacing Agent/RAG/storage APIs. Backend observation language is in `backend/app/vision/language.py`; confidence/state logic remains separate.

DOT reading was additive because there was no label-reading page/provider. Remote calls remain disabled. IMPRINT edit was additive; original save/profile/delete endpoints remain. English interface preparation does not automatically translate the existing Chinese KB or provider messages.

## Warm bilingual interface

Public interface copy now shows Chinese and English together. The header control changes their order, not visibility. BilingualText marks language runs for assistive technology. Existing user messages, Agent responses and knowledge records retain their original language; no background translation/model calls were added.

Palette: warm cream #FFF7EF, soft apricot #FAE8D9/#F9E8DA, deep brown #352922 and terracotta #8B4935. Calculated contrast: main text/background 13.28:1, secondary text/background 6.99:1, white/primary button 6.77:1. These are design checks, not a claim that every disabled person prefers this palette or that full accessibility certification has been completed.

Validation: frontend 18 tests and production build passed. Browser checked Chinese/English order switch, DOT consent text, and 390px mobile width without horizontal overflow. Existing backend/DeepSeek configuration untouched. Desktop acceptance image: design/trace-bilingual-warm.png.
