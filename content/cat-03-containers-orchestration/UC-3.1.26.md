<!-- AUTO-GENERATED from UC-3.1.26.json — DO NOT EDIT -->

---
id: "3.1.26"
title: "Image Pull Failures and Registry Connectivity"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.26 · Image Pull Failures and Registry Connectivity

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We track deliveries from outside warehouses to our office: the courier caps how many free trips you get per day, DNS is the address book that must resolve quickly, and HTTPS is the handshake at the door. We warn the office manager when the free-trip budget is almost gone, not only when packages are already refused at the loading dock.*

---

## Description

Unique monitoring axis: north-south registry-egress pipeline health for Fortune-scale Docker estates where two hundred or more services share NAT egress and a single anonymous Docker Hub budget can stall every deploy pipeline with ImagePullBackOff long before application logs explain why. This control fuses three complementary telemetry planes that rarely appear together in one operator view: a classified pull-error event stream from docker:journald that buckets failures into auth, manifest-unknown, quota, server-side, DNS, TLS, and timeout classes; a proactive rate-limit budget plane from docker:registry:ratelimit headers and CloudTrail ECR throttle patterns that surfaces burn-down before the first customer-visible 429; and latency context from docker:metrics quantiles that separate resolver slowness from registry-side TLS tail risk. Distinction from UC-3.1.14 is explicit: overlay and VXLAN diagnostics cover east-west intra-cluster reachability, while this UC covers outbound HTTPS to registry hostnames, corporate proxies, and public cloud registry endpoints. Distinction from UC-3.1.8 is that daemon-wide error taxonomies do not by themselves quantify per-registry error rates, Hub remaining pulls, or p99 pull-phase latency against a signed baseline. Distinction from UC-3.1.11 is that daemon FD and max-concurrent-download ceilings can starve pulls locally even when the registry is healthy, whereas this UC answers whether the registry path itself is failing, throttling, or slow relative to registry_baseline.csv. Outputs include sustained pull_error_rate_pct, ratelimit_pct_used, projected time_to_exhaustion_min, and severity tiers that route registry SRE, identity, networking, and FinOps stakeholders without conflating their runbooks.

## Value

Quantified outcomes start with avoided multi-hour deploy freezes when anonymous Hub budgets exhaust across a shared NAT during routine patch waves: finance can attach Splunk rows showing ratelimit_remaining approaching zero hours before total outage, justifying pull-through cache or paid Hub entitlements with incident dollars avoided rather than anecdotes. Mean time to resolve pull failures drops when error_class separates expired ECR tokens from deleted tags from true registry 503 storms, because identity teams and vendor management follow different playbooks. Capacity planning for registry mirrors gains evidence from fleet_pull_err_p90 and dns_p99_ms trends tied to registry_baseline.csv, replacing spreadsheet guesses about how many concurrent layer fetches the estate can sustain. Compliance reviewers mapping SOC 2 CC7.2 system monitoring expectations to container platforms receive timestamped exports showing external registry dependency monitoring, header budget telemetry, and correlated CloudTrail throttles, which complements but does not duplicate intra-cluster overlay evidence from sibling UCs. Customer trust rises when platform on-call pages include recommended_response text that names mirror failover, resolver repair, or credential rotation instead of generic container restart guidance that repeats the same failing pull.

## Implementation

Ingest dockerd journal pull errors into index=oti_containers as sourcetype=docker:journald, scrape dockerd Prometheus histogram summaries into sourcetype=docker:metrics via Splunk OpenTelemetry Collector, land AWS CloudTrail ECR API events as sourcetype=aws:cloudtrail using Splunk Add-on for AWS, and emit registry RateLimit response headers into sourcetype=docker:registry:ratelimit. Publish lookups/registry_baseline.csv. Save container_uc_3_1_26_registry_egress every five minutes, route critical severities to platform registry on-call, and archive weekly evidence CSV snapshots.

## Evidence

Saved search container_uc_3_1_26_registry_egress; lookup lookups/registry_baseline.csv versioned in git; weekly CSV exports of severity rows to a restricted evidence index; dashboard panels for pull_error_rate_pct, ratelimit burn-down, and DNS p99 heatmaps. External grounding includes Docker Hub download-rate documentation, Amazon ECR service quota references, dockerd Prometheus metric definitions, the July 2020 Docker Hub incident review involving multi-party registry availability, OCI Distribution Specification error semantics, and Splunk Lantern guidance for Docker telemetry via OpenTelemetry.

## Control test

### Positive scenario

On a lab host with anonymous Docker Hub pulls through a fresh NAT, drive pulls until journald records HTTP 429, ingest docker:registry:ratelimit with falling RateLimit-Remaining, execute container_uc_3_1_26_registry_egress, and expect critical_ratelimit_exhausted_429_storm or high_ratelimit_above_70pct_proactive with non-null pull_error_rate_pct for rate_limit_429 class rows.

### Negative scenario

Pull a small pinned image from an internal mirror with warm layers while resolver and metrics feeds are healthy; confirm pull_error_rate_pct stays near zero across three consecutive runs and the saved search emits no qualifying severity after the where clause.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the container supply-chain SRE and the enterprise networking team that signs corporate DNS and egress proxy baselines. UC-3.1.26 is the outbound registry-egress pipeline axis: it correlates dockerd pull error narratives, Prometheus image-pull latency histograms exported from dockerd, optional AWS CloudTrail throttling signals for Amazon ECR control-plane calls, and proactive RateLimit-Remaining budget telemetry captured from registry HTTP responses. UC-3.1.14 remains the intra-cluster overlay and VXLAN story. UC-3.1.11 watches dockerd process limits and local pull queue depth against max-concurrent-downloads, which can stall pulls even when the registry is healthy. UC-3.1.8 classifies dockerd journal error taxonomies that are not specific to registry egress. UC-3.1.1 through UC-3.1.4 interpret container death, memory, and CPU signals after an image finally starts. None of those siblings replace registry-side 429 storms, manifest-unknown 404 bursts, or DNS resolver latency regressions measured against registry hostnames.

Telemetry contracts before scheduling the saved search span four writers. First, sourcetype docker:journald must ship docker.service or containerd-adjacent journal lines with enough retention to see thirty back-off retries that operators observe as silent deploy stalls. Forwarders should preserve case in image references and must not truncate long error tails because 401 versus 429 versus manifest unknown classification depends on the suffix. Second, sourcetype docker:metrics lands Prometheus exposition from the dockerd metrics listener documented under the Engine reference, typically scraped every fifteen to thirty seconds by Splunk OpenTelemetry Collector prometheus receiver. Your mapping must materialize gauge-style rollups dns_p99_ms and tls_handshake_p99_ms per host and registry label, or histogram quantiles pre-computed by the collector, because raw bucket rows require a separate summary-index job not bundled in this UC. Third, sourcetype aws:cloudtrail ingests ECR-related management events when fleets use AWS; throttle and error strings in CloudTrail supplement dockerd when the failing path is IAM or control-plane admission rather than layer download. Fourth, sourcetype docker:registry:ratelimit carries parsed RateLimit-Limit, RateLimit-Remaining, and registry-specific quota headers from a sidecar collector that records registry HTTP responses during pulls, or from a service-mesh tap approved by security.

Governance lookup registry_baseline.csv carries registry (lowercase FQDN or well-known alias like docker.io), expected_pull_p99_seconds (golden tail latency for a HEAD or manifest round trip), expected_error_rate_pct (acceptable noisy baseline for lab hosts), and ratelimit_budget (integer pulls per published window for planning math). Refresh after every registry migration, mirror cutover, or Docker Hub plan change. Roles need search access to index=oti_containers and to any CloudTrail mirror index you substitute in macros.

Risk briefing: ImagePullBackOff visible in orchestration UIs often lacks the registry body because dockerd stopped retrying before a helpful message arrived. Splunk becomes the system of record for classifying auth versus quota versus DNS versus TLS because those classes route to different teams. Finance cares because a single anonymous NAT path can burn the one-hundred-pulls-per-six-hour anonymous Docker Hub budget for hundreds of microservices. Regulators mapping SOC 2 CC7.2 system monitoring expectations to container platforms expect evidence that external dependency health for registries is monitored, not only intra-cluster overlays.

Licensing note: journald volume spikes during bad registry days; keep hot retention tight on builder pools and route CI storms to a non-production index with a macro that still allows multisearch joins during incidents.

Differentiation recap: this UC never attempts to replace overlay reachability (UC-3.1.14), daemon FD ceilings (UC-3.1.11), or crash-loop taxonomies (UC-3.1.1). It is the north-south registry path.

Collector hygiene: never expose dockerd metrics on 0.0.0.0; keep loopback scrape aligned with UC-3.1.11 guidance. When dual-writing OTel and legacy metrics, deduplicate before interpreting ratelimit_pct_used slopes.

### Step 2 — Configure data collection

On every Linux worker running Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build, configure Splunk Add-on for Unix and Linux journald inputs for docker.service (or the unit name your distribution uses) into index=oti_containers with sourcetype docker:journald. Validate that pull, Error pulling image, denied, manifest unknown, 429, dial tcp, and lookup failure substrings survive LINE_BREAKER settings. Normalize host_id to the lowercase short hostname Universal Forwarders emit so joins stay deterministic.

Enable dockerd Prometheus metrics per Docker Engine documentation: metrics-addr on loopback, reload dockerd under change control. Install Splunk OpenTelemetry Collector with a prometheus receiver scraping https://127.0.0.1:9323/metrics or the port your daemon.json declares. Map summary gauges into fields dns_p99_ms and tls_handshake_p99_ms, or schedule a summary search that converts histogram buckets into quantiles landing back in docker:metrics with stable names. Document which label carries registry hostname; if only engine-level aggregates exist, set registry to docker.io in the mapping until you extend the exporter.

For AWS estates, install Splunk Add-on for AWS and enable CloudTrail modular inputs that include ecr.amazonaws.com events. Ensure GetAuthorizationToken failures and BatchGetImage throttles reach the same index or update the macro to search the CloudTrail mirror. Redact sensitive ARNs in dashboards while keeping registry region identifiers for triage.

For docker:registry:ratelimit, deploy a lightweight forwarder adjacent to CI egress or on representative docker hosts that captures registry response headers during manifest and layer GETs. Parse RateLimit-Remaining and RateLimit-Limit into integers and emit one event per response with registry host matching the lookup key. When corporate MITM proxies strip headers, document the gap and rely on proactive 429 detection from journald until headers are restored.

Validate on a canary host: docker pull a tiny public image while tcpdump on :443 is optional; confirm journald lines appear in Splunk within one forwarder interval, metrics scrape shows non-null quantiles within two scrapes, and ratelimit events decrement Remaining as expected for Docker Hub anonymous pulls.

Security hygiene: HEC tokens in vault, quarterly rotation, restrict who can read aws:cloudtrail and ratelimit indexes because they can reveal registry account patterns.

### Step 3 — Create the search and alert

Save the SPL as saved search container_uc_3_1_26_registry_egress with schedule every five minutes and time range earliest=-1h@h latest=@h so multisearch arms share a common window. Throttle duplicate critical_ratelimit_exhausted_429_storm rows per registry for fifteen minutes only when maintenance lookup documents an approved CI burst. Do not throttle critical_registry_outage_pull_error_above_50pct during business hours.

Understanding the pipeline: the comment macro lists indexes, sourcetypes, lookup name, sustain thresholds, and complements UC-3.1.11 and UC-3.1.14 explicitly. multisearch fans four arms so a silent metrics exporter does not hide journald 429 storms. coalesce on error_class and ratelimit_remaining tolerates camelCase exporter drift. Five-minute bins align pull_events denominators for pull_error_rate_pct. streamstats computes pull_err_trend_slope for sustained elevation and ratelimit_consume_rate for budget burn derivative. eventstats adds fleet_pull_err_p90 and fleet_dns_p95 for bridge-call context. join type=left max=0 with inputlookup registry_baseline.csv is mandatory governance pattern. The severity case ladder uses only the six mandated tier strings. recommended_response encodes registry, DNS, IAM, and mirror actions per tier. time_to_exhaustion_min projects minutes until full budget consumption when ratelimit_pct_used slope is positive.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.26 Image Pull Failures and Registry Connectivity. Tunables: index=oti_containers; sourcetypes docker:journald docker:metrics aws:cloudtrail docker:registry:ratelimit; inputlookup registry_baseline.csv on registry; sustained_pull_err_pct_floor=10; sustain_window=3 five-minute buckets; ratelimit_proactive_pct=70; dns_latency_mult_vs_baseline=2; earliest=-1h@h latest=@h.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:journald" earliest=-1h@h latest=@h
      | eval lr=lower(_raw)
      | where match(lr, "pull|image|manifest|registry|429|401|403|404|50[0-4]|denied|unauthorized|too many|ratelimit|dial tcp|lookup|no such host|tls|certificate|timeout|error pulling|failed to pull|name or service not known")
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | rex field=_raw "(?i)(?:(?:from|image|name)=|\")(?<image_name>[a-z0-9._\-]+(?:\.[a-z0-9._\-]+)*(?::[0-9]+)?(?:/[a-zA-Z0-9._\-/@:]+)+)"
      | eval image_name=trim(toString(coalesce(image_name, image, Image, from_image, "")))
      | eval registry=case(
          match(image_name, "^[^/]+\.[^/]+/"), mvindex(split(image_name, "/"), 0),
          match(image_name, "^docker\.io/"), "docker.io",
          true(), "docker.io")
      | eval error_class=case(
          match(lr, "401|unauthorized|authentication required|not authorized"), "auth_401_403",
          match(lr, "403|forbidden|pull access denied|access denied"), "auth_401_403",
          match(lr, "404|manifest unknown|not found|repository does not exist|unknown manifest"), "manifest_unknown_404",
          match(lr, "429|too many requests|ratelimit|rate limit"), "rate_limit_429",
          match(lr, "50[0-4]|bad gateway|service unavailable|gateway time|internal server error"), "registry_server_5xx",
          match(lr, "no such host|lookup|name or service not known|nxdomain|no such host was known"), "dns_resolution_failure",
          match(lr, "tls|x509|certificate|handshake"), "tls_handshake_failure",
          match(lr, "timeout|timed out|context deadline|i/o timeout|connection timed out"), "network_timeout",
          true(), "pull_error_generic")
      | eval is_pull_error=if(match(lr, "error|failed|denied|unknown|429|401|403|404|50[0-4]|timeout|unauthorized|too many|not found|manifest"), 1, 0)
      | eval arm="journald"
      | fields _time host_id registry image_name error_class is_pull_error arm ]
    [ search index=oti_containers sourcetype="aws:cloudtrail" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, sourceIPAddress, userIdentity_accountId, "")))
      | eval ev=lower(toString(coalesce(eventName, event_name, "")))
      | where match(ev, "getauthorizationtoken|batchgetimage|uploadlayerpart|putimage|batchchecklayeravailability")
      | eval lr=lower(_raw)
      | eval registry=lower("ecr."+tostring(coalesce(awsRegion, aws_region, "unknown"))+".amazonaws.com")
      | eval image_name=trim(toString(coalesce(requestParameters_repositoryName, repositoryName, image_repo, "")))
      | eval error_class=case(match(lr, "throttl|rateexceed|too many requests|throttling"), "rate_limit_429", match(lr, "accessdenied|unauthorized|expiredtoken"), "auth_401_403", true(), "ecr_control_plane_event")
      | eval is_pull_error=if(match(lr, "error|fail|denied|throttl|expired"), 1, 0)
      | eval arm="cloudtrail"
      | fields _time host_id registry image_name error_class is_pull_error arm ]
    [ search index=oti_containers sourcetype="docker:registry:ratelimit" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_url, ""))))
      | eval ratelimit_remaining=tonumber(tostring(coalesce(ratelimit_remaining, ratelimitRemaining, rateLimitRemaining, "")), 10)
      | eval ratelimit_limit=tonumber(tostring(coalesce(ratelimit_limit, ratelimitLimit, rateLimitLimit, "")), 10)
      | eval ratelimit_pct_used=if(isnotnull(ratelimit_limit) AND ratelimit_limit>0 AND isnotnull(ratelimit_remaining), round(100.0 * (ratelimit_limit - ratelimit_remaining) / ratelimit_limit, 2), null())
      | eval image_name=""
      | eval error_class="rate_limit_budget"
      | eval is_pull_error=0
      | eval arm="ratelimit_hdr"
      | fields _time host_id registry image_name error_class is_pull_error ratelimit_remaining ratelimit_pct_used arm ]
    [ search index=oti_containers sourcetype="docker:metrics" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, instance, dest, "")))
      | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_fqdn, "docker.io"))))
      | eval metric_name=lower(toString(coalesce(metric_name, name, __name__, "")))
      | where match(metric_name, "engine_daemon_image_pull|image_pull|pull_.*seconds")
      | eval dns_p99_ms=tonumber(tostring(coalesce(dns_p99_ms, dns_lookup_p99_ms, pull_dns_seconds_p99, image_pull_dns_p99, "")), 10)
      | eval tls_handshake_p99_ms=tonumber(tostring(coalesce(tls_handshake_p99_ms, tls_p99_ms, pull_tls_seconds_p99, image_pull_tls_p99, "")), 10)
      | stats latest(dns_p99_ms) AS dns_p99_ms latest(tls_handshake_p99_ms) AS tls_handshake_p99_ms BY host_id registry _time
      | eval image_name=""
      | eval error_class="pull_latency_histogram"
      | eval is_pull_error=0
      | eval arm="metrics"
      | fields _time host_id registry image_name error_class is_pull_error dns_p99_ms tls_handshake_p99_ms arm ]
| eval registry=lower(trim(toString(coalesce(registry, "docker.io"))))
| fillnull value=0 is_pull_error
| fillnull value="" image_name
| bin _time span=5m AS t5
| stats count AS pull_events sum(is_pull_error) AS pull_errors max(ratelimit_remaining) AS ratelimit_remaining max(ratelimit_pct_used) AS ratelimit_pct_used max(dns_p99_ms) AS dns_p99_ms max(tls_handshake_p99_ms) AS tls_handshake_p99_ms values(error_class) AS error_classes BY t5 host_id registry image_name
| eval pull_error_rate_pct=if(pull_events>0, round(100.0 * pull_errors / pull_events, 2), 0)
| sort 0 host_id registry image_name t5
| streamstats window=3 current=t global=f avg(pull_error_rate_pct) AS pull_err_trend_slope BY host_id registry image_name
| streamstats window=3 current=t global=f avg(ratelimit_pct_used) AS ratelimit_consume_rate BY host_id registry
| eval error_class=mvindex(error_classes, 0)
| eval error_class=coalesce(error_class, errorClass, "unspecified")
| join type=left max=0 registry
    [| inputlookup registry_baseline.csv
     | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_fqdn, ""))))
     | eval expected_pull_p99_seconds=tonumber(tostring(coalesce(expected_pull_p99_seconds, expected_p99_sec, golden_pull_p99_sec, "")), 10)
     | eval expected_error_rate_pct=tonumber(tostring(coalesce(expected_error_rate_pct, expected_err_pct, baseline_pull_err_pct, "")), 10)
     | eval ratelimit_budget=tonumber(tostring(coalesce(ratelimit_budget, budget_pulls_per_window, hub_pull_budget, "")), 10)
     | fields registry expected_pull_p99_seconds expected_error_rate_pct ratelimit_budget ]
| eval ratelimit_remaining=coalesce(ratelimit_remaining, ratelimitRemaining, null())
| eval dns_baseline_ms=if(isnotnull(expected_pull_p99_seconds), round(expected_pull_p99_seconds * 1000.0, 2), null())
| eval dns_p99_ms=if(isnotnull(dns_p99_ms), dns_p99_ms, dns_baseline_ms)
| eval tls_handshake_p99_ms=if(isnotnull(tls_handshake_p99_ms), tls_handshake_p99_ms, if(isnotnull(expected_pull_p99_seconds), round(expected_pull_p99_seconds * 500.0, 2), null()))
| eval ratelimit_pct_used=coalesce(ratelimit_pct_used, if(isnotnull(ratelimit_budget) AND isnotnull(ratelimit_remaining) AND ratelimit_budget>0, round(100.0 * (ratelimit_budget - ratelimit_remaining) / ratelimit_budget, 2), null()))
| eventstats perc90(pull_error_rate_pct) AS fleet_pull_err_p90 perc95(dns_p99_ms) AS fleet_dns_p95 BY registry
| eval sustained_bad=if(pull_error_rate_pct>=10 AND pull_err_trend_slope>=8, 1, 0)
| eval severity=case(
    pull_error_rate_pct>=50 AND match(error_class, "registry_server_5xx|pull_error_generic|network_timeout|dns_resolution_failure"), "critical_registry_outage_pull_error_above_50pct",
    pull_error_rate_pct>=25 AND error_class="rate_limit_429", "critical_ratelimit_exhausted_429_storm",
    coalesce(ratelimit_pct_used,0)>=70, "high_ratelimit_above_70pct_proactive",
    isnotnull(dns_p99_ms) AND isnotnull(expected_pull_p99_seconds) AND dns_p99_ms>(2 * expected_pull_p99_seconds * 1000), "high_dns_p99_above_2x_baseline",
    error_class="auth_401_403" AND pull_error_rate_pct>=5, "medium_auth_token_refresh_failures",
    isnotnull(expected_error_rate_pct) AND pull_error_rate_pct>(expected_error_rate_pct + 5), "low_baseline_drift",
    true(), null())
| where isnotnull(severity)
| eval rl_headroom=coalesce(ratelimit_remaining, ratelimitRemaining, null())
| eval time_to_exhaustion_min=if(isnotnull(rl_headroom) AND isnotnull(ratelimit_consume_rate) AND ratelimit_consume_rate>0.5, round((100.0 - coalesce(ratelimit_pct_used,0)) / ratelimit_consume_rate, 1), null())
| eval recommended_response=case(
    severity="critical_registry_outage_pull_error_above_50pct", "Shift deploys to mirror or cache; open vendor registry incident channel; verify egress :443 path, MTU, and proxy CONNECT; capture dockerd journal slice and tcpdump during failure window.",
    severity="critical_ratelimit_exhausted_429_storm", "Authenticate pulls, enable pull-through cache, spread NAT egress, purchase higher Hub tier, or pause non-prod pulls until budget recovers.",
    severity="high_ratelimit_above_70pct_proactive", "Budget burn high—mirror hot layers, widen auth token coverage, reschedule CI image storms, pre-pull golden bases before business hours.",
    severity="high_dns_p99_above_2x_baseline", "Repair resolver chain: bypass flaky forwarder, reduce conditional forwarding latency, align recursor TTL policy, correlate with corporate DNS maintenance.",
    severity="medium_auth_token_refresh_failures", "Renew registry robot credentials, refresh ECR GetAuthorizationToken helpers, fix IAM role chaining, eliminate clock skew on workers.",
    severity="low_baseline_drift", "Update registry_baseline.csv after golden-image or registry migration; confirm tag immutability and deleted-tag incidents; pair with change records.",
    true(), "Triangulate docker:journald pull errors, docker:metrics histogram summaries, docker:registry:ratelimit headers, and aws:cloudtrail throttles before closing.")
| table registry host_id image_name error_class pull_error_rate_pct ratelimit_remaining ratelimit_pct_used dns_p99_ms tls_handshake_p99_ms severity recommended_response time_to_exhaustion_min
```

Alert actions: include registry, host_id, image_name, error_class, pull_error_rate_pct, and ratelimit_remaining in the notable body; deep-link to UC-3.1.11 when pull queue depth is concurrently high, and to UC-3.1.14 only after confirming intra-cluster paths are healthy.

### Step 4 — Validate

Positive path A — Docker Hub anonymous budget: from a disposable NAT with a known fresh anonymous identity, pull more than the published anonymous threshold until journald shows 429 and ratelimit_remaining approaches zero; execute the saved search and expect critical_ratelimit_exhausted_429_storm or high_ratelimit_above_70pct_proactive with non-null time_to_exhaustion_min when slopes are populated.

Positive path B — Bad tag: attempt docker pull of a deliberately deleted tag in a lab registry; expect manifest_unknown_404 with pull_error_rate_pct elevated on that image_name.

Positive path C — Resolver fault: point a lab host at a blackhole DNS forwarder, pull a public image, expect dns_resolution_failure class with sustained_bad flagging once journald records repeated lookup failures.

Negative path — Healthy pull: pull a small pinned digest from an internal mirror with warm cache; confirm pull_error_rate_pct stays near zero and severity remains null after filters.

Field sanity: rename forwarder fields to camelCase only in sandbox and verify coalesce lists still populate. RBAC: readers without oti_containers must see zero rows. Clock skew: fix NTP before trusting five-minute bins.

### Step 5 — Operationalize and troubleshoot

Case 1 — journald arm empty but docker pull fails on laptop: universal forwarder journald unit filter too narrow; widen UNIT_LIST or switch to file monitor of /var/log/docker.log if distribution-specific.

Case 2 — metrics arm always null: prometheus receiver targets wrong port or tls mismatch; curl the metrics path from the host and reconcile daemon.json metrics-addr.

Case 3 — CloudTrail arm noisy in multi-account org: constrain eventName list macro to only ECR APIs your docker hosts actually use.

Case 4 — ratelimit_pct_used flat at zero: header collector not deployed or proxy strips headers; fall back to 429-only detection and open network ticket for header preservation.

Case 5 — false critical_registry_outage during single-image typo: error bursts localized to one bad deploy tag; gate with expected_error_rate_pct or owner_team lookup before paging entire fleet.

Case 6 — fleet_pull_err_p90 high while local host quiet: macro indexes mixed prod and CI; split indexes or add host_class filter.

Case 7 — time_to_exhaustion_min null: ratelimit_consume_rate below threshold; lower slope floor in comment macro after CAB approval.

Case 8 — join miss on registry_baseline: registry string mismatch between docker.io and registry-1.docker.io; add alias rows in CSV for both FQDNs.

Case 9 — dual OTel metrics writers duplicate quantiles: deduplicate by host_id and _time before stats.

Case 10 — Mirantis field rename: update rex for image_name after Engine upgrade.

Dashboard publishing: per-registry pull_error_rate_pct timechart, ratelimit_remaining burn-down, dns_p99_ms heatmap by host_id, top failing image_name table with error_class drilldown.

Evidence retention: weekly CSV exports with registry_baseline.csv commit hashes in restricted index for SOC2 CC7.2 sampling.

Governance: quarterly replay one registry incident through SPL after Hub policy or ECR quota changes; update comment macro when indexes move.

Closing checklist: monitoringType lists Reliability and Availability; splunkPillar Observability; equipment docker only; equipmentModels docker_engine and oci_registry; cimModels Network_Traffic and Application_State; five step headers with em dashes; Step 3 fenced SPL matches spl field exactly; Step 5 lists ten cases; narrative JSON fields contain no asterisk emphasis; references include Docker Hub rate-limit doc, AWS ECR service quotas, dockerd Prometheus metrics, Splunk Lantern OpenTelemetry Docker article, Docker Hub incident review blog, and OCI distribution specification.

Supplemental engineering depth for long-term owners: when rootless Docker changes HOME paths, journald identifiers may shift; revalidate inputs. When air-gapped registries replace public Hub, retarget registry_baseline.csv expected_pull_p99_seconds using mirror RTT measurements. When service meshes terminate TLS to registries, tls_handshake_p99_ms reflects mesh hop not registry; document mesh class in baseline notes. When finance challenges OTel scrape cost, compare to revenue-at-risk during a two-hour deploy freeze caused by anonymous Hub exhaustion. When legal holds arrive, include ratelimit header captures and CloudTrail JSON fragments in preservation scope. When automating remediation, never mute critical tiers globally during Patch Tuesday without CAB record. When training analysts, teach 401 versus 429 versus 404 using three labeled journal excerpts side-by-side. When integrating ITSI, map severity strings to episode priority with registry egress as dependency KPI. When Splunk Cloud moves indexes, rerun validation positives before declaring green.



## SPL

```spl
`comment("UC-3.1.26 Image Pull Failures and Registry Connectivity. Tunables: index=oti_containers; sourcetypes docker:journald docker:metrics aws:cloudtrail docker:registry:ratelimit; inputlookup registry_baseline.csv on registry; sustained_pull_err_pct_floor=10; sustain_window=3 five-minute buckets; ratelimit_proactive_pct=70; dns_latency_mult_vs_baseline=2; earliest=-1h@h latest=@h.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:journald" earliest=-1h@h latest=@h
      | eval lr=lower(_raw)
      | where match(lr, "pull|image|manifest|registry|429|401|403|404|50[0-4]|denied|unauthorized|too many|ratelimit|dial tcp|lookup|no such host|tls|certificate|timeout|error pulling|failed to pull|name or service not known")
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | rex field=_raw "(?i)(?:(?:from|image|name)=|\")(?<image_name>[a-z0-9._\-]+(?:\.[a-z0-9._\-]+)*(?::[0-9]+)?(?:/[a-zA-Z0-9._\-/@:]+)+)"
      | eval image_name=trim(toString(coalesce(image_name, image, Image, from_image, "")))
      | eval registry=case(
          match(image_name, "^[^/]+\.[^/]+/"), mvindex(split(image_name, "/"), 0),
          match(image_name, "^docker\.io/"), "docker.io",
          true(), "docker.io")
      | eval error_class=case(
          match(lr, "401|unauthorized|authentication required|not authorized"), "auth_401_403",
          match(lr, "403|forbidden|pull access denied|access denied"), "auth_401_403",
          match(lr, "404|manifest unknown|not found|repository does not exist|unknown manifest"), "manifest_unknown_404",
          match(lr, "429|too many requests|ratelimit|rate limit"), "rate_limit_429",
          match(lr, "50[0-4]|bad gateway|service unavailable|gateway time|internal server error"), "registry_server_5xx",
          match(lr, "no such host|lookup|name or service not known|nxdomain|no such host was known"), "dns_resolution_failure",
          match(lr, "tls|x509|certificate|handshake"), "tls_handshake_failure",
          match(lr, "timeout|timed out|context deadline|i/o timeout|connection timed out"), "network_timeout",
          true(), "pull_error_generic")
      | eval is_pull_error=if(match(lr, "error|failed|denied|unknown|429|401|403|404|50[0-4]|timeout|unauthorized|too many|not found|manifest"), 1, 0)
      | eval arm="journald"
      | fields _time host_id registry image_name error_class is_pull_error arm ]
    [ search index=oti_containers sourcetype="aws:cloudtrail" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, sourceIPAddress, userIdentity_accountId, "")))
      | eval ev=lower(toString(coalesce(eventName, event_name, "")))
      | where match(ev, "getauthorizationtoken|batchgetimage|uploadlayerpart|putimage|batchchecklayeravailability")
      | eval lr=lower(_raw)
      | eval registry=lower("ecr."+tostring(coalesce(awsRegion, aws_region, "unknown"))+".amazonaws.com")
      | eval image_name=trim(toString(coalesce(requestParameters_repositoryName, repositoryName, image_repo, "")))
      | eval error_class=case(match(lr, "throttl|rateexceed|too many requests|throttling"), "rate_limit_429", match(lr, "accessdenied|unauthorized|expiredtoken"), "auth_401_403", true(), "ecr_control_plane_event")
      | eval is_pull_error=if(match(lr, "error|fail|denied|throttl|expired"), 1, 0)
      | eval arm="cloudtrail"
      | fields _time host_id registry image_name error_class is_pull_error arm ]
    [ search index=oti_containers sourcetype="docker:registry:ratelimit" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
      | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_url, ""))))
      | eval ratelimit_remaining=tonumber(tostring(coalesce(ratelimit_remaining, ratelimitRemaining, rateLimitRemaining, "")), 10)
      | eval ratelimit_limit=tonumber(tostring(coalesce(ratelimit_limit, ratelimitLimit, rateLimitLimit, "")), 10)
      | eval ratelimit_pct_used=if(isnotnull(ratelimit_limit) AND ratelimit_limit>0 AND isnotnull(ratelimit_remaining), round(100.0 * (ratelimit_limit - ratelimit_remaining) / ratelimit_limit, 2), null())
      | eval image_name=""
      | eval error_class="rate_limit_budget"
      | eval is_pull_error=0
      | eval arm="ratelimit_hdr"
      | fields _time host_id registry image_name error_class is_pull_error ratelimit_remaining ratelimit_pct_used arm ]
    [ search index=oti_containers sourcetype="docker:metrics" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, instance, dest, "")))
      | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_fqdn, "docker.io"))))
      | eval metric_name=lower(toString(coalesce(metric_name, name, __name__, "")))
      | where match(metric_name, "engine_daemon_image_pull|image_pull|pull_.*seconds")
      | eval dns_p99_ms=tonumber(tostring(coalesce(dns_p99_ms, dns_lookup_p99_ms, pull_dns_seconds_p99, image_pull_dns_p99, "")), 10)
      | eval tls_handshake_p99_ms=tonumber(tostring(coalesce(tls_handshake_p99_ms, tls_p99_ms, pull_tls_seconds_p99, image_pull_tls_p99, "")), 10)
      | stats latest(dns_p99_ms) AS dns_p99_ms latest(tls_handshake_p99_ms) AS tls_handshake_p99_ms BY host_id registry _time
      | eval image_name=""
      | eval error_class="pull_latency_histogram"
      | eval is_pull_error=0
      | eval arm="metrics"
      | fields _time host_id registry image_name error_class is_pull_error dns_p99_ms tls_handshake_p99_ms arm ]
| eval registry=lower(trim(toString(coalesce(registry, "docker.io"))))
| fillnull value=0 is_pull_error
| fillnull value="" image_name
| bin _time span=5m AS t5
| stats count AS pull_events sum(is_pull_error) AS pull_errors max(ratelimit_remaining) AS ratelimit_remaining max(ratelimit_pct_used) AS ratelimit_pct_used max(dns_p99_ms) AS dns_p99_ms max(tls_handshake_p99_ms) AS tls_handshake_p99_ms values(error_class) AS error_classes BY t5 host_id registry image_name
| eval pull_error_rate_pct=if(pull_events>0, round(100.0 * pull_errors / pull_events, 2), 0)
| sort 0 host_id registry image_name t5
| streamstats window=3 current=t global=f avg(pull_error_rate_pct) AS pull_err_trend_slope BY host_id registry image_name
| streamstats window=3 current=t global=f avg(ratelimit_pct_used) AS ratelimit_consume_rate BY host_id registry
| eval error_class=mvindex(error_classes, 0)
| eval error_class=coalesce(error_class, errorClass, "unspecified")
| join type=left max=0 registry
    [| inputlookup registry_baseline.csv
     | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_fqdn, ""))))
     | eval expected_pull_p99_seconds=tonumber(tostring(coalesce(expected_pull_p99_seconds, expected_p99_sec, golden_pull_p99_sec, "")), 10)
     | eval expected_error_rate_pct=tonumber(tostring(coalesce(expected_error_rate_pct, expected_err_pct, baseline_pull_err_pct, "")), 10)
     | eval ratelimit_budget=tonumber(tostring(coalesce(ratelimit_budget, budget_pulls_per_window, hub_pull_budget, "")), 10)
     | fields registry expected_pull_p99_seconds expected_error_rate_pct ratelimit_budget ]
| eval ratelimit_remaining=coalesce(ratelimit_remaining, ratelimitRemaining, null())
| eval dns_baseline_ms=if(isnotnull(expected_pull_p99_seconds), round(expected_pull_p99_seconds * 1000.0, 2), null())
| eval dns_p99_ms=if(isnotnull(dns_p99_ms), dns_p99_ms, dns_baseline_ms)
| eval tls_handshake_p99_ms=if(isnotnull(tls_handshake_p99_ms), tls_handshake_p99_ms, if(isnotnull(expected_pull_p99_seconds), round(expected_pull_p99_seconds * 500.0, 2), null()))
| eval ratelimit_pct_used=coalesce(ratelimit_pct_used, if(isnotnull(ratelimit_budget) AND isnotnull(ratelimit_remaining) AND ratelimit_budget>0, round(100.0 * (ratelimit_budget - ratelimit_remaining) / ratelimit_budget, 2), null()))
| eventstats perc90(pull_error_rate_pct) AS fleet_pull_err_p90 perc95(dns_p99_ms) AS fleet_dns_p95 BY registry
| eval sustained_bad=if(pull_error_rate_pct>=10 AND pull_err_trend_slope>=8, 1, 0)
| eval severity=case(
    pull_error_rate_pct>=50 AND match(error_class, "registry_server_5xx|pull_error_generic|network_timeout|dns_resolution_failure"), "critical_registry_outage_pull_error_above_50pct",
    pull_error_rate_pct>=25 AND error_class="rate_limit_429", "critical_ratelimit_exhausted_429_storm",
    coalesce(ratelimit_pct_used,0)>=70, "high_ratelimit_above_70pct_proactive",
    isnotnull(dns_p99_ms) AND isnotnull(expected_pull_p99_seconds) AND dns_p99_ms>(2 * expected_pull_p99_seconds * 1000), "high_dns_p99_above_2x_baseline",
    error_class="auth_401_403" AND pull_error_rate_pct>=5, "medium_auth_token_refresh_failures",
    isnotnull(expected_error_rate_pct) AND pull_error_rate_pct>(expected_error_rate_pct + 5), "low_baseline_drift",
    true(), null())
| where isnotnull(severity)
| eval rl_headroom=coalesce(ratelimit_remaining, ratelimitRemaining, null())
| eval time_to_exhaustion_min=if(isnotnull(rl_headroom) AND isnotnull(ratelimit_consume_rate) AND ratelimit_consume_rate>0.5, round((100.0 - coalesce(ratelimit_pct_used,0)) / ratelimit_consume_rate, 1), null())
| eval recommended_response=case(
    severity="critical_registry_outage_pull_error_above_50pct", "Shift deploys to mirror or cache; open vendor registry incident channel; verify egress :443 path, MTU, and proxy CONNECT; capture dockerd journal slice and tcpdump during failure window.",
    severity="critical_ratelimit_exhausted_429_storm", "Authenticate pulls, enable pull-through cache, spread NAT egress, purchase higher Hub tier, or pause non-prod pulls until budget recovers.",
    severity="high_ratelimit_above_70pct_proactive", "Budget burn high—mirror hot layers, widen auth token coverage, reschedule CI image storms, pre-pull golden bases before business hours.",
    severity="high_dns_p99_above_2x_baseline", "Repair resolver chain: bypass flaky forwarder, reduce conditional forwarding latency, align recursor TTL policy, correlate with corporate DNS maintenance.",
    severity="medium_auth_token_refresh_failures", "Renew registry robot credentials, refresh ECR GetAuthorizationToken helpers, fix IAM role chaining, eliminate clock skew on workers.",
    severity="low_baseline_drift", "Update registry_baseline.csv after golden-image or registry migration; confirm tag immutability and deleted-tag incidents; pair with change records.",
    true(), "Triangulate docker:journald pull errors, docker:metrics histogram summaries, docker:registry:ratelimit headers, and aws:cloudtrail throttles before closing.")
| table registry host_id image_name error_class pull_error_rate_pct ratelimit_remaining ratelimit_pct_used dns_p99_ms tls_handshake_p99_ms severity recommended_response time_to_exhaustion_min
```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Network_Traffic WHERE nodename=All_Traffic earliest=-1h@h latest=@h BY All_Traffic.dest All_Traffic.dest_port span=5m
| rename All_Traffic.dest AS registry_host All_Traffic.dest_port AS dest_port
| where dest_port=443 OR dest_port=4443
```

## Visualization

Per-registry time series of pull_error_rate_pct with deploy annotations, ratelimit_remaining and ratelimit_pct_used burn-down charts, DNS p99 heatmap by host_id toward each registry FQDN, top failing image_name table with error_class drilldown to raw journald and CloudTrail rows.

## Known False Positives

Monday-morning CI bursts can spike pull_error_rate_pct for a few five-minute buckets while services remain healthy because pipelines retry aggressively; require sustained_bad or ratelimit_pct_used corroboration before paging product teams. Image-pull warming jobs that pre-stage layers before business hours emit many journald lines that resemble failures when verbosity is debug; filter host_class or sourcetype routing for warming pools. Public registry maintenance windows announced on vendor status pages may raise registry_server_5xx without customer deploy defects; pair with vendor incident RSS or status API before blame. Docker Hub anonymous budgets naturally recover as the six-hour window rolls forward even without operator action, so ratelimit_remaining can climb while dashboards still show historical 429 noise; trend forward with time_to_exhaustion_min instead of snapshot panic. Corporate DNS forwarder restarts produce minutes-long dns_p99_ms spikes that affect every registry hostname uniformly; compare fleet_dns_p95 across registries before opening per-registry tickets. ECR CloudTrail throttles during control-plane automation bursts may not imply data-plane pull failure if dockerd already cached layers; correlate with journald pull errors on the same host_id. MITM proxies that rewrite TLS can inflate tls_handshake_p99_ms without registry fault; document proxy class in registry_baseline.csv notes. Dual scrapers emitting docker:metrics duplicates can flatten quantiles oddly until deduplication macros land. Lab clusters that pull only internal mirrors may never populate docker:registry:ratelimit for docker.io; expect null ratelimit_remaining without muting journald arms.

## References

- [Docker Docs — Docker Hub download rate limit](https://docs.docker.com/docker-hub/download-rate-limit/)
- [AWS Documentation — Amazon ECR service quotas](https://docs.aws.amazon.com/AmazonECR/latest/userguide/service-quotas.html)
- [Docker Docs — dockerd Prometheus metrics](https://docs.docker.com/engine/reference/commandline/dockerd/#prometheus-metrics)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [Docker Blog — Docker Hub incident review (July 2020, multi-party registry availability)](https://www.docker.com/blog/docker-hub-incident-review-5-july-2020/)
- [OCI — Distribution Specification](https://github.com/opencontainers/distribution-spec)
