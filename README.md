# oh-my-skills

个人 Claude Code skill 集合，以 **plugin marketplace** 形式管理：skill 按领域拆成多个 plugin，按需安装。来源既有自研，也有从他人优秀 skill 借鉴改造的（出处见 [INDEX.md](INDEX.md)）。

## 安装

```shell
# 添加本 marketplace（GitHub 或本地路径均可）
/plugin marketplace add GOGOYAO/oh-my-skills

# 按领域安装 plugin
/plugin install <领域名>@oh-my-skills

# 之后同步更新
/plugin marketplace update oh-my-skills
```

## 使用

- 手动调用：`/<领域名>:<skill-name> <参数>`，各 skill 的具体用法见下表
- 自动触发：多数 skill 会被 Claude 根据对话内容自动使用，无需手动调用

## Skill 列表

<!-- 标记段内容由 scripts/build_catalog.py 生成，勿手改；改动 SKILL.md 后运行 python3 scripts/build_catalog.py 刷新 -->
<!-- catalog:start -->
共 1 个领域 / 1 个 skill。

### education（1 个）

> 教育课程学习辅助与流程自动化

| Skill | 功能 | 适用场景 | 用法 |
|---|---|---|---|
| [cmechina-course-runner](plugins/education/skills/cmechina-course-runner/SKILL.md) | 在 Chrome 中按真实播放状态推进 CMEChina 视频、考试与全部小节 | 当用户授权完成或继续 CMEChina 课程时使用。 | Claude Code：`/education:cmechina-course-runner 完成 https://www.cmechina.net/cme/study2.jsp?course_id=123&courseware_id=01 的全部小节`。Codex：`$cmechina-course-runner` 后提供课程网址及完成要求。 |
<!-- catalog:end -->

## 开发

如何新增领域、开发或引入 skill、写法约定与出处台账，见 [DEVELOPMENT.md](DEVELOPMENT.md)。
