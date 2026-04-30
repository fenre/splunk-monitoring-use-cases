<!-- AUTO-GENERATED from UC-3.4.1.json — DO NOT EDIT -->

---
id: "3.4.1"
title: "Image Push/Pull Audit"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.1 · Image Push/Pull Audit

## Description

Tracks every container image **push**, **pull**, and **delete** event across **Harbor**, **Docker Distribution**, and cloud-managed registries by correlating webhook notifications with API audit logs, surfacing who touched which repository and tag, from what source address, and whether the action deviated from authorized baselines — the foundational audit trail for container supply-chain governance.

## Value

A tampered or unauthorized image reaching production is a supply-chain breach that no amount of runtime detection can undo; auditing every registry write and read at the source gives change-advisory boards proof of provenance, lets security teams detect credential theft or insider exfiltration within minutes of the pull, and satisfies the artifact-integrity evidence requirements that SOC 2, PCI DSS, and internal DevSecOps policies increasingly demand.

## Implementation

Configure Harbor webhooks (PUSH_ARTIFACT, PULL_ARTIFACT, DELETE_ARTIFACT, SCANNING_COMPLETED, TAG_RETENTION, REPLICATION, QUOTA events) to POST to Splunk HEC as sourcetype=harbor:webhook. Supplement with REST polling of /api/v2.0/audit-logs via rest_ta for historical completeness and Universal Forwarder collection of Harbor nginx access logs. Build lookup tables for authorized actors and schedule alerts on unauthorized pulls, tag mutations, and destructive deletes.

## Detailed Implementation

Prerequisites
• **Harbor** 2.6+ (or **Docker Distribution** 2.8+ for plain registries without Harbor's audit layer) with **HTTPS** enabled on **443/tcp**; earlier Harbor 1.x lacks structured **webhook** payloads and the **`/api/v2.0/audit-logs`** endpoint used in Step 1.
• A dedicated **Harbor robot account** scoped to project-level read on every project you audit — never reuse interactive admin credentials for automated collection; rotate the robot secret on a 90-day cadence aligned with your credential policy.
• **Splunk HEC** token provisioned on an indexer or heavy forwarder, assigned to **`index=containers`** with default **`sourcetype=harbor:webhook`**; a second HEC token or source override for API-polled events landing as **`sourcetype=harbor:audit`**; optional third stream for **`sourcetype=harbor:access`** via **Universal Forwarder** on the Harbor host.
• **Splunk REST API Modular Input** (**rest_ta**, **Splunkbase 1546**) on a heavy forwarder if you choose the REST polling path for `/api/v2.0/audit-logs` instead of relying solely on webhooks; the scripted-input alternative in Step 1 avoids this dependency.
• Network: 443/tcp from the Splunk collector to the **Harbor API**; **8088/tcp** (or custom HEC port) from Harbor to the Splunk HEC endpoint — firewall rules and any intermediate load-balancer health checks must be in place before enabling webhook delivery.
• **RBAC**: Splunk users running audit searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (`registry_auditor`) rather than granting admin.
• License estimate: each webhook event averages ~1.2 KB; a registry handling 500 image pushes/day across 20 projects generates ~2.5 MB/day from webhooks plus ~4 MB/day from access logs — total under 10 MB/day for most enterprises.

Step 1 — Configure data collection
(1) **Webhook path** (recommended for real-time audit): in the **Harbor admin console** navigate to **Administration → Webhooks** (or per-project under **Project → Webhooks**). Create a webhook endpoint:
— Endpoint URL: `https://<splunk-hec-host>:8088/services/collector/event`
— Auth Header: `Splunk <your-hec-token>`
— Events to subscribe: **`PUSH_ARTIFACT`, **`PULL_ARTIFACT`**, **`DELETE_ARTIFACT`**, `SCANNING_COMPLETED`, `TAG_RETENTION`, `REPLICATION`, `QUOTA_EXCEED`, `QUOTA_WARNING`**
— Payload Format: JSON (Harbor sends a structured **`event_data`** object with nested fields **`repository.repo_full_name`, `repository.tag`, `repository.digest`, `repository.namespace`**)
Test by pushing a scratch image: `docker push harbor.example.com/library/test:latest` then verify arrival: `index=containers sourcetype=harbor:webhook | head 1`. The **`event_type`** field should read **`PUSH_ARTIFACT`**.

(2) **API polling path** (for audit-log completeness and historical backfill): configure **rest_ta** (**Splunkbase 1546**) or a **scripted input** to poll `GET /api/v2.0/audit-logs?page=1&page_size=100&sort=-op_time` every **300 seconds**. Authenticate with `X-Harbor-Robot: <robot-secret>` or **basic auth** against the robot account. Map responses to `sourcetype=harbor:audit` in `index=containers`. Key fields in the JSON response: **`operation`** (create, delete, pull), `resource` (repository path), `resource_type` (artifact, tag, project), **`username`, `op_time`**.

(3) **Access log path** (optional, for IP-level forensics): deploy a **Universal Forwarder** on the Harbor host and monitor `/var/log/harbor/nginx/access.log` as `sourcetype=harbor:access` in `index=containers`. This captures HTTP method, URI, status code, client IP, and user agent — layer-7 detail that webhooks omit (HEAD requests for manifest checks, partial layer downloads).

(4) **Docker Distribution fallback** (non-Harbor registries): enable `notifications` in the registry `config.yml` with an endpoint pointing to **Splunk HEC**. Events arrive as **`sourcetype=docker:registry:events`** with fields **`action`, `target.repository`, `target.tag`, `actor.name`, `request.addr`**.

(5) **Lookup setup**: create `authorized_registry_users.csv` with columns `actor`, `project`, `authorized` (yes/no) in `$SPLUNK_HOME/etc/apps/registry_audit/lookups/` and define the transform in **`transforms.conf`**. Populate from your CI/CD service-account inventory — this powers the unauthorized-pull detection variant in Step 2.

Step 2 — Create the search and alert
The primary SPL normalizes **webhook, API**, and **access-log** events into a unified audit trail. The **`coalesce`** chain across `event_type`, `operation`, and `type` handles the three different field names Harbor uses depending on whether the event came from a webhook (`event_type=PUSH_ARTIFACT`), the audit API (`operation=create`), or the access log (`type=pull`). The `case` normalization maps all variants to lowercase canonical verbs.

**`action_class`** groups actions into `write` (push, replicate), `read` (pull), `destructive` (delete), and `lifecycle` (scan, retention, quota) — destructive actions route to security, lifecycle events route to platform ops.

The **`is_robot`** and **`is_service_account`** flags distinguish expected automation from interactive human access; set the **`authorized_registry_users`** lookup from Step 1(5) to suppress known CI/CD actors in alert conditions.

Schedule the primary audit search every **15 minutes** over `-15m@m to @m`; alert on `action_class=destructive AND is_robot_account=0 AND is_ci_account=0` (human-initiated deletes). The tag-mutation variant runs every **1 hour** over `-24h` and alerts when `overwrite_count > 0` for tags matching `:latest` or `:stable` — mutable tags in production signal supply-chain risk.

Step 3 — Validate
(a) In **Harbor UI** → **Logs** → filter to last 1 hour. Count **push** and **pull** entries. In Splunk: `index=containers (sourcetype="harbor:webhook" OR sourcetype="harbor:audit") earliest=-1h | stats count by action`. Counts should agree within ±5% — the gap is polling-interval lag on the API path.
(b) Pick a known image push from the last hour. In Harbor UI note the **repository**, **tag**, **digest** (first 12 chars), and **username**. In Splunk: `index=containers sourcetype="harbor:webhook" event_type="PUSH_ARTIFACT" | head 5 | table _time repository tag digest actor`. Fields should match.
(c) Verify access-log enrichment: `index=containers sourcetype="harbor:access" earliest=-1h | stats count`. Zero rows means the UF monitor stanza path or file permissions need attention.
(d) Test the unauthorized-pull lookup: temporarily add a test user to `authorized_registry_users.csv` with `authorized=no` and verify the lookup-based search returns that user's pulls.
(e) Confirm role permissions: `| rest splunk_server=local /servicesNS/-/-/authorization/roles | search title="registry_auditor" | table title srchIndexesAllowed` — must include `containers`.
(f) Compare `docker:registry:events` volume for non-Harbor registries: `index=containers sourcetype="docker:registry:events" earliest=-1h | stats count by action`.

Step 4 — Operationalize dashboards and runbooks
• Row A: **timechart** of event volume by `action_class` over 24 hours as stacked area so shifts between write/read/destructive are visible.
• Row B: **single-value tiles** — pushes last 4h, unique actors last 4h, delete events last 4h (red threshold ≥ 1 for non-robot deletes), tag mutations last 24h (red threshold ≥ 1).
• Row C: **sortable table** of actors by `event_count` — columns: actor, project, action_class, repos_touched, unique_sources, is_robot_account, session_hours, last_seen. Drilldown opens per-actor **timeline**.
• Row D: **tag-mutation table** — columns: repository, tag, overwrite_count, pushers, window_hours. Red highlighting when tag matches `latest` or `stable`.
• **Alerting**: unauthorized delete → Slack `#security-ops` + **PagerDuty** P2; tag mutation on protected tags → `#devops-alerts` with provenance link; anomalous pull volume (>100 pulls/hour from single actor outside lookup) → security for credential-compromise investigation.
• **Runbook** (owner: DevSecOps on-call): (1) check actor identity against service-account inventory, (2) cross-reference with change management via `index=containers sourcetype="harbor:audit" actor=<user> earliest=-4h`, (3) for deletes verify no active deployments reference the artifact, (4) for tag mutations compare **digests** against CI/CD pipeline expected output.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: pair the `action_class` stacked area chart with a **sankey** flowing actor → action → project to show who does what in which namespace; add a **geo-map** panel plotting `src_ip` locations for pulls outside expected CIDR ranges; use `timechart count by action_class` with overlay lines for daily push/pull ratio trending.
• **Alert design**: include `actor`, `repository`, `tag`, `digest` (truncated to 12 chars), `action`, `src_ip`, and `registry_host` in every alert payload so responders have full context; use `| sendalert` with a custom alert action posting to your SIEM or SOAR for automated triage workflows.
• **No webhook events arriving** — verify the Harbor webhook endpoint URL in **Administration → Webhooks**; check **`harbor-core`** container logs (`docker logs harbor-core 2>&1 | grep webhook`) for delivery failures (HTTP 4xx/5xx); confirm TLS certificate trust between Harbor and Splunk HEC; test HEC reachability: `curl -k https://<hec-host>:8088/services/collector/health`.
• **Webhook events arrive but fields are null** — Harbor 2.6+ changed the webhook payload schema; confirm **`props.conf`** extractions handle the nested `event_data.repository.*` JSON path; use `| spath` as diagnostic: `index=containers sourcetype="harbor:webhook" | spath | head 1`.
• **API polling returns empty or stale results** — `/api/v2.0/audit-logs` requires at least `project-admin` scope on every audited project; a project-scoped robot account only sees its own project's logs; check **rest_ta** entries in **`splunkd.log`** for HTTP 401/403.
• **Duplicate events from webhook and API paths** — expected when both are active for the same action; deduplicate with `| dedup actor, repository, tag, action, _time span=60s` or maintain separate saved searches per sourcetype.
• **Massive pull volume from scanners** — **Trivy** or **Grype** pull every layer of every image on scan; suppress by filtering scanner service-account actors or excluding `scan_complete` lifecycle events from pull-volume alerts.
• **Delete events during garbage collection** — Harbor **GC** jobs produce bulk deletes in a narrow window; correlate with `sourcetype="harbor:audit" operation="gc"` and suppress via **`maintenance_windows`** lookup.

## SPL

```spl
`comment("--- Harbor Registry Audit — Unified Webhook + API Event Stream ---")`
index=containers (sourcetype="harbor:webhook" OR sourcetype="harbor:audit" OR sourcetype="harbor:access")
| eval raw_action=coalesce(event_type, operation, type, "unknown")
| eval action=case(
    match(raw_action, "(?i)^(PUSH_ARTIFACT|push|create)$"), "push",
    match(raw_action, "(?i)^(PULL_ARTIFACT|pull|read)$"), "pull",
    match(raw_action, "(?i)^(DELETE_ARTIFACT|delete|remove)$"), "delete",
    match(raw_action, "(?i)^(SCANNING_COMPLETED|scan)$"), "scan_complete",
    match(raw_action, "(?i)^(TAG_RETENTION|tag_retention)$"), "retention",
    match(raw_action, "(?i)^(REPLICATION|replicate)$"), "replicate",
    match(raw_action, "(?i)^(QUOTA_[A-Z]+)$"), "quota",
    1=1, lower(raw_action))
| eval repository=coalesce('event_data.repository.repo_full_name', 'resource.detail', resource, repository)
| eval tag=coalesce('event_data.repository.tag', tag, "untagged")
| eval digest=coalesce('event_data.repository.digest', digest, "")
| eval actor=coalesce(operator, username, 'event_data.repository.namespace', "anonymous")
| eval src_ip=coalesce(client_ip, src_ip, src, "unknown")
| eval registry_host=coalesce(registry, endpoint, host)
| eval project=coalesce('event_data.repository.namespace', mvindex(split(repository, "/"), 0))
| eval image_ref=if(tag!="untagged", repository.":".tag, repository."@".digest)
| eval action_class=case(
    action IN ("push", "replicate"), "write",
    action="pull", "read",
    action="delete", "destructive",
    action IN ("scan_complete", "retention", "quota"), "lifecycle",
    1=1, "other")
| eval is_robot=if(match(actor, "^robot\\$"), 1, 0)
| eval is_service_account=if(match(actor, "^(ci|jenkins|github-actions|gitlab-ci|argocd|flux)"), 1, 0)
| stats count as event_count,
    dc(action) as action_diversity,
    values(action) as actions,
    dc(src_ip) as unique_sources,
    values(src_ip) as source_ips,
    dc(repository) as repos_touched,
    latest(_time) as last_seen,
    earliest(_time) as first_seen,
    max(is_robot) as is_robot_account,
    max(is_service_account) as is_ci_account
    by actor, project, action_class, registry_host
| eval session_hours=round((last_seen - first_seen) / 3600, 2)
| sort -event_count

`comment("--- Unauthorized or Anomalous Pull Detection ---")`
index=containers (sourcetype="harbor:webhook" OR sourcetype="harbor:audit" OR sourcetype="harbor:access")
| eval action=lower(coalesce(event_type, operation, type))
| search action="pull" OR action="pull_artifact"
| eval actor=coalesce(operator, username, "anonymous")
| eval repository=coalesce('event_data.repository.repo_full_name', resource, repository)
| eval src_ip=coalesce(client_ip, src_ip, src)
| eval project=mvindex(split(repository, "/"), 0)
| lookup authorized_registry_users actor, project OUTPUT authorized
| where isnull(authorized) OR authorized!="yes"
| stats count as pull_count,
    dc(repository) as unique_repos,
    values(repository) as repos_pulled,
    dc(src_ip) as source_count,
    values(src_ip) as source_ips,
    latest(_time) as latest_pull,
    earliest(_time) as earliest_pull
    by actor, project
| eval pull_rate_per_hour=round(pull_count / max(1, (latest_pull - earliest_pull) / 3600), 1)
| where pull_count > 25 OR unique_repos > 5 OR pull_rate_per_hour > 100
| sort -pull_count

```

## Visualization

Stacked area chart (event volume by action_class over 24h), single-value tiles (push/pull/delete counts, unique actors, tag mutations), sortable actor-activity table with drilldown, tag-mutation table with red highlighting on protected tags, and optional geo-map of pull source IPs.

## Known False Positives

**webhook_replay_storm** — Harbor retries failed webhook deliveries with exponential backoff up to 10 attempts; a brief Splunk HEC outage followed by recovery replays hours of queued events, creating artificial volume spikes that look like a pull storm. Compare **`_time`** versus **`_indextime`** skew to identify replayed batches and deduplicate using the **`event_data.repository.digest`** plus **`op_time`** pair.

**service_account_noise** — CI/CD pipelines (Jenkins, GitHub Actions, GitLab CI, ArgoCD, Flux) generate high-volume pull events during build and deployment cycles that dominate audit dashboards; unless filtered by the **`is_ci_account`** flag or suppressed via the **`authorized_registry_users`** lookup, these legitimate pulls trigger anomalous-volume alerts every deployment window. Baseline normal CI pull rates per project and set thresholds at 2x the 95th percentile.

**mirror_replication_echo** — Harbor project-level replication jobs between a primary and disaster-recovery registry generate paired push events on both sides that appear as distinct human pushes; tag these with a **`replication`** action filter and exclude from supply-chain integrity alerts unless the replication target is an unexpected endpoint.

**scanner_pull_amplification** — Integrated vulnerability scanners (Trivy, Grype, Clair) pull every layer of every image on scan, generating pull counts 5–20x higher than actual developer or deployment activity; distinguish scanner actors by username pattern (`scanner-*`, `trivy-*`) or correlate with **`SCANNING_COMPLETED`** webhook events.

**gc_delete_burst** — Harbor scheduled garbage collection removes unreferenced blobs and manifests, producing hundreds of delete events in a narrow window that looks like mass artifact destruction; correlate timestamps with the Harbor GC schedule in your **`maintenance_windows`** lookup and suppress alerts during those windows.

**anonymous_pull_allowance** — Public-facing projects with anonymous pull enabled generate pull events without an actor identity, which the unauthorized-pull search flags as suspicious; whitelist public project names in the lookup or add a **`project_visibility`** field from the Harbor API to exclude public-project pulls.

**robot_credential_rotation** — When Harbor robot accounts are rotated, the old credential continues generating events during the overlap window while the new credential ramps up, creating dual-actor pulls on the same images; correlate with robot creation timestamps from **`harbor:audit`** `operation=create resource_type=robot` to distinguish rotation from credential sharing.

**tag_retention_cleanup** — Harbor tag retention policies automatically delete tags exceeding retention rules, generating delete events that are intentional lifecycle management rather than unauthorized destruction; filter by checking whether **`event_type`** is **`TAG_RETENTION`** rather than **`DELETE_ARTIFACT`**.

## References

- [Harbor Administration — Webhook Notifications](https://goharbor.io/docs/2.10.0/administration/webhook-notifications/)
- [Harbor API v2.0 — Audit Logs](https://goharbor.io/docs/2.10.0/build-customize-contribute/swagger/)
- [Docker Distribution Notification Configuration](https://distribution.github.io/distribution/about/notifications/)
- [Splunk REST API Modular Input (Splunkbase 1546)](https://splunkbase.splunk.com/app/1546)
- [Splunk HTTP Event Collector (HEC) Reference](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
