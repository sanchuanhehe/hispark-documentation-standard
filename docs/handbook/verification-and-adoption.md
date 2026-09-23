---
title: 验证与接入手册：模板和参考实现
short_title: 验证与接入
---

本页是非规范性参考实现，不新增符合性条件。下面的模板、工具和组织方式均可替换；判定依据始终是所链接的正文条款。示意值不是产品支持声明、获批预算、真实测试证据或例外批准。

## 三层内容放在哪里

| 层次 | 保存内容 | 不保存什么 |
|---|---|---|
| 规范正文 | 可独立审查的义务、边界和证据要求 | SDK 下载地址、具体 Target 或平台语法 |
| 非规范性参考实现 | 本手册、模板、参考检查器和测试 | 新的强制工具或合规认证 |
| 采用项目配置 | 实际仓库、版本、Target、命令、平台、预算、调度和留存 | 改写通用规则的隐含例外 |

参考数据位于仓库 `examples/contracts/`，参考检查器位于 `scripts/validate_contracts.py`；不要求采用项目复制这些目录名。正文依据集中在[第 8 章](../part-2-authoring/08-specialized-content.md)、[第 9 章](../part-3-quality/09-validation-and-testing.md)、[第 10 章](../part-3-quality/10-review-and-merge.md)及[第 12 章](../part-4-governance/12-governance-and-maintenance.md)。

## 路径与预算模板

为每个叶子登记：标识、首次成功目标、完成判据、入口路径、适用平台与交互方式、必要准备入口、预算、观测值、用户测试、Owner 和批准记录。预算覆盖路径经过的公共页及外部必要准备，重复展示不重复计算独立决策。

`tutorial.example.json` 展示可替换的字段布局。数字只是测试输入，不是推荐阈值；正式采用前用获批项目预算及真实观测替换。字段中的 `selections` 用稳定维度标识连接控件；每次出现保留标签、顺序、语义和联动组。一个 CLI/VS Code 选择与一个 Windows/Linux 展示维度不等于四个首次成功目标。

一种实现是在 Windows/Linux 联动 Tabs 中保持相同标签顺序和选择状态，逐平台核对主要动作及完成判据。不同控件的数量不作为决策数；是否确实属于同一维度仍需人工审查。WSL、Dev Drive 等优化可链接在成功后，不写进首次成功前置。

## 八阶段矩阵与证据模板

每个叶子/变体一组记录，分别列出 source/static、environment、configure、build、flash、serial、Smoke、HIL。可用如下短表呈现；完整执行上下文放关联证据，避免超宽表格。

| 阶段 | 是否必需及理由 | 状态 | 判据与证据 | 缺口及负责人 |
|---|---|---|---|---|
| `<stage>` | `<required / applicability>` | `<scenario-status>` | `<criterion / evidence>` | `<reason / owner / plan / review-date>` |

证据记录的可填写骨架如下，状态词及适用性按[第 9.4 节](../part-3-quality/09-validation-and-testing.md)解释：

```yaml
scenario_id: <leaf-platform-interaction>
page: <document-path-and-revision>
facts_revision: <contract-commit-or-hash>
scope: <product-target-config-hardware>
environment:
  os: <exact-version>
  runner: <runner-kind>
  architecture: <architecture>
  sdk: <exact-version-and-commit>
  tools: <tool-versions-or-commits>
sources:
  documentation: <repository-ref-resolved-sha>
  checkout: <repository-ref-resolved-sha>
  equivalence: <method-scope-digest-result>
stages:
  - stage: <one-of-eight-stages>
    status: not_run
    required: <true-or-false-with-reason>
    criterion: <independently-defined-criterion>
    started_at: null
    ended_at: null
    working_directory: null
    command: null
    config_changes: null
    exit_code: null
    log: null
    artifacts: []
    reason: <why-not-executed-or-no-artifact>
    boundary: <what-is-not-proven>
    followup: <owner-plan-review-date>
```

执行后记录真实时间、命令、退出码和日志，产物条目包含路径、字节大小和 SHA-256。不要把此模板中的 `not_run` 批量改为 `passed`。同样不要把服务器构建记录当作桌面 GUI、USB 或实板验证。

## 可执行文档参考实现

可将版本、仓库、分支、Target、命令、配置变化及产物写入一个项目事实文件。生成器从事实文件生成命令块，页面只保留一个明确占位符；构建适配器检查占位符恰好出现一次，再调用生成器。静态检查核对渲染后的命令，Runner 消费相同事实文件，证据验证器核对实际执行参数和产物。

这些层次不要求特定文档框架。仓库级 Python 工具包是一种实现：工作流只调用统一命令，规则、生成器、Runner 和测试放在可导入模块中；也可采用其他语言或组织方式。旧入口只做转发，登记调用方、Owner、移除条件和截止日期。

接入时可逐层注入以下错误，确认检查确实失败：

| 注入点 | 预期发现 |
|---|---|
| 事实源或独立判据 | 字段缺失、版本不匹配或判据无来源 |
| 生成器与占位符 | 零次/多次替换、陈旧命令或参数丢失 |
| 构建适配器与渲染 | Hook 未运行、输出仍有占位符或内容漂移 |
| Runner | 使用另一分支、Target、配置或命令 |
| 证据验证 | 退出码丢失、日志截断、产物哈希不符 |

这里给出接入测试清单，不声称本仓库已实现或执行任何 SDK 的上述链路。

## 报告与聚合参考实现

`gate-plan.example.json` 声明预期提交、运行标识及必需检查；`gate-report.example.json` 是配套的合成报告，故意保留一项 `known` 发现。它的 `new` 计数为零，但参考检查器仍返回非零退出码。

```bash
python3 scripts/validate_contracts.py gate \
  examples/contracts/gate-plan.example.json \
  examples/contracts/gate-report.example.json
```

参考实现只验证报告结构、身份、计数、必需检查、归档回执字段和无例外的总体判定；它不查询归档服务、不证明日志或批准的真实性，也不验证 SDK 能力。它有意不实现例外放行，采用项目如需支持例外，需按正文接入可信批准记录及过期检查，而不是在报告内设置一个自批布尔值。

完整机器报告保留所有发现；摘要按规则和分类聚合，再按配置上限为每类选少量 annotation 并链接完整报告。上限只控制展示。零发现使用有效的空发现数组，不生成空文件。

每个必需检查由聚合器按预期清单查找，不从收到的报告反推清单。上传成功以归档服务回执核验；日志流式输出并保留原进程退出码。长任务可定期发进度，超时/取消时终止整个进程树并等待退出，再收集最终证据。平台适配器还需要故障注入测试，不以本参考检查器单元测试替代。

## 采用、例外与变更清单模板

`adoption.template.yaml` 提供规范采用记录骨架，涵盖规范身份、profile、Owner、Skill 身份和同步机制。没有采用 Skill 时显式记录不适用。标签解析到不可变提交后再登记。

每项例外另填：唯一标识、偏离条款、适用发现、提交/版本范围、原因、影响、补偿措施、Owner、独立批准人、批准时间、到期日期、复核及恢复阻断机制。预算例外另附用户测试证据。模板没有预先批准任何例外。

删除、移动或重命名页面时，可逐项登记：旧文件/新文件、旧 URL/新入口、导航引用、正文入链、重定向/保留页/迁移映射、旧入口验证结果、Owner 和回滚方式。生成器、契约、渲染适配器、Runner 和测试一并检查 Reviewer 路由，不只检查页面。

构建闭包清单可记录：依赖对象、来源、精确版本/摘要、获取方式、递归依赖、公开构建环境可访问性和复现结果。部署清单连接提交、总体门禁运行、已验证产物摘要与实际部署摘要；存在缺口就保留阻塞，不从别的运行借用绿色状态。

## 工具运行与迁移提示

原子化提交可以按语义模型、门禁契约和配套实现组织，但每组都检查自洽性，避免只提交生成器而漏掉调用方。发布前检查实际 diff，生成产物是否入库由项目政策决定。

需要 GitHub 镜像时，先确认上游、目标账号、仓库名、可见性和授权，再创建镜像并推送指定分支，最后读回远端身份及提交。镜像创建成功并不证明其验证可以用于上游，仍需[镜像等价证据](../part-2-authoring/07-upstream-downstream.md)。

网络排障先区分沙箱/网络权限、DNS、代理、TLS、服务可达性与认证失败；不要因连接失败就判定 token 过期。确认目标后再检查账号及权限，不输出凭据、不接受未授权许可、不通过关闭安全校验规避问题。本段是操作提示，不规定采用平台或认证实现。
