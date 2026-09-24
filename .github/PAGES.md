# GitHub Pages 发布

工作流 `pages.yml` 在 `main` 推送及手动触发时验证并部署；PR 只验证，不部署。main 内容发布到 `/dev/`；根地址和固定版本地址从已发布 Release 的已验证附件恢复，详见[发布与版本维护](RELEASING.md)。

- 使用锁定的 MyST 依赖，运行现有 `npm run check` 和全部 Python 测试。
- `scripts/build_pages.py` 在临时目录生成 Annotated HTML，严格检查构建和外链，并添加与正文分离的版本提示；`scripts/assemble_pages.py` 校验历史 Release 后组合完整站点。
- `BASE_URL` 使用仓库名，避免项目站点 CSS、脚本和页面链接丢失前缀。
- `_build/pages` 是实际上传的产物；各版本的 `build-manifest.json` 记录提交、运行身份和文件摘要，`deployment-manifest.json` 记录组合部署的全部文件，`versions.json` 列出可用版本。
- 每个已渲染页面同时发布原始 Markdown，例如 `preface.md`、`authoring.md`；另保留 `docs/preface.md`、`docs/part-2-authoring/06-authoring.md` 等源目录地址，以保留原文相对文件链接的路径上下文。短地址不改写原文中的相对链接；需要沿原文链接阅读时使用源目录地址。源格式的跨页锚点由文档生成器解析，纯文本端点不提供 HTML 的锚点跳转行为。
- 原文逐字节复制自同次构建的源快照，含 Front Matter 与指令，不是从 HTML 反向转换。`build-manifest.json` 的 `markdown_sources` 给出源路径、页面标识、两个发布地址及 SHA-256，文件摘要涵盖所有原文；缺页、重复映射、路径越界或目的文件冲突时构建失败。不发布未渲染页面或整个仓库。
- 构建/检查/证据归档失败则不部署。日志与清单归档为 Actions artifact。
- 此发布范围为 HTML 和 Markdown 原文；不在公开 Runner 中复制商业字体，也不发布旧 PDF。PDF/TeX 下载按钮仅在临时站点配置中移除，不修改规范正文、Core 范围或本地导出配置。

本地复现（先按仓库 README 安装依赖）：

```bash
npm ci
npm run check
python3 -m unittest discover -s scripts -p 'test_*.py'
BASE_URL=/hispark-documentation-standard python3 scripts/build_pages.py
```

站点验证不等于规范的人工批准，也不证明采用项目的 SDK 或硬件行为。外链检查依赖外部服务，失败时查归档日志后修复或重跑，不跳过检查。

## 已删除页面的兼容入口

`verification-and-adoption/`、`verification-and-adoption.md` 和
`docs/handbook/verification-and-adoption.md` 只发布删除提示，链接到验证与测试、治理与持续维护和迁移方案。原手册已从正文、导航和 PDF/TeX 导出清单移除；历史内容可从 Git 恢复。

保留页由发布脚本生成，不属于规范正文，不进入搜索或 `markdown_sources` 原文清单；文件摘要仍纳入 `build-manifest.json`。构建时检查替代页面存在，测试覆盖三个旧地址、路径前缀和目的文件冲突。
