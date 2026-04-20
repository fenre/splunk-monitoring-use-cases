---
id: "5.1.6"
title: "Spanning Tree Topology Change"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.6 · Spanning Tree Topology Change

## Description

STP topology changes cause brief disruption and MAC flushing. Root bridge changes are critical.

## Value

STP topology changes cause brief disruption and MAC flushing. Root bridge changes are critical.

## Implementation

Forward syslog. Alert on root bridge changes (critical). Track topology change frequency per VLAN.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog. Alert on root bridge changes (critical). Track topology change frequency per VLAN.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE"
| stats count by host | where count > 5 | sort -count
```

Understanding this SPL

**Spanning Tree Topology Change** — STP topology changes cause brief disruption and MAC flushing. Root bridge changes are critical.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timeline, Bar chart by VLAN.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE"
| stats count by host | where count > 5 | sort -count
```

## Visualization

Table, Timeline, Bar chart by VLAN.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
