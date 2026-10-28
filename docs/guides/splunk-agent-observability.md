---
title: Splunk Agent Observability Guide
type: integration-guide
---

# Splunk Agent Observability

Splunk Agent Observability records each LLM agent request as a trace, scores stored traces with evaluators, and can block or steer a step inline with Agent Control. It is the Galileo platform after Cisco's acquisition. The Python package is `splunk-ao`; import `SplunkAOLogger` from `splunk_ao`.

The use cases in subcategory 13.8 are implemented in Splunk Agent Observability, not in the Splunk platform. They carry product artifacts (instrumentation code, evaluator settings, stream alerts, Agent Control definitions, access reviews, Model Pricing and Tokenomics) instead of SPL. All of them are drafts: they were written from the product documentation without tenant access, and each should be confirmed in the console before it is promoted.

Splunk Agent Observability is not Splunk Observability Cloud<sup class="ref">[<a href="#ref-5">5</a>]</sup>. Its traces do not appear in Observability Cloud global search or on APM pages. For OpenTelemetry GenAI telemetry indexed in the Splunk platform, see the AI & LLM Observability guide (subcategory 13.4).

---

## Which loop a use case needs

| Need | Loop | What it can do | Use cases |
| --- | --- | --- | --- |
| Show what the agent did | Trace | Store the span tree | UC-13.8.1 to UC-13.8.8 |
| Is this any good? | Evaluator on the Agent Stream | Score stored traces. Never blocks the reply | UC-13.8.13 to UC-13.8.23 |
| Tell someone | Alert on the Agent Stream | Email, Slack or webhook after a window of scores. Never blocks | UC-13.8.9 to UC-13.8.12, UC-13.8.24, UC-13.8.25 |
| Stop or redirect this step | Agent Control | Deny, steer or observe inline | UC-13.8.26 to UC-13.8.31 |

A Tool Selection Quality score on a trace does not mean that check runs as a control. Agent Control runs its own checks (regex, list, JSON, SQL, Luna-2, custom); it does not run the stream's evaluators.

Access governance (UC-13.8.32 to UC-13.8.34) and cost (UC-13.8.35 to UC-13.8.37) sit alongside the loops.

## Data model

Project → Agent Stream → session → trace → span.

- **Project:** one application, and the visibility boundary. By default only the creator and admins see it. A second project for the same application splits its traces.
- **Agent Stream:** one environment or one agent inside the project. The SDK and REST API call it a log stream (`log_stream_id`). Names are case-sensitive, and logging to a name that does not exist creates it.
- **Session:** groups the traces of one conversation.
- **Trace:** one request.
- **Span:** one LLM call, tool call, retrieval or agent step.

Evaluators, alerts and sampling are set per Agent Stream. Span filters are set per project.

## Instrumentation

Agents read `SPLUNK_AO_PROJECT` and `SPLUNK_AO_AGENT_STREAM` from the environment. SaaS tenants authenticate with `SPLUNK_AO_REALM` and `SPLUNK_AO_O11Y_TOKEN`. On-prem tenants use `SPLUNK_AO_API_KEY` plus `SPLUNK_AO_CONSOLE_URL`; the SDK derives the API host from the console URL, and `SPLUNK_AO_API_URL` is set only when that derivation is wrong. `SPLUNK_AO_USER`, `SPLUNK_AO_PASSWORD` and `SPLUNK_AO_USER_ID` are console login and never belong in agent code (UC-13.8.34).

Points that decide whether traces arrive:

- A trace with no spans is never exported, and nothing reports it (UC-13.8.2).
- `conclude()` closes the current open span, not the whole tree. Spans left open are not exported. `conclude(conclude_all=True)` closes everything.
- Exceptions should conclude the trace with `status_code=500` and flush before re-raising (UC-13.8.4).
- LLM spans need the `tools` schemas for Tool Selection Quality (UC-13.8.13, UC-13.8.14).
- For LangChain and LangGraph, pass the Splunk callback on the graph invoke, not only on the chat model (UC-13.8.7).

## Evaluators

Evaluators are defined for the organization and turned on per Agent Stream. `enable_evaluators` replaces the stream's set (UC-13.8.22). They run after the trace is stored, on a sample, and there is no documented default sample rate.

- Preset judges are LLM-as-a-judge and need a model integration on the org.
- Luna judges are Splunk-hosted small models with no customer model key. On SaaS, Luna is limited to Prompt Injection, Toxicity, Sexism, PII and Context Adherence (UC-13.8.16 to UC-13.8.20).
- Custom LLM-as-a-judge needs a model integration. Autotune rewrites its prompt from reviewer corrections (UC-13.8.21).
- Experiments are the offline loop: one trace per dataset row, runnable in CI (UC-13.8.23).

## Alerts

Alerts sit on the Agent Stream's Alerts tab: an evaluator or a built-in metric (Status Code, Cost, Latency, Trace Count), an aggregation, a threshold and a window. Notifications go to email, a Slack incoming webhook or a generic HTTP webhook. An alert on an evaluator sees sampled traces only.

The webhook body includes `event` (`alert.triggered`), `conditions[].observed_value`, `dedup_key`, `deep_link` and any configured `metadata`. Forwarding it into the Splunk platform (for example to HTTP Event Collector) would add `splunk-platform` as a second product with SPL over the alert events. No use case does this yet, because that path has not been tested on a live tenant.

## Agent Control

The app calls `agent_control.init` and decorates each controlled step with `@control(step_name=...)`. A control is scoped by step type, step name and stage (`pre` or `post`); its action is deny, steer or observe, with deny winning over steer over observe. If the control server cannot be reached, the call is blocked (UC-13.8.29). Attaching a control to a stream clones it, and editing the original does not update the clone (UC-13.8.30).

## Cost and access

Per-trace cost is the token counts on LLM spans times the org Model Pricing table (UC-13.8.35). Tokenomics is a different system: spend reported by Claude Code, Codex, Cursor, GitHub Copilot and Windsurf, joined to a Workday directory (UC-13.8.37). Do not add the two together.

SaaS system roles are `agent_observability_admin`, `_manager`, `_user` and `_read_only`; project collaborators are owner, editor, annotator and viewer (UC-13.8.32, UC-13.8.33).

## Open questions in the documentation

The documentation disagrees or is silent on these, so no use case relies on them:

- whether Luna-3 can be fine-tuned;
- whether a manager sees every project or only shared ones;
- how long a control check takes, and the default judge count;
- whether an alert can watch control deny counts.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Splunk Agent Observability Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://agent-observability-docs.splunk.com/

### Supporting sources

<a id="ref-2"></a>**[2]** OpenTelemetry Authors. (2026). *OpenTelemetry Semantic Conventions*. Cloud Native Computing Foundation. Retrieved May 11, 2026, from https://opentelemetry.io/docs/specs/semconv/

<a id="ref-3"></a>**[3]** OpenTelemetry Authors. (2026). *OpenTelemetry Specification*. Cloud Native Computing Foundation. Retrieved May 11, 2026, from https://opentelemetry.io/docs/specs/otel/

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Observability Cloud Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/observability/en/

<!-- END-AUTOGENERATED-SOURCES -->
