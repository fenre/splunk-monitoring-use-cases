#!/usr/bin/env python3
"""
Redistribute use cases from 10.9 (Splunk Security Essentials) into the most
appropriate subcategories 10.1–10.8 using Security domain, title, and value.

Usage:
  python3 redistribute_sse_ucs.py [--dry-run]

Reads cat-10-security-infrastructure.md, classifies each 10.9.x UC to 10.1–10.8,
renumbers them, and rewrites the file with the 10.9 section removed.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
CAT_10 = SCRIPT_DIR / "cat-10-security-infrastructure.md"

# Current max UC index per subcategory (so we start new UCs at .6, .9, etc.)
MAX_INDEX = {"10.1": 5, "10.2": 5, "10.3": 8, "10.4": 7, "10.5": 7, "10.6": 7, "10.7": 6, "10.8": 5}

# Keywords to map title/value to subcategory (more specific first)
KEYWORDS_SUBCAT = [
    (["email", "phishing", "attachment", "exchange", "o365", "mail", "outlook", "m365", "defender for office", "safe links", "safe attachment"], "10.4"),
    (["web proxy", "swg", "secure web gateway", "url filter", "zscaler", "umbrella", "casb", "shadow it", "blocked category"], "10.5"),
    (["vuln", "cve", "patch", "vulnerability", "scan", "ecr scan", "container scan", "remediation", "prioritization"], "10.6"),
    (["certificate", "pki", "tls", "ssl cert", "cert expiry", "revocation", "ct log"], "10.8"),
    (["cisco asa", "palo alto", "pan_", "fortinet", "fortigate", "ngfw", "firewall", "wildfire", "sinkhole"], "10.1"),
    (["ids", "ips", "suricata", "snort", "signature", "lateral movement", "alert severity"], "10.2"),
    (["endpoint", "edr", "malware", "quarantine", "isolat", "ransomware", "behavioral detection", "agent health"], "10.3"),
    (["siem", "soar", "playbook", "correlation", "alert volume", "mttd", "mttr", "analyst", "risk"], "10.7"),
]


def extract_sdomain_and_title(block: str):
    sdomain = ""
    m = re.search(r"-\s*\*\*Security domain:\*\*\s*(.+?)(?:\n|$)", block, re.IGNORECASE)
    if m:
        sdomain = m.group(1).strip().lower()
    title = ""
    m = re.match(r"###\s+UC-\d+\.\d+\.\d+\s+[·•]\s*(.+?)(?:\n|$)", block)
    if m:
        title = m.group(1).strip().lower()
    value = ""
    m = re.search(r"-\s*\*\*Value:\*\*\s*(.+?)(?:\n(?:-\s*\*\*|\n\n)|$)", block, re.DOTALL | re.IGNORECASE)
    if m:
        value = (m.group(1).strip() or "").lower()[:500]
    return sdomain, title, value


def classify_to_subcat(sdomain: str, title: str, value: str) -> str:
    combined = " ".join([sdomain, title, value])
    for keywords, subcat in KEYWORDS_SUBCAT:
        if any(kw in combined for kw in keywords):
            return subcat
    if sdomain == "endpoint":
        return "10.3"
    if sdomain == "network":
        if any(k in combined for k in ["asa", "firewall", "palo", "fortinet", "pan_"]):
            return "10.1"
        return "10.2"
    if sdomain in ("identity", "access", "audit"):
        return "10.7"
    if sdomain == "cloud":
        if any(k in combined for k in ["vuln", "cve", "scan", "ecr"]):
            return "10.6"
        return "10.7"
    return "10.7"


def extract_uc_blocks(content: str):
    """Return list of (uc_id, block_text). Block runs from ### UC- to (not including) next ### UC- or ### 10. or ## ."""
    pattern = r"###\s+UC-(10\.\d+\.\d+)\s+[·•](.+?)(?=\n###\s+UC-10\.|\n###\s+10\.\d+\s+|\n##\s+\d+\.|\Z)"
    matches = list(re.finditer(pattern, content, re.DOTALL))
    blocks = []
    for m in matches:
        uc_id = m.group(1)
        rest = m.group(2)
        block = "### UC-" + uc_id + " ·" + rest
        blocks.append((uc_id, block))
    return blocks


def get_section_header(content: str, subcat: str) -> str:
    """Return the section header for 10.X (from ### 10.X to just before ### UC-10.X.1)."""
    # Search for "### 10.1 " (with trailing space) so we don't match "### 10.10 "
    start = content.find(f"### {subcat} ")
    if start < 0:
        return f"### {subcat} (Security)\n\n---\n\n"
    first_uc = content.find(f"### UC-{subcat}.1 ", start)
    if first_uc < 0:
        first_uc = len(content)
    return content[start:first_uc].rstrip()


def main():
    dry_run = "--dry-run" in sys.argv
    if not CAT_10.exists():
        print(f"Not found: {CAT_10}", file=sys.stderr)
        return 1
    content = CAT_10.read_text(encoding="utf-8")
    blocks = extract_uc_blocks(content)
    original = [(uid, blk) for uid, blk in blocks if not uid.startswith("10.9.")]
    sse = [(uid, blk) for uid, blk in blocks if uid.startswith("10.9.")]
    by_subcat = defaultdict(list)
    for uid, blk in original:
        subcat = re.match(r"(10\.\d+)\.\d+", uid).group(1)
        by_subcat[subcat].append((uid, blk))
    next_idx = {f"10.{i}": MAX_INDEX[f"10.{i}"] + 1 for i in range(1, 9)}
    for uid, blk in sse:
        sdomain, title, value = extract_sdomain_and_title(blk)
        subcat = classify_to_subcat(sdomain, title, value)
        new_id = f"{subcat}.{next_idx[subcat]}"
        next_idx[subcat] += 1
        new_block = re.sub(r"^###\s+UC-10\.9\.\d+\s+", f"### UC-{new_id} ", blk, count=1)
        by_subcat[subcat].append((new_id, new_block))
    if dry_run:
        print("Dry run: would redistribute", len(sse), "UCs from 10.9 into 10.1–10.8", flush=True)
        for subcat in ["10.1", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7", "10.8"]:
            n = len(by_subcat.get(subcat, []))
            print(f"  {subcat}: {n} UCs", flush=True)
        return 0
    # Intro: from start until "### 10.1 "
    intro_end = content.find("### 10.1 ")
    if intro_end < 0:
        intro_end = 0
    intro = content[:intro_end].rstrip()
    out = [intro, "\n\n"]
    for i in range(1, 9):
        subcat = f"10.{i}"
        header = get_section_header(content, subcat)
        out.append(header)
        out.append("\n\n")
        ucs = sorted(by_subcat.get(subcat, []), key=lambda x: (int(x[0].split(".")[1]), int(x[0].split(".")[2])))
        for _uid, blk in ucs:
            out.append(blk.rstrip())
            out.append("\n\n---\n\n")
    new_content = "".join(out).rstrip() + "\n"
    CAT_10.write_text(new_content, encoding="utf-8")
    print("Redistributed", len(sse), "UCs; removed 10.9. Wrote", CAT_10, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
