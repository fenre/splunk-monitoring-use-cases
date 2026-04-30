<!-- AUTO-GENERATED from UC-3.4.2.json — DO NOT EDIT -->

---
id: "3.4.2"
title: "Vulnerability Scan Results"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.2 · Vulnerability Scan Results

## Description

Ingests **Trivy** and **Grype** container image scan results to compute per-image vulnerability severity distributions (critical, high, medium, low), identifies fixable CVEs with available patches, and ranks images by risk tier — giving security teams a prioritized remediation queue before vulnerable images reach production.

## Value

Every unpatched critical CVE in a deployed image is an open attack surface that compounds with time; correlating scan results across the registry in Splunk gives security and platform teams a single view of which images carry the most risk, which vulnerabilities have available fixes, and whether the overall vulnerability backlog is shrinking or growing — evidence that patch-management reviews and compliance audits require.

## Implementation

Configure CI/CD pipelines to run Trivy or Grype scans after each image build and POST JSON results to Splunk HEC as sourcetype=trivy:scan or sourcetype=grype:scan. Optionally poll Harbor's vulnerability API via rest_ta for registry-wide scan results. Build searches for severity distribution by image, fixable CVE patch priority lists, and image risk tier classification. Alert on any image with critical CVEs and schedule daily reports for security review.

## Detailed Implementation

Prerequisites
• **Trivy** 0.45+ or **Grype** 0.70+ installed in your **CI/CD pipeline** (GitHub Actions, GitLab CI, Jenkins) or integrated into **Harbor** as the default scanner; verify with `trivy --version` or `grype version`.
• **Harbor** 2.6+ with **scan-on-push** enabled per project (Project → Configuration → Vulnerability scanning → Automatically scan images on push) so every pushed image is scanned without manual intervention.
• **Splunk HEC** token provisioned for **`index=containers`** with default **`sourcetype=trivy:scan`**; a second HEC token or source override for **Grype** results landing as **`sourcetype=grype:scan`**; third stream for **Harbor** webhooks as **`sourcetype=harbor:webhook`**.
• **Splunk **REST API** Modular Input** (**rest_ta**, **Splunkbase 1546**) on a **heavy forwarder** if you want to poll Harbor's **vulnerability API** for registry-wide scan results rather than relying solely on CI/CD pipeline output.
• **CI/CD integration**: add a post-build step that runs the scanner and sends results to HEC. Example for **Trivy**: `trivy image --format json --output results.json <image>:<tag> && curl -k https://<hec>:8088/services/collector/event -H "Authorization: Splunk <token>" -d @results.json`. Grype: `grype <image>:<tag> -o json | curl -k https://<hec>:8088/services/collector/event -H "Authorization: Splunk <token>" -d @-`.
• **RBAC**: Splunk users running vulnerability searches need **`srchIndexesAllowed`** including **`containers`**; assign via a custom role (**`vuln_analyst`**).
• **License estimate**: a typical scan report for a single image contains 50–500 CVE entries at ~100 bytes each; scanning 200 images/day generates ~5–50 MB/day.

Step 1 — Configure data collection
(1) **CI/CD pipeline path** (recommended for shift-left scanning): add **Trivy** or **Grype** as a build step that runs after `docker build` and before `docker push`. Configure the scanner to output **JSON format** and POST results to **Splunk HEC**. For Trivy, use `--format json` and pipe through `curl`; for Grype, use `-o json`. Include the image reference (repository:tag@digest) in the HEC event metadata so each scan result is tied to a specific image build.

(2) **Harbor **scan-on-push** path** (registry-integrated): Harbor runs the configured scanner (Trivy by default since Harbor 2.2) automatically on every pushed artifact. Poll the scan results via **REST API**: `GET /api/v2.0/projects/{project_name}/repositories/{repo_name}/artifacts/{reference}/additions/vulnerabilities`. Configure **rest_ta** (**Splunkbase 1546**) or a **scripted input** to poll this endpoint for each project every **1 hour**, indexing results as **`sourcetype=harbor:audit`**.

(3) **Harbor webhook path**: subscribe to the **`SCANNING_COMPLETED`** webhook event in Harbor (see UC-3.4.1 Step 1 for webhook setup). The webhook payload includes the scan overview (total CVE counts by severity) but not individual CVE details — use it as a trigger to poll the full vulnerability API for the scanned artifact.

(4) **Running-image correlation**: collect **`sourcetype=kube:container:status`** from the OTel Collector or Splunk Connect for Kubernetes to capture which image digests are actually running in the cluster. This lets you distinguish between "vulnerable image in registry" (informational) and "vulnerable image running in production" (actionable).

(5) **Lookup setup**: create **`cve_exceptions.csv`** with columns `cve_id`, `image_pattern`, `exception_reason`, `expiry_date` for **accepted-risk** CVEs that should not trigger alerts. Define in **`transforms.conf`** and reference in the search with `| lookup cve_exceptions cve_id OUTPUT exception_reason | where isnull(exception_reason)`.

Step 2 — Create the search and alert
The primary SPL normalizes **Trivy** and **Grype** JSON structures into a common schema. The **`coalesce`** chains handle the different field names: Trivy uses **`VulnerabilityID`**, **`Severity`**, **`PkgName`**, **`InstalledVersion`**, **`FixedVersion`**, **`Target`**; Grype uses `id`, `severity`, `package.name`, `package.version`, `fix.versions{}`, `artifact_name`.

The **`risk_tier`** classification assigns each image a tier based on the highest-severity vulnerabilities present: any critical CVE → CRITICAL tier, more than 5 high CVEs → HIGH tier, any high → MEDIUM, otherwise LOW. This drives dashboard color-coding and alert routing.

The **`has_fix`** field distinguishes CVEs with available patches (`fixable`) from those without (`no-fix`), which directly impacts remediation priority — a fixable critical CVE is more urgent than an unfixable one because the team can act immediately.

The **patch-priority** variant filters to fixable critical/high CVEs and groups by `cve_id` + `pkg_name` to show which single package upgrade would fix the most images — the highest-leverage remediation action.

Schedule the severity-distribution search **daily at 07:00** over **`-24h`** for the morning security review. Schedule the patch-priority search **weekly** for the remediation planning meeting. Alert **immediately** (every 15 minutes over `-15m`) when any image has **critical > 0** and the CVE is not in the exceptions lookup.

Step 3 — Validate
(a) Push a known-vulnerable image: `docker pull nginx:1.14` (contains known CVEs), scan with `trivy image nginx:1.14 --format json`, send to HEC. Verify: `index=containers sourcetype="trivy:scan" earliest=-1h | stats dc(VulnerabilityID) as cves`. Should return several dozen CVEs.
(b) Compare Trivy CLI output with Splunk: `trivy image nginx:1.14 --severity CRITICAL,HIGH` shows a count; `index=containers sourcetype="trivy:scan" Target="nginx:1.14" Severity IN ("CRITICAL","HIGH") | stats dc(VulnerabilityID)` should match.
(c) Verify **Grype** normalization: if using both scanners, scan the same image with both and confirm the Splunk search produces comparable CVE counts (they may differ slightly due to different **vulnerability databases**).
(d) Test the exceptions lookup: add a known CVE to **`cve_exceptions.csv`** and verify the alert search excludes it.
(e) Verify **running-image correlation**: `index=containers sourcetype="kube:container:status" | stats dc(container_image_digest) as running_images` should return the count of unique image digests in the cluster.

Step 4 — Operationalize dashboards and runbooks
• Row A: **stacked bar chart** of CVE counts by severity (critical/high/medium/low) per image — immediately shows which images carry the most risk.
• Row B: **single-value tiles** — total critical CVEs across all images, percentage of CVEs that are fixable, images scanned in last 24h, images with zero critical/high CVEs (green count for positive reinforcement).
• Row C: **patch-priority table** from the second SPL variant — columns: cve_id, severity, pkg_name, current_ver, fix_ver, max_cvss, affected_images. Drilldown opens **NVD** detail page for the CVE.
• Row D: **risk-tier treemap** — each image is a rectangle sized by total CVE count and colored by risk_tier (red=CRITICAL, orange=HIGH, yellow=MEDIUM, green=LOW).
• **Alerting**: critical CVE in any image → Slack `#security-vulns` + Jira ticket auto-creation; critical CVE in a running production image → **PagerDuty** P2; weekly digest of fixable high CVEs → email to engineering leads.
• **Runbook** (owner: AppSec on-call): (1) verify the CVE applies to the image's OS/package (some scanners report kernel CVEs in userspace images), (2) check if a fixed version exists in `fix_ver`, (3) rebuild the image with the updated base or package, (4) if no fix exists, add to `cve_exceptions.csv` with expiry date and justification.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **risk matrix** (custom viz or Dashboard Studio grid) with images on the Y-axis and CVE severities on the X-axis, cell color by count; pair with a **trend line** of total critical CVEs over 30 days to show whether remediation is outpacing new discoveries; add a **pie chart** of fixable vs. unfixable CVEs.
• **Alert design**: include `image_ref`, `cve_id`, `severity`, `pkg_name`, `installed_ver`, `fixed_ver`, `cvss_score`, and a direct NVD link (`https://nvd.nist.gov/vuln/detail/<cve_id>`) in every alert payload.
• **No scan results arriving** — verify the CI/CD pipeline step runs after `docker build`; check HEC token validity and network connectivity from the CI runner to the HEC endpoint; inspect pipeline logs for `curl` errors.
• **Scan results arrive but severity is null** — Trivy versions before 0.30 use lowercase severity values; check **`props.conf`** for case-sensitive field extraction; the SPL `upper()` call normalizes this.
• **Duplicate CVEs across scanners** — expected when running both Trivy and Grype on the same image; the search groups `by image_ref, scanner` to keep results separate. For a unified view, add `| dedup cve_id, image_ref` after the `eval` chain.
• **Harbor scan-on-push not triggering** — verify the project-level scan policy is enabled; check Harbor's `jobservice` container logs for scan queue errors; confirm the scanner adapter (Trivy) is healthy: `curl https://<harbor>/api/v2.0/scanners`.
• **CVSS score always zero** — some CVEs lack NVD **CVSS** v3 scores; the `coalesce` chain falls through to `"0"`; for more accurate scoring, enrich with a CVSS lookup from the NVD API or use the scanner's built-in CVSS calculation.
• **Alert fatigue from known-accepted CVEs** — populate the **`cve_exceptions.csv`** lookup with accepted-risk CVEs and their expiry dates; review and prune the exceptions quarterly.

## SPL

```spl
`comment("--- Vulnerability Scan Results — Severity Distribution by Image ---")`
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| eval scanner=case(
    sourcetype="trivy:scan", "trivy",
    sourcetype="grype:scan", "grype",
    1=1, "unknown")
| eval cve_id=coalesce(VulnerabilityID, id, vulnerability, "unknown")
| eval severity=upper(coalesce(Severity, severity, "UNKNOWN"))
| eval pkg_name=coalesce(PkgName, package.name, artifact.name, "unknown")
| eval installed_ver=coalesce(InstalledVersion, package.version, artifact.version, "")
| eval fixed_ver=coalesce(FixedVersion, fix.versions{}, "none")
| eval cvss_score=tonumber(coalesce('CVSS.nvd.V3Score', 'cvss.value', cvss_v3_score, "0"))
| eval image_ref=coalesce(Target, artifact_name, image, "unknown")
| eval has_fix=if(fixed_ver!="none" AND fixed_ver!="", "fixable", "no-fix")
| stats dc(cve_id) as unique_cves,
    dc(eval(if(severity="CRITICAL", cve_id, null()))) as critical,
    dc(eval(if(severity="HIGH", cve_id, null()))) as high,
    dc(eval(if(severity="MEDIUM", cve_id, null()))) as medium,
    dc(eval(if(severity="LOW", cve_id, null()))) as low,
    dc(eval(if(has_fix="fixable", cve_id, null()))) as fixable,
    max(cvss_score) as max_cvss,
    latest(_time) as last_scan
    by image_ref, scanner
| eval risk_tier=case(
    critical > 0, "CRITICAL",
    high > 5, "HIGH",
    high > 0, "MEDIUM",
    1=1, "LOW")
| sort -critical -high -max_cvss
| head 100
| table image_ref scanner unique_cves critical high medium low fixable max_cvss risk_tier last_scan

`comment("--- Fixable Critical/High CVEs — Patch Priority List ---")`
index=containers (sourcetype="trivy:scan" OR sourcetype="grype:scan")
| eval severity=upper(coalesce(Severity, severity))
| where severity IN ("CRITICAL", "HIGH")
| eval cve_id=coalesce(VulnerabilityID, id, vulnerability)
| eval pkg_name=coalesce(PkgName, package.name, artifact.name)
| eval installed_ver=coalesce(InstalledVersion, package.version, artifact.version)
| eval fixed_ver=coalesce(FixedVersion, fix.versions{}, "none")
| eval image_ref=coalesce(Target, artifact_name, image)
| eval cvss_score=tonumber(coalesce('CVSS.nvd.V3Score', 'cvss.value', cvss_v3_score, "0"))
| where fixed_ver!="none" AND fixed_ver!=""
| stats dc(image_ref) as affected_images,
    values(image_ref) as images,
    latest(installed_ver) as current_ver,
    latest(fixed_ver) as fix_ver,
    max(cvss_score) as max_cvss,
    latest(_time) as last_seen
    by cve_id, pkg_name, severity
| sort -max_cvss -affected_images
| head 50
| table cve_id severity pkg_name current_ver fix_ver max_cvss affected_images images last_seen
```

## Visualization

Stacked bar chart (CVE severity distribution by image), sortable patch-priority table, single-value tiles (total critical CVEs, fixable percentage, images scanned today), risk-tier treemap.

## Known False Positives

**base_image_inheritance** — CVEs reported against the base OS layer (alpine, debian, ubuntu) appear in every image built on that base, inflating the total count even though a single base-image update would remediate all of them. Group CVEs by `pkg_name` and base image to identify this pattern and prioritize the base-image rebuild over individual image patches.

**scanner_database_lag** — Trivy and Grype update their vulnerability databases on different schedules; a scan run immediately after a new CVE is published may not detect it until the database refreshes (typically within 6–12 hours). Re-scan images after database updates to ensure coverage.

**disputed_cve_noise** — Some CVEs are disputed or marked as "not a vulnerability" by the upstream maintainer but remain in the NVD database. These inflate severity counts without representing real risk. Cross-reference flagged CVEs with upstream advisories and add confirmed false positives to `cve_exceptions.csv`.

**dev_image_pollution** — Development and test images (tagged `dev-*`, `test-*`, `snapshot-*`) often contain debug tools, extra packages, and unpatched dependencies that inflate vulnerability counts. Filter by image tag pattern or namespace to separate production image risk from development noise.

**go_binary_phantom** — Go binaries compiled with older Go toolchains report CVEs against the Go standard library even when the vulnerable code path is not reachable from the application. Trivy's Go module analysis may overreport; verify reachability before prioritizing remediation.

**kernel_cve_in_container** — Scanners sometimes report kernel CVEs against container images even though containers share the host kernel and cannot independently patch it. These CVEs should be tracked at the node/host level, not the container image level; suppress with an exceptions lookup keyed to kernel-related package names.

## References

- [Trivy — Container Image Vulnerability Scanner](https://aquasecurity.github.io/trivy/latest/)
- [Grype — Container Image Vulnerability Scanner](https://github.com/anchore/grype)
- [Harbor — Vulnerability Scanning](https://goharbor.io/docs/2.10.0/administration/vulnerability-scanning/)
- [Splunk REST API Modular Input (Splunkbase 1546)](https://splunkbase.splunk.com/app/1546)
- [NVD — National Vulnerability Database](https://nvd.nist.gov/)
