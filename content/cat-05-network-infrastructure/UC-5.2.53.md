---
id: "5.2.53"
title: "Check Point HTTPS Inspection Status and Bypass (Check Point)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.53 · Check Point HTTPS Inspection Status and Bypass (Check Point)

## Description

HTTPS inspection (SSL/TLS decryption) enables deep packet inspection of encrypted traffic. Connections that bypass inspection — due to certificate pinning, bypass rules, or resource limits — create visibility gaps. Monitoring bypass rates ensures that security coverage remains effective and identifies applications or categories that need policy updates.

## Value

HTTPS inspection (SSL/TLS decryption) enables deep packet inspection of encrypted traffic. Connections that bypass inspection — due to certificate pinning, bypass rules, or resource limits — create visibility gaps. Monitoring bypass rates ensures that security coverage remains effective and identifies applications or categories that need policy updates.

## Implementation

Enable HTTPS inspection logging (log bypassed and inspected connections). Baseline bypass rate per category. Alert when bypass percentage increases (new cert-pinned apps, resource limits). Report on inspection coverage for compliance (PCI DSS, SOX). Correlate with gateway CPU — high CPU can trigger automatic inspection bypass.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (firewall/HTTPS inspection logs).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable HTTPS inspection logging (log bypassed and inspected connections). Baseline bypass rate per category. Alert when bypass percentage increases (new cert-pinned apps, resource limits). Report on inspection coverage for compliance (PCI DSS, SOX). Correlate with gateway CPU — high CPU can trigger automatic inspection bypass.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(product),"(?i)https.?inspection|ssl.?inspection") OR match(lower(logdesc),"(?i)bypass|inspect|decrypt")
| eval inspected=if(match(lower(logdesc),"(?i)inspect|decrypt") AND NOT match(lower(logdesc),"(?i)bypass|skip|fail"),1,0)
| stats count sum(inspected) as inspected_count by rule_name, category
| eval bypass_pct=round(100*(count-inspected_count)/count,1)
| where bypass_pct > 20
| sort -bypass_pct
```

Understanding this SPL

**Check Point HTTPS Inspection Status and Bypass (Check Point)** — HTTPS inspection (SSL/TLS decryption) enables deep packet inspection of encrypted traffic. Connections that bypass inspection — due to certificate pinning, bypass rules, or resource limits — create visibility gaps. Monitoring bypass rates ensures that security coverage remains effective and identifies applications or categories that need policy updates.

Documented **Data sources**: `sourcetype=cp_log` (firewall/HTTPS inspection logs). **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(product),"(?i)https.?inspection|ssl.?inspection") OR match(lower(logdesc),"(?i)bypass|inspect|decrypt")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **inspected** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by rule_name, category** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **bypass_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where bypass_pct > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.action span=1h
```

Understanding this CIM / accelerated SPL

**Check Point HTTPS Inspection Status and Bypass (Check Point)** — HTTPS inspection (SSL/TLS decryption) enables deep packet inspection of encrypted traffic. Connections that bypass inspection — due to certificate pinning, bypass rules, or resource limits — create visibility gaps. Monitoring bypass rates ensures that security coverage remains effective and identifies applications or categories that need policy updates.

Documented **Data sources**: `sourcetype=cp_log` (firewall/HTTPS inspection logs). **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (inspected vs bypassed), Bar chart (bypass by category), Line chart (bypass rate trend), Table (top bypass rules).

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-24h
| where match(lower(product),"(?i)https.?inspection|ssl.?inspection") OR match(lower(logdesc),"(?i)bypass|inspect|decrypt")
| eval inspected=if(match(lower(logdesc),"(?i)inspect|decrypt") AND NOT match(lower(logdesc),"(?i)bypass|skip|fail"),1,0)
| stats count sum(inspected) as inspected_count by rule_name, category
| eval bypass_pct=round(100*(count-inspected_count)/count,1)
| where bypass_pct > 20
| sort -bypass_pct
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.action span=1h
```

## Visualization

Pie chart (inspected vs bypassed), Bar chart (bypass by category), Line chart (bypass rate trend), Table (top bypass rules).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
