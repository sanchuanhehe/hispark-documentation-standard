# HiSpark 文档规范工程

本仓库使用 MyST Markdown 维护规范正文，并通过 LaTeX 输出正式 PDF。规范正文位于 `docs/`，导航与导出配置位于 `myst.yml`。

## Get Started 试点反馈回灌

条款映射、既有覆盖及修改前后说明见[回灌变更说明](changes/2026-09-23-get-started-feedback.md)。规范性正文保持工具与产品无关；[验证与接入手册](docs/handbook/verification-and-adoption.md)及 `examples/contracts/` 是非规范性模板和参考实现；真实产品参数留在采用项目。

参考检查器支持报告聚合、逐叶预算和八阶段矩阵的部分确定性检查，不能授予整体符合性：

```bash
npm run test:contracts
python3 scripts/validate_contracts.py tutorial examples/contracts/tutorial.example.json
```

`gate-report.example.json` 故意包含一项历史发现，搭配 `gate-plan.example.json` 执行 `gate` 子命令时预期失败。完整报告没有被展示上限截断，也没有用零新增债务冒充总体合格。归档回执真实性、用户测试、独立批准、SDK 和硬件行为需要采用项目自己的证据与检查。

## V1.2 结构整改试行

日常阅读从[十项基础要求](docs/part-1-foundations/04-core-principles.md)开始。作者进入[写作入口与模板](docs/handbook/write-a-page.md)，再按页面内容查阅专项条款。Reviewer 使用[本次文档变更清单](docs/part-4-governance/14-conformance-checklist.md)，项目负责人使用同页的项目与发布清单。

本次主要减少首次阅读与重复核对的负担：前言说明编写背景与阅读方式、导航按任务分组、模板集中、Review 和检查表引用规则定义处。完整章节号与源文件路径保留。基础摘编是阅读入口，不是新的符合性等级；完整条款强度不变，渐进采用需要披露未完成项。

生成短篇基础阅读摘编：

```bash
npm run build:pdf:basics
```

产物为 `exports/hispark-documentation-basics.pdf` 及对应 `-tex.zip`。构建从同一份第 4 章源文件提取正文，省略解释块，附上第 2.1 节关键词定义；离线摘编以章号指向完整规则，不生成指向未收录章节的失效链接。

建议先用一篇真实 Sample 实践指南试行，按[第 13 章](docs/part-4-governance/13-migration.md)记录找模板时间、需口头解释的问题和首轮评审结果；尚未进行用户试验时，不宣称采用效率已提高。

## 构建 Profile

工程提供两种可复现构建：

- **Annotated（默认完整版本）**：保留第 2.2 节及全部“背景与解决思路”非规范性解释块；现有不带后缀的构建命令和产物均属于此 Profile。
- **Core（可选核心版本）**：排除第 2.2 节、11 个非规范性解释块、两条只服务于解释层的 Review/符合性检查项，以及两条只服务于第 2.2 节的参考资料。

第 2.2 节自身包含 BCP 14 规范性要求，因此 Core 是一个范围更小的独立符合性 Profile，不应称为“仅规范性内容版”。两种版本共享 `docs/` 中同一份正文；Core 构建根据 `profiles/core.json` 在 `_build/variants/` 中生成临时影子工程，不修改源文档。每个选择器必须在源文档中恰好命中一次，内容漂移、重复命中或未闭合指令块都会使构建失败。

## 配套 Skills

仓库在 `.agents/skills/` 提供四个可独立使用的 Agent Skill：

| Skill | 适用任务 |
|---|---|
| `$hispark-doc-author` | 分类、编写或重构教程、实践指南、参考资料和解释说明 |
| `$hispark-doc-review` | 审查页面、变更或 Pull Request，输出证据化问题清单和 Reviewer 缺口 |
| `$hispark-doc-verify` | 验证文档构建、技术声明、Sample 覆盖、PR 门禁和 Daily CI |
| `$hispark-doc-maintain` | 审计生命周期、上游同步、Owner、Sample 契约、发布复核和渐进迁移 |

Skills 通过[在线规范](https://github.sanchuanhehe.com/hispark-documentation-standard/)的章节与小节链接读取正文，不依赖安装位置或本地规范副本；执行前核对采用版本、Profile 与[部署清单](https://github.sanchuanhehe.com/hispark-documentation-standard/build-manifest.json)，不静默升级项目采用版本。入口文件保持精简，角色专属工作手册按需从各自 `references/` 加载。它们不预设具体芯片、产品、文档生成器或绝对路径；执行时应发现采用项目实际声明的工具和检查入口。

支持仓库级 Skills 的 Agent 可以直接从 `.agents/skills/` 发现它们。也可以将需要的 Skill 目录复制到个人 Codex Skills 目录：

```bash
cp -R .agents/skills/hispark-doc-author "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## 环境要求

- Node.js 20 或更高版本；
- npm；
- Python 3.10 或更高版本；PDF 产物检查依赖 `requirements-pdf.txt` 中锁定的 pypdf；
- MyST CLI（已通过 `package-lock.json` 锁定）；
- 完整 TeX Live，包含 XeLaTeX、latexmk 和中文排版支持；
- Microsoft YaHei（微软雅黑）和 Arial 字体。PDF 构建会在缺少任一字体时失败，不使用替代字体静默降级。

## 本地构建

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-pdf.txt
npm install
npm run check
npm run build:pdf
npm run build:site
npm run build:html
npm run build:tex
```

PDF 导出会将本书章节链接和显式锚点转换为文内跳转；命名具体节的链接定位到该节，范围链接定位到范围起点。构建会检查实际 PDF 的链接动作、目标页和正文点击区域，拒绝指向本地外部文件的链接或丢失的引用。`exports/*.links.json` 保存该次构建的来源与目标映射；可使用 `npm run check:pdf-links` 复查完整 PDF。基础摘编不收录的章节仍保留为普通文字引用。

`npm run check` 会分别验证 Annotated 与 Core 的结构并执行两种严格站点构建；检查过程不依赖预先存在的 PDF/TeX 下载文件。

Core 构建：

```bash
npm run build:site:core
npm run build:html:core
npm run build:pdf:core
npm run build:tex:core
```

一次生成两个 Profile 的全部产物和基础阅读摘编：

```bash
npm run build:all:profiles
```

本地预览：

```bash
npm run start
npm run start:core
```

以上两条命令分别预览 Annotated 与 Core。Core 预览使用临时影子工程，退出预览进程后自动清理。

主要输出：

| Profile | HTML | MyST 站点内容 | PDF | LaTeX |
|---|---|---|---|---|
| Annotated | `_build/html/` | `_build/site/` | `exports/hispark-documentation-standard.pdf` | `exports/hispark-documentation-standard-tex.zip` |
| Core | `_build/html-core/` | `_build/site-core/` | `exports/hispark-documentation-standard-core.pdf` | `exports/hispark-documentation-standard-core-tex.zip` |
| 基础阅读摘编 | 网站基础规范入口 | 复用第 4 章源文件 | `exports/hispark-documentation-basics.pdf` | `exports/hispark-documentation-basics-tex.zip` |

## 工程结构

```text
.
├── .agents/skills/       # 编写、审查、验证和维护治理 Skills
├── docs/                 # MyST 规范正文与前言
├── latex/                # LaTeX 输出和维护说明
├── profiles/             # 可选构建的失败关闭选择器清单
├── scripts/              # Profile 构建、结构验证和单元测试
├── myst.yml              # 导航、网站和 PDF/TeX 导出配置
├── package.json          # 锁定 MyST CLI 与构建命令
└── Makefile              # 常用构建入口
```

正文的唯一事实源是 `docs/`。MUST NOT 直接修改构建生成的 HTML、PDF、`.tex` 文件或 Core 影子工程来替代源文档变更。需要调整 Core 范围时，应修改 `profiles/core.json` 并让全部 Profile 检查通过。
