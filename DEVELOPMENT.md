# 开发指南

维护者视角的完整规范：如何新增领域、开发或引入 skill。约定由 `scripts/build_catalog.py` 强制校验；给 agent 的精简版硬约束在 [CLAUDE.md](CLAUDE.md)。

## 仓库结构

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
├── scripts/
│   └── build_catalog.py      # 校验写法约定 + 生成 README 的 skill 列表（--check 供 CI 用）
├── README.md                 # 使用者文档；skill 列表在标记段内，为生成物
├── INDEX.md                  # 引入台账：来源、上游、license、改动
├── CLAUDE.md                 # 给维护 agent 的硬约束
├── DEVELOPMENT.md            # 本文件
└── TODO.md                   # 待办（eval 体系等）
```

## SKILL.md 写法约定（`build_catalog.py` 强制校验）

- frontmatter `name` 与目录名一致，kebab-case
- `description` 格式：**一句话功能。适用场景：当…时使用**（借鉴的英文 skill 可保留 "Use when…"）。Claude 靠它决定是否自动触发；README 列表的「功能」「适用场景」两列也从这里拆
- 正文必须有 **`## 用法`** 小节：调用方式 + 一个最小示例，会被抽进 README 列表的「用法」列

## 新增领域 plugin

1. 拷贝 `templates/domain-plugin/` 到 `plugins/<领域名>/`，改 `plugin.json` 的 `name`（= 目录名）和 `description`
2. 在 `.claude-plugin/marketplace.json` 的 `plugins` 数组登记：
   ```json
   { "name": "<领域名>", "source": "./plugins/<领域名>", "description": "..." }
   ```
   （`source` 使用以 `./` 开头的仓库相对路径）
3. 把模板里的 example-skill 换成真实 skill，走下面的收尾

## 开发自研 skill

在目标领域的 `skills/<skill-name>/` 下写 SKILL.md（模板见 `templates/domain-plugin/skills/example-skill/`），遵守写法约定，然后走收尾。

## 引入借鉴 skill（checklist）

1. **拷贝**：把上游 skill 目录复制到目标领域 plugin 的 `skills/` 下
2. **改名**：目录名和 frontmatter `name` 改成符合本仓库命名的新名字（kebab-case，避免与上游及其他 plugin 撞名）
3. **改造**：按需修改内容，并补齐写法约定（触发语 + `## 用法` 小节）；上游引用的相对路径、脚本一并检查
4. **记录**：在 [INDEX.md](INDEX.md) 登记上游 repo（带 commit SHA）、原名、license、改动说明；license 要求署名的在 skill 目录放 NOTICE
5. 走下面的收尾

## 收尾（每次改动 skill 后必做）

1. `python3 scripts/build_catalog.py` —— 校验约定 + 刷新 README 的 skill 列表
2. `claude plugin validate .` 与 `claude plugin validate plugins/<领域名>` —— 校验 marketplace / plugin manifest
3. 实际触发一次 skill 确认可用
