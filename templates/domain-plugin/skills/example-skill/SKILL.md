---
name: example-skill
description: 一句话说明这个 skill 做什么。适用场景：当用户提到 X、需要 Y 时使用。
---

# example-skill

## 用法

`/<plugin-name>:example-skill <参数>`

示例：`/<plugin-name>:example-skill foo`

## 指令

这里是 skill 正文：写给 Claude 的操作指令。

写法约定（`scripts/build_catalog.py` 会强制校验）：

- frontmatter `name` 必须与目录名一致（kebab-case）
- `description` 必须含「适用场景：」触发语（借鉴的英文 skill 可用 "Use when"），Claude 靠它决定是否自动触发
- 「## 用法」小节必须存在（调用方式 + 最小示例），会被抽取进 README 的 skill 列表
- 辅助材料（reference.md、scripts/ 等）放本目录下，正文中引用
