<!-- AUTO-GENERATED from UC-5.6.7.json — DO NOT EDIT -->

---
id: "5.6.7"
title: "DNS Record Change Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.6.7 · DNS Record Change Audit

## Description

Unauthorized DNS changes can redirect traffic to attacker infrastructure (DNS hijacking).

## Value

Unauthorized DNS changes can redirect traffic to attacker infrastructure (DNS hijacking).

## Implementation

Forward DNS server audit logs. Alert on changes to critical domains. Correlate with change tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_infoblox, DNS update logs.
• Ensure the following data sources are available: Infoblox audit log, DNS dynamic update logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DNS server audit logs. Alert on changes to critical domains. Correlate with change tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype="infoblox:audit" ("Added" OR "Deleted" OR "Modified") AND ("record" OR "zone")
| table _time admin record_type record_name record_data action | sort -_time
```

Understanding this SPL

**DNS Record Change Audit** — Unauthorized DNS changes can redirect traffic to attacker infrastructure (DNS hijacking).

Documented **Data sources**: Infoblox audit log, DNS dynamic update logs. **App/TA** (typical add-on context): Splunk_TA_infoblox, DNS update logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns; **sourcetype**: infoblox:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=dns, sourcetype="infoblox:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **DNS Record Change Audit**): table _time admin record_type record_name record_data action
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Infoblox (Audit Log / grid audit) or your DNS admin audit trail, open the same time range and compare administrator, record name, and action to the Splunk rows. Tie each change to an approved change ticket when possible.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (record, action, who, when), Timeline, Single value.

## SPL

```spl
index=dns sourcetype="infoblox:audit" ("Added" OR "Deleted" OR "Modified") AND ("record" OR "zone")
| table _time admin record_type record_name record_data action | sort -_time
```

## Visualization

Table (record, action, who, when), Timeline, Single value.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
