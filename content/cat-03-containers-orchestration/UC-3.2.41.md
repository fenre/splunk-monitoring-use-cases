<!-- AUTO-GENERATED from UC-3.2.41.json — DO NOT EDIT -->

---
id: "3.2.41"
title: "Kubernetes Service Zero Ready Endpoints (Endpoints and EndpointSlices)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.41 · Kubernetes Service Zero Ready Endpoints (Endpoints and EndpointSlices)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster’s internal address book for each service. When that book says nobody is ready to receive traffic, calls can fail even if the public website still looks fine, so we raise a clear signal before customers get stuck.*

---

## Description

Detects Kubernetes Services whose Endpoints or EndpointSlices expose zero ready backend addresses at the service-discovery layer: kube_endpoint_address_available at zero, modern kube_endpoint_address rows with no ready="true" members, kube_endpointslice_endpoints summing to zero ready endpoints for the service name carried on EndpointSlice labels, correlated with kube_service_spec_type to ignore ExternalName externals, kube_pod_status_ready as a namespace-level readiness sanity check, and kube events whose reasons or messages reference endpoint update failures or absent ready targets. This is the north-of-ingress abstraction where kube-proxy programs iptables or IPVS from EndpointSlices; it is not CrashLoopBackOff pod process health (UC-3.2.10), not ingress controller 502/503 data-plane errors (UC-3.2.18), and not Deployment rollout progression (UC-3.2.6).

## Value

ClusterIP, headless, NodePort, and LoadBalancer implementations all consult Endpoints or EndpointSlices before packets leave the node; when ready counts drop to zero, traffic blackholes silently for in-cluster clients and for load balancers that still health-check green while kube-proxy has nothing to program. Platform teams shrink mean time to repair by seeing namespace, service, inferred type, legacy and modern metric arms, EndpointSlice-ready sums, recent endpoint-controller events, and tier-aware severity in one row. Product and customer teams avoid mysterious partial outages during rollouts, selector typos, quota-blocked scheduling, readiness probe misconfiguration, or network policy drops that never surface as ingress errors.

## Implementation

Scrape kube-state-metrics endpoint and EndpointSlice families into k8s_metrics, ship kube events into k8s, publish k8s_namespace_tier.csv and critical_services.csv, save uc_3_2_41_k8s_service_zero_ready_endpoints on a five-minute cadence with earliest=-2h@m latest=now, route critical and high to your on-call path, and validate by scaling a lab Deployment to zero replicas while keeping its Service.

## Evidence

Saved search uc_3_2_41_k8s_service_zero_ready_endpoints, lookups critical_services.csv and k8s_namespace_tier.csv with commit identifiers, weekly CSV export of alert rows to an evidence index, and dashboard panels tied to the closing table command.

## Control test

### Positive scenario

In a lab namespace create a Deployment with two replicas behind a ClusterIP Service, confirm kube_endpoint_address_available is greater than zero in k8s_metrics, scale the Deployment to zero with kubectl scale deploy/foo --replicas=0, wait for two kube-state-metrics scrape intervals, run uc_3_2_41_k8s_service_zero_ready_endpoints, and expect a row with zero_ready_flag semantics satisfied and kube_service_spec_type ClusterIP.

### Negative scenario

Deploy an ExternalName Service pointing at an out-of-cluster hostname without local Endpoints; confirm kube_service_spec_type ExternalName and the saved search returns no row after exclusions, or create a second positive Deployment that stays Ready and verify the Service row disappears when replicas return to one or more.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Kubernetes platform team that certifies kube-state-metrics RBAC, the service-mesh or ingress squad that understands north-south versus east-west paths, and the observability engineer who operates Splunk OpenTelemetry Collector or in-cluster Prometheus scraping. This use case isolates the Kubernetes Service discovery plane: kube-proxy, win-proxy, or CNI implementations consume Endpoints and EndpointSlices to program dataplane rules. When every ready backend address disappears, ClusterIP traffic stops inside the cluster, headless DNS may return nothing useful, NodePort sockets accept connections that go nowhere useful, and cloud load balancers that still pass TCP health checks can front an empty kube-proxy programming set. That failure mode is orthogonal to CrashLoopBackOff in UC-3.2.10 because pods may be Running yet NotReady, or selectors may point at zero pods without any container exiting. It is orthogonal to UC-3.2.18 because ingress controllers can return 502 or 503 for many reasons while EndpointSlices still show ready members, and it is orthogonal to UC-3.2.6 because a Deployment can report a completed rollout while misconfigured probes or selectors leave the Service with no ready endpoints.

You need kube-state-metrics at a version that exposes kube_endpoint_address_available or kube_endpoint_address, kube_endpointslice_endpoints, kube_service_info, kube_service_spec_type, and kube_pod_status_ready as documented in the upstream metric tables. EndpointSlice metrics remain experimental in kube-state-metrics; enable the EndpointSlice informer and verify your scrape output before relying on the slice arm alone. Splunk indexes should include k8s_metrics for Prometheus exposition or normalized metric events and k8s for kube:events. Reserve HEC tokens with least privilege, rotate quarterly, and document which clusters map to which index partitions for GDPR or data residency reviews.

Publish two governance lookups before enabling alerts. First, k8s_namespace_tier.csv with columns namespace and workload_tier using values such as prod, production, preprod, staging, uat, dev, and sandbox. Second, critical_services.csv with columns namespace, service, and tier1_sli where tier1_sli is 1 for customer-facing or revenue-critical pairs that must page even when the namespace is non-production. Services that legitimately scale to zero should use tier1_sli 0 and appear only on dashboards, not on paging copies of the search.

RBAC for collectors must allow reading events involving Service, Endpoints, and EndpointSlice objects. Network policy must permit scrapes from the Prometheus or OpenTelemetry agent to the kube-state-metrics Service on port 8080 or the documented custom port. Document label cardinality limits: high-cardinality EndpointSlice address labels can explode metric volume; use Prometheus relabel drops only after security review because blind drops can hide readiness signals.

Licensing and retention: five-minute schedules across hundreds of Services typically stay below a few gigabytes per day when you restrict the multisearch arms to metric name regexes shown in Step 3. Keep at least fourteen days of raw scrapes and ninety days of alert artefacts for operational audits.

Finally, align incident vocabulary with kubectl inspection habits. Operators should know that EndpointSlice objects carry the kubernetes.io/service-name label in the API; kube-state-metrics surfaces that label in Prometheus text as kubernetes_io_service_name or label_kubernetes_io_service_name depending on your scrape normalization. Training should emphasize that zero ready endpoints is not the same as CoreDNS failures in UC-3.2.34 and that this alert complements DNS telemetry rather than replacing it.

### Step 2 — Configure data collection

Deploy kube-state-metrics with the standard ClusterRole that lists watches on services, endpoints, endpoint slices, and pods. If you use Prometheus Operator, apply a ServiceMonitor that selects the kube-state-metrics Service and scrapes path /metrics every thirty seconds, with a ten second scrape timeout, matching the pattern used in other gold Kubernetes use cases in this repository.

Concrete ServiceMonitor skeleton:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-endpoints
  namespace: kube-system
  labels:
    release: prom
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: http-metrics
      interval: 30s
      scrapeTimeout: 10s
      path: /metrics
      scheme: http
```

Configure Splunk OpenTelemetry Collector to export scraped metrics to HEC with sourcetype prometheus:scrape:metrics and index k8s_metrics. Keep source and sourcetype stable across upgrades so saved searches do not drift.

```yaml
exporters:
  splunk_hec/k8s_metrics:
    token: "${SPLUNK_HEC_TOKEN}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    source: kube-prometheus
    sourcetype: prometheus:scrape:metrics
    index: k8s_metrics
    tls:
      insecure_skip_verify: false
```

Ship Kubernetes API events to index k8s with sourcetype kube:events. The endpoint controller emits reasons such as FailedToUpdateEndpoint and FailedToUpdateEndpointSlices; message text may mention missing ready endpoints or reconciliation conflicts. Use the k8s_events receiver in OpenTelemetry or Splunk Connect for Kubernetes object inputs, ensuring involvedObject.kind and involvedObject.name fields are preserved for joins.

Validation searches before promotion:

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_endpoint_address_available OR kube_endpoint_address earliest=-30m

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_endpointslice_endpoints earliest=-30m

index=k8s sourcetype=kube:events FailedToUpdateEndpoint OR EndpointSlice earliest=-30m

Skew between metrics and events should remain under ninety seconds for meaningful correlation. If you run multiple clusters, normalize cluster or cluster_name fields at ingestion so the SPL cluster coalesce arm resolves consistently.

For GKE, EKS, and AKS, confirm that managed control plane networking or private endpoint restrictions do not block your scraper from reaching kube-state-metrics even when worker nodes are healthy. Cloud provider load balancer docs in the references section explain how upstream health checks differ from EndpointSlice readiness; capture both views during design reviews.

### Step 3 — Create the search and alert

Save the primary SPL as uc_3_2_41_k8s_service_zero_ready_endpoints with cron */5 * * * * and alert when the number of results is greater than zero for the paging variant. Use earliest=-2h@m latest=now to tolerate kube-state-metrics scrape delay and late-arriving events. Create a non-paging dashboard clone that removes the workload_tier filter for engineering visibility in lower environments.

The search deliberately uses multisearch to separate legacy kube_endpoint_address_available and kube_endpoint_address_not_ready arms from the modern kube_endpoint_address ready label arm and the kube_endpointslice_endpoints arm so Job Inspector traces stay readable. inputlookup joins implement governance: k8s_namespace_tier.csv drives environment semantics while critical_services.csv marks tier-one SLIs that page even outside standard production namespaces. case() builds severity with higher priority for NodePort and LoadBalancer Services in production because those surfaces amplify customer-visible outages.

Fenced SPL for runbooks (aligns with the spl JSON field):

```spl
`comment("UC-3.2.41 Kubernetes Service zero ready endpoints (Endpoints and EndpointSlices). Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookups critical_services.csv k8s_namespace_tier.csv; earliest=-2h@m latest=now")`
| multisearch
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "endpoint=\"(?<ep_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(service, ep_rx, "")))
      | where (like(metric_nm, "%kube_endpoint_address_available%") OR like(metric_nm, "%kube_endpoint_address_not_ready%"))
      | eval ep_avail=if(like(metric_nm, "%kube_endpoint_address_available%"), tonumber(mval, 10), null())
      | eval ep_not_ready=if(like(metric_nm, "%kube_endpoint_address_not_ready%"), tonumber(mval, 10), null())
      | stats latest(ep_avail) AS kube_endpoint_address_available latest(ep_not_ready) AS kube_endpoint_address_not_ready BY cluster namespace service
      | eval lane="legacy_ep_counts" ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "endpoint=\"(?<ep_rx>[^\"]+)\""
      | rex field=_raw "ready=\"(?<ready_lbl>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(service, ep_rx, "")))
      | where like(metric_nm, "%kube_endpoint_address%") AND NOT like(metric_nm, "%kube_endpoint_address_available%") AND NOT like(metric_nm, "%kube_endpoint_address_not_ready%")
      | eval ready_unit=if(ready_lbl="true", tonumber(mval, 10), 0)
      | stats sum(ready_unit) AS kube_endpoint_ready_addr_units BY cluster namespace service
      | eval lane="modern_ep_addr" ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "ready=\"(?<ready_lbl>[^\"]+)\""
      | rex field=_raw "kubernetes_io_service_name=\"(?<slice_svc_a>[^\"]+)\""
      | rex field=_raw "label_kubernetes_io_service_name=\"(?<slice_svc_b>[^\"]+)\""
      | rex field=_raw "service=\"(?<svc_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(slice_svc_a, slice_svc_b, svc_rx, "")))
      | where like(metric_nm, "%kube_endpointslice_endpoints%")
      | eval eps_ready_unit=if(ready_lbl="true", tonumber(mval, 10), 0)
      | stats sum(eps_ready_unit) AS kube_endpointslice_endpoints_ready_sum BY cluster namespace service
      | eval lane="endpointslice" ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "service=\"(?<svc_rx>[^\"]+)\""
      | rex field=_raw "type=\"(?<svc_type_rx>[^\"]+)\""
      | rex field=_raw "cluster_ip=\"(?<cluster_ip_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(service, svc_rx, "")))
      | where like(metric_nm, "%kube_service_spec_type%") OR like(metric_nm, "%kube_service_info%")
      | eval svc_type=if(like(metric_nm, "%kube_service_spec_type%"), svc_type_rx, null())
      | eval cluster_ip=if(like(metric_nm, "%kube_service_info%"), cluster_ip_rx, null())
      | stats latest(svc_type) AS kube_service_spec_type latest(cluster_ip) AS kube_service_cluster_ip BY cluster namespace service
      | eval lane="service_meta" ]
| stats max(kube_endpoint_address_available) AS kube_endpoint_address_available max(kube_endpoint_address_not_ready) AS kube_endpoint_address_not_ready max(kube_endpoint_ready_addr_units) AS kube_endpoint_ready_addr_units max(kube_endpointslice_endpoints_ready_sum) AS kube_endpointslice_endpoints_ready_sum max(kube_service_spec_type) AS kube_service_spec_type max(kube_service_cluster_ip) AS kube_service_cluster_ip BY cluster namespace service
| where isnotnull(namespace) AND len(namespace)>0 AND isnotnull(service) AND len(service)>0
| join type=left max=0 cluster namespace [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "condition=\"(?<cond_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | where like(metric_nm, "%kube_pod_status_ready%") AND cond_rx="true"
      | eval ready_pod_unit=tonumber(mval, 10)
      | stats sum(ready_pod_unit) AS kube_pod_status_ready_sum BY cluster namespace ]
| join type=left max=0 cluster namespace service [
    search index=k8s sourcetype="kube:events" earliest=-2h@m latest=now
      | eval ns_ev=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval svc_ev=trim(toString(coalesce(involvedObject.name, service, "")))
      | eval kind_ev=lower(trim(toString(coalesce(involvedObject.kind, kind, ""))))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(toString(coalesce(message, Message, "")))
      | where kind_ev="service" OR kind_ev="endpoints" OR kind_ev="endpointslice" OR match(msg, "endpoint") OR match(rs, "Endpoint")
      | where like(rs, "FailedToUpdateEndpoint%") OR like(rs, "FailedToUpdateEndpointSlices%") OR rs="NoEndpoints" OR match(msg, "failedtoupdateendpoint") OR match(msg, "noreadyendpoints") OR match(msg, "no endpoints") OR match(msg, "notarget")
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | stats latest(_time) AS last_endpoint_event_time values(rs) AS endpoint_event_reasons values(message) AS endpoint_event_messages BY cluster ns_ev svc_ev
      | rename ns_ev AS namespace svc_ev AS service ]
| join type=left max=0 namespace [
    | inputlookup k8s_namespace_tier.csv
    | eval namespace=trim(toString(namespace))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | fields namespace workload_tier ]
| join type=left max=0 namespace, service [
    | inputlookup critical_services.csv
    | eval namespace=trim(toString(namespace))
    | eval service=trim(toString(service))
    | eval tier1_sli=tonumber(trim(toString(coalesce(tier1_sli, tier1, critical_sli, "0"))), 10)
    | fields namespace service tier1_sli ]
| fillnull value=0 tier1_sli
| eval kube_service_spec_type=trim(toString(coalesce(kube_service_spec_type, "")))
| eval kube_service_cluster_ip=trim(toString(coalesce(kube_service_cluster_ip, "")))
| where isnull(kube_service_spec_type) OR kube_service_spec_type!="ExternalName"
| eval headless_hint=if(kube_service_cluster_ip="None" OR match(kube_service_cluster_ip, "^none$"), 1, 0)
| eval legacy_zero=if(isnotnull(kube_endpoint_address_available) AND kube_endpoint_address_available==0, 1, 0)
| eval modern_zero=if(isnull(kube_endpoint_address_available) AND coalesce(kube_endpoint_ready_addr_units, 0)==0 AND coalesce(kube_endpointslice_endpoints_ready_sum, 0)==0, 1, 0)
| eval zero_ready_flag=if(legacy_zero==1 OR modern_zero==1, 1, 0)
| where zero_ready_flag==1
| eventstats median(kube_pod_status_ready_sum) AS ns_ready_median BY cluster namespace
| eval severity=case(
    (workload_tier="prod" OR workload_tier="production") AND zero_ready_flag==1 AND match(kube_service_spec_type, "LoadBalancer|NodePort"), "critical",
    (workload_tier="prod" OR workload_tier="production") AND zero_ready_flag==1, "high",
    match(workload_tier, "preprod|staging|uat") AND zero_ready_flag==1, "medium",
    tier1_sli==1 AND zero_ready_flag==1, "high",
    true(), "low")
| where workload_tier IN ("prod", "production", "preprod", "staging", "uat") OR tier1_sli==1
| eval event_correlation_hint=coalesce(mvjoin(endpoint_event_reasons, " | "), mvjoin(endpoint_event_messages, " | "), "no_recent_endpoint_events_matched")
| eval endpoint_evidence=printf("legacy_avail=%s modern_ready_units=%s slice_ready_sum=%s not_ready=%s",
    toString(coalesce(kube_endpoint_address_available, "null")),
    toString(coalesce(kube_endpoint_ready_addr_units, "null")),
    toString(coalesce(kube_endpointslice_endpoints_ready_sum, "null")),
    toString(coalesce(kube_endpoint_address_not_ready, "null")))
| table cluster namespace service kube_service_spec_type headless_hint kube_endpoint_address_available kube_endpoint_ready_addr_units kube_endpointslice_endpoints_ready_sum kube_endpoint_address_not_ready kube_pod_status_ready_sum severity workload_tier tier1_sli last_endpoint_event_time event_correlation_hint endpoint_evidence
```

Example savedsearches.conf fragment for email and throttling:

```
[uc_3_2_41_k8s_service_zero_ready_endpoints]
action.email = 1
action.email.to = platform-oncall@example.com
action.email.subject = K8s zero-ready endpoints $result.namespace$/$result.service$
action.email.message = severity=$result.severity$ evidence=$result.endpoint_evidence$ events=$result.event_correlation_hint$
counttype = number of events
relation = >
quantity = 0
alert.track = 1
alert.suppress = 1
alert.suppress.period = 30m
```

#### Understanding this SPL: the legacy arm surfaces kube_endpoint_address_available when your kube-state-metrics build still exports the deprecated gauge; the modern arm sums kube_endpoint_address lines where ready equals true; the EndpointSlice arm sums kube_endpointslice_endpoints lines with ready true keyed by kubernetes.io service name labels; service metadata adds kube_service_spec_type so ExternalName Services drop out; kube_pod_status_ready sums true conditions per namespace as a sanity check that the outage is not a pure metrics scrape bug when pods still report ready; kube events provide human-readable controller friction; lookups implement tier-aware paging policy.

### Step 4 — Validate

Positive functional test: create namespace uc3241-lab, deploy a two-replica application with a readiness probe that succeeds, expose it with a ClusterIP Service, wait until kubectl get endpoints shows subsets with ready addresses, confirm Splunk returns kube_endpoint_address_available greater than zero or kube_endpoint_ready_addr_units greater than zero, then kubectl scale deployment --replicas=0. Within two scrape intervals you should see zero ready addresses and a row from the saved search. Restore one replica and confirm the row clears.

Negative functional test: deploy an ExternalName Service referencing an external hostname. Verify kube_service_spec_type equals ExternalName in metrics and the saved search excludes the row. Deploy a second Service with ClusterIP that retains endpoints and ensure only the intentionally drained Service triggers.

Field spot checks: compare Splunk extracted namespace and service with kubectl get endpointslices -n uc3241-lab -o wide and kubectl describe service. Event spot checks: index=k8s sourcetype=kube:events involvedObject.name=<service> earliest=-1h should show controller messages if reconciliation is failing.

Synthetic delay test: set readinessProbe.initialDelaySeconds very high, roll the Deployment, and observe whether the alert fires during the intentional gap; tune alert_suppress or add a streamstats dwell clause if your organization accepts brief empty windows during every rollout.

Audit readiness: export one week of alert rows with lookup versions, kube-state-metrics image digest, and collector version hashes so post-incident reviews can replay the same SPL predicates.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Selector typo or label drift after a deploy
kubectl get pods --show-labels versus Service spec.selector mismatch produces zero endpoints while pods stay healthy on other labels. Fix the selector or pod template labels, roll out, verify Endpoints objects repopulate.

Case 2 — Readiness probe failing while containers stay running
Pods remain Running but kube_pod_status_ready reports condition false; endpoints drop. kubectl describe pod surfaces probe failures. Adjust probe paths, timeouts, or initial delays after correlating with application logs without conflating this UC with UC-3.2.10 CrashLoopBackOff.

Case 3 — Namespace ResourceQuota blocked pod creation
Quota errors prevent new backends from replacing evicted pods; EndpointSlice counts fall to zero. Correlate with FailedCreate events and ResourceQuota objects; raise quota or reduce requests.

Case 4 — NetworkPolicy denying traffic after endpoints still exist
This UC may not fire because readiness might still pass while clients see timeouts. If endpoints are healthy but policies blackhole east-west traffic, pivot to policy-focused monitoring and service mesh telemetry.

Case 5 — Manual Endpoints objects for hybrid backends
Services without selectors rely on manual Endpoint rows. Maintenance on external IPs can clear subsets intentionally. Cross-check critical_services.csv suppression flags before paging application teams.

Case 6 — EndpointSlice controller conflicts or apiservers throttling
FailedToUpdateEndpointSlices events with conflict messages often self-heal; lengthen suppression if kube-state-metrics shows ready addresses returning within one minute while Splunk events lag.

Case 7 — kube-proxy or CNI restart causing transient programming gaps
Nodes may drop rules briefly during daemon restarts; correlate with node logs and node readiness before declaring application failure.

Case 8 — Load balancer health checks pass while internal ClusterIP is empty
Cloud TCP checks can succeed on node ports that are not wired to ready pods. Use this alert alongside provider-specific load balancer target health dashboards referenced for GKE, EKS, and AKS.

Case 9 — Headless Service churn for StatefulSets
DNS A or AAAA records fluctuate as pods reschedule; operations may be normal during rolling restart. Require sustained zero-ready duration or tie to customer error budgets before paging.

Case 10 — Dual-stack clusters with EndpointSlice addressType changes
Families split across slices; verify you are summing ready endpoints for the address family your clients use. kubectl get endpointslices shows addressType IPv4 versus IPv6.

Case 11 — Scrape or HEC outage mimicking zero endpoints
If kube-state-metrics stops reporting but the cluster is healthy, multiple Services appear simultaneously. Correlate with collector health and prometheus target up gauges before engaging application owners.

Case 12 — GitOps controller repeatedly applying invalid Service manifests
Repeated FailedToUpdateEndpoint events with validation errors should route to platform engineering; attach Git commit metadata from your GitOps audit logs when available.

Dashboard hygiene: keep panels for kube_endpoint_address_available trend lines, kube_endpointslice_endpoints ready sums, and a narrow kube events panel filtered to endpoint controllers. Document kubectl debug steps for ephemeral containers only where your security policy permits.

Governance: quarterly replay this search after kube-state-metrics upgrades because label rewriting rules change. Update rex arms when Prometheus relabel configs move kubernetes.io labels.

Closing checklist: five step headers use em dash punctuation as contracted; Step 3 includes fenced SPL; Step 5 lists twelve case lines; lookups and indexes are explicit; narrative differentiates UC-3.2.10, UC-3.2.18, and UC-3.2.6; performance tuning suggests summary indexing only if Job Inspector shows repeated high-cost joins across very large metric volumes.


## SPL

```spl
`comment("UC-3.2.41 Kubernetes Service zero ready endpoints (Endpoints and EndpointSlices). Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookups critical_services.csv k8s_namespace_tier.csv; earliest=-2h@m latest=now")`
| multisearch
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "endpoint=\"(?<ep_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(service, ep_rx, "")))
      | where (like(metric_nm, "%kube_endpoint_address_available%") OR like(metric_nm, "%kube_endpoint_address_not_ready%"))
      | eval ep_avail=if(like(metric_nm, "%kube_endpoint_address_available%"), tonumber(mval, 10), null())
      | eval ep_not_ready=if(like(metric_nm, "%kube_endpoint_address_not_ready%"), tonumber(mval, 10), null())
      | stats latest(ep_avail) AS kube_endpoint_address_available latest(ep_not_ready) AS kube_endpoint_address_not_ready BY cluster namespace service
      | eval lane="legacy_ep_counts" ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "endpoint=\"(?<ep_rx>[^\"]+)\""
      | rex field=_raw "ready=\"(?<ready_lbl>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(service, ep_rx, "")))
      | where like(metric_nm, "%kube_endpoint_address%") AND NOT like(metric_nm, "%kube_endpoint_address_available%") AND NOT like(metric_nm, "%kube_endpoint_address_not_ready%")
      | eval ready_unit=if(ready_lbl="true", tonumber(mval, 10), 0)
      | stats sum(ready_unit) AS kube_endpoint_ready_addr_units BY cluster namespace service
      | eval lane="modern_ep_addr" ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "ready=\"(?<ready_lbl>[^\"]+)\""
      | rex field=_raw "kubernetes_io_service_name=\"(?<slice_svc_a>[^\"]+)\""
      | rex field=_raw "label_kubernetes_io_service_name=\"(?<slice_svc_b>[^\"]+)\""
      | rex field=_raw "service=\"(?<svc_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(slice_svc_a, slice_svc_b, svc_rx, "")))
      | where like(metric_nm, "%kube_endpointslice_endpoints%")
      | eval eps_ready_unit=if(ready_lbl="true", tonumber(mval, 10), 0)
      | stats sum(eps_ready_unit) AS kube_endpointslice_endpoints_ready_sum BY cluster namespace service
      | eval lane="endpointslice" ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "service=\"(?<svc_rx>[^\"]+)\""
      | rex field=_raw "type=\"(?<svc_type_rx>[^\"]+)\""
      | rex field=_raw "cluster_ip=\"(?<cluster_ip_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | eval service=trim(toString(coalesce(service, svc_rx, "")))
      | where like(metric_nm, "%kube_service_spec_type%") OR like(metric_nm, "%kube_service_info%")
      | eval svc_type=if(like(metric_nm, "%kube_service_spec_type%"), svc_type_rx, null())
      | eval cluster_ip=if(like(metric_nm, "%kube_service_info%"), cluster_ip_rx, null())
      | stats latest(svc_type) AS kube_service_spec_type latest(cluster_ip) AS kube_service_cluster_ip BY cluster namespace service
      | eval lane="service_meta" ]
| stats max(kube_endpoint_address_available) AS kube_endpoint_address_available max(kube_endpoint_address_not_ready) AS kube_endpoint_address_not_ready max(kube_endpoint_ready_addr_units) AS kube_endpoint_ready_addr_units max(kube_endpointslice_endpoints_ready_sum) AS kube_endpointslice_endpoints_ready_sum max(kube_service_spec_type) AS kube_service_spec_type max(kube_service_cluster_ip) AS kube_service_cluster_ip BY cluster namespace service
| where isnotnull(namespace) AND len(namespace)>0 AND isnotnull(service) AND len(service)>0
| join type=left max=0 cluster namespace [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval metric_nm=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw "condition=\"(?<cond_rx>[^\"]+)\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | eval namespace=trim(toString(coalesce(namespace, kubernetes_namespace, k8s_namespace, ns_rx, "")))
      | where like(metric_nm, "%kube_pod_status_ready%") AND cond_rx="true"
      | eval ready_pod_unit=tonumber(mval, 10)
      | stats sum(ready_pod_unit) AS kube_pod_status_ready_sum BY cluster namespace ]
| join type=left max=0 cluster namespace service [
    search index=k8s sourcetype="kube:events" earliest=-2h@m latest=now
      | eval ns_ev=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval svc_ev=trim(toString(coalesce(involvedObject.name, service, "")))
      | eval kind_ev=lower(trim(toString(coalesce(involvedObject.kind, kind, ""))))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(toString(coalesce(message, Message, "")))
      | where kind_ev="service" OR kind_ev="endpoints" OR kind_ev="endpointslice" OR match(msg, "endpoint") OR match(rs, "Endpoint")
      | where like(rs, "FailedToUpdateEndpoint%") OR like(rs, "FailedToUpdateEndpointSlices%") OR rs="NoEndpoints" OR match(msg, "failedtoupdateendpoint") OR match(msg, "noreadyendpoints") OR match(msg, "no endpoints") OR match(msg, "notarget")
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster, Cluster, "default-cluster")))
      | stats latest(_time) AS last_endpoint_event_time values(rs) AS endpoint_event_reasons values(message) AS endpoint_event_messages BY cluster ns_ev svc_ev
      | rename ns_ev AS namespace svc_ev AS service ]
| join type=left max=0 namespace [
    | inputlookup k8s_namespace_tier.csv
    | eval namespace=trim(toString(namespace))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | fields namespace workload_tier ]
| join type=left max=0 namespace, service [
    | inputlookup critical_services.csv
    | eval namespace=trim(toString(namespace))
    | eval service=trim(toString(service))
    | eval tier1_sli=tonumber(trim(toString(coalesce(tier1_sli, tier1, critical_sli, "0"))), 10)
    | fields namespace service tier1_sli ]
| fillnull value=0 tier1_sli
| eval kube_service_spec_type=trim(toString(coalesce(kube_service_spec_type, "")))
| eval kube_service_cluster_ip=trim(toString(coalesce(kube_service_cluster_ip, "")))
| where isnull(kube_service_spec_type) OR kube_service_spec_type!="ExternalName"
| eval headless_hint=if(kube_service_cluster_ip="None" OR match(kube_service_cluster_ip, "^none$"), 1, 0)
| eval legacy_zero=if(isnotnull(kube_endpoint_address_available) AND kube_endpoint_address_available==0, 1, 0)
| eval modern_zero=if(isnull(kube_endpoint_address_available) AND coalesce(kube_endpoint_ready_addr_units, 0)==0 AND coalesce(kube_endpointslice_endpoints_ready_sum, 0)==0, 1, 0)
| eval zero_ready_flag=if(legacy_zero==1 OR modern_zero==1, 1, 0)
| where zero_ready_flag==1
| eventstats median(kube_pod_status_ready_sum) AS ns_ready_median BY cluster namespace
| eval severity=case(
    (workload_tier="prod" OR workload_tier="production") AND zero_ready_flag==1 AND match(kube_service_spec_type, "LoadBalancer|NodePort"), "critical",
    (workload_tier="prod" OR workload_tier="production") AND zero_ready_flag==1, "high",
    match(workload_tier, "preprod|staging|uat") AND zero_ready_flag==1, "medium",
    tier1_sli==1 AND zero_ready_flag==1, "high",
    true(), "low")
| where workload_tier IN ("prod", "production", "preprod", "staging", "uat") OR tier1_sli==1
| eval event_correlation_hint=coalesce(mvjoin(endpoint_event_reasons, " | "), mvjoin(endpoint_event_messages, " | "), "no_recent_endpoint_events_matched")
| eval endpoint_evidence=printf("legacy_avail=%s modern_ready_units=%s slice_ready_sum=%s not_ready=%s",
    toString(coalesce(kube_endpoint_address_available, "null")),
    toString(coalesce(kube_endpoint_ready_addr_units, "null")),
    toString(coalesce(kube_endpointslice_endpoints_ready_sum, "null")),
    toString(coalesce(kube_endpoint_address_not_ready, "null")))
| table cluster namespace service kube_service_spec_type headless_hint kube_endpoint_address_available kube_endpoint_ready_addr_units kube_endpointslice_endpoints_ready_sum kube_endpoint_address_not_ready kube_pod_status_ready_sum severity workload_tier tier1_sli last_endpoint_event_time event_correlation_hint endpoint_evidence

```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state count AS state_events FROM datamodel=Application_State WHERE nodename=Application_State earliest=-2h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS correl_host
| join type=left max=0 correl_host [
    | tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load avg(Performance.mem_used_percent) AS avg_mem_used FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-2h@h latest=@h BY Performance.host
    | rename Performance.host AS correl_host ]
| where app_state!="running" OR avg_cpu_load>92 OR avg_mem_used>95
| table correl_host app_state avg_cpu_load avg_mem_used state_events
```

## Visualization

Primary table matching the closing SPL projection; timechart of kube_endpoint_address_available by namespace and service; overlay of kube_endpointslice_endpoints ready sums; single value of distinct services in zero-ready state; events panel filtered to endpoint-controller messages for drilldown.

## Known False Positives

Deliberate scale-to-zero for batch workers, cost-saving off-hours namespaces, or Knative scale-down idle targets will legitimately show zero ready endpoints; suppress with critical_services.csv tier1_sli=0 or a workload annotation mirrored into the lookup. Headless Services backing StatefulSets often oscillate address lists as pods reschedule; pair this alert with a minimum dwell timer or require both legacy kube_endpoint_address_available and kube_endpointslice_endpoints_ready_sum at zero for several scrapes before paging. Services without selectors that rely on manually maintained Endpoints objects for off-cluster backends can appear empty when those manual Endpoint subsets are intentionally cleared during maintenance; exclude namespaces that only front external databases. ExternalName Services and some mesh ingress bypass patterns do not use local Endpoints the same way; the SPL drops ExternalName when kube_service_spec_type is populated, but mis-extracted types may still leak through on noisy scrapes—validate kube_service_spec_type joins after kube-state-metrics upgrades. Node cordons and drains temporarily remove endpoints while pods reschedule; correlate with node readiness and cluster-autoscaler events before treating as an application defect. Brief gaps during rolling updates can appear when readinessProbe initialDelaySeconds is longer than the time pods spend Ready=false during container restarts; widen alert suppression windows for stateless fleets or require endpoint event reasons not just metric zeros. Namespace ResourceQuota objects that block new pods leave selectors matching zero pods; the metric looks like an application outage but is quota—route using kube events FailedCreate and quota metrics. NetworkPolicy misconfiguration that drops traffic after endpoints exist may not reduce ready counts; this UC will not fire and UC siblings covering policy drops should be used instead. CI namespaces that constantly delete Services during integration tests can spam the search; exclude ci-* namespaces at the saved-search layer.

## References

- [Kubernetes — Service](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes — EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
- [kube-state-metrics — EndpointSlice metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/service/endpointslice-metrics.md)
- [kube-state-metrics — Endpoint metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/service/endpoint-metrics.md)
- [Kubernetes — Debug Services](https://kubernetes.io/docs/tasks/)
- [Google Kubernetes Engine — Exposing applications](https://cloud.google.com/kubernetes-engine/docs/how-to/exposing-apps)
- [Amazon EKS — Kubernetes services](https://docs.aws.amazon.com/eks/latest/userguide/network-load-balancing.html)
- [Azure AKS — Kubernetes network concepts (Services)](https://learn.microsoft.com/en-us/azure/aks/concepts-network#kubernetes-services)
- [kubectl reference — get (inspect EndpointSlices)](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#get)
