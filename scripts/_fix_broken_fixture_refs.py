#!/usr/bin/env python3
"""One-off: clear broken fixtureRef values and mark as pending."""
import json
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"

fixed = 0
for uc_path in sorted(CONTENT_DIR.rglob("UC-*.json")):
    data = json.loads(uc_path.read_text(encoding="utf-8"))
    ct = data.get("controlTest")
    if not isinstance(ct, dict):
        continue
    ref = ct.get("fixtureRef", "")
    if ref and not (PROJECT_ROOT / ref).exists():
        ct["fixtureRef"] = ""
        ct["fixtureStatus"] = "pending"
        uc_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        fixed += 1

print(f"Fixed {fixed} broken fixtureRef(s).")
