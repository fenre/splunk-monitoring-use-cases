---
title: Cloud & Containers Monitoring Domain Guide
type: domain-guide
domains: [Cloud, Containers]
categories: [3, 4, 20]
last_updated: 2026-04-30
---

# Cloud & Containers Monitoring Domain Guide

This guide situates the **cloud-native** slice of the Splunk monitoring catalog: container runtimes and orchestrators, hyperscaler control planes, multi-cloud posture, serverless footprints, and FinOps-aligned cost and capacity governance. It aligns CNCF-style observability layering, vendor-native audit and threat telemetry, and Splunk ingestion patterns so teams can prioritize signals that precede outages, credential abuse, and runaway spend.

Practitioners should read Categories **3**, **4**, and **20** together—Kubernetes saturation rarely explains a quarter’s invoice spike unless correlated with IAM changes that enabled oversized node pools or forgotten sandbox clusters left running on premium SKUs. Splunk becomes the synthesis layer where CloudTrail parity, kube-state timelines, and CUR-backed dollar traces land in one searchable timeline.

Treat missing audit delivery as an incident precursor: silent CloudTrail gaps blind FinOps reconciliation as surely as they blind SOC hunts.

Browse the domain categories directly: [Browse Containers & Orchestration](index.html#cat-3), [Browse Cloud Infrastructure](index.html#cat-4), [Browse Cost & Capacity Management](index.html#cat-20).

---

## Category 3: Containers & Orchestration (129 use cases)

Containers & Orchestration spans [Docker](index.html#cat-3/3.1) (29), [Kubernetes](index.html#cat-3/3.2) (46), [OpenShift](index.html#cat-3/3.3) (25), [Container Registries](index.html#cat-3/3.4) (9), [Service Mesh & Serverless Containers](index.html#cat-3/3.5) (14), and [Container & Kubernetes Trending](index.html#cat-3/3.6) (6). Together they capture workload lifecycle narratives—crash loops, admission failures, image supply-chain risk, mesh latency, and platform SLO regressions—that guest-only OS metrics miss when the unit of deployment is a pod, not a VM.

Brownfield clusters frequently omit etcd scraping until API latency incidents strike—prioritize backlog metrics in the first hardening sprint because incident response traffic can compound write pressure on an already degraded datastore.

### Kubernetes vendor-aligned monitoring layers (CNCF and Red Hat practice)

The Cloud Native Computing Foundation and Red Hat document monitoring as a **stack of concerns** from metal-like nodes through customer-facing SLOs. The following five layers are the industry framing teams use when they separate “platform broke” from “application misbehaved.”

**1) Node and cluster infrastructure**

- **WHAT:** Monitor kubelet/cRI health, node pressure (CPU, memory, disk, PID), eviction signals, network plugin errors, and storage CSI attach/detach latency.
- **WHY:** Workloads inherit node faults; control-plane dashboards stay green while kubelet stops reporting or the CNI blackholes traffic.
- **HOW:** Ingest node-exporter-style metrics or cloud provider node health, journald/kubelet logs, and `Node` conditions via **Splunk Connect for Kubernetes** (cluster events) and **Splunk OpenTelemetry Collector for Kubernetes** (OTLP metrics/logs). Correlate with cloud instance status when nodes are cloud VMs.

**2) Kubernetes control plane**

- **WHAT:** Track API server request latency/error rate, scheduler rate-limits, controller-manager reconciliation lag, and **etcd** health (leader elections, proposal failures, disk fsync latency, database size).
- **WHY:** etcd is the source of truth; API latency spikes often trace to etcd saturation or leader instability before user-visible symptoms appear.
- **HOW:** Prometheus-style scrapes or cloud-managed metrics exports into Splunk; for etcd specifically, monitor **backend commit duration**—[etcd documentation](https://etcd.io/docs/v3.5/op-guide/monitoring/) calls out commit latency as a primary health signal. Operational practice in the field treats **sustained commit latency above ~25 ms** as a warning that merits investigation (tune against your baseline; vendor docs emphasize trend and percentile analysis over a single universal constant). Also track **database size**, **leader changes**, and defragmentation windows. Catalog anchors: [Control Plane Health](index.html#uc-3.2.7), [etcd Cluster Health](index.html#uc-3.2.8).

**3) Workloads (pods, deployments, HPAs)**

- **WHAT:** Pod phase transitions, restart counts, scheduling latency, PDB violations, HPA saturation, and pending workload queues.
- **WHY:** These signals isolate deployment pipeline issues, resource starvation, and autoscaling misconfiguration from application code defects.
- **HOW:** Ship `kube-state-metrics` style state to Splunk; alert on **CrashLoopBackOff** with restart thresholds—common operational practice treats **more than five restarts** in a lookback window as **critical** because it indicates a non-recoverable loop rather than a single transient fault. Alert when **pods stay Pending beyond five minutes** to catch quota, taint/toleration, and volume binding failures early. Catalog touchpoints: [Pod Restart Rate](index.html#uc-3.2.1), [Container Crash Loops](index.html#uc-3.1.1), [Container Restart Loop](index.html#uc-3.1.13).

**4) Applications inside containers**

- **WHAT:** RED/USE-style app metrics, structured logs, traces, and business KPIs exported with OpenTelemetry SDKs.
- **WHY:** Platform health can be perfect while latency SLOs burn due to code regressions or dependency outages.
- **HOW:** OTel pipelines to Splunk Observability Cloud or HEC-backed indexes; unify with kube metadata (`pod`, `namespace`, `workload`) for service-centric dashboards.

**5) External endpoints and dependencies**

- **WHAT:** Synthetic probes, egress errors, DNS resolution, and TLS failures to SaaS APIs and data stores.
- **WHY:** Microservices amplify fan-out; a single DNS or certificate regression becomes a widespread incident.
- **HOW:** Combine black-box checks with mesh or core-DNS telemetry where [Istio](https://istio.io/latest/docs/tasks/observability/metrics/) / Envoy access logs feed Splunk via OTel or log sidecars.

### Prometheus and the kube-prometheus-stack as the de facto metrics baseline

- **WHAT:** Deploy **Prometheus** with **kube-prometheus-stack** (community Helm chart bundling exporters, scrape configs, and Grafana) to collect cluster and workload metrics.
- **WHY:** It is the **industry-standard** Kubernetes metrics reference implementation; Splunk teams often either federate Prometheus metrics into Splunk or run parallel OTel exporters to avoid losing community dashboards during migration.
- **HOW:** Keep scrape cardinality bounded; ship selected series to Splunk via OTel Prometheus receiver or remote-write integrations, and retain Prometheus for on-cluster troubleshooting when needed.

### Resource requests versus actual usage (cost-efficiency)

- **WHAT:** Compare `resources.requests` and `limits` to measured CPU/memory utilization from cAdvisor/kubelet or OTel host metrics.
- **WHY:** Over-requesting starves scheduling; under-requesting causes throttling and OOMs. FinOps and platform teams need the same chart to defend rightsizing.
- **HOW:** Weekly reports by namespace/team with recommender-style hints; tie reductions to change records. Pair with [Container OOM Kills](index.html#uc-3.1.2) alerts to validate that cuts do not breach headroom.

### AIOps for containerized environments

- **WHAT:** Apply multivariate anomaly detection (seasonal spend, error rates, saturation) across deployment, metric, and log features.
- **WHY:** Kubernetes failure modes are combinatorial; static thresholds miss novel interaction faults (for example, quota + image pull backoff + HPA oscillation).
- **HOW:** Splunk AI Assistant for SPL, Machine Learning Toolkit baselines, or **Splunk IT Service Intelligence** episodes correlating pod churn KPIs—optional but valuable when pager noise exceeds human triage capacity.

### Splunk ingestion paths for Kubernetes and Docker

- **Splunk Connect for Kubernetes (SCK):** collects cluster logs and Kubernetes events—essential for audit-grade timelines of scheduling and Volume failures when correlated with Splunk RBAC-aware dashboards.
- **Splunk OpenTelemetry Collector:** aligns with OpenTelemetry conventions for logs, metrics, and traces; preferred when standardizing collection across clouds and on-prem clusters ([Splunk Kubernetes OTel guidance](https://docs.splunk.com/observability/en/gdi/opentelemetry/install-k8s.html)).

Docker-centric estates still benefit from **Splunk Connect for Docker** for Engine API events and container logs where Kubernetes is absent.

### Docker-focused operational baseline (standalone Engine)

Even without an orchestrator, Docker hosts remain security- and reliability-sensitive: the Engine API and default socket permissions are high-value targets, and lifecycle events (`die`, `oom`, `kill`) tell a cleaner failure story than host-only CPU charts.

- **WHAT:** Capture `docker events` streams, container JSON logs, optional `docker stats`, and cgroup OOM markers on the Linux host.
- **WHY:** Swarm-less Docker still experiences image pull storms, restart thrash, and memory pressure visible only when container scope is retained.
- **HOW:** Modular inputs against a **hardened** socket path (never exposed to the network); pair with auditd or equivalent for access to `/var/run/docker.sock` investigations. Reinforce posture reviews with [Docker Socket Exposure](index.html#uc-3.1.25).

### OpenShift platform overlays (Red Hat)

OpenShift layers an opinionated operator model, cluster versioning, and integrated registry/Router/Ingress paths on upstream Kubernetes. Red Hat documents cluster health in terms of **Cluster Version Operator** progress, **machine** and **node** health, and **etcd** quorum—aligning with the five-layer model but adding **platform release** and **upgrade** risk dimensions per [Red Hat OpenShift Container Platform monitoring](https://docs.openshift.com/container-platform/latest/monitoring/monitoring-overview.html) guidance.

- **WHAT:** Monitor upgrade channels, ClusterOperator degraded conditions, ingress/dns availability, and registry pull success in addition to generic Kubernetes KPIs.
- **WHY:** Platform teams experience incident classes (CVO stalls, Operators flapping, Route admission failures) that do not surface on vanilla kube dashboards.
- **HOW:** Forward OpenShift API audit and platform logs into Splunk; scrape Red Hat metrics endpoints per supported patterns; anchor catalog narratives such as [OpenShift ClusterVersion Upgrade Progress and CVO Stuck Detection (Z- and Y-stream lifecycle)](index.html#uc-3.3.1).

### Container registries and supply-chain telemetry

Registries are the distribution choke point for compromised or policy-violating images.

- **WHAT:** Track push/pull volumes, authentication failures, manifest digests tagged across environments, and webhook-driven admission outcomes.
- **WHY:** Silent policy drift (public read, weak signing posture) precedes lateral movement via malicious layers.
- **HOW:** REST collectors or SCM-style webhooks normalized into Splunk—pair governance scans with catalog patterns like [Image Push/Pull Audit](index.html#uc-3.4.1) and complement with vulnerability scanner exports where SecOps consumes Splunk as the correlation hub.

### Service mesh and serverless containers — golden signals

Service meshes expose **L7 request volume, latency, error rates**, and peer identities—telemetry essential when pods churn faster than classic LB dashboards refresh.

- **WHAT:** Envoy/Istio access logs, downstream/upstream cluster metrics, and mTLS handshake failures.
- **WHY:** Network policies and retries hide systemic faults until queues saturate mesh-wide.
- **HOW:** OTel receivers shipping Prometheus exposition from Istio components; exemplar anchor [Istio Mesh Traffic Monitoring](index.html#uc-3.5.1).

Serverless containers (ECS/Fargate, Cloud Run, Azure Container Apps) shift observability toward **task lifecycle APIs**, **cold-start latency**, **platform throttle counters**, and **vendor-managed scaling decisions**.

- **WHAT:** Pull AWS/Azure/GCP metrics for CPU/mem throttle, revision/instance counts, and request concurrency ceilings.
- **WHY:** Capacity appears infinite until concurrency caps or subnet/IP exhaustion manifests as HTTP 503 storms.
- **HOW:** Mirror vendor APIs through the same **Splunk Add-on for AWS**, **Splunk Add-on for Microsoft Cloud Services**, or **Splunk Add-on for Google Cloud Platform** stacks used for Category 4—retain consistent `cloud.account` and `region` dimensions for multi-workload dashboards.

### Critical container signals — catalog anchors

| Risk | Representative UC |
|------|---------------------|
| Crash loops / unstable workloads | [Container Crash Loops](index.html#uc-3.1.1), [Pod Restart Rate](index.html#uc-3.2.1), [Container Restart Loop](index.html#uc-3.1.13) |
| Memory pressure | [Container OOM Kills](index.html#uc-3.1.2) |
| Privileged exposure | [Docker Socket Exposure](index.html#uc-3.1.25) |
| Control plane instability | [Control Plane Health](index.html#uc-3.2.7), [etcd Cluster Health](index.html#uc-3.2.8) |

---

## Category 4: Cloud Infrastructure (227 use cases)

Cloud Infrastructure spans [AWS](index.html#cat-4/4.1) (77), [Azure](index.html#cat-4/4.2) (57), [GCP](index.html#cat-4/4.3) (40), [Multi-Cloud & Cloud Management](index.html#cat-4/4.4) (31), [Serverless & FaaS](index.html#cat-4/4.5) (16), and [Cloud Infrastructure Trending](index.html#cat-4/4.6) (6). Hyperscaler telemetry centers on **who changed what**, **whether defenses fired**, and **whether delivery pipelines for audit logs broke**.

### AWS vendor-aligned practices

**AWS CloudTrail — multi-region API audit**

- **WHAT:** Capture management events across **all used regions**, including global IAM and STS narratives, with organization trails where applicable.
- **WHY:** Attackers pivot region-to-region; investigations fail if logs are incomplete. [AWS CloudTrail documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html) emphasizes trail configuration and integrity.
- **HOW:** Forward CloudTrail S3 buckets or CloudWatch Logs subscriptions into Splunk via **Splunk Add-on for AWS**; normalize `eventName`, `userIdentity`, `sourceIPAddress`, and `errorCode` fields for detections and dashboards.

**Amazon GuardDuty — intelligent threat detection**

- **WHAT:** Ingest GuardDuty findings ( IAM, VPC, malware, Kubernetes, S3 protections as enabled).
- **WHY:** Augments rule-based SIEM logic with AWS-native anomaly and threat intelligence.
- **HOW:** SNS → SQS or EventBridge fan-out into Splunk; severity and type drive SOAR playbooks—see also [GuardDuty Finding Ingestion](index.html#uc-4.1.8).

**CloudWatch metrics with Splunk**

- **WHAT:** Pull service-level CloudWatch metrics (ELB target health, Lambda throttles, RDS) into Splunk for unified SLO dashboards.
- **WHY:** Operators need capacity and saturation next to audit data.
- **HOW:** TA pollers or Kinesis/Data Firehose streams; tune pull intervals against API limits documented by AWS.

**Cost and usage transparency**

- **WHAT:** Combine **AWS Cost Explorer** curated views with **Cost and Usage Reports (CUR)** detail for Splunk-backed allocation.
- **WHY:** CUR supports chargeback tags and hourly granularity required for anomaly algorithms—aligned with FinOps practices covered in Category 20.
- **HOW:** Land CUR parquet/csv in S3, ingest selectively into Splunk summary indexes for trending joins with deployment events.

**AWS Security Hub and AWS Config (state vs event)**

- **WHAT:** Ingest Security Hub control findings (CIS/other frameworks as enabled) and AWS Config timeline snapshots for resource drift—security groups, S3 public access, encryption posture.
- **WHY:** CloudTrail answers **who invoked an API**; Config answers **whether the resource remained non-compliant afterward**. Investigations frequently chain both per [AWS Config concepts](https://docs.aws.amazon.com/config/latest/developerguide/evaluate-config.html).
- **HOW:** EventBridge targets forwarding findings into Splunk; enrich with account/Organizational Unit lookups so unresolved posture gaps escalate alongside IAM misuse narratives.

### AWS IAM security practices

- **WHAT:** Monitor IAM policy changes, root account usage, access key rotation, cross-account role assumptions, and STS token abuse patterns.
- **WHY:** IAM is the attack surface in cloud—lateral movement often starts with overprivileged roles or leaked access keys, not network exploits.
- **HOW:** Normalize CloudTrail `CreateRole`, `AttachRolePolicy`, and `AssumeRole` event families via the **Splunk Add-on for AWS**; alert on `ConsoleLogin` without MFA, new access key creation for root, and cross-account `AssumeRole` from unexpected source accounts. Catalog anchors: [Root Account Usage](index.html#uc-4.1.2), [IAM Policy Changes](index.html#uc-4.1.4).

### AWS VPC and network telemetry

- **WHAT:** VPC Flow Logs (v5 enriched format preferred), Transit Gateway flow logs, Security Group change auditing, and NACLs.
- **WHY:** East-west visibility in cloud requires flow logs—there are no SPAN ports. Security group changes are a common misconfiguration vector in AWS breaches.
- **HOW:** Land flow logs in S3 and ingest with the TA; normalize `srcaddr`, `dstaddr`, and `action` into **CIM Network_Traffic** for correlation with on-premises firewall feeds. Alert on `REJECT` spikes correlated with GuardDuty findings. Catalog anchor: [VPC Flow Log Analysis](index.html#uc-4.1.9).

### AWS Lambda and serverless depth

- **WHAT:** Invocation errors, duration p99, concurrent execution limits, dead-letter queue depth, and cold-start frequency by function version.
- **WHY:** Serverless hides infrastructure but not failure modes—concurrency throttles can manifest as HTTP 502 storms for API Gateway callers.
- **HOW:** Pull CloudWatch metrics via the TA poller plus structured Lambda logging through CloudWatch Logs → Kinesis (or Firehose) → Splunk; tag function ARN and version for deployment correlation. Catalog anchors: [Lambda Concurrent Executions and Throttling](index.html#uc-4.1.51), [Lambda Cold Start and Init Duration Latency](index.html#uc-4.5.2).

### AWS EKS specific practices

- **WHAT:** EKS control plane audit logs, managed node group scaling events, Fargate pod scheduling latency, and EKS add-on health.
- **WHY:** Managed Kubernetes still requires audit-grade control plane visibility—AWS manages etcd, but customers own workload security and admission policy.
- **HOW:** Enable EKS audit logging to CloudWatch and forward into Splunk; combine with `kube-state-metrics` and cluster signals from Category **3** (Containers). Cross-reference [Control Plane Health](index.html#uc-3.2.7) with EKS-specific upgrade and add-on events.

### Critical AWS-aligned catalog anchors

| Risk | Representative UC |
|------|---------------------|
| Privileged misuse | [Root Account Usage](index.html#uc-4.1.2) |
| IAM drift | [IAM Policy Changes](index.html#uc-4.1.4) |
| Network visibility | [VPC Flow Log Analysis](index.html#uc-4.1.9) |
| Availability | [ELB Target Health](index.html#uc-4.1.22) |
| Audit integrity | [CloudTrail Log File Delivery Failures](index.html#uc-4.1.30) |
| Storage exposure | [S3 Bucket Policy Changes](index.html#uc-4.1.7) |
| Threat detection | [GuardDuty Finding Ingestion](index.html#uc-4.1.8) |
| Serverless throttles | [Lambda Concurrent Executions and Throttling](index.html#uc-4.1.51) |

### Microsoft Azure practices

**Azure Activity Log**

- **WHAT:** Subscription-level administrative operations—ARM deployments, RBAC edits, policy violations.
- **WHY:** Equivalent control-plane narrative to CloudTrail for Azure estates.
- **HOW:** Stream diagnostic settings to Event Hub → Splunk via **Splunk Add-on for Microsoft Cloud Services** ([Azure Monitor export paths](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log)).

**Microsoft Defender for Cloud**

- **WHAT:** Secure-score regressions, regulatory recommendations, threat alerts across VMs, APIs, and Kubernetes.
- **WHY:** Native posture narrative complements Splunk correlators for hybrid SOC workflows.
- **HOW:** Ingest alerts continuously—catalog anchor [Defender for Cloud Alerts](index.html#uc-4.2.9).

**Azure Monitor metrics and logs**

- **WHAT:** Platform metrics (VM, App Service, AKS), resource logs, and dependency traces.
- **WHY:** Bridges infra saturation with application telemetry when forwarded consistently.
- **HOW:** Diagnostic settings to Event Hub or direct export patterns supported by the TA—map `ResourceId`, `subscription`, and `region` fields for tenant-wide reporting.

### Azure NSG and network telemetry

- **WHAT:** NSG flow logs, Azure Firewall logs, Application Gateway WAF logs, and Private Link audit trails.
- **WHY:** Microsegmentation in Azure depends on NSG enforcement visibility—silent rule changes create exposure windows that are hard to see without Splunk correlation.
- **HOW:** Route diagnostic settings to Event Hub → Splunk; normalize `FlowDirection`, `RuleAction`, and related fields for **CIM Network_Traffic** parity with AWS VPC flows. Catalog anchor: [NSG Flow Log Analysis](index.html#uc-4.2.4).

### Azure AKS practices

- **WHAT:** AKS diagnostics (kube-apiserver, kube-controller-manager, kube-scheduler, cluster-autoscaler), Azure Policy for AKS, and Azure Container Registry vulnerability scanning.
- **WHY:** Managed Kubernetes reduces ops burden, but auditors still require control plane evidence and admission policy proof.
- **HOW:** Use diagnostic settings to capture AKS master-tier logs; pair with Category **3** workload signals. Catalog anchor: [AKS Cluster Health](index.html#uc-4.2.7).

#### Azure catalog anchors

| Risk | Representative UC |
|------|---------------------|
| Posture regression | [Defender for Cloud Alerts](index.html#uc-4.2.9) |
| Network exposure | [NSG Flow Log Analysis](index.html#uc-4.2.4) |
| Container platform | [AKS Cluster Health](index.html#uc-4.2.7) |

### Google Cloud Platform practices

**Cloud Audit Logs**

- **WHAT:** Admin Activity, Data Access, System Event audit streams for IAM, Compute, GKE, Cloud Storage.
- **WHY:** Forensic accountability for GCP control plane and sensitive data-plane access.
- **HOW:** Pub/Sub sink to Splunk via **Splunk Add-on for Google Cloud Platform** following [GCP logging export](https://cloud.google.com/logging/docs/export) guidance.

**Security Command Center (SCC)**

- **WHAT:** Organization-level findings across assets, vulnerabilities, and threats when SCC tiers are licensed.
- **WHY:** Aggregates posture signals beyond raw logs—useful for executive risk summaries correlated with Splunk incident timelines.
- **HOW:** Feed SCC findings streams where APIs permit; tie assets back to CMDB entities for blast-radius overlays.

### GCP VPC and network telemetry

- **WHAT:** VPC Flow Logs, Firewall Rules Logging, Cloud NAT logs, and Packet Mirroring summaries.
- **WHY:** GCP's software-defined networking model means all enforcement is virtual—log evidence replaces physical tap infrastructure.
- **HOW:** Use log sinks to Pub/Sub → **Splunk Add-on for Google Cloud Platform**; normalize into **CIM Network_Traffic** for multi-cloud correlation.

### GKE practices

- **WHAT:** GKE system and workload logs, Binary Authorization admission events, and GKE Security Posture findings.
- **WHY:** GKE Autopilot reduces configuration surface, but Binary Authorization failures indicate supply chain policy violations worth escalating.
- **HOW:** Export Cloud Logging → Pub/Sub → Splunk with `resource.type=k8s_cluster` (and related) filters; correlate with Category **3** container signals.

#### GCP catalog anchors

| Risk | Representative UC |
|------|---------------------|
| Identity drift | [IAM Policy Changes](index.html#uc-4.3.2) |
| Posture findings | [Security Command Center Findings](index.html#uc-4.3.30) |

### Multi-cloud posture: normalization before dashboards

Operating two or three hyperscalers magnifies cardinality problems unless Splunk fields converge early.

- **WHAT:** Canonical fields—`principal`, `cloud.provider`, `cloud.account`, `region`, `resource.type`, `network.direction`, `policy.action`—mapped across ARN formats (AWS), Azure Resource IDs, and GCP resource names.
- **WHY:** Analysts cannot correlate lateral movement when the same analyst workflow requires three regex dialects per query.
- **HOW:** Splunk **Transforms**/`EVAL`-heavy routing plus KV lookups refreshed from CMDB exports; reserve separate indexes per vendor only when retention/legal differs—otherwise federated searches proliferate.

### Serverless hygiene beyond generic wrappers

Serverless stacks emphasize four recurring KPI classes: **latency percentiles**, **throttles and concurrency caps**, **dead-letter queues or failed invocations**, and **platform delivery of logs/metrics themselves** (missed telemetry = missed incident).

- **WHAT:** Vendor metrics (CloudWatch/Azure Monitor/Cloud Monitoring) per function revision plus asynchronous sink depth when applicable.
- **WHY:** Cold starts and quota exhaustion manifest as saturation invisible to upstream callers until timeouts cascade.
- **HOW:** Splunk TA pulls or streaming exports—tie Lambda/Azure Function revisions back to CI/CD release IDs carried as structured logging fields.

Cross-reference burst-spend anomalies with deployment hashes—patterns surfaced later under Category 20 anchors such as [Cost Anomaly Detection](index.html#uc-20.1.2).

---

## Category 20: Cost & Capacity Management (77 use cases)

Cost & Capacity Management spans [Cloud Cost Monitoring](index.html#cat-20/20.1) (27), [Capacity Planning](index.html#cat-20/20.2) (33), and [License & Subscription Management](index.html#cat-20/20.3) (17). It connects telemetry-derived utilization with contractual spend—closing the loop between observability and finance stakeholders.

### FinOps Foundation-aligned practices

Per the [FinOps Framework](https://www.finops.org/framework/), mature organizations expose **near-real-time cost visibility**, continuously **right-size** resources, and optimize **commitment-based discounts** without starving reliability.

**Real-time visibility**

- **WHAT:** Dashboard daily/hourly spend by team, service, tag, and region with anomaly overlays.
- **WHY:** Budget breaches discovered monthly arrive too late for corrective architecture decisions.
- **HOW:** Ingest CUR/Billing exports into Splunk; join with deployment tags from CI/CD—anchors [Daily Spend Trending](index.html#uc-20.1.1), [Budget Threshold Alerting](index.html#uc-20.1.5).

**Rightsizing**

- **WHAT:** Compare billed capacity units to measured utilization percentiles across EC2/RDS/analogues.
- **WHY:** Eliminates structural waste uncovered only when observability meets billing granularity.
- **HOW:** Automated recommendations tracked through ticketing—pair with [Idle Resource Identification](index.html#uc-20.1.4).

**Commitment optimization**

- **WHAT:** Model savings plans/reserved instances vs on-demand spikes using rolling forecasts.
- **WHY:** Maximizes discount uptake without locking spend ahead of workload deprecation.
- **HOW:** Forecast indexes populated from utilization baselines—see [Compute Capacity Forecasting](index.html#uc-20.2.1) and [Storage Growth Forecasting](index.html#uc-20.2.2).

### Critical FinOps-aligned anomaly detection anchors

| Scenario | Representative UC |
|----------|---------------------|
| Spend spikes | [Cost Anomaly Detection](index.html#uc-20.1.2), [Cost Anomaly by Cloud Service](index.html#uc-20.1.13) |
| Seasonality-aware alerting | [Cost Anomaly with Seasonal Decomposition](index.html#uc-20.2.24) |

Seasonal decomposition matters because weekly release cadences and quarter-close batch jobs produce benign spikes—models must separate repeating patterns from genuine leakage events.

### License and subscription telemetry (bridging Category 20.3)

Cloud invoices increasingly bundle SaaS seats, marketplace subscriptions, and committed credits beside raw compute meters.

- **WHAT:** Normalize entitlement exports—Microsoft 365/Azure hybrid benefit posture, Salesforce licenses, Splunk license usage (`license_usage.log` summaries)—alongside CUR/Billing rows.
- **WHY:** Capacity planners reconcile **contracts** with **provisioned capacity**; ignoring license drift creates duplicate spend (over-provisioned SaaS plus redundant IaaS capacity for the same workflow).
- **HOW:** Scheduled transforms from billing APIs and entitlement APIs into Splunk summary indexes with alert thresholds aligned to procurement calendars—not merely engineering cadences.

Where Splunk ingests its own meter data for hybrid estates, finance-adjacent dashboards should annotate whether anomalies trace to indexer/cluster expansion versus purely bursty search concurrency—tie narratives back to observability KPIs from Category **13** when Splunk itself scales inside customer estates.

---

### Getting started checklist

1. **Audit trails first** — CloudTrail (multi-region), Azure Activity Log, GCP Admin Activity logs. Without audit parity, investigations fail.
2. **Threat detection second** — GuardDuty, Defender for Cloud, SCC findings. Native ML complements Splunk rule-based detections.
3. **IAM monitoring third** — root usage, cross-account roles, service principal changes. IAM is the cloud attack surface.
4. **Network flows fourth** — VPC Flow Logs / NSG flows for east-west visibility absent from traditional SNMP.
5. **Workload signals fifth** — Kubernetes events and metrics via OpenTelemetry or Splunk Connect for Kubernetes, paired with cloud-managed node health.
6. **Cost telemetry last** — CUR / billing exports for FinOps correlation with deployment events.

---

## Putting it together in Splunk operations

Operate cloud and container telemetry as **three braided timelines**: **audit identity plane changes**, **watch saturation SLO curves**, and **tie spend anomalies to deployments**. Splunk’s additive **Splunkbase** integrations (`Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`) supply normalization scaffolding—your differentiation comes from tagging discipline, baseline envelopes per workload tier, and executive dashboards that narrate blast radius plus dollars—not isolated alerts.

When migrating from Prometheus-centric stacks, preserve kube-system dashboards until OTel parity is verified for etcd and scheduler KPIs that historically lived in Grafana—those signals anchor stability arguments during incident reviews tied to catalog UC IDs above.

Executive-ready summaries typically stitch three perspectives into one Splunk dashboard suite: **blast radius from IAM/API narratives**, **saturation curves from workloads and meshes**, and **dollar attribution lines from CUR-equivalent feeds**. Teams that operationalize those stitches graduate from pager storms to preventative governance—whether tightening RBAC guardrails after GuardDuty correlations or resizing autoscalers before budgets trip.
