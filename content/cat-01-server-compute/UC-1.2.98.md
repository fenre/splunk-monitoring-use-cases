<!-- AUTO-GENERATED from UC-1.2.98.json — DO NOT EDIT -->

---
id: "1.2.98"
title: "NPS / RADIUS Authentication Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.98 · NPS / RADIUS Authentication Monitoring

## Description

Network Policy Server handles VPN, Wi-Fi, and 802.1X authentication. Monitoring NPS detects brute-force attacks, misconfigured policies, and unauthorized network access.

## Value

Denied and odd RADIUS attempts at the edge often show password spray, mis-set shared secrets, or devices trying the wrong VLAN policy before VPN or office Wi-Fi teams get flooded with tickets.

## Implementation

NPS logs authentication events to the Security log. Track granted (6272), denied (6273), and discarded (6274) requests. Alert on high denial rates from specific users (brute-force) or NAS devices (misconfiguration). Monitor for authentication attempts using disabled accounts or from unknown calling station IDs. Correlate with VPN gateway logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 6272, 6273, 6274, 6278).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
NPS logs authentication events to the Security log. Track granted (6272), denied (6273), and discarded (6274) requests. Alert on high denial rates from specific users (brute-force) or NAS devices (misconfiguration). Monitor for authentication attempts using disabled accounts or from unknown calling station IDs. Correlate with VPN gateway logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (6272, 6273, 6274)
| eval Result=case(EventCode=6272,"Access_Granted", EventCode=6273,"Access_Denied", EventCode=6274,"Discarded", 1=1,"Other")
| stats count by Result, UserName, CallingStationID, NASIPAddress, AuthenticationProvider
| where Result="Access_Denied"
| sort -count
```

Understanding this SPL

**NPS / RADIUS Authentication Monitoring** — Network Policy Server handles VPN, Wi-Fi, and 802.1X authentication. Monitoring NPS detects brute-force attacks, misconfigured policies, and unauthorized network access.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 6272, 6273, 6274, 6278). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Result** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by Result, UserName, CallingStationID, NASIPAddress, AuthenticationProvider** so each row reflects one combination of those dimensions.
• Filters the current rows with `where Result="Access_Denied"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (NPS 6273 as `action=failure` when tagged):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

Enable **data model acceleration** on `Authentication`. If 6273 is not in summaries, keep the `EventCode` search in Step 2.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (grant vs deny ratio), Table (denied requests), Timechart (auth attempts by hour).

## SPL

```spl
index=wineventlog EventCode IN (6272, 6273, 6274)
| eval Result=case(EventCode=6272,"Access_Granted", EventCode=6273,"Access_Denied", EventCode=6274,"Discarded", 1=1,"Other")
| stats count by Result, UserName, CallingStationID, NASIPAddress, AuthenticationProvider
| where Result="Access_Denied"
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

## Visualization

Pie chart (grant vs deny ratio), Table (denied requests), Timechart (auth attempts by hour).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
