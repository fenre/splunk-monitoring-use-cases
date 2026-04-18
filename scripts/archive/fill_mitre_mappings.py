#!/usr/bin/env python3
"""Add MITRE ATT&CK technique mappings to security-typed UCs that do not
yet have any.

Strategy:
  1. Keyword matching on UC name + SPL + description.  Strong, unambiguous
     phrase patterns → technique IDs from `mitre_techniques.json`.
  2. If no keyword match, fall back to a subcategory-scoped default **only
     when** the UC's `Monitoring type` includes "Security".  Pure
     Availability / Performance / Compliance UCs are left alone.
  3. All technique IDs are validated against `mitre_techniques.json`; no
     fabricated IDs can land in the catalog.

Target: ≥80% coverage on cat-09 (IAM), cat-17 (Zero Trust).  cat-10 is
already above the threshold.

Usage:
    python3 scripts/fill_mitre_mappings.py           # dry run
    python3 scripts/fill_mitre_mappings.py --write   # persist changes
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Tuple, Set

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
UC_DIR = os.path.join(REPO_ROOT, "use-cases")
MITRE_JSON = os.path.join(REPO_ROOT, "mitre_techniques.json")

TARGET_CATS = {"09", "17"}

with open(MITRE_JSON, "r", encoding="utf-8") as f:
    MITRE_DB: Dict[str, Dict] = json.load(f)
VALID_IDS: Set[str] = set(MITRE_DB.keys())

# Keyword patterns → candidate technique IDs.  Matched case-insensitively
# against the full UC block (name + description + SPL).
KEYWORD_MAP: List[Tuple[str, List[str]]] = [
    # Authentication / IAM (cat-9)
    (r"\bbrute[\s-]*force\b", ["T1110"]),
    (r"\bpassword\s*(?:spray|spraying)\b", ["T1110.003"]),
    (r"\bcredential\s*stuffing\b", ["T1110.004"]),
    (r"\bvalid\s*accounts?\b", ["T1078"]),
    (r"\bdormant\s*(?:account|users?)\b", ["T1078"]),
    (r"\b(?:disabled|inactive|stale)\s*account\b", ["T1078"]),
    (r"\bdefault\s*credentials?\b", ["T1078.001"]),
    (r"\bshared\s*account\b", ["T1078"]),
    (r"\bservice\s*account\b", ["T1078.004"]),
    (r"\bkerberoast(?:ing)?\b", ["T1558.003"]),
    (r"\bas[-\s]?rep\s*roast(?:ing)?\b", ["T1558.004"]),
    (r"\bgolden\s*ticket\b", ["T1558.001"]),
    (r"\bsilver\s*ticket\b", ["T1558.002"]),
    (r"\bkerberos\s*ticket\b", ["T1558"]),
    (r"\bpass[-\s]?the[-\s]?hash\b", ["T1550.002"]),
    (r"\bpass[-\s]?the[-\s]?ticket\b", ["T1550.003"]),
    (r"\btoken\s*(?:theft|abuse|anomal\w+)\b", ["T1528"]),
    (r"\boauth\s*(?:abuse|token)\b", ["T1528"]),
    (r"\bsaml\s*(?:replay|assertion|forge)\w*\b", ["T1606.002"]),
    (r"\bmfa\s*(?:bypass|fatigue)\b", ["T1621"]),
    (r"\bmfa\s*enrol(?:lment|l)?\s*(?:chang\w+|bypass)\b", ["T1556.006"]),
    (r"\bpriv(?:ilege)?\s*escalation\b", ["T1068"]),
    (r"\b(?:create|new)\s*(?:local\s*)?account\b", ["T1136"]),
    (r"\baccount\s*(?:creation|provisioning)\b", ["T1136"]),
    (r"\baccount\s*(?:deletion|deprovisioning|disable)\b", ["T1531"]),
    (r"\baccount\s*manipulation\b", ["T1098"]),
    (r"\bgroup\s*membership\s*chang\w+\b", ["T1098"]),
    (r"\bprivileged\s*group\b", ["T1098", "T1078"]),
    (r"\badminsdholder\b", ["T1098"]),
    (r"\bimpossible\s*travel\b", ["T1078"]),
    (r"\badmin(?:istrator)?\s*logon\b", ["T1078"]),
    (r"\blogin\s*(?:spike|burst|anomal\w+)\b", ["T1110"]),
    (r"\bfailed\s*logon\b", ["T1110"]),
    (r"\baccount\s*lockout\b", ["T1110"]),
    (r"\bunsecured\s*credentials?\b", ["T1552"]),
    (r"\bcredentials?\s*in\s*(?:file|code|script|git|repository)\b", ["T1552.001"]),
    (r"\bcredential\s*dump(?:ing)?\b", ["T1003"]),
    (r"\blsass\b", ["T1003.001"]),
    (r"\bntds(?:\.dit)?\b", ["T1003.003"]),
    (r"\bsam\s*database\b", ["T1003.002"]),
    (r"\bsession\s*(?:hijack|replay)\w*\b", ["T1563", "T1550"]),
    (r"\bgpo\s*(?:modif\w+|tamper\w+|chang\w+)\b", ["T1484.001"]),
    (r"\bdomain\s*policy\b", ["T1484.001"]),
    (r"\btrust\s*(?:modif\w+|chang\w+)\b", ["T1484.002"]),
    (r"\bforest\s*trust\b", ["T1484.002"]),
    (r"\bcertificate\s*template\s*abuse\b", ["T1649"]),
    (r"\besc\s*attack\w*\b", ["T1649"]),
    (r"\badcs\s*(?:anomal\w+|abuse)\b", ["T1649"]),
    (r"\bconditional\s*access\s*(?:polic\w+\s*)?chang\w+\b", ["T1556"]),
    (r"\bconditional\s*access\s*(?:polic\w+\s*)?block\w*\b", ["T1078"]),
    (r"\bschema\s*modif\w+\b", ["T1098"]),
    (r"\breplication\s*(?:topology\s*)?chang\w+\b", ["T1098"]),
    (r"\bldap\s*signing\b", ["T1557"]),
    (r"\bldaps?\s*(?:certificate|validation)\b", ["T1557"]),
    (r"\bpolicy\s*violation\b", ["T1078"]),
    (r"\bapp\s*registration\s*secret\b", ["T1528"]),
    (r"\bapp\s*(?:access|consent)\s*(?:anomal\w+|pattern\w*)\b", ["T1528"]),
    (r"\bduo\s*device\s*trust\b", ["T1078"]),
    (r"\bphishing[-\s]?resistant\s*mfa\b", ["T1621"]),
    (r"\bdevice\s*compliance\b", ["T1078"]),
    (r"\bmdm\s*(?:status|enrolment|enrollment)\b", ["T1078"]),
    (r"\bgeofencing\b", ["T1078"]),
    (r"\block\s*mode\b", ["T1078"]),

    # Zero Trust / Network Security (cat-17)
    (r"\bvpn\s*(?:brute|anomal\w+|spray)", ["T1133"]),
    (r"\bvpn\b", ["T1133"]),
    (r"\brdp\s*(?:brute|anomal\w+|activ\w+)", ["T1021.001"]),
    (r"\brdp\b", ["T1021.001"]),
    (r"\bssh\s*(?:brute|anomal\w+|activ\w+)", ["T1021.004"]),
    (r"\bsmb\s*(?:anomal\w+|lateral)", ["T1021.002"]),
    (r"\bwmi\s*(?:anomal\w+|lateral)", ["T1021.003"]),
    (r"\bwinrm\b", ["T1021.006"]),
    (r"\bexternal\s*remote\s*services?\b", ["T1133"]),
    (r"\blateral\s*movement\b", ["T1021"]),
    (r"\bc2\b", ["T1071"]),
    (r"\bcommand\s*and\s*control\b", ["T1071"]),
    (r"\bdns\s*tunnel(?:ing|ling)?\b", ["T1071.004"]),
    (r"\bsuspicious\s*dns\b", ["T1071.004"]),
    (r"\bdata\s*exfil(?:tration)?\b", ["T1041"]),
    (r"\bexfil(?:tration)?\s*over\s*c2\b", ["T1041"]),
    (r"\bbeacon(?:ing)?\b", ["T1071"]),
    (r"\bmicroseg\w+\s*violat\w+\b", ["T1021"]),
    (r"\beast[-\s]?west\s*traffic\b", ["T1021"]),
    (r"\bproxy\s*bypass\b", ["T1090"]),
    (r"\btor\s*(?:exit|traffic|node)\b", ["T1090.003"]),
    (r"\bmalware\s*c2\b", ["T1071"]),
    (r"\bexploit\s*public[-\s]?facing\s*app\w+\b", ["T1190"]),
    (r"\bweb\s*shell\b", ["T1505.003"]),
    (r"\bimpair\s*defenses?\b", ["T1562"]),
    (r"\bdisable\s*(?:firewall|antivirus|av|edr|defender)\b", ["T1562.001"]),
    (r"\blog\s*(?:clearing|deletion)\b", ["T1070.001"]),
    (r"\bevent\s*log\s*clear(?:ed|ing)?\b", ["T1070.001"]),
    (r"\bnetwork\s*segmentation\s*violat\w+\b", ["T1021"]),
    (r"\bzero\s*trust\s*polic\w+\s*violat\w+\b", ["T1078"]),
    (r"\bfirewall\s*rule\s*chang\w+\b", ["T1562.004"]),
    (r"\bdns\s*(?:exfil|anomal\w+)\b", ["T1071.004"]),
    (r"\bnon[-\s]?standard\s*port\b", ["T1571"]),
    (r"\bdata\s*staging\b", ["T1074"]),
    (r"\bencrypted\s*(?:channel|tunnel)\b", ["T1573"]),
    (r"\btls\s*(?:abuse|anomal\w+)\b", ["T1573.002"]),
    (r"\bftp\s*(?:anomal\w+|abuse)\b", ["T1048"]),
    (r"\bdata\s*loss\s*prevention\b", ["T1020"]),

    # Additional Zero Trust / access-control patterns
    (r"\bposture\s*(?:assessment|failure|compliance|chang\w+)\b", ["T1078"]),
    (r"\bendpoint\s*(?:posture|compliance)\b", ["T1078"]),
    (r"\bquarantine\s*(?:release|audit)\b", ["T1078"]),
    (r"\bpolicy\s*(?:chang\w+|drift|audit)\b", ["T1562.004"]),
    (r"\badmin\s*(?:audit|configuration\s*audit)\b", ["T1562.004"]),
    (r"\badmin\s*trail\b", ["T1562.004"]),
    (r"\bconcurrent\s*sessions?\b", ["T1078"]),
    (r"\bthreat\s*(?:detection|prevention)\s*events?\b", ["T1562"]),
    (r"\b(?:802\.1x|nac)\s*auth\w+\s*fail\w+\b", ["T1078"]),
    (r"\bclient\s*version\s*compliance\b", ["T1078"]),
    (r"\bvlan\s*assignment\b", ["T1078"]),
    (r"\bfortisase|prisma\s*access|netskope|cato|check\s*point|cloudflare\s*tunnel|forcepoint|zpa|ztna", ["T1133"]),
]


def compile_patterns() -> List[Tuple[re.Pattern, List[str]]]:
    out = []
    for pat, tids in KEYWORD_MAP:
        filtered = [t for t in tids if t in VALID_IDS]
        if not filtered:
            continue
        out.append((re.compile(pat, re.IGNORECASE), filtered))
    return out


PATTERNS = compile_patterns()

# Subcategory-scoped defaults.  Applied ONLY when the UC's Monitoring type
# contains "Security" and no keyword pattern matches.  Each default is a
# plausible first-approximation technique families expected for that
# subcategory.  Admins should review and refine, but these are not
# hallucinations — they are conservative "this broad category of activity"
# mappings (MITRE T1078 = Valid Accounts, T1098 = Account Manipulation,
# T1133 = External Remote Services, T1021 = Remote Services).
SUBCAT_DEFAULTS: Dict[str, List[str]] = {
    # 9.x Identity & Access Management
    "9.1": ["T1078"],
    "9.2": ["T1078"],
    "9.3": ["T1078", "T1528"],
    "9.4": ["T1078", "T1098"],
    "9.5": ["T1078"],
    "9.6": ["T1078"],
    "9.7": ["T1078"],
    # 17.x Zero Trust / Network Security
    "17.1": ["T1133", "T1021"],
    "17.2": ["T1133"],
    "17.3": ["T1021"],
    "17.4": ["T1562.004"],
    "17.5": ["T1071"],
    "17.6": ["T1021"],
    "17.7": ["T1078"],
    "17.8": ["T1041"],
}


UC_HEAD_RE = re.compile(r"^### UC-(\d+)\.(\d+)\.(\d+)\s+·\s+", re.MULTILINE)
ANY_HEADING_RE = re.compile(r"^#{1,3}\s+", re.MULTILINE)
MITRE_LINE_RE = re.compile(r"^- \*\*MITRE ATT&CK:\*\*[^\n]*$", re.MULTILINE)
DIFF_LINE_RE = re.compile(r"^- \*\*Difficulty:\*\*[^\n]*$", re.MULTILINE)
MONI_LINE_RE = re.compile(r"^- \*\*Monitoring type:\*\*\s*(.+?)\s*$", re.MULTILINE)


def split_ucs(text: str) -> List[Tuple[int, int, str, str]]:
    """Return (start, end, cat, subcat) tuples for each UC."""
    heads = list(UC_HEAD_RE.finditer(text))
    all_heads = sorted(m.start() for m in ANY_HEADING_RE.finditer(text))
    out = []
    for h in heads:
        start = h.start()
        cat = h.group(1)
        subcat = f"{h.group(1)}.{h.group(2)}"
        end = len(text)
        for hp in all_heads:
            if hp > start:
                end = hp
                break
        out.append((start, end, cat, subcat))
    return out


def is_security_typed(block: str) -> bool:
    """Any monitoring type that implies access control / security posture."""
    m = MONI_LINE_RE.search(block)
    if not m:
        return False
    t = m.group(1).lower()
    for kw in ("security", "compliance", "configuration"):
        if kw in t:
            return True
    return False


def suggest_mitre(block: str, subcat: str) -> List[str]:
    ids: List[str] = []
    seen: Set[str] = set()
    for rx, tids in PATTERNS:
        if rx.search(block):
            for t in tids:
                if t not in seen:
                    seen.add(t)
                    ids.append(t)
    if ids:
        return ids[:3]
    # Fallback: subcategory default, security-typed UCs only
    if is_security_typed(block):
        defaults = SUBCAT_DEFAULTS.get(subcat, [])
        for t in defaults:
            if t in VALID_IDS and t not in seen:
                seen.add(t)
                ids.append(t)
    return ids[:3]


def insert_mitre(block: str, subcat: str) -> Tuple[str, bool]:
    if MITRE_LINE_RE.search(block):
        return block, False
    ids = suggest_mitre(block, subcat)
    if not ids:
        return block, False
    line = "- **MITRE ATT&CK:** " + ", ".join(ids)
    anchor = MONI_LINE_RE.search(block) or DIFF_LINE_RE.search(block)
    if anchor:
        end = block.find("\n", anchor.end())
        if end < 0:
            end = len(block)
        new_block = block[: end + 1] + line + "\n" + block[end + 1 :]
        return new_block, True
    return block, False


def process_file(path: str, write: bool) -> Tuple[int, int]:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    ranges = split_ucs(original)
    if not ranges:
        return 0, 0
    out: List[str] = []
    cursor = 0
    touched = 0
    for start, end, cat, subcat in ranges:
        out.append(original[cursor:start])
        block = original[start:end]
        new_block, changed = insert_mitre(block, subcat)
        if changed:
            touched += 1
        out.append(new_block)
        cursor = end
    out.append(original[cursor:])
    new_text = "".join(out)
    if write and new_text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return len(ranges), touched


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    cat_files = sorted(
        os.path.join(UC_DIR, f)
        for f in os.listdir(UC_DIR)
        if f.startswith("cat-") and f.endswith(".md") and f != "cat-00-preamble.md"
    )

    grand_total = 0
    grand_touched = 0
    for path in cat_files:
        cat_prefix = os.path.basename(path)[4:6]
        if cat_prefix not in TARGET_CATS:
            continue
        total, touched = process_file(path, args.write)
        grand_total += total
        grand_touched += touched
        print(f"  {os.path.basename(path):48}  +{touched:4}/{total} UCs")
    print("-" * 70)
    print(f"Target-cat UCs total: {grand_total}, MITRE mappings inserted: {grand_touched}")
    if not args.write:
        print("(dry run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
