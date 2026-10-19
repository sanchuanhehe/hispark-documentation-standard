# LaTeX 输出说明

本地默认字体方案为 `licensed`：中文使用 Microsoft YaHei（微软雅黑），英文、数字和代码使用 Arial。公开 CI 显式选择 `PDF_FONT_PROFILE=open`：中文使用 Noto Sans CJK SC，英文、数字和代码使用 Liberation Sans。两种方案不互为自动回退；缺少所选字体时构建失败。

LaTeX 模板只声明字体家族名，不包含构建机绝对路径；构建脚本通过 Fontconfig 解析所选字体及 TTC 字体集索引，在临时构建目录创建链接，编译后立即移除。仓库和 LaTeX 导出包均不记录本机路径，也不复制受许可约束的字体文件。自动构建的封面及 `pdf-manifest.json` 明示字体方案和版本身份，并检查 PDF 实际嵌入字体。

本工程不维护与 MyST 正文并行的第二份手写 LaTeX 内容。LaTeX 由同一组 MyST 页面生成，以避免事实源分裂。

MyST 1.10.1 的 LaTeX 渲染器会对部分代码块中的连字符进行排版性空格处理。工程中的 `scripts/build_latex.py` 会从 MyST 源页面恢复代码块原文，再调用 XeLaTeX；构建同时验证源代码块与生成的 `lstlisting` 数量一致，防止静默错配。

运行：

```bash
npm run build:tex
```

输出文件为 `exports/hispark-documentation-standard-tex.zip`。归档包含 MyST 生成的 `.tex` 文件及构建所需资源，可用于版式审查和二次排版。

运行：

```bash
npm run build:pdf
```

MyST 使用工程内的 `plain_latex_book_zh` 模板生成 LaTeX，并调用本地 XeLaTeX 工具链生成 `exports/hispark-documentation-standard.pdf`。模板基于 `ctexbook`，关闭隐式字体集，按上述显式方案选择字体。

## 自动化构建三套 PDF

在 Ubuntu 24.04 上先运行 `bash scripts/install_pdf_dependencies.sh`。脚本安装指定版本的 TeX 主包和开源字体，并归档完整包版本清单；它需要 apt 安装权限。字体上游分别为 [Noto CJK](https://github.com/notofonts/noto-cjk) 和 [Liberation Fonts](https://github.com/liberationfonts/liberation-fonts)，所用 Ubuntu 包在 `/usr/share/doc/` 提供版权和许可文本。

```bash
PDF_FONT_PROFILE=open python3 scripts/build_pdfs.py
```

该入口从隔离源快照构建 Annotated、Core 和基础阅读摘编，不使用 `exports/` 中的旧文件。默认是开发快照；正式 Release 由工作流传入 `--channel release` 和经过标签检查的提交。输出位于 `_build/pdf-release/`，日志位于 `_build/pdf-evidence/`。自动检查覆盖字体嵌入、正文内链、版本/提交身份、源文件摘要和产物完整性；视觉排版仍需人工抽查。
