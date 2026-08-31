# HiSpark 文档规范工程

本仓库使用 MyST Markdown 维护规范正文，并通过 LaTeX 输出正式 PDF。规范正文位于 `docs/`，导航与导出配置位于 `myst.yml`。

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
npm run build:html
npm run build:pdf
npm run build:tex
```

本地预览：

```bash
npm run start
```

主要输出：

- HTML：`_build/html/`
- MyST 站点内容：`_build/site/`
- PDF：`exports/hispark-documentation-standard.pdf`
- LaTeX：`exports/hispark-documentation-standard-tex.zip`

## 工程结构

```text
.
├── docs/                 # MyST 规范正文与前言
├── latex/                # LaTeX 输出和维护说明
├── scripts/              # 结构与内容验证
├── myst.yml              # 导航、网站和 PDF/TeX 导出配置
├── package.json          # 锁定 MyST CLI 与构建命令
└── Makefile              # 常用构建入口
```

正文的唯一事实源是 `docs/`。MUST NOT 直接修改构建生成的 HTML、PDF 或 `.tex` 文件来替代源文档变更。
