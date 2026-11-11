# 欧莱雅 Accessible Beauty Demo｜组员导入指南

**当前状态：内部验证版。** 已有软件验证、Mac 净安装及部分键盘操作记录；双平台真实读屏、实体音视频、真实供应商、专业课程审核和目标用户验收仍待完成。2026-11-11 核对以共享源码 `747f994` 为基线，本次整理未重新实测应用。

- **[项目进度总览：现在能做什么、缺什么、下一步做什么](docs/STATUS.md)**
- [任务看板与状态筛选](docs/STATUS.md#任务看板) · [未完成 Issues](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues?q=is%3Aissue+is%3Aopen) · [交付里程碑](https://github.com/Nah1zuj/codex-loreal-continuous-update/milestones)
- [组员使用与进度更新方法](CONTRIBUTING.md) · [本次整理报告](docs/team-update-2026-11-11.md)
- [交付验证记录](specs/008-accessible-release/verification.md) · [设备验收清单](specs/008-accessible-release/device-acceptance.md)

未设置人员分工或 Assignee。每项任务都有依赖、执行清单和完成标准。

GitHub 仓库：<https://github.com/Nah1zuj/codex-loreal-continuous-update>

## 1. 下载项目

推荐用 Git 克隆，这样之后可以拉取更新：

```bash
git clone https://github.com/Nah1zuj/codex-loreal-continuous-update.git
```

也可以在 GitHub 页面点 **Code → Download ZIP**，下载后解压。用 Codex 时，选择 **Open folder / 打开文件夹**，打开克隆或解压后的 `codex-loreal-continuous-update` 文件夹。

## 2. 安装并启动

安装 Python 3.12.x 和 Node.js 26.10.0。Windows 使用 x64 Python 并包含 Python Launcher。安装依赖和下载模型需要联网。

- **Mac**：双击 `首次安装_Mac.command`，完成后双击 `启动Demo_Mac.command`。
- **Windows**：双击 `首次安装_Windows.bat`，完成后双击 `启动Demo_Windows.bat`。安装 Python 时请包含 Python Launcher；推荐 Python 3.12。

首次安装会下载依赖并构建前端。语音模型按下方命令单独下载并校验固定版本，缺少模型时可先使用文字功能。启动后按终端提示打开 <http://127.0.0.1:5180/>；停止时在启动终端按 `Control+C`。

如果已安装依赖但想单独补齐语音模型，在 `AccessibleBeautyAgent` 目录运行：

```bash
.venv-portable/bin/python voice/setup_local_voice_models.py --download
```

Windows PowerShell 对应命令：

```powershell
.\.venv-portable\Scripts\python.exe voice\setup_local_voice_models.py --download
```

## 3. 配置自己的模型密钥（可选）

项目默认使用 mock 配置，可以先启动体验。要接入真实模型时，在 `AccessibleBeautyAgent` 目录复制配置模板：

```bash
cp .env.example .env
```

然后只在本机编辑 `.env`，填入自己有权使用的服务商 API Key 和模型配置，再重启 Demo。**不要把 `.env` 发到群里或提交到 GitHub**；仓库已忽略该文件。每位组员应使用自己的密钥。

## 4. 获取更新和提交修改

先阅读 [进度总览](docs/STATUS.md) 和本次关联的 Issue，再从最新 `main` 创建任务分支。下面以 Issue #1 为例，分支名按实际任务修改：

```bash
git switch main
git pull --ff-only
git switch -c task/issue-1-demo-verification
# 完成本次范围内的修改和验证
git add <本次修改的文件>
git commit -m "说明本次修改"
git push -u origin HEAD
```

在 GitHub 从该分支向 `main` 开 Pull Request，关联 Issue，说明实际验证、未验事项和影响。验收通过后再合并；部分完成不要自动关闭整项任务。已有本地修改时先保存并检查工作区，再切换分支，不覆盖他人的改动。完整方法见 [CONTRIBUTING.md](CONTRIBUTING.md)。

仓库保持 Private，仅获准协作者可访问。若没有访问权限或无法克隆，联系仓库所有者核对账号和邀请状态；本文不预设邀请是否已经接受。

## 仓库中没有的本机文件

- `AccessibleBeautyAgent/.env`：每个人自行从 `.env.example` 复制并填写，不共享密钥。
- `AccessibleBeautyAgent/voice/models/asr/model.int8.onnx`：约 228 MB，GitHub 普通文件上限为 100 MB，因此不放进仓库。上方模型下载命令会从官方来源下载并校验文件，写入原目录；如果已有本地模型文件，保留在该目录即可，Git 更新不会提交它。

其余运行说明、项目资料和验证记录见本目录的 `00_先读我_运行说明.txt` 及 `AccessibleBeautyAgent/README.md`。
