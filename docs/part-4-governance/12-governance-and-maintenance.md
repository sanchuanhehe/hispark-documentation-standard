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

每个一级目录 MUST 有明确 Owner。高频变更的 Sample、API 和工具文档 SHOULD 通过 CODEOWNERS 或等价机制自动请求评审。

## 12.2 持续维护要求

1. 文档 Owner MUST 维护页面准确性和生命周期；领域 Owner MUST 维护技术事实，二者 SHOULD 形成联合评审关系。
2. 项目 MUST 建立“源码路径或配置变更到受影响文档与测试”的依赖映射或等价检查。
3. 每次 SDK 发布 MUST 生成文档与 Sample 复核报告，至少列出已验证、失败、阻塞、废弃和未运行项。
4. 项目 MUST 定期识别超过验证有效期、Owner 失效、外链失效或来源漂移的页面，并分配修复责任。
5. 维护工作 MUST 以关闭证据缺口为目标；仅更新日期、状态文字或覆盖率数字而未重新验证，MUST NOT 延长 `verified` 状态。
6. 例外和阻塞项 MUST 有 Owner、原因、风险、下一步和复核日期；无期限阻塞 MUST NOT 被隐藏在聚合覆盖率中。

对本规范的长期例外 MUST 记录：

- 偏离的条款；
- 业务或技术理由；
- 已评估的影响；
- 补偿措施；
- Owner；
- 到期或复核日期。

(sample-maintenance-contract)=
## 12.3 Sample 维护契约

`samples/` 不只是文档集合，也是示例源码、配置、构建目标、测试和页面之间的维护契约。

:::{admonition} 背景与解决思路：Sample 的代码、页面与测试各自演进（非规范性）
:class: note

**问题背景。** Sample 容易被当作一次性交付：源码路径、配置项、公开接口、Target 或成功日志变化后，页面和测试由不同人员在不同时间维护。结果是仓库里仍能找到示例，却无法按文档可靠构建和复现，失败也没有明确责任人。

**解决机制。** 稳定的 `sample_id`、源码—页面—测试双向映射、同一变更内的联动更新，以及由 Sample Owner 统筹代码、文档与证据，可以把三者作为一个维护单元；失效或过期时的状态降级则防止它继续被推荐。

**预期效果。** 源码变化后，团队能够通过映射定位需要复核的文档和测试；用户看到的 Sample 清单更接近真实支持范围，维护者也能从断裂映射中定位修复责任。
:::

1. 项目 MUST 建立 Sample 清单，为每个纳入支持范围的 Sample 分配稳定的 `sample_id`、源码路径、文档路径、Owner、支持状态和适用版本。
2. 每个 `samples/` 实践指南 MUST 与一个或多个真实源码入口建立可验证映射；每个纳入支持范围的 Sample 源码 MUST 有对应实践指南，或有经过批准的“不提供用户文档”理由。
3. Sample 的源码、公开 API、Kconfig、构建 Target、工具链、目录或预期输出发生变化时，对应文档和测试 MUST 在同一个变更中更新。
4. Sample Owner MUST 同时负责代码可构建性、文档准确性和测试证据；文档 Maintainer MUST NOT 被设为唯一技术 Owner。
5. 每个项目 MUST 定义 Sample 复核周期。进入正式发布或默认导航的 Sample MUST 在每个受支持发布版本上重新确认适用性。
6. 出现源码路径失效、配置项删除、API 签名变化、Target 下线、测试持续失败或超过项目规定的验证有效期时，Sample MUST 自动或人工标记为待复核。
7. 无 Owner、无源码、无可复现构建或无完成判据的 Sample MUST NOT 标记为 `verified`，MUST NOT 进入默认推荐路径。
8. 废弃 Sample MUST 标明最后支持版本、替代方案和移除计划；删除源码时 MUST 同步删除或重定向文档、导航和测试。
9. 新增 Sample 的 PR MUST 同时提供实践指南、清单登记和最低测试；无法同时提供时，Sample MUST 保持非推荐状态，并 MUST 关联有 Owner 和截止条件的跟踪项。

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
