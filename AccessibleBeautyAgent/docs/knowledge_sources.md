# 知识来源与使用权

当前 canonical 集合：3 LOOK、3 ROUTINE、2 REFERENCE_CASE、12 PRODUCT、49 ACCESSIBILITY_GUIDANCE、2 SOURCE。其中新增 48 段项目原创中英文教程草稿，原文件 `data/import/trace-original-tutorials.json`；不称其为专业审核数据或训练样本。

来源登记于 `data/config/knowledge_sources.json`，只接受 original / cc-by / cc0 / licensed 且附权利证据的文本 JSON。unknown / citation_only 不复制；每次最多 500 段 / 4MB，按来源、语言和正文去重。带时间戳的文本段可导入，整段视频、图片不导入。导入先 dry-run，commit 后仍为 DRAFT、verified=false，需知识后台人工审阅后才可进入生产 verified-only 检索。开发模式可显示演示/草稿，必须披露来源状态。

L’Oréal 的四大业务部门与品牌只作为参考语境，来源为 [官方品牌组合](https://www.loreal.com/en/our-global-brands-portfolio/)，不是全品类 SKU、库存、价格或购买承诺。无障碍化妆参考登记 [RNIB applying make-up](https://www.rnib.org.uk/living-with-sight-loss/independent-living/applying-make-up/)，当前仅 citation-only，没有复制全文。

不把公开访问当复制许可，不自动抓取未知权利教程。尚未采购/授权专家教程、标注照片或金标准，不进行视觉模型训练。Mock embedding 是本地测试近似，不是真实语义训练；可另配置兼容检索供应商，但未在本次启用远程 embedding。
