<!-- AUTO-GENERATED from UC-3.3.9.json — DO NOT EDIT -->

---
id: "3.3.9"
title: "OpenShift Router HAProxy Backend Saturation, Connection Pool Exhaustion, and 5xx Spike Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.9 · OpenShift Router HAProxy Backend Saturation, Connection Pool Exhaustion, and 5xx Spike Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the front door load balancer that ships with OpenShift—the one that carries customer web traffic into your apps. When that door is overwhelmed, connections pile up or errors spike, and we raise a clear signal so teams fix the shared edge before many apps suffer at once.*

---

## Description

Detects data-plane saturation and error bursts on the OpenShift platform IngressController operand: HAProxy-backed router-default Pods in openshift-ingress that terminate Route objects and expose Prometheus metrics on port 1936. The analytic correlates frontend session pressure against HAProxy maxconn semantics, backend queue depth and session ceilings on server lines, rising haproxy_backend_response_errors_total and haproxy_backend_http_responses_total for 5xx classes, per-route labeled server response counters when exporters preserve route labels, listener and frontend dropped connection counters, process memory around reload-heavy windows, IngressController status generation drift versus observedGeneration, and complementary router Pod CPU saturation because each HAProxy worker is effectively single-threaded for hot paths. UC-3.2.9 remains generic Kubernetes Ingress controller error analytics without openshift-ingress HAProxy semantics. UC-3.2.18 remains namespace-scoped ingress 5xx narratives that do not require haproxy_backend_* series from router-default scrapes. UC-3.3.8 remains Route TLS certificate expiry and edge trust governance, not runtime queue and session economics. UC-3.3.6 remains ClusterOperator condition reconciliation, not per-router Pod saturation.

## Value

Customer traffic reaches applications through the platform-owned router layer before any in-cluster microservice sees a socket. When HAProxy frontends hug maxconn, backends pile into queues, or 5xx counters climb by route label, executive stakeholders need evidence that the failure mode is the shared edge rather than a single Deployment misconfiguration buried inside a namespace dashboard. Splunk preserves a cross-signal ledger that ties Prometheus gauge and counter math to IngressController CR status, audit trails of route storms that force reloads, and Kubernetes events that admit or reject Routes so platform leaders shorten mean time to innocence during regional incidents. Capacity planners also receive defensible charts linking router Pod CPU ceilings to connection concurrency because horizontal scale-out of router shards only helps when publishing strategy and shard placement keep pace with aggregate SYN load.

## Implementation

Land ocp_haproxy_metrics and ocp_router_metrics from user-workload or platform Prometheus federation into index=ocp_metrics or index=ocp_router with metric_name and dimension fields normalized; land ocp_ingresscontroller snapshots for IngressController status; forward ocp_events and ocp_audit with cluster labels. Save openshift_uc_3_3_9_router_haproxy_saturation on a five-minute cadence over earliest=-2h@h; route page and warn to platform ingress on-call; throttle duplicate cluster and shard rows for twenty minutes unless severity escalates.

## Evidence

Saved search openshift_uc_3_3_9_router_haproxy_saturation with five or fifteen minute schedule; dashboard drilldowns on mstats-backed HAProxy metrics, ocp_ingresscontroller snapshots, ocp_events reload messages, and ocp_audit ingress mutations; alert stanza with platform ingress routing keys; weekly CSV exports to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift cluster, enable router scrapes on port 1936, generate sustained load against a canary Route while temporarily lowering IngressController maxConnections under change control, ingest mstats series showing rising fe_sat_ratio and bk_queue_max with nonzero xx5_delta, add ocp_events rows citing reload activity, execute openshift_uc_3_3_9_router_haproxy_saturation, and expect page or warn severity with non-null recommended_action within two five-minute windows.

### Negative scenario

Remove load, restore maxConnections to standard values, confirm router Pods are ready and HAProxy gauges return to baseline with xx5_window near zero for thirty minutes, and verify the alert wrapper filtered to page and warn emits zero qualifying rows while synthetic route checks stay green.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift networking and ingress engineering lead, the observability staff who operate Splunk HTTP Event Collector tokens and OpenTelemetry Collector agents that federate user-workload monitoring scrapes, and the site reliability engineers who operate external DNS and load balancer publishing for OpenShift clusters. This use case isolates the IngressController custom resource in group operator.openshift.io and its operand Deployment in namespace openshift-ingress, commonly named router-default for the default shard, backed by HAProxy and the template-router control process that reconciles Route objects into a running configuration. Every admitted Route can force a configuration reload; high churn amplifies CPU cost, widens windows where sticky tables rewarm, and interacts with maxconn and queue limits on frontends, backends, and server lines. Prometheus metrics exposed on the router stats port include families such as haproxy_frontend_current_sessions, haproxy_frontend_max_sessions or limit analogs your exporter version emits, haproxy_backend_current_queue, haproxy_backend_max_queue, haproxy_backend_connections_total, haproxy_backend_session_total, haproxy_backend_http_responses_total with code labels, haproxy_backend_response_errors_total, haproxy_server_current_sessions with paired max session or max connection labels depending on HAProxy build and exporter mapping, haproxy_frontend_connections_dropped_total, listener overflow style haproxy_listener_* metrics when enabled, and process gauges such as haproxy_process_resident_memory_bytes. The routermonitor ServiceMonitor in openshift-ingress namespaces scrapes these series from the router Service on port 1936; your Splunk pipeline must preserve kubernetes pod labels, route labels when the exporter adds them to server metrics, namespace and service labels, and a stable cluster identifier drawn from management-cluster context or external_labels on Prometheus.

UC-3.2.9 remains vanilla Kubernetes Ingress controller analytics aimed at NGINX, Traefik, or other community controllers without coupling to openshift-ingress HAProxy metric names. UC-3.2.18 remains generic ingress 5xx correlation keyed primarily by Kubernetes Ingress namespace and upstream service, not by OpenShift Route and haproxy_server_http_responses_total route label cardinality. UC-3.3.8 remains TLS notAfter governance on Route objects and IngressController default certificates, not live saturation of HAProxy queues. UC-3.3.6 remains ClusterOperator Available Progressing Degraded semantics for the ingress operator at the control plane, while this UC focuses on operand Pod data plane pressure and metric-derived exhaustion signals even when the operator still reports Available=True. UC-3.3.1 ClusterVersion progression is out of scope except when upgrade windows correlate with intentional router scaling events you annotate in change metadata.

Index and permission design land before field extraction. Designate index=ocp_metrics or index=ocp_router for metrics series with sourcetype=ocp_haproxy_metrics when your collector tags HAProxy scrapes distinctly, sourcetype=ocp_router_metrics when you combine router and controller metrics, and sourcetype=ocp_ingresscontroller when you export IngressController API snapshots including status.observedGeneration, status.domain, status.endpointPublishingStrategy type, and availableReplicas style fields your OpenShift minor exposes. Designate index=ocp_events for Kubernetes events with sourcetype=ocp_events. Designate index=ocp_audit for apiserver audit JSON with sourcetype=ocp_audit. Issue distinct HEC tokens per environment with least privilege: platform ingress roles may search all listed sourcetypes; application teams receive filtered views that redact internal hostnames when counsel requires minimization. Retention should cover at least fourteen days hot for incident replay on saturation minutes, thirty days for monthly capacity reviews, and align cold storage with enterprise observability policy.

RBAC and safety: federation jobs must use read-only ServiceAccount tokens bound to monitoring or dedicated scrape identities, not kubeadmin kubeconfig files on employee laptops. When you supplement mstats queries with ad hoc oc debug against router Pods, follow vendor guidance and change control because debug hooks affect production edges. Legal review should confirm route hostnames and internal service names in metric labels are acceptable in Splunk.

Field normalization expectations: map Prometheus metric names into Splunk metric_name values without silent rewrites that break alert portability across clusters. Preserve labels route, namespace, service, backend, proxy, server, pod, instance, ingresscontroller, and shard hints such as router-default versus custom shard names. Flatten IngressController metadata.name into ingresscontroller_name and status.generation into ic_gen with observedGeneration into ic_obs_gen for stale reconciliation math. If you ingest snapshots as JSON events rather than native metrics, add props.conf INDEXED_EXTRACTIONS=json and FIELDALIAS rules so coalesce ladders in SPL still resolve.

Risk briefing: short spikes in haproxy_backend_http_responses_total for 5xx during canary rollouts or autoscaling events can be healthy when error budgets tolerate them; require sustained rates, multi-minute queue depth, or concurrent frontend saturation before paging executives. Sticky-session routes legitimately redistribute sessions after reloads; pair saturation signals with event lanes that show RouterReloaded bursts to avoid blaming backends for expected churn. Sharded ingress clusters shift traffic between router Deployments; a saturated default shard may be intentional if DNS or IngressController scheduling targets a different shard. maxconn tuning for shared development clusters is often deliberately low; compare against environment lookup tables before treating the same numeric thresholds as production incidents. Control-plane scrape outages can drop mstats arms while HAProxy continues serving; combine metric silence with secondary process signals or synthetic route probes before declaring health.

Differentiation recap: openshift-ingress HAProxy router-default metrics and Route-oriented labels, not generic Kubernetes Ingress controller logs alone, not TLS expiry analytics, not ClusterOperator condition tables without data plane metrics.

Operational posture: stamp change_ticket_id onto HEC events when maintenance mutates IngressController replicas, maxConnections settings, tuning ConfigMaps, or endpointPublishingStrategy. When Splunk shows saturation without matching application deploys, suspect volumetric attacks, partner network tests, or mis-aimed health checks; correlate with firewall and CDN dashboards external to this UC.

### Step 2 — Configure data collection

Stand up five complementary lanes Splunk multisearch can fuse: HAProxy frontend saturation gauges via mstats, backend and server pool pressure via mstats, 5xx and error counter ramps via mstats, reload and control-plane churn via ocp_events and ocp_audit searches, and router Pod CPU utilization via mstats on container or process CPU series.

Metrics lane prerequisites: enable the router ServiceMonitor or equivalent user-workload monitoring scrape of openshift-ingress router metrics on port 1936, verify targets in the OpenShift console monitoring UI, and confirm metric_name cardinality is bounded on route labels in large multitenant clusters. Forward native Prometheus remote write or OTLP metrics into Splunk metrics indexes with explicit metric_name values matching haproxy_* strings. Document whether your pipeline stores counters as monotonically increasing values suitable for per-span max or delta math.

IngressController snapshot lane: schedule a management utility every five minutes to oc get ingresscontroller -o json or watch operator.openshift.io IngressController objects. Emit sourcetype=ocp_ingresscontroller events with ingresscontroller_name, ic_gen, ic_obs_gen, endpoint_publishing_strategy, available_router_replicas or equivalent fields, and domain strings that map to public DNS expectations.

Events lane: forward Kubernetes events with sourcetype=ocp_events using Splunk OpenShift App patterns or an OpenTelemetry Collector k8s_events receiver. Preserve reasons and messages referencing Route admission failures, router reloads, and ingress operator hints.

Audit lane: ship Kubernetes API audit logs into index=ocp_audit with sourcetype=ocp_audit. Ensure objectRef captures ingresscontroller.operator.openshift.io and route.route.openshift.io resources, verbs capture create update patch delete, and user identities map to GitOps service accounts during route storms.

Router CPU lane: federate container_cpu_usage_seconds_total or namespace_workload_pod:kube_pod_owner:relabel style recording rules limited to openshift-ingress and deployment router-default, or process_cpu_seconds_total when exposed without excessive cardinality. Preserve pod labels for join keys.

Example oc verification operators run during design reviews before Splunk paging goes live:

oc -n openshift-ingress get pods -l ingresscontroller.operator.openshift.io/deployment-ingresscontroller=default
oc -n openshift-ingress get svc router-default -o wide
oc -n openshift-ingress get servicemonitor routermonitor -o yaml
oc get ingresscontroller default -o jsonpath='{.status.observedGeneration}{"\n"}'

props.conf guidance: TRUNCATE sufficiently large for Prometheus text lines if any arm still ingests raw exposition, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER rules for multiplexed syslog headers when forwarders wrap metrics.

Pre-save validation: mstats earliest=-1h against haproxy_frontend_current_sessions must return non-zero buckets on busy clusters; ocp_events should show RouterReloaded or equivalent messages during controlled route create delete drills; ocp_audit should show ingresscontroller patches under approved changes; CPU metrics should align with oc adm top pod -n openshift-ingress samples within instrumentation delay.

Collector hardening: TLS to Splunk, quarterly HEC token rotation, separate dev and prod metric indexes, region and cloud_account labels on every event when one tenant spans continents.

Dashboards: Splunk OpenShift App panels should include shard-level severity coloring from this saved search, drilldowns to raw metric series, IngressController JSON, events, and audit excerpts, plus single-value tiles for count of clusters at page severity.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_9_router_haproxy_saturation with a five minute schedule for high-traffic production, a fifteen minute schedule for standard estates, dispatch earliest=-2h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster, ingresscontroller_name, and backend_key rows for twenty minutes unless severity escalates from warn to page. Include recommended_action, fe_sat_ratio, bk_queue_max, xx5_rate_hint, reload_burst_cnt, and router_cpu_sat in pager bodies so incident commanders open the correct runbook section without rerunning ad hoc searches.

Pipeline narrative for operators: multisearch fans frontend mstats, backend mstats, 5xx counter mstats, reload and audit event searches, and router CPU mstats so a silent single-arm outage does not hide genuine edge saturation. coalesce() absorbs kubernetes_pod_name versus pod versus pod_name label drift. streamstats measures short-term velocity on counter-derived rates and queue ramps. eventstats adds cluster-level percentiles for saturation ratios and reload bursts. case() maps combined frontend pressure, queue depth, 5xx acceleration, listener drop hints, reload storms, generation drift, and CPU ceilings into page warn or info tiers. recommended_action encodes verbs referencing oc describe ingresscontroller, oc logs deployment router-default, HAProxy stats socket investigation under vendor guidance, shard scaling, maxConnections review, and backend readiness probes without pretending Splunk replaces tcpdump on edge nodes.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.9 OpenShift router HAProxy saturation — mstats arms: frontend backend 5xx reload_events router_cpu. Indexes: ocp_metrics|ocp_router. Tunables: earliest=-2h@h latest=now; fe_sat_warn=0.82 fe_sat_page=0.95; q_warn=50 r5xx_warn=25 cpu_warn=0.85")`
| multisearch
    [ | mstats latest(_value) AS fe_sessions WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_frontend_current_sessions earliest=-2h@h latest=now span=1m BY cluster pod proxy
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | eval proxy=lower(trim(toString(coalesce(proxy, frontend, ""))))
      | join type=left max=0 cluster pod proxy [ | mstats latest(_value) AS fe_max_sessions WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_frontend_max_sessions earliest=-2h@h latest=now span=1m BY cluster pod proxy
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval proxy=lower(trim(toString(coalesce(proxy, frontend, "")))) ]
      | eval fe_max_sessions=coalesce(fe_max_sessions, fe_sessions, 0)
      | eval fe_sat_ratio=if(fe_max_sessions>0, round(fe_sessions/fe_max_sessions, 4), null())
      | eval lane="fe_sat"
      | eval backend_key=strcat(cluster,"#",coalesce(proxy,"fe"))
      | fields cluster pod fe_sessions fe_max_sessions fe_sat_ratio lane backend_key ]
    [ | mstats max(_value) AS bk_queue_max WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_current_queue earliest=-2h@h latest=now span=1m BY cluster pod backend server
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
      | eval server=lower(trim(toString(coalesce(server, srv, ""))))
      | join type=left max=0 cluster pod backend server [ | mstats max(_value) AS bk_queue_limit WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_max_queue earliest=-2h@h latest=now span=1m BY cluster pod backend server
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
        | eval server=lower(trim(toString(coalesce(server, srv, "")))) ]
      | join type=left max=0 cluster pod backend server [ | mstats max(_value) AS srv_sessions_peak WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_server_current_sessions earliest=-2h@h latest=now span=1m BY cluster pod backend server
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
        | eval server=lower(trim(toString(coalesce(server, srv, "")))) ]
      | eval backend_key=strcat(cluster,"#",coalesce(backend,"bk"),"#",coalesce(server,"srv"))
      | eval lane="bk_pool"
      | fields cluster pod backend server bk_queue_max bk_queue_limit srv_sessions_peak lane backend_key ]
    [ | mstats max(_value) AS r5xx WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_http_responses_total earliest=-2h@h latest=now span=1m BY cluster pod backend route code
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
      | eval route=lower(trim(toString(coalesce(route, openshift_route, host, ""))))
      | eval code=lower(trim(toString(coalesce(code, status_code, ""))))
      | where match(code,"5..|5xx")
      | stats sum(r5xx) AS xx5_sum BY cluster pod backend route
      | join type=left max=0 cluster pod backend route [ | mstats max(_value) AS err_raw WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_response_errors_total earliest=-2h@h latest=now span=1m BY cluster pod backend route
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
        | eval route=lower(trim(toString(coalesce(route, openshift_route, host, ""))))
        | stats sum(err_raw) AS err_sum BY cluster pod backend route ]
      | fillnull value=0 err_sum xx5_sum
      | sort cluster pod backend route - _time
      | streamstats window=2 current=t global=f last(xx5_sum) AS prev_xx5 BY cluster pod backend route
      | eval xx5_delta=xx5_sum-coalesce(prev_xx5,xx5_sum)
      | eval backend_key=strcat(cluster,"#",coalesce(backend,"bk"),"#",coalesce(route,"rt"))
      | eval lane="xx5"
      | fields cluster pod backend route xx5_sum err_sum xx5_delta lane backend_key ]
    [ search (index=ocp_events OR index=ocp_audit) (sourcetype=ocp_events OR sourcetype=ocp_audit) earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval lane=if(sourcetype=="ocp_audit", "reload_aud", "reload_evt")
      | eval msg=lower(toString(coalesce(message, Message, objectRef_name, verb, "")))
      | where match(msg,"routerreload|reload|ingresscontroller|route\.route\.openshift") OR match(_raw,"RouterReloaded|IngressController")
      | eval reload_hit=1
      | stats sum(reload_hit) AS reload_burst_cnt earliest(_time) AS reload_first latest(_time) AS reload_last BY cluster lane
      | eval backend_key=strcat(cluster,"#reload")
      | fields cluster reload_burst_cnt reload_first reload_last lane backend_key ]
    [ | mstats avg(_value) AS cpu_core_avg WHERE (index=ocp_metrics OR index=ocp_router) metric_name=container_cpu_usage_seconds_total earliest=-2h@h latest=now span=1m BY cluster pod namespace container
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | where namespace="openshift-ingress" OR match(pod,"router-default")
      | stats max(cpu_core_avg) AS router_cpu_sat BY cluster pod
      | eval lane="router_cpu"
      | eval backend_key=strcat(cluster,"#",pod)
      | fields cluster pod router_cpu_sat lane backend_key ]
| eval cluster=lower(trim(coalesce(cluster, "unknown_cluster")))
| eval backend_key=coalesce(backend_key, strcat(cluster,"#agg"))
| stats
    max(eval(if(lane=="fe_sat", fe_sat_ratio, null()))) AS fe_sat_ratio
    max(eval(if(lane=="fe_sat", fe_sessions, null()))) AS fe_sessions
    max(eval(if(lane=="fe_sat", fe_max_sessions, null()))) AS fe_max_sessions
    max(eval(if(lane=="bk_pool", bk_queue_max, null()))) AS bk_queue_max
    max(eval(if(lane=="bk_pool", bk_queue_limit, null()))) AS bk_queue_limit
    max(eval(if(lane=="bk_pool", srv_sessions_peak, null()))) AS srv_sessions_peak
    max(eval(if(lane=="xx5", xx5_delta, null()))) AS xx5_delta
    max(eval(if(lane=="xx5", err_sum, null()))) AS err_sum
    max(eval(if(lane=="xx5", route, null()))) AS hot_route
    max(eval(if(lane=="reload_evt" OR lane=="reload_aud", reload_burst_cnt, null()))) AS reload_burst_cnt
    max(eval(if(lane=="router_cpu", router_cpu_sat, null()))) AS router_cpu_sat
    values(lane) AS lanes_seen
    max(_time) AS last_seen
  BY cluster backend_key
| eventstats perc90(fe_sat_ratio) AS fleet_fe_p90 perc90(bk_queue_max) AS fleet_q_p90 BY cluster
| streamstats window=12 current=t global=f sum(xx5_delta) AS xx5_window BY cluster backend_key
| join type=left max=0 cluster [
    search (index=ocp_metrics OR index=ocp_router) sourcetype=ocp_ingresscontroller earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval ic_gen=tonumber(tostring(coalesce(generation, metadata_generation, "")),10)
      | eval ic_obs=tonumber(tostring(coalesce(observedGeneration, status_observedGeneration, "")),10)
      | eval ic_gap=abs(ic_gen-ic_obs)
      | stats max(ic_gap) AS ic_gap_max BY cluster ]
| fillnull value=0 ic_gap_max reload_burst_cnt xx5_window err_sum router_cpu_sat bk_queue_max fe_sat_ratio
| eval severity=case(
    fe_sat_ratio>=0.95 AND bk_queue_max>=50, "page",
    xx5_window>=25 AND fe_sat_ratio>=0.75, "page",
    bk_queue_max>=200 OR err_sum>=500, "page",
    fe_sat_ratio>=0.82 OR bk_queue_max>=50, "warn",
    xx5_window>=10, "warn",
    reload_burst_cnt>=12, "warn",
    ic_gap_max>=3, "warn",
    router_cpu_sat>=0.85, "warn",
    true(), "info")
| eval recommended_action=case(
    severity=="page" AND fe_sat_ratio>=0.9, "scale_router_replicas_or_shard_routes_review_maxconn_and_publish_strategy",
    severity=="page" AND xx5_window>=25, "triage_per_route_backend_readiness_and_upstream_503_sources",
    bk_queue_max>=200, "inspect_backend_capacity_and_haproxy_timeout_tuning",
    reload_burst_cnt>=12, "correlate_route_gitops_storms_and_template_router_logs",
    ic_gap_max>=3, "oc_describe_ingresscontroller_and_verify_operand_rollout",
    router_cpu_sat>=0.85, "confirm_cpu_limits_and_horizontal_shard_strategy_for_single_threaded_haproxy_hot_paths",
    true(), "continue_monitoring_router_metrics_and_synthetic_route_probes")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster backend_key fe_sessions fe_max_sessions fe_sat_ratio fleet_fe_p90 bk_queue_max bk_queue_limit srv_sessions_peak fleet_q_p90 xx5_window err_sum hot_route reload_burst_cnt router_cpu_sat ic_gap_max lanes_seen severity recommended_action last_seen cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_9_router_haproxy_saturation_alert]
cron_schedule = */5 * * * *
dispatch.earliest_time = -2h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-ingress-oncall@example.com
action.email.subject = OCP router HAProxy $result.severity$ $result.cluster$ $result.backend_key$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_9_router_haproxy_saturation | where severity IN ("page","warn")
```

Performance: high-cardinality route labels can explode mstats cost; use recording rules in Prometheus to pre-aggregate 5xx rates per namespace or shard before Splunk ingestion when Job Inspector shows queue delays. Materialize five-minute summaries per cluster and shard into a summary index for fleet dashboards while retaining this search for investigations.

For Splunk ITSI optional deployments, bind KPIs to fe_sat_ratio and bk_queue_max by cluster entity, attaching episode policies when two consecutive windows exceed warn thresholds during business hours.

### Step 4 — Validate

Ground truth begins on-cluster with HAProxy statistics and router Pod health. Exec or debug into openshift-ingress router Pods only under vendor-approved procedures and compare Prometheus gauges on port 1936 to Splunk mstats rows for the same minute buckets. When numbers disagree, verify clock skew, duplicated scrapes, or stale pod labels after rollouts.

IngressController status: oc describe ingresscontroller default and compare generation to observedGeneration against Splunk ic_gap_max logic. Confirm available router replica counts match Deployment readiness before muting saturation alerts as false.

Event correlation: during validation drills, create and delete test Routes in a lab namespace and confirm ocp_events captures reload-related messages while audit records show route create delete verbs with expected service accounts.

5xx correlation: open application dashboards for backends tied to hot_route labels when exporters provide them; when labels are absent, pivot from backend_key to Service and Endpoints objects via namespace conventions.

Synthetic load: in lab only, generate reproducible load against a canary Route while lowering maxConnections in a dedicated test IngressController, observe rising fe_sat_ratio and queue metrics in Splunk, then restore limits and confirm severity returns to info.

Negative test: on a quiet window with healthy backends, confirm fe_sat_ratio stays below warn thresholds, xx5_window remains near zero, and the alert wrapper filtered to page and warn emits zero rows.

Scrape failure drill: pause user-workload monitoring scrape of router targets briefly in lab and confirm the search surfaces info severity or analyst-visible lane gaps without silent empty results that masquerade as healthy edges.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Frontend fe_sat_ratio pinned high with flat application deploys: inspect SYN flood or unexpected client retries, validate external load balancer health checks, and confirm DNS still targets the intended shard publishing strategy.

Case 2 — Backend bk_queue_max climbs while Endpoints show ready replicas: tighten readiness probes only after confirming traffic shift is intentional, check upstream keepalive mismatches, and review HAProxy timeout client server values for slow microservices.

Case 3 — Per-route xx5_window spikes during canary rollouts: treat as legitimate microservice blip when SLO burn is within budget; page only when duration exceeds governance minutes or affects multiple routes sharing a backend pool.

Case 4 — haproxy_server_current_sessions approaches maxconn on specific servers: scale application replicas, verify anti-affinity, and review Route shard placement so one router Pod does not own all heavy sticky clients.

Case 5 — reload_burst_cnt high after GitOps reconciles hundreds of Routes: batch route updates, evaluate sharding, and coordinate controller-level rate limits with platform networking before blaming HAProxy memory alone.

Case 6 — ic_gap_max nonzero with operator Available=True: capture template-router logs, verify ConfigMap mounts, and check for SDN or node pressure delaying Pod restarts.

Case 7 — router_cpu_sat high with moderate session counts: profile TLS cipher cost, certificate chain size, and logging verbosity on routers; consider moving verbose access logs off hot paths.

Case 8 — Listener or frontend drop counters rise without queue depth: investigate kernel somaxconn and sysctl tuning on nodes hosting router Pods, plus NIC drops on underlying hardware.

Case 9 — Intentionally low maxConnections on shared dev clusters: annotate lookup metadata to downgrade severity for non-production cluster labels while keeping production thresholds strict.

Case 10 — Scheduled external blackbox monitors generate synthetic 5xx: whitelist probe source addresses or schedule maintenance windows that suppress xx5_window alerts during probe configuration changes.

Case 11 — Sticky-session warm-up after prolonged reload storm: expect temporary imbalance across server lines; validate convergence within minutes before opening backend defects.

Case 12 — Healthy control test: page and warn filters silent for thirty minutes while mstats arms show fe_sat_ratio below warn, queues stable, ITSI episodes inactive, and synthetic route checks green across shards.

Closing checklist: multisearch lists five arms; coalesce normalizes cluster and pod labels; streamstats and eventstats quantify 5xx velocity and fleet saturation context; case maps severity; closing table includes cluster, backend_key, fe_sessions, fe_max_sessions, fe_sat_ratio, fleet_fe_p90, bk_queue_max, bk_queue_limit, srv_sessions_peak, fleet_q_p90, xx5_window, err_sum, hot_route, reload_burst_cnt, router_cpu_sat, ic_gap_max, lanes_seen, severity, recommended_action, last_seen for nineteen analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.9 OpenShift router HAProxy saturation — mstats arms: frontend backend 5xx reload_events router_cpu. Indexes: ocp_metrics|ocp_router. Tunables: earliest=-2h@h latest=now; fe_sat_warn=0.82 fe_sat_page=0.95; q_warn=50 r5xx_warn=25 cpu_warn=0.85")`
| multisearch
    [ | mstats latest(_value) AS fe_sessions WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_frontend_current_sessions earliest=-2h@h latest=now span=1m BY cluster pod proxy
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | eval proxy=lower(trim(toString(coalesce(proxy, frontend, ""))))
      | join type=left max=0 cluster pod proxy [ | mstats latest(_value) AS fe_max_sessions WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_frontend_max_sessions earliest=-2h@h latest=now span=1m BY cluster pod proxy
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval proxy=lower(trim(toString(coalesce(proxy, frontend, "")))) ]
      | eval fe_max_sessions=coalesce(fe_max_sessions, fe_sessions, 0)
      | eval fe_sat_ratio=if(fe_max_sessions>0, round(fe_sessions/fe_max_sessions, 4), null())
      | eval lane="fe_sat"
      | eval backend_key=strcat(cluster,"#",coalesce(proxy,"fe"))
      | fields cluster pod fe_sessions fe_max_sessions fe_sat_ratio lane backend_key ]
    [ | mstats max(_value) AS bk_queue_max WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_current_queue earliest=-2h@h latest=now span=1m BY cluster pod backend server
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
      | eval server=lower(trim(toString(coalesce(server, srv, ""))))
      | join type=left max=0 cluster pod backend server [ | mstats max(_value) AS bk_queue_limit WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_max_queue earliest=-2h@h latest=now span=1m BY cluster pod backend server
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
        | eval server=lower(trim(toString(coalesce(server, srv, "")))) ]
      | join type=left max=0 cluster pod backend server [ | mstats max(_value) AS srv_sessions_peak WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_server_current_sessions earliest=-2h@h latest=now span=1m BY cluster pod backend server
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
        | eval server=lower(trim(toString(coalesce(server, srv, "")))) ]
      | eval backend_key=strcat(cluster,"#",coalesce(backend,"bk"),"#",coalesce(server,"srv"))
      | eval lane="bk_pool"
      | fields cluster pod backend server bk_queue_max bk_queue_limit srv_sessions_peak lane backend_key ]
    [ | mstats max(_value) AS r5xx WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_http_responses_total earliest=-2h@h latest=now span=1m BY cluster pod backend route code
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
      | eval route=lower(trim(toString(coalesce(route, openshift_route, host, ""))))
      | eval code=lower(trim(toString(coalesce(code, status_code, ""))))
      | where match(code,"5..|5xx")
      | stats sum(r5xx) AS xx5_sum BY cluster pod backend route
      | join type=left max=0 cluster pod backend route [ | mstats max(_value) AS err_raw WHERE (index=ocp_metrics OR index=ocp_router) metric_name=haproxy_backend_response_errors_total earliest=-2h@h latest=now span=1m BY cluster pod backend route
        | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
        | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
        | eval backend=lower(trim(toString(coalesce(backend, proxy, ""))))
        | eval route=lower(trim(toString(coalesce(route, openshift_route, host, ""))))
        | stats sum(err_raw) AS err_sum BY cluster pod backend route ]
      | fillnull value=0 err_sum xx5_sum
      | sort cluster pod backend route - _time
      | streamstats window=2 current=t global=f last(xx5_sum) AS prev_xx5 BY cluster pod backend route
      | eval xx5_delta=xx5_sum-coalesce(prev_xx5,xx5_sum)
      | eval backend_key=strcat(cluster,"#",coalesce(backend,"bk"),"#",coalesce(route,"rt"))
      | eval lane="xx5"
      | fields cluster pod backend route xx5_sum err_sum xx5_delta lane backend_key ]
    [ search (index=ocp_events OR index=ocp_audit) (sourcetype=ocp_events OR sourcetype=ocp_audit) earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval lane=if(sourcetype=="ocp_audit", "reload_aud", "reload_evt")
      | eval msg=lower(toString(coalesce(message, Message, objectRef_name, verb, "")))
      | where match(msg,"routerreload|reload|ingresscontroller|route\.route\.openshift") OR match(_raw,"RouterReloaded|IngressController")
      | eval reload_hit=1
      | stats sum(reload_hit) AS reload_burst_cnt earliest(_time) AS reload_first latest(_time) AS reload_last BY cluster lane
      | eval backend_key=strcat(cluster,"#reload")
      | fields cluster reload_burst_cnt reload_first reload_last lane backend_key ]
    [ | mstats avg(_value) AS cpu_core_avg WHERE (index=ocp_metrics OR index=ocp_router) metric_name=container_cpu_usage_seconds_total earliest=-2h@h latest=now span=1m BY cluster pod namespace container
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, kubernetes_pod_name, pod_name, ""))))
      | where namespace="openshift-ingress" OR match(pod,"router-default")
      | stats max(cpu_core_avg) AS router_cpu_sat BY cluster pod
      | eval lane="router_cpu"
      | eval backend_key=strcat(cluster,"#",pod)
      | fields cluster pod router_cpu_sat lane backend_key ]
| eval cluster=lower(trim(coalesce(cluster, "unknown_cluster")))
| eval backend_key=coalesce(backend_key, strcat(cluster,"#agg"))
| stats
    max(eval(if(lane=="fe_sat", fe_sat_ratio, null()))) AS fe_sat_ratio
    max(eval(if(lane=="fe_sat", fe_sessions, null()))) AS fe_sessions
    max(eval(if(lane=="fe_sat", fe_max_sessions, null()))) AS fe_max_sessions
    max(eval(if(lane=="bk_pool", bk_queue_max, null()))) AS bk_queue_max
    max(eval(if(lane=="bk_pool", bk_queue_limit, null()))) AS bk_queue_limit
    max(eval(if(lane=="bk_pool", srv_sessions_peak, null()))) AS srv_sessions_peak
    max(eval(if(lane=="xx5", xx5_delta, null()))) AS xx5_delta
    max(eval(if(lane=="xx5", err_sum, null()))) AS err_sum
    max(eval(if(lane=="xx5", route, null()))) AS hot_route
    max(eval(if(lane=="reload_evt" OR lane=="reload_aud", reload_burst_cnt, null()))) AS reload_burst_cnt
    max(eval(if(lane=="router_cpu", router_cpu_sat, null()))) AS router_cpu_sat
    values(lane) AS lanes_seen
    max(_time) AS last_seen
  BY cluster backend_key
| eventstats perc90(fe_sat_ratio) AS fleet_fe_p90 perc90(bk_queue_max) AS fleet_q_p90 BY cluster
| streamstats window=12 current=t global=f sum(xx5_delta) AS xx5_window BY cluster backend_key
| join type=left max=0 cluster [
    search (index=ocp_metrics OR index=ocp_router) sourcetype=ocp_ingresscontroller earliest=-2h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval ic_gen=tonumber(tostring(coalesce(generation, metadata_generation, "")),10)
      | eval ic_obs=tonumber(tostring(coalesce(observedGeneration, status_observedGeneration, "")),10)
      | eval ic_gap=abs(ic_gen-ic_obs)
      | stats max(ic_gap) AS ic_gap_max BY cluster ]
| fillnull value=0 ic_gap_max reload_burst_cnt xx5_window err_sum router_cpu_sat bk_queue_max fe_sat_ratio
| eval severity=case(
    fe_sat_ratio>=0.95 AND bk_queue_max>=50, "page",
    xx5_window>=25 AND fe_sat_ratio>=0.75, "page",
    bk_queue_max>=200 OR err_sum>=500, "page",
    fe_sat_ratio>=0.82 OR bk_queue_max>=50, "warn",
    xx5_window>=10, "warn",
    reload_burst_cnt>=12, "warn",
    ic_gap_max>=3, "warn",
    router_cpu_sat>=0.85, "warn",
    true(), "info")
| eval recommended_action=case(
    severity=="page" AND fe_sat_ratio>=0.9, "scale_router_replicas_or_shard_routes_review_maxconn_and_publish_strategy",
    severity=="page" AND xx5_window>=25, "triage_per_route_backend_readiness_and_upstream_503_sources",
    bk_queue_max>=200, "inspect_backend_capacity_and_haproxy_timeout_tuning",
    reload_burst_cnt>=12, "correlate_route_gitops_storms_and_template_router_logs",
    ic_gap_max>=3, "oc_describe_ingresscontroller_and_verify_operand_rollout",
    router_cpu_sat>=0.85, "confirm_cpu_limits_and_horizontal_shard_strategy_for_single_threaded_haproxy_hot_paths",
    true(), "continue_monitoring_router_metrics_and_synthetic_route_probes")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster backend_key fe_sessions fe_max_sessions fe_sat_ratio fleet_fe_p90 bk_queue_max bk_queue_limit srv_sessions_peak fleet_q_p90 xx5_window err_sum hot_route reload_burst_cnt router_cpu_sat ic_gap_max lanes_seen severity recommended_action last_seen cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Performance.cpu_load_percent) AS cpu_load latest(Performance.mem_used) AS mem_used FROM datamodel=Performance WHERE nodename=Performance earliest=-2h@h latest=now BY Performance.host
| rename Performance.host AS perf_host
| join type=left max=0 perf_host
    [| tstats summariesonly=t latest(Web.status) AS web_status latest(Web.url) AS web_url FROM datamodel=Web WHERE nodename=Web earliest=-2h@h latest=now BY Web.src
     | rename Web.src AS perf_host ]
| where like(lower(web_url), "%apps%") OR like(lower(perf_host), "%router%")
| table perf_host cpu_load mem_used web_status web_url
```

## Visualization

Severity-colored table by cluster and backend_key with drilldowns to mstats-backed metric series, ocp_ingresscontroller JSON, ocp_events reload messages, and ocp_audit ingress mutations; timechart of fe_sat_ratio and bk_queue_max; single-value tiles for page severity counts per fleet.

## Known False Positives

Legitimate canary or blue-green rollouts often emit short-lived bursts of 5xx responses while new pods warm up or while load shifts between ReplicationControllers; require sustained xx5_window minutes or customer-impact corroboration before paging platform executives. Teams sometimes tune maxConnections and router Pod resource limits deliberately low on shared development clusters to contain noisy-neighbor cost; join alerts to environment lookups so non-production shards downgrade automatically. Planned horizontal pod autoscaler scale-down events during low-traffic windows can compress headroom and make transient saturation look severe until traffic returns; annotate maintenance metadata on HTTP Event Collector events when autoscaler policies change. Peering partners or WAN acceleration appliances occasionally run scripted connection tests that resemble storms; correlate source addresses and change tickets before blaming internal microservices. Sticky-session routes after large reload windows can skew server-level session counts until the affinity table stabilizes; treat brief haproxy_server_current_sessions imbalance as expected when reload_burst_cnt was high minutes earlier. Scheduled blackbox probes from external monitoring platforms sometimes target canary hostnames that intentionally fail authentication; whitelist probe identities or exclude those hostnames from 5xx rate math. Certificate reissue or IngressController publishing strategy edits can spike reload counts without user-facing errors; pair reload_burst_cnt with fe_sat_ratio before declaring incidents. Prometheus cardinality or scrape delays can null individual mstats arms while HAProxy remains healthy; avoid auto-closing incidents solely because one arm is silent without cross-checking router Pod readiness. Multi-shard estates may show saturation on non-default shards during DNS migration projects; confirm which IngressController owns the hostname before remediating router-default alone.

## References

- [OpenShift Documentation — Configuring ingress cluster traffic overview](https://docs.openshift.com/container-platform/latest/networking/configuring_ingress_cluster_traffic/configuring-ingress-cluster-traffic-overview.html)
- [OpenShift Documentation — Ingress Operator](https://docs.openshift.com/container-platform/latest/networking/networking_operators/ingress-operator.html)
- [OpenShift Documentation — Managing ingress sharding](https://docs.openshift.com/container-platform/latest/networking/configuring_ingress_cluster_traffic/ingress-sharding.html)
- [OpenShift Documentation — Managing metrics](https://docs.openshift.com/container-platform/latest/monitoring/managing-metrics/managing-metrics.html)
- [Red Hat Blog — HAProxy tuning and performance optimization](https://www.redhat.com/en/blog/red-hat-openshift-container-platform-4-now-defaults-haproxy-2-0-router)
- [HAProxy Enterprise — Prometheus metrics and observability](https://www.haproxy.com/documentation/hapee/latest/observability/prometheus/)
- [HAProxy Documentation — Configuration manual](https://www.haproxy.com/documentation/haproxy-configuration-manual/latest/)
