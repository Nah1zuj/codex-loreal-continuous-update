# 需求追踪与阶段入口

阶段内追踪采用「US → FR → 契约/设计 → T → 测试/人工操作 → 证据 → Git 版本」。缺陷 B 与结构项 C 另见 [缺陷](bugs.md) 和 [结构清单](architecture-cleanup.md)。

| 阶段 | 规格 | 前置依赖 | 验收证据归属 |
|---|---|---|---|
| 0 | [基线](baseline.md) | 原始代码和环境 | evidence/stage-0.md |
| 1 | [001-runtime-baseline](../../specs/001-runtime-baseline/spec.md) | 阶段 0 | [运行基线](../../specs/001-runtime-baseline/verification.md) |
| 2 | [002-session-control](../../specs/002-session-control/spec.md) | 1 | [会话命令、SQLite 和回归](../../specs/002-session-control/verification.md) |
| 3 | [003-dialogue-knowledge](../../specs/003-dialogue-knowledge/spec.md) | 2 | [文字链路、课程审核与检索](../../specs/003-dialogue-knowledge/verification.md) |
| 4 | [004-voice-interaction](../../specs/004-voice-interaction/spec.md) | 2、3 | [语音软件验证与设备待办](../../specs/004-voice-interaction/verification.md) |
| 5 | [005-local-vision](../../specs/005-local-vision/spec.md) | 2 | [本地视觉和撤销](../../specs/005-local-vision/verification.md) |
| 6 | [006-styling-reading](../../specs/006-styling-reading/spec.md) | 3、5 的授权约束 | [六领域、标签与产品比较](../../specs/006-styling-reading/verification.md) |
| 7 | [007-confirmed-memory](../../specs/007-confirmed-memory/spec.md) | 2、3 | [确认、删除与回退](../../specs/007-confirmed-memory/verification.md) |
| 8 | [008-accessible-release](../../specs/008-accessible-release/spec.md) | 1–7 | [软件及双平台发布门槛](../../specs/008-accessible-release/verification.md) |

每阶段开始前细化对应规格。无障碍、权限与去冗余贯穿全程。真实试用还需专业及目标用户验收。
