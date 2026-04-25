<!-- AUTO-GENERATED from UC-5.2.16.json — DO NOT EDIT -->

---
id: "5.2.16"
title: "SSL/TLS Decryption Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.16 · SSL/TLS Decryption Failures

## Description

Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.

## Value

Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.

## Implementation

Enable decryption logging. Group failures by reason (unsupported cipher, certificate pinning, policy exclude). Review and update decryption policy based on findings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:decryption`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable decryption logging. Group failures by reason (unsupported cipher, certificate pinning, policy exclude). Review and update decryption policy based on findings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="pan:decryption" action="decrypt-error" OR action="no-decrypt"
| stats count by reason, dest, dest_port
| sort 50 -count
```

Understanding this SPL

**SSL/TLS Decryption Failures** — Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.

Documented **Data sources**: `sourcetype=pan:decryption`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: pan:decryption. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="pan:decryption". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by reason, dest, dest_port** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (failure reasons), Table (top undecrypted destinations), Pie chart (by reason).

## SPL

```spl
index=network sourcetype="pan:decryption" action="decrypt-error" OR action="no-decrypt"
| stats count by reason, dest, dest_port
| sort 50 -count
```

## Visualization

Bar chart (failure reasons), Table (top undecrypted destinations), Pie chart (by reason).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
