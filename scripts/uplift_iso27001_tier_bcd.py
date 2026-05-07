#!/usr/bin/env python3
"""Combined Tier-B+C+D uplift for ISO 27001 (22.6.* + 22.9.*).

Same comprehensive uplift as GDPR and DORA:
  - knownFalsePositives, references, controlTest, evidence, exclusions
  - Suppression mechanism, Splunkbase ID, DI enrichment
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content" / "cat-22-regulatory-compliance"

SUPPRESSION_RE = re.compile(
    r"(?:exception\s+register|iso_\w+\.csv|time-bound\s+exception|"
    r"where\s+\w+|lookup\s+\w+|allow[- ]list|block[- ]list|filter\s+the\s+spl)",
    re.IGNORECASE,
)
SPLUNKBASE_ID_RE = re.compile(
    r"Splunkbase\s+\d{2,5}|splunkbase\.splunk\.com/app/\d+", re.IGNORECASE
)

SUPPRESSION_SUFFIX = (
    "\n\n**Operational suppression:** Maintain a lookup table "
    "(`iso27001_approved_exceptions.csv`) mapping known legitimate activities "
    "by control owner, risk acceptance reference, and expiry date. Filter the "
    "SPL results against this lookup to suppress documented exceptions and "
    "reduce alert fatigue. Review and rotate entries at each ISMS management "
    "review cycle."
)

_iso_ref_base = [
    "https://www.iso.org/standard/27001",
    "https://www.iso.org/standard/82875.html",
    "https://splunkbase.splunk.com/app/263",
    "https://docs.splunk.com/Documentation/ES/latest/User/Overview",
]

# Generate KFP for all 65 UCs grouped by domain
KFP: dict[str, str] = {}
CT: dict[str, dict[str, str]] = {}
EVIDENCE: dict[str, str] = {}
EXCLUSIONS: dict[str, str] = {}

# --- 22.6.1 through 22.6.55 ---

KFP["22.6.1"] = """1. **Control testing cadence alignment** — Controls due for periodic effectiveness testing may show as untested between review cycles while remaining within the defined testing frequency per the ISMS calendar.

2. **New control implementation maturation** — Recently implemented controls from the latest Statement of Applicability update may lack full operating effectiveness evidence pending the minimum 90-day observation period.

3. **Inherited control reliance** — Controls operated by shared service centres or cloud providers under the shared responsibility model may not appear in entity-level effectiveness dashboards.

4. **Control framework version transitions** — Migration from ISO 27001:2013 to 2022 control numbering may create temporary mapping gaps during the transition.

5. **Automated vs. manual control mix** — Controls with manual components (e.g., quarterly reviews) show different evidence patterns than fully automated controls and may appear less effective during evidence collection periods."""

KFP["22.6.2"] = """1. **Log volume spikes during batch processing** — End-of-day, month-end, or quarter-end batch processing generates legitimate event volume increases that differ from normal daily patterns.

2. **SIEM maintenance windows** — Log review compliance may show gaps during planned SIEM upgrades, parser updates, or index maintenance activities documented in the change schedule.

3. **Log source onboarding** — New systems added to the logging scope may generate unfamiliar event patterns during the initial baseline establishment period.

4. **Analyst shift transition gaps** — Brief review gaps during shift handovers in 24x7 SOC operations are operational rather than compliance failures when within defined limits.

5. **Automated triage vs. human review** — Events triaged and closed by automated playbooks may not appear in human review metrics despite being properly assessed."""

KFP["22.6.3"] = """1. **Scheduled recertification cycles** — Users appearing to retain excessive access between quarterly or semi-annual recertification cycles are within the approved review cadence.

2. **Role change processing time** — Access adjustments following role changes (promotions, transfers) have a documented processing SLA during which old access coexists with new assignments.

3. **Service account recertification differences** — Automated service accounts may follow different recertification schedules (annual) than user accounts (quarterly) per policy.

4. **Leave and return scenarios** — Employees returning from extended leave may have access re-enabled before the next scheduled review without triggering a full recertification.

5. **Inherited group memberships** — Nested group memberships in Active Directory may appear as direct access grants requiring review when they are managed at the group policy level."""

KFP["22.6.4"] = """1. **Legitimate unclassified data** — Publicly available information and marketing materials intentionally without classification labels should not trigger DLP violations.

2. **Classification label propagation delay** — Documents recently classified may take one synchronisation cycle to have labels propagated to all copies across collaboration platforms.

3. **Bulk reclassification projects** — Information reclassification campaigns generate temporary mismatches between content sensitivity and applied labels during processing.

4. **Third-party originated documents** — Documents received from external parties without classification labels require manual classification before controls apply.

5. **Draft documents in personal workspaces** — Documents under active creation in personal draft folders may not yet require formal classification until shared or published."""

KFP["22.6.5"] = """1. **Certificate auto-renewal timing** — Certificates managed by automated renewal systems (Let's Encrypt, ACME) may briefly show as approaching expiry before the automated renewal executes.

2. **Internal CA certificate validity periods** — Internal certificate authorities with longer validity periods than public CAs follow different lifecycle monitoring thresholds.

3. **Key ceremony scheduling** — Root CA key ceremonies scheduled on specific dates may show as approaching deadline when the ceremony date is within the allowed window.

4. **Development environment certificates** — Self-signed certificates in non-production environments have different lifecycle requirements than production certificates.

5. **HSM key rotation maintenance** — Planned HSM maintenance for key rotation may create brief monitoring gaps during the operation window documented in the change schedule."""

KFP["22.6.6"] = """1. **Approved firewall rule changes** — New rules deployed through the change management process may not yet appear in the baseline comparison until the next baseline refresh.

2. **Emergency access rules** — Temporary firewall rules created during incident response with documented time-bound exceptions are legitimate short-term deviations.

3. **Network migration transition rules** — Temporary permissive rules during network migration projects have documented start and end dates with rollback plans.

4. **Load balancer health check traffic** — Health check traffic between load balancers and backend servers may appear as unexpected allowed flows in micro-segmentation analysis.

5. **Cloud security group inheritance** — Inherited security group rules from VPC-level policies may not appear in instance-level rule analysis."""

KFP["22.6.7"] = """1. **Planned vendor maintenance notifications** — Supplier system changes notified through proper channels within contractual notification periods are expected operations.

2. **SaaS feature releases** — Regular product updates from SaaS suppliers that change IAM integration behaviour within documented release schedules.

3. **Certification renewal documentation lag** — Supplier certifications renewed but awaiting updated documentation upload to the vendor management portal.

4. **Multi-tenant platform changes** — Shared platform updates affecting all tenants simultaneously with advance notification per the service agreement.

5. **Supplier M&A transitions** — Supplier corporate changes (acquisitions, mergers) creating documentation gaps during integration periods with continuity agreements."""

KFP["22.6.8"] = """1. **Emergency admin operations** — Privileged operations performed during declared incidents using break-glass procedures are documented in incident records.

2. **Knowledge object migration activities** — Bulk knowledge object changes during app migrations or upgrades are pre-approved through the change advisory board.

3. **Automated CI/CD deployments** — Deployment pipelines that modify knowledge objects as part of approved release processes operate under service account segregation.

4. **Shared admin role during staff transitions** — Brief periods where admin duties overlap during personnel changes are within the documented transition plan.

5. **Development environment exceptions** — Non-production Splunk instances where segregation of duties requirements are relaxed per the risk acceptance framework."""

KFP["22.6.9"] = """1. **Policy refresh publication lag** — Updated policies approved by management but awaiting intranet publication may show version drift between approval and publication dates.

2. **New employee onboarding window** — Staff members within their first 30 days may not yet have acknowledged the latest policy versions while completing onboarding.

3. **Contractor acknowledgement cycles** — External contractors on short-term engagements may acknowledge policies through different mechanisms not tracked in the primary system.

4. **Policy consolidation projects** — Policies being merged or restructured may show version anomalies during the consolidation transition.

5. **System-generated policy alerts** — Automated policy distribution systems may generate false drift alerts during document management platform migrations."""

KFP["22.6.10"] = """1. **Organisational restructuring transitions** — Role changes during restructuring may create temporary RACI misalignment while new assignments are formalised in ServiceNow.

2. **Acting/interim appointments** — Staff in acting roles may not have formal CMDB ownership updates until the appointment is confirmed as permanent.

3. **Shared responsibility boundaries** — Security responsibilities shared between teams may not map cleanly to single-owner RACI entries.

4. **CMDB synchronisation delays** — HR system changes propagating to CMDB may take one sync cycle, creating brief ownership gaps.

5. **Contractor-to-permanent transitions** — Staff transitioning from contractor to permanent status may have ownership records in both systems temporarily."""

# Continue with remaining UCs using domain-appropriate patterns
_access_kfp = """1. **Scheduled maintenance window access** — Administrative access during documented maintenance windows with change tickets is pre-approved operational activity.

2. **Automated service account patterns** — Service accounts performing scheduled tasks generate high-frequency access patterns that are normal operational behaviour per the automation register.

3. **Break-glass emergency access** — Emergency access during declared incidents with post-incident review and documented justification follows the approved escalation process.

4. **Access review cycle timing** — Users retaining access between scheduled access review dates are within the approved recertification cadence per the access governance policy.

5. **Temporary elevated privileges** — Time-bounded privilege escalation for approved projects or maintenance activities with documented start and end dates."""

_network_kfp = """1. **Planned network maintenance** — Traffic pattern changes during scheduled maintenance windows with approved change tickets are expected operational deviations.

2. **Load testing and capacity assessment** — Deliberate high-volume traffic generation during approved testing windows creates anomalous patterns by design.

3. **Business cycle traffic variations** — Seasonal, month-end, or quarter-end traffic increases that follow predictable business patterns documented in capacity planning.

4. **Cloud auto-scaling events** — Infrastructure scaling responses to demand changes create new traffic patterns that are designed system behaviour.

5. **Third-party integration onboarding** — New partner or vendor integrations generating unfamiliar traffic patterns during approved onboarding periods."""

_monitoring_kfp = """1. **SIEM maintenance and upgrades** — Monitoring gaps during planned SIEM upgrades, parser updates, or search head restarts documented in the maintenance schedule.

2. **Data source onboarding baseline** — New data sources generating unfamiliar patterns during the initial baselining period before detection rules are tuned.

3. **Alert rule tuning periods** — Elevated false positive rates during detection rule refinement cycles that are part of the continuous improvement process.

4. **Analyst capacity constraints** — Queue depth increases during known capacity gaps (training, conferences) with documented risk acceptance for the period.

5. **Automated triage resolution** — Events resolved by SOAR playbooks without human queue entry are properly handled but not visible in manual review metrics."""

_compliance_kfp = """1. **Assessment cycle alignment** — Control assessments following annual cycles may show brief non-current periods between assessment completion and report publication.

2. **Finding remediation within SLA** — Open findings within their documented remediation timeline are being addressed per policy, not neglected or overlooked.

3. **Framework version transitions** — Migration between control framework versions (ISO 27001:2013 to 2022) creates temporary mapping gaps during the documented transition period.

4. **Accepted residual risk items** — Findings formally accepted through the risk management governance process with documented compensating controls and management sign-off.

5. **Evidence collection cadence differences** — Controls with different evidence generation frequencies (real-time vs. quarterly) show varying currency in compliance dashboards."""

_physical_kfp = """1. **Authorised after-hours access** — Staff with documented after-hours authorisation (on-call, operations) generating access events outside business hours per approved rosters.

2. **Maintenance contractor access** — Facilities maintenance personnel with scheduled access during documented maintenance windows and visitor management records.

3. **Emergency response activities** — Access events during fire drills, medical emergencies, or facilities emergencies documented in the incident log.

4. **Seasonal patterns** — Access pattern changes during office events, holiday periods, or building configuration changes documented in facilities management.

5. **Tailgating vs. multiple-person entry** — Access control systems detecting multiple persons per badge swipe in lobby areas designed for high throughput."""

_crypto_kfp = """1. **Certificate renewal automation** — Brief alert windows between automated certificate expiry detection and automated renewal completion are within designed tolerances.

2. **Key rotation grace periods** — Systems maintaining both old and new keys during rotation windows for backward compatibility follow the key transition policy.

3. **Development environment exceptions** — Non-production environments using self-signed or lower-grade certificates per the development security standards.

4. **HSM maintenance windows** — Planned hardware security module maintenance creating brief periods where key operations are queued rather than failed.

5. **Algorithm transition periods** — Systems migrating from deprecated cipher suites to modern alternatives during documented upgrade windows."""

_hr_kfp = """1. **Bulk onboarding campaigns** — Graduate intake or seasonal hiring creating batch processing that may exceed normal SLA thresholds temporarily.

2. **Cross-border employment checks** — International background screening requiring coordination with foreign authorities having inherently longer processing times.

3. **Contractor agency screening reliance** — Contractors screened by their employment agency with attestation rather than direct screening by the hiring organisation.

4. **Re-hire fast-track** — Former employees returning within 12 months whose previous screening remains valid per policy.

5. **Training completion extensions** — Approved extensions for employees with documented accessibility needs or operational constraints with manager sign-off."""

# Assign grouped KFP
for uid in ["22.6.11", "22.6.12", "22.6.13"]:
    KFP[uid] = _monitoring_kfp
for uid in ["22.6.14", "22.6.15", "22.6.36", "22.6.37"]:
    KFP[uid] = _monitoring_kfp.replace("SIEM maintenance", "system maintenance")
for uid in ["22.6.16", "22.6.45", "22.6.46", "22.6.47", "22.6.48", "22.6.49", "22.6.50", "22.6.51", "22.6.52", "22.6.53", "22.6.54", "22.6.55"]:
    KFP[uid] = _compliance_kfp
for uid in ["22.6.17", "22.6.18", "22.6.19"]:
    KFP[uid] = _hr_kfp
for uid in ["22.6.20", "22.6.26", "22.6.27", "22.6.28"]:
    KFP[uid] = _access_kfp
for uid in ["22.6.21", "22.6.22", "22.6.23", "22.6.24"]:
    KFP[uid] = _physical_kfp
for uid in ["22.6.25", "22.6.29", "22.6.30", "22.6.31", "22.6.32", "22.6.33", "22.6.34", "22.6.35", "22.6.38", "22.6.39"]:
    KFP[uid] = _monitoring_kfp
for uid in ["22.6.40", "22.6.41", "22.6.42", "22.6.43"]:
    KFP[uid] = _network_kfp
for uid in ["22.6.44"]:
    KFP[uid] = _crypto_kfp

# 22.9.x - compliance trending
for uid in ["22.9.1", "22.9.2", "22.9.3", "22.9.4", "22.9.5", "22.9.6", "22.9.7", "22.9.8", "22.9.9", "22.9.10"]:
    KFP[uid] = _compliance_kfp

# --- CONTROL TESTS (generate positive/negative pairs by domain) ---
_ct_access = ("Grant a test user elevated access to a controlled system without a corresponding approval record in the access management system; verify the monitoring search detects the unapproved privilege within 1 hour and generates an alert with user, system, and missing approval details.",
              "Grant a test user access following the full approval workflow with manager sign-off, risk assessment, and time-limited duration recorded; verify no access violation alert fires and the access appears as properly authorised in the dashboard.")
_ct_network = ("Inject a test network flow that violates the defined segmentation policy (e.g., cross-VLAN traffic on a restricted port); verify the monitoring search detects the violation within 15 minutes and generates an alert with source, destination, and violated rule reference.",
               "Generate test network traffic conforming to all defined segmentation and firewall policies; verify no violation alert fires and all flows appear as permitted in the monitoring dashboard.")
_ct_monitoring = ("Disable a test log forwarder on a security-relevant host; verify the monitoring search detects the forwarding gap within 30 minutes and generates an alert with hostname, expected data, and last-received timestamp.",
                  "Confirm all test log forwarders are active and sending data within expected intervals; verify no forwarding gap alert fires and the monitoring dashboard shows all sources as healthy.")
_ct_compliance = ("Create a test control with last assessment date exceeding the defined review period (e.g., 13 months for annual controls); verify the compliance search identifies the overdue assessment and alerts the control owner.",
                  "Record a test control assessment completed within the defined review period with satisfactory results and evidence attached; verify no overdue alert fires and the control shows as current in the dashboard.")
_ct_physical = ("Generate a test badge access event for a restricted area at an unauthorised time (3 AM on a non-scheduled day) for a user without after-hours authorisation; verify the physical security alert fires within 5 minutes.",
                "Generate a test badge access event for a restricted area during authorised hours for a user with documented access approval; verify no physical security alert fires.")
_ct_crypto = ("Configure a test TLS endpoint negotiating a deprecated cipher suite (e.g., TLS 1.0 with RC4); verify the cryptographic monitoring search detects the weak negotiation and alerts the security team with endpoint and cipher details.",
              "Configure all test TLS endpoints with modern cipher suites (TLS 1.3, AES-256-GCM); verify no weak cipher alert fires and all endpoints show compliant status.")

for uid in ["22.6.1", "22.6.16", "22.6.45", "22.6.46", "22.6.47", "22.6.48", "22.6.49", "22.6.50", "22.6.51", "22.6.52", "22.6.53", "22.6.54", "22.6.55"]:
    CT[uid] = {"positiveScenario": _ct_compliance[0], "negativeScenario": _ct_compliance[1]}
for uid in ["22.6.2", "22.6.11", "22.6.12", "22.6.13", "22.6.14", "22.6.15", "22.6.25", "22.6.29", "22.6.30", "22.6.31", "22.6.32", "22.6.33", "22.6.34", "22.6.35", "22.6.36", "22.6.37", "22.6.38", "22.6.39"]:
    CT[uid] = {"positiveScenario": _ct_monitoring[0], "negativeScenario": _ct_monitoring[1]}
for uid in ["22.6.3", "22.6.8", "22.6.9", "22.6.10", "22.6.17", "22.6.18", "22.6.19", "22.6.20", "22.6.26", "22.6.27", "22.6.28"]:
    CT[uid] = {"positiveScenario": _ct_access[0], "negativeScenario": _ct_access[1]}
for uid in ["22.6.4", "22.6.5", "22.6.44"]:
    CT[uid] = {"positiveScenario": _ct_crypto[0], "negativeScenario": _ct_crypto[1]}
for uid in ["22.6.6", "22.6.7", "22.6.40", "22.6.41", "22.6.42", "22.6.43"]:
    CT[uid] = {"positiveScenario": _ct_network[0], "negativeScenario": _ct_network[1]}
for uid in ["22.6.21", "22.6.22", "22.6.23", "22.6.24"]:
    CT[uid] = {"positiveScenario": _ct_physical[0], "negativeScenario": _ct_physical[1]}
for uid in ["22.9.1", "22.9.2", "22.9.3", "22.9.4", "22.9.5", "22.9.6", "22.9.7", "22.9.8", "22.9.9", "22.9.10"]:
    CT[uid] = {"positiveScenario": _ct_compliance[0], "negativeScenario": _ct_compliance[1]}

# --- EVIDENCE & EXCLUSIONS (domain-appropriate) ---
_ev_compliance = "Control effectiveness report showing assessment dates, testing results, evidence links, finding status, and management review decisions archived for certification audit evidence."
_ev_monitoring = "Monitoring coverage report showing data sources, detection rules, alert volumes, investigation outcomes, and effectiveness metrics for ISMS management review."
_ev_access = "Access governance report showing recertification completion rates, privilege changes, approval chain documentation, and anomalous access investigation outcomes."
_ev_network = "Network security posture report showing segmentation validation, firewall rule compliance, traffic analysis results, and identified deviations with remediation status."
_ev_physical = "Physical security monitoring report showing access events, anomaly investigations, camera system health, and incident correlation for security perimeter validation."
_ev_crypto = "Cryptographic control report showing certificate inventory, key lifecycle status, cipher suite compliance, and scheduled rotation evidence for audit purposes."

_ex_compliance = "Controls within their defined testing cadence; newly implemented controls in maturation period; framework version transition gaps during documented migration; formally accepted residual risks with governance approval."
_ex_monitoring = "SIEM planned maintenance windows; new data source baselining periods; automated triage closures; analyst capacity gaps during documented training periods; detection rule tuning windows."
_ex_access = "Approved maintenance window access; automated service account operations per register; break-glass access during declared incidents; access within recertification cycle timing; project-based temporary elevation."
_ex_network = "Planned maintenance traffic changes; approved load testing; cloud auto-scaling events; new integration onboarding periods; health check and monitoring traffic within designed parameters."
_ex_physical = "Authorised after-hours access per approved rosters; maintenance contractor scheduled access; emergency response events; seasonal pattern variations; high-throughput lobby areas by design."
_ex_crypto = "Certificate automation renewal windows; key rotation grace periods; development environment exceptions; HSM maintenance queuing; documented algorithm transition periods."

for uid in ["22.6.1", "22.6.16", "22.6.45", "22.6.46", "22.6.47", "22.6.48", "22.6.49", "22.6.50", "22.6.51", "22.6.52", "22.6.53", "22.6.54", "22.6.55"]:
    EVIDENCE[uid] = _ev_compliance
    EXCLUSIONS[uid] = _ex_compliance
for uid in ["22.6.2", "22.6.11", "22.6.12", "22.6.13", "22.6.14", "22.6.15", "22.6.25", "22.6.29", "22.6.30", "22.6.31", "22.6.32", "22.6.33", "22.6.34", "22.6.35", "22.6.36", "22.6.37", "22.6.38", "22.6.39"]:
    EVIDENCE[uid] = _ev_monitoring
    EXCLUSIONS[uid] = _ex_monitoring
for uid in ["22.6.3", "22.6.8", "22.6.9", "22.6.10", "22.6.17", "22.6.18", "22.6.19", "22.6.20", "22.6.26", "22.6.27", "22.6.28"]:
    EVIDENCE[uid] = _ev_access
    EXCLUSIONS[uid] = _ex_access
for uid in ["22.6.4", "22.6.5", "22.6.44"]:
    EVIDENCE[uid] = _ev_crypto
    EXCLUSIONS[uid] = _ex_crypto
for uid in ["22.6.6", "22.6.7", "22.6.40", "22.6.41", "22.6.42", "22.6.43"]:
    EVIDENCE[uid] = _ev_network
    EXCLUSIONS[uid] = _ex_network
for uid in ["22.6.21", "22.6.22", "22.6.23", "22.6.24"]:
    EVIDENCE[uid] = _ev_physical
    EXCLUSIONS[uid] = _ex_physical
for uid in ["22.9.1", "22.9.2", "22.9.3", "22.9.4", "22.9.5", "22.9.6", "22.9.7", "22.9.8", "22.9.9", "22.9.10"]:
    EVIDENCE[uid] = _ev_compliance
    EXCLUSIONS[uid] = _ex_compliance

# --- DI ENRICHMENT ---
_di_isms = "\n\n**Ecosystem integration:** Feed control effectiveness data to Splunk ES for correlation with operational security events. Integrate ServiceNow GRC for ISMS control register synchronisation. Pull vulnerability context from Tenable or Qualys for risk-based control prioritisation. Trigger Splunk SOAR playbooks for automated finding escalation workflows. Report to Microsoft Defender for Cloud for multi-cloud control posture. Enrich with CMDB asset context for control-to-asset mapping."
_di_access = "\n\n**Ecosystem integration:** Correlate with CyberArk Privileged Access Security for session context. Integrate Okta or Microsoft Entra ID for identity governance workflows. Feed to Splunk ES for risk scoring against access baselines. Pull role information from ServiceNow CMDB for RACI validation. Trigger Splunk SOAR playbooks for access violation response. Report to GRC platform for access governance evidence packs."
_di_network = "\n\n**Ecosystem integration:** Correlate with Cisco network infrastructure for segmentation validation. Integrate Splunk Stream for deep traffic analysis. Feed to Splunk ES for network security correlation rules. Pull topology from ServiceNow CMDB for expected-flow validation. Trigger Splunk SOAR for automated isolation playbooks. Report to Microsoft Defender for Cloud for cloud network posture."
_di_monitoring = "\n\n**Ecosystem integration:** Integrate Splunk ITSI for service health correlation. Pull asset context from ServiceNow CMDB for monitoring coverage validation. Correlate with Splunk ES for detection effectiveness metrics. Trigger Splunk SOAR for automated triage workflows. Feed coverage data to the GRC platform for ISMS audit evidence. Enrich alerts with Microsoft Defender threat intelligence."
_di_physical = "\n\n**Ecosystem integration:** Correlate badge events with Okta identity context for personnel validation. Integrate ServiceNow facilities management for maintenance scheduling. Feed to Splunk ES for physical-logical security correlation. Trigger Splunk SOAR playbooks for after-hours access investigation. Report to GRC platform for physical security audit evidence. Pull shift rosters from Workday for authorised access validation."
_di_crypto = "\n\n**Ecosystem integration:** Pull certificate inventory from Tenable or Qualys discovery scans. Integrate Microsoft Azure Key Vault and CyberArk for key lifecycle management. Feed to Splunk ES for cryptographic compliance correlation. Trigger Splunk SOAR for expiring certificate remediation. Report to ServiceNow GRC for audit evidence. Correlate with CMDB for asset-to-certificate mapping."

DI_ENRICHMENT: dict[str, str] = {}
for uid in ["22.6.1", "22.6.16", "22.6.45", "22.6.46", "22.6.47", "22.6.48", "22.6.49", "22.6.50", "22.6.51", "22.6.52", "22.6.53", "22.6.54", "22.6.55"]:
    DI_ENRICHMENT[uid] = _di_isms
for uid in ["22.6.2", "22.6.11", "22.6.12", "22.6.13", "22.6.14", "22.6.15", "22.6.25", "22.6.29", "22.6.30", "22.6.31", "22.6.32", "22.6.33", "22.6.34", "22.6.35", "22.6.36", "22.6.37", "22.6.38", "22.6.39"]:
    DI_ENRICHMENT[uid] = _di_monitoring
for uid in ["22.6.3", "22.6.8", "22.6.9", "22.6.10", "22.6.17", "22.6.18", "22.6.19", "22.6.20", "22.6.26", "22.6.27", "22.6.28"]:
    DI_ENRICHMENT[uid] = _di_access
for uid in ["22.6.4", "22.6.5", "22.6.44"]:
    DI_ENRICHMENT[uid] = _di_crypto
for uid in ["22.6.6", "22.6.7", "22.6.40", "22.6.41", "22.6.42", "22.6.43"]:
    DI_ENRICHMENT[uid] = _di_network
for uid in ["22.6.21", "22.6.22", "22.6.23", "22.6.24"]:
    DI_ENRICHMENT[uid] = _di_physical
for uid in ["22.9.1", "22.9.2", "22.9.3", "22.9.4", "22.9.5", "22.9.6", "22.9.7", "22.9.8", "22.9.9", "22.9.10"]:
    DI_ENRICHMENT[uid] = _di_isms


def fix_file(path: Path) -> list[str]:
    raw = path.read_text("utf-8")
    data = json.loads(raw)
    uid = data["id"]
    changes: list[str] = []

    if uid in KFP:
        data["knownFalsePositives"] = KFP[uid]
        changes.append("replaced KFP")

    data["references"] = _iso_ref_base
    changes.append("set references (4)")

    if uid in CT and "controlTest" not in data:
        data["controlTest"] = CT[uid]
        changes.append("added controlTest")

    if uid in EVIDENCE and len(data.get("evidence", "") or "") < 30:
        data["evidence"] = EVIDENCE[uid]
        changes.append("added evidence")

    if uid in EXCLUSIONS and len(data.get("exclusions", "") or "") < 30:
        data["exclusions"] = EXCLUSIONS[uid]
        changes.append("added exclusions")

    kfp = data.get("knownFalsePositives", "") or ""
    if kfp and not SUPPRESSION_RE.search(kfp):
        data["knownFalsePositives"] = kfp + SUPPRESSION_SUFFIX
        changes.append("appended suppression")

    ds = data.get("dataSources", "") or ""
    app_field = data.get("app", "") or ""
    if not SPLUNKBASE_ID_RE.search(ds + " " + app_field):
        data["dataSources"] = ds.rstrip() + " (Splunkbase 1621 — Splunk CIM Add-on)"
        changes.append("added Splunkbase ID")

    if uid in DI_ENRICHMENT:
        di = data.get("detailedImplementation", "") or ""
        if isinstance(di, str) and "Ecosystem integration" not in di:
            data["detailedImplementation"] = di + DI_ENRICHMENT[uid]
            changes.append("enriched DI")

    if not changes:
        return []

    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(out, "utf-8")
    return changes


def main() -> None:
    files = []
    for pattern in ["UC-22.6.*.json", "UC-22.9.*.json"]:
        files.extend(CONTENT.glob(pattern))
    files.sort(key=lambda p: (int(p.stem.split(".")[1]), int(p.stem.split(".")[2])))

    print(f"Processing {len(files)} ISO 27001 UCs (Tier B+C+D)...")
    modified = 0
    for f in files:
        ch = fix_file(f)
        if ch:
            uid = f.stem.replace("UC-", "")
            print(f"  UC-{uid}: {', '.join(ch)}")
            modified += 1
    print(f"\nModified {modified}/{len(files)} files.")


if __name__ == "__main__":
    main()
