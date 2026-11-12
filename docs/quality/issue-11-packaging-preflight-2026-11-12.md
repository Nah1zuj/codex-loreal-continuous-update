# Issue #11 固定 main 打包预检（2026-11-12）

关联任务：[#11 复核交付包与工程候选资格](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/11)

## 首次结果：FAIL

在独立 worktree 对 GitHub `main` `db485ed098d433758358e8cc6280af5d4003afe1` 执行打包器，首次以退出码 1 失败：

```text
Packaging failed: private or local file tracked in release tree: AccessibleBeautyAgent/voice/models/
```

原因是 main 已跟踪本地语音模型目录和资产，而打包器在判断 ZIP 目录项之前调用私有路径拒绝逻辑。此前 `fd6154a` 的打包通过不能证明最新 main 可打包，因为该提交没有跟踪这组模型资产。

修正目录项顺序后，第二次执行继续以退出码 1 失败，指向根目录 `本次桌面备份说明/`。进一步枚举确认 main 还跟踪 `项目资料/`、`验证与历史说明/` 等本地研究包和历史验证资料，其中包含大型论文、旧压缩包、截图和历史回归记录；这些目录本来就在打包器的 `LOCAL_DIRECTORIES` 排除集合中，但旧实现同样选择报错而不是跳过。

## 修复边界

打包规则原本就要求语音模型、运行目录、本地研究资料和历史验证文件不进入源码包。本修复先验证归档路径安全，再忽略目录项，并明确跳过 `AccessibleBeautyAgent/voice/models/` 以及 `LOCAL_DIRECTORIES` 命中的整棵树。数据库、密钥、私有环境、用户数据、未获批准的公开媒体和意外符号链接仍按原规则拒绝，不把“排除已知本地树”扩大成放松私有文件检查。

新增两项回归：

1. Git 快照同时含模型目录、ONNX、tokens 和公开 README 时，只打包 README，manifest 只列公开文件。
2. 快照含用户 SQLite 时仍必须失败。

## 资格边界

本修复只解除“最新 main 因已跟踪模型目录无法生成源码包”的软件缺陷。即使固定提交的临时审计包随后通过，也不能提升为工程候选：#2–#7、#9、#10 的真实设备、服务和人工结论仍未全部满足，且正式候选包必须从最终合并后的固定 commit 重新生成。

## 修复后精确 main 审计包：PASS

使用本分支修正后的打包器，对未修改的 `main` 固定提交 `db485ed098d433758358e8cc6280af5d4003afe1` 重新生成审计包：

| 项目 | 结果 |
| --- | --- |
| Git commit | `db485ed098d433758358e8cc6280af5d4003afe1` |
| manifest 跟踪文件 | 569 |
| ZIP 条目 | 570（含 manifest） |
| 文件大小 | 6,093,117 bytes |
| SHA-256 | `17b1b9c4e6b79947f3b116014ca10c4a094f52a2870107e5470a0364e9a2ae56` |
| manifest 逐文件大小/哈希 | 全部匹配 |
| 禁止条目 | 0 |
| 必要入口 | `README.md`、`install-portable.ps1`、`launch-portable.py`、`start-portable.ps1` 均存在 |

补充复核发现，上述 SHA-256 只对应当时保留的单次临时产物：旧实现给 manifest ZIP 条目写入当前时间，因此同一固定 commit 重打包会得到不同的 ZIP 哈希。后续修复把 manifest 时间戳固定，并增加双次打包逐字节一致回归；正式候选必须使用修复后的打包器重新生成，不能把上表旧哈希当作可由源码重现的候选哈希。

使用 Python 标准库独立解压同一 ZIP 后，在解压副本中复用已有本地 Python 与前端依赖，仅验证归档内容能否运行现有检查；未把本机依赖写入 ZIP：

- `scripts/verify_runtime.py --missing-voice`：通过；端口占用保护、隔离 SQLite、文本轮次、会话恢复、重复启动归属、诊断与端口释放均通过，语音按无模型模式报告 `assets_missing_or_invalid`。
- `scripts/validate_kb.py`：通过；记录分布为 LOOK 3、ROUTINE 3、REFERENCE_CASE 2、PRODUCT 14、ACCESSIBILITY_GUIDANCE 73、SOURCE 5。
- 前端测试：36 个文件、191 项测试全部通过；测试环境仍提示 jsdom 未实现 Canvas，不影响退出结果。
- 前端构建：通过；保留大于 500 kB 分块警告。

系统自带 `unzip` 首次解压时因中文文件名编码兼容问题失败；改用 Python `zipfile` 后 570 个条目全部解出，且先前的 CRC、manifest 大小与哈希核验均通过。因此这是本机旧解压工具兼容问题，不是 ZIP 损坏。

前端命令第一次误在应用根目录执行，因该目录没有 `package.json` 而退出；改在 `frontend/` 后测试与构建均通过。此项同样是检查命令路径错误，不是产品失败。

## 尚未完成

本次没有在全新 Windows 环境执行 `install-portable.ps1`，也没有真实演练卸载/回退；解压验证复用了本机已有依赖。因此 Issue #11 的“安装、启停和回退”验收项不能据此勾选。正式候选还必须在相关 PR 合并后，从新的固定 commit 重新生成并复验，且不能替代真实设备、真实服务和人工审核结论。
