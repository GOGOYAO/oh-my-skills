# oh-my-skills

个人 Claude Code skill 集合，以 **plugin marketplace** 形式管理：skill 按领域拆成多个 plugin，按需安装。来源既有自研，也有从他人优秀 skill 借鉴改造的（出处见 [INDEX.md](INDEX.md)）。

## 安装（Claude Code）

```shell
# 添加本 marketplace（GitHub 或本地路径均可）
/plugin marketplace add GOGOYAO/oh-my-skills

# 按领域安装 plugin
/plugin install <领域名>@oh-my-skills

# 之后同步更新
/plugin marketplace update oh-my-skills
```

## 安装（Codex 独立 skill）

在 Codex 对话中输入：

```text
$skill-installer 安装 https://github.com/GOGOYAO/oh-my-skills/tree/main/plugins/education/skills/cmechina-course-runner
```

Claude Code marketplace 安装命令不等于 Codex skill 安装。安装后从 skill 选择器确认可见；若未出现，重启客户端。

## 使用

- Claude Code 手动调用：`/<领域名>:<skill-name> <参数>`，各 skill 的具体用法见下表
- Codex 独立 skill 调用：`$cmechina-course-runner 完成 <课程网址> 的全部小节视频及考试`。
- 自动触发：多数 skill 会被 Claude 根据对话内容自动使用，无需手动调用

## Skill 列表

<!-- 标记段内容由 scripts/build_catalog.py 生成，勿手改；改动 SKILL.md 后运行 python3 scripts/build_catalog.py 刷新 -->
<!-- catalog:start -->
共 1 个领域 / 1 个 skill。

### education（1 个）

> 教育课程学习辅助与流程自动化

| Skill | 功能 | 适用场景 | 用法 |
|---|---|---|---|
| [cmechina-course-runner](plugins/education/skills/cmechina-course-runner/SKILL.md) | 在 Chrome 中按真实播放状态推进 CMEChina 视频、考试与全部小节 | 当用户授权完成或继续 CMEChina 课程时使用。 | 安装后在客户端对话输入（将 `<课程网址>` 替换为 Chrome 中的实际 CMEChina 课程网址）：<br>- Claude Code plugin：`/education:cmechina-course-runner 完成 <课程网址> 的全部小节视频及考试`。<br>- Codex 独立 skill：`$cmechina-course-runner 完成 <课程网址> 的全部小节视频及考试`。<br>最小示例：`/education:cmechina-course-runner 完成 https://www.cmechina.net/cme/study2.jsp?course_id=202601015609&courseware_id=01 的全部小节视频及考试`；Codex 将开头替换为 `$cmechina-course-runner`。网址仅为格式示例，实际操作使用用户提供的课程。 |
<!-- catalog:end -->

## 开发

如何新增领域、开发或引入 skill、写法约定与出处台账，见 [DEVELOPMENT.md](DEVELOPMENT.md)。
