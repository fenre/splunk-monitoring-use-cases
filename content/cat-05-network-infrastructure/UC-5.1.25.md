<!-- AUTO-GENERATED from UC-5.1.25.json — DO NOT EDIT -->

---
id: "5.1.25"
title: "Network Configuration Drift Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.25 · Network Configuration Drift Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Configuration, Security

*We help you know early when something looks wrong with network configuration drift detection so the team can act before it grows into a bigger outage.*

---

## Description

Running config differs from baseline/golden config.

## Value

Compliance teams detect network configuration drift by comparing running configurations against golden baselines, identifying unauthorized or undocumented changes that create security and operational risk.

## Implementation

Run diff (e.g., `diff running golden`) via Oxidized hooks or custom script. Ingest diff output or Git commit metadata. Store golden configs in Git; compare after each backup. Alert on any non-whitelisted drift. Use `git diff` or `rancid -d` output as sourcetype.

## Detailed Implementation

### Prerequisites
* Configuration drift detection data. Requires comparison of current running-config against a known-good baseline (golden config). Data from backup tools (RANCID, Oxidized) diffs, or Cisco DNA Center compliance engine. Data in `index=network` with `sourcetype=network:config:diff` or similar.
* Configuration drift: unauthorized or undocumented changes from the approved baseline. Causes security vulnerabilities, compliance failures, and unexpected behavior. Automated comparison of running vs golden config detects drift.

### Step 1 — - Configure data collection
```
# Scripted input to compare configs
[script:///opt/splunk/etc/apps/network_mon/bin/config_drift.sh]
interval = 86400
sourcetype = network:config:drift
index = network

# config_drift.sh
#!/bin/bash
GOLDEN_DIR="/var/configs/golden"
CURRENT_DIR="/var/backups/network"
for f in "$CURRENT_DIR"/*.cfg; do
    device=$(basename "$f" .cfg)
    golden="$GOLDEN_DIR/$device.cfg"
    if [ -f "$golden" ]; then
        diff_count=$(diff "$golden" "$f" | grep -c "^[<>]" 2>/dev/null)
        echo "device=$device drift_lines=$diff_count golden=$golden current=$f"
    fi
done
```
Verify:
```spl
index=network sourcetype="network:config:drift" earliest=-2d
| stats latest(drift_lines) by device
| sort -latest(drift_lines)
```

### Step 2 — - Create the search and alert

**Primary search -- Configuration drift detection:**
```spl
index=network sourcetype="network:config:drift" earliest=-2d
| eval device=coalesce(device, hostname, host)
| eval drift=tonumber(drift_lines)
| lookup network_devices.csv hostname AS device OUTPUT device_type, site, criticality
| eval severity=case(
    drift > 50, "CRITICAL -- major configuration drift (".drift." lines differ)",
    drift > 20, "WARNING -- significant drift detected",
    drift > 0, "INFO -- minor drift",
    1==1, "OK")
| where severity != "OK"
| table device, device_type, site, criticality, drift, severity
| sort severity, -drift
```

### Step 3 — - Validate
(a) Review diff output for specific changes: access the backup tool's diff viewer.
(b) Cross-reference with change management system for approved changes.
(c) Identify if drift is security-relevant (ACL changes, authentication changes).

### Step 4 — - Operationalize
Dashboard ("Network -- Configuration Drift"):
* Row 1 -- Single-value: "Devices with drift", "Major drift (>50 lines)", "Compliant devices".
* Row 2 -- Drift severity table.

Alert: Critical (major drift on critical device): investigate unauthorized changes.

### Step 5 — - Troubleshooting

* **Expected drift after approved change** -- Update the golden config baseline after verified changes. Document the change ticket reference.

* **Security-relevant drift** -- ACL, authentication, or encryption configuration changes require immediate security review. Compare with change management tickets.

* **Drift on many devices simultaneously** -- May indicate bulk configuration push (approved or not). Check change management and automation tool logs.

## SPL

```spl
index=network sourcetype=config_drift OR sourcetype=git:commit
| search "diff" OR "drift" OR "changed" OR "modified"
| rex "device[=:]\s*(?<device>\S+)" | rex "lines?\s*(?<lines_changed>\d+)"
| stats count as drift_events, values(diff_summary) as changes by device, host
| where drift_events > 0
| table device host drift_events changes
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.command All_Changes.action span=1h
| sort -count
```

## Visualization

Table (device, drift count, summary), Timeline (drift events), Single value (devices with drift).

## Known False Positives

Intentional hotfixes, emergency ACL inserts, and lab merges create drift you want—use allowlists and ticket IDs in comments.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
