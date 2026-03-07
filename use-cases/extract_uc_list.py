#!/usr/bin/env python3
"""
Parse cat-XX-*.md files and extract UC id, title, and first line of Value
into use-cases/uc_list.json.
"""
import json
import re
from pathlib import Path

USE_CASES_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = USE_CASES_DIR / "uc_list.json"

# Match ### UC-X.Y.Z · Title (optional spaces around ·)
UC_HEADER_RE = re.compile(r"^###\s+UC-(\d+(?:\.\d+)*)\s*[·]\s*(.+)$", re.MULTILINE)
# Match - **Value:** optional rest of line
VALUE_RE = re.compile(r"^-\s*\*\*Value:\*\*\s*(.*)$", re.MULTILINE)


def parse_file(path: Path) -> list[tuple[str, str, str]]:
    """Parse a single cat-XX-*.md file. Returns list of (uc_id, title, value)."""
    content = path.read_text(encoding="utf-8")
    results = []
    for header_match in UC_HEADER_RE.finditer(content):
        uc_id = header_match.group(1)  # e.g. "1.1.1", "2.1.1"
        title = header_match.group(2).strip()
        # Find - **Value:** after this header (before next ###)
        value_match = VALUE_RE.search(content, header_match.end())
        if not value_match:
            value = ""
        else:
            rest = value_match.group(1).strip()
            value = rest.split("\n")[0].strip() if rest else ""
            if not value:
                end_of_match = value_match.end()
                next_nl = content.find("\n", end_of_match)
                if next_nl != -1:
                    value = content[end_of_match:next_nl].strip()
        results.append((uc_id, title, value))
    return results


def main():
    uc_list = {}
    for md_file in sorted(USE_CASES_DIR.glob("cat-*.md")):
        name = md_file.name
        if name.startswith("cat-00"):
            continue
        # cat-01-... -> 1, cat-20-... -> 20
        cat_match = re.match(r"cat-(\d+)-", name)
        if not cat_match:
            continue
        for uc_id, title, value in parse_file(md_file):
            uc_list[uc_id] = {"title": title, "value": value}

    USE_CASES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(uc_list, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(uc_list)} use cases to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
