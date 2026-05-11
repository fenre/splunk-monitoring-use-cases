<!-- AUTO-GENERATED from UC-3.5.11.json — DO NOT EDIT -->

---
id: "3.5.11"
title: "Sidecar Injection Validation"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-3.5.11 · Sidecar Injection Validation

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Fault &middot; **Wave:** Crawl &middot; **Status:** Verified

*Every program in our network is supposed to have a security guard assigned to it — we regularly check which programs are missing their guard and report them so they can be fixed before sensitive information travels unprotected.*

---

## Description

Continuously validates that all pods running in Istio **injection-enabled namespaces** contain the **istio-proxy** sidecar container, cross-referencing namespace labels with pod container lists and tracking istiod webhook **injection success rates** — identifying pods that bypass mesh policy enforcement, mTLS encryption, and traffic management because the sidecar was never injected or silently failed to start.

## Value

A pod running in an injection-enabled namespace without a sidecar is a security and observability gap — it communicates in plaintext while peers expect mTLS, it bypasses authorization policies, and its traffic is invisible to the mesh. This happens more often than expected: a deployment with `sidecar.istio.io/inject: false` annotation, a webhook timeout during cluster pressure, or a namespace label accidentally removed during a Helm upgrade. Continuous validation catches these gaps within minutes rather than discovering them during a security audit or incident investigation weeks later.

## Implementation

Collect pod status snapshots and namespace labels via Splunk Connect for Kubernetes or OTel k8s_cluster receiver into index=containers. Build two search variants: point-in-time compliance check comparing pod container lists against namespace injection labels, and hourly injection success rate trend from istiod Prometheus metrics. Alert on any non-compliant pods in injection-enabled namespaces or injection failure rate > 1%.

## Detailed Implementation

### Prerequisites
- **Istio** 1.14+ service mesh with **sidecar injection** configured via **namespace labels**. **Istio** supports two injection modes:
  — **Label-based**: `istio-injection=enabled` label on the namespace (legacy)
  — **Revision-based**: `istio.io/rev=<revision>` label on the namespace (recommended for **canary upgrades**)
  Both modes use a **MutatingWebhookConfiguration** (`istio-sidecar-injector`) to intercept **pod CREATE** requests and inject the `istio-proxy` sidecar container and `istio-init` init container.
- **Splunk Connect for Kubernetes** deployed to collect **`sourcetype=kube:pod:status`** from the **Kubernetes API**. The pod status snapshot must include the **container list** (names of all containers in the pod spec) and the pod namespace.
- **Namespace label collection**: the **OTel Collector**'s **k8s_cluster receiver** collects namespace metadata including labels. Alternatively, create a **scheduled scripted input** that runs `kubectl get namespaces --show-labels -o json` and indexes the output as **`sourcetype=kube:namespace:labels`**.
- **Namespace injection lookup**: create **`namespace_injection_status.csv`** mapping `namespace` to `injection_enabled` (true/false) and `injection_revision` (the Istio revision label if using canary upgrades). Populate this lookup from the namespace label collection — either manually or via a **scheduled search**:
  `index=containers sourcetype="kube:namespace:labels" | eval injection_enabled=if(match(labels, "istio-injection=enabled") OR match(labels, "istio.io/rev="), "true", "false") | table namespace injection_enabled`
- **Splunk HEC** token for **`index=containers`** with appropriate sourcetype routing.
- **istiod metrics**: configure the OTel Collector **Prometheus receiver** to scrape the istiod `/metrics` endpoint for injection metrics:
  — `sidecar_injection_requests_total` (counter — all injection attempts)
  — `sidecar_injection_success_total` (counter — successful injections)
  — `sidecar_injection_failure_total` (counter — failed injections, labeled by `reason`)
- Splunk RBAC: users running compliance searches need **`srchIndexesAllowed`** including `containers`; assign via a **`mesh_compliance`** role.
- **License estimate**: pod status snapshots generate approximately 1–5 MB/day for a 200-pod cluster. Injection metrics are negligible (~50 KB/day).

### Step 1 — Configure data collection
(1) **Pod status collection**: the **`kube:pod:status`** sourcetype must include the following fields for **compliance check**ing:
— **`containers`** or **`spec.containers`** — the list of container names in the pod. The search checks for the presence of **`istio-proxy`** in this list.
— **`namespace`** — the pod's namespace, used to look up injection status.
— **`ownerReferences`** — the workload controller (Deployment, DaemonSet, StatefulSet, Job) that owns the pod. Used to classify exemptions and aggregate non-compliance by workload rather than individual pods.
— **`annotations`** — pod-level annotations including `sidecar.istio.io/inject` (which can override namespace-level injection when set to `false`)

(2) **Exemption classification**: not all pods in **injection-enabled namespaces** should have sidecars. The search classifies non-compliant pods:
— **CONTROL_PLANE_EXEMPT**: Istio control plane pods (istiod, istio-ingressgateway, istio-egressgateway) do not need injection — they ARE the mesh infrastructure.
— **DAEMONSET_EXEMPT_CHECK**: **DaemonSets** (log collectors, monitoring agents, **CNI plugin**s) are often explicitly excluded from injection because they need **host networking** or privileged access. Review these on a case-by-case basis.
— **INIT_PRESENT_SIDECAR_MISSING**: the **istio-init** container ran but **istio-proxy** is not present — this may indicate the sidecar container **crashed during startup** (check **pod events** and **container status**).
— **INJECTION_BYPASSED**: the pod has no injection-related containers at all — the webhook either did not fire (webhook misconfiguration) or the pod has an explicit **opt-out annotation** (`sidecar.istio.io/inject: "false"`).

(3) **API server audit logs** (optional): for the most comprehensive injection monitoring, collect **API server audit log** entries for the istio-sidecar-injector webhook. These show every pod CREATE request that was processed by the webhook, including the **admission decision** (Allowed/Denied) and any errors. This catches cases where the webhook itself malfunctions.

(4) **Namespace label change detection**: create an alert that triggers when a namespace's `istio-injection` label is removed or changed. This catches accidental label removal during **Helm upgrades** or `kubectl label` operations that silently disable injection for an entire namespace.

### Step 2 — Create the search and alert
The compliance check SPL uses a **lookup** to identify injection-enabled namespaces, then finds pods in those namespaces that lack the `istio-proxy` container. The **`dedup`** by namespace and pod name (sorted by most recent `_time`) ensures each pod is counted once using its latest status.

The injection success rate SPL aggregates istiod's injection metrics hourly:
— **CRITICAL**: failure rate exceeds **10%** — the webhook is actively failing to inject sidecars. New deployments are launching without mesh membership.
— **DEGRADED**: failure rate exceeds **1%** — occasional injection failures that should be investigated.
— **HEALTHY**: failure rate is negligible.

Schedule the compliance check every **30 minutes** and alert when any namespace has `non_compliant_pods > 0`. Schedule the injection success rate every **hour** and alert on CRITICAL or sustained DEGRADED for 3+ hours.

### Step 3 — Validate
(a) Verify pod status collection: `index=containers sourcetype="kube:pod:status" earliest=-1h | stats dc(pod_name) as total_pods, dc(namespace) as namespaces`. Should show all monitored namespaces and pods.
(b) Deploy a non-compliant test pod: `kubectl run no-sidecar --image=nginx --overrides='{"metadata":{"annotations":{"sidecar.istio.io/inject":"false"}}}' -n <injection-enabled-ns>`. Verify it appears in the compliance search results.
(c) Verify the **namespace lookup**: `| inputlookup namespace_injection_status.csv | table namespace injection_enabled injection_revision`. Should list all namespaces with their injection status.
(d) Verify injection metrics: `index=containers sourcetype="otel:metrics" metric_name="sidecar_injection_requests_total" earliest=-1h | stats sum(metric_value) as total`. Should be non-zero if pods have been created recently.
(e) Test exemption logic: verify that istiod pods and system DaemonSets are correctly classified as exempt.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — total injection-enabled namespaces, total pods in those namespaces, non-compliant pod count (red if > 0), compliance percentage, injection success rate.
- Row B: **compliance heatmap** — namespace × compliance status (green=100% compliant, amber=95–99%, red=<95%). Click to drill down to non-compliant pods.
- Row C: **line chart** of injection success rate over 7 days at 1-hour granularity. Overlay injection request count as secondary Y-axis.
- Row D: **non-compliant pod table** — namespace, pod name, owner (Deployment/StatefulSet/DaemonSet), non_compliant_reason, pod age. Sorted by namespace.
- **Alerting**: any non-compliant pod → Slack `#mesh-security` with namespace and pod details; injection failure rate > 1% → Slack `#mesh-ops`; namespace label removed → PagerDuty **P3** (entire namespace may lose injection); injection failure rate > 10% → PagerDuty **P2** (**webhook malfunction**).
- **Runbook** (owner: service mesh platform team): (1) for INJECTION_BYPASSED: check **pod annotations** for explicit opt-out: `kubectl get pod <pod> -n <ns> -o jsonpath='{.metadata.annotations}'`, (2) for INIT_PRESENT_SIDECAR_MISSING: check istio-proxy container status: `kubectl describe pod <pod> -n <ns> | grep -A5 istio-proxy`, (3) for webhook failures: check istiod logs: `kubectl logs -n istio-system deploy/istiod --tail=50 | grep inject`, (4) for namespace label changes: review recent kubectl/Helm operations.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **namespace compliance matrix** showing each namespace as a colored cell — green (100% compliant), amber (partially compliant), red (non-compliant) — with hover showing the count of non-compliant pods. Pair with a **timeline** showing injection events over 24 hours.
- **Alert design**: include `namespace`, `non_compliant_pods`, `affected_workloads`, `non_compliant_reason`, and `example_pods` in the compliance alert payload. For injection rate alerts include `failure_rate`, `total_requests`, and `injection_health`.
- **Multi-revision injection tracking** — when using Istio **revision-based upgrades** with the **`istio.io/rev`** label, track which namespaces are on which revision to ensure complete migration. A namespace stuck on an old revision after all istiod pods for that revision are removed will silently lose injection.
- **Per-workload compliance reporting** — aggregate non-compliant pods by **ownerReferences** (Deployment, StatefulSet, DaemonSet) to report at the workload level rather than individual pods. This provides **actionable remediation** targets for development teams.
- **All pods show as non-compliant** — the `containers` field in the pod status may not include the full container list if the pod snapshot is incomplete. Verify the raw event includes all containers: `index=containers sourcetype="kube:pod:status" pod_name="<known-injected-pod>" | table containers`.
- **Namespace lookup is empty** — the scheduled search that populates `namespace_injection_status.csv` may not be running. Check the saved search status and permissions. Alternatively, manually populate the CSV from `kubectl get ns --show-labels`.
- **False compliance** — some pods may have the `istio-proxy` container but it is in **CrashLoopBackOff** or **not ready**. The basic compliance check only verifies container presence, not health. Extend the check to include container readiness status for comprehensive validation.
- **Injection metrics show zero requests** — no pods have been created or updated recently. In a stable cluster, the injection webhook is only invoked during pod creation. Deploy a test pod to generate injection activity.

## SPL

```spl
`comment("--- Sidecar Injection Compliance — Pods Missing istio-proxy in Injection-Enabled Namespaces ---")`
index=containers sourcetype="kube:pod:status"
| eval ns=coalesce(namespace, metadata.namespace, pod_namespace)
| eval pod=coalesce(pod_name, metadata.name)
| eval containers_list=coalesce(containers, spec.containers)
| eval has_sidecar=if(match(containers_list, "istio-proxy"), 1, 0)
| eval has_init=if(match(containers_list, "istio-init") OR match(containers_list, "istio-validation"), 1, 0)
| eval owner_kind=coalesce(owner_kind, ownerReferences.kind, "standalone")
| eval owner_name=coalesce(owner_name, ownerReferences.name, pod)
| dedup ns, pod sortby -_time
| lookup namespace_injection_status.csv namespace as ns OUTPUT injection_enabled, injection_revision
| where injection_enabled="true" AND has_sidecar=0
| eval non_compliant_reason=case(
    has_init=1 AND has_sidecar=0, "INIT_PRESENT_SIDECAR_MISSING",
    match(pod, "^istio-") OR match(pod, "^istiod"), "CONTROL_PLANE_EXEMPT",
    owner_kind="DaemonSet", "DAEMONSET_EXEMPT_CHECK",
    1=1, "INJECTION_BYPASSED")
| where non_compliant_reason NOT IN ("CONTROL_PLANE_EXEMPT")
| stats count as non_compliant_pods,
    dc(owner_name) as affected_workloads,
    values(non_compliant_reason) as reasons,
    values(pod) as example_pods
    by ns
| eval compliance_pct=0
| sort -non_compliant_pods
| table ns non_compliant_pods affected_workloads reasons example_pods

`comment("--- Injection Success Rate — istiod Webhook Metrics Trend ---")`
index=containers sourcetype="otel:metrics" metric_name IN ("sidecar_injection_requests_total", "sidecar_injection_success_total", "sidecar_injection_failure_total")
| eval metric=coalesce(metric_name, _metric_name)
| bin _time span=1h
| stats sum(eval(if(metric="sidecar_injection_requests_total", metric_value, 0))) as total_requests,
    sum(eval(if(metric="sidecar_injection_success_total", metric_value, 0))) as successes,
    sum(eval(if(metric="sidecar_injection_failure_total", metric_value, 0))) as failures
    by _time
| eval success_rate=if(total_requests > 0, round(100 * successes / total_requests, 2), 100)
| eval failure_rate=if(total_requests > 0, round(100 * failures / total_requests, 2), 0)
| eval injection_health=case(
    failure_rate > 10, "CRITICAL",
    failure_rate > 1, "DEGRADED",
    1=1, "HEALTHY")
| table _time total_requests successes failures success_rate failure_rate injection_health

`comment("--- Namespace Injection Label Change Detection ---")`
index=containers sourcetype="kube:namespace:labels"
| eval ns=coalesce(namespace, metadata.name)
| eval injection_label=coalesce(mvfilter(match(labels, "istio-injection")), mvfilter(match(labels, "istio.io/rev")), "none")
| sort 0 ns, _time
| streamstats current=f last(injection_label) as prev_label by ns
| where injection_label != prev_label AND isnotnull(prev_label)
| eval change_type=case(
    prev_label="none" AND injection_label!="none", "ENABLED",
    prev_label!="none" AND injection_label="none", "DISABLED",
    1=1, "CHANGED")
| table _time ns prev_label injection_label change_type
```

## Visualization

Compliance gauge (% pods with sidecar in injection-enabled namespaces), non-compliant pod table, injection success rate trend line, namespace-level compliance heatmap, single-value tiles (non-compliant count, failure rate).

## Known False Positives

**explicit_opt_out_annotation** — Development teams may intentionally disable sidecar injection for specific pods using the `sidecar.istio.io/inject: false` annotation. This is a deliberate decision, not a compliance gap. The compliance search should cross-reference pod annotations and maintain an exemption registry to distinguish intentional opt-outs from accidental omissions.

**daemonset_host_networking** — DaemonSets that require host networking (monitoring agents, log collectors, CNI plugins) cannot run with Istio sidecars because the sidecar's iptables rules conflict with host network access. These pods will always appear as non-compliant in injection-enabled namespaces. Add DaemonSet owner_kind to the exemption list.

**job_and_cronjob_completion** — Kubernetes Jobs and CronJobs with sidecars have a known issue where the job container completes but the sidecar keeps running, preventing the pod from terminating. Some teams disable injection for jobs to avoid this. These appear as non-compliant but are a pragmatic workaround for a known Istio limitation.

**webhook_timeout_transient** — During cluster-wide pressure (node scaling, API server load, etcd compaction), the istio-sidecar-injector webhook may timeout for individual pod CREATE requests. The pod is created without a sidecar. These are transient failures that resolve when cluster pressure subsides. The injection success rate search surfaces the frequency.

**revision_label_mismatch** — When using Istio canary upgrades with revision labels, a namespace labeled with a revision that has been removed creates pods without injection because no webhook matches the revision. This appears as non-compliant but is actually a stale revision reference.

**init_container_network_policy** — In clusters with strict NetworkPolicy enforcement, the istio-init container may fail to set up iptables rules if the CNI plugin blocks the required operations. The pod starts without proper traffic interception even though istio-proxy is present. This is a partial compliance failure not caught by container-name-only checking.

## References

- [Istio — Sidecar Injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/)
- [Istio — Controlling the Injection Policy](https://istio.io/latest/docs/ops/configuration/mesh/)
- [Kubernetes — Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [Splunk Connect for Kubernetes](https://github.com/splunk/splunk-connect-for-kubernetes)
- [Splunk lookup Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Lookup)
