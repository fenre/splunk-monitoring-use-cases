# 3. Containers & Orchestration

## 3.1 Docker

**Primary App/TA:** Splunk Connect for Docker, custom scripted inputs

---

### UC-3.1.1 · Container Crash Loops
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Containers restarting repeatedly indicate application bugs, misconfiguration, or dependency failures. Crash loops consume resources and never reach healthy state.
- **App/TA:** Splunk Connect for Docker, Docker events via syslog
- **Data Sources:** `sourcetype=docker:events`, Docker daemon logs
- **SPL:**
```spl
index=containers sourcetype="docker:events" action="die"
| eval exit_code=exitCode
| where exit_code != "0"
| stats count as crashes by container_name, image, exit_code
| where crashes > 3
| sort -crashes
```
- **Implementation:** Install Splunk Connect for Docker or configure Docker logging driver to forward to Splunk HEC. Collect Docker events via `docker events --format '{{json .}}'`. Alert when a container restarts >3 times in 15 minutes.
- **Visualization:** Table (container, image, crashes, exit code), Bar chart by container, Timeline.
- **CIM Models:** N/A

---

### UC-3.1.2 · Container OOM Kills
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** OOM kills mean the container exceeded its memory limit. The application is either leaking memory or undersized. Data loss is likely.
- **App/TA:** Splunk Connect for Docker, host syslog
- **Data Sources:** `sourcetype=docker:events`, host `dmesg`/syslog
- **SPL:**
```spl
index=containers sourcetype="docker:events" action="oom"
| table _time container_name image host
| sort -_time

| comment "Also check host syslog for cgroup OOM"
index=os sourcetype=syslog "Memory cgroup out of memory" OR "oom-kill"
| rex "task (?<process>\S+)"
| table _time host process _raw
```
- **Implementation:** Collect Docker events and forward host syslog. Alert immediately on any OOM event. Include container memory limit in the alert context to aid right-sizing decisions.
- **Visualization:** Events timeline, Single value (OOM count last 24h), Table with container details.
- **CIM Models:** N/A

---

### UC-3.1.3 · Container CPU Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** CPU throttling means the container is hitting its CPU limit and being artificially slowed. Causes latency spikes invisible to standard CPU utilization metrics.
- **App/TA:** Custom scripted input (cgroup stats), Splunk OpenTelemetry Collector
- **Data Sources:** `sourcetype=docker:stats`, cgroup `cpu.stat`
- **SPL:**
```spl
index=containers sourcetype="docker:stats"
| eval throttle_pct = round(nr_throttled / nr_periods * 100, 1)
| where throttle_pct > 25
| stats avg(throttle_pct) as avg_throttle by container_name
| sort -avg_throttle
```
- **Implementation:** Collect Docker stats via `docker stats --format '{{json .}}'` or read cgroup files directly (`/sys/fs/cgroup/cpu/docker/<id>/cpu.stat`). Monitor `throttled_time` and `nr_throttled`. Alert when >25% of periods are throttled.
- **Visualization:** Line chart (throttle % over time), Table (container, throttle %, CPU limit), Bar chart.
- **CIM Models:** N/A

---

### UC-3.1.4 · Container Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Tracking memory usage relative to limits catches containers approaching OOM before they're killed. Enables proactive limit adjustments.
- **App/TA:** Splunk Connect for Docker, custom scripted input
- **Data Sources:** `sourcetype=docker:stats`
- **SPL:**
```spl
index=containers sourcetype="docker:stats"
| eval mem_pct = round(mem_usage / mem_limit * 100, 1)
| stats latest(mem_pct) as mem_pct by container_name
| where mem_pct > 80
| sort -mem_pct
```
- **Implementation:** Collect `docker stats` output at regular intervals. Alert when memory usage exceeds 80% of limit. Trend over time to catch gradual memory leaks.
- **Visualization:** Gauge per container, Table with limit context, Line chart (trending).
- **CIM Models:** N/A

---

### UC-3.1.5 · Image Vulnerability Scanning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Container images with known CVEs are deployed directly into production. Scanning and tracking vulnerabilities prevents running exploitable workloads.
- **App/TA:** Custom input (Trivy, Snyk, Grype JSON output)
- **Data Sources:** JSON scan results from vulnerability scanners
- **SPL:**
```spl
index=containers sourcetype="trivy:scan"
| stats count by image, Severity
| xyseries image Severity count
| sort -CRITICAL -HIGH
```
- **Implementation:** Run vulnerability scans in CI/CD pipeline (Trivy, Grype, or Snyk). Forward JSON results to Splunk via HEC. Create dashboard showing vulnerability counts per image by severity. Alert on CRITICAL vulnerabilities in production-tagged images.
- **Visualization:** Table (image, critical, high, medium, low), Stacked bar chart by image, Trend line.
- **CIM Models:** N/A

---

### UC-3.1.6 · Privileged Container Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Privileged containers have full host access — a container escape gives root on the host. Should be flagged and justified in production.
- **App/TA:** Docker events, custom audit input
- **Data Sources:** `docker inspect` output, Kubernetes pod security
- **SPL:**
```spl
index=containers sourcetype="docker:inspect"
| where Privileged="true"
| table container_name image host Privileged
```
- **Implementation:** Create scripted input: `docker inspect --format '{{.Name}} {{.HostConfig.Privileged}}' $(docker ps -q)`. Run every 300 seconds. Alert on any privileged container in production. Maintain an allowlist for justified exceptions.
- **Visualization:** Table (container, image, host), Single value (count of privileged), Status indicator.
- **CIM Models:** N/A

---

### UC-3.1.7 · Container Sprawl
- **Criticality:** 🟢 Low
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Stopped containers and dangling images waste disk space. In development environments, sprawl can consume all available storage.
- **App/TA:** Custom scripted input
- **Data Sources:** `docker ps -a`, `docker images`
- **SPL:**
```spl
index=containers sourcetype="docker:ps"
| where status="exited"
| eval days_stopped = round((now() - strptime(finished_at, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where days_stopped > 7
| stats count by host
```
- **Implementation:** Scripted input: `docker ps -a --format '{{json .}}'` and `docker system df`. Run daily. Report on stopped containers >7 days and total disk reclamation possible.
- **Visualization:** Table, Single value (reclaimable space), Bar chart by host.
- **CIM Models:** N/A

---

### UC-3.1.8 · Docker Daemon Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Docker daemon errors affect all containers on the host. Network, storage driver, and containerd errors can cause widespread container failures.
- **App/TA:** Syslog, Docker daemon log forwarding
- **Data Sources:** `/var/log/docker.log` or `journalctl -u docker`
- **SPL:**
```spl
index=containers sourcetype="docker:daemon" level="error" OR level="fatal"
| stats count by host, msg
| sort -count
```
- **Implementation:** Forward Docker daemon logs (usually via journald or `/var/log/docker.log`). Alert on fatal errors. Track error patterns by host.
- **Visualization:** Table (host, error, count), Timeline, Bar chart by error type.
- **CIM Models:** N/A

---

### UC-3.1.9 · Docker Daemon Health and Version Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Configuration
- **Value:** Docker engine responsiveness and version mismatches across fleet.
- **App/TA:** Custom scripted input (docker info, docker version)
- **Data Sources:** docker info JSON output, docker version
- **SPL:**
```spl
index=containers sourcetype="docker:info"
| stats latest(ServerVersion) as version, latest(Containers) as containers, latest(Images) as images by host
| table host version containers images _time

| comment "Version drift across hosts"
index=containers sourcetype="docker:info"
| stats values(ServerVersion) as versions by host
| eval version_count = mvcount(versions)
| where version_count > 1
| mvexpand versions
| table host versions
```
- **Implementation:** Create scripted input that runs `docker info --format '{{json .}}'` and `docker version --format '{{json .}}'` every 300 seconds. Parse ServerVersion, ServerErrors, Containers, Images, and DriverStatus. Forward to Splunk via HEC. Alert when Docker daemon is unresponsive (no data for >5 minutes) or when ServerErrors is non-empty. Report version drift: alert when multiple Engine versions exist across the fleet.
- **Visualization:** Table (host, version, containers, images), Single value (version count), Status grid (host health).
- **CIM Models:** N/A

---

### UC-3.1.10 · Container Image Vulnerability Scanning Results
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Centralizing scanner output (severity, package, image digest) proves compliance and speeds remediation when new CVEs hit production images.
- **App/TA:** Custom HEC (Trivy, Grype, Snyk JSON), CI pipeline artifacts
- **Data Sources:** `sourcetype=trivy:scan`, `sourcetype=grype:scan`
- **SPL:**
```spl
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| stats latest(Severity) as sev, values(VulnerabilityID) as cves, dc(VulnerabilityID) as vuln_count by image_name, image_digest, Target
| where mvfind(sev, "CRITICAL") OR mvfind(sev, "HIGH")
| sort -vuln_count
```
- **Implementation:** Forward CI and registry scan JSON to Splunk with stable fields (`image_name`, `image_digest`, `Target`). Deduplicate on digest+CVE. Alert when CRITICAL/HIGH appears on images referenced by running tags.
- **Visualization:** Table (image, digest, vuln count, severities), Treemap by repo, Trend (open vulns over time).
- **CIM Models:** N/A

---

### UC-3.1.11 · Docker Daemon Resource Limits Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Host-level CPU, memory, and storage pressure on the Docker engine starves containers before per-container limits trigger; early detection avoids fleet-wide slowdowns.
- **App/TA:** Splunk Connect for Docker, host metrics (Telegraf/OTel)
- **Data Sources:** `sourcetype=docker:info`, `sourcetype=docker:system`
- **SPL:**
```spl
index=containers sourcetype="docker:info"
| eval mem_total_gb=round(MemTotal/1073741824, 2)
| eval mem_avail_gb=round(MemAvailable/1073741824, 2)
| eval mem_used_pct=round((MemTotal-MemAvailable)/MemTotal*100, 1)
| where mem_used_pct > 85 OR NCPU < 2
| table _time host mem_total_gb mem_avail_gb mem_used_pct NCPU
| sort -mem_used_pct
```
- **Implementation:** Ingest `docker info` JSON (or `docker system df`) on an interval plus host memory/CPU from the node. Correlate with `docker:events` throttling and OOM. Alert when host memory used >85% or CPU saturation sustained >10 minutes.
- **Visualization:** Line chart (mem %, CPU load), Table (host, limits), Single value (hosts over threshold).
- **CIM Models:** N/A

---

### UC-3.1.12 · Compose Service Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Docker Compose stacks power dev/stage and edge; tracking service `healthcheck` state and replica counts catches bad releases before they reach Kubernetes.
- **App/TA:** Custom script (docker compose ps --format json), vector/file collector
- **Data Sources:** `sourcetype=docker:compose:ps`
- **SPL:**
```spl
index=containers sourcetype="docker:compose:ps"
| eval healthy=if(Health=="healthy",1,0)
| stats latest(Health) as health, latest(State) as state, values(Service) as services by project, Name
| where health=0 OR match(state, "^(exited|restarting)")
| table project Name health state services
```
- **Implementation:** Scheduled `docker compose -f <file> ps --format json` per project; parse `Health`, `State`, `Service`. Ship to HEC. Alert on unhealthy or restarting services for >5 minutes.
- **Visualization:** Status grid by service, Table (project, service, health), Timeline of state changes.
- **CIM Models:** N/A

---

### UC-3.1.13 · Container Restart Loop Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Rapid start/die cycles burn CPU and obscure root cause; detecting loops early isolates bad images or bad configs before cascading failures.
- **App/TA:** Splunk Connect for Docker
- **Data Sources:** `sourcetype=docker:events`
- **SPL:**
```spl
index=containers sourcetype="docker:events" action="die" OR action="start"
| bin _time span=5m
| stats dc(action) as actions, count by _time, container_name, host
| where actions>=2 AND count>=6
| sort -count
```
- **Implementation:** Track paired start/die bursts per container in sliding windows. Alert when >3 restart cycles in 15 minutes. Enrich with `exitCode` from die events.
- **Visualization:** Timeline (start/die), Table (container, cycles, host), Single value (looping containers).
- **CIM Models:** N/A

---

### UC-3.1.14 · Docker Network Overlay Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Overlay plugins (VXLAN, weave, custom bridges) failures cause intermittent connectivity between containers on different hosts.
- **App/TA:** Docker daemon logs, syslog
- **Data Sources:** `sourcetype=docker:daemon`, `sourcetype=syslog`
- **SPL:**
```spl
index=containers sourcetype="docker:daemon" (network OR overlay OR iptables OR vxlan)
| search (level="error" OR level="warn")
| stats count by host, msg
| sort -count

| comment "Host network stack"
index=os sourcetype=syslog (docker OR "br-" OR "vxlan")
| search fail OR error OR unreachable
| stats count by host, _raw
```
- **Implementation:** Forward daemon logs with network driver context. Pattern-match overlay create/delete errors, IPAM failures, and iptables sync issues. Correlate multi-host with timestamps.
- **Visualization:** Table (host, error signature, count), Timeline, Bar chart by error type.
- **CIM Models:** N/A

---

### UC-3.1.15 · Image Layer Bloat Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Large layer stacks slow pulls and increase attack surface; trending layer count and size guides image slimming and base image updates.
- **App/TA:** Custom input (`docker history --no-trunc`, `docker image inspect`)
- **Data Sources:** `sourcetype=docker:image:history`
- **SPL:**
```spl
index=containers sourcetype="docker:image:history"
| stats sum(layer_size_bytes) as total_bytes, dc(layer_id) as layer_count by image_id, repository
| eval total_mb=round(total_bytes/1048576,1)
| where layer_count>25 OR total_mb>800
| sort -total_mb
```
- **Implementation:** Nightly job exports `docker history` JSON per promoted image. Store per-layer size and count. Report images exceeding policy thresholds.
- **Visualization:** Bar chart (image vs MB), Table (image, layers, total MB), Trend (average image size).
- **CIM Models:** N/A

---

### UC-3.1.16 · Docker Volume Usage Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Named volumes grow with databases and caches; trending usage prevents write failures and emergency disk expansion.
- **App/TA:** Custom scripted input (`docker system df -v`)
- **Data Sources:** `sourcetype=docker:volumes`
- **SPL:**
```spl
index=containers sourcetype="docker:volumes"
| eval used_pct=if(SizeGB>0, round(UsedGB/SizeGB*100,1), null())
| timechart span=1d avg(UsedGB) as used_gb by volume_name
```
- **Implementation:** Parse `docker system df -v` or volume inspect into Splunk daily. Alert when volume used GB grows >20% week-over-week or host filesystem backing the volume >85%.
- **Visualization:** Line chart (used GB over time), Table (volume, host, used %), Single value (largest volume).
- **CIM Models:** N/A

---

### UC-3.1.17 · Container Resource Limit Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Verifying cgroup limits match declared `docker run`/`compose` settings catches silent misconfigurations that allow noisy neighbors or false capacity plans.
- **App/TA:** Splunk Connect for Docker
- **Data Sources:** `sourcetype=docker:inspect`
- **SPL:**
```spl
index=containers sourcetype="docker:inspect"
| eval mem_limit_bytes=tonumber(HostConfig.Memory)
| eval nano_cpus=tonumber(HostConfig.NanoCpus)
| eval cpu_quota=tonumber(HostConfig.CpuQuota)
| where isnull(mem_limit_bytes) OR mem_limit_bytes=0 OR (nano_cpus=0 AND cpu_quota<=0)
| table container_name image host mem_limit_bytes nano_cpus cpu_quota
```
- **Implementation:** Periodically ingest `docker inspect` for running containers. Flag production workloads with unlimited memory or CPU when policy requires limits. Cross-check with `docker:stats` actual usage.
- **Visualization:** Table (container, mem limit, CPU), Compliance single value (% with limits), Bar chart by host.
- **CIM Models:** N/A

---

### UC-3.1.18 · Docker Build Cache Efficiency
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Poor cache reuse lengthens CI pipelines and increases registry churn; measuring cache hits guides Dockerfile ordering and BuildKit settings.
- **App/TA:** CI log forwarding (BuildKit, docker build --progress=plain)
- **Data Sources:** `sourcetype=docker:build`
- **SPL:**
```spl
index=containers sourcetype="docker:build"
| eval cache_hit=if(match(_raw, "(?i)CACHED"),1,0)
| stats sum(cache_hit) as hits, count as steps by build_id, image_name
| eval hit_rate=round(100*hits/steps,1)
| where hit_rate < 30 AND steps>10
| sort hit_rate
```
- **Implementation:** Ship structured build logs to Splunk. Parse CACHED vs executed steps. Dashboard average cache hit rate per repo branch. Alert on sustained drop after Dockerfile changes.
- **Visualization:** Line chart (hit rate over builds), Table (repo, hit rate), Bar chart (CI duration vs hit rate).
- **CIM Models:** N/A

---

### UC-3.1.19 · Container Log Driver Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** When the logging driver backs up or errors, application logs are dropped—blinding security and operations during incidents.
- **App/TA:** Docker daemon logs, Splunk Connect for Docker
- **Data Sources:** `sourcetype=docker:daemon`
- **SPL:**
```spl
index=containers sourcetype="docker:daemon" ("log driver" OR "failed to log" OR "splunk" OR "fluentd")
| search (level="error" OR level="warn")
| stats count by host, msg
| sort -count
```
- **Implementation:** Monitor daemon for log driver write failures, buffer overflow, and remote endpoint timeouts. Correlate with missing log volume in Splunk for the same container IDs.
- **Visualization:** Table (host, error, count), Timeline, Single value (log driver errors/hour).
- **CIM Models:** N/A

---

### UC-3.1.20 · Docker Registry Mirror Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Registry mirrors reduce pull latency and hub rate limits; a stale or failing mirror causes random image pull delays across the fleet.
- **App/TA:** Docker daemon config audit, mirror HTTP checks
- **Data Sources:** `sourcetype=docker:info`, `sourcetype=docker:daemon`
- **SPL:**
```spl
index=containers sourcetype="docker:daemon" ("mirror" OR "registry-mirror" OR "connection refused")
| stats count by host, msg
| sort -count

| comment "Mirror reachability synthetic"
index=containers sourcetype="http:check" check_type="registry_mirror"
| where status!=200 OR response_time_ms>2000
| table _time mirror_url host status response_time_ms
```
- **Implementation:** Log `Registry Mirrors` from `docker info` and probe mirror `/v2/` with auth-less ping where allowed. Alert on daemon errors referencing mirrors or failed probes.
- **Visualization:** Table (mirror, status, latency), Map or bar by region, Timeline of failures.
- **CIM Models:** N/A

---

### UC-3.1.21 · Container Runtime Security Events
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Falco/sysdig/Falco-sidekick style rules surface unexpected shells, sensitive mounts, and syscall anomalies at runtime—complementing image scanning for zero-day behavior.
- **App/TA:** Falco (JSON to HEC), Sysdig Secure
- **Data Sources:** `sourcetype=falco:alert`, `sourcetype=sysdig:secure`
- **SPL:**
```spl
index=containers sourcetype="falco:alert" priority="Critical" OR priority="Error"
| stats count by rule, container.name, k8s.pod.name, proc.name
| sort -count
```
- **Implementation:** Forward Falco JSON with `rule`, `priority`, container/k8s metadata. Tune noise with allowlists. Page on Critical; dashboard top rules by container image.
- **Visualization:** Table (rule, container, count), Timeline, Heatmap (rule vs namespace).
- **CIM Models:** N/A

---

## 3.2 Kubernetes

**Primary App/TA:** Splunk OpenTelemetry Collector for Kubernetes, Splunk Connect for Kubernetes — Free

---

### UC-3.2.1 · Pod Restart Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High restart counts indicate application instability. Pods may appear "Running" but are constantly crashing and restarting, degrading service quality.
- **App/TA:** Splunk OpenTelemetry Collector for K8s
- **Data Sources:** `sourcetype=kube:container:meta`, kube-state-metrics
- **SPL:**
```spl
index=k8s sourcetype="kube:container:meta"
| stats max(restartCount) as restarts by namespace, pod_name, container_name
| where restarts > 5
| sort -restarts
```
- **Implementation:** Deploy Splunk OTel Collector as a DaemonSet. It collects container metadata including restart counts. Alert when any pod exceeds 5 restarts in 1 hour. Include the pod's last termination reason.
- **Visualization:** Table (namespace, pod, container, restarts), Bar chart by namespace, Trending line.
- **CIM Models:** N/A

---

### UC-3.2.2 · Pod Scheduling Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Pods stuck in Pending can't serve traffic. Usually caused by insufficient CPU/memory, node affinity rules, or persistent volume claim issues.
- **App/TA:** Splunk OTel Collector, Kubernetes event forwarding
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward Kubernetes events to Splunk. Alert on FailedScheduling events persisting >5 minutes. Parse the event message for the specific cause (Insufficient cpu, node affinity, PVC not bound, etc.).
- **Visualization:** Table (pod, namespace, reason), Single value (pending pods), Timeline.
- **CIM Models:** N/A

---

### UC-3.2.3 · Node NotReady Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** A NotReady node can't run pods. Existing pods are evicted after the toleration timeout (default 5 min). Causes service disruption if no replacement capacity.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:node:meta`, Kubernetes events
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="NodeNotReady"
| table _time node message
| sort -_time

| comment "Or from node conditions"
index=k8s sourcetype="kube:node:meta"
| where condition_ready="False"
| table _time node condition_ready
```
- **Implementation:** OTel Collector monitors node conditions. Alert immediately on any node transitioning to NotReady. Correlate with kubelet logs on the affected node for root cause (disk pressure, memory pressure, PID pressure, network).
- **Visualization:** Node status grid (green/red), Events timeline, Table.
- **CIM Models:** N/A

---

### UC-3.2.4 · Resource Quota Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** When namespace quotas are exhausted, new pods can't be created. Impacts deployments, autoscaling, and job scheduling within the namespace.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:resourcequota:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 80
| table namespace resource used hard used_pct
| sort -used_pct
```
- **Implementation:** kube-state-metrics exposes resource quota data. Collect via OTel Collector. Alert when any resource (cpu, memory, pods, services) exceeds 80% of quota.
- **Visualization:** Gauge per namespace/resource, Table, Bar chart by namespace.
- **CIM Models:** N/A

---

### UC-3.2.5 · Persistent Volume Claims
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Unbound PVCs prevent stateful workloads (databases, message queues) from starting. Often caused by storage class misconfiguration or capacity.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`, `sourcetype=kube:pvc:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="ProvisioningFailed" OR reason="FailedBinding"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward Kubernetes events and PVC metadata. Alert on PVCs in Pending phase >5 minutes. Include storage class and requested size in alert context.
- **Visualization:** Table (PVC, namespace, status, storage class), Status indicators.
- **CIM Models:** N/A

---

### UC-3.2.6 · Deployment Rollout Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** A failed rollout means new code isn't deploying successfully. Pods may be crash-looping, image pulls failing, or health checks not passing.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="Deployment" (reason="ProgressDeadlineExceeded" OR reason="ReplicaSetUpdated" OR reason="FailedCreate")
| table _time namespace involvedObject.name reason message
| sort -_time
```
- **Implementation:** Monitor deployment events. Alert on `ProgressDeadlineExceeded` which means the deployment failed to complete within its configured deadline. Correlate with pod events for root cause.
- **Visualization:** Table (deployment, namespace, reason), Timeline, Status panel.
- **CIM Models:** N/A

---

### UC-3.2.7 · Control Plane Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** The control plane (API server, etcd, scheduler, controller-manager) is the brain of Kubernetes. Degradation affects all cluster operations.
- **App/TA:** Splunk OTel Collector, control plane component metrics
- **Data Sources:** API server metrics, etcd metrics, scheduler/controller-manager logs
- **SPL:**
```spl
index=k8s sourcetype="kube:apiserver"
| timechart span=5m avg(apiserver_request_duration_seconds) as avg_latency by verb
| where avg_latency > 1
```
- **Implementation:** Configure OTel Collector to scrape control plane metrics endpoints (/metrics on each component). Monitor API server request latency, etcd request duration, scheduler binding latency. Alert on P99 latency >1s or error rates >1%.
- **Visualization:** Line chart (latency by verb), Single value (error rate), Multi-panel dashboard per component.
- **CIM Models:** N/A

---

### UC-3.2.8 · etcd Cluster Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** etcd stores all Kubernetes state. etcd problems (leader elections, compaction failures, high latency) cascade into cluster-wide failures.
- **App/TA:** Splunk OTel Collector, etcd metrics
- **Data Sources:** etcd Prometheus metrics (scraped by OTel)
- **SPL:**
```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_disk_wal_fsync_duration_seconds) as fsync_latency, sum(etcd_server_leader_changes_seen_total) as leader_changes
| where fsync_latency > 0.01 OR leader_changes > 0
```
- **Implementation:** Scrape etcd metrics via OTel Collector. Monitor disk fsync latency (<10ms healthy), database size, leader changes, and proposal failures. Alert on leader changes (indicates instability) and high fsync latency.
- **Visualization:** Line chart (fsync latency, db size), Single value (leader changes), Gauge (db size).
- **CIM Models:** N/A

---

### UC-3.2.9 · Ingress Error Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Ingress controllers are the front door to your services. High error rates mean users are getting errors. Catches backend failures and misconfigurations.
- **App/TA:** Ingress controller log forwarding (NGINX, Traefik, etc.)
- **Data Sources:** `sourcetype=kube:ingress:nginx` or similar
- **SPL:**
```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval is_error = if(status >= 500, 1, 0)
| timechart span=5m sum(is_error) as errors, count as total
| eval error_rate = if(total>0, round(errors/total*100, 2), 0)
| where error_rate > 5
```
- **Implementation:** Forward ingress controller access logs. Parse status code, upstream response time, and backend server. Alert when 5xx error rate exceeds 5% over 5 minutes.
- **Visualization:** Line chart (error rate over time), Table (top error paths), Single value (current error rate).
- **CIM Models:** N/A

---

### UC-3.2.10 · CrashLoopBackOff Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** CrashLoopBackOff is the most common Kubernetes failure mode. The pod is crashing, restarting, and crashing again with exponential backoff. Service is down.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:container:meta`, Kubernetes events
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="BackOff"
| stats count by namespace, involvedObject.name, message
| where count > 3
| sort -count
```
- **Implementation:** Monitor Kubernetes events for `BackOff` reason. Also check container status for `waiting.reason=CrashLoopBackOff`. Alert immediately. Include container logs in alert for diagnostic context.
- **Visualization:** Table (pod, namespace, count, message), Status panel, Single value (CrashLoop pods count).
- **CIM Models:** N/A

---

### UC-3.2.11 · HPA Scaling Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** HPA scaling events show when applications are hitting capacity. Repeated max-scale events indicate undersized limits or unexpected traffic.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="HorizontalPodAutoscaler"
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```
- **Implementation:** Forward Kubernetes events. Track scaling decisions and current vs. desired replicas. Alert when HPA reaches maxReplicas (application may be under-provisioned).
- **Visualization:** Line chart (replica count over time), Table of scaling events, Area chart.
- **CIM Models:** N/A

---

### UC-3.2.12 · RBAC Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Compliance
- **Value:** RBAC misconfigurations grant excessive permissions. Unauthorized access attempts indicate potential compromise or misconfigured service accounts.
- **App/TA:** Kubernetes audit log forwarding
- **Data Sources:** `sourcetype=kube:audit`
- **SPL:**
```spl
index=k8s sourcetype="kube:audit" responseStatus.code>=403
| stats count by user.username, verb, objectRef.resource, objectRef.namespace
| sort -count
```
- **Implementation:** Enable Kubernetes audit logging (audit policy file). Forward audit logs to Splunk. Alert on 403 Forbidden responses, especially from service accounts. Track RBAC changes (ClusterRole, ClusterRoleBinding modifications).
- **Visualization:** Table (user, resource, verb, denials), Bar chart by user, Timeline.
- **CIM Models:** N/A

---

### UC-3.2.13 · Certificate Expiration
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Kubernetes uses TLS certificates extensively (API server, kubelet, etcd). Expired certs cause cluster communication failures and outages.
- **App/TA:** cert-manager metrics, custom scripted input
- **Data Sources:** cert-manager events, `kubeadm certs check-expiration` output
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="Certificate" reason="Issuing" OR reason="Expired"
| table _time namespace involvedObject.name reason message
| sort -_time

| comment "Or from cert-manager metrics"
index=k8s sourcetype="certmanager:metrics"
| eval days_left = round((certmanager_certificate_expiration_timestamp_seconds - now()) / 86400, 0)
| where days_left < 30
```
- **Implementation:** Deploy cert-manager and scrape its metrics. Monitor certificate expiration timestamps. Alert at 30/14/7 day thresholds. For kubeadm clusters, scripted input running `kubeadm certs check-expiration`.
- **Visualization:** Table (cert, namespace, days remaining), Single value (certs expiring soon), Status indicator.
- **CIM Models:** N/A

---

### UC-3.2.14 · Container Image Pull Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** ImagePullBackOff prevents pods from starting. Caused by wrong image tags, registry auth failures, or network issues. Blocks deployments.
- **App/TA:** Splunk OTel Collector, Kubernetes events
- **Data Sources:** `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" (reason="ErrImagePull" OR reason="ImagePullBackOff" OR reason="Failed" message="*pulling image*")
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward Kubernetes events. Alert on ImagePullBackOff events. Parse the image name and registry to identify whether it's an auth issue, missing tag, or network issue.
- **Visualization:** Table (pod, image, error), Single value (pull failures last hour), Bar chart by namespace.
- **CIM Models:** N/A

---

### UC-3.2.15 · DaemonSet Completeness
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** DaemonSets (monitoring agents, log forwarders, network plugins) must run on every eligible node. Missing instances create monitoring or networking gaps.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:daemonset:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing = desiredNumberScheduled - numberReady
| where missing > 0
| table namespace daemonset_name desiredNumberScheduled numberReady missing
```
- **Implementation:** kube-state-metrics reports DaemonSet status. Alert when `numberReady < desiredNumberScheduled` for >5 minutes. Critical for infrastructure DaemonSets (CNI plugins, OTel Collector, kube-proxy).
- **Visualization:** Table (DaemonSet, desired, ready, missing), Status indicator, Single value.
- **CIM Models:** N/A

---

### UC-3.2.16 · Kubernetes PersistentVolume Claim Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** PVC approaching storage limits; prevents application failures from full volumes.
- **App/TA:** Splunk Connect for Kubernetes, metrics from kubelet
- **Data Sources:** kubelet metrics (`kubelet_volume_stats_used_bytes`, `kubelet_volume_stats_capacity_bytes`)
- **SPL:**
```spl
index=k8s sourcetype="kube:metrics" (metric_name="kubelet_volume_stats_used_bytes" OR metric_name="kubelet_volume_stats_capacity_bytes")
| stats latest(_value) as value by metric_name, namespace, persistentvolumeclaim, node
| xyseries namespace,persistentvolumeclaim,node metric_name value
| eval used_pct = round(kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100, 1)
| where used_pct > 80
| table namespace persistentvolumeclaim node used_pct kubelet_volume_stats_used_bytes kubelet_volume_stats_capacity_bytes
| sort -used_pct
```
- **Implementation:** Configure Splunk Connect for Kubernetes or OTel Collector to scrape kubelet metrics. The kubelet exposes volume stats at `/metrics` on each node. Extract `kubelet_volume_stats_used_bytes` and `kubelet_volume_stats_capacity_bytes` with labels `namespace`, `persistentvolumeclaim`. Alert when any PVC exceeds 80% capacity. Consider 90% for critical stateful workloads.
- **Visualization:** Gauge per PVC, Table (namespace, PVC, node, used %, bytes), Line chart (trend over time).
- **CIM Models:** N/A

---

### UC-3.2.17 · Kubernetes HorizontalPodAutoscaler Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** HPA at max replicas, unable to scale, or flapping between min and max.
- **App/TA:** Splunk Connect for Kubernetes
- **Data Sources:** kube-state-metrics (`kube_horizontalpodautoscaler_status_current_replicas`, `kube_horizontalpodautoscaler_spec_min_replicas`, `kube_horizontalpodautoscaler_spec_max_replicas`)
- **SPL:**
```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_*"
| stats latest(_value) as value by metric_name, namespace, horizontalpodautoscaler
| eval current_replicas = case(metric_name="kube_horizontalpodautoscaler_status_current_replicas", value)
| eval min_replicas = case(metric_name="kube_horizontalpodautoscaler_spec_min_replicas", value)
| eval max_replicas = case(metric_name="kube_horizontalpodautoscaler_spec_max_replicas", value)
| stats max(current_replicas) as current_replicas, max(min_replicas) as min_replicas, max(max_replicas) as max_replicas by namespace, horizontalpodautoscaler
| eval at_max = if(current_replicas >= max_replicas AND max_replicas > 0, 1, 0)
| where at_max=1
| table namespace horizontalpodautoscaler current_replicas min_replicas max_replicas
| sort -current_replicas
```
- **Implementation:** Collect kube-state-metrics HPA series via Splunk Connect for Kubernetes. Alert when `current_replicas == max_replicas` (HPA cannot scale further; application may be under-provisioned). Also alert on rapid replica flapping (e.g. current oscillating between min and max within 10 minutes) indicating unstable scaling.
- **Visualization:** Table (HPA, namespace, current, min, max), Status indicator (at max = warning), Line chart (replicas over time).
- **CIM Models:** N/A

---

### UC-3.2.18 · Kubernetes Ingress Backend Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Ingress controller returning 502/503 due to unhealthy backends.
- **App/TA:** Splunk Connect for Kubernetes, ingress controller logs
- **Data Sources:** nginx-ingress controller logs, traefik logs
- **SPL:**
```spl
index=k8s (sourcetype="kube:ingress:nginx" OR sourcetype="kube:ingress:traefik")
| eval is_backend_error = if(status>=502 AND status<=503, 1, 0)
| bin _time span=5m
| stats sum(is_backend_error) as backend_errors, count as total by host, path, upstream, _time
| eval error_rate = if(total>0, round(backend_errors/total*100, 2), 0)
| where error_rate > 5 OR backend_errors > 10
| table _time host path upstream backend_errors total error_rate
| sort -error_rate
```
- **Implementation:** Forward ingress controller access logs to Splunk. For NGINX Ingress, enable access log format with `$upstream_addr` and `$upstream_status`. For Traefik, enable access logs with backend info. Parse status, host, path, and upstream. Alert when 502/503 rate exceeds 5% over 5 minutes or absolute count >10. Correlate with pod readiness and service endpoints.
- **Visualization:** Table (host, path, upstream, errors, rate), Line chart (error rate over time), Single value (current 5xx rate).
- **CIM Models:** N/A

---

### UC-3.2.19 · Kubernetes DaemonSet Missing Pods
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** DaemonSet pods not running on all expected nodes.
- **App/TA:** Splunk Connect for Kubernetes
- **Data Sources:** kube-state-metrics (`kube_daemonset_status_desired_number_scheduled`, `kube_daemonset_status_current_number_scheduled`, `kube_daemonset_status_number_ready`)
- **SPL:**
```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing_scheduled = desiredNumberScheduled - currentNumberScheduled
| eval missing_ready = desiredNumberScheduled - numberReady
| where missing_scheduled > 0 OR missing_ready > 0
| table namespace daemonset_name desiredNumberScheduled currentNumberScheduled numberReady missing_scheduled missing_ready
| sort -missing_ready
```
- **Implementation:** kube-state-metrics exposes DaemonSet status. Splunk Connect for Kubernetes collects this. Alert when `currentNumberScheduled < desiredNumberScheduled` (pods not scheduled) or `numberReady < desiredNumberScheduled` (pods scheduled but not ready). Critical for CNI, kube-proxy, and monitoring DaemonSets. Investigate node taints, resource constraints, or image pull issues.
- **Visualization:** Table (DaemonSet, desired, scheduled, ready, missing), Status grid by DaemonSet, Single value (DaemonSets with gaps).
- **CIM Models:** N/A

---

### UC-3.2.20 · Kubernetes Job and CronJob Failure Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Failed jobs and missed cron schedules.
- **App/TA:** Splunk Connect for Kubernetes
- **Data Sources:** kube-state-metrics (`kube_job_status_failed`, `kube_cronjob_status_last_schedule_time`)
- **SPL:**
```spl
index=k8s sourcetype="kube:events" (involvedObject.kind="Job" OR involvedObject.kind="CronJob") (reason="Failed" OR reason="BackoffLimitExceeded")
| stats count by namespace, involvedObject.name, involvedObject.kind, message
| sort -count

| comment "CronJob missed schedule - last_schedule_time stale"
index=k8s sourcetype="kube:metrics" metric_name="kube_cronjob_status_last_schedule_time"
| eval hours_since_schedule = (now() - _value) / 3600
| where hours_since_schedule > 2
| table namespace cronjob hours_since_schedule _value
```
- **Implementation:** Forward Kubernetes events for Job/CronJob failures. Collect `kube_job_status_failed` and `kube_cronjob_status_last_schedule_time` from kube-state-metrics. Alert on any Job with `failed > 0` or BackoffLimitExceeded. For CronJobs, alert when `last_schedule_time` is older than expected (e.g. 2x the cron interval) indicating missed runs.
- **Visualization:** Table (job/cronjob, namespace, failures, message), Line chart (failure rate over time), Single value (failed jobs last 24h).
- **CIM Models:** N/A

---

### UC-3.2.21 · Kubernetes Admission Webhook Latency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Slow webhooks causing API server delays and impacting cluster operations.
- **App/TA:** Splunk Connect for Kubernetes
- **Data Sources:** apiserver metrics (`apiserver_admission_webhook_admission_duration_seconds`)
- **SPL:**
```spl
index=k8s sourcetype="kube:apiserver" metric_name="apiserver_admission_webhook_admission_duration_seconds"
| bin _time span=5m
| stats avg(_value) as avg_sec, max(_value) as max_sec, count by webhook, operation, _time
| where avg_sec > 0.5 OR max_sec > 2
| table _time webhook operation avg_sec max_sec count
| sort -avg_sec
```
- **Implementation:** Scrape API server metrics (typically via kube-apiserver /metrics or OTel Collector). The `apiserver_admission_webhook_admission_duration_seconds` histogram has labels `name` (webhook) and `operation`. Alert when P99 or average exceeds 500ms. Slow webhooks (e.g. OPA, Kyverno, cert-manager) block all API requests. Identify and optimize or remove slow webhooks.
- **Visualization:** Table (webhook, operation, avg, max latency), Line chart (latency over time by webhook), Heatmap.
- **CIM Models:** N/A

---

### UC-3.2.22 · Pod Security Admission Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** PSA denials block risky pods at admission; tracking them exposes misconfigured workloads and policy gaps before they reach production namespaces.
- **App/TA:** Kubernetes audit log forwarding
- **Data Sources:** `sourcetype=kube:audit`
- **SPL:**
```spl
index=k8s sourcetype="kube:audit" objectRef.resource="pods"
| search "PodSecurity" OR "pod-security.kubernetes.io" OR "denied the request"
| stats count by user.username, objectRef.namespace, objectRef.name, responseStatus.reason
| sort -count
```
- **Implementation:** Enable audit policy capturing Pod create/update denials. Parse PSA-specific messages. Alert on spikes in a namespace or repeated denials for the same workload pattern.
- **Visualization:** Table (namespace, user, count), Bar chart by namespace, Timeline.
- **CIM Models:** N/A

---

### UC-3.2.23 · RBAC Audit Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** ClusterRoleBinding changes and cluster-admin paths are high-risk; structured audit analysis supports least-privilege reviews and incident response.
- **App/TA:** Kubernetes audit to Splunk (HEC)
- **Data Sources:** `sourcetype=kube:audit`
- **SPL:**
```spl
index=k8s sourcetype="kube:audit" verb="create" OR verb="patch" OR verb="update"
| where objectRef.resource="clusterroles" OR objectRef.resource="clusterrolebindings" OR objectRef.resource="roles" OR objectRef.resource="rolebindings"
| stats count by user.username, objectRef.resource, objectRef.name, verb
| sort -count
```
- **Implementation:** Retain audit JSON with `user`, `verb`, `objectRef`. Scheduled reports for RBAC mutations; alert on non-break-glass users attaching `cluster-admin` bindings.
- **Visualization:** Table (user, resource, object), Timeline of changes, Bar chart by user.
- **CIM Models:** N/A

---

### UC-3.2.24 · HPA Scale-Out Event Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Correlating HPA decisions with replica metrics explains surprise scale-outs and validates max replica settings under load.
- **App/TA:** Splunk OTel Collector, kube-state-metrics
- **Data Sources:** `sourcetype=kube:objects:events`, `sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:objects:events" involvedObject.kind="HorizontalPodAutoscaler"
| stats latest(message) as msg, count by namespace, involvedObject.name, reason
| sort -count

| comment "Current replicas"
index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_status_current_replicas"
| stats latest(_value) as current by namespace, horizontalpodautoscaler
| join type=left namespace horizontalpodautoscaler [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_spec_max_replicas"
    | stats latest(_value) as max_rep by namespace, horizontalpodautoscaler
]
| where current>=max_rep AND max_rep>0
| table namespace horizontalpodautoscaler current max_rep
```
- **Implementation:** Ingest HPA events and kube-state-metrics HPA series. Join current replicas with event stream for postmortems. Alert when scaling messages repeat while replicas stay at max.
- **Visualization:** Line chart (replicas over time), Table (HPA, events), Single value (scale events/hour).
- **CIM Models:** N/A

---

### UC-3.2.25 · PV/PVC Capacity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Proactive free-space visibility on bound PVs avoids read-only filesystems and database corruption across the cluster.
- **App/TA:** Splunk OTel Collector (kubelet metrics)
- **Data Sources:** `sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:metrics" metric_name="kubelet_volume_stats_used_bytes"
| stats latest(_value) as used by namespace, persistentvolumeclaim, node
| join type=left namespace persistentvolumeclaim node [
    search index=k8s sourcetype="kube:metrics" metric_name="kubelet_volume_stats_capacity_bytes"
    | stats latest(_value) as cap by namespace, persistentvolumeclaim, node
]
| eval used_pct=if(cap>0, round(used/cap*100,1), null())
| where used_pct>85
| table namespace persistentvolumeclaim node used_pct used cap
| sort -used_pct
```
- **Implementation:** Scrape kubelet volume stats with PVC labels. Dashboard all namespaces; alert at 85%/95% tiers. Include storage class in lookup tables for business priority.
- **Visualization:** Gauge per PVC, Table (namespace, PVC, used %), Heatmap (node × PVC).
- **CIM Models:** N/A

---

### UC-3.2.26 · etcd Health and Latency
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** etcd request latency and raft health predict API slowness and split-brain risk; early warning preserves control plane stability.
- **App/TA:** Splunk OTel Collector
- **Data Sources:** `sourcetype=kube:etcd`
- **SPL:**
```spl
index=k8s sourcetype="kube:etcd"
| timechart span=5m avg(etcd_network_peer_round_trip_time_seconds) as rtt, avg(etcd_disk_backend_commit_duration_seconds) as commit
| where rtt>0.05 OR commit>0.1
```
- **Implementation:** Scrape etcd `/metrics` from members (managed clusters: use cloud metrics export if direct scrape is blocked). Alert on rising commit duration, peer RTT, or leader election counters.
- **Visualization:** Line chart (latency, DB size), Single value (leader changes), Table (member ID, health).
- **CIM Models:** N/A

---

### UC-3.2.27 · Ingress Controller Error Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Controller-level 5xx and upstream errors isolate bad ingress classes, TLS backends, and canary routes before user-facing SLO breach.
- **App/TA:** Ingress controller log pipeline (NGINX, Traefik, HAProxy)
- **Data Sources:** `sourcetype=kube:ingress:nginx`
- **SPL:**
```spl
index=k8s sourcetype="kube:ingress:nginx"
| eval err=if(status>=500,1,0)
| bin _time span=5m
| stats sum(err) as e, count as n by ingress_class, upstream, _time
| eval err_rate=if(n>0, round(100*e/n,2), 0)
| where err_rate>2
| sort -err_rate
```
- **Implementation:** Standardize access log JSON with `ingress_class`, `upstream`, `status`. Baseline per ingress. Alert on error rate versus 7-day same-hour baseline.
- **Visualization:** Line chart (5xx rate by class), Table (upstream, err %), Single value (global ingress 5xx/min).
- **CIM Models:** N/A

---

### UC-3.2.28 · Node Pressure Conditions (Disk/Memory/PID)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Kubelet pressure conditions drive evictions; monitoring them reduces surprise pod kills and scheduling failures.
- **App/TA:** Splunk OTel Collector, node exporter
- **Data Sources:** `sourcetype=kube:node:meta`, `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:node:meta"
| where condition_memory_pressure="True" OR condition_disk_pressure="True" OR condition_pid_pressure="True"
| table _time node condition_memory_pressure condition_disk_pressure condition_pid_pressure

| comment "Related events"
index=k8s sourcetype="kube:events" (reason="EvictionThresholdMet" OR reason="FreeDiskSpaceFailed")
| stats count by involvedObject.kind, involvedObject.name, message
```
- **Implementation:** Ingest node conditions from kube-state-metrics or OTel node receiver. Correlate with eviction events and node `Allocatable` vs usage. Page on any pressure True >2 minutes.
- **Visualization:** Node heatmap (pressure flags), Timeline (evictions), Table (node, condition).
- **CIM Models:** N/A

---

### UC-3.2.29 · CronJob Failure Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Missed batch jobs break SLAs for reporting and cleanup; tracking last successful run and Job failures closes blind spots.
- **App/TA:** Splunk OTel Collector
- **Data Sources:** `sourcetype=kube:events`, `sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" involvedObject.kind="Job" (reason="BackoffLimitExceeded" OR reason="Failed")
| stats count by namespace, involvedObject.name, message
| sort -count

| comment "Stale CronJob schedule"
index=k8s sourcetype="kube:metrics" metric_name="kube_cronjob_status_last_schedule_time"
| eval hours_since=(now()-_value)/3600
| where hours_since>24
| table namespace cronjob hours_since
```
- **Implementation:** Combine event-based failures with `kube_cronjob_status_last_schedule_time` staleness versus expected schedule. Alert when no successful Job completion in expected window.
- **Visualization:** Table (cronjob, last schedule, failures), Line chart (failure count), Single value (failed jobs 24h).
- **CIM Models:** N/A

---

### UC-3.2.30 · Init Container Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Failed inits block app containers entirely; fast detection shortens MTTR for migrations and secret-fetch steps.
- **App/TA:** Kubernetes events, container status JSON
- **Data Sources:** `sourcetype=kube:objects:events`, `sourcetype=kube:container:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:objects:events" "*init container*" (Failed OR Error)
| stats count by namespace, involvedObject.name, message
| sort -count

| comment "Init container state"
index=k8s sourcetype="kube:container:meta" init="true"
| where exit_code!=0 OR state="waiting"
| table namespace pod_name container_name state exit_code
```
- **Implementation:** Forward events mentioning init containers; optionally ingest pod status subresource via exporter. Alert on non-zero init exit or ImagePull errors on init images.
- **Visualization:** Table (pod, init container, reason), Timeline, Single value (failed inits/hour).
- **CIM Models:** N/A

---

### UC-3.2.31 · Sidecar Injection Validation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures service mesh or security sidecars are present where policy requires—avoiding accidental unencrypted east-west traffic.
- **App/TA:** kube-state-metrics, policy controller (optional)
- **Data Sources:** `sourcetype=kube:pod:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:pod:meta"
| eval has_proxy=if(match(container_names, "(istio-proxy|linkerd-proxy|envoy)"),1,0)
| where namespace_injection_enabled=1 AND has_proxy=0
| table namespace pod_name container_names
```
- **Implementation:** Periodically snapshot pod container lists and namespace labels (`istio-injection`, etc.). Flag mismatches. Integrate with CI to fail deploys that skip injection in labeled namespaces.
- **Visualization:** Table (namespace, pod, missing sidecar), Compliance %, Bar chart by team.
- **CIM Models:** N/A

---

### UC-3.2.32 · Namespace Quota Utilization Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Namespaces hitting CPU/memory/object quotas block rollouts; trending utilization prevents deployment freezes during releases.
- **App/TA:** Splunk OTel Collector
- **Data Sources:** `sourcetype=kube:resourcequota:meta`
- **SPL:**
```spl
index=k8s sourcetype="kube:resourcequota:meta"
| eval used_pct = round(used / hard * 100, 1)
| where used_pct > 90
| table namespace resource used hard used_pct
| sort -used_pct
```
- **Implementation:** Same quota feed as UC-3.2.4; use a stricter 90% threshold for release windows. Split alerts by resource type (cpu, memory, pods).
- **Visualization:** Stacked bar (used vs hard), Gauge per quota, Table.
- **CIM Models:** N/A

---

### UC-3.2.33 · Node Drain Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Draining nodes for maintenance evicts workloads; correlating drains with pod disruption helps explain transient unavailability.
- **App/TA:** Kubernetes audit, controller logs
- **Data Sources:** `sourcetype=kube:audit`, `sourcetype=kube:objects:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:audit" objectRef.resource="nodes" (verb="patch" OR verb="update")
| search "unschedulable" OR "NoSchedule"
| stats count by user.username, objectRef.name
| sort -count

| comment "Drain-related events"
index=k8s sourcetype="kube:objects:events" "*drain*" OR reason="NodeSchedulable"
| table _time involvedObject.name message
```
- **Implementation:** Capture cordon/drain API calls via audit. Dashboard maintenance windows. Alert on unexpected uncordon outside change windows.
- **Visualization:** Timeline (drain/cordon), Table (user, node), Map of affected nodes.
- **CIM Models:** N/A

---

### UC-3.2.34 · Cluster DNS Resolution Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** CoreDNS failures cause widespread `SERVFAIL` and intermittent app errors; monitoring query errors and upstream timeouts is essential.
- **App/TA:** CoreDNS log forwarding, Prometheus metrics
- **Data Sources:** `sourcetype=kube:coredns`, `sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:coredns" (SERVFAIL OR timeout OR "i/o timeout")
| stats count by qname, rcode, pod_name
| sort -count

| comment "Response codes"
index=k8s sourcetype="kube:metrics" metric_name="coredns_dns_responses_total"
| stats sum(_value) as responses by rcode
| where rcode!="NOERROR" AND rcode!="NXDOMAIN"
```
- **Implementation:** Forward CoreDNS logs with response code. Scrape `coredns_dns_responses_total` by rcode. Alert on SERVFAIL spike or upstream forward errors.
- **Visualization:** Line chart (errors by rcode), Table (qname, count), Single value (SERVFAIL/min).
- **CIM Models:** N/A

---

### UC-3.2.35 · Pod Anti-Affinity Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Scheduling cannot always satisfy anti-affinity; detecting pending pods or topology spread skew avoids accidental single-AZ concentration.
- **App/TA:** kube-scheduler logs, Kubernetes events
- **Data Sources:** `sourcetype=kube:scheduler`, `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| search "affinity" OR "anti-affinity" OR "topology spread"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Capture scheduler `FailedScheduling` messages with affinity terms. Optional: compare replica distribution by zone label versus `topologySpreadConstraints`. Alert when scheduling failures mention anti-affinity for >10 minutes.
- **Visualization:** Table (pod, message), Bar chart by zone (replica counts), Timeline.
- **CIM Models:** N/A

---

### UC-3.2.36 · Namespace Resource Limit Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** `LimitRange` defaults and max per-container caps prevent one pod from consuming a whole namespace budget; violations indicate chart misconfigurations.
- **App/TA:** Kubernetes events, admission audit
- **Data Sources:** `sourcetype=kube:objects:events`, `sourcetype=kube:audit`
- **SPL:**
```spl
index=k8s sourcetype="kube:objects:events" "*LimitRange*" OR "*exceeds limit*"
| stats count by namespace, involvedObject.name, message
| sort -count

| comment "Admission denied"
index=k8s sourcetype="kube:audit" objectRef.resource="pods" responseStatus.code=422
| stats count by objectRef.namespace, user.username
```
- **Implementation:** Track events when requests exceed LimitRange. Use audit 422 responses. Dashboard per namespace against documented standards.
- **Visualization:** Table (namespace, workload, reason), Timeline, Single value (limit violations/day).
- **CIM Models:** N/A

---

### UC-3.2.37 · Pod Disruption Budget Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** PDBs protect availability during voluntary disruptions; monitoring expected vs healthy pods avoids accidental full service outages during drains.
- **App/TA:** kube-state-metrics
- **Data Sources:** `sourcetype=kube:metrics`, `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_poddisruptionbudget_status_expected_pods"
| stats latest(_value) as expected by namespace, poddisruptionbudget
| join type=left namespace poddisruptionbudget [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_poddisruptionbudget_status_current_healthy"
    | stats latest(_value) as healthy by namespace, poddisruptionbudget
]
| where isnotnull(healthy) AND healthy<expected
| table namespace poddisruptionbudget expected healthy
```
- **Implementation:** Scrape PDB status metrics; correlate with `Cannot evict pod` events during drains. Alert when healthy < expected minimum for PDB.
- **Visualization:** Table (PDB, healthy vs expected), Timeline (blocked evictions), Status panel.
- **CIM Models:** N/A

---

### UC-3.2.38 · Vertical Pod Autoscaler Recommendations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** VPA recommendation divergence from actual requests drives right-sizing and prevents CPU starvation when recommendations are not applied.
- **App/TA:** VPA metrics export, `kubectl describe vpa` JSON job
- **Data Sources:** `sourcetype=kube:metrics`, `sourcetype=kube:vpa:status`
- **SPL:**
```spl
index=k8s sourcetype="kube:metrics" metric_name="vpa_recommendation_target_cpu"
| stats latest(_value) as target_millicores by namespace, verticalpodautoscaler
| join type=left namespace verticalpodautoscaler [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_pod_container_resource_requests" resource="cpu"
    | stats latest(_value) as request_millicores by namespace, pod
]
| eval gap_m=abs(target_millicores-request_millicores)
| where gap_m>500
| table namespace verticalpodautoscaler target_millicores request_millicores gap_m
```
- **Implementation:** Ingest VPA recommendation metrics (or periodic JSON status). Compare recommendation to live requests. Alert on large sustained gaps for tier-1 workloads.
- **Visualization:** Table (workload, target vs request), Line chart (recommendation drift), Bar chart (gap).
- **CIM Models:** N/A

---

### UC-3.2.39 · Kubernetes Events Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Sudden `Warning` event storms often precede control plane or network incidents; statistical baselines catch abnormal rates per namespace.
- **App/TA:** Splunk ML Toolkit (optional) or scheduled analytics
- **Data Sources:** `sourcetype=kube:objects:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:objects:events" type="Warning"
| bin _time span=15m
| stats count as warn_count by _time, namespace
| eventstats avg(warn_count) as avg_w stdev(warn_count) as sd by namespace
| eval z=if(sd>0 AND sd!=null, (warn_count-avg_w)/sd, 0)
| where abs(z)>3 AND warn_count>10
| table _time namespace warn_count avg_w z
| sort -warn_count
```
- **Implementation:** Baseline Warning rate per namespace with rolling stdev. Tune thresholds for chatty namespaces. Optional: replace with `anomalydetection` or MLTK for seasonality.
- **Visualization:** Timechart with overlay, Table (namespace, spike z-score), Single value (anomaly intervals).
- **CIM Models:** N/A

---

### UC-3.2.40 · Persistent Volume Snapshot Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Failed or stale snapshots break restore RPO; monitoring `VolumeSnapshot` and CSI driver status supports backup verification.
- **App/TA:** Kubernetes events, CSI driver metrics
- **Data Sources:** `sourcetype=kube:objects:events`, `sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:objects:events" involvedObject.kind="VolumeSnapshot" (Failed OR Error)
| stats count by namespace, involvedObject.name, message
| sort -count

| comment "Snapshot not ready"
index=k8s sourcetype="kube:metrics" metric_name="kube_volume_snapshot_ready"
| where _value=0
| table namespace volumesnapshot _time
```
- **Implementation:** Forward VolumeSnapshot events and optional readiness gauge from CSI. Alert on failed snapshot jobs or readiness stuck false >1 hour.
- **Visualization:** Table (snapshot, status), Timeline, Single value (failed snapshots 24h).
- **CIM Models:** N/A

---

### UC-3.2.41 · Service Endpoint Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Services with zero ready endpoints drop traffic for ClusterIP clients; fast detection isolates label selector and readiness probe issues.
- **App/TA:** kube-state-metrics
- **Data Sources:** `sourcetype=kube:metrics`
- **SPL:**
```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_endpoint_address_available"
| stats latest(_value) as avail by namespace, service
| join type=left namespace service [
    search index=k8s sourcetype="kube:metrics" metric_name="kube_endpoint_address_not_ready"
    | stats latest(_value) as not_ready by namespace, service
]
| where avail=0 OR not_ready>0
| table namespace service avail not_ready
```
- **Implementation:** Scrape EndpointSlice metrics (`kube_endpoint_*`). Exclude headless where appropriate. Alert when `available==0` for production Services.
- **Visualization:** Table (service, endpoints), Status grid, Line chart (ready endpoints).
- **CIM Models:** N/A

---

### UC-3.2.42 · Kubelet Certificate Rotation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Kubelet client/server cert expiry breaks node registration and pod lifecycle; tracking rotation events prevents surprise NotReady storms.
- **App/TA:** kubelet logs, node cert exporter
- **Data Sources:** `sourcetype=kube:kubelet`, `sourcetype=kube:node:cert`
- **SPL:**
```spl
index=k8s sourcetype="kube:kubelet" ("certificate" OR "x509" OR "rotate")
| search fail OR error OR expired
| stats count by host, message
| sort -count

| comment "Structured notAfter"
index=k8s sourcetype="kube:node:cert" role="kubelet"
| eval days_left=round((not_after-now())/86400,0)
| where days_left<30
| table host role days_left
```
- **Implementation:** Forward kubelet logs and optional script exporting kubelet cert `NotAfter`. Alert at 30/14 days for self-managed rotation.
- **Visualization:** Table (node, days left), Timeline (rotation success), Single value (nodes expiring <30d).
- **CIM Models:** N/A

---

### UC-3.2.43 · Container Probe Failure Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Repeated readiness/liveness probe failures indicate dependency outages or mis-tuned thresholds before user-visible errors dominate.
- **App/TA:** kubelet logs, Kubernetes events
- **Data Sources:** `sourcetype=kube:kubelet`, `sourcetype=kube:objects:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:kubelet" ("Probe failed" OR "Liveness probe failed" OR "Readiness probe failed")
| stats count by host, pod, container
| sort -count

| comment "Unhealthy events"
index=k8s sourcetype="kube:objects:events" reason="Unhealthy"
| stats count by namespace, involvedObject.name, message
```
- **Implementation:** Collect kubelet probe log lines. Bucket by container. Alert on sustained probe failure rate after deployments.
- **Visualization:** Table (pod, container, count), Timeline, Bar chart by workload.
- **CIM Models:** N/A

---

### UC-3.2.44 · Node Pool Auto-Repair Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Managed Kubernetes auto-replace unhealthy nodes; tracking repairs explains brief capacity dips and correlates with hardware or image issues.
- **App/TA:** Cloud cluster logs (EKS, GKE, AKS) to Splunk
- **Data Sources:** `sourcetype=aws:eks:node`, `sourcetype=gcp:gke:operation`, `sourcetype=azure:aks:node`
- **SPL:**
```spl
index=cloud (sourcetype="aws:eks:node" OR sourcetype="gcp:gke:operation" OR sourcetype="azure:aks:node")
| search repair OR replace OR recreate OR "auto repair"
| stats count by cluster_name, node_pool, _raw
| sort -_time
```
- **Implementation:** Export node pool operations via cloud add-ons or EventBridge/Activity Log. Tag auto-repair operations. Alert on repair rate spike versus baseline.
- **Visualization:** Timeline (repairs), Table (pool, message), Single value (repairs/day).
- **CIM Models:** N/A

---

### UC-3.2.45 · Admission Webhook Latency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** P95/P99 webhook latency drives API server tail latency; isolating slow validating/mutating hooks prevents global API degradation.
- **App/TA:** Splunk OTel Collector (apiserver metrics)
- **Data Sources:** `sourcetype=kube:apiserver`
- **SPL:**
```spl
index=k8s sourcetype="kube:apiserver" metric_name="apiserver_admission_webhook_admission_duration_seconds"
| bin _time span=5m
| stats perc95(_value) as p95, perc99(_value) as p99 by name, operation, _time
| where p95>0.25 OR p99>1
| sort -p99
```
- **Implementation:** Same histogram as UC-3.2.21; emphasize percentile SLOs per webhook `name` and `operation`. Page on P99 >1s for production webhooks.
- **Visualization:** Line chart (p95/p99 by webhook), Table (webhook, p99), Heatmap.
- **CIM Models:** N/A

---

### UC-3.2.46 · Cluster Autoscaler Pending Pods
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Cluster autoscaler unable to scale out leaves pods pending during traffic spikes; monitoring pending duration and CA logs protects scale-out SLAs.
- **App/TA:** cluster-autoscaler logs, Kubernetes events
- **Data Sources:** `sourcetype=kube:cluster-autoscaler`, `sourcetype=kube:events`
- **SPL:**
```spl
index=k8s sourcetype="kube:cluster-autoscaler" ("scale-up" OR "failed" OR "NotTriggeredScaleUp")
| stats count by cluster_name, _raw
| sort -count

| comment "Long-pending pods"
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| eval age_sec=now()-_time
| where age_sec>300
| stats max(age_sec) as max_pending by namespace, involvedObject.name, message
| sort -max_pending
```
- **Implementation:** Forward cluster-autoscaler Deployment logs. Correlate `NotTriggeredScaleUp` with max node pool size and quotas. Alert when scheduling failures persist >5 minutes while CA reports scale blocked.
- **Visualization:** Table (reason, count), Timeline (scale-up), Single value (pending pods).
- **CIM Models:** N/A

---

## 3.3 OpenShift

**Primary App/TA:** OpenTelemetry Collector, OpenShift audit log forwarding

---

### UC-3.3.1 · Cluster Version & Upgrade Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** OpenShift upgrades can stall. Tracking upgrade progress and version across clusters ensures consistency and support compliance.
- **App/TA:** Custom API input (ClusterVersion API)
- **Data Sources:** ClusterVersion resource, OpenShift events
- **SPL:**
```spl
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available by cluster
| table cluster version upgrading available
```
- **Implementation:** Create scripted input querying `oc get clusterversion -o json`. Run hourly. Alert when upgrade is progressing but stalled (>2 hours without progress).
- **Visualization:** Table (cluster, version, status), Status indicator.
- **CIM Models:** N/A

---

### UC-3.3.2 · Operator Degraded Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **Value:** Cluster operators manage core OpenShift components (networking, ingress, monitoring, authentication). Degraded operators mean partial cluster functionality loss.
- **App/TA:** Custom API input
- **Data Sources:** ClusterOperator resources
- **SPL:**
```spl
index=openshift sourcetype="openshift:clusteroperator"
| where degraded="True" OR available="False"
| table _time cluster operator degraded available message
| sort -_time
```
- **Implementation:** Scripted input: `oc get clusteroperators -o json`. Run every 300 seconds. Alert when any operator reports `Degraded=True` or `Available=False`.
- **Visualization:** Operator status grid (green/yellow/red), Table with details, Timeline.
- **CIM Models:** N/A

---

### UC-3.3.3 · Build Failure Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** OpenShift Source-to-Image (S2I) build failures block application deployments. Trend analysis reveals systemic build infrastructure issues.
- **App/TA:** OpenShift event forwarding
- **Data Sources:** `sourcetype=kube:events` (Build events)
- **SPL:**
```spl
index=openshift sourcetype="kube:events" involvedObject.kind="Build" reason="BuildFailed"
| stats count by namespace, involvedObject.name, message
| sort -count
```
- **Implementation:** Forward OpenShift events. Alert on BuildFailed events. Track build success/failure rate per namespace over time. Investigate common failure reasons (image pull, compile errors, push failures).
- **Visualization:** Table (build, namespace, reason), Line chart (success rate %), Bar chart by failure type.
- **CIM Models:** N/A

---

### UC-3.3.4 · SCC Violation Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Security Context Constraint violations mean pods are attempting to run with permissions beyond their allowed scope. Could indicate misconfiguration or an attack.
- **App/TA:** OpenShift audit log forwarding
- **Data Sources:** `sourcetype=openshift:audit`
- **SPL:**
```spl
index=openshift sourcetype="openshift:audit" responseStatus.code=403 objectRef.resource="pods"
| search "unable to validate against any security context constraint"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```
- **Implementation:** Enable and forward OpenShift audit logs. Alert on SCC-related 403 errors. Track which SCCs are most commonly requested and denied.
- **Visualization:** Table (user, namespace, pod, SCC requested), Bar chart by SCC, Timeline.
- **CIM Models:** N/A

---

### UC-3.3.5 · Helm Release Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Deployed state differs from declared chart version.
- **App/TA:** Custom scripted input (helm list --output json)
- **Data Sources:** helm list output, GitOps desired state
- **SPL:**
```spl
index=k8s sourcetype="helm:list"
| stats latest(chart) as chart, latest(app_version) as app_version, latest(updated) as updated by namespace, name
| table namespace name chart app_version updated

| comment "Compare with GitOps desired state"
index=k8s (sourcetype="helm:list" OR sourcetype="gitops:desired")
| eval chart_version = mvindex(split(chart, "-"), -1)
| stats values(chart_version) as versions by namespace, name, source
| eval version_count = mvcount(versions)
| where version_count > 1
| table namespace name versions source
```
- **Implementation:** Scripted input: `helm list -A -o json` (all namespaces). Parse name, namespace, chart (includes version), app_version, status, updated. Run every 600 seconds. Optionally ingest GitOps desired state (Argo CD, Flux) from API or Git. Compare deployed chart version to desired. Alert when drift detected (deployed != desired). Useful for detecting manual changes or failed syncs.
- **Visualization:** Table (namespace, release, chart, version, status), Drift indicator (deployed vs desired), Timeline of updates.
- **CIM Models:** N/A

---

### UC-3.3.6 · Operator Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** OpenShift operators reconcile cluster components; tracking Available/Progressing/Degraded across the full operator set surfaces partial failures before user-facing symptoms.
- **App/TA:** Custom API input (`oc get clusteroperator -o json`)
- **Data Sources:** `sourcetype=openshift:clusteroperator`
- **SPL:**
```spl
index=openshift sourcetype="openshift:clusteroperator"
| where progressing="True" OR degraded="True" OR available="False"
| stats values(available) as avail, values(degraded) as deg, values(progressing) as prog by cluster, operator
| sort cluster, operator
```
- **Implementation:** Ingest ClusterOperator status on a 5-minute cadence. Build a health matrix per cluster. Alert when any operator is `Degraded=True` or `Available=False` beyond the remediation SLA.
- **Visualization:** Operator matrix (green/yellow/red), Table (operator, conditions), Timeline of flapping.
- **CIM Models:** N/A

---

### UC-3.3.7 · Build Config Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** `BuildConfig` runs power S2I and Docker builds; failed builds block image promotion and rollouts tied to CI/CD.
- **App/TA:** OpenShift event forwarding
- **Data Sources:** `sourcetype=kube:objects:events`
- **SPL:**
```spl
index=openshift sourcetype="kube:objects:events" involvedObject.kind="Build" (reason="BuildFailed" OR reason="Error" OR reason="Failed")
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```
- **Implementation:** Ensure build events include `BuildConfig` correlation. Group by namespace and builder image. Alert on repeated failures for the same `BuildConfig` within 1 hour.
- **Visualization:** Table (build, namespace, message), Line chart (failure rate), Bar chart by builder image.
- **CIM Models:** N/A

---

### UC-3.3.8 · Route TLS Expiry Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** OpenShift Routes terminate TLS for apps; expiring certs on edge or re-encrypt routes cause sudden browser and API client failures.
- **App/TA:** cert-manager, `oc get route -o json` scripted input
- **Data Sources:** `sourcetype=openshift:route`, `sourcetype=certmanager:metrics`
- **SPL:**
```spl
index=openshift sourcetype="openshift:route"
| eval days_left=round((strptime(tls_not_after,"%Y-%m-%dT%H:%M:%SZ")-now())/86400,0)
| where days_left < 30 OR isnull(days_left)
| table namespace name host tls_not_after days_left
| sort days_left

| comment "cert-manager Certificate"
index=openshift sourcetype="certmanager:metrics" metric_name="certmanager_certificate_expiration_timestamp_seconds"
| eval days_left=round((_value-now())/86400,0)
| where days_left < 30
| table namespace name days_left
```
- **Implementation:** Periodically export Route TLS `notAfter` from `oc` or ingress controller. If using cert-manager, scrape expiration metrics. Alert at 30/14/7 days; page inside 7 days for customer-facing hostnames.
- **Visualization:** Table (route, hostname, days left), Single value (soonest expiry), Gauge.
- **CIM Models:** N/A

---

### UC-3.3.9 · Cluster Version Upgrade Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Long-running or failing upgrades leave clusters on unsupported versions; monitoring `ClusterVersion` conditions and history pins down stuck machine-config or operator prerequisites.
- **App/TA:** Custom API input (`oc get clusterversion version -o json`)
- **Data Sources:** `sourcetype=openshift:clusterversion`
- **SPL:**
```spl
index=openshift sourcetype="openshift:clusterversion"
| stats latest(version) as version, latest(progressing) as upgrading, latest(available) as available, latest(failing) as failing by cluster
| where upgrading="True" OR failing="True" OR available="False"
| table cluster version upgrading failing available
```
- **Implementation:** Parse `status.conditions` (Failing, Progressing, Available) and `status.history[]` from JSON into indexed fields. Alert when `progressing` remains true >2 hours or `Failing=True`. Complements UC-3.3.1 with failure messages from `status.history[].message`.
- **Visualization:** Upgrade timeline per cluster, Table (version, phase, message), Single value (clusters not on target channel).
- **CIM Models:** N/A

---

### UC-3.3.10 · Image Stream Tag Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** ImageStreams can point to unexpected digests after imports or mirroring; drift from expected tags breaks reproducible builds and compliance baselines.
- **App/TA:** `oc get imagestream -o json` scripted input
- **Data Sources:** `sourcetype=openshift:imagestream`
- **SPL:**
```spl
index=openshift sourcetype="openshift:imagestream"
| where isnotnull(expected_digest) AND isnotnull(digest) AND digest!=expected_digest
| table namespace name tag digest expected_digest source
| sort namespace, name
```
- **Implementation:** Scripted input emits `digest` per tag plus `expected_digest` from GitOps/CMDB (or use `| lookup` against a KV store). Alert on mismatch for `latest` and release tags used in production pipelines.
- **Visualization:** Table (imagestream, tag, digests), Drift count single value, Timeline of tag updates.
- **CIM Models:** N/A

---

### UC-3.3.11 · Operator Subscription Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** OLM subscriptions deliver operator upgrades; unhealthy subscriptions block security patches and CRD updates for platform add-ons.
- **App/TA:** `oc get subscription -A -o json` scripted input
- **Data Sources:** `sourcetype=openshift:subscription`
- **SPL:**
```spl
index=openshift sourcetype="openshift:subscription"
| where state!="AtLatestKnown" OR match(_raw,"InstallPlanPending|CatalogSourcesUnhealthy")
| stats latest(state) as state, latest(message) as msg by namespace, name, channel
| sort namespace, name
```
- **Implementation:** Parse Subscription `status.state` and conditions. Alert on `CatalogSourcesUnhealthy`, `InstallPlanPending` beyond SLA, or repeated upgrade failures. Correlate with CatalogSource pod health.
- **Visualization:** Table (subscription, state, message), Status grid by namespace, Timeline.
- **CIM Models:** N/A

---

## 3.4 Container Registries

**Primary App/TA:** Custom API inputs, webhook receivers

---

### UC-3.4.1 · Image Push/Pull Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Audit trail for who pushed or pulled what images. Detects unauthorized access, supply chain concerns, and usage patterns.
- **App/TA:** Registry webhook to Splunk HEC, API polling
- **Data Sources:** Registry audit/webhook events
- **SPL:**
```spl
index=containers sourcetype="registry:audit"
| stats count by action, repository, tag, user
| sort -count
```
- **Implementation:** Configure registry webhooks (Harbor, ACR, ECR) to send events to Splunk HEC. Alternatively, poll registry API for audit logs. Track push events (new deployments) and pull events (consumption).
- **Visualization:** Table (user, image, action, time), Bar chart by repository, Timeline.
- **CIM Models:** N/A

---

### UC-3.4.2 · Vulnerability Scan Results
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Registry-level scanning catches vulnerabilities before images are deployed. Trending shows whether security posture is improving or degrading.
- **App/TA:** Custom input (Harbor, ACR, ECR scan APIs)
- **Data Sources:** Scan result JSON from registry API
- **SPL:**
```spl
index=containers sourcetype="registry:scan"
| stats sum(critical) as critical, sum(high) as high, sum(medium) as medium by repository, tag
| where critical > 0
| sort -critical
```
- **Implementation:** Poll registry scan APIs for results or configure webhook notifications on scan completion. Forward to Splunk via HEC. Alert on critical vulnerabilities in images tagged for production.
- **Visualization:** Stacked bar chart (vulns by severity per image), Table, Trend line (vulns over time).
- **CIM Models:** N/A

---

### UC-3.4.3 · Storage Quota Monitoring
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Registry storage exhaustion prevents image pushes, blocking CI/CD pipelines. Monitoring enables proactive cleanup policy tuning.
- **App/TA:** Custom API input
- **Data Sources:** Registry storage API metrics
- **SPL:**
```spl
index=containers sourcetype="registry:metrics"
| stats latest(storage_used_bytes) as used, latest(storage_quota_bytes) as quota by registry
| eval used_pct = round(used / quota * 100, 1)
| where used_pct > 80
```
- **Implementation:** Poll registry API for storage metrics. Alert when usage exceeds 80%. Review and tune image retention/garbage collection policies.
- **Visualization:** Gauge (storage usage), Line chart (growth trend), Table.
- **CIM Models:** N/A

---

### UC-3.4.4 · Registry Image Vulnerability Scan Results
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Compliance
- **Value:** Images with known CVEs in the registry pose risk when deployed. Tracking scan results ensures only approved images are used and triggers remediation.
- **App/TA:** Custom API input (Trivy, Clair, registry scanner)
- **Data Sources:** Registry vulnerability scan output (JSON/CSV)
- **SPL:**
```spl
index=containers sourcetype="registry:vuln_scan"
| search severity="Critical" OR severity="High"
| stats count as vuln_count, values(cve_id) as cves by image_tag, registry
| where vuln_count > 0
| sort -vuln_count
```
- **Implementation:** Run vulnerability scanner against registry images (e.g. Trivy, Clair) and ingest results. Alert when Critical/High CVEs appear. Enforce policy to block deployment of failing images.
- **Visualization:** Table (image, CVE count, severity), Bar chart by image, Single value (images with critical vulns).
- **CIM Models:** N/A

---

### UC-3.4.5 · Registry Authentication and Authorization Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed logins and denied pushes/pulls may indicate credential abuse or misconfiguration. Detecting anomalies supports security and access troubleshooting.
- **App/TA:** Registry audit logs (Harbor, Docker Registry, ECR)
- **Data Sources:** Registry audit log API or log files
- **SPL:**
```spl
index=containers sourcetype="registry:audit" (action="login_failed" OR action="pull_denied" OR action="push_denied")
| bin _time span=1h
| stats count by user, action, repository, _time
| where count > 10
| sort -count
```
- **Implementation:** Forward registry audit logs to Splunk. Extract user, action, repository. Alert on high failure rates or denied actions for critical repos.
- **Visualization:** Table (user, action, count), Timechart of failures, Events list.
- **CIM Models:** Authentication

---

### UC-3.4.6 · Registry Replication Lag and Consistency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** Replication lag between registry replicas can cause inconsistent image availability and failed pulls. Monitoring supports HA and DR assurance.
- **App/TA:** Custom API input (registry replication status)
- **Data Sources:** Registry replication API or admin metrics
- **SPL:**
```spl
index=containers sourcetype="registry:replication"
| stats latest(lag_seconds) as lag, latest(status) as status by source_registry, target_registry
| where lag > 300 OR status != "success"
| table source_registry target_registry lag status _time
```
- **Implementation:** Poll replication status from registry (e.g. Harbor replication jobs). Ingest lag and status. Alert when lag exceeds 5 minutes or status is failed.
- **Visualization:** Line chart (lag over time), Table (source, target, lag, status), Single value (max lag).
- **CIM Models:** N/A

---

### UC-3.4.7 · Registry Image Tag Retention and Orphan Cleanup
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Untagged and old tags consume storage and complicate governance. Tracking supports retention policy tuning and cleanup automation.
- **App/TA:** Custom API input (registry catalog API)
- **Data Sources:** Registry catalog, image manifest API
- **SPL:**
```spl
index=containers sourcetype="registry:tags"
| eval age_days=round((now()-tag_time)/86400, 0)
| stats count as tag_count, values(tag) as tags by repository
| where tag_count > 100 OR age_days > 90
| table repository tag_count age_days
```
- **Implementation:** List repositories and tags via registry API. Compute tag count and oldest tag age per repo. Report repos with excessive tags or very old tags for retention policy review.
- **Visualization:** Table (repository, tag count, oldest tag), Bar chart (tags per repo).
- **CIM Models:** N/A

---

### UC-3.4.8 · Registry TLS and Certificate Expiration
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Security
- **Value:** Expired or expiring registry certificates break all pulls and pushes. Proactive monitoring prevents pipeline and runtime failures.
- **App/TA:** Custom scripted input (openssl s_client, registry health API)
- **Data Sources:** TLS certificate from registry endpoint
- **SPL:**
```spl
index=containers sourcetype="registry:tls"
| eval days_left=round((expiry_time-now())/86400, 0)
| where days_left < 30
| table registry_host expiry_time days_left subject
| sort days_left
```
- **Implementation:** Script that connects to registry HTTPS and extracts cert expiry (e.g. `openssl s_client -connect registry:443 -servername registry`). Ingest daily. Alert when expiry is within 30 days.
- **Visualization:** Table (registry, expiry, days left), Single value (soonest expiry), Gauge (days remaining).
- **CIM Models:** N/A

---

### UC-3.4.9 · Container Image Vulnerability Age
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Images running with known CVEs older than N days.
- **App/TA:** Custom (Trivy, Grype, or registry scanner output)
- **Data Sources:** vulnerability scanner JSON output
- **SPL:**
```spl
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan" OR sourcetype="registry:vuln_scan")
| eval vuln_date = coalesce(discovered_at, PublishedDate, published_date)
| eval vuln_age_days = round((now() - strptime(vuln_date, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| where (Severity="Critical" OR Severity="High") AND vuln_age_days > 7
| stats count as vuln_count, min(vuln_age_days) as oldest_vuln_days by image, tag, Severity
| sort -oldest_vuln_days -vuln_count
```
- **Implementation:** Run Trivy, Grype, or registry-native scanner (Harbor, ACR) against running images or registry catalog. Output JSON with image, CVE ID, severity, and discovered_at (or published date). Forward to Splunk via HEC. Alert when Critical/High CVEs have been known for >7 days (configurable). Integrate with CI/CD to block deployment of images with aged critical vulns. Track remediation SLA.
- **Visualization:** Table (image, tag, severity, vuln count, oldest days), Bar chart (images by vuln age), Single value (images with aged critical vulns).
- **CIM Models:** N/A

---

## 3.5 Service Mesh & Serverless Containers

**Primary App/TA:** Splunk OpenTelemetry Collector (Istio/Envoy metrics and access logs), `Splunk_TA_aws` (ECS/Fargate), `Splunk_TA_microsoft-cloudservices` (Azure Monitor), `Splunk_TA_google-cloudplatform` (Cloud Run / Cloud Monitoring)

---

### UC-3.5.1 · Istio Mesh Traffic Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Baseline and anomaly detection on east-west traffic prevents silent degradation and helps isolate failing workloads before user impact spreads.
- **App/TA:** Splunk OTel Collector (Prometheus receiver scraping Istio sidecar `15090`), `istio-mixer`/`istio` telemetry
- **Data Sources:** `sourcetype=otel:metrics` or `sourcetype=prometheus:istio`
- **SPL:**
```spl
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where like(metric_name, "istio_requests_total%") OR like(name, "istio_requests_total%")
| eval rc=tonumber(response_code)
| stats sum(value) as requests by destination_service_name, reporter, rc
| eval is_error=if(rc>=500 OR rc=0 OR isnull(rc), 1, 0)
| stats sum(requests) as total, sum(eval(if(is_error=1, requests, 0))) as err by destination_service_name
| eval err_rate=round(100*err/total, 2)
| where err_rate > 1
| sort -err_rate
```
- **Implementation:** Deploy the OTel Collector with a Prometheus receiver targeting Istio workload and ingress scrape configs (per Istio observability docs). Forward metrics to Splunk via OTLP or Splunk HEC. Normalize `destination_service_name` and `response_code` labels into dimensions. Build baselines per service pair and alert on sustained error-rate spikes versus historical traffic.
- **Visualization:** Time chart (requests and 5xx by destination), Table (top error rates by service), Single value (mesh-wide error %).
- **CIM Models:** N/A

---

### UC-3.5.2 · Sidecar Proxy Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Unhealthy Envoy sidecars drop or misroute traffic; catching not-ready or crash-looping proxies avoids cascading failures across the mesh.
- **App/TA:** Splunk OTel Collector (kubelet/cAdvisor or Prometheus kube-state-metrics), Kubernetes metadata
- **Data Sources:** `sourcetype=kube:metrics` or `sourcetype=otel:metrics`
- **SPL:**
```spl
index=containers (sourcetype="kube:metrics" OR sourcetype="otel:metrics")
| where match(pod, ".*-istio-proxy$") OR container_name="istio-proxy"
| stats latest(ready) as ready, latest(restarts) as restarts, latest(phase) as phase by pod, namespace, node
| where ready=0 OR restarts>3 OR phase!="Running"
| sort namespace, pod
```
- **Implementation:** Ingest pod/container metrics from Prometheus or OTel Kubernetes receiver so `istio-proxy` containers expose readiness and restart counts. Correlate with kube-state-metrics `kube_pod_container_status_restarts_total` where available. Alert when sidecars are not ready or restart churn exceeds threshold after mesh upgrades.
- **Visualization:** Table (namespace, pod, ready, restarts), Timeline (restarts), Single value (unhealthy sidecar count).
- **CIM Models:** N/A

---

### UC-3.5.3 · mTLS Certificate Expiry
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Expired Istio workload or gateway certs break mTLS between services; proactive expiry tracking avoids sudden mesh-wide authentication failures.
- **App/TA:** Custom script or `istioctl proxy-config secret` output to HEC, optional cert-manager logs
- **Data Sources:** `sourcetype=istio:cert_status` or `sourcetype=kubernetes:audit`
- **SPL:**
```spl
index=containers sourcetype="istio:cert_status"
| eval days_left=round((strptime(not_after, "%Y-%m-%dT%H:%M:%SZ")-now())/86400, 0)
| where days_left < 30 OR isnull(days_left)
| stats min(days_left) as soonest_expiry by workload_name, namespace, serial
| sort soonest_expiry
```
- **Implementation:** Schedule `istioctl proxy-config secret` or Citadel/istiod cert status exports and send JSON to Splunk (HEC). Include `not_after` for each SPIFFE identity. Alternatively parse cert-manager Certificate resources’ status. Alert at 30/14/7 days and page on any cert already expired.
- **Visualization:** Table (workload, namespace, soonest expiry days), Single value (minimum days to expiry), Gauge per cluster.
- **CIM Models:** N/A

---

### UC-3.5.4 · AWS Fargate Task Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Fargate tasks are the unit of scale; tracking stopped tasks and resource limits surfaces platform issues before services miss SLAs.
- **App/TA:** `Splunk_TA_aws` (CloudWatch Logs/Metrics)
- **Data Sources:** `sourcetype=aws:cloudwatch:metric` or `sourcetype=aws:cloudwatchlogs`
- **SPL:**
```spl
index=cloud sourcetype="aws:cloudwatch:metric" Namespace="AWS/ECS" MetricName="CPUUtilization"
| stats avg(Average) as cpu_avg, max(Maximum) as cpu_max by ServiceName, ClusterName
| where cpu_max>90
| sort -cpu_max
```
- **Implementation:** Enable CloudWatch Container Insights for ECS on Fargate and pull metrics via `Splunk_TA_aws` CloudWatch metric input. Ship task and service logs to Splunk (FireLens, Lambda, or direct subscription) and run a companion search on `sourcetype=aws:cloudwatchlogs` for `Task stopped` / error patterns. Map dimensions `ClusterName`, `ServiceName`, `TaskId`. Alert on sustained high CPU/memory, task stop reasons, and log error bursts.
- **Visualization:** Time chart (CPU/memory by service), Table (stopped tasks with reason), Single value (running task count).
- **CIM Models:** N/A

---

### UC-3.5.5 · Azure Container Instances Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** ACI containers are short-lived and opaque without platform metrics; monitoring restarts and resource exhaustion preserves burst workloads and integrations.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics)
- **Data Sources:** `sourcetype=azure:monitor:metric` or `sourcetype=azure:diagnostics`
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.containerinstance/containergroups"
| stats avg(average) as cpu_avg, max(maximum) as cpu_peak by resource_name, resource_group
| join type=left resource_name [
    search index=cloud sourcetype="azure:diagnostics" Category="ContainerInstanceLog"
    | where match(_raw, "(?i)error|fail|OOM")
    | stats count as log_errors by resource_name
]
| where cpu_peak>85 OR log_errors>0
| sort -cpu_peak
```
- **Implementation:** Route Azure Monitor metrics for Container Instances to Splunk using the Azure Add-on (Event Hub or metrics export). Enable diagnostic logs for container groups. Normalize `resource_name` to container group. Alert on CPU/memory threshold breaches, exit code non-zero patterns in logs, and restart counts from platform events.
- **Visualization:** Line chart (CPU/memory over time), Table (container group, region, state), Bar chart (events by group).
- **CIM Models:** N/A

---

### UC-3.5.6 · GCP Cloud Run Task Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.
- **App/TA:** `Splunk_TA_google-cloudplatform` (Pub/Sub logging/metrics) or OTel export from Cloud Ops
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` or `sourcetype=gcp:monitoring:timeseries`
- **SPL:**
```spl
index=cloud sourcetype="gcp:monitoring:timeseries"
| where like(metric.type, "run.googleapis.com%")
| stats avg(value) as val_avg, max(value) as val_max by metric.type
| where match(metric.type, "(?i)request|latency|instance|container")
| sort -val_max
```
- **Implementation:** Export Cloud Run request, latency, and instance metrics via GCP monitoring sink to Pub/Sub and ingest with `Splunk_TA_google-cloudplatform`, or forward OpenTelemetry from a sidecar/collector if you run hybrid instrumentation. Ensure `service_name` and `revision_name` are extracted. Alert on elevated `server_request_latencies` and `5xx` ratio versus SLO.
- **Visualization:** Time chart (p95 latency, request rate), Table (service, revision, error rate), Single value (active instances).
- **CIM Models:** N/A

---

### UC-3.5.7 · Envoy Proxy Error Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Envoy aggregates L7 failures; trending 4xx/5xx and upstream errors isolates bad clusters and config rollouts quickly.
- **App/TA:** Splunk OTel Collector (Envoy admin `/stats` or access log pipeline), `envoy.access_log`
- **Data Sources:** `sourcetype=envoy:access` or `sourcetype=otel:metrics`
- **SPL:**
```spl
index=containers sourcetype="envoy:access"
| eval status=tonumber(response_code)
| eval is_err=if(status>=400 OR upstream_cluster="-" , 1, 0)
| stats count as total, sum(is_err) as err by route_name, upstream_cluster, cluster_name
| eval err_pct=round(100*err/total, 2)
| where err_pct>1 AND total>100
| sort -err_pct
```
- **Implementation:** Configure Envoy access logs (JSON) to stdout and collect via OTel filelog receiver or Fluent Bit to Splunk. Include `response_code`, `route_name`, `upstream_cluster`, `duration`. Optionally scrape `envoy_cluster_upstream_rq_xx` from Prometheus. Baseline error percentages per route and alert on spikes after deployments.
- **Visualization:** Time chart (4xx/5xx rate by route), Table (top routes by error %), Heatmap (cluster vs status).
- **CIM Models:** N/A

---

### UC-3.5.8 · Circuit Breaker Trips
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Reliability
- **Value:** Outlier detection and open circuits protect the mesh; frequent trips signal upstream saturation or bad health checks that need capacity or code fixes.
- **App/TA:** Splunk OTel Collector (Envoy/Istio Prometheus metrics)
- **Data Sources:** `sourcetype=prometheus:istio` or `sourcetype=otel:metrics`
- **SPL:**
```spl
index=containers (sourcetype="prometheus:istio" OR sourcetype="otel:metrics")
| where match(metric_name, "envoy_cluster_upstream_rq_pending_overflow") OR match(metric_name, "circuit_breakers.*overflow")
| stats sum(value) as trips by cluster_name, destination_service_name
| where trips>0
| sort -trips
```
- **Implementation:** Scrape Istio/Envoy Prometheus endpoints (port 15090) with OTel Prometheus receiver. Map overflow and ejection counters to Splunk metrics. Correlate trips with deploy times and upstream latency. Alert when overflow rate accelerates versus steady-state for a cluster.
- **Visualization:** Time chart (overflow counters by cluster), Table (cluster, trips, destination), Bar chart (trips per namespace).
- **CIM Models:** N/A

---

### UC-3.5.9 · Service Mesh Control Plane Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** istiod and validating webhook outages block config pushes and sidecar updates; early detection prevents a widening blast radius across namespaces.
- **App/TA:** Splunk OTel Collector, Kubernetes metrics/logs
- **Data Sources:** `sourcetype=kube:logs` or `sourcetype=otel:logs`
- **SPL:**
```spl
index=containers (sourcetype="kube:logs" OR sourcetype="otel:logs") (istiod OR "istiod-")
| stats count(eval(match(_raw, "(?i)error|panic|failed"))) as err_count, count as line_count by pod, namespace
| eval err_rate=round(100*err_count/line_count, 2)
| where err_rate>5 OR err_count>50
| sort -err_count
```
- **Implementation:** Collect istiod container logs and kube-state-metrics for Deployment replicas (`istiod` available vs desired). Ingest admission webhook failure events from API server audit if enabled. Alert on istiod pod restarts, gRPC push errors in logs, and replica mismatch.
- **Visualization:** Single value (istiod ready replicas), Timeline (pod restarts), Table (error snippets by pod).
- **CIM Models:** N/A

---

### UC-3.5.10 · Ingress Gateway Latency
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** North-south latency reflects TLS, auth, and routing at the edge; regressions here affect every external client before internal mesh metrics move.
- **App/TA:** Splunk OTel Collector (Istio ingress gateway metrics), Envoy access logs
- **Data Sources:** `sourcetype=otel:metrics` or `sourcetype=envoy:access`
- **SPL:**
```spl
index=containers sourcetype="envoy:access"
| where like(gateway_workload, "istio-ingress%") OR like(kubernetes_pod_name, "istio-ingress%")
| eval dur_ms=tonumber(duration_ms)
| timechart span=5m perc95(dur_ms) as p95_ms, perc99(dur_ms) as p99_ms by route_name
```
- **Implementation:** Label ingress gateway access logs with `gateway_workload` or filter Kubernetes workload name. Export histogram or timer metrics (`istio_request_duration_milliseconds`) via OTel. Set SLO windows on p95/p99 per host and route. Compare canary vs stable gateway revisions during rollouts.
- **Visualization:** Time chart (p95/p99 latency by route), Geographic or by-AZ breakdown if multi-region, Single value (SLO burn).
- **CIM Models:** N/A

---

### UC-3.5.11 · Sidecar Injection Validation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Pods without injection bypass mesh policy and mTLS; continuous validation enforces namespace labels and mutating webhook coverage.
- **App/TA:** Kubernetes API audit or controller logs, `kube:objects` snapshot
- **Data Sources:** `sourcetype=kubernetes:audit` or `sourcetype=kube:objects`
- **SPL:**
```spl
index=containers sourcetype="kubernetes:audit" objectRef.resource="pods"
| eval has_sidecar=if(match(_raw, "istio-proxy"), 1, 0)
| join type=left objectRef.namespace [
    search index=containers sourcetype="kube:objects" kind="Namespace"
    | eval inject=if(match(_raw, "istio-injection=enabled"), 1, 0)
    | stats max(inject) as should_inject by metadata.name
    | rename metadata.name as objectRef.namespace
]
| where should_inject=1 AND has_sidecar=0
| stats count by objectRef.namespace, objectRef.name
```
- **Implementation:** Periodically inventory pods in `istio-injection=enabled` namespaces (CI job or Splunk scheduled search against cached object JSON). Flag workloads missing `istio-proxy`. Optionally parse audit logs for pod create with webhook bypass. Integrate with policy-as-code to fail builds that skip mesh membership.
- **Visualization:** Table (namespace, pod, missing sidecar), Single value (non-compliant pod count), Trend (compliance %).
- **CIM Models:** N/A

---

### UC-3.5.12 · Rate Limiting and Traffic Policy Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Confirms quotas and Istio `RateLimitService`/Local rate limit configs actually throttle abuse; drift between policy and observed denials indicates misconfiguration or bypass attempts.
- **App/TA:** Splunk OTel Collector (Envoy local rate limit / RLS metrics), Envoy access logs
- **Data Sources:** `sourcetype=envoy:access` or `sourcetype=otel:metrics`
- **SPL:**
```spl
index=containers sourcetype="envoy:access"
| eval denied=if(response_code=429 OR match(response_flags, "RL"), 1, 0)
| stats count as total, sum(denied) as rate_limited by route_name, cluster_name
| eval rl_pct=round(100*rate_limited/total, 3)
| where rate_limited>0
| sort -rate_limited
```
- **Implementation:** Ensure access logs include `response_code` 429 and Envoy `response_flags` (e.g. `RL` for rate limited). For global RLS, scrape `ratelimit_service_*` or service metrics. Dashboard expected 429 share per route against policy (e.g. per-API key). Alert on unexpected absence of throttling during attacks or sudden spikes in 429s indicating config errors.
- **Visualization:** Time chart (429 rate by route), Table (routes with throttle events), Stacked bar (allowed vs rate-limited volume).
- **CIM Models:** N/A

