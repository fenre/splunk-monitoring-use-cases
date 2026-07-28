#!/usr/bin/env python3
"""Final parent-review corrections for the UC-1.1.24–UC-1.1.43 batch."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content" / "cat-01-server-compute"

PROSE = {
    "1.1.24": {
        "description": "Reports one row per Linux host and complete five-minute bucket when more than five indexed kernel-transport journal records have priority 0 (emergency) through 3 (error). The row reports the qualifying record count, average records per minute, first and last event times, observed priorities, boot IDs, optional kernel device or subsystem context, and one sample message.",
    },
    "1.1.26": {
        "description": "Measures five-minute CPU frequency-transition rates from successive Linux CPUFreq `stats/total_trans` samples, separately for each host and kernel policy. A result requires sufficient observation time, an enabled host/policy threshold, a rate above that threshold, and no active exact-key exception. Counter decreases are treated as resets, while `scaling_cur_freq` is shown only as point-in-time context.",
        "value": "Detecting unexpected transition churn helps platform engineers identify governor, firmware, workload, or power-policy changes before they compound latency regressions. Policy-specific baselines reduce noise across dissimilar drivers, while retained driver, governor, CPU set, rate, and raw counters improve comparison before kernel or firmware changes.",
    },
    "1.1.27": {
        "description": "Reports one row per Linux virtual machine only when three consecutive, complete five-minute buckets each average at least 5.0 percentage points of aggregate CPU steal. It validates the collector's percentage against raw counter deltas, removes repeated sample identities, and excludes only exact hosts covered by a currently valid change record.",
    },
    "1.1.28": {
        "description": "Reports one row per Linux host when the busiest included CPU handles at least three times its equal-share portion of numeric hardware-interrupt increments in each of two consecutive complete five-minute buckets, with at least 10,000 interrupts and two valid included CPUs in both buckets. The result identifies the busiest CPU and reports counts, percentages, core coverage, and concentration ratios.",
        "value": "Detecting sustained interrupt concentration helps platform teams correct a stopped or misconfigured balancing service, unintended affinity, or overloaded queue before interrupt handling contributes to packet loss, storage latency, or uneven application performance. Host, core, load volume, and concentration ratio improve focused investigation.",
    },
    "1.1.31": {
        "description": "Reports a host when the newest default-size HugeTLB pool snapshot in each of three closely spaced five-minute buckets has less than 10 percent unreserved headroom. It distinguishes allocated pages from pages committed by reservations and preserves the kernel's page counts and kilobyte fields for triage.",
    },
    "1.1.33": {
        "description": "Reports one row per Linux host, filesystem, and mount point when the latest valid `df.sh` inode sample in the preceding 15 minutes is at least 85 percentage points used or has 10,000 or fewer free inodes. It marks a row critical at 95 percentage points used or 1,000 or fewer free inodes and reports both relative and absolute headroom.",
    },
    "1.1.35": {
        "description": "Tracks the latest LVM2 thin-pool data-area and metadata-area utilization for each Linux host, volume group, and pool. It reports the percentages separately, rejects malformed measurements, enriches the result with pool size, volume-group extension headroom, dmeventd monitoring state, and full-pool policy, and applies an exact time-bounded exception only after a breach.",
        "value": "Detecting thin-pool data or metadata exhaustion early helps prevent disrupted writes across multiple thin volumes. Pool-specific measurements, volume-group free extents, monitoring state, and full-pool policy improve storage operators' ability to validate growth and extension headroom before documented full-pool behavior is reached.",
    },
    "1.1.36": {
        "value": "Detecting the first failed multipath path helps Linux and storage teams prevent a later path loss from turning degraded redundancy into an outage. Preserved map, path, host, state, and message context improves investigation of HBA, fabric, target-port, configuration, and path-flapping problems even while I/O still succeeds.",
    },
    "1.1.37": {
        "value": "Detecting stale NFS handles promptly helps Linux, application, and storage owners prevent repeated reads, writes, traversal, backup, build, or database failures from widening an outage. Source-preserving evidence improves identification of the affected path and server-side change even when the mount remains present.",
    },
    "1.1.39": {
        "description": "Reports one row per five-minute bucket, Linux host, and extracted ext4 device when at least one collected record matches a kernel-defined `EXT4-fs error (device ...)` form and yields a function and source line. It counts matching errors and reports exact journal-recovery-required or recovery-complete messages for that host, device, and bucket; recovery context never cancels an error.",
    },
    "1.1.41": {
        "description": "Reports the newest failing row per host and stable device key from a closed 35-minute search interval when smartctl reports a failed health verdict, its current ATA prefailure-threshold bit is set, or an NVMe critical-warning value is nonzero. It preserves device identity, protocol, model, exit mask, normalized verdicts, and reason while excluding collector errors from health conclusions.",
    },
}


def load_sidecar(uc_id: str) -> tuple[Path, dict]:
    path = CONTENT / f"UC-{uc_id}.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


for uc_id, fields in PROSE.items():
    path, payload = load_sidecar(uc_id)
    payload.update(fields)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

path, payload = load_sidecar("1.1.36")
payload["knownFalsePositives"] = (
    "1. **Approved fabric failover test** — A SAN, HBA, cable, or target-port "
    "test deliberately moves traffic. Correlate the exact host, path, map, and "
    "event time with the approved change before suppressing it.\n\n"
    "2. **Operator-issued multipathd command** — `multipathd fail path` creates "
    "a real transition during controlled maintenance. Confirm the terminal or "
    "automation record and retain the failure as test evidence.\n\n"
    "3. **Duplicate syslog ingestion** — Overlapping file monitors or a "
    "forwarding loop can replay one daemon message. Compare `_raw`, host, source, "
    "and original timestamp; fix collection instead of widening the threshold.\n\n"
    "4. **Synthetic control event** — A test record can enter a production index "
    "without a marker. Require test events to carry a dedicated host or index and "
    "remove them from operational alert routing.\n\n"
    "**Suppression mechanism:** use a time-bound exception lookup keyed by "
    "`host`, `path`, and `map`, with change ID, owner, start, and expiry. Repeated "
    "down/up changes, `reinstate failed`, or checker errors are not false positives "
    "merely because another path still carries I/O."
)
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
