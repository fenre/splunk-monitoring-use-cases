---
id: "3.2.13"
title: "Certificate Expiration"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.13 · Certificate Expiration

## Description

Kubernetes uses TLS certificates extensively (API server, kubelet, etcd). Expired certs cause cluster communication failures and outages.

## Value

Kubernetes uses TLS certificates extensively (API server, kubelet, etcd). Expired certs cause cluster communication failures and outages.

## Implementation

Deploy cert-manager and scrape its metrics. Monitor certificate expiration timestamps. Alert at 30/14/7 day thresholds. For kubeadm clusters, scripted input running `kubeadm certs check-expiration`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: cert-manager metrics, custom scripted input.
• Ensure the following data sources are available: cert-manager events, `kubeadm certs check-expiration` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy cert-manager and scrape its metrics. Monitor certificate expiration timestamps. Alert at 30/14/7 day thresholds. For kubeadm clusters, scripted input running `kubeadm certs check-expiration`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="certmanager:metrics"
| eval days_left = round((certmanager_certificate_expiration_timestamp_seconds - now()) / 86400, 0)
| where days_left < 30
```

Understanding this SPL

**Certificate Expiration** — Kubernetes uses TLS certificates extensively (API server, kubelet, etcd). Expired certs cause cluster communication failures and outages.

Documented **Data sources**: cert-manager events, `kubeadm certs check-expiration` output. **App/TA** (typical add-on context): cert-manager metrics, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: certmanager:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="certmanager:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left < 30` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cert, namespace, days remaining), Single value (certs expiring soon), Status indicator.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=k8s sourcetype="certmanager:metrics"
| eval days_left = round((certmanager_certificate_expiration_timestamp_seconds - now()) / 86400, 0)
| where days_left < 30
```

## Visualization

Table (cert, namespace, days remaining), Single value (certs expiring soon), Status indicator.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
