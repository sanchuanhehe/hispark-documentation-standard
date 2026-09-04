---
name: hispark-doc-verify
description: Execute or assess HiSpark SDK documentation builds, links, metadata, technical claims, Sample coverage, and CI evidence without overstating results. Use for documentation QA, release readiness, PR gates, Daily CI runs, coverage audits, or verification-status decisions; do not use for lifecycle governance or migration planning.
---

# HiSpark 文档验证

建立“声明—检查—证据—结论”的可审计链条，并准确区分静态、构建、Smoke 与 HIL 验证。

## 权威来源

先查找采用项目声明的 HiSpark 文档规范。本 Skill 随规范仓库使用时，规范位于 Skill 目录向上三级的 `docs/`。重点读取第 4.4、6.1、8、9、10.3、10.4、11、12.3 和 14 章；规范正文优先于本 Skill 摘要。

需要测试矩阵、覆盖率或报告格式时，读取 [references/verification-matrix.md](references/verification-matrix.md)。

## 验证流程

1. 列出待验证声明、适用产品/版本/Target/硬件对象、要求的验证级别和成功判据。没有明确分母、范围或判据时，先把结果标为不可判定。
2. 从仓库配置、CI 文件和维护文档中发现项目定义的检查入口与锁定依赖，不假设特定文档生成器、命令或绝对路径。优先复用 PR、Daily CI 和本地共同使用的实现。
3. 按层执行并保存证据：
   - source：源格式、元数据、术语、路径大小写、结构和敏感信息；
   - build：严格站点构建、导航、内链、锚点、图片、代码片段和可读渲染；
   - smoke：目标环境中的关键命令与可观察成功标记；
   - HIL：声明产品和硬件对象上的端到端行为。
4. 验证 API、Sample、配置、Target、上游引用和页面之间的映射。链接可访问不代表版本适配；构建成功不代表目标板行为正确。
5. Sample 覆盖分别统计 Build、Smoke、HIL、负向和版本覆盖。每项同时报告分子、分母、适用版本、日期和阻塞项；仓库文件数或脚本数不是覆盖率。
6. 对超时、设备无响应、串口静默、缺少成功标记、日志不完整或证据上传失败采用失败关闭。不得继承旧的绿色结果。
7. 若用户要求评估 Daily CI，确认它复用 PR 检查实现，并具有时区、计划、最长未成功时间、告警接收方、故障 Owner、证据归档和回归跟踪项。

## 结论边界

结论只能达到实际完成的最高层级。无法运行硬件、缺少凭据或没有目标环境时，继续完成静态和构建验证，并把其余项标为 `blocked` 或 `not-run`，不得推断通过。

交付验证矩阵、实际命令、关键输出或产物位置、失败/阻塞原因以及 `verified` 尚缺的证据。除非用户明确要求，不修改 CI、不触发外部发布，也不改变页面状态。
