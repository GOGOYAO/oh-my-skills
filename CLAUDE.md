# 维护协议

本 repo 是个人 Claude Code skill 的 plugin marketplace（一个领域 = 一个 plugin）。动 `plugins/` 下任何内容前，先读 [DEVELOPMENT.md](DEVELOPMENT.md) 并遵守其中的写法约定和流程。

硬约束：

- README.md 中 `<!-- catalog:start -->` … `<!-- catalog:end -->` 标记段是生成物，**勿手改**
- 借鉴引入的 skill 必须在 [INDEX.md](INDEX.md) 登记出处（上游 repo + commit、原名、license、改动）
- 每次改动 skill 后收尾：`python3 scripts/build_catalog.py` && `claude plugin validate .` 与目标领域的 `claude plugin validate plugins/<领域名>`
