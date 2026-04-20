---
id: "3.1.17"
title: "Container Resource Limit Enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.17 · Container Resource Limit Enforcement

## Description

Verifying cgroup limits match declared `docker run`/`compose` settings catches silent misconfigurations that allow noisy neighbors or false capacity plans.

## Value

Verifying cgroup limits match declared `docker run`/`compose` settings catches silent misconfigurations that allow noisy neighbors or false capacity plans.

## Implementation

Periodically ingest `docker inspect` for running containers. Flag production workloads with unlimited memory or CPU when policy requires limits. Cross-check with `docker:stats` actual usage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Docker.
• Ensure the following data sources are available: `sourcetype=docker:inspect`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically ingest `docker inspect` for running containers. Flag production workloads with unlimited memory or CPU when policy requires limits. Cross-check with `docker:stats` actual usage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:inspect"
| eval mem_limit_bytes=tonumber(HostConfig.Memory)
| eval nano_cpus=tonumber(HostConfig.NanoCpus)
| eval cpu_quota=tonumber(HostConfig.CpuQuota)
| where isnull(mem_limit_bytes) OR mem_limit_bytes=0 OR (nano_cpus=0 AND cpu_quota<=0)
| table container_name image host mem_limit_bytes nano_cpus cpu_quota
```

Understanding this SPL

**Container Resource Limit Enforcement** — Verifying cgroup limits match declared `docker run`/`compose` settings catches silent misconfigurations that allow noisy neighbors or false capacity plans.

Documented **Data sources**: `sourcetype=docker:inspect`. **App/TA** (typical add-on context): Splunk Connect for Docker. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:inspect. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:inspect". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mem_limit_bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **nano_cpus** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **cpu_quota** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where isnull(mem_limit_bytes) OR mem_limit_bytes=0 OR (nano_cpus=0 AND cpu_quota<=0)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Container Resource Limit Enforcement**): table container_name image host mem_limit_bytes nano_cpus cpu_quota


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (container, mem limit, CPU), Compliance single value (% with limits), Bar chart by host.

## SPL

```spl
index=containers sourcetype="docker:inspect"
| eval mem_limit_bytes=tonumber(HostConfig.Memory)
| eval nano_cpus=tonumber(HostConfig.NanoCpus)
| eval cpu_quota=tonumber(HostConfig.CpuQuota)
| where isnull(mem_limit_bytes) OR mem_limit_bytes=0 OR (nano_cpus=0 AND cpu_quota<=0)
| table container_name image host mem_limit_bytes nano_cpus cpu_quota
```

## Visualization

Table (container, mem limit, CPU), Compliance single value (% with limits), Bar chart by host.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
