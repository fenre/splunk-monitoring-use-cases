#!/usr/bin/env python3
"""Final parent-review corrections for the UC-1.1.4–UC-1.1.23 batch.

This one-shot is retained as review provenance. The substantive rewrites were
authored individually; this script applies the final cross-batch prose-gate
corrections and two explicit UC-1.1.16 audit clarifications.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content" / "cat-01-server-compute"

PROSE = {
    "1.1.4": {
        "description": "Reports one row per Linux host and block device when at least five valid `iostat` samples in the delayed ten-minute window have mean request completion time above 20 milliseconds. The row includes mean `util` only as diagnostic context; high `await` can indicate queueing or storage-path delay but does not, by itself, prove hardware saturation.",
        "value": "Detecting sustained device latency early helps an infrastructure owner correlate application slowness with the affected storage path before timeouts or backlog propagate across a service. Requiring several samples and retaining the measured latency, coverage count, and exception reason reduces escalation based on a single host-wide spike.",
    },
    "1.1.5": {
        "description": "Reports one row per Linux host when its one-minute load average, averaged within each of three consecutive five-minute buckets containing at least four samples, is at or above a host-specific ratio of logical CPUs in all three buckets. The default ratio is 1.5, so the alert represents 15 minutes of sustained runnable or uninterruptible work rather than a single sample.",
        "value": "Detecting sustained queueing gives Linux operators time to separate CPU contention from storage or kernel blocking, redistribute work, and correct stale capacity assignments before it becomes user-visible latency or an availability incident. Requiring three complete buckets reduces alerts from short compilation and startup bursts.",
    },
    "1.1.7": {
        "description": "Reports one row for each collected Linux kernel victim record whose raw text contains the specific `Killed process <pid> (<name>) total-vm:<kilobytes>kB` shape. The scheduled search evaluates one completed five-minute event-time window, extracts the victim and available memory fields, and fires when at least one parsed row exists; no count or memory-size threshold is implied.",
    },
    "1.1.12": {
        "description": "Tracks the newest valid normalized chrony or ntpq timing sample for each Linux host in a ten-minute lookback. One row is returned when that sample reports an unsynchronized daemon state or an absolute system-time offset greater than 100 milliseconds; the row preserves the collector, reference, optional stratum, and reason for triage.",
        "value": "Detecting unreliable host time helps platform teams prevent misleading event order, distributed-trace confusion, and failures in time-dependent services. The normalized result directs responders to the affected host and collector without pretending that stratum alone measures clock error.",
    },
    "1.1.13": {
        "description": "Reports one row per Linux host when the latest process snapshot in each of three consecutive closed five-minute buckets contains at least five distinct processes in zombie state. It expands the add-on's table event into process rows, recognizes both current `STAT` and legacy `S` fields, and counts numeric process identifiers rather than counting snapshot events.",
        "value": "Detecting persistent unreaped children helps operators correct faulty parent-process lifecycle handling before zombie growth consumes process identifiers and prevents new work from starting. Requiring the condition in three complete buckets reduces noise from normal exit/reap timing while preserving process names and identifiers for triage.",
    },
    "1.1.15": {
        "description": "Reports one row per Linux host and network interface when receive errors, transmit errors, or collisions increase by at least one count in the latest complete five-minute bucket. It compares cumulative counters with the preceding bucket, rejects decreases as resets, and reports both current counter values and newly observed increments.",
    },
    "1.1.16": {
        "description": "Reports the latest confirmed, active package-attributed vulnerability finding for each asset, scanner plugin, and package identity. The scanner—not a package-name lookup—determines the finding using its checks, advisory knowledge, and package-version semantics; Splunk tracks the resulting state and preserves installed and available-fix versions for investigation.",
        "value": "Using scanner-grounded package findings helps vulnerability and platform teams prioritize affected hosts without falsely declaring every similarly named installation vulnerable. Preserving scanner identity, state, version context, and collection freshness improves remediation review and exposes stale scan coverage before teams mistake silence for safety.",
    },
    "1.1.17": {
        "description": "Reports one row per Linux host and inventoried systemd service when its two most recent 60-second observations are both unhealthy. An observation is unhealthy when collection failed, the unit definition is not loaded, systemd `ActiveState` is not `active`, or `systemctl is-active` returns nonzero; the newest observation must be no more than 180 seconds old.",
        "value": "Detecting a persistent unhealthy service helps operators restore an essential daemon after a crash, failed deployment, dependency problem, or accidental stop before the outage spreads. Requiring two observations reduces alerts from brief restart transitions while preserving the exact systemd state needed for triage.",
    },
    "1.1.18": {
        "description": "Reports one row per Linux Audit event when a local user or group is created, deleted, locked, unlocked, or modified, or when a configured audit watch records a write attempt against a local identity database. It preserves the reported actor, target, operation, outcome, executable, and Audit event identifier without treating command-name text in an authentication log as proof of a change.",
        "value": "Detecting unexpected account, credential, lock-state, group, and identity-file changes helps prevent persistent unauthorized access and disruption of legitimate administration. Outcome-aware records improve comparison of the exact host, actor, process, and target with approved lifecycle work while retaining failed attempts and collection limitations.",
    },
    "1.1.19": {
        "value": "Detecting a forced read-only transition helps prevent databases, queues, package managers, and other services from continuing unsafe writes while ordinary read and process checks still appear healthy. Prompt device-level evidence lets operators protect data, stop retry loops, engage storage owners, and plan offline repair before a local fault becomes a wider outage.",
    },
    "1.1.21": {
        "description": "Reports one row per Linux Audit event identifier and host when the interpreted SYSCALL record contains an `init_module` or `finit_module` attempt. The search joins any same-event KERN_MODULE record to expose the module name and preserves process, user, success, and return-code context. A saved search running over a ten-minute lookback produces a result for every matching attempt, successful or failed.",
        "value": "Detecting unexpected kernel-module attempts helps responders prevent unapproved kernel-level code and persistence from going unnoticed. The caller, module, host role, outcome, and change record improve triage, while failed calls retain evidence of probing that a success-only search would miss.",
    },
}


def load_sidecar(uc_id: str) -> tuple[Path, dict]:
    path = CONTENT / f"UC-{uc_id}.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


for uc_id, fields in PROSE.items():
    path, payload = load_sidecar(uc_id)
    payload.update(fields)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

path, payload = load_sidecar("1.1.16")
payload["knownFalsePositives"] = payload["knownFalsePositives"].replace(
    "**Safe suppression:** suppress only",
    "**Suppression mechanism:** use a time-bound exception to suppress only",
)
payload["detailedImplementation"] = payload["detailedImplementation"].replace(
    "Store API and HEC secrets in the deployment's secret manager; never place them in SPL, lookup files, or event payloads.",
    "Store API and HEC secrets in the deployment's secret manager; never place them in SPL, lookup files, or event payloads. Configure the collector's exact `/vulns/export` API path and HEC output for `index=vulnerability sourcetype=tenable:io:software_vuln` in its protected configuration; do not disguise it as an `inputs.conf` modular input.",
)
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
