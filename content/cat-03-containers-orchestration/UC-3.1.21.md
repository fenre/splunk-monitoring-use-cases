<!-- AUTO-GENERATED from UC-3.1.21.json — DO NOT EDIT -->

---
id: "3.1.21"
title: "Container Runtime Security Events"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.21 · Container Runtime Security Events

## Description

Falco/sysdig/Falco-sidekick style rules surface unexpected shells, sensitive mounts, and syscall anomalies at runtime—complementing image scanning for zero-day behavior.

## Value

Falco/sysdig/Falco-sidekick style rules surface unexpected shells, sensitive mounts, and syscall anomalies at runtime—complementing image scanning for zero-day behavior.

## Implementation

Forward Falco JSON with `rule`, `priority`, container/k8s metadata. Tune noise with allowlists. Page on Critical; dashboard top rules by container image.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Falco (JSON to HEC), Sysdig Secure.
• Ensure the following data sources are available: `sourcetype=falco:alert`, `sourcetype=sysdig:secure`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Falco JSON with `rule`, `priority`, container/k8s metadata. Tune noise with allowlists. Page on Critical; dashboard top rules by container image.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="falco:alert" priority="Critical" OR priority="Error"
| stats count by rule, container.name, k8s.pod.name, proc.name
| sort -count
```

Understanding this SPL

**Container Runtime Security Events** — Falco/sysdig/Falco-sidekick style rules surface unexpected shells, sensitive mounts, and syscall anomalies at runtime—complementing image scanning for zero-day behavior.

Documented **Data sources**: `sourcetype=falco:alert`, `sourcetype=sysdig:secure`. **App/TA** (typical add-on context): Falco (JSON to HEC), Sysdig Secure. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: falco:alert. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="falco:alert". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by rule, container.name, k8s.pod.name, proc.name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Docker data, spot-check a few events against the Docker engine on the host and the container list you expect. Compare with known good and bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule, container, count), Timeline, Heatmap (rule vs namespace).

## SPL

```spl
index=containers sourcetype="falco:alert" priority="Critical" OR priority="Error"
| stats count by rule, container.name, k8s.pod.name, proc.name
| sort -count
```

## Visualization

Table (rule, container, count), Timeline, Heatmap (rule vs namespace).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
