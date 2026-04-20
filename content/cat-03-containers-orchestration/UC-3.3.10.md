---
id: "3.3.10"
title: "Image Stream Tag Drift"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.10 · Image Stream Tag Drift

## Description

ImageStreams can point to unexpected digests after imports or mirroring; drift from expected tags breaks reproducible builds and compliance baselines.

## Value

ImageStreams can point to unexpected digests after imports or mirroring; drift from expected tags breaks reproducible builds and compliance baselines.

## Implementation

Scripted input emits `digest` per tag plus `expected_digest` from GitOps/CMDB (or use `| lookup` against a KV store). Alert on mismatch for `latest` and release tags used in production pipelines.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `oc get imagestream -o json` scripted input.
• Ensure the following data sources are available: `sourcetype=openshift:imagestream`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input emits `digest` per tag plus `expected_digest` from GitOps/CMDB (or use `| lookup` against a KV store). Alert on mismatch for `latest` and release tags used in production pipelines.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:imagestream"
| where isnotnull(expected_digest) AND isnotnull(digest) AND digest!=expected_digest
| table namespace name tag digest expected_digest source
| sort namespace, name
```

Understanding this SPL

**Image Stream Tag Drift** — ImageStreams can point to unexpected digests after imports or mirroring; drift from expected tags breaks reproducible builds and compliance baselines.

Documented **Data sources**: `sourcetype=openshift:imagestream`. **App/TA** (typical add-on context): `oc get imagestream -o json` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:imagestream. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:imagestream". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where isnotnull(expected_digest) AND isnotnull(digest) AND digest!=expected_digest` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Image Stream Tag Drift**): table namespace name tag digest expected_digest source
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (imagestream, tag, digests), Drift count single value, Timeline of tag updates.

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
index=openshift sourcetype="openshift:imagestream"
| where isnotnull(expected_digest) AND isnotnull(digest) AND digest!=expected_digest
| table namespace name tag digest expected_digest source
| sort namespace, name
```

## Visualization

Table (imagestream, tag, digests), Drift count single value, Timeline of tag updates.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
