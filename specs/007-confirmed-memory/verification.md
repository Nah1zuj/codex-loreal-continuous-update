# 确认式记忆阶段验证

**日期** 2026-11-07

**环境** macOS arm64，Python 3.12，隔离 SQLite，mock 与合成内容。回环 HTTP 使用独立 Uvicorn 进程和端口。实际评审者确认仍待办。

| 需求 | 结果 | 证据 |
|---|---|---|
| FR-701 查看、朗读、修改与拒绝 | PASS（软件） | 完成时输出候选，拾光界面允许阅读或朗读。修改后须再预览，未勾选确认时保存按钮不可用。拒绝后候选不可重放，无摘要行。组件测试覆盖修改和确认；实体朗读见阶段 8。 |
| FR-702 摘要版本与幂等 | PASS | 跨版本、篡改、未授权均拒绝；并发确认只保存一条。回环实测编辑和重试。 |
| FR-703 独立授权与日志 | PASS | 摘要与偏好确认不写日志。独立日志支持保存、版本编辑、复制为草稿与删除，删除同步清除已授权原文。偏好由 `/memory/preview` 或会话提供版本，缺版本的布尔确认被拒绝。 |
| FR-704 旧记录和数据删除 | PASS | 未确认旧摘要不会进入复用；重新确认后，只有显式选择的风格枚举可用于新计划。删除清除已确认摘要、旧来源和复用指针；偏好删除清除派生档案、旧日志内嵌快照及未来对话上下文。 |
| FR-705 保留与隔离 | PASS | 测试模拟进度与摘要过期并核对事件和回执清理。日志和偏好不随 30 天清理；跨浏览器读取、确认与删除失败。同浏览器的命名空间可读取和确认其自身课程摘要，列表与默认空间隔离。 |
| 实际设备与评审 | NOT RUN | 保留 Mac VoiceOver、Windows NVDA、实际人工清单与试用验证。 |

隔离后端定向回归 52 项通过。前端拾光、日志和造型保存相关的 4 项组件测试通过，类型检查通过。真实回环 HTTP 确认摘要和偏好独立版本、重复提交和删除均通过。无日常库迁移。

后续复核在上一交付包以两个独立浏览器身份复现 B-010。普通 JSON 会拒绝外部身份，特殊请求头下后端仍读取 JSON 并执行命令。修复后，供应商类型 JSON、缺失或空白的 `Content-Type`、大小写变体、重复请求头均按同一身份规则处理。真实回环后端拒绝第二个身份，课程步骤保持不变；同一拥有者可继续操作。测试库回归同时覆盖独立日志保存、越权删除和正常删除。

复核从应用目录执行。

```bash
.venv-portable/bin/python -m pytest -o addopts='' -q tests/test_confirmed_memory.py tests/test_private_journal.py tests/test_v2_privacy.py tests/test_trace_phase3.py tests/regression/test_acceptance.py tests/test_v4_full_look.py tests/test_recollection_v2.py
cd frontend && npm test -- --run src/pages/LookRecollection.test.tsx src/pages/Journal.test.tsx src/components/SaveLookRecord.test.tsx
```
