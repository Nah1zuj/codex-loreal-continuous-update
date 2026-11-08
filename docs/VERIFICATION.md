# 第五阶段：TRACE-Next 通用迁移验收

日期：2026-11-08。结论：**通用迁移的软件候选通过本轮自动验收，可进入赛事特化设计讨论；未切换或替换旧项目，尚非已上线的支付宝参赛作品。**

## 源码与实现范围

旧基线：fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07。旧项目576个已跟踪文件SHA-256全部未变，HEAD未变，工作树干净（证据：migration/evidence/old-source-unchanged.json）。没有读取或搬运旧.env、用户数据库或录音。基线执行副本从git archive固定提交生成。

新目录：TRACE-Next。398个旧文件按A—E组迁入，其中392个逐字节复用，6个调整（入口、默认端口、发布标识、说明和对应端口测试）；新增服务组装composition.py、应用工厂factory.py、命名扩展extensions.py、9个工厂边界检查和迁移工具/规格。不是宣称全量重写；优先保留已有领域逻辑，真正重构应用组装与接入边界。逐文件哈希与处理方式见migration/port-manifest.json。

## 本轮实际执行

| 检查 | 结果 | 证据 |
|---|---|---|
| 旧提交隔离副本后端回归 | 268通过、3跳过 | migration/evidence/baseline-pytest.log |
| 新独立Python环境后端回归 | 277通过、3跳过 | migration/evidence/new-pytest.log、new-pytest.xml |
| 前端单元/组件检查 | 191通过、0失败 | migration/evidence/frontend-test-summary.json |
| 类型检查和生产构建 | 通过，保留大分包警告 | migration/evidence/frontend-build.log |
| 本地语音软件单元 | 10通过 | migration/evidence/voice-tests.log |
| 知识库结构/来源检查 | PASS；3Look/3Routine/2Reference/14Product/73Guidance/5Source | migration/evidence/knowledge-validation.log |
| 相同输入新旧对照 | 4组场景、52组成对请求；响应码/完整JSON与SSE/状态/数据库内容无差异 | migration/evidence/compatibility-report.json |
| 运行时OpenAPI与SQLite schema | 新旧完全相同 | migration/evidence/old-compatibility.json、new-compatibility.json |
| 实际启动与无模型退路 | 占用端口不抢占；前端/API/SQLite/文字/恢复正常；重复启动保护、doctor、停止释放端口通过 | migration/evidence/runtime-smoke.log |
| Mac新目录独立安装 | 锁定依赖安装、pip check、npm ci/build通过；不依赖旧目录虚拟环境启动 | migration/evidence/installation.log |
| 旧源保护 | 576文件SHA/HEAD/工作树复核通过 | migration/evidence/old-source-unchanged.json |

3个跳过项：2个Windows PowerShell平台专用检查；1个需要下载本地视觉模型的检查。未将它们计作通过。新旧副本均不含下载权重，正是缺模型降级验证条件。

A组先验证知识与记忆的同意、签名版本、幂等、所有者、删除重放和重复SQL迁移；B组核心依赖闭包及工厂131项通过后继续C（语音10/硬件9），D（前端），E（独立安装及运行）。集成回归发现一项旧测试写死5180，改为读取runtime默认端口后通过；未放宽来源限制。新默认5280/8112/8113与旧5180/8012/8013分开。

## 对照方法及限制

两个独立进程加载各自的源码，采用同样的mock配置、合成身份、固定UUID/随机数/时间、各自临时SQLite。逐次核对请求响应、SSE事件和状态，并核对场景结束数据库行。仅将SQLite记录迁移应用时间的applied_at和源码根目录路径归一化，不删除业务字段、错误或状态。对照工具在migration/compatibility.py，可重新执行；样本为migration/evidence/compatibility-samples.json。固定随机数只用于独立验收进程，不进入产品运行代码。

52对请求包括正式晚餐旧课程、新教学幂等/冲突/暂停/继续/跳过/提前结束、陌生浏览器及5种JSON Content-Type拒绝、恢复与重启回执、偏好审阅和严格同意/篡改/删除重放、造型版本冲突、标签演示与拒绝、流式开始与结束。它不是对所有83条静态路由的逐路由独立对照，其他细分行为由完整原有回归及逐字节复用覆盖。

新增扩展只提供命名挂载与服务上下文。未来支付的账户、订单所有者、回调验签、退款、交付和权益必须单独实现，不能因为继承/api中间件就宣称已有支付安全性。

## 未完成和不自动切换的边界

- 未接入支付宝SDK、订单/支付回调/退款/权益，未报名、未创建真实交易、未发布。
- 没有在本轮下载/实测语音或视觉模型，语音10项是软件单元，视觉回归主要为mock/合成输入；不能称作真实视障美妆准确率证据。
- Windows实机、Mac/Windows真实读屏、实体麦克风/摄像头、远程AI供应商、专业课程审核、目标用户试用尚待独立验收。本轮没有重做网页视觉对照，前端源文件除发布标识外逐字节保留。
- 当前匿名Cookie只适用本机隔离；管理与CORS规则仍按本地工程设计，不能直接把Vite开发服务暴露成生产参赛入口。
- 旧用户数据不迁移、不覆盖。回退时停新目录、运行旧目录。后续如要搬用户数据，需另做一致性备份、迁移和回退验证。

## 本轮交付后的下一步

已要求赛事调研聊天重读新项目与本报告，输出《支付宝比赛特化计划书》。推荐赛道与商业模式是待讨论建议，不因通用迁移完成而自动获得批准。正式账号、商户/产品准入、商品/价格/退款规则、真实付款及发布等由该计划明确前置条件。
