<!-- AUTO-GENERATED from UC-1.2.16.json — DO NOT EDIT -->

---
id: "1.2.16"
title: "DHCP Scope Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.16 · DHCP Scope Exhaustion

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when a network ran out of addresses to hand out, so new phones and laptops can still get online in busy places.*

---

## Description

When DHCP scopes run out of addresses, new devices can't get network access. Often manifests as "network down" complaints.

## Value

Scope exhaustion is a silent brownout for new clients—fixing it fast avoids an invisible outage that support hears as “wifi is weird.”

## Implementation

Forward DHCP server audit logs from `%windir%\System32\Dhcp`. Create scripted input running `Get-DhcpServerv4ScopeStatistics` to get scope utilization. Alert when any scope exceeds 90% utilization.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_windows`.
- Ensure the following data sources are available: `sourcetype=DhcpSrvLog`, DHCP audit logs.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Forward DHCP server audit logs from `%windir%\System32\Dhcp`. Create scripted input running `Get-DhcpServerv4ScopeStatistics` to get scope utilization. Alert when any scope exceeds 90% utilization.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dhcp sourcetype="DhcpSrvLog"
| where EventID=13 OR EventID=14
| stats count by Description
```

#### Understanding this SPL

**DHCP Scope Exhaustion** — When DHCP scopes run out of addresses, new devices can't get network access. Often manifests as "network down" complaints.

Documented **Data sources**: `sourcetype=DhcpSrvLog`, DHCP audit logs. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dhcp; **sourcetype**: DhcpSrvLog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=dhcp, sourcetype="DhcpSrvLog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Filters the current rows with `where EventID=13 OR EventID=14` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by Description** so each row reflects one combination of those dimensions.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per scope, Table (scope, used, available, % full), Trend line.

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
index=dhcp sourcetype="DhcpSrvLog"
| where EventID=13 OR EventID=14
| stats count by Description
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

## Visualization

Gauge per scope, Table (scope, used, available, % full), Trend line.

## Known False Positives

New sites, big events, and guest surges can exhaust a scope. Some exhaustion alerts are by design in lab or isolation VLANs; tune with subnet owners.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
