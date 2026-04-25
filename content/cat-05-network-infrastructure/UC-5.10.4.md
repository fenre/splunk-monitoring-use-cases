<!-- AUTO-GENERATED from UC-5.10.4.json — DO NOT EDIT -->

---
id: "5.10.4"
title: "Carrier SIP Trunk Failure Analysis"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.10.4 · Carrier SIP Trunk Failure Analysis

## Description

Monitors SIP response codes on carrier trunks to detect call routing failures, trunk congestion, and destination unreachable conditions — directly impacting voice service availability and revenue.

## Value

Monitors SIP response codes on carrier trunks to detect call routing failures, trunk congestion, and destination unreachable conditions — directly impacting voice service availability and revenue.

## Implementation

Configure Splunk App for Stream to capture SIP signaling on trunk-facing interfaces. Enable SIP protocol extraction for fields `method`, `reply_code`, `caller`, `callee`, and `dest`. Focus on INVITE transactions as these represent call attempts. Group by `dest` to identify problematic trunks or destinations. SIP 4xx codes indicate client errors (e.g., 404 Not Found, 486 Busy Here), 5xx codes indicate server errors, and 6xx codes indicate global failures. Alert when failure rate exceeds 5% sustained over 15 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk App for Stream` (Splunkbase #1809).
• Ensure the following data sources are available: `sourcetype=stream:sip`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk App for Stream to capture SIP signaling on trunk-facing interfaces. Enable SIP protocol extraction for fields `method`, `reply_code`, `caller`, `callee`, and `dest`. Focus on INVITE transactions as these represent call attempts. Group by `dest` to identify problematic trunks or destinations. SIP 4xx codes indicate client errors (e.g., 404 Not Found, 486 Busy Here), 5xx codes indicate server errors, and 6xx codes indicate global failures. Alert when failure rate exceeds 5% sustai…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
sourcetype="stream:sip" method="INVITE"
| stats count as total, sum(eval(if(reply_code>=400, 1, 0))) as failures by dest
| eval failure_rate=round(failures*100/total, 2)
| where failure_rate>5 OR failures>50
| sort -failure_rate
```

Understanding this SPL

**Carrier SIP Trunk Failure Analysis** — Monitors SIP response codes on carrier trunks to detect call routing failures, trunk congestion, and destination unreachable conditions — directly impacting voice service availability and revenue.

Documented **Data sources**: `sourcetype=stream:sip`. **App/TA** (typical add-on context): `Splunk App for Stream` (Splunkbase #1809). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: stream:sip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: sourcetype="stream:sip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by dest** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **failure_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failure_rate>5 OR failures>50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare Splunk counts in the same time window to your packet capture or Stream job scope (VLAN, SPAN, or tap). On the core element (PCRF, SBC, or PGW) console or EMS, open the matching subscriber or trunk counters and confirm codes such as Diameter `result_code` or SIP `reply_code` line up. After any network or mirror change, re-check that the Stream capture still includes the trunks you care about.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (overall SIP trunk success rate with thresholds: green >95%, yellow 90-95%, red <90%), Column chart (failure count by dest), Table (dest, total attempts, failures, failure_rate — sortable), Timechart (SIP 4xx/5xx/6xx responses over 24h by response code class).

## SPL

```spl
sourcetype="stream:sip" method="INVITE"
| stats count as total, sum(eval(if(reply_code>=400, 1, 0))) as failures by dest
| eval failure_rate=round(failures*100/total, 2)
| where failure_rate>5 OR failures>50
| sort -failure_rate
```

## Visualization

Single value (overall SIP trunk success rate with thresholds: green >95%, yellow 90-95%, red <90%), Column chart (failure count by dest), Table (dest, total attempts, failures, failure_rate — sortable), Timechart (SIP 4xx/5xx/6xx responses over 24h by response code class).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
