---
id: "4.1.64"
title: "EKS Control Plane Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.1.64 · EKS Control Plane Audit

## Description

Kubernetes audit logs capture who changed roles, secrets, and workloads; essential for forensics and SOC2 evidence on EKS.

## Value

Kubernetes audit logs capture who changed roles, secrets, and workloads; essential for forensics and SOC2 evidence on EKS.

## Implementation

Enable EKS audit logging to CloudWatch Logs and subscribe to Splunk. Optionally include CloudTrail for `CreateCluster`, `AssociateIdentityProviderConfig`. Alert on cluster-admin bindings, anonymous access, or secret reads from unexpected service accounts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: EKS control plane logs in `sourcetype=aws:cloudwatchlogs` (cluster audit), CloudTrail `eks.amazonaws.com` API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable EKS audit logging to CloudWatch Logs and subscribe to Splunk. Optionally include CloudTrail for `CreateCluster`, `AssociateIdentityProviderConfig`. Alert on cluster-admin bindings, anonymous access, or secret reads from unexpected service accounts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatchlogs" log_group="/aws/eks/*/cluster"
| search "audit.k8s.io" verb="create" objectRef.resource="clusterroles" OR objectRef.resource="secrets"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```

Understanding this SPL

**EKS Control Plane Audit** — Kubernetes audit logs capture who changed roles, secrets, and workloads; essential for forensics and SOC2 evidence on EKS.

Documented **Data sources**: EKS control plane logs in `sourcetype=aws:cloudwatchlogs` (cluster audit), CloudTrail `eks.amazonaws.com` API. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatchlogs. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatchlogs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by user.username, objectRef.namespace, objectRef.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**EKS Control Plane Audit** — Kubernetes audit logs capture who changed roles, secrets, and workloads; essential for forensics and SOC2 evidence on EKS.

Documented **Data sources**: EKS control plane logs in `sourcetype=aws:cloudwatchlogs` (cluster audit), CloudTrail `eks.amazonaws.com` API. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, resource, count), Timeline (privileged API calls), Sankey (user→namespace).

## SPL

```spl
index=aws sourcetype="aws:cloudwatchlogs" log_group="/aws/eks/*/cluster"
| search "audit.k8s.io" verb="create" objectRef.resource="clusterroles" OR objectRef.resource="secrets"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

## Visualization

Table (user, resource, count), Timeline (privileged API calls), Sankey (user→namespace).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
