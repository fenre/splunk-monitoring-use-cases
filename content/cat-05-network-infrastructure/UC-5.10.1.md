<!-- AUTO-GENERATED from UC-5.10.1.json — DO NOT EDIT -->

---
id: "5.10.1"
title: "Diameter Signaling Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.10.1 · Diameter Signaling Health Monitoring

## Description

Tracks the success and failure rates of Diameter signaling messages (authentication, authorization, accounting) in the mobile core, essential for maintaining service availability and subscriber experience.

## Value

Tracks the success and failure rates of Diameter signaling messages (authentication, authorization, accounting) in the mobile core, essential for maintaining service availability and subscriber experience.

## Implementation

Install Splunk App for Stream and configure it to capture Diameter protocol traffic on the core network. Enable the Diameter protocol for full field extraction. Monitor `command_code` and `result_code` to detect signaling issues. Create alerts for sustained drops in success rate or spikes in failure codes such as DIAMETER_AUTHENTICATION_REJECTED (5003) or DIAMETER_UNABLE_TO_DELIVER (3002).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk App for Stream` (Splunkbase #1809).
• Ensure the following data sources are available: `sourcetype=stream:diameter`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install Splunk App for Stream and configure it to capture Diameter protocol traffic on the core network. Enable the Diameter protocol for full field extraction. Monitor `command_code` and `result_code` to detect signaling issues. Create alerts for sustained drops in success rate or spikes in failure codes such as DIAMETER_AUTHENTICATION_REJECTED (5003) or DIAMETER_UNABLE_TO_DELIVER (3002).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
sourcetype="stream:diameter"
| stats count by command_code, result_code, origin_host, application_id
| eval status=if(result_code==2001, "Success", "Failure")
| stats sum(eval(if(status=="Success", 1, 0))) as successful, sum(eval(if(status=="Failure", 1, 0))) as failed by command_code, application_id
| eval success_rate=round(successful*100/(successful+failed), 2)
| where failed>0 OR success_rate<99
```

Understanding this SPL

**Diameter Signaling Health Monitoring** — Tracks the success and failure rates of Diameter signaling messages (authentication, authorization, accounting) in the mobile core, essential for maintaining service availability and subscriber experience.

Documented **Data sources**: `sourcetype=stream:diameter`. **App/TA** (typical add-on context): `Splunk App for Stream` (Splunkbase #1809). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: stream:diameter. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: sourcetype="stream:diameter". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by command_code, result_code, origin_host, application_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by command_code, application_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **success_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failed>0 OR success_rate<99` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare Splunk counts in the same time window to your packet capture or Stream job scope (VLAN, SPAN, or tap). On the core element (PCRF, SBC, or PGW) console or EMS, open the matching subscriber or trunk counters and confirm codes such as Diameter `result_code` or SIP `reply_code` line up. After any network or mirror change, re-check that the Stream capture still includes the trunks you care about.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (overall Diameter success rate with color-coded threshold: green >99%, yellow 95-99%, red <95%), Pie chart (failure breakdown by command_code), Table (origin_host, command_code, result_code, count — sortable), Line chart (success rate trend over 24h with 15-min buckets).

## SPL

```spl
sourcetype="stream:diameter"
| stats count by command_code, result_code, origin_host, application_id
| eval status=if(result_code==2001, "Success", "Failure")
| stats sum(eval(if(status=="Success", 1, 0))) as successful, sum(eval(if(status=="Failure", 1, 0))) as failed by command_code, application_id
| eval success_rate=round(successful*100/(successful+failed), 2)
| where failed>0 OR success_rate<99
```

## Visualization

Single value (overall Diameter success rate with color-coded threshold: green >99%, yellow 95-99%, red <95%), Pie chart (failure breakdown by command_code), Table (origin_host, command_code, result_code, count — sortable), Line chart (success rate trend over 24h with 15-min buckets).

## References

- [Splunkbase — Splunk App for Stream](https://splunkbase.splunk.com/app/1809)
