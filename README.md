# HiSpark 文档规范工程

本仓库使用 MyST Markdown 维护规范正文，并通过 LaTeX 输出正式 PDF。规范正文位于 `docs/`，导航与导出配置位于 `myst.yml`。

## 构建 Profile

工程提供两种可复现构建：

- **Annotated（默认完整版本）**：保留第 2.2 节及全部“背景与解决思路”非规范性解释块；现有不带后缀的构建命令和产物均属于此 Profile。
- **Core（可选核心版本）**：排除第 2.2 节、10 个非规范性解释块、两条只服务于解释层的 Review/符合性检查项，以及两条只服务于第 2.2 节的参考资料。

第 2.2 节自身包含 BCP 14 规范性要求，因此 Core 是一个范围更小的独立符合性 Profile，不应称为“仅规范性内容版”。两种版本共享 `docs/` 中同一份正文；Core 构建根据 `profiles/core.json` 在 `_build/variants/` 中生成临时影子工程，不修改源文档。每个选择器必须在源文档中恰好命中一次，内容漂移、重复命中或未闭合指令块都会使构建失败。

## 配套 Skills

仓库在 `.agents/skills/` 提供四个可独立使用的 Agent Skill：

| Skill | 适用任务 |
|---|---|
| `$hispark-doc-author` | 分类、编写或重构教程、实践指南、参考资料和解释说明 |
| `$hispark-doc-review` | 审查页面、变更或 Pull Request，输出证据化问题清单和 Reviewer 缺口 |
| `$hispark-doc-verify` | 验证文档构建、技术声明、Sample 覆盖、PR 门禁和 Daily CI |
| `$hispark-doc-maintain` | 审计生命周期、上游同步、Owner、Sample 契约、发布复核和渐进迁移 |

Skills 将本仓库 `docs/` 视为权威规范来源，入口文件保持精简，角色专属工作手册按需从各自 `references/` 加载。它们不预设具体芯片、产品、文档生成器或绝对路径；执行时应发现采用项目实际声明的工具和检查入口。

支持仓库级 Skills 的 Agent 可以直接从 `.agents/skills/` 发现它们。也可以将需要的 Skill 目录复制到个人 Codex Skills 目录：

```bash
cp -R .agents/skills/hispark-doc-author "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## 环境要求

- Node.js 20 或更高版本；
- npm；
- MyST CLI（已通过 `package-lock.json` 锁定）；
- 完整 TeX Live，包含 XeLaTeX、latexmk 和中文排版支持；
- Microsoft YaHei（微软雅黑）和 Arial 字体。PDF 构建会在缺少任一字体时失败，不使用替代字体静默降级。

## 本地构建

```bash
npm install
npm run check
npm run build:pdf
npm run build:site
npm run build:html
npm run build:tex
```

`npm run check` 会分别验证 Annotated 与 Core 的结构并执行两种严格站点构建；检查过程不依赖预先存在的 PDF/TeX 下载文件。

Core 构建：

```bash
npm run build:site:core
npm run build:html:core
npm run build:pdf:core
npm run build:tex:core
```

一次生成两个 Profile 的全部产物：

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
