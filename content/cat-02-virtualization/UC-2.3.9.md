---
id: "2.3.9"
title: "QEMU Process Crash and Zombie Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.3.9 · QEMU Process Crash and Zombie Detection

## Description

Each KVM VM runs as a qemu-kvm process on the host. If the process crashes, the VM dies instantly without graceful shutdown. Zombie qemu processes consume resources without running a VM. Detecting crashes enables rapid restart, while zombie detection prevents resource leaks.

## Value

Each KVM VM runs as a qemu-kvm process on the host. If the process crashes, the VM dies instantly without graceful shutdown. Zombie qemu processes consume resources without running a VM. Detecting crashes enables rapid restart, while zombie detection prevents resource leaks.

## Implementation

Monitor syslog and `/var/log/libvirt/qemu/*.log` for qemu-kvm crash messages. Create a scripted input to detect zombie processes: `ps aux | grep qemu-kvm | grep -v grep | awk '{if($8=="Z") print}'`. Alert immediately on crash events. Cross-reference with libvirt domain list to detect processes without corresponding VMs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, custom scripted input.
• Ensure the following data sources are available: Syslog, libvirt logs, process monitoring.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor syslog and `/var/log/libvirt/qemu/*.log` for qemu-kvm crash messages. Create a scripted input to detect zombie processes: `ps aux | grep qemu-kvm | grep -v grep | awk '{if($8=="Z") print}'`. Alert immediately on crash events. Cross-reference with libvirt domain list to detect processes without corresponding VMs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("qemu-kvm" AND ("killed" OR "segfault" OR "core dumped" OR "terminated"))
| rex "qemu-kvm\[(?<pid>\d+)\]"
| table _time, host, pid, _raw
| sort -_time
```

Understanding this SPL

**QEMU Process Crash and Zombie Detection** — Each KVM VM runs as a qemu-kvm process on the host. If the process crashes, the VM dies instantly without graceful shutdown. Zombie qemu processes consume resources without running a VM. Detecting crashes enables rapid restart, while zombie detection prevents resource leaks.

Documented **Data sources**: Syslog, libvirt logs, process monitoring. **App/TA** (typical add-on context): `Splunk_TA_nix`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **QEMU Process Crash and Zombie Detection**): table _time, host, pid, _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (crash events), Table (crashed VMs), Single value (active zombies).

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
index=os sourcetype=syslog ("qemu-kvm" AND ("killed" OR "segfault" OR "core dumped" OR "terminated"))
| rex "qemu-kvm\[(?<pid>\d+)\]"
| table _time, host, pid, _raw
| sort -_time
```

## Visualization

Timeline (crash events), Table (crashed VMs), Single value (active zombies).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
