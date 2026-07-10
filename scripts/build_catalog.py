#!/usr/bin/env python3
"""校验 skill 写法约定，并把 skill 目录表生成进 README.md 的标记段。

用法:
    python3 scripts/build_catalog.py          # 校验 + 刷新 README 的 skill 列表
    python3 scripts/build_catalog.py --check  # 只校验，并检查 README 列表是否过期（CI 用）

约定（违反即报错，退出码 2）:
  - plugins/<领域>/skills/<skill>/SKILL.md 必须有 frontmatter，含 name 和 description
  - name 必须与所在目录名一致
  - description 必须含触发语「适用场景：」（或英文 "Use when"）
  - 正文必须有「## 用法」小节
  - plugins/ 下每个领域目录必须已在 .claude-plugin/marketplace.json 登记，反之亦然
  - plugin.json 的 name 必须与领域目录名一致
  - README.md 必须含 <!-- catalog:start --> / <!-- catalog:end --> 标记对

--check 模式下若 README 标记段与生成结果不一致，退出码 1。
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MARK_START = "<!-- catalog:start -->"
MARK_END = "<!-- catalog:end -->"
TRIGGER_RE = re.compile(r"适用场景[：:]|\buse when\b", re.IGNORECASE)
USAGE_HEADING_RE = re.compile(r"^##\s*用法\s*$")
FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)")


def parse_frontmatter(text, errors, where):
    """返回 (frontmatter dict, 正文)。只支持 `key: value` 与缩进续行的简单 YAML。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        errors.append(f"{where}: 缺少 frontmatter（--- 包裹的元数据块）")
        return {}, text
    fm = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z][\w-]*\s*:", line):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val in (">", ">-", ">+", "|", "|-", "|+"):
                val = ""  # YAML 折叠/字面量标记，真实值在续行里
            elif len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            fm[key] = val
        elif key and line[:1] in (" ", "\t"):
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, text[m.end():]


def split_desc(desc):
    """把 description 拆成（功能, 适用场景）。调用前须保证 TRIGGER_RE 能匹配。"""
    m = TRIGGER_RE.search(desc)
    func = desc[: m.start()].strip(" 。.;；,，")
    trig = re.sub(r"^适用场景[：:]\s*", "", desc[m.start():]).strip()
    return func or "—", trig or "—"


def extract_usage(body):
    """返回「## 用法」小节内容；缺失或为空返回 None。忽略代码围栏内的假标题。"""
    lines = body.splitlines()
    in_fence = False
    fence_marker = ""
    start = None
    for i, line in enumerate(lines):
        fence = FENCE_RE.match(line)
        if fence:
            if not in_fence:
                in_fence, fence_marker = True, fence.group(1)[:3]
            elif fence.group(1).startswith(fence_marker):
                in_fence = False
            continue
        if in_fence:
            continue
        if start is None:
            if USAGE_HEADING_RE.match(line):
                start = i + 1
        elif re.match(r"^#{1,2}\s", line):
            return "\n".join(lines[start:i]).strip() or None
    if start is None:
        return None
    return "\n".join(lines[start:]).strip() or None


def cell(text):
    """把多行文本压成 Markdown 表格单元格。"""
    lines = [ln.strip() for ln in text.replace("|", "\\|").splitlines() if ln.strip()]
    return "<br>".join(lines) or "—"


def collect(errors):
    """遍历 plugins/，返回 [(领域名, 领域描述, [(skill名, 相对路径, 功能, 场景, 用法), ...]), ...]"""
    mk_path = ROOT / ".claude-plugin" / "marketplace.json"
    registered = set()
    try:
        mk = json.loads(mk_path.read_text(encoding="utf-8-sig"))
        entries = mk.get("plugins", [])
        registered = {p.get("name") for p in entries if isinstance(p, dict) and p.get("name")}
        nameless = len(entries) - sum(1 for p in entries if isinstance(p, dict) and p.get("name"))
        if nameless:
            errors.append(f"marketplace.json: {nameless} 个 plugin 登记项缺少 name")
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"{mk_path.relative_to(ROOT)}: 读取失败（{e}）")

    plugins_dir = ROOT / "plugins"
    domain_dirs = (
        sorted(d for d in plugins_dir.iterdir() if d.is_dir())
        if plugins_dir.is_dir()
        else []
    )
    domain_names = {d.name for d in domain_dirs}
    for name in sorted(registered - domain_names):
        errors.append(f"marketplace.json 登记了 {name}，但 plugins/{name}/ 不存在")
    for name in sorted(domain_names - registered):
        errors.append(f"plugins/{name}/ 存在，但未在 marketplace.json 登记")

    domains = []
    for d in domain_dirs:
        pj_path = d / ".claude-plugin" / "plugin.json"
        pdesc = ""
        if pj_path.is_file():
            try:
                pj = json.loads(pj_path.read_text(encoding="utf-8-sig"))
                if pj.get("name") != d.name:
                    errors.append(
                        f'{pj_path.relative_to(ROOT)}: name "{pj.get("name")}" 与目录名 {d.name} 不一致'
                    )
                pdesc = pj.get("description", "")
            except json.JSONDecodeError as e:
                errors.append(f"{pj_path.relative_to(ROOT)}: JSON 解析失败（{e}）")
        else:
            errors.append(f"plugins/{d.name}/: 缺少 .claude-plugin/plugin.json")

        rows = []
        skills_dir = d / "skills"
        for s in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
            sk = s / "SKILL.md"
            rel = sk.relative_to(ROOT).as_posix()
            if not sk.is_file():
                errors.append(f"{s.relative_to(ROOT)}/: 缺少 SKILL.md")
                continue
            fm, body = parse_frontmatter(sk.read_text(encoding="utf-8-sig"), errors, rel)
            name, desc = fm.get("name", ""), fm.get("description", "")
            if not name:
                errors.append(f"{rel}: frontmatter 缺少 name")
            elif name != s.name:
                errors.append(f'{rel}: name "{name}" 与目录名 {s.name} 不一致')
            if not desc:
                errors.append(f"{rel}: frontmatter 缺少 description")
                func = trig = "—"
            elif not TRIGGER_RE.search(desc):
                errors.append(f'{rel}: description 缺少触发语（「适用场景：」或 "Use when"）')
                func, trig = desc, "—"
            else:
                func, trig = split_desc(desc)
            usage = extract_usage(body)
            if usage is None:
                errors.append(f'{rel}: 正文缺少「## 用法」小节（或小节为空）')
                usage = f"`/{d.name}:{s.name}`"
            rows.append((s.name, rel, func, trig, usage))
        domains.append((d.name, pdesc, rows))
    return domains


def render_block(domains):
    """生成 README 标记段内的目录内容（不含标记本身）。"""
    total = sum(len(rows) for _, _, rows in domains)
    lines = [f"共 {len(domains)} 个领域 / {total} 个 skill。"]
    if total == 0:
        lines += ["", "*（暂无 skill —— 引入第一个后运行 `python3 scripts/build_catalog.py` 刷新）*"]
    for dname, pdesc, rows in domains:
        lines += ["", f"### {dname}（{len(rows)} 个）", ""]
        if pdesc:
            lines += [f"> {pdesc}", ""]
        lines += ["| Skill | 功能 | 适用场景 | 用法 |", "|---|---|---|---|"]
        for sname, rel, func, trig, usage in rows:
            lines.append(f"| [{sname}]({rel}) | {cell(func)} | {cell(trig)} | {cell(usage)} |")
    return "\n".join(lines)


def inject(readme_text, block, errors):
    """把 block 替换进 README 的标记对之间，返回完整新文本。"""
    start = readme_text.find(MARK_START)
    end = readme_text.find(MARK_END)
    if start == -1 or end == -1 or end < start:
        errors.append(f"README.md: 缺少（或错序）标记对 {MARK_START} … {MARK_END}")
        return readme_text
    head = readme_text[: start + len(MARK_START)]
    tail = readme_text[end:]
    return f"{head}\n{block}\n{tail}"


def main():
    check = "--check" in sys.argv[1:]
    errors = []
    domains = collect(errors)
    if README.is_file():
        readme_text = README.read_text(encoding="utf-8-sig")
    else:
        errors.append("README.md 不存在")
        readme_text = ""
    content = inject(readme_text, render_block(domains), errors)

    if errors:
        print(f"✘ 发现 {len(errors)} 个约定违规：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)

    data = content.encode("utf-8")
    existing = README.read_bytes() if README.is_file() else None
    if check:
        if existing != data:
            print("✘ README 的 skill 列表已过期，请运行 python3 scripts/build_catalog.py 刷新", file=sys.stderr)
            sys.exit(1)
        print("✔ 约定校验通过，README 的 skill 列表已是最新")
    elif existing == data:
        print("✔ 约定校验通过，README 的 skill 列表无变化")
    else:
        README.write_bytes(data)
        print("✔ 约定校验通过，已刷新 README.md 的 skill 列表")


if __name__ == "__main__":
    main()
