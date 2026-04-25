<!-- AUTO-GENERATED from UC-3.3.20.json — DO NOT EDIT -->

---
id: "3.3.20"
title: "Cluster Certificate Expiry"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.3.20 · Cluster Certificate Expiry

## Description

OpenShift uses dozens of internal certificates for API server, kubelet, etcd, and service-serving. Expired internal certificates cause sudden cluster-wide outages that are difficult to recover from without backup.

## Value

OpenShift uses dozens of internal certificates for API server, kubelet, etcd, and service-serving. Expired internal certificates cause sudden cluster-wide outages that are difficult to recover from without backup.

## Implementation

Scripted input parsing TLS secrets or extracting from `openssl x509 -noout -enddate`. Also scrape `apiserver_client_certificate_expiration_seconds` Prometheus metric. Alert at 30/14/7 days before expiry. Page at 3 days for cluster-critical certificates.

## Detailed Implementation

Prerequisites
• Install and configure: `oc get secret -A -o json` scripted input (TLS secrets), OpenShift Monitoring Prometheus metrics
• Have these sources flowing into Splunk: `sourcetype=openshift:certificates`
• For app layout, inputs, and HEC, see docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input parsing TLS secrets or extracting from `openssl x509 -noout -enddate`. Also scrape `apiserver_client_certificate_expiration_seconds` Prometheus metric. Alert at 30/14/7 days before expiry. Page at 3 days for cluster-critical certificates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:certificates"
| eval days_left=round((expiry_epoch-now())/86400,0)
| where days_left<30
| table namespace secret_name cn days_left issuer
| sort days_left
```

Understanding this SPL

**Cluster Certificate Expiry** — OpenShift uses dozens of internal certificates for API server, kubelet, etcd, and service-serving.

Documented **Data sources**: `sourcetype=openshift:certificates`. **App/TA** context: `oc get secret -A -o json` scripted input (TLS secrets), OpenShift Monitoring Prometheus metrics. Use the same index and sourcetype names you configured in production.

**Pipeline walkthrough** — follow the search from top to bottom: narrow to the right index and sourcetype, extract or compute the fields the alert needs, then aggregate or filter to your threshold. Adjust macros or field names to match your field extractions.

Step 3 — Validate
Confirm that events land in the index and that a manual spot-check (small time window) matches the cluster or host reality. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with a known test case if you have one. Check permissions and field spelling.

Step 4 — Operationalize
Add the saved search to a team dashboard, wire alert actions, and document who owns the runbook. Suggested views: Table (certificate, namespace, days left, issuer), Single value (soonest expiry), Gauge.

## SPL

```spl
index=openshift sourcetype="openshift:certificates"
| eval days_left=round((expiry_epoch-now())/86400,0)
| where days_left<30
| table namespace secret_name cn days_left issuer
| sort days_left
```

## Visualization

Table (certificate, namespace, days left, issuer), Single value (soonest expiry), Gauge.

## References

- [OpenShift certificate management](https://docs.openshift.com/container-platform/latest/security/certificates/api-server.html)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
