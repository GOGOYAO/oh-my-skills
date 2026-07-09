# oh-my-skills

个人 Claude Code skill 集合，以 **plugin marketplace** 形式管理：skill 按领域拆成多个 plugin，按需安装。

skill 来源两类：**自研**（从头设计）和 **借鉴**（从他人优秀 skill 一次性拷贝、按需改动、改名归化，之后与上游断开，不跟踪更新）。所有 skill 的出处与改动记录见 [INDEX.md](INDEX.md)。

## 安装使用

```shell
# 添加本 marketplace（本地路径或 GitHub repo 均可）
/plugin marketplace add /Users/ago/workspace/oh-my-skills

# 按领域安装 plugin
/plugin install <领域名>@oh-my-skills

# 调用 skill（带 plugin 命名空间）
/<领域名>:<skill-name>
```

推送到 GitHub 后，其他机器用 `/plugin marketplace add <owner>/oh-my-skills` 添加，`/plugin marketplace update` 拉取更新。

## 目录结构

```
oh-my-skills/
├── .claude-plugin/
│   └── marketplace.json      # marketplace 清单，登记所有领域 plugin
├── plugins/
│   └── <领域名>/             # 一个领域 = 一个 plugin
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/
│       │   └── <skill-name>/
│       │       └── SKILL.md
│       ├── agents/           # 按需扩展：subagent 定义
│       ├── commands/         # 按需扩展：flat .md 命令
│       └── hooks/            # 按需扩展：hooks.json
├── templates/
│   └── domain-plugin/        # 新建领域 plugin 时拷贝这个模板
├── INDEX.md                  # skill 索引：名字、领域、来源、license、改动
└── TODO.md                   # 待办（eval 体系等）
```

## 约定

### 新增领域 plugin

1. 拷贝 `templates/domain-plugin/` 到 `plugins/<领域名>/`，改 `plugin.json` 的 `name` 和 `description`
2. 在 `.claude-plugin/marketplace.json` 的 `plugins` 数组登记：
   ```json
   { "name": "<领域名>", "source": "<领域名>", "description": "..." }
   ```
   （`metadata.pluginRoot` 已设为 `./plugins`，`source` 直接写目录名）
3. 校验：`claude plugin validate . --strict`

### 引入借鉴 skill（checklist）

1. **拷贝**：把上游 skill 目录复制到目标领域 plugin 的 `skills/` 下
2. **改名**：目录名和 frontmatter `name` 改成符合本仓库命名的新名字（kebab-case，避免与上游及其他 plugin 撞名）
3. **改动**：按需修改内容；上游引用的相对路径、脚本一并检查
4. **记录**：在 [INDEX.md](INDEX.md) 登记上游 repo（带 commit SHA）、原名、license、改动说明；license 要求署名的在 skill 目录放 NOTICE
5. **校验**：`claude plugin validate . --strict`，并实际触发一次确认可用

### 命名

- marketplace / plugin / skill 名一律 kebab-case
- skill 的 `description` 是自动触发的依据，必须写清触发场景和关键词
