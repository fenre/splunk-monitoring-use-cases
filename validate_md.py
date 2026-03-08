#!/usr/bin/env python3
"""Validate use case markdown files: structure, UC-ID consistency, code block balance."""
import re
import os

USE_CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "use-cases")
SKIP = {"cat-00-preamble.md", "cat-10-sse-import.md"}

def validate_file(path):
    name = os.path.basename(path)
    if name in SKIP:
        return [], []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    errors = []
    warnings = []

    # Category number from # N. or ## N.
    cat_match = re.search(r"^#{1,2}\s+(\d+)\.\s+", content, re.MULTILINE)
    if not cat_match:
        return [(path, "no category heading (# N. Name)")], []
    cat_num = int(cat_match.group(1))

    # UC- IDs must be cat_num.1.1, cat_num.1.2, ...
    uc_ids = re.findall(r"^#{3,4}\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*", content, re.MULTILINE)
    for uid in uc_ids:
        if not uid.startswith(f"{cat_num}."):
            errors.append((path, f"UC-ID {uid} does not match category {cat_num}"))

    # Code block balance: ``` must come in pairs (per block)
    backticks = [i for i, l in enumerate(lines) if re.match(r"^\s*```", l)]
    if len(backticks) % 2 != 0:
        errors.append((path, f"odd number of ``` lines ({len(backticks)}); unclosed code block"))

    # Field pattern: - **Name:** value
    field_pattern = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")
    # Subcategory: ## 1.1 or ### 1.1
    subcat_pattern = re.compile(r"^#{2,3}\s+(\d+\.\d+)\s+(.+)$")
    seen_subcats = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        m_uc = re.match(r"^#{3,4}\s+UC-(\d+\.\d+)\.(\d+)\s*[·•]\s*(.+)$", stripped)
        if m_uc:
            subcat = m_uc.group(1)  # e.g. 1.1
            num = m_uc.group(2)
            if cat_num and not subcat.startswith(f"{cat_num}."):
                errors.append((path, f"line {i+1}: UC subcategory {subcat} doesn't match category {cat_num}"))
        m_sub = subcat_pattern.match(stripped)
        if m_sub and cat_num:
            sc = m_sub.group(1)
            if not sc.startswith(f"{cat_num}."):
                errors.append((path, f"line {i+1}: subcategory {sc} doesn't match category {cat_num}"))

    return errors, warnings

def main():
    all_errors = []
    for f in sorted(os.listdir(USE_CASES_DIR)):
        if not f.startswith("cat-") or not f.endswith(".md"):
            continue
        path = os.path.join(USE_CASES_DIR, f)
        if not os.path.isfile(path):
            continue
        errs, warns = validate_file(path)
        all_errors.extend(errs)
    if all_errors:
        for path, msg in all_errors:
            print(f"{path}: {msg}")
        return 1
    print("Validation passed: structure and UC-ID consistency OK.")
    return 0

if __name__ == "__main__":
    exit(main())
