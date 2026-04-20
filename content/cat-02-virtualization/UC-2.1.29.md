---
id: "2.1.29"
title: "VM Affinity and Anti-Affinity Rule Violations"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.29 · VM Affinity and Anti-Affinity Rule Violations

## Description

Anti-affinity rules ensure redundant VMs (e.g., HA pairs, database replicas) run on different hosts. Rule violations mean a single host failure can take down both instances. Affinity rules keep related VMs together for performance. DRS may violate rules when resources are constrained.

## Value

Anti-affinity rules ensure redundant VMs (e.g., HA pairs, database replicas) run on different hosts. Rule violations mean a single host failure can take down both instances. Affinity rules keep related VMs together for performance. DRS may violate rules when resources are constrained.

## Implementation

Collect vCenter events via Splunk_TA_vmware. DRS logs rule violations as events. Also create a scripted input using PowerCLI to enumerate cluster rules and check current VM placement. Alert immediately on anti-affinity violations in production. Review affinity rule compliance weekly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`, cluster rule configuration.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect vCenter events via Splunk_TA_vmware. DRS logs rule violations as events. Also create a scripted input using PowerCLI to enumerate cluster rules and check current VM placement. Alert immediately on anti-affinity violations in production. Review affinity rule compliance weekly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" event_type="DrsRuleViolatedEvent"
| table _time, cluster, rule_name, vm_name, host, message
| sort -_time
```

Understanding this SPL

**VM Affinity and Anti-Affinity Rule Violations** — Anti-affinity rules ensure redundant VMs (e.g., HA pairs, database replicas) run on different hosts. Rule violations mean a single host failure can take down both instances. Affinity rules keep related VMs together for performance. DRS may violate rules when resources are constrained.

Documented **Data sources**: `sourcetype=vmware:events`, cluster rule configuration. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **VM Affinity and Anti-Affinity Rule Violations**): table _time, cluster, rule_name, vm_name, host, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (violated rules), Status grid (rule compliance), Alert panel.

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
index=vmware sourcetype="vmware:events" event_type="DrsRuleViolatedEvent"
| table _time, cluster, rule_name, vm_name, host, message
| sort -_time
```

## Visualization

Table (violated rules), Status grid (rule compliance), Alert panel.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
