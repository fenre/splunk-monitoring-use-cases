<!-- AUTO-GENERATED from UC-3.4.4.json — DO NOT EDIT -->

---
id: "3.4.4"
title: "Registry Image Vulnerability Scan Results"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.4.4 · Registry Image Vulnerability Scan Results

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance, Audit &middot; **Wave:** Crawl &middot; **Status:** Verified

*Before any software package is allowed to run in our systems, it must pass a security inspection — we track which packages passed, which were blocked, and whether any slipped through without inspection.*

---

## Description

Monitors **Harbor** scan-on-push policy compliance by tracking SCANNING_COMPLETED webhook verdicts across every project, computing per-project pass/block/warning rates, and correlating with **Kubernetes admission controller** deny events from **OPA Gatekeeper** or **Kyverno** to verify that vulnerable images are actually prevented from deploying — closing the loop between registry scanning and runtime enforcement.

## Value

Scanning images without enforcing the results is security theater — the scan itself does not prevent a critical CVE from reaching production. This use case closes the enforcement gap by tracking whether policy verdicts are honored end-to-end: a BLOCKED verdict in the registry should produce a corresponding deny in the admission controller, and any mismatch reveals a policy bypass that attackers could exploit.

## Implementation

Configure Harbor scan-on-push with SCANNING_COMPLETED webhooks sent to Splunk HEC. Collect Kubernetes admission controller audit logs from OPA Gatekeeper or Kyverno to track image deployment denials. Build two search variants: per-project scan compliance rates (passed/blocked/warning/failed) and admission controller enforcement tracking. Alert when compliance rate drops below 95% or when blocked images appear in running containers.

## Detailed Implementation

### Prerequisites
- **Harbor** 2.6+ with **scan-on-push** enabled per project and a **vulnerability policy** configured (Project → Configuration → **Deployment Security** → set severity threshold for blocking pulls — e.g., block pulls when critical CVE count > 0).
- **OPA Gatekeeper** 3.12+ or **Kyverno** 1.9+ deployed as a **Kubernetes admission controller** with image scanning policies that validate each pod's container images against scan results before allowing deployment. Example: Gatekeeper **`ConstraintTemplate`** that queries the registry API for scan status and denies admission if the image has not passed the vulnerability scan.
- **Splunk HEC** token for **`index=containers`** with **`sourcetype=harbor:webhook`** for scan completion events; secondary streams for **`sourcetype=kube:admission`** (**admission controller** audit events) and **`sourcetype=kube:container:status`** (running image **digest**s).
- **Kubernetes audit logging** enabled at the API server with the admission response recorded at the **RequestResponse** **audit level** so denied requests are captured with their reason and policy details.
- **Splunk Connect for Kubernetes** or **OTel Collector** collecting **admission audit events** — Gatekeeper logs decisions to the **audit log** and also emits constraint violation metrics; Kyverno logs policy reports as **Kubernetes** custom resources.
- Splunk RBAC: users running **compliance search**es need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`security_compliance_analyst`**).
- **License estimate**: scan completion webhooks are ~1–2 KB each; admission controller events ~500 bytes each; a registry scanning 200 images/day with 50 deployment attempts produces ~1 MB/day.

### Step 1 — Configure data collection
(1) **Harbor scan webhooks**: subscribe to **`SCANNING_COMPLETED`** and **`SCANNING_FAILED`** webhook events in Harbor (Administration → Webhooks or per-project under Project → Webhooks). The SCANNING_COMPLETED payload includes:
— **`scan_overview.scan_status`** (Success, Error, Queued)
— **`scan_overview.summary`** (severity counts: Critical, High, Medium, Low, Unknown)
— **`repository.repo_full_name`**, **`repository.tag`**, **`repository.digest`**
This is the source-of-truth for whether each image's scan verdict is PASSED, BLOCKED, or FAILED.

(2) **Harbor deployment security policy**: configure the **pull-prevention** policy in Harbor (Project → Configuration → **Deployment Security**) to **block pulls** when the image has critical CVEs. This creates an enforcement point at the registry level. The SPL's **`policy_verdict`** classification mirrors this threshold.

(3) **Admission controller events**: for **OPA Gatekeeper**, collect the gatekeeper-audit-controller logs as **`sourcetype=kube:admission`** — denied requests include the **`constraint_template`** name, **`message`** (reason for denial), and the rejected **pod specification** including image references. For **Kyverno**, collect **PolicyReport** custom resources or Kyverno's **admission webhook** logs.

(4) **Running image verification**: collect **`sourcetype=kube:container:status`** to detect enforcement bypass — images that appear as running containers despite having a BLOCKED scan verdict in the registry. This catches scenarios where the admission controller is misconfigured, running in audit-only mode, or not covering all namespaces.

(5) **Policy exception lookup**: create **`scan_policy_exceptions.csv`** with columns `image_pattern`, `project`, `exception_reason`, `approved_by`, `expiry_date` for images with approved **policy exception**s. Reference in the compliance search to distinguish intentional exceptions from policy gaps.

### Step 2 — Create the search and alert
The primary SPL computes per-project **scan compliance rates** by classifying each scan result into PASSED (zero critical CVEs), BLOCKED (critical > 0), WARNING (high > 5), or SCAN_FAILED. The **`compliance_pct`** metric shows what percentage of images in each project have clean scan results.

The admission-controller variant tracks actual **deployment denials** — each denied admission event represents a vulnerable image that was prevented from running. Grouping by namespace and showing the enforcing policy names provides accountability for which policies are actively protecting each environment.

The enforcement gap is measured by comparing the two searches: BLOCKED images in the registry that do NOT have corresponding deny events in the admission controller indicate a **policy bypass**. Conversely, admission denials without a corresponding BLOCKED scan result may indicate overly strict admission policies or misconfigured policy rules.

Schedule the compliance search **hourly** and alert when any **production** project's `compliance_pct` drops below 95%. Schedule the **admission search** every **15 minutes** and alert on any denial to provide immediate feedback to the deploying team. Run a **daily correlation search** comparing BLOCKED image digests against running container digests to detect bypass.

### Step 3 — Validate
(a) Push a clean image (no critical CVEs) and verify: `index=containers sourcetype="harbor:webhook" event_type="SCANNING_COMPLETED" | head 1 | table scan_status critical high`. Should show `scan_status=Success`, `critical=0`.
(b) Push a known-vulnerable image (e.g., `nginx:1.14`) and verify the scan result shows `critical > 0` and the `policy_verdict=BLOCKED` in the SPL output.
(c) Attempt to deploy the BLOCKED image: `kubectl run vuln-test --image=<harbor>/library/nginx:1.14` — the admission controller should deny the request. Verify: `index=containers sourcetype="kube:admission" action=deny | head 1`.
(d) Verify **compliance percentage**: count the PASSED and BLOCKED images manually in Harbor UI and compare with the Splunk `compliance_pct` value.
(e) Test the **bypass detection**: if the admission controller is in audit-only mode, the deployment succeeds despite a BLOCKED verdict. The daily correlation search should surface the deployed digest as a **policy bypass**.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **gauge charts** per project showing **compliance percentage** with color bands (green ≥ 95%, yellow ≥ 85%, red < 85%).
- Row B: **single-value tiles** — overall compliance %, total BLOCKED images, admission denials today, scan failures today, active policy exceptions.
- Row C: **blocked images table** — project, image_ref, digest, critical, high, scan_status, verdict. Drilldown opens the CVE detail from UC-3.4.2.
- Row D: **admission denial table** — ns, deny_count, unique_images_blocked, enforcing_policies, last_reason. Drilldown shows the full admission event.
- **Alerting**: project compliance < 95% → email to **project security lead**; BLOCKED image running in production (bypass detection) → **PagerDuty** P1; scan failure → Slack `#registry-ops`; admission denial → Slack `#deploy-feedback` with image name and reason.
- **Runbook** (owner: AppSec team): (1) for BLOCKED images: check if the critical CVEs have fixes (cross-reference UC-3.4.2 patch priority), (2) for scan failures: check Harbor scanner health in Harbor UI → Interrogation Services, (3) for admission denials: verify the policy is correct and not blocking legitimate deployments, (4) for bypass detection: check admission controller mode (enforce vs. audit-only) and namespace coverage.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **compliance scorecard** (**Dashboard Studio**) showing each project as a colored card (green/yellow/red) with the compliance percentage and BLOCKED count; pair with a **Sankey diagram** flowing scan verdict → admission decision → deployment outcome to visualize the end-to-end **enforcement pipeline**; add a **trend chart** of daily compliance_pct per project to show whether enforcement is improving.
- **Alert design**: include `project`, `image_ref`, `verdict`, `critical`, `high`, `compliance_pct` in scan alerts; for admission alerts include `ns`, `image`, `policy`, `reason`; for bypass alerts include the running pod name, namespace, and image digest with a Harbor **deep-link**.
- **Scan webhooks arrive but severity counts are null** — Harbor versions before 2.8 use a different scan_overview JSON structure. Check the raw event with `| spath` and adjust the `coalesce` chain to match your version's field paths.
- **Admission events missing** — Gatekeeper's audit controller may not be configured to emit webhook logs; check `kubectl logs -n gatekeeper-system deployment/gatekeeper-audit-controller`. For Kyverno, check the admission webhook configuration: `kubectl get validatingwebhookconfigurations`.
- **Compliance shows 100% but known-vulnerable images exist** — the search evaluates the latest scan per image; if a **rescan** has not run since new CVEs were published, the previous clean result persists. Ensure **nightly scheduled** scans (UC-3.4.2 Step 1) keep results current.
- **High admission denial count** — may indicate a policy that is too strict or a team deploying images from an unscanned registry. Check whether denied images have any scan results at all.
- **Bypass detection correlation fails** — **kube:container:status** image digests must use the same format as Harbor digests (sha256:xxx). Normalize with `| eval digest=replace(container_image_digest, "^sha256:", "")`.

## SPL

```spl
`comment("--- Registry Scan Policy Compliance — Pass/Fail by Project and Image ---")`
index=containers (sourcetype="harbor:webhook" OR sourcetype="harbor:audit")
| eval event=coalesce(event_type, operation, type)
| where match(event, "(?i)scanning_completed|scan_completed|scan")
| eval repository=coalesce('event_data.repository.repo_full_name', resource, repository)
| eval tag=coalesce('event_data.repository.tag', tag, "untagged")
| eval digest=coalesce('event_data.repository.digest', digest, "")
| eval project=coalesce('event_data.repository.namespace', mvindex(split(repository, "/"), 0))
| eval scan_status=coalesce('event_data.scan_overview.scan_status', scan_status, "unknown")
| eval critical=tonumber(coalesce('event_data.scan_overview.summary.Critical', critical_count, "0"))
| eval high=tonumber(coalesce('event_data.scan_overview.summary.High', high_count, "0"))
| eval medium=tonumber(coalesce('event_data.scan_overview.summary.Medium', medium_count, "0"))
| eval total_cves=critical + high + medium
| eval policy_verdict=case(
    critical > 0, "BLOCKED",
    high > 5, "WARNING",
    scan_status="Error", "SCAN_FAILED",
    scan_status="Success" AND critical=0, "PASSED",
    1=1, "UNKNOWN")
| eval image_ref=repository.":".tag
| stats latest(policy_verdict) as verdict,
    latest(critical) as critical,
    latest(high) as high,
    latest(medium) as medium,
    latest(scan_status) as scan_status,
    latest(_time) as last_scan
    by project, image_ref, digest
| stats count(eval(verdict="PASSED")) as passed,
    count(eval(verdict="BLOCKED")) as blocked,
    count(eval(verdict="WARNING")) as warnings,
    count(eval(verdict="SCAN_FAILED")) as scan_failures,
    count as total_images
    by project
| eval compliance_pct=round(100 * passed / max(1, total_images), 1)
| sort -blocked
| table project total_images passed blocked warnings scan_failures compliance_pct

`comment("--- Admission Controller Enforcement — Blocked Deployments ---")`
index=containers sourcetype="kube:admission"
| eval action=lower(coalesce(decision, response_allowed, "unknown"))
| where action IN ("deny", "false", "rejected")
| eval ns=coalesce(namespace, request_namespace, object_namespace)
| eval image=coalesce(request_image, container_image, spec_image)
| eval policy=coalesce(constraint_template, policy_name, admission_policy)
| eval reason=coalesce(message, status_message, reason, "policy violation")
| stats count as deny_count,
    dc(image) as unique_images_blocked,
    values(image) as blocked_images,
    values(policy) as enforcing_policies,
    latest(reason) as last_reason,
    latest(_time) as last_denied
    by ns
| sort -deny_count
| table ns deny_count unique_images_blocked enforcing_policies last_reason last_denied blocked_images
```

## Visualization

Compliance rate gauge per project, blocked/passed bar chart, admission denial table with policy details, single-value tiles (overall compliance %, blocked images, scan failures).

## Known False Positives

**audit_mode_inflation** — When the Kubernetes admission controller runs in audit-only mode rather than enforce mode, it logs policy violations as informational events rather than actual denials. The admission denial search counts these as blocked deployments even though the image was allowed to run. Filter by the admission controller's mode field or cross-reference with running containers.

**rescan_verdict_flip** — Harbor's nightly scheduled rescan may change a previously PASSED image to BLOCKED when new CVEs are published against its packages. The compliance search shows a sudden compliance drop that reflects new vulnerability discoveries, not a regression in the build pipeline. Compare with the CVE publication date to distinguish.

**multi_scanner_disagreement** — If both Trivy and Clair are configured as Harbor scanners, they may produce different severity classifications for the same CVE due to different scoring methodologies. An image may show as PASSED by one scanner and BLOCKED by another. Standardize on a single scanner for policy enforcement.

**tag_immutability_bypass** — Images pushed with a mutable tag (e.g., `:latest`) can be replaced after scanning, resulting in a PASSED verdict for a different image than what is currently tagged. Enable tag immutability in Harbor project settings to prevent this bypass.

**namespace_exclusion_gap** — Admission controllers typically exclude system namespaces (kube-system, istio-system) from image scan policies. Images deployed to these namespaces bypass the enforcement gate legitimately. Document excluded namespaces in the policy exception lookup.

**init_container_scan_skip** — Some admission policies only validate the main container images but skip init containers and ephemeral containers. A vulnerable init container image can be deployed without triggering an admission denial. Extend the admission policy to cover all container types.

## References

- [Harbor — Vulnerability Scanning Policies](https://goharbor.io/docs/2.10.0/administration/vulnerability-scanning/)
- [Harbor — Webhook Notifications](https://goharbor.io/docs/2.10.0/administration/webhook-notifications/)
- [OPA Gatekeeper — Kubernetes Admission Controller](https://open-policy-agent.github.io/gatekeeper/website/docs/)
- [Kyverno — Kubernetes Policy Engine](https://kyverno.io/docs/introduction/)
- [Kubernetes Admission Controllers Reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
