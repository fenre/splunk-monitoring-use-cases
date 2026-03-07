#!/usr/bin/env python3
"""
Replace '- **Monitoring type:** <anything>' in each UC block with the correct type
from monitoring_type_mapping.json. Run after build_monitoring_type_mapping.py.
"""
import json
import re
from pathlib import Path

USE_CASES_DIR = Path(__file__).resolve().parent
MAPPING_PATH = USE_CASES_DIR / "monitoring_type_mapping.json"


def process_file(filepath: Path, mapping: dict) -> int:
    content = filepath.read_text(encoding="utf-8")
    blocks = re.split(r"(?=### UC-\d+\.\d+\.\d+ · )", content)
    out = []
    updated = 0
    for block in blocks:
        if not block.strip():
            out.append(block)
            continue
        match = re.match(r"### UC-(\d+\.\d+\.\d+) · ([^\n]+)", block)
        if not match:
            out.append(block)
            continue
        uc_id = match.group(1)
        if uc_id not in mapping:
            out.append(block)
            continue
        new_type = mapping[uc_id]
        # Replace existing Monitoring type line (any value) with correct one
        pat = re.compile(r"^(-\s*\*\*Monitoring type:\*\*)\s*.+$", re.MULTILINE)
        new_block, n = pat.subn(r"\1 " + new_type, block, count=1)
        if n:
            updated += 1
        out.append(new_block)
    filepath.write_text("".join(out), encoding="utf-8")
    return updated


def main():
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    total = 0
    for md_file in sorted(USE_CASES_DIR.glob("cat-[0-9]*.md")):
        if md_file.name.startswith("cat-00"):
            continue
        n = process_file(md_file, mapping)
        total += n
        if n:
            print(f"  {md_file.name}: updated {n} use cases")
    print(f"\nTotal: updated {total} Monitoring type lines.")


if __name__ == "__main__":
    main()
