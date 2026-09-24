# LaTeX 输出说明

正式 PDF 的中文使用 Microsoft YaHei（微软雅黑），英文、数字和代码使用 Arial。LaTeX 模板只声明字体家族名，不包含构建机绝对路径；构建脚本通过 Fontconfig 解析已安装字体，在临时构建目录创建字体链接，编译后立即移除。仓库和 LaTeX 导出包均不记录本机路径，也不复制受许可约束的字体文件。构建必须（MUST）在缺少字体时失败，不得静默换用替代字体。

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

MyST 使用工程内的 `plain_latex_book_zh` 模板生成 LaTeX，并调用本地 XeLaTeX 工具链生成 `exports/hispark-documentation-standard.pdf`。模板基于 `ctexbook` 和 TeX Live 自带 Fandol 字体，避免依赖单台计算机的私有中文字体。
