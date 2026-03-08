#!/usr/bin/env python3
"""
Backfill cat-10 use cases: add missing Value and Implementation text,
and add Premium Apps field when the use case requires Splunk Enterprise Security (ES),
ITSI, or SOAR.

Usage:
    python3 scripts/backfill_cat10_value_impl_premium.py

Reads: use-cases/cat-10-security-infrastructure.md
Writes: same file (in place). Also scans other cat-*.md to add Premium Apps when relevant.
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
UC_DIR = os.path.join(REPO_ROOT, "use-cases")
CAT10_PATH = os.path.join(UC_DIR, "cat-10-security-infrastructure.md")

# Value template for ESCU/security detections when Value is empty
def gen_value(title: str) -> str:
    return (
        f"This detection identifies {title}. "
        "It supports security monitoring and incident response. "
        "Part of Splunk Security Essentials (ESCU) where applicable."
    )

# Implementation template when Implementation is empty
def gen_impl(data_sources: str) -> str:
    ds = data_sources.strip() or "see Data Sources above"
    return (
        f"Deploy the detection from Splunk Security Essentials (ESCU) or the security_content repository. "
        f"Ensure the required data sources ({ds}) are ingested and normalized. "
        "For Risk-based detections, Splunk Enterprise Security is required to populate the Risk datamodel and generate Notable events. "
        "Configure as a correlation search or saved search with alerting as needed."
    )

def needs_enterprise_security(body: str, app_ta: str) -> bool:
    if "**Premium Apps:**" in body or "**Premium apps:**" in body:
        return False
    if "Risk.All_Risk" in body or "datamodel Risk" in body:
        return True
    app_lower = (app_ta or "").lower()
    if "escu" in app_lower or "security essentials" in app_lower or "enterprise security" in app_lower:
        return True
    return False

def process_cat10_block(header: str, body: str) -> str:
    title_match = re.match(r"^### UC-10\.\d+\.\d+ · (.+)$", header.strip())
    title = title_match.group(1).strip() if title_match else "this activity"

    # Fill empty Value
    if "- **Value:** |" in body:
        body = body.replace(
            "- **Value:** |",
            "- **Value:** " + gen_value(title),
            1,
        )

    # Extract Data Sources for Implementation
    ds_match = re.search(r"- \*\*Data Sources:\*\*\s*(.+?)(?=\n- \*\*|\n```|\Z)", body, re.DOTALL)
    data_sources = ds_match.group(1).strip() if ds_match else ""

    # Fill empty Implementation (with or without trailing space)
    impl_marker1 = "- **Implementation:** \n- **Visualization:**"
    impl_marker2 = "- **Implementation:**\n- **Visualization:**"
    impl_text = gen_impl(data_sources)
    if impl_marker1 in body:
        body = body.replace(impl_marker1, "- **Implementation:** " + impl_text + "\n- **Visualization:**", 1)
    elif impl_marker2 in body:
        body = body.replace(impl_marker2, "- **Implementation:** " + impl_text + "\n- **Visualization:**", 1)

    # Add Premium Apps after App/TA when required
    app_ta_match = re.search(r"- \*\*App/TA:\*\*\s*(.+?)(?=\n|$)", body, re.DOTALL)
    app_ta = app_ta_match.group(1).strip() if app_ta_match else ""
    if needs_enterprise_security(body, app_ta):
        # Insert "- **Premium Apps:** Splunk Enterprise Security" after App/TA line
        body = re.sub(
            r"(- \*\*App/TA:\*\* .+?\n)",
            r"\1- **Premium Apps:** Splunk Enterprise Security\n",
            body,
            count=1,
        )

    return body

def process_cat10():
    with open(CAT10_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by UC headers; keep the delimiter so we can reassemble
    parts = re.split(r"(### UC-10\.\d+\.\d+ · .+\n)", content)
    if len(parts) < 2:
        print("  No UC blocks found in cat-10")
        return 0

    intro = parts[0]
    result = [intro]
    count_value = 0
    count_impl = 0
    count_premium = 0

    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        had_value = "- **Value:** |" in body or bool(re.search(r"- \*\*Value:\*\* \|\s*$", body, re.MULTILINE))
        had_impl = bool(re.search(r"- \*\*Implementation:\*\*\s*\n- \*\*Visualization:\*\*", body))
        had_premium_before = "**Premium Apps:**" in body

        new_body = process_cat10_block(header, body)

        if had_value and "- **Value:** |" not in new_body:
            count_value += 1
        if had_impl and not re.search(r"- \*\*Implementation:\*\*\s*\n- \*\*Visualization:\*\*", new_body):
            count_impl += 1
        if not had_premium_before and "**Premium Apps:**" in new_body:
            count_premium += 1

        result.append(header)
        result.append(new_body)

    new_content = "".join(result)
    with open(CAT10_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  cat-10: filled {count_value} empty Values, {count_impl} empty Implementations, added {count_premium} Premium Apps (ES)")
    return count_value + count_impl + count_premium

def add_premium_apps_other_categories():
    """Scan all other cat-*.md and add Premium Apps when ES/ITSI/SOAR is clearly required."""
    pattern = os.path.join(UC_DIR, "cat-*.md")
    import glob
    files = sorted(glob.glob(pattern))
    total_added = 0
    for filepath in files:
        if "cat-10-" in filepath:
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        original = content
        # Only add Premium Apps line if not already present
        if "**Premium Apps:**" in content or "**Premium apps:**" in content:
            continue
        # ITSI: add Premium Apps when App/TA line mentions ITSI
        itsi_match = re.search(r"- \*\*App/TA:\*\* [^\n]*(?:ITSI|Splunk ITSI)[^\n]*", content, re.I)
        if itsi_match:
            content = re.sub(
                r"(- \*\*App/TA:\*\* [^\n]*(?:ITSI|Splunk ITSI)[^\n]*\n)",
                r"\1- **Premium Apps:** Splunk ITSI\n",
                content,
                count=1,
            )
        # SOAR: add Premium Apps when App/TA line mentions SOAR/Phantom/adaptive response
        soar_match = re.search(r"- \*\*App/TA:\*\* [^\n]*(?:SOAR|Phantom|adaptive response)[^\n]*", content, re.I)
        if soar_match:
            content = re.sub(
                r"(- \*\*App/TA:\*\* [^\n]*(?:SOAR|Phantom|adaptive response)[^\n]*\n)",
                r"\1- **Premium Apps:** Splunk SOAR\n",
                content,
                count=1,
            )
        if content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            total_added += 1
            print(f"  {os.path.basename(filepath)}: added Premium Apps")
    return total_added

def main():
    os.chdir(REPO_ROOT)
    if not os.path.isfile(CAT10_PATH):
        print(f"ERROR: {CAT10_PATH} not found", file=sys.stderr)
        sys.exit(1)
    print("Backfilling cat-10 (Value, Implementation, Premium Apps)...")
    n = process_cat10()
    print("Checking other categories for Premium Apps...")
    add_premium_apps_other_categories()
    print(f"Done. Total backfills in cat-10: {n}")

if __name__ == "__main__":
    main()
