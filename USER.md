# USER.md - About Your Human

## Stable preferences
- 用户偏好在有新任务时，优先从参考技能仓库检索可用 skill，再给出选项、风险提示与推荐安装项。
- 参考技能仓库：`https://github.com/VoltAgent/awesome-openclaw-skills`
- 默认视为用户正在操作自有项目仓库。
- 涉及 GitHub 提交/推送时，默认按用户既有偏好自动执行，不反复确认。
- workspace 相关归档/会话总结，默认采用顶层备份仓库提交流程（`/home/moonlight/.openclaw`），通过 `session-archives/*.md` 摘要迁移方式提交并推送。

## Interaction style preferences
- 用户希望优先寻找全局最优解。
- 当用户前提/假设可能不成立时，应主动指出并给更合理替代方案。
- 偏好直接、务实、少废话的协作风格。

## Boundaries
- USER.md 只保留用户长期偏好与协作习惯。
- 系统政策、工具 gate、运行协议不要堆到这里；应放到 `POLICIES/` 或对应规则文件中。
