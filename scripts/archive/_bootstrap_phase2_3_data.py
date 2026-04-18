#!/usr/bin/env python3
"""Phase 2.3 data-file bootstrap.

One-shot builder that constructs ``data/per-regulation/phase2.3.json``
from compact in-script UC definitions.

The JSON file that this script emits is the authoring source of truth
for the Phase 2.3 per-regulation content fills. It is consumed by
``scripts/generate_phase2_3_per_regulation.py`` to render markdown
blocks and JSON sidecars.

This bootstrap is committed (rather than discarded) so reviewers can
diff *what* authoring data produced the JSON, while the runtime
generator only ever consumes the JSON.

.. WARNING:: Destructive when run with ``--write``.

   The on-disk fixture has been **hand-edited** since the original
   bootstrap to apply later quality fixes (e.g. CIM-model name
   normalisation, monitoring-type adjustments). Re-running the
   bootstrap with ``--write`` will silently drop those fixes.

   The default mode is ``--check``: the script rebuilds the JSON in
   memory and reports a unified diff vs the on-disk file. Use that to
   inspect intent without modifying anything.

Phase 2.3 closes the remaining tier-1 clause gaps in the thinnest
five frameworks:

- PCI-DSS v4.0 (16 clauses: 1.3, 2.2, 3.3, 5.2, 6.2, 8.3, 8.4, 8.6,
  10.3, 10.4, 10.6, 10.7, 11.3, 11.4, 12.10, 12.3)    -> UCs 22.11.91 .. 22.11.106
- ISO/IEC 27001:2022 (10 clauses: 6.1, 6.2, 8.2, 9.1, 9.2, A.5.24,
  A.5.25, 7.2, 7.5, 8.1)                              -> UCs 22.6.46  .. 22.6.55
- SOC 2 TSC 2017 (9 clauses: CC6.6, CC6.7, CC7.1, CC7.3, CC7.4,
  CC1.1, CC9.1, C1.1, P1.1)                           -> UCs 22.8.31  .. 22.8.39
- SOX-ITGC PCAOB AS 2201 (5 clauses: AccessMgmt.Provisioning,
  AccessMgmt.Termination, ChangeMgmt.Testing,
  ChangeMgmt.Approval, Operations.JobSchedule)        -> UCs 22.12.36 .. 22.12.40
- DORA Regulation (EU) 2022/2554 (5 clauses: Art.6, Art.7, Art.8,
  Art.17, Art.24)                                     -> UCs 22.3.41  .. 22.3.45

Total: 45 UCs.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT = REPO_ROOT / "data" / "per-regulation" / "phase2.3.json"

RETRIEVED = "2026-04-16"

# Canonical URLs per framework (mirrors regulations.json).
URL = {
    "pci-dss": "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf",
    "soc-2": "https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services",
    "iso-27001": "https://www.iso.org/standard/27001",
    "sox-itgc": "https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201",
    "dora": "https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
    "gdpr": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "hipaa": "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164",
    "nis2": "https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
    "nist-800-53": "https://doi.org/10.6028/NIST.SP.800-53r5",
    "nist-csf": "https://www.nist.gov/cyberframework",
    "cmmc": "https://dodcio.defense.gov/CMMC/",
}


def _ref(reg_key: str, title: str) -> Dict[str, str]:
    return {"url": URL[reg_key], "title": title, "retrieved": RETRIEVED}


def _mitre_ref(tid: str) -> Dict[str, str]:
    return {
        "url": f"https://attack.mitre.org/techniques/{tid.split('.')[0]}/",
        "title": f"MITRE ATT&CK — {tid}",
        "retrieved": RETRIEVED,
    }


# ---------------------------------------------------------------------------
# Compliance-entry factories (clause strings match regulations.json grammars)
# ---------------------------------------------------------------------------

def c_pci(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "PCI-DSS",
        "version": "v4.0",
        "clause": clause,
        "clauseUrl": URL["pci-dss"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_soc2(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "SOC-2",
        "version": "2017 TSC",
        "clause": clause,
        "clauseUrl": URL["soc-2"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_iso(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "ISO/IEC 27001",
        "version": "2022",
        "clause": clause,
        "clauseUrl": URL["iso-27001"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_sox(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "SOX-ITGC",
        "version": "PCAOB AS 2201",
        "clause": clause,
        "clauseUrl": URL["sox-itgc"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_dora(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "DORA",
        "version": "Regulation (EU) 2022/2554",
        "clause": clause,
        "clauseUrl": URL["dora"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_nist53(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "NIST 800-53",
        "version": "Rev. 5",
        "clause": clause,
        "clauseUrl": URL["nist-800-53"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_nis2(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "NIS2",
        "version": "Directive (EU) 2022/2555",
        "clause": clause,
        "clauseUrl": URL["nis2"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


def c_hipaa(clause: str, assurance: str, rationale: str, mode: str = "satisfies") -> Dict:
    return {
        "regulation": "HIPAA Security Rule",
        "version": "2013-final",
        "clause": clause,
        "clauseUrl": URL["hipaa"],
        "mode": mode,
        "assurance": assurance,
        "assurance_rationale": rationale,
    }


# ---------------------------------------------------------------------------
# UC factory
# ---------------------------------------------------------------------------

def uc(
    *,
    id_: str,
    title: str,
    criticality: str,
    difficulty: str,
    owner: str,
    control_family: str,
    security_domain: str,
    detection_type: str,
    splunk_pillar: str,
    monitoring_type: List[str],
    exclusions: str,
    evidence: str,
    data_sources: str,
    app: str,
    spl: str,
    description: str,
    value: str,
    implementation: str,
    visualization: str,
    cim_models: List[str],
    known_fp: str,
    required_fields: List[str],
    compliance: List[Dict],
    control_test_positive: str,
    control_test_negative: str,
    mitre_attack: List[str] | None = None,
    control_test_attack_technique: str | None = None,
    extra_refs: List[Dict] | None = None,
) -> Dict:
    """Build one UC dict matching schemas/uc.schema.json."""

    # Build references: one per unique regulation URL, plus MITRE refs, plus extras.
    refs: List[Dict] = []
    seen_urls = set()

    def _add(r: Dict) -> None:
        if r["url"] in seen_urls:
            return
        seen_urls.add(r["url"])
        refs.append(r)

    for c in compliance:
        if c.get("clauseUrl"):
            # Use regulation name in the ref title.
            _add({"url": c["clauseUrl"], "title": f"{c['regulation']} {c['version']}", "retrieved": RETRIEVED})
    for tid in mitre_attack or []:
        _add(_mitre_ref(tid))
    for r in extra_refs or []:
        _add(r)

    out: Dict = {
        "id": id_,
        "title": title,
        "criticality": criticality,
        "difficulty": difficulty,
        "monitoringType": monitoring_type,
        "splunkPillar": splunk_pillar,
        "owner": owner,
        "controlFamily": control_family,
        "exclusions": exclusions,
        "evidence": evidence,
        "compliance": compliance,
        "controlTest": {
            "positiveScenario": control_test_positive,
            "negativeScenario": control_test_negative,
            "fixtureRef": f"sample-data/uc-{id_}-fixture.json",
        },
        "dataSources": data_sources,
        "app": app,
        "spl": spl,
        "description": description,
        "value": value,
        "implementation": implementation,
        "visualization": visualization,
        "cimModels": cim_models,
        "references": refs,
        "knownFalsePositives": known_fp,
        "detectionType": detection_type,
        "securityDomain": security_domain,
        "requiredFields": required_fields,
    }
    if control_test_attack_technique:
        out["controlTest"]["attackTechnique"] = control_test_attack_technique
    if mitre_attack:
        out["mitreAttack"] = mitre_attack
    return out


# ---------------------------------------------------------------------------
# DORA — 5 UCs (22.3.41 .. 22.3.45)
# ---------------------------------------------------------------------------

DORA_UCS: List[Dict] = [
    uc(
        id_="22.3.41",
        title="DORA Art.6 — ICT risk-management framework evidence: control catalogue drift detection",
        criticality="high",
        difficulty="advanced",
        owner="CISO",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT assess control design effectiveness; only detects drift between the documented control catalogue and operational control inventory in the governance platform (Archer, ServiceNow GRC, etc.).",
        evidence="Saved search 'dora_art6_control_catalogue_drift' (daily) produces the delta of documented vs operational controls, counts of orphaned controls, and the list of ICT assets whose controlFamily is not in the approved catalogue; routed to the compliance_summary index.",
        data_sources="`index=grc` sourcetype=archer:control, sourcetype=servicenow:grc_control; `index=cmdb` sourcetype=cmdb:ci_ict_service; controlFamily catalogue lookup `dora_control_catalogue.csv`.",
        app="Splunk Enterprise Security, Splunk Add-on for ServiceNow",
        spl=(
            "index=grc sourcetype IN (archer:control,servicenow:grc_control) earliest=-1d\n"
            "| stats latest(control_family) AS control_family latest(state) AS state BY control_id ict_service\n"
            "| lookup dora_control_catalogue.csv control_family OUTPUT approved\n"
            "| where isnull(approved) OR state=\"inactive\"\n"
            "| table ict_service control_id control_family state approved"
        ),
        description="Compares the live control inventory from the governance platform against the Board-approved DORA control catalogue (per Art.6 requirement for a documented ICT risk-management framework). Surfaces orphan controls (in operations but not in catalogue) and decayed controls (in catalogue but now inactive).",
        value="Replaces the annual 'do we still have the framework' attestation with a continuous reconciliation — regulators under DORA Art.6 expect the framework to be 'soundly, comprehensively and well-documented', meaning drift must be detected and remediated, not just discovered at the next audit.",
        implementation="(1) Export control inventory daily from Archer/ServiceNow GRC into Splunk; (2) maintain dora_control_catalogue.csv as the Board-approved baseline with approval date and approver; (3) schedule UC daily; (4) drift >0 opens a risk-register entry assigned to the CISO with 30-day remediation SLA; (5) quarterly sign-off by the ICT risk committee.",
        visualization="Table of drifted controls, timechart of drift count by day, single value 'days since last zero-drift state'.",
        cim_models=["Change"],
        known_fp="Catalogue refreshes legitimately introduce new control_family values until the GRC platform syncs — maintain a 24h grace window in the lookup's effective-from date.",
        required_fields=["control_id", "control_family", "state", "ict_service", "_time"],
        compliance=[
            c_dora("Art.6", "full",
                   "Art.6 requires a 'sound, comprehensive and well-documented ICT risk-management framework'. A continuously-verified delta between documented and operational controls is the direct evidence a supervisor would request."),
            c_iso("A.5.1", "partial",
                  "ISO/IEC 27001:2022 A.5.1 policies for information security — contributing evidence that the policy framework is operational, but ISO requires additional management-review artefacts."),
            c_nist53("PM-9", "contributing",
                     "NIST 800-53 PM-9 (Risk Management Strategy) — contributes by proving the strategy's control mapping is current."),
        ],
        control_test_positive="Deleting a control in the GRC tool (state=inactive) that is still listed in dora_control_catalogue.csv causes the UC to fire within 24h naming the specific control_id and ict_service.",
        control_test_negative="A newly-added control whose family is present in the approved catalogue and whose state is active does NOT fire.",
        control_test_attack_technique="T1562",
        mitre_attack=["T1562"],
    ),
    uc(
        id_="22.3.42",
        title="DORA Art.7 — ICT systems inventory completeness: unmanaged endpoints attached to financial services",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IT Operations",
        control_family="log-source-completeness",
        security_domain="endpoint",
        detection_type="Baseline",
        splunk_pillar="IT Operations",
        monitoring_type=["Compliance", "Availability", "Security"],
        exclusions="Does NOT test the operating-system patch posture (covered by separate vulnerability-management UCs); detects only the presence of hosts handling financial-service traffic that are absent from the ICT asset inventory.",
        evidence="Saved search 'dora_art7_unmanaged_endpoint' (hourly) outputs per-host diagnostic record: asset_id (if any), hostname, observed_financial_service, inventory_gap_reason, to the compliance_summary index.",
        data_sources="`index=endpoint` sourcetype=WinEventLog:Security / sourcetype=linux:audit; `index=cmdb` sourcetype=cmdb:ci_server; authoritative financial-service CMDB view `financial_services_servers.csv`.",
        app="Splunk Enterprise Security, Splunk Add-on for Microsoft Windows, Splunk Add-on for Unix and Linux",
        spl=(
            "| tstats summariesonly=t count FROM datamodel=Authentication WHERE Authentication.app IN (\"payments\",\"trading\",\"settlement\") BY Authentication.dest\n"
            "| rename Authentication.dest AS hostname\n"
            "| lookup financial_services_servers.csv hostname OUTPUT asset_id owner team\n"
            "| where isnull(asset_id)\n"
            "| eval inventory_gap_reason=\"not in ICT asset inventory\"\n"
            "| table hostname inventory_gap_reason count"
        ),
        description="Uses the CIM Authentication data model to find hosts that have been seen handling financial-service traffic but are absent from the official ICT asset CMDB. Under DORA Art.7 the financial entity must maintain 'up-to-date inventories' of ICT systems; a shadow endpoint with access to payments/trading/settlement is a direct Art.7 non-conformance.",
        value="Turns the quarterly 'asset inventory reconciliation' into a continuous signal, closing the time window during which an unmanaged host can process financial transactions unnoticed.",
        implementation="(1) Onboard auth data to CIM Authentication DM; (2) maintain financial_services_servers.csv from the ICT asset register nightly; (3) schedule UC hourly; (4) hit opens a ServiceNow CMDB task to register the host; (5) SLA: resolve within 72h or isolate; (6) exclude build/imaging windows with an effective-from allowlist.",
        visualization="Bar chart of inventory gaps by financial service, table of hosts with count, single value 'hosts in gap'.",
        cim_models=["Authentication", "Inventory"],
        known_fp="Short-lived CI/CD build runners used for payments tests may legitimately appear off-inventory — allow-list by hostname-pattern in financial_services_servers.csv with a 24h TTL.",
        required_fields=["dest", "app", "_time"],
        compliance=[
            c_dora("Art.7", "full",
                   "Art.7 requires ICT systems, protocols and tools to be 'reliable' and 'technologically up to date' with an up-to-date inventory; an unmanaged host attached to payments is the direct failure mode this UC detects."),
            c_iso("A.5.9", "full",
                  "ISO/IEC 27001:2022 A.5.9 (Inventory of information and other associated assets) — same control objective, directly evidenced."),
            c_nis2("Art.21(2)(d)", "partial",
                   "NIS2 Art.21(2)(d) asset-management subclause is directly supported."),
        ],
        control_test_positive="Simulating an authentication by a non-inventoried host against the trading app causes the UC to fire within the hour naming the hostname and inventory_gap_reason='not in ICT asset inventory'.",
        control_test_negative="A fully-inventoried host performing the same authentication does NOT fire.",
        control_test_attack_technique="T1078",
        mitre_attack=["T1078"],
    ),
    uc(
        id_="22.3.43",
        title="DORA Art.8 — ICT risk identification: newly discovered high-severity exposure on critical financial services",
        criticality="critical",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="regulation-specific",
        security_domain="threat",
        detection_type="Correlation",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT replace the scanner; consumes the scanner's output and prioritises findings on the subset of hosts classified as 'critical financial service' per DORA Art.8(1).",
        evidence="Saved search 'dora_art8_new_crit_exposure' (every 15m) emits, per finding: finding_id, ict_service, cvss, cve, discovered_time, registration_sla_met (boolean), to the compliance_summary index.",
        data_sources="`index=vm` sourcetype=tenable:sc:vuln OR sourcetype=qualys:host; `index=cmdb` sourcetype=cmdb:ci_ict_service; DORA critical-service lookup `dora_critical_services.csv`.",
        app="Splunk Enterprise Security, Splunk Add-on for Tenable, Splunk Add-on for Qualys",
        spl=(
            "index=vm sourcetype IN (tenable:sc:vuln,qualys:host) cvss>=7 earliest=-15m\n"
            "| rename dest AS hostname\n"
            "| lookup dora_critical_services.csv hostname OUTPUT ict_service criticality_tier\n"
            "| where criticality_tier=\"critical\"\n"
            "| eval registration_sla_met=if(relative_time(now(),\"-24h\")<=_time,1,0)\n"
            "| stats count BY ict_service cvss cve hostname registration_sla_met"
        ),
        description="Identifies newly-discovered CVSS>=7 exposures on hosts supporting a DORA-critical financial service. Measures whether the finding is registered in the ICT risk register within the 24h target implied by Art.8 'continuous identification'.",
        value="Produces per-finding evidence that critical-service exposure is identified and logged within the DORA-aligned window, rather than relying on monthly scanner review meetings.",
        implementation="(1) Onboard scanner output; (2) tag hosts with ict_service + criticality_tier nightly; (3) schedule UC every 15m; (4) each hit opens a risk-register entry (ServiceNow) within 24h; (5) weekly report to ICT risk committee; (6) breach of 24h SLA escalates to the Head of IR and Board/Audit Committee.",
        visualization="Timechart of new criticals per ICT service, table of unresolved findings, single value 'findings past 24h SLA'.",
        cim_models=["Vulnerabilities"],
        known_fp="Scanner re-baselines after signature updates can produce a one-time spike of 're-discovered' findings — cross-reference against first_seen and exclude.",
        required_fields=["dest", "cvss", "cve", "_time"],
        compliance=[
            c_dora("Art.8", "full",
                   "Art.8 requires continuous identification of ICT-related risks; a 15-minute detection + 24h register SLA directly maps to that obligation for critical services."),
            c_iso("A.8.8", "full",
                  "ISO/IEC 27001:2022 A.8.8 Management of technical vulnerabilities — directly evidenced."),
            c_nist53("RA-5", "partial",
                     "NIST 800-53 RA-5 Vulnerability Scanning — contributes; monitoring here is a scanner consumer."),
            c_pci("11.3.1", "partial",
                  "PCI-DSS 11.3.1 internal vulnerability scans; this UC reuses the same scanner feed to detect material exposures."),
        ],
        control_test_positive="Creating a test finding with CVSS=8 on a host tagged criticality_tier=critical causes the UC to fire within 15m naming the CVE and ict_service.",
        control_test_negative="A CVSS=5 or non-critical host finding does NOT fire.",
        control_test_attack_technique="T1190",
        mitre_attack=["T1190"],
    ),
    uc(
        id_="22.3.44",
        title="DORA Art.17 — ICT incident classification timeliness: major-incident clock evidence",
        criticality="critical",
        difficulty="advanced",
        owner="Head of IR",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Correlation",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security", "Availability"],
        exclusions="Does NOT classify whether an incident is 'major' (that is a human decision by the incident commander); detects only the elapsed time between detection, initial, intermediate, and final notification fields in the incident record.",
        evidence="Saved search 'dora_art17_incident_clock' (every 5m) produces per-incident timing: detected_at, classified_at, notified_at, notification_intermediate_at, notification_final_at, SLA_breached fields; routed to compliance_summary.",
        data_sources="`index=soar` sourcetype=servicenow:sir_incident OR sourcetype=phantom:incident; `index=ticketing` sourcetype=jira:issue (IR project); regulator notification log `index=compliance` sourcetype=dora:notification.",
        app="Splunk SOAR, Splunk Add-on for ServiceNow",
        spl=(
            "index=soar sourcetype IN (servicenow:sir_incident,phantom:incident) tag::major_incident=true earliest=-1d\n"
            "| stats min(detected_at) AS detected_at min(classified_at) AS classified_at min(notified_at) AS notified_at min(intermediate_at) AS intermediate_at min(final_at) AS final_at BY incident_id\n"
            "| eval detect_to_classify_h=round((classified_at-detected_at)/3600,2)\n"
            "| eval classify_to_initial_h=round((notified_at-classified_at)/3600,2)\n"
            "| eval initial_to_inter_h=round((intermediate_at-notified_at)/3600,2)\n"
            "| eval inter_to_final_h=round((final_at-intermediate_at)/3600,2)\n"
            "| eval SLA_breached=if(detect_to_classify_h>24 OR classify_to_initial_h>24 OR initial_to_inter_h>72 OR inter_to_final_h>720,1,0)\n"
            "| table incident_id detected_at classified_at notified_at intermediate_at final_at detect_to_classify_h classify_to_initial_h initial_to_inter_h inter_to_final_h SLA_breached"
        ),
        description="Measures, per major ICT incident, the elapsed time between detection, classification, initial notification, intermediate notification, and final report. Any SLA breach against the DORA Art.17 + ESA RTS timeline (24h initial / 72h intermediate / 30d final) sets SLA_breached=1 and triggers a finding.",
        value="Supervisors under DORA request the per-incident clock evidence. This UC produces it automatically, so the entity can prove the notification workflow was operated within the required windows or identify the exact root cause of a miss.",
        implementation="(1) Normalise detected_at/classified_at/notified_at/intermediate_at/final_at in the IR tool; (2) tag major incidents at classification; (3) schedule UC every 5m; (4) SLA_breached=1 escalates to CISO + Head of IR; (5) monthly roll-up to Board; (6) annual tabletop exercise validates clock fidelity.",
        visualization="Per-incident Gantt of phase durations, timechart of breaches per quarter, single value 'open incidents at risk of SLA breach in next 4h'.",
        cim_models=["Alerts", "Ticket Management"],
        known_fp="Incidents re-classified as non-major after initial raise can show a misleading 'breach' until tag::major_incident is cleared — dedup on latest tag state before computing SLAs.",
        required_fields=["incident_id", "detected_at", "classified_at", "notified_at", "_time"],
        compliance=[
            c_dora("Art.17", "full",
                   "Art.17(1) requires an ICT-related incident management process; Art.19(4) + the RTS impose the 24h/72h/30d notification clock this UC measures."),
            c_nis2("Art.23", "full",
                   "NIS2 Art.23 incident notification — the same clock structure applies, so this UC double-counts for both frameworks in financial entities subject to both."),
            c_iso("A.5.24", "full",
                  "ISO/IEC 27001:2022 A.5.24 Information security incident management planning and preparation — directly evidenced."),
        ],
        control_test_positive="Injecting a synthetic major_incident with detected_at=-25h and no classified_at sets SLA_breached=1 on the next 5-min cycle.",
        control_test_negative="A major incident with detect→classify in 4h, classify→initial in 10h, initial→intermediate in 30h, intermediate→final in 15d returns SLA_breached=0.",
        control_test_attack_technique="T1090",
        mitre_attack=["T1090"],
    ),
    uc(
        id_="22.3.45",
        title="DORA Art.24 — Digital operational-resilience testing: test-plan execution attestation",
        criticality="high",
        difficulty="intermediate",
        owner="CISO",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT assess the quality of the test (not a TLPT scope tool); attests that the annual testing programme executed on time and the per-test evidence is present.",
        evidence="Saved search 'dora_art24_testing_attest' (daily) emits per test: test_id, test_type, scope_service, planned_date, actual_run_date, pass_fail, finding_count, evidence_complete (boolean), to the compliance_summary index.",
        data_sources="`index=testing` sourcetype=test:plan_execution (BAS/TLPT/DR runs); `index=ticketing` sourcetype=jira:issue (findings tickets); test-plan register `dora_test_plan.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup dora_test_plan.csv\n"
            "| eval planned_date_et=strptime(planned_date,\"%Y-%m-%d\")\n"
            "| join type=outer test_id\n"
            "  [search index=testing sourcetype=test:plan_execution\n"
            "   | stats latest(_time) AS actual_run_time latest(pass_fail) AS pass_fail sum(finding_count) AS finding_count BY test_id]\n"
            "| eval evidence_complete=if(isnotnull(actual_run_time),1,0)\n"
            "| eval on_time=if(actual_run_time<=planned_date_et+86400*14,1,0)\n"
            "| table test_id test_type scope_service planned_date actual_run_time pass_fail finding_count evidence_complete on_time"
        ),
        description="Pivots the DORA test-plan register against the actual execution telemetry from the BAS/TLPT/DR tooling. Each planned test either has matching execution evidence within a 14-day tolerance or it does not — the latter is a direct Art.24 non-conformance.",
        value="Gives the CISO and the ICT risk committee a single-query attestation that the operational-resilience testing programme executed as planned, replacing an email-based reconciliation that typically slips by weeks.",
        implementation="(1) Maintain dora_test_plan.csv as the approved annual programme; (2) normalise execution output from BAS/DR tools to sourcetype=test:plan_execution; (3) schedule UC daily; (4) evidence_complete=0 past planned_date + 14d escalates to CISO; (5) per-quarter report to Board; (6) missing TLPT for significant entities escalates immediately.",
        visualization="Calendar heatmap of test executions, bar chart of findings per scope service, single value 'tests past due'.",
        cim_models=["Change"],
        known_fp="Tests rescheduled due to change freeze produce a legitimate gap — record the rescheduled_date and rebase the 14d tolerance.",
        required_fields=["test_id", "planned_date", "actual_run_time", "pass_fail"],
        compliance=[
            c_dora("Art.24", "full",
                   "Art.24 requires an established digital operational-resilience testing programme; evidencing that the plan executed with per-test evidence is the direct control output."),
            c_iso("A.5.29", "partial",
                  "ISO/IEC 27001:2022 A.5.29 Information security during disruption — related; DR scope overlaps with the testing programme."),
            c_nist53("CA-8", "contributing",
                     "NIST 800-53 CA-8 Penetration Testing — contributing evidence for the penetration-test subset of the plan."),
        ],
        control_test_positive="Removing a planned test's execution record from index=testing past its planned_date+14d causes the UC to flag evidence_complete=0 on the next daily run.",
        control_test_negative="A test with a recorded actual_run_time within the tolerance window reports evidence_complete=1, on_time=1.",
        control_test_attack_technique="T1562",
        mitre_attack=["T1562"],
    ),
]


# ---------------------------------------------------------------------------
# ISO/IEC 27001:2022 — 10 UCs (22.6.46 .. 22.6.55)
# ---------------------------------------------------------------------------

ISO_UCS: List[Dict] = [
    uc(
        id_="22.6.46",
        title="ISO/IEC 27001:2022 Clause 6.1 — Risk-assessment evidence: live risk register decay",
        criticality="high",
        difficulty="intermediate",
        owner="CISO",
        control_family="board-exec-reporting",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT evaluate the qualitative content of the risk assessment; surfaces risks whose last_reviewed timestamp exceeds the ISMS-defined review cadence.",
        evidence="Saved search 'iso_27001_6_1_risk_decay' (daily) outputs per risk: risk_id, category, owner, last_reviewed, days_overdue, to compliance_summary.",
        data_sources="`index=grc` sourcetype=archer:risk OR sourcetype=servicenow:grc_risk; ISMS cadence lookup `iso_27001_risk_cadence.csv` (per category, review frequency in days).",
        app="Splunk Enterprise Security, Splunk Add-on for ServiceNow",
        spl=(
            "index=grc sourcetype IN (archer:risk,servicenow:grc_risk) earliest=-1d\n"
            "| stats latest(last_reviewed) AS last_reviewed latest(category) AS category latest(owner) AS owner BY risk_id\n"
            "| lookup iso_27001_risk_cadence.csv category OUTPUT cadence_days\n"
            "| eval days_overdue=round((now()-last_reviewed)/86400,0)-cadence_days\n"
            "| where days_overdue>0\n"
            "| table risk_id category owner last_reviewed cadence_days days_overdue"
        ),
        description="Continuously measures how many risks in the register are past their per-category review cadence. Clause 6.1 requires planning that 'addresses risks and opportunities'; a register that has decayed is not planning.",
        value="Produces the evidence the external auditor expects at stage-2: proof that each risk line in the ISMS register was reviewed within its cadence, identifying exact owners of overdue entries.",
        implementation="(1) Export GRC risk register daily to Splunk; (2) maintain iso_27001_risk_cadence.csv by risk category; (3) schedule UC daily; (4) overdue > 0 opens a task to the risk owner; (5) Board quarterly report uses the rolling 90-day mean of overdue risks.",
        visualization="Histogram of days_overdue by category, table of top-overdue risks, single value 'total risks overdue today'.",
        cim_models=["Change"],
        known_fp="Category cadence changes introduced via ISMS committee need a 24h propagation grace — suppress new overdue hits for 24h after the lookup change.",
        required_fields=["risk_id", "last_reviewed", "category", "owner", "_time"],
        compliance=[
            c_iso("6.1", "full",
                  "Clause 6.1 requires planning to address risks and opportunities; measurable cadence adherence is the direct evidence."),
            c_nist53("PM-9", "contributing",
                     "NIST 800-53 PM-9 Risk Management Strategy — register review cadence is one component of the strategy's operation."),
            c_dora("Art.6", "partial",
                   "DORA Art.6 — the same register is commonly reused by financial entities; review cadence is one maintenance dimension."),
        ],
        control_test_positive="Setting a test risk's last_reviewed to now()-cadence_days-7d causes the UC to surface it with days_overdue=7.",
        control_test_negative="A risk reviewed within its cadence window is absent from the output.",
    ),
    uc(
        id_="22.6.47",
        title="ISO/IEC 27001:2022 Clause 6.2 — Information-security objectives: measurable-target attainment",
        criticality="medium",
        difficulty="intermediate",
        owner="CISO",
        control_family="board-exec-reporting",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT synthesise objectives; consumes the objectives the ISMS committee has set and reports current attainment against the numeric target for each.",
        evidence="Saved search 'iso_27001_6_2_objective_attainment' (daily) emits per objective: objective_id, target, current, attainment_pct, trend_7d, status, to compliance_summary.",
        data_sources="`index=compliance` sourcetype=isms:objective_result (push from ISMS KPIs); objective targets lookup `iso_27001_objectives.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup iso_27001_objectives.csv\n"
            "| join type=outer objective_id\n"
            "  [search index=compliance sourcetype=isms:objective_result earliest=-30d\n"
            "   | stats latest(value) AS current latest(_time) AS measured_at BY objective_id\n"
            "   | eval measured_at=strftime(measured_at,\"%Y-%m-%d\")]\n"
            "| eval attainment_pct=round(100*current/target,1)\n"
            "| eval status=if(attainment_pct>=100,\"met\",\"below_target\")\n"
            "| table objective_id target current attainment_pct measured_at status"
        ),
        description="Aligns every Clause 6.2 numeric objective (e.g., 'mean-time-to-patch <30d', 'phishing click rate <3%', 'privileged-session-recording coverage >95%') against its live value. The table is the quarterly Board report.",
        value="Replaces the manual spreadsheet most ISMS programmes use to report objective attainment. Auditors see the live measurement, the target, and the last update in a single reproducible query.",
        implementation="(1) Push each KPI to index=compliance nightly with objective_id tag; (2) maintain iso_27001_objectives.csv as the ISMS-committee-approved target list; (3) schedule UC daily; (4) status=below_target opens an ISMS action; (5) quarterly Board pack exports the table.",
        visualization="Bullet chart of attainment % vs target, line chart of 30-day trend per objective, single value 'objectives below target'.",
        cim_models=["N/A"],
        known_fp="Objective targets revised by the ISMS committee within the look-back window create an apparent regression — use the effective-from column in the lookup to compute status.",
        required_fields=["objective_id", "value", "_time"],
        compliance=[
            c_iso("6.2", "full",
                  "Clause 6.2 requires information-security objectives to be measurable; live attainment against the documented target is the direct evidence."),
            c_iso("9.1", "partial",
                  "Clause 9.1 (monitoring, measurement, analysis, evaluation) — same measurements feed it."),
            c_nist53("PM-6", "contributing",
                     "NIST 800-53 PM-6 Measures of Performance — contributes evidence."),
        ],
        control_test_positive="An objective whose current value is below its target returns status=below_target in the next daily run.",
        control_test_negative="An objective meeting its target returns status=met.",
    ),
    uc(
        id_="22.6.48",
        title="ISO/IEC 27001:2022 Clause 8.2 — Operational risk-assessment: per-change risk-score recalculation",
        criticality="high",
        difficulty="advanced",
        owner="CISO",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT replace the architect's design review; detects only that a material change (asset scope, data classification, exposure) occurred without a corresponding risk-score recalculation within 7 days.",
        evidence="Saved search 'iso_27001_8_2_change_risk_recalc' (daily) outputs per change: change_id, asset, old_score, new_score, delta, recalc_performed, to compliance_summary.",
        data_sources="`index=change` sourcetype=servicenow:change; `index=grc` sourcetype=archer:risk_score; change-to-risk mapping `iso_27001_change_to_risk.csv`.",
        app="Splunk Enterprise Security, Splunk Add-on for ServiceNow",
        spl=(
            "index=change sourcetype=servicenow:change state=closed earliest=-14d\n"
            "| rename affected_ci AS asset\n"
            "| lookup iso_27001_change_to_risk.csv asset OUTPUT risk_id\n"
            "| join type=outer risk_id\n"
            "  [search index=grc sourcetype=archer:risk_score earliest=-14d\n"
            "   | stats latest(score) AS new_score earliest(score) AS old_score latest(_time) AS recalc_time BY risk_id]\n"
            "| eval delta=new_score-old_score\n"
            "| eval recalc_performed=if(recalc_time>=_time AND recalc_time<=_time+604800,1,0)\n"
            "| where recalc_performed=0 AND abs(delta)>0\n"
            "| table change_id asset risk_id old_score new_score delta recalc_performed"
        ),
        description="Joins closed changes against their linked risk-register entries and asserts that a score recalculation was produced within 7 days. Clause 8.2 requires the organisation to perform information-security risk assessments 'at planned intervals or when significant changes are proposed' — this UC is the 'significant change' trigger.",
        value="Gives Clause 8.2 an operational verification signal instead of an annual narrative. Audit objection 'where is the evidence the risk was reassessed after the 2024-Q3 PCI change?' becomes a one-query answer.",
        implementation="(1) Link every CMDB change to affected risks in iso_27001_change_to_risk.csv; (2) normalise Archer risk_score events; (3) schedule UC daily; (4) recalc_performed=0 opens an ISMS action to the risk owner; (5) monthly report to risk committee.",
        visualization="Scatter of change impact vs recalc latency, table of changes missing recalc, single value 'changes in 14d missing recalc'.",
        cim_models=["Change"],
        known_fp="Changes categorised 'standard' (no risk implication) should be excluded — filter on change_category!='standard' in the base search.",
        required_fields=["change_id", "affected_ci", "state", "_time"],
        compliance=[
            c_iso("8.2", "full",
                  "Clause 8.2 Information security risk assessment at planned intervals or on significant change — directly evidenced."),
            c_iso("6.1", "partial",
                  "Clause 6.1 Actions to address risks and opportunities — related."),
            c_nist53("RA-3", "partial",
                     "NIST 800-53 RA-3 Risk Assessment — contributes."),
        ],
        control_test_positive="A closed change whose linked risk_id shows no change in score within 7d sets recalc_performed=0 and appears in the report.",
        control_test_negative="A change followed by a score update within 7d is absent.",
    ),
    uc(
        id_="22.6.49",
        title="ISO/IEC 27001:2022 Clause 9.1 — Monitoring programme coverage: KPI telemetry uptime",
        criticality="high",
        difficulty="intermediate",
        owner="Head of Platform",
        control_family="log-source-completeness",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Platform",
        monitoring_type=["Compliance", "Availability"],
        exclusions="Does NOT evaluate KPI correctness; detects KPIs whose data pipeline has been silent beyond their contracted freshness window, which means the monitoring programme itself has decayed.",
        evidence="Saved search 'iso_27001_9_1_kpi_uptime' (every 15m) emits per KPI: kpi_id, last_seen, sla_minutes, is_stale, to compliance_summary.",
        data_sources="`index=_internal` sourcetype=splunkd (scheduler logs); `index=compliance` sourcetype=isms:objective_result; KPI freshness lookup `iso_27001_kpi_freshness.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup iso_27001_kpi_freshness.csv\n"
            "| join type=outer kpi_id\n"
            "  [search index=compliance sourcetype=isms:objective_result earliest=-7d\n"
            "   | stats latest(_time) AS last_seen BY kpi_id]\n"
            "| eval age_min=round((now()-last_seen)/60,0)\n"
            "| eval is_stale=if(age_min>sla_minutes OR isnull(last_seen),1,0)\n"
            "| table kpi_id last_seen age_min sla_minutes is_stale"
        ),
        description="For every ISMS KPI the committee has agreed to measure under Clause 9.1, check the pipeline is alive within the KPI's freshness SLA. Stale pipelines are a silent failure mode of monitoring programmes.",
        value="Prevents the worst external-audit outcome (monitoring 'was in place' but had silently died) and gives the Head of Platform a single dashboard tile showing ISMS telemetry health.",
        implementation="(1) Push each KPI into index=compliance; (2) maintain iso_27001_kpi_freshness.csv per KPI with its SLA; (3) schedule UC every 15m; (4) is_stale=1 pages the data-engineering owner of the KPI; (5) weekly ISMS report attaches the latest state.",
        visualization="Heatmap of KPI staleness, table of stale KPIs, single value 'stale KPIs right now'.",
        cim_models=["Performance"],
        known_fp="KPI suspended during maintenance windows legitimately shows as stale — exclude with a maintenance_calendar.csv lookup.",
        required_fields=["kpi_id", "_time"],
        compliance=[
            c_iso("9.1", "full",
                  "Clause 9.1 requires monitoring, measurement, analysis, and evaluation; proof the telemetry is alive is a prerequisite for the rest of the clause."),
            c_nist53("CA-7", "partial",
                     "NIST 800-53 CA-7 Continuous Monitoring — contributing evidence."),
            c_soc2("CC7.1", "partial",
                   "SOC 2 CC7.1 System Operations Monitoring — contributing."),
        ],
        control_test_positive="Stopping the data-engineering job for kpi_id=patch_mttr for 1h past its sla_minutes sets is_stale=1.",
        control_test_negative="A KPI posting within sla_minutes is absent.",
    ),
    uc(
        id_="22.6.50",
        title="ISO/IEC 27001:2022 Clause 9.2 — Internal audit coverage: control sample rotation",
        criticality="medium",
        difficulty="intermediate",
        owner="Board / Audit Committee",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT perform the audit; attests that the internal-audit programme has exercised at least N% of ISMS controls over the rolling year and that no control was audited twice while another was never audited.",
        evidence="Saved search 'iso_27001_9_2_audit_rotation' (weekly) emits: control_id, last_audited, audit_count_365d, due_for_audit, to compliance_summary.",
        data_sources="`index=grc` sourcetype=archer:audit_test OR sourcetype=servicenow:audit_finding; ISMS control catalogue `iso_27001_control_catalog.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup iso_27001_control_catalog.csv\n"
            "| join type=outer control_id\n"
            "  [search index=grc sourcetype IN (archer:audit_test,servicenow:audit_finding) earliest=-365d\n"
            "   | stats latest(_time) AS last_audited count AS audit_count_365d BY control_id]\n"
            "| eval days_since=round((now()-last_audited)/86400,0)\n"
            "| eval due_for_audit=if(isnull(last_audited) OR days_since>365,1,0)\n"
            "| table control_id category last_audited days_since audit_count_365d due_for_audit"
        ),
        description="Joins the ISMS control catalogue with internal-audit test records over the trailing 365 days. The output tells the Audit Committee which controls are overdue.",
        value="Closes the typical gap where internal audit over-samples 'hot' controls and silently skips administrative ones. The rotation evidence is what ISO 9.2 requires and what the registrar looks for.",
        implementation="(1) Maintain iso_27001_control_catalog.csv; (2) require internal-audit output to index=grc with control_id tag; (3) schedule UC weekly; (4) due_for_audit=1 adds the control to the next quarter audit plan; (5) annual Audit Committee report.",
        visualization="Stacked bar of audit count by category, table of overdue controls, single value 'controls never audited'.",
        cim_models=["N/A"],
        known_fp="Controls retired in-year but still in catalog produce false 'overdue' entries — mark retired=true in the lookup.",
        required_fields=["control_id", "_time"],
        compliance=[
            c_iso("9.2", "full",
                  "Clause 9.2 requires an internal-audit programme exercised at planned intervals; rotation evidence directly satisfies the planned-interval requirement."),
            c_soc2("CC4.1", "contributing",
                   "SOC 2 CC4.1 — monitoring effectiveness of controls, contributing."),
            c_nist53("CA-2", "contributing",
                     "NIST 800-53 CA-2 Control Assessments — contributing."),
        ],
        control_test_positive="A catalog control with no audit_test events in 365d returns due_for_audit=1 in the weekly run.",
        control_test_negative="A control audited within the window is absent from the overdue table.",
    ),
    uc(
        id_="22.6.51",
        title="ISO/IEC 27001:2022 Annex A.5.24 — Incident-management planning: runbook currency attestation",
        criticality="medium",
        difficulty="beginner",
        owner="Head of IR",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT rate runbook quality; detects runbooks past their review cadence or never reviewed.",
        evidence="Saved search 'iso_27001_a_5_24_runbook_currency' (daily) emits: runbook_id, last_reviewed, cadence_days, is_stale, owner, to compliance_summary.",
        data_sources="`index=soar` sourcetype=phantom:playbook OR sourcetype=runbook:metadata; runbook register lookup `ir_runbook_register.csv`.",
        app="Splunk SOAR",
        spl=(
            "| inputlookup ir_runbook_register.csv\n"
            "| eval last_reviewed=strptime(last_reviewed,\"%Y-%m-%d\")\n"
            "| eval age_days=round((now()-last_reviewed)/86400,0)\n"
            "| eval is_stale=if(age_days>cadence_days,1,0)\n"
            "| where is_stale=1\n"
            "| table runbook_id owner last_reviewed age_days cadence_days is_stale"
        ),
        description="Flags runbooks past their configured review cadence so the IR team can recertify them before an incident proves they are stale.",
        value="Satisfies the A.5.24 'planning and preparation' sub-requirement: incident procedures are continuously refreshed, not one-time written.",
        implementation="(1) Maintain ir_runbook_register.csv with owner + cadence_days; (2) schedule UC daily; (3) stale runbooks open a recertification task to the owner with 14d SLA; (4) monthly IR committee review.",
        visualization="Table of stale runbooks by owner, single value 'stale runbooks', bar chart of age by runbook family.",
        cim_models=["N/A"],
        known_fp="Runbooks under active revision have an incomplete last_reviewed — exclude where state=in_review.",
        required_fields=["runbook_id", "last_reviewed", "cadence_days"],
        compliance=[
            c_iso("A.5.24", "full",
                  "A.5.24 Information security incident-management planning and preparation — runbook recency is a direct prerequisite."),
            c_dora("Art.17", "partial",
                   "DORA Art.17 incident-management process — contributes."),
            c_nist53("IR-4", "contributing",
                     "NIST 800-53 IR-4 Incident Handling — contributes."),
        ],
        control_test_positive="Setting a runbook's last_reviewed to now()-cadence_days-1d returns is_stale=1.",
        control_test_negative="A runbook reviewed within its cadence is not in the output.",
    ),
    uc(
        id_="22.6.52",
        title="ISO/IEC 27001:2022 Annex A.5.25 — Event classification decisions: SIEM-to-incident triage traceability",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Correlation",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT judge whether the classification was correct; asserts that every high-severity SIEM alert has a documented classification decision within the configured SLA.",
        evidence="Saved search 'iso_27001_a_5_25_event_classification' (every 10m) emits: alert_id, severity, classified_at, decision, decision_sla_met, to compliance_summary.",
        data_sources="`index=notable` (ES notable events); `index=soar` sourcetype=phantom:incident (classification decisions).",
        app="Splunk Enterprise Security, Splunk SOAR",
        spl=(
            "search `notable` severity IN (\"high\",\"critical\") earliest=-7d\n"
            "| rename event_id AS alert_id\n"
            "| join type=outer alert_id\n"
            "  [search index=soar sourcetype=phantom:incident earliest=-7d\n"
            "   | stats latest(_time) AS classified_at latest(decision) AS decision BY alert_id]\n"
            "| eval decision_sla_met=if(classified_at<=_time+3600,1,0)\n"
            "| where isnull(decision) OR decision_sla_met=0\n"
            "| table alert_id severity _time classified_at decision decision_sla_met"
        ),
        description="Measures whether every high/critical SIEM alert received a classification decision (incident / false-positive / suppressed) within the 1h SLA implied by A.5.25.",
        value="Gives the Audit Committee a single number: 'classification SLA adherence %'. Analysts know their backlog, auditors see the proof.",
        implementation="(1) Ensure SOAR writes classification decisions with alert_id tag; (2) schedule UC every 10m; (3) SLA miss escalates to shift lead; (4) daily SOC report of adherence %; (5) monthly to Audit Committee.",
        visualization="Funnel from total alerts → classified → on-time, line chart of adherence %, single value 'open unclassified alerts'.",
        cim_models=["Alerts", "Ticket Management"],
        known_fp="Alerts suppressed by tuning rules do not need classification decisions — filter out suppression_reason IS NOT NULL.",
        required_fields=["alert_id", "severity", "_time"],
        compliance=[
            c_iso("A.5.25", "full",
                  "A.5.25 Assessment and decision on information security events — directly measured by this UC."),
            c_soc2("CC7.3", "full",
                   "SOC 2 CC7.3 Evaluated events and incidents — aligns."),
            c_dora("Art.17", "partial",
                   "DORA Art.17 — contributes to the classification step of the incident lifecycle."),
            c_nist53("IR-4", "contributing",
                     "NIST 800-53 IR-4 Incident Handling — contributes."),
        ],
        control_test_positive="A high-severity notable with no phantom:incident record within 1h returns decision_sla_met=0.",
        control_test_negative="A critical alert followed by a classification decision within 30 minutes is absent.",
        control_test_attack_technique="T1070",
        mitre_attack=["T1070"],
    ),
    uc(
        id_="22.6.53",
        title="ISO/IEC 27001:2022 Clause 7.2 — Competence evidence: role-based training completion",
        criticality="medium",
        difficulty="beginner",
        owner="HR",
        control_family="training-effectiveness",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Platform",
        monitoring_type=["Compliance"],
        exclusions="Does NOT assess training effectiveness; attests that role-required modules are completed within policy cadence by each person in the role.",
        evidence="Saved search 'iso_27001_7_2_competence' (daily) emits per person: user, role, required_modules, completed_modules, compliance_pct, to compliance_summary.",
        data_sources="`index=hr` sourcetype=lms:completion; `index=hr` sourcetype=hr:role_assignment; required-module matrix `iso_27001_training_matrix.csv`.",
        app="Splunk Add-on for Microsoft Windows (742)",
        spl=(
            "index=hr sourcetype=hr:role_assignment earliest=-30d\n"
            "| stats latest(role) AS role BY user\n"
            "| lookup iso_27001_training_matrix.csv role OUTPUT required_modules\n"
            "| eval required_modules=split(required_modules,\",\")\n"
            "| join user\n"
            "  [search index=hr sourcetype=lms:completion status=completed earliest=-365d\n"
            "   | stats values(module) AS completed_modules BY user]\n"
            "| eval covered=mvmap(required_modules, if(isnotnull(mvfind(completed_modules,x)),1,0))\n"
            "| eval compliance_pct=round(100*sum(covered)/mvcount(required_modules),0)\n"
            "| where compliance_pct<100\n"
            "| table user role required_modules completed_modules compliance_pct"
        ),
        description="Joins the role-to-module matrix against LMS completions to report each person's coverage. Clause 7.2 requires the organisation to determine and maintain competence.",
        value="Replaces the annual LMS export with a daily compliance signal. HR can notify managers proactively rather than after the audit finding.",
        implementation="(1) Onboard LMS completions; (2) maintain iso_27001_training_matrix.csv per role; (3) schedule UC daily; (4) compliance_pct<100 triggers an HR email; (5) quarterly report to ISMS committee.",
        visualization="Stacked bar by role, table of sub-100% users, single value 'users below 100%'.",
        cim_models=["N/A"],
        known_fp="New hires in their grace window (30d) appear as non-compliant — exclude by hire_date.",
        required_fields=["user", "role", "module", "status", "_time"],
        compliance=[
            c_iso("7.2", "full",
                  "Clause 7.2 Competence — directly evidenced by role-based module completion."),
            c_hipaa("§164.308(a)(5)", "partial",
                    "HIPAA Security §164.308(a)(5) Security Awareness and Training — contributes."),
            c_pci("12.6", "partial",
                  "PCI-DSS 12.6 Security awareness programme — contributes."),
        ],
        control_test_positive="A user missing a required module shows compliance_pct<100 in the next daily run.",
        control_test_negative="A user with all required modules completed within cadence is absent.",
    ),
    uc(
        id_="22.6.54",
        title="ISO/IEC 27001:2022 Clause 7.5 — Documented information control: policy register approval trail",
        criticality="medium",
        difficulty="intermediate",
        owner="CISO",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT edit policies; detects policy register entries missing an approval record or past their review cadence.",
        evidence="Saved search 'iso_27001_7_5_policy_trail' (weekly) emits per policy: policy_id, version, approved_by, approved_at, days_to_next_review, to compliance_summary.",
        data_sources="`index=grc` sourcetype=policyhub:policy (change of state); policy cadence lookup `iso_27001_policy_cadence.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "index=grc sourcetype=policyhub:policy action=approved earliest=-400d\n"
            "| stats latest(_time) AS approved_at latest(version) AS version latest(approved_by) AS approved_by BY policy_id\n"
            "| lookup iso_27001_policy_cadence.csv policy_id OUTPUT cadence_days owner\n"
            "| eval days_to_next_review=cadence_days-round((now()-approved_at)/86400,0)\n"
            "| where days_to_next_review<=30 OR isnull(approved_at)\n"
            "| table policy_id version approved_by approved_at days_to_next_review owner"
        ),
        description="For every policy in the register, produce the last approval record and the time to the next review. Policies within 30 days of expiry or with no approval record are surfaced for action.",
        value="Prevents the common deficiency of policies that 'used to be' approved but whose approval trail has expired — a direct Clause 7.5 non-conformance.",
        implementation="(1) Route policyhub approval events into index=grc; (2) maintain iso_27001_policy_cadence.csv; (3) schedule UC weekly; (4) days_to_next_review<=30 opens a review task to policy owner; (5) quarterly CISO review.",
        visualization="Table of near-expiry policies, bar chart by owner, single value 'policies expired'.",
        cim_models=["Change"],
        known_fp="Newly-issued policies within 30 days of issue appear as near-expiry until the first cadence period completes — exclude if age<30d.",
        required_fields=["policy_id", "approved_at", "approved_by", "version", "_time"],
        compliance=[
            c_iso("7.5", "full",
                  "Clause 7.5 Documented information — approval trail + cadence adherence directly evidenced."),
            c_soc2("CC1.4", "partial",
                   "SOC 2 CC1.4 — contributes to commitment-and-accountability evidence."),
            c_nist53("PL-2", "contributing",
                     "NIST 800-53 PL-2 System Security Plan — contributes."),
        ],
        control_test_positive="Setting a policy's approval to now()-cadence_days+29d returns days_to_next_review=1 (near-expiry).",
        control_test_negative="A policy with a recent approval and 200 days remaining is absent.",
    ),
    uc(
        id_="22.6.55",
        title="ISO/IEC 27001:2022 Clause 8.1 — Operational planning: change advisory board (CAB) approval evidence",
        criticality="medium",
        difficulty="intermediate",
        owner="Head of IT Operations",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="IT Operations",
        monitoring_type=["Compliance"],
        exclusions="Does NOT approve or reject changes; attests that 'normal' and 'emergency' changes have the required CAB approval record before implementation.",
        evidence="Saved search 'iso_27001_8_1_cab_approval' (hourly) emits per change: change_id, type, implemented_at, cab_approved_at, approval_met, approver, to compliance_summary.",
        data_sources="`index=change` sourcetype=servicenow:change; approver-role lookup `cab_roles.csv`.",
        app="Splunk Add-on for ServiceNow",
        spl=(
            "index=change sourcetype=servicenow:change state IN (implemented,closed) earliest=-7d\n"
            "| stats latest(type) AS type latest(_time) AS implemented_at latest(approval_status) AS approval_status latest(approver) AS approver latest(approval_date) AS cab_approved_at BY change_id\n"
            "| lookup cab_roles.csv approver OUTPUT is_authorised_cab\n"
            "| eval approval_met=if(type=\"emergency\",1,if(approval_status=\"approved\" AND is_authorised_cab=1 AND cab_approved_at<=implemented_at,1,0))\n"
            "| where approval_met=0\n"
            "| table change_id type implemented_at cab_approved_at approver approval_met"
        ),
        description="Flags implemented changes that were not approved by an authorised CAB member prior to implementation. Clause 8.1 requires the organisation to plan, implement and control processes to meet information-security requirements — CAB approval is the direct control.",
        value="Turns the 'post-implementation review' into a pre-emptive signal. The Head of IT Operations sees the breach list within the hour.",
        implementation="(1) Export ServiceNow change events; (2) maintain cab_roles.csv listing authorised approvers; (3) schedule UC hourly; (4) approval_met=0 opens a deficiency record with 7d remediation; (5) monthly Audit Committee report.",
        visualization="Table of unapproved changes, bar chart of breach count by team, single value 'unapproved changes in last 7d'.",
        cim_models=["Change"],
        known_fp="Emergency changes legitimately bypass CAB; their follow-up retrospective approval must exist separately — this UC excludes type=emergency by design.",
        required_fields=["change_id", "approver", "approval_status", "state", "_time"],
        compliance=[
            c_iso("8.1", "full",
                  "Clause 8.1 Operational planning and control — CAB approval adherence is the direct control signal."),
            c_sox("ITGC.ChangeMgmt.Approval", "full",
                  "SOX-ITGC ChangeMgmt.Approval — directly evidenced."),
            c_soc2("CC8.1", "partial",
                   "SOC 2 CC8.1 — change management — contributing."),
        ],
        control_test_positive="Closing a change with approval_status='rejected' but state='implemented' returns approval_met=0.",
        control_test_negative="A change approved by a CAB-role user before implementation is absent.",
    ),
]


# ---------------------------------------------------------------------------
# SOC 2 2017 TSC — 9 UCs (22.8.31 .. 22.8.39)
# ---------------------------------------------------------------------------

SOC2_UCS: List[Dict] = [
    uc(
        id_="22.8.31",
        title="SOC 2 CC6.6 — Encryption-in-transit validation: cleartext protocols crossing the trust boundary",
        criticality="high",
        difficulty="intermediate",
        owner="CISO",
        control_family="crypto-drift",
        security_domain="network",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT inspect payload; identifies sessions that negotiated plaintext or deprecated TLS versions crossing the production trust zone.",
        evidence="Saved search 'soc2_cc6_6_intransit_enc' (every 30m) outputs src, dest, dest_port, protocol, tls_version, is_deprecated, to compliance_summary.",
        data_sources="`index=stream` sourcetype=stream:tcp OR sourcetype=stream:http OR sourcetype=stream:tls; trust-zone lookup `trust_zones.csv`.",
        app="Splunk Stream",
        spl=(
            "index=stream sourcetype=stream:tls earliest=-30m\n"
            "| rename src_ip AS src dest_ip AS dest\n"
            "| lookup trust_zones.csv ip=src OUTPUT zone AS src_zone\n"
            "| lookup trust_zones.csv ip=dest OUTPUT zone AS dest_zone\n"
            "| where src_zone!=dest_zone\n"
            "| eval is_deprecated=if(tls_version IN (\"SSLv3\",\"TLS1.0\",\"TLS1.1\"),1,0)\n"
            "| where is_deprecated=1 OR protocol IN (\"http\",\"ftp\",\"telnet\",\"smtp\")\n"
            "| stats count BY src dest dest_port protocol tls_version is_deprecated"
        ),
        description="Detects sessions crossing trust-zone boundaries that negotiated plaintext or deprecated TLS (pre-TLS1.2). Under CC6.6 the service organisation must 'implement logical access security measures to protect against threats from sources outside its system boundaries'; plaintext at the boundary is the failure mode.",
        value="Replaces annual TLS-compliance scans with a continuous signal, so drift (a new container accidentally exposing http) is caught within 30 minutes.",
        implementation="(1) Onboard Splunk Stream TLS data; (2) maintain trust_zones.csv; (3) schedule UC every 30m; (4) each hit opens a Platform ticket with src/dest/dest_port; (5) SLA: remediate within 24h.",
        visualization="Sankey of src_zone → dest_zone by protocol, table of deprecated sessions, single value 'deprecated TLS sessions right now'.",
        cim_models=["Network_Traffic", "Certificates"],
        known_fp="Explicit plaintext management LANs (backup target, ILO) are allowlisted in trust_zones.csv via category='management-cleartext-allowed'.",
        required_fields=["src", "dest", "dest_port", "protocol", "tls_version", "_time"],
        compliance=[
            c_soc2("CC6.6", "full",
                   "CC6.6 Logical access security measures protect the boundary — cleartext crossing a trust boundary is the direct failure detected."),
            c_pci("4.2.1", "full",
                  "PCI-DSS 4.2.1 strong cryptography for transmission of cardholder data across open networks — directly evidenced."),
            c_iso("A.8.24", "full",
                  "ISO/IEC 27001:2022 A.8.24 Use of cryptography — directly evidenced."),
            c_hipaa("§164.312(e)(1)", "partial",
                    "HIPAA Security §164.312(e)(1) Transmission security — contributing."),
        ],
        control_test_positive="Initiating a deliberate http request across trust zones causes a hit within 30m naming the src/dest/protocol.",
        control_test_negative="A TLS1.2+ session with an approved cipher between two zones is absent.",
        control_test_attack_technique="T1071",
        mitre_attack=["T1071"],
    ),
    uc(
        id_="22.8.32",
        title="SOC 2 CC6.7 — System boundary & data-transmission control: unapproved egress destinations",
        criticality="high",
        difficulty="intermediate",
        owner="Head of Platform",
        control_family="data-flow-cross-border",
        security_domain="network",
        detection_type="Anomaly",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT block traffic; detects outbound flows whose destination ASN/country is absent from the approved-egress registry for the originating service.",
        evidence="Saved search 'soc2_cc6_7_egress_boundary' (every 15m) outputs src_service, dest_ip, dest_asn, dest_country, approved, to compliance_summary.",
        data_sources="`index=netfw` sourcetype=pan:traffic; ASN/country enrichment via `asn_country.csv`; approved-egress registry `approved_egress.csv`.",
        app="Splunk Add-on for Palo Alto Networks (2757)",
        spl=(
            "index=netfw sourcetype=pan:traffic action=allow direction=outbound earliest=-15m\n"
            "| rename src AS src_ip dest AS dest_ip\n"
            "| lookup service_by_src.csv src_ip OUTPUT src_service\n"
            "| lookup asn_country.csv ip=dest_ip OUTPUT asn AS dest_asn country AS dest_country\n"
            "| lookup approved_egress.csv src_service dest_asn OUTPUT approved\n"
            "| where isnull(approved) OR approved!=\"yes\"\n"
            "| stats count sum(bytes_out) AS bytes BY src_service dest_ip dest_asn dest_country"
        ),
        description="Evaluates outbound flows against the per-service approved-egress registry. A flow to an unapproved ASN or country is a direct CC6.7 boundary violation.",
        value="Provides the evidence SOC 2 auditors want: proof that outbound flows are governed and deviations are captured. Supports reduction of shadow SaaS risk.",
        implementation="(1) Enrich Palo Alto traffic with service/ASN/country; (2) maintain approved_egress.csv; (3) schedule UC every 15m; (4) hit opens a ticket to service owner; (5) 48h SLA; (6) weekly review by Platform team.",
        visualization="Geo map of unapproved destinations, bar chart by service, single value 'unapproved egress flows (1h)'.",
        cim_models=["Network_Traffic"],
        known_fp="Public CDNs and package mirrors that use anycast may produce transient country churn — allowlist by ASN in approved_egress.csv.",
        required_fields=["src_ip", "dest_ip", "dest_port", "bytes_out", "_time"],
        compliance=[
            c_soc2("CC6.7", "full",
                   "CC6.7 Information transmission and disposal — unapproved egress is the direct failure."),
            c_iso("A.8.23", "partial",
                  "ISO/IEC 27001:2022 A.8.23 Web filtering — contributing."),
            c_pci("1.3.1", "partial",
                  "PCI-DSS 1.3.1 traffic to and from the CDE — contributing."),
            c_dora("Art.7", "partial",
                   "DORA Art.7 — contributing."),
        ],
        control_test_positive="An outbound flow from the payments service to an ASN not in approved_egress.csv is surfaced within 15m.",
        control_test_negative="A flow to an approved ASN+country tuple is absent.",
        control_test_attack_technique="T1041",
        mitre_attack=["T1041"],
    ),
    uc(
        id_="22.8.33",
        title="SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IT Operations",
        control_family="log-source-completeness",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="IT Operations",
        monitoring_type=["Compliance", "Availability"],
        exclusions="Does NOT redesign the monitoring stack; reports coverage (systems with heartbeat) + noise (alerts per system) so the monitoring programme is evaluable.",
        evidence="Saved search 'soc2_cc7_1_monitoring_ledger' (daily) emits per system: ci_id, heartbeat_last_seen, alerts_24h, coverage_status, to compliance_summary.",
        data_sources="`index=monitoring` sourcetype=heartbeat:agent; `index=alerts` sourcetype=opsgenie:alert; CMDB lookup `cmdb_ci_list.csv`.",
        app="Splunk IT Service Intelligence",
        spl=(
            "| inputlookup cmdb_ci_list.csv\n"
            "| join type=outer ci_id\n"
            "  [search index=monitoring sourcetype=heartbeat:agent earliest=-1d\n"
            "   | stats latest(_time) AS heartbeat_last_seen BY ci_id]\n"
            "| join type=outer ci_id\n"
            "  [search index=alerts sourcetype=opsgenie:alert earliest=-1d\n"
            "   | stats count AS alerts_24h BY ci_id]\n"
            "| eval coverage_status=case(isnull(heartbeat_last_seen),\"no-heartbeat\",heartbeat_last_seen<now()-1800,\"stale\",true(),\"healthy\")\n"
            "| table ci_id heartbeat_last_seen alerts_24h coverage_status"
        ),
        description="Pivots the CMDB CI list against live heartbeat and alert telemetry to measure which systems are monitored and how noisy they are. CC7.1 requires the entity to 'detect the occurrence of anomalies'; unheartbeated systems cannot be monitored.",
        value="Lets the Head of IT Operations present the Audit Committee with coverage % (target 100% for production) and alert-noise % (target <5/day/CI). The same query replaces three spreadsheets.",
        implementation="(1) Nightly CMDB sync; (2) heartbeat agent installed on every CI; (3) schedule UC daily; (4) no-heartbeat CIs open a task to IT Ops; (5) quarterly Audit Committee report.",
        visualization="Donut of coverage_status, top-10 noisiest CIs, single value 'coverage %'.",
        cim_models=["Performance", "Alerts"],
        known_fp="Decommissioned CIs legitimately stop heartbeats — mark retired=true in CMDB lookup.",
        required_fields=["ci_id", "_time"],
        compliance=[
            c_soc2("CC7.1", "full",
                   "CC7.1 System monitoring for anomalies — coverage + noise are the two programme health metrics."),
            c_iso("8.1", "partial",
                  "ISO/IEC 27001:2022 Clause 8.1 Operational planning and control — contributing."),
            c_nist53("SI-4", "partial",
                     "NIST 800-53 SI-4 System Monitoring — contributing."),
            c_dora("Art.10", "partial",
                   "DORA Art.10 Detection mechanisms — contributing."),
        ],
        control_test_positive="Stopping the heartbeat agent on a test CI for 31 minutes sets coverage_status='stale'.",
        control_test_negative="A CI heartbeating within 30m and with alerts_24h<5 reports healthy.",
    ),
    uc(
        id_="22.8.34",
        title="SOC 2 CC7.3 — Evaluated events: threshold breaches without documented rationale",
        criticality="medium",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Correlation",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT auto-classify events; identifies threshold breaches that closed without an analyst rationale field populated.",
        evidence="Saved search 'soc2_cc7_3_rationale_missing' (hourly) emits per alert: alert_id, severity, rationale_present, closed_at, analyst, to compliance_summary.",
        data_sources="`index=notable` (ES notable); `index=soar` sourcetype=phantom:incident.",
        app="Splunk Enterprise Security, Splunk SOAR",
        spl=(
            "search `notable` severity IN (\"medium\",\"high\",\"critical\") earliest=-7d\n"
            "| rename event_id AS alert_id\n"
            "| join type=outer alert_id\n"
            "  [search index=soar sourcetype=phantom:incident state=closed earliest=-7d\n"
            "   | stats latest(closed_at) AS closed_at latest(analyst) AS analyst latest(rationale) AS rationale BY alert_id]\n"
            "| eval rationale_present=if(len(rationale)>20,1,0)\n"
            "| where isnotnull(closed_at) AND rationale_present=0\n"
            "| table alert_id severity closed_at analyst rationale_present"
        ),
        description="CC7.3 requires the entity to evaluate events and incidents. Closing a threshold-breach event without a rationale field is a direct control failure.",
        value="Gives leadership proof that events are not only closed but justifiably closed. Auditors consider an 'auto-closed without rationale' event a material weakness.",
        implementation="(1) Enforce rationale field on SOAR close action; (2) schedule UC hourly; (3) rationale_present=0 reopens the alert for review; (4) weekly SOC report.",
        visualization="Stacked bar of alerts by analyst × rationale_present, single value 'closed-without-rationale'.",
        cim_models=["Alerts"],
        known_fp="Alerts closed by automation rules must use rationale='auto-closed:<rule_id>' rather than blank — reject blank in SOAR.",
        required_fields=["alert_id", "rationale", "closed_at", "analyst", "_time"],
        compliance=[
            c_soc2("CC7.3", "full",
                   "CC7.3 Evaluated events and incidents — rationale adherence is the direct signal."),
            c_iso("A.5.25", "partial",
                  "ISO/IEC 27001:2022 A.5.25 Event assessment — contributing."),
            c_dora("Art.17", "partial",
                   "DORA Art.17 Incident management process — contributing."),
        ],
        control_test_positive="Closing an ES notable via SOAR with empty rationale returns rationale_present=0 on the next hour.",
        control_test_negative="A close with a populated rationale >20 characters is absent.",
    ),
    uc(
        id_="22.8.35",
        title="SOC 2 CC7.4 — Incident response: post-incident review completion SLA",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT judge PIR content; asserts the PIR record exists with required fields within the policy-defined window after incident close.",
        evidence="Saved search 'soc2_cc7_4_pir_sla' (daily) emits per incident: incident_id, closed_at, pir_completed_at, pir_sla_met, to compliance_summary.",
        data_sources="`index=soar` sourcetype=phantom:incident; `index=ticketing` sourcetype=jira:issue (PIR project).",
        app="Splunk SOAR",
        spl=(
            "index=soar sourcetype=phantom:incident state=closed earliest=-30d\n"
            "| stats latest(closed_at) AS closed_at BY incident_id\n"
            "| join type=outer incident_id\n"
            "  [search index=ticketing sourcetype=jira:issue project=PIR earliest=-60d\n"
            "   | stats latest(_time) AS pir_completed_at BY incident_id]\n"
            "| eval pir_sla_met=if(isnotnull(pir_completed_at) AND pir_completed_at<=closed_at+604800,1,0)\n"
            "| where pir_sla_met=0\n"
            "| table incident_id closed_at pir_completed_at pir_sla_met"
        ),
        description="CC7.4 requires the entity to 'respond, including by establishing a post-incident review'. This UC measures 7-day PIR completion SLA per closed incident.",
        value="Surfaces PIR backlog before it becomes an audit finding. Board sees a rolling '% of PIRs on time' metric.",
        implementation="(1) Ensure PIR Jira project is populated; (2) schedule UC daily; (3) pir_sla_met=0 opens a reminder ticket; (4) weekly SOC report; (5) quarterly Board report.",
        visualization="Waterfall of incidents → PIR completed → on time, single value 'open incidents overdue PIR'.",
        cim_models=["Ticket Management"],
        known_fp="Incidents reopened and later re-closed legitimately extend the window — use latest(closed_at).",
        required_fields=["incident_id", "closed_at", "_time"],
        compliance=[
            c_soc2("CC7.4", "full",
                   "CC7.4 Incident response with post-incident review — SLA adherence is the direct control signal."),
            c_iso("A.5.26", "full",
                  "ISO/IEC 27001:2022 A.5.26 Response to information security incidents — contributing."),
            c_dora("Art.17", "partial",
                   "DORA Art.17 Incident management process — contributing."),
        ],
        control_test_positive="An incident closed 8 days ago with no PIR record returns pir_sla_met=0.",
        control_test_negative="An incident closed 3 days ago with a PIR created 4 days ago returns pir_sla_met=1.",
    ),
    uc(
        id_="22.8.36",
        title="SOC 2 CC1.1 — Integrity and ethical values: code-of-conduct acknowledgement trail",
        criticality="medium",
        difficulty="beginner",
        owner="HR",
        control_family="training-effectiveness",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Platform",
        monitoring_type=["Compliance"],
        exclusions="Does NOT test the substance of the code of conduct; attests that every active employee has acknowledged the current version within policy cadence.",
        evidence="Saved search 'soc2_cc1_1_coc_ack' (daily) emits per employee: user, hire_date, latest_ack_version, latest_ack_date, is_compliant, to compliance_summary.",
        data_sources="`index=hr` sourcetype=hr:employee (active roster); `index=hr` sourcetype=lms:acknowledgement; policy-version lookup `coc_versions.csv`.",
        app="Splunk Add-on for Microsoft Windows (742)",
        spl=(
            "index=hr sourcetype=hr:employee status=active earliest=-30d\n"
            "| stats latest(hire_date) AS hire_date BY user\n"
            "| join user type=outer\n"
            "  [search index=hr sourcetype=lms:acknowledgement module=code_of_conduct earliest=-2y\n"
            "   | stats latest(version) AS latest_ack_version latest(_time) AS latest_ack_date BY user]\n"
            "| lookup coc_versions.csv AS latest OUTPUT current_version\n"
            "| eval is_compliant=if(latest_ack_version==current_version AND latest_ack_date>now()-31536000,1,0)\n"
            "| where is_compliant=0\n"
            "| table user hire_date latest_ack_version latest_ack_date is_compliant"
        ),
        description="Surfaces active employees who have not acknowledged the current code-of-conduct version within the last 12 months.",
        value="Removes the audit finding 'CoC acknowledgement trail is incomplete' by making HR's coverage measurable daily.",
        implementation="(1) Nightly HR roster sync; (2) maintain coc_versions.csv; (3) schedule UC daily; (4) is_compliant=0 triggers an HR reminder email; (5) quarterly compliance report.",
        visualization="Table of non-acknowledging users, bar chart by department, single value 'non-compliant users'.",
        cim_models=["N/A"],
        known_fp="Employees within their 30-day grace window are excluded via hire_date.",
        required_fields=["user", "hire_date", "module", "version", "_time"],
        compliance=[
            c_soc2("CC1.1", "full",
                   "CC1.1 Integrity and ethical values — acknowledgement coverage is the direct evidence."),
            c_iso("6.3", "partial",
                  "ISO/IEC 27001:2022 Clause 6.3 Competence — contributing; the CoC is one training module."),
        ],
        control_test_positive="A user with no CoC acknowledgement in 13 months returns is_compliant=0.",
        control_test_negative="A user who acknowledged the current version within the year is absent.",
    ),
    uc(
        id_="22.8.37",
        title="SOC 2 CC9.1 — Risk-mitigation activity: vendor-risk action closure SLA",
        criticality="medium",
        difficulty="intermediate",
        owner="Procurement",
        control_family="third-party-activity",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT rate vendors; measures closure SLA for risk-mitigation actions from vendor assessments.",
        evidence="Saved search 'soc2_cc9_1_vendor_risk_sla' (daily) emits per action: action_id, vendor, severity, due_at, closed_at, sla_met, to compliance_summary.",
        data_sources="`index=grc` sourcetype=servicenow:vendor_risk; vendor register lookup `vendor_register.csv`.",
        app="Splunk Add-on for ServiceNow",
        spl=(
            "index=grc sourcetype=servicenow:vendor_risk state IN (open,closed) earliest=-120d\n"
            "| stats latest(state) AS state latest(severity) AS severity latest(due_at) AS due_at latest(closed_at) AS closed_at BY action_id vendor\n"
            "| eval sla_met=case(state=\"closed\" AND closed_at<=due_at,1,state=\"closed\",0,now()>due_at,0,true(),1)\n"
            "| where sla_met=0\n"
            "| table action_id vendor severity due_at closed_at sla_met"
        ),
        description="CC9.1 requires the entity to identify, select, and develop risk-mitigation activities. Closure SLA on vendor-risk actions is a direct control output.",
        value="Replaces the quarterly Procurement PowerPoint with a continuous signal. Top vendors with overdue actions are the first line of an Audit Committee brief.",
        implementation="(1) Route vendor_risk events from ServiceNow GRC; (2) maintain vendor_register.csv; (3) schedule UC daily; (4) sla_met=0 escalates per severity matrix; (5) monthly CISO report.",
        visualization="Table of overdue actions by vendor, bar chart of SLA adherence by severity, single value 'overdue vendor-risk actions'.",
        cim_models=["Change"],
        known_fp="Actions waiting on vendor response can be legitimately late — mark state='awaiting-vendor' and exclude.",
        required_fields=["action_id", "vendor", "severity", "due_at", "closed_at", "_time"],
        compliance=[
            c_soc2("CC9.1", "full",
                   "CC9.1 Risk mitigation — vendor-action closure is the direct evidence."),
            c_iso("A.5.19", "partial",
                  "ISO/IEC 27001:2022 A.5.19 Information security in supplier relationships — contributing."),
            c_dora("Art.28", "partial",
                   "DORA Art.28 ICT third-party risk — contributing."),
        ],
        control_test_positive="A high-severity action past due_at with state=open returns sla_met=0.",
        control_test_negative="A closed action that was closed before due_at is absent.",
    ),
    uc(
        id_="22.8.38",
        title="SOC 2 C1.1 — Confidentiality: sensitive-data exposure at the egress boundary",
        criticality="high",
        difficulty="advanced",
        owner="DPO",
        control_family="data-flow-cross-border",
        security_domain="network",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT intercept content; consumes DLP telemetry and focuses on confidential-class detections leaving the trust boundary to an unapproved destination.",
        evidence="Saved search 'soc2_c1_1_egress_confidential' (every 30m) emits per detection: dlp_policy, severity, user, dest, approved, to compliance_summary.",
        data_sources="`index=dlp` sourcetype=symantec:dlp OR sourcetype=microsoft:purview:dlp; approved-destination lookup `approved_egress.csv`.",
        app="Splunk Add-on for Microsoft Purview, Splunk Add-on for Symantec DLP",
        spl=(
            "index=dlp sourcetype IN (symantec:dlp,microsoft:purview:dlp) severity IN (\"high\",\"critical\") earliest=-30m\n"
            "| rename destination_ip AS dest policy_name AS dlp_policy\n"
            "| lookup approved_egress.csv dest OUTPUT approved\n"
            "| where approved!=\"yes\" OR isnull(approved)\n"
            "| stats count BY dlp_policy severity user dest approved"
        ),
        description="Surfaces DLP detections for confidential-class data whose destination is not in the approved-egress registry.",
        value="C1.1 confidentiality assurance hinges on continuous detection of data leaving the boundary. This UC gives the DPO a queryable control output.",
        implementation="(1) Onboard DLP; (2) maintain approved_egress.csv; (3) schedule UC every 30m; (4) hit opens a P1 to DPO + user's manager; (5) weekly DPO report.",
        visualization="Table of unapproved egress detections, bar chart by policy, single value 'new unapproved egress (1h)'.",
        cim_models=["Data Loss Prevention"],
        known_fp="Legitimate cross-tenant file shares with approved partners can produce detections — allowlist by partner in approved_egress.csv.",
        required_fields=["dlp_policy", "severity", "user", "destination_ip", "_time"],
        compliance=[
            c_soc2("C1.1", "full",
                   "C1.1 Confidentiality — continuous DLP boundary detection is the direct evidence."),
            c_iso("A.8.12", "full",
                  "ISO/IEC 27001:2022 A.8.12 Data leakage prevention — directly evidenced."),
            c_hipaa("§164.312(e)(1)", "partial",
                    "HIPAA Security §164.312(e)(1) Transmission security — contributing."),
            c_pci("10.6.2", "partial",
                  "PCI-DSS 10.6.2 Review logs for anomalies (applied to DLP) — contributing."),
        ],
        control_test_positive="A deliberate DLP test file containing cardholder PAN sent to an unlisted cloud-share triggers a hit within 30m.",
        control_test_negative="Confidential data sent to a partner with approved='yes' is absent.",
        control_test_attack_technique="T1048",
        mitre_attack=["T1048"],
    ),
    uc(
        id_="22.8.39",
        title="SOC 2 P1.1 — Privacy notice: consent-record freshness for privacy-notice version changes",
        criticality="medium",
        difficulty="intermediate",
        owner="DPO",
        control_family="data-subject-request-lifecycle",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT rewrite consent records; measures each data subject's consent version vs the current notice version.",
        evidence="Saved search 'soc2_p1_1_consent_freshness' (daily) emits per subject: subject_id, consent_version, current_version, days_stale, needs_refresh, to compliance_summary.",
        data_sources="`index=consent` sourcetype=onetrust:consent; privacy-notice version lookup `privacy_notice_versions.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "index=consent sourcetype=onetrust:consent earliest=-14d\n"
            "| stats latest(consent_version) AS consent_version latest(_time) AS consent_time BY subject_id\n"
            "| lookup privacy_notice_versions.csv AS latest OUTPUT current_version\n"
            "| eval days_stale=round((now()-consent_time)/86400,0)\n"
            "| eval needs_refresh=if(consent_version!=current_version,1,0)\n"
            "| where needs_refresh=1\n"
            "| table subject_id consent_version current_version days_stale needs_refresh"
        ),
        description="When the privacy notice changes version, subjects whose consent was against the old version must be re-prompted. This UC measures the backlog.",
        value="Prevents P1.1 findings: 'consent records reference a superseded notice'. Satisfies the '<v-current>' regulator question asked at every annual audit.",
        implementation="(1) Push consent changes to index=consent; (2) maintain privacy_notice_versions.csv; (3) schedule UC daily; (4) batch subjects needing refresh by cohort; (5) DPO owns the refresh campaign.",
        visualization="Timechart of stale consent backlog, table of cohorts, single value 'subjects needing refresh'.",
        cim_models=["N/A"],
        known_fp="Deceased/closed subject accounts legitimately have stale consent — exclude by account_state.",
        required_fields=["subject_id", "consent_version", "_time"],
        compliance=[
            c_soc2("P1.1", "full",
                   "P1.1 Privacy notice — consent-version adherence is the direct control."),
            {
                "regulation": "GDPR",
                "version": "2016/679",
                "clause": "Art.7",
                "clauseUrl": URL["gdpr"],
                "mode": "satisfies",
                "assurance": "partial",
                "assurance_rationale": "GDPR Art.7 conditions for consent — contributing when the privacy notice changes materially.",
            },
        ],
        control_test_positive="Bumping the privacy notice to v4 when a subject's consent is at v3 returns needs_refresh=1.",
        control_test_negative="A subject whose consent matches the current notice is absent.",
    ),
]


# ---------------------------------------------------------------------------
# PCI-DSS v4.0 — 16 UCs (22.11.91 .. 22.11.106)
# ---------------------------------------------------------------------------

PCI_UCS: List[Dict] = [
    uc(
        id_="22.11.91",
        title="PCI-DSS 1.3 — CDE network boundary: unauthorised flows between CDE and untrusted networks",
        criticality="critical",
        difficulty="intermediate",
        owner="Head of Platform",
        control_family="regulation-specific",
        security_domain="network",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT enforce the firewall (that is the NSC); detects allowed flows between CDE and untrusted zones that are not in the Req-1.2.1 approved list.",
        evidence="Saved search 'pci_1_3_cde_boundary' (every 15m) emits: src, src_zone, dest, dest_zone, dest_port, protocol, approved, to compliance_summary.",
        data_sources="`index=netfw` sourcetype IN (pan:traffic,cisco:asa); zone lookup `cde_zones.csv`; approved-flows lookup `pci_approved_flows.csv`.",
        app="Splunk Add-on for Palo Alto Networks (2757)",
        spl=(
            "index=netfw sourcetype IN (pan:traffic,cisco:asa) action=allow earliest=-15m\n"
            "| lookup cde_zones.csv ip=src OUTPUT zone AS src_zone\n"
            "| lookup cde_zones.csv ip=dest OUTPUT zone AS dest_zone\n"
            "| where (src_zone=\"CDE\" AND dest_zone=\"UNTRUSTED\") OR (src_zone=\"UNTRUSTED\" AND dest_zone=\"CDE\")\n"
            "| lookup pci_approved_flows.csv src_zone dest_zone dest_port protocol OUTPUT approved\n"
            "| where approved!=\"yes\" OR isnull(approved)\n"
            "| stats count BY src src_zone dest dest_zone dest_port protocol approved"
        ),
        description="Detects any CDE-to-untrusted or untrusted-to-CDE flow that was allowed by the NSC but is not on the approved-flows list. PCI-DSS 1.3 mandates network segmentation between CDE and other networks; an allowed unapproved flow is a direct non-conformance.",
        value="Provides QSAs the direct evidence that CDE boundary controls are intact and deviations are captured within 15 minutes.",
        implementation="(1) Onboard Palo Alto + ASA traffic; (2) maintain cde_zones.csv (CIDR → zone) and pci_approved_flows.csv; (3) schedule UC every 15m; (4) hit opens a P1 to NSC team; (5) daily report to compliance officer.",
        visualization="Sankey of src_zone→dest_zone with unapproved highlighted, table of unapproved flows, single value 'unapproved CDE flows (1h)'.",
        cim_models=["Network_Traffic"],
        known_fp="Cold-failover rules activated during DR days produce ephemeral unapproved flows — add DR-day allowlist with effective-from/to timestamps.",
        required_fields=["src", "dest", "dest_port", "protocol", "action", "_time"],
        compliance=[
            c_pci("1.3", "full",
                  "PCI-DSS 1.3 Network segmentation between CDE and other networks — directly evidenced."),
            c_iso("A.8.22", "partial",
                  "ISO/IEC 27001:2022 A.8.22 Segregation of networks — contributing."),
            c_soc2("CC6.6", "partial",
                   "SOC 2 CC6.6 — contributing."),
        ],
        control_test_positive="A synthetic allow rule permitting UNTRUSTED→CDE on port 3306 fires within 15m.",
        control_test_negative="A flow approved in pci_approved_flows.csv is absent.",
        control_test_attack_technique="T1021",
        mitre_attack=["T1021"],
    ),
    uc(
        id_="22.11.92",
        title="PCI-DSS 2.2 — Secure configuration baseline: drift from approved hardening template",
        criticality="high",
        difficulty="intermediate",
        owner="Head of Platform",
        control_family="policy-to-control-traceability",
        security_domain="endpoint",
        detection_type="Baseline",
        splunk_pillar="Platform",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT replace Tripwire or OS STIGs; surfaces hosts whose Chef/Ansible run report diverges from the declared baseline for >24h.",
        evidence="Saved search 'pci_2_2_config_drift' (every 30m) emits per host: hostname, role, baseline_version, drift_count, last_converged, to compliance_summary.",
        data_sources="`index=configmgmt` sourcetype=chef:compliance OR sourcetype=ansible:callback; baseline lookup `pci_baselines.csv`.",
        app="Splunk Enterprise / Splunk Cloud Platform",
        spl=(
            "index=configmgmt sourcetype IN (chef:compliance,ansible:callback) earliest=-30m\n"
            "| stats latest(role) AS role latest(baseline_version) AS baseline_version latest(resource_failed) AS resource_failed latest(_time) AS last_converged BY hostname\n"
            "| eval drift_count=coalesce(resource_failed,0)\n"
            "| where drift_count>0 OR last_converged<now()-86400\n"
            "| table hostname role baseline_version drift_count last_converged"
        ),
        description="Baseline compliance for CDE hosts. PCI-DSS 2.2 requires configuration standards that address known security vulnerabilities; drift from the approved baseline is the direct failure.",
        value="Turns the quarterly 'baseline assessment' into a 30-minute signal. Platform team sees regressions before the QSA.",
        implementation="(1) Enforce Chef/Ansible on all CDE hosts; (2) emit convergence events; (3) maintain pci_baselines.csv with the current approved baseline_version per role; (4) schedule UC every 30m; (5) drift opens a Platform ticket.",
        visualization="Bar of drift_count by role, table of top-drift hosts, single value 'hosts in drift'.",
        cim_models=["Change", "Endpoint"],
        known_fp="Baseline upgrades take effect over a staged rollout — support multiple active baseline_versions in the lookup.",
        required_fields=["hostname", "role", "baseline_version", "_time"],
        compliance=[
            c_pci("2.2", "full",
                  "PCI-DSS 2.2 Configuration standards — directly evidenced."),
            c_iso("A.8.9", "full",
                  "ISO/IEC 27001:2022 A.8.9 Configuration management — directly evidenced."),
            c_soc2("CC8.1", "partial",
                   "SOC 2 CC8.1 — contributing."),
            c_nist53("CM-6", "partial",
                     "NIST 800-53 CM-6 Configuration Settings — contributing."),
        ],
        control_test_positive="Setting a test host's baseline_version to a superseded value returns it in the drift table.",
        control_test_negative="A host fully converged in the last 30m is absent.",
    ),
    uc(
        id_="22.11.93",
        title="PCI-DSS 3.3 — Sensitive authentication data: cleartext PAN/CVV detection in logs",
        criticality="critical",
        difficulty="advanced",
        owner="DPO",
        control_family="regulation-specific",
        security_domain="audit",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT enforce masking (application-side); identifies occurrences of cleartext PAN or full-track data in application logs as a compliance violation.",
        evidence="Saved search 'pci_3_3_cleartext_sad' (every 10m) outputs: sourcetype, host, line_id, match_type, redaction_status, to compliance_summary_sensitive (access-controlled).",
        data_sources="`index=app` sourcetypes from payment applications; `index=web` access logs; redaction-pipeline attestation events.",
        app="Splunk Enterprise / Splunk Cloud Platform",
        spl=(
            "index=app OR index=web earliest=-10m\n"
            "| eval pan_match=if(match(_raw,\"(?<![0-9])(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})(?![0-9])\"),1,0)\n"
            "| eval cvv_match=if(match(_raw,\"(?i)cvv=[0-9]{3,4}\"),1,0)\n"
            "| where pan_match=1 OR cvv_match=1\n"
            "| eval match_type=case(pan_match=1 AND cvv_match=1,\"pan+cvv\",pan_match=1,\"pan\",true(),\"cvv\")\n"
            "| stats count BY sourcetype host match_type"
        ),
        description="Detects cleartext PAN or CVV patterns in application / web logs. PCI-DSS 3.3 prohibits storing sensitive authentication data post-authorisation; logs containing such data are a direct non-conformance.",
        value="Reduces the window between a logging regression introducing a cleartext PAN and the compliance team's discovery from 'next log review' to 10 minutes.",
        implementation="(1) Apply a separate restrictive index for hits (ACL); (2) schedule UC every 10m; (3) hit creates a P1 to DPO + app owner; (4) index-time redaction must be fixed + backfill scrub; (5) monthly DPO report.",
        visualization="Timechart of match_count, table of top offending sourcetypes, single value 'detections in last hour'.",
        cim_models=["N/A"],
        known_fp="Synthetic test data may look like a PAN — allow-list via the synthetic_test flag in the application.",
        required_fields=["_raw", "sourcetype", "host", "_time"],
        compliance=[
            c_pci("3.3", "full",
                  "PCI-DSS 3.3 Sensitive authentication data not stored after authorisation — directly evidenced in the logs pipeline."),
            c_iso("A.8.12", "full",
                  "ISO/IEC 27001:2022 A.8.12 Data leakage prevention — contributing."),
            c_soc2("C1.1", "partial",
                   "SOC 2 C1.1 — contributing."),
        ],
        control_test_positive="Injecting a synthetic event with '4242424242424242' into a monitored sourcetype fires the UC within 10m.",
        control_test_negative="Payment events with PAN already masked (4242******4242) are absent.",
        control_test_attack_technique="T1005",
        mitre_attack=["T1005"],
    ),
    uc(
        id_="22.11.94",
        title="PCI-DSS 5.2 — Anti-malware: EDR coverage + detection-queue attestation",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="log-source-completeness",
        security_domain="endpoint",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT replace the EDR; attests CDE coverage (every CDE host reporting) + that the detection queue is not backed up.",
        evidence="Saved search 'pci_5_2_edr_attest' (every 30m) emits: hostname, role, edr_seen, last_event, agent_state, queue_backlog, to compliance_summary.",
        data_sources="`index=edr` sourcetype IN (crowdstrike:hosts,microsoft:defender:host); `index=cmdb` CDE host list.",
        app="Splunk Add-on for CrowdStrike FDR (5082)",
        spl=(
            "| inputlookup cde_hosts.csv\n"
            "| join type=outer hostname\n"
            "  [search index=edr sourcetype IN (crowdstrike:hosts,microsoft:defender:host) earliest=-1h\n"
            "   | stats latest(_time) AS last_event latest(agent_state) AS agent_state BY hostname]\n"
            "| eval edr_seen=if(isnotnull(last_event) AND last_event>now()-1800,1,0)\n"
            "| where edr_seen=0 OR agent_state!=\"healthy\"\n"
            "| table hostname role edr_seen last_event agent_state"
        ),
        description="Coverage attestation for CDE anti-malware: every CDE host has an EDR event within 30 minutes and the agent is healthy.",
        value="Converts the annual 'EDR deployed' claim into a 30-minute ground-truth signal — directly auditable against PCI-DSS 5.2 requirement for deployed anti-malware.",
        implementation="(1) Maintain cde_hosts.csv from CMDB; (2) schedule UC every 30m; (3) gap opens a ticket to the host owner; (4) 24h SLA; (5) weekly CISO report.",
        visualization="Bar chart of coverage by role, table of gaps, single value 'CDE hosts without EDR'.",
        cim_models=["Endpoint"],
        known_fp="Hosts under image-build or maintenance windows legitimately show no EDR — use maintenance_calendar.csv.",
        required_fields=["hostname", "agent_state", "_time"],
        compliance=[
            c_pci("5.2", "full",
                  "PCI-DSS 5.2 Anti-malware mechanisms — directly evidenced by coverage + health."),
            c_iso("A.8.7", "full",
                  "ISO/IEC 27001:2022 A.8.7 Protection against malware — directly evidenced."),
            c_nist53("SI-3", "full",
                     "NIST 800-53 SI-3 Malicious Code Protection — directly evidenced."),
        ],
        control_test_positive="Stopping the EDR agent on a CDE host for 40m sets edr_seen=0.",
        control_test_negative="A healthy agent emitting events within 30m is absent.",
    ),
    uc(
        id_="22.11.95",
        title="PCI-DSS 6.2 — Bespoke-software SDLC: code-review + SAST completion before CDE deploy",
        criticality="high",
        difficulty="advanced",
        owner="Head of Platform",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Platform",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT build or review the code; attests the required SDLC gates completed for any artifact deployed to a CDE service.",
        evidence="Saved search 'pci_6_2_sdlc_gates' (hourly) emits per deploy: artifact, commit_sha, sast_state, review_state, deployed_at, gates_met, to compliance_summary.",
        data_sources="`index=cicd` sourcetype=github:actions OR sourcetype=gitlab:pipeline; SAST output `index=security` sourcetype=veracode:scan; CDE-service lookup `cde_services.csv`.",
        app="Splunk Add-on for GitHub",
        spl=(
            "index=cicd sourcetype IN (github:actions,gitlab:pipeline) event_type=deployment target_env IN (\"prod-cde\") earliest=-24h\n"
            "| stats latest(_time) AS deployed_at latest(commit_sha) AS commit_sha BY artifact service\n"
            "| join type=outer commit_sha\n"
            "  [search index=security sourcetype=veracode:scan earliest=-30d\n"
            "   | stats latest(overall_state) AS sast_state BY commit_sha]\n"
            "| join type=outer commit_sha\n"
            "  [search index=cicd event_type=pr_review state=approved earliest=-30d\n"
            "   | stats latest(reviewer) AS reviewer BY commit_sha\n"
            "   | eval review_state=\"approved\"]\n"
            "| eval gates_met=if(sast_state=\"pass\" AND review_state=\"approved\",1,0)\n"
            "| where gates_met=0\n"
            "| table artifact commit_sha service deployed_at sast_state review_state gates_met"
        ),
        description="For every deploy to a CDE service, assert that SAST passed and a PR review was approved before deploy. PCI-DSS 6.2 mandates a documented SDLC.",
        value="Replaces the pre-release tick-box with continuous gate-enforcement evidence. Auditors see the commit→gate→deploy chain for every CDE deploy.",
        implementation="(1) Route CI/CD + SAST events; (2) maintain cde_services.csv; (3) schedule UC hourly; (4) gates_met=0 opens a security ticket; (5) pipeline policy revisions add gates.",
        visualization="Table of gate-missing deploys, bar chart by service, single value 'recent deploys missing gates'.",
        cim_models=["Change"],
        known_fp="Hotfix deploys via break-glass workflow have an alternate review path — exclude with the workflow label hotfix=true when attested separately.",
        required_fields=["artifact", "commit_sha", "target_env", "event_type", "_time"],
        compliance=[
            c_pci("6.2", "full",
                  "PCI-DSS 6.2 Bespoke and custom software — gate adherence is directly evidenced."),
            c_iso("A.8.25", "full",
                  "ISO/IEC 27001:2022 A.8.25 Secure development lifecycle — directly evidenced."),
            c_soc2("CC8.1", "partial",
                   "SOC 2 CC8.1 Change management — contributing."),
            c_sox("ITGC.ChangeMgmt.Testing", "partial",
                  "SOX-ITGC ChangeMgmt.Testing — contributing."),
        ],
        control_test_positive="Deploying a commit whose Veracode scan reports overall_state=fail returns gates_met=0.",
        control_test_negative="A deploy with SAST pass + approved PR review is absent.",
        control_test_attack_technique="T1195",
        mitre_attack=["T1195"],
    ),
    uc(
        id_="22.11.96",
        title="PCI-DSS 8.3 — Strong authentication: password-only logins against privileged accounts",
        criticality="critical",
        difficulty="intermediate",
        owner="CISO",
        control_family="privileged-session-recording",
        security_domain="identity",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT de-privilege accounts; detects successful logins to privileged accounts that used single-factor password authentication.",
        evidence="Saved search 'pci_8_3_password_only_priv' (every 10m) emits: user, src, dest, auth_method, mfa_used, to compliance_summary.",
        data_sources="`index=windows` sourcetype=WinEventLog:Security (4624); `index=linux` sourcetype=auditd; IDP `index=idp` sourcetype=okta:system_log.",
        app="Splunk Add-on for Microsoft Windows (742), Splunk Add-on for Okta",
        spl=(
            "search (index=windows sourcetype=WinEventLog:Security EventCode=4624) OR (index=idp sourcetype=okta:system_log eventType=user.session.start) earliest=-10m\n"
            "| lookup privileged_accounts.csv user OUTPUT is_privileged\n"
            "| where is_privileged=\"yes\"\n"
            "| eval auth_method=case(isnotnull(LogonType) AND LogonType IN (\"2\",\"10\"),\"interactive\",isnotnull(factor),factor,true(),\"password\")\n"
            "| eval mfa_used=if(auth_method IN (\"mfa_push\",\"mfa_totp\",\"webauthn\",\"smartcard\",\"token:hardware\"),1,0)\n"
            "| where mfa_used=0\n"
            "| table user src dest auth_method mfa_used"
        ),
        description="Detects a successful login to a privileged account that did not complete a second factor. PCI-DSS 8.3 requires strong authentication for all access to system components.",
        value="Catches the exact condition that has historically resulted in CDE breaches (privileged password-only sessions). MTTR shrinks from weeks to minutes.",
        implementation="(1) Maintain privileged_accounts.csv; (2) ensure IDP emits factor evidence; (3) schedule UC every 10m; (4) hit opens a P1 and disables the session; (5) monthly CISO review of patterns.",
        visualization="Timechart of non-MFA privileged logins, table of top accounts, single value 'non-MFA priv logins (1h)'.",
        cim_models=["Authentication"],
        known_fp="Service-account logins using smart-card-equivalent client cert may not show 'factor'; capture via cert-login sourcetype and mark mfa_used=1.",
        required_fields=["user", "src", "dest", "LogonType", "_time"],
        compliance=[
            c_pci("8.3", "full",
                  "PCI-DSS 8.3 Strong authentication — directly evidenced for privileged access."),
            c_iso("A.8.5", "full",
                  "ISO/IEC 27001:2022 A.8.5 Secure authentication — directly evidenced."),
            c_soc2("CC6.1", "partial",
                   "SOC 2 CC6.1 — contributing."),
            c_nist53("IA-2", "full",
                     "NIST 800-53 IA-2 Identification and Authentication (Organizational Users) — directly evidenced."),
        ],
        control_test_positive="A test privileged login via password-only completes and appears in the UC within 10m.",
        control_test_negative="A privileged login with MFA_push factor does NOT fire.",
        control_test_attack_technique="T1078",
        mitre_attack=["T1078"],
    ),
    uc(
        id_="22.11.97",
        title="PCI-DSS 8.4 — MFA coverage: administrative access to CDE without MFA",
        criticality="critical",
        difficulty="intermediate",
        owner="CISO",
        control_family="privileged-session-recording",
        security_domain="identity",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT govern who can be an admin; detects admin access attempts into the CDE that did not use MFA.",
        evidence="Saved search 'pci_8_4_mfa_coverage' (every 10m) emits per session: admin, dest, session_type, mfa_used, to compliance_summary.",
        data_sources="`index=windows` EventCode 4624/4672; `index=linux` auditd; bastion/PAM `index=pam` sourcetype=cyberark:pam; CDE-dest lookup `cde_hosts.csv`.",
        app="Splunk Add-on for CyberArk",
        spl=(
            "search (index=windows sourcetype=WinEventLog:Security EventCode IN (4624,4672)) OR (index=pam sourcetype=cyberark:pam event_type=session_start) earliest=-10m\n"
            "| rename target_host AS dest\n"
            "| lookup cde_hosts.csv hostname=dest OUTPUT in_cde\n"
            "| lookup privileged_accounts.csv user AS admin OUTPUT is_privileged\n"
            "| where in_cde=\"yes\" AND is_privileged=\"yes\"\n"
            "| eval mfa_used=if(match(_raw,\"(?i)mfa|2fa|push|webauthn|smartcard\"),1,0)\n"
            "| where mfa_used=0\n"
            "| table admin dest session_type mfa_used"
        ),
        description="Administrative access to the CDE must use MFA. PCI-DSS 8.4 (formerly 8.3) explicitly requires MFA for administrative access. This UC detects misses.",
        value="The #1 QSA finding in failed assessments. Converting this to a 10-minute detection reduces remediation cost 100×.",
        implementation="(1) Integrate PAM/bastion; (2) maintain cde_hosts.csv + privileged_accounts.csv; (3) schedule UC every 10m; (4) hit revokes session; (5) monthly CISO review.",
        visualization="Heatmap of admins × destinations, table of non-MFA sessions, single value 'non-MFA admin in CDE'.",
        cim_models=["Authentication"],
        known_fp="Break-glass emergency access with compensating controls (hardware-token-only) must log mfa_used=1 via its own sourcetype — route to the field correctly.",
        required_fields=["admin", "dest", "session_type", "_time"],
        compliance=[
            c_pci("8.4", "full",
                  "PCI-DSS 8.4 MFA for administrative access to the CDE — directly evidenced."),
            c_iso("A.8.5", "full",
                  "ISO/IEC 27001:2022 A.8.5 Secure authentication — directly evidenced."),
            c_nist53("IA-2(1)", "full",
                     "NIST 800-53 IA-2(1) MFA to privileged accounts — directly evidenced."),
            c_dora("Art.9", "partial",
                   "DORA Art.9 Protection — contributing."),
        ],
        control_test_positive="A test admin session from bastion to a CDE host with mfa_used=0 fires within 10m.",
        control_test_negative="A bastion session showing mfa_used=1 is absent.",
        control_test_attack_technique="T1078",
        mitre_attack=["T1078"],
    ),
    uc(
        id_="22.11.98",
        title="PCI-DSS 8.6 — Application and system accounts: interactive use of a service account",
        criticality="high",
        difficulty="intermediate",
        owner="CISO",
        control_family="privileged-session-recording",
        security_domain="identity",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT restrict the account; detects interactive (console/RDP/SSH) use of an account flagged service-only in the identity registry.",
        evidence="Saved search 'pci_8_6_svc_account_interactive' (every 10m) emits per event: user, src, dest, LogonType, account_type, to compliance_summary.",
        data_sources="`index=windows` EventCode 4624; `index=linux` auditd; service-account lookup `service_accounts.csv`.",
        app="Splunk Add-on for Microsoft Windows (742)",
        spl=(
            "index=windows sourcetype=WinEventLog:Security EventCode=4624 LogonType IN (2,10,11) earliest=-10m\n"
            "| rename TargetUserName AS user\n"
            "| lookup service_accounts.csv user OUTPUT account_type\n"
            "| where account_type=\"service-only\"\n"
            "| table user src dest LogonType account_type"
        ),
        description="Detects an interactive session on a service-only account — direct PCI-DSS 8.6 violation, which requires application/system accounts not be used interactively.",
        value="Removes the common post-audit-finding 'we didn't know that account was used interactively' narrative by making the misuse visible in 10 minutes.",
        implementation="(1) Maintain service_accounts.csv with account_type tag; (2) schedule UC every 10m; (3) hit opens a P1 and disables the account; (4) weekly IAM review.",
        visualization="Table of interactive service-account logins, time chart, single value 'events in last hour'.",
        cim_models=["Authentication"],
        known_fp="Admin password rotations performed by a service-account-using tool may be reported as interactive — exclude via tool's user-as-tool mapping.",
        required_fields=["TargetUserName", "LogonType", "src", "dest", "_time"],
        compliance=[
            c_pci("8.6", "full",
                  "PCI-DSS 8.6 Application and system accounts not used interactively — directly evidenced."),
            c_iso("A.5.16", "full",
                  "ISO/IEC 27001:2022 A.5.16 Identity management — directly evidenced."),
            c_nist53("IA-2", "partial",
                     "NIST 800-53 IA-2 Identification and Authentication — contributing."),
        ],
        control_test_positive="Logging into a service-only account via RDP fires the UC within 10m.",
        control_test_negative="A service-account login via LogonType 3 (network, non-interactive) is absent.",
        control_test_attack_technique="T1078.002",
        mitre_attack=["T1078.002"],
    ),
    uc(
        id_="22.11.99",
        title="PCI-DSS 10.3 — Audit log integrity: tampering/deletion detection on CDE log source",
        criticality="critical",
        difficulty="advanced",
        owner="CISO",
        control_family="evidence-continuity",
        security_domain="audit",
        detection_type="TTP",
        splunk_pillar="Platform",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT prevent tampering; raises on attempts to clear, delete, or modify CDE audit logs.",
        evidence="Saved search 'pci_10_3_log_tamper' (every 10m) emits per event: host, action, actor, target_log, to compliance_summary.",
        data_sources="`index=windows` EventCode IN (1102,104); `index=linux` auditd log clears, syslog `rotated-by-hand`.",
        app="Splunk Add-on for Microsoft Windows (742), Splunk Add-on for Unix and Linux (833)",
        spl=(
            "search (index=windows sourcetype=WinEventLog:Security EventCode=1102) OR (index=windows sourcetype=WinEventLog:System EventCode=104) OR (index=linux sourcetype=auditd type=CONFIG_CHANGE op=remove_rule) earliest=-10m\n"
            "| eval action=case(EventCode=1102,\"audit_log_cleared\",EventCode=104,\"event_log_cleared\",op=\"remove_rule\",\"auditd_rule_removed\",true(),\"unknown\")\n"
            "| rename TargetUserName AS actor host AS host\n"
            "| table host action actor target_log"
        ),
        description="PCI-DSS 10.3 requires audit logs be protected from modification and deletion. This UC fires on the exact telemetry those operations emit.",
        value="A cleared Windows Security log on a CDE host is a near-certain indicator of attacker presence. Closing the detection gap to 10 minutes saves forensics time.",
        implementation="(1) Forward Windows Security + System + Linux auditd to Splunk; (2) schedule UC every 10m; (3) hit opens a P1 to IR + isolates host; (4) quarterly IR drill validates response.",
        visualization="Table of events by action, time chart, single value 'clears in last hour'.",
        cim_models=["Change"],
        known_fp="Host-retirement scripts may legitimately clear logs — exclude only with scheduled-retirement ticket linked.",
        required_fields=["host", "EventCode", "TargetUserName", "_time"],
        compliance=[
            c_pci("10.3", "full",
                  "PCI-DSS 10.3 Audit logs protected from modification — directly evidenced."),
            c_iso("A.8.15", "full",
                  "ISO/IEC 27001:2022 A.8.15 Logging — directly evidenced."),
            c_soc2("CC7.2", "partial",
                   "SOC 2 CC7.2 — contributing."),
            c_sox("ITGC.Logging.Integrity", "full",
                  "SOX-ITGC Logging.Integrity — directly evidenced."),
        ],
        control_test_positive="Clearing a Windows Security log on a CDE test host (EventCode 1102) fires the UC.",
        control_test_negative="Normal log rotation via scheduled task (with matching ticket) does NOT fire.",
        control_test_attack_technique="T1070.001",
        mitre_attack=["T1070.001"],
    ),
    uc(
        id_="22.11.100",
        title="PCI-DSS 10.4 — Time synchronisation: NTP drift on CDE hosts",
        criticality="high",
        difficulty="beginner",
        owner="Head of Platform",
        control_family="log-source-completeness",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="IT Operations",
        monitoring_type=["Compliance"],
        exclusions="Does NOT replace NTP; surfaces CDE hosts whose measured offset from the authoritative time source exceeds 1s.",
        evidence="Saved search 'pci_10_4_ntp_drift' (every 15m) emits per host: hostname, offset_ms, stratum, last_ntp_sync, to compliance_summary.",
        data_sources="`index=windows` sourcetype=w32time; `index=linux` sourcetype=chronyd OR sourcetype=ntpd; CDE lookup `cde_hosts.csv`.",
        app="Splunk Add-on for Microsoft Windows (742), Splunk Add-on for Unix and Linux (833)",
        spl=(
            "search (index=windows sourcetype=w32time) OR (index=linux sourcetype IN (chronyd,ntpd)) earliest=-15m\n"
            "| stats latest(offset_ms) AS offset_ms latest(stratum) AS stratum latest(_time) AS last_ntp_sync BY hostname\n"
            "| lookup cde_hosts.csv hostname OUTPUT in_cde\n"
            "| where in_cde=\"yes\" AND (abs(offset_ms)>1000 OR last_ntp_sync<now()-3600)\n"
            "| table hostname offset_ms stratum last_ntp_sync"
        ),
        description="PCI-DSS 10.4 requires time synchronisation across CDE systems. This UC flags drift > 1s or NTP sync gaps > 1h.",
        value="Prevents the classic forensic nightmare of 'when exactly did the event occur' because the CDE clocks disagreed.",
        implementation="(1) Enforce w32time/chrony logs to Splunk; (2) maintain cde_hosts.csv; (3) schedule UC every 15m; (4) drift opens a Platform ticket; (5) quarterly sampling for auditor.",
        visualization="Scatter of offset_ms per host, table of drifted hosts, single value 'hosts over 1s drift'.",
        cim_models=["Performance"],
        known_fp="Virtualisation drift during host migration may cause short bursts — smooth with 5-minute averaging before trigger.",
        required_fields=["hostname", "offset_ms", "stratum", "_time"],
        compliance=[
            c_pci("10.4", "full",
                  "PCI-DSS 10.4 Time synchronisation — directly evidenced."),
            c_iso("A.8.17", "full",
                  "ISO/IEC 27001:2022 A.8.17 Clock synchronisation — directly evidenced."),
            c_nist53("AU-8", "full",
                     "NIST 800-53 AU-8 Time Stamps — directly evidenced."),
        ],
        control_test_positive="Forcing a 2-second offset via NTP test fires the UC within 15m.",
        control_test_negative="A host with <100ms offset is absent.",
    ),
    uc(
        id_="22.11.101",
        title="PCI-DSS 10.6 — Log review: daily-review evidence for CDE data sources",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="evidence-continuity",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT review logs; attests a scheduled review artefact exists daily per CDE data source.",
        evidence="Saved search 'pci_10_6_daily_review' (daily) emits per source: source, reviewer, reviewed_at, artefact_id, to compliance_summary.",
        data_sources="`index=compliance` sourcetype=review:daily (from SOC daily review tool); CDE-source list `pci_cde_log_sources.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup pci_cde_log_sources.csv\n"
            "| join type=outer source\n"
            "  [search index=compliance sourcetype=review:daily earliest=-1d\n"
            "   | stats latest(reviewer) AS reviewer latest(_time) AS reviewed_at latest(artefact_id) AS artefact_id BY source]\n"
            "| eval review_today=if(reviewed_at>=relative_time(now(),\"@d\"),1,0)\n"
            "| where review_today=0\n"
            "| table source reviewer reviewed_at artefact_id review_today"
        ),
        description="PCI-DSS 10.6 requires daily review of logs. This UC tests the presence of the daily review record — the auditor-visible outcome of the control.",
        value="Auditors frequently disallow 'we review daily' without evidence. The review artefact lookup gives the evidence.",
        implementation="(1) SOC tool must write review artefacts to index=compliance; (2) maintain pci_cde_log_sources.csv; (3) schedule UC daily at 23:55 UTC; (4) gap opens a ticket for the next morning's shift; (5) monthly CISO report.",
        visualization="Table of sources missing review, time chart by day, single value 'days with gaps (30d)'.",
        cim_models=["N/A"],
        known_fp="Automated high-fidelity systems (e.g., PAN unified logging with correlation) may substitute for daily review — allow-list via source_type='automated-attest' in the lookup.",
        required_fields=["source", "reviewer", "_time"],
        compliance=[
            c_pci("10.6", "full",
                  "PCI-DSS 10.6 Logs reviewed — review artefact is the direct evidence."),
            c_iso("A.5.28", "partial",
                  "ISO/IEC 27001:2022 A.5.28 Collection of evidence — contributing."),
            c_soc2("CC7.1", "partial",
                   "SOC 2 CC7.1 — contributing."),
        ],
        control_test_positive="Removing today's review artefact for the pan:traffic source returns it in the daily output.",
        control_test_negative="A source with a reviewed_at timestamp within the day is absent.",
    ),
    uc(
        id_="22.11.102",
        title="PCI-DSS 10.7 — Log retention: CDE data-source retention + immutability attestation",
        criticality="high",
        difficulty="intermediate",
        owner="Head of Platform",
        control_family="evidence-continuity",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Platform",
        monitoring_type=["Compliance"],
        exclusions="Does NOT change retention; attests (a) configured index retention for CDE indexes ≥ 365d and (b) WORM archive currency.",
        evidence="Saved search 'pci_10_7_retention_attest' (daily) emits per index: index, configured_days, oldest_event_age_d, worm_last_write, to compliance_summary.",
        data_sources="Splunk REST /services/data/indexes; `index=compliance` sourcetype=worm:signer.",
        app="Splunk Enterprise / Splunk Cloud Platform",
        spl=(
            "| rest /services/data/indexes\n"
            "| where match(title,\"^(cde|pci)_\")\n"
            "| eval configured_days=round(frozenTimePeriodInSecs/86400,0)\n"
            "| table title configured_days minTime maxTime\n"
            "| rename title AS index\n"
            "| eval oldest_event_age_d=round((now()-strptime(minTime,\"%Y-%m-%dT%H:%M:%S%z\"))/86400,0)\n"
            "| join type=outer index\n"
            "  [search index=compliance sourcetype=worm:signer earliest=-7d\n"
            "   | stats latest(_time) AS worm_last_write BY index]\n"
            "| where configured_days<365 OR oldest_event_age_d<365 OR worm_last_write<now()-86400\n"
            "| table index configured_days oldest_event_age_d worm_last_write"
        ),
        description="Attests the retention and WORM posture required by PCI-DSS 10.7 (one-year retention, three months immediately available).",
        value="Prevents the audit-killing discovery that retention was silently reduced during an index rebuild. Daily attestation beats the quarterly spot-check.",
        implementation="(1) Name CDE indexes with cde_/pci_ prefix; (2) WORM signer writes per-index heartbeat; (3) schedule UC daily; (4) gap opens a Platform ticket; (5) monthly CISO review.",
        visualization="Bar of retention days by index, table of gaps, single value 'indexes below 365d'.",
        cim_models=["N/A"],
        known_fp="New indexes legitimately have oldest_event_age_d<365 until one year passes — mark age_exempt=true in an index-metadata lookup.",
        required_fields=["index", "frozenTimePeriodInSecs", "minTime", "maxTime"],
        compliance=[
            c_pci("10.7", "full",
                  "PCI-DSS 10.7 Log retention — retention + WORM attestation is directly evidenced."),
            c_iso("A.5.33", "full",
                  "ISO/IEC 27001:2022 A.5.33 Protection of records — directly evidenced."),
            c_nist53("AU-11", "full",
                     "NIST 800-53 AU-11 Audit Record Retention — directly evidenced."),
            c_sox("ITGC.Logging.Integrity", "partial",
                  "SOX-ITGC Logging.Integrity — contributing."),
        ],
        control_test_positive="Setting a CDE index frozenTimePeriodInSecs to 180d returns configured_days=180 in the output.",
        control_test_negative="An index with 400d retention + recent WORM heartbeat is absent.",
    ),
    uc(
        id_="22.11.103",
        title="PCI-DSS 11.3 — Vulnerability programme: overdue scan cadence and unremediated high-severity",
        criticality="high",
        difficulty="intermediate",
        owner="CISO",
        control_family="regulation-specific",
        security_domain="threat",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT replace the scanner; measures cadence adherence (quarterly for external, internal as required) and remediation SLA for high/critical findings.",
        evidence="Saved search 'pci_11_3_scan_sla' (daily) emits per scope: scope, last_scan_at, sla_met, open_high_findings, mean_age_days, to compliance_summary.",
        data_sources="`index=vm` sourcetype=tenable:sc:vuln, qualys:host; scan-scope lookup `pci_scan_scope.csv`.",
        app="Splunk Add-on for Tenable (4060)",
        spl=(
            "index=vm sourcetype IN (tenable:sc:vuln,qualys:host) earliest=-120d\n"
            "| stats latest(_time) AS last_scan_at count(eval(severity IN (\"high\",\"critical\") AND state=\"open\")) AS open_high_findings avg(eval(if(state=\"open\" AND severity IN (\"high\",\"critical\"),now()-first_seen,null))) AS mean_age_s BY scan_scope\n"
            "| eval mean_age_days=round(mean_age_s/86400,0)\n"
            "| lookup pci_scan_scope.csv scan_scope OUTPUT cadence_days sla_days\n"
            "| eval sla_met=if(last_scan_at>=now()-cadence_days*86400 AND mean_age_days<=sla_days,1,0)\n"
            "| where sla_met=0\n"
            "| table scan_scope last_scan_at sla_met open_high_findings mean_age_days"
        ),
        description="Produces, per scan scope, the evidence required by PCI-DSS 11.3 — scans are on cadence and high/critical findings are remediated within SLA.",
        value="Closes the #1 open-finding reason at QSAs — 'the scan history was incomplete'. Continuous measurement is the intended replacement.",
        implementation="(1) Normalise scanner feeds; (2) maintain pci_scan_scope.csv (quarterly external, per-change internal); (3) schedule UC daily; (4) sla_met=0 opens a P2; (5) quarterly QSA report.",
        visualization="Bullet chart of SLA adherence by scope, table of overdue scopes, single value 'scopes overdue'.",
        cim_models=["Vulnerabilities"],
        known_fp="Immaterial findings whose exception was approved in the risk register show as 'open' — tag state='accepted_risk' and exclude.",
        required_fields=["scan_scope", "severity", "state", "first_seen", "_time"],
        compliance=[
            c_pci("11.3", "full",
                  "PCI-DSS 11.3 External and internal vulnerabilities identified — directly evidenced."),
            c_iso("A.8.8", "full",
                  "ISO/IEC 27001:2022 A.8.8 Management of technical vulnerabilities — directly evidenced."),
            c_nist53("RA-5", "full",
                     "NIST 800-53 RA-5 Vulnerability Scanning — directly evidenced."),
            c_dora("Art.8", "partial",
                   "DORA Art.8 ICT risk identification — contributing."),
        ],
        control_test_positive="A scope whose last_scan_at is 100 days ago with 3 open high findings aged 45 days returns sla_met=0.",
        control_test_negative="A scope scanned within cadence with all findings <30 days old is absent.",
        control_test_attack_technique="T1595",
        mitre_attack=["T1595"],
    ),
    uc(
        id_="22.11.104",
        title="PCI-DSS 11.4 — Intrusion detection: IDS signature/health attestation + untuned alert monitoring",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="log-source-completeness",
        security_domain="network",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT review alerts; attests the IDS/IPS sensors are healthy, up-to-date on signatures, and producing events.",
        evidence="Saved search 'pci_11_4_ids_attest' (every 30m) emits per sensor: sensor, last_seen, sig_version, age_d, state, to compliance_summary.",
        data_sources="`index=ids` sourcetype IN (suricata:eve,snort:ids,palo:threat); sensor inventory `pci_ids_sensors.csv`.",
        app="Splunk Add-on for Suricata, Splunk Add-on for Palo Alto Networks (2757)",
        spl=(
            "| inputlookup pci_ids_sensors.csv\n"
            "| join type=outer sensor\n"
            "  [search index=ids earliest=-30m\n"
            "   | stats latest(_time) AS last_seen latest(sig_version) AS sig_version BY sensor]\n"
            "| eval age_d=round((now()-strptime(sig_version,\"%Y-%m-%d\"))/86400,0)\n"
            "| eval state=case(isnull(last_seen),\"offline\",last_seen<now()-1800,\"stale\",age_d>7,\"signatures-stale\",true(),\"healthy\")\n"
            "| where state!=\"healthy\"\n"
            "| table sensor last_seen sig_version age_d state"
        ),
        description="PCI-DSS 11.4 requires IDS/IPS use. This UC attests the sensors are alive and their signatures are fresh. Sensor gaps are a top-3 audit finding.",
        value="Transforms annual sign-off into 30-minute ground-truth. IR team sees stale signatures before they become an audit issue.",
        implementation="(1) Maintain pci_ids_sensors.csv; (2) onboard sensor telemetry; (3) schedule UC every 30m; (4) non-healthy state opens a P1/P2; (5) monthly CISO review.",
        visualization="Donut of state, table of non-healthy sensors, single value 'stale sensors'.",
        cim_models=["Intrusion_Detection"],
        known_fp="Sensor maintenance windows legitimately show 'offline' — allowlist with maintenance_calendar.csv.",
        required_fields=["sensor", "sig_version", "_time"],
        compliance=[
            c_pci("11.4", "full",
                  "PCI-DSS 11.4 Intrusion detection / prevention — directly evidenced."),
            c_iso("A.8.16", "full",
                  "ISO/IEC 27001:2022 A.8.16 Monitoring activities — directly evidenced."),
            c_soc2("CC7.1", "partial",
                   "SOC 2 CC7.1 — contributing."),
        ],
        control_test_positive="Disabling a sensor for 40m returns it with state=offline.",
        control_test_negative="A healthy sensor with signatures ≤7d old is absent.",
    ),
    uc(
        id_="22.11.105",
        title="PCI-DSS 12.10 — Incident response: IR readiness — playbook exercise evidence",
        criticality="high",
        difficulty="intermediate",
        owner="Head of IR",
        control_family="ir-drill-evidence",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT run the exercise; measures whether the CDE IR playbook has been exercised within policy cadence (annually) and if the exercise produced findings.",
        evidence="Saved search 'pci_12_10_ir_exercise' (weekly) emits per playbook: playbook_id, scope_cde, last_exercise_at, finding_count, exercise_lead, cadence_met, to compliance_summary.",
        data_sources="`index=testing` sourcetype=ir:drill; playbook register `ir_playbook_register.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup ir_playbook_register.csv\n"
            "| where scope_cde=\"yes\"\n"
            "| join type=outer playbook_id\n"
            "  [search index=testing sourcetype=ir:drill earliest=-14mon\n"
            "   | stats latest(_time) AS last_exercise_at latest(finding_count) AS finding_count latest(exercise_lead) AS exercise_lead BY playbook_id]\n"
            "| eval cadence_met=if(last_exercise_at>=now()-365*86400,1,0)\n"
            "| table playbook_id scope_cde last_exercise_at finding_count exercise_lead cadence_met"
        ),
        description="PCI-DSS 12.10.2 requires IR plan testing at least annually. This UC evidences the test happened per CDE playbook.",
        value="Converts the 'we did a tabletop' email into indexed evidence auditors can query directly.",
        implementation="(1) IR exercise tool writes drill events to index=testing; (2) maintain ir_playbook_register.csv; (3) schedule UC weekly; (4) cadence_met=0 schedules a drill; (5) annual Board report.",
        visualization="Table of playbooks with drill history, bar chart of findings per exercise, single value 'playbooks overdue'.",
        cim_models=["Change"],
        known_fp="Combined multi-playbook drills may link to one of several playbook_ids — maintain a drill_to_playbook mapping.",
        required_fields=["playbook_id", "_time"],
        compliance=[
            c_pci("12.10", "full",
                  "PCI-DSS 12.10 Security incident response — drill cadence is direct evidence."),
            c_iso("A.5.24", "partial",
                  "ISO/IEC 27001:2022 A.5.24 Incident management planning — contributing."),
            c_dora("Art.24", "partial",
                   "DORA Art.24 Testing programme — contributing."),
            c_soc2("CC7.4", "partial",
                   "SOC 2 CC7.4 — contributing."),
        ],
        control_test_positive="A CDE playbook with no drill event in 13 months returns cadence_met=0.",
        control_test_negative="A playbook exercised within the year is absent.",
    ),
    uc(
        id_="22.11.106",
        title="PCI-DSS 12.3 — Targeted risk analysis: frequency adherence for per-requirement TRAs",
        criticality="medium",
        difficulty="intermediate",
        owner="CISO",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT evaluate the TRA content; reports TRAs whose refresh is overdue per documented frequency.",
        evidence="Saved search 'pci_12_3_tra_refresh' (daily) emits per TRA: tra_id, requirement, frequency_days, last_refresh_at, overdue_days, to compliance_summary.",
        data_sources="`index=grc` sourcetype=archer:tra_record; TRA register `pci_tra_register.csv`.",
        app="Splunk Enterprise Security",
        spl=(
            "| inputlookup pci_tra_register.csv\n"
            "| join type=outer tra_id\n"
            "  [search index=grc sourcetype=archer:tra_record earliest=-2y\n"
            "   | stats latest(_time) AS last_refresh_at BY tra_id]\n"
            "| eval overdue_days=round((now()-last_refresh_at)/86400,0)-frequency_days\n"
            "| where overdue_days>0 OR isnull(last_refresh_at)\n"
            "| table tra_id requirement frequency_days last_refresh_at overdue_days"
        ),
        description="PCI-DSS v4.0 introduced targeted risk analyses (TRAs) at 12.3. This UC makes the refresh cadence measurable.",
        value="Gives compliance an explicit overdue list — the v4.0 TRA is a common reason for 'in progress' at year-two assessments.",
        implementation="(1) Maintain pci_tra_register.csv with requirement and frequency_days; (2) GRC writes each refresh event; (3) schedule UC daily; (4) overdue TRAs open a CISO-owned task; (5) quarterly compliance report.",
        visualization="Table of overdue TRAs, bar chart by requirement, single value 'TRAs overdue'.",
        cim_models=["N/A"],
        known_fp="TRAs whose requirement is marked 'not applicable' should be excluded via scope_applicable=false.",
        required_fields=["tra_id", "requirement", "_time"],
        compliance=[
            c_pci("12.3", "full",
                  "PCI-DSS 12.3 Targeted risk analysis — cadence adherence is direct evidence."),
            c_iso("8.2", "partial",
                  "ISO/IEC 27001:2022 Clause 8.2 Information security risk assessment — contributing."),
            c_dora("Art.6", "partial",
                   "DORA Art.6 ICT risk-management framework — contributing."),
        ],
        control_test_positive="A TRA with frequency_days=365 and last_refresh_at 400d ago returns overdue_days=35.",
        control_test_negative="A TRA refreshed in the past 200d with frequency_days=365 is absent.",
    ),
]


# ---------------------------------------------------------------------------
# SOX-ITGC PCAOB AS 2201 — 5 UCs (22.12.36 .. 22.12.40)
# ---------------------------------------------------------------------------

SOX_UCS: List[Dict] = [
    uc(
        id_="22.12.36",
        title="SOX-ITGC AccessMgmt.Provisioning — Financial-system user provisioning SLA & workflow adherence",
        criticality="high",
        difficulty="intermediate",
        owner="CFO",
        control_family="access-review-cadence",
        security_domain="identity",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT grant access; measures (a) every add to a financial-system group followed an approved ticket and (b) provisioning happened within the SLA from approval.",
        evidence="Saved search 'sox_itgc_provisioning' (daily) emits per add: group, user, added_at, ticket_id, approved_at, sla_met, to compliance_summary.",
        data_sources="`index=iam` sourcetype=okta:system_log OR sourcetype=ad:group_change; ticketing `index=ticketing` sourcetype=servicenow:request.",
        app="Splunk Add-on for Okta, Splunk Add-on for ServiceNow",
        spl=(
            "index=iam eventType=group.user_membership.add earliest=-7d\n"
            "| lookup financial_systems_groups.csv group OUTPUT in_scope\n"
            "| where in_scope=\"yes\"\n"
            "| rename actor AS added_by target.id AS user\n"
            "| eval added_at=_time\n"
            "| join type=outer user group\n"
            "  [search index=ticketing sourcetype=servicenow:request request_type=access_request state=approved earliest=-30d\n"
            "   | stats latest(ticket_id) AS ticket_id latest(approved_at) AS approved_at BY user target_group\n"
            "   | rename target_group AS group]\n"
            "| eval sla_met=if(isnotnull(approved_at) AND added_at<=approved_at+24*3600,1,0)\n"
            "| where sla_met=0\n"
            "| table group user added_at ticket_id approved_at sla_met"
        ),
        description="For every add to a financial-system group, assert an approved ServiceNow request exists and provisioning happened within 24h of approval.",
        value="Closes the #1 SOX deficiency 'access provisioned without an approved ticket'. Internal audit gets a daily report rather than a quarterly spot-check.",
        implementation="(1) Maintain financial_systems_groups.csv; (2) enforce ServiceNow workflow; (3) schedule UC daily; (4) sla_met=0 opens a SOX deficiency record; (5) monthly CFO report.",
        visualization="Table of provisioning without approval, bar chart by group, single value 'unapproved provisions (7d)'.",
        cim_models=["Change", "Authentication"],
        known_fp="Break-glass adds via approved emergency-access workflow populate approved_at via a separate sourcetype — ensure the join covers both.",
        required_fields=["eventType", "actor", "target.id", "group", "_time"],
        compliance=[
            c_sox("ITGC.AccessMgmt.Provisioning", "full",
                  "SOX-ITGC AccessMgmt.Provisioning — approval + SLA evidence is the direct control output."),
            c_soc2("CC6.2", "partial",
                   "SOC 2 CC6.2 Logical access provisioning — contributing."),
            c_iso("A.5.18", "full",
                  "ISO/IEC 27001:2022 A.5.18 Access rights — directly evidenced."),
            c_pci("8.2.4", "partial",
                  "PCI-DSS 8.2.4 User provisioning — contributing."),
        ],
        control_test_positive="Adding a user to a financial-system group with no matching ServiceNow approval returns sla_met=0.",
        control_test_negative="An add that follows an approved ticket within 24h is absent.",
        control_test_attack_technique="T1098",
        mitre_attack=["T1098"],
    ),
    uc(
        id_="22.12.37",
        title="SOX-ITGC AccessMgmt.Termination — Deprovisioning SLA after HR termination event",
        criticality="critical",
        difficulty="intermediate",
        owner="CFO",
        control_family="access-review-cadence",
        security_domain="identity",
        detection_type="Correlation",
        splunk_pillar="Security",
        monitoring_type=["Compliance", "Security"],
        exclusions="Does NOT deprovision; measures elapsed time between HR termination and removal of all financial-system access.",
        evidence="Saved search 'sox_itgc_termination_sla' (hourly) emits per terminated user: user, term_date, last_access_revoked, elapsed_hours, sla_met, to compliance_summary.",
        data_sources="`index=hr` sourcetype=workday:termination; `index=iam` sourcetype=okta:system_log (user.lifecycle.deactivate + group.user_membership.remove).",
        app="Splunk Add-on for Okta, Splunk Add-on for Workday",
        spl=(
            "index=hr sourcetype=workday:termination earliest=-7d\n"
            "| stats latest(_time) AS term_date BY user\n"
            "| join user type=outer\n"
            "  [search index=iam (eventType=user.lifecycle.deactivate OR eventType=group.user_membership.remove) earliest=-7d\n"
            "   | stats max(_time) AS last_access_revoked BY user]\n"
            "| eval elapsed_hours=round((last_access_revoked-term_date)/3600,1)\n"
            "| eval sla_met=if(elapsed_hours<=24 AND isnotnull(last_access_revoked),1,0)\n"
            "| where sla_met=0\n"
            "| table user term_date last_access_revoked elapsed_hours sla_met"
        ),
        description="Joins HR termination events against IAM deactivation/removal events to measure whether access was revoked within the 24h SLA implied by SOX-ITGC AccessMgmt.Termination.",
        value="The most common SOX finding — ex-employees retaining access — becomes measurable hour-by-hour.",
        implementation="(1) Route Workday terminations to Splunk; (2) route Okta lifecycle events; (3) schedule UC hourly; (4) sla_met=0 pages the IAM team; (5) monthly CFO report.",
        visualization="Timechart of SLA adherence %, table of breaches, single value 'open SLA breaches'.",
        cim_models=["Authentication", "Change"],
        known_fp="Contractor terminations with delayed HR events may produce a false breach — backfill term_date from contract_end_date in vendor_register.csv.",
        required_fields=["user", "eventType", "_time"],
        compliance=[
            c_sox("ITGC.AccessMgmt.Termination", "full",
                  "SOX-ITGC AccessMgmt.Termination — revocation SLA is direct evidence."),
            c_soc2("CC6.3", "full",
                   "SOC 2 CC6.3 Logical access removal — directly evidenced."),
            c_iso("A.5.18", "full",
                  "ISO/IEC 27001:2022 A.5.18 Access rights — directly evidenced."),
            c_pci("8.2.5", "partial",
                  "PCI-DSS 8.2.5 Terminate access within 1 business day — contributing."),
        ],
        control_test_positive="A Workday termination not followed by an IAM deactivate event within 24h returns sla_met=0.",
        control_test_negative="A termination with a matching deactivate event within 2h is absent.",
        control_test_attack_technique="T1078",
        mitre_attack=["T1078"],
    ),
    uc(
        id_="22.12.38",
        title="SOX-ITGC ChangeMgmt.Testing — Financial-system change test-evidence completeness",
        criticality="high",
        difficulty="intermediate",
        owner="CFO",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT judge test quality; attests each financial-system change has test evidence (UAT artefact, attachment or ticket) linked to it before deploy.",
        evidence="Saved search 'sox_itgc_change_testing' (hourly) emits per change: change_id, system, test_evidence_present, tester, deployed_at, to compliance_summary.",
        data_sources="`index=change` sourcetype=servicenow:change; test evidence sub-table sourcetype=servicenow:change_task (type=UAT).",
        app="Splunk Add-on for ServiceNow",
        spl=(
            "index=change sourcetype=servicenow:change state=implemented earliest=-7d\n"
            "| lookup financial_systems_apps.csv system OUTPUT in_scope\n"
            "| where in_scope=\"yes\"\n"
            "| stats latest(_time) AS deployed_at latest(change_id) AS change_id BY change_id system\n"
            "| join type=outer change_id\n"
            "  [search index=change sourcetype=servicenow:change_task task_type=uat state=closed_complete earliest=-60d\n"
            "   | stats latest(assigned_to) AS tester count AS uat_tasks BY change_id]\n"
            "| eval test_evidence_present=if(uat_tasks>=1,1,0)\n"
            "| where test_evidence_present=0\n"
            "| table change_id system tester deployed_at test_evidence_present"
        ),
        description="For every change to a financial system, assert a closed-complete UAT task exists. SOX-ITGC ChangeMgmt.Testing requires documented test evidence.",
        value="Converts a common sampling control into full-coverage evidence, reducing audit sampling and cost.",
        implementation="(1) Maintain financial_systems_apps.csv; (2) configure ServiceNow to require a UAT subtask; (3) schedule UC hourly; (4) test_evidence_present=0 triggers a deficiency record.",
        visualization="Table of missing-test changes, bar chart by system, single value 'missing test evidence'.",
        cim_models=["Change"],
        known_fp="Automated changes (configuration as code) may use automated test jobs rather than UAT tasks — accept sourcetype=cicd:tests result=pass as equivalent evidence.",
        required_fields=["change_id", "system", "state", "_time"],
        compliance=[
            c_sox("ITGC.ChangeMgmt.Testing", "full",
                  "SOX-ITGC ChangeMgmt.Testing — test-evidence presence is direct evidence."),
            c_soc2("CC8.1", "full",
                   "SOC 2 CC8.1 Change management — directly evidenced."),
            c_iso("A.8.32", "full",
                  "ISO/IEC 27001:2022 A.8.32 Change management — directly evidenced."),
            c_pci("6.4.6", "partial",
                  "PCI-DSS 6.4.6 Impact of changes — contributing."),
        ],
        control_test_positive="Implementing a financial-system change with no UAT subtask returns test_evidence_present=0.",
        control_test_negative="A change with a closed-complete UAT subtask is absent.",
    ),
    uc(
        id_="22.12.39",
        title="SOX-ITGC ChangeMgmt.Approval — Segregation of duties in financial-system change approval",
        criticality="critical",
        difficulty="advanced",
        owner="CFO",
        control_family="policy-to-control-traceability",
        security_domain="audit",
        detection_type="TTP",
        splunk_pillar="Security",
        monitoring_type=["Compliance"],
        exclusions="Does NOT configure workflow; detects changes where implementer == approver, or approval occurred AFTER implementation.",
        evidence="Saved search 'sox_itgc_change_approval' (hourly) emits per change: change_id, system, implementer, approver, approval_before_implementation, sod_violation, to compliance_summary.",
        data_sources="`index=change` sourcetype=servicenow:change (workflow events).",
        app="Splunk Add-on for ServiceNow",
        spl=(
            "index=change sourcetype=servicenow:change earliest=-7d\n"
            "| stats latest(implementer) AS implementer latest(approver) AS approver latest(approval_date) AS approved_at latest(state_date) AS implemented_at BY change_id system\n"
            "| lookup financial_systems_apps.csv system OUTPUT in_scope\n"
            "| where in_scope=\"yes\"\n"
            "| eval sod_violation=if(implementer=approver,1,0)\n"
            "| eval approval_before_implementation=if(approved_at<=implemented_at,1,0)\n"
            "| where sod_violation=1 OR approval_before_implementation=0\n"
            "| table change_id system implementer approver approved_at implemented_at sod_violation approval_before_implementation"
        ),
        description="Detects (a) implementer = approver SoD violations and (b) approvals post-dating implementation.",
        value="Eliminates the two patterns that SOX auditors most frequently cite. The daily report is the control evidence.",
        implementation="(1) Maintain financial_systems_apps.csv; (2) capture ServiceNow workflow events; (3) schedule UC hourly; (4) violations open an immediate deficiency; (5) monthly CFO report.",
        visualization="Table of violations, bar chart by system, single value 'SoD + post-implementation approvals'.",
        cim_models=["Change"],
        known_fp="Standard-pre-approved changes legitimately have matching implementer/approver — filter on type!='standard'.",
        required_fields=["change_id", "implementer", "approver", "approval_date", "state_date", "_time"],
        compliance=[
            c_sox("ITGC.ChangeMgmt.Approval", "full",
                  "SOX-ITGC ChangeMgmt.Approval — SoD evidence is direct."),
            c_soc2("CC8.1", "full",
                   "SOC 2 CC8.1 Change management — directly evidenced."),
            c_iso("A.5.3", "partial",
                  "ISO/IEC 27001:2022 A.5.3 Segregation of duties — contributing."),
            c_pci("6.4.4", "partial",
                  "PCI-DSS 6.4.4 Change approvals — contributing."),
        ],
        control_test_positive="A financial-system change with implementer=approver returns sod_violation=1.",
        control_test_negative="A change with distinct implementer/approver and approval_date<=state_date is absent.",
        control_test_attack_technique="T1098",
        mitre_attack=["T1098"],
    ),
    uc(
        id_="22.12.40",
        title="SOX-ITGC Operations.JobSchedule — Batch-schedule monitoring: financial-job exception visibility",
        criticality="medium",
        difficulty="intermediate",
        owner="CFO",
        control_family="regulation-specific",
        security_domain="audit",
        detection_type="Baseline",
        splunk_pillar="IT Operations",
        monitoring_type=["Compliance", "Availability"],
        exclusions="Does NOT run the jobs; detects financial batch jobs that missed their window, failed, or ran with warnings without operator acknowledgement.",
        evidence="Saved search 'sox_itgc_batch_jobs' (every 30m) emits per job: job_id, run_at, state, ack_operator, ack_at, ack_met, to compliance_summary.",
        data_sources="`index=batch` sourcetype=autosys:event OR sourcetype=controlm:job; operator ack `index=ticketing` sourcetype=servicenow:incident (category=batch-ack).",
        app="Splunk Enterprise Security",
        spl=(
            "index=batch sourcetype IN (autosys:event,controlm:job) earliest=-30m\n"
            "| lookup financial_batch_jobs.csv job_id OUTPUT in_scope expected_window\n"
            "| where in_scope=\"yes\"\n"
            "| stats latest(state) AS state latest(_time) AS run_at BY job_id\n"
            "| where state IN (\"FAILED\",\"LATE\",\"WARNING\")\n"
            "| join type=outer job_id\n"
            "  [search index=ticketing sourcetype=servicenow:incident category=batch-ack earliest=-24h\n"
            "   | stats latest(assigned_to) AS ack_operator latest(_time) AS ack_at BY job_id]\n"
            "| eval ack_met=if(isnotnull(ack_operator) AND ack_at>=run_at AND ack_at<=run_at+4*3600,1,0)\n"
            "| where ack_met=0\n"
            "| table job_id run_at state ack_operator ack_at ack_met"
        ),
        description="Measures per-job batch exceptions and requires operator acknowledgement within 4h. SOX-ITGC Operations.JobSchedule requires exception monitoring for financial batch jobs.",
        value="Makes the typically-spreadsheet-based batch monitoring queryable — Ops has a live queue, auditors have a history.",
        implementation="(1) Route Autosys/Control-M events; (2) maintain financial_batch_jobs.csv; (3) schedule UC every 30m; (4) unacked exceptions open an incident; (5) monthly CFO + Head of IT Ops review.",
        visualization="Table of unacked exceptions, time chart of exception rate, single value 'open batch exceptions'.",
        cim_models=["Performance", "Alerts"],
        known_fp="Jobs whose expected_window is currently paused (month-end blackout) should be excluded via the lookup's active window.",
        required_fields=["job_id", "state", "_time"],
        compliance=[
            c_sox("ITGC.Operations.JobSchedule", "full",
                  "SOX-ITGC Operations.JobSchedule — exception acknowledgement evidence."),
            c_soc2("CC7.1", "partial",
                   "SOC 2 CC7.1 — contributing."),
            c_iso("A.8.30", "partial",
                  "ISO/IEC 27001:2022 A.8.30 Outsourced development (for outsourced batch) — contributing."),
        ],
        control_test_positive="A FAILED financial-job with no batch-ack incident within 4h returns ack_met=0.",
        control_test_negative="A job returning state=OK is absent.",
    ),
]


# ---------------------------------------------------------------------------
# Subcategory-title metadata (used when rendering the fenced markdown block)
# ---------------------------------------------------------------------------

SUBCAT_TITLES: Dict[str, str] = {
    "22.3": "DORA — per-regulation content fill (Phase 2.3)",
    "22.6": "ISO/IEC 27001 — per-regulation content fill (Phase 2.3)",
    "22.8": "SOC 2 — per-regulation content fill (Phase 2.3)",
    "22.11": "PCI DSS v4.0 — per-regulation content fill (Phase 2.3)",
    "22.12": "SOX / ITGC — per-regulation content fill (Phase 2.3)",
}


def _build_payload() -> tuple[dict, list[Dict]]:
    all_ucs: List[Dict] = DORA_UCS + ISO_UCS + SOC2_UCS + PCI_UCS + SOX_UCS

    def _key(u: Dict) -> tuple:
        parts = u["id"].split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    all_ucs.sort(key=_key)

    payload = {
        "$comment": "Phase 2.3 authoring source — per-regulation content fills closing tier-1 clause gaps for DORA, ISO/IEC 27001:2022, SOC 2 2017 TSC, PCI-DSS v4.0, and SOX-ITGC PCAOB AS 2201. Generated by scripts/archive/_bootstrap_phase2_3_data.py. Consumed by scripts/generate_phase2_3_per_regulation.py.",
        "schema_version": "2.3.0",
        "generator": "scripts/generate_phase2_3_per_regulation.py",
        "subcat_titles": SUBCAT_TITLES,
        "new_ucs": all_ucs,
    }
    return payload, all_ucs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap data/per-regulation/phase2.3.json from in-script UC "
            "definitions. Default mode is --check (read-only diff). Pass "
            "--write to overwrite the on-disk fixture (destructive — see "
            "module docstring)."
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite the on-disk fixture with the freshly built payload.",
    )
    args = parser.parse_args(argv)

    payload, all_ucs = _build_payload()
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered, encoding="utf-8")
        print(f"Wrote {len(all_ucs)} UCs to {OUT.relative_to(REPO_ROOT)}")
        return 0

    if not OUT.exists():
        print(
            f"FAIL: {OUT.relative_to(REPO_ROOT)} does not exist. "
            "Run with --write to bootstrap a fresh copy.",
            file=sys.stderr,
        )
        return 1

    on_disk = OUT.read_text(encoding="utf-8")
    if on_disk == rendered:
        print(
            f"OK: {OUT.relative_to(REPO_ROOT)} matches the in-script source "
            f"({len(all_ucs)} UCs)."
        )
        return 0

    diff = difflib.unified_diff(
        on_disk.splitlines(keepends=True),
        rendered.splitlines(keepends=True),
        fromfile=str(OUT.relative_to(REPO_ROOT)),
        tofile="rebuilt-from-script",
        n=3,
    )
    sys.stdout.writelines(diff)
    print(
        f"\nDRIFT: on-disk fixture differs from in-script source. "
        "Inspect the diff above; if intentional fixes have been hand-applied "
        "to the JSON since the original bootstrap, do NOT overwrite."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
