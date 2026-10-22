---
title: '12. 治理与持续维护'
---

## 12.1 角色与职责

| 角色 | 主要职责 |
|---|---|
| 文档作者 | 明确用户问题、分类、来源、版本和验证边界 |
| 领域 Owner | 审核技术事实、限制、风险和产品边界 |
| 文档 Maintainer | 审核信息架构、术语、风格、链接和生命周期 |
| 测试/CI Owner | 提供构建、smoke、HIL 和文档门禁 |
| 发布 Owner | 保证文档版本、SDK 发布物、URL 和变更说明一致 |

每个一级目录必须（MUST）有明确 Owner。高频变更的 Sample、API 和工具文档应当（SHOULD）通过 CODEOWNERS 或等价机制自动请求评审。

## 12.2 持续维护要求

1. 文档 Owner 必须（MUST）维护页面准确性和生命周期；领域 Owner 必须（MUST）维护技术事实，二者应当（SHOULD）共同评审相关内容。
2. 项目必须（MUST）建立对应关系或等价检查，使源码路径或配置变化后能找到受影响的文档和测试。
3. 每次 SDK 发布必须（MUST）生成文档与 Sample 复核报告，至少列出已验证、失败、阻塞、废弃和未运行项。
4. 项目必须（MUST）定期检查页面是否超过验证有效期、Owner 是否仍有效、外链是否失效、来源是否变化，并安排相应人员修复。
5. 维护工作必须（MUST）以补齐缺失的验证证据为目标；如果只更新日期、状态文字或覆盖率数字，却没有重新验证，不得（MUST NOT）延长 `verified` 状态。
6. 例外和阻塞项必须（MUST）记录 Owner、原因、风险、下一步和复核日期；不得（MUST NOT）只展示汇总覆盖率，把长期没有解决期限的阻塞项藏起来。

对本规范的长期例外必须（MUST）记录：

- 偏离的条款；
- 业务或技术理由；
- 已评估的影响；
- 补偿措施；
- Owner；
- 到期或复核日期。

如果例外会改变门禁对问题的处理，必须（MUST）记录唯一标识、明确到期日期、批准人、批准时间、适用发现/条款，以及提交或版本范围；必须（MUST）完成[第 10.2 节](../part-3-quality/10-review-and-merge.md)适用的独立评审。只有复核计划，或由 Owner 自行登记，不得（MUST NOT）算作批准。

即使例外获批，也不得（MUST NOT）删除发现、伪造验证通过，或省略报告完整性检查及失败传播要求；处理原则见[第 10.5 节](../part-3-quality/10-review-and-merge.md)。

(sample-maintenance-contract)=
## 12.3 Sample 维护契约

维护 `samples/` 时，示例源码、配置、构建目标、测试和页面需要一起考虑。本节规定它们如何对应、由谁负责、何时一起更新。

:::{admonition} 背景与解决思路：Sample 的代码、页面与测试各自演进（非规范性）
:class: note

**问题背景。** Sample 第一次交付时能用，不代表以后一直能用。源码路径、配置、公开接口、Target 或成功日志变了，文档和测试如果由不同的人各自更新，就容易跟不上。用户还能在仓库里找到示例，却无法照着文档构建和运行，出了问题也不知道找谁。

**解决机制。** 用稳定的 `sample_id` 把源码、页面和测试关联起来，修改时一起更新，由 Sample Owner 负责协调代码、文档和证据。示例失效或验证过期时，调整状态，不再继续推荐。

**预期效果。** 源码改了，团队能查到哪些文档和测试需要复核；发现对应关系断了，也能找到负责人。用户看到的 Sample 清单因此更接近实际支持情况。
:::

1. 项目必须（MUST）建立 Sample 清单，为每个纳入支持范围的 Sample 分配稳定的 `sample_id`、源码路径、文档路径、Owner、支持状态和适用版本。
2. 每个 `samples/` 实践指南必须（MUST）与一个或多个真实源码入口建立可验证映射；每个纳入支持范围的 Sample 源码必须（MUST）有对应实践指南，或有经过批准的“不提供用户文档”理由。
3. Sample 的源码、公开 API、Kconfig、构建 Target、工具链、目录或预期输出发生变化时，对应文档和测试必须（MUST）在同一个变更中更新。
4. Sample Owner 必须（MUST）同时负责代码可构建性、文档准确性和测试证据；文档 Maintainer 不得（MUST NOT）被设为唯一技术 Owner。
5. 每个项目必须（MUST）定义 Sample 复核周期。进入正式发布或默认导航的 Sample 必须（MUST）在每个受支持发布版本上重新确认适用性。
6. 出现源码路径失效、配置项删除、API 签名变化、Target 下线、测试持续失败或超过项目规定的验证有效期时，Sample 必须（MUST）自动或人工标记为待复核。
7. 无 Owner、无源码、无可复现构建或无完成判据的 Sample 不得（MUST NOT）标记为 `verified`，不得（MUST NOT）进入默认推荐路径。
8. 废弃 Sample 必须（MUST）标明最后支持版本、替代方案和移除计划；删除源码时必须（MUST）同步删除或重定向文档、导航和测试。
9. 新增 Sample 的 PR 必须（MUST）同时提供实践指南、清单登记和最低测试；无法同时提供时，Sample 必须（MUST）保持非推荐状态，并必须（MUST）关联有 Owner 和截止条件的跟踪项。

推荐的 Sample 清单字段如下：

```yaml
- sample_id: <sample-id>
  source: <sample-source-path>
  document: <sample-document-path>
  owner: <responsible-owner>
  products: ["<product-id>"]
  targets: ["<build-target>"]
  status: verified
  last_verified: 2026-08-29
  evidence: artifacts/sample-tests/<sample-id>/
```

## 12.4 规范采用清单

采用项目必须（MUST）维护一份可审查的清单，说明采用哪份规范、谁负责、何时同步。至少记录规范仓库、采用的 commit/tag（标签必须（MUST）解析到提交）、profile、采用日期、Owner、适用范围、当前例外，以及什么情况下同步、如何复核。profile 必须（MUST）列清适用条款范围，不得（MUST NOT）因此降低该范围内的必需门禁。

采用仓库本地 Skill 时，清单必须（MUST）记录来源、版本或内容哈希、同步日期和负责人；未采用 Skill 时，必须（MUST）注明不适用。

同步规范、Skill 或检查代码时，必须（MUST） Review 要求含义是否变化、记录不兼容变化并重新验证，不得（MUST NOT）只复制文件或更新版本号。Skill 摘要与规范正文冲突时，必须（MUST）以项目声明采用的正文为准，并登记摘要修正任务。
