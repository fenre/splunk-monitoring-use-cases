<!-- AUTO-GENERATED from UC-9.1.15.json — DO NOT EDIT -->

---
id: "9.1.15"
title: "Kerberoasting Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.15 · Kerberoasting Detection

## Description

Attackers request weakly encrypted TGS tickets for service accounts to crack passwords offline. Focused Kerberoasting detection complements generic Kerberos monitoring.

## Value

Attackers request weakly encrypted TGS tickets for service accounts to crack passwords offline. Focused Kerberoasting detection complements generic Kerberos monitoring.

## Implementation

Forward 4769 from DCs. Flag RC4 (0x17) TGS requests in bulk per user; tune thresholds for service accounts that legitimately use RC4. Enforce AES for sensitive SPNs in AD and rotate krbtgt on schedule.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4769 — Kerberos service ticket requested).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward 4769 from DCs. Flag RC4 (0x17) TGS requests in bulk per user; tune thresholds for service accounts that legitimately use RC4. Enforce AES for sensitive SPNs in AD and rotate krbtgt on schedule.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count, values(Service_Name) as spns by Account_Name
| where count >= 5
| sort -count
```

Understanding this SPL

**Kerberoasting Detection** — Attackers request weakly encrypted TGS tickets for service accounts to crack passwords offline. Focused Kerberoasting detection complements generic Kerberos monitoring.

Documented **Data sources**: Security Event Log (4769 — Kerberos service ticket requested). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Account_Name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count >= 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action='success'
  by Authentication.user Authentication.src span=1h
| where count > 50
```

Understanding this CIM / accelerated SPL

**Kerberoasting Detection** — Attackers request weakly encrypted TGS tickets for service accounts to crack passwords offline. Focused Kerberoasting detection complements generic Kerberos monitoring.

Documented **Data sources**: Security Event Log (4769 — Kerberos service ticket requested). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 50` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, SPN, request count), Bar chart (Kerberoasting candidates by OU), Timeline (spikes).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count, values(Service_Name) as spns by Account_Name
| where count >= 5
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action='success'
  by Authentication.user Authentication.src span=1h
| where count > 50
```

## Visualization

Table (user, SPN, request count), Bar chart (Kerberoasting candidates by OU), Timeline (spikes).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
