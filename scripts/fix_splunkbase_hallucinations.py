#!/usr/bin/env python3
"""Fix Splunkbase app ID hallucinations found during audit.

Each entry in FIXES is a 3-tuple:
    (regex_pattern, replacement_string, description)

The script walks the `use-cases/` directory and applies fixes to every
Markdown file, printing a summary of changes per file.

All ID corrections were verified against live Splunkbase listings.
"""
from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple

FIXES: List[Tuple[str, str, str]] = [
    # 6056 is SentinelOne (SOAR); 6553 is the real Okta TA
    (
        r"Splunk Add-on for Okta Identity Cloud \(Splunkbase\s*6056\)",
        "Splunk Add-on for Okta Identity Cloud (Splunkbase 6553)",
        "Okta: 6056 -> 6553",
    ),
    (r"\(Splunk\s+Add-on\s+for\s+Okta\s+Identity\s+Cloud\s+\(6056\)\)",
     "(Splunk Add-on for Okta Identity Cloud (6553))",
     "Okta short form: 6056 -> 6553"),
    (r"Splunk Add-on for Okta Identity Cloud \(6056\)",
     "Splunk Add-on for Okta Identity Cloud (6553)",
     "Okta short form: 6056 -> 6553"),

    # 4185 is Conducive Archiver; 2941 is the real Splunk UBA
    (
        r"Splunk UBA \(Splunkbase\s*4185\)",
        "Splunk UBA (Splunkbase 2941)",
        "Splunk UBA: 4185 -> 2941",
    ),
    (
        r"Splunk UBA \(4185\)",
        "Splunk UBA (2941)",
        "Splunk UBA short form: 4185 -> 2941",
    ),

    # 3435 is Splunk Security Essentials; 5402 is CCX Unified Checkpoint TA
    (
        r"`Splunk_TA_checkpoint`\s*\(Splunkbase\s*3435\)",
        "`Splunk_TA_checkpoint` (Splunkbase 5402)",
        "Checkpoint TA: 3435 -> 5402",
    ),

    # 830 is "indextime search" (2011 utility); 3186 is real Apache TA
    (
        r"https://splunkbase\.splunk\.com/app/830\)",
        "https://splunkbase.splunk.com/app/3186)",
        "Apache URL: /app/830 -> /app/3186",
    ),

    # 3178 is License Usage Dashboard; 3258 is real NGINX TA
    (
        r"https://splunkbase\.splunk\.com/app/3178\)",
        "https://splunkbase.splunk.com/app/3258)",
        "NGINX URL: /app/3178 -> /app/3258",
    ),

    # 2185 doesn't exist (404); 7593 is Veritas Data Protection Add-On
    (
        r"Splunk Add-on for NetBackup \(Splunkbase\s*2185\)",
        "Veritas Data Protection Add-On (Splunkbase 7593)",
        "NetBackup: 2185 -> 7593",
    ),

    # 4097 is Sophos App; 5556 is real Google Workspace TA
    (
        r"Splunk Add-on for Google Workspace \(Splunkbase\s*4097\)",
        "Splunk Add-on for Google Workspace (Splunkbase 5556)",
        "Google Workspace: 4097 -> 5556",
    ),

    # 7173 is AbuseIPDB; 7312 is real Veeam App for Splunk
    (
        r"Splunk Add-on for Veeam \(Splunkbase\s*7173\)",
        "Veeam App for Splunk (Splunkbase 7312)",
        "Veeam: 7173 -> 7312",
    ),

    # 6238 is MongoDB Atlas; 7125 is real OpenTelemetry Collector TA
    (
        r"Splunk Add-on for OpenTelemetry \(Splunkbase\s*6238\)",
        "Splunk Add-on for OpenTelemetry Collector (Splunkbase 7125)",
        "OpenTelemetry: 6238 -> 7125",
    ),

    # /app/2913 returns 404; 3215 is the current VMware TA
    (
        r"https://splunkbase\.splunk\.com/app/2913\)",
        "https://splunkbase.splunk.com/app/3215)",
        "VMware URL: /app/2913 -> /app/3215",
    ),
]


def fix_file(path: str) -> List[Tuple[str, int]]:
    """Apply all FIXES to one file. Return list of (description, count) tuples."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    original = text
    counts: List[Tuple[str, int]] = []
    for pattern, replacement, desc in FIXES:
        new_text, n = re.subn(pattern, replacement, text)
        if n > 0:
            counts.append((desc, n))
            text = new_text
    if text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return counts


def main(argv: List[str]) -> int:
    root = "use-cases"
    total = 0
    files_changed = 0
    for fname in sorted(os.listdir(root)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(root, fname)
        counts = fix_file(path)
        if counts:
            files_changed += 1
            print(f"{fname}:")
            for desc, n in counts:
                print(f"   {desc}: {n}")
                total += n
    print(f"\nTotal fixes applied: {total} across {files_changed} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
