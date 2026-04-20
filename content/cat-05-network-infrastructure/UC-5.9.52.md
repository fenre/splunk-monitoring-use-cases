---
id: "5.9.52"
title: "ThousandEyes Trace Span Analysis and Drill-Down"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.52 · ThousandEyes Trace Span Analysis and Drill-Down

## Description

ThousandEyes Transaction tests can emit OpenTelemetry traces with span-level timing for each step of the scripted workflow. Ingesting these traces into Splunk enables correlation with application traces from Splunk APM for end-to-end distributed tracing.

## Value

ThousandEyes Transaction tests can emit OpenTelemetry traces with span-level timing for each step of the scripted workflow. Ingesting these traces into Splunk enables correlation with application traces from Splunk APM for end-to-end distributed tracing.

## Implementation

Enable the Tests Stream — Traces input in the Cisco ThousandEyes App. Traces are emitted for Transaction tests and provide span-level timing for each step of the scripted workflow. The trace data follows OpenTelemetry conventions with `trace_id`, `span_id`, `parent_span_id`, `service.name`, `span.name`, `duration`, and custom attributes. Traces can be correlated with Splunk APM traces using shared context propagation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Traces.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the Tests Stream — Traces input in the Cisco ThousandEyes App. Traces are emitted for Transaction tests and provide span-level timing for each step of the scripted workflow. The trace data follows OpenTelemetry conventions with `trace_id`, `span_id`, `parent_span_id`, `service.name`, `span.name`, `duration`, and custom attributes. Traces can be correlated with Splunk APM traces using shared context propagation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` sourcetype="thousandeyes:traces"
| stats count avg(duration_ms) as avg_span_duration_ms by service.name, span.name, span.kind
| sort -avg_span_duration_ms
```

Understanding this SPL

**ThousandEyes Trace Span Analysis and Drill-Down** — ThousandEyes Transaction tests can emit OpenTelemetry traces with span-level timing for each step of the scripted workflow. Ingesting these traces into Splunk enables correlation with application traces from Splunk APM for end-to-end distributed tracing.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Traces. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: thousandeyes:traces. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by service.name, span.name, span.kind** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (spans by duration), Trace waterfall (via Splunk APM or custom visualization), Bar chart (avg span duration by step).

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
`stream_index` sourcetype="thousandeyes:traces"
| stats count avg(duration_ms) as avg_span_duration_ms by service.name, span.name, span.kind
| sort -avg_span_duration_ms
```

## Visualization

Table (spans by duration), Trace waterfall (via Splunk APM or custom visualization), Bar chart (avg span duration by step).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
