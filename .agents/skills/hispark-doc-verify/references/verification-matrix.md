# 验证与覆盖矩阵

本手册是执行摘要；按入口 Skill 的版本核对要求读取在线[第 9 章：验证与测试](https://github.sanchuanhehe.com/hispark-documentation-standard/validation-and-testing/)，其中第 9.4 节定义多变体矩阵与证据要求。

## 1. 证据等级

| 等级 | 能证明什么 | 不能据此声称什么 |
|---|---|---|
| Static | 源格式、元数据、链接目标、源码/配置一致性等静态事实 | 已构建、已运行 |
| Build | 在声明环境中配置、编译、链接或生成站点成功 | 目标行为已发生 |
| Smoke | 关键路径在目标环境启动并出现明确成功标记 | 全功能或全部边界已验证 |
| HIL | 指定硬件对象上的端到端可观察行为 | 未覆盖产品、版本或配置也适用 |

页面的 `verification_level` 不能高于证据。硬件行为通常需要 HIL；静态核对不能写成“已验证运行”。

## 2. 文档门禁

至少检查项目适用的以下内容：

- 源格式、结构化元数据、枚举值、术语和禁用写法；
- 使用锁定依赖的严格站点构建；
- 导航、内链、锚点、图片、资源和 Linux 路径大小写；
- 外链、上游版本、目标章节及内容漂移；
- API、Sample、Kconfig、Target、源码与文档映射；
- 代码片段、命令和关键预期输出；
- `get-started/` 页面/步骤/前置条件/分支/完成时间预算；
- 图片替代文本、孤立资源、重复哈希、文件限制、可编辑图源映射和敏感信息；
- 下游与上游疑似大段重复内容；
- 受影响 Sample 的构建、Smoke、HIL 和覆盖矩阵更新。

只修改文档的变更也必须进入适用门禁。

## 3. Sample 覆盖

对每个 Sample 至少记录：

- `sample_id`、源码、文档、Owner、产品、版本、Target 和单板；
- Build、Smoke、HIL、负向和版本覆盖状态；
- 成功判据、证据位置、执行日期和环境；
- `passed`、`failed`、`blocked`、`not_run` 或 `not_applicable`；
- 失败/阻塞原因、下一步与复核日期。

覆盖率使用明确分母：

`coverage = passed applicable cases / all applicable cases`

无法执行的适用场景仍进入分母并标为 `blocked` 或 `not_run`。不要用 Sample 数、页面数、脚本数或单一“测试通过”代替分层覆盖率。

Get Started 按正文[第 9.4 节](https://github.sanchuanhehe.com/hispark-documentation-standard/validation-and-testing/#id-9-4-get-started)逐叶/变体记录 source/static、environment、configure、build、flash、serial、Smoke、HIL。平台展示等价不代表验证等价，服务器非 HIL Build 不证明桌面 GUI、USB 或实板行为。可执行文档检查覆盖事实源到渲染、Runner 和证据验证，获取源与检出源不同则补齐镜像等价证明。

## 4. 失败关闭条件

以下任一情况不能判定为通过：

- 命令超时或非预期返回码；
- 设备无响应或串口静默；
- 缺少规范中声明的关键成功标记；
- 日志截断、环境信息缺失或证据无法归档；
- 使用了与页面不匹配的产品、版本、Target、单板或上游版本；
- 定时任务未执行却沿用上次绿色结果。

按正文[第 10.5—10.6 节](https://github.sanchuanhehe.com/hispark-documentation-standard/review-and-merge/#id-10-5)、[第 11.1 节](https://github.sanchuanhehe.com/hispark-documentation-standard/daily-ci/#id-11-1)，还需核对当前 known/new 发现、预期必需检查集合、取消/意外跳过、完整机器报告及其身份和计数、归档回执；增量信号不能代替总体门禁。正式限期例外不擦除发现或伪造通过。

## 5. 结果模板

| 声明/对象 | 范围 | 要求等级 | 实际检查 | 结果 | 证据 | 缺口/Owner |
|---|---|---|---|---|---|---|

结果摘要至少回答：

1. 哪些结论已经被什么证据支持；
2. 哪些只完成静态或构建验证；
3. 哪些失败、阻塞或未运行；
4. 是否满足页面状态和发布门槛；
5. 下一步由谁在何时补齐什么证据。
