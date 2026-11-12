# TRACE 交付复核手册

[本地运行说明](../../AccessibleBeautyAgent/README.md) 是安装、启动和模型配置的入口。[阶段追踪](traceability.md) 汇总当前验证状态。本轮本地包供内部验证使用，包内清单注明提交及分类。

## 本地演示

1. 使用独立工作目录启动，确认健康页面显示 mock 和本机语音模型实际状态。无模型也可以完成文字任务。
2. 在文字页输入一个场合和偏好，查看是否需要澄清，或点击进入映照。明确开始后，重复说明、跳过一步、暂停再恢复、提前结束。
3. 刷新，核对当前进度及相机和麦克风关闭。选择拒绝授权，再用文字继续。若使用合成设备，只将结果列为软件验证。
4. 打开拾光，分别检查本次小结与历史记录。确认或拒绝前先查看实际内容。测试数据写入独立目录。
5. 检查六领域和标签入口，按界面标示区分真实服务、模拟、待确认来源和未知项。

## 复查人员与记录

[双平台实机验收](../../specs/008-accessible-release/device-acceptance.md) 提供复测步骤、已观察结果和现场记录表。

| 环境 | 操作 | 应记录的证据 |
|---|---|---|
| Mac Chrome＋VoiceOver | 从初始页用 Tab 与跳转链接进入内容，切换语言，完成文字教学并拒绝媒体权限，再在自愿的情况下测试相机和语音 | 版本、焦点顺序、实际播报、状态和失败提示、使用的设备 |
| Windows Chrome＋NVDA | 同样完成核心路径，并检查安装入口、字体放大、200% 缩放、语音故障后继续用文字 | 版本、NVDA 语音查看器摘录、截图或测试说明 |
| 软件故障验证 | 无模型、目录移动、断网重连、后端中断、重启、长会话及停止媒体 | 环境与 Git 版本、运行证据、清理后的媒体及连接状态 |
| 专业与试用 | 由具备资质的人员审阅实际课程，让目标用户独立完成场景 | 审核人、课程版本、试用条件和真实反馈 |

## 真实文字与标签联调

由项目负责人准备一份仅用于联调的私有配置，按 [本地运行说明](../../AccessibleBeautyAgent/README.md) 填入已批准的供应商、模型、凭据和 `ALLOW_REMOTE_AI=true`。凭据保存在本机配置中。为标签准备清晰与模糊各一张虚构 JPEG 或 PNG，只保留测试文字。每张图在运行前核对内容和目标主机。

在应用目录启动独立的回环后端。替换 `trace_config` 为私有配置路径，按实际情况选用空闲端口。日常项目配置和数据库无需参与。

```bash
mkdir -p work
trace_check_dir="$(mktemp -d "$PWD/work/remote-check.XXXXXX")"
TRACE_ENV_FILE="$trace_config" MEMORY_PATH="$trace_check_dir/check.sqlite" \
VISION_PROVIDER=mock REFERENCE_PROVIDER=mock EMBEDDING_PROVIDER=mock RERANKER_PROVIDER=mock \
DEVELOPER_MODE=true ADMIN_ENABLED=false \
.venv-portable/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 64527
```

在另一窗口从应用目录先运行不带 `--execute` 的命令。按私有配置选择 `--provider`。标签服务另需指定界面显示的实际目标主机。

```bash
.venv-portable/bin/python scripts/verify_remote_services.py --port 64527 text --provider "$trace_text_provider"
.venv-portable/bin/python scripts/verify_remote_services.py --port 64527 label --provider "$trace_label_provider" --destination-host "$trace_label_host"
```

确认目的地后，文字命令加 `--execute`，会向所选文字服务发送一条固定虚构语句。标签命令每次加 `--execute --image "$trace_label_file" --expect-sha256 "$trace_label_sha256"`，再按样本加 `--expect-text "$trace_label_expected"` 或 `--expect-uncertain`。哈希必须是本次明确确认图片的 64 位小写 SHA-256；文件内容变化时命令会在本地拒绝，且不会发送 POST。一次只发送一张经确认的 PNG 或 JPEG。文字检查须收到完成事件和实际供应商响应证据，且固定验证语句不得产生课程进度提交事件。清晰标签须返回已知原文，模糊标签须保留不确定性且不推断色号、成分或用法。必要时现场复核原文及难辨片段，记录版本、供应商、日期和结果。配置就绪和替身测试分别记录。联调结束后用 Control+C 停止后端。

## 打包和回退

用应用 Python 执行 `scripts/pack_source.py work/trace-internal.zip --commit HEAD`。归档从固定 Git 提交读取，排除运行目录、旧启动器、密钥、数据库及非公开运行资产。界面公开素材保留。测试语音样本留在开发检出中。解压后按运行说明安装，缺少模型可先验证文字路径。打包工具应从有 Git 元数据的开发目录运行。

升级前停机并制作个人库一致性备份。回退时从原提交另行检出，使用对应的库备份，并保留升级后数据的单独副本。阶段 2 的计划载荷及后续确认式记忆结构见对应规格。Git 包不用于备份个人记录。

[日志升级与回退实演](../../specs/007-confirmed-memory/verification.md#日志升级与回退实演) 记录实际旧版和当前安全修订包之间的隔离验证，包含浏览器身份、旧日志和两份独立数据库备份。
