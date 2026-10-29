# V4 产品、材料与媒体审查

核验日期：2026-10-11。所有新增记录在 `data/research/v4/` 隔离，没有修改 canonical data/knowledge，没有自动导入RAG，没有human_verified=true，没有公开素材或发送真人图像。

本轮读取旧 source_registry、两份 image_review_queue、FullLook research shortlist。重新计算 27 张图片 SHA256（6原始照片、11视频帧、10新增参考图），见 `assets_hash_review.json` / `hash_duplicates.json`。只核对完全相同字节，不宣称感知去重。既有表记载旧上传文件存在重复，不能把文件名备注当本轮哈希结果。

每张本轮资产登记 source、creator未知null、permission_status=UNKNOWN、may_display_publicly=false、content_role=INTERNAL_REFERENCE_ONLY、annotation_status=DRAFT、gold_label_eligible=false。FullLook VISREF004/005为合成Prompt例；002/007/010为广告对比，其余按原审核表分类。所有版权未知资产继续内部隔离，不把广告/AI前后图当真实功效、识别Gold Set或独立真值。未取得素材授权，公开展示数量为0。视频仅审核既有帧，不传播完整视频。

[欧莱雅官方品牌组合](https://www.loreal.com/en/our-global-brands-portfolio/)用于集团归属边界。只核对品牌美国官方页，没有将美国版当中国在售版，也没有推断衣物业务。

| 类别 | 官方候选 | 本轮可核对的品牌宣称 |
|---|---|---|
| base | [L’Oréal Paris True Match Nude Hyaluronic Tinted Serum](https://www.lorealparisusa.com/makeup/face/true-match-nude-hyaluronic-tinted-serum-hydrates-all-in-1) | 轻量覆盖、自然光泽；1%玻尿酸为官方宣称 |
| blush | [Maybelline Cheek Heat Gel-Cream Blush](https://www.maybelline.com/face-makeup/blush-and-bronzer/cheek-heat-gel-cream-blush-face-makeup) | 水基凝霜、可叠加色彩、柔和水光 |
| lip | [NYX Butter Gloss](https://www.nyxcosmetics.com/lip/lip-gloss/butter-gloss-non-sticky-lip-gloss/NYX_089.html) | 高光泽、薄至中等覆盖、不黏为官方宣称 |
| fragrance | [Lancôme Idôle Eau de Parfum](https://www.lancome-usa.com/fragrance/fragrance-by-collection/idole/idole-eau-de-parfum/LAN387.html) | 品牌Fresh Floral分类；玫瑰/茉莉中调，白麝香/香草/广藿香/雪松基调 |

候选 CSV 和 JSON字段含title、brand、region、shade、finish、official_claims、official_url、accessed_at、source_id、review_status。4项全部DRAFT，shade=null；香氛finish=null。独立科学证据=null。没有摘录消费者评论作为官方宣称；香气不能通过摄像头检测。用户不喜欢甜香时，Idôle含香草的官方描述不能用来保证“不甜”。没有选色号或替用户确认耐受性。商品页可访问不表示授权复用产品图。

材料候选见 `material_candidates.json`，8项全部DRAFT/human_verified=false。来源包括Cotton Incorporated、Alliance Flax-Linen-Hemp、Woolmark、Silk Mark India、Toray、Lenzing。厂商/行业组织的性能宣传不等于跨所有织物的独立科学定论。

| 条目 | 类型 | 安全描述与来源 |
|---|---|---|
| 棉 | fiber | [CottonWorks技术资料](https://cottonworks.com/product-innovation/nonwovens/technical-and-performance-guide/)；纤维可构成梭织/针织，吸湿与透气不是同一指标 |
| 亚麻 | fiber | [Alliance属性资料](https://allianceflaxlinenhemp.eu/en/flax-performance-and-properties)；自然纹理候选，具体透气性仍依结构与厚度 |
| 羊毛 | fiber | [Woolmark Cool Wool](https://www.woolmark.com/industry/use-wool/product-innovations/cool-wool/)；也有轻薄织物，不能一定厚热/不刺痒 |
| 丝绸 | fiber | [Silk Mark官方FAQ](https://silkmarkindia.com/index.php/faq/)；认证针对天然丝，照片光泽不能确认成分 |
| 缎面 | weave | [CottonWorks梭织组织](https://cottonworks.com/learning-hub/weaving/basic-woven-fabric-designs/)；长浮线常形成光泽，术语有地域差异，缎面不是成分证明 |
| 聚酯 | fiber | [Toray官方技术介绍](https://www.toray.com/aboutus/download/pdf/toray_g_dl2018.pdf)；抗皱为厂商一般描述，手感依工艺 |
| 粘胶 | fiber | [Lenzing生产技术](https://www.lenzing.com/technology-production/technologies/)；再生纤维素，不等于棉/天然丝 |
| 针织 | knit | [CottonWorks Knit Basics](https://cottonworks.com/learning-hub/knitting/knit-basics/?highlight=jersey%2Bknit)；线圈结构，可有结构伸展性，不等于羊毛 |

统一边界：重量/垂坠/柔软度/光泽/透气性分别表达，以具体织物及标签为准；不保证舒适、过敏安全；照片只描述可见光泽、褶皱等，不确定纤维百分比。洗护依据具体衣物标签。服装建议为品牌中立类别级资料。

后续人工任务：确认论文全文和适用性；审核材料中文概述；选地区SKU和色号；获取原创者及发布许可；建立独立授权Gold Set。只有完成审批的记录才可进入正式索引。此次没有重建RAG，因此不存在可宣称的本轮新索引时间/条目计数。
