# HiSpark 文档规范

基于 Diátaxis 的 SDK 文档设计、质量与治理规范，覆盖信息架构、页面创作、上游复用、验证、Review、CI 和持续维护。规范正文不绑定具体芯片、产品或文档工具；本仓库使用 MyST Markdown 维护正文，通过 LaTeX 输出 PDF，并提供配套 Skills、模板和参考检查器。

## 阅读与使用

[在线阅读](https://github.sanchuanhehe.com/hispark-documentation-standard/)提供完整规范，目录从前言、第 1—3 章开始，也可以按任务直接进入：

| 需求 | 阅读入口 |
|---|---|
| 了解背景与适用范围 | [前言](docs/preface.md)、[适用范围与目的](docs/part-1-foundations/01-scope-and-purpose.md) |
| 掌握共同要求 | [十项基础要求](docs/part-1-foundations/04-core-principles.md) |
| 编写文档 | [写作入口与模板](docs/handbook/write-a-page.md) |
| 审查变更或准备发布 | [Review 要求](docs/part-3-quality/10-review-and-merge.md)、[变更与项目检查表](docs/part-4-governance/14-conformance-checklist.md) |
| 接入验证与治理 | [验证与测试](docs/part-3-quality/09-validation-and-testing.md)、[迁移方案](docs/part-4-governance/13-migration.md) |

每篇在线文档同时提供 Markdown 原文，例如[前言原文](https://github.sanchuanhehe.com/hispark-documentation-standard/preface.md)。需要保留相对文件链接的路径上下文时，使用[源目录地址](https://github.sanchuanhehe.com/hispark-documentation-standard/docs/preface.md)。

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

## 构建版本

发布版本以 [VERSION](VERSION) 为准，变更记录见 [Changelog](CHANGELOG.md)，发布操作见[发布手册](.github/RELEASING.md)。构建 Profile 与发布版本是两个维度。

- [最新稳定版](https://github.sanchuanhehe.com/hispark-documentation-standard/)：最近正式发布的规范。
- [固定版本 v0.1.5](https://github.sanchuanhehe.com/hispark-documentation-standard/v0.1.5/)：可用于固定版本引用。
- [开发版](https://github.sanchuanhehe.com/hispark-documentation-standard/dev/)：main 快照，不作为正式发布。

- **Annotated（默认完整版本）**：保留第 2.2 节及全部非规范性解释块。
- **Core（可选核心版本）**：排除第 2.2 节、解释块及仅服务于解释层的检查项和参考资料，具体范围由 [profiles/core.json](profiles/core.json) 定义。
- **基础阅读摘编**：提取第 4 章十项共同要求，省略解释块，并附第 2.1 节关键词定义。它是阅读入口，不是新的符合性等级，也不替代完整规范或 Core。

第 2.2 节自身包含 BCP 14 规范性要求，因此 Core 是范围更小的独立符合性 Profile，不应称为“仅规范性内容版”。两种 Profile 共享 `docs/` 中的正文；Core 在 `_build/variants/` 中生成临时影子工程，不修改源文档。选择器缺失、重复命中或指令块未闭合都会使构建失败。

## 本地预览与构建

### 环境准备

- Node.js 20 或更高版本；
- npm；
- Python 3.10 或更高版本；PDF 产物检查依赖 `requirements-pdf.txt` 中锁定的 pypdf；
- MyST CLI，通过 `package-lock.json` 安装锁定版本。

生成 PDF 还需要完整 TeX Live（含 XeLaTeX、latexmk 和中文排版支持）、Microsoft YaHei（微软雅黑）及 Arial 字体。缺少任一指定字体时构建失败，不使用替代字体静默降级；仅构建网站或运行基础检查不要求这些字体。

在仓库根目录执行以下命令安装依赖，无需管理员权限：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-pdf.txt
npm ci
npm run check
```

`npm run check` 会验证源结构、执行 Profile/PDF 链接/契约测试，并严格构建两种 Profile；不依赖预先存在的 PDF/TeX 下载文件。成功时命令退出码为零；出错时先修复日志指出的问题，再继续构建。

### 预览

```bash
npm run start
```

浏览器打开终端输出的本地地址，按 `Ctrl+C` 停止。预览 Core 时改用 `npm run start:core`；其临时影子工程会在进程退出后清理。

### 生成产物

以下命令均在仓库根目录、已激活的虚拟环境中执行。选择所需输出：

| 输出 | Annotated | Core |
|---|---|---|
| PDF | `npm run build:pdf` | `npm run build:pdf:core` |
| LaTeX | `npm run build:tex` | `npm run build:tex:core` |
| 站点内容 | `npm run build:site` | `npm run build:site:core` |
| 静态 HTML | `npm run build:html` | `npm run build:html:core` |

本地 Annotated 站点配置包含下载项，首次生成站点/HTML 前先生成 PDF 和 LaTeX；无 PDF 环境的静态站点构建使用下文的 Pages 构建入口。

仅生成基础阅读摘编：

```bash
npm run build:pdf:basics
```

一次生成两个 Profile 的全部产物和基础阅读摘编：

```bash
npm run build:all:profiles
```

主要产物：

| Profile | HTML | MyST 站点内容 | PDF | LaTeX |
|---|---|---|---|---|
| Annotated | `_build/html/` | `_build/site/` | `exports/hispark-documentation-standard.pdf` | `exports/hispark-documentation-standard-tex.zip` |
| Core | `_build/html-core/` | `_build/site-core/` | `exports/hispark-documentation-standard-core.pdf` | `exports/hispark-documentation-standard-core-tex.zip` |
| 基础阅读摘编 | 网站基础规范入口 | 复用第 4 章源文件 | `exports/hispark-documentation-basics.pdf` | `exports/hispark-documentation-basics-tex.zip` |

PDF 构建会审计实际跳转目标和正文点击区域，映射保存于 `exports/*.links.json`。已有完整版 PDF 可用 `npm run check:pdf-links` 复查；基础摘编未收录的章节仅保留为文字引用。

## 检查与参考实现

[examples/contracts/](examples/contracts/) 提供非规范性模板和参考数据，不要求采用项目使用同一工具。真实产品参数与证据留在采用项目。

在仓库根目录、已激活的虚拟环境中运行全部单元测试，或检查合成的逐叶预算示例：

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_contracts.py tutorial examples/contracts/tutorial.example.json
```

参考检查器支持报告聚合、逐叶预算及八阶段矩阵的部分确定性检查，不授予整体符合性。`gate-report.example.json` 故意含一项历史发现，与 `gate-plan.example.json` 配套执行 `gate` 子命令时预期失败；零新增债务不代表总体合格。真实批准、归档回执、SDK 和硬件行为仍需采用项目提供证据。

## 网站发布

GitHub Pages 在 `main` 推送或手动触发时检查并发布，PR 只验证。发布 HTML 与 Markdown 原文，不上传本地 PDF/TeX 或商业字体。流程与验证边界见 [Pages 发布说明](.github/PAGES.md)。

在仓库根目录、已激活的虚拟环境中生成同等布局的部署产物：

```bash
BASE_URL=/hispark-documentation-standard python3 scripts/build_pages.py
```

输出位于 `_build/pages/`。`build-manifest.json` 记录提交、运行标识、文件哈希及原文映射；本地未提供 CI 身份时标为 `local-uncommitted`，不代表已经发布。

## 工程结构

```text
.
├── .agents/skills/       # 编写、审查、验证和维护治理 Skills
├── .github/              # Pages 工作流与发布说明
├── docs/                 # MyST 规范正文与前言
├── examples/contracts/  # 非规范性契约模板与合成数据
├── latex/                # LaTeX 输出和维护说明
├── profiles/             # 可选构建的失败关闭选择器清单
├── scripts/              # Profile 构建、结构验证和单元测试
├── myst.yml              # 导航、网站和 PDF/TeX 导出配置
├── package.json          # 锁定 MyST CLI 与构建命令
└── Makefile              # 常用构建入口
```

正文的唯一事实源是 `docs/`。不得（MUST NOT）直接修改构建生成的 HTML、PDF、`.tex` 文件或 Core 影子工程来替代源文档变更。需要调整 Core 范围时，应修改 `profiles/core.json` 并让全部 Profile 检查通过。
