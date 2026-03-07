#!/usr/bin/env python3
"""
Add '- **Monitoring type:** <Type>' after '- **Difficulty:**' in every ### UC-X.Y.Z block
across all cat-*.md files. Skips blocks that already have Monitoring type.
Uses keyword inference from the use case title.
"""
import glob
import os
import re

UC_DIR = os.path.dirname(os.path.abspath(__file__))

# Keywords in title -> monitoring type (first match wins)
TITLE_KEYWORDS = [
    (r"\b(up.?down|state|status|health|failover|tunnel|peer|adjacency|offline|uptime|availability|reload)\b", "Availability"),
    (r"\b(utilization|throughput|latency|response time|error rate|jitter|bandwidth|cpu|memory|rssi|signal|saturation|load)\b", "Performance"),
    (r"\b(acl|deny|threat|auth|vpn|rogue|ids|ips|policy violation|botnet|c2|security|malware|dlp|geo|brute|unauthorized|vulnerability|login)\b", "Security"),
    (r"\b(config|change|drift|policy change|audit)\b", "Configuration"),
    (r"\b(exhaustion|pool|scope|trending|capacity|queue depth|budget|forecast)\b", "Capacity"),
    (r"\b(environmental|power|fan|hardware|failure|temperature|humidity|sensor|panic|crash|oom)\b", "Fault"),
    (r"\b(flapping|anomaly|instability|mac flap|route flap|storm)\b", "Anomaly"),
    (r"\b(compliance|backup|posture|change window)\b", "Compliance"),
]


def infer_type(title: str) -> str:
    title_lower = title.lower()
    for pattern, mtype in TITLE_KEYWORDS:
        if re.search(pattern, title_lower, re.I):
            return mtype
    return "Performance"


def process_file(filepath: str) -> int:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by ### UC-<digits>.<digits>.<digits> · (any category)
    blocks = re.split(r"(?=### UC-\d+\.\d+\.\d+ · )", content)
    out = []
    added = 0
    for block in blocks:
        if not block.strip():
            out.append(block)
            continue
        match = re.match(r"### (UC-\d+\.\d+\.\d+) · ([^\n]+)", block)
        if not match:
            out.append(block)
            continue
        title = match.group(2).strip()
        # Skip if already has Monitoring type
        if "**Monitoring type:**" in block or "**monitoring type:**" in block:
            out.append(block)
            continue
        mtype = infer_type(title)

        difficulty_pat = re.compile(
            r"^(- \*\*Difficulty:\*\* .+)$",
            re.MULTILINE,
        )
        new_block, n = difficulty_pat.subn(
            r"\1\n- **Monitoring type:** " + mtype,
            block,
            count=1,
        )
        if n:
            added += 1
        out.append(new_block)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("".join(out))
    return added


def main():
    pattern = os.path.join(UC_DIR, "cat-[0-9]*.md")
    files = sorted(glob.glob(pattern))
    # Exclude preamble (no category number)
    files = [f for f in files if "cat-00" not in os.path.basename(f)]
    total = 0
    for filepath in files:
        n = process_file(filepath)
        total += n
        if n:
            print(f"  {os.path.basename(filepath)}: added Monitoring type to {n} use cases")
    print(f"\nTotal: added Monitoring type to {total} use case blocks.")


if __name__ == "__main__":
    main()
