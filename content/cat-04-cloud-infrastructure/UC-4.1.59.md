---
id: "4.1.59"
title: "S3 Suspicious Access Patterns"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.59 · S3 Suspicious Access Patterns

## Description

Unusual ListBucket volume, access from new regions, or anonymous reads often precede data exfiltration; pattern detection reduces dwell time.

## Value

Unusual ListBucket volume, access from new regions, or anonymous reads often precede data exfiltration; pattern detection reduces dwell time.

## Implementation

Baseline normal GetObject/ListBucket rates per bucket and principal. Enrich with GeoIP on `sourceIPAddress`. Alert on first-seen ASN, burst downloads, or ListBucket without matching application inventory. Correlate with GuardDuty S3 findings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudtrail` (s3.amazonaws.com), optional S3 server access logs `sourcetype=aws:s3:accesslogs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline normal GetObject/ListBucket rates per bucket and principal. Enrich with GeoIP on `sourceIPAddress`. Alert on first-seen ASN, burst downloads, or ListBucket without matching application inventory. Correlate with GuardDuty S3 findings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="s3.amazonaws.com" eventName="GetObject"
| eval geo=if(isnull(sourceIPAddress),"unknown",sourceIPAddress)
| stats dc(eventName) as ops, dc(awsRegion) as regions, count by userIdentity.arn, requestParameters.bucketName
| where regions > 3 OR count > 10000
| sort -count
```

Understanding this SPL

**S3 Suspicious Access Patterns** — Unusual ListBucket volume, access from new regions, or anonymous reads often precede data exfiltration; pattern detection reduces dwell time.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (s3.amazonaws.com), optional S3 server access logs `sourcetype=aws:s3:accesslogs`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **geo** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by userIdentity.arn, requestParameters.bucketName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where regions > 3 OR count > 10000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

Understanding this CIM / accelerated SPL

**S3 Suspicious Access Patterns** — Unusual ListBucket volume, access from new regions, or anonymous reads often precede data exfiltration; pattern detection reduces dwell time.

Documented **Data sources**: `sourcetype=aws:cloudtrail` (s3.amazonaws.com), optional S3 server access logs `sourcetype=aws:s3:accesslogs`. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (bucket, principal, count), Map (source IP), Timeline (access spikes).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" eventSource="s3.amazonaws.com" eventName="GetObject"
| eval geo=if(isnull(sourceIPAddress),"unknown",sourceIPAddress)
| stats dc(eventName) as ops, dc(awsRegion) as regions, count by userIdentity.arn, requestParameters.bucketName
| where regions > 3 OR count > 10000
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

## Visualization

Table (bucket, principal, count), Map (source IP), Timeline (access spikes).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
