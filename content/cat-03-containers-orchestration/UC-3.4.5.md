<!-- AUTO-GENERATED from UC-3.4.5.json — DO NOT EDIT -->

---
id: "3.4.5"
title: "Registry Authentication and Authorization Failures"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.5 · Registry Authentication and Authorization Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Audit, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch for anyone trying to access our software storage with the wrong password or without permission, catching repeated break-in attempts and alerting when legitimate workers get locked out because their access expired.*

---

## Description

Detects **authentication failures** (HTTP 401) and **authorization denials** (HTTP 403) across **Harbor** and **Docker Distribution** registries by analyzing access logs and audit events, classifying each denied request by action type (login, pull, push, catalog), and flagging patterns indicative of credential brute-force or project enumeration — then correlating with Kubernetes **ImagePullBackOff** events to quantify the deployment impact of registry access failures.

## Value

A compromised registry credential gives an attacker the ability to poison the software supply chain by pushing trojaned images or exfiltrating proprietary code via pulls. Detecting authentication failure patterns at the registry layer catches credential stuffing and stolen-token abuse before the attacker succeeds, while ImagePullBackOff correlation reveals when legitimate workloads are blocked by expired secrets or misconfigured RBAC.

## Implementation

Collect Harbor nginx access logs (401/403 responses) via Universal Forwarder and Harbor audit API via rest_ta into index=containers. Build two search variants: auth failure analysis with brute-force and enumeration detection, and ImagePullBackOff correlation with registry auth errors. Alert on brute-force patterns (>20 failures in 30 minutes) and on any ImagePullBackOff affecting production namespaces.

## Detailed Implementation

### Prerequisites
- **Harbor** 2.6+ with **HTTPS** enabled and **nginx **access log**ging** active (default configuration logs all requests including status codes, client IPs, and user agents to `/var/log/harbor/nginx/access.log`).
- **Universal Forwarder** deployed on the **Harbor host** monitoring the **nginx access log** file and forwarding as **`sourcetype=harbor:access`** to `index=containers`. Configure the **monitor stanza** in `inputs.conf` with `sourcetype=harbor:access` and `index=containers`.
- **Splunk REST API Modular Input** (**rest_ta**, **Splunkbase 1546**) on a **heavy forwarder** polling the **Harbor audit API** (`GET /api/v2.0/audit-logs?sort=-op_time`) every **300 seconds** for structured audit entries as **`sourcetype=harbor:audit`**.
- **Splunk HEC** token for **`index=containers`** with webhook reception for **`sourcetype=harbor:webhook`** events.
- **Kubernetes event collection**: **Splunk Connect for Kubernetes** or **OTel Collector** capturing **`sourcetype=kube:events`** with reasons `ImagePullBackOff`, `ErrImagePull`, and `Failed` to correlate registry **auth failure**s with pod scheduling impact.
- Splunk RBAC: users running auth failure searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`registry_security_analyst`**).
- **Baseline data**: collect at least 7 days of access logs before tuning **brute-force thresholds** — legitimate **CI/CD** pipelines can generate bursts of auth attempts during credential rotation.
- **License estimate**: each access log entry is ~500 bytes; a registry serving 1,000 pull/push requests/day generates ~500 KB/day of access logs.

### Step 1 — Configure data collection
(1) **nginx access log collection**: deploy a **Universal Forwarder** on the Harbor host with a **monitor stanza** targeting `/var/log/harbor/nginx/access.log`. The default Harbor nginx log format includes: `remote_addr`, `remote_user`, `request`, `status`, `body_bytes_sent`, `http_referer`, `http_user_agent`. For enhanced forensics, configure Harbor's nginx to use a **JSON log format** that adds `upstream_response_time` and `request_time` fields.

(2) **Field extraction**: create **`props.conf`** extractions for the Harbor access log format to produce fields: `client_ip`, `remote_user`, `request_uri`, `http_status`, `user_agent`. For 401/403 analysis, the key fields are **`http_status`** (the response code), **`remote_user`** (authenticated user or `-` for anonymous), **`request`** (the HTTP method + URI), and **`remote_addr`** (client IP).

(3) **Harbor audit API**: poll `GET /api/v2.0/audit-logs` which returns structured JSON with fields: `username`, `operation` (login, create, pull, push, delete), `resource` (project/repo path), `resource_type`, `op_time`. Filter for failed operations by checking `operation` values that indicate denial.

(4) **Docker Distribution fallback**: for non-Harbor registries, collect the Docker Distribution **notification endpoint** events as **`sourcetype=docker:registry:events`**. Failed authentication appears as events with an empty `actor.name` field or missing authorization headers.

(5) **Lookup setup**: create **`known_service_accounts.csv`** with columns `actor`, `account_type` (robot, ci_pipeline, human), `owner_team` to distinguish known automation from suspicious actors. Define in **`transforms.conf`** and reference in the search.

### Step 2 — Create the search and alert
The primary SPL filters for **HTTP 401** (authentication failure — invalid or missing credentials) and **HTTP 403** (authorization denied — valid credentials but insufficient permissions) responses from the access log and **audit API**.

The **`action`** classification uses URI patterns to determine what the user was attempting: manifest pulls (`/v2/.*/manifests/`), blob pushes (`/v2/.*/blobs/uploads`), catalog enumeration (`/v2/_catalog`), login (`/api/v2.0/users/login`), or token requests (`/service/token`).

The **`is_brute_force`** flag triggers when a single actor produces > 20 failures in less than 30 minutes — this threshold catches automated **credential stuffing** while allowing for legitimate burst failures during CI/CD credential rotation. The **`is_enumeration`** flag detects actors probing multiple projects with diverse action types, suggesting **reconnaissance** rather than a simple misconfiguration.

The **ImagePullBackOff variant** correlates **Kubernetes** pod scheduling failures caused by registry auth errors — when a pod enters ImagePullBackOff due to a 401/403 from the registry, this search quantifies how many pods and namespaces are affected.

Schedule the auth failure search every **15 minutes** over **`-15m`** and alert on `is_brute_force=LIKELY` or `is_enumeration=LIKELY`. Schedule the ImagePullBackOff search every **5 minutes** and alert when `affected_pods > 3` in any production namespace.

### Step 3 — Validate
(a) Generate a test 401: `curl -u wronguser:wrongpass https://<harbor>/v2/_catalog` and verify the access log entry appears: `index=containers sourcetype="harbor:access" status=401 | head 1`.
(b) Generate a test 403: use a **robot account** with read-only scope and attempt a push: `docker push <harbor>/library/test:latest` — should produce a 403. Verify: `index=containers sourcetype="harbor:access" status=403 | head 1`.
(c) Test **brute-force detection**: run a loop of 25 failed login attempts in under 30 minutes and verify `is_brute_force=LIKELY` in the search output.
(d) Test **ImagePullBackOff correlation**: create a pod referencing a non-existent registry **secret**: `kubectl run pull-test --image=<harbor>/nonexistent:latest` and verify the kube:events search captures the ErrImagePull event.
(e) Verify **known_service_accounts lookup**: add a CI/CD robot account to the lookup and confirm it is enriched with `account_type=robot` in the search output.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **timechart** of auth failures by `failure_type` (401 vs 403) over 24 hours — spikes indicate credential issues or targeted attacks.
- Row B: **single-value tiles** — total auth failures (last 4h), unique actors with failures, actors flagged as **brute-force**, pods in ImagePullBackOff.
- Row C: **actor table** — actor, failure_type, failure_count, source_ips, projects_targeted, is_brute_force, is_enumeration. Red rows for brute-force/enumeration. Drilldown opens per-actor timeline.
- Row D: **ImagePullBackOff table** — ns, registry, event_count, affected_pods, last_message. Drilldown opens pod detail.
- **Alerting**: brute-force detected → **PagerDuty** P2 + Slack `#security-ops`; enumeration detected → P3; ImagePullBackOff in production → Slack `#platform-ops` with pod names.
- **Runbook** (owner: security on-call): (1) for brute-force: check if the actor is a known **service account** or robot — if not, block the source IP and rotate credentials, (2) for enumeration: review the actor's access scope and disable if unauthorized, (3) for ImagePullBackOff: check **imagePullSecrets** on the pod spec and verify the referenced Secret contains valid credentials.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **geo-map** panel plotting auth failure source IPs to identify geographic anomalies (e.g., login attempts from unexpected countries); pair with an **auth failure funnel** showing total attempts → unique actors → brute-force flagged → successfully blocked; add a **correlation panel** linking auth failure actors with their first successful login (if any) from `harbor:access status=200`.
- **Alert design**: include `actor`, `failure_type`, `failure_count`, `source_ips`, `projects_targeted`, `is_brute_force`, `is_enumeration`, `session_min` in auth alerts; for ImagePullBackOff include `ns`, `registry`, `affected_pods`, `last_message`; add a **deep-link** to the Harbor user management page for the flagged actor.
- **High failure count from CI/CD robot accounts** — robot credential rotation creates a burst of 401s during the overlap window. Correlate with robot creation timestamps and suppress during planned rotation windows via a **`maintenance_windows`** lookup.
- **Anonymous 401s dominate the search** — Harbor returns 401 for unauthenticated requests to private projects (prompting the client to authenticate). Filter by excluding actors with `remote_user="-"` and `action="token_request"` which are the normal Docker client auth flow.
- **ImagePullBackOff without 401/403 in access logs** — the pull may be hitting a different registry (Docker Hub, GCR, ECR) not monitored by this search. Check the `registry` field in the kube:events to identify the source.
- **Account lockout integration** — configure a **correlation search** that detects brute-force flagged actors and automatically adds them to a **blocked_actors** lookup that a Harbor webhook validation script uses to reject all subsequent requests from that actor until manual review.
- **No access log events** — verify the Universal Forwarder **monitor stanza** path matches the actual nginx log location; check file permissions and forwarder status.

## SPL

```spl
`comment("--- Registry Auth Failures — Denied Logins, Pulls, and Pushes ---")`
index=containers (sourcetype="harbor:access" OR sourcetype="harbor:audit")
| eval status_code=coalesce(status, http_status, response_code)
| where status_code IN ("401", "403", 401, 403)
| eval actor=coalesce(remote_user, username, operator, "anonymous")
| eval src_ip=coalesce(client_ip, remote_addr, src_ip, src)
| eval request_uri=coalesce(request, uri, resource, "")
| eval user_agent=coalesce(http_user_agent, user_agent, "unknown")
| eval failure_type=case(
    status_code=401 OR status_code="401", "authentication_failure",
    status_code=403 OR status_code="403", "authorization_denied",
    1=1, "unknown")
| eval action=case(
    match(request_uri, "(?i)/v2/.*/manifests/"), "pull_manifest",
    match(request_uri, "(?i)/v2/.*/blobs/uploads"), "push_blob",
    match(request_uri, "(?i)/v2/_catalog"), "catalog_list",
    match(request_uri, "(?i)/api/v2\.0/users/login"), "login",
    match(request_uri, "(?i)/service/token"), "token_request",
    match(request_uri, "(?i)/v2/"), "registry_api",
    1=1, "other")
| eval project=if(action!="login", mvindex(split(replace(request_uri, "^/v2/", ""), "/"), 0), "global")
| stats count as failure_count,
    dc(action) as action_diversity,
    values(action) as attempted_actions,
    dc(src_ip) as source_ips,
    dc(project) as projects_targeted,
    earliest(_time) as first_failure,
    latest(_time) as last_failure
    by actor, failure_type
| eval session_min=round((last_failure - first_failure) / 60, 1)
| eval is_brute_force=if(failure_count > 20 AND session_min < 30, "LIKELY", "NO")
| eval is_enumeration=if(projects_targeted > 5 AND action_diversity > 2, "LIKELY", "NO")
| sort -failure_count
| head 50
| table actor failure_type failure_count source_ips projects_targeted attempted_actions session_min is_brute_force is_enumeration

`comment("--- ImagePullBackOff Correlation — Registry Auth Failures Blocking Pods ---")`
index=containers sourcetype="kube:events" reason="Failed" message="*401*" OR message="*403*" OR message="*unauthorized*" OR reason="ErrImagePull" OR reason="ImagePullBackOff"
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace)
| eval pod_name=coalesce(involvedObject.name, object_name)
| eval image=coalesce(involvedObject.fieldPath, container_image)
| eval registry=mvindex(split(image, "/"), 0)
| stats count as event_count,
    dc(pod_name) as affected_pods,
    values(pod_name) as pods,
    latest(message) as last_message,
    latest(_time) as last_event
    by ns, registry
| sort -event_count
| table ns registry event_count affected_pods last_message last_event pods
```

## Visualization

Auth failure timeline by actor, brute-force indicator table, ImagePullBackOff heat map by namespace, single-value tiles (total auth failures, unique attackers, affected pods).

## Known False Positives

**robot_credential_rotation_burst** — When Harbor robot account credentials are rotated, the old secret continues to be used by CI/CD pipelines until the new secret is propagated, generating a burst of 401 failures that resolves within minutes. Correlate with robot account creation events and suppress during planned rotation windows.

**docker_client_auth_flow** — The Docker client's authentication handshake first sends an unauthenticated request to the registry, receives a 401 with a `WWW-Authenticate` challenge header, then retries with credentials. These initial 401s are part of the normal auth protocol, not failures. Filter by checking if the same actor has a subsequent 200 within the same second.

**imagepullsecret_expiry_cascade** — When a Kubernetes imagePullSecret expires, every pod in the namespace that references it enters ImagePullBackOff simultaneously. This produces a burst of auth failures proportional to the number of pods, not the number of attack attempts. Check whether all affected pods reference the same Secret name.

**ldap_backend_timeout** — Harbor configured with LDAP authentication may return 401 during LDAP server unavailability even for valid credentials. The access log shows auth failures, but the root cause is infrastructure, not credential abuse. Correlate with LDAP server health monitoring.

**catalog_endpoint_enumeration** — Security scanners and compliance tools routinely call `/v2/_catalog` to inventory images, which triggers 403 responses if the service account lacks catalog scope. These are legitimate compliance activities, not reconnaissance. Add scanner service accounts to the known_service_accounts lookup.

**proxy_cache_stale_token** — When Harbor is fronted by a CDN or reverse proxy that caches authentication tokens, clients may present stale tokens after rotation, generating a wave of 401s that resolves when the cache refreshes. Check for uniform user agent strings indicating proxy-mediated requests.

## References

- [Harbor — RBAC and User Management](https://goharbor.io/docs/2.10.0/administration/managing-users/)
- [Harbor — Robot Accounts](https://goharbor.io/docs/2.10.0/working-with-projects/project-configuration/create-robot-accounts/)
- [Docker Distribution — Authentication Specification](https://distribution.github.io/distribution/spec/auth/)
- [Kubernetes — ImagePullBackOff Troubleshooting](https://kubernetes.io/docs/concepts/containers/images/#imagepullbackoff)
- [Splunk REST API Modular Input (Splunkbase 1546)](https://splunkbase.splunk.com/app/1546)
