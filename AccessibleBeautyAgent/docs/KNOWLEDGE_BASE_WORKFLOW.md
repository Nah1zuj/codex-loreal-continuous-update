# Beauty KB 非工程师工作流程

实际项目：D:\AccessibleBeautyAgent。内部页面只在本机使用。当前所有模型为 mock，ALLOW_REMOTE_AI=false；没有发送到 Qwen 或 DeepSeek。

## 从第一张图片开始

1. 启动后打开 http://127.0.0.1:5173/admin/references。
2. 选择已有 Look（例如 Soft Formal），选择 JPEG / PNG / WebP。真实研究不要勾选“演示数据”；测试图请勾选。
3. 点击“上传到本机”。图片副本保存到 data/references/raw，来源和 RAW 记录一起保存。
4. 点击 Analyze。mock 不观察图片，生成未知属性草稿，状态 AI_GENERATED，不会自动通过审核。
5. 逐项填写可确认属性，例如 blush intensity=light_medium；不确定的值留空。补充来源和审核备注。
6. 勾选人工审核确认，填写审核者，点击 Verify & Save。保存版本、审核人、时间和历史。
7. 打开 /admin/rag，点击“重建 RAG 索引”。后台立即启用新索引，不需要重启。
8. 搜索“Dinner，想正式一点但不要太成熟”；Look 过滤可填 soft_formal，审核过滤选 verified=true 查看审核参考。

已审核记录再次 Analyze 只保存修订建议，原记录不变。人工修订必须再次审核，版本冲突要求重新加载。Reject/停用保留图片和历史，退出检索。保存不等于索引已更新；INDEXED 只表示当前版本在内存索引中。

## Look、流程与产品

在 /admin/knowledge 切换知识类型，创建或编辑；保存草稿用于研究，审核保存用于可用知识。新增 Look 可以先保存空 routine_ids，再创建属于该 Look 的 Routine，最后返回关联流程。所有编号唯一，保留稳定编号；不要把修改编号当作重命名。

流程按 order 排序；每步填写一个动作、慢速/重复指令、原因、成功条件、替代动作。视觉检查必须带 visual_task（blush_presence 或 lip_presence），用户仍可跳过。

产品只录入可核对的属性与官方声明；没有资料时填空/null，不推测。Source 记录 URL / 作者 / 日期 / 本地文件；相关知识的 source_ids 使用相同编号。所有事实都要由研究者核对。

## Excel / CSV

模板：templates/beauty_kb_template.xlsx；七张表为 LOOKS、ROUTINES、ROUTINE_STEPS、REFERENCE_CASES、PRODUCTS、ACCESSIBILITY、SOURCES。同目录有对应 CSV。第二行是 SAMPLE，必须替换编号、来源、内容和 demo_data。列表用 | 分隔，布尔 true/false，未知留空。删除不使用的示例行；表头保留，不使用公式。

在 /admin/knowledge 选择文件，CSV 先选对应类型。预览检查 accepted/rejected/warnings 和每个 sheet/row/field/message；再点击导入接受的草稿。导入不覆盖任何已有编号，verified 输入不会跳过人工审核。修正错误行后以相同新编号重试；已成功导入的编号会报告重复。

命令行（项目根目录）：
```powershell
.\.venv\Scripts\python.exe scripts/import_kb.py --file templates/beauty_kb_template.xlsx
.\.venv\Scripts\python.exe scripts/import_kb.py --file templates/products_template.csv --type PRODUCT --commit
```
默认仅预览。报告保存在 reports，CLI 暂存规范记录在 data/import/staged。异常不会静默丢弃：非法字段、未知工作表、空表头、公式、重复编号和失效关联都会提示。未知词表值是 warning，确认拼写后扩展 data/config 即可。

## 图片批量草稿和视频

```powershell
.\.venv\Scripts\python.exe scripts/analyze_reference_media.py --input data/references/inbox --look-id soft_formal --provider mock
.\.venv\Scripts\python.exe scripts/extract_video_frames.py --file data/references/inbox/tutorial.mp4 --timestamps 0:10,0:25,0:40
```
批量分析逐文件处理；失败文件出现在 reports/analysis_*.json，其他文件继续。所有结果仍需人工审核。视频仅抽选定帧，不调用模型、不分析整段视频；metadata.json 保留来源视频、请求/实际秒数。将帧作为图片导入，在编辑器填写 media_type=video_frame、frame_timestamp，并创建视频来源记录。不要把整段视频当作已分析的事实。

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
