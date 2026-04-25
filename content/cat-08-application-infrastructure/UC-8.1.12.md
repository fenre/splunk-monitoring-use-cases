<!-- AUTO-GENERATED from UC-8.1.12.json — DO NOT EDIT -->

---
id: "8.1.12"
title: "Apache mod_security WAF Blocks"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.1.12 · Apache mod_security WAF Blocks

## Description

Tracks ModSecurity rule IDs and scores for blocked requests. Supports tuning false positives and detecting attack campaigns.

## Value

Tracks ModSecurity rule IDs and scores for blocked requests. Supports tuning false positives and detecting attack campaigns.

## Implementation

Ingest JSON or native ModSecurity audit format. Extract `rule_id`, `msg`. Alert on spike in unique IPs or new rule_id firing at high volume.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, modsec audit log.
• Ensure the following data sources are available: `modsec_audit.log`, `SecRule` action deny entries.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest JSON or native ModSecurity audit format. Extract `rule_id`, `msg`. Alert on spike in unique IPs or new rule_id firing at high volume.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="apache:modsec"
| search action="denied" OR intercept_phase="phase:2"
| stats count by rule_id, uri_path, src
| sort -count
| head 30
```

Understanding this SPL

**Apache mod_security WAF Blocks** — Tracks ModSecurity rule IDs and scores for blocked requests. Supports tuning false positives and detecting attack campaigns.

Documented **Data sources**: `modsec_audit.log`, `SecRule` action deny entries. **App/TA** (typical add-on context): `Splunk_TA_apache`, modsec audit log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: apache:modsec. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="apache:modsec". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by rule_id, uri_path, src** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule, URI, count), Bar chart (blocks by rule), Map (src).

## SPL

```spl
index=web sourcetype="apache:modsec"
| search action="denied" OR intercept_phase="phase:2"
| stats count by rule_id, uri_path, src
| sort -count
| head 30
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.src | sort - count
```

## Visualization

Table (rule, URI, count), Bar chart (blocks by rule), Map (src).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
