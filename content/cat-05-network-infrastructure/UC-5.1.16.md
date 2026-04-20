---
id: "5.1.16"
title: "Route Table Flapping"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.16 · Route Table Flapping

## Description

Unstable routes cause packet loss and reachability failures. Detecting flapping routes prevents cascading network outages across your infrastructure.

## Value

Unstable routes cause packet loss and reachability failures. Detecting flapping routes prevents cascading network outages across your infrastructure.

## Implementation

Collect syslog from all routers. Alert on >5 route changes for the same prefix in 10 minutes. Correlate with interface flaps. Use `streamstats` to detect patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect syslog from all routers. Alert on >5 route changes for the same prefix in 10 minutes. Correlate with interface flaps. Use `streamstats` to detect patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "ROUTING" OR "RT_ENTRY" OR "%DUAL-5-NBRCHANGE" OR "%BGP-5-ADJCHANGE" OR "%OSPF-5-ADJCHG"
| rex "(?<protocol>BGP|OSPF|EIGRP).*?(?<prefix>\d+\.\d+\.\d+\.\d+/?\d*)"
| bin _time span=10m | stats count as changes by _time, host, protocol, prefix
| where changes > 5 | sort -changes
```

Understanding this SPL

**Route Table Flapping** — Unstable routes cause packet loss and reachability failures. Detecting flapping routes prevents cascading network outages across your infrastructure.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, host, protocol, prefix** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where changes > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (flapping events), Table (prefix, host, count), Line chart (change frequency).

## SPL

```spl
index=network sourcetype="cisco:ios" "ROUTING" OR "RT_ENTRY" OR "%DUAL-5-NBRCHANGE" OR "%BGP-5-ADJCHANGE" OR "%OSPF-5-ADJCHG"
| rex "(?<protocol>BGP|OSPF|EIGRP).*?(?<prefix>\d+\.\d+\.\d+\.\d+/?\d*)"
| bin _time span=10m | stats count as changes by _time, host, protocol, prefix
| where changes > 5 | sort -changes
```

## Visualization

Timeline (flapping events), Table (prefix, host, count), Line chart (change frequency).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
