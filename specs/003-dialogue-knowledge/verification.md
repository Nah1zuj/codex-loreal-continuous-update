# 对话与课程阶段验证

**日期** 2026-11-07

**基线** a04b0ec 后的阶段 3 实现，当前分支；Python 3.12 环境，隔离 SQLite，运行知识库中 `trace_original_phase4` 版本 2。

**审核** [实际评审清单](checklists/requirements.md) 待真实评审者确认。

| 要求 | 结果 | 证据 |
|---|---|---|
| FR-301 无意推进 | PASS | 定向测试覆盖询问下一步、否定、前一步说明、重复、闲聊以及明确下一步。询问前一步和未完成声明保持版本。 |
| FR-302 草稿需求 | PASS | 新测试验证场合、妆感、时间、工具、避讳；选择避开底妆时不编入底妆。真实 Uvicorn 回环 SSE 使用 mock 与隔离库，澄清、开课与推进均通过。 |
| FR-303 候选校验 | PASS | 注入供应商传输测试覆盖未知步骤、缺环节、乱序、重复、越权工具与合法同主题替代。开课和推进播报使用权威数据。 |
| FR-304 来源和试用准入 | PASS（软件） | 数据校验通过；临时库验证来源不足无法批准、五步通过审核后可进入，未审核译文不会替换，停用后不能继续。 |
| FR-305 基础课程 | PASS（软件） | 中英五步课程与四个检索案例检查动作相关性、来源、版本、开发草稿及试用门控。 |
| FR-306 远程故障 | PASS（注入） | 注入的传输故障保留已提交步骤并返回错误事件。 |
| 实际文字供应商 | BLOCKED | 当前项目配置 mock、关闭远程、无有效配置密钥。未发送远程请求。 |
| 专业审核和真实试用 | BLOCKED | 尚无实际审核者确认，工程草稿不进入真实试用。 |

复核命令在应用目录执行。

```bash
.venv-portable/bin/python -m pytest -o addopts='' -q tests/test_dialogue_knowledge.py tests/test_phase4_intents.py tests/test_phase4_flow.py tests/test_phase4_controller.py tests/test_voice_first_guidance.py tests/test_session_commands.py tests/test_v2_conversation.py tests/rag
.venv-portable/bin/python scripts/validate_kb.py
```

定向回归 87 项通过。知识库检查 PASS（3 妆容、3 流程、2 参考、12 产品、73 指引、3 来源；其他阶段新增记录另计）。Spec Kit prerequisites 通过。远程模型的非命令自由对话仍是生成文本，服务端只允许已验证的业务事实进入命令响应。

联调复核已跑通独立 TRACE 后端和回环 HTTP 供应商替身。脚本先检查配置，再在明确执行时发送固定虚构语句，核对最终事件及同一浏览器身份中的供应商响应证据。测试没有外发语句，真实供应商仍待配置和联调。[联调步骤](../../docs/quality/release-runbook.md#真实文字与标签联调)
