# 欧莱雅 Accessible Beauty Demo｜组员导入指南

GitHub 仓库：<https://github.com/Nah1zuj/codex-loreal-continuous-update>

## 1. 下载项目

推荐用 Git 克隆，这样之后可以拉取更新：

```bash
git clone https://github.com/Nah1zuj/codex-loreal-continuous-update.git
```

也可以在 GitHub 页面点 **Code → Download ZIP**，下载后解压。用 Codex 时，选择 **Open folder / 打开文件夹**，打开克隆或解压后的 `codex-loreal-continuous-update` 文件夹。

## 2. 安装并启动

需要联网安装依赖和语音模型，并安装 Node.js 22.12+、Python 3.12（Mac 也支持 3.13）。

- **Mac**：双击 `首次安装_Mac.command`，完成后双击 `启动Demo_Mac.command`。
- **Windows**：双击 `首次安装_Windows.bat`，完成后双击 `启动Demo_Windows.bat`。安装 Python 时请包含 Python Launcher；推荐 Python 3.12。

首次安装会下载依赖、构建前端，并从官方来源下载本地语音模型，可能需要一些时间。启动后按终端提示打开 <http://127.0.0.1:5180/>；停止时在启动终端按 `Control+C`。

如果已安装依赖但想单独补齐语音模型，在 `AccessibleBeautyAgent` 目录运行：

```bash
.venv-portable/bin/python voice/setup_local_voice_models.py
```

Windows PowerShell 对应命令：

```powershell
.\.venv-portable\Scripts\python.exe voice\setup_local_voice_models.py
```

## 3. 配置自己的模型密钥（可选）

项目默认使用 mock 配置，可以先启动体验。要接入真实模型时，在 `AccessibleBeautyAgent` 目录复制配置模板：

```bash
cp .env.example .env
```

然后只在本机编辑 `.env`，填入自己有权使用的服务商 API Key 和模型配置，再重启 Demo。**不要把 `.env` 发到群里或提交到 GitHub**；仓库已忽略该文件。每位组员应使用自己的密钥。

## 4. 获取更新和提交修改

有仓库写入权限的组员可以拉取最新版本、提交并推送：

```bash
git pull
git add <修改的文件>
git commit -m "说明本次修改"
git push
```

仓库目前是 Private，只有仓库所有者和获准的协作者能查看、下载和修改。已邀请 `guiyuxuan23` 与 `liuy47543-art` 并授予写入权限；他们需要先接受 GitHub 邀请，之后才能克隆仓库和推送修改。其他组员需要先联系仓库所有者添加账号。

## 仓库中没有的本机文件

- `AccessibleBeautyAgent/.env`：每个人自行从 `.env.example` 复制并填写，不共享密钥。
- `AccessibleBeautyAgent/voice/models/asr/model.int8.onnx`：约 228 MB，GitHub 普通文件上限为 100 MB，因此不放进仓库。安装脚本会下载官方模型到原目录；如果已有本地模型文件，保留在该目录即可，Git 更新不会提交它。

其余运行说明、项目资料和验证记录见本目录的 `00_先读我_运行说明.txt` 及 `AccessibleBeautyAgent/README.md`。
