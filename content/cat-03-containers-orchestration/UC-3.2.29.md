<!-- AUTO-GENERATED from UC-3.2.29.json — DO NOT EDIT -->

---
id: "3.2.29"
title: "Kubernetes CronJob Lateness, Missed-Schedule Detection, and Schedule-SLA Breach (CronJob Lateness Axis)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.29 · Kubernetes CronJob Lateness, Missed-Schedule Detection, and Schedule-SLA Breach (CronJob Lateness Axis)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster's timed jobs so they start when promised and finish on time. When a schedule quietly slips, time zones disagree, or policy blocks the next run, we raise a clear signal before nightly work like backups or reports stops happening.*

---

## Description

Detects Kubernetes CronJob schedule fidelity breaches before execution-failure analytics apply: lastScheduleTime and lastSuccessfulTime drift versus governed cadence from kube_cronjob_status_last_schedule_time and kube_cronjob_status_last_successful_time, Warning events with MissedSchedule or FailedNeedsStart, wrongful suspend while governance still expects runs, concurrencyPolicy drift and Forbid stalls with active child Jobs, kube_job_owner linkage gaps, resourceVersion churn after edits, fleet-wide skew hints when every CronJob slips together, and startingDeadlineSeconds pressure without proving a Pod exited non-zero.

## Value

Nightly ETL, certificate rotation, and backup CronJobs fail quietly when the schedule plane breaks—no CrashLoopBackOff, no failed Job Pod, just missing lastScheduleTime movement or endless MissedSchedule warnings while concurrencyPolicy=Forbid blocks behind a hung predecessor. Finance and security teams need one row that names schedule ages, success proof ages, event counts, suspend truth, active Job counts, and ownership so bridges open on lateness SLAs instead of re-running UC-3.2.20 execution searches that stay empty when nothing ever ran.

## Implementation

Ingest kube-state-metrics CronJob timestamp and spec gauges plus kube_job_owner into k8s_metrics, stream kube:events CronJob warnings into k8s, publish critical_cronjobs.csv with cadence and concurrency intent, save uc_3_2_29_kube_cronjob_lateness_missed_schedule_sla every five minutes with earliest=-8h@m, route critical and high rows per savedsearches.conf, and validate with a lab CronJob that stops scheduling while suspended jobs remain absent from failure metrics.

## Evidence

Saved search uc_3_2_29_kube_cronjob_lateness_missed_schedule_sla with five-minute schedule; critical_cronjobs.csv versioned in git; weekly CSV export of the closing table to a restricted evidence index with kube-state-metrics chart version and collector digest.

## Control test

### Positive scenario

In lab namespace qa-cron-lateness-3229 create or patch a governed CronJob so reconciliation stops or spec.suspend conflicts with should_be_running=1 while kube:events emit MissedSchedule for the CronJob involvedObject; execute uc_3_2_29_kube_cronjob_lateness_missed_schedule_sla and expect a row with missed_schedule_evt_cnt greater than zero or schedule_sla_breach equal to one when last_schedule_age_min exceeds stale_after_min from critical_cronjobs.csv.

### Negative scenario

Run a healthy minutely CronJob with short Job duration, should_be_running=1, accurate expected_cadence_minutes, and no suspend drift; confirm last_schedule_age_min stays below stale_after_min for forty minutes and the alert predicate emits zero qualifying rows without intentional injects.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform site reliability engineers, batch data owners, and observability engineers who operate Splunk OpenTelemetry Collector plus kube-state-metrics across production, pre-production, and regulated partitions. This use case isolates the CronJob lateness and schedule-fidelity plane: when a CronJob should have fired by wall clock versus status.lastScheduleTime, when status.lastSuccessfulTime drifts far behind the schedule implied by spec.schedule and optional spec.timeZone (stable from v1.27 onward), when Warning events carry reason MissedSchedule or FailedNeedsStart, when concurrencyPolicy Allow versus Forbid versus Replace creates skipped windows without a failed Pod story, when kube_cronjob_metadata_resource_version jumps after edits while executions pause, when startingDeadlineSeconds causes intentional late-start drops, when cluster clock skew or apiserver time disagrees with Splunk indexer time, when successful Job objects disappear because ttlSecondsAfterFinished and history limits plus controller housekeeping removed the only proof of a good run, and when a data-warehouse ETL CronJob misses 02:00 local intent for two weeks while dashboards still show green CPU. UC-3.2.20 remains the execution-failure axis for batch workloads that actually ran and then failed: BackoffLimitExceeded, non-zero exits, OOMKilled in the Job Pod, and kube_job_status_failed positivity. If the child Job never becomes healthy enough to fail, or the CronJob never enqueues a Job at all, UC-3.2.20 may stay quiet while this UC still fires. UC-3.2.6 remains Deployment Progressing and Available condition analytics. UC-3.2.39 remains the fleet-wide Warning event statistical storm detector without schedule-SLA math on kube-state-metrics timestamps.

Operational prerequisites begin with trustworthy time. Compare apiserver object timestamps, node NTP, kube-controller-manager leader clock, and Splunk _time skew. Latency-sensitive math uses last_schedule_age_min and last_success_age_min derived from kube_cronjob_status_last_schedule_time and kube_cronjob_status_last_successful_time as seconds-since-epoch gauges from kube-state-metrics. A ninety-second skew between Prometheus scrape time and Splunk event time is usually tolerable; beyond three minutes, false schedule breaches accumulate.

Indexing layout mirrors other category three gold controls: index=k8s_metrics for Prometheus text or normalized scrape events from kube-state-metrics, index=k8s for kube:events with CronJob involvedObject kind, and index=k8s_audit when you must attribute kubectl patch, GitOps sync, or Argo CD suspend operations against spec.suspend. HEC tokens stay in vaults with quarterly rotation. RBAC for collectors must list watches on CronJobs, Jobs, and Events.

kube-state-metrics must expose kube_cronjob_status_last_schedule_time, kube_cronjob_status_last_successful_time, kube_cronjob_spec_schedule (schedule label), kube_cronjob_spec_starting_deadline_seconds, kube_cronjob_spec_suspend, kube_cronjob_metadata_resource_version, kube_cronjob_status_active, plus kube_job_owner labeled with owner_kind CronJob so Splunk can correlate active child Job cardinality to a parent CronJob without assuming name-prefix heuristics alone. Confirm chart semver against upstream cronjob-metrics documentation because label names occasionally shift across minors.

Governance lookup critical_cronjobs.csv must carry cluster, namespace, cronjob_name, expected_cadence_minutes, owner_team, tier, should_be_running, and expected_concurrency_policy when you want drift detection between live metrics and change-management intent. Refresh the CSV when new CronJobs onboard, when finance close freezes suspend automation, when daylight-saving policy changes, or when a CronJob gains spec.timeZone that moves local intent relative to UTC dashboards.

CIM mapping uses Application_State because scheduled batch controllers are first-class application objects whose schedule health describes reliability, not merely CPU curves. Performance supplies a deliberate tstats correlation tick in the opening join so estates that accelerate Performance summaries still exercise the same datamodel path during audits; expand the join when you tie lateness to node saturation during cron storms.

Risk briefing for executives: a silent CronJob miss looks like a flat dashboard until invoices are wrong, certificates expire, or backups stop. This UC names cluster, namespace, cronjob, schedule string token, ages, suspend bit, active children, event counts, Forbid stall logic, and severity without claiming the Pod exited non-zero.

Licensing note: high-cardinality job_name labels from Helm hashes can explode series counts; use recording rules or allow-list labels only after FinOps review. Privacy note: event messages can echo volume handles; restrict dashboard ACLs.

Training: teach responders to read last_schedule_age_min alongside expected_cadence_minutes from the lookup, to treat MissedSchedule as schedule-plane evidence distinct from CrashLoopBackOff, and to verify spec.timeZone before blaming the controller.

Review cadence: quarterly replay one historical missed-schedule incident after kube-state-metrics upgrades because regex arms drift when exporters rename metrics.

Differentiation recap: schedule fidelity, lateness, and missed enqueue semantics are the axis; Job execution failure after a Pod runs is UC-3.2.20.

Escalation alignment: tier-one rows with critical severity should page both owner_team from critical_cronjobs.csv and the platform bridge when kube_cronjob_spec_suspend disagrees with should_be_running during undeclared freezes.

Telemetry hygiene: deduplicate overlapping Prometheus and OpenTelemetry scrapes without stable dedup keys only after you understand double-counting risk.

FinOps alignment: CronJobs that spike concurrent Jobs during recovery still burn node budget; pair this UC with chargeback reviews when Replace policy creates thundering herds.

Security alignment: suspend bits without change tickets may indicate break-glass abuse; correlate k8s_audit when available.

Hardware scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed clusters where kube-state-metrics RBAC can list CronJobs cluster-wide; Arm and x86 worker fleets are in scope when metric text lines remain Prometheus compatible.

OpenShift note: map project to namespace consistently in the lookup. GKE Autopilot and AKS managed Kubernetes may surface different default concurrency policies; document provider overrides beside each row.

Splunk Enterprise or Splunk Cloud 9.2 plus is assumed for scheduled searches, drilldowns, and optional accelerated models referenced in cimSpl.

Platform onboarding checklist for new clusters: verify kube-state-metrics version exposes required CronJob families, verify kubernetes events receiver delivers MissedSchedule reasons, verify critical_cronjobs.csv includes every production CronJob that touches money or customer data, verify alert throttles per namespace, verify runbook links for kubectl describe cronjob and kubectl get events --field-selector involvedObject.kind=CronJob, verify time zone documentation is attached to finance CronJobs, verify completed Job retention policies are understood before accusing controllers of lying.

Additional platform depth for large estates: when GitOps controllers reconcile CronJob objects from many repositories, normalize cluster naming in critical_cronjobs.csv to the same strings your prometheus relabel rules emit. When teams use Helm release names as CronJob name prefixes, decide whether lookup keys on the Kubernetes object name only or on kube_cronjob_info labels; document the decision in the runbook.

Capacity planning note: when hundreds of CronJobs share the same minute boundary, apiserver admission latency can delay lastScheduleTime across unrelated namespaces; keep scrape intervals aligned and avoid assuming a single-namespace root cause when fleet_worst_last_schedule_age_min spikes cluster-wide.

Documentation note: attach links to internal wiki pages that map business phrases such as nightly ETL to concrete namespace and cronjob object names so executives do not mis-route bridges.

FinOps note: short scrape intervals increase license cost; justify tighter intervals only for tier-one money CronJobs after cost review.

Security note: CronJob command lines may appear in object dumps; keep evidence exports free of Secret env var expansions by relying on metrics and Warning events instead of full manifest captures when possible.

Compliance note: schedule-SLO evidence often supports backup and processing continuity narratives; pair exports with change tickets when suspensions are intentional.

Training depth: teach junior responders the difference between a missed schedule event and a failed pod event using kubectl event timestamps side by side with kube_cronjob_status_last_schedule_time in metrics explorers before they open UC-3.2.10.

Vendor note: managed control planes still depend on customer VPC networking for in-cluster scrapes; verify reachability after every landing-zone change.

Observability note: dual-write periods during Splunk index migrations can duplicate rows; deduplicate alert bodies by cluster namespace cronjob hash before paging.

Runbook note: link kubectl debug guidance for stuck Jobs separately from this UC so operators do not conflate schedule-plane signals with execution-plane signals.

Architecture note: when CronJobs trigger Jobs that fan out to external queues, lastSuccessfulTime may reflect Kubernetes completion while business SLAs still fail; extend lookup columns with external_checkpoint when finance demands end-to-end proof.

Governance note: expected_concurrency_policy must reflect Git truth, not only live cluster discovery, or drift alerts become noise during intentional hot fixes.

Escalation note: critical severity rows should include owner_team and tier in the ticket title to reduce bridge spin-up time.

Review note: after Kubernetes minor upgrades, revalidate whether FailedNeedsStart still appears for your distribution; some vendors consolidate messages.

Integration note: service meshes and sidecar injection can delay Job pod ready time enough to overlap Forbid windows without OOM; document mesh class in the lookup when relevant.

Backup note: etcd restore drills can reset CronJob status timestamps; treat sudden youth in last_schedule_time as expected during DR exercises and annotate should_be_running accordingly.

Patch note: kube-controller-manager image bumps belong in the same change record as alert threshold reviews when schedule behavior changes.

Observability sampling note: if metrics are downsampled, widen stale_mult slightly rather than disabling the control entirely.

Executive note: translate schedule ages into calendar language in bridges; raw epoch math confuses non-platform leaders.

Closing prerequisites checklist: indexes named, kube-state-metrics CronJob metric families enumerated, critical_cronjobs.csv schema documented, boundaries versus UC-3.2.20, UC-3.2.6, and UC-3.2.39 restated, CIM Application_State plus Performance rationale captured for reviewers who ask why the analytic touches those models.

### Step 2 — Configure data collection

Deploy kube-state-metrics with cluster-scoped RBAC that can list CronJobs and Jobs. Point Splunk OpenTelemetry Collector prometheus receiver at the kube-state-metrics Service on port 8080 or 8443 depending on your chart, preserve namespace, cronjob, cluster, concurrency_policy, and schedule labels through relabel_config blocks, and export to HEC into index=k8s_metrics with sourcetype prometheus:scrape:metrics. Mirror other cat-3 collector hygiene: bearer_token_file for kubelet scrapes is separate from in-cluster kube-state-metrics HTTP scraping.

Concrete ServiceMonitor style reference:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-cron
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  endpoints:
    - port: http-metrics
      interval: 30s
      path: /metrics
```

OpenTelemetry Collector fragment showing prometheus scrape plus kubernetes events export:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: kube-state-metrics
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              action: keep
              regex: kube-state-metrics
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s
    sourcetype: kube:events
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      exporters: [splunk_hec/metrics]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
```

critical_cronjobs.csv sample schema:

```csv
cluster,namespace,cronjob_name,expected_cadence_minutes,owner_team,tier,should_be_running,expected_concurrency_policy
prod-eks-us-east-1,finance-dw,nightly-etl-0200,1440,finance-data,prod,1,forbid
prod-eks-us-east-1,platform-security,cert-renew-hourly,60,platform-security,prod,1,forbid
lab-gke-west,qa-batch,smoke-cron,15,qa,dev,1,allow
```

Validate raw signal presence before alerts: index=k8s_metrics kube_cronjob_status_last_schedule_time earliest=-30m, index=k8s_metrics kube_cronjob_status_last_successful_time earliest=-30m, index=k8s sourcetype=kube:events MissedSchedule earliest=-24h. Skew between scrapes and API events must stay under sixty seconds for meaningful joins.

props.conf guidance: normalize __name__, value, namespace, cronjob, and metric_name fields onto indexed extractions where volume warrants; keep coalesce ladders in SPL until extractions stabilize.

Security: redact internal volume handles from collector debug logs. Restrict k8s_audit to roles that need attribution.

Cloud control planes: on EKS verify security groups still allow node to cluster IP reachability for metrics after landing-zone changes; on GKE verify managed Prometheus if you offloaded scrapes; on AKS verify managed Grafana agent label mapping still populates cronjob.

Frequency: scrape interval, alert interval, and expected_cadence_minutes must align mathematically; a fifteen-minute cadence with five-minute scrapes and a five-minute alert schedule is the minimum sane pairing for tier-one schedule-SLO reviews.

Back-pressure: if kube-apiserver event watch disconnects, collector buffers should not grow unbounded; set retry and drop policies per vendor guidance.

Version pinning: record kube-state-metrics chart version in evidence packs quarterly.

Integration with kubectl: operators should still run kubectl describe cronjob for instantaneous truth; Splunk carries history and correlation that kubectl alone lacks across clusters.

Dashboard seeds: timechart of last_schedule_age_min for governed CronJobs, single value of fleet_worst_last_schedule_age_min from a clone search, and table of this UC output for executive summaries.

Summary index optional: materialize five-minute snapshots of last_sched_epoch and last_succ_epoch into k8s_cron_lateness_summary when raw k8s_metrics scan costs dominate.

Extended validation note for multi-team platforms: before promoting alerts, compare kube_cronjob_status_last_schedule_time against kubectl get cronjob -o jsonpath for lastScheduleTime for three representative namespaces; mismatches usually mean label extraction drift or dual scrape duplication, not true missed schedules.

Closing data collection checklist: ServiceMonitor or scrape job live, events pipeline live, CSV published, validation searches green, collector TLS verified, deduplication story documented when dual agents scrape the same targets.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_29_kube_cronjob_lateness_missed_schedule_sla with five-minute schedule, dispatch earliest=-8h@m, dispatch latest=now, and throttle duplicate pages per cluster, namespace, and cronjob for thirty minutes unless severity escalates from high to critical. Attach drilldown searches to kube:events for the same involvedObject and to UC-3.2.20 only after you confirm child Jobs exist and failed, not when no Job was created.

Understanding the pipeline: the opening comment lists tunables so on-call engineers retune without opening this document. The tstats join against Performance provides a correlation tick required by the CIM overlay narrative. multisearch fans a kube-state-metrics CronJob metric arm and a kube_job_owner arm so parent-child linkage stays visible when active Jobs exist. Each arm ends with stats latest by cluster, namespace, and cronjob so rows collapse before outer coalesce ladders run. coalesce normalizes null epochs to zero only after distinct metric kinds are split inside the metric arm.

The critical_cronjobs inputlookup join adds expected_cadence_minutes, owner_team, tier, should_be_running, and expected_concurrency_policy for governance-aware severity. The kube:events join counts MissedSchedule and FailedNeedsStart warnings for CronJob involved objects. stale_mult defaults to 2.12 so a nightly job may absorb more than one missed scrape window before paging while still catching fourteen-day ETL silence. streamstats compares successive kube_cronjob_metadata_resource_version and last_schedule_age_min samples per cronjob to expose manifest edits, clock repairs, and daylight-saving discontinuities. eventstats max(last_schedule_age_min) by cluster surfaces fleet skew when every CronJob slips together after scheduler or apiserver incidents.

case implements severity: production tier escalates schedule SLA breaches, proof staleness with breached schedules, repeated missed events, wrongful suspends, Forbid stalls, and deadline pressure. The closing table lists seventeen analyst columns for drilldowns: cluster, namespace, cronjob, spec_schedule_token, expected_cadence_minutes, last_schedule_age_min, last_success_age_min, success_lag_after_schedule_min, kube_cronjob_status_active, kube_cronjob_spec_suspend, kube_cronjob_spec_starting_deadline_seconds, missed_schedule_evt_cnt, failed_needs_start_evt_cnt, forbid_stall, concurrency_policy_live, severity, owner_team, lateness_summary, fleet_worst_last_schedule_age_min.

cimSpl in the JSON field mirrors Application_State and Performance tstats usage for environments that map Kubernetes nodes into Performance.host; adapt nodename filters to your Common Information Model implementation.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.29 CronJob lateness, missed-schedule, schedule-SLA breach axis (NOT container exit/backoff failures — see UC-3.2.20). Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookup critical_cronjobs.csv; stale_mult=2.12 skew_warn_min=30; earliest=-8h@m latest=now")`
| eval join_key="uc3229"
| join type=left join_key [
| tstats count AS perf_cron_tick FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-8h@h latest=now
| eval join_key="uc3229"
]
| fields - join_key perf_cron_tick
| eval stale_mult=2.12
| eval skew_warn_min=30
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-8h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "cronjob=\\\"(?<cronjob>[^\\\"]+)\\\""
      | rex field=_raw "concurrency_policy=\\\"(?<concurrency_policy>[^\\\"]+)\\\""
      | rex field=_raw "schedule=\\\"(?<spec_schedule_token>[^\\\"]*)\\\""
      | where like(mn,"%kube_cronjob_status_last_schedule_time%") OR like(mn,"%kube_cronjob_status_last_successful_time%") OR like(mn,"%kube_cronjob_spec_schedule%") OR like(mn,"%kube_cronjob_spec_starting_deadline_seconds%") OR like(mn,"%kube_cronjob_spec_suspend%") OR like(mn,"%kube_cronjob_metadata_resource_version%") OR like(mn,"%kube_cronjob_status_active%")
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval mv=tonumber(mval,10)
      | eval last_sched_epoch=if(like(mn,"%kube_cronjob_status_last_schedule_time%"),mv,null())
      | eval last_succ_epoch=if(like(mn,"%kube_cronjob_status_last_successful_time%"),mv,null())
      | eval kube_cronjob_spec_starting_deadline_seconds=if(like(mn,"%kube_cronjob_spec_starting_deadline_seconds%"),mv,null())
      | eval kube_cronjob_spec_suspend=if(like(mn,"%kube_cronjob_spec_suspend%"),mv,null())
      | eval kube_cronjob_metadata_resource_version=if(like(mn,"%kube_cronjob_metadata_resource_version%"),mv,null())
      | eval kube_cronjob_status_active=if(like(mn,"%kube_cronjob_status_active%"),mv,null())
      | stats latest(_time) AS metric_time latest(last_sched_epoch) AS last_sched_epoch latest(last_succ_epoch) AS last_succ_epoch latest(kube_cronjob_spec_starting_deadline_seconds) AS kube_cronjob_spec_starting_deadline_seconds latest(kube_cronjob_spec_suspend) AS kube_cronjob_spec_suspend latest(kube_cronjob_metadata_resource_version) AS kube_cronjob_metadata_resource_version latest(kube_cronjob_status_active) AS kube_cronjob_status_active latest(spec_schedule_token) AS spec_schedule_token latest(concurrency_policy) AS concurrency_policy BY cluster namespace cronjob ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-8h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "job_name=\\\"(?<job_name>[^\\\"]+)\\\""
      | rex field=_raw "owner_name=\\\"(?<owner_cronjob>[^\\\"]+)\\\""
      | where like(mn,"%kube_job_owner%") AND match(_raw,"owner_kind=\\\"CronJob\\\"")
      | stats dc(job_name) AS kube_job_owner_child_dc latest(_time) AS job_owner_metric_time BY cluster namespace owner_cronjob
      | rename owner_cronjob AS cronjob ]
| stats latest(metric_time) AS metric_time latest(last_sched_epoch) AS last_sched_epoch latest(last_succ_epoch) AS last_succ_epoch latest(kube_cronjob_spec_starting_deadline_seconds) AS kube_cronjob_spec_starting_deadline_seconds latest(kube_cronjob_spec_suspend) AS kube_cronjob_spec_suspend latest(kube_cronjob_metadata_resource_version) AS kube_cronjob_metadata_resource_version latest(kube_cronjob_status_active) AS kube_cronjob_status_active latest(spec_schedule_token) AS spec_schedule_token latest(concurrency_policy) AS concurrency_policy latest(job_owner_metric_time) AS job_owner_metric_time latest(kube_job_owner_child_dc) AS kube_job_owner_child_dc BY cluster namespace cronjob
| eval cluster=coalesce(nullif(trim(cluster),""),"unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace),""),"unknown-namespace")
| eval cronjob=coalesce(nullif(trim(cronjob),""),"unknown-cronjob")
| eval last_sched_epoch=coalesce(last_sched_epoch,0)
| eval last_succ_epoch=coalesce(last_succ_epoch,0)
| eval kube_cronjob_spec_starting_deadline_seconds=coalesce(kube_cronjob_spec_starting_deadline_seconds,0)
| eval kube_cronjob_spec_suspend=coalesce(kube_cronjob_spec_suspend,0)
| eval kube_cronjob_metadata_resource_version=coalesce(kube_cronjob_metadata_resource_version,"0")
| eval kube_cronjob_status_active=coalesce(kube_cronjob_status_active,0)
| eval kube_job_owner_child_dc=coalesce(kube_job_owner_child_dc,0)
| eval now_wall=now()
| eval last_schedule_age_min=if(last_sched_epoch>1, round((now_wall-last_sched_epoch)/60,3), null())
| eval last_success_age_min=if(last_succ_epoch>1, round((now_wall-last_succ_epoch)/60,3), null())
| eval success_lag_after_schedule_min=if(last_sched_epoch>1 AND last_succ_epoch>1 AND last_sched_epoch>last_succ_epoch, round((last_sched_epoch-last_succ_epoch)/60,3), null())
| join type=left max=0 cluster namespace cronjob [
    | inputlookup critical_cronjobs.csv
    | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
    | eval namespace=trim(toString(namespace))
    | eval cronjob=trim(toString(coalesce(cronjob_name, cronjob, name, workload_name, "")))
    | eval expected_cadence_minutes=tonumber(trim(toString(coalesce(expected_cadence_minutes, schedule_minutes, cadence_min, "1440"))),10)
    | eval owner_team=trim(toString(coalesce(owner_team, squad, pagerduty_service, "")))
    | eval tier=lower(trim(toString(coalesce(tier, workload_tier, env_tier, "dev"))))
    | eval should_be_running=tonumber(trim(toString(coalesce(should_be_running, active_expected, "1"))),10)
    | eval expected_concurrency_policy=lower(trim(toString(coalesce(expected_concurrency_policy, concurrency_expect, ""))))
    | fields cluster namespace cronjob expected_cadence_minutes owner_team tier should_be_running expected_concurrency_policy ]
| fillnull value=1440 expected_cadence_minutes
| fillnull value=1 should_be_running
| fillnull value="unassigned" owner_team
| fillnull value="dev" tier
| join type=left max=0 cluster namespace cronjob [
    search index=k8s sourcetype="kube:events" earliest=-8h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, "")))
      | eval cronjob=trim(toString(coalesce(involvedObject.name, involvedObject_name, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval k=trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, "")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where k="CronJob" AND rs IN ("MissedSchedule","FailedNeedsStart")
      | eval miss_hit=if(rs="MissedSchedule",1,0)
      | eval fns_hit=if(rs="FailedNeedsStart",1,0)
      | stats sum(miss_hit) AS missed_schedule_evt_cnt sum(fns_hit) AS failed_needs_start_evt_cnt max(_time) AS last_cron_warning_evt BY cluster namespace cronjob ]
| fillnull value=0 missed_schedule_evt_cnt
| fillnull value=0 failed_needs_start_evt_cnt
| eval stale_after_min=expected_cadence_minutes*stale_mult
| eval schedule_sla_breach=if(should_be_running=1 AND isnotnull(last_schedule_age_min) AND last_schedule_age_min>stale_after_min,1,0)
| eval success_proof_stale=if(should_be_running=1 AND (last_succ_epoch<=1 OR isnull(last_success_age_min) OR last_success_age_min>stale_after_min),1,0)
| eval never_scheduled_yet=if(should_be_running=1 AND (last_sched_epoch<=1 OR isnull(last_schedule_age_min)),1,0)
| eval bad_suspend=if(should_be_running=1 AND kube_cronjob_spec_suspend=1,1,0)
| eval concurrency_policy_live=lower(trim(toString(coalesce(concurrency_policy, "unknown"))))
| eval concurrency_drift=if(len(expected_concurrency_policy)>0 AND len(concurrency_policy_live)>0 AND expected_concurrency_policy!=concurrency_policy_live,1,0)
| eval forbid_stall=if(match(concurrency_policy_live,"forbid") AND kube_cronjob_status_active>=1 AND missed_schedule_evt_cnt>=1 AND coalesce(last_schedule_age_min,0)>(0.45*expected_cadence_minutes),1,0)
| eval owner_link_gap=if(kube_job_owner_child_dc=0 AND kube_cronjob_status_active>=1,1,0)
| eval deadline_pressure=if(kube_cronjob_spec_starting_deadline_seconds>0 AND failed_needs_start_evt_cnt>0,1,0)
| sort 0 cluster namespace cronjob metric_time
| streamstats current=f last(kube_cronjob_metadata_resource_version) AS prev_resource_version last(last_schedule_age_min) AS prev_last_sched_age BY cluster namespace cronjob
| eval resource_version_changed=if(prev_resource_version!=kube_cronjob_metadata_resource_version,1,0)
| eval schedule_age_jump_min=if(isnotnull(last_schedule_age_min) AND isnotnull(prev_last_sched_age), round(abs(last_schedule_age_min-prev_last_sched_age),3), null())
| eventstats max(last_schedule_age_min) AS fleet_worst_last_schedule_age_min BY cluster
| eval cluster_skew_warn=if(isnotnull(fleet_worst_last_schedule_age_min) AND isnotnull(last_schedule_age_min) AND (last_schedule_age_min+skew_warn_min)<fleet_worst_last_schedule_age_min,1,0)
| eval severity=case(
    never_scheduled_yet=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    schedule_sla_breach=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    success_proof_stale=1 AND schedule_sla_breach=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    missed_schedule_evt_cnt>=3 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    bad_suspend=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "high",
    forbid_stall=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "high",
    deadline_pressure=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "high",
    schedule_sla_breach=1, "high",
    success_proof_stale=1, "high",
    missed_schedule_evt_cnt>=1, "medium",
    failed_needs_start_evt_cnt>=1, "medium",
    forbid_stall=1, "medium",
    concurrency_drift=1, "medium",
    cluster_skew_warn=1, "medium",
    never_scheduled_yet=1, "medium",
    true(), "low")
| where schedule_sla_breach=1 OR success_proof_stale=1 OR missed_schedule_evt_cnt>0 OR failed_needs_start_evt_cnt>0 OR bad_suspend=1 OR forbid_stall=1 OR never_scheduled_yet=1 OR concurrency_drift=1 OR cluster_skew_warn=1 OR deadline_pressure=1 OR (resource_version_changed=1 AND (never_scheduled_yet=1 OR missed_schedule_evt_cnt>0 OR failed_needs_start_evt_cnt>0 OR schedule_sla_breach=1 OR success_proof_stale=1 OR bad_suspend=1 OR forbid_stall=1))
| eval lateness_summary=printf("sched_age=%s succ_age=%s miss_ev=%u fns_ev=%u suspend=%u forbid=%u", coalesce(tostring(last_schedule_age_min),"na"), coalesce(tostring(last_success_age_min),"na"), missed_schedule_evt_cnt, failed_needs_start_evt_cnt, kube_cronjob_spec_suspend, forbid_stall)
| table cluster namespace cronjob spec_schedule_token expected_cadence_minutes last_schedule_age_min last_success_age_min success_lag_after_schedule_min kube_cronjob_status_active kube_cronjob_spec_suspend kube_cronjob_spec_starting_deadline_seconds missed_schedule_evt_cnt failed_needs_start_evt_cnt forbid_stall concurrency_policy_live severity owner_team lateness_summary fleet_worst_last_schedule_age_min
```

Alert actions should include cluster, namespace, cronjob, severity, owner_team, lateness_summary, missed_schedule_evt_cnt, and failed_needs_start_evt_cnt in email or ITSI notable bodies. Provide a drilldown that runs index=k8s sourcetype=kube:events involvedObject.kind=CronJob involvedObject.name=$cronjob$ earliest=-8h. Provide a secondary drilldown for kubectl audit when index=k8s_audit is populated.

Performance: if Job Inspector warns on multisearch cost, split fleet dashboards into per-region saved searches or materialize CronJob timestamp snapshots hourly.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two consecutive intervals of schedule_sla_breach before paging scrape outages unless kube:events still show MissedSchedule.

Governance: weekly CSV export of alert rows with lookup commit hash satisfies internal platform evidence when paired with kube-state-metrics version stamps.

savedsearches.conf quantity thresholds should align with row counts from the table command; use alert.track=1 and suppress keys on cluster namespace cronjob.

Closing Step 3 checklist: fenced SPL present, matches spl field, references critical_cronjobs.csv, explains tstats join purpose, documents multisearch arms, clarifies schedule SLA math, and names notification fields.

### Step 4 — Validate

Synthetic schedule breach: in lab namespace qa-cron-lateness-3229 patch a governed CronJob to use an intentionally fast schedule while lowering expected_cadence_minutes in the lookup to a few minutes, stop the controller-manager or block CronJob reconciliation only in a disposable lab under change control, confirm last_schedule_age_min crosses stale_after_min, and expect schedule_sla_breach equals one with severity at least high.

Synthetic MissedSchedule narrative: simulate Forbid concurrency with a long-running Job Pod so the next window skips, confirm kube:events emit MissedSchedule, confirm missed_schedule_evt_cnt rises, and expect forbid_stall logic to classify the row when active child Jobs remain.

Synthetic suspend mismatch: kubectl patch a governed CronJob to spec.suspend true while should_be_running remains one in the CSV, confirm bad_suspend drives severity, then revert the patch and confirm rows clear.

Negative test: run a healthy minutely CronJob with short Jobs, should_be_running=1, correct expected_cadence_minutes, and matching time zone documentation; confirm last_schedule_age_min stays below the stale gate for forty minutes and no qualifying rows appear without intentional injects.

Field sanity: rename a forwarder field to camelCase-only in a sandbox and verify coalesce still resolves namespace labels.

RBAC: readers without k8s_metrics access must see zero rows.

Correlation: compare Splunk timestamps to kubectl describe cronjob and kubectl get events for the same minute.

Validation SPL for raw metrics presence:

| multisearch [
    [ search index=k8s_metrics earliest=-30m latest=now kube_cronjob_status_last_schedule_time | stats count ]
    [ search index=k8s_metrics earliest=-30m latest=now kube_cronjob_status_last_successful_time | stats count ]
  ]
| stats sum(count) AS samples

Tear-down: delete lab CronJobs, revert patches, and confirm saved search result counts return to zero.

Audit drill: index=k8s_audit sourcetype=kube:audit objectRef.resource=cronjobs verb=patch OR verb=update earliest=-2h to recover actors for suspend, deadline, timeZone, or concurrency changes.

Clock skew: verify NTP alignment between nodes, kube-apiserver, and Splunk indexers; skew beyond ninety seconds invalidates last_schedule_age_min comparisons.

Documentation: attach kubectl describe excerpts to the evidence ticket without exposing Secret material.

Closing Step 4 checklist: positive schedule breach scenario, positive missed-schedule scenario, negative healthy cron scenario, metrics presence multisearch, audit correlation note, tear-down verified, clock skew warning documented.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Fourteen-day silent ETL miss with flat infrastructure dashboards
Confirm spec.suspend, spec.timeZone, and lookup should_be_running; compare last_schedule_age_min to finance intent; recover controller-manager health; open UC-3.2.20 only if child Jobs exist with failures.

Case 2 — Certificate renewal CronJob emits no Job objects
Read kube:events for FailedNeedsStart and validation errors; kubectl describe cronjob for illegal schedule strings; fix spec then verify kube_cronjob_status_active increments.

Case 3 — concurrencyPolicy Forbid with a hung previous Job
Identify kube_cronjob_status_active and live Job Pods; terminate the stuck Job only under CAB; document legitimate long runs in the lookup to tune expected_cadence_minutes.

Case 4 — Fleet-wide thirty-minute lateness after control-plane incident
Use fleet_worst_last_schedule_age_min and cluster_skew_warn patterns; pivot to UC-3.2.7 style control-plane health reviews when every namespace slips together.

Case 5 — spec.timeZone added in v1.27 shifts local 02:00 intent versus UTC observers
Reconcile critical_cronjobs.csv expectations with documented zone; train finance that Splunk age math is UTC unless you normalize with a business calendar macro.

Case 6 — startingDeadlineSeconds shorter than maintenance or blackout windows
Expect FailedNeedsStart counts to rise without Pod failures; widen deadlines only after architecture review, not only to silence alerts.

Case 7 — Completed Job reaped by ttlSecondsAfterFinished while lastSuccessfulTime lags
Cross-check kube_cronjob_status_last_successful_time against apiserver; increase history or ttl only when policy allows; avoid accusing applications of success when metrics lag.

Case 8 — kube_job_owner_child_dc disagrees with kube_cronjob_status_active
Investigate ownerReference mismatches, orphaned Jobs, or label extraction drift on job_name; fix Prometheus relabel rules before muting.

Case 9 — GitOps suspend via Argo CD during DR test
Set should_be_running=0 for the DR window in critical_cronjobs.csv and attach the change ticket to weekly evidence exports.

Case 10 — Spring-forward DST creates a perceived missed hour
Compare schedule_age_jump_min from streamstats to calendar; require dual evidence from MissedSchedule before executive escalation on the single skipped instant.

Case 11 — Replace policy thundering herd after recovery
Latency may spike without schedule breach; use this UC for schedule ages while watching node saturation via Performance dashboards referenced in cimSpl.

Case 12 — Parser errors on cron schedule strings after edit
Validate kubectl apply output; expect never_scheduled_yet with resource_version_changed; roll back malformed spec.schedule before tuning Splunk thresholds.

Dashboard hygiene: keep a panel for missed_schedule_evt_cnt by namespace and overlay UC-3.2.39 only when the burst is fleet-wide noise rather than CronJob-specific warnings.

Evidence retention: archive weekly CSV exports with kube-state-metrics chart version, collector digest, and Splunk search head cluster name.

Training replay: twice-yearly game day that combines MissedSchedule storms with controller downtime to prove operators open this UC before reopening UC-3.2.6 tickets.

Cloud nuances: managed Kubernetes control planes still expose the same kube-state-metrics families when you scrape inside the customer VPC; verify scrape paths when cloud networking policies change.

Governance: when legal requests preservation, include hashed CronJob manifests rather than raw Secret-laden YAML in tickets.

Performance note: if inputlookup critical_cronjobs.csv grows beyond ten thousand rows, migrate to KV Store with automatic filter on cluster before join.

Fleet operations note: publish a clone saved search that filters severity IN ("critical","high") before the table command for paging while keeping the fleet dashboard unfiltered.

Executive storytelling note: translate lateness_summary into customer impact language; executives rarely parse Prometheus label semantics on first read.

Operator wellbeing note: pair this alert with shift handoff templates so secondary responders inherit schedule age deltas without re-running full SPL manually.

Closing Step 5 checklist: twelve cases present with exact Case N — formatting, cross-links to related UCs by number where troubleshooting pivots, dashboard and evidence notes for long-term operations, and explicit reminder that Job execution failure analytics remain UC-3.2.20.

## SPL

```spl
`comment("UC-3.2.29 CronJob lateness, missed-schedule, schedule-SLA breach axis (NOT container exit/backoff failures — see UC-3.2.20). Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookup critical_cronjobs.csv; stale_mult=2.12 skew_warn_min=30; earliest=-8h@m latest=now")`
| eval join_key="uc3229"
| join type=left join_key [
| tstats count AS perf_cron_tick FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-8h@h latest=now
| eval join_key="uc3229"
]
| fields - join_key perf_cron_tick
| eval stale_mult=2.12
| eval skew_warn_min=30
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-8h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "cronjob=\\\"(?<cronjob>[^\\\"]+)\\\""
      | rex field=_raw "concurrency_policy=\\\"(?<concurrency_policy>[^\\\"]+)\\\""
      | rex field=_raw "schedule=\\\"(?<spec_schedule_token>[^\\\"]*)\\\""
      | where like(mn,"%kube_cronjob_status_last_schedule_time%") OR like(mn,"%kube_cronjob_status_last_successful_time%") OR like(mn,"%kube_cronjob_spec_schedule%") OR like(mn,"%kube_cronjob_spec_starting_deadline_seconds%") OR like(mn,"%kube_cronjob_spec_suspend%") OR like(mn,"%kube_cronjob_metadata_resource_version%") OR like(mn,"%kube_cronjob_status_active%")
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval mv=tonumber(mval,10)
      | eval last_sched_epoch=if(like(mn,"%kube_cronjob_status_last_schedule_time%"),mv,null())
      | eval last_succ_epoch=if(like(mn,"%kube_cronjob_status_last_successful_time%"),mv,null())
      | eval kube_cronjob_spec_starting_deadline_seconds=if(like(mn,"%kube_cronjob_spec_starting_deadline_seconds%"),mv,null())
      | eval kube_cronjob_spec_suspend=if(like(mn,"%kube_cronjob_spec_suspend%"),mv,null())
      | eval kube_cronjob_metadata_resource_version=if(like(mn,"%kube_cronjob_metadata_resource_version%"),mv,null())
      | eval kube_cronjob_status_active=if(like(mn,"%kube_cronjob_status_active%"),mv,null())
      | stats latest(_time) AS metric_time latest(last_sched_epoch) AS last_sched_epoch latest(last_succ_epoch) AS last_succ_epoch latest(kube_cronjob_spec_starting_deadline_seconds) AS kube_cronjob_spec_starting_deadline_seconds latest(kube_cronjob_spec_suspend) AS kube_cronjob_spec_suspend latest(kube_cronjob_metadata_resource_version) AS kube_cronjob_metadata_resource_version latest(kube_cronjob_status_active) AS kube_cronjob_status_active latest(spec_schedule_token) AS spec_schedule_token latest(concurrency_policy) AS concurrency_policy BY cluster namespace cronjob ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-8h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "job_name=\\\"(?<job_name>[^\\\"]+)\\\""
      | rex field=_raw "owner_name=\\\"(?<owner_cronjob>[^\\\"]+)\\\""
      | where like(mn,"%kube_job_owner%") AND match(_raw,"owner_kind=\\\"CronJob\\\"")
      | stats dc(job_name) AS kube_job_owner_child_dc latest(_time) AS job_owner_metric_time BY cluster namespace owner_cronjob
      | rename owner_cronjob AS cronjob ]
| stats latest(metric_time) AS metric_time latest(last_sched_epoch) AS last_sched_epoch latest(last_succ_epoch) AS last_succ_epoch latest(kube_cronjob_spec_starting_deadline_seconds) AS kube_cronjob_spec_starting_deadline_seconds latest(kube_cronjob_spec_suspend) AS kube_cronjob_spec_suspend latest(kube_cronjob_metadata_resource_version) AS kube_cronjob_metadata_resource_version latest(kube_cronjob_status_active) AS kube_cronjob_status_active latest(spec_schedule_token) AS spec_schedule_token latest(concurrency_policy) AS concurrency_policy latest(job_owner_metric_time) AS job_owner_metric_time latest(kube_job_owner_child_dc) AS kube_job_owner_child_dc BY cluster namespace cronjob
| eval cluster=coalesce(nullif(trim(cluster),""),"unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace),""),"unknown-namespace")
| eval cronjob=coalesce(nullif(trim(cronjob),""),"unknown-cronjob")
| eval last_sched_epoch=coalesce(last_sched_epoch,0)
| eval last_succ_epoch=coalesce(last_succ_epoch,0)
| eval kube_cronjob_spec_starting_deadline_seconds=coalesce(kube_cronjob_spec_starting_deadline_seconds,0)
| eval kube_cronjob_spec_suspend=coalesce(kube_cronjob_spec_suspend,0)
| eval kube_cronjob_metadata_resource_version=coalesce(kube_cronjob_metadata_resource_version,"0")
| eval kube_cronjob_status_active=coalesce(kube_cronjob_status_active,0)
| eval kube_job_owner_child_dc=coalesce(kube_job_owner_child_dc,0)
| eval now_wall=now()
| eval last_schedule_age_min=if(last_sched_epoch>1, round((now_wall-last_sched_epoch)/60,3), null())
| eval last_success_age_min=if(last_succ_epoch>1, round((now_wall-last_succ_epoch)/60,3), null())
| eval success_lag_after_schedule_min=if(last_sched_epoch>1 AND last_succ_epoch>1 AND last_sched_epoch>last_succ_epoch, round((last_sched_epoch-last_succ_epoch)/60,3), null())
| join type=left max=0 cluster namespace cronjob [
    | inputlookup critical_cronjobs.csv
    | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
    | eval namespace=trim(toString(namespace))
    | eval cronjob=trim(toString(coalesce(cronjob_name, cronjob, name, workload_name, "")))
    | eval expected_cadence_minutes=tonumber(trim(toString(coalesce(expected_cadence_minutes, schedule_minutes, cadence_min, "1440"))),10)
    | eval owner_team=trim(toString(coalesce(owner_team, squad, pagerduty_service, "")))
    | eval tier=lower(trim(toString(coalesce(tier, workload_tier, env_tier, "dev"))))
    | eval should_be_running=tonumber(trim(toString(coalesce(should_be_running, active_expected, "1"))),10)
    | eval expected_concurrency_policy=lower(trim(toString(coalesce(expected_concurrency_policy, concurrency_expect, ""))))
    | fields cluster namespace cronjob expected_cadence_minutes owner_team tier should_be_running expected_concurrency_policy ]
| fillnull value=1440 expected_cadence_minutes
| fillnull value=1 should_be_running
| fillnull value="unassigned" owner_team
| fillnull value="dev" tier
| join type=left max=0 cluster namespace cronjob [
    search index=k8s sourcetype="kube:events" earliest=-8h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, "")))
      | eval cronjob=trim(toString(coalesce(involvedObject.name, involvedObject_name, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval k=trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, "")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where k="CronJob" AND rs IN ("MissedSchedule","FailedNeedsStart")
      | eval miss_hit=if(rs="MissedSchedule",1,0)
      | eval fns_hit=if(rs="FailedNeedsStart",1,0)
      | stats sum(miss_hit) AS missed_schedule_evt_cnt sum(fns_hit) AS failed_needs_start_evt_cnt max(_time) AS last_cron_warning_evt BY cluster namespace cronjob ]
| fillnull value=0 missed_schedule_evt_cnt
| fillnull value=0 failed_needs_start_evt_cnt
| eval stale_after_min=expected_cadence_minutes*stale_mult
| eval schedule_sla_breach=if(should_be_running=1 AND isnotnull(last_schedule_age_min) AND last_schedule_age_min>stale_after_min,1,0)
| eval success_proof_stale=if(should_be_running=1 AND (last_succ_epoch<=1 OR isnull(last_success_age_min) OR last_success_age_min>stale_after_min),1,0)
| eval never_scheduled_yet=if(should_be_running=1 AND (last_sched_epoch<=1 OR isnull(last_schedule_age_min)),1,0)
| eval bad_suspend=if(should_be_running=1 AND kube_cronjob_spec_suspend=1,1,0)
| eval concurrency_policy_live=lower(trim(toString(coalesce(concurrency_policy, "unknown"))))
| eval concurrency_drift=if(len(expected_concurrency_policy)>0 AND len(concurrency_policy_live)>0 AND expected_concurrency_policy!=concurrency_policy_live,1,0)
| eval forbid_stall=if(match(concurrency_policy_live,"forbid") AND kube_cronjob_status_active>=1 AND missed_schedule_evt_cnt>=1 AND coalesce(last_schedule_age_min,0)>(0.45*expected_cadence_minutes),1,0)
| eval owner_link_gap=if(kube_job_owner_child_dc=0 AND kube_cronjob_status_active>=1,1,0)
| eval deadline_pressure=if(kube_cronjob_spec_starting_deadline_seconds>0 AND failed_needs_start_evt_cnt>0,1,0)
| sort 0 cluster namespace cronjob metric_time
| streamstats current=f last(kube_cronjob_metadata_resource_version) AS prev_resource_version last(last_schedule_age_min) AS prev_last_sched_age BY cluster namespace cronjob
| eval resource_version_changed=if(prev_resource_version!=kube_cronjob_metadata_resource_version,1,0)
| eval schedule_age_jump_min=if(isnotnull(last_schedule_age_min) AND isnotnull(prev_last_sched_age), round(abs(last_schedule_age_min-prev_last_sched_age),3), null())
| eventstats max(last_schedule_age_min) AS fleet_worst_last_schedule_age_min BY cluster
| eval cluster_skew_warn=if(isnotnull(fleet_worst_last_schedule_age_min) AND isnotnull(last_schedule_age_min) AND (last_schedule_age_min+skew_warn_min)<fleet_worst_last_schedule_age_min,1,0)
| eval severity=case(
    never_scheduled_yet=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    schedule_sla_breach=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    success_proof_stale=1 AND schedule_sla_breach=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    missed_schedule_evt_cnt>=3 AND match(tier,"prod|production|gold|tier1|tier-1"), "critical",
    bad_suspend=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "high",
    forbid_stall=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "high",
    deadline_pressure=1 AND match(tier,"prod|production|gold|tier1|tier-1"), "high",
    schedule_sla_breach=1, "high",
    success_proof_stale=1, "high",
    missed_schedule_evt_cnt>=1, "medium",
    failed_needs_start_evt_cnt>=1, "medium",
    forbid_stall=1, "medium",
    concurrency_drift=1, "medium",
    cluster_skew_warn=1, "medium",
    never_scheduled_yet=1, "medium",
    true(), "low")
| where schedule_sla_breach=1 OR success_proof_stale=1 OR missed_schedule_evt_cnt>0 OR failed_needs_start_evt_cnt>0 OR bad_suspend=1 OR forbid_stall=1 OR never_scheduled_yet=1 OR concurrency_drift=1 OR cluster_skew_warn=1 OR deadline_pressure=1 OR (resource_version_changed=1 AND (never_scheduled_yet=1 OR missed_schedule_evt_cnt>0 OR failed_needs_start_evt_cnt>0 OR schedule_sla_breach=1 OR success_proof_stale=1 OR bad_suspend=1 OR forbid_stall=1))
| eval lateness_summary=printf("sched_age=%s succ_age=%s miss_ev=%u fns_ev=%u suspend=%u forbid=%u", coalesce(tostring(last_schedule_age_min),"na"), coalesce(tostring(last_success_age_min),"na"), missed_schedule_evt_cnt, failed_needs_start_evt_cnt, kube_cronjob_spec_suspend, forbid_stall)
| table cluster namespace cronjob spec_schedule_token expected_cadence_minutes last_schedule_age_min last_success_age_min success_lag_after_schedule_min kube_cronjob_status_active kube_cronjob_spec_suspend kube_cronjob_spec_starting_deadline_seconds missed_schedule_evt_cnt failed_needs_start_evt_cnt forbid_stall concurrency_policy_live severity owner_team lateness_summary fleet_worst_last_schedule_age_min
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-8h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS cim_host Application_State.app AS cim_app
| join type=left max=0 cim_host [
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu latest(Performance.mem_used_percent) AS mem_used FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-8h@h latest=@h BY Performance.host
| rename Performance.host AS cim_host ]
| where len(cim_host)>0
| table cim_host cim_app app_state app_info avg_cpu mem_used
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of last_schedule_age_min versus expected_cadence_minutes; single value of fleet_worst_last_schedule_age_min; heatmap of missed_schedule_evt_cnt by namespace; drilldown from lateness_summary to raw kube:events.

## Known False Positives

spec.suspend=true during approved maintenance, finance close, or disaster-recovery rehearsal should set should_be_running=0 in critical_cronjobs.csv so wrongful-suspend severity does not page. Scheduled DR-test runs that intentionally pause automation via GitOps sync should carry the same lookup flag and a change ticket id in weekly evidence exports. Holiday cron expressions that assume local time while observers watch UTC dashboards can look fourteen hours late until spec.timeZone and business calendars align; document zone intent beside each row. concurrencyPolicy=Forbid legitimately blocks the next window when a long-running prior Job still owns capacity; pair missed events with kube_cronjob_status_active before treating the skip as an incident. Recent CronJob create or spec.edit with no successful completion yet can show success_proof_stale until the first healthy Job finishes; require two intervals or a non-zero lastScheduleTime before paging brand-new objects. completed-job grace-period reaping and aggressive ttlSecondsAfterFinished can delete the only succeeded Job while kube_cronjob_status_last_successful_time still lags; verify apiserver status before blaming application code. Misconfigured @yearly or non-standard cron tokens that the apiserver rejects produce never_scheduled_yet without Pod failures; fix validation errors in kubectl describe before tuning Splunk. Daylight-saving spring-forward creates a single skipped local instant; demand corroborating MissedSchedule counts or fleet skew, not only one bucket spike. Deliberate startingDeadlineSeconds shorter than a known maintenance blackout yields FailedNeedsStart warnings by design; annotate blackout windows in the lookup rather than muting the control globally. CronJob suspended via Argo CD Application sync options should mirror should_be_running=0 for the suspension window and attach the Argo change record to the evidence bundle. Brief kube-state-metrics scrape outages after upgrades can inflate last_schedule_age_min once; require consecutive breaches or event-backed MissedSchedule before executive escalation. Batch namespaces that intentionally run only on business days need cadence columns that reflect five-day schedules, not naive 1440-minute multiples, or stale math will false alarm every weekend.

## References

- [Kubernetes — CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Kubernetes API — CronJob v1](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/cron-job-v1/)
- [KEP-4367 — Support TimeZone field for CronJobs](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/)
- [kube-state-metrics — CronJob metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/cronjob-metrics.md)
- [Kubernetes — Events in cluster (MissedSchedule source path)](https://kubernetes.io/docs/concepts/overview/working-with-objects/)
- [Kubernetes scheduling — scheduler design documentation](https://kubernetes.io/docs/concepts/scheduling-eviction/)
- [Kubernetes community — sig-apps (CronJob controller ownership)](https://github.com/kubernetes/community/blob/master/sig-apps/README.md)
- [Amazon EKS — Batch and job workloads](https://docs.aws.amazon.com/eks/latest/userguide/batch-jobs.html)
- [Google Cloud — Run CronJobs on GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/cronjobs)
- [Microsoft Learn — Run CronJobs on Azure Kubernetes Service](https://learn.microsoft.com/en-us/azure/aks/)
