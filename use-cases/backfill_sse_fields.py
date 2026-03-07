#!/usr/bin/env python3
"""
Backfill SSE-derived fields into cat-10 use cases (10.9.4 through 10.9.1990).

Reads detection YAMLs from a local security_content clone in the same order as
import_sse_detections.py, extracts known_false_positives, references, type,
mitre_attack_id, security_domain, required_fields, and inserts them into the
corresponding UC blocks in cat-10-security-infrastructure.md.

Usage:
  python3 backfill_sse_fields.py --repo /path/to/security_content

Run from use-cases/ or pass repo path. Requires _sse_content or --repo.
"""

import argparse
import re
from pathlib import Path

# Reuse parser and iteration from import_sse_detections
from import_sse_detections import (
    get_existing_cat10_titles,
    detection_already_covered,
    parse_detection_yaml,
    SKIP_FOLDERS,
)

SCRIPT_DIR = Path(__file__).resolve().parent
CAT_10_PATH = SCRIPT_DIR / "cat-10-security-infrastructure.md"


def get_original_10_9_titles_only():
    """Return normalized titles only for UC-10.9.1, 10.9.2, 10.9.3 (the 3 samples). Used so we skip the same 3 as at import time."""
    titles = set()
    if not CAT_10_PATH.exists():
        return titles
    text = CAT_10_PATH.read_text(encoding="utf-8")
    for uc_id in ("10.9.1", "10.9.2", "10.9.3"):
        m = re.search(rf"### UC-{re.escape(uc_id)} · (.+?)(?:\n|$)", text)
        if m:
            t = m.group(1).strip().lower()
            t = re.sub(r"\s+", " ", t)
            titles.add(t)
    return titles


def iter_detection_yamls(repo_path):
    """Yield (uc_id, yaml_path) in same order as import_sse_detections (10.9.4, 10.9.5, ...)."""
    repo = Path(repo_path)
    detections_dir = repo / "detections"
    if not detections_dir.is_dir():
        return
    # Only skip the 3 original sample UCs (10.9.1–10.9.3), not the 1988 we added
    existing = get_original_10_9_titles_only()
    next_id = 4  # first new is 10.9.4
    for folder in sorted(detections_dir.iterdir()):
        if not folder.is_dir() or folder.name in SKIP_FOLDERS:
            continue
        for yf in sorted(folder.glob("*.yml")):
            det = parse_detection_yaml(yf)
            if not det:
                continue
            name = det.get("name") or yf.stem.replace("_", " ").title()
            if detection_already_covered(name, existing):
                continue
            yield f"10.9.{next_id}", yf
            next_id += 1


def md_line(key, value):
    """Format a single markdown field line."""
    if not value or (isinstance(value, list) and not value):
        return None
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    value = str(value).strip()
    if not value:
        return None
    # Escape pipe in value for markdown
    return f"- **{key}:** {value}"


def insert_fields_into_uc_block(block_text, kfp, refs, dtype, mitre, sdomain, reqf):
    """Insert new field lines before the final --- of the UC block. Skip if line already present."""
    lines = block_text.split("\n")
    new_lines = []
    if kfp and "**Known false positives:**" not in block_text:
        new_lines.append(md_line("Known false positives", kfp))
    if refs and "**References:**" not in block_text:
        ref_val = refs if isinstance(refs, str) else ", ".join(refs)
        new_lines.append(md_line("References", ref_val))
    if mitre and "**MITRE ATT&CK:**" not in block_text:
        new_lines.append(md_line("MITRE ATT&CK", ", ".join(mitre)))
    if dtype and "**Detection type:**" not in block_text:
        new_lines.append(md_line("Detection type", dtype))
    if sdomain and "**Security domain:**" not in block_text:
        new_lines.append(md_line("Security domain", sdomain))
    if reqf and "**Required fields:**" not in block_text:
        req_val = reqf if isinstance(reqf, str) else ", ".join(reqf)
        new_lines.append(md_line("Required fields", req_val))
    if not new_lines:
        return block_text
    # Find the last "---" in the block (closing the UC)
    insert_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "---":
            insert_idx = i
            break
    if insert_idx is None:
        return block_text
    # Insert before ---
    inserted = "\n".join(new_lines) + "\n\n"
    new_block = "\n".join(lines[:insert_idx]) + "\n" + inserted + "\n".join(lines[insert_idx:])
    return new_block


def main():
    ap = argparse.ArgumentParser(description="Backfill SSE fields into cat-10 10.9.x UCs.")
    ap.add_argument("--repo", type=str, default=str(SCRIPT_DIR.parent / "_sse_content"), help="Path to security_content clone")
    ap.add_argument("--dry-run", action="store_true", help="Only report what would be updated")
    args = ap.parse_args()
    repo = Path(args.repo)
    if not repo.is_dir() or not (repo / "detections").is_dir():
        print(f"Repo not found or missing detections/: {repo}", flush=True)
        return 1
    if not CAT_10_PATH.exists():
        print(f"Cat-10 not found: {CAT_10_PATH}", flush=True)
        return 1
    content = CAT_10_PATH.read_text(encoding="utf-8")
    updates = 0
    for uc_id, yaml_path in iter_detection_yamls(repo):
        det = parse_detection_yaml(yaml_path)
        if not det:
            continue
        kfp = det.get("known_false_positives") or ""
        refs = det.get("references") or []
        dtype = det.get("type") or ""
        mitre = det.get("mitre_attack_id") or []
        sdomain = det.get("security_domain") or ""
        reqf = det.get("required_fields") or []
        if not any([kfp, refs, dtype, mitre, sdomain, reqf]):
            continue
        # Match from ### UC-10.9.N through the closing --- (before next UC or section)
        pattern = rf"(### UC-{re.escape(uc_id)} · .+?\n---)(?=\n\n|\n### UC-|\n## \d+\.|\Z)"
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            continue
        block = m.group(1)
        new_block = insert_fields_into_uc_block(block, kfp, refs, dtype, mitre, sdomain, reqf)
        if new_block != block:
            updates += 1
            if not args.dry_run:
                content = content.replace(block, new_block, 1)
    if not args.dry_run and updates > 0:
        CAT_10_PATH.write_text(content, encoding="utf-8")
        print(f"Updated {updates} UC blocks in {CAT_10_PATH}", flush=True)
    else:
        print(f"Would update {updates} UC blocks (dry-run)" if args.dry_run else f"Updated {updates} UC blocks", flush=True)
    return 0


if __name__ == "__main__":
    exit(main())
