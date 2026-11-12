# Issues #6／#7 远程服务安全预检（2026-11-12）

关联任务：[#6 真实文字供应商联调](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/6) · [#7 真实标签识别联调](https://github.com/Nah1zuj/codex-loreal-continuous-update/issues/7)

## 结论

当前本机私有配置没有解除真实服务阻塞。项目目录存在未提交的私有 `.env`，但远程开关为关闭，文字供应商和标签读取供应商均为 `mock`，三个支持的密钥字段均为空。预检没有发送文字或图片，也没有调用任何外部主机。

本页只记录配置类型、布尔状态和软件检查；不记录或提交秘密值。

## 源码与隔离环境

- 实际执行源码：`fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07`。
- GitHub 最新 main：`db485ed098d433758358e8cc6280af5d4003afe1`。两者的远程验证脚本、配置和服务源码一致；应用目录差异仅为 main 新增的已跟踪语音模型／测试音频资产。
- 独立后端：`127.0.0.1:64527`，独立 SQLite 位于 Git 忽略的临时目录。
- `VISION_PROVIDER`、`REFERENCE_PROVIDER`、`EMBEDDING_PROVIDER`、`RERANKER_PROVIDER` 均强制为 mock；管理入口关闭。
- 结束后后端正常停止，64527 端口释放，Git 工作区保持干净。

## 私有配置状态（不含秘密）

| 项目 | 实际状态 |
|---|---|
| 私有 `.env` | 存在，仅在本机；未提交 |
| `ALLOW_REMOTE_AI` | `false` |
| 文字供应商 | `mock` |
| 标签读取供应商 | `mock` |
| `COMPATIBLE_API_KEY` | 未设置 |
| `DEEPSEEK_API_KEY` | 未设置 |
| `DASHSCOPE_API_KEY` | 未设置 |
| 标签目的地主机 | 未设置 |

## 不外发预检

启动隔离后端后，健康接口返回：

- `provider_mode=mock`
- `remote_text_configured=false`
- 标签服务 `provider=mock`、`status=demo`、目的地主机为空、真实验证状态为 `unverified`

随后运行文字预检但不添加 `--execute`。脚本以退出码 1 返回：预期真实文字供应商未配置和启用。后端访问记录只有三次本机 GET（健康、标签可用性、健康），没有 POST；因此没有发送固定虚构语句、图片或任何个人数据。

远程验证器与健康状态专项测试为 **6 passed**，覆盖未加 `--execute` 时只检查配置、不发送请求，以及远程配置状态的真假边界。

## Issue #7 合成标签准备

已在本机 Git 忽略的 `work/issue7-labels/` 生成并人工查看两张 1200×760 RGB PNG，均无真人、个人信息、品牌包装或真实商品数据，且小于 2 MB：

| 文件 | 用途与预期 | SHA-256 |
|---|---|---|
| `clear.png` | 虚构英文标签；真实联调时预期至少包含 `TRACE TEST LABEL` | `8bb54f50521e8b7f6b5d4662e289f5778ec2fde1d222913b12a1f6a619095332` |
| `blurred.png` | 同一标签强模糊版本；预期 `UNCERTAIN`，且 shade／composition／instructions 保持未知 | `423300e620ab7242ffbedc0b0c118fb2278bad9cdc403183601780c6ac08b19f` |

图片没有上传到 GitHub，也没有发送给供应商。真实联调前仍须明确确认供应商、目的地主机、单张图片和用途。

## 仍然受阻

1. 尚无已批准且有效的真实文字供应商配置，不能运行 #6 的 `--execute`。
2. 尚无已批准的标签供应商、有效凭据和目的地主机，不能运行 #7 的 `--execute`。
3. 清晰／模糊标签的真实响应、原文人工对照、失败／取消和零调用边界尚无外部服务证据。

因此 #6、#7 继续保持“受阻”。阻塞解除后，从固定 commit 的独立环境重新预检；只在逐项确认后执行一次固定虚构文字或一张合成标签。
