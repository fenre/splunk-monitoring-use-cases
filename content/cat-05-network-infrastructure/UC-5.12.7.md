<!-- AUTO-GENERATED from UC-5.12.7.json — DO NOT EDIT -->

---
id: "5.12.7"
title: "IMS Registration Failure Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.12.7 · IMS Registration Failure Rate

## Description

HSS/UDM or P-CSCF failures show up as elevated 401/403/timeout on REGISTER — impacts VoLTE attach and VoWiFi.

## Value

HSS/UDM or P-CSCF failures show up as elevated 401/403/timeout on REGISTER — impacts VoLTE attach and VoWiFi.

## Implementation

Break out by `visited_network` for roaming; correlate with certificate expiry on IPSec for VoWiFi.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: P-CSCF logs, IMS CDR.
• Ensure the following data sources are available: `sourcetype="ims:sip"` `method=REGISTER`, `sourcetype="stream:sip"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Break out by `visited_network` for roaming; correlate with certificate expiry on IPSec for VoWiFi.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ims sourcetype="ims:sip" method="REGISTER"
| eval fail=if(match(reply_code,"^(401|403|408|5..)$"),1,0)
| timechart span=5m sum(fail) as fails, count as attempts
| eval fail_rate=round(100*fails/attempts,2)
| where fail_rate > 5
```

Understanding this SPL

**IMS Registration Failure Rate** — HSS/UDM or P-CSCF failures show up as elevated 401/403/timeout on REGISTER — impacts VoLTE attach and VoWiFi.

Documented **Data sources**: `sourcetype="ims:sip"` `method=REGISTER`, `sourcetype="stream:sip"`. **App/TA** (typical add-on context): P-CSCF logs, IMS CDR. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ims; **sourcetype**: ims:sip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=ims, sourcetype="ims:sip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **fail** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_rate > 5` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For a spike, compare Splunk to the IMS/EPG/UCM node that serves those subscribers; align subscriber keys and time zone. Re-check DNS, Diameter link, and HSS/HSS replica lag on the same clock.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (fail rate), Bar chart (SIP reason by S-CSCF), Table (IMSI hash top failures).

## SPL

```spl
index=ims sourcetype="ims:sip" method="REGISTER"
| eval fail=if(match(reply_code,"^(401|403|408|5..)$"),1,0)
| timechart span=5m sum(fail) as fails, count as attempts
| eval fail_rate=round(100*fails/attempts,2)
| where fail_rate > 5
```

## Visualization

Line chart (fail rate), Bar chart (SIP reason by S-CSCF), Table (IMSI hash top failures).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
