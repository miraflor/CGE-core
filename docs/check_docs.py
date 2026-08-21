"""Lightweight source-level checks for the CGE-Core Jupyter Book.

This does not replace Sphinx/Jupyter Book.  It catches easy-to-introduce
documentation mistakes before the build is deployed: missing TOC files,
unlisted Markdown pages, broken {doc} targets, and incompatible directive
configuration.
"""
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

# 1. Every TOC target must exist.
for target in sorted(toc_files):
    path = DOCS / md_path(target)
    if not path.is_file():
        errors.append(f"TOC target does not exist: {target} -> {path.relative_to(DOCS)}")

# 2. Every documentation Markdown page should be in the TOC.
all_md = {
    str(p.relative_to(DOCS).with_suffix("")).replace("\\", "/")
    for p in DOCS.rglob("*.md")
    if "_build" not in p.parts
}
unlisted = sorted(all_md - toc_files)
for target in unlisted:
    errors.append(f"Markdown page is not listed in _toc.yml: {target}.md")

# 3. We use colon-fenced Sphinx Design cards; make sure parsing is enabled.
config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
extensions = (
    config.get("parse", {}).get("myst_enable_extensions", [])
    if isinstance(config, dict)
    else []
)
if "colon_fence" not in extensions:
    errors.append(
        "docs/intro.md uses ::::/::: directives but 'colon_fence' is not "
        "enabled in parse.myst_enable_extensions."
    )

# 4. Check local {doc}`...` references.
doc_role = re.compile(r"\{doc\}`([^`]+)`")
for source in sorted(DOCS.rglob("*.md")):
    if "_build" in source.parts:
        continue
    text = source.read_text(encoding="utf-8")
    for raw in doc_role.findall(text):
        # Explicit-title form: {doc}`label <target>`
        target = raw
        if "<" in raw and raw.endswith(">"):
            target = raw.rsplit("<", 1)[1][:-1].strip()

        if "://" in target:
            continue

        base = source.parent
        candidate = (base / md_path(target)).resolve()
        try:
            candidate.relative_to(DOCS.resolve())
        except ValueError:
            errors.append(f"{source.relative_to(DOCS)}: doc target escapes docs/: {raw}")
            continue

        if not candidate.is_file():
            errors.append(
                f"{source.relative_to(DOCS)}: broken doc target {raw!r} "
                f"(expected {candidate.relative_to(DOCS.resolve())})"
            )

# 5. Guard against the delimiter mistake that previously broke theory math.
for source in [
    DOCS / "MODEL.md",
    *sorted((DOCS / "theory").glob("*.md")),
]:
    text = source.read_text(encoding="utf-8")
    if r"\[" in text or r"\]" in text or r"\(" in text or r"\)" in text:
        errors.append(
            f"{source.relative_to(DOCS)} contains backslash math delimiters; "
            "use $...$ or a fenced {math} directive in this book."
        )

if errors:
    print("Documentation source checks FAILED:\n")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(
    f"Documentation source checks passed: "
    f"{len(toc_files)} TOC pages, {len(all_md)} Markdown pages."
)
