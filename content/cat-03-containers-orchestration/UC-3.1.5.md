<!-- AUTO-GENERATED from UC-3.1.5.json — DO NOT EDIT -->

---
id: "3.1.5"
title: "Image Vulnerability Scanning Coverage and Patch SLA"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.5 · Image Vulnerability Scanning Coverage and Patch SLA

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We check that every serious meal leaving the kitchen still has a fresh safety inspection sticker, not only that yesterday's menu listed ingredients. If the sticker is missing, expired, or the kitchen swapped the plate without a new check, we raise the alarm so teams fix the process—not just one dish.*

---

## Description

Fortune-scale container programs can paste impressive CVE dashboards yet still run production workloads whose digests have never been scanned in the governed pipeline, whose last attestation predates an active upstream advisory, or whose mutable production tags silently repointed to rebuilt layers without a fresh scan record. This use case detects those governance failures by correlating scanner governance manifests, Kubernetes and registry admission evidence, and scanner pipeline heartbeats. It measures scan staleness versus a production freshness SLA, admission gates without matching attestations, scanner database freshness drift, per-severity remediation aging with Critical seven-day, High fourteen-day, Medium thirty-day, and Low ninety-day clocks, mutable-tag digest shifts, and fleet coverage percentage for in-scope images. UC-3.1.10 remains the deep CVE triage and enrichment story once scan rows exist; this UC answers whether scanning and attestation processes themselves are complete, timely, and trustworthy.

## Value

Audit and risk committees gain defensible evidence that production images stay inside scan coverage and patch SLAs instead of relying on anecdotal CI schedules. Mean-time-to-remediate improves when Critical and High breaches surface as accountable rows tied to owners, not buried in scanner CSV exports. Operational toil drops when admission denials, stale attestations, and heartbeat silence route to the same Splunk view, shrinking war rooms that previously debated whether a missing CVE row meant clean software or a broken scanner. Customer and regulator conversations about ISO 27001 A.12.6, PCI DSS 6.2 style patching discipline, and NIST SP 800-190 container supply-chain expectations strengthen when coverage_pct and SLA breach tables export with timestamps and lookup versions.

## Implementation

Land trivy:governance:manifest, grype:governance:manifest, snyk:container:governance, kube:audit, k8s:admission:gatekeeper, registry:webhook:admission, and scanner:pipeline:heartbeat in index=oti_containers via HEC or approved collectors. Publish prod_image_scope.csv and scanner_telemetry_baseline.csv in git. Save container_uc_3_1_5_image_scan_coverage_patch_sla hourly, route BREACH and COVERAGE-GAP tiers to platform and appsec bridges, and archive weekly evidence exports with lookup hashes.

## Evidence

Saved search container_uc_3_1_5_image_scan_coverage_patch_sla with weekly CSV exports to a restricted evidence index, versioned prod_image_scope.csv and scanner_telemetry_baseline.csv commit hashes, dashboard drilldowns linking to raw governance manifests and kube:audit JSON.

## Control test

### Positive scenario

In a lab cluster, deploy a digest listed in prod_image_scope.csv with kube:audit evidence, withhold scan_attest manifests beyond the configured prod_scan_sla_hours, run the saved search, and expect COVERAGE-GAP or stale_scan_attestation with non-null action_required.

### Negative scenario

Ingest matching governance manifest and admission rows for the same digest within SLA hours with zero open findings, confirm sla_breach_severity stays WITHIN-SLA and coverage_gap equals scan_current after lookups classify the row in scope.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the application security lead, the CI and registry platform owner, and the vulnerability management lead who signs remediation SLAs. UC-3.1.5 is the governance plane above raw scanner findings: it proves that production-bound images receive timely vulnerability scans, that scanner databases and pipelines stay observable, that admission and audit evidence lines up with attestations, and that patch clocks per severity are measurable per image identity. UC-3.1.10 remains the sibling that triages CVE rows, Known Exploited Vulnerability enrichment, and EPSS-weighted prioritization once a scan exists. UC-3.1.21 covers Falco and eBPF runtime behavior after workloads execute. UC-3.1.26 covers registry pull failures and north-south connectivity. None of those substitutes scan coverage percentage, admission-time attestation gaps, or per-severity remediation aging sourced from governance manifests.

Before indexing, define data contracts. Governance manifests must land as one sourcetype per vendor family (trivy:governance:manifest, grype:governance:manifest, snyk:container:governance) with stable fields for image digest, optional mutable tag, registry host, repository, open counts by severity, oldest open epoch per severity, and scanner database refresh epoch. Admission and audit sources must preserve Kubernetes objectRef.namespace, resolved digest when mutating admission controllers rewrite tags, and denial reasons from Gatekeeper constraints. Pipeline heartbeat events use scanner:pipeline:heartbeat with scanner identity, last successful database sync epoch, and optional semantic version for drift tracking versus scanner_telemetry_baseline.csv in a companion alert the platform team schedules every five minutes.

RBAC separates developers who may see aggregate coverage tiles from security operations staff who see row-level owner and digest detail. HEC tokens live in vault with quarterly rotation. Customer or internal identifiers in repository paths should be redacted when regulation demands.

Lookups require version control in git. prod_image_scope.csv lists row_key (digest preferred, else normalized image reference), in_production_scope flag, owner_team, and optional notes for shared golden images. scanner_telemetry_baseline.csv lists expected minimum scanner semver and maximum acceptable vulndb age per registry shard for drift analytics that complement this search.

Risk context for executives: an image with zero Critical findings on paper is still a governance failure if the scan is ninety-six hours stale during an active upstream advisory window, or if admission logs show a digest that never received a matching attestation row. Coverage metrics matter as much as vulnerability counts for audit narratives.

Licensing and volume: governance manifests are far smaller than per-CVE JSON streams; heartbeat rows are tiny. Budget impact is dominated by audit and admission volumes on busy clusters, so route noisy dev namespaces to a non-production index with macros that still allow multisearch joins during incidents.

Legal and privacy: admission payloads can include environment variables or command arguments in some cluster configurations; strip or hash fields at ingest when counsel requires minimization.

Differentiation recap: this UC never attempts to replace UC-3.1.10 CVE triage, UC-3.1.21 runtime detections, UC-3.1.25 docker.sock exposure, or UC-3.1.26 registry egress health. It is the scanning coverage, attestation freshness, and remediation SLA clock layer.

### Step 2 — Configure data collection

Configure CI systems such as GitHub Actions, GitLab CI, Jenkins, Tekton, or Argo CD hooks to emit governance manifests immediately after scanner jobs succeed, posting JSON to Splunk HTTP Event Collector with sourcetype locked per vendor. Normalize RepoDigest strings to lowercase sha256 form before send. When scanners run in registry-integrated mode (Aqua Trivy against Harbor, Anchore Enterprise against ECR), forward the summary object your vendor exposes rather than full CVE arrays.

For Kubernetes, enable audit logging at the API server with storage backends that forward to Splunk via Splunk Connect for Kubernetes patterns or an approved OpenTelemetry collector. Map sourcetype kube:audit for pod and deployment mutations. Install Gatekeeper or an equivalent policy engine and forward constraint violation events to sourcetype k8s:admission:gatekeeper with denial messages and attempted image references. Registry admission webhooks that enforce Cosign or vulnerability scan attestations should emit structured JSON to sourcetype registry:webhook:admission including resolved digest fields.

Schedule centralized scanner jobs to emit scanner:pipeline:heartbeat every five or fifteen minutes with db_last_success_epoch populated from the scanner vendor API or local Trivy DB metadata. Pair heartbeat monitoring with a lightweight saved search that alerts when now() minus the latest heartbeat exceeds two intervals, independent of per-image stats, so scanner silence never hides inside digest aggregation.

On Splunk indexers, create props.conf and transforms.conf that timestamp events at scan completion or admission decision time, extract nested JSON without dropping digest casing rules, and route quarantined namespaces to alternate indexes only when macros are updated in parallel.

Validate with a canary digest: run a known scan, confirm governance manifest arrives within one forwarder interval, mutate a deployment to pull the digest, confirm kube:audit rows share the same row_key, and verify heartbeat age stays below the documented threshold in lab.

Security hygiene: never ship registry credentials inside HEC payloads. Use short-lived tokens on collectors. Document air-gapped mirror lag separately because database freshness epochs will reflect internal mirror sync, not public NVD latency.

### Step 3 — Create the search and alert

Save the SPL as saved search container_uc_3_1_5_image_scan_coverage_patch_sla with schedule hourly over earliest=-30d@d latest=now for governance dashboards, and throttle duplicate COVERAGE-GAP rows per row_key for six hours unless severity escalates to a BREACH tier within the same business day.

Pipeline walkthrough for operators: the opening comment macro lists every index, sourcetype family, SLA day count, scan freshness hour gate, and lookup contract so on-call engineers avoid improvising thresholds during incidents. The multisearch fans two arms so a silent scanner feed does not hide admission evidence, and a quiet cluster does not imply scanners are healthy without consulting the separate heartbeat alert described in Step 2.

The scan_attest arm normalizes Trivy, Grype, and Snyk governance manifests that your CI or registry sidecar emits after each scan completes. These events intentionally carry counts and oldest-open epochs per severity rather than full CVE listings, keeping this UC orthogonal to UC-3.1.10 digest triage. The deploy_admission arm ingests Kubernetes audit create and patch operations, OPA Gatekeeper denials, and registry admission webhooks that prove which image reference attempted to enter production.

After fan-in, stats collapses to one row per row_key registry repo tag grain. last_scan_epoch and last_deploy_epoch provide the timestamps needed for stale attestation and pre-deploy gate analytics. latest_deploy_digest supports mutable-tag drift logic without re-implementing UC-3.1.10 per-CVE math.

The join type=left max=0 against prod_image_scope.csv marks images that are truly in production scope versus lab-only runners, and binds owner for paging. coverage_gap encodes never_scanned, stale_scan_attestation, scan_current, and out_of_scope states. digest_mismatch_hint surfaces silent rebuild bypass risk when admission resolves a digest that no longer matches the attested row key.

Remediation SLA evaluation uses open counts with oldest-open epochs: Critical beyond seven days, High beyond fourteen, Medium beyond thirty, Low beyond ninety. sla_breach_severity merges coverage and mutability outcomes ahead of a quiet WITHIN-SLA bucket. streamstats window=2 provides a minimal sequence counter for registry-level trending in dashboards without replacing full summary indexing. eventstats computes fleet_scanned_current against fleet_total for coverage_pct scorecards per result set.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.1.5 Image Vulnerability Scanning Coverage and Patch SLA. Tunables: index=oti_containers; prod_scan_max_age_hours=24; scanner_db_stale_warn_hours=72; remediation_SLA_days Critical=7 High=14 Medium=30 Low=90; lookups prod_image_scope.csv scanner_telemetry_baseline.csv; earliest=-30d@d latest=now")`
| multisearch
    [ search index=oti_containers (sourcetype="trivy:governance:manifest" OR sourcetype="grype:governance:manifest" OR sourcetype="snyk:container:governance")
      earliest=-30d@d latest=now
      | eval lane="scan_attest"
      | eval row_key=lower(trim(toString(coalesce(image_digest, digest, RepoDigest, repo_digest, ""))))
      | eval row_key=if(len(row_key)>12, row_key, lower(trim(toString(coalesce(image_ref, ArtifactName, Target, image_name, image, "")))))
      | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_fqdn, ""))))
      | eval repo=trim(toString(coalesce(repository, repo, image_repo, "")))
      | eval tag=trim(toString(coalesce(tag, image_tag, mutable_tag, "")))
      | eval scanner=case(sourcetype="trivy:governance:manifest", "trivy", sourcetype="grype:governance:manifest", "grype", true(), "snyk")
      | eval db_fresh_epoch=tonumber(tostring(coalesce(scanner_db_updated_epoch, vulndb_last_sync_epoch, grype_db_epoch, "0")), 10)
      | eval has_open_critical=tonumber(tostring(coalesce(open_critical_count, crit_open, "0")), 10)
      | eval has_open_high=tonumber(tostring(coalesce(open_high_count, high_open, "0")), 10)
      | eval has_open_medium=tonumber(tostring(coalesce(open_medium_count, med_open, "0")), 10)
      | eval has_open_low=tonumber(tostring(coalesce(open_low_count, low_open, "0")), 10)
      | eval oldest_crit_open_epoch=tonumber(tostring(coalesce(oldest_critical_open_epoch, critical_first_seen_epoch, "0")), 10)
      | eval oldest_high_open_epoch=tonumber(tostring(coalesce(oldest_high_open_epoch, high_first_seen_epoch, "0")), 10)
      | eval oldest_med_open_epoch=tonumber(tostring(coalesce(oldest_medium_open_epoch, med_first_seen_epoch, "0")), 10)
      | eval oldest_low_open_epoch=tonumber(tostring(coalesce(oldest_low_open_epoch, low_first_seen_epoch, "0")), 10)
      | eval namespace=trim(toString(coalesce(k8s_namespace, namespace, team_namespace, "")))
      | eval deploy_digest_cand=""
      | fields _time lane row_key registry repo tag scanner db_fresh_epoch has_open_critical has_open_high has_open_medium has_open_low oldest_crit_open_epoch oldest_high_open_epoch oldest_med_open_epoch oldest_low_open_epoch namespace deploy_digest_cand ]
    [ search index=oti_containers (sourcetype="kube:audit" OR sourcetype="k8s:admission:gatekeeper" OR sourcetype="registry:webhook:admission")
      earliest=-30d@d latest=now
      | eval lane="deploy_admission"
      | eval image_ref=trim(toString(coalesce(requestObject_spec_containers_0_image, object_spec_image, image, container_image, denied_image, "")))
      | eval row_key=lower(trim(toString(coalesce(image_digest, resolved_digest, ""))))
      | eval row_key=if(len(row_key)>12, row_key, lower(trim(image_ref)))
      | eval deploy_digest_cand=lower(trim(toString(coalesce(image_digest, resolved_digest, ""))))
      | eval registry=lower(trim(toString(coalesce(registry, ""))))
      | eval repo=trim(toString(coalesce(repository, repo, "")))
      | eval tag=trim(toString(coalesce(tag, "")))
      | eval namespace=trim(toString(coalesce(objectRef_namespace, namespace, "")))
      | eval scanner=""
      | eval db_fresh_epoch=0
      | eval has_open_critical=0 | eval has_open_high=0 | eval has_open_medium=0 | eval has_open_low=0
      | eval oldest_crit_open_epoch=0 | eval oldest_high_open_epoch=0 | eval oldest_med_open_epoch=0 | eval oldest_low_open_epoch=0
      | where len(row_key)>5
      | fields _time lane row_key registry repo tag scanner db_fresh_epoch has_open_critical has_open_high has_open_medium has_open_low oldest_crit_open_epoch oldest_high_open_epoch oldest_med_open_epoch oldest_low_open_epoch namespace deploy_digest_cand ]
| stats
    max(eval(if(lane="scan_attest", _time, null()))) AS last_scan_epoch
    max(eval(if(lane="deploy_admission", _time, null()))) AS last_deploy_epoch
    max(eval(if(lane="deploy_admission" AND len(deploy_digest_cand)>12, deploy_digest_cand, null()))) AS latest_deploy_digest
    max(eval(if(lane="scan_attest", db_fresh_epoch, null()))) AS last_scan_db_epoch
    values(scanner) AS scanners_seen
    max(has_open_critical) AS open_critical
    max(has_open_high) AS open_high
    max(has_open_medium) AS open_medium
    max(has_open_low) AS open_low
    max(oldest_crit_open_epoch) AS crit_first_epoch
    max(oldest_high_open_epoch) AS high_first_epoch
    max(oldest_med_open_epoch) AS med_first_epoch
    max(oldest_low_open_epoch) AS low_first_epoch
    values(lane) AS lanes_present
    latest(namespace) AS namespace
  BY row_key registry repo tag
| eval team=coalesce(namespace, "unassigned")
| join type=left max=0 row_key
    [| inputlookup prod_image_scope.csv
     | eval row_key=lower(trim(toString(coalesce(row_key, image_digest, image_ref_key, ""))))
     | eval in_prod_scope=tonumber(tostring(coalesce(in_production_scope, prod, "1")), 10)
     | eval owner=trim(toString(coalesce(owner_team, accountable_owner, platform_owner, "")))
     | fields row_key in_prod_scope owner ]
| fillnull value=1 in_prod_scope
| fillnull value="" owner
| eval scan_age_hours=if(isnotnull(last_scan_epoch) AND last_scan_epoch>0, round((now()-last_scan_epoch)/3600, 2), null())
| eval deploy_age_hours=if(isnotnull(last_deploy_epoch) AND last_deploy_epoch>0, round((now()-last_deploy_epoch)/3600, 2), null())
| eval scanner_db_freshness_hours=if(last_scan_db_epoch>100000, round((now()-last_scan_db_epoch)/3600, 2), null())
| eval prod_scan_sla_hours=24
| eval coverage_gap=case(in_prod_scope=0, "out_of_scope", isnull(last_scan_epoch) OR last_scan_epoch<=0, "never_scanned", scan_age_hours>prod_scan_sla_hours, "stale_scan_attestation", true(), "scan_current")
| eval digest_mismatch_hint=case(
    len(latest_deploy_digest)>12 AND len(row_key)>12 AND latest_deploy_digest!=row_key AND match(row_key, "^sha256:[a-f0-9]{8,}"), "digest_repointed_rescan_required",
    len(latest_deploy_digest)>12 AND len(row_key)>12 AND latest_deploy_digest!=row_key AND NOT match(row_key, "^sha256:"), "mutable_tag_digest_shift",
    true(), "digest_ok_or_unknown")
| eval crit_age_days=if(crit_first_epoch>100000, round((now()-crit_first_epoch)/86400, 2), 0)
| eval high_age_days=if(high_first_epoch>100000, round((now()-high_first_epoch)/86400, 2), 0)
| eval med_age_days=if(med_first_epoch>100000, round((now()-med_first_epoch)/86400, 2), 0)
| eval low_age_days=if(low_first_epoch>100000, round((now()-low_first_epoch)/86400, 2), 0)
| eval sla_breach_severity=case(
    open_critical>0 AND crit_age_days>7, "BREACH-CRITICAL",
    open_high>0 AND high_age_days>14, "BREACH-HIGH",
    open_medium>0 AND med_age_days>30, "BREACH-MEDIUM",
    open_low>0 AND low_age_days>90, "BREACH-LOW",
    match(coverage_gap, "never_scanned|stale_scan_attestation"), "COVERAGE-GAP",
    match(digest_mismatch_hint, "digest_repointed|mutable_tag"), "MUTABILITY-BYPASS-RISK",
    true(), "WITHIN-SLA")
| eval action_required=case(
    sla_breach_severity="BREACH-CRITICAL", "expedite_rebuild_rescan_and_vendor_exception_review",
    sla_breach_severity="BREACH-HIGH", "assign_owner_patch_within_14d_SLA",
    sla_breach_severity="COVERAGE-GAP", "invoke_scanner_on_recorded_digest",
    sla_breach_severity="MUTABILITY-BYPASS-RISK", "block_admission_until_fresh_attestation",
    true(), "monitor_and_trend")
| streamstats window=2 global=f count AS scan_trend_seq BY registry
| eventstats sum(eval(if(coverage_gap="scan_current", 1, 0))) AS fleet_scanned_current count AS fleet_total
| eval coverage_pct=if(fleet_total>0, round(100.0 * fleet_scanned_current / fleet_total, 2), null())
| sort - sla_breach_severity scan_age_hours
| table row_key team registry repo tag deploy_age_hours scan_age_hours scanner_db_freshness_hours open_critical open_high open_medium coverage_gap digest_mismatch_hint sla_breach_severity coverage_pct owner action_required
```

### Step 4 — Validate

Positive path A — stale scan: ingest a governance manifest with _time from seventy-two hours ago for a digest still marked in prod_image_scope.csv, run the search, and expect coverage_gap stale_scan_attestation with scan_age_hours greater than twenty-four when prod_scan_sla_hours remains at twenty-four.

Positive path B — never scanned: ingest kube:audit rows for a new digest without any scan_attest lane event, expect never_scanned or COVERAGE-GAP in sla_breach_severity depending on ordering, and confirm action_required invokes_scanner_on_recorded_digest.

Positive path C — SLA breach: send a manifest with open_critical greater than zero and oldest_critical_open_epoch older than eight days, expect BREACH-CRITICAL with crit_age_days above seven.

Positive path D — High SLA: set open_high above zero with high_first_seen_epoch beyond fifteen days, expect BREACH-HIGH reflecting the fourteen-day SLA used here rather than the thirty-day window used in UC-3.1.10 triage examples.

Positive path E — mutable tag drift: admission rows with latest_deploy_digest different from the attested row_key should raise MUTABILITY-BYPASS-RISK or digest_mismatch_hint containing mutable_tag language when tag-only keys remain in scope.

Negative path — clean digest: manifest within SLA hours, zero open findings, matching admission digest, expect WITHIN-SLA and scan_current coverage_gap.

Performance: use Job Inspector to confirm multisearch fan-in stays within search budget; if not, materialize nightly summaries per digest into a summary index and point this search at summaries for dashboards while keeping raw multisearch for investigations.

RBAC: readers without oti_containers must see zero rows. Clock skew: enforce chrony on forwarders before trusting epoch math.

Correlation: compare alert times to UC-3.1.10 for CVE detail drill-down when BREACH tiers fire, and to UC-3.1.26 when coverage gaps coincide with registry throttling that prevented scanner pulls.

Field sanity: rename one vendor field to camelCase in lab and confirm coalesce lists still populate row_key and open counts.

### Step 5 — Operationalize & Troubleshoot

Operationalize with a coverage scorecard panel showing coverage_pct and fleet_total, a table sorted by sla_breach_severity with drilldowns to raw governance manifests and kube:audit lines, a timechart of scanner:pipeline:heartbeat db_freshness lag from the companion alert, and annotations when scanner semver falls behind scanner_telemetry_baseline.csv in drift dashboards. Archive weekly CSV exports with lookup commit hashes to your evidence index for SOC 2 CC7.1 style vulnerability management discussions and ISO 27001 A.12.6 technical review packets.

Troubleshooting

Case 1 — Rows show never_scanned for busy production digests: kube:audit field extractions omit resolved_digest → expand props or add a mutating webhook that logs digest explicitly before relying on this UC.

Case 2 — scan_age_hours null while manifests exist: _time skew or stats max picking wrong lane → verify clock sync and confirm lane field equals scan_attest on manifests.

Case 3 — False MUTABILITY-BYPASS-RISK after promotions: row_key uses tag while admission emits digest only → normalize prod_image_scope.csv to digest-first keys and backfill attestation rows.

Case 4 — coverage_pct stuck at zero: all rows out_of_scope or never_scanned → confirm in_prod_scope flags and prod_scan_sla_hours macro before interpreting numerator.

Case 5 — eventstats fleet_total surprises executives: duplicate digest rows from multi-cluster feeds → dedupe with stats latest by row_key before eventstats in a wrapper macro.

Case 6 — streamstats scan_trend_seq resets each run: expected for stateless searches → move trend to summary index if continuity is required across schedule boundaries.

Case 7 — Join misses on prod_image_scope.csv: CSV uses uppercase digest → lowercase normalization in lookup subsearch already present; verify no UTF-8 BOM on first column.

Case 8 — Gatekeeper denials missing image_ref: constraint templates omit copy of attempted image → update template auditing to include image from review request.

Case 9 — Scanner DB freshness always null: db_fresh_epoch not extracted from manifests → add eval alias from vendor metadata field names in props.

Case 10 — Duplicate row_key collisions across registries: registry is already in stats BY clause; if collisions remain, append repo to row_key in a pre-stats eval macro.

Case 11 — BREACH rows without open counts: oldest epochs default zero cleared counts → confirm governance job sends non-zero open counts or derive ages from UC-3.1.10 summary index joins.

Case 12 — Heartbeat alert storms during rolling scanner upgrades: maintenance window metadata must annotate expected silence or analysts will conflate upgrade with outage.

Governance cadence: quarterly replay one historical advisory week through the SPL after scanner upgrades, and update the comment macro when indexes or sourcetype names change.

Closing differentiation note for steering committees: pairing this UC with admission controller decisions documents that images without fresh attestations never reached production, satisfying questions that raw CVE spreadsheets cannot answer when UC-3.1.10 alone is silent on coverage.

Supplemental engineering depth for long-term owners: document how air-gapped registries shift scanner_db_updated_epoch interpretation, how multi-arch manifests require one row per architecture in prod_image_scope.csv to avoid false never_scanned states, and how FinOps reviewers should compare scanner pipeline compute cost against mean-time-to-remediate regressions surfaced by BREACH tiers. When legal holds land, include governance manifests and admission JSON excerpts in the preservation scope. When migrating from Docker-only to mixed containerd paths, revisit field extractions without conflating this UC with UC-3.1.21 runtime signals. When red teams simulate supply-chain swaps, tag exercise windows in lookups so COVERAGE-GAP noise does not exhaust on-call capacity. When service meshes inject opaque image references, normalize sidecar images in prod_image_scope.csv with the same rigor as application images. When board members ask for a single metric, lead with coverage_pct trend rather than raw CVE counts. When auditors reference NIST SP 800-190, attach this saved search description plus lookup versions to the evidence bundle. When capacity planning for Splunk indexers, model admission growth separately from manifest volume because admission JSON is wider. When OT edge gateways reuse container tooling, duplicate owner routing with OT accountability fields. When finance challenges dual scanners, show avoided incident cost from stale attestation detection rather than license bytes alone. When platform teams adopt Sigstore, map attestation timestamps into the same last_scan_epoch logic via a small transforms alias. When GDPR concerns arise, hash developer identifiers in namespace labels before dashboards leave the SOC. When PCI scope narrows, filter prod_image_scope.csv to in-scope clusters only via a macro without forking the SPL. When ITIL change records are mandatory, embed change_ticket in lookup rows for automatic ticket deep links from the closing table. When Chaos Engineering injects registry latency, pair results with UC-3.1.26 to avoid misclassifying scanner backlog as governance drift.


Extended platform steering notes for coverage scorecards: namespace-level rollups can reuse the same SPL with stats BY team after the closing table, registry-level burn-down charts should plot scan_age_hours p95 versus admission volume, and executive slides should pair coverage_pct with absolute counts of never_scanned digests to avoid percentage smooth-over when denominators shrink during cluster decommission events. For COSO-style internal controls, map each BREACH tier to a compensating control narrative and owner attestation. For DORA ICT incident evidence, timestamp exports when COVERAGE-GAP coincides with regulatory reporting windows. For FedRAMP moderate baselines, cite this UC alongside CM configuration management evidence that images are scanned before promotion. For hybrid estates, duplicate macros per cloud landing zone so Azure ACR and Amazon ECR feeds do not collapse coverage into one misleading average. For academic research clusters, mark out_of_scope explicitly rather than deleting feeds so historical dashboards remain reproducible.

Clair and Anchore Enterprise operators should mirror field names into the same coalesce lists used for Trivy and Grype so manifest upgrades do not require SPL forks. Aqua CSPM JSON can land as trivy:governance:manifest aliases when Aqua wraps Trivy outputs underneath a single vendor envelope. SLSA provenance bundles ingested as separate sourcetypes should still cross-reference row_key through external_id fields you add in transforms.conf.

Workload identity for scanners must be rotation-safe: if scanner service accounts expire, heartbeat gaps resemble outages; encode identity_expiry_epoch alongside db_last_success_epoch for quicker RCA.

Admission review API latency can delay kube:audit arrival; widen earliest only for investigations, not for hourly alerts, unless storage backlog is proven.

Align paging verbs with ITSM categories: COVERAGE-GAP routes to platform reliability engineering, BREACH tiers route to appsec and owning squad, MUTABILITY-BYPASS-RISK routes to supply-chain and registry administration jointly.

Cosign signature verification timestamps from policy controllers can be copied into a sidecar field cosign_attested_epoch; when present, treat max(cosign_attested_epoch, last_scan_epoch) as the effective attestation time in a forked macro if legal demands cryptographic proof beyond scanner JSON.

Policy-as-code repositories that version OPA bundles should emit a lightweight bundle_git_sha event into the same index so analysts can correlate Gatekeeper denials with the exact policy revision without opening Git.

For Windows node pools mixed into Linux-majority clusters, ensure admission logs still carry image references in the same JSON paths assumed here or extend coalesce lists rather than excluding those nodes silently.

When using managed Kubernetes audit sinks to S3 then forward to Splunk, account for sink lag in last_deploy_epoch interpretation during incident reviews.

FinOps dashboards can divide scanner CPU seconds by digest count to show cost per covered image, helping justify parallel scanner shards when coverage_pct plateaus due to queue depth rather than policy gaps.


## SPL

```spl
`comment("UC-3.1.5 Image Vulnerability Scanning Coverage and Patch SLA. Tunables: index=oti_containers; prod_scan_max_age_hours=24; scanner_db_stale_warn_hours=72; remediation_SLA_days Critical=7 High=14 Medium=30 Low=90; lookups prod_image_scope.csv scanner_telemetry_baseline.csv; earliest=-30d@d latest=now")`
| multisearch
    [ search index=oti_containers (sourcetype="trivy:governance:manifest" OR sourcetype="grype:governance:manifest" OR sourcetype="snyk:container:governance")
      earliest=-30d@d latest=now
      | eval lane="scan_attest"
      | eval row_key=lower(trim(toString(coalesce(image_digest, digest, RepoDigest, repo_digest, ""))))
      | eval row_key=if(len(row_key)>12, row_key, lower(trim(toString(coalesce(image_ref, ArtifactName, Target, image_name, image, "")))))
      | eval registry=lower(trim(toString(coalesce(registry, registry_host, registry_fqdn, ""))))
      | eval repo=trim(toString(coalesce(repository, repo, image_repo, "")))
      | eval tag=trim(toString(coalesce(tag, image_tag, mutable_tag, "")))
      | eval scanner=case(sourcetype="trivy:governance:manifest", "trivy", sourcetype="grype:governance:manifest", "grype", true(), "snyk")
      | eval db_fresh_epoch=tonumber(tostring(coalesce(scanner_db_updated_epoch, vulndb_last_sync_epoch, grype_db_epoch, "0")), 10)
      | eval has_open_critical=tonumber(tostring(coalesce(open_critical_count, crit_open, "0")), 10)
      | eval has_open_high=tonumber(tostring(coalesce(open_high_count, high_open, "0")), 10)
      | eval has_open_medium=tonumber(tostring(coalesce(open_medium_count, med_open, "0")), 10)
      | eval has_open_low=tonumber(tostring(coalesce(open_low_count, low_open, "0")), 10)
      | eval oldest_crit_open_epoch=tonumber(tostring(coalesce(oldest_critical_open_epoch, critical_first_seen_epoch, "0")), 10)
      | eval oldest_high_open_epoch=tonumber(tostring(coalesce(oldest_high_open_epoch, high_first_seen_epoch, "0")), 10)
      | eval oldest_med_open_epoch=tonumber(tostring(coalesce(oldest_medium_open_epoch, med_first_seen_epoch, "0")), 10)
      | eval oldest_low_open_epoch=tonumber(tostring(coalesce(oldest_low_open_epoch, low_first_seen_epoch, "0")), 10)
      | eval namespace=trim(toString(coalesce(k8s_namespace, namespace, team_namespace, "")))
      | eval deploy_digest_cand=""
      | fields _time lane row_key registry repo tag scanner db_fresh_epoch has_open_critical has_open_high has_open_medium has_open_low oldest_crit_open_epoch oldest_high_open_epoch oldest_med_open_epoch oldest_low_open_epoch namespace deploy_digest_cand ]
    [ search index=oti_containers (sourcetype="kube:audit" OR sourcetype="k8s:admission:gatekeeper" OR sourcetype="registry:webhook:admission")
      earliest=-30d@d latest=now
      | eval lane="deploy_admission"
      | eval image_ref=trim(toString(coalesce(requestObject_spec_containers_0_image, object_spec_image, image, container_image, denied_image, "")))
      | eval row_key=lower(trim(toString(coalesce(image_digest, resolved_digest, ""))))
      | eval row_key=if(len(row_key)>12, row_key, lower(trim(image_ref)))
      | eval deploy_digest_cand=lower(trim(toString(coalesce(image_digest, resolved_digest, ""))))
      | eval registry=lower(trim(toString(coalesce(registry, ""))))
      | eval repo=trim(toString(coalesce(repository, repo, "")))
      | eval tag=trim(toString(coalesce(tag, "")))
      | eval namespace=trim(toString(coalesce(objectRef_namespace, namespace, "")))
      | eval scanner=""
      | eval db_fresh_epoch=0
      | eval has_open_critical=0 | eval has_open_high=0 | eval has_open_medium=0 | eval has_open_low=0
      | eval oldest_crit_open_epoch=0 | eval oldest_high_open_epoch=0 | eval oldest_med_open_epoch=0 | eval oldest_low_open_epoch=0
      | where len(row_key)>5
      | fields _time lane row_key registry repo tag scanner db_fresh_epoch has_open_critical has_open_high has_open_medium has_open_low oldest_crit_open_epoch oldest_high_open_epoch oldest_med_open_epoch oldest_low_open_epoch namespace deploy_digest_cand ]
| stats
    max(eval(if(lane="scan_attest", _time, null()))) AS last_scan_epoch
    max(eval(if(lane="deploy_admission", _time, null()))) AS last_deploy_epoch
    max(eval(if(lane="deploy_admission" AND len(deploy_digest_cand)>12, deploy_digest_cand, null()))) AS latest_deploy_digest
    max(eval(if(lane="scan_attest", db_fresh_epoch, null()))) AS last_scan_db_epoch
    values(scanner) AS scanners_seen
    max(has_open_critical) AS open_critical
    max(has_open_high) AS open_high
    max(has_open_medium) AS open_medium
    max(has_open_low) AS open_low
    max(oldest_crit_open_epoch) AS crit_first_epoch
    max(oldest_high_open_epoch) AS high_first_epoch
    max(oldest_med_open_epoch) AS med_first_epoch
    max(oldest_low_open_epoch) AS low_first_epoch
    values(lane) AS lanes_present
    latest(namespace) AS namespace
  BY row_key registry repo tag
| eval team=coalesce(namespace, "unassigned")
| join type=left max=0 row_key
    [| inputlookup prod_image_scope.csv
     | eval row_key=lower(trim(toString(coalesce(row_key, image_digest, image_ref_key, ""))))
     | eval in_prod_scope=tonumber(tostring(coalesce(in_production_scope, prod, "1")), 10)
     | eval owner=trim(toString(coalesce(owner_team, accountable_owner, platform_owner, "")))
     | fields row_key in_prod_scope owner ]
| fillnull value=1 in_prod_scope
| fillnull value="" owner
| eval scan_age_hours=if(isnotnull(last_scan_epoch) AND last_scan_epoch>0, round((now()-last_scan_epoch)/3600, 2), null())
| eval deploy_age_hours=if(isnotnull(last_deploy_epoch) AND last_deploy_epoch>0, round((now()-last_deploy_epoch)/3600, 2), null())
| eval scanner_db_freshness_hours=if(last_scan_db_epoch>100000, round((now()-last_scan_db_epoch)/3600, 2), null())
| eval prod_scan_sla_hours=24
| eval coverage_gap=case(in_prod_scope=0, "out_of_scope", isnull(last_scan_epoch) OR last_scan_epoch<=0, "never_scanned", scan_age_hours>prod_scan_sla_hours, "stale_scan_attestation", true(), "scan_current")
| eval digest_mismatch_hint=case(
    len(latest_deploy_digest)>12 AND len(row_key)>12 AND latest_deploy_digest!=row_key AND match(row_key, "^sha256:[a-f0-9]{8,}"), "digest_repointed_rescan_required",
    len(latest_deploy_digest)>12 AND len(row_key)>12 AND latest_deploy_digest!=row_key AND NOT match(row_key, "^sha256:"), "mutable_tag_digest_shift",
    true(), "digest_ok_or_unknown")
| eval crit_age_days=if(crit_first_epoch>100000, round((now()-crit_first_epoch)/86400, 2), 0)
| eval high_age_days=if(high_first_epoch>100000, round((now()-high_first_epoch)/86400, 2), 0)
| eval med_age_days=if(med_first_epoch>100000, round((now()-med_first_epoch)/86400, 2), 0)
| eval low_age_days=if(low_first_epoch>100000, round((now()-low_first_epoch)/86400, 2), 0)
| eval sla_breach_severity=case(
    open_critical>0 AND crit_age_days>7, "BREACH-CRITICAL",
    open_high>0 AND high_age_days>14, "BREACH-HIGH",
    open_medium>0 AND med_age_days>30, "BREACH-MEDIUM",
    open_low>0 AND low_age_days>90, "BREACH-LOW",
    match(coverage_gap, "never_scanned|stale_scan_attestation"), "COVERAGE-GAP",
    match(digest_mismatch_hint, "digest_repointed|mutable_tag"), "MUTABILITY-BYPASS-RISK",
    true(), "WITHIN-SLA")
| eval action_required=case(
    sla_breach_severity="BREACH-CRITICAL", "expedite_rebuild_rescan_and_vendor_exception_review",
    sla_breach_severity="BREACH-HIGH", "assign_owner_patch_within_14d_SLA",
    sla_breach_severity="COVERAGE-GAP", "invoke_scanner_on_recorded_digest",
    sla_breach_severity="MUTABILITY-BYPASS-RISK", "block_admission_until_fresh_attestation",
    true(), "monitor_and_trend")
| streamstats window=2 global=f count AS scan_trend_seq BY registry
| eventstats sum(eval(if(coverage_gap="scan_current", 1, 0))) AS fleet_scanned_current count AS fleet_total
| eval coverage_pct=if(fleet_total>0, round(100.0 * fleet_scanned_current / fleet_total, 2), null())
| sort - sla_breach_severity scan_age_hours
| table row_key team registry repo tag deploy_age_hours scan_age_hours scanner_db_freshness_hours open_critical open_high open_medium coverage_gap digest_mismatch_hint sla_breach_severity coverage_pct owner action_required
```

## CIM SPL

```spl
| tstats summariesonly=true latest(_time) AS last_seen FROM datamodel=Vulnerabilities WHERE nodename=Vulnerabilities earliest=-7d latest=now BY Vulnerabilities.dest Vulnerabilities.signature
| rename Vulnerabilities.dest AS image_key
```

## Visualization

Coverage scorecard single value for coverage_pct with fleet_total context, severity-sorted table of row_key owner and sla_breach_severity, timechart of scanner_db_freshness_hours by registry, mutability drift panel for digest_mismatch_hint, and admission denial rate overlay from k8s:admission:gatekeeper.

## Known False Positives

Security-approved scan-skip annotations on vendor appliance images or emergency break-glass digests can present as never_scanned until prod_image_scope.csv marks them exempt_with_ticket and a companion macro filters exempt rows from paging queues. Planned scanner maintenance windows legitimately pause heartbeat emissions for short intervals; require sustained silence exceeding two missed heartbeats before declaring pipeline failure, and annotate maintenance tickets in dashboard overlays. Multi-architecture manifests may emit one digest per architecture while admission logs show a manifest list digest; normalize with architecture-specific scope rows or aggregate keys to avoid false MUTABILITY-BYPASS-RISK. Golden base images that intentionally freeze on a digest with a dated attestation can look stale on calendar clocks even when risk is accepted; tie those rows to exception_expires_epoch in lookups instead of muting the sourcetype. Scanner-side rate limiting against huge registries can delay manifests without implying compromise; correlate with UC-3.1.26 pull telemetry before escalating. Air-gapped mirrors sometimes refresh internal vulnerability databases on a slower cadence than public feeds; adjust scanner_db_stale_warn_hours per zone documented in scanner_telemetry_baseline.csv. CI rescans that replay identical digest results can reset oldest-open epochs in ways that temporarily hide SLA breaches; cross-check against UC-3.1.10 historical summaries before closing tickets. Kubernetes audit sampling, if enabled, can drop admission evidence for some mutations; never treat sampled absence alone as proof of safety. Duplicate HEC writers can inflate coverage_pct denominators until deduplication macros land; dedupe on row_key and _time in a summary index when needed.

## References

- [Trivy documentation](https://aquasecurity.github.io/trivy/)
- [Snyk Docs — Snyk Container](https://docs.snyk.io/scan-with-snyk/snyk-container/snyk-container-overview)
- [Sigstore Cosign — Overview](https://docs.sigstore.dev/cosign/overview/)
- [Kubernetes Documentation — Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
- [Splunk Docs — Splunk CIM Vulnerabilities](https://docs.splunk.com/Documentation/CIM/latest/User/Vulnerabilities)
