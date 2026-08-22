"""Lightweight source-level checks for the CGE-Core Jupyter Book."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

DOCS = Path(__file__).resolve().parent
TOC = DOCS / "_toc.yml"
CONFIG = DOCS / "_config.yml"

errors: list[str] = []


def md_path(target: str) -> Path:
    p = Path(target)
    if p.suffix != ".md":
        p = p.with_suffix(".md")
    return p


def walk_toc(node, found: set[str]) -> None:
    if isinstance(node, dict):
        if "file" in node:
            found.add(node["file"])
        if "root" in node:
            found.add(node["root"])
        for value in node.values():
            walk_toc(value, found)
    elif isinstance(node, list):
        for item in node:
            walk_toc(item, found)


toc_data = yaml.safe_load(TOC.read_text(encoding="utf-8"))
toc_files: set[str] = set()
walk_toc(toc_data, toc_files)

# Every TOC target must exist.
for target in sorted(toc_files):
    path = DOCS / md_path(target)
    if not path.is_file():
        errors.append(
            f"TOC target does not exist: {target} -> {path.relative_to(DOCS)}"
        )

# Every documentation Markdown page should be in the TOC.
all_md = {
    str(p.relative_to(DOCS).with_suffix("")).replace("\\", "/")
    for p in DOCS.rglob("*.md")
    if "_build" not in p.parts
}
for target in sorted(all_md - toc_files):
    errors.append(f"Markdown page is not listed in _toc.yml: {target}.md")

# Check local {doc}`...` references.
doc_role = re.compile(r"\{doc\}`([^`]+)`")
for source in sorted(DOCS.rglob("*.md")):
    if "_build" in source.parts:
        continue
    text = source.read_text(encoding="utf-8")
    for raw in doc_role.findall(text):
        target = raw
        if "<" in raw and raw.endswith(">"):
            target = raw.rsplit("<", 1)[1][:-1].strip()

        if "://" in target:
            continue

        candidate = (source.parent / md_path(target)).resolve()
        try:
            candidate.relative_to(DOCS.resolve())
        except ValueError:
            errors.append(
                f"{source.relative_to(DOCS)}: doc target escapes docs/: {raw}"
            )
            continue

        if not candidate.is_file():
            errors.append(
                f"{source.relative_to(DOCS)}: broken doc target {raw!r} "
                f"(expected {candidate.relative_to(DOCS.resolve())})"
            )

# Guard against the delimiter mistake that previously broke theory math.
for source in [
    DOCS / "MODEL.md",
    *sorted((DOCS / "theory").glob("*.md")),
]:
    text = source.read_text(encoding="utf-8")
    if r"\[" in text or r"\]" in text or r"\(" in text or r"\)" in text:
        errors.append(
            f"{source.relative_to(DOCS)} contains backslash math delimiters; "
            "use $...$ or a fenced {math} directive."
        )

# Keep the site deliberately simple: no Sphinx Design grids or Mermaid.
for source in sorted(DOCS.rglob("*.md")):
    if "_build" in source.parts:
        continue
    text = source.read_text(encoding="utf-8")
    if "{grid}" in text or "{grid-item-card}" in text:
        errors.append(
            f"{source.relative_to(DOCS)} contains Sphinx Design grid markup."
        )
    if "{mermaid}" in text:
        errors.append(
            f"{source.relative_to(DOCS)} contains Mermaid markup."
        )

# The documentation should not configure a sidebar logo.
config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
if isinstance(config, dict) and config.get("logo"):
    errors.append("docs/_config.yml still configures a documentation logo.")

if errors:
    print("Documentation source checks FAILED:\n")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(
    f"Documentation source checks passed: "
    f"{len(toc_files)} TOC pages, {len(all_md)} Markdown pages."
)
