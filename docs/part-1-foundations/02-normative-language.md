---
title: '2. 规范性引用与规范性语言'
---

## 2.1 BCP 14 关键词

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [BCP 14](https://www.rfc-editor.org/info/bcp14) [RFC2119](https://www.rfc-editor.org/info/rfc2119/) [RFC8174](https://www.rfc-editor.org/info/rfc8174/) when, and only when, they appear in all capitals, as shown here.

本规范使用以下中文释义帮助阅读，但规范效力由大写英文关键词确定：

| 关键词 | 中文释义 | 使用规则 |
|---|---|---|
| `MUST`、`REQUIRED`、`SHALL` | 必须 | 绝对要求；不满足即不符合本规范 |
| `MUST NOT`、`SHALL NOT` | 禁止、不得 | 绝对禁止 |
| `SHOULD`、`RECOMMENDED` | 应该、推荐 | 仅在存在充分理由且理解后果时可以偏离；偏离理由 MUST 记录 |
| `SHOULD NOT`、`NOT RECOMMENDED` | 不应该、不推荐 | 仅在存在充分理由且理解后果时可以采用；采用理由 MUST 记录 |
| `MAY`、`OPTIONAL` | 可以、可选 | 是否采用由项目决定，不影响基础符合性 |

大写关键词 SHOULD 谨慎使用。普通中文“必须”“应该”“可以”或小写英文 `must`、`should`、`may` 不具有 BCP 14 的特殊规范含义。

## 2.2 规范性条款与非规范性说明

规范 MAY 在条款附近搭配解释性内容，以帮助作者、Reviewer 和采用项目理解设计理由、落地方法和常见误区。解释性内容 MUST 明确标为“非规范性”，并 MUST 与具有约束力的条款保持视觉和语义边界。

### 2.2.1 解释性内容的任务

解释性内容 SHOULD 以采用项目在文档设计、创作、验证或维护中遇到的实际问题为对象，并 SHOULD 帮助读者依次理解：

1. 这项要求出现于什么背景或工作场景；
2. 未处理时会出现哪些可观察问题，为什么容易反复发生；
3. 相邻条款通过什么机制降低问题；
4. 采用后预期改善什么，以及作者或 Reviewer 可以观察什么信号。

解释性内容 SHOULD 将事实、经验判断和建议分开表达。它 MUST NOT 只解释本规范的编辑或解释机制，例如 BCP 14 关键词、解释块标记或显式标签，也 MUST NOT 用“有助于提升质量”一类抽象结论代替具体问题和作用机制。针对文档分类规则的说明仍应从用户任务、可观察问题和维护影响出发。关于本规范自身的阅读方式和解释规则 MUST 放在前言或本章正文中。

### 2.2.2 允许的解释块

| 类型 | 回答的问题 | 适合内容 | 不适合内容 |
|---|---|---|---|
| 背景与解决思路（Context and rationale） | 问题为什么反复出现，相邻条款如何缓解？ | 工作场景、可观察症状、成因、作用机制、预期改善和观察信号 | 只说规则重要、重复条款全文或承诺无法验证的效果 |
| 实施提示（Implementation guidance） | 通常怎样落地？ | 推荐步骤、检查顺序、工具思路、责任协作 | 伪装成唯一合规实现 |
| 示例（Example） | 符合要求是什么样？ | 最小正例、元数据、Review 或测试记录 | 暗示具体产品具备某能力 |
| 反例（Counterexample） | 常见错误是什么？ | 易混淆写法、错误证据链、错误归类 | 未说明原因的负面评价 |

1. 规范性条款 MUST 在没有解释块时仍然完整、无歧义且可独立审查。
2. 解释块 MUST NOT 引入新的符合性条件、例外、产品能力或责任边界，也 MUST NOT 改写或削弱相邻条款。
3. 解释块 MUST NOT 使用大写 BCP 14 关键词表达自身要求；需要引用条款时 SHOULD 链接到条款，而不是复制条款全文。
4. 解释块 SHOULD 紧邻其解释的条款，并 SHOULD 只处理一个局部问题。发展为完整流程、概念体系或参数参考时 MUST 迁移到相应的实践指南、解释说明或参考资料页面。
5. 解释块标题 SHOULD 使用“类型：具体问题（非规范性）”形式，MUST NOT 只用“设计理由”或“说明”等无法指示问题主题的名称。用于传达条款背景和 know-how 时 SHOULD 使用“背景与解决思路：具体问题（非规范性）”。
6. 关键或被多处引用的规范性条款 SHOULD 使用稳定、语义化的显式标签；标签变化 MUST 视为链接兼容性变化处理。
7. Reviewer MUST 分别检查条款的可执行性和解释块的准确性，并执行“删除测试”：临时忽略解释块后，符合性结论 MUST 保持不变。

解释块 MUST 使用项目统一的结构化标记或语义组件，至少携带解释类型和“非规范性”标识。需要稳定引用的相邻条款 SHOULD 使用不依赖显示序号的语义化显式标识。采用项目 MAY 自主选择满足这些要求的源格式、构建系统和呈现方式。
