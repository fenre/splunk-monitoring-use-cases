---
id: "2.1.41"
title: "ESXi Host Coredump Configuration"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.41 · ESXi Host Coredump Configuration

## Description

When an ESXi host experiences a PSOD (Purple Screen of Death), the coredump contains critical diagnostic information. Without a properly configured dump target (network or local), the coredump is lost on reboot and root cause analysis becomes impossible. Particularly important for diskless/boot-from-SAN hosts.

## Value

When an ESXi host experiences a PSOD (Purple Screen of Death), the coredump contains critical diagnostic information. Without a properly configured dump target (network or local), the coredump is lost on reboot and root cause analysis becomes impossible. Particularly important for diskless/boot-from-SAN hosts.

## Implementation

Create scripted input via PowerCLI or SSH: `esxcli system coredump network get` and `esxcli system coredump partition get`. Run daily. Alert on hosts without any dump target configured. For stateless/diskless hosts, ensure network dump collector is configured and reachable.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (`esxcli system coredump`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input via PowerCLI or SSH: `esxcli system coredump network get` and `esxcli system coredump partition get`. Run daily. Alert on hosts without any dump target configured. For stateless/diskless hosts, ensure network dump collector is configured and reachable.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="esxi_coredump"
| stats latest(network_configured) as net_dump, latest(partition_configured) as part_dump by host
| eval dump_ok=if(net_dump="true" OR part_dump="true", "Yes", "No")
| where dump_ok="No"
| table host, net_dump, part_dump, dump_ok
```

Understanding this SPL

**ESXi Host Coredump Configuration** — When an ESXi host experiences a PSOD (Purple Screen of Death), the coredump contains critical diagnostic information. Without a properly configured dump target (network or local), the coredump is lost on reboot and root cause analysis becomes impossible. Particularly important for diskless/boot-from-SAN hosts.

Documented **Data sources**: Custom scripted input (`esxcli system coredump`). **App/TA** (typical add-on context): `Splunk_TA_vmware`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: esxi_coredump. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="esxi_coredump". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **dump_ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dump_ok="No"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **ESXi Host Coredump Configuration**): table host, net_dump, part_dump, dump_ok


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (dump config per host), Table (unconfigured hosts), Compliance percentage.

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
index=vmware sourcetype="esxi_coredump"
| stats latest(network_configured) as net_dump, latest(partition_configured) as part_dump by host
| eval dump_ok=if(net_dump="true" OR part_dump="true", "Yes", "No")
| where dump_ok="No"
| table host, net_dump, part_dump, dump_ok
```

## Visualization

Status grid (dump config per host), Table (unconfigured hosts), Compliance percentage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
