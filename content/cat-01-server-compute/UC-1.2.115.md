---
id: "1.2.115"
title: "Logon Session Anomalies (Type 3 / Network Logon)"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.115 · Logon Session Anomalies (Type 3 / Network Logon)

## Description

Network logons (Type 3) from unexpected sources indicate lateral movement with stolen credentials. Baselining normal patterns reveals compromised accounts.

## Value

Network logons (Type 3) from unexpected sources indicate lateral movement with stolen credentials. Baselining normal patterns reveals compromised accounts.

## Implementation

Monitor Type 3 (Network) logons across all systems. Build baseline of normal logon patterns: which accounts log into which systems from where. Alert on accounts that suddenly access many more systems than usual (lateral movement), network logons from unusual subnets, and logons using service accounts from non-service IPs. Exclude machine accounts (ending in $) for noise reduction. Combine with EventCode 4648 (explicit credentials).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4624).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Type 3 (Network) logons across all systems. Build baseline of normal logon patterns: which accounts log into which systems from where. Alert on accounts that suddenly access many more systems than usual (lateral movement), network logons from unusual subnets, and logons using service accounts from non-service IPs. Exclude machine accounts (ending in $) for noise reduction. Combine with EventCode 4648 (explicit credentials).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=4624 Logon_Type=3
| eval src=coalesce(Source_Network_Address, IpAddress, "unknown")
| stats dc(host) as TargetCount values(host) as Targets count by TargetUserName, src
| where TargetCount>5
| sort -TargetCount
```

Understanding this SPL

**Logon Session Anomalies (Type 3 / Network Logon)** — Network logons (Type 3) from unexpected sources indicate lateral movement with stolen credentials. Baselining normal patterns reveals compromised accounts.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **src** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by TargetUserName, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where TargetCount>5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

Understanding this CIM / accelerated SPL

**Logon Session Anomalies (Type 3 / Network Logon)** — Network logons (Type 3) from unexpected sources indicate lateral movement with stolen credentials. Baselining normal patterns reveals compromised accounts.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network diagram (account-to-host), Timechart (logon volume), Alert on anomalous spread.

## SPL

```spl
index=wineventlog EventCode=4624 Logon_Type=3
| eval src=coalesce(Source_Network_Address, IpAddress, "unknown")
| stats dc(host) as TargetCount values(host) as Targets count by TargetUserName, src
| where TargetCount>5
| sort -TargetCount
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

## Visualization

Network diagram (account-to-host), Timechart (logon volume), Alert on anomalous spread.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
