# 维护与迁移模型

## 1. 基线清单

页面或内容单元至少记录：

- 路径、导航入口、标题和 `doc_type`；
- 正式产品、版本、Target、硬件对象和配置；
- `status`、Owner、`last_verified`、`verification_level`；
- `source_refs`、`upstream_refs`、相关测试和证据；
- URL、入链、重定向和替代页面；
- 已知例外、阻塞项及复核日期。

按 `verified`、`reviewed`、`draft`、`deprecated`、失效/待复核分别统计，不用“页面存在”代表可用。

## 2. 角色边界

| 角色 | 维护责任 |
|---|---|
| 文档作者 | 用户问题、分类、来源、版本和验证边界 |
| 领域 Owner | 技术事实、限制、风险和产品边界 |
| 文档 Maintainer | 信息架构、术语、链接和生命周期 |
| 测试/CI Owner | Build、Smoke、HIL 和文档门禁 |
| 发布 Owner | 文档版本、SDK 发布物、URL 和变更说明一致性 |

每个一级目录需要 Owner。文档 Maintainer 不能成为 Sample 的唯一技术 Owner。

## 3. 上游与下游维护

下游页面只维护：

- 本产品入口和环境上下文；
- 相对上游的增加、替换、限制与不适用项；
- 版本匹配的最小调用；
- 本产品验证结果和恢复边界。

检查上游项目、版本、URL、锚点和许可/可访问性。没有产品差异时只保留导航入口。上游移动、失配或与下游证据冲突时，页面降级为待复核。

## 4. Sample 维护契约

每个纳入支持范围的 Sample 建立：

```yaml
- sample_id: <stable-id>
  source: <source-path>
  document: <document-path>
  owner: <responsible-owner>
  products: [<product-id>]
  targets: [<build-target>]
  status: <status>
  last_verified: <yyyy-mm-dd>
  evidence: <evidence-location>
```

源码、公开 API、Kconfig、Target、工具链、目录或预期输出变化时，文档和测试在同一变更中更新。无 Owner、无源码、无可复现构建或无完成判据的 Sample 不进入默认推荐路径。

## 5. Daily CI 与发布

Daily CI 与 PR 门禁复用锁定依赖和检查实现，至少覆盖：

- 全量严格构建、导航、链接、图片和大小写；
- 上游 URL、锚点、固定版本、内容漂移与疑似重复；
- `get-started/` 预算和隐含前置条件；
- API、配置、Target、Sample 和页面映射漂移；
- 应执行的 Build、Smoke、HIL 与覆盖矩阵；
- `last_verified`、Owner、例外、阻塞和临时副本过期；
- 结果、依赖版本、提交和证据归档。

明确时区、计划、最长允许未成功运行时间、告警接收方和故障 Owner。未执行或证据缺失不能继承旧绿色结果。影响 Happy Path、公开 API 或推荐 Sample 的回归阻断相关发布。

每次 SDK 发布输出复核报告，分别列出已验证、失败、阻塞、废弃和未运行项。

## 6. 渐进迁移

1. **建立基线**：补分类、范围、Owner 和验证状态，暂不批量移动。
2. **明确职责**：收敛 Happy Path，拆分混合页面，去除上游副本，整理 Sample 与 FAQ。
3. **建立证据**：锁定构建，接入链接/元数据/映射/覆盖门禁和 Daily CI。
4. **推广复用**：先试点并记录例外，再推广稳定模型。

迁移始终保留稳定 URL；必须移动时提供重定向或兼容入口并修复站内引用。

## 7. 计划条目格式

| 对象 | 当前问题 | 规范依据 | 风险 | 目标状态 | Owner | 验收证据 | 截止/复核 | URL 策略 |
|---|---|---|---|---|---|---|---|---|

把未知事实和组织决策明确标为待确认，不为团队虚构 Owner、期限、覆盖率或完成状态。
