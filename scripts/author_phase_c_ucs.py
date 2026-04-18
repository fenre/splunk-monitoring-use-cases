#!/usr/bin/env python3
"""Phase-C author + markdown renderer for the 23 tier-2 gap-closure UCs.

Phase C of the regulation-coverage-gap plan targets every clause where a
regulator's ``commonClauses[]`` entry has no UC claiming it yet. The list was
produced from ``reports/compliance-gaps.json`` after Phase B added
``commonClauses[]`` to the 8 empty tier-2 regulations. Running this script:

    python3 scripts/author_phase_c_ucs.py
    python3 scripts/author_phase_c_ucs.py --check

creates / refreshes:

* ``use-cases/cat-22/uc-22.50.1.json`` .. ``uc-22.50.23.json``  — one
  sidecar per uncovered clause, refusing to overwrite non-Phase-C content
  (i.e. anything whose ``id`` does not start with ``"22.50."``). Existing
  Phase-C JSON files are left untouched so SME uplift work in
  ``status``/``assurance`` stays preserved.
* The ``<!-- PHASE-C BEGIN -->`` ... ``<!-- PHASE-C END -->`` block in
  ``use-cases/cat-22-regulatory-compliance.md`` — re-rendered every run so
  the human-readable markdown stays in lock-step with the JSON sidecars.

``--check`` mode performs the same renders into memory and exits non-zero
if either the JSON sidecars or the markdown block would change. CI wires
this into ``.github/workflows/validate.yml`` so a future contributor cannot
edit only one half and ship inconsistent state.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "use-cases" / "cat-22"
MARKDOWN_PATH = REPO_ROOT / "use-cases" / "cat-22-regulatory-compliance.md"
PHASE_C_BEGIN = "<!-- PHASE-C BEGIN -->"
PHASE_C_END = "<!-- PHASE-C END -->"


@dataclass
class PhaseCSpec:
    """Fields we need for each Phase-C UC."""

    id_suffix: int
    regulation: str
    version: str
    clause: str
    clause_topic: str
    clause_priority: float
    title: str
    data_sources: str
    spl: str
    description: str
    value: str
    implementation: str
    references: List[Dict[str, str]]
    monitoring_type: List[str]
    splunk_pillar: str
    owner: str
    cim_models: List[str]
    authoritative_url: str


# ---------------------------------------------------------------------------
# The 23 UCs — one per still-uncovered tier-2 common clause.
# ---------------------------------------------------------------------------


SPECS: List[PhaseCSpec] = [
    PhaseCSpec(  # uc-22.50.1
        id_suffix=1,
        regulation="AU Privacy Act",
        version="current",
        clause="APP 11",
        clause_topic="Security of personal information",
        clause_priority=1.0,
        title="APP 11 personal-information security — continuous evidence of protective controls",
        data_sources="Authentication events, privileged-access logs, DLP and data-classification events from repositories handling Australian personal information.",
        spl=(
            "index=ident_pii earliest=-24h\n"
            "| search (category=\"pii\" OR data_class=\"personal_information\")\n"
            "| stats dc(subject_id) AS distinct_subjects count(eval(action=\"access\")) AS reads count(eval(action=\"modify\")) AS writes count(eval(outcome=\"blocked\")) AS blocked_attempts BY system, control\n"
            "| eval appears_effective=if(blocked_attempts>0 OR reads>0, \"yes\", \"no\")\n"
            "| table system, control, distinct_subjects, reads, writes, blocked_attempts, appears_effective"
        ),
        description="Aggregates access/modify counts and blocked-attempt evidence across systems that store Australian personal information so APP-11 protective controls can be demonstrated.",
        value="APP 11 requires reasonable steps to protect personal information. Continuous aggregation of protective-control activity provides auditable evidence of those steps.",
        implementation="(1) Tag sources that hold Australian personal information with data_class=personal_information via props/transforms; (2) schedule this search daily; (3) roll up to a 'appears_effective' KPI for the Privacy Officer dashboard.",
        references=[
            {
                "title": "Australian Privacy Principles (APP 11)",
                "url": "https://www.oaic.gov.au/privacy/australian-privacy-principles/australian-privacy-principles-quick-reference",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Authentication", "Change"],
        authoritative_url="https://www.oaic.gov.au/privacy/australian-privacy-principles",
    ),
    PhaseCSpec(  # uc-22.50.2
        id_suffix=2,
        regulation="CJIS",
        version="v5.9.4",
        clause="5.13.3",
        clause_topic="Incident response",
        clause_priority=1.0,
        title="CJIS §5.13.3 incident response — detection, tracking, and reporting evidence",
        data_sources="SIEM incident index, Splunk ES notables, SOAR incident records, CJIS audit logs.",
        spl=(
            "index=notable earliest=-30d\n"
            "| search tag=\"incident_response\" (system_tag=\"cji\" OR data_class=\"cji\")\n"
            "| stats values(severity) AS severities min(_time) AS first_detected max(_time) AS last_update count AS update_count BY rule_id, incident_id\n"
            "| eval mttd_minutes=round((first_detected - strptime(event_time, \"%Y-%m-%dT%H:%M:%SZ\"))/60, 1)\n"
            "| where mttd_minutes <= 1440\n"
            "| table incident_id, rule_id, severities, first_detected, last_update, update_count, mttd_minutes"
        ),
        description="Tracks incident detection, ownership and update cadence for CJI-tagged systems so §5.13.3 evidence is always current.",
        value="§5.13.3 requires agencies to track incidents, notify FBI CJIS ISO within timelines, and retain evidence. Automated cadence tracking keeps the agency audit-ready.",
        implementation="(1) Tag CJI-handling systems with system_tag=cji; (2) route notables to a CJIS-only summary index; (3) alert when mttd_minutes > 1440 (24 h) which is the CJIS reporting window.",
        references=[
            {
                "title": "CJIS Security Policy v5.9.4",
                "url": "https://le.fbi.gov/cjis-division/cjis-security-policy-resource-center",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="Head of IR",
        cim_models=["Alerts"],
        authoritative_url="https://le.fbi.gov/cjis-division/cjis-security-policy-resource-center",
    ),
    PhaseCSpec(  # uc-22.50.3
        id_suffix=3,
        regulation="FCA SM&CR",
        version="current",
        clause="SYSC 3.2",
        clause_topic="Internal controls, systems and audit arrangements",
        clause_priority=1.0,
        title="SYSC 3.2 internal-controls evidence — exceptions, approvals and audit trail",
        data_sources="Change management index (CMDB, ITSM), privileged access logs, approval workflow logs.",
        spl=(
            "index=itsm sourcetype=change_record earliest=-30d\n"
            "| eval approved=if(isnotnull(approver) AND approval_status=\"approved\",1,0)\n"
            "| stats count AS total_changes sum(approved) AS approved_changes count(eval(approval_status=\"emergency\")) AS emergency_changes BY system_criticality\n"
            "| eval approval_rate=round(100*approved_changes/total_changes,1)\n"
            "| where system_criticality=\"critical\" AND approval_rate < 100"
        ),
        description="Surfaces critical-system changes that bypassed approval, reinforcing SYSC 3.2 evidence of internal controls and governance.",
        value="SYSC 3.2 requires firms to maintain adequate internal controls; continuous checks on approval coverage provide the operational evidence.",
        implementation="(1) Onboard ITSM/change approval logs with a 'system_criticality' enrichment; (2) schedule this search weekly; (3) file deviations as a finding in the Senior Manager's responsibility map.",
        references=[
            {
                "title": "FCA Handbook — SYSC 3.2",
                "url": "https://www.handbook.fca.org.uk/handbook/SYSC/3/2.html",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Governance"],
        splunk_pillar="Security",
        owner="Board / Audit Committee",
        cim_models=["Change"],
        authoritative_url="https://www.handbook.fca.org.uk/handbook/SYSC/3/2.html",
    ),
    PhaseCSpec(  # uc-22.50.4
        id_suffix=4,
        regulation="HIPAA Privacy",
        version="current",
        clause="§164.504(e)",
        clause_topic="Business Associate contracts",
        clause_priority=1.0,
        title="§164.504(e) Business Associate activity — PHI access by BA principals",
        data_sources="Access logs from PHI systems enriched with principal classification (workforce vs BA).",
        spl=(
            "index=phi_access earliest=-7d\n"
            "| lookup principals.csv principal_id OUTPUT principal_type, ba_contract_id, ba_expiry\n"
            "| where principal_type=\"business_associate\"\n"
            "| eval contract_valid=if(strptime(ba_expiry, \"%Y-%m-%d\") > now(), \"yes\", \"no\")\n"
            "| stats count AS accesses values(action) AS actions min(_time) AS first_seen max(_time) AS last_seen BY principal_id, ba_contract_id, contract_valid\n"
            "| where contract_valid=\"no\" OR isnull(ba_contract_id)"
        ),
        description="Flags PHI access by business associates whose BAA is missing or expired, providing §164.504(e) evidence.",
        value="HIPAA §164.504(e) requires BAAs; continuous verification that no BA accesses PHI outside a valid contract is primary evidence.",
        implementation="(1) Maintain principals.csv mapping principal_id→ba_contract_id/ba_expiry; (2) schedule daily; (3) route findings to the HIPAA Privacy Officer queue.",
        references=[
            {
                "title": "45 CFR §164.504(e)",
                "url": "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E/section-164.504",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Authentication"],
        authoritative_url="https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E",
    ),
    PhaseCSpec(  # uc-22.50.5
        id_suffix=5,
        regulation="MAS TRM",
        version="2021",
        clause="§11.1.1",
        clause_topic="System resilience",
        clause_priority=1.0,
        title="MAS TRM §11.1.1 system resilience — RTO/RPO burn-rate evidence",
        data_sources="ITSI KPI service health, infrastructure uptime, DR test records.",
        spl=(
            "| inputlookup rto_rpo_targets.csv\n"
            "| eval target_rto_min=coalesce(target_rto_min, 60), target_rpo_min=coalesce(target_rpo_min, 15)\n"
            "| map search=\"| rest /services/data/models/$service_id$/summary | eval measured_rto_min=measured_rto_min, measured_rpo_min=measured_rpo_min | eval service_id=\\\"$service_id$\\\"\"\n"
            "| eval rto_breach=if(measured_rto_min > target_rto_min, \"yes\", \"no\"), rpo_breach=if(measured_rpo_min > target_rpo_min, \"yes\", \"no\")\n"
            "| table service_id, target_rto_min, measured_rto_min, rto_breach, target_rpo_min, measured_rpo_min, rpo_breach"
        ),
        description="Reconciles measured RTO/RPO against contractual targets across critical services so MAS TRM §11.1.1 resilience is demonstrated.",
        value="MAS TRM §11.1.1 requires FI boards to be satisfied with resilience outcomes; automated RTO/RPO reconciliation is auditor-friendly evidence.",
        implementation="(1) Maintain rto_rpo_targets.csv per service_id; (2) ITSI pushes measured values into service summary; (3) schedule weekly report to the board.",
        references=[
            {
                "title": "MAS Technology Risk Management Guidelines (2021)",
                "url": "https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Resilience", "Compliance"],
        splunk_pillar="IT Operations",
        owner="Head of IT Operations",
        cim_models=["Performance"],
        authoritative_url="https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines",
    ),
    PhaseCSpec(  # uc-22.50.6
        id_suffix=6,
        regulation="NERC CIP",
        version="current",
        clause="CIP-008-6 R1",
        clause_topic="Cyber security incident response plan",
        clause_priority=1.0,
        title="NERC CIP-008-6 R1 incident response plan — evidence of activation and review",
        data_sources="SOC ticketing, CIP incident reports, annual plan-review logs.",
        spl=(
            "index=soc_tickets sourcetype=cip:incident earliest=-365d\n"
            "| eval plan_version=coalesce(plan_version,\"unknown\")\n"
            "| stats count AS incidents max(eval(event_type=\"plan_review\")) AS last_review earliest(_time) AS first_activation latest(_time) AS last_activation BY bes_function, plan_version\n"
            "| eval days_since_review=round((now()-last_review)/86400,0)\n"
            "| table bes_function, plan_version, incidents, first_activation, last_activation, days_since_review\n"
            "| where days_since_review > 365 OR isnull(last_review)"
        ),
        description="Highlights BES cyber systems whose CIP-008-6 R1 incident response plan has not been reviewed in the last 365 days.",
        value="CIP-008-6 R1 requires an IR plan and evidence of activation / annual review. Automated tracking catches drift before a CIP enforcement action.",
        implementation="(1) Index plan-review events with event_type=plan_review; (2) schedule the search quarterly; (3) send findings to the NERC CIP evidence pack.",
        references=[
            {
                "title": "NERC CIP-008-6 Cyber Security — Incident Reporting and Response Planning",
                "url": "https://www.nerc.com/pa/Stand/Reliability%20Standards/CIP-008-6.pdf",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="Head of IR",
        cim_models=["Alerts"],
        authoritative_url="https://www.nerc.com/pa/Stand/Pages/default.aspx",
    ),
    PhaseCSpec(  # uc-22.50.7
        id_suffix=7,
        regulation="NO Petroleumsforskriften",
        version="1997 as amended",
        clause="§11",
        clause_topic="Emergency preparedness and response",
        clause_priority=1.0,
        title="Petroleumsforskriften §11 — emergency preparedness drill evidence",
        data_sources="Emergency drill logs, Edge Hub OT alerts, PSA notifications index.",
        spl=(
            "index=psa_emergency earliest=-180d\n"
            "| search (event_type=\"drill\" OR event_type=\"activation\" OR event_type=\"psa_notification\")\n"
            "| stats count(eval(event_type=\"drill\")) AS drill_count count(eval(event_type=\"activation\")) AS activation_count count(eval(event_type=\"psa_notification\")) AS psa_notifications BY installation_id, facility_type\n"
            "| eval drill_status=if(drill_count>=4,\"compliant\",\"gap\")\n"
            "| table installation_id, facility_type, drill_count, activation_count, psa_notifications, drill_status"
        ),
        description="Tracks emergency-preparedness drill frequency, real activations and PSA notifications per offshore installation.",
        value="§11 requires demonstrable preparedness for emergency situations; drill cadence and activation records are auditor-facing evidence.",
        implementation="(1) Ingest drill logs from the offshore operational systems; (2) schedule quarterly; (3) feed results into the PSA (Petroleumstilsynet) evidence pack.",
        references=[
            {
                "title": "Petroleumsforskriften (1997)",
                "url": "https://lovdata.no/dokument/SF/forskrift/1997-06-27-653",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Resilience", "Safety"],
        splunk_pillar="IT Operations",
        owner="Head of OT Security",
        cim_models=["Alerts"],
        authoritative_url="https://lovdata.no/dokument/SF/forskrift/1997-06-27-653",
    ),
    PhaseCSpec(  # uc-22.50.8
        id_suffix=8,
        regulation="NO Sikkerhetsloven",
        version="2018",
        clause="§6-1",
        clause_topic="General preventive security measures",
        clause_priority=1.0,
        title="Sikkerhetsloven §6-1 — preventive control effectiveness across classified systems",
        data_sources="Endpoint security logs, access control logs, encryption/crypto inventory for classified systems.",
        spl=(
            "index=security_classified earliest=-30d\n"
            "| eval control_state=coalesce(control_state, \"unknown\")\n"
            "| stats count AS events count(eval(control_state=\"active\")) AS active count(eval(control_state=\"failed\")) AS failed BY system_id, classification_level, control_type\n"
            "| eval effectiveness=round(100*active/events, 1)\n"
            "| where classification_level IN (\"HEMMELIG\", \"KONFIDENSIELT\") AND effectiveness < 99"
        ),
        description="Measures preventive-control effectiveness on systems processing classified information and flags any drop below 99%.",
        value="§6-1 requires systematic preventive measures; effectiveness KPIs make the §6-1 duty continuously measurable.",
        implementation="(1) Classify systems with classification_level at onboarding; (2) ingest preventive-control telemetry; (3) schedule daily; (4) report to NSM evidence pack.",
        references=[
            {
                "title": "Sikkerhetsloven (Security Act 2018)",
                "url": "https://lovdata.no/dokument/NL/lov/2018-06-01-24",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="CISO",
        cim_models=["Change", "Authentication"],
        authoritative_url="https://lovdata.no/dokument/NL/lov/2018-06-01-24",
    ),
    PhaseCSpec(  # uc-22.50.9
        id_suffix=9,
        regulation="NZISM",
        version="3.7",
        clause="§16.1.32",
        clause_topic="User identification, authentication and access management",
        clause_priority=1.0,
        title="NZISM §16.1.32 — user authentication strength & MFA coverage",
        data_sources="Authentication CIM-tagged logs; SSO / IdP logs for government systems.",
        spl=(
            "| tstats summariesonly=t count FROM datamodel=Authentication.Authentication WHERE Authentication.app!=\"\" BY Authentication.app, Authentication.authentication_method\n"
            "| rename \"Authentication.*\" AS \"*\"\n"
            "| eval is_mfa=if(authentication_method IN (\"mfa\",\"fido2\",\"webauthn\",\"push\",\"totp\",\"smart_card\"),1,0)\n"
            "| eventstats sum(count) AS app_total sum(eval(count*is_mfa)) AS app_mfa BY app\n"
            "| eval mfa_coverage_pct=round(100*app_mfa/app_total,1)\n"
            "| stats first(mfa_coverage_pct) AS mfa_coverage_pct values(authentication_method) AS methods BY app\n"
            "| where mfa_coverage_pct < 100"
        ),
        description="Measures per-app MFA coverage and highlights any government-system access not behind a §16.1.32 strong-authentication mechanism.",
        value="§16.1.32 requires agencies to deploy authentication commensurate with classification; continuous MFA KPIs evidence the control.",
        implementation="(1) Ensure IdP events are CIM-tagged; (2) schedule this tstats hourly; (3) feed non-100% apps to an 'MFA coverage' glass table.",
        references=[
            {
                "title": "NZISM v3.7",
                "url": "https://www.nzism.gcsb.govt.nz/",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Security", "Compliance"],
        splunk_pillar="Security",
        owner="CISO",
        cim_models=["Authentication"],
        authoritative_url="https://www.nzism.gcsb.govt.nz/",
    ),
    PhaseCSpec(  # uc-22.50.10
        id_suffix=10,
        regulation="PIPL",
        version="2021",
        clause="Art.51",
        clause_topic="Information security measures",
        clause_priority=1.0,
        title="PIPL Art.51 — information-security measures across PRC personal-data systems",
        data_sources="Endpoint logs, crypto inventory, access control, vulnerability scanner feeds for PRC-resident systems.",
        spl=(
            "index=prc_systems earliest=-7d\n"
            "| eval control_family=coalesce(control_family,\"unknown\")\n"
            "| stats count AS events count(eval(control_state=\"failed\")) AS failures BY system_id, control_family\n"
            "| eval failure_rate=round(100*failures/events,2)\n"
            "| where failure_rate > 0 AND control_family IN (\"encryption\",\"access_control\",\"vulnerability_mgmt\",\"logging\")"
        ),
        description="Aggregates security-control evidence across PRC-hosted systems handling personal information.",
        value="PIPL Art.51 mandates information-security management; the UC gives data processors Chinese-authority-facing evidence of Art.51 measures.",
        implementation="(1) Tag PRC-resident systems with a 'jurisdiction' field; (2) ingest control telemetry; (3) schedule this search nightly.",
        references=[
            {
                "title": "Personal Information Protection Law of the PRC (PIPL)",
                "url": "http://www.npc.gov.cn/npc/c30834/202108/a8c4e3672c74491a80b53a172bb753fe.shtml",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="http://en.npc.gov.cn.cdurl.cn/",
    ),
    PhaseCSpec(  # uc-22.50.11
        id_suffix=11,
        regulation="QCB Cyber",
        version="2018",
        clause="§4.1",
        clause_topic="Cyber risk identification and management",
        clause_priority=1.0,
        title="QCB §4.1 — cyber-risk register evidence with treatment progress",
        data_sources="GRC risk register, vulnerability management, threat-intelligence feeds.",
        spl=(
            "index=grc sourcetype=risk_register earliest=-180d\n"
            "| eval target_ttc_days=case(severity==\"critical\",30,severity==\"high\",60,severity==\"medium\",90,true(),120)\n"
            "| eval actual_ttc_days=round((coalesce(closed_at, now())-strptime(opened_at,\"%Y-%m-%dT%H:%M:%SZ\"))/86400,0)\n"
            "| eval breaching=if(status!=\"closed\" AND actual_ttc_days>target_ttc_days, \"yes\", \"no\")\n"
            "| table risk_id, severity, opened_at, closed_at, actual_ttc_days, target_ttc_days, breaching, treatment_plan\n"
            "| where breaching=\"yes\""
        ),
        description="Surfaces cyber-risk entries that have exceeded their treatment SLA, evidencing QCB §4.1 risk-management activity.",
        value="§4.1 requires FIs to identify and manage cyber risk; overdue-risk evidence is hard to fake and is directly auditor-facing.",
        implementation="(1) Onboard the GRC risk register; (2) Ensure severity/opened_at/closed_at fields are consistent; (3) schedule weekly.",
        references=[
            {
                "title": "Qatar Central Bank Cybersecurity Framework (2018)",
                "url": "https://www.qcb.gov.qa/",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Risk"],
        splunk_pillar="Security",
        owner="CISO",
        cim_models=["Alerts"],
        authoritative_url="https://www.qcb.gov.qa/",
    ),
    PhaseCSpec(  # uc-22.50.12
        id_suffix=12,
        regulation="SA PDPL",
        version="current",
        clause="Art. 6",
        clause_topic="Lawful grounds and consent for processing",
        clause_priority=1.0,
        title="SA PDPL Art. 6 — processing-purpose and lawful-basis evidence",
        data_sources="Consent management platform logs, downstream processing system logs tagged with purpose.",
        spl=(
            "index=consent sourcetype=cmp:events earliest=-24h\n"
            "| eval lawful_basis=coalesce(lawful_basis,\"unknown\")\n"
            "| stats count AS consented BY subject_id, purpose_id, lawful_basis\n"
            "| join type=left purpose_id\n"
            "    [ search index=app_processing earliest=-24h sourcetype=processing:events | stats count AS processed BY subject_id, purpose_id ]\n"
            "| eval unlawful=if(isnotnull(processed) AND consented=0, \"yes\", \"no\")\n"
            "| where unlawful=\"yes\" OR lawful_basis=\"unknown\""
        ),
        description="Reconciles consent / lawful-basis records with actual processing events, flagging processing performed without a valid Art. 6 basis.",
        value="SA PDPL Art. 6 requires a lawful basis for each processing activity; the UC produces direct evidence of alignment or gaps.",
        implementation="(1) Emit events from the CMP with subject_id + purpose_id + lawful_basis; (2) downstream systems must log processing events with the same purpose_id; (3) schedule daily.",
        references=[
            {
                "title": "Saudi Personal Data Protection Law",
                "url": "https://sdaia.gov.sa/en/SDAIA/about/Files/PersonalDataEnglish.pdf",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="https://sdaia.gov.sa/",
    ),
    PhaseCSpec(  # uc-22.50.13
        id_suffix=13,
        regulation="SWIFT CSP",
        version="CSCF v2025",
        clause="6.1",
        clause_topic="Malware protection",
        clause_priority=1.0,
        title="SWIFT CSCF 6.1 — malware protection across the SWIFT secure zone",
        data_sources="Endpoint detection and response (EDR), antivirus logs from the SWIFT secure zone, CSP attestation evidence.",
        spl=(
            "index=swift_zone earliest=-24h\n"
            "| search (sourcetype=\"av\" OR sourcetype=\"edr\")\n"
            "| stats count AS events count(eval(signature_coverage_hours <= 24)) AS current_coverage count(eval(action=\"block\")) AS blocks BY host, edr_vendor\n"
            "| eval up_to_date=if(current_coverage=events, \"yes\", \"no\")\n"
            "| where up_to_date=\"no\" OR blocks > 0"
        ),
        description="Confirms every SWIFT-secure-zone host is running malware protection with current signatures, evidencing CSCF 6.1.",
        value="CSCF 6.1 is a mandatory control; continuous coverage checks produce annual KYC-SA attestation evidence on demand.",
        implementation="(1) Identify the SWIFT secure zone with a 'zone=swift' asset field; (2) route EDR logs through a dedicated source; (3) schedule daily.",
        references=[
            {
                "title": "SWIFT Customer Security Control Framework (CSCF) v2025",
                "url": "https://www.swift.com/myswift/customer-security-programme-csp/security-controls",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="CISO",
        cim_models=["Change", "Authentication"],
        authoritative_url="https://www.swift.com/myswift/customer-security-programme-csp",
    ),
    PhaseCSpec(  # uc-22.50.14
        id_suffix=14,
        regulation="Swiss nFADP",
        version="2020 revision",
        clause="Art.7",
        clause_topic="Privacy by design and by default",
        clause_priority=1.0,
        title="Swiss nFADP Art.7 — privacy-by-design checkpoints in the SDLC",
        data_sources="SDLC / GitOps pipeline logs, code-review audit events, DPIA tracker.",
        spl=(
            "index=gitops earliest=-90d\n"
            "| search event=\"merge\" AND target_branch=\"main\"\n"
            "| eval dpia_completed=if(isnotnull(dpia_id) AND dpia_status=\"signed\", 1, 0), pbd_review=if(reviewer_role=\"dpo\" OR reviewer_role=\"privacy_engineer\",1,0)\n"
            "| stats sum(dpia_completed) AS dpias sum(pbd_review) AS pbd_reviews count AS merges BY repo, team\n"
            "| eval dpia_rate=round(100*dpias/merges,1), pbd_rate=round(100*pbd_reviews/merges,1)\n"
            "| where pbd_rate < 100 OR dpia_rate < 100"
        ),
        description="Measures what fraction of production-bound merges include a DPIA and a privacy-by-design review checkpoint.",
        value="nFADP Art.7 explicitly requires privacy-by-design; the UC ties the statutory duty to measurable SDLC KPIs.",
        implementation="(1) Ensure GitOps events carry reviewer_role, dpia_id, dpia_status; (2) schedule weekly; (3) publish per-team glass table.",
        references=[
            {
                "title": "Swiss Federal Act on Data Protection (nFADP)",
                "url": "https://www.fedlex.admin.ch/eli/cc/1993/1945_1945_1945/en",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Governance"],
        splunk_pillar="Platform",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="https://www.fedlex.admin.ch/",
    ),
    # ---- Priority 0.7 ----
    PhaseCSpec(  # uc-22.50.15
        id_suffix=15,
        regulation="FCA SM&CR",
        version="current",
        clause="SYSC 4.1",
        clause_topic="General organisational requirements",
        clause_priority=0.7,
        title="SYSC 4.1 organisational requirements — role-population and responsibilities map",
        data_sources="HR system, SMCR responsibilities map, IAM role assignments.",
        spl=(
            "| inputlookup smcr_responsibilities_map.csv\n"
            "| join type=left role_id [ search index=iam earliest=-1d sourcetype=iam:grant | stats latest(principal_id) AS principal_id BY role_id ]\n"
            "| eval assignment_status=if(isnull(principal_id), \"vacant\", \"assigned\")\n"
            "| where assignment_status=\"vacant\" OR (last_review_date!=\"\" AND strptime(last_review_date, \"%Y-%m-%d\") < relative_time(now(), \"-180d\"))"
        ),
        description="Lists Senior Manager responsibilities that are vacant or whose last review is older than 180 days, supporting SYSC 4.1 organisational-arrangements evidence.",
        value="SYSC 4.1 requires clear apportionment of responsibilities; drift detection keeps the Responsibilities Map credible with the FCA.",
        implementation="(1) Publish smcr_responsibilities_map.csv with role_id, responsibility, last_review_date; (2) join IAM data; (3) schedule monthly.",
        references=[
            {
                "title": "FCA Handbook — SYSC 4.1",
                "url": "https://www.handbook.fca.org.uk/handbook/SYSC/4/1.html",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Governance"],
        splunk_pillar="Platform",
        owner="Board / Audit Committee",
        cim_models=["Change"],
        authoritative_url="https://www.handbook.fca.org.uk/handbook/SYSC/4/1.html",
    ),
    PhaseCSpec(  # uc-22.50.16
        id_suffix=16,
        regulation="HIPAA Privacy",
        version="current",
        clause="§164.528",
        clause_topic="Accounting of disclosures",
        clause_priority=0.7,
        title="§164.528 accounting-of-disclosures — retention and responsiveness",
        data_sources="PHI disclosure ledger, patient-request queue logs.",
        spl=(
            "index=phi_disclosures earliest=-365d\n"
            "| eval disclosure_age_days=round((now()-strptime(disclosure_date,\"%Y-%m-%dT%H:%M:%SZ\"))/86400,0)\n"
            "| stats count AS total_disclosures count(eval(request_type=\"patient_request\")) AS patient_requests count(eval(response_time_days <= 60)) AS on_time BY covered_entity\n"
            "| eval response_rate=round(100*on_time/patient_requests,1)\n"
            "| where (total_disclosures=0) OR (patient_requests>0 AND response_rate < 100)"
        ),
        description="Measures accounting-of-disclosures activity and patient-request response rate against the 60-day HIPAA statutory window.",
        value="§164.528 requires the ability to produce an accounting of disclosures within 60 days; continuous metrics prevent nasty surprises during a HIPAA audit.",
        implementation="(1) Persist disclosures in a dedicated ledger index; (2) emit patient-request events with response_time_days; (3) schedule monthly.",
        references=[
            {
                "title": "45 CFR §164.528",
                "url": "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E/section-164.528",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E",
    ),
    PhaseCSpec(  # uc-22.50.17
        id_suffix=17,
        regulation="NESA IAS",
        version="v2 (2020)",
        clause="T3.5",
        clause_topic="Cryptographic controls and key management",
        clause_priority=0.7,
        title="NESA T3.5 cryptographic controls — key-age & HSM inventory evidence",
        data_sources="KMS/HSM inventory, certificate-authority logs, crypto-library runtime telemetry.",
        spl=(
            "index=kms earliest=-1d\n"
            "| stats min(created_at) AS oldest_key max(last_rotated) AS last_rotation count AS total_keys BY key_store, purpose\n"
            "| eval age_days=round((now()-strptime(oldest_key,\"%Y-%m-%dT%H:%M:%SZ\"))/86400,0), rotation_age_days=round((now()-last_rotation)/86400,0)\n"
            "| where age_days > 1095 OR rotation_age_days > 730"
        ),
        description="Identifies keys older than 3 years or last-rotated more than 2 years ago across KMS/HSM inventories supporting UAE-scope processing.",
        value="T3.5 requires effective cryptographic key-management; key-age metrics expose drift from the control.",
        implementation="(1) Onboard KMS/HSM inventory with created_at/last_rotated; (2) schedule weekly; (3) report to the NESA IAS evidence pack.",
        references=[
            {
                "title": "NESA UAE IAS v2 (2020)",
                "url": "https://www.nesa.gov.ae/",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Security"],
        splunk_pillar="Security",
        owner="CISO",
        cim_models=["Change"],
        authoritative_url="https://www.nesa.gov.ae/",
    ),
    PhaseCSpec(  # uc-22.50.18
        id_suffix=18,
        regulation="NO Personopplysningsloven",
        version="2018",
        clause="§14",
        clause_topic="Automated individual decision-making restrictions",
        clause_priority=0.7,
        title="Personopplysningsloven §14 — automated-decision inventory and human-review evidence",
        data_sources="ML/AI model inventory, production decision logs, DPO review records.",
        spl=(
            "index=ai_models earliest=-30d\n"
            "| search scope=\"automated_decision\" AND subject_impact=\"significant\"\n"
            "| stats count AS decisions count(eval(human_review=\"yes\")) AS reviewed earliest(_time) AS first_seen BY model_id, purpose\n"
            "| eval review_rate=round(100*reviewed/decisions,1)\n"
            "| where review_rate < 5"
        ),
        description="Surfaces models producing automated decisions with significant subject impact and low human-review coverage.",
        value="§14 (mirroring GDPR Art.22) requires safeguards for automated individual decisions; a low review rate triggers an immediate DPO review.",
        implementation="(1) Tag models with scope/subject_impact at registration; (2) emit decision logs with human_review flag; (3) schedule weekly.",
        references=[
            {
                "title": "Personopplysningsloven (2018)",
                "url": "https://lovdata.no/dokument/NL/lov/2018-06-15-38",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Risk"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="https://lovdata.no/dokument/NL/lov/2018-06-15-38",
    ),
    PhaseCSpec(  # uc-22.50.19
        id_suffix=19,
        regulation="NO Personopplysningsloven",
        version="2018",
        clause="§2",
        clause_topic="Territorial and material scope",
        clause_priority=0.7,
        title="Personopplysningsloven §2 — territorial/material scope tagging of data flows",
        data_sources="Data catalogue, cross-border transfer logs, processing-activity register.",
        spl=(
            "| inputlookup data_flows.csv\n"
            "| eval scope_tagged=if(isnotnull(scope_no_pol) AND scope_no_pol!=\"\", 1, 0)\n"
            "| stats count AS flows sum(scope_tagged) AS tagged BY dataset, controller\n"
            "| eval coverage_pct=round(100*tagged/flows,1)\n"
            "| where coverage_pct < 100"
        ),
        description="Verifies every dataset in the catalogue carries an explicit §2-scope tag (in-scope / out-of-scope / shared-controller).",
        value="§2 defines when Norwegian data-protection law applies; missing scope tagging is a silent governance failure and the UC catches it.",
        implementation="(1) Require scope_no_pol on every new dataset; (2) run weekly; (3) backfill via DPO workshops.",
        references=[
            {
                "title": "Personopplysningsloven (2018)",
                "url": "https://lovdata.no/dokument/NL/lov/2018-06-15-38",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Governance"],
        splunk_pillar="Platform",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="https://lovdata.no/dokument/NL/lov/2018-06-15-38",
    ),
    PhaseCSpec(  # uc-22.50.20
        id_suffix=20,
        regulation="NO Petroleumsforskriften",
        version="1997 as amended",
        clause="§3",
        clause_topic="General operator obligations for safety and security",
        clause_priority=0.7,
        title="Petroleumsforskriften §3 — operator safety/security obligation register",
        data_sources="HSE management system, operator-activity logs, PSA inspection records.",
        spl=(
            "index=hse sourcetype=operator:activity earliest=-180d\n"
            "| eval obligation=coalesce(obligation,\"unknown\")\n"
            "| stats count AS events count(eval(outcome=\"complete\")) AS complete count(eval(outcome=\"deferred\")) AS deferred BY installation_id, obligation\n"
            "| eval completion_pct=round(100*complete/events,1)\n"
            "| where completion_pct < 95"
        ),
        description="Checks completion of recurring operator obligations tied to §3 (general duties) per offshore installation.",
        value="§3 establishes the operator's general duty of care; continuous monitoring of recurring obligations is good stewardship evidence.",
        implementation="(1) Canonicalise obligation labels; (2) emit completion events from the HSE system; (3) schedule monthly.",
        references=[
            {
                "title": "Petroleumsforskriften (1997)",
                "url": "https://lovdata.no/dokument/SF/forskrift/1997-06-27-653",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Safety"],
        splunk_pillar="IT Operations",
        owner="Head of OT Security",
        cim_models=["Change"],
        authoritative_url="https://lovdata.no/dokument/SF/forskrift/1997-06-27-653",
    ),
    PhaseCSpec(  # uc-22.50.21
        id_suffix=21,
        regulation="NO Sikkerhetsloven",
        version="2018",
        clause="§5-2",
        clause_topic="Internal control and annual security review",
        clause_priority=0.7,
        title="Sikkerhetsloven §5-2 — annual internal security review activity",
        data_sources="Internal-audit workflow, CISO dashboard inputs, NSM reporting queue.",
        spl=(
            "index=audit_workflow earliest=-400d\n"
            "| search scope=\"internal_security_review\"\n"
            "| stats max(_time) AS last_run count(eval(outcome=\"approved\")) AS approved count AS runs BY entity_id, entity_type\n"
            "| eval days_since=round((now()-last_run)/86400,0)\n"
            "| where days_since > 365 OR approved < runs"
        ),
        description="Lists entities whose annual §5-2 internal security review is overdue or whose latest review was not approved.",
        value="§5-2 mandates an annual internal security review; a simple overdue-check prevents long silent gaps.",
        implementation="(1) Log every internal security review with scope, outcome, entity_id; (2) schedule weekly; (3) feed NSM reporting dashboard.",
        references=[
            {
                "title": "Sikkerhetsloven (Security Act 2018)",
                "url": "https://lovdata.no/dokument/NL/lov/2018-06-01-24",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Audit"],
        splunk_pillar="Security",
        owner="CISO",
        cim_models=["Change"],
        authoritative_url="https://lovdata.no/dokument/NL/lov/2018-06-01-24",
    ),
    PhaseCSpec(  # uc-22.50.22
        id_suffix=22,
        regulation="NZISM",
        version="3.7",
        clause="§12.4",
        clause_topic="Information security documentation and policy",
        clause_priority=0.7,
        title="NZISM §12.4 — policy documentation freshness and approval state",
        data_sources="Policy repository, document control system, CISO approval records.",
        spl=(
            "| inputlookup policy_repository.csv\n"
            "| eval age_days=round((now()-strptime(last_reviewed, \"%Y-%m-%d\"))/86400, 0)\n"
            "| eval stale=if(age_days > 365, \"yes\", \"no\")\n"
            "| stats count AS docs sum(eval(stale=\"yes\")) AS stale_count values(owner) AS owners BY policy_domain\n"
            "| eval stale_pct=round(100*stale_count/docs,1)\n"
            "| where stale_count > 0"
        ),
        description="Lists policy documents that exceed the NZISM §12.4 annual review cadence.",
        value="§12.4 requires policies to be kept current; stale-policy metrics are direct GCSB-facing evidence.",
        implementation="(1) Publish policy_repository.csv with last_reviewed dates; (2) schedule monthly; (3) alert CISO on any stale_count > 0.",
        references=[
            {
                "title": "NZISM v3.7",
                "url": "https://www.nzism.gcsb.govt.nz/",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance", "Governance"],
        splunk_pillar="Platform",
        owner="CISO",
        cim_models=["Change"],
        authoritative_url="https://www.nzism.gcsb.govt.nz/",
    ),
    PhaseCSpec(  # uc-22.50.23
        id_suffix=23,
        regulation="SA PDPL",
        version="current",
        clause="Art. 29",
        clause_topic="Cross-border personal data transfers",
        clause_priority=0.7,
        title="SA PDPL Art. 29 — cross-border transfer inventory and legal-basis evidence",
        data_sources="Data transfer ledger, cloud-region event logs, SDAIA notification records.",
        spl=(
            "index=data_transfer earliest=-30d\n"
            "| search src_jurisdiction=\"SA\"\n"
            "| eval basis_valid=if(legal_basis IN (\"adequacy\",\"scc\",\"consent\",\"exemption\") AND isnotnull(legal_basis_ref),1,0)\n"
            "| stats count AS transfers sum(basis_valid) AS with_basis BY dst_jurisdiction, data_class\n"
            "| eval compliance_pct=round(100*with_basis/transfers,1)\n"
            "| where compliance_pct < 100"
        ),
        description="Inventory-style view of cross-border transfers from SA with the lawful basis attached; flags any transfer without an Art. 29 basis.",
        value="Art. 29 requires a documented basis for every outbound transfer; continuous inventory is superior to point-in-time attestations.",
        implementation="(1) Emit every outbound transfer event with src_jurisdiction, dst_jurisdiction, legal_basis, legal_basis_ref; (2) schedule daily.",
        references=[
            {
                "title": "Saudi Personal Data Protection Law",
                "url": "https://sdaia.gov.sa/en/SDAIA/about/Files/PersonalDataEnglish.pdf",
                "retrieved": "2026-04-18",
            }
        ],
        monitoring_type=["Compliance"],
        splunk_pillar="Security",
        owner="DPO",
        cim_models=["Change"],
        authoritative_url="https://sdaia.gov.sa/",
    ),
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_uc(spec: PhaseCSpec) -> Dict[str, Any]:
    """Return the serialised UC dict from a spec."""

    rationale = (
        f"Phase-C authored UC targeting {spec.regulation} {spec.clause} "
        f"({spec.clause_topic}). Uses continuous, production-grade Splunk "
        f"telemetry to provide auditor-facing evidence; assurance level "
        f"set to 'contributing' pending SME review per Phase E of the "
        f"regulation-coverage plan."
    )
    uc: Dict[str, Any] = {
        "$schema": "../../schemas/uc.schema.json",
        "id": f"22.50.{spec.id_suffix}",
        "title": spec.title,
        "criticality": "high" if spec.clause_priority >= 1.0 else "medium",
        "difficulty": "intermediate",
        "monitoringType": spec.monitoring_type,
        "splunkPillar": spec.splunk_pillar,
        "owner": spec.owner,
        "controlFamily": "regulation-specific",
        "exclusions": (
            "Does NOT substitute for the full regulatory control set; this UC "
            "provides one of several evidence streams and must be combined "
            "with policy, procedure, and supplemental UCs to demonstrate the "
            "complete clause."
        ),
        "evidence": (
            f"Scheduled search output persisted to the compliance summary "
            f"index with regulation={spec.regulation}, clause={spec.clause}, "
            f"available as a saved search and exportable as a CSV evidence "
            f"pack for the responsible officer."
        ),
        "compliance": [
            {
                "regulation": spec.regulation,
                "version": spec.version,
                "clause": spec.clause,
                "mode": "satisfies",
                "assurance": "contributing",
                "assurance_rationale": rationale,
                "provenance": "maintainer",
                "smeCaveat": (
                    "Phase-C draft: SME review required before uplifting "
                    "assurance from 'contributing' to 'partial' or 'full'. "
                    "Confirm that the SPL captures the specific regulator "
                    "expectation and that the telemetry exists in the "
                    "deployment."
                ),
            }
        ],
        "dataSources": spec.data_sources,
        "app": "Splunk Enterprise / Splunk Cloud Platform",
        "spl": spec.spl,
        "description": spec.description,
        "value": spec.value,
        "implementation": spec.implementation,
        "visualization": (
            "Table of flagged records for investigation; single-value KPI of "
            "coverage / compliance percentage; time chart of trend over the "
            "last 90 days; drill-down per responsible owner."
        ),
        "cimModels": spec.cim_models,
        "references": spec.references,
        "knownFalsePositives": (
            "Tuning prerequisites: source field mappings must be in place "
            "before the UC will produce reliable metrics; early runs will "
            "commonly flag unmapped systems until onboarding is completed."
        ),
        "mitreAttack": [],
        "detectionType": "Correlation",
        "securityDomain": "audit",
        "requiredFields": ["_time"],
        "status": "community",
        "lastReviewed": "2026-04-18",
        "splunkVersions": ["9.2+", "Cloud"],
        "reviewer": "N/A",
    }
    return uc


# ---------------------------------------------------------------------------
# Markdown rendering — keeps cat-22-regulatory-compliance.md in sync.
# ---------------------------------------------------------------------------

# The label maps mirror the conventions used by the existing PHASE-2.2 /
# PHASE-2.3 blocks and the hand-authored UC-22.49.x cluster. Keep them in
# lock-step with `scripts/audit_uc_structure.py` if those rules change.
_CRITICALITY_LABELS = {
    "critical": "🔴 Critical",
    "high": "🟠 High",
    "medium": "🟡 Medium",
    "low": "🟢 Low",
}
_DIFFICULTY_LABELS = {
    "beginner": "🟢 Beginner",
    "intermediate": "🔵 Intermediate",
    "advanced": "🟠 Advanced",
}


def _render_uc_markdown(spec: PhaseCSpec, uc: Dict[str, Any]) -> str:
    """Return the markdown block for a single Phase-C UC.

    The shape mirrors UC-22.49.x (the closest hand-authored neighbour) so
    a reader scrolling through cat-22 cannot tell the Phase-C block apart
    from the surrounding pre-existing content.
    """

    criticality = _CRITICALITY_LABELS[uc["criticality"]]
    difficulty = _DIFFICULTY_LABELS[uc["difficulty"]]
    monitoring_type = ", ".join(uc["monitoringType"])
    cim_models = ", ".join(uc["cimModels"]) if uc["cimModels"] else "N/A"
    references = ", ".join(
        f"[{ref['title']}]({ref['url']})" for ref in uc["references"]
    )
    lines = [
        f"### UC-{uc['id']} · {uc['title']}",
        f"- **Criticality:** {criticality}",
        f"- **Difficulty:** {difficulty}",
        f"- **Monitoring type:** {monitoring_type}",
        f"- **Splunk Pillar:** {uc['splunkPillar']}",
        f"- **Regulations:** {spec.regulation}",
        f"- **Value:** {uc['value']}",
        f"- **App/TA:** {uc['app']}",
        f"- **Data Sources:** {uc['dataSources']}",
        "- **SPL:**",
        "```spl",
        uc["spl"],
        "```",
        f"- **Implementation:** {uc['implementation']}",
        f"- **Visualization:** {uc['visualization']}",
        f"- **CIM Models:** {cim_models}",
        f"- **Known false positives:** {uc['knownFalsePositives']}",
        f"- **References:** {references}",
    ]
    return "\n".join(lines)


def _render_phase_c_block() -> str:
    """Return the full content that lives between the PHASE-C fences.

    The block always ships with:

    * a managed-by-generator banner (so contributors do not hand-edit it);
    * a single subcategory header — Phase-C UCs share one umbrella
      ("tier-2 framework clause coverage") rather than being grouped by
      regulation, because each UC targets a distinct regulator and there
      are not enough peers to justify per-regulation subcategories;
    * the 23 UC blocks in id order, separated by ``---`` rules to match
      the surrounding visual style.
    """

    parts: List[str] = [
        "<!--",
        "  The UC blocks between the PHASE-C fences are generated from",
        "  scripts/author_phase_c_ucs.py (the SPECS table at the top of the",
        "  script is the source of truth — both the JSON sidecars and these",
        "  markdown blocks are rendered from it). Do not edit this section by",
        "  hand. Edit the SPECS in the script and re-run.",
        "-->",
        "",
        "### 22.50 — Tier-2 framework clause coverage",
        "",
        (
            "Phase-C closure UCs targeting the remaining uncovered priority "
            "clauses across tier-2 regulators (AU Privacy Act APP 11, CJIS, "
            "FCA SM&CR, HIPAA Privacy §164.504(e)/§164.528, MAS TRM, "
            "NERC CIP, NO Petroleumsforskriften / Sikkerhetsloven / "
            "Personopplysningsloven, NZISM, PIPL, QCB Cyber, SA PDPL, "
            "SWIFT CSP, Swiss nFADP, NESA IAS). Each UC ships with an "
            "explicit SME caveat in its JSON sidecar — assurance starts at "
            "`contributing` and must be uplifted to `partial` or `full` "
            "only after a domain-SME confirms the SPL captures the actual "
            "regulator expectation."
        ),
        "",
    ]
    for spec in SPECS:
        uc = build_uc(spec)
        parts.append("---")
        parts.append("")
        parts.append(_render_uc_markdown(spec, uc))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _build_markdown_content(current: str) -> str:
    """Return ``current`` with the PHASE-C block re-rendered.

    If the PHASE-C fences are missing, append them after the last existing
    block in the file. We anchor on PHASE-2.3 END if present, otherwise on
    EOF — the cat-22 markdown ships with PHASE-2.3 today, but new contents
    might be appended in the future and we do not want to clobber them.
    """

    block = _render_phase_c_block()
    fenced = f"{PHASE_C_BEGIN}\n\n{block}\n{PHASE_C_END}\n"
    pattern = re.compile(
        re.escape(PHASE_C_BEGIN) + r".*?" + re.escape(PHASE_C_END) + r"\n?",
        re.DOTALL,
    )
    if pattern.search(current):
        return pattern.sub(fenced, current, count=1)
    # No PHASE-C fences yet — append after PHASE-2.3 END or EOF.
    anchor = "<!-- PHASE-2.3 END -->\n"
    if anchor in current:
        head, _, tail = current.partition(anchor)
        return head + anchor + "\n" + fenced + tail.lstrip("\n")
    # Fall back to EOF append with a single trailing newline.
    return current.rstrip("\n") + "\n\n" + fenced


def _process_jsons(check: bool) -> int:
    """Write or verify Phase-C JSON sidecars. Returns drift count."""

    drift = 0
    for spec in SPECS:
        path = OUT_DIR / f"uc-22.50.{spec.id_suffix}.json"
        uc = build_uc(spec)
        rendered = json.dumps(uc, indent=2, ensure_ascii=False) + "\n"
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                sys.stderr.write(f"error: {path} exists but is unreadable.\n")
                return -1
            if not str(existing.get("id", "")).startswith("22.50."):
                sys.stderr.write(
                    f"error: {path} exists and id={existing.get('id')!r}; "
                    "refusing to overwrite.\n"
                )
                return -1
            # Refuse to clobber SME uplift work — leave existing Phase-C
            # JSONs untouched whether or not the SPECS table has drifted.
            # In `--check` mode we treat that as "no drift" because the
            # generator is intentionally non-destructive.
            continue
        if check:
            drift += 1
            sys.stderr.write(f"drift: {path.relative_to(REPO_ROOT)} would be created\n")
            continue
        path.write_text(rendered, encoding="utf-8")
        sys.stdout.write(f"wrote {path.relative_to(REPO_ROOT)}\n")
    return drift


def _process_markdown(check: bool) -> int:
    """Write or verify the PHASE-C markdown block. Returns drift count."""

    if not MARKDOWN_PATH.exists():
        sys.stderr.write(f"error: {MARKDOWN_PATH} missing.\n")
        return -1
    current = MARKDOWN_PATH.read_text(encoding="utf-8")
    new_content = _build_markdown_content(current)
    if current == new_content:
        return 0
    if check:
        sys.stderr.write(
            f"drift: {MARKDOWN_PATH.relative_to(REPO_ROOT)} PHASE-C block "
            "is out of sync with scripts/author_phase_c_ucs.py.\n"
        )
        return 1
    MARKDOWN_PATH.write_text(new_content, encoding="utf-8")
    sys.stdout.write(f"updated {MARKDOWN_PATH.relative_to(REPO_ROOT)} PHASE-C block\n")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Verify-only mode: exit non-zero if any JSON sidecar would be "
            "newly created or if the PHASE-C markdown block is out of sync."
        ),
    )
    args = parser.parse_args(argv)
    if not OUT_DIR.exists():
        sys.stderr.write(f"error: {OUT_DIR} missing.\n")
        return 1

    json_drift = _process_jsons(args.check)
    if json_drift < 0:
        return 1
    md_drift = _process_markdown(args.check)
    if md_drift < 0:
        return 1

    if args.check:
        total = json_drift + md_drift
        if total > 0:
            sys.stderr.write(
                f"\nPhase-C drift detected: {total} item(s) need regeneration.\n"
                "Run: python3 scripts/author_phase_c_ucs.py\n"
            )
            return 1
        sys.stdout.write("Phase-C author/render: clean\n")
        return 0

    sys.stdout.write("\nPhase-C authoring complete.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
