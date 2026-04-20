---
id: "1.1.57"
title: "ARP Table Overflow Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.57 · ARP Table Overflow Detection

## Description

ARP table overflow causes network connectivity issues and may indicate ARP spoofing attacks or network misconfiguration.

## Value

ARP table overflow causes network connectivity issues and may indicate ARP spoofing attacks or network misconfiguration.

## Implementation

Create a scripted input that counts /proc/net/arp entries and monitors /proc/sys/net/ipv4/neigh/*/gc_thresh* limits. Alert when ARP table approaches limits. Correlate with network scans or spoofing indicators.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:arp, /proc/net/arp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that counts /proc/net/arp entries and monitors /proc/sys/net/ipv4/neigh/*/gc_thresh* limits. Alert when ARP table approaches limits. Correlate with network scans or spoofing indicators.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:arp host=*
| stats count as arp_entry_count by host
| eval max_entries=1024
| where arp_entry_count > (max_entries * 0.8)
```

Understanding this SPL

**ARP Table Overflow Detection** — ARP table overflow causes network connectivity issues and may indicate ARP spoofing attacks or network misconfiguration.

Documented **Data sources**: `sourcetype=custom:arp, /proc/net/arp`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:arp. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:arp. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **max_entries** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where arp_entry_count > (max_entries * 0.8)` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Alert

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=custom:arp host=*
| stats count as arp_entry_count by host
| eval max_entries=1024
| where arp_entry_count > (max_entries * 0.8)
```

## Visualization

Gauge, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
