---
title: '14. 按任务选择检查表'
short_title: 变更与项目检查
---

先选择检查对象：本次页面修改使用第 14.1 节；项目接入、日常治理或发布复核使用第 14.2 节。清单是条款索引，不重复定义规则，不免除已适用的要求。

## 14.1 本次文档变更

作者先提供证据，由对应 Reviewer 作判断；只读当前修改触发的专项内容。依据列指向完整判定规则。

| 检查问题 | 最小可审查材料 | 依据 |
|---|---|---|
| 页面只服务一个主要意图，类型与入口一致吗？ | 标题、正文、`doc_type` 和导航位置 | [第 4 章](../part-1-foundations/04-core-principles.md)、[第 5 章](../part-2-authoring/05-information-architecture.md) |
| 产品、版本、Owner、状态和来源清楚吗？ | 元数据及可定位的源码、配置或正式资料 | [第 6.1—6.2 节](../part-2-authoring/06-authoring.md) |
| 下游只写集成上下文和产品差异吗？ | 版本匹配的上游链接；副本例外记录（如有） | [第 7 章](../part-2-authoring/07-upstream-downstream.md) |
| 用户能执行、观察结果并在失败后恢复吗？ | 命令环境、判据和动作之前的风险说明 | [第 6.3、6.5 节](../part-2-authoring/06-authoring.md) |
| 验证证据足以支持页面声明吗？ | 实际日志、环境、产物、日期和未验证边界 | [第 9.1 节](../part-3-quality/09-validation-and-testing.md) |
| 链接、术语、图片和渲染可用吗？ | 对应检查结果及渲染；图片等价文字、图源和版本 | [第 6.4—6.6 节](../part-2-authoring/06-authoring.md) |
| 适用门禁与独立评审已完成吗？ | 当前提交的 CI、批准及阻塞意见处置记录 | [第 10 章](../part-3-quality/10-review-and-merge.md) |

以下检查只在对应内容受到影响时追加：

- [ ] 快速入门：唯一首次成功目标/判据，入口决策与联动维度一致，逐叶预算及数值用时，必要准备可直接进入，优化不作前置；见[第 8.1 节](../part-2-authoring/08-specialized-content.md)。
- [ ] 多变体验证：八阶段状态、精确环境、命令/退出码/日志/产物摘要及未验证边界；事实源到渲染、Runner 和证据链一致，见[第 9.4—9.5 节](../part-3-quality/09-validation-and-testing.md)。
- [ ] 导航或 URL 变化：导航角色不继承教程验证；删除、移动、重命名同步检查文件、导航、引用和旧入口处置，见[第 6.1、6.4 节](../part-2-authoring/06-authoring.md)。
- [ ] Sample：源码、实践指南、Owner 和测试有效映射；配置变化同步更新页面及覆盖记录，见[第 8.2 节](../part-2-authoring/08-specialized-content.md)、[第 9.2 节](#sample-test-coverage)、[第 12.3 节](#sample-maintenance-contract)。
- [ ] API 或硬件：与发布头文件或正式硬件资料逐项核对，见[第 8.3—8.4 节](../part-2-authoring/08-specialized-content.md)。
- [ ] 解释性内容：核对实际问题、成因、作用机制与预期效果，并执行删除测试，见[第 2.2 节](../part-1-foundations/02-normative-language.md)。
- [ ] 生成内容、高风险操作、URL 移动或发布版本变化：追加[第 10.2 节](#review-requirements)所需角色，审查生成源/渲染、风险、重定向或版本兼容。

## 14.2 项目、周期与发布复核

由项目负责人组织相应 Owner 提供材料。每项结果记录为满足、有缺口或经说明不适用；缺口记录原因、风险、Owner、下一步和复核日期。完整例外要求见[第 12.2 节](../part-4-governance/12-governance-and-maintenance.md)。

| 复核对象 | 负责人 | 需要查的材料 | 依据 |
|---|---|---|---|
| 目录、页面状态与生命周期 | 文档 Maintainer、领域 Owner | 页面清单、一级目录 Owner、过期与废弃处理、替代入口 | [第 5.2 节](../part-2-authoring/05-information-architecture.md)、[第 6.2 节](../part-2-authoring/06-authoring.md)、[第 12.1—12.2 节](../part-4-governance/12-governance-and-maintenance.md) |
| Review 机制 | 文档 Maintainer、相关领域 Owner | 自动请求、角色覆盖、独立性、批准 SHA、升级路径和例外到期 | [第 10.2 节](#review-requirements) |
| PR 自动门禁 | 测试/CI Owner | 锁定依赖、检查入口、docs-only 触发、图源/导出映射与敏感信息检查 | [第 10.3 节](../part-3-quality/10-review-and-merge.md) |
| 每日持续检查 | 测试/CI Owner、故障 Owner | 时区、计划、最近成功时间、全量报告、告警和回归跟踪 | [第 11 章](../part-3-quality/11-daily-ci.md) |
| 上游及资产维护 | 文档 Maintainer、领域 Owner | 版本/锚点漂移、疑似重复报告、临时副本、共享图片及引用关系 | [第 7 章](../part-2-authoring/07-upstream-downstream.md)、[第 6.6 节](../part-2-authoring/06-authoring.md) |
| Sample 覆盖与联动 | Sample Owner、测试/CI Owner | 双向映射；Build、Smoke、HIL、负向和版本覆盖；分子/分母；阻塞项 | [第 9.2—9.3 节](#sample-test-coverage)、[第 12.3 节](#sample-maintenance-contract) |
| 发布候选与正式发布 | 发布 Owner、受影响领域 Owner | 推荐路径、最低覆盖、Known Issues、证据归档、URL 和版本一致性 | [第 9.3 节](#sample-execution-levels)、[第 12.2 节](../part-4-governance/12-governance-and-maintenance.md) |
| 规范采用与同步 | 文档 Maintainer | 规范仓库/提交、profile、采用日、Owner、例外、Skill 身份和同步复核 | [第 12.4 节](12-governance-and-maintenance.md) |
| 总体门禁与完整报告 | 测试/CI Owner | 发现分类与计数、完整报告、归档回执、必需检查集合、失败传播 | [第 10.5—10.6 节](../part-3-quality/10-review-and-merge.md)、[第 11.1 节](../part-3-quality/11-daily-ci.md) |
| 构建与部署身份 | 发布 Owner | 依赖闭包、获取源/检出源等价、同一提交及已验证产物摘要 | [第 7.3 节](../part-2-authoring/07-upstream-downstream.md)、[第 10.7 节](../part-3-quality/10-review-and-merge.md) |

项目治理有缺口时，记录其影响和处置；不要把一次页面检查通过写成整个项目已经符合规范。影响推荐路径或发布的阻塞按相应条款处理。

## 14.3 如何报告结论

建议采用下面的短格式，并链接已有证据，避免重新抄写完整报告：

- **对象与范围**：页面/提交，或项目/发布版本。
- **已满足**：适用条款及对应证据位置。
- **未满足或未验证**：原因、影响、Owner、下一步、复核日期。
- **不适用项**：明确场景理由。
- **Review 与结论**：实际批准记录，以及当前可支持的页面状态或发布结论。
