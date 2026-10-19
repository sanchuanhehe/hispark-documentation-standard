# 发布与版本维护

## 版本身份

`VERSION` 是规范发布版本的唯一来源，格式为 `MAJOR.MINOR.PATCH`，Git 标签为 `vMAJOR.MINOR.PATCH`。`package.json`、锁文件和首页是受检查的副本；发布日期来自 `CHANGELOG.md` 对应条目，并与首页及导出配置一致。`myst.yml` 的顶层 `version: 1`、Profile 的 `version` 和部署清单的 `schema_version` 是各自格式版本，不是规范版本。

修改规范、Skills 或工具后，先在 Changelog 的 `Unreleased` 中记录用户可见影响。发布时按 SemVer 决定版本，将这些条目整理到带日期的新版本下，使用 Added、Changed、Deprecated、Removed、Fixed、Security 中适用的分类。不要用提交日志替代 Changelog，不修改已发布版本记录来隐藏兼容性变化。当前从 `v0.1.4` 建立首个带标签基线，不补造历史 Release。

## 发布步骤

以下命令从仓库根目录运行，需要有该仓库推送及发布权限，不需要系统管理员权限。

1. 更新 `VERSION`、包版本副本、首页版本/日期和 `myst.yml` 的项目日期，整理 `CHANGELOG.md` 的发布条目和比较链接。
2. 执行 `npm ci`、`npm run check` 及 `python3 -m unittest discover -s scripts -p 'test_*.py'`；通过 PR 合入 main。
3. 对已合入且验证通过的提交创建标签并推送：

   ```bash
   git tag -a vMAJOR.MINOR.PATCH <verified-commit> -m "Release vMAJOR.MINOR.PATCH"
   git push origin vMAJOR.MINOR.PATCH
   ```

4. `release.yml` 检查标签/版本/提交一致且属于 main，复用全部文档检查，严格构建根地址与固定版本地址，以及 Annotated、Core、基础阅读摘编三套 PDF。CI 显式使用开源字体方案，不下载或复制商业字体；PDF 封面标明字体与版本身份。所有 PDF 通过内链和实际嵌入字体审计后，再核对网站与 PDF 的源文件摘要一致。
5. 验证证据归档及附件上传全部成功后，才将 draft 发布为正式 Release。然后显式触发 `pages.yml`，不依赖 GITHUB_TOKEN 创建的 Release 自动触发另一工作流。
6. 核对 Release、Pages 工作流、线上 `versions.json`、版本目录的 `build-manifest.json` 以及 `deployment-manifest.json`。只有 Release 已创建不代表网站已部署。

Release 附件包含 `site-vX.Y.Z.tar.gz`、`skills-vX.Y.Z.zip`、三份带版本号的 PDF、各自的 `.links.json`、`pdf-manifest.json` 和覆盖上述文件的 `SHA256SUMS`。发布摘要仍直接取自 Changelog。缺 PDF、缺验证清单、版本/提交不符、源文件漂移、字体不符、链接失败或上传失败均阻断正式发布。构建过程有进度心跳和超时子进程组清理，日志和环境证据归档到 Actions。

失败时停止发布或部署，不关闭严格检查。已经公开的标签和附件不覆盖、不重写；修复后使用新版本。若仅 Pages 部署失败，修复基础设施后重跑 Pages，仍使用原发布附件。失败留下的 draft 需先核对标签、提交和资产完整性，再由维护者明确清理或继续；Action 不自动覆盖 draft 或已有 Release。

## 网站地址与回滚

- `/hispark-documentation-standard/`：语义版本最大的正式 Release；保留已有章节及 Markdown 入口。
- `/hispark-documentation-standard/v0.1.4/`：对应发布的固定快照。未来版本按标签保留目录。
- `/hispark-documentation-standard/dev/`：main 的开发快照，显式标为非正式发布。
- `versions.json`：最新稳定版本、历史版本、对应提交和地址。
- `/hispark-documentation-standard/versions/`：供读者选择历史版本的入口，各页面页脚均提供链接。
- 新构建快照中的 `changelog/`：从同提交 `CHANGELOG.md` 生成的更新记录页面；`changelog.md` 和 `CHANGELOG.md` 为逐字节一致的原文。规范章节与 PDF 正文不混入发布记录。
- 新正式版本的页脚提供对应版本三套 PDF 的 Release 下载入口。开发版不指向尚未发布或旧版本的 PDF。
- `deployment-manifest.json`：组合部署中全部文件的摘要及开发版/发布版身份。

后续部署从 Release 附件恢复所有历史站点，不用新工具链重新构建旧版。每个附件必须通过 SHA-256、文件覆盖、内容身份、标签提交及路径校验；缺失或损坏均阻断整个部署。当前根目录的 `build-manifest.json` 继续描述稳定版本自身，整个组合站点以 `deployment-manifest.json` 为准。

旧版发布产物不写入 Git 分支，不依赖会过期的 Actions artifacts；不要删除历史 Release 附件。发布序列只接受稳定三段版本；预发布标签暂不支持。回滚可先将用户引导到指定旧版本地址；改变默认稳定版本策略需要单独评审，不移动已有标签。

Pages 环境只需允许 main 部署；Release 工作流本身不直接访问 Pages 环境。Release 的写权限仅在发布 job 开放；PR 不发布，也不读取写入凭据。工作流级串行部署防止多个组合产物交叉覆盖。

版本标识使用主题原生页眉/页脚组件生成，不修改规范 Markdown 原文。跨版本地址由 `SITE_ORIGIN`（默认当前公开域名）和仓库路径组合；正式发布时不要使用本机预览域名。规范外链在加入跨版本界面前完整检查，跨版本入口在最终组合产物中检查，避免将尚未发布的网址误当成规范外链或忽略真正的断链。

Changelog 的 GitHub 比较链接可能指向 PR 尚未创建的发布标签，因此它作为发布元数据在规范外链检查之后加入；页面仍参与严格 HTML 构建和原文覆盖检查。PDF 下载链接由版本和固定附件名生成，附件缺失会阻断发布。历史版本不补写新页面或新下载链接。
