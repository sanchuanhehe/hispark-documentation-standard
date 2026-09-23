# GitHub Pages 发布

工作流 `pages.yml` 在 `main` 推送及手动触发时验证并发布；PR 只验证，不部署。

- 使用锁定的 MyST 依赖，运行现有 `npm run check` 和全部 Python 测试。
- `scripts/build_pages.py` 在临时目录生成 Annotated HTML，严格检查构建和外链。
- `BASE_URL` 使用仓库名，避免项目站点 CSS、脚本和页面链接丢失前缀。
- `_build/pages` 是实际上传的产物；`build-manifest.json` 记录提交、运行身份和文件摘要。
- 构建/检查/证据归档失败则不部署。日志与清单归档为 Actions artifact。
- 此发布范围仅为 HTML；不在公开 Runner 中复制商业字体，也不发布旧 PDF。PDF/TeX 下载按钮仅在临时站点配置中移除，不修改规范正文、Core 范围或本地导出配置。

本地复现（先按仓库 README 安装依赖）：

```bash
npm ci
npm run check
python3 -m unittest discover -s scripts -p 'test_*.py'
BASE_URL=/hispark-documentation-standard python3 scripts/build_pages.py
```

站点验证不等于规范的人工批准，也不证明采用项目的 SDK 或硬件行为。外链检查依赖外部服务，失败时查归档日志后修复或重跑，不跳过检查。
