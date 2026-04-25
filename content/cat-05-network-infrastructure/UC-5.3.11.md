<!-- AUTO-GENERATED from UC-5.3.11.json — DO NOT EDIT -->

---
id: "5.3.11"
title: "Rate Limiting and DDoS Mitigation Events (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.3.11 · Rate Limiting and DDoS Mitigation Events (F5 BIG-IP)

## Description

Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.

## Value

Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.

## Implementation

Enable ASM/WAF logging. Configure rate limiting policies per virtual server. Alert on sustained rate limiting events. Track source IP patterns for blocklisting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler.
• Ensure the following data sources are available: `sourcetype=f5:bigip:asm`, `sourcetype=f5:bigip:ltm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable ASM/WAF logging. Configure rate limiting policies per virtual server. Alert on sustained rate limiting events. Track source IP patterns for blocklisting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:asm" attack_type="*dos*" OR violation="Rate Limiting"
| stats count values(src) as src_values dc(src) as unique_sources by virtual_server, attack_type
| sort -count
```

Understanding this SPL

**Rate Limiting and DDoS Mitigation Events (F5 BIG-IP)** — Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.

Documented **Data sources**: `sourcetype=f5:bigip:asm`, `sourcetype=f5:bigip:ltm`. **App/TA** (typical add-on context): F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:asm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:asm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by virtual_server, attack_type** so each row reflects one combination of those dimensions.
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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (events over time), Table (source IPs, attack types), Single value (blocked requests).

## SPL

```spl
index=network sourcetype="f5:bigip:asm" attack_type="*dos*" OR violation="Rate Limiting"
| stats count values(src) as src_values dc(src) as unique_sources by virtual_server, attack_type
| sort -count
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

Timechart (events over time), Table (source IPs, attack types), Single value (blocked requests).

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
