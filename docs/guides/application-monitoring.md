---
title: Application & Service Monitoring Domain Guide
type: domain-guide
domains: [Applications, Services]
categories: [7, 8, 12, 13, 16]
last_updated: 2026-04-30
---

# Application & Service Monitoring Domain Guide

This guide situates the **application and platform service** pillar of the Splunk monitoring catalog: relational and polyglot data platforms, HTTP and middleware tiers, DevOps pipelines, the observability stack that measures Splunk itself (including Splunk IT Service Intelligence), and IT service management bridges that translate telemetry into SLA reality. It ties vendor-native database, web, queue, and CI/CD instrumentation to Splunk normalization so teams can watch **user-visible failure classes**—slow transactions, TLS surprises, Kafka backlogs, poisoned deployments, indexer saturation, and breached SLAs—with defensible WHAT/WHY/HOW runbooks rather than vanity metrics.

Browse the domain categories directly: [Browse Database & Data Platforms](index.html#cat-7), [Browse Application Infrastructure](index.html#cat-8), [Browse DevOps & CI/CD](index.html#cat-12), [Browse Observability & Monitoring Stack](index.html#cat-13), [Browse Service Management & ITSM](index.html#cat-16).

Treat these categories as one **service graph**: the database exposes tail latency; the gateway and queue shape fan-out; CI/CD decides which binary ever reaches the pool; Splunk tells you whether your evidence pipeline is trustworthy; ITSM timestamps whether recovery met the contract.

Nothing in this guide replaces load testing—Splunk reveals **production truth**, but synthetic probes still validate assumptions when autoscaling policies or JVM heap sizing change. Instrument both.

---

## Category 7: Database & Data Platforms (122 use cases)

Database & Data Platforms spans [Relational Databases](index.html#cat-7/7.1) (15), [NoSQL Databases](index.html#cat-7/7.2) (23), [Cloud-Managed Databases](index.html#cat-7/7.3) (17), [Data Warehouses & Lakehouses](index.html#cat-7/7.4) (41), [Search & Analytics Engines](index.html#cat-7/7.5) (21), and [Database & Data Platform Trending](index.html#cat-7/7.6) (5). SQL and document engines remain the persistence choke point for most business workloads—when they throttle, every upstream cache and autoscale rule lies.

**Splunk integration primer:** **`splunk_app_db_connect`** ([Splunk DB Connect documentation](https://docs.splunk.com/Documentation/DBX/latest/DBX/Introduction)) executes JDBC queries on schedules or triggers—ideal for DMV/pg_stat snapshots—while Universal Forwarders tail slow-query files where JDBC cannot observe filesystem latency directly. Choose DB Connect when SQL access is stable and audited; choose UF tails when vendors mandate raw log fidelity.

Platform engineers should budget **extra DB CPU** for observability polling—monitoring queries compete with OLTP unless isolated readers/replicas serve dashboards (WHAT); OLTP regressions attributed to “Splunk broke prod” destroy observability programs (WHY); route heavy trending searches through replicas or warehouse replicas explicitly labeled non-production workloads (HOW).

---

**MySQL — WHAT/WHY/HOW**

- **WHAT:** Collect the **slow query log** (file or table destination) with normalized fields for `query_time`, `lock_time`, `rows_examined`, digest, and connection identity.
- **WHY:** Long-running statements hold locks, inflate buffers, and mask as “CPU problems” on app servers until you read the statements the optimizer actually executed—[MySQL slow query log documentation](https://dev.mysql.com/doc/refman/8.0/en/slow-query-log.html) anchors the instrumentation contract.
- **HOW:** UF/HEC tail of `slow.log` into Splunk with multiline aggregation; correlate with Galera/InnoDB cluster state for causality (not just blame the last query).

**PostgreSQL — WHAT/WHY/HOW**

- **WHAT:** Prefer `pg_stat_statements` aggregates (normalized query text, mean/total time, shared blocks hit) augmented with auto-explain sampling for outliers.
- **WHY:** Single-statement tails miss repeated mid-cost queries that dominate when fan-out multiplies—`pg_stat_statements` exposes the **regime** behind p95 latency [per PostgreSQL monitoring guidance](https://www.postgresql.org/docs/current/pgstatstatements.html).
- **HOW:** Scheduled `dbxquery` or scripted polls into Splunk summary indexes; alert on digest-level regression vs weekly baselines.

**SQL Server — WHAT/WHY/HOW**

- **WHAT:** Blend **Extended Events** or **Query Store** outputs with DMV snapshots (`sys.dm_exec_query_stats`, waits, blocking chains).
- **WHY:** Plan regressions swap hash loops for nested loops silently; only plan and wait-class telemetry explains **why** latency doubled with “the same release.”
- **HOW:** Splunk Add-on paths for SQL Server or DB Connect extracts; unify `database_id` and `application` fields for tenant-level SLO dashboards.

Catalog anchor tying the thread together: [Slow Query Detection](index.html#uc-7.1.1).

### Connection pool monitoring (application and database sides)

- **WHAT:** Track **pool active/idle**, **checkout wait**, **timeout counts** on Tomcat/WebLogic/Spring pools **and** database-side `max_connections`/session utilization (`V$SESSION`, `pg_stat_activity`, `sys.dm_exec_connections`).
- **WHY:** Pools mask database saturation until both sides exhaust—apps see queued requests while DBAs see full `max_connections`.
- **HOW:** JVM JMX/log ship for pool stats; DB Connect or vendor TA for DMV-style queries—pair [Connection Pool Exhaustion](index.html#uc-7.1.3) with [Database Connection Pool Exhaustion](index.html#uc-7.1.17) for end-to-end narratives.

### Replication lag and topology health

- **WHAT:** Measure **bytes/seconds behind primary** (MySQL replication, PG replication slots, Mongo oplog lag, SQL Server AG REDO queue) plus **quorum/election events** in clustered NoSQL engines.
- **WHY:** Read scaling and DR depend on bounded lag; unbounded lag precedes split-brain acceptance of stale reads or failed failovers.
- **HOW:** Native exporter metrics into Splunk; elevate when lag crosses **SLA envelopes** derived from historical batch windows—cluster exemplar [Cluster Membership Changes](index.html#uc-7.2.1).

### Deadlock detection

- **WHAT:** Parse deadlock graphs (SQL Server trace flag / XEvents, InnoDB `LATEST DETECTED DEADLOCK`, PostgreSQL `log_lock_waits` + deadlock detail).
- **WHY:** Deadlocks are **correctness events**—silent retries burn user trust and mask data races.
- **HOW:** Structured extractions into Splunk with **session/app stack** preserved for dev triage—[Deadlock Monitoring](index.html#uc-7.1.2).

### Availability groups and clustered SQL

- **WHAT:** Track **synchronization state**, **redo queue**, **commit policy** (synchronous vs async), and listener routing health.
- **WHY:** Partial quorum or lagging secondary invalidates RPO assumptions mid-incident.
- **HOW:** DMVs + Windows cluster events correlated—[Database Availability Group Health](index.html#uc-7.1.12).

### Data warehouses and lakehouses — credits, queues, and concurrency

Snowflake/BigQuery/Databricks-class platforms expose **warehouse queues**, **slot contention**, **spill-to-remote-storage volume**, and **failed micro-partitions**—signals analogous to OS run queues but billed per credit.

- **WHAT:** Pull **query history** exports (latency, credits consumed, queued time), **pipe/stream lag** for ingestion paths, and **cluster resize events**.
- **WHY:** Interactive dashboards stall when warehouses throttle concurrency exactly while finance closes quarterly reporting—the loudest complaints arrive without classic CPU alarms because credits abstract infrastructure.
- **HOW:** Scheduled exports via vendor REST APIs into Splunk summary indexes; correlate BI login spikes with concurrent warehouse saturation **before** executive SLA decks miss deadlines.

Join warehouse KPI baselines with Category **20** ([Browse Cost & Capacity Management](index.html#cat-20)) spend anomalies when burst workloads coincide with oversized warehouse SKUs left running after one-off campaigns.

### Search and analytics engines — Elasticsearch/OpenSearch patterns

Beyond generic slow-query narratives, search clusters add **shard allocation**, **circuit breaker trips**, **cross-cluster replication lag**, and **bulk indexing refusal rates**.

- **WHAT:** Cluster health transitions (`yellow`/`red`), pending tasks, JVM heap pressure per data node, indexing latency histograms.
- **WHY:** Search timeouts resemble application defects until analysts realize primaries saturated indexing queues during nightly ETL overlaps.
- **HOW:** Structured Elastic/OpenSearch APIs ingested via scripted polls or Elastic Agent streams normalized into Splunk—dashboard shard imbalance alongside JVM KPIs referenced under Category **8** JVM heap guidance.

### Cloud-managed relational databases

RDS/Aurora/Cloud SQL/Azure SQL Managed Instance abstracts hosts yet exposes **Performance Insights**, **deadlocks**, **failovers**, **storage auto-grow**, and **backup slot contention**. Splunk excels when API-fed narratives combine with application-side pool stats so **cloud patch windows** never masquerade as rogue application deploys—tag `maintenance_window_id` from provider notifications wherever APIs expose them.

### NoSQL breadth — consensus and ops pacing

Document and wide-column engines emphasize **election churn**, **compaction backlog**, **hot partitions**, **repliset lag**. Same discipline applies: define WHAT shards throttle writes, WHY ops pacing predicts SLA breaches before disks fill, HOW exporter metrics plus audit logs land in Splunk with bounded cardinality—cross-reference NoSQL exemplars such as [Cluster Membership Changes](index.html#uc-7.2.1).
### Critical database/catalog anchors

| Risk | Representative UC |
|------|---------------------|
| Statement regression | [Slow Query Detection](index.html#uc-7.1.1) |
| Correctness | [Deadlock Monitoring](index.html#uc-7.1.2) |
| HA topologies | [Database Availability Group Health](index.html#uc-7.1.12) |
| Saturation | [Connection Pool Exhaustion](index.html#uc-7.1.3), [Database Connection Pool Exhaustion](index.html#uc-7.1.17) |

Augment drill paths with privilege-abuse surveillance when DB audit streams justify it—[Privilege Escalation Audit](index.html#uc-7.1.15), and tune space-growth narratives with [Tablespace / Data File Growth](index.html#uc-7.1.5) plus maintenance hygiene through [Table and Index Bloat and Maintenance Window](index.html#uc-7.1.19) when vacuum/rebuild schedules drift.

---

## Category 8: Application Infrastructure (106 use cases)

Application Infrastructure spans [Web Servers & Reverse Proxies](index.html#cat-8/8.1) (18), [Application Servers & Runtimes](index.html#cat-8/8.2) (23), [Message Queues & Event Streaming](index.html#cat-8/8.3) (21), [API Gateways & Service Mesh Adjacent](index.html#cat-8/8.4) (16), [Caching & Session Stores](index.html#cat-8/8.5) (12), [Network Service Availability](index.html#cat-8/8.6) (11), and [Application Infrastructure Trending](index.html#cat-8/8.7) (5). This layer turns **protocol-level behavior**—HTTP semantics, JVM memory, broker health, TLS identity, cache hit rate—into SLO dashboards.

### HTTP error rates and saturation

- **WHAT:** Partition **5xx vs 4xx**, **upstream connect failures**, **retry storms**, and **latency percentiles** per route/service—not a single red/green uptime bit.
- **WHY:** Retry-unaware clients amplify partial outages; distinguishing `502` upstream from `503` overload drives the right remediation (rollback vs scale-out).
- **HOW:** Reverse proxy access logs (Apache, NGINX, HAProxy) with normalized `status`, `upstream_status`, `request_time`, `upstream_response_time`—[HTTP Error Rate Monitoring](index.html#uc-8.1.1).

### SSL/TLS certificate lifecycle

- **WHAT:** Track **notAfter** dates, chain completeness, OCSP stapling failures, and policy compliance (cipher suites allowed).
- **WHY:** Certificates expire on calendar time—not deployment cadence—and silently break mobile apps before browsers surface errors uniformly.
- **HOW:** Scripted probes + CT log correlation where adopted—critical anchor [SSL Certificate Monitoring](index.html#uc-8.1.5); complementary hygiene under catalog framing [SSL Certificate Expiry](index.html#uc-8.1.14).

### HAProxy and load balancer backends

- **WHAT:** Backend **UP/DOWN transitions**, **session rates**, **queue depth**, **retry counts**, **health check failures**.
- **WHY:** A drained backend shifts entire cohorts of sessions—latency spikes precede complete outage if pools shrink asymmetrically.
- **HOW:** Splunk TA paths or syslog structured logs—[HAProxy Backend Health](index.html#uc-8.1.15).

### JVM heap, GC, and runtime stalls

- **WHAT:** Heap utilization (`Old Gen`), GC pause times (`Pause Young`, `Pause Full`), thread deadlocks, thread pool exhaustion.
- **WHY:** GC storms masquerade as network latency when pause times exceed client timeouts.
- **HOW:** JMX/JFR exporters via TA-jmx or OTel—anchor exemplar [JVM Heap Utilization](index.html#uc-8.2.1).

### Kafka — consumer lag and broker health

- **WHAT:** **Consumer group lag** per topic/partition, **under-replicated partitions**, **offline replicas**, **controller elections**, **ISR shrink events**.
- **WHY:** Streaming backlogs propagate into downstream DB writes and batch SLA misses faster than disk KPIs move.
- **HOW:** Kafka exporter metrics + Cruise Control narratives where deployed—[Consumer Lag Monitoring](index.html#uc-8.3.1), [Broker Health Monitoring](index.html#uc-8.3.3).

### ActiveMQ / classic brokers — memory pressure

- **WHAT:** Memory percent usage, store paging, blocking producers, DLQ depth.
- **WHY:** Broker memory thresholds throttle publishers—latency climbs nonlinearly once paging activates.
- **HOW:** JMX + broker logs normalized—[ActiveMQ Memory Pressure](index.html#uc-8.1.32).

### Redis/Memcached — cache efficacy

- **WHAT:** Evictions, hit ratio, connections, replication lag (Redis), slab churn (Memcached).
- **WHY:** Cache stampede amplifies DB load exactly when protection was assumed.
- **HOW:** INFO telemetry via scripted polls or Redis Insight exports—pair Redis KPI baselines with database slow-query regressions from Category **7**.

### API gateways — quotas, auth failures, and backend mapping

Modern gateways (Kong, Apigee, AWS API Gateway, Azure APIM) emit **rate-limit counters**, **JWT validation failures**, **latency histograms per route/key**, **backend connectivity faults**.

- **WHAT:** Normalize **consumer/subscription identifiers**, **429 vs 503**, **quota exhaustion**, **certificate pinning mismatches** when east-west TLS terminates twice.
- **WHY:** Gateway charts isolate whether degradation sits in **edge policy** vs **origin services**—misattribution wastes war-room hours.
- **HOW:** Structured access logs shipped to Splunk with `route_id` and `backend_target` dimensions; correlate with upstream HTTP KPIs already ingested per [HTTP Error Rate Monitoring](index.html#uc-8.1.1).

### DNS and core network dependencies (Category 8.6 overlap)

Recursive resolver failures (`SERVFAIL`, truncated responses) and authoritative **TTL anomalies** cascade into “mystery” 5xx when load balancers depend on stale records. Splunk dashboards that join **DNS query logs** with reverse-proxy timelines close that gap—pair with broader [Network Service Availability](index.html#cat-8/8.6) catalog coverage for health-probe narratives.

### IIS / Windows web stacks

Microsoft IIS remains pervasive for .NET APIs even when Linux gateways front customer traffic.

- **WHAT:** `W3SVC` logs, Windows Event Log application errors, ASP.NET **request queues**, Application Pool recycle reasons.
- **WHY:** Recycles mid-flight mimic upstream 502s—Splunk timelines must differentiate **worker process crashes** from **deployment-induced restarts**.
- **HOW:** Splunk Universal Forwarder with **`Splunk_TA_windows`** inputs—join IIS `sc-status`, `sc-substatus`, `time-taken` with Windows Process exits for causality narratives feeding the same HTTP dashboards described for NGINX.

### CDN and edge offload awareness

When CDN tiers absorb traffic, origin HTTP dashboards lose fidelity unless **`X-Cache`** / **`Age`** headers or CDN analytics APIs contribute cache-hit context—otherwise engineering debates whether microservices regressed when edge caches expired simultaneously during marketing spikes.

---

## Category 12: DevOps & CI/CD (88 use cases)

DevOps & CI/CD spans [Source Control](index.html#cat-12/12.1) (20), [CI/CD Pipelines](index.html#cat-12/12.2) (26), [Artifact & Package Management](index.html#cat-12/12.3) (12), [Infrastructure as Code](index.html#cat-12/12.4) (16), [GitOps & Progressive Delivery](index.html#cat-12/12.5) (10), and [DevOps & CI/CD Trending](index.html#cat-12/12.6) (4). Telemetry here answers whether **engineering velocity** trades off against **change safety**.

### DORA metrics — deployment frequency, lead time, change failure rate, MTTR

Per **Accelerate** / **DORA** research ([Google Cloud DevOps capabilities](https://cloud.google.com/devops)), elite teams optimize four outcomes:

| Metric | WHAT | WHY | HOW (Splunk angle) |
|--------|------|-----|---------------------|
| Deployment frequency | Count successful prod deploy events per day/week | Validates CI/CD throughput—infrequent deploys hide integration debt | Parse GitHub/GitLab/Jenkins/Azure DevOps webhook payloads into Splunk—dashboard deploy velocity by team/service |
| Lead time for changes | Timestamp commit merge → prod-ready deploy | Long lead times correlate with batch risk | Correlate SCM merge IDs with pipeline completion timestamps |
| Change failure rate | Ratio of deployments causing incidents/rollback | Measures quality gates—not raw velocity | Join deployment hashes with incident tickets (Category **16**) |
| Mean time to restore | Detection → mitigation window | Stress-tests rollback automation | Combine CI/CD rollback events with MTTR KPIs |

Operational maturity ships **thin vertical slices**: smaller batches reduce blast radius—mirror that philosophy in Splunk dashboards by tagging builds with **risk tier** and **feature flags**.

### Supply chain security — SBOM and dependency scanning

- **WHAT:** Ingest SBOM artifacts (CycloneDX/SPDX), container image digest signing outcomes, and scanner verdicts from pipelines (SAST/DAST/dependency CVE gates).
- **WHY:** Log4Shell-class defects propagate faster than manual spreadsheet audits; SBOM plus scanner telemetry proves **what shipped**, not what README claims.
- **HOW:** Pipeline JSON → HEC with immutable linkage `(repo,commit,digest)`—complement catalog anchors like [Dependency Vulnerability Alerts](index.html#uc-12.3.2) and [Security Scan Results in Pipeline](index.html#uc-12.2.8).

### Source-control governance signals

| Risk | Representative UC |
|------|---------------------|
| Secrets in repos | [Secret Exposure Detection](index.html#uc-12.1.4) |
| Policy drift | [Branch Protection Bypasses](index.html#uc-12.1.2) |
| Destructive history | [Force Push to Protected Branches](index.html#uc-12.1.10) |

Pair governance alerts with velocity baselines—[Commit Activity Trending](index.html#uc-12.1.1)—when correlating unusual merge volume with potential automation abuse or compromised tokens.

### Pipeline reliability beyond green builds

Failed deployments anchor operational improvement loops—[Failed Deployment Tracking](index.html#uc-12.2.5). Trend rollback counts alongside change failure rate to prove whether incident reductions stem from safer automation versus quieter calendars.

### Infrastructure as Code and GitOps reconciliation

Terraform/CloudFormation/Pulumi apply events and Argo CD / Flux reconciliation health tell you **whether declared state matches live state** before an application ever logs an error.

- **WHAT:** Capture **plan/apply summaries**, **drift detection**, **sync failures**, **pruned resources**, **helm hook outcomes**.
- **WHY:** Silent drift invites tomorrow’s outage today—Kubernetes controllers heal pods while underlying IAM roles remain dangerously broad after manual console edits.
- **HOW:** CI/CD structured logs plus GitOps controller logs normalized into Splunk with `commit_sha` tying changes to SCM anchors already monitored under [Branch Protection Bypasses](index.html#uc-12.1.2).

Progressive delivery signals (canary promotion percentages, automated rollback triggers) belong in the same dashboards as HTTP error composites—percent-canary adoption explains latency deltas better than coarse deployment timestamps alone.

---

## Category 13: Observability & Monitoring Stack (143 use cases)

Observability & Monitoring Stack spans [Splunk Platform Health](index.html#cat-13/13.1) (51), [Splunk ITSI](index.html#cat-13/13.2) (37), [Third-Party Monitoring Integration](index.html#cat-13/13.3) (19), [AI & LLM Observability](index.html#cat-13/13.4) (15), and [OpenTelemetry, Observability Pipelines & SRE Patterns](index.html#cat-13/13.5) (21). This meta-category monitors **the measurement apparatus itself**—critical because silent indexer drops mimic application recovery while evidence disappears.

### Splunk platform KPIs — ingestion and topology

- **WHAT:** Monitor **indexer queue fill**, forwarder connectivity, SHC captain health, indexer replication backlog.
- **WHY:** Observability debt cascades—customers blame apps when Splunk stalled ingestion mid-incident.
- **HOW:** `_internal`, `_audit`, Monitoring Console exports—anchors [Indexer Queue Fill Ratio](index.html#uc-13.1.1), [Forwarder Connectivity](index.html#uc-13.1.3), [Search Head Cluster Status](index.html#uc-13.1.10), [Indexer Cluster Bucket Replication Health](index.html#uc-13.1.11).

### Splunk ITSI vendor-aligned KPI practices

Splunk documents KPI construction across ITSI releases ([Splunk ITSI KPI overview](https://docs.splunk.com/Documentation/ITSI/latest/Configure/KPIoverview)) emphasizing flexible search backing and entity-aware thresholds.

**KPI source search types — WHAT/WHY/HOW**

| Type | WHAT | WHY | HOW |
|------|------|-----|-----|
| Data model KPI | KPI searches accelerated against **data models** | Faster recurring KPI computations over governed fields | Define models matching CIM/OT schemas before KPI schedules scale |
| Ad hoc KPI | Direct SPL against raw indexes | Maximum flexibility when models lag bespoke telemetry | Guard cardinality—entity splits multiply workload |
| Metrics KPI | Native metrics indexes (`mstats`) | Efficient numeric telemetry at scale | Normalize metric names/units via OTel conventions |
| Base search KPI | Shared heavy searches feeding dependent KPIs | Reduces redundant scanning across sibling KPIs | Profile base search skew carefully—dependency graphs amplify latency |

**Split/filter KPIs by entities**

- **WHAT:** Attach KPIs to **entities** (hosts, services, business apps) rather than global aggregates alone.
- **WHY:** Global averages hide localized breaches until blast radius expands—entities localize episodes for actionable bridges.
- **HOW:** Import entities via CSV/KV sync from CMDB or discovery searches; bind KPI thresholds per tier.

**Entity-level thresholds**

- **WHAT:** Threshold bands (`critical`, `high`, `medium`) tuned **per entity cohort**, not universal constants.
- **WHY:** Tier-1 OLTP demands tighter envelopes than sandbox workloads sharing infrastructure.
- **HOW:** Threshold templates applied via ITSI bulk tooling—combine with predictive alerting below.

**Predictive analytics for disruption prevention**

- **WHAT:** Multivariate anomaly detection + forecasting baselines when statistical readiness exists.
- **WHY:** Threshold breaches lag causal saturation—prediction buys change-window negotiation before outage windows intersect payroll batches.
- **HOW:** ITSI **Predictive Analytics** / Adaptive Thresholding features per Splunk licensing—anchor trending visuals via [Service Health Score Trending](index.html#uc-13.2.1), operational stability via [Rules Engine Health](index.html#uc-13.2.6).

**Service templates, glass tables, and episode management**

- **WHAT:** Model business services as first-class objects with dependency edges, KPI rollups, and optional **Glass Table** situational dashboards; feed **Episode Analytics** alert grouping to reduce redundant pages.
- **WHY:** Raw alert streams from dozens of KPIs recreate pager storms unless correlation groups symptoms under a single service narrative—the pattern Splunk documents for ITSI operations centers ([Splunk ITSI service insights](https://docs.splunk.com/Documentation/ITSI/latest/ServiceInsights/AboutServiceInsights)).
- **HOW:** Import **Service Templates** from content packs where applicable; customize entity rules per data center; wire REST episode actions back to ServiceNow tickets using the same `service_id` fields embedded in CI exports from Category **16**.

**Content Pack for Monitoring & Alerting (baseline parity)**

- **WHAT:** Leverage Splunk-provided KPIs for Splunk Enterprise componentry when available—reduces bespoke `_internal` SPL drift across sites.
- **WHY:** Homogeneous KPI definitions matter when executives compare regions; bespoke per-site macros erode trust in red/green tiles.
- **HOW:** Align local threshold overrides with change records; test in non-prod SHC mirrors before promoting adaptive threshold learning to production KPIs.

### Third-party telemetry bridges

Prometheus/Grafana/Datadog estates federate through **[Splunk Observability Cloud](https://docs.splunk.com/Observability)** collectors or webhook relays—preserve **golden signal** parity (`latency`, `traffic`, `errors`, `saturation`) when migrating dashboards. The [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/trace/api/) defines consistent attribute names—`service.name`, `deployment.environment`, `k8s.*`—so third-party spans stitch to Splunk APM traces without regex archaeology.

### SRE error budgets and burn rates

Site Reliability Engineering practice ([Google SRE books](https://sre.google/books/)) frames reliability as **budgeted risk**: multi-window burn alerts fire when error budget consumption **accelerates** toward the end of the window, not merely when an absolute error count crosses a line.

- **WHAT:** Track **burn rate** (budget consumption per hour) for each SLO objective (availability, latency tail).
- **WHY:** Short bursty outages may stay under static thresholds while annihilating quarterly budget—burn catches acceleration early enough for throttle/rollback conversations.
- **HOW:** SPL or OTel-derived metrics feeding ITSI KPIs—pair burn dashboards with deployment hashes from Category **12** and Splunk platform KPIs from Category **13** so observers distinguish **feature-induced** regressions from **observability pipeline gaps**.

### AI & LLM observability edge

LLM gateways demand **token economics**, **policy-filter blocks**, **retrieval-augmented grounding failures**, and **prompt-injection mitigation telemetry** when regulated workloads adopt Copilot-style assistants.

- **WHAT:** Histogram latency per model/route, refusal counts, citation/recall scores where pipelines expose them.
- **WHY:** Slow-first-token latency differs diagnostically from slow-last-token streaming—customers perceive failures differently across ChatGPT-class UX patterns.
- **HOW:** Gateway logs plus OTel spans exported from inference middleware—normalize `gen_ai.*` semantic conventions where collectors support OpenTelemetry GenAI instrumentation previews.

---

## Category 16: Service Management & ITSM (81 use cases)

Service Management & ITSM spans [Ticketing Systems](index.html#cat-16/16.1) (27), [Configuration Management (CMDB)](index.html#cat-16/16.2) (18), [Business Process Monitoring](index.html#cat-16/16.3) (16), [Change & Release Management](index.html#cat-16/16.4) (12), and [Service Management Trending](index.html#cat-16/16.5) (8). Telemetry without ticketing context describes **pain** without **contractual consequence**—ITSM closes that gap.

### ITIL v4-aligned incident and SLA practices

**Incident management — WHAT/WHY/HOW**

- **WHAT:** Track incident lifecycle timestamps (`opened`, `assigned`, `resolved`), prioritization queues, reassignment counts, customer-visible communications.
- **WHY:** ITIL emphasizes **coordinated restoration** minimizing business impact—not merely closing tickets quickly without restoring service ([Axelos ITIL incident management practice](https://www.axelos.com/best-practice-solutions/itil)).
- **HOW:** Splunk dashboards joining vendor incidents with uptime probes—tie breaches to causal deployments via correlation UC below.

**SLA monitoring**

- **WHAT:** Percentage of incidents/meeting response/restoration targets **by priority tier**, drift trends, backlog age distributions.
- **WHY:** SLA misses imply contractual penalties or regulatory exposure—not vanity backlog charts.
- **HOW:** Scheduled Splunk searches over ITSM exports—[SLA Compliance Monitoring](index.html#uc-16.1.2), [SLA Breach Prediction](index.html#uc-16.1.14).

**MTTR analytics**

- **WHAT:** Mean and percentiles of **detection→mitigation** segmented by category (`database`, `network`, `application`).
- **WHY:** Identifies systemic tooling gaps versus training gaps—mean hides outliers important for executive narratives.
- **HOW:** Splunk joins CMDB CI categories—[MTTR by Category](index.html#uc-16.1.3).

### Change management correlation

- **WHAT:** Join change records (`CHG`) with incident spikes (`INC`) within configurable proximity windows plus blast-radius overlaps via CI relationships.
- **WHY:** Change-induced incidents remain the dominant preventable outage class when approvals lack automated guardrails.
- **HOW:** Time-based correlation searches with CMDB lookups—[Change-Incident Correlation](index.html#uc-16.1.9), [Change Success Rate](index.html#uc-16.1.4).

### Problem management hooks (ITIL continual improvement)

Beyond reactive incidents, **problem records** aggregate recurring themes—flaky tests that chronic-deploy incidents reference, database drivers that spike CPU quarterly.

- **WHAT:** Trend incident categories linked to **problem** backlog aging; measure percent incidents tied to known-error documentation vs unknown root causes.
- **WHY:** ITIL **problem management** converts incident streams into structural remediation investments rather than perpetual heroics ([Axelos ITIL practice guides](https://www.axelos.com/best-practice-solutions/itil)).
- **HOW:** Splunk schedules grouping `(short_description_signature)` clusters feeding monthly reliability reviews—pair MTTR deltas from [MTTR by Category](index.html#uc-16.1.3) with CI/CD defect density.

### ServiceNow integration via Splunk Add-on

- **WHAT:** Pull **incident, change, CMDB** entities on poll or push webhooks bidirectionally depending on architectural pattern.
- **WHY:** Splunk stays the analytics brain; ServiceNow stays the workflow system of record—duplicate UI work creates drift.
- **HOW:** Configure `Splunk_TA_snow` inputs with least-privilege service accounts—map `sys_id` fields for joins with telemetry events carrying `configuration_item` tags.

CMDB hygiene feeds **entity** quality in ITSI and database owner lookups—[CMDB Data Quality Score](index.html#uc-16.2.1).

### ITSM anchors table

| Focus | Representative UC |
|-------|---------------------|
| Contractual risk | [SLA Compliance Monitoring](index.html#uc-16.1.2), [SLA Breach Prediction](index.html#uc-16.1.14) |
| Change causality | [Change-Incident Correlation](index.html#uc-16.1.9) |

Round out volume baselines with [Incident Volume Trending](index.html#uc-16.1.1) when capacity planning for support staffing must track macro demand shifts, not single fat-finger spikes.

---

### Getting started checklist

1. **Database slow queries first** — MySQL slow log, PostgreSQL `pg_stat_statements`, SQL Server DMVs. Statement-level visibility anchors every upstream latency investigation ([Slow Query Detection](index.html#uc-7.1.1)).
2. **HTTP error rates second** — reverse proxy access logs with status, upstream_status, and timing fields. Distinguish 502 upstream from 503 overload ([HTTP Error Rate Monitoring](index.html#uc-8.1.1)).
3. **Message queue health third** — Kafka consumer lag and broker partition status. Streaming backlogs cascade into DB pressure and batch SLA misses ([Consumer Lag Monitoring](index.html#uc-8.3.1)).
4. **TLS certificate lifecycle fourth** — automate notAfter tracking before silent mobile app breakage ([SSL Certificate Monitoring](index.html#uc-8.1.5)).
5. **Splunk platform health fifth** — indexer queue fill and forwarder connectivity. If the evidence pipeline stalls, all other dashboards lie ([Indexer Queue Fill Ratio](index.html#uc-13.1.1)).
6. **CI/CD deployment events sixth** — pipeline webhooks tagged with `deployment_hash` and `service_id` for change correlation ([Failed Deployment Tracking](index.html#uc-12.2.5)).
7. **ITSM integration last** — incident and change records from ServiceNow for SLA and MTTR measurement ([SLA Compliance Monitoring](index.html#uc-16.1.2)).

## Operating the full application/service graph in Splunk

Successful programs **join categories**, not silos: database slow-query regressions appear alongside HTTP 499/502 stacks, Kafka lag, failing CI/CD gates, Splunk `_internal` queue depth, and ITSM change windows. Build saved searches that **share identifiers**—`service_id`, `deployment_hash`, `change_number`—so one drill path carries engineers from customer symptom to causal change without re-asking questions the tools already answered.

When Splunk itself shows stress ([Indexer Queue Fill Ratio](index.html#uc-13.1.1)), treat observability degradation as **incident-class**: if evidence pipelines stall, downstream MTTR metrics from Category **16** mislead leadership exactly when accuracy matters most.

Closing the loop requires **cultural** discipline alongside tooling: teams must agree which fields are mandatory (`service`, `version`, `change_number`) before dashboards graduate from pilot to enterprise mandate—otherwise joins fail silently while executives still receive green SLA tiles built on hollow extracts.

Finally, revisit thresholds quarterly: JVM heaps grow with features, Kafka topics partition with geographic expansion, and ITSM priorities shift when regulatory calendars add freeze windows. Monitoring debt is **configuration drift** measured in outdated Splunk searches as surely as stale firewall rules—schedule systematic threshold reviews tied to architecture council milestones.

Owners should align Splunk macros with **vendor minor releases**: PostgreSQL optimizer statistics behavior and SQL Server cardinality estimator shifts alter percentile envelopes—baseline searches referencing pre-upgrade steady states silently lie until recomputed against post-upgrade windows documented in vendor release notes.

Add **game-day validation** exercises that replay historical incident searches after major collector upgrades (OTel, DB Connect, Windows TA) to ensure field extractions remain stable—telemetry shape drift breaks dashboards faster than application regressions when parsers fall behind vendor log formats.

Pair documentation with **on-call playbooks** that cite which saved search backs each executive tile—transparency prevents “green dashboard syndrome” when underlying searches were disabled during a misguided cost-saving hunt.

That discipline scales when observability budgets fluctuate quarter to quarter.


