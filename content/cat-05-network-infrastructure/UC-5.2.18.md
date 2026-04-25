<!-- AUTO-GENERATED from UC-5.2.18.json — DO NOT EDIT -->

---
id: "5.2.18"
title: "Threat Prevention Signature Coverage"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.18 · Threat Prevention Signature Coverage

## Description

Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.

## Value

Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.

## Implementation

Forward system logs. Alert when signature updates are >7 days old. Compare across firewalls to detect update failures. Schedule weekly compliance reports.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:system`, `sourcetype=fgt_event`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward system logs. Alert when signature updates are >7 days old. Compare across firewalls to detect update failures. Schedule weekly compliance reports.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="pan:system" "threat version" OR "content update"
| rex "installed (?<content_type>threats|antivirus|wildfire) version (?<version>\S+)"
| stats latest(version) as current_version, latest(_time) as last_update by dvc, content_type
| eval days_since_update=round((now()-last_update)/86400,0)
| where days_since_update > 7
```

Understanding this SPL

**Threat Prevention Signature Coverage** — Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.

Documented **Data sources**: `sourcetype=pan:system`, `sourcetype=fgt_event`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: pan:system. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="pan:system". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by dvc, content_type** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **days_since_update** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since_update > 7` — typically the threshold or rule expression for this monitoring goal.




Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Change data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Change model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (firewall, content type, version, days since update), Single value (outdated count).

## SPL

```spl
index=network sourcetype="pan:system" "threat version" OR "content update"
| rex "installed (?<content_type>threats|antivirus|wildfire) version (?<version>\S+)"
| stats latest(version) as current_version, latest(_time) as last_update by dvc, content_type
| eval days_since_update=round((now()-last_update)/86400,0)
| where days_since_update > 7
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Table (firewall, content type, version, days since update), Single value (outdated count).

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
