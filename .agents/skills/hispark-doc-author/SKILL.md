---
name: hispark-doc-author
description: Design, write, or refactor Simplified Chinese documentation for HiSpark SDK-class projects under the HiSpark documentation standard. Use for tutorials, how-to guides, reference, explanation, get-started, Sample, API, or hardware pages; do not use for review-only requests.
---

# HiSpark 文档编写

产出一篇用户意图单一、产品边界明确、事实可追溯并能按声明级别验证的中文技术文档。

## 权威来源

先查找采用项目声明的 HiSpark 文档规范。本 Skill 随规范仓库使用时，规范位于 Skill 目录向上三级的 `docs/`。规范正文优先于本 Skill 的工作摘要；不得把 Skill 中的摘要解释成新的规范性条款。

根据任务读取相关章节：

- 分类、目录与页面结构：第 5、6 章；
- 上游与下游内容边界：第 7 章；
- `get-started/`、Sample、API 或硬件内容：第 8 章；
- 验证证据：第 9 章；
- Review 与完成定义：第 10 章。

需要具体模板、检查点或交付格式时，读取 [references/authoring-playbook.md](references/authoring-playbook.md)。

## 工作方式

1. 从用户任务、目标读者和完成判据确定页面的一个主要意图，并据此选择 `tutorial`、`how-to`、`reference` 或 `explanation`。历史目录名或“示例”“指南”等名称不能替代分类判断。
2. 检查页面的产品、版本、硬件对象、Target、配置和验证范围。缺少证据时标为未知、待验证或不适用，不得借同系列产品或上游支持推断当前产品能力。
3. 收集或保留必需元数据：`title`、`doc_type`、`product`、`applies_to`、`status`、`owner`、`verification_level`，以及适用时的 `last_verified`、`source_refs`、`upstream_refs`。适配项目的实际字段载体，不假定特定 Markdown 或构建工具。
4. 写下游内容前先检查上游。通用说明链接到版本匹配的权威上游文档；下游只写集成入口、产品差异、限制、配置、验证结果和恢复边界。
5. 按文档类型组织正文。命令说明执行环境和预期结果；危险动作在动作前说明风险与恢复方式；图片只承载文字难以等效表达的必要视觉信息。
6. 将事实、设计决策、推论和建议分开。只声明已经获得的验证等级，静态检查不得写成构建、Smoke 或 HIL 通过。
7. 运行项目已有的格式、构建、链接和领域检查。若无法运行，明确列出未验证项以及达到 `verified` 仍缺少的证据。

## 交付

交付修改后的源文件，并简要说明页面类型、适用范围、事实来源、实际完成的验证和剩余边界。除非用户明确要求，不发布、不合入，也不把草稿标记为 `verified`。
