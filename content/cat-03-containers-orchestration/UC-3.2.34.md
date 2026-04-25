<!-- AUTO-GENERATED from UC-3.2.34.json — DO NOT EDIT -->

---
id: "3.2.34"
title: "Cluster DNS Resolution Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.34 · Cluster DNS Resolution Failures

## Description

CoreDNS failures cause widespread `SERVFAIL` and intermittent app errors; monitoring query errors and upstream timeouts is essential.

## Value

CoreDNS failures cause widespread `SERVFAIL` and intermittent app errors; monitoring query errors and upstream timeouts is essential.

## Implementation

Forward CoreDNS logs with response code. Scrape `coredns_dns_responses_total` by rcode. Alert on SERVFAIL spike or upstream forward errors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CoreDNS log forwarding, Prometheus metrics.
• Ensure the following data sources are available: `sourcetype=kube:coredns`, `sourcetype=kube:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward CoreDNS logs with response code. Scrape `coredns_dns_responses_total` by rcode. Alert on SERVFAIL spike or upstream forward errors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="coredns_dns_responses_total"
| stats sum(_value) as responses by rcode
| where rcode!="NOERROR" AND rcode!="NXDOMAIN"
```

Understanding this SPL

**Cluster DNS Resolution Failures** — CoreDNS failures cause widespread `SERVFAIL` and intermittent app errors; monitoring query errors and upstream timeouts is essential.

Documented **Data sources**: `sourcetype=kube:coredns`, `sourcetype=kube:metrics`. **App/TA** (typical add-on context): CoreDNS log forwarding, Prometheus metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by rcode** so each row reflects one combination of those dimensions.
• Filters the current rows with `where rcode!="NOERROR" AND rcode!="NXDOMAIN"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors by rcode), Table (qname, count), Single value (SERVFAIL/min).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="coredns_dns_responses_total"
| stats sum(_value) as responses by rcode
| where rcode!="NOERROR" AND rcode!="NXDOMAIN"
```

## Visualization

Line chart (errors by rcode), Table (qname, count), Single value (SERVFAIL/min).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
