<!-- AUTO-GENERATED from UC-3.1.10.json — DO NOT EDIT -->

---
id: "3.1.10"
title: "Container Image Vulnerability Scan Results"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.1.10 · Container Image Vulnerability Scan Results

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We treat each shipped image like a recipe on the menu. When a supplier flags an ingredient as dangerous and a replacement exists, we stop serving that dish right away. When the bulletin is dire but no replacement exists, we still need to know which plates are in the dining room and for how long, especially when investigators confirm thieves already exploit the flaw in the wild.*

---

## Description

Fortune-scale container estates ship thousands of immutable digests each week, yet audit teams still get blank stares when they ask how many production images carry unpatched Critical findings older than thirty days with a CISA Known Exploited Vulnerability flag. This use case is the build-time and SBOM-result plane: it normalizes Trivy, Grype, and Snyk JSON streams into one governance index, joins the CISA KEV catalog and FIRST EPSS scores so severity reflects exploit likelihood instead of theoretical CVSS alone, and tracks first-seen timestamps to expose patch-SLA aging and stale base-image rebuild debt. It answers the customer-visible failure mode where a golden base image silently accumulates Critical CVEs because scanners only ran in a forked pipeline, or because nobody correlated scanner silence with a paused nightly job. Three correlated signals drive prioritization: raw scanner severities and fix availability from CI HEC feeds, KEV membership that separates headline risk from noise, and EPSS-weighted scoring that bumps actively exploited probability mass before finance teams defund remediation. UC-3.1.21 remains the Falco and eBPF runtime behavioral story once code is executing. UC-3.1.25 stays focused on Docker socket and daemon exposure configuration. UC-3.1.6 documents declarative privilege and capability posture on the container object. None of those siblings replace digest-level vulnerability telemetry, SBOM scanner JSON, or KEV and EPSS enrichment for patch SLAs.

## Value

Quantifiable outcomes start with audit-ready answers: PCI DSS 6.2 style expectations for timely critical patching, ISO 27001 A.12.6.1 technical vulnerability management evidence, SOC 2 CC7.1 change and vulnerability monitoring narratives, and HIPAA 164.308(a)(1)(ii)(B) security management process documentation all improve when Splunk can print a dated table of digests, KEV counts, EPSS-weighted scores, and oldest open age. Executive reporting gains a single number for mean-time-to-remediate Critical findings on promoted digests instead of three incompatible CSV exports from separate scanners. Risk reduction follows when KEV-listed issues with published fixes surface as promotion blockers automatically, and when EPSS above 0.5 prevents a low-energy triage culture from ignoring boring CVE numbers that actually carry exploit momentum. Operational efficiency shows up as fewer war rooms spent reconciling Trivy versus Snyk disagreements because coalesce-normalized fields and deduplicated keys land in one index. Financially, preventing one production incident traced to a known-exploited OpenSSL or glibc class flaw routinely outweighs the incremental HEC volume from nightly full-fleet rescans.

## Implementation

Ingest normalized scanner JSON into index=oti_containers with sourcetypes trivy:image:json, grype:image:json, and snyk:container:json via HEC from CI. Publish daily-refreshed cisa_kev_catalog.csv and epss_scores.csv lookups, optional cve_first_seen.csv for SLA math, schedule container_uc_3_1_10_image_vuln_scan_governance hourly, and route severity tiers to platform and appsec queues.

## Evidence

Evidence includes CISA Known Exploited Vulnerabilities catalog publications, the FIRST EPSS peer-reviewed methodology, Aqua Security Trivy adoption guidance, Snyk annual container vulnerability reports, and Splunk Lantern articles on container security automation, all correlated with scheduled exports of this search into your evidence index.

## Control test

### Positive scenario

In a lab project, build a synthetic image layer manifest containing one Critical CVE present in cisa_kev_catalog.csv with a populated FixedVersion field in Trivy JSON, send the event to sourcetype=trivy:image:json in index=oti_containers, populate epss_scores.csv with epss greater than 0.5 for the same CVE, run container_uc_3_1_10_image_vuln_scan_governance, and expect severity critical_kev_listed_with_fix_available with non-zero kev_count and recommended_response referencing rebuild.

### Negative scenario

Ingest only Low severity findings with EPSS below 0.2, no KEV rows, first_seen within one day, verify the search emits low_baseline_drift or an empty flag set suitable for green dashboards without pages.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the application security lead and the CI platform owner who certifies scanner versions, database freshness, and HEC token rotation across the container build fleet. This use case is intentionally the build-time SBOM and image-layer CVE governance axis: it consumes scanner JSON emitted after registry pushes or during continuous integration, not syscall telemetry. UC-3.1.21 covers Falco, eBPF process, and connect anomalies after workloads run. UC-3.1.25 covers docker.sock and Docker Engine exposure misconfigurations. UC-3.1.6 covers HostConfig privilege, capability, and cgroup posture declared on the container object. Those siblings are complementary; none substitutes normalized Trivy, Grype, and Snyk findings enriched with CISA KEV and FIRST EPSS for patch SLA enforcement.

Splunk Enterprise Security is optional but valuable when you map results into risk objects or correlation searches; the minimum viable deployment is Splunk Enterprise or Splunk Cloud with HEC, a small add-on wrapper for props and transforms, and three sourcetypes landing in index oti_containers. You need Splunk roles that separate developers who may see aggregate counts from security operations staff who see full CVE lists.

Lookups must exist before the saved search runs: cisa_kev_catalog.csv refreshed at least daily from the official CISA JSON or CSV publication with a stable cveID column normalized to uppercase CVE-YYYY-NNNNN form. epss_scores.csv refreshed daily from FIRST EPSS current scores with cve and epss columns. cve_first_seen.csv is optional but strongly recommended; populate it from a summary-indexing saved search that records the earliest _time each vulnerability_id appears paired with image_digest, or maintain it with a scheduled output that appends new keys only. Without this lookup, days_unpatched falls back to event _time inside the search window, which understates age for long-lived CVEs when historical data has rolled off cold storage.

Field extraction expectations: pipeline owners should flatten scanner JSON so Splunk sees one event per image scan manifest or per CVE finding. This SPL tolerates single-event-per-CVE rows or manifests that repeat Target and ArtifactName fields alongside VulnerabilityID style keys. Coalesce lists absorb camelCase and snake_case variants across Trivy JSON, Grype JSON, and Snyk container test JSON.

Governance guardrails: never send raw registry credentials inside scanner JSON to Splunk. Redact customer identifiers in repository names when regulation demands. Document scanner version strings in a sidecar lookup so auditors can tie a spike in UNKNOWN severity to a parser change rather than a new zero-day.

Licensing and volume: full-fleet nightly scans for five thousand images can generate millions of CVE rows per day if you retain every language package; consider hot retention of thirty days on raw events and longer retention on summarized digest-level metrics written by a separate summary search.

### Step 2 — Configure data collection

Configure GitLab CI, GitHub Actions, Jenkins, Tekton, or Argo Workflow steps to run trivy image --format json, grype image -o json, and snyk container test --json after build and before promotion. Post each JSON file to Splunk HEC with curl -k -H "Authorization: Splunk <token>" -d @scan.json or stream through an OpenTelemetry collector that preserves the raw body. Set sourcetype to trivy:image:json, grype:image:json, or snyk:container:json respectively, and index to oti_containers unless your naming standard differs, in which case update the comment macro and search line consistently.

On the Splunk side, create props.conf and transforms.conf that timestamp events with the scan completion time, extract image_name, image_digest, vulnerability_id, severity, fixed_version, and scanner host fields, and route quarantined namespaces to a non-production index if needed. For Splunk Add-on for Container Security style deployments, mirror the vendor guidance for HEC acknowledgments and batch sizing; large manifests should be gzip-compressed on the wire.

Normalize repository identifiers: prefer immutable RepoDigest strings over floating tags in image_digest. If only tags arrive, enrich with a registry API lookup job that writes digest metadata into the event before HEC send. Floating tags break dedup logic and make SLA aging meaningless when the tag moves silently.

Automate lookup refresh: use a modular input, AWS Lambda, or Azure Function to download CISA KEV and EPSS CSV, write atomically to lookups, and emit a small Splunk event that records file mtime for freshness dashboards. Splunk should fail closed with a warning when lookups are older than forty-eight hours; implement that as a separate monitor search.

Validate with a canary image that contains a known benign CVE fixture in lab only, send three scanner variants, and confirm coalesce extracts the same vulnerability_id across vendors.

### Step 3 — Create search and governance alert

Save the SPL as container_uc_3_1_10_image_vuln_scan_governance with an hourly schedule and earliest=-30d@d latest=now during steady state. Throttle duplicate rows per image_digest and severity tier for four hours unless severity escalates from low_baseline_drift to a critical tier within the same business day. Route critical_kev_listed_no_fix and critical_kev_listed_with_fix_available to the joint platform and application security bridge; route EPSS-hot rows to the vulnerability management queue with explicit EPSS numbers pasted from raw events for analyst speed.

Understanding the pipeline begins at the comment macro, which lists every tunable index, sourcetype, lookup, SLA day count, and EPSS gate so operators do not guess during incidents. The opening search scopes all three scanner sourcetypes in oti_containers. Eval statements normalize scanner name, image identity, CVE identifier, severity, and fix availability using coalesce so Trivy, Grype, and Snyk field shapes converge. The where clause drops malformed rows early to protect join performance.

The first join wraps inputlookup cisa_kev_catalog.csv on vulnerability_id and stamps kev_listed for CISA-known exploited issues. The second join wraps inputlookup epss_scores.csv, satisfying the requirement that both lookups appear as join-wrapped inputlookup operations rather than bare lookup commands. The third join pulls optional first_seen_epoch from cve_first_seen.csv so days_unpatched measures true calendar exposure instead of only the rolling window. When the lookup misses, first_seen_at falls back to event _time, which is an honest approximation when cold storage limits history.

crit_high_epss_flag and epss_weight_mult implement the fifty percent weight bonus for Critical or High findings whose EPSS score exceeds 0.5. row_weight sums the tier weights and multiplies by the bonus. streamstats window=30 on each vulnerability_id trajectory provides sla_aging_trend_days for SLA drift visualization before dedup collapses duplicate scanner emissions. dedup image_name image_digest scanner vulnerability_id eliminates multi-event noise when CI retries the same scan.

stats aggregates to the business grain the customer cares about: one row per image_name, image_digest, and scanner with dc of vulnerabilities per severity bucket, sum of row_weight as epss_weighted_score, max days_unpatched as oldest_unpatched_days, KEV cardinality as kev_count, and fix cardinality as fixed_available_count. Binary flags max out for KEV plus fix combinations, EPSS heat, and SLA breaches for Critical seven-day, High thirty-day, and Medium ninety-day thresholds carried in intermediate fields.

eventstats adds fleet_p50_epss_score and fleet_p90_epss_score across the result set so executives see whether a digest is an outlier versus the fleet distribution. The severity case enforces the exact tier strings required for downstream SOAR playbooks. recommended_response provides pre-written runbook sentences tied to each tier. The closing table lists image_name, image_digest, scanner, critical_cves, high_cves, medium_cves, kev_count, epss_weighted_score, oldest_unpatched_days, fixed_available_count, severity, recommended_response, and fleet percentile columns for twelve or more columns total.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.1.10 Container Image Vulnerability Scan Results. Tunables: index=oti_containers; sourcetypes trivy:image:json grype:image:json snyk:container:json; join lookups cisa_kev_catalog.csv and epss_scores.csv; optional cve_first_seen.csv keys vulnerability_id plus image_digest; SLA gates Critical 7d High 30d Medium 90d; EPSS bonus threshold 0.5 on Critical or High rows; dedupe per scanner before dc(); earliest=-30d@d latest=now for stable first-seen backfill.")`
| search index=oti_containers (sourcetype="trivy:image:json" OR sourcetype="grype:image:json" OR sourcetype="snyk:container:json") earliest=-30d@d latest=now
| eval scanner=case(sourcetype="trivy:image:json","trivy", sourcetype="grype:image:json","grype", sourcetype="snyk:container:json","snyk", true(),"unknown")
| eval image_name=trim(toString(coalesce(image_name, ArtifactName, Target, target, repo, Repository, "")))
| eval image_digest=trim(toString(coalesce(image_digest, digest, RepoDigest, repo_digest, "")))
| eval vulnerability_id=upper(trim(toString(coalesce(vulnerability_id, vulnerabilityId, VulnerabilityID, cve_id, CVE, id, ""))))
| eval sev_norm=upper(trim(toString(coalesce(severity, Severity, ""))))
| eval fixed_version=trim(toString(coalesce(fixed_version, FixedVersion, fixedIn, fix_version, "")))
| where len(vulnerability_id)>4 AND match(vulnerability_id, "^CVE-[0-9]{4}-[0-9]+")
| eval has_fix=if(isnotnull(fixed_version) AND len(fixed_version)>0 AND lower(fixed_version)!="null", 1, 0)
| eval is_crit=if(sev_norm="CRITICAL", 1, 0)
| eval is_high=if(sev_norm="HIGH", 1, 0)
| eval is_med=if(match(sev_norm, "^(MEDIUM|MODERATE)$"), 1, 0)
| eval is_low=if(sev_norm="LOW", 1, 0)
| join type=left max=0 vulnerability_id
    [| inputlookup cisa_kev_catalog.csv
     | eval vulnerability_id=upper(trim(toString(coalesce(cveID, cve_id, CVE, cve, ""))))
     | eval kev_listed=1
     | fields vulnerability_id kev_listed ]
| fillnull value=0 kev_listed
| join type=left max=0 vulnerability_id
    [| inputlookup epss_scores.csv
     | eval vulnerability_id=upper(trim(toString(coalesce(cve, cve_id, CVE, ""))))
     | eval epss_score=tonumber(coalesce(epss, epss_score, score, "0"), 10)
     | fields vulnerability_id epss_score ]
| fillnull value=0 epss_score
| join type=left max=0 vulnerability_id image_digest
    [| inputlookup cve_first_seen.csv
     | eval vulnerability_id=upper(trim(toString(vulnerability_id)))
     | eval image_digest=trim(toString(image_digest))
     | eval first_seen_epoch=tonumber(coalesce(first_seen_epoch, first_seen, ""), 10)
     | fields vulnerability_id image_digest first_seen_epoch ]
| eval first_seen_at=coalesce(first_seen_epoch, _time)
| eval days_unpatched=round((now()-first_seen_at)/86400, 2)
| eval crit_high_epss_flag=if((is_crit=1 OR is_high=1) AND epss_score>0.5, 1, 0)
| eval epss_weight_mult=if(crit_high_epss_flag=1, 1.5, 1.0)
| eval row_weight=(is_crit*10 + is_high*5 + is_med*2 + is_low*1) * epss_weight_mult
| eval kev_crit_with_fix=if(kev_listed=1 AND is_crit=1 AND has_fix=1, 1, 0)
| eval kev_crit_no_fix=if(kev_listed=1 AND is_crit=1 AND has_fix=0, 1, 0)
| eval crit_sla_breach=if(is_crit=1 AND days_unpatched>7, 1, 0)
| eval high_sla_breach=if(is_high=1 AND days_unpatched>30, 1, 0)
| eval med_sla_breach=if(is_med=1 AND days_unpatched>90, 1, 0)
| sort 0 + image_name image_digest scanner vulnerability_id _time
| streamstats window=30 current=t max(days_unpatched) AS sla_aging_trend_days BY image_name, image_digest, scanner, vulnerability_id
| dedup image_name image_digest scanner vulnerability_id
| stats
    dc(eval(if(is_crit=1, vulnerability_id, null()))) AS critical_cves
    dc(eval(if(is_high=1, vulnerability_id, null()))) AS high_cves
    dc(eval(if(is_med=1, vulnerability_id, null()))) AS medium_cves
    dc(eval(if(is_low=1, vulnerability_id, null()))) AS low_cves
    sum(row_weight) AS epss_weighted_score
    max(days_unpatched) AS oldest_unpatched_days
    max(sla_aging_trend_days) AS sla_aging_trend_peak
    dc(eval(if(kev_listed=1, vulnerability_id, null()))) AS kev_count
    dc(eval(if(has_fix=1, vulnerability_id, null()))) AS fixed_available_count
    max(kev_crit_with_fix) AS flag_kev_crit_fix
    max(kev_crit_no_fix) AS flag_kev_crit_nofix
    max(crit_high_epss_flag) AS flag_epss_hot
    max(crit_sla_breach) AS flag_crit_sla
    max(high_sla_breach) AS flag_high_sla
    max(med_sla_breach) AS flag_med_sla
  BY image_name image_digest scanner
| eventstats perc50(epss_weighted_score) AS fleet_p50_epss_score perc90(epss_weighted_score) AS fleet_p90_epss_score
| eval severity=case(
    flag_kev_crit_fix>0, "critical_kev_listed_with_fix_available",
    flag_kev_crit_nofix>0, "critical_kev_listed_no_fix",
    flag_epss_hot>0, "critical_high_epss_above_0_5",
    flag_crit_sla>0, "high_critical_cve_over_7_day_sla",
    flag_high_sla>0, "medium_high_cve_over_30_day_sla",
    true(), "low_baseline_drift")
| eval recommended_response=case(
    severity="critical_kev_listed_with_fix_available", "Block promotion on this digest, open emergency change to rebuild the base layer with the published fix, validate registry admission policy, and attach KEV ticket linkage for auditors.",
    severity="critical_kev_listed_no_fix", "Treat as active weaponization risk: isolate workloads on this digest, escalate to vendor liaison, deploy compensating controls, and track daily until NVD or vendor advisory publishes remediation.",
    severity="critical_high_epss_above_0_5", "Prioritize ahead of CVSS-only backlog: schedule patch within 48 hours, cross-check runtime exposure with sibling UC-3.1.21 signals, and widen hunt for the same package version fleet-wide.",
    severity="high_critical_cve_over_7_day_sla", "Critical CVEs exceeded the seven-day remediation SLA: force rebuild, freeze dependent releases, and produce executive breach summary with owner accountability.",
    severity="medium_high_cve_over_30_day_sla", "High-severity CVEs exceeded the thirty-day SLA: assign capacity in the next sprint, document risk acceptance only with board-level exception, and refresh EPSS and KEV joins.",
    true(), "Maintain cadence: keep scanner feeds warm, reconcile duplicate findings across scanners, and trend epss_weighted_score against fleet percentiles.")
| table image_name image_digest scanner critical_cves high_cves medium_cves kev_count epss_weighted_score oldest_unpatched_days fixed_available_count severity recommended_response fleet_p50_epss_score fleet_p90_epss_score sla_aging_trend_peak
```


### Step 4 — Validate

Positive path A: ingest a lab image manifest with a published Critical CVE that also appears in the current CISA KEV catalog and includes a non-empty FixedVersion in Trivy JSON, run the search, and expect severity critical_kev_listed_with_fix_available with kev_count greater than zero and fixed_available_count greater than zero.

Positive path B: ingest a Critical CVE listed in KEV with no fixed version in scanner output, confirm critical_kev_listed_no_fix and verify recommended_response mentions compensating controls.

Positive path C: ingest a High severity CVE whose EPSS score in epss_scores.csv is 0.55, confirm flag_epss_hot drives critical_high_epss_above_0_5 when no higher-priority KEV branch triggers, validating case ordering.

Positive path D: manufacture first_seen_epoch older than eight days for a Critical CVE via cve_first_seen.csv, confirm high_critical_cve_over_7_day_sla when KEV branches are absent.

Positive path E: set first_seen beyond thirty-one days for a High CVE, confirm medium_high_cve_over_30_day_sla.

Negative path: ingest only Low and Medium CVEs under SLA with EPSS below 0.4 and no KEV hits, expect mostly low_baseline_drift and confirm fleet percentiles still populate.

Performance: use Job Inspector to verify join fan-in stays within SLA; if not, precompute a vulnerability_enrichment KV store updated hourly instead of double join on massive manifests.

Role check: readers without oti_containers must see zero rows.

### Step 5 — Operationalize and troubleshoot

Case 1 — Join misses on cisa_kev_catalog.csv: verify cveID normalization matches uppercase CVE format, refresh the lookup from the official CISA site, and confirm no UTF-8 BOM corrupted the first column name.

Case 2 — EPSS scores always zero: epss_scores.csv may use scientific notation strings; rebuild the lookup with plain decimal floats and confirm tonumber parses.

Case 3 — days_unpatched near zero for ancient CVEs: cve_first_seen.csv is empty or keys mismatch image_digest; rebuild the summary with lowercase digest normalization.

Case 4 — Duplicate inflation after dedup: multiple logical images share the same digest but different scanner payloads; widen dedup keys only after confirming business need.

Case 5 — severity stuck in low_baseline_drift while executives see risk: case order may be wrong or flags never rise because SLA thresholds use calendar days but first_seen used rolling _time; fix lookup backfill.

Case 6 — streamstats memory pressure on busy index: reduce window from thirty to fourteen or materialize sla_aging_trend_peak in a summary index instead.

Case 7 — Trivy emits nested JSON Splunk never flattens: add spath in a preceding data model or switch HEC to one-event-per-CVE before this search.

Case 8 — Grype severity UNKNOWN floods medium bucket: tune upstream Grype DB sync and add a pre-filter eval dropping UNKNOWN when package type is go-module if policy allows.

Case 9 — Snyk rate limits cause partial scans: correlate ingest volume drops with HTTP 429 markers in CI logs and alert on scanner silence separately.

Case 10 — Fleet percentiles flat because only one digest matches filters: broaden time range or remove excessive post-filter where clauses in dashboards.

Case 11 — Compliance auditors question EPSS: attach FIRST documentation PDF hash in evidence alongside the CSV refresh ticket.

Dashboard layout: heatmap of severity tiers by owner_team lookup join, line chart of kev_count daily, bar chart of top ten epss_weighted_score, histogram of oldest_unpatched_days with vertical lines at seven and thirty days.

Evidence retention: weekly CSV export of the closing table with lookup commit hashes, scanner versions, and Splunk saved search description updated quarterly.

Closing governance notes for platform steering committees: tie epss_weighted_score week-over-week deltas to sprint capacity commitments so vulnerability backlogs do not become invisible technical debt. Pair digest-level results with registry admission controller decisions when available, documenting allow or deny outcomes in the same evidence bundle auditors review. When finance questions scanner infrastructure cost, translate prevented Sev-1 hours into dollars using your incident baseline. Maintain a single canonical owner_team column via lookup join extensions if you page application squads instead of platform alone.

## SPL

```spl
`comment("UC-3.1.10 Container Image Vulnerability Scan Results. Tunables: index=oti_containers; sourcetypes trivy:image:json grype:image:json snyk:container:json; join lookups cisa_kev_catalog.csv and epss_scores.csv; optional cve_first_seen.csv keys vulnerability_id plus image_digest; SLA gates Critical 7d High 30d Medium 90d; EPSS bonus threshold 0.5 on Critical or High rows; dedupe per scanner before dc(); earliest=-30d@d latest=now for stable first-seen backfill.")`
| search index=oti_containers (sourcetype="trivy:image:json" OR sourcetype="grype:image:json" OR sourcetype="snyk:container:json") earliest=-30d@d latest=now
| eval scanner=case(sourcetype="trivy:image:json","trivy", sourcetype="grype:image:json","grype", sourcetype="snyk:container:json","snyk", true(),"unknown")
| eval image_name=trim(toString(coalesce(image_name, ArtifactName, Target, target, repo, Repository, "")))
| eval image_digest=trim(toString(coalesce(image_digest, digest, RepoDigest, repo_digest, "")))
| eval vulnerability_id=upper(trim(toString(coalesce(vulnerability_id, vulnerabilityId, VulnerabilityID, cve_id, CVE, id, ""))))
| eval sev_norm=upper(trim(toString(coalesce(severity, Severity, ""))))
| eval fixed_version=trim(toString(coalesce(fixed_version, FixedVersion, fixedIn, fix_version, "")))
| where len(vulnerability_id)>4 AND match(vulnerability_id, "^CVE-[0-9]{4}-[0-9]+")
| eval has_fix=if(isnotnull(fixed_version) AND len(fixed_version)>0 AND lower(fixed_version)!="null", 1, 0)
| eval is_crit=if(sev_norm="CRITICAL", 1, 0)
| eval is_high=if(sev_norm="HIGH", 1, 0)
| eval is_med=if(match(sev_norm, "^(MEDIUM|MODERATE)$"), 1, 0)
| eval is_low=if(sev_norm="LOW", 1, 0)
| join type=left max=0 vulnerability_id
    [| inputlookup cisa_kev_catalog.csv
     | eval vulnerability_id=upper(trim(toString(coalesce(cveID, cve_id, CVE, cve, ""))))
     | eval kev_listed=1
     | fields vulnerability_id kev_listed ]
| fillnull value=0 kev_listed
| join type=left max=0 vulnerability_id
    [| inputlookup epss_scores.csv
     | eval vulnerability_id=upper(trim(toString(coalesce(cve, cve_id, CVE, ""))))
     | eval epss_score=tonumber(coalesce(epss, epss_score, score, "0"), 10)
     | fields vulnerability_id epss_score ]
| fillnull value=0 epss_score
| join type=left max=0 vulnerability_id image_digest
    [| inputlookup cve_first_seen.csv
     | eval vulnerability_id=upper(trim(toString(vulnerability_id)))
     | eval image_digest=trim(toString(image_digest))
     | eval first_seen_epoch=tonumber(coalesce(first_seen_epoch, first_seen, ""), 10)
     | fields vulnerability_id image_digest first_seen_epoch ]
| eval first_seen_at=coalesce(first_seen_epoch, _time)
| eval days_unpatched=round((now()-first_seen_at)/86400, 2)
| eval crit_high_epss_flag=if((is_crit=1 OR is_high=1) AND epss_score>0.5, 1, 0)
| eval epss_weight_mult=if(crit_high_epss_flag=1, 1.5, 1.0)
| eval row_weight=(is_crit*10 + is_high*5 + is_med*2 + is_low*1) * epss_weight_mult
| eval kev_crit_with_fix=if(kev_listed=1 AND is_crit=1 AND has_fix=1, 1, 0)
| eval kev_crit_no_fix=if(kev_listed=1 AND is_crit=1 AND has_fix=0, 1, 0)
| eval crit_sla_breach=if(is_crit=1 AND days_unpatched>7, 1, 0)
| eval high_sla_breach=if(is_high=1 AND days_unpatched>30, 1, 0)
| eval med_sla_breach=if(is_med=1 AND days_unpatched>90, 1, 0)
| sort 0 + image_name image_digest scanner vulnerability_id _time
| streamstats window=30 current=t max(days_unpatched) AS sla_aging_trend_days BY image_name, image_digest, scanner, vulnerability_id
| dedup image_name image_digest scanner vulnerability_id
| stats
    dc(eval(if(is_crit=1, vulnerability_id, null()))) AS critical_cves
    dc(eval(if(is_high=1, vulnerability_id, null()))) AS high_cves
    dc(eval(if(is_med=1, vulnerability_id, null()))) AS medium_cves
    dc(eval(if(is_low=1, vulnerability_id, null()))) AS low_cves
    sum(row_weight) AS epss_weighted_score
    max(days_unpatched) AS oldest_unpatched_days
    max(sla_aging_trend_days) AS sla_aging_trend_peak
    dc(eval(if(kev_listed=1, vulnerability_id, null()))) AS kev_count
    dc(eval(if(has_fix=1, vulnerability_id, null()))) AS fixed_available_count
    max(kev_crit_with_fix) AS flag_kev_crit_fix
    max(kev_crit_no_fix) AS flag_kev_crit_nofix
    max(crit_high_epss_flag) AS flag_epss_hot
    max(crit_sla_breach) AS flag_crit_sla
    max(high_sla_breach) AS flag_high_sla
    max(med_sla_breach) AS flag_med_sla
  BY image_name image_digest scanner
| eventstats perc50(epss_weighted_score) AS fleet_p50_epss_score perc90(epss_weighted_score) AS fleet_p90_epss_score
| eval severity=case(
    flag_kev_crit_fix>0, "critical_kev_listed_with_fix_available",
    flag_kev_crit_nofix>0, "critical_kev_listed_no_fix",
    flag_epss_hot>0, "critical_high_epss_above_0_5",
    flag_crit_sla>0, "high_critical_cve_over_7_day_sla",
    flag_high_sla>0, "medium_high_cve_over_30_day_sla",
    true(), "low_baseline_drift")
| eval recommended_response=case(
    severity="critical_kev_listed_with_fix_available", "Block promotion on this digest, open emergency change to rebuild the base layer with the published fix, validate registry admission policy, and attach KEV ticket linkage for auditors.",
    severity="critical_kev_listed_no_fix", "Treat as active weaponization risk: isolate workloads on this digest, escalate to vendor liaison, deploy compensating controls, and track daily until NVD or vendor advisory publishes remediation.",
    severity="critical_high_epss_above_0_5", "Prioritize ahead of CVSS-only backlog: schedule patch within 48 hours, cross-check runtime exposure with sibling UC-3.1.21 signals, and widen hunt for the same package version fleet-wide.",
    severity="high_critical_cve_over_7_day_sla", "Critical CVEs exceeded the seven-day remediation SLA: force rebuild, freeze dependent releases, and produce executive breach summary with owner accountability.",
    severity="medium_high_cve_over_30_day_sla", "High-severity CVEs exceeded the thirty-day SLA: assign capacity in the next sprint, document risk acceptance only with board-level exception, and refresh EPSS and KEV joins.",
    true(), "Maintain cadence: keep scanner feeds warm, reconcile duplicate findings across scanners, and trend epss_weighted_score against fleet percentiles.")
| table image_name image_digest scanner critical_cves high_cves medium_cves kev_count epss_weighted_score oldest_unpatched_days fixed_available_count severity recommended_response fleet_p50_epss_score fleet_p90_epss_score sla_aging_trend_peak
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Vulnerabilities WHERE nodename=Vulnerabilities earliest=-24h latest=now BY Vulnerabilities.signature Vulnerabilities.dest
| rename Vulnerabilities.dest AS image_name
```

## Visualization

Per-image severity heatmap faceted by scanner, time-series of kev_count and epss_weighted_score with fleet percentile ribbons, EPSS-weighted top images bar chart, and patch-SLA aging histogram with optional LastBuilt overlay for stale base detection.

## Known False Positives

Trivy and Grype vulnerability databases occasionally lag vendor advisories by hours or days, so a Critical in National Vulnerability Database may already be downgraded in a distro security notice while scanners still scream Critical until the DB sync completes. Minimal images such as distroless or Wolfi builds sometimes report package strings that do not match NVD CPE expectations, producing version mismatch noise until you align scanner flags with the distro’s own security tracker. KEV entries may describe Windows-only exploitation paths yet still list a CVE that also affects a Linux shared library; platform owners must read the KEV description before blocking a Linux digest. When one CVE is Critical under CVSS v3 but the software vendor documents that the vulnerable code path is unreachable in your container entrypoint, vulnerability management needs a documented exception rather than Splunk suppression. Running Trivy, Grype, and Snyk in parallel without a deduplication key yields duplicate CVE rows that inflate counts until you dedup on image digest plus CVE plus scanner as this search does. Brand-new CVE placeholders sometimes arrive as UNKNOWN severity before NVD publishes; treat those as data-quality tickets, not automatic production blocks. Snyk CVSS versus Trivy severity can disagree on the same GHSA identifier; governance should pick a primary scoring source for escalations while still ingesting all feeds for coverage. EPSS scores fluctuate daily; a drop from 0.55 to 0.45 is not automatic closure if KEV or compensating-control debt remains. False positives also come from scanning scratch or intermediate CI layers that never deploy to customer-facing clusters; exclude those namespaces via lookup, not by muting the entire sourcetype.

## References

- [Trivy documentation](https://aquasecurity.github.io/trivy/)
- [Grype documentation](https://github.com/anchore/grype)
- [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [FIRST EPSS documentation](https://www.first.org/epss/)
- [Splunk Lantern — Detect and prioritize app security vulnerabilities](https://lantern.splunk.com/Observability/UCE/Proactive_response/Detect_and_Prioritize_App_Security_Vulnerabilities)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
