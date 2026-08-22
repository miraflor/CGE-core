"""Lightweight source-level checks for the CGE-Core Jupyter Book."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
errors: list[str] = []


def md_path(target: str) -> Path:
    p = Path(target)
    return p if p.suffix == ".md" else p.with_suffix(".md")


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


toc_data = yaml.safe_load((DOCS / "_toc.yml").read_text(encoding="utf-8"))
toc_files: set[str] = set()
walk_toc(toc_data, toc_files)

for target in sorted(toc_files):
    path = DOCS / md_path(target)
    if not path.is_file():
        errors.append(f"TOC target does not exist: {target}")

all_md = {
    str(p.relative_to(DOCS).with_suffix("")).replace("\\", "/")
    for p in DOCS.rglob("*.md")
    if "_build" not in p.parts
}
for target in sorted(all_md - toc_files):
    errors.append(f"Markdown page is not listed in _toc.yml: {target}.md")

doc_role = re.compile(r"\{doc\}`([^`]+)`")
for source in sorted(DOCS.rglob("*.md")):
    if "_build" in source.parts:
        continue
    text = source.read_text(encoding="utf-8")
    for raw in doc_role.findall(text):
        target = (
            raw.rsplit("<", 1)[1][:-1].strip()
            if "<" in raw and raw.endswith(">")
            else raw
        )
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
                f"{source.relative_to(DOCS)}: broken doc target {raw!r}"
            )

for source in [DOCS / "MODEL.md", *sorted((DOCS / "theory").glob("*.md"))]:
    text = source.read_text(encoding="utf-8")
    if r"\[" in text or r"\]" in text or r"\(" in text or r"\)" in text:
        errors.append(
            f"{source.relative_to(DOCS)} contains backslash math delimiters."
        )

# The root-level Architecture page may use a relative source path, but the
# nested Theory page must use a source-root absolute path. In Sphinx, relative
# file references are resolved from the directory of the containing document.
approved_mermaid = {
    Path("architecture.md"): "diagrams/pycge-architecture.mmd",
    Path("theory/overview.md"): "/diagrams/standard-cge-theory.mmd",
}

for page, directive_source in approved_mermaid.items():
    page_path = DOCS / page
    source_path = DOCS / directive_source.lstrip("/")

    if not source_path.is_file():
        errors.append(
            f"Missing Mermaid source file: {directive_source.lstrip('/')}"
        )
        continue

    page_text = page_path.read_text(encoding="utf-8")
    directive = f"```{{mermaid}} {directive_source}"
    if directive not in page_text:
        errors.append(
            f"{page} must render Mermaid from {directive_source}."
        )

    source_root_path = "/" + directive_source.lstrip("/")
    if f"{{download}}`Download the .mmd source <{source_root_path}>`" not in page_text:
        errors.append(f"{page} must provide a Mermaid source download.")

    if f"```{{literalinclude}} {source_root_path}" not in page_text:
        errors.append(f"{page} must expose a copyable Mermaid source block.")

for source in sorted(DOCS.rglob("*.md")):
    if "_build" in source.parts:
        continue
    rel = source.relative_to(DOCS)
    text = source.read_text(encoding="utf-8")

    if "{grid}" in text or "{grid-item-card}" in text:
        errors.append(f"{rel} contains Sphinx Design grid markup.")

    if "{mermaid}" in text and rel not in approved_mermaid:
        errors.append(f"{rel} contains Mermaid outside approved diagram pages.")

    if "%%{init:" in text:
        errors.append(
            f"{rel} contains an inline Mermaid init block; configure Mermaid "
            "through docs/_config.yml instead."
        )

config = yaml.safe_load((DOCS / "_config.yml").read_text(encoding="utf-8"))
extra = (
    config.get("sphinx", {}).get("extra_extensions", [])
    if isinstance(config, dict)
    else []
)
sphinx_config = (
    config.get("sphinx", {}).get("config", {})
    if isinstance(config, dict)
    else {}
)

if "sphinxcontrib.mermaid" not in extra:
    errors.append("sphinxcontrib.mermaid is not enabled.")

if sphinx_config.get("mermaid_light_theme") != "neutral":
    errors.append("Set mermaid_light_theme to 'neutral'.")
if sphinx_config.get("mermaid_dark_theme") != "dark":
    errors.append("Set mermaid_dark_theme to 'dark'.")
if sphinx_config.get("mermaid_d3_zoom") is not True:
    errors.append("Enable mermaid_d3_zoom for diagram zoom and pan.")
if sphinx_config.get("mermaid_fullscreen") is not True:
    errors.append("Enable mermaid_fullscreen for full-screen inspection.")

if isinstance(config, dict) and config.get("logo"):
    errors.append("docs/_config.yml still configures a documentation logo.")

pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
if "sphinxcontrib-mermaid>=2.0.2,<3" not in pyproject:
    errors.append(
        "Documentation must use sphinxcontrib-mermaid>=2.0.2,<3."
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
