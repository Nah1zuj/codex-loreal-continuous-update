# 需求追踪与阶段入口

阶段内追踪采用「US → FR → 契约/设计 → T → 测试/人工操作 → 证据 → Git 版本」。缺陷 B 与结构项 C 另见 [缺陷](bugs.md) 和 [结构清单](architecture-cleanup.md)。

| 阶段 | 规格 | 前置依赖 | 验收证据归属 |
|---|---|---|---|
| 0 | [基线](baseline.md) | 原始代码和环境 | evidence/stage-0.md |
| 1 | [001-runtime-baseline](../../specs/001-runtime-baseline/spec.md) | 阶段 0 | 该规格 verification |
| 2 | 002-session-control | 1 | 会话命令契约、SQLite 和竞争回归 |
| 3 | 003-dialogue-knowledge | 2 | 真实文字、课程审核与检索 |
| 4 | 004-voice-interaction | 2、3 | 合成音频与双平台设备 |
| 5 | 005-local-vision | 2 | 视觉样例与撤销 |
| 6 | 006-styling-reading | 3、5 的授权约束 | 六域局部修改、远程标签及比较 |
| 7 | 007-confirmed-memory | 2、3 | 迁移和回退、隔离和删除 |
| 8 | 008-accessible-release | 1–7 | 实体读屏、发布清单、完整链路 |

每阶段开始前细化对应规格。无障碍、权限与去冗余贯穿全程。真实试用还需专业及目标用户验收。
