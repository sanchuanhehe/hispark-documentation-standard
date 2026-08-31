---
title: '11. 每日文档持续集成（Daily CI）'
---

每个采用本规范的项目 MUST 配置每日文档 CI，并 SHOULD 支持手动触发。Daily CI MUST 与 PR 门禁使用相同的锁定依赖和检查实现，MUST NOT 成为一套无法在 PR 或本地复现的独立脚本。

Daily CI 至少 MUST 执行：

1. 全量严格站点构建、导航、内链、锚点、图片和大小写检查；
2. 全量上游 URL、目标锚点、固定版本可用性及版本漂移检查；
3. 下游与上游疑似重复内容扫描，并输出待人工确认清单；
4. `get-started/` 预算、唯一 Happy Path、必要术语和隐含前置条件检查；
5. API、配置、Target、Sample 源码和文档映射漂移检查；
6. Sample 清单、构建矩阵以及应在当日执行的 Smoke/HIL 场景；
7. `last_verified`、临时上游副本、例外、阻塞项和 Owner 的过期检查；
8. 结果、失败原因、适用提交、依赖版本和证据产物归档。

Daily CI 的时区、计划表达式、最长允许未成功运行时间、告警接收方和故障 Owner MUST 明确记录。默认最长允许未成功运行时间为 24 小时；因平台故障未执行或证据未上传 MUST 标记为失败或阻塞，MUST NOT 沿用上一次绿色结果。

Daily CI MUST NOT 替代 PR 门禁。Daily 发现回归时 MUST 自动创建或关联可跟踪项，至少包含失败范围、首次发现时间、最近成功提交、Owner 和证据链接；影响默认 Happy Path、公开 API 或推荐 Sample 时 MUST 阻止相关发布。
