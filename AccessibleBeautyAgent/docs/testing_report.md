# V2 功能验收报告

2026-10-12。后端以 Mock / ALLOW_REMOTE_AI=false 完整回归，前端使用可控接口与媒体 fixture；这些结果不是模型准确率。

| 检查 | 结果 |
| --- | --- |
| 后端完整测试 | PASS：130 项（包括多工具 usage 累计回归） |
| 前端 npm test | PASS：功能 G 18 文件 / 122 项；最终补修与 Story 19 文件 / 127 项 |
| npm run build | PASS：功能 G 91 modules；最终 Story 94 modules；首次 role 推导 TypeScript 错误已修复后重跑通过 |
| scripts/validate_kb.py | PASS：3/3/2/12/49/2；来源 local_file 缺失警告已修复 |
| 新导入 / 隐私 / 新帧 / 多轮定向 | PASS：14 项；usage 累计额外 RED→GREEN 后进入完整回归 |
| 真实 DeepSeek SSE | PASS：两轮虚构文字，239/431 字；客户端首次 delta 2978/4271ms，总 4195/6046ms；第二轮实际 search_knowledge/get_memory 成功，routine_started 保持 false |
| 真实浏览器日志 | PASS：确认后保存、另行原文勾选、日历标签、刷新及原文读取；虚构记录已清理 |
| 真人妆效准确率 / 模型训练 | NOT_TESTED / 未实施 |
| 真麦克风、可听 TTS、实体相机、读屏 | NOT_TESTED |
| 其他兼容 API、生产账户/多设备同步 | NOT_TESTED / 未实现 |

真实 token usage 由供应商返回；诊断现累计全部工具轮而非只取最终轮，固定 transport 回归覆盖。上面的真实接口测量发生在累计修复前，不拿最后一轮 usage 当整个对话费用；没有配置价格，cost_estimate=null。

最终8002实测再次通过：首 delta 5345/8115ms，总8390/11039ms；第二轮实际两轮供应商usage合计5078tokens（1879+3199）。延迟波动真实记录，不承诺固定速度。最终浏览器、性能与截图详见 STORY_GENERATIVE_REPORT.md。

曾发生 B 阶段完整前端 5 项旧 fixture 回归失败仍提交，已如实登记并在 C 修复；不隐去失败历史。合成视觉统计始终 UNCERTAIN。旧浏览器权限/媒体 fixture 的 PASS 只代表模拟生命周期。
