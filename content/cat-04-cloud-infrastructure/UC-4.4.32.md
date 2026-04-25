<!-- AUTO-GENERATED from UC-4.4.32.json — DO NOT EDIT -->

---
id: "4.4.32"
title: "Cloud Control Plane API Call Volume Anomaly (MLTK)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.4.32 · Cloud Control Plane API Call Volume Anomaly (MLTK)

## Description

Cloud control plane API calls (EC2 RunInstances, IAM CreateUser, S3 PutBucketPolicy) follow predictable patterns tied to deployment schedules and automation cadence. Anomalous spikes in API call volume may indicate compromised credentials, runaway automation, or an attacker enumerating resources — all of which are invisible to static rate limits but detectable through ML-based baselining.

## Value

Cloud control plane API calls (EC2 RunInstances, IAM CreateUser, S3 PutBucketPolicy) follow predictable patterns tied to deployment schedules and automation cadence. Anomalous spikes in API call volume may indicate compromised credentials, runaway automation, or an attacker enumerating resources — all of which are invisible to static rate limits but detectable through ML-based baselining.

## Implementation

Aggregate CloudTrail / Activity Log / Admin Activity events hourly by API action and principal. Train DensityFunction models per API action on 30 days of data to capture automation schedules and deployment patterns. Flag calls that exceed 3 standard deviations from the learned baseline. Prioritize high-risk APIs: IAM mutations, security group changes, KMS key operations, and resource creation. Enrich with source IP geolocation and threat intelligence. Correlate with CI/CD deployment events (cat-12) to suppress planned automation bursts. Generate risk events for Splunk ES with MITRE T1078/T1580 annotations. Retrain models weekly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Machine Learning Toolkit (MLTK), Splunk Add-on for AWS / Azure / GCP.
• Ensure the following data sources are available: `index=cloud sourcetype=aws:cloudtrail` or `sourcetype=azure:monitor:activity` or `sourcetype=google:gcp:pubsub:message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Aggregate CloudTrail / Activity Log / Admin Activity events hourly by API action and principal. Train DensityFunction models per API action on 30 days of data to capture automation schedules and deployment patterns. Flag calls that exceed 3 standard deviations from the learned baseline. Prioritize high-risk APIs: IAM mutations, security group changes, KMS key operations, and resource creation. Enrich with source IP geolocation and threat intelligence. Correlate with CI/CD deployment events (cat-…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype IN ("aws:cloudtrail","azure:monitor:activity","google:gcp:pubsub:message")
| bin _time span=1h
| stats count by _time, eventName, userIdentity.arn, sourceIPAddress
| eventstats avg(count) as baseline_avg, stdev(count) as baseline_std by eventName
| eval z_score=round((count - baseline_avg) / nullif(baseline_std, 0), 2)
| where z_score > 3 AND count > 50
| fit DensityFunction count by eventName into cloud_api_anomaly_model
| rename "IsOutlier(count)" as isOutlier
| where isOutlier > 0
| table _time, eventName, userIdentity.arn, sourceIPAddress, count, baseline_avg, z_score
| sort -z_score
```

Understanding this SPL

**Cloud Control Plane API Call Volume Anomaly (MLTK)** — Cloud control plane API calls (EC2 RunInstances, IAM CreateUser, S3 PutBucketPolicy) follow predictable patterns tied to deployment schedules and automation cadence. Anomalous spikes in API call volume may indicate compromised credentials, runaway automation, or an attacker enumerating resources — all of which are invisible to static rate limits but detectable through ML-based baselining.

Documented **Data sources**: `index=cloud sourcetype=aws:cloudtrail` or `sourcetype=azure:monitor:activity` or `sourcetype=google:gcp:pubsub:message`. **App/TA** (typical add-on context): Splunk Machine Learning Toolkit (MLTK), Splunk Add-on for AWS / Azure / GCP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud.

**Pipeline walkthrough**

• Scopes the data: index=cloud. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, eventName, userIdentity.arn, sourceIPAddress** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by eventName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **z_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where z_score > 3 AND count > 50` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cloud Control Plane API Call Volume Anomaly (MLTK)**): fit DensityFunction count by eventName into cloud_api_anomaly_model
• Renames fields with `rename` for clarity or joins.
• Filters the current rows with `where isOutlier > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cloud Control Plane API Call Volume Anomaly (MLTK)**): table _time, eventName, userIdentity.arn, sourceIPAddress, count, baseline_avg, z_score
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Cloud Control Plane API Call Volume Anomaly (MLTK)** — Cloud control plane API calls (EC2 RunInstances, IAM CreateUser, S3 PutBucketPolicy) follow predictable patterns tied to deployment schedules and automation cadence.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (API call volume vs baseline), Table (anomalous API calls with z-scores), Bar chart (top anomalous APIs by principal).

## SPL

```spl
index=cloud sourcetype IN ("aws:cloudtrail","azure:monitor:activity","google:gcp:pubsub:message")
| bin _time span=1h
| stats count by _time, eventName, userIdentity.arn, sourceIPAddress
| eventstats avg(count) as baseline_avg, stdev(count) as baseline_std by eventName
| eval z_score=round((count - baseline_avg) / nullif(baseline_std, 0), 2)
| where z_score > 3 AND count > 50
| fit DensityFunction count by eventName into cloud_api_anomaly_model
| rename "IsOutlier(count)" as isOutlier
| where isOutlier > 0
| table _time, eventName, userIdentity.arn, sourceIPAddress, count, baseline_avg, z_score
| sort -z_score
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Line chart (API call volume vs baseline), Table (anomalous API calls with z-scores), Bar chart (top anomalous APIs by principal).

## References

- [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
