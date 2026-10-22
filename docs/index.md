---
title: HiSpark 文档规范
short_title: 从这里开始
---

先读[基础规范：十项共同要求](part-1-foundations/04-core-principles.md)，再按下面的任务找具体要求。不必先读完整套规范，才能开始写一篇文档。

:::{admonition} 文档状态
:class: note

- 规范版本：v0.1.5
- 发布日期：2026-09-24
- 网站版本提示区分正式发布快照与开发快照；采用时同时记录版本、提交和 Profile
- 适用对象：采用本规范的 HiSpark SDK 类项目
- 产品、芯片、单板及能力由采用项目明确声明
:::

## 我现在要做什么

| 当前任务 | 最短阅读路径 |
|---|---|
| 第一次采用规范 | [十项基础要求](part-1-foundations/04-core-principles.md) → [试点与迁移](part-4-governance/13-migration.md) |
| 写一篇文档 | [页面创作规范](part-2-authoring/06-authoring.md) → 对应专项要求 |
| 审查一次修改 | [Review 要求](part-3-quality/10-review-and-merge.md) → [文档变更检查](part-4-governance/14-conformance-checklist.md) |
| 验证文档或 Sample | [验证与测试](part-3-quality/09-validation-and-testing.md) → [分层执行要求](#sample-execution-levels) |
| 维护项目或准备发布 | [项目与发布检查](part-4-governance/14-conformance-checklist.md) → [Daily CI](part-3-quality/11-daily-ci.md)、[维护契约](part-4-governance/12-governance-and-maintenance.md) |
| 查关键词或正式术语 | [规范性语言](part-1-foundations/02-normative-language.md)、[术语](part-1-foundations/03-terminology.md) |

## 哪些要求对我适用

所有内容页都要遵守基础要求，再根据实际内容查专项要求。写 Sample 就查 Sample 专项；说明硬件运行结果，就提供对应的实板证据；只解释概念的页面，则做技术评审及必要的静态核对。

作者提供页面所用的事实和证据，文档、领域、测试与发布负责人完成各自负责的评审和项目检查。项目检查不需要每位作者重复做，但仍需由相应负责人完成。

判断是否符合规范时，以条款中的大写 BCP 14 关键词及适用条件为准。摘编、角色入口和模板方便查阅，不代表只满足这些内容就符合完整规范。具体依据见[适用范围](part-1-foundations/01-scope-and-purpose.md)。

## 阅读与下载版本

- **基础阅读摘编**：只导出十项共同要求，适合首次阅读；详细规则按章号查完整规范。
- **完整版本**：保留所有详细条款、示例及解释层，用于查阅和正式评审。
- **Core 版本**：按既有可选范围构建，不包含解释性内容及其管理条款；它不是基础阅读摘编。

网站按任务组织导航，完整 PDF 保留稳定章号，方便已有引用继续使用。[前言](preface.md)介绍编写背景与阅读方式。
