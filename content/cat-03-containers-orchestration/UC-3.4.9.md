<!-- AUTO-GENERATED from UC-3.4.9.json — DO NOT EDIT -->

---
id: "3.4.9"
title: "Container Image Vulnerability Age"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.4.9 · Container Image Vulnerability Age

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We track how many days each known security problem has been sitting unpatched in our software packages and flag the ones that have been ignored past the deadline, so the team fixes the most overdue ones first.*

---

## Description

Tracks the **age of known Critical and High CVEs** in container images against remediation SLA windows (Critical: 7 days, High: 30 days), then cross-references vulnerability scan results with **actively running pods** to identify which production workloads are operating with overdue vulnerabilities — providing the security and compliance evidence needed to prioritize patching and enforce remediation timelines.

## Value

Knowing that a vulnerability exists is not enough — knowing how long it has been known and whether a fix is available transforms vulnerability management from a scan-and-forget exercise into a measurable remediation program. A Critical CVE published 3 days ago is an acceptable risk; the same CVE at 30 days old with a fix available is a compliance violation and a security incident waiting to happen. Tracking vulnerability age against SLA windows gives security teams the data to escalate overdue patches, measure mean-time-to-remediate (MTTR), and prove compliance with organizational security policies and regulatory frameworks (SOC 2, PCI DSS, HIPAA).

## Implementation

Ingest Trivy/Grype/Harbor scan results into index=containers via HEC. Build two search variants: SLA tracking with age-based breach classification for Critical (>7d) and High (>30d) CVEs, and cross-reference with running pod images to identify deployed workloads with aged vulnerabilities. Alert on SLA_BREACH for any deployed image.

## Detailed Implementation

### Prerequisites
- **Vulnerability scanning** integrated at two stages:
  — **CI/CD pipeline**: run **Trivy** or **Grype** as a pipeline step that scans container images after build and outputs **JSON results** to **Splunk HEC** as **`sourcetype=trivy:scan`** or **`sourcetype=grype:scan`**.
  — **Registry-level**: configure **Harbor's** built-in Trivy integration to scan images on push and periodically re-scan stored images. Harbor **scan result**s are available via the **`/api/v2.0/projects/{name}/repositories/{name}/artifacts/{reference}/additions/vulnerabilities`** API endpoint.
- **Splunk HEC** token for **`index=containers`** with sourcetype routing for scan results, pod status, and events.
- **Pod status collection**: **Splunk Connect for Kubernetes** or the OTel Collector's **k8s_cluster receiver** collecting **`sourcetype=kube:pod:status`** with container **image reference**s. This is essential for cross-referencing scan results with **actively deployed images**.
- **SLA definition**: establish remediation SLAs by severity:
  — **Critical**: remediate within **7 days** of CVE publication (or 3 days for actively exploited CVEs with CISA KEV listing)
  — **High**: remediate within **30 days**
  — **Medium**: remediate within **90 days**
  — **Low**: remediate within **180 days** or accept risk
  Store SLA thresholds in a **lookup** (`vuln_sla_thresholds.csv`) for flexible tuning.
- **CVE enrichment**: create a **lookup** (`cisa_kev.csv`) containing the CISA Known Exploited Vulnerabilities catalog. CVEs on this list require accelerated remediation (3-day SLA). Update this lookup weekly from the CISA KEV API.
- Splunk RBAC: assign a **`security_analyst`** role with **`srchIndexesAllowed`** including `containers`.
- **License estimate**: a scan of a typical container image produces 50–500 vulnerability records (~50 KB–500 KB per scan). A registry with 200 images scanned daily generates 10–100 MB/day.

### Step 1 — Configure data collection
(1) **Trivy CI/CD integration**: add Trivy as a pipeline step that outputs JSON results:
```bash
trivy image --format json --output trivy-results.json $IMAGE_REF
curl -k https://<splunk-hec>:8088/services/collector/event \
  -H "Authorization: Splunk $HEC_TOKEN" \
  -d @trivy-results.json
```

Key fields in Trivy JSON output:
— **`Target`** (the image reference: `registry/repo:tag`)
— **`Vulnerabilities[].VulnerabilityID`** (CVE ID, e.g., CVE-2024-1234)
— **`Vulnerabilities[].Severity`** (Critical, High, Medium, Low)
— **`Vulnerabilities[].PkgName`** (the vulnerable package)
— **`Vulnerabilities[].InstalledVersion`** / **`FixedVersion`** (current and fix versions)
— **`Vulnerabilities[].PublishedDate`** (when the CVE was published — this is the baseline for age calculation)
— **`Vulnerabilities[].CVSS`** (**CVSS v3** score and vector)

(2) **Grype scanner integration**: Grype outputs similar JSON with slightly different field names. The SPL uses **`coalesce`** to normalize between Trivy and Grype field names.

(3) **Harbor scan result collection**: configure a `rest_ta` input to poll Harbor's vulnerability API for each artifact. Harbor aggregates Trivy results and provides **severity counts** per artifact, making it possible to track vulnerability posture at the **registry level** without running separate scans.

(4) **Running pod image inventory**: collect **`sourcetype=kube:pod:status`** with the `container_image` field. This creates a real-time inventory of which images are **actually running** in production, enabling the critical cross-reference between scan results and deployed workloads. Without this cross-reference, vulnerability reports show what is in the registry, not what is in production.

(5) **Admission controller events**: if **OPA Gatekeeper** or **Kyverno** policies block deployments with aged vulnerabilities (UC-3.4.4), collect the **`sourcetype=kube:events`** from these admission controllers to track how many deployment attempts were blocked and why.
\n• **SBOM correlation**: correlate vulnerability age data with **Software Bill of Materials** (**SBOM**) records from **Syft** or **Trivy SBOM** output. Mapping CVEs to the **SBOM dependency graph** reveals whether a vulnerability exists in a direct dependency (immediately actionable) or a transitive dependency (requires upstream update). This distinction affects **remediation priority** and **effort estimation**.
### Step 2 — Create the search and alert
The primary SPL tracks **vulnerability age** against SLA windows:
— **SLA_BREACH**: Critical CVEs older than **7 days** or High CVEs older than **30 days** — these are overdue for remediation.
— **SLA_WARNING**: Critical CVEs older than **3 days** or High CVEs older than **14 days** — these are approaching SLA deadlines.
— **WITHIN_SLA**: vulnerabilities within acceptable age.

The **`has_fix`** field is critical for prioritization — a CVE with a fix available is actionable (update the package), while a CVE without a fix requires a compensating control (WAF rule, network segmentation, image replacement).

The cross-reference variant joins scan results with **running pod images** to produce a risk-prioritized list: images running in production with the most aged CVEs ranked first. This is the primary actionable output for security and platform teams.

Schedule the SLA tracking search **daily** at **08:00** and alert on any SLA_BREACH. Schedule the deployed image cross-reference **daily** and send a summary report to the security team.

### Step 3 — Validate
(a) Verify scan data: `index=containers sourcetype="trivy:scan" earliest=-7d | stats dc(Target) as images_scanned, dc(VulnerabilityID) as unique_cves`. Should show recent scans.
(b) Test age calculation: find a known CVE with a published date and verify `vuln_age_days` matches: `index=containers sourcetype="trivy:scan" VulnerabilityID="CVE-2024-1234" | table PublishedDate vuln_age_days`.
(c) Verify SLA classification: `index=containers sourcetype="trivy:scan" Severity="Critical" earliest=-30d | eval vuln_age_days=round((now()-strptime(PublishedDate,"%Y-%m-%dT%H:%M:%S"))/86400,0) | where vuln_age_days > 7 | stats count`. Should show Critical CVEs in SLA_BREACH.
(d) Test cross-reference: `index=containers sourcetype="kube:pod:status" earliest=-1h | stats dc(container_image) as running_images`. Should match the number of unique images in production.
(e) Verify enrichment: `| inputlookup cisa_kev.csv | stats count`. Should contain the current CISA KEV catalog.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — total images scanned, SLA_BREACH count (red), SLA_WARNING count (amber), deployed images at risk, oldest unpatched CVE (days).
- Row B: **vulnerability age histogram** — distribution of CVE ages in buckets (0–7d, 8–30d, 31–90d, 91–180d, 180d+) for Critical and High severities.
- Row C: **deployed image risk table** — namespace, image_ref, running_pods, total_aged_cves, worst_age. Red rows for SLA_BREACH.
- Row D: **SLA compliance trend** — weekly percentage of images within SLA over 30 days. Shows whether the organization's vulnerability posture is improving or degrading.
- **Alerting**: SLA_BREACH for any deployed image → Slack `#security-ops` + email to image owner; SLA_WARNING → daily digest; CISA KEV match → PagerDuty P2 (actively exploited CVE in production); SLA compliance below 80% → weekly escalation to management.
- **Runbook** (owner: security operations): (1) identify the owning team from the namespace and image name, (2) check if a **FixedVersion** exists — if yes, update the **base image** or package, (3) if no fix: assess CVSS vector for exploitability and implement compensating controls, (4) update the image tag and trigger redeployment, (5) re-scan to verify the CVE is resolved.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **bubble chart** where each bubble represents an image, X-axis is oldest CVE age, Y-axis is CVE count, and bubble size is running pod count — large bubbles in the upper-right corner are the highest-priority remediation targets. Color by SLA status.
- **Alert design**: include `image_ref`, `severity`, `unique_cves`, `oldest_cve_days`, `fixable_cves`, `sla_status`, and `cve_list` (top 5) in the alert payload. For deployed image alerts include `ns`, `running_pods`, and `worst_age`.
- **Scan results show zero vulnerabilities** — the scanner may be running against a minimal/distroless image that has no OS-level packages. Verify by running a scan against a known-vulnerable image (e.g., `nginx:1.21`) and confirming CVEs appear.
- **Age calculation shows negative days** — the CVE's `PublishedDate` is in the future, which indicates a data quality issue in the **vulnerability database**. Filter these with `where vuln_age_days >= 0`.
- **Cross-reference shows no matches** — the `image_ref` format differs between scan results (e.g., `registry.example.com/app:v1.0`) and pod status (e.g., `registry.example.com/app@sha256:abc`). Normalize image references by stripping the tag/digest suffix before joining.
- **SLA breach count is very high** — many organizations initially discover thousands of aged vulnerabilities when first implementing SLA tracking. Focus on **Critical CVEs with fixes available** and **images deployed in production** to prioritize the remediation backlog.

## SPL

```spl
`comment("--- Vulnerability Age SLA Tracking — Critical/High CVEs Beyond Remediation Window ---")`
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan" OR sourcetype="harbor:scan")
| eval cve_id=coalesce(VulnerabilityID, vulnerability_id, cve, "unknown")
| eval severity=coalesce(Severity, severity, vuln_severity)
| eval pkg=coalesce(PkgName, package, artifact_name)
| eval installed=coalesce(InstalledVersion, installed_version)
| eval fixed=coalesce(FixedVersion, fix_versions, "none")
| eval vuln_date=coalesce(PublishedDate, published_date, discovered_at)
| eval vuln_epoch=strptime(vuln_date, "%Y-%m-%dT%H:%M:%S")
| eval vuln_age_days=round((now() - vuln_epoch) / 86400, 0)
| eval image_ref=coalesce(Target, image, artifact_digest)
| eval has_fix=if(fixed != "none" AND fixed != "", 1, 0)
| eval sla_status=case(
    severity IN ("Critical","CRITICAL") AND vuln_age_days > 7, "SLA_BREACH",
    severity IN ("High","HIGH") AND vuln_age_days > 30, "SLA_BREACH",
    severity IN ("Critical","CRITICAL") AND vuln_age_days > 3, "SLA_WARNING",
    severity IN ("High","HIGH") AND vuln_age_days > 14, "SLA_WARNING",
    1=1, "WITHIN_SLA")
| where sla_status != "WITHIN_SLA"
| stats dc(cve_id) as unique_cves,
    max(vuln_age_days) as oldest_cve_days,
    sum(has_fix) as fixable_cves,
    values(cve_id) as cve_list
    by image_ref, severity, sla_status
| sort -oldest_cve_days
| head 50
| table image_ref severity unique_cves oldest_cve_days fixable_cves sla_status cve_list

`comment("--- Deployed Image Vulnerability Cross-Reference — Running Pods with Aged CVEs ---")`
index=containers sourcetype="kube:pod:status"
| eval ns=coalesce(namespace, metadata.namespace)
| eval pod=coalesce(pod_name, metadata.name)
| eval image_ref=coalesce(container_image, image)
| dedup ns, pod, image_ref sortby -_time
| join type=left image_ref [
    search index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
    | eval severity=coalesce(Severity, severity)
    | eval vuln_date=coalesce(PublishedDate, published_date)
    | eval vuln_epoch=strptime(vuln_date, "%Y-%m-%dT%H:%M:%S")
    | eval vuln_age_days=round((now() - vuln_epoch) / 86400, 0)
    | eval image_ref=coalesce(Target, image)
    | where severity IN ("Critical","CRITICAL","High","HIGH") AND vuln_age_days > 7
    | stats dc(VulnerabilityID) as aged_cves, max(vuln_age_days) as max_age by image_ref
]
| where aged_cves > 0
| stats sum(aged_cves) as total_aged_cves,
    max(max_age) as worst_age,
    dc(pod) as running_pods
    by ns, image_ref
| sort -worst_age
| table ns image_ref running_pods total_aged_cves worst_age
```

## Visualization

SLA compliance gauge, vulnerability age distribution histogram, image-to-CVE heatmap, running-pods-at-risk table, MTTR trend line, severity-colored SLA status table.

## Known False Positives

**disputed_cve_classification** — Some CVEs are disputed by the software vendor or classified at a higher severity by the NVD than the vendor considers appropriate. A Critical CVE that the vendor has assessed as Low risk inflates the SLA breach count. Cross-reference with vendor security advisories and maintain a dispute lookup to reclassify known disputed CVEs.

**base_image_inherited_cves** — Many CVEs come from the base image (debian, ubuntu, alpine) packages that are not used by the application. These packages exist in the image layer but are never executed. The vulnerability is technically present but not exploitable in context. Use Trivy's VEX (Vulnerability Exploitability eXchange) support to mark non-exploitable CVEs.

**scanner_database_lag** — Vulnerability scanners depend on their vulnerability database being current. If the database is outdated, recently published CVEs will not appear in scan results, creating a false sense of compliance. Monitor the scanner's database update timestamp and alert when it is more than 24 hours stale.

**image_tag_reuse** — If image tags are reused (e.g., the same `latest` tag points to different digests over time), scan results may reference an image that has been replaced by a newer build. The aged CVE may have been fixed in the current image but the scan result refers to the old digest. Use image digests rather than tags for precise cross-referencing.

**fix_version_not_yet_released** — A CVE may have a known fix in upstream code but no released package version yet. The scan shows the CVE as fixable but no update is available to install. Track the `FixedVersion` field — if it contains a version not yet released in the package repository, the CVE is not yet actionable.

**dev_namespace_noise** — Development and staging namespaces intentionally run older image versions for testing purposes. These images may have many aged CVEs that do not represent production risk. Use namespace classification to separate production SLA tracking from non-production environments.

## References

- [Trivy — Container Image Scanning](https://aquasecurity.github.io/trivy/latest/docs/target/container_image/)
- [Grype — Vulnerability Scanner](https://github.com/anchore/grype)
- [NIST — Vulnerability Metrics and Scoring](https://nvd.nist.gov/vuln-metrics/cvss)
- [Harbor — Vulnerability Scanning](https://goharbor.io/docs/latest/administration/vulnerability-scanning/)
- [Splunk join Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Join)
