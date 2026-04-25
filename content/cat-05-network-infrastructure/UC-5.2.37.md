<!-- AUTO-GENERATED from UC-5.2.37.json — DO NOT EDIT -->

---
id: "5.2.37"
title: "Auto VPN Path Changes and Tunnel Switching (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.37 · Auto VPN Path Changes and Tunnel Switching (Meraki MX)

## Description

Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.

## Value

Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.

## Implementation

Monitor Auto VPN path optimization events. Alert on excessive changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=vpn signature="*Auto VPN*" OR signature="*path change*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Auto VPN path optimization events. Alert on excessive changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=vpn (signature="*Auto VPN*" OR signature="*path change*")
| stats count as path_change_count by tunnel_id, new_path, old_path
| where path_change_count > 3
```

Understanding this SPL

**Auto VPN Path Changes and Tunnel Switching (Meraki MX)** — Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.

Documented **Data sources**: `sourcetype=meraki type=vpn signature="*Auto VPN*" OR signature="*path change*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by tunnel_id, new_path, old_path** so each row reflects one combination of those dimensions.
• Filters the current rows with `where path_change_count > 3` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm VPN paths, tunnel states, uplinks, and device names you expect there match the Splunk view.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Path change timeline; tunnel path change distribution; convergence analysis.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn (signature="*Auto VPN*" OR signature="*path change*")
| stats count as path_change_count by tunnel_id, new_path, old_path
| where path_change_count > 3
```

## Visualization

Path change timeline; tunnel path change distribution; convergence analysis.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
