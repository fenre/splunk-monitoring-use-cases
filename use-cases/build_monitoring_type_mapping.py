#!/usr/bin/env python3
"""
Build monitoring_type_mapping.json: correct Monitoring type for every use case.
Uses: EXPLICIT_CORRECT (per-UC reviewed), OVERRIDES, NETWORK_TYPE_BY_UC (5.1–5.8), then value/title inference.
"""
import json
import re
from pathlib import Path

from monitoring_type_overrides import OVERRIDES, NETWORK_TYPE_BY_UC, EXPLICIT_CORRECT

USE_CASES_DIR = Path(__file__).resolve().parent
UC_LIST_PATH = USE_CASES_DIR / "uc_list.json"
OUTPUT_PATH = USE_CASES_DIR / "monitoring_type_mapping.json"

# Value line keywords (checked first) -> type. Order matters.
VALUE_KEYWORDS = [
    (r"\b(compliance|audit trail|SOX|PCI|HIPAA|posture|regulatory)\b", "Compliance"),
    (r"\b(unauthorized|privilege escalation|attack|compromise|intrusion|rootkit|malware|threat|exploit)\b", "Security"),
    (r"\b(availability|uptime|failover|health|stopped services|offline|service.*fail|replication)\b", "Availability"),
    (r"\b(failure|crash|panic|OOM|hardware failure|corruption|read-only|degradation|stale|BSOD)\b", "Fault"),
    (r"\b(exhaustion|full filesystem|capacity planning|procurement|overflow|exhaust)\b", "Capacity"),
    (r"\b(config change|drift|modification|parameter change|time sync|clock)\b", "Configuration"),
    (r"\b(anomaly|flapping|instability|flood|runaway)\b", "Anomaly"),
]

# Title keywords (if no value match)
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


def infer_from_value(value: str) -> str | None:
    v = (value or "").lower()
    for pattern, mtype in VALUE_KEYWORDS:
        if re.search(pattern, v, re.I):
            return mtype
    return None


def infer_from_title(title: str) -> str:
    t = (title or "").lower()
    for pattern, mtype in TITLE_KEYWORDS:
        if re.search(pattern, t, re.I):
            return mtype
    return "Performance"


def infer_type(uc_id: str, title: str, value: str) -> str:
    # Per-UC reviewed correct type (double-checked list)
    if uc_id in EXPLICIT_CORRECT:
        return EXPLICIT_CORRECT[uc_id]
    if uc_id in OVERRIDES:
        return OVERRIDES[uc_id]
    if uc_id in NETWORK_TYPE_BY_UC:
        return NETWORK_TYPE_BY_UC[uc_id]
    from_title = infer_from_title(title)
    from_val = infer_from_value(value)
    if from_val and from_val in ("Compliance", "Fault", "Security", "Configuration", "Availability"):
        return from_val
    return from_title


def main():
    uc_list = json.loads(UC_LIST_PATH.read_text(encoding="utf-8"))
    mapping = {}
    for uc_id, data in uc_list.items():
        title = data.get("title", "")
        value = data.get("value", "")
        mapping[uc_id] = infer_type(uc_id, title, value)
    OUTPUT_PATH.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(mapping)} entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
