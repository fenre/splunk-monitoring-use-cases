<!-- AUTO-GENERATED from UC-3.5.14.json — DO NOT EDIT -->

---
id: "3.5.14"
title: "eBPF Process-Level Security Observability (Tetragon)"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.5.14 · eBPF Process-Level Security Observability (Tetragon)

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We place invisible sensors inside each program container that detect when something unusual happens — like an unauthorized person trying to open a locked filing cabinet or running tools they should not have — and immediately alert the security team.*

---

## Description

Ingests Cilium **Tetragon** eBPF runtime security events to detect **suspicious process executions** (reverse shells, reconnaissance tools, package managers in production), **sensitive file access** (/etc/shadow, SSH keys, kubeconfig), and **privilege escalation syscalls** (ptrace, mount, unshare) inside containers — classifying events by severity (CRITICAL/HIGH/MEDIUM) and correlating with Kubernetes pod identity for immediate incident response.

## Value

Container security traditionally relies on image scanning (pre-deployment) and network policy (connection-level). Neither detects what happens inside a running container after deployment — a compromised application executing a reverse shell, reading credential files, or escalating privileges. Tetragon fills this gap by observing every process execution and sensitive syscall at the Linux kernel level via eBPF, with negligible performance overhead. Ingesting these events into Splunk enables correlation with network flows (UC-3.5.13), application logs, and infrastructure metrics to reconstruct the full attack chain from initial compromise to lateral movement.

## Implementation

Deploy Tetragon as a DaemonSet with TracingPolicy resources defining monitored syscalls and file paths. Export events to Splunk via the OTel filelog receiver or FluentBit. Build two search variants: severity-classified security event detection and new-binary-in-namespace anomaly detection. Alert on CRITICAL events immediately and HIGH events within 15 minutes.

## Detailed Implementation

### Prerequisites
- **Tetragon** 1.0+ deployed as a **DaemonSet** in the cluster. Tetragon installs **eBPF programs** into the Linux kernel that intercept **process execution**, **file operations**, **network connections**, and configurable **kernel functions** (**kprobes**/**tracepoints**) — providing ****kernel-level** runtime security observability** without modifying application code or **container images**.
- **TracingPolicy** custom resources defining what to monitor. Tetragon ships with default policies for common **security events**, but production deployments should define explicit policies:
  — **Process execution monitoring**: capture all `execve` **syscalls** with binary path, arguments, UID, and parent process lineage
  — **Sensitive **file access****: monitor reads/writes to `/etc/shadow`, `/etc/passwd`, `~/.ssh/`, `~/.kube/config`, `/proc/*/mem`
  — **Privilege escalation syscalls**: monitor `ptrace`, `mount`, `unshare`, `setuid`, `setgid`, `capset`
  — **Network connection monitoring**: capture `connect` and `bind` syscalls with destination IP/port
- **Event export configuration**: Tetragon exports events as JSON via its **export API** (`/var/run/tetragon/tetragon.log` by default). Configure the OTel Collector's **filelog receiver** to tail this file and send events to **Splunk HEC** as **`sourcetype=tetragon:events`**.
- **Splunk HEC** token for **`index=containers`** with sourcetype routing for Tetragon events, policies, and Kubernetes context.
- **Kubernetes **security context****: Tetragon runs as a **privileged DaemonSet** with **host PID** namespace access. The Tetragon agent's **ServiceAccount** needs RBAC permissions to read pod metadata for Kubernetes identity enrichment.
- **Performance impact**: Tetragon's eBPF programs are JIT-compiled by the kernel and execute in microseconds per event. The overhead is typically **<1% CPU** on monitored nodes. Event export volume depends on policy breadth — a policy monitoring all **process executions** generates more data than one monitoring only sensitive file access.
- **License estimate**: event volume varies significantly by policy breadth and workload activity. A 20-node cluster with standard security policies generates approximately **10–100 MB/day** of Tetragon events. High-activity clusters with broad kprobe policies may generate 500 MB+/day.
- Splunk RBAC: assign a **`security_analyst`** role with **`srchIndexesAllowed`** including `containers`.

### Step 1 — Configure data collection
(1) **TracingPolicy for sensitive file access**: create a TracingPolicy that monitors file open operations on sensitive paths:
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: sensitive-file-access
spec:
  kprobes:
  - call: security_file_open
    args:
    - index: 0
      type: file
    selectors:
    - matchArgs:
      - index: 0
        operator: Prefix
        values:
        - /etc/shadow
        - /etc/passwd
        - /root/.ssh
        - /home/*/.ssh
        - /root/.kube
```

This policy generates a **kprobe event** whenever a container process opens any of the specified sensitive files. Each event includes the **binary path** (which process opened the file), **arguments**, **UID/GID**, and full **Kubernetes metadata** (namespace, pod name, container name).

(2) **TracingPolicy for **privilege escalation****: monitor syscalls that indicate privilege escalation attempts:
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: privilege-escalation
spec:
  kprobes:
  - call: sys_ptrace
  - call: sys_mount
  - call: sys_unshare
  - call: sys_setuid
```

(3) **Process execution baseline**: Tetragon captures all `process_exec` events by default. These events include the **full binary path**, **command-line arguments**, **parent process**, and **cgroup** information. This data enables two security use cases:
  — **Known-bad detection**: match binaries against a list of suspicious tools (nc, ncat, nmap, etc.)
  — **Anomaly detection**: identify binaries that have **never been seen before** in a namespace. The "**new binary** detection" search variant finds process executions where the binary has never appeared in the namespace's history — a strong indicator of **container compromise**.

(4) **Kubernetes identity enrichment**: Tetragon automatically enriches events with Kubernetes metadata (namespace, pod name, container name, labels) by mapping the process's **cgroup** to the Kubernetes API. This enrichment is critical for identifying which workload generated the security event without additional join operations in Splunk.

(5) **Event volume control**: use TracingPolicy **selectors** to filter events at the kernel level rather than in Splunk. For example, exclude events from known system processes (**PID 1**, **container entrypoints**) or from specific namespaces (monitoring, kube-system) where certain activities are expected.

### Step 2 — Create the search and alert
The primary SPL classifies Tetragon events by severity based on the binary, file path, and syscall involved:
— **CRITICAL**: access to credential files (/etc/shadow, SSH keys, kubeconfig) OR execution of known **attack tools** (nc, nmap, curl, wget, python, perl) as **root** (UID 0). These require **immediate investigation**.
— **HIGH**: **kprobe** events for privilege escalation syscalls (ptrace, mount, unshare) OR **root shell** execution (bash, sh as UID 0). These are strong indicators of container compromise.
— **MEDIUM**: execution of **package managers** (apt, yum, apk, pip, npm) in production. Package installation in a running container is a deviation from immutable infrastructure principles.

The new-binary detection variant identifies process executions where the binary has **never been seen before** in the namespace within the last hour. This **anomaly detection** catches novel attack tools, downloaded malware, and compiled exploit code.

Schedule the **severity classification** search every **5 minutes** and alert on CRITICAL events immediately (PagerDuty P1) and HIGH events within 15 minutes (P2). Schedule the new-binary detection every **hour** and alert on any new binaries in production namespaces.

### Step 3 — Validate
(a) Verify Tetragon event collection: `index=containers sourcetype="tetragon:events" earliest=-1h | stats count by event_type`. Should show PROCESS_EXEC and other event types.
(b) Test sensitive file detection: `kubectl exec <test-pod> -- cat /etc/shadow`. Verify a CRITICAL event appears: `index=containers sourcetype="tetragon:events" filepath="/etc/shadow" earliest=-5m`.
(c) Test suspicious binary detection: `kubectl exec <test-pod> -- apt-get update`. Verify a MEDIUM event for apt-get appears.
(d) Verify Kubernetes enrichment: `index=containers sourcetype="tetragon:events" earliest=-1h | table k8s_ns k8s_pod binary`. All events should have namespace and pod information.
(e) Test new-binary detection: copy a unique binary into a container and execute it. Verify it appears in the new-binary search within the next hour.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — CRITICAL events (last 1h, red if > 0), HIGH events (last 1h), affected namespaces, new binaries detected, Tetragon agent coverage (nodes with agent vs total nodes).
- Row B: **event timeline** colored by severity over 24h — shows temporal patterns of security events.
- Row C: **security event table** — k8s_ns, event_type, severity, binaries, files, events, affected_pods. Red rows for CRITICAL.
- Row D: **new binary table** — binary, k8s_ns, first_seen, hours_old, exec_count. Any entry is suspicious.
- **Alerting**: CRITICAL event → PagerDuty P1 + Slack `#security-incident` (potential active compromise); HIGH event → PagerDuty P2; MEDIUM event in production namespace → Slack `#security-ops`; new binary in production → Slack `#security-ops`.
- **Runbook** (owner: security operations): (1) for CRITICAL/HIGH: identify the pod and namespace, (2) collect additional context: `kubectl describe pod <pod> -n <ns>`, (3) check if the activity was authorized (maintenance, debugging), (4) if unauthorized: isolate the pod via network policy, preserve evidence, escalate to **incident response**.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **process tree** visualization showing parent-child process relationships within a container — this reveals the **attack chain** from initial execution to privilege escalation. Pair with a **binary frequency histogram** per namespace showing the distribution of executed binaries.
- **Alert design**: include `k8s_ns`, `k8s_pod`, `event_type`, `severity`, `binary`, `args`, `filepath`, `uid`, and `parent_binary` in the alert payload.
- **No events appearing** — Tetragon may not be deployed or the export file may not be readable by the OTel Collector. Verify: `kubectl get pods -n kube-system -l app.kubernetes.io/name=tetragon` and `kubectl logs -n kube-system <tetragon-pod> --tail=10`.
- **High event volume from system processes** — Tetragon monitors all processes including container entrypoints and **health check** scripts. Use TracingPolicy selectors to exclude known system binaries or use the severity classification to filter low-severity events.
- **Kubernetes metadata missing** — Tetragon needs access to the Kubernetes API for identity enrichment. Verify the Tetragon ServiceAccount has the required RBAC permissions and that the API server is reachable from the agent pods.

## SPL

```spl
`comment("--- Tetragon Security Events — High-Severity Process and File Access Detection ---")`
index=containers sourcetype="tetragon:events"
| eval event_type=case(
    isnotnull(process_exec), "PROCESS_EXEC",
    isnotnull(process_kprobe), "KPROBE",
    isnotnull(process_tracepoint), "TRACEPOINT",
    isnotnull(process_exit), "PROCESS_EXIT",
    1=1, "OTHER")
| eval binary=coalesce(process_exec.binary, process_kprobe.process.binary, binary)
| eval args=coalesce(process_exec.arguments, process_kprobe.args, arguments)
| eval filepath=coalesce(process_kprobe.args.path, file_path, "")
| eval k8s_ns=coalesce(process_exec.process.pod.namespace, k8s_namespace, namespace)
| eval k8s_pod=coalesce(process_exec.process.pod.name, k8s_pod_name, pod)
| eval uid=coalesce(process_exec.process.uid, uid, 0)
| eval severity=case(
    match(filepath, "(?i)/etc/shadow|/etc/passwd|.ssh/|.kube/config"), "CRITICAL",
    match(binary, "(?i)/(nc|ncat|nmap|curl|wget|python|perl|ruby)$") AND uid=0, "CRITICAL",
    event_type="KPROBE" AND match(args, "(?i)ptrace|mount|unshare"), "HIGH",
    match(binary, "(?i)/(bash|sh|dash|zsh)$") AND uid=0, "HIGH",
    match(binary, "(?i)/(apt|yum|apk|pip|npm)$"), "MEDIUM",
    1=1, "LOW")
| where severity IN ("CRITICAL", "HIGH", "MEDIUM")
| bin _time span=5m
| stats count as events,
    dc(binary) as unique_binaries,
    dc(k8s_pod) as affected_pods,
    values(binary) as binaries,
    values(filepath) as files,
    latest(args) as last_args
    by _time, k8s_ns, event_type, severity
| sort -severity, -events
| table _time k8s_ns event_type severity events unique_binaries affected_pods binaries files

`comment("--- Process Execution Baseline Deviation — New Binary Detection ---")`
index=containers sourcetype="tetragon:events" process_exec.binary=*
| eval binary=coalesce(process_exec.binary, binary)
| eval k8s_ns=coalesce(process_exec.process.pod.namespace, k8s_namespace)
| eval k8s_pod=coalesce(process_exec.process.pod.name, k8s_pod_name)
| eval container=coalesce(process_exec.process.docker, container_id)
| stats earliest(_time) as first_seen, count as exec_count by binary, k8s_ns
| where first_seen > relative_time(now(), "-1h")
| eval hours_old=round((now() - first_seen) / 3600, 1)
| sort -exec_count
| table binary k8s_ns first_seen hours_old exec_count

`comment("--- TracingPolicy Compliance — Node Coverage and Policy Deployment Status ---")`
index=containers sourcetype="tetragon:policy"
| eval policy_name=coalesce(metadata.name, policy_name)
| eval policy_ns=coalesce(metadata.namespace, "cluster-wide")
| eval policy_kind=coalesce(kind, policy_kind)
| stats latest(_time) as last_seen, count as event_count by policy_name, policy_ns, policy_kind
| eval hours_since=round((now() - last_seen) / 3600, 1)
| eval status=case(
    hours_since > 24, "STALE",
    hours_since > 6, "WARNING",
    1=1, "ACTIVE")
| sort -hours_since
| table policy_name policy_ns policy_kind last_seen hours_since status
```

## Visualization

Security event timeline by severity, process tree diagram, binary execution heatmap by namespace, file access table, new binary alert list, single-value tiles (CRITICAL count, affected namespaces).

## Known False Positives

**legitimate_debugging_sessions** — Developers or SREs using kubectl exec to debug production pods generate process execution events (bash, sh, cat, curl) that match suspicious binary patterns. These are legitimate troubleshooting activities, not attacks. Correlate with kubectl audit logs and maintenance windows to classify debugging sessions.

**container_init_processes** — Container entrypoint scripts often execute shell processes and file access operations during startup that trigger Tetragon events. These are transient startup activities, not runtime anomalies. Filter events from processes with PID 1 or within the first 30 seconds of container start time.

**health_check_execution** — Kubernetes liveness and readiness probes that execute commands (exec probes) generate repeated process execution events for the probe command. These are expected periodic executions, not suspicious activity. Identify and exclude known probe command patterns.

**ci_cd_build_containers** — CI/CD pipeline containers (build, test, deploy stages) legitimately execute package managers, compilers, and shell scripts as part of their function. These containers run in CI namespaces and should be excluded from production security alerts via namespace-scoped TracingPolicies.

**operator_reconciliation_loops** — Kubernetes operators and controllers running inside the cluster execute kubectl, curl, or custom binaries as part of their reconciliation loops. These process executions are expected and continuous. Identify operator pods by label and exclude from anomaly detection.

**sidecar_proxy_binary** — Service mesh sidecar proxies (Envoy, istio-proxy) execute specific binaries during startup and configuration reload that may trigger process execution events. These are expected mesh infrastructure activities.

## References

- [Tetragon — Introduction and Architecture](https://tetragon.io/docs/overview/)
- [Tetragon — TracingPolicy Reference](https://tetragon.io/docs/concepts/tracing-policy/)
- [Tetragon — Security Observability Use Cases](https://tetragon.io/docs/use-cases/)
- [Cilium — eBPF Runtime Security](https://docs.cilium.io/en/stable/security/)
- [Splunk — Endpoint Data Model](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
