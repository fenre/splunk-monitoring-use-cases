<!-- AUTO-GENERATED from UC-4.3.29.json — DO NOT EDIT -->

---
id: "4.3.29"
title: "Pub/Sub Subscription Backlog"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.29 · Pub/Sub Subscription Backlog

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Performance

*Growing backlog signals consumer lag or -provisioned workers; oldest-unacked age breaches processing service promises.*

---

## Description

Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

## Value

Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

## Implementation

Set per-subscription SLOs for max backlog and oldest age. Scale push subscribers or fix poison messages. Use dead-letter topics for bad payloads.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
- Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (`pubsub.googleapis.com/subscription/num_undelivered_messages`, `oldest_unacked_message_age`).
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Set per-subscription SLOs for max backlog and oldest age. Scale push subscribers or fix poison messages. Use dead-letter topics for bad payloads.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| stats latest(value) as backlog by resource.labels.subscription_id, bin(_time, 5m)
| where backlog > 10000
| sort - backlog
```

#### Understanding this SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (`pubsub.googleapis.com/subscription/num_undelivered_messages`, `oldest_unacked_message_age`). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by resource.labels.subscription_id, bin(_time, 5m)** so each row reflects one combination of those dimensions.
- Filters the current rows with `where backlog > 10000` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on accelerated data model the CPU-related Performance model — enable that model in Data Models and CIM add-ons, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (backlog over time), Single value (oldest message age), Table (subscription, backlog).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| stats latest(value) as backlog by resource.labels.subscription_id, bin(_time, 5m)
| where backlog > 10000
| sort - backlog
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Line chart (backlog over time), Single value (oldest message age), Table (subscription, backlog).

## Known False Positives

Short spikes at deploy time, autoscale thrash, or a noisy neighbor on shared hosts can look bad for a few minutes. We require the condition to last across several intervals or clear on its own before we wake someone.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
