<!-- AUTO-GENERATED from UC-5.5.17.json — DO NOT EDIT -->

---
id: "5.5.17"
title: "Security Policy Violations (UTD)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.5.17 · Security Policy Violations (UTD)

## Description

SD-WAN edges running Unified Threat Defense (UTD) perform IPS, URL filtering, and AMP inline. Monitoring these events at the WAN edge catches threats that bypass centralized firewalls, especially for direct internet access (DIA) traffic that never traverses the data center.

## Value

SD-WAN edges running Unified Threat Defense (UTD) perform IPS, URL filtering, and AMP inline. Monitoring these events at the WAN edge catches threats that bypass centralized firewalls, especially for direct internet access (DIA) traffic that never traverses the data center.

## Implementation

Enable UTD (IPS/URL filtering/AMP) on SD-WAN edges handling DIA traffic. Collect security events via vManage. Alert on critical/high severity IPS signatures and malware detections. Correlate with Umbrella/Secure Access if deployed for layered defense. Track blocked URL categories to refine acceptable-use policies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage UTD events, `sourcetype=cisco:sdwan:utd`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable UTD (IPS/URL filtering/AMP) on SD-WAN edges handling DIA traffic. Collect security events via vManage. Alert on critical/high severity IPS signatures and malware detections. Correlate with Umbrella/Secure Access if deployed for layered defense. Track blocked URL categories to refine acceptable-use policies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:utd"
| stats count by event_type, signature, severity, src_ip, dst_ip, site_id
| where severity IN ("critical","high")
| sort -count
| table event_type signature severity src_ip dst_ip site_id count
```

Understanding this SPL

**Security Policy Violations (UTD)** — SD-WAN edges running Unified Threat Defense (UTD) perform IPS, URL filtering, and AMP inline. Monitoring these events at the WAN edge catches threats that bypass centralized firewalls, especially for direct internet access (DIA) traffic that never traverses the data center.

Documented **Data sources**: vManage UTD events, `sourcetype=cisco:sdwan:utd`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:utd. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:utd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by event_type, signature, severity, src_ip, dst_ip, site_id** so each row reflects one combination of those dimensions.
• Filters the current rows with `where severity IN ("critical","high")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Security Policy Violations (UTD)**): table event_type signature severity src_ip dst_ip site_id count


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (signature, severity, source, destination), Bar chart (events by category), Timeline (event frequency).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:utd"
| stats count by event_type, signature, severity, src_ip, dst_ip, site_id
| where severity IN ("critical","high")
| sort -count
| table event_type signature severity src_ip dst_ip site_id count
```

## Visualization

Table (signature, severity, source, destination), Bar chart (events by category), Timeline (event frequency).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
