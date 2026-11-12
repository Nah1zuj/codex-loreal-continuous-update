# Windows x64 净安装与启停验收包

关联任务：[#2 完成 Windows 净安装、启停与恢复验收](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/2)

本页用于在真实 Windows x64 设备上执行阶段 1 验收。macOS 运行、PowerShell 静态解析、交叉下载 Windows 轮包、历史 Windows 文档和自动化模拟均不能替代本页的实机结果。

## 准备

1. 使用从固定 Git commit 生成的源码包，先在下载位置核对 ZIP SHA-256，再解压到同时包含中文和空格的新目录，例如 `C:\TRACE 验收\本轮 中文路径`。不要复用已有 `.venv-portable`、`work` 或模型目录。
2. 安装 Windows x64 Python 3.12.x（含 Python Launcher）、项目锁定的 Node.js、Chrome 和 PowerShell。记录实际版本，不只写“最新版”。
3. 源码包根目录须保留 `TRACE-BUNDLE-MANIFEST.json`。包内 manifest commit、命令参数中的 commit 和本轮验收 commit 必须相同。
4. 不复制 `.env`、密钥、个人 SQLite、照片或录音。自动预检强制使用隔离目录、mock 服务和回环端口，不调用远程供应商。

## 自动预检

在 `AccessibleBeautyAgent` 目录打开 Windows PowerShell，执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_windows_acceptance.ps1 `
  -ExpectedCommit <40位Git提交> `
  -PackageSha256 <64位ZIP-SHA256> `
  -PackagePath <下载的源码ZIP完整路径> `
  -DownloadModels
```

脚本只允许在 Windows x64 运行，并要求当前路径同时含非 ASCII 字符和空格。它将：

- 实际计算所给 ZIP 的 SHA-256，核对包 manifest commit，并逐文件复核解压内容的大小和哈希；
- 记录 Python、Node、PowerShell 和 Chrome 版本；
- 确认干净包最初没有有效语音模型；
- 调用当前 `install-portable.ps1 --force` 完成实际依赖安装；
- 在无模型状态执行 `verify_runtime.py --missing-voice`；
- 使用 `-DownloadModels` 时下载并校验固定语音模型，再执行有模型运行检查；
- 把端口占用保护、重复启动不夺权、诊断、隔离 SQLite、文字流程和本次端口释放结果写入 `work/windows-acceptance/<UTC时间>/windows-acceptance.json`。

若不加 `-DownloadModels`，模型安装与有模型运行保持 `NOT_RUN`，总结果必为 `BLOCKED`。任何命令失败均写为 `FAIL`，不得删掉失败记录后只保留重跑成功结果。

## 必须人工完成的实机步骤

自动预检不会模拟双击或目录移动。完成下列步骤后，在生成的 JSON 中把对应项从 `NOT_RUN` 改成实际 `PASS` 或 `FAIL`，并写清不含个人信息的观察：

1. 在同一干净副本双击外层 `首次安装_Windows.bat`，确认窗口返回成功；记录入口名称和实际结果。
2. 双击外层 `启动Demo_Windows.bat`，确认浏览器、UI、`/api/health` 和 `/local-voice/health` 可达；保留启动窗口。
3. 关闭启动窗口，确认本次启动的三个端口均释放；另一个预先占用的测试端口仍由原进程持有。
4. 将整个解压目录移动到另一个同样含中文和空格的位置，重新运行首次安装和启动入口；确认旧虚拟环境不会被误用，文字流程可恢复。
5. 运行 Windows 专用测试：

   ```powershell
   .\.venv-portable\Scripts\python.exe -m pytest -q tests\regression\test_windows_setup.py
   ```

6. 运行记录校验：

   ```powershell
   .\.venv-portable\Scripts\python.exe scripts\windows_acceptance.py validate `
     work\windows-acceptance\<UTC时间>\windows-acceptance.json
   ```

校验结果含义：

- `PASS`：真实 Windows x64 记录中所有自动和人工项目均为 `PASS`，且声明结论一致。
- `FAIL`：至少一个项目实际失败；应建立具体缺陷并保留本项开放。
- `BLOCKED`：存在 `NOT_RUN`，或只是合成模板；不能作为 Windows 实机通过证据。
- `INVALID`：字段、版本、哈希、证据分类或声明结论矛盾。

## 记录边界

记录不得包含设备所有者姓名、Windows 用户名、主机名、邮箱、电话、完整个人目录、密钥或上游响应。路径只记录是否含中文／空格，不记录完整路径。自动检查通过不代替 Chrome、NVDA、麦克风、扬声器、耳机或相机的人工体验；其中读屏与实体媒体分别回填 Issue #3、#4、#5。
