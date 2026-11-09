# TRACE：独立视障美妆陪伴项目

TRACE 面向盲人和低视力用户，提供语音优先的美妆交流、分步引导、标签阅读、产品类型比较与个人记忆。项目独立于任何化妆品公司、支付平台或比赛，不限定品牌；默认用单品名称和品类描述建议，并优先从用户已经拥有、熟悉的物品开始。

## 启动

Mac 双击「首次安装_Mac.command」，完成后双击「启动Demo_Mac.command」。Windows 对应使用 .bat 入口。需要 Python 3.12.x、Node.js 26.10.0。默认页面 http://127.0.0.1:5280 ，API 8112、语音 8113，和旧版端口分开。保留启动窗口，Control+C 停止。

本次环境已在 Mac 安装并验证。默认 mock，无私有 `.env`、用户数据库或下载模型。缺语音/视觉模型时保留文字路径；按应用 README 安装固定模型后才能检查本地识别。没有把旧用户记录迁入新目录。

## 阅读顺序

- [必须保留的行为](SPEC.md)
- [新架构与新旧模块对应](docs/ARCHITECTURE.md)
- [独立产品方向](docs/PRODUCT_DIRECTION.md)
- [检查及证据](docs/VERIFICATION.md)
- [应用运行说明](AccessibleBeautyAgent/README.md)
- [移植文件清单](migration/port-manifest.json)

迁移工作区父目录保留五阶段迁移审计材料；赛事讨论稿不属于当前产品路线。旧版源码和用户数据保持原位。正式部署、课程专业审核和目标用户试用仍需独立完成。
