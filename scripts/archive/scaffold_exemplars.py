#!/usr/bin/env python3
"""scripts/archive/scaffold_exemplars.py — Phase 1.6 authoring driver.

Emits the 40 exemplar use cases that populate the 15 cross-regulation mini-
categories (22.35 - 22.49). The script is the single source of truth for the
authoring tuples; it writes:

1. ``use-cases/cat-22/uc-22.NN.N.json`` — JSON sidecars with full structured
   ``compliance[]`` + ``controlTest`` blocks (schema-validated).
2. ``use-cases/cat-22-regulatory-compliance.md`` — appends 15 subcategory
   headings and the canonical markdown for each UC so the catalogue /
   website picks them up.

The Phase 1.6 authoring pass is **complete**; this script lives under
``scripts/archive/`` for audit-replay only.

.. WARNING:: Destructive when run with ``--write``.

   The on-disk sidecars and Phase 1.6 markdown block have been **enriched**
   since the original scaffold (e.g. ``derived-from-parent`` compliance
   entries seeded by Phase 2.x generators, hand-applied SME edits). Re-
   running the scaffold with ``--write`` will silently drop those
   enrichments.

   The default mode is ``--check``: the script renders the expected sidecars
   and markdown block in memory and reports a unified diff vs the on-disk
   files. Use that to inspect intent without modifying anything.

Security note (codeguard-0-input-validation-injection + no-hardcoded-credentials):
this script writes static, curated content. It performs no shell execution,
no dynamic regex compilation, and reads no user-supplied files outside the
repo tree. All UC IDs, titles, SPL, and compliance tuples are hand-reviewed
constants.
"""

from __future__ import annotations

import argparse
import difflib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
SIDECAR_DIR = ROOT / "use-cases" / "cat-22"
MARKDOWN_PATH = ROOT / "use-cases" / "cat-22-regulatory-compliance.md"
FIXTURE_DIR = ROOT / "sample-data"

BEGIN_SENTINEL = "<!-- PHASE-1.6 BEGIN -->"
END_SENTINEL = "<!-- PHASE-1.6 END -->"

CRITICALITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
DIFFICULTY_EMOJI = {"beginner": "🟢", "intermediate": "🔵", "advanced": "🟠", "expert": "🔴"}


def _as_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


# ---------------------------------------------------------------------------
# Common reference URL helpers (static; no interpolation of user data).
# ---------------------------------------------------------------------------
REF = {
    "gdpr": ("https://eur-lex.europa.eu/eli/reg/2016/679/oj", "Regulation (EU) 2016/679 — GDPR"),
    "hipaa": ("https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164", "45 CFR Part 164 — HIPAA"),
    "pci": ("https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf", "PCI DSS v4.0"),
    "soc2": ("https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022", "AICPA Trust Services Criteria"),
    "soxitgc": ("https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201", "PCAOB AS 2201"),
    "iso27001": ("https://www.iso.org/standard/82875.html", "ISO/IEC 27001:2022"),
    "nistcsf": ("https://www.nist.gov/cyberframework", "NIST Cybersecurity Framework 2.0"),
    "nist80053": ("https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final", "NIST SP 800-53 Rev. 5"),
    "nis2": ("https://eur-lex.europa.eu/eli/dir/2022/2555/oj", "Directive (EU) 2022/2555 — NIS2"),
    "dora": ("https://eur-lex.europa.eu/eli/reg/2022/2554/oj", "Regulation (EU) 2022/2554 — DORA"),
    "ccpa": ("https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV&division=3.&title=1.81.5.&part=4.&chapter=&article=", "California Consumer Privacy Act (CCPA/CPRA)"),
    "nerc": ("https://www.nerc.com/pa/Stand/Reliability%20Standards%20Complete%20Set/RSCompleteSet.pdf", "NERC Reliability Standards — CIP"),
}


def _ref(*keys: str, extra: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for k in keys:
        url, title = REF[k]
        out.append({"url": url, "title": title, "retrieved": "2026-04-16"})
    if extra:
        out.extend(extra)
    return out


# ---------------------------------------------------------------------------
# The 40 exemplar definitions.
#
# Each entry has the authoring fields we care about; rendering fills defaults.
# Only fields listed here become part of the sidecar/markdown.
# ---------------------------------------------------------------------------
SUBCATEGORIES = [
    {
        "id": "22.35",
        "name": "Evidence continuity and log integrity",
        "primary_app_ta": "Splunk Enterprise / Splunk Cloud Platform (native _internal metrics), Splunk Enterprise Security (263) for notables, Splunk ITSI (1841) for service health.",
        "data_sources": "_internal metrics.log (group=per_sourcetype_thruput, group=per_index_thruput), _audit, indexer cluster replication telemetry, KMS audit events, WORM bucket lifecycle events.",
    },
    {
        "id": "22.36",
        "name": "Data subject rights fulfillment",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk App for Data Privacy / DSAR workflow connectors, Splunk Add-on for Salesforce (2882), Splunk Add-on for ServiceNow (1928).",
        "data_sources": "DSAR ticketing system (ServiceNow, OneTrust, TrustArc), CRM deletion job logs, ETL / DWH deletion manifests, portability export audit logs.",
    },
    {
        "id": "22.37",
        "name": "Consent lifecycle and lawful basis",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for OneTrust / TrustArc / Cookiebot, Splunk Common Information Model Add-on (1621).",
        "data_sources": "Consent management platform (CMP) event streams, IdP tokens carrying consent claims, application-level consent audit logs, Global Privacy Control signal telemetry.",
    },
    {
        "id": "22.38",
        "name": "Cross-border transfer controls",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for AWS (1876) / Azure (3110) / GCP (3088), Splunk Stream / CIM Network Traffic.",
        "data_sources": "VPC / NSG / cloud-egress flow logs, storage-replication audit logs, DLP email/cloud egress events, DPA/SCC register lookups.",
    },
    {
        "id": "22.39",
        "name": "Incident notification timeliness",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk SOAR (1717), Splunk Add-on for ServiceNow (1928), Splunk ITSI (1841).",
        "data_sources": "SIEM notable events (ES), SOAR case audit logs, regulator-portal submission APIs, email/comms delivery receipts.",
    },
    {
        "id": "22.40",
        "name": "Privileged access evidence",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for CyberArk (4295) / BeyondTrust / Delinea, Splunk UBA (4976).",
        "data_sources": "PAM vault audit logs, session-recording metadata, IdP PIM/PAM activation events, break-glass account usage logs.",
    },
    {
        "id": "22.41",
        "name": "Encryption and key management attestation",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for AWS KMS / Azure Key Vault / GCP KMS, Splunk Add-on for F5 (2776) / load balancers.",
        "data_sources": "KMS/HSM audit logs, TLS cert-inventory scanners, cloud storage encryption-configuration APIs, vulnerability scanner weak-cipher findings.",
    },
    {
        "id": "22.42",
        "name": "Change management and configuration baseline",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for ServiceNow Change Management (1928), Splunk Add-on for Ansible Tower / Terraform.",
        "data_sources": "ITSM change records, CI/CD pipeline audit logs, host configuration-drift scanners (Tripwire, CIS-CAT, osquery), CM baseline lookups.",
    },
    {
        "id": "22.43",
        "name": "Vulnerability management and patch SLAs",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for Tenable (5099) / Qualys (2919) / Rapid7 (2985), Splunk Vulnerability data model.",
        "data_sources": "Vulnerability scanner findings, patch-management agent events (SCCM, Intune, JAMF, BigFix), CVE feeds.",
    },
    {
        "id": "22.44",
        "name": "Third-party and supply-chain risk",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for OneTrust Vendorpedia / ServiceNow VRM, Splunk Cloud Compliance Assistant.",
        "data_sources": "Vendor risk management (VRM) attestation records, SBOM ingestion, subprocessor registers, fourth-party dependency graphs.",
    },
    {
        "id": "22.45",
        "name": "Backup integrity and recovery testing",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for Veeam (4182) / Commvault / Rubrik / NetBackup, Splunk ITSI (1841).",
        "data_sources": "Backup job logs, restore-test audit logs, immutable/air-gapped storage lifecycle events, checksum verification outputs.",
    },
    {
        "id": "22.46",
        "name": "Training and awareness",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for KnowBe4 (5039) / Proofpoint Security Awareness, Splunk Add-on for ServiceNow (1928).",
        "data_sources": "LMS completion events, phishing-simulation campaign results, HR roster lookups, role-based training catalog.",
    },
    {
        "id": "22.47",
        "name": "Control testing evidence freshness",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk App for PCI Compliance (2897), Splunk Add-on for ServiceNow GRC (1928).",
        "data_sources": "GRC control-test audit logs, internal-audit evidence-request workflow, control-owner attestation ledger, evidence-pack build manifests.",
    },
    {
        "id": "22.48",
        "name": "Segregation of duties enforcement",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for SAP (6006) / Oracle / Workday, Splunk UBA (4976).",
        "data_sources": "ERP / HRIS role-assignment audit logs, IdP group-membership changes, SOX-ITGC toxic-combination lookups.",
    },
    {
        "id": "22.49",
        "name": "Retention and disposal automation",
        "primary_app_ta": "Splunk Enterprise Security (263), Splunk Add-on for AWS S3 (1876) / Azure Blob / GCS, Splunk Add-on for Commvault / Varonis.",
        "data_sources": "Object-store lifecycle events, database TTL job logs, litigation-hold registry changes, data-classification engine outputs.",
    },
]


UCS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------
    # 22.35 Evidence continuity and log integrity
    # 22.35.1 existed before Phase 1.6; its authoritative sidecar lives at
    # use-cases/cat-22/uc-22.35.1.json. We replay the key fields here so
    # the markdown block shows all three UCs together. ``markdown_only`` is
    # set so _write_sidecar does NOT overwrite the pre-existing sidecar.
    # -----------------------------------------------------------------
    {
        "id": "22.35.1",
        "markdown_only": True,
        "title": "Audit-log continuity: detect indexing gap indicating lost evidence",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "CISO",
        "control_family": "evidence-continuity",
        "exclusions": "Does NOT detect confidentiality compromise of log content itself, nor physical tampering of the indexer host; see UC-22.35.2 (indexer integrity) and UC-22.35.3 (log-content confidentiality).",
        "evidence": "Saved search 'audit_log_gap_detection' (daily) outputs a per-source gap report to the compliance summary index; dashboard panel 'Audit log continuity — last 30d' on the evidence-pack dashboard.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32(1)(b)", "mode": "satisfies", "assurance": "partial", "assurance_rationale": "Detects interruption of the audit trail but the clause also requires confidentiality/integrity guarantees not covered here."},
            {"regulation": "HIPAA", "version": "2013-final", "clause": "§164.312(b)", "mode": "satisfies", "assurance": "full", "assurance_rationale": "§164.312(b) 'Audit controls' is satisfied when the covered entity can show audit logs are captured continuously."},
            {"regulation": "PCI-DSS", "version": "v4.0", "clause": "10.2.1", "mode": "satisfies", "assurance": "partial", "assurance_rationale": "PCI 10.2.1 requires audit logs enabled; this UC detects loss of telemetry but not 10.2.1.1-10.2.1.7 sub-requirements."},
            {"regulation": "SOC-2", "version": "2017 TSC", "clause": "CC7.2", "mode": "satisfies", "assurance": "partial", "assurance_rationale": "CC7.2 requires monitoring to detect anomalies; gap detection is one necessary signal."},
            {"regulation": "SOX-ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.Logging.Continuity", "mode": "detects-violation-of", "assurance": "contributing", "assurance_rationale": "Unexplained audit gaps are a material ITGC finding; this UC surfaces the signal."},
        ],
        "control_test": {
            "positiveScenario": "When any ingest source known to produce continuous events stops producing events for more than 60 seconds (and no planned-maintenance window is active), the UC fires within the next search interval and names the affected source.",
            "negativeScenario": "Normal event-rate jitter (up to 30-second gaps), or a source in a pre-declared maintenance window (tag=maintenance), does NOT fire the UC.",
            "fixtureRef": "sample-data/uc-22.35.1-fixture.json",
            "attackTechnique": "T1562.008",
        },
        "data_sources": "_internal metrics.log (group=per_sourcetype_thruput), _audit (action=indexing), or any index-time metric that exposes per-source event rates.",
        "app": "Splunk Enterprise / Splunk Cloud Platform (native; no separate TA required)",
        "spl": "| tstats count as events where index=_internal source=*metrics.log* group=per_sourcetype_thruput earliest=-30m by sourcetype _time span=1m\n| eventstats avg(events) as avg_events, stdev(events) as stdev_events by sourcetype\n| where events=0 AND avg_events>0\n| eval gap_seconds=60\n| table _time sourcetype events avg_events stdev_events gap_seconds\n| sort - _time",
        "description": "Detects any sourcetype that was previously producing events but has stopped indexing for more than a rolling 60-second window. A regression in event ingestion is the earliest indicator that the audit trail required by almost every modern regulation has been compromised.",
        "value": "Without continuous audit logs, compliance claims are unfalsifiable. Auditors across GDPR, HIPAA, PCI DSS, SOC 2, and SOX all treat log-gaps as a finding.",
        "implementation": "(1) Schedule every 5 minutes; (2) route hits to a restricted summary index (compliance_summary); (3) wire to ITSI service health or ES notable depending on deployment; (4) maintain a maintenance-window lookup (maintenance_windows.csv).",
        "visualization": "Timeline of event rate per sourcetype with red bars for gap periods; heat-map of sources-by-day with green/amber/red cells; single value for '% of last 30d with full coverage'.",
        "references": _ref("gdpr", "hipaa", "pci", extra=[
            {"url": "https://attack.mitre.org/techniques/T1562/008/", "title": "MITRE ATT&CK — T1562.008 Impair Defenses: Disable or Modify Cloud Logs", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Planned maintenance windows or expected cold-standby sources that receive low volume. Mitigate with a maintenance_windows.csv lookup and a `not source IN [$lookup]` clause.",
        "mitre": ["T1562.008"],
        "detection_type": "Anomaly",
        "security_domain": "audit",
    },
    {
        "id": "22.35.2",
        "title": "Log tamper detection via write-once-read-many chain-of-custody",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "CISO",
        "control_family": "evidence-continuity",
        "exclusions": "Does NOT detect insider exfiltration of log content or modifications outside the WORM store; see UC-22.35.3 (replication) and UC-22.41.3 (KMS rotation).",
        "evidence": "Saved search 'worm_chain_of_custody' runs every 15 minutes and writes hash-chain verification results to the compliance_summary index; dashboard 'Audit log tamper evidence — 30d' surfaces any unverified buckets.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32",
             "clauseUrl": "https://eur-lex.europa.eu/eli/reg/2016/679/oj#d1e2833-1-1",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.32 requires 'integrity ... of processing systems'; cryptographic hash-chain verification of audit storage is one of the standard technical measures cited by EDPB guidance on log integrity."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.312(c)(1)",
             "clauseUrl": "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312#p-164.312(c)(1)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.312(c)(1) Integrity requires mechanisms to corroborate that ePHI has not been altered. Hash-chain verification over the audit store is a direct implementation."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "10.5",
             "clauseUrl": "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf#page=131",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "PCI 10.5 requires audit-log integrity controls; WORM + hash-chain is explicitly called out as an acceptable method in the v4.0 Guidance."},
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "CC7.2",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "CC7.2 covers anomaly detection; log-integrity verification contributes to the evaluated-events program but additional processing controls apply."},
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.Logging.Continuity",
             "mode": "detects-violation-of", "assurance": "contributing",
             "assurance_rationale": "A broken hash chain in an audit period is a material ITGC exception; this UC surfaces the signal and writes it to the audit-evidence index."},
        ],
        "control_test": {
            "positiveScenario": "When an indexer's primary bucket hash ceases to match the replicated peer's hash, the UC fires within one search interval and records the bucket_id, index, and divergence timestamp.",
            "negativeScenario": "During normal hot-to-warm rolling (which re-hashes but preserves chain continuity) the UC does NOT fire.",
            "fixtureRef": "sample-data/uc-22.35.2-fixture.json",
            "attackTechnique": "T1070",
        },
        "spl": "| rest /services/cluster/master/buckets splunk_server=* | eval primary_hash=coalesce('primaries{}.bucket_flags.hash','bucket_hash') | stats values(primary_hash) as hashes dc(primary_hash) as uniques by index, bucket_id | where uniques>1\n| eval divergence_detected_at=strftime(now(),\"%Y-%m-%dT%H:%M:%SZ\")\n| table divergence_detected_at index bucket_id hashes",
        "description": "Compares the cryptographic bucket hash across indexer peer nodes and raises a finding whenever the primary and its replicas disagree. A divergence is the earliest evidence of on-disk tampering or a replication-layer fault — both of which break the audit chain-of-custody that GDPR, HIPAA, PCI DSS, SOC 2, and SOX ITGC assume.",
        "value": "Produces defensible chain-of-custody evidence: auditors can be shown a 30-day view in which every bucket was either green or had a timestamped remediation ticket.",
        "implementation": "(1) Enable indexer-cluster replication with searchFactor≥2, replicationFactor≥3; (2) schedule the REST probe every 5 minutes; (3) pipe hits to compliance_summary and to ITSI as a KPI; (4) escalate to CISO on any bucket divergence older than 30 minutes.",
        "visualization": "Heat-map of indexes × buckets over 30d (green/red); single value for '% of buckets verified'; time-chart of open divergences.",
        "references": _ref("gdpr", "hipaa", "pci", "soc2", extra=[
            {"url": "https://attack.mitre.org/techniques/T1070/", "title": "MITRE ATT&CK — T1070 Indicator Removal", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Planned rolling restarts of indexer peers can briefly show hash mismatches during re-balancing. Use maintenance_windows.csv and a 10-minute grace window.",
        "mitre": ["T1070"],
        "detection_type": "Anomaly",
        "security_domain": "audit",
    },
    {
        "id": "22.35.3",
        "title": "Indexer replication lag exposing evidence to single-point failure",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Operational"],
        "splunk_pillar": "Platform",
        "owner": "Head of Platform",
        "control_family": "evidence-continuity",
        "exclusions": "Does NOT evaluate content confidentiality or tamper at rest (UC-22.35.2); focuses on replication SLO only.",
        "evidence": "Daily saved search writes indexer replication-lag stats to compliance_summary with an SLA gauge; evidence-pack dashboard panel 'Replication SLO — last 90d'.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.32(1)(c) requires 'the ability to restore the availability and access to personal data in a timely manner'; replication lag is a leading indicator."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.12",
             "clauseUrl": "https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.12 requires backup policies and recovery methods with tested RPO; this UC alerts when replication RPO is exceeded in flight."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "AU-9",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "AU-9 requires protection of audit information from unauthorized access, modification, and deletion; replication is a standard enhancement for AU-9(2)."},
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "A1.2",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "A1.2 covers availability commitments; replication lag monitoring is one input."},
        ],
        "control_test": {
            "positiveScenario": "When replication lag across any index exceeds the configured RPO (default 5 minutes) for more than two consecutive search intervals, the UC fires and lists affected indexes with their lag in seconds.",
            "negativeScenario": "Transient spikes (up to 90 seconds) during hot-bucket roll do NOT fire.",
            "fixtureRef": "sample-data/uc-22.35.3-fixture.json",
        },
        "spl": "| rest /services/cluster/master/indexes splunk_server=* | stats max(replication_factor_met) as rf_met max(search_factor_met) as sf_met by title | eval index=title, rf_met=coalesce(rf_met,0), sf_met=coalesce(sf_met,0) | where rf_met=0 OR sf_met=0",
        "description": "Polls indexer cluster topology and raises a finding whenever replication-factor or search-factor is not met. Because auditors treat a single-replica audit trail as equivalent to no audit trail, a sustained lag above the stated RPO breaks the compliance claim.",
        "value": "Turns an otherwise-silent SLO breach into evidence that the control was monitored continuously, even across shards that never had an incident.",
        "implementation": "(1) Schedule hourly; (2) parameterise RPO via macro `worm_rpo_seconds`; (3) correlate with maintenance-window lookup to suppress planned reboots; (4) wire to ITSI availability KPI for cross-pillar visibility.",
        "visualization": "Line chart of replication lag by index; table of out-of-SLA indexes with duration; single-value for '% of time within RPO'.",
        "references": _ref("dora", "nist80053", "soc2"),
        "known_fp": "Planned rolling restarts, primary-peer failovers, or newly-added indexes (before first replication cycle) can briefly show lag. Apply maintenance-window suppression.",
        "mitre": [],
        "detection_type": "Anomaly",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.36 Data subject rights fulfillment (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.36.1",
        "title": "DSAR fulfillment SLA tracker with verification evidence trail",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-subject-request-lifecycle",
        "exclusions": "Does NOT detect incomplete returns (scope-gap); pair with UC-22.36.2 for erasure propagation.",
        "evidence": "Daily report 'dsar_sla_tracker' writes per-ticket status (received/verified/responded/fulfilled) to compliance_summary; Glass Table panel shows funnel with aging.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.15",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.15 right of access requires fulfilment 'without undue delay and in any event within one month' (Art.12(3)); SLA tracker measures this directly with verifiable timestamps."},
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.12",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.12 governs transparent communication; the UC evidences that the response SLA was met and identifies the exceptions."},
            {"regulation": "CCPA/CPRA", "version": "CPRA (as amended)", "clause": "§1798.100",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§1798.100 gives consumers the right to request the categories/specific pieces of PI a business has collected; CCPA requires a 45-day response with one 45-day extension — the SLA tracker is direct evidence of compliance."},
        ],
        "control_test": {
            "positiveScenario": "When a DSAR ticket crosses the 25-day mark without a 'verified' transition, the UC fires and lists the ticket_id, data subject token, and days_open.",
            "negativeScenario": "Tickets within their SLA window, or tickets on a lawfully-extended clock (Art.12(3)) with an approved extension in the lookup, do NOT fire.",
            "fixtureRef": "sample-data/uc-22.36.1-fixture.json",
        },
        "spl": "index=dsar sourcetype=onetrust:dsar OR sourcetype=servicenow:privacy earliest=-90d\n| stats min(_time) as received max(eval(case(status=\"verified\",_time))) as verified max(eval(case(status=\"fulfilled\",_time))) as fulfilled by ticket_id subject_token\n| eval days_open=round((coalesce(fulfilled,now())-received)/86400,1), sla_breach=if(isnull(fulfilled) AND days_open>25,1,0)\n| where sla_breach=1\n| table ticket_id subject_token received verified days_open",
        "description": "Produces per-ticket SLA evidence for every data-subject access / deletion / portability request. Tickets that approach the statutory response window are surfaced so the DPO can intervene; tickets that breached are logged to the evidence pack with clear root cause.",
        "value": "Replaces the common 'DPO exports a CSV from OneTrust' evidence pattern with a continuously-measured, tamper-evident record that directly supports auditor questions about Art.12/Art.15 response timeliness.",
        "implementation": "(1) Ingest the DSAR platform (OneTrust, TrustArc, ServiceNow Privacy) via its API; (2) join to an `extensions.csv` for legitimately extended tickets; (3) alert to DPO when breach is imminent; (4) emit KPI to ITSI privacy service.",
        "visualization": "Funnel (received → verified → responded → fulfilled), aging bar chart, single-value for '% of DSARs fulfilled within SLA (90d)'.",
        "references": _ref("gdpr", "ccpa"),
        "known_fp": "Legitimately extended requests (Art.12(3)) look like SLA breaches unless the extension_approved_on field in extensions.csv is populated.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.36.2",
        "title": "Right-to-erasure propagation completeness across downstream systems",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-subject-request-lifecycle",
        "exclusions": "Does NOT validate erasure from third-party processors (see UC-22.44.1) or legitimately-retained records under Art.17(3) exceptions.",
        "evidence": "Saved search 'erasure_propagation_gap' runs hourly and writes system-by-system deletion evidence to compliance_summary; evidence-pack report per erasure request.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.17",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.17 right to erasure requires that the data be erased 'without undue delay'. The UC tracks completion across every downstream system listed in the ROPA."},
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.17(2)",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.17(2) requires reasonable measures to inform third parties; this UC surfaces the subset of third-party processors that acknowledged the erasure, but the DPO must verify the remainder manually."},
            {"regulation": "CCPA/CPRA", "version": "CPRA (as amended)", "clause": "§1798.105",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§1798.105 consumer right to delete; the UC tracks deletion across every system registered in the business's consumer-facing record."},
        ],
        "control_test": {
            "positiveScenario": "When an erasure ticket is closed but at least one registered downstream system has no deletion_ack within 7 days, the UC fires naming the subject_token and the system(s) missing the ack.",
            "negativeScenario": "Systems covered by a lawful-retention exception (retention_hold=true in erasure_exceptions.csv) do NOT fire.",
            "fixtureRef": "sample-data/uc-22.36.2-fixture.json",
        },
        "spl": "index=dsar subject_token=* action=erasure earliest=-180d\n| stats values(system) as acked_systems by subject_token ticket_id\n| lookup ropa_system_map.csv ticket_id OUTPUT systems_in_scope\n| eval missing=mvfilter(NOT match(acked_systems, system))\n| where mvcount(missing)>0\n| table ticket_id subject_token systems_in_scope acked_systems missing",
        "description": "Enforces that every registered downstream system reports a deletion acknowledgement for each accepted erasure request within seven days. A subject_token that persists past the SLA in any system is a direct Art.17 / CPRA §1798.105 finding.",
        "value": "Moves the erasure claim from 'we believe it propagated' to 'we proved it propagated, system by system' — exactly the evidence supervisory authorities ask for on first inspection.",
        "implementation": "(1) Publish a ropa_system_map.csv lookup keyed by ticket_id → list of systems-in-scope; (2) ingest deletion-ack events from each system (DB TTL jobs, DWH deletion manifests, app-level hooks); (3) run hourly; (4) integrate with SOAR to auto-reopen tickets with missing acks.",
        "visualization": "Matrix of ticket_id × system with green/red cells; aging histogram; single-value for 'in-scope systems with ack in SLA'.",
        "references": _ref("gdpr", "ccpa"),
        "known_fp": "Systems that hold data under a legitimate retention obligation (tax law, medical records) will 'miss' an ack. Use erasure_exceptions.csv to exclude them per ticket.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.36.3",
        "title": "Portability export integrity — signed manifest verification",
        "criticality": "medium",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-subject-request-lifecycle",
        "exclusions": "Does NOT verify whether the export format is machine-readable (Art.20 — format scoring is a content review handled outside Splunk).",
        "evidence": "Hourly search 'portability_manifest_verify' hashes each portability export bundle and cross-checks against the signed manifest stored in compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.20",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.20 grants the right to receive 'in a structured, commonly used and machine-readable format'; the UC verifies export integrity so the bundle the subject receives matches what was generated."},
        ],
        "control_test": {
            "positiveScenario": "When a portability export bundle's SHA-256 does not match its signed manifest at delivery time, the UC fires naming the export_id, the subject_token, and the divergent hash.",
            "negativeScenario": "Normal re-hashing during CDN-assisted delivery (content-encoding=gzip) where the manifest carries the pre-compression hash does NOT fire.",
            "fixtureRef": "sample-data/uc-22.36.3-fixture.json",
        },
        "spl": "index=dsar sourcetype=portability:export action=delivered earliest=-30d\n| join export_id [search index=dsar sourcetype=portability:manifest | fields export_id, manifest_hash]\n| where delivered_hash!=manifest_hash\n| table _time export_id subject_token delivered_hash manifest_hash",
        "description": "Validates that the bytes delivered to a data subject match the signed manifest produced when the export was generated. Any divergence is evidence of in-transit tampering or a broken CDN path; either way the export cannot be trusted as a lawful Art.20 response.",
        "value": "Adds cryptographic evidence to what is otherwise a 'we generated the file' audit trail.",
        "implementation": "(1) Sign manifests at export time with an HSM key scoped to the privacy program; (2) log manifest_hash and delivered_hash at each delivery; (3) run hourly; (4) on hit, auto-open an Art.12 remediation ticket.",
        "visualization": "Table of failures, single-value for '% verified (30d)', time chart of failures.",
        "references": _ref("gdpr"),
        "known_fp": "Content encoding transforms can change the on-wire hash. Require manifest to record pre-compression hash and compare apples to apples.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.37 Consent lifecycle and lawful basis (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.37.1",
        "title": "Consent capture evidence freshness — stale-consent alerting",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-subject-request-lifecycle",
        "exclusions": "Does NOT evaluate whether the consent text itself meets Art.7 transparency — that is a legal review, handled outside the platform.",
        "evidence": "Daily 'consent_freshness' search writes per-subject consent age and scope to compliance_summary; panel shows distribution of consent ages by lawful basis.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.7",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.7 conditions for consent — the UC evidences when consent was captured and surfaces subjects whose consent is older than the policy threshold."},
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.6",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.6(1)(a) lawful basis of consent requires demonstrable consent. Missing or stale evidence means no lawful basis."},
        ],
        "control_test": {
            "positiveScenario": "When a subject's active consent grant is older than the configured max_consent_age_days (default 365) and the processing activity is still observed in application logs, the UC fires.",
            "negativeScenario": "Processing activities with lawful basis ≠ consent (e.g. Art.6(1)(c) legal obligation) do NOT fire.",
            "fixtureRef": "sample-data/uc-22.37.1-fixture.json",
        },
        "spl": "index=cmp sourcetype=onetrust:consent earliest=-400d\n| stats max(_time) as last_consent by subject_token purpose\n| eval consent_age_days=round((now()-last_consent)/86400,0)\n| where consent_age_days>365\n| join subject_token [search index=app_activity earliest=-30d | stats count by subject_token | where count>0]\n| table subject_token purpose last_consent consent_age_days",
        "description": "Flags subjects whose consent is older than the program threshold yet whose data is still being processed. Stale consent is a lawful-basis failure — Art.6/Art.7 require consent to remain current and demonstrable.",
        "value": "Prevents the 'set-and-forget' consent anti-pattern that surfaces in nearly every GDPR supervisory-authority enforcement action.",
        "implementation": "(1) Ingest CMP events with purpose taxonomy; (2) set max_consent_age_days via macro; (3) run daily; (4) pipe to SOAR to drive a re-consent workflow.",
        "visualization": "Histogram of consent age by purpose; table of stale subjects; single-value for '% of processing with fresh consent'.",
        "references": _ref("gdpr"),
        "known_fp": "Long-lived contractual relationships where consent is not the lawful basis. Use a lawful_basis.csv join to filter them out.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.37.2",
        "title": "Consent withdrawal propagation SLA — downstream stop-processing evidence",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-subject-request-lifecycle",
        "exclusions": "Does NOT cover physical deletion (that is UC-22.36.2); focuses on stop-processing only.",
        "evidence": "Saved search 'consent_withdrawal_propagation' runs every 30 minutes and writes per-system stop-processing acks to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.7",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.7(3) requires that withdrawal of consent is as easy as giving it and must take effect without delay; the UC measures the system-by-system stop-processing latency."},
            {"regulation": "CCPA/CPRA", "version": "CPRA (as amended)", "clause": "§1798.100",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "CCPA §1798.100 and the GPC obligations under §1798.135 require honoring opt-outs promptly; propagation monitoring is necessary evidence."},
        ],
        "control_test": {
            "positiveScenario": "When a consent withdrawal is recorded but any in-scope downstream system continues to emit processing events for that subject after 24 hours, the UC fires naming the system and activity_type.",
            "negativeScenario": "Processing activities with lawful basis ≠ consent are NOT treated as withdrawal violations.",
            "fixtureRef": "sample-data/uc-22.37.2-fixture.json",
        },
        "spl": "index=cmp action=withdraw earliest=-7d\n| join subject_token [search index=app_activity (lawful_basis=consent) earliest=-7d]\n| where _time>=withdrawal_time + 86400\n| stats values(system) as systems_still_processing count by subject_token withdrawal_time\n| where count>0\n| table withdrawal_time subject_token systems_still_processing count",
        "description": "Cross-checks consent-withdrawal events against live processing telemetry. If a system continues to process a subject's data more than 24 hours after withdrawal, the UC raises a finding and opens a remediation task.",
        "value": "Withdrawals that do not propagate are a primary source of supervisory-authority enforcement; this UC turns a weak process control into a tested technical control.",
        "implementation": "(1) Instrument each consent-governed processing activity to emit subject_token and lawful_basis; (2) ingest withdrawals from the CMP; (3) run every 30 min; (4) on hit, open a SOAR case with the system owner.",
        "visualization": "Matrix of system × withdrawal-breach count (7d), single-value 'withdrawals propagated within 24h'.",
        "references": _ref("gdpr", "ccpa"),
        "known_fp": "Systems that process under non-consent lawful bases must emit the correct lawful_basis value; unmapped systems can appear as FPs.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.37.3",
        "title": "Global Privacy Control (GPC) signal honoring — server-side audit",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-subject-request-lifecycle",
        "exclusions": "Does NOT evaluate first-party ad-tech placement quality; focuses on sale/share opt-out honoring.",
        "evidence": "Hourly report 'gpc_honor_audit' writes per-session GPC signal + sale/share decision to compliance_summary.",
        "compliance": [
            {"regulation": "CCPA/CPRA", "version": "CPRA (as amended)", "clause": "§1798.135",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§1798.135(b) and CCPA Regs §7025 require honoring Global Privacy Control signals as valid opt-out signals. The UC audits every web session."},
        ],
        "control_test": {
            "positiveScenario": "When an inbound web request carries Sec-GPC: 1 but a downstream ad-tech call fires within the same session, the UC fires naming the session_id, the ad-tech partner, and the endpoint.",
            "negativeScenario": "Sessions without GPC and no opt-out cookie do NOT fire.",
            "fixtureRef": "sample-data/uc-22.37.3-fixture.json",
        },
        "spl": "index=web sourcetype=access_combined earliest=-24h\n| rex field=_raw \"Sec-GPC:\\s*(?<gpc>\\d)\"\n| where gpc=1\n| join session_id [search index=web sourcetype=adtech_call earliest=-24h | stats count by session_id vendor endpoint]\n| table session_id vendor endpoint count",
        "description": "Audits compliance with the Global Privacy Control signal. For any session that carried GPC=1, any subsequent third-party ad-tech call is a direct CCPA §7025 violation that must appear in the annual privacy report.",
        "value": "Automates the evidence collection California AG investigations have asked for in recent settlements (Sephora, DoorDash).",
        "implementation": "(1) Ensure `Sec-GPC` is preserved in access logs; (2) list regulated ad-tech partners in an allowlist; (3) run hourly; (4) pipe to privacy-metric KPI.",
        "visualization": "Table of violating sessions, vendor bar chart, single-value 'sessions honoring GPC (24h)'.",
        "references": _ref("ccpa"),
        "known_fp": "Essential functional third parties (payment, fraud) are not 'sale/share'. Allowlist via gpc_exempt_vendors.csv.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.38 Cross-border transfer controls (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.38.1",
        "title": "Cross-border personal-data flow anomaly — egress to unsanctioned jurisdictions",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-flow-cross-border",
        "exclusions": "Does NOT detect transfer purpose (legitimate-interest balancing); focuses on geographic egress only.",
        "evidence": "Saved search 'cross_border_egress_anomaly' runs every 15 min and writes sanctioned/unsanctioned egress stats to compliance_summary; Glass Table 'International transfers map'.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.44",
             "mode": "detects-violation-of", "assurance": "full",
             "assurance_rationale": "Art.44 prohibits transfers to third countries absent Art.45/46/49 safeguards; the UC detects egress to jurisdictions not on the adequacy list or SCC register."},
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.46",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.46 Standard Contractual Clauses — the UC evidences that transfers only occur to destinations registered as SCC-covered."},
        ],
        "control_test": {
            "positiveScenario": "When PII-classified data egresses to a destination IP whose geolocation is not on the sanctioned_transfer_jurisdictions.csv list, the UC fires naming the source system, destination country, and PII classification.",
            "negativeScenario": "Traffic within the EEA or to adequacy-decision jurisdictions with active SCCs does NOT fire.",
            "fixtureRef": "sample-data/uc-22.38.1-fixture.json",
            "attackTechnique": "T1567.002",
        },
        "spl": "| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic where All_Traffic.tag=egress earliest=-1h by All_Traffic.dest, All_Traffic.src, All_Traffic.bytes_out\n| `get_geolocation(dest)`\n| lookup sanctioned_transfer_jurisdictions.csv country as dest_country OUTPUT scc_active adequacy_decision\n| where isnull(scc_active) AND isnull(adequacy_decision)\n| join src [search index=dlp tag=pii | stats values(classification) as pii_class by src]\n| table _time src dest dest_country pii_class bytes_out",
        "description": "Joins CIM Network_Traffic egress telemetry with DLP PII classification and a sanctioned-jurisdictions lookup. Any transfer of PII-classified traffic to a non-sanctioned destination is a direct Art.44 finding.",
        "value": "Operationalises a control that is otherwise verifiable only via quarterly desk review of the transfer register.",
        "implementation": "(1) Ensure DLP emits CIM-compatible PII classification; (2) maintain sanctioned_transfer_jurisdictions.csv driven by the Art.45 adequacy list and the SCC register; (3) schedule every 15 min; (4) escalate via SOAR to DPO.",
        "visualization": "World-map of egress flows (green=sanctioned, red=finding), table of findings, single-value 'transfers in sanctioned geographies'.",
        "references": _ref("gdpr", extra=[
            {"url": "https://attack.mitre.org/techniques/T1567/002/", "title": "MITRE ATT&CK — T1567.002 Exfiltration to Cloud Storage", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Corporate VPN endpoints that present a destination IP in a non-sanctioned country can mis-geolocate; add vpn_exits.csv to suppress.",
        "mitre": ["T1567.002"],
        "detection_type": "Anomaly",
        "security_domain": "audit",
    },
    {
        "id": "22.38.2",
        "title": "SCC / adequacy decision reference freshness — stale-safeguard detector",
        "criticality": "medium",
        "difficulty": "beginner",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-flow-cross-border",
        "exclusions": "Does NOT evaluate the sufficiency of Article-28 DPAs; see UC-22.44.2.",
        "evidence": "Daily 'scc_adequacy_freshness' writes stale-safeguard findings into compliance_summary; dashboard 'SCC inventory 90-day view'.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.46",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.46 requires appropriate safeguards; out-of-date SCCs (e.g. pre-2021 Module mismatches) are no longer appropriate and must be re-papered."},
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.45",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.45 adequacy decisions — the UC flags transfers that rely on a superseded or rescinded decision (e.g. Privacy Shield)."},
        ],
        "control_test": {
            "positiveScenario": "When an active transfer register entry points to an SCC version or adequacy decision published more than 36 months ago, or one marked 'rescinded' in the reference list, the UC fires.",
            "negativeScenario": "Entries that match an active SCC template or a current adequacy decision do NOT fire.",
            "fixtureRef": "sample-data/uc-22.38.2-fixture.json",
        },
        "spl": "| inputlookup transfer_register.csv\n| lookup scc_reference.csv template_id OUTPUT template_active effective_from superseded_by\n| eval age_days=round((now()-strptime(effective_from,\"%Y-%m-%d\"))/86400,0)\n| where NOT template_active OR age_days>1095 OR isnotnull(superseded_by)\n| table transfer_id destination template_id template_active age_days superseded_by",
        "description": "Cross-references the transfer register against the official SCC templates and the Art.45 adequacy register. Entries that rely on stale or rescinded safeguards appear immediately.",
        "value": "Prevents silent expiration of the legal basis for international transfers — the single most common finding in SCC-era enforcement.",
        "implementation": "(1) Maintain scc_reference.csv synced nightly against EDPB / Commission publications; (2) maintain transfer_register.csv as part of Art.30 ROPA; (3) run daily.",
        "visualization": "Stacked bar of active vs stale vs rescinded, table of findings, single-value '% of transfers with fresh safeguards'.",
        "references": _ref("gdpr"),
        "known_fp": "Transfer entries mid-migration (with `migration=in_flight`) should be allow-listed by a start/end date.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.38.3",
        "title": "Data localization enforcement — regulated-data must-stay-in-region",
        "criticality": "high",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "data-flow-cross-border",
        "exclusions": "Does NOT detect misconfigured cloud replication within an allowed region; see UC-22.42.2.",
        "evidence": "Saved search 'data_localization_breach' runs hourly and writes localization-breach findings to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.44",
             "mode": "detects-violation-of", "assurance": "full",
             "assurance_rationale": "Detects transfers that violate localization-based lawful-basis constraints expressed via SCCs or national derogations."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.28",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "DORA Art.28 ICT third-party risk — localization commitments in outsourcing contracts; the UC evidences compliance with contracted hosting regions."},
        ],
        "control_test": {
            "positiveScenario": "When a data object tagged regulated_scope=EU,CH,UK is observed in a cloud storage bucket whose region is outside the allowed_regions list for that scope, the UC fires naming the bucket, region, and classification.",
            "negativeScenario": "Objects that match the allowed-regions list do NOT fire.",
            "fixtureRef": "sample-data/uc-22.38.3-fixture.json",
        },
        "spl": "index=cloud_storage sourcetype=aws:s3:objectaccess OR sourcetype=azure:blob:access earliest=-1h\n| lookup data_classification.csv key=object_key OUTPUT classification regulated_scope\n| lookup localization_policy.csv regulated_scope OUTPUT allowed_regions\n| where isnotnull(regulated_scope) AND NOT match(bucket_region, allowed_regions)\n| table _time bucket bucket_region object_key classification regulated_scope allowed_regions",
        "description": "Evaluates data-localization commitments at the object-access layer. A regulated object that appears in the wrong region is a hard policy breach — and the cloud storage audit log is the definitive evidence.",
        "value": "Replaces 'we think the bucket is in eu-west-1' with 'we proved every access was in-region for the full audit period'.",
        "implementation": "(1) Tag objects with data-classification via the cloud provider's object metadata; (2) maintain localization_policy.csv keyed by regulated_scope; (3) run hourly; (4) escalate breaches via SOAR.",
        "visualization": "Table of breaches by bucket, bar chart of breaches by scope, single-value '% of accesses in sanctioned region'.",
        "references": _ref("gdpr", "dora"),
        "known_fp": "Disaster-recovery replication to allowed DR regions appears as a breach if those regions are not in allowed_regions.csv.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.39 Incident notification timeliness (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.39.1",
        "title": "Multi-regulator breach-notification SLA tracker (24h NIS2 / 72h GDPR / 72h HIPAA)",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "ir-drill-evidence",
        "exclusions": "Does NOT determine whether an event rises to 'breach'; relies on classification decided in the incident-management system.",
        "evidence": "Saved search 'breach_notification_sla' runs every 15 min and writes per-incident SLA status (against every applicable regulator) to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.33",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.33(1) requires notification to the supervisory authority without undue delay and where feasible within 72 hours; the UC measures elapsed time from classification to submission evidence."},
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.23",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "NIS2 Art.23 imposes an early-warning obligation within 24h and an incident notification within 72h; the UC evidences both clocks for every eligible incident."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.19",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "DORA Art.19 requires major ICT-related incident reporting; SLA tracking against intermediate and final reports is the canonical evidence."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.308(a)(6)",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "§164.308(a)(6) security incident procedures include notification duties per §164.400-414; the UC surfaces the timer but breach assessment is decided by the privacy officer."},
        ],
        "control_test": {
            "positiveScenario": "When an incident is classified 'breach' (per incident_register.csv) and no regulator-submission record exists 90 minutes before the applicable SLA deadline, the UC fires with a warning; at breach, it fires at severity critical.",
            "negativeScenario": "Incidents not classified as breach, or incidents whose notification was submitted before the deadline with a valid tracking_id, do NOT fire.",
            "fixtureRef": "sample-data/uc-22.39.1-fixture.json",
        },
        "spl": "| inputlookup incident_register.csv\n| where classification=\"breach\"\n| eval applicable_regs=split(applicable_regs,\",\")\n| mvexpand applicable_regs\n| lookup sla_catalog.csv regulator as applicable_regs OUTPUT sla_hours\n| eval deadline=strptime(classified_at,\"%Y-%m-%dT%H:%M:%SZ\")+sla_hours*3600\n| join incident_id applicable_regs [search index=notifications sourcetype=regulator:submission | fields incident_id applicable_regs tracking_id submitted_at]\n| eval status=case(isnull(tracking_id) AND now()>deadline, \"breach\", isnull(tracking_id) AND (deadline-now())<5400, \"imminent\", isnotnull(tracking_id), \"submitted\")\n| table incident_id applicable_regs deadline submitted_at status",
        "description": "Tracks every incident that has crossed the 'breach' threshold and reports on the notification clock per applicable regulator. Imminent breaches trigger a warning; missed deadlines trigger a critical notable and a board-level communication.",
        "value": "Most enforcement actions against supervisory breaches (ICO, DPC, BaFin) focus on notification timeliness. This UC turns the obligation into a visible KPI instead of a post-facto audit finding.",
        "implementation": "(1) Ingest classifications from ServiceNow / ES incident index; (2) maintain sla_catalog.csv with regulator → SLA hours; (3) ingest notification-portal tracking IDs; (4) schedule every 15 min; (5) integrate with SOAR to auto-escalate.",
        "visualization": "Gantt of incidents vs SLA deadlines, single-value 'incidents notified on time (90d)', breakdown by regulator.",
        "references": _ref("gdpr", "nis2", "dora", "hipaa"),
        "known_fp": "Incidents whose submission happens offline with post-hoc upload require a timezone-normalised submitted_at; mis-mapped timezones produce false SLA breaches.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "threat",
    },
    {
        "id": "22.39.2",
        "title": "Regulator-portal submission evidence — one-way API acknowledgement audit",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "ir-drill-evidence",
        "exclusions": "Does NOT validate correctness of the report content; pairs with internal QA review.",
        "evidence": "Hourly search 'regulator_submission_ack' captures submission → acknowledgement round-trip and stores receipts to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.33",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.33 requires the notification to reach the authority; a submitted-without-ack outcome is not a completed notification."},
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.23",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "NIS2 Art.23 requires CSIRT notification with acknowledgement; the UC evidences the closed loop."},
        ],
        "control_test": {
            "positiveScenario": "When a regulator submission is sent but no acknowledgement is captured within 15 minutes of submission, the UC fires and escalates to the incident coordinator.",
            "negativeScenario": "Submissions with a valid tracking_id and an ack event do NOT fire.",
            "fixtureRef": "sample-data/uc-22.39.2-fixture.json",
        },
        "spl": "index=notifications sourcetype=regulator:submission earliest=-72h\n| stats values(tracking_id) as tracking_id min(_time) as submitted by incident_id regulator\n| join type=outer incident_id regulator [search index=notifications sourcetype=regulator:ack earliest=-72h | stats values(tracking_id) as ack_tracking_id max(_time) as acked by incident_id regulator]\n| where isnull(ack_tracking_id) OR (acked-submitted)>900\n| table incident_id regulator tracking_id submitted acked",
        "description": "Closes the loop on regulator submissions by requiring a matching ack. Silent failures of the submission channel show up within minutes instead of being noticed during audit months later.",
        "value": "Addresses the repeatedly-cited 'we submitted but the authority never acknowledged' defence that now carries no weight in supervisory decisions.",
        "implementation": "(1) Instrument submission and ack channels to emit matching tracking_ids; (2) schedule hourly; (3) on miss, SOAR opens an incident-notification retry case.",
        "visualization": "Funnel (submitted → acked), bar chart of delays by regulator, single-value 'submissions acked within 15 min'.",
        "references": _ref("gdpr", "nis2"),
        "known_fp": "Regulator portals that batch acks daily produce legitimate lag; configure a per-regulator grace window.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "threat",
    },
    {
        "id": "22.39.3",
        "title": "Data-subject breach communication timeline tracker (Art.34 / §164.404)",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Security",
        "owner": "DPO",
        "control_family": "ir-drill-evidence",
        "exclusions": "Does NOT evaluate risk assessment that drives the Art.34 threshold — that classification is input to this UC.",
        "evidence": "Daily search 'data_subject_comm_sla' writes the fan-out state of every Art.34 / §164.404 communication campaign to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.34",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.34 high-risk breach communication to data subjects — the UC tracks message dispatch, delivery, and failure rates."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.404",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.404 notification to individuals within 60 days; the UC measures completion rate and flags overdue individuals."},
        ],
        "control_test": {
            "positiveScenario": "When an Art.34 / §164.404 campaign is open and fewer than 95% of in-scope data subjects have a confirmed delivery or bounced-and-retried event 50 days after classification, the UC fires.",
            "negativeScenario": "Campaigns that hit the 95% threshold, or individual bounces handled via registered post fall-back, do NOT fire.",
            "fixtureRef": "sample-data/uc-22.39.3-fixture.json",
        },
        "spl": "index=comms sourcetype=breach:notification earliest=-90d\n| stats count(eval(status=\"delivered\")) as delivered count(eval(status=\"bounced_handled\")) as fallback count as total by campaign_id\n| eval ok=(delivered+fallback)/total\n| lookup breach_campaigns.csv campaign_id OUTPUT classification classified_at\n| eval age_days=round((now()-strptime(classified_at,\"%Y-%m-%dT%H:%M:%SZ\"))/86400,0)\n| where age_days>=50 AND ok<0.95\n| table campaign_id classified_at age_days total delivered fallback ok",
        "description": "Measures every open high-risk-breach communication campaign against the statutory clocks (GDPR 'without undue delay', HIPAA 60 days). Campaigns falling behind the completion-rate threshold are surfaced to the DPO for intervention.",
        "value": "Data-subject communication is routinely cited in enforcement decisions (Meta, Uber, British Airways); measuring it is the only credible evidence of 'taken reasonable efforts'.",
        "implementation": "(1) Ingest campaign events from the messaging platform; (2) join to breach_campaigns.csv with classification timestamps; (3) run daily; (4) escalate via SOAR.",
        "visualization": "Per-campaign completion funnel, aging bar chart, single-value '% of campaigns on track'.",
        "references": _ref("gdpr", "hipaa"),
        "known_fp": "Subjects without deliverable contact info require the fall-back channel; bounces without fall-back handling should be followed up manually.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "threat",
    },

    # -----------------------------------------------------------------
    # 22.40 Privileged access evidence (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.40.1",
        "title": "Privileged session recording — missing recordings for elevated sessions",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "privileged-session-recording",
        "exclusions": "Does NOT grade the recording content; pairs with manual periodic review.",
        "evidence": "Hourly report 'pam_session_recording_gap' writes unrecorded privileged sessions to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "AC-6",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "AC-6(9) requires logging execution of privileged functions; session recording is the canonical control."},
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.AccessMgmt.Privileged",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SOX ITGC privileged access requires evidence of control operation; session recordings are the auditable artefact."},
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "CC6.1",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CC6.1 logical access controls — evidence of privileged activity is a standard SOC 2 control."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "10.2",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "PCI 10.2 logs all actions by administrative / root users; recording completes the evidentiary loop."},
        ],
        "control_test": {
            "positiveScenario": "When an IdP elevation event (role='admin' OR tag='pim-activated') is not matched by a PAM session-recording registration within 5 minutes, the UC fires naming the user, target_host, and session_id.",
            "negativeScenario": "Elevation events matched by a recording id within the grace window do NOT fire.",
            "fixtureRef": "sample-data/uc-22.40.1-fixture.json",
            "attackTechnique": "T1078.004",
        },
        "spl": "index=idp sourcetype=azuread:audit OR sourcetype=okta:audit earliest=-1h eventtype=privilege_elevation\n| rename user as admin_user\n| join type=outer admin_user [search index=pam sourcetype=cyberark:session OR sourcetype=beyondtrust:session earliest=-1h | fields admin_user recording_id session_id target_host _time]\n| where isnull(recording_id)\n| table _time admin_user target_host session_id",
        "description": "Correlates every privileged-role activation with a matching PAM session recording. Any elevation without a recording is a control failure to be investigated, not an accepted operational cost.",
        "value": "Converts 'we have PAM' into 'we can prove every privileged session was recorded' — the question auditors actually ask.",
        "implementation": "(1) Ingest IdP PIM/PAM activation events; (2) ingest PAM session registration events; (3) run hourly; (4) on miss, SOAR opens a P2 case for the session.",
        "visualization": "Time chart of recorded-vs-unrecorded elevations, table of gaps, single-value 'privileged sessions with recording (7d)'.",
        "references": _ref("nist80053", "soxitgc", "soc2", "pci", extra=[
            {"url": "https://attack.mitre.org/techniques/T1078/004/", "title": "MITRE ATT&CK — T1078.004 Valid Accounts: Cloud Accounts", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Elevations for emergency service accounts recorded outside the PAM (agent-based) require a secondary allowlist.",
        "mitre": ["T1078.004"],
        "detection_type": "Correlation",
        "security_domain": "identity",
    },
    {
        "id": "22.40.2",
        "title": "Break-glass account usage review with mandatory post-use approval",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "privileged-session-recording",
        "exclusions": "Does NOT verify the root cause of the emergency; focuses on the governance loop only.",
        "evidence": "Saved search 'breakglass_post_use_review' runs every 30 min; writes per-incident review status to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "AC-6",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "AC-6(7) requires review of privileges; break-glass use demands post-hoc approval by design."},
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.5.15",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "A.5.15 access control — emergency access procedures require review and sign-off."},
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.AccessMgmt.Privileged",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Privileged access must be timely reviewed — break-glass is the exception that most frequently fails an ITGC review."},
        ],
        "control_test": {
            "positiveScenario": "When a break-glass account is used but no matching approval record exists 48 hours after session close, the UC fires naming the account, session_id, and initiator.",
            "negativeScenario": "Usages with an approval record and sign-off by the designated reviewer do NOT fire.",
            "fixtureRef": "sample-data/uc-22.40.2-fixture.json",
        },
        "spl": "index=pam breakglass=true earliest=-14d\n| stats min(_time) as started max(_time) as ended values(session_id) as session_id by account initiator\n| join account session_id [search index=grc sourcetype=breakglass:approval | stats values(approver) as approver max(_time) as approved_at by account session_id]\n| where isnull(approved_at) AND (now()-ended)>172800\n| table account initiator started ended session_id approved_at",
        "description": "Every break-glass activation must be followed by a reviewer sign-off within 48 hours. The UC surfaces any usage that escaped the governance loop.",
        "value": "Break-glass misuse is the most audited sub-case of privileged access; a missing approval is a textbook SOX-ITGC deficiency.",
        "implementation": "(1) Tag break-glass accounts at vault time; (2) emit approval events from the GRC tool; (3) schedule every 30 min; (4) on miss, notify CISO and engage SOAR.",
        "visualization": "Table of break-glass activations with approval status, bar chart of usages per quarter, single-value 'activations with 48h approval'.",
        "references": _ref("nist80053", "iso27001", "soxitgc"),
        "known_fp": "Approval events tagged against the wrong session_id will look like misses; maintain strict id-matching contracts.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "identity",
    },
    {
        "id": "22.40.3",
        "title": "Periodic access review SLA — stale certifications by control owner",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "privileged-session-recording",
        "exclusions": "Does NOT judge the quality of the certification (rubber-stamp vs diligent); follows up with sampling review.",
        "evidence": "Daily report 'access_review_freshness' writes review-age per control owner to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "AC-2",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "AC-2(j) requires review of accounts at least annually; the UC measures compliance continuously."},
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.5.18",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "A.5.18 access rights — periodic review is a core requirement."},
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.AccessMgmt.Review",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SOX ITGC periodic access review is a cornerstone audit test."},
        ],
        "control_test": {
            "positiveScenario": "When a control owner has not completed an access review for a scoped application in 90+ days, the UC fires with the owner, app_id, and last_review_at.",
            "negativeScenario": "Applications with reviews certified within the 90-day window do NOT fire.",
            "fixtureRef": "sample-data/uc-22.40.3-fixture.json",
        },
        "spl": "index=grc sourcetype=iam:access_review earliest=-365d\n| stats max(_time) as last_review by app_id reviewer\n| eval days_since=round((now()-last_review)/86400,0)\n| where days_since>90\n| lookup app_inventory.csv app_id OUTPUT owner criticality\n| table owner app_id criticality last_review days_since",
        "description": "Tracks the age of the most recent access review per application and control owner. Applications falling outside the 90-day cadence drive follow-up tickets.",
        "value": "Access review is the #1 ITGC deficiency in typical public-company audits; turning it into a green/red KPI changes the operating rhythm.",
        "implementation": "(1) Ingest review-completion events from the GRC tool; (2) refresh app_inventory.csv weekly; (3) run daily.",
        "visualization": "Heatmap of owner × application age, table of overdue, single-value '% of apps reviewed within 90 days'.",
        "references": _ref("nist80053", "iso27001", "soxitgc"),
        "known_fp": "New applications added in-cycle need a baseline review; track onboarding date.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "identity",
    },

    # -----------------------------------------------------------------
    # 22.41 Encryption and key management attestation (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.41.1",
        "title": "Encryption-at-rest coverage gap — unencrypted storage with regulated data",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "CISO",
        "control_family": "crypto-drift",
        "exclusions": "Does NOT judge algorithm strength (see UC-22.41.2); focuses on coverage only.",
        "evidence": "Daily report 'encryption_at_rest_gap' writes unencrypted-volume findings to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.32(1)(a) encryption is a recommended technical measure; gap detection is a leading indicator of Art.32 compliance."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.312(a)(2)(iv)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.312(a)(2)(iv) encryption addressable specification — the UC provides evidence of coverage."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "3.5",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "PCI 3.5 requires rendering stored account data unreadable; the UC detects any CHD-scoped storage without encryption."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "SC-13",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SC-13 cryptographic protection — the UC evidences coverage for regulated data."},
        ],
        "control_test": {
            "positiveScenario": "When cloud-storage or database volumes tagged regulated_data=true are observed without an active encryption configuration (EBS-encryption, SSE-KMS, TDE), the UC fires naming the volume and classification.",
            "negativeScenario": "Volumes with an encryption key ARN and AES-256 / AES-GCM active do NOT fire.",
            "fixtureRef": "sample-data/uc-22.41.1-fixture.json",
        },
        "spl": "| rest /services/cloud_storage/inventory splunk_server=* | where regulated_data=\"true\"\n| stats values(encryption_state) as state by volume_id region tenant\n| where mvfind(state, \"enabled\")<0\n| lookup data_classification.csv volume_id OUTPUT classification\n| table tenant region volume_id classification state",
        "description": "Produces a daily inventory of storage volumes that hold regulated data but are not encrypted at rest. Findings feed the remediation backlog and the evidence pack.",
        "value": "Unencrypted regulated data is the most common PCI 3.5 / HIPAA finding — preventing it from appearing on the audit spreadsheet is the goal.",
        "implementation": "(1) Ingest cloud-inventory telemetry; (2) tag volumes via data_classification.csv; (3) run daily; (4) on finding, auto-open a CISO review.",
        "visualization": "Stacked bar of encrypted vs unencrypted by tenant, table of findings, single-value '% of regulated volumes encrypted'.",
        "references": _ref("gdpr", "hipaa", "pci", "nist80053"),
        "known_fp": "Volumes undergoing pre-encryption migration require a time-bounded allowance (migration_end_date).",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.41.2",
        "title": "Certificate / TLS posture — weak cipher and expired-cert detection",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "crypto-drift",
        "exclusions": "Does NOT detect pinning misconfiguration in client apps; see UC-22.38.3 for localization.",
        "evidence": "Hourly saved search 'tls_posture_audit' writes TLS scan findings to compliance_summary.",
        "compliance": [
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "4.2",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "PCI 4.2 requires strong cryptography and security protocols; the UC flags weak ciphers and outdated protocols."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.312(e)(1)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.312(e)(1) transmission security; TLS posture is the primary evidence."},
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.21(2)(h)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.21(2)(h) cryptography — the UC continuously validates posture."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "SC-8",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SC-8(1) transmission confidentiality and integrity — implemented via strong TLS."},
        ],
        "control_test": {
            "positiveScenario": "When a TLS scan reveals a certificate expiring within 21 days, a protocol < TLS 1.2, or a non-AEAD cipher, the UC fires listing host, cert_expires_in, protocol, and cipher.",
            "negativeScenario": "Hosts with TLS 1.2/1.3, AEAD ciphers, and certs ≥21 days from expiry do NOT fire.",
            "fixtureRef": "sample-data/uc-22.41.2-fixture.json",
        },
        "spl": "index=tls sourcetype=tls:scan earliest=-1h\n| eval days_to_expiry=round((expires-now())/86400,0)\n| where days_to_expiry<21 OR protocol!=\"TLSv1.2\" AND protocol!=\"TLSv1.3\" OR NOT match(cipher, \"^TLS_(AES|CHACHA20|ECDHE)\")\n| table host days_to_expiry protocol cipher",
        "description": "Continuous TLS-posture audit replacing periodic scan spreadsheets. Any finding feeds remediation and the cipher-and-cert evidence pack.",
        "value": "Moves TLS posture from 'we scan quarterly' to 'we proved every TLS endpoint was compliant for every day of the period'.",
        "implementation": "(1) Run scanner (SSL Labs CLI, OpenSSL-based scripts, Qualys SSL Labs); (2) feed to Splunk; (3) schedule hourly; (4) on finding, ticket via SOAR.",
        "visualization": "Table of non-compliant hosts, stacked bar of protocol distribution, single-value '% of endpoints with strong TLS'.",
        "references": _ref("pci", "hipaa", "nis2", "nist80053"),
        "known_fp": "Internal / lab endpoints may legitimately use non-standard configurations; maintain scan_scope.csv to include only in-scope systems.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.41.3",
        "title": "Key rotation attestation — KMS/HSM rotation SLA tracker",
        "criticality": "high",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "CISO",
        "control_family": "crypto-drift",
        "exclusions": "Does NOT evaluate key-wrap hierarchy; KEK/DEK design is out of scope.",
        "evidence": "Daily report 'kms_rotation_sla' writes per-key rotation evidence to compliance_summary.",
        "compliance": [
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "3.6",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "PCI 3.6 requires key rotation at end-of-cryptoperiod; the UC evidences compliance per key."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "SC-13",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SC-13 key management encompasses rotation."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.9",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.9 protection and prevention — crypto key lifecycle is part of the ICT framework."},
        ],
        "control_test": {
            "positiveScenario": "When a key's last rotation is older than the cryptoperiod defined in key_policy.csv, the UC fires with key_id, last_rotation, and cryptoperiod.",
            "negativeScenario": "Keys within their cryptoperiod and keys marked key_type=archive are NOT flagged.",
            "fixtureRef": "sample-data/uc-22.41.3-fixture.json",
        },
        "spl": "index=kms (sourcetype=aws:kms OR sourcetype=azure:keyvault OR sourcetype=gcp:kms) action=rotate\n| stats max(_time) as last_rotation by key_id tenant\n| lookup key_policy.csv key_id OUTPUT cryptoperiod_days key_type\n| where key_type!=\"archive\"\n| eval age_days=round((now()-last_rotation)/86400,0)\n| where age_days>cryptoperiod_days\n| table tenant key_id last_rotation age_days cryptoperiod_days",
        "description": "Verifies every encryption key is rotated within its policy cryptoperiod. Overdue keys are highlighted and evidence is written to the compliance index for audit.",
        "value": "Gives the cryptographic custodian the ability to defend the 'our keys are rotated' claim with per-key evidence rather than a policy document.",
        "implementation": "(1) Ingest KMS audit logs; (2) maintain key_policy.csv; (3) run daily; (4) escalate via SOAR to the crypto custodian.",
        "visualization": "Table of overdue keys, scatter plot age vs cryptoperiod, single-value '% of keys within cryptoperiod'.",
        "references": _ref("pci", "nist80053", "dora"),
        "known_fp": "Keys under a temporary freeze (key_status=frozen) for investigation should be excluded via a status filter.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.42 Change management and configuration baseline (2 new)
    # -----------------------------------------------------------------
    {
        "id": "22.42.1",
        "title": "Unauthorized production change — no approved CR matches the observed change",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "policy-to-control-traceability",
        "exclusions": "Does NOT evaluate the contents of an approved change; focuses on authorisation only.",
        "evidence": "Hourly search 'unauthorized_prod_change' writes findings to compliance_summary.",
        "compliance": [
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "CC8.1",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CC8.1 requires that changes are authorised, designed, documented, and tested; the UC enforces the authorisation gate technically."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "CM-3",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CM-3 configuration-change control — the UC is a direct implementation."},
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.ChangeMgmt.Authorization",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SOX ITGC change authorisation — the UC is a textbook control test."},
        ],
        "control_test": {
            "positiveScenario": "When a production-system change event arrives without a matching approved CR within the 60-minute correlation window, the UC fires.",
            "negativeScenario": "Changes with a CR in approved_state at the time of execution do NOT fire.",
            "fixtureRef": "sample-data/uc-22.42.1-fixture.json",
            "attackTechnique": "T1562.001",
        },
        "spl": "index=change sourcetype=prod:change earliest=-1h\n| join type=outer change_id [search index=itsm sourcetype=servicenow:change earliest=-1h state=approved | fields change_id approved_at]\n| where isnull(approved_at)\n| table _time change_id system applied_by system_owner",
        "description": "Validates every production change event against the CR database in real time. Any change without an approved CR is an immediate ITGC deficiency — and a potential security event.",
        "value": "Replaces the standard quarterly-sample audit with continuous evidence of the authorisation gate.",
        "implementation": "(1) Force CI/CD tools to emit change events tagged with change_id; (2) ingest CR state from the ITSM platform; (3) run hourly; (4) on finding, escalate via SOAR.",
        "visualization": "Stacked bar approved vs unauthorised by system, table of findings, single-value '% authorised changes'.",
        "references": _ref("soc2", "nist80053", "soxitgc", extra=[
            {"url": "https://attack.mitre.org/techniques/T1562/001/", "title": "MITRE ATT&CK — T1562.001 Impair Defenses: Disable Tools", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Emergency changes executed under break-glass must reference a retro-CR id; without one they look unauthorised.",
        "mitre": ["T1562.001"],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.42.2",
        "title": "Configuration baseline drift — regulated hosts deviating from CIS benchmark",
        "criticality": "high",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "Head of Platform",
        "control_family": "policy-to-control-traceability",
        "exclusions": "Does NOT enforce changes; see UC-22.42.1 for authorisation.",
        "evidence": "Daily 'config_drift_evidence' writes per-host drift deltas to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "CM-2",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CM-2 baseline configuration — the UC evidences drift from the approved baseline."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "CM-6",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CM-6 configuration settings — validates against established settings."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "1.2",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "PCI 1.2 (network security controls) and 2.2 (system-component configuration) both benefit from continuous drift evidence."},
        ],
        "control_test": {
            "positiveScenario": "When a scheduled CIS/osquery scan reports a deviation at severity ≥ medium on a host tagged regulated=true, the UC fires naming the host, rule_id, and deviation detail.",
            "negativeScenario": "Hosts fully compliant with their baseline produce no finding.",
            "fixtureRef": "sample-data/uc-22.42.2-fixture.json",
        },
        "spl": "index=baseline sourcetype=osquery:cis OR sourcetype=ciscat earliest=-24h severity>=medium\n| join host [search index=asset regulated=true | fields host tenant classification]\n| table host tenant classification rule_id severity deviation",
        "description": "Continuously compares live configuration to the approved CIS / osquery baseline. Only deviations on regulated systems are escalated to avoid alert fatigue.",
        "value": "Turns baseline drift from a quarterly scan artefact into a continuous control that auditors can review any day.",
        "implementation": "(1) Schedule osquery/CIS-CAT agents; (2) publish baselines via config-management tooling; (3) run daily; (4) on finding, open a P2 ticket.",
        "visualization": "Heatmap of tenants × controls, bar chart of findings by severity, single-value 'regulated hosts in compliance'.",
        "references": _ref("nist80053", "pci"),
        "known_fp": "Hosts mid-patching cycle can appear out-of-baseline briefly; tolerate a 4-hour grace window.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.43 Vulnerability management and patch SLAs (2 new)
    # -----------------------------------------------------------------
    {
        "id": "22.43.1",
        "title": "Critical vulnerability SLA tracker — unpatched 30+ days with exploited-in-the-wild indicator",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "regulation-specific",
        "exclusions": "Does NOT validate compensating controls; that is a separate manual process.",
        "evidence": "Daily report 'critical_vuln_sla' writes per-host per-CVE SLA evidence to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "RA-5",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "RA-5 vulnerability scanning — the UC produces SLA evidence for remediation timeliness."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "6.3",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "PCI 6.3 requires addressing vulnerabilities within a defined window — 30 days for critical."},
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.21(2)(e)",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.21(2)(e) security in acquisition / development / maintenance — patching is the operational component."},
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.8.8",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "A.8.8 management of technical vulnerabilities — SLA evidence demonstrates operation of the control."},
        ],
        "control_test": {
            "positiveScenario": "When a CVE with CVSS ≥ 9.0 or marked exploited-in-the-wild is observed on a host for more than 30 days without a remediation record, the UC fires.",
            "negativeScenario": "Hosts remediated within 30 days or hosts with an accepted-risk token (valid period) do NOT fire.",
            "fixtureRef": "sample-data/uc-22.43.1-fixture.json",
            "attackTechnique": "T1190",
        },
        "spl": "index=vuln sourcetype=tenable:vm OR sourcetype=qualys:vm OR sourcetype=rapid7:vm earliest=-60d cvss_v3_base>=9.0\n| stats min(_time) as first_seen max(_time) as last_seen values(cve) as cves by host\n| eval age_days=round((now()-first_seen)/86400,0)\n| where age_days>30\n| join type=outer host cves [search index=vuln action=remediated]\n| where isnull(remediated_at)\n| table host cves first_seen age_days",
        "description": "Continuously measures how long critical or exploited-in-the-wild vulnerabilities have persisted. Breaches are surfaced immediately and feed the evidence pack with per-host details.",
        "value": "A missed critical patch is the #1 root cause of breaches — proving remediation timeliness is the matching audit control.",
        "implementation": "(1) Ingest scanner data into Splunk via TA; (2) consume CISA KEV list into exploited_in_wild.csv; (3) run daily; (4) integrate with SOAR to auto-open remediation.",
        "visualization": "Bar chart of age buckets, table of breaches, single-value '% of critical CVEs remediated within 30 days'.",
        "references": _ref("nist80053", "pci", "nis2", "iso27001", extra=[
            {"url": "https://attack.mitre.org/techniques/T1190/", "title": "MITRE ATT&CK — T1190 Exploit Public-Facing Application", "retrieved": "2026-04-16"},
            {"url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "title": "CISA Known Exploited Vulnerabilities Catalog", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Compensating controls (e.g. WAF rules) can legitimately extend the SLA; capture them in vuln_exceptions.csv.",
        "mitre": ["T1190"],
        "detection_type": "Correlation",
        "security_domain": "threat",
    },
    {
        "id": "22.43.2",
        "title": "Vulnerability rediscovery after patch — regressed exposures",
        "criticality": "high",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "regulation-specific",
        "exclusions": "Does NOT root-cause the regression; hands off to remediation with evidence.",
        "evidence": "Daily 'vuln_regression' captures reappearing CVEs and writes them to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "RA-5",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Part of RA-5 is verifying remediation effectiveness — the UC catches patch regressions that would otherwise be silent."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "6.3",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "PCI 6.3 requires proactive verification; regressed vulns defeat the remediation."},
        ],
        "control_test": {
            "positiveScenario": "When a CVE previously marked remediated on a host reappears in a subsequent scan, the UC fires with host, cve, remediated_at, rediscovered_at.",
            "negativeScenario": "Remediated CVEs that remain undetected in subsequent scans do NOT fire.",
            "fixtureRef": "sample-data/uc-22.43.2-fixture.json",
        },
        "spl": "index=vuln earliest=-90d | sort 0 host cve _time | streamstats latest(action) as last_action by host cve\n| where last_action=\"remediated\"\n| join host cve [search index=vuln action=detected earliest=-7d]\n| table host cve remediated_at _time as rediscovered_at",
        "description": "Catches situations where a patched vulnerability resurfaces — typically due to image rollback, snapshot restore, or patch-management regression. Every reappearance erodes prior compliance evidence.",
        "value": "Prevents the compliance report from overstating the remediation rate by double-counting recurring findings.",
        "implementation": "(1) Maintain history of vulnerability state per host/CVE; (2) run daily; (3) on finding, re-open original remediation ticket.",
        "visualization": "Table of regressions, trend of regressions per scan cycle, single-value 'patches holding (30d)'.",
        "references": _ref("nist80053", "pci"),
        "known_fp": "Scanner credential changes can cause false positives that look like regressions; correlate with scanner health.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "threat",
    },

    # -----------------------------------------------------------------
    # 22.44 Third-party / supply-chain risk (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.44.1",
        "title": "Supplier attestation currency — stale SOC 2 / ISO 27001 reports for critical vendors",
        "criticality": "high",
        "difficulty": "beginner",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Procurement",
        "control_family": "third-party-activity",
        "exclusions": "Does NOT evaluate findings in the supplier's report; focuses on currency only.",
        "evidence": "Daily 'supplier_attestation_currency' writes expiring/expired attestations to compliance_summary.",
        "compliance": [
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.28",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "DORA Art.28 ICT third-party risk — requires currency of supplier risk information."},
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.21(2)(d)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.21(2)(d) supply-chain security — continuous tracking of attestation currency."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "SR-3",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "SR-3 supply chain controls — attestations are one of the control artefacts."},
        ],
        "control_test": {
            "positiveScenario": "When a critical supplier's SOC 2 or ISO 27001 attestation is within 30 days of expiry or already expired, the UC fires.",
            "negativeScenario": "Suppliers with a current attestation ≥30 days from expiry do NOT fire.",
            "fixtureRef": "sample-data/uc-22.44.1-fixture.json",
        },
        "spl": "| inputlookup vrm_attestations.csv\n| where criticality IN (\"critical\",\"high\")\n| eval days_to_expiry=round((strptime(expires,\"%Y-%m-%d\")-now())/86400,0)\n| where days_to_expiry<=30\n| table vendor attestation_type expires days_to_expiry",
        "description": "Tracks supplier attestation lifecycles against the TPRM policy and surfaces expiring evidence before the risk committee sees it as an overdue item.",
        "value": "Makes vendor-risk currency a live signal rather than an annual gap report.",
        "implementation": "(1) Push attestation metadata from OneTrust/ServiceNow VRM into vrm_attestations.csv nightly; (2) run daily; (3) on finding, email supplier contact and assigned procurement lead.",
        "visualization": "Table of expiring attestations, Sankey of attestation types per vendor, single-value 'critical vendors with current attestation'.",
        "references": _ref("dora", "nis2", "nist80053"),
        "known_fp": "Re-certification in progress produces a brief 'expired' window; tolerate with an in-progress flag.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.44.2",
        "title": "Subprocessor inventory change — notification SLA to data controllers",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "third-party-activity",
        "exclusions": "Does NOT assess whether the new subprocessor is acceptable; focuses on notification SLA.",
        "evidence": "Saved search 'subprocessor_change_sla' runs every hour and evidences each notification's dispatch status.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.28",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.28(2)/(4) requires prior specific / general authorisation for subprocessors and information about changes; the UC measures notification timeliness."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.28",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "DORA Art.28 includes contractual arrangements for sub-outsourcing; notifications are a key control artefact."},
        ],
        "control_test": {
            "positiveScenario": "When a subprocessor change event is recorded and no controller-notification event is observed within the contractual notice period (default 30 days), the UC fires with the vendor and controllers awaiting notification.",
            "negativeScenario": "Changes with a notification event for every in-scope controller within the window do NOT fire.",
            "fixtureRef": "sample-data/uc-22.44.2-fixture.json",
        },
        "spl": "index=vrm sourcetype=subprocessor:change earliest=-60d\n| join change_id [search index=vrm sourcetype=controller:notification | stats values(controller_id) as controllers_notified by change_id]\n| lookup subprocessor_scope.csv change_id OUTPUT controllers_in_scope notice_days\n| eval days_since=round((now()-_time)/86400,0), missing=mvfilter(NOT match(controllers_notified, controller_id))\n| where days_since>=notice_days AND mvcount(missing)>0\n| table change_id vendor controllers_in_scope controllers_notified missing",
        "description": "Tracks subprocessor-change notifications against each in-scope data controller and raises findings for any notification that misses the contractual window.",
        "value": "Notifications to controllers are a standard audit focus; this UC removes the manual book-keeping.",
        "implementation": "(1) Ingest subprocessor-change events and notification dispatch events; (2) maintain subprocessor_scope.csv; (3) run hourly; (4) escalate missed notices via SOAR.",
        "visualization": "Matrix controller × change with notification status, aging bar chart, single-value 'notifications on time'.",
        "references": _ref("gdpr", "dora"),
        "known_fp": "Controllers whose contracts do not require notification should be excluded via scope lookup.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.44.3",
        "title": "Fourth-party concentration risk — shared critical dependencies across vendors",
        "criticality": "medium",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Procurement",
        "control_family": "third-party-activity",
        "exclusions": "Does NOT rate the fourth-party itself; focuses on concentration score only.",
        "evidence": "Monthly 'fourth_party_concentration' writes concentration scores to compliance_summary.",
        "compliance": [
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.28",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "DORA Art.28 requires institutions to assess concentration risk in ICT outsourcing; the UC provides the quantitative foundation."},
        ],
        "control_test": {
            "positiveScenario": "When a fourth-party is a critical dependency for ≥3 high-criticality vendors, the UC fires with the fourth-party id and the concentration score (>0.6).",
            "negativeScenario": "Fourth-parties with lower concentration OR lower upstream criticality do NOT fire.",
            "fixtureRef": "sample-data/uc-22.44.3-fixture.json",
        },
        "spl": "| inputlookup vendor_dependency_graph.csv\n| where vendor_criticality IN (\"critical\",\"high\")\n| stats dc(vendor) as dependent_count, values(vendor) as vendors by fourth_party\n| eval concentration_score=min(dependent_count/3,1)\n| where concentration_score>=0.6\n| table fourth_party dependent_count vendors concentration_score",
        "description": "Computes a monthly concentration score for each fourth-party dependency across the vendor graph. Surfaces candidates for additional due-diligence or contractual controls.",
        "value": "Addresses the DORA supervisory-priorities theme that regulators ask 'who do your vendors depend on?'.",
        "implementation": "(1) Maintain vendor_dependency_graph.csv enriched monthly; (2) run monthly; (3) surface to risk committee.",
        "visualization": "Network graph of concentration, bar chart of fourth-parties by score, single-value 'fourth-parties above concentration threshold'.",
        "references": _ref("dora"),
        "known_fp": "Depth-1 dependencies where the upstream vendor has alternate providers should be discounted (substitutability>0).",
        "mitre": [],
        "detection_type": "Baseline",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.45 Backup integrity and recovery testing (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.45.1",
        "title": "Backup restore test evidence — RPO/RTO SLA compliance per tier",
        "criticality": "critical",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Head of IT Operations",
        "control_family": "backup-restore-evidence",
        "exclusions": "Does NOT evaluate data-integrity of restored content; pairs with UC-22.45.2.",
        "evidence": "Weekly 'backup_restore_sla' writes RPO/RTO test evidence per tier to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "CP-9",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CP-9 system backup — the UC evidences successful test restoration."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.12",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.12 backup policies and recovery methods — mandates tested RPO/RTO."},
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "A1.2",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "A1.2 availability — backup testing is standard SOC 2 evidence."},
        ],
        "control_test": {
            "positiveScenario": "When a tier-1 system misses either its RPO or RTO during the weekly test, the UC fires with system, tier, measured_rpo, measured_rto.",
            "negativeScenario": "Tier-1 systems meeting both RPO and RTO do NOT fire.",
            "fixtureRef": "sample-data/uc-22.45.1-fixture.json",
        },
        "spl": "index=backup sourcetype=restore:test earliest=-7d\n| stats max(rpo_seconds) as rpo_s, max(rto_seconds) as rto_s by system tier test_id\n| lookup dr_tiers.csv tier OUTPUT rpo_slo rto_slo\n| where rpo_s>rpo_slo OR rto_s>rto_slo\n| table system tier rpo_s rpo_slo rto_s rto_slo",
        "description": "Weekly restore-test evidence with per-tier SLOs. Any failing test becomes an audit-visible finding instead of a silently-missed DR exercise.",
        "value": "Makes backup testing a continuous control rather than an annual artefact.",
        "implementation": "(1) Configure restore test jobs; (2) ingest durations and results; (3) schedule weekly; (4) on miss, escalate to continuity lead.",
        "visualization": "Table of tests, line chart of RPO/RTO trend, single-value '% of tier-1 systems within SLO'.",
        "references": _ref("nist80053", "dora", "soc2"),
        "known_fp": "Tier-2/-3 systems may legitimately miss the tier-1 SLO; ensure tier lookup is current.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "cloud",
    },
    {
        "id": "22.45.2",
        "title": "Backup encryption and air-gap integrity — tamper detection on immutable storage",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Platform",
        "owner": "Head of IT Operations",
        "control_family": "backup-restore-evidence",
        "exclusions": "Does NOT test restore path; see UC-22.45.1.",
        "evidence": "Hourly 'backup_immutable_tamper' writes any immutability-lock or checksum-failure events to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "CP-9",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CP-9(8) cryptographic protection of backups — the UC continuously validates immutability."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.308(a)(7)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.308(a)(7) contingency plan, specifically 164.308(a)(7)(ii)(D) testing and revision — immutability is the protective control during incidents."},
        ],
        "control_test": {
            "positiveScenario": "When a backup repository reports an immutability-lock violation or a checksum failure, the UC fires.",
            "negativeScenario": "Expected retention-expiry deletions with an approved lifecycle-policy_id do NOT fire.",
            "fixtureRef": "sample-data/uc-22.45.2-fixture.json",
            "attackTechnique": "T1490",
        },
        "spl": "index=backup sourcetype=immutable:events earliest=-1h (event=tamper OR event=lock_violation OR event=checksum_mismatch)\n| lookup backup_lifecycle.csv repo_id OUTPUT policy_id\n| where event!=\"lifecycle_expiry\" OR isnull(policy_id)\n| table _time repo_id event detail policy_id",
        "description": "Watches immutable/air-gap backup repositories for any tamper, lock-violation, or checksum-failure. Tampering is a known post-intrusion step (T1490) and breaks the compliance evidence chain.",
        "value": "Prevents the compliance claim of 'we have immutable backups' from silently becoming untrue.",
        "implementation": "(1) Enable repository audit logs; (2) emit checksum-verification events on a schedule; (3) run hourly; (4) on finding, escalate to security.",
        "visualization": "Timeline of events, table of findings, single-value 'hours with no tamper events (30d)'.",
        "references": _ref("nist80053", "hipaa", extra=[
            {"url": "https://attack.mitre.org/techniques/T1490/", "title": "MITRE ATT&CK — T1490 Inhibit System Recovery", "retrieved": "2026-04-16"},
        ]),
        "known_fp": "Planned decommission of repositories should carry a decommission_id in the lookup to avoid noise.",
        "mitre": ["T1490"],
        "detection_type": "Anomaly",
        "security_domain": "cloud",
    },
    {
        "id": "22.45.3",
        "title": "Backup completeness — unprotected workloads with regulated data",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Head of IT Operations",
        "control_family": "backup-restore-evidence",
        "exclusions": "Does NOT assess backup frequency; see UC-22.45.1 for RPO.",
        "evidence": "Daily 'backup_coverage_gap' writes unprotected-workload findings to compliance_summary.",
        "compliance": [
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "CP-9",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CP-9 requires backup of system-level and user-level information — uncovered workloads fail the control."},
            {"regulation": "DORA", "version": "Regulation (EU) 2022/2554", "clause": "Art.12",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.12 requires comprehensive backup; a gap is a direct finding."},
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.Operations.Backup",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "ITGC backup and restore — coverage is the threshold question."},
        ],
        "control_test": {
            "positiveScenario": "When a workload tagged regulated=true has no successful backup within the configured window (default 24h for tier-1), the UC fires naming the workload, tier, last_success.",
            "negativeScenario": "Workloads with a successful backup within the window do NOT fire.",
            "fixtureRef": "sample-data/uc-22.45.3-fixture.json",
        },
        "spl": "| rest /services/backup/inventory splunk_server=* | where regulated=\"true\"\n| stats max(last_success) as last_ok by workload tier\n| lookup dr_tiers.csv tier OUTPUT expected_interval_hours\n| eval hours_since=round((now()-last_ok)/3600,0)\n| where hours_since>expected_interval_hours\n| table tier workload last_ok hours_since expected_interval_hours",
        "description": "Cross-checks the backup inventory against the regulated-workload asset list. Any covered workload without a successful backup in its window becomes a finding.",
        "value": "Coverage gaps are the single most common backup finding at audit; continuous evidence eliminates surprise findings.",
        "implementation": "(1) Tag regulated workloads; (2) publish dr_tiers.csv; (3) run daily; (4) escalate via SOAR.",
        "visualization": "Heatmap of workload × day, bar chart of gaps by tier, single-value '% of regulated workloads protected'.",
        "references": _ref("nist80053", "dora", "soxitgc"),
        "known_fp": "Workloads in a DR cutover window can temporarily appear uncovered; tolerate via a maintenance window.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "cloud",
    },

    # -----------------------------------------------------------------
    # 22.46 Training and awareness (2 new)
    # -----------------------------------------------------------------
    {
        "id": "22.46.1",
        "title": "Mandatory security training — completion SLA by role",
        "criticality": "medium",
        "difficulty": "beginner",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "HR",
        "control_family": "training-effectiveness",
        "exclusions": "Does NOT evaluate training quality or effectiveness; see UC-22.46.2.",
        "evidence": "Weekly 'training_completion_sla' writes completion evidence per role to compliance_summary.",
        "compliance": [
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.308(a)(5)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.308(a)(5) security awareness and training — completion evidence is required."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "12.6",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "PCI 12.6 security awareness — the UC evidences completion at cadence."},
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.21(2)(g)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.21(2)(g) cyber hygiene and training — completion tracking is standard evidence."},
        ],
        "control_test": {
            "positiveScenario": "When an employee in an in-scope role has no completion record for the annual mandatory course within the 365-day window, the UC fires with employee, role, last_completion.",
            "negativeScenario": "Employees with a completion in the current cycle OR employees on approved leave do NOT fire.",
            "fixtureRef": "sample-data/uc-22.46.1-fixture.json",
        },
        "spl": "index=lms sourcetype=completion earliest=-365d course_id=security_awareness\n| stats max(_time) as last_completion by employee_id\n| lookup hr_roster.csv employee_id OUTPUT role status\n| where status=\"active\" AND (isnull(last_completion) OR (now()-last_completion)>31536000)\n| table employee_id role last_completion",
        "description": "Produces per-employee completion evidence for the mandatory annual training. Gaps are surfaced in time for HR to re-enroll before the cycle closes.",
        "value": "Moves completion from a retrospective export to a continuously-known KPI.",
        "implementation": "(1) Ingest LMS events; (2) refresh hr_roster.csv nightly; (3) run weekly; (4) on finding, auto-enrol via HR integration.",
        "visualization": "Bar chart of completion by department, table of overdue, single-value '% completion in cycle'.",
        "references": _ref("hipaa", "pci", "nis2"),
        "known_fp": "Employees on long leave (maternity, sabbatical) should be excluded via a leave flag.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.46.2",
        "title": "Phishing simulation efficacy — click-rate trend and repeat-clicker detection",
        "criticality": "medium",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "training-effectiveness",
        "exclusions": "Does NOT deliver remediation content directly; feeds HR / L&D for follow-up.",
        "evidence": "Monthly 'phishing_sim_efficacy' writes click-rate trend and repeat-clicker lists to compliance_summary.",
        "compliance": [
            {"regulation": "NIS2", "version": "Directive (EU) 2022/2555", "clause": "Art.21(2)(g)",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Art.21(2)(g) — beyond completion, regulators want to see the program is effective."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "12.6",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "PCI 12.6 effectiveness via knowledge retention — simulation click rate is an accepted metric."},
        ],
        "control_test": {
            "positiveScenario": "When the 90-day rolling click-rate rises above the programme baseline by +3 percentage points, or when an employee clicks on 3+ simulations in 180 days, the UC fires.",
            "negativeScenario": "Click-rates within baseline and employees with ≤2 clicks do NOT fire.",
            "fixtureRef": "sample-data/uc-22.46.2-fixture.json",
        },
        "spl": "index=phishing sourcetype=knowbe4:campaign OR sourcetype=proofpoint:psa earliest=-180d\n| bin _time span=30d\n| stats count(eval(action=\"clicked\")) as clicks count as total by _time\n| eval click_rate=round(clicks/total*100,2)\n| stats last(click_rate) as current avg(click_rate) as baseline\n| eval drift=current-baseline\n| where drift>3\n| appendpipe [search index=phishing action=clicked earliest=-180d | stats dc(campaign_id) as clicks by employee | where clicks>=3]",
        "description": "Tracks efficacy: the programme is green only if click-rate stays within baseline and repeat-clickers are followed up. Drift above threshold is a programme-level finding.",
        "value": "Turns the awareness programme into a measurable control, not an annual training badge.",
        "implementation": "(1) Ingest campaign events from the phishing-sim platform; (2) compute baselines per quarter; (3) run monthly; (4) deliver repeat-clicker lists to HR for targeted training.",
        "visualization": "Line chart of click rate over time with baseline band, table of repeat clickers, single-value 'current click rate vs baseline'.",
        "references": _ref("nis2", "pci"),
        "known_fp": "Newly-onboarded employees inflate click-rate; compute baseline excluding the first 30 days post-start.",
        "mitre": [],
        "detection_type": "Baseline",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.47 Control testing evidence freshness (2 new)
    # -----------------------------------------------------------------
    {
        "id": "22.47.1",
        "title": "Control test freshness — evidence older than policy cadence",
        "criticality": "medium",
        "difficulty": "beginner",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Board / Audit Committee",
        "control_family": "policy-to-control-traceability",
        "exclusions": "Does NOT evaluate whether evidence content is sufficient; focuses on freshness.",
        "evidence": "Weekly 'control_test_freshness' writes overdue-evidence findings to compliance_summary.",
        "compliance": [
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "CC5.1",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "CC5.1 establishment of control activities — freshness is required for continuous operation."},
            {"regulation": "NIST 800-53", "version": "Rev. 5", "clause": "PM-1",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "PM-1 information security program plan — evidence currency supports the program."},
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.5.36",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "A.5.36 compliance with information security policies — evidence freshness is the operational control."},
        ],
        "control_test": {
            "positiveScenario": "When any in-scope control has no test-of-operation evidence within its policy cadence, the UC fires.",
            "negativeScenario": "Controls with current evidence do NOT fire.",
            "fixtureRef": "sample-data/uc-22.47.1-fixture.json",
        },
        "spl": "| inputlookup control_inventory.csv\n| lookup control_test_log.csv control_id OUTPUT last_tested\n| eval age_days=round((now()-strptime(last_tested,\"%Y-%m-%d\"))/86400,0)\n| where age_days>cadence_days\n| table control_id control_family cadence_days last_tested age_days",
        "description": "Cross-references the control inventory with the evidence ledger. Produces a list of controls whose evidence is older than their policy cadence.",
        "value": "Provides internal audit with a continuously-updated testing backlog rather than a pre-audit scramble.",
        "implementation": "(1) Maintain control_inventory.csv with cadence per control; (2) emit control_test_log.csv from GRC tooling; (3) run weekly.",
        "visualization": "Heatmap of control × age, table of overdue, single-value '% of controls with fresh evidence'.",
        "references": _ref("soc2", "nist80053", "iso27001"),
        "known_fp": "Controls mid-transition (ownership change) may legitimately exceed cadence; tag with a transition flag.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.47.2",
        "title": "Repeat audit findings — same control deficiency across consecutive audit cycles",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Board / Audit Committee",
        "control_family": "policy-to-control-traceability",
        "exclusions": "Does NOT evaluate root cause; surfaces the pattern for management attention.",
        "evidence": "Quarterly 'repeat_findings_report' writes repeat deficiencies to compliance_summary.",
        "compliance": [
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.Logging.Review",
             "mode": "detects-violation-of", "assurance": "contributing",
             "assurance_rationale": "Repeat findings are an indicator of material weakness; this UC surfaces the early pattern."},
            {"regulation": "SOC 2", "version": "2017 TSC", "clause": "CC3.1",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "CC3.1 risk assessment — repeat findings indicate unresolved risk."},
        ],
        "control_test": {
            "positiveScenario": "When the same control (control_id) has an open deficiency in two consecutive audit cycles, the UC fires.",
            "negativeScenario": "Controls whose deficiencies were closed between cycles do NOT fire.",
            "fixtureRef": "sample-data/uc-22.47.2-fixture.json",
        },
        "spl": "index=grc sourcetype=audit:finding earliest=-2y\n| stats dc(cycle_id) as cycles, values(cycle_id) as cycle_ids by control_id\n| where cycles>=2\n| table control_id cycles cycle_ids",
        "description": "Surfaces controls whose deficiencies persist across audit cycles — the canonical trigger for escalation to the audit committee.",
        "value": "Converts the 'prior year issue' anecdote into a quantitative signal.",
        "implementation": "(1) Ingest audit findings per cycle; (2) schedule quarterly; (3) escalate to audit committee.",
        "visualization": "Bar chart of repeat controls, heatmap of control × cycle, single-value 'repeat findings count'.",
        "references": _ref("soxitgc", "soc2"),
        "known_fp": "Findings closed with carry-over remediation plans can legitimately appear repeat; validate remediation_status.",
        "mitre": [],
        "detection_type": "Baseline",
        "security_domain": "audit",
    },

    # -----------------------------------------------------------------
    # 22.48 Segregation of duties enforcement (2 new)
    # -----------------------------------------------------------------
    {
        "id": "22.48.1",
        "title": "Segregation of duties — toxic role combinations in IAM",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "access-review-cadence",
        "exclusions": "Does NOT assess business-justified exceptions; captured in a lookup.",
        "evidence": "Daily 'sod_toxic_combos' writes toxic-combo findings to compliance_summary.",
        "compliance": [
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.AccessMgmt.SOD",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "SOX SoD — matching toxic combinations is the canonical SOX-ITGC test."},
            {"regulation": "PCI DSS", "version": "v4.0", "clause": "7.2",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "PCI 7.2 privilege assignment — SoD is a typical implementation."},
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.5.3",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "A.5.3 segregation of duties — explicit policy control."},
        ],
        "control_test": {
            "positiveScenario": "When any principal (human or service account) holds two roles listed as a toxic combo in sod_matrix.csv, the UC fires with principal, role_a, role_b.",
            "negativeScenario": "Principals with role-combos that are expressly marked permitted_with_compensating=true do NOT fire.",
            "fixtureRef": "sample-data/uc-22.48.1-fixture.json",
        },
        "spl": "| rest /services/iam/principals splunk_server=* | fields principal roles\n| mvexpand roles\n| join principal [| rest /services/iam/principals splunk_server=* | fields principal roles | mvexpand roles | rename roles as other_role]\n| where roles!=other_role\n| lookup sod_matrix.csv role_a=roles role_b=other_role OUTPUT toxic permitted_with_compensating\n| where toxic=\"true\" AND permitted_with_compensating!=\"true\"\n| table principal roles other_role",
        "description": "Enforces the SoD matrix every day across all principals. Toxic combos become visible the moment they are assigned, not at the next audit.",
        "value": "SoD failures are the top SOX ITGC finding in the Fortune-1000 cohort; automating them is the only defensible posture.",
        "implementation": "(1) Maintain sod_matrix.csv with the company's SoD rules; (2) ingest IAM state via REST; (3) run daily; (4) on finding, auto-open a remediation ticket.",
        "visualization": "Table of violations, network graph of role interactions, single-value 'principals with SoD violations'.",
        "references": _ref("soxitgc", "pci", "iso27001"),
        "known_fp": "Break-glass admin accounts require explicit permitted_with_compensating=true.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "identity",
    },
    {
        "id": "22.48.2",
        "title": "SoD violations via break-glass usage — emergency role abuse",
        "criticality": "critical",
        "difficulty": "advanced",
        "monitoring_type": ["Compliance", "Security"],
        "splunk_pillar": "Security",
        "owner": "CISO",
        "control_family": "access-review-cadence",
        "exclusions": "Pairs with UC-22.40.2 for post-use approval.",
        "evidence": "Real-time 'breakglass_sod_violation' detects SoD violations during break-glass usage.",
        "compliance": [
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.AccessMgmt.SOD",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "Break-glass that crosses SoD boundaries must be compensated; this UC generates the signal at session close."},
        ],
        "control_test": {
            "positiveScenario": "When a break-glass session performs actions that cross an SoD boundary (per sod_matrix.csv) without a pre-approved emergency-exception ticket, the UC fires.",
            "negativeScenario": "Break-glass sessions that stay within the permitted action set do NOT fire.",
            "fixtureRef": "sample-data/uc-22.48.2-fixture.json",
        },
        "spl": "index=pam breakglass=true earliest=-24h\n| stats values(action_category) as actions by session_id account\n| mvexpand actions\n| lookup sod_matrix.csv action_a=actions OUTPUT toxic_against\n| mvexpand toxic_against\n| join session_id toxic_against [search index=pam breakglass=true earliest=-24h | eval hit=action_category]\n| join session_id [search index=grc sourcetype=emergency:exception | fields session_id exception_id]\n| where isnull(exception_id)\n| table session_id account actions toxic_against",
        "description": "Detects break-glass sessions that executed actions which would normally violate segregation of duties. Unless there is an emergency-exception ticket, the session breaches SoD even if the break-glass approval is otherwise valid.",
        "value": "Break-glass is often abused to step around SoD; this UC catches that pattern without waiting for audit.",
        "implementation": "(1) Tag PAM session actions into SoD categories; (2) maintain sod_matrix.csv; (3) require emergency exceptions to log to GRC; (4) run hourly.",
        "visualization": "Table of sessions with SoD crossings, single-value 'SoD-compliant emergency sessions'.",
        "references": _ref("soxitgc"),
        "known_fp": "Sessions whose category mapping is imprecise can look like crossings; refine sod_matrix.csv categories quarterly.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "identity",
    },

    # -----------------------------------------------------------------
    # 22.49 Retention and disposal automation (3 new)
    # -----------------------------------------------------------------
    {
        "id": "22.49.1",
        "title": "Retention execution evidence — records past retention still present",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "retention-end-enforcement",
        "exclusions": "Does NOT cover litigation-hold exceptions; see UC-22.49.3.",
        "evidence": "Daily 'retention_execution' writes past-retention records to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.5",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.5(1)(e) storage limitation — data must not be kept longer than necessary; the UC evidences compliance."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.310(d)(1)",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "§164.310(d)(1) device and media controls — disposal is included."},
            {"regulation": "CCPA/CPRA", "version": "CPRA (as amended)", "clause": "§1798.100",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "CCPA requires data minimisation; retention enforcement is a necessary control."},
        ],
        "control_test": {
            "positiveScenario": "When a record in a scoped store is older than its retention_period_days and lacks a litigation-hold flag, the UC fires with store, record_id, age_days.",
            "negativeScenario": "Records within retention OR under litigation hold do NOT fire.",
            "fixtureRef": "sample-data/uc-22.49.1-fixture.json",
        },
        "spl": "index=datastore sourcetype=retention:inventory earliest=-1d\n| lookup retention_policy.csv data_domain OUTPUT retention_period_days\n| eval age_days=round((now()-strptime(created_at,\"%Y-%m-%dT%H:%M:%SZ\"))/86400,0)\n| where age_days>retention_period_days AND litigation_hold!=\"true\"\n| table store record_id data_domain age_days retention_period_days",
        "description": "Cross-references data-store inventory with the retention policy and produces evidence of lapsed retention.",
        "value": "Retention failures quickly become GDPR enforcement actions — continuous monitoring is the only real defence.",
        "implementation": "(1) Maintain retention_policy.csv per data_domain; (2) ingest store inventory with created_at / litigation_hold flags; (3) run daily.",
        "visualization": "Heatmap of store × age buckets, table of overdue records, single-value '% of records within retention'.",
        "references": _ref("gdpr", "hipaa", "ccpa"),
        "known_fp": "Data under litigation hold must carry the flag; without it, the UC will flag it.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.49.2",
        "title": "Disposal workflow completion — failed disposals requiring manual review",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "DPO",
        "control_family": "retention-end-enforcement",
        "exclusions": "Does NOT judge the choice of disposal method; see the retention policy documentation.",
        "evidence": "Daily 'disposal_workflow' writes incomplete dispositions to compliance_summary.",
        "compliance": [
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.5",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "Art.5(1)(e) storage limitation — failed disposal breaches the control."},
            {"regulation": "HIPAA Security", "version": "2013-final", "clause": "§164.310(d)(1)",
             "mode": "satisfies", "assurance": "full",
             "assurance_rationale": "§164.310(d)(1) device and media controls — disposal evidence is required."},
        ],
        "control_test": {
            "positiveScenario": "When a disposal job is started but does not reach completed status within 48 hours, the UC fires.",
            "negativeScenario": "Disposal jobs that complete within 48 hours do NOT fire.",
            "fixtureRef": "sample-data/uc-22.49.2-fixture.json",
        },
        "spl": "index=datastore sourcetype=disposal:job earliest=-7d\n| stats values(status) as states min(_time) as started max(_time) as last_update by job_id\n| where NOT match(states, \"completed\") AND (now()-started)>172800\n| table job_id started last_update states",
        "description": "Monitors disposal jobs across systems and raises findings for jobs that stall. Stalled disposals leak regulated data beyond its lawful window.",
        "value": "Ensures the disposal pipeline is as observable as the ingest pipeline.",
        "implementation": "(1) Instrument disposal tooling to emit lifecycle events; (2) run daily; (3) on stall, notify the data owner.",
        "visualization": "Funnel started → in-progress → completed, table of stalled jobs, single-value '% of disposals completed within 48h'.",
        "references": _ref("gdpr", "hipaa"),
        "known_fp": "Long-running large-scale disposals legitimately take >48h; parametrise per data_domain.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
    {
        "id": "22.49.3",
        "title": "Litigation-hold override audit — holds applied/released without ticket",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoring_type": ["Compliance"],
        "splunk_pillar": "Platform",
        "owner": "Legal",
        "control_family": "retention-end-enforcement",
        "exclusions": "Does NOT assess legal sufficiency; that is a human review.",
        "evidence": "Hourly 'litigation_hold_audit' writes unapproved hold changes to compliance_summary.",
        "compliance": [
            {"regulation": "SOX ITGC", "version": "PCAOB AS 2201", "clause": "ITGC.Logging.Review",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "SOX and e-discovery obligations require documented litigation-hold processes; this UC detects untracked hold changes."},
            {"regulation": "ISO 27001", "version": "2022", "clause": "A.5.33",
             "mode": "satisfies", "assurance": "partial",
             "assurance_rationale": "A.5.33 protection of records — legal holds are a specific implementation."},
        ],
        "control_test": {
            "positiveScenario": "When a litigation-hold is applied or released on any in-scope record and no matching legal ticket exists within 24 hours, the UC fires.",
            "negativeScenario": "Hold changes accompanied by a valid legal ticket do NOT fire.",
            "fixtureRef": "sample-data/uc-22.49.3-fixture.json",
        },
        "spl": "index=datastore sourcetype=hold:change earliest=-24h\n| join hold_id [search index=legal sourcetype=hold:ticket | fields hold_id ticket_id requested_by]\n| where isnull(ticket_id)\n| table _time hold_id record_id action ticket_id",
        "description": "Detects unauthorised application or release of litigation holds — both of which are common sources of adverse inference in discovery.",
        "value": "Prevents silent tampering with evidence preservation.",
        "implementation": "(1) Ingest hold-change audit events from data stores and from the legal-hold tool; (2) run hourly.",
        "visualization": "Table of unauthorised changes, single-value 'hold changes with ticket (30d)'.",
        "references": _ref("soxitgc", "iso27001"),
        "known_fp": "Bulk hold changes during DR or system migration should carry a maintenance ticket.",
        "mitre": [],
        "detection_type": "Correlation",
        "security_domain": "audit",
    },
]


# ---------------------------------------------------------------------------
# Sidecar emission
# ---------------------------------------------------------------------------


def _sidecar_payload(uc: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble the JSON sidecar body matching schemas/uc.schema.json."""
    return {
        "$schema": "../../schemas/uc.schema.json",
        "id": uc["id"],
        "title": uc["title"],
        "criticality": uc["criticality"],
        "difficulty": uc["difficulty"],
        "monitoringType": uc["monitoring_type"],
        "splunkPillar": uc["splunk_pillar"],
        "owner": uc["owner"],
        "controlFamily": uc["control_family"],
        "exclusions": uc["exclusions"],
        "evidence": uc["evidence"],
        "compliance": uc["compliance"],
        "controlTest": uc["control_test"],
        "dataSources": uc.get("data_sources", "See subcategory preamble."),
        "app": uc.get("app", "Splunk Enterprise / Splunk Cloud Platform"),
        "spl": uc["spl"],
        "description": uc["description"],
        "value": uc["value"],
        "implementation": uc["implementation"],
        "visualization": uc["visualization"],
        "references": uc["references"],
        "knownFalsePositives": uc["known_fp"],
        "mitreAttack": uc.get("mitre", []),
        "detectionType": uc.get("detection_type", "Workflow"),
        "securityDomain": uc.get("security_domain", "compliance"),
        "requiredFields": uc.get("required_fields", ["_time"]),
        "status": "community",
        "lastReviewed": "2026-04-16",
        "splunkVersions": ["9.2+", "Cloud"],
        "reviewer": "N/A",
    }


def _write_sidecar(uc: Dict[str, Any]) -> Path:
    target = SIDECAR_DIR / f"uc-{uc['id']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(_sidecar_payload(uc), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return target


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _format_refs(refs: List[Dict[str, str]]) -> str:
    return ", ".join(f"[{r['title']}]({r['url']})" for r in refs)


def _render_uc_markdown(uc: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"### UC-{uc['id']} · {uc['title']}")
    lines.append(f"- **Criticality:** {CRITICALITY_EMOJI[uc['criticality']]} {uc['criticality'].capitalize()}")
    lines.append(f"- **Difficulty:** {DIFFICULTY_EMOJI[uc['difficulty']]} {uc['difficulty'].capitalize()}")
    lines.append(f"- **Monitoring type:** {', '.join(uc['monitoring_type'])}")
    if uc.get("mitre"):
        lines.append(f"- **MITRE ATT&CK:** {', '.join(uc['mitre'])}")
    lines.append(f"- **Splunk Pillar:** {uc['splunk_pillar']}")
    regs = sorted({c["regulation"] for c in uc["compliance"]})
    lines.append(f"- **Regulations:** {', '.join(regs)}")
    lines.append(f"- **Value:** {uc['value']}")
    lines.append(f"- **App/TA:** {uc.get('app', 'Splunk Enterprise / Splunk Cloud Platform')}")
    lines.append(f"- **Data Sources:** {uc.get('data_sources', 'See subcategory preamble.')}")
    lines.append("- **SPL:**")
    lines.append("```spl")
    lines.append(uc["spl"])
    lines.append("```")
    lines.append(f"- **Implementation:** {uc['implementation']}")
    lines.append(f"- **Visualization:** {uc['visualization']}")
    lines.append(f"- **Known false positives:** {uc['known_fp']}")
    lines.append(f"- **References:** {_format_refs(uc['references'])}")
    return "\n".join(lines) + "\n"


def _render_subcategory_header(sc: Dict[str, str]) -> str:
    lines = [
        f"### {sc['id']} {sc['name']}",
        "",
        f"**Primary App/TA:** {sc['primary_app_ta']}",
        "",
        f"**Data Sources:** {sc['data_sources']}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def _render_markdown_block() -> str:
    parts = [
        BEGIN_SENTINEL,
        "<!--",
        "Phase 1.6 exemplar use cases — cross-regulation mini-categories.",
        "This block was generated by scripts/archive/scaffold_exemplars.py during the",
        "Phase 1.6 authoring pass. The scaffold has since been overtaken by hand-applied",
        "enrichments and Phase 2.x derivative-regulation tagging, so do NOT regenerate",
        "this block by re-running the scaffold without --write. Authoritative content",
        "now lives in the matching JSON sidecars under use-cases/cat-22/.",
        "-->",
        "",
    ]

    ucs_by_sub: Dict[str, List[Dict[str, Any]]] = {}
    for uc in UCS:
        subcat_id = uc["id"].rsplit(".", 1)[0]
        ucs_by_sub.setdefault(subcat_id, []).append(uc)

    for sc in SUBCATEGORIES:
        parts.append(_render_subcategory_header(sc))
        for uc in ucs_by_sub.get(sc["id"], []):
            parts.append(_render_uc_markdown(uc))
            parts.append("")
            parts.append("---")
            parts.append("")

    parts.append(END_SENTINEL)
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Fixture emission (minimal; every fixtureRef gets a readable JSON file)
# ---------------------------------------------------------------------------


def _write_fixture(uc: Dict[str, Any]) -> Optional[Path]:
    ref = uc.get("control_test", {}).get("fixtureRef")
    if not ref:
        return None
    fx_path = ROOT / ref
    fx_path.parent.mkdir(parents=True, exist_ok=True)
    stub = {
        "$comment": "Placeholder fixture for Phase 1.6 exemplar UC; replace with production-grade sample-data as part of Phase 4.5 sandbox validation.",
        "uc_id": uc["id"],
        "description": f"Fixture exercising positive scenario for {uc['id']}: {uc['control_test']['positiveScenario']}",
        "events_positive": [],
        "events_negative": [],
    }
    with fx_path.open("w", encoding="utf-8") as f:
        json.dump(stub, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return fx_path


# ---------------------------------------------------------------------------
# Markdown insertion
# ---------------------------------------------------------------------------


def _rewrite_markdown(block: str) -> None:
    text = MARKDOWN_PATH.read_text(encoding="utf-8")
    if BEGIN_SENTINEL in text and END_SENTINEL in text:
        pre = text.split(BEGIN_SENTINEL, 1)[0]
        post = text.split(END_SENTINEL, 1)[1]
        new = pre + block + post
    else:
        suffix = "\n" if not text.endswith("\n") else ""
        new = text + suffix + block
    MARKDOWN_PATH.write_text(new, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _render_sidecar(uc: Dict[str, Any]) -> tuple[Path, str]:
    """Render a single sidecar payload in memory without writing it.

    Mirrors the on-disk layout (`json.dumps(..., indent=2,
    ensure_ascii=False)` + trailing newline) used by `_write_sidecar`.
    """
    sidecar = _sidecar_payload(uc)
    path = SIDECAR_DIR / f"uc-{uc['id']}.json"
    rendered = json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
    return path, rendered


def _diff(label: str, on_disk: str, rendered: str) -> str:
    diff = difflib.unified_diff(
        on_disk.splitlines(keepends=True),
        rendered.splitlines(keepends=True),
        fromfile=label,
        tofile=f"{label} (rebuilt-from-script)",
        n=3,
    )
    return "".join(diff)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 1.6 exemplar scaffold for cat-22.35..49. Default mode is "
            "--check (read-only diff). Pass --write to overwrite on-disk "
            "sidecars + markdown block (destructive — see module docstring)."
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Overwrite on-disk sidecars, fixtures, and the Phase 1.6 "
            "markdown block with the freshly scaffolded payload."
        ),
    )
    args = parser.parse_args(argv)

    if args.write:
        sidecar_count = 0
        for uc in UCS:
            if uc.get("markdown_only"):
                continue
            _write_sidecar(uc)
            _write_fixture(uc)
            sidecar_count += 1
        block = _render_markdown_block()
        _rewrite_markdown(block)
        print(
            f"Wrote {sidecar_count} exemplar sidecars "
            f"({len([u for u in UCS if u.get('markdown_only')])} "
            "markdown-only) and regenerated Phase 1.6 markdown block."
        )
        return 0

    drift_files: List[str] = []
    diff_chunks: List[str] = []

    for uc in UCS:
        if uc.get("markdown_only"):
            continue
        path, rendered = _render_sidecar(uc)
        if not path.exists():
            drift_files.append(f"missing: {path.relative_to(ROOT)}")
            continue
        on_disk = path.read_text(encoding="utf-8")
        if on_disk != rendered:
            drift_files.append(str(path.relative_to(ROOT)))
            diff_chunks.append(_diff(str(path.relative_to(ROOT)), on_disk, rendered))

    expected_block = _render_markdown_block()
    md_text = MARKDOWN_PATH.read_text(encoding="utf-8")
    if BEGIN_SENTINEL in md_text and END_SENTINEL in md_text:
        pre = md_text.split(BEGIN_SENTINEL, 1)[0]
        post = md_text.split(END_SENTINEL, 1)[1]
        on_disk_block = (
            BEGIN_SENTINEL
            + md_text.split(BEGIN_SENTINEL, 1)[1].split(END_SENTINEL, 1)[0]
            + END_SENTINEL
            + "\n"
        )
        if on_disk_block != expected_block:
            drift_files.append(
                f"{MARKDOWN_PATH.relative_to(ROOT)} (between Phase 1.6 sentinels)"
            )
            diff_chunks.append(
                _diff(
                    str(MARKDOWN_PATH.relative_to(ROOT)) + " (Phase 1.6 block)",
                    on_disk_block,
                    expected_block,
                )
            )
    else:
        drift_files.append(
            f"{MARKDOWN_PATH.relative_to(ROOT)} (missing Phase 1.6 sentinels)"
        )

    if not drift_files:
        print(
            f"OK: all {len([u for u in UCS if not u.get('markdown_only')])} "
            "Phase 1.6 sidecars and markdown block match the in-script scaffold."
        )
        return 0

    sys.stdout.writelines(diff_chunks)
    print(
        f"\nDRIFT: {len(drift_files)} on-disk artefact(s) differ from the "
        "in-script Phase 1.6 scaffold.",
        file=sys.stderr,
    )
    for f in drift_files[:20]:
        print(f"  - {f}", file=sys.stderr)
    if len(drift_files) > 20:
        print(f"  ... and {len(drift_files) - 20} more", file=sys.stderr)
    print(
        "\nIf the divergence is intentional (e.g. derived-from-parent "
        "enrichment from later Phase 2.x generators or hand-applied SME "
        "edits), do NOT pass --write — the scaffold's authoring data has "
        "been overtaken.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
