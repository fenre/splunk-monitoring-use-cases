---
id: "5.2.41"
title: "Juniper SRX IDP/IPS Event Monitoring (Juniper SRX)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.41 · Juniper SRX IDP/IPS Event Monitoring (Juniper SRX)

## Description

Juniper SRX runs an integrated IDP/IPS engine with signature-based and protocol-anomaly detection alongside firewall state. Because events are generated in the same flow path as security policy, logs carry application context, zones, and session identifiers that standalone IPS appliances often lack. Monitoring attack name, severity, destination service, and enforcement action (drop, close, ignore) lets you prioritize true positives, spot targeted attacks, and prove that prevention is working without waiting for incident tickets.

## Value

Juniper SRX runs an integrated IDP/IPS engine with signature-based and protocol-anomaly detection alongside firewall state. Because events are generated in the same flow path as security policy, logs carry application context, zones, and session identifiers that standalone IPS appliances often lack. Monitoring attack name, severity, destination service, and enforcement action (drop, close, ignore) lets you prioritize true positives, spot targeted attacks, and prove that prevention is working without waiting for incident tickets.

## Implementation

Enable IDP on applicable SRX policies and send IDP logs to Splunk (structured syslog preferred). Install and enable the Juniper TA for field extraction. Build alerts for `sev` in (critical, high) or for rapid growth in `hits` against the same `dest_ip`/service. Correlate with allow/deny traffic logs on the same five-tuple. Add suppressions for known vulnerability scanners after a baseline window. Validate CIM `Intrusion_Detection` tags if you accelerate the data model.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper` (Splunkbase 2847).
• Ensure the following data sources are available: `sourcetype=juniper:junos:idp`, `sourcetype=juniper:junos:idp:structured`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable IDP on applicable SRX policies and send IDP logs to Splunk (structured syslog preferred). Install and enable the Juniper TA for field extraction. Build alerts for `sev` in (critical, high) or for rapid growth in `hits` against the same `dest_ip`/service. Correlate with allow/deny traffic logs on the same five-tuple. Add suppressions for known vulnerability scanners after a baseline window. Validate CIM `Intrusion_Detection` tags if you accelerate the data model.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network (sourcetype="juniper:junos:idp" OR sourcetype="juniper:junos:idp:structured")
| eval attack=coalesce(attack_name, signature, threat_name, idp_attack_name)
| eval sev=lower(coalesce(severity, threat_severity, idp_severity))
| eval act=coalesce(action, idp_action, policy_action)
| eval src_ip=coalesce(src, src_ip, srcaddr)
| eval dest_ip=coalesce(dest, dest_ip, dstaddr)
| stats count as hits by host attack sev act src_ip dest_ip dest_port service
| sort -hits
```

Understanding this SPL

**Juniper SRX IDP/IPS Event Monitoring (Juniper SRX)** — Juniper SRX runs an integrated IDP/IPS engine with signature-based and protocol-anomaly detection alongside firewall state. Because events are generated in the same flow path as security policy, logs carry application context, zones, and session identifiers that standalone IPS appliances often lack. Monitoring attack name, severity, destination service, and enforcement action (drop, close, ignore) lets you prioritize true positives, spot targeted attacks, and prove that…

Documented **Data sources**: `sourcetype=juniper:junos:idp`, `sourcetype=juniper:junos:idp:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper` (Splunkbase 2847). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:idp, juniper:junos:idp:structured. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:idp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **attack** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **sev** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **act** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **src_ip** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **dest_ip** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host attack sev act src_ip dest_ip dest_port service** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection
  by IDS_Attacks.signature, IDS_Attacks.severity, IDS_Attacks.src, IDS_Attacks.dest span=1h
| where count > 0
| sort -count
```

Understanding this CIM / accelerated SPL

**Juniper SRX IDP/IPS Event Monitoring (Juniper SRX)** — Juniper SRX runs an integrated IDP/IPS engine with signature-based and protocol-anomaly detection alongside firewall state. Because events are generated in the same flow path as security policy, logs carry application context, zones, and session identifiers that standalone IPS appliances often lack. Monitoring attack name, severity, destination service, and enforcement action (drop, close, ignore) lets you prioritize true positives, spot targeted attacks, and prove that…

Documented **Data sources**: `sourcetype=juniper:junos:idp`, `sourcetype=juniper:junos:idp:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper` (Splunkbase 2847). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Intrusion_Detection` — enable acceleration for that model.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (attack, severity, action, endpoints), Bar chart (top signatures), Timeline (bursts by host).

## SPL

```spl
index=network (sourcetype="juniper:junos:idp" OR sourcetype="juniper:junos:idp:structured")
| eval attack=coalesce(attack_name, signature, threat_name, idp_attack_name)
| eval sev=lower(coalesce(severity, threat_severity, idp_severity))
| eval act=coalesce(action, idp_action, policy_action)
| eval src_ip=coalesce(src, src_ip, srcaddr)
| eval dest_ip=coalesce(dest, dest_ip, dstaddr)
| stats count as hits by host attack sev act src_ip dest_ip dest_port service
| sort -hits
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection
  by IDS_Attacks.signature, IDS_Attacks.severity, IDS_Attacks.src, IDS_Attacks.dest span=1h
| where count > 0
| sort -count
```

## Visualization

Table (attack, severity, action, endpoints), Bar chart (top signatures), Timeline (bursts by host).

## References

- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
