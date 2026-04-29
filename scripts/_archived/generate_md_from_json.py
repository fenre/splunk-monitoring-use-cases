#!/usr/bin/env python3
"""Generate .md companion files from UC JSON source-of-truth.

JSON is the single source of truth for all use case content. This script
reads every content/cat-*/UC-*.json and emits a corresponding UC-*.md
using a consistent template. The .md files are build artifacts — they
should never be hand-edited.

Usage:
    python3 scripts/generate_md_from_json.py          # generate all
    python3 scripts/generate_md_from_json.py --check   # CI mode: exit 1 if stale
    python3 scripts/generate_md_from_json.py --files UC-5.13.1.json UC-5.13.2.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
HEADER = "<!-- AUTO-GENERATED from {filename} — DO NOT EDIT -->\n"


def render_md(uc: dict, json_filename: str) -> str:
    """Render a UC dict to markdown string."""
    uc_id = uc.get("id", "")
    title = uc.get("title", "")
    criticality = uc.get("criticality", "")
    pillar = uc.get("splunkPillar", "")

    lines: list[str] = []
    lines.append(HEADER.format(filename=json_filename))

    # Frontmatter
    lines.append("---")
    lines.append(f'id: "{uc_id}"')
    lines.append(f'title: "{title}"')
    if criticality:
        lines.append(f'criticality: "{criticality}"')
    if pillar:
        lines.append(f'splunkPillar: "{pillar}"')
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# UC-{uc_id} \u00b7 {title}")
    lines.append("")

    # Description
    desc = uc.get("description", "")
    if desc:
        lines.append("## Description")
        lines.append("")
        lines.append(desc)
        lines.append("")

    # Value
    value = uc.get("value", "")
    if value:
        lines.append("## Value")
        lines.append("")
        lines.append(value)
        lines.append("")

    # Implementation (short)
    impl = uc.get("implementation", "")
    if impl:
        lines.append("## Implementation")
        lines.append("")
        lines.append(impl)
        lines.append("")

    # Detailed Implementation
    detailed = uc.get("detailedImplementation", "")
    if detailed:
        lines.append("## Detailed Implementation")
        lines.append("")
        lines.append(detailed)
        lines.append("")

    # SPL
    spl = uc.get("spl", "")
    if spl:
        lines.append("## SPL")
        lines.append("")
        lines.append("```spl")
        lines.append(spl)
        lines.append("```")
        lines.append("")

    # CIM SPL
    cim_spl = uc.get("cimSpl", "")
    if cim_spl:
        lines.append("## CIM SPL")
        lines.append("")
        lines.append("```spl")
        lines.append(cim_spl)
        lines.append("```")
        lines.append("")

    # Visualization
    viz = uc.get("visualization", "")
    if viz:
        lines.append("## Visualization")
        lines.append("")
        lines.append(viz)
        lines.append("")

    # References
    refs = uc.get("references", [])
    if refs:
        lines.append("## References")
        lines.append("")
        for ref in refs:
            ref_title = ref.get("title", ref.get("url", ""))
            ref_url = ref.get("url", "")
            if ref_url:
                lines.append(f"- [{ref_title}]({ref_url})")
            elif ref_title:
                lines.append(f"- {ref_title}")
        lines.append("")

    return "\n".join(lines)


def find_uc_json_files(specific_files: list[str] | None = None) -> list[Path]:
    """Find UC JSON files to process."""
    if specific_files:
        resolved = []
        for f in specific_files:
            p = Path(f)
            if not p.is_absolute():
                p = REPO_ROOT / p
            if p.exists():
                resolved.append(p)
            else:
                for match in CONTENT_DIR.rglob(p.name):
                    resolved.append(match)
        return sorted(resolved)

    return sorted(CONTENT_DIR.rglob("UC-*.json"))


def process_file(json_path: Path, check_only: bool = False) -> bool:
    """Process a single JSON file. Returns True if up-to-date."""
    with open(json_path, "r", encoding="utf-8") as fh:
        uc = json.load(fh)

    md_content = render_md(uc, json_path.name)
    md_path = json_path.with_suffix(".md")

    if check_only:
        if not md_path.exists():
            print(f"MISSING: {md_path.relative_to(REPO_ROOT)}")
            return False
        existing = md_path.read_text(encoding="utf-8")
        if existing != md_content:
            print(f"STALE:   {md_path.relative_to(REPO_ROOT)}")
            return False
        return True

    md_path.write_text(md_content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate .md files from UC JSON source-of-truth."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: exit 1 if any .md is missing or stale.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        metavar="FILE",
        help="Process only specific JSON files.",
    )
    args = parser.parse_args()

    json_files = find_uc_json_files(args.files)
    if not json_files:
        print("No UC JSON files found.")
        return 1 if args.check else 0

    stale_count = 0
    for jf in json_files:
        ok = process_file(jf, check_only=args.check)
        if not ok:
            stale_count += 1

    if args.check:
        total = len(json_files)
        if stale_count:
            print(f"\n{stale_count}/{total} .md files are stale or missing.")
            return 1
        print(f"All {total} .md files are up-to-date.")
        return 0

    print(f"Generated {len(json_files)} .md files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
