---
name: hispark-doc-review
description: Review HiSpark SDK documentation changes for information architecture, product scope, technical evidence, usability, and merge readiness. Use when asked to review a page, diff, pull request, generated documentation, or proposed approval; do not use for authoring-only work.
---

# HiSpark 文档审查

给出证据可定位、严重性清晰、可直接修复的文档审查结果。Review 不等同于措辞润色，也不能替代缺失的领域、验证、安全或发布批准。

## 权威来源

从[HiSpark 文档规范在线版](https://github.sanchuanhehe.com/hispark-documentation-standard/)按任务读取正文，不依赖 Skill 安装目录或本地规范副本。规范正文优先于本 Skill 摘要。

先核对采用项目声明的 commit/tag、Profile 与[在线部署清单](https://github.sanchuanhehe.com/hispark-documentation-standard/build-manifest.json)。在线版随发布更新；版本或范围不一致时，以项目声明采用的版本核对，不静默升级。无法读取所需正文时明确报告缺口，不用 Skill 摘要代替条款。

按审查范围读取：

- 条款解释与内容组织：[第 2 章](https://github.sanchuanhehe.com/hispark-documentation-standard/normative-language/)、[第 4 章](https://github.sanchuanhehe.com/hispark-documentation-standard/core-principles/)、[第 5 章](https://github.sanchuanhehe.com/hispark-documentation-standard/information-architecture/)；
- 上游、专项与证据：[第 7 章](https://github.sanchuanhehe.com/hispark-documentation-standard/upstream-downstream/)、[第 8 章](https://github.sanchuanhehe.com/hispark-documentation-standard/specialized-content/)、[第 9 章](https://github.sanchuanhehe.com/hispark-documentation-standard/validation-and-testing/)；
- 评审、治理与清单：[第 10 章](https://github.sanchuanhehe.com/hispark-documentation-standard/review-and-merge/)、[第 12 章](https://github.sanchuanhehe.com/hispark-documentation-standard/governance-and-maintenance/)、[第 14 章](https://github.sanchuanhehe.com/hispark-documentation-standard/conformance-checklist/)。

执行完整审查或判定 Reviewer 时，读取 [references/review-checklist.md](references/review-checklist.md)。

## 审查流程

1. 明确审查对象、目标分支、适用版本和当前提交。优先查看实际 diff、页面源文件、相关源码/配置、构建结果与渲染产物，不以 PR 描述代替证据。
2. 根据变更类型确定需要覆盖的审查角色。只评价自己有证据判断的范围；缺少领域能力或运行证据时明确要求相应 Reviewer，不给出“看起来可以”的代替结论。
3. 依次检查：
   - 页面主要意图、`doc_type`、目录职责和认知负担；
   - 产品、版本、Target、硬件对象、上游差异和事实来源；
   - 命令、风险、预期结果、恢复路径和验证等级；
   - Sample/API/配置映射、Owner、状态、覆盖率分母和生命周期；
   - 图片必要性、等价文本、可编辑图源、版本与敏感信息；
   - 自动门禁、Daily CI、例外和 Review 记录。
4. 解释性内容存在时，分别检查相邻条款和解释块。执行删除测试：忽略解释块后，符合性结论必须不变；解释块不能增加要求、产品能力或责任边界。
5. 对生成内容同时检查事实源、生成器或模板变化和最终可读渲染。不得因“工具生成”而跳过审查。
6. 按正文[第 10.2.4 节](https://github.sanchuanhehe.com/hispark-documentation-standard/review-and-merge/#id-10-2-4-review)、[第 10.5—10.7 节](https://github.sanchuanhehe.com/hispark-documentation-standard/review-and-merge/#id-10-5)核对契约、渲染适配器、Runner 和测试是否受到等价 Reviewer 约束；历史债务仍存在或完整报告、身份、证据缺失时，不将增量绿色认定为总体合格。

## 输出

先列问题，按严重性从高到低排序。每条问题包含：严重性、短标题、准确文件/行号、可观察证据、影响、对应规范要点和最小修复建议。只报告本次变更新增或暴露、且作者能够处理的问题。

若没有阻塞问题，明确写“未发现阻塞性问题”，并继续列出验证范围、未覆盖风险和仍需的人类 Reviewer。除非用户同时要求修复，否则不修改文件；任何情况下都不得冒充实际批准人或伪造 Review 记录。
