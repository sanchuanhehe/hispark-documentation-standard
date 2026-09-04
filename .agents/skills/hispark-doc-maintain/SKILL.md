---
name: hispark-doc-maintain
description: Govern HiSpark SDK documentation lifecycles, ownership, upstream/downstream boundaries, Sample contracts, migrations, and recurring quality controls. Use for documentation inventory, stale-content cleanup, release review, governance design, or migration planning; use the verification skill when the task is only to run existing checks.
---

# HiSpark 文档维护

让文档、代码、配置、上游依赖、测试证据和 Owner 作为一个有生命周期的系统持续演进。

## 权威来源

先查找采用项目声明的 HiSpark 文档规范。本 Skill 随规范仓库使用时，规范位于 Skill 目录向上三级的 `docs/`。重点读取第 4.6、5.2、6.2、7、8、11、12、13 和 14 章；规范正文优先于本 Skill 摘要。

进行仓库级审计、迁移或发布复核时，读取 [references/maintenance-model.md](references/maintenance-model.md)。

## 工作方式

1. 建立可审计基线：页面、导航入口、`doc_type`、产品/版本、Owner、状态、验证日期、源码/配置引用、上游引用、Sample 和测试入口。空页、占位页、失效路径和跨产品污染单独标记。
2. 检查一级目录职责和页面主要意图。不要从批量移动文件开始；先分类、补边界和建立映射。
3. 识别下游重复维护的上游通用内容。优先换成版本匹配、上下文明确的上游链接，仅保留下游集成入口、产品差异、限制与验证结果。无法链接而保留临时副本时，记录来源、版本、Owner、理由和复核日期。
4. 建立“源码或配置变化 → 受影响文档与测试”的依赖映射。Sample 使用稳定 `sample_id` 连接源码、实践指南、Owner、产品/Target、状态和测试证据。
5. 校验生命周期：失去 Owner、超过验证期限、上游漂移、源码/API/Kconfig/Target 变化或测试持续失败时，页面/示例降级为待复核；不要只改日期或状态文字来延长 `verified`。
6. 规划 URL 兼容的渐进迁移。页面移动或删除前给出重定向、替代入口、受影响链接和回滚边界。
7. 检查 PR 门禁、Daily CI 和发布复核是否使用同一套可复现检查，并把失败、阻塞、未运行和过期例外转为有 Owner 的跟踪项。

## 交付

先报告现状和证据缺口，再给出按风险、依赖和收益排序的迁移或维护计划。每项包含对象、问题、依据、Owner、验收证据、截止/复核条件和 URL 兼容策略。

普通审计请求只做只读检查。除非用户明确要求实施，不移动、删除、归档页面，不更新状态，也不创建外部跟踪项。
