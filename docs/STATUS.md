# TRACE 项目进度总览

核对日期：2026-11-11（UTC+8）  
核对源码：[`747f994`](https://github.com/Nah1zuj/codex-loreal-continuous-update/commit/747f99432594201487c3b20e8d82b11b3e8babcb)  
当前交付分类：**内部验证版**。工程候选、真实试用资格仍未通过完整验收。

本页是仓库证据的摘要，不是本次运行报告。2026-11-07 的软件测试、Mac 净安装及部分键盘操作记录已经存在；本次只核对仓库、建立任务和工作约定，未重新运行应用、调用真实供应商或开展人工验收。历史测试数量对应不同快照，不合并计算。已在线下完成但未回填的事项，提交实际证据后再更新。

> 2026-11-12 补充：Issue #12 已在固定 `main` `db485ed` 上准备匿名观察包、合成格式样例和记录校验器；校验器对当前未通过的 #8／#11 前置输出 `BLOCKED`。这不是目标用户试用，也不改变内部验证版分类；实时进展以 Issue #12 和关联 PR 为准。

## 先看这里

- [所有未完成任务](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aopen)；[4个里程碑](https://github.com/Nah1zuj/codex-loreal-continuous-update/milestones)。
- [安装和运行](../AccessibleBeautyAgent/README.md)；[演示与回退](quality/release-runbook.md)。
- [阶段和证据索引](quality/traceability.md)；[当前交付验证](../specs/008-accessible-release/verification.md)；[设备验收表](../specs/008-accessible-release/device-acceptance.md)。
- [贡献和进度更新方法](../CONTRIBUTING.md)；[给组员的整理报告](team-update-2026-11-11.md)。

## 当前目标和范围

先在共享仓库的固定版本上复核内部演示，再补齐真实服务与双平台设备证据，满足章程后标为工程候选。专业课程审核可并行准备；工程候选和课程审核通过后，才安排目标用户任务验收并判定真实试用资格。

核心流程：表达需求 → 澄清 → 可选方案或分步教学 → 暂停／恢复／结束 → 查看事实性小结 → 自主决定是否保存。自由交流、文字退路、权限分开确认和版本绑定均沿用现有规格。真实妆效判断、颜色阈值研究与真实硬件接入不作为本轮已交付能力。

## 已有证据与剩余缺口

下表“待验收”表示已有实现和软件证据，仍缺对应的完整验收；不把各阶段 tasks 的软件勾选理解为工程候选资格已通过。

> 2026-11-12 进展：已提出引入 [Pull Request 软件检查](quality/ci-software-checks.md) 的待审改动，用于后续 PR 的 Ubuntu 软件回归。该改动尚未合并，不改变 12 个验收 Issue 的当前状态，也不覆盖设备、真实服务和人工证据缺口。

| 模块 | 状态 | 已有证据 | 剩余事项 | 关联任务 |
|---|---|---|---|---|
| 1 运行与安装 | 待验收 | Mac 净安装、模型冷安装、缺模型文字路径与启停有历史记录 | 固定共享验收版本，Windows 净安装／实际入口与回归 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) |
| 2 会话与控制 | 待验收 | 权威计划、幂等命令、断流恢复、刷新不重开媒体有软件记录 | 实体媒体、双端读屏和实际独立评审 | [#3](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/3) [#4](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/4) [#5](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/5) [#10](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/10) |
| 3 对话与课程 | 受阻 | mock／回环替身、课程来源与审核门控有软件记录 | 真实文字供应商、专业课程审核 | [#6](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) [#8](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/8) |
| 4 语音 | 待验收 | 生命周期、120秒边界、合成输入及本机模型加载有记录 | 双平台麦克风、扬声器、耳机、回声、断连和真实播报 | [#3](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/3) [#4](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/4) |
| 5 本地视觉 | 待验收 | 授权撤销、过期结果、合成质量输入和模拟相机有记录 | 实体相机、光线／遮挡、左右理解和断开清理 | [#5](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/5) |
| 6 造型／标签／比较 | 受阻 | 六域操作、单张授权、原文和不确定性、比较出处有软件记录 | 真实标签服务、产品资料团队审阅 | [#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7) [#9](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/9) |
| 7 小结、日志与偏好 | 待验收 | 版本确认、防重放、删除、隔离和回退有软件记录 | 真实读屏及实际独立评审 | [#3](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/3) [#10](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/10) |
| 8 无障碍与交付 | 受阻 | 内部源码包、哈希清单、Mac 200% 部分键盘场景有记录 | 双平台完整验收、工程候选资格、目标用户任务验收 | [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2)–[#5](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/5) [#11](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/11) [#12](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/12) |

证据按上方阶段索引进入各 `verification.md`。本次核对也查看了运行配置、前端入口、联调与打包脚本；这是实现和文档对应核对，不代替完整代码审查或应用实测。

## 四个交付里程碑

| 里程碑 | 退出条件 | 当前情况 |
|---|---|---|
| [M1 内部演示复核](https://github.com/Nah1zuj/codex-loreal-continuous-update/milestone/1) | 固定共享验收 commit，内部关键路径和本轮软件结果可复查 | 历史内部记录已存在；本轮 [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) 待开始 |
| [M2 工程候选验收](https://github.com/Nah1zuj/codex-loreal-continuous-update/milestone/2) | 双平台安装、读屏、实体媒体、真实服务、资料与独立清单通过；无未解决P0和核心P1；交付包可复核 | [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2)–[#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7)、[#9](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/9)–[#11](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/11) 开放 |
| [M3 专业课程审核](https://github.com/Nah1zuj/codex-loreal-continuous-update/milestone/3) | 固定中英课程版本由实际专业审核者给出有效结论，并验证准入 | [#8](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/8) 受阻；可与M2并行准备 |
| [M4 目标用户试用](https://github.com/Nah1zuj/codex-loreal-continuous-update/milestone/4) | M2、M3通过后，按实际任务结果判定真实试用资格 | [#12](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/12) 受阻 |

没有约定截止日期，因此里程碑未设置日期。上述分组是交付阶段，不安排人员分工。

## 任务看板

当前使用 **Issues＋唯一状态标签＋里程碑** 作为轻量看板。已创建里程碑和标签；尚未创建原生 GitHub Projects，CLI 当前缺少 `project` 权限。这一限制不影响任务、状态及阶段维护。后续若补齐权限，可将现有 Issues 加入 Projects，避免重复建任务。

| 待开始 | 进行中 | 待验收 | 受阻 | 已完成 |
|---|---|---|---|---|
| [筛选](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aopen+label%3Astatus%3Atodo) | [筛选](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aopen+label%3Astatus%3Ain-progress) | [筛选](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aopen+label%3Astatus%3Areview) | [筛选](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aopen+label%3Astatus%3Ablocked) | [筛选](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aclosed+label%3Astatus%3Adone) |

这是 2026-11-11 的初始任务快照，后续实时状态以各 Issue 的最新正文／评论、状态标签和关联证据为准。每次推进同步本页摘要；只新增任务不算“进行中”。

| 任务 | 初始状态 | 已完成部分／剩余工作 | 前置依赖 | 完成标准摘要 |
|---|---|---|---|---|
| [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) 固定共享验收版本，复核内部演示 | 待开始 | 已有历史内部记录；剩共享版本的本轮复核 | 无 | 验收 commit 和环境明确，内部演示关键路径可复查 |
| [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) 完成 Windows 净安装、启停与恢复验收 | 受阻 | 已有Windows静态检查；剩实机安装启停 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) | Windows 实机记录绑定同一验收 commit，安装和启停各有结果 |
| [#3](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/3) 验收双平台键盘、缩放和真实读屏播报 | 待验收 | 已有软件及Mac部分键盘记录；剩双端实际播报 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) | 双平台关键场景均有实际播报摘录或现场观察和结论 |
| [#4](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/4) 验收双平台实体麦克风、扬声器与耳机 | 待验收 | 已有合成及模型记录；剩双端实体音频 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) | 双平台每个实体场景有输入、期望、实际结果及观察证据 |
| [#5](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/5) 验收实体相机、左右理解与撤权清理 | 待验收 | 已有模拟相机记录；剩实体相机与方向理解 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) | 实体相机与模拟输入结果分列，双平台场景有记录 |
| [#6](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) 完成真实文字供应商联调 | 受阻 | 已有替身协议；剩实际文字调用 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) | 真实供应商、模型、commit、日期与执行命令可核查，凭据不进入记录 |
| [#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7) 完成真实标签识别与单张授权联调 | 受阻 | 已有替身及授权检查；剩清晰／模糊真实标签 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) | 真实服务清晰与模糊输入各有实际响应和人工对照结果 |
| [#8](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/8) 完成中英基础课程的真实专业审核 | 受阻 | 已有审核包；剩真实专业意见与准入 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) | 中英文每个必要步骤都有真实审核意见与最终状态 |
| [#9](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/9) 完成产品比较资料的团队审阅 | 待验收 | 已有官方出处草稿；剩实际团队资料审阅 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) | 每条现有比较资料有来源及真实团队审阅结论 |
| [#10](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/10) 完成阶段1–8独立清单与结构收敛评审 | 待验收 | 已有规格与软件材料；剩独立清单结论 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) [#3](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/3) [#4](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/4) [#5](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/5) [#6](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) [#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7) [#9](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/9) | 阶段1–8各有实际评审范围和结论，未验项目保留未勾选 |
| [#11](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/11) 复核交付包与工程候选资格 | 受阻 | 已有内部包和手册；剩完整资格与固定版本包复核 | [#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) [#3](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/3) [#4](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/4) [#5](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/5) [#6](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) [#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7) [#9](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/9) [#10](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/10) | 前置任务达到各自完成标准，双平台真实证据完整 |
| [#12](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/12) 开展目标用户关键任务试用并判定真实试用资格 | 受阻 | 已有任务表及待审的匿名观察准备包／格式校验；剩 #8、#11 通过后的真实目标用户观察 | [#8](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/8) [#11](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/11) | 参与条件、实际样本数、逐任务原始观察与结论可复查 |

初始12项：待开始1、待验收5、受阻6；没有已确认的本轮进行中任务。它们只统计本次剩余验收清单，不代表整个产品完成率。每项详细步骤、验收标准、资料和解除条件见对应 Issue。

## 阻塞与待核实

- **Windows：**仓库缺实体记录，不据此推断团队一定没有设备。核实设备或回填已有记录后更新 [#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2)。
- **真实服务：**历史记录为 mock／关闭远程／无有效凭据；本次未读取私有配置。核实批准的配置、目的地及实际响应后更新 [#6](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) [#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7)。
- **专业与用户验收：**缺真实课程审核和目标用户观察记录，按 [#8](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/8) → [#12](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/12) 的条件推进。
- **版本与文档：**多个历史包、共享合并提交和测试数量并存。[#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) 先固定共同验收版本。路线图原有“尚未启动实施”和结尾“仅整理计划书”已修正；能力矩阵保留为阶段0快照，勿当实时状态。
- **实际独立评审：**多份清单仍待实际评审者确认；软件勾选不能替代，见 [#10](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/10)。保留构建分包警告，不将其隐去或未经分析升级为缺陷结论。

## 下一步最值得推进的三项

1. **[#1](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/1) 固定验收版本、复核内部演示。**为后续证据提供同一基准。
2. **[#2](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2) 核实 Windows 环境并完成净安装。**解除双平台设备验收的共同前置。
3. **[#6](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) 核实并联调真实文字服务。**填补当前自由对话只有 mock／替身证据的缺口。

三项没有人员分配。Windows准备、私有配置预检、课程审核联系和Mac场景可并行；编号不等于必须逐项串行。真实标签服务 [#7](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7) 的准备也不依赖文字服务联调完成。

## 状态如何更新

每个 Issue 恰好一个 `status:*` 标签，并与标题和正文一致：待开始／进行中／待验收／受阻／已完成。受阻时写具体条件、已做尝试和下一步；部分完成勾选对应步骤并保持开放。全部标准满足、证据可复查且相关修改已进入共享验收版本后，标为已完成并关闭；有PR不等于完成。

每次更新记录日期、实际 commit、环境、操作与结果、剩余事项、PR和证据链接。软件验证用 PASS／FAIL／NOT RUN／BLOCKED 分层记录；不把旧记录当新实测，不公开密钥和个人数据。具体流程见 [CONTRIBUTING](../CONTRIBUTING.md)。
