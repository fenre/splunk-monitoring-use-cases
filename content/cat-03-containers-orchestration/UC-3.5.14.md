---
id: "3.5.14"
title: "eBPF Process-Level Security Observability (Tetragon)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.5.14 · eBPF Process-Level Security Observability (Tetragon)

## Description

Container runtime security traditionally relies on syscall interception (Falco/seccomp) or agent-based file integrity monitoring — both with performance overhead and blind spots. Tetragon provides kernel-level visibility into process execution, file access, network connections, and privilege escalation via eBPF tracing policies, with minimal overhead. Ingesting Tetragon events into Splunk enables correlation with application traces and infrastructure metrics — connecting "a process opened /etc/shadow" with "which user request triggered this" via trace context.

## Value

Container runtime security traditionally relies on syscall interception (Falco/seccomp) or agent-based file integrity monitoring — both with performance overhead and blind spots. Tetragon provides kernel-level visibility into process execution, file access, network connections, and privilege escalation via eBPF tracing policies, with minimal overhead. Ingesting Tetragon events into Splunk enables correlation with application traces and infrastructure metrics — connecting "a process opened /etc/shadow" with "which user request triggered this" via trace context.

## Implementation

Deploy Tetragon as a DaemonSet in Kubernetes. Define TracingPolicies to capture security-relevant events: process execution (detect shells, interpreters, network tools in production containers), file access (sensitive paths like /etc/shadow, SSH keys, Kubernetes secrets), network connections (unexpected outbound connections from application pods), and kprobe events (privilege escalation syscalls like ptrace, mount). Export Tetragon events via JSON log file or gRPC stream to the OTel Collector's filelog receiver, then forward to Splunk HEC. Classify events by severity based on the binary executed (shells and network tools in production = high risk) and file paths accessed (credentials and keys = critical). Correlate with Kubernetes context (pod, namespace, node, container image) for investigation. Integrate with Splunk ES as risk events on container/pod entities.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Distribution of OpenTelemetry Collector, Tetragon (Isovalent/Cilium).
• Ensure the following data sources are available: `sourcetype=tetragon:events`, Tetragon JSON event stream via FluentBit or OTel filelog receiver.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Tetragon as a DaemonSet in Kubernetes. Define TracingPolicies to capture security-relevant events: process execution (detect shells, interpreters, network tools in production containers), file access (sensitive paths like /etc/shadow, SSH keys, Kubernetes secrets), network connections (unexpected outbound connections from application pods), and kprobe events (privilege escalation syscalls like ptrace, mount). Export Tetragon events via JSON log file or gRPC stream to the OTel Collector's …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="tetragon:events"
| eval event_type=case(
    process_exec!="", "process_exec",
    process_file!="", "file_access",
    process_connect!="", "network_connect",
    process_kprobe!="", "kprobe",
    1==1, "other")
| eval severity=case(
    match(binary, "/(nc|ncat|curl|wget|python|perl|ruby|bash|sh)$"), "High",
    match(filepath, "/(etc/shadow|etc/passwd|.ssh/|.kube/)"), "Critical",
    match(event_type, "kprobe") AND match(function_name, "sys_ptrace|sys_mount"), "Critical",
    1==1, "Info")
| where severity IN ("High", "Critical")
| stats count as events, values(binary) as binaries, values(filepath) as files, values(k8s_pod) as pods by _time, k8s_namespace, event_type, severity
| sort -severity, -events
| table _time, k8s_namespace, pods, event_type, severity, binaries, files, events
```

Understanding this SPL

**eBPF Process-Level Security Observability (Tetragon)** — Container runtime security traditionally relies on syscall interception (Falco/seccomp) or agent-based file integrity monitoring — both with performance overhead and blind spots. Tetragon provides kernel-level visibility into process execution, file access, network connections, and privilege escalation via eBPF tracing policies, with minimal overhead. Ingesting Tetragon events into Splunk enables correlation with application traces and infrastructure metrics — connecting "a…

Documented **Data sources**: `sourcetype=tetragon:events`, Tetragon JSON event stream via FluentBit or OTel filelog receiver. **App/TA** (typical add-on context): Splunk Distribution of OpenTelemetry Collector, Tetragon (Isovalent/Cilium). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: tetragon:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="tetragon:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **event_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where severity IN ("High", "Critical")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by _time, k8s_namespace, event_type, severity** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **eBPF Process-Level Security Observability (Tetragon)**): table _time, k8s_namespace, pods, event_type, severity, binaries, files, events

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Endpoint.Processes by Processes.process_name, Processes.user, Processes.dest | sort - count
```

Understanding this CIM / accelerated SPL

**eBPF Process-Level Security Observability (Tetragon)** — Container runtime security traditionally relies on syscall interception (Falco/seccomp) or agent-based file integrity monitoring — both with performance overhead and blind spots. Tetragon provides kernel-level visibility into process execution, file access, network connections, and privilege escalation via eBPF tracing policies, with minimal overhead. Ingesting Tetragon events into Splunk enables correlation with application traces and infrastructure metrics — connecting "a…

Documented **Data sources**: `sourcetype=tetragon:events`, Tetragon JSON event stream via FluentBit or OTel filelog receiver. **App/TA** (typical add-on context): Splunk Distribution of OpenTelemetry Collector, Tetragon (Isovalent/Cilium). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Processes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (security events per namespace), Table (critical events with pod and binary details), Bar chart (events by type and severity), Single value (critical events in last hour).

## SPL

```spl
index=containers sourcetype="tetragon:events"
| eval event_type=case(
    process_exec!="", "process_exec",
    process_file!="", "file_access",
    process_connect!="", "network_connect",
    process_kprobe!="", "kprobe",
    1==1, "other")
| eval severity=case(
    match(binary, "/(nc|ncat|curl|wget|python|perl|ruby|bash|sh)$"), "High",
    match(filepath, "/(etc/shadow|etc/passwd|.ssh/|.kube/)"), "Critical",
    match(event_type, "kprobe") AND match(function_name, "sys_ptrace|sys_mount"), "Critical",
    1==1, "Info")
| where severity IN ("High", "Critical")
| stats count as events, values(binary) as binaries, values(filepath) as files, values(k8s_pod) as pods by _time, k8s_namespace, event_type, severity
| sort -severity, -events
| table _time, k8s_namespace, pods, event_type, severity, binaries, files, events
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Endpoint.Processes by Processes.process_name, Processes.user, Processes.dest | sort - count
```

## Visualization

Timeline (security events per namespace), Table (critical events with pod and binary details), Bar chart (events by type and severity), Single value (critical events in last hour).

## References

- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
