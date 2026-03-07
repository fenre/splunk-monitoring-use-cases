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
| eval throttle_pct = round(throttled_periods / nr_periods * 100, 1)
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
- **Monitoring type:** Performance
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
| eval error_rate = round(errors / total * 100, 2)
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

