#!/usr/bin/env python3
"""
Assign the correct Monitoring type to every use case by reviewing title + value.
Uses: OVERRIDES, NETWORK_TYPE_BY_UC, then refined value/title rules, then EXPLICIT_CORRECT.
Outputs monitoring_type_mapping.json. Run apply_monitoring_types_to_md.py after.
"""
import json
import re
from pathlib import Path

from monitoring_type_overrides import OVERRIDES, NETWORK_TYPE_BY_UC

USE_CASES_DIR = Path(__file__).resolve().parent
UC_LIST_PATH = USE_CASES_DIR / "uc_list.json"
OUTPUT_PATH = USE_CASES_DIR / "monitoring_type_mapping.json"

# Value patterns (checked first) - order matters; first match wins
VALUE_PATTERNS = [
    (r"\b(compliance|audit trail|SOX|PCI|HIPAA|posture|regulatory)\b", "Compliance"),
    (r"\b(unauthorized|privilege escalation|attack|compromise|intrusion|rootkit|malware|threat|exploit)\b", "Security"),
    (r"\b(availability|uptime|failover|health|stopped services|offline|service.*fail|replication)\b", "Availability"),
    (r"\b(failure|crash|panic|OOM|hardware failure|corruption|read-only|degradation|stale|BSOD)\b", "Fault"),
    (r"\b(exhaustion|full filesystem|capacity planning|procurement|overflow|exhaust)\b", "Capacity"),
    (r"\b(config change|drift|modification|parameter change|time sync|clock)\b", "Configuration"),
    (r"\b(anomaly|flapping|instability|flood|runaway)\b", "Anomaly"),
]

# Title patterns (when no value match)
TITLE_PATTERNS = [
    (r"\b(up.?down|state|status|health|failover|tunnel|peer|adjacency|offline|uptime|availability|reload)\b", "Availability"),
    (r"\b(utilization|throughput|latency|response time|error rate|jitter|bandwidth|cpu|memory|rssi|signal|saturation|load)\b", "Performance"),
    (r"\b(acl|deny|threat|auth|vpn|rogue|ids|ips|policy violation|botnet|c2|security|malware|dlp|brute|unauthorized|vulnerability|login)\b", "Security"),
    (r"\b(config|change|drift|policy change|audit)\b", "Configuration"),
    (r"\b(exhaustion|pool|scope|trending|capacity|queue depth|budget|forecast)\b", "Capacity"),
    (r"\b(environmental|power|fan|hardware|failure|temperature|humidity|sensor|panic|crash|oom)\b", "Fault"),
    (r"\b(flapping|anomaly|instability|storm)\b", "Anomaly"),
    (r"\b(compliance|backup|posture|change window)\b", "Compliance"),
]

# Explicit correct type for UCs where rules would assign wrong type (reviewed per use case)
EXPLICIT_CORRECT = {
    # Cat 1.1 - Linux
    "1.1.34": "Fault",       # RAID Array Degradation - data loss risk
    "1.1.37": "Fault",      # NFS Mount Stale Handle
    "1.1.42": "Fault",      # SSD Wear - predictive failure
    "1.1.54": "Security",  # Network Namespace - container escape
    "1.1.57": "Security",  # ARP Table Overflow - spoofing
    "1.1.80": "Availability",  # Systemd Unit Failures
    "1.1.82": "Fault",     # D-State Process - hang/deadlock
    "1.1.86": "Fault",     # Fork Bomb
    "1.1.89": "Anomaly",   # Syslog Flood
    "1.1.97": "Performance",  # CPU C-State Residency
    "1.1.112": "Fault",    # Unowned File - corruption
    "1.1.114": "Capacity",  # Open File Handle per process
    "1.1.119": "Fault",    # Defunct Zombie accumulation
    # Cat 1.2 - Windows
    "1.2.45": "Configuration",  # W32Time - time sync
    "1.2.52": "Availability",  # NIC Teaming Failover
    "1.2.58": "Fault",     # Storage Spaces Health
    "1.2.62": "Capacity",  # TCP Connection State - port exhaustion
    "1.2.68": "Fault",     # NTFS Corruption
    "1.2.73": "Performance",  # LDAP Query Performance
    "1.2.85": "Availability",  # IIS App Pool Crashes
    "1.2.88": "Fault",     # Windows Search Indexer
    "1.2.89": "Availability, Fault",  # Unexpected Restarts
}


def from_value(value: str) -> str | None:
    v = (value or "").lower()
    for pattern, mtype in VALUE_PATTERNS:
        if re.search(pattern, v, re.I):
            return mtype
    return None


def from_title(title: str) -> str:
    t = (title or "").lower()
    for pattern, mtype in TITLE_PATTERNS:
        if re.search(pattern, t, re.I):
            return mtype
    return "Performance"


def get_correct_type(uc_id: str, title: str, value: str) -> str:
    if uc_id in OVERRIDES:
        return OVERRIDES[uc_id]
    if uc_id in EXPLICIT_CORRECT:
        return EXPLICIT_CORRECT[uc_id]
    if uc_id in NETWORK_TYPE_BY_UC:
        return NETWORK_TYPE_BY_UC[uc_id]
    from_val = from_value(value)
    from_tit = from_title(title)
    if from_val and from_val in ("Compliance", "Fault", "Security", "Configuration", "Availability"):
        return from_val
    return from_tit


def main():
    uc_list = json.loads(UC_LIST_PATH.read_text(encoding="utf-8"))
    mapping = {}
    for uc_id, data in uc_list.items():
        title = data.get("title", "")
        value = data.get("value", "")
        mapping[uc_id] = get_correct_type(uc_id, title, value)
    OUTPUT_PATH.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(mapping)} entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
