# TRACE-Next：独立迁移候选

从 TRACE 固定提交 fd6154a3fb2eb97dd97b8fc4d5cb05d96ace8a07 分组迁入，保留已有领域逻辑，重构服务组装、应用工厂和命名扩展入口。它尚未接入支付宝，不是已上线的参赛作品。

## 启动

Mac 双击「首次安装_Mac.command」，完成后双击「启动Demo_Mac.command」。Windows 对应使用 .bat 入口。需要 Python 3.12.x、Node.js 26.10.0。默认页面 http://127.0.0.1:5280 ，API 8112、语音 8113，和旧版端口分开。保留启动窗口，Control+C 停止。

本次新环境已在 Mac 安装并验证。默认 mock，无私有 .env、用户数据库、下载模型或真实支付配置。缺语音/视觉模型时保留文字路径；按应用README安装固定模型后才能检查本地识别。没有把旧用户记录迁入新目录。

## 阅读顺序

- [必须保留的行为](SPEC.md)
- [新架构与新旧模块对应](docs/ARCHITECTURE.md)
- [检查及证据](docs/VERIFICATION.md)
- [应用运行说明](AccessibleBeautyAgent/README.md)
- [移植文件清单](migration/port-manifest.json)

迁移工作区父目录包含五阶段计划、只读审计、赛事调研与赛事特化计划书。旧版源码和用户数据保持原位，是否切换须结合设备/真实服务验收。此候选仅完成软件层通用迁移，实际支付、正式部署、课程专业审核和目标用户试用另行进行。
