<!-- AUTO-GENERATED from UC-3.3.8.json — DO NOT EDIT -->

---
id: "3.3.8"
title: "Route TLS Expiry Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.3.8 · Route TLS Expiry Detection

## Description

OpenShift Routes terminate TLS for apps; expiring certs on edge or re-encrypt routes cause sudden browser and API client failures.

## Value

OpenShift Routes terminate TLS for apps; expiring certs on edge or re-encrypt routes cause sudden browser and API client failures.

## Implementation

Periodically export Route TLS `notAfter` from `oc` or ingress controller. If using cert-manager, scrape expiration metrics. Alert at 30/14/7 days; page inside 7 days for customer-facing hostnames.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: cert-manager, `oc get route -o json` scripted input.
• Ensure the following data sources are available: `sourcetype=openshift:route`, `sourcetype=certmanager:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically export Route TLS `notAfter` from `oc` or ingress controller. If using cert-manager, scrape expiration metrics. Alert at 30/14/7 days; page inside 7 days for customer-facing hostnames.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="certmanager:metrics" metric_name="certmanager_certificate_expiration_timestamp_seconds"
| eval days_left=round((_value-now())/86400,0)
| where days_left < 30
| table namespace name days_left
```

Understanding this SPL

**Route TLS Expiry Detection** — OpenShift Routes terminate TLS for apps; expiring certs on edge or re-encrypt routes cause sudden browser and API client failures.

Documented **Data sources**: `sourcetype=openshift:route`, `sourcetype=certmanager:metrics`. **App/TA** (typical add-on context): cert-manager, `oc get route -o json` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: certmanager:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="certmanager:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left < 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Route TLS Expiry Detection**): table namespace name days_left


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (route, hostname, days left), Single value (soonest expiry), Gauge.

## SPL

```spl
index=openshift sourcetype="certmanager:metrics" metric_name="certmanager_certificate_expiration_timestamp_seconds"
| eval days_left=round((_value-now())/86400,0)
| where days_left < 30
| table namespace name days_left
```

## Visualization

Table (route, hostname, days left), Single value (soonest expiry), Gauge.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
