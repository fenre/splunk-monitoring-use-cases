<!-- AUTO-GENERATED from UC-5.2.39.json — DO NOT EDIT -->

---
id: "5.2.39"
title: "Data Loss Prevention (DLP) Event Analysis (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.39 · Data Loss Prevention (DLP) Event Analysis (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count data loss style events on the same edge so risky uploads to personal storage and odd data paths get a second look in time.*

---

## Description

Detects and alerts on sensitive data transmission to prevent data exfiltration.

## Value

Security teams monitor Meraki MX content filtering blocks as DLP proxy indicators, detecting potential data exfiltration attempts to file sharing, cloud storage, and high-risk upload destinations.

## Implementation

1. Configure SC4S for MX syslog and enable URLs syslog category in Meraki Dashboard. 2. Maintain a pii_keyword_list.csv lookup with columns (keyword, pii_category) reflecting your sensitive-data terms. 3. The URL field comes from the message body 'request: GET <url>'. 4. For comprehensive DLP coverage deploy a purpose-built DLP product — Meraki MX has no native DLP and the URL-keyword matching here will only catch HTTP requests where the keyword is in the URL path/query, missing all HTTPS body content.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki, type=urls) receiving Meraki content filtering events. NOTE: Meraki MX does NOT have a built-in DLP engine. This UC uses a customer-maintained pii_keyword_list lookup against blocked URLs as a weak proxy. For real DLP coverage deploy a dedicated DLP product (Cisco Secure Email, Microsoft Purview, Forcepoint DLP, Symantec DLP) and ingest its events instead — this UC's premise is fundamentally limited on a Meraki-only stack..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX syslog and enable URLs syslog category in Meraki Dashboard. 2. Maintain a pii_keyword_list.csv lookup with columns (keyword, pii_category) reflecting your sensitive-data terms. 3. The URL field comes from the message body 'request: GET <url>'. 4. For comprehensive DLP coverage deploy a purpose-built DLP product — Meraki MX has no native DLP and the URL-keyword matching here will only catch HTTP requests where the keyword is in the URL path/query, missing all HTTPS body c…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=urls action="blocked"
    earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "request: (?:GET|POST) (?<url>https?://[^\s]+)"
| lookup pii_keyword_list keyword OUTPUTNEW pii_category
| where isnotnull(pii_category)
| stats count as event_count,
        values(url) as urls,
        values(pii_category) as categories
         by src_ip
| sort - event_count
```

#### Understanding this SPL

**Data Loss Prevention (DLP) Event Analysis (Meraki MX)** — Security teams monitor Meraki MX content filtering blocks as DLP proxy indicators, detecting potential data exfiltration attempts to file sharing, cloud storage, and high-risk upload destinations.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=urls) receiving Meraki content filtering events. NOTE: Meraki MX does NOT have a built-in DLP engine. This UC uses a customer-maintained pii_keyword_list lookup against blocked URLs as a weak proxy. For real DLP coverage deploy a dedicated DLP product (Cisco Secure Email, Microsoft Purview, Forcepoint DLP, Symantec DLP) and ingest its events instead — this UC's premise is fundamentally limited on a Meraki-only stack. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
- Filters the current rows with `where isnotnull(pii_category)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by src_ip** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: DLP incident timeline; data type breakdown; source/destination detail.

## SPL

```spl
index=meraki sourcetype="meraki" type=urls action="blocked"
    earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "request: (?:GET|POST) (?<url>https?://[^\s]+)"
| lookup pii_keyword_list keyword OUTPUTNEW pii_category
| where isnotnull(pii_category)
| stats count as event_count,
        values(url) as urls,
        values(pii_category) as categories
         by src_ip
| sort - event_count
```

## Visualization

DLP incident timeline; data type breakdown; source/destination detail.

## Known False Positives

False positives, large legitimate uploads, and user mistakes can all trip data-loss rules you still need to review.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
