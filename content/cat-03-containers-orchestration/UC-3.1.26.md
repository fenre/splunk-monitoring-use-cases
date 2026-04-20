---
id: "3.1.26"
title: "Image Pull Failures and Registry Connectivity"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.26 · Image Pull Failures and Registry Connectivity

## Description

Failed image pulls block container starts, scaling operations, and deployments. Common causes include registry rate limits (Docker Hub's 100 pulls/6h for free accounts), expired credentials, network issues, and deleted image tags.

## Value

Failed image pulls block container starts, scaling operations, and deployments. Common causes include registry rate limits (Docker Hub's 100 pulls/6h for free accounts), expired credentials, network issues, and deleted image tags.

## Implementation

Forward Docker daemon logs to Splunk. Search for pull-related error messages including authentication failures, rate limit responses (HTTP 429), image-not-found errors, and network timeouts. Alert on any pull failure in production. Track pull failure rate over time to detect intermittent registry connectivity issues. For Docker Hub rate limits, monitor the `RateLimit-Remaining` header if available in debug logs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Docker daemon logs, `docker events` scripted input.
• Ensure the following data sources are available: `sourcetype=docker:daemon`, `sourcetype=docker:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Docker daemon logs to Splunk. Search for pull-related error messages including authentication failures, rate limit responses (HTTP 429), image-not-found errors, and network timeouts. Alert on any pull failure in production. Track pull failure rate over time to detect intermittent registry connectivity issues. For Docker Hub rate limits, monitor the `RateLimit-Remaining` header if available in debug logs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="docker:daemon" ("pull" AND ("error" OR "denied" OR "rate limit" OR "not found" OR "timeout"))
| rex "Error response from daemon: (?<error_msg>.+)"
| stats count as failures, latest(error_msg) as last_error by image, host
| sort -failures
```

Understanding this SPL

**Image Pull Failures and Registry Connectivity** — Failed image pulls block container starts, scaling operations, and deployments. Common causes include registry rate limits (Docker Hub's 100 pulls/6h for free accounts), expired credentials, network issues, and deleted image tags.

Documented **Data sources**: `sourcetype=docker:daemon`, `sourcetype=docker:events`. **App/TA** (typical add-on context): Docker daemon logs, `docker events` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: docker:daemon. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="docker:daemon". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by image, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed images with error), Bar chart (failures by registry), Line chart (pull failure rate over time).

## SPL

```spl
index=containers sourcetype="docker:daemon" ("pull" AND ("error" OR "denied" OR "rate limit" OR "not found" OR "timeout"))
| rex "Error response from daemon: (?<error_msg>.+)"
| stats count as failures, latest(error_msg) as last_error by image, host
| sort -failures
```

## Visualization

Table (failed images with error), Bar chart (failures by registry), Line chart (pull failure rate over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
