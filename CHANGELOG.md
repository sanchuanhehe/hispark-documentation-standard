# Changelog

本文件记录对使用者有影响的变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [Unreleased]

## [0.1.5] - 2026-09-24

### Changed

- Present normative keywords as Chinese terms followed by BCP 14 keywords, such as 必须（MUST） and 不得（MUST NOT）, throughout the standard and reading extracts without changing requirement strength.
- Clarify the keyword table and reading guidance while preserving the original BCP 14 declaration and the Annotated/Core content boundaries.

### Added

- Check Chinese/English keyword pairs during source validation and add regression tests for negative keywords, literal code, and both document profiles.

## [0.1.4] - 2026-09-24

这是本仓库首个带 Git 标签的发布基线，包含此前已维护的规范及配套工具。不追溯虚构 v0.1.0–v0.1.3 发布；此前页面中的 V1.2 和构建包中的 1.1.0 是未统一的内部标识，不代表已有正式 Release。

### Added

- 提供基于 Diátaxis 的文档规范、Annotated/Core 构建和基础阅读摘编，以及写作、评审、验证、维护四个配套 Skills。
- 增加发布 Action：核对版本和标签，执行文档门禁，打包站点与 Skills，并从本文件生成 Release 说明。
- 提供固定版本网站、独立开发版入口、历史版本选择和页面版本提示；Release 附件保存已验证的站点产物及 SHA-256 校验值。
- 支持 Markdown 原文直链和原始目录路径访问，部署清单记录文档与产物身份。

### Changed

- 以 VERSION 为版本号来源，统一构建包、首页、阅读摘编和部署清单；版本或发布日期漂移阻断检查。
- 前言和第 1–3 章位于导航前部，其余入口按写作、审查与维护任务组织。
- 根站点展示最新稳定版，main 更新只进入开发版；历史发布从已验证附件恢复，不随 main 重新构建。
- 明确快速入门逐叶预算、验证边界、报告契约、历史债务和失败传播等要求，并同步配套 Skills。

### Removed

- 删除《验证与接入手册：模板和参考实现》及其导航引用；旧网址保留删除提示和相关章节入口。
- 移除首页和摘编中的旧试行版本标识。

### Fixed

- 修复 PDF 正文内链目标，并通过自动检查验证实际跳转。
- 补齐文档导航、原文发布覆盖和页面删除兼容入口的回归测试。

[Unreleased]: https://github.com/sanchuanhehe/hispark-documentation-standard/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/sanchuanhehe/hispark-documentation-standard/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/sanchuanhehe/hispark-documentation-standard/releases/tag/v0.1.4
