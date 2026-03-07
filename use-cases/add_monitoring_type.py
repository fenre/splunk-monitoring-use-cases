#!/usr/bin/env python3
"""
Add '- **Monitoring type:** <Type>' after '- **Difficulty:**' in each ### UC-5.x.y block.
"""
import re

FILE = "cat-05-network-infrastructure.md"

# Keywords in title -> primary monitoring type (order matters; first match wins for inference)
TITLE_KEYWORDS = [
    (r"\b(up.?down|state|status|health|failover|tunnel|peer|adjacency|offline|uptime|availability|reload)\b", "Availability"),
    (r"\b(utilization|throughput|latency|response time|error rate|jitter|bandwidth|throughput|cpu|memory|rssi|signal)\b", "Performance"),
    (r"\b(acl|deny|threat|auth|vpn|rogue|ids|ips|policy violation|botnet|c2|security|malware|dlp|geo)\b", "Security"),
    (r"\b(config|change|drift|policy change|audit)\b", "Configuration"),
    (r"\b(exhaustion|pool|scope|trending|capacity|queue depth|budget)\b", "Capacity"),
    (r"\b(environmental|power|fan|hardware|failure|temperature|humidity|sensor)\b", "Fault"),
    (r"\b(flapping|anomaly|instability|mac flap|route flap|storm)\b", "Anomaly"),
    (r"\b(compliance|backup|posture|change window)\b", "Compliance"),
]

# Explicit mapping for 5.1–5.8 (optional override)
TYPE_BY_UC = {
    "5.1.1": "Availability", "5.1.2": "Performance", "5.1.3": "Performance, Capacity",
    "5.1.4": "Availability", "5.1.5": "Availability", "5.1.6": "Availability, Anomaly",
    "5.1.7": "Configuration, Compliance", "5.1.8": "Performance, Capacity",
    "5.1.9": "Availability, Fault", "5.1.10": "Configuration, Compliance",
    "5.1.11": "Fault", "5.1.12": "Anomaly, Security", "5.1.13": "Security",
    "5.1.14": "Security", "5.1.15": "Fault", "5.1.16": "Anomaly",
    "5.1.17": "Performance, Fault", "5.1.18": "Availability, Configuration",
    "5.1.19": "Capacity, Fault", "5.1.20": "Anomaly, Availability",
    "5.1.21": "Performance", "5.1.22": "Availability", "5.1.23": "Availability",
    "5.2.1": "Security", "5.2.2": "Configuration, Compliance", "5.2.3": "Security",
    "5.2.4": "Availability", "5.2.5": "Security", "5.2.6": "Security, Anomaly",
    "5.2.7": "Anomaly, Performance", "5.2.8": "Security", "5.2.9": "Security",
    "5.2.10": "Compliance", "5.2.11": "Performance, Capacity", "5.2.12": "Capacity",
    "5.2.13": "Capacity", "5.2.14": "Availability", "5.2.15": "Security",
    "5.2.16": "Security", "5.2.17": "Performance", "5.2.18": "Security",
    "5.3.1": "Availability", "5.3.2": "Availability", "5.3.3": "Performance, Capacity",
    "5.3.4": "Fault", "5.3.5": "Performance", "5.3.6": "Performance",
    "5.3.7": "Performance, Anomaly", "5.3.8": "Security", "5.3.9": "Capacity, Performance",
    "5.3.10": "Performance", "5.3.11": "Security, Anomaly", "5.3.12": "Fault",
    "5.4.1": "Availability", "5.4.2": "Availability", "5.4.3": "Performance, Capacity",
    "5.4.4": "Security", "5.4.5": "Capacity", "5.4.6": "Fault, Performance",
    "5.4.7": "Security", "5.4.8": "Security", "5.4.9": "Performance, Anomaly",
    "5.4.10": "Security", "5.4.11": "Performance",
    "5.5.1": "Availability", "5.5.2": "Availability", "5.5.3": "Performance",
    "5.5.4": "Availability", "5.5.5": "Availability", "5.5.6": "Fault",
    "5.5.7": "Performance, Capacity", "5.5.8": "Performance", "5.5.9": "Performance",
    "5.5.10": "Performance, Capacity",
    "5.6.1": "Capacity", "5.6.2": "Security, Anomaly", "5.6.3": "Availability",
    "5.6.4": "Security", "5.6.5": "Capacity", "5.6.6": "Security",
    "5.6.7": "Configuration, Compliance", "5.6.8": "Performance",
    "5.6.9": "Performance", "5.6.10": "Security", "5.6.11": "Capacity",
    "5.6.12": "Performance, Capacity",
    "5.7.1": "Performance, Capacity", "5.7.2": "Anomaly", "5.7.3": "Performance, Capacity",
    "5.7.4": "Performance, Security", "5.7.5": "Security", "5.7.6": "Security",
    "5.7.7": "Performance", "5.7.8": "Performance", "5.7.9": "Security",
    "5.7.10": "Anomaly, Security",
    "5.8.1": "Availability", "5.8.2": "Availability", "5.8.3": "Fault",
    "5.8.4": "Configuration", "5.8.5": "Compliance", "5.8.6": "Compliance",
    "5.8.7": "Configuration", "5.8.8": "Availability",
}


def infer_type(uc_id: str, title: str) -> str:
    if uc_id in TYPE_BY_UC:
        return TYPE_BY_UC[uc_id]
    title_lower = title.lower()
    for pattern, mtype in TITLE_KEYWORDS:
        if re.search(pattern, title_lower, re.I):
            return mtype
    return "Performance"  # default


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by ### UC-5. to get blocks (keep the delimiter with the following block)
    blocks = re.split(r"(?=### UC-5\.\d+\.\d+ · )", content)
    out = []
    for block in blocks:
        if not block.strip():
            out.append(block)
            continue
        match = re.match(r"### (UC-5\.\d+\.\d+) · ([^\n]+)", block)
        if not match:
            out.append(block)
            continue
        uc_full, title = match.group(1), match.group(2).strip()
        uc_id = uc_full.replace("UC-", "")  # e.g. 5.1.1
        mtype = infer_type(uc_id, title)

        # Insert "- **Monitoring type:** <type>" after the first "- **Difficulty:**" line in this block
        difficulty_pat = re.compile(
            r"^(- \*\*Difficulty:\*\* .+)$",
            re.MULTILINE,
        )
        new_block, n = difficulty_pat.subn(
            r"\1\n- **Monitoring type:** " + mtype,
            block,
            count=1,
        )
        if n == 0:
            # No Difficulty line in this block (e.g. header), leave as is
            new_block = block
        out.append(new_block)

    with open(FILE, "w", encoding="utf-8") as f:
        f.write("".join(out))
    print("Done. Added Monitoring type to all UC blocks.")


if __name__ == "__main__":
    main()
