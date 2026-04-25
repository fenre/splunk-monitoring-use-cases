<!-- AUTO-GENERATED from UC-2.3.3.json — DO NOT EDIT -->

---
id: "2.3.3"
title: "VM Lifecycle Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.3.3 · VM Lifecycle Events

## Description

Audit trail for VM start, stop, migrate, and crash events. Essential for troubleshooting and change management in open-source virtualization.

## Value

Audit trail for VM start, stop, migrate, and crash events. Essential for troubleshooting and change management in open-source virtualization.

## Implementation

Forward `/var/log/libvirt/qemu/*.log` and libvirt system logs. Parse VM name and event type. Alert on unexpected VM shutdowns or crashes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Syslog, libvirt logs.
• Ensure the following data sources are available: `/var/log/libvirt/`, syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward `/var/log/libvirt/qemu/*.log` and libvirt system logs. Parse VM name and event type. Alert on unexpected VM shutdowns or crashes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=syslog source="/var/log/libvirt/*"
| search "shutting down" OR "starting up" OR "migrating" OR "crashed"
| rex "domain (?<vm_name>\S+)"
| table _time host vm_name _raw
| sort -_time
```

Understanding this SPL

**VM Lifecycle Events** — Audit trail for VM start, stop, migrate, and crash events. Essential for troubleshooting and change management in open-source virtualization.

Documented **Data sources**: `/var/log/libvirt/`, syslog. **App/TA** (typical add-on context): Syslog, libvirt logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **VM Lifecycle Events**): table _time host vm_name _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table (VM, event, time).

## SPL

```spl
index=virtualization sourcetype=syslog source="/var/log/libvirt/*"
| search "shutting down" OR "starting up" OR "migrating" OR "crashed"
| rex "domain (?<vm_name>\S+)"
| table _time host vm_name _raw
| sort -_time
```

## Visualization

Events timeline, Table (VM, event, time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
