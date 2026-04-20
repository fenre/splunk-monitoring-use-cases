---
id: "3.1.25"
title: "Docker Socket Exposure Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.1.25 · Docker Socket Exposure Detection

## Description

Mounting `/var/run/docker.sock` inside a container grants full Docker API access, effectively giving root-level control over the host. This is the most common Docker privilege escalation vector and should be flagged immediately.

## Value

Mounting `/var/run/docker.sock` inside a container grants full Docker API access, effectively giving root-level control over the host. This is the most common Docker privilege escalation vector and should be flagged immediately.

## Implementation

Periodically run `docker inspect` on all containers and forward the JSON output. Search bind mounts for `/var/run/docker.sock` or the Docker API socket path. Alert on any detection. For runtime detection, use Falco rules that trigger on socket access. Also check for TCP Docker daemon exposure (`-H tcp://0.0.0.0`) in daemon configuration. Only allow socket mounting for explicitly approved infrastructure containers (e.g., Portainer, Traefik) via an allowlist lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `docker inspect` scripted input, Falco.
• Ensure the following data sources are available: `sourcetype=docker:inspect`, `sourcetype=falco:alert`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically run `docker inspect` on all containers and forward the JSON output. Search bind mounts for `/var/run/docker.sock` or the Docker API socket path. Alert on any detection. For runtime detection, use Falco rules that trigger on socket access. Also check for TCP Docker daemon exposure (`-H tcp://0.0.0.0`) in daemon configuration. Only allow socket mounting for explicitly approved infrastructure containers (e.g., Portainer, Traefik) via an allowlist lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:inspect"
| spath output=mounts path=Mounts{}
| mvexpand mounts
| spath input=mounts output=mount_source path=Source
| where mount_source="/var/run/docker.sock"
| table _time, container_name, image, host, mount_source
```

Understanding this SPL

**Docker Socket Exposure Detection** — Mounting `/var/run/docker.sock` inside a container grants full Docker API access, effectively giving root-level control over the host. This is the most common Docker privilege escalation vector and should be flagged immediately.

Documented **Data sources**: `sourcetype=docker:inspect`, `sourcetype=falco:alert`. **App/TA** (typical add-on context): `docker inspect` scripted input, Falco. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:inspect. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:inspect". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where mount_source="/var/run/docker.sock"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Docker Socket Exposure Detection**): table _time, container_name, image, host, mount_source


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (containers with socket mount), Single value (exposed container count), Alert (immediate page).

## SPL

```spl
index=containers sourcetype="docker:inspect"
| spath output=mounts path=Mounts{}
| mvexpand mounts
| spath input=mounts output=mount_source path=Source
| where mount_source="/var/run/docker.sock"
| table _time, container_name, image, host, mount_source
```

## Visualization

Table (containers with socket mount), Single value (exposed container count), Alert (immediate page).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
