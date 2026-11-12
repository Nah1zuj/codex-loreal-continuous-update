# Issue #9 产品资料来源字段初审（2026-11-12）

关联任务：[#9 完成产品比较资料的团队审阅](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/9)

## 结论

两条现有比较资料的名称、类别和妆效字段仍可由 Maybelline 美国官网支持；应用没有把价格、购买信息、功效、配方、持妆声明或适用性带入比较。Matte Ink 的 `matte` 为直接对应；Vinyl Ink 的 `glossy` 是对官网 `instant shine / vinyl finish` 的亮泽类别归一化，必须保留这一解释，不能写成官网逐字字段。

本页是 GPT/Codex 的来源字段初审，不是 TRACE 团队成员的实际审阅签字，也不评价产品是否适合任何用户。

## 字段对照

| 目录条目 | 应用字段 | 官方页面支持 | 当前处理 |
|---|---|---|---|
| Super Stay Matte Ink Liquid Lipstick | 品牌、名称、唇部类别、`matte` | 页面标题与 About/Finish 支持 | 保留；底调、饱和度未知 |
| Super Stay Vinyl Ink Longwear Liquid Lipcolor | 品牌、名称、唇部类别、`glossy` | 页面标题与 About/Finish 支持 `instant shine / vinyl finish` | 保留 `glossy` 作为亮泽类别归一化并明确边界；底调、饱和度未知 |

官方页面虽然还包含价格、具体色号、配方、使用方法和持妆等信息，本项目当前比较接口没有纳入这些字段。本轮也没有据此扩张产品主张。

## 界面与软件边界

- `evidence_kind=source` 显示“厂商公开资料”；虚构样例显示“虚构演示属性”；未知条目显示“缺少可追溯的资料”。
- 两条来源产品仍为 `DRAFT`，界面显示“团队审核待完成”，没有冒充已核验。
- 没有具体色号时，饱和度和底调保持 `null` 并显示“未知”。
- 用户的 matte/glossy 选择单独显示为“你的个人偏好”，不写回厂商字段。
- 来源链接和查看日期随比较结果显示；查看日期更新为 2026-11-12。

新增 `Pair.test.tsx` 覆盖上述来源、未知值、待审核标记、链接及偏好隔离。后端既有比较测试继续覆盖来源、虚构样例和未知条目的分类。

补充增加 `scripts/verify_product_source_boundaries.py`：校验当前目录仍为 14 条（12 条虚构演示、2 条厂商来源草稿），两条真实记录只包含本次审阅覆盖的名称、品牌、唇部类别、妆效、来源和审核状态字段；来源 URL、标题、查看日期和本轮完整边界备注必须保持一致。产品与来源编号必须唯一，`demo_data` 必须是严格布尔值；保留原有关键词后追加宣传语也会失败，避免将未经审阅的扩张藏进自由文本。普通模式和 `python -O` 均通过；产品边界与读取服务定向测试共 31 项通过。该检查只锁定仓库内的字段边界，不能代替重新打开网页或团队审阅。

## 尚未完成

1. TRACE 团队实际审阅者尚未填写结论；产品状态继续为 `DRAFT`。
2. 若团队不接受 `glossy` 作为 `instant shine / vinyl finish` 的归一化，应另行决定受控词表，而不是静默改写官网表述。
3. 任何未来新增的价格、配方、功效、具体色号或购买建议都需要新的字段级来源和审阅，不能沿用本页结论。

## 来源

- [Maybelline Super Stay Matte Ink](https://www.maybelline.com/lip-makeup/lipstick/superstay-matte-ink-liquid-lipstick)，2026-11-12 查看。
- [Maybelline Super Stay Vinyl Ink](https://www.maybelline.com/lip-makeup/lipstick/super-stay-vinyl-ink-longwear-liquid-lipstick)，2026-11-12 查看。
