---
id: "5.2.52"
title: "Check Point Anti-Spoofing Violations (Check Point)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.52 · Check Point Anti-Spoofing Violations (Check Point)

## Description

Anti-spoofing validates that packets arriving on an interface have source IPs consistent with the interface's defined topology. Violations indicate either network misconfiguration (asymmetric routing, missing routes) or actual IP spoofing attacks. High violation rates from specific sources warrant immediate investigation as they may mask data exfiltration or DDoS reflection.

## Value

Anti-spoofing validates that packets arriving on an interface have source IPs consistent with the interface's defined topology. Violations indicate either network misconfiguration (asymmetric routing, missing routes) or actual IP spoofing attacks. High violation rates from specific sources warrant immediate investigation as they may mask data exfiltration or DDoS reflection.

## Implementation

Forward firewall drop logs including anti-spoofing events. Map `inzone` and `outzone` to topology to distinguish misconfiguration from attacks. Alert on new source IPs triggering anti-spoofing. Correlate with routing changes. Tune anti-spoofing topology definitions after legitimate asymmetric routing is identified.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (firewall logs with anti-spoofing drops).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward firewall drop logs including anti-spoofing events. Map `inzone` and `outzone` to topology to distinguish misconfiguration from attacks. Alert on new source IPs triggering anti-spoofing. Correlate with routing changes. Tune anti-spoofing topology definitions after legitimate asymmetric routing is identified.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(action),"(?i)drop") AND match(lower(logdesc),"(?i)anti.?spoof|spoofing")
| stats count by src, inzone, outzone, rule_name, orig
| sort -count
```

Understanding this SPL

**Check Point Anti-Spoofing Violations (Check Point)** — Anti-spoofing validates that packets arriving on an interface have source IPs consistent with the interface's defined topology. Violations indicate either network misconfiguration (asymmetric routing, missing routes) or actual IP spoofing attacks. High violation rates from specific sources warrant immediate investigation as they may mask data exfiltration or DDoS reflection.

Documented **Data sources**: `sourcetype=cp_log` (firewall logs with anti-spoofing drops). **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(action),"(?i)drop") AND match(lower(logdesc),"(?i)anti.?spoof|spoofing")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src, inzone, outzone, rule_name, orig** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="blocked"
  by All_Traffic.src All_Traffic.dest span=1h
```

Understanding this CIM / accelerated SPL

**Check Point Anti-Spoofing Violations (Check Point)** — Anti-spoofing validates that packets arriving on an interface have source IPs consistent with the interface's defined topology. Violations indicate either network misconfiguration (asymmetric routing, missing routes) or actual IP spoofing attacks. High violation rates from specific sources warrant immediate investigation as they may mask data exfiltration or DDoS reflection.

Documented **Data sources**: `sourcetype=cp_log` (firewall logs with anti-spoofing drops). **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (spoofing violations by source), Bar chart (violations by interface/zone), Line chart (violation trend), Map (source geo if available).

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(action),"(?i)drop") AND match(lower(logdesc),"(?i)anti.?spoof|spoofing")
| stats count by src, inzone, outzone, rule_name, orig
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="blocked"
  by All_Traffic.src All_Traffic.dest span=1h
```

## Visualization

Table (spoofing violations by source), Bar chart (violations by interface/zone), Line chart (violation trend), Map (source geo if available).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
