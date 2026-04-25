<!-- AUTO-GENERATED from UC-5.3.8.json — DO NOT EDIT -->

---
id: "5.3.8"
title: "WAF Policy Violations (F5 BIG-IP ASM)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.8 · WAF Policy Violations (F5 BIG-IP ASM)

## Description

WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

## Value

WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

## Implementation

Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip` (ASM).
• Ensure the following data sources are available: `sourcetype=f5:bigip:asm:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src, request_uri, severity | sort -count
```

Understanding this SPL

**WAF Policy Violations (F5 BIG-IP ASM)** — WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

Documented **Data sources**: `sourcetype=f5:bigip:asm:syslog`. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip` (ASM). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:asm:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:asm:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by violation_name, src, request_uri, severity** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.




Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Intrusion_Detection data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Intrusion_Detection model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
In the F5 Configuration utility or tmsh, open Local Traffic and Application Security (ASM) for the same time range, and confirm blocked requests, policy names, and virtuals match the Splunk results.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Bar chart by violation, Map (source IPs), Timeline.

## SPL

```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src, request_uri, severity | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Table, Bar chart by violation, Map (source IPs), Timeline.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
