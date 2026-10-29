# V4 研究证据到运行规则

核验日期：2026-10-11。状态：研究登记完成；运行时接入及回归由主实施者验证。此文件不代表模型已经训练，也不代表真实 BLV 用户验收通过。

读取了 SoftFormal 的 source_registry / evidence_to_policy、FullLook 的 research_evidence_shortlist、Integration Bundle 的官方来源索引，以及 Downloads/accessibility_evidence.xlsx（只读）。Excel 9 个工作表的实际非空行数在 `data/research/v4/excel_inventory.json`。Excel 的 curated/verified 标记不能替代本轮全文核验。

在项目、Downloads 与 Documents/Codex 按相关论文中英文文件名扫描，没有定位索引对应的本地授权 PDF，记为 **MISSING_IN_SEARCHED_PATHS**，不表示用户其它磁盘一定没有。未读取不相关个人文件。没有下载全文或绕过付费墙。

本轮核对 **9 篇原始研究来源**，其中 8 篇摘要/研究库描述，1 篇 Frontiers 原文方法与摘要部分。未完成 8–15 篇全文精读，明确记为未达到全文深读目标。来源、边界与全部规则分别在 `sources.json` / `evidence_rules.json`；全部保留 DRAFT。

| 来源 | 核对范围 / 迁移 | 规则与回归案例 |
|---|---|---|
| [Li 2025](https://arxiv.org/abs/2507.03942) | 摘要；15 位 VI 化妆用户、5 位化妆师；直接化妆 | 用户可要求概览/慢一点/重复；慢一点不得自动下一步；触觉策略不变成所有人的统一偏好 |
| [Li 2022](https://arxiv.org/abs/2203.08864) | 摘要；145 视频、12 访谈；直接化妆 | 保留用户既有指腹等技法；不强制重学 |
| [Daniels/Khadaroo 2024](https://ualresearchonline.arts.ac.uk/id/eprint/23071/) | 研究库摘要；vlogger主题分析；直接化妆 | 产品熟悉与反复练习是研究观察，不默认无能或需要从零开始；DOI核对为10.1386/csfb_00078_1 |
| [Pradhan/Daniels 2021](https://ualresearchonline.arts.ac.uk/id/eprint/16706/) | 研究库描述；综述和调查；直接商品可及性 | DOT只读清楚的标签；半截色号不得猜；未核对调查样本量 |
| [Amershi 2019](https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf) | 原始摘要/作者官方指南；一般HAI远迁移 | 能力说明、纠正、撤销、跳过；Mock必须明确演示 |
| [Kim 2024](https://arxiv.org/abs/2405.00623) | 摘要；N=404医疗问题实验；远迁移 | 不确定必须有具体边界；并非腮红识别验证，措辞不能替代校准 |
| [Bharadwaj 2019](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2019.00443/full) | 摘要及方法；14招募、12纳入；导航近迁移 | 保留暂停与替代通道；不能断言化妆用户一定喜欢触觉或声音 |
| [VizWiz 2018](https://arxiv.org/abs/1802.08218) | 摘要；盲人真实摄影问答；近迁移 | 遮挡/不包含目标可无法回答，重拍或跳过 |
| [PSGAN](https://arxiv.org/abs/1909.06956) | 摘要；妆容图像迁移；技术背景 | 合成妆效图不得变成ECHO真实识别Gold Set |

Sharif称呼偏好及Edge-Based Color Constancy仍登记 **NOT_VERIFIED_THIS_RUN**；ACM DOI请求403，没有以二手搜索结果替代原始论文核查。现有称呼/颜色规则保留为项目约束或待审核设计推论，而非本轮核实研究结论。

运行映射已经接入并在本机验证：`backend/app/policies/registry.py` 在 Agent 启动时读取 accessibility、guidance、visual_feedback、full_look_planner、material_description、brand_copy 六份 v4 策略，健康接口返回各文件 SHA-256；语言、视觉和吊牌读取服务把对应策略加入实际 provider 请求。`tests/test_v4_policies.py` 验证文件加载、语言 prompt、服装成分未知与不清字符降级。Camera/Memory 同意仍由程序状态机强制，不能依赖 Prompt。测试命令和数量见 `TRACE_V4_TEST_REPORT.md`。

明确的项目约束：不得从照片推断残障、焦虑或真实情绪；不得怜悯/幼儿化；品牌语言不进入执行危险动作；造型确认不等于长期Memory同意。这些是产品约束，不能倒称所有论文逐项实证支持。
