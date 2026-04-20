---
id: "6.1.29"
title: "MDS Zone Configuration Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.1.29 · MDS Zone Configuration Compliance

## Description

Zoning controls which initiators can communicate with which targets. Misconfigured zones create security risks (unauthorized access) and operational risks (accidental data access). Tracking zone changes and validating against a known-good baseline prevents drift.

## Value

Zoning controls which initiators can communicate with which targets. Misconfigured zones create security risks (unauthorized access) and operational risks (accidental data access). Tracking zone changes and validating against a known-good baseline prevents drift.

## Implementation

Export zone configuration periodically via NX-API. Maintain a baseline lookup of approved zones per VSAN. Detect zone additions, removals, and activations via syslog. Alert on any zone change outside change windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `cisco:mds` syslog, scripted input (MDS NX-API / CLI).
• Ensure the following data sources are available: MDS syslog (zone change events), NX-API CLI (`show zone`, `show zoneset active`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export zone configuration periodically via NX-API. Maintain a baseline lookup of approved zones per VSAN. Detect zone additions, removals, and activations via syslog. Alert on any zone change outside change windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:mds" "ZONE" ("added" OR "removed" OR "activated" OR "changed")
| stats count by switch, vsan_id, zone_name, action, user
| append [| inputlookup mds_approved_zones | eval source="baseline"]
| stats values(source) as sources by vsan_id, zone_name
| where NOT match(sources,"baseline")
| table vsan_id, zone_name, sources
```

Understanding this SPL

**MDS Zone Configuration Compliance** — Zoning controls which initiators can communicate with which targets. Misconfigured zones create security risks (unauthorized access) and operational risks (accidental data access). Tracking zone changes and validating against a known-good baseline prevents drift.

Documented **Data sources**: MDS syslog (zone change events), NX-API CLI (`show zone`, `show zoneset active`). **App/TA** (typical add-on context): `cisco:mds` syslog, scripted input (MDS NX-API / CLI). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:mds. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:mds". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch, vsan_id, zone_name, action, user** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Appends rows from a subsearch with `append`.
• `stats` rolls up events into metrics; results are split **by vsan_id, zone_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where NOT match(sources,"baseline")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MDS Zone Configuration Compliance**): table vsan_id, zone_name, sources

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**MDS Zone Configuration Compliance** — Zoning controls which initiators can communicate with which targets. Misconfigured zones create security risks (unauthorized access) and operational risks (accidental data access). Tracking zone changes and validating against a known-good baseline prevents drift.

Documented **Data sources**: MDS syslog (zone change events), NX-API CLI (`show zone`, `show zoneset active`). **App/TA** (typical add-on context): `cisco:mds` syslog, scripted input (MDS NX-API / CLI). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (zone changes), Timeline (change events), Diff view (current vs baseline).

## SPL

```spl
index=network sourcetype="cisco:mds" "ZONE" ("added" OR "removed" OR "activated" OR "changed")
| stats count by switch, vsan_id, zone_name, action, user
| append [| inputlookup mds_approved_zones | eval source="baseline"]
| stats values(source) as sources by vsan_id, zone_name
| where NOT match(sources,"baseline")
| table vsan_id, zone_name, sources
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.user | sort - count
```

## Visualization

Table (zone changes), Timeline (change events), Diff view (current vs baseline).

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
