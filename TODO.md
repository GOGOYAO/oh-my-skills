# TODO

## Eval 体系（长期，暂不实现）

- [ ] 为核心 skill 配 eval。Claude Code CLI 已原生支持：`claude plugin eval <path|plugin@marketplace>`
  - 约定结构：plugin 内 `evals/**/case.yaml`，或 `evals/**/prompt.md` + `graders/*.md`
  - 跑分时会自动加一个 no-plugin baseline 对照组
- [ ] 借鉴 skill 改动后，用 eval 验证"改动没有破坏原有能力"

## 工程化

- [ ] CI：push 时跑 `python3 scripts/build_catalog.py --check`（写法约定 + README skill 列表是否过期）和 `claude plugin validate . --strict`（对 marketplace 和每个 plugin）
- [ ] 借鉴 skill 引入前的 license 检查清单化
