#!/usr/bin/env python3
"""One-shot generator: compliance gap-closure UC sidecars (Wave 1).

Reads the locked gap manifest and writes cat-22 JSON sidecars that map
each uncovered commonClauses[] entry in data/regulations.json.

Run from repo root:
    python3 scripts/generate_compliance_gap_closure.py
    python3 scripts/generate_compliance_gap_closure.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(REPO_ROOT, "content", "cat-22-regulatory-compliance")

TSA_VERSION = "2024-consolidated-pipeline-rail"
SOCI_VERSION = "2022-SLACIP+CIRMP-2023"
SG_VERSION = "2018-amended-2024"
CLC_VERSION = "2021-with-iec63452-alignment"
IEC61511_VERSION = "2016-iec-61511-ed-2-with-isa-tr84-00-09"
AWIA_VERSION = "2018-amended-SDWA-1433"
CERTIN_VERSION = "2022-04-28-cert-in-directions-with-2023-dpdp"
CNSL_VERSION = "2017-csl-with-2021-dsl-pipl-and-2022-ciio-cross-border"
FRLPM_VERSION = "2013-2018-with-anssi-2024-decrees"
IMO_VERSION = "2017-msc-428-98-with-2022-circ-3-rev-2-and-2024-iacs-e26-e27"

DETAILED_IMPL = """## Prerequisites

- Splunk Enterprise 9.2+ or Splunk Cloud with Enterprise Security (Splunkbase 263).
- Splunk Common Information Model Add-on (Splunkbase 1621).
- Splunk Add-on for ServiceNow (Splunkbase 1928) when ITSM or CMDB evidence is referenced.
- Dedicated `index=audit_evidence` with at least a seven-year retention policy for regulatory artefacts.
- RBAC: compliance-analyst role with read on source indexes and write on `audit_evidence`.

## Step 1 — Configure data collection

Populate the KV Store / lookup named in `dataSources` from the authoritative GRC or operational source of record. Validate ingest with a 24-hour `timechart count` on each sourcetype before enabling the scheduled search.

## Step 2 — Create the search and alert

Schedule the saved search on the cadence documented in `implementation`. Route `action_required` or equivalent status values to an ES notable with severity mapped to business impact. Archive every result row to `audit_evidence` using a summary-index action with markers `uc=<id>` and `clause=<clause>`.

## Step 3 — Validate deployment

**(a)** Inject a synthetic non-compliant row into the lookup and confirm the search surfaces it within one schedule interval.

**(b)** Restore compliant values and confirm the search returns zero actionable rows.

**(c)** Export a CSV from the dashboard and verify column names match the `evidence` field contract.

## Step 4 — Operationalize

Build the dashboard referenced in `visualization`. Integrate the runbook with the control owner named in `owner`. Review false-positive suppressions monthly.

## Step 5 — Troubleshooting

**Lookup drift** — reconcile weekly against the source system.

**Silent search** — confirm modular inputs are enabled and license volume has headroom.

**False-positive storm** — tune suppressions in the documented KV Store exception collection with time-bound grants.

**Audit export gaps** — verify summary-index routing and retention on `audit_evidence`.

**Cross-timezone timestamps** — normalise all `_time` fields to UTC before SLA math.

**SOAR / ticket desync** — ensure bidirectional sync populates disposition fields used in the SPL filter."""

KNOWN_FPS = """1. **Planned maintenance window** — documented change windows in the exception lookup suppress benign activity during approved work.

2. **Pen-test / red-team activity** — engagements carrying an agreed rules-of-engagement marker must be excluded via `pentest_window_lookup`.

3. **Vendor remote-access sessions** — authorised vendor PAM sessions cross-reference `vendor_session_lookup` before alerting.

4. **Commissioning / factory acceptance** — temporary engineering states are pinned in the exception register with a 30-day maximum grant.

**Suppression mechanism**: KV Store `<uc_id>_exceptions` with documented control-owner approval and time-bound expiry."""


def _entry(
    uc_id: str,
    title: str,
    regulation: str,
    version: str,
    clause: str,
    *,
    industry: str = "Critical Infrastructure",
    owner: str = "CISO",
    assurance: str = "partial",
    spl: str,
    description: str,
    value: str,
    data_sources: str,
    evidence: str,
    control_objective: str,
    evidence_artifact: str,
    assurance_rationale: str,
    prerequisite: list[str] | None = None,
    wave: str = "walk",
    difficulty: str = "intermediate",
    criticality: str = "high",
    control_family: str = "regulation-specific",
    exclusions: str | None = None,
    authoritative_url: str | None = None,
) -> dict[str, Any]:
    obligation_ref = f"{regulation}@{version}#{clause}"
    if exclusions is None:
        exclusions = (
            "Excludes assets explicitly out of regulatory scope. "
            "Excludes documented exception windows in the UC-specific suppression lookup."
        )
    refs = [
        {
            "title": f"Authoritative source — {regulation} {clause}",
            "url": authoritative_url or "https://www.example.com/regulatory-source",
        },
        {
            "title": "Splunk Enterprise Security",
            "url": "https://splunkbase.splunk.com/app/263",
        },
        {
            "title": "Splunk Common Information Model Add-on",
            "url": "https://splunkbase.splunk.com/app/1621",
        },
        {
            "title": "Splunk Add-on for ServiceNow",
            "url": "https://splunkbase.splunk.com/app/1928",
        },
    ]
    doc: dict[str, Any] = {
        "$schema": "../../schemas/uc.schema.json",
        "id": uc_id,
        "title": title,
        "criticality": criticality,
        "difficulty": difficulty,
        "monitoringType": ["Compliance", "Governance"],
        "splunkPillar": "Security",
        "industry": industry,
        "owner": owner,
        "controlFamily": control_family,
        "exclusions": exclusions,
        "evidence": evidence,
        "compliance": [
            {
                "regulation": regulation,
                "version": version,
                "clause": clause,
                "mode": "satisfies",
                "assurance": assurance,
                "assurance_rationale": assurance_rationale,
                "controlObjective": control_objective,
                "evidenceArtifact": evidence_artifact,
                "obligationRef": obligation_ref,
                "requires_sme_review": True,
                "provenance": "maintainer",
            }
        ],
        "controlTest": {
            "positiveScenario": (
                f"Set a synthetic non-compliant state in the governing lookup for {clause}. "
                f"The saved search UC-{uc_id} MUST surface an actionable row within one schedule interval."
            ),
            "negativeScenario": (
                f"Restore compliant values in the lookup. UC-{uc_id} MUST NOT produce actionable rows."
            ),
        },
        "dataSources": data_sources,
        "app": "Splunk Enterprise Security (Splunkbase 263), Splunk Common Information Model Add-on (Splunkbase 1621), Splunk Add-on for ServiceNow (Splunkbase 1928).",
        "spl": spl,
        "description": description,
        "value": value,
        "implementation": (
            f"(1) Populate lookups referenced in dataSources. "
            f"(2) Schedule UC-{uc_id} per the control cadence. "
            f"(3) Route actionable rows to ES notables and archive to audit_evidence. "
            f"(4) Build the compliance dashboard panel for {clause}."
        ),
        "visualization": (
            f"(Panel 1) Compliance status summary for {clause}. "
            f"(Panel 2) Open exceptions / overdue items. "
            f"(Panel 3) 90-day trend. "
            f"(Panel 4) Evidence export readiness."
        ),
        "cimModels": ["Change", "Inventory"],
        "references": refs,
        "knownFalsePositives": KNOWN_FPS,
        "mitreAttack": ["T1078"],
        "requiredFields": ["status", "last_reviewed_at"],
        "equipment": ["servicenow", "splunk-es"],
        "equipmentModels": ["Splunk Enterprise Security 7.x (Splunkbase 263)"],
        "status": "community",
        "lastReviewed": "2026-07-24",
        "splunkVersions": ["9.2+", "Cloud"],
        "reviewer": "Compliance SME Panel",
        "premiumApps": ["Splunk Enterprise Security"],
        "detailedImplementation": DETAILED_IMPL.replace("<uc_id>", uc_id.replace(".", "_")).replace("<id>", uc_id).replace("<clause>", clause),
        "grandmaExplanation": (
            f"We keep an eye on {title.split('—')[0].strip()} so auditors can see we are meeting "
            f"the rule {clause} and we get warned before we fall out of compliance."
        ),
        "splunkbaseApps": [
            {
                "id": 263,
                "name": "Splunk Enterprise Security",
                "url": "https://splunkbase.splunk.com/app/263",
                "role": "premium",
                "requiresSmeReview": True,
            }
        ],
        "wave": wave,
    }
    if prerequisite:
        doc["prerequisiteUseCases"] = prerequisite
    return doc


def manifest() -> list[dict[str, Any]]:
    """All 46 gap-closure UCs with stable IDs."""
    m: list[dict[str, Any]] = []

    # --- TSA Surface (22.56.29–46) ---
    tsa_spl_gov = '| inputlookup {lookup}\n| eval status = case(isnull({field}) OR {field}!="current", "action_required", 1=1, "current")\n| where status="action_required"\n| table * status'
    tsa_entries = [
        ("22.56.29", "TSA-SD Freight Rail Cybersecurity Coordinator designation — roster, SSI eligibility, and 7-day TSA notification", "TSA-SD-1580-82-2022-01-s3", "tsa_freight_cc_roster_lookup", "roster_status"),
        ("22.56.30", "TSA-SD Freight Rail CIRP annual exercise — scheduling, after-action evidence, and corrective-action ledger", "TSA-SD-1580-82-2022-01-s4", "tsa_freight_cirp_exercise_lookup", "exercise_status"),
        ("22.56.31", "TSA-SD Freight Rail cybersecurity vulnerability assessment — cadence, scope, and remediation tracking", "TSA-SD-1580-82-2022-01-s5", "tsa_freight_vuln_assessment_lookup", "assessment_status"),
        ("22.56.32", "TSA-SD Freight Rail annual CIP attestation and corrective-action submission evidence", "TSA-SD-1580-82-2022-01-s6", "tsa_freight_cip_attestation_lookup", "attestation_status"),
        ("22.56.33", "TSA-SD Passenger Rail Cybersecurity Coordinator designation — roster, SSI eligibility, and 7-day TSA notification", "TSA-SD-1582-2022-01-s3", "tsa_passenger_cc_roster_lookup", "roster_status"),
        ("22.56.34", "TSA-SD Passenger Rail CIRP annual exercise — scheduling, after-action evidence, and corrective-action ledger", "TSA-SD-1582-2022-01-s4", "tsa_passenger_cirp_exercise_lookup", "exercise_status"),
        ("22.56.35", "TSA-SD Passenger Rail CIP control family 1 — IT/OT network segmentation drift detection", "TSA-SD-1582-2022-01-cf-1", "tsa_passenger_zones_lookup", "drift_status"),
        ("22.56.36", "TSA-SD Passenger Rail CIP control family 2 — access control and MFA for OT remote access", "TSA-SD-1582-2022-01-cf-2", "tsa_passenger_access_lookup", "access_status"),
        ("22.56.37", "TSA-SD Passenger Rail CIP control family 3 — continuous monitoring and detection coverage", "TSA-SD-1582-2022-01-cf-3", "tsa_passenger_monitoring_lookup", "monitoring_status"),
        ("22.56.38", "TSA-SD Passenger Rail CIP control family 4 — timely patching with OT maintenance-window governance", "TSA-SD-1582-2022-01-cf-4", "tsa_passenger_patch_lookup", "patch_status"),
        ("22.56.39", "TSA-SD Passenger Rail CIP control family 5 — cybersecurity assessment and CSAS evidence package", "TSA-SD-1582-2022-01-cf-5", "tsa_passenger_csas_lookup", "csas_status"),
        ("22.56.40", "TSA-SD Passenger Rail OT configuration management — baseline drift and change-authorisation evidence", "TSA-SD-1582-2022-01-cf-6", "tsa_passenger_config_lookup", "config_status"),
        ("22.56.41", "TSA-SD Surface Authorized Compliance Official (ACO) designation and notification surveillance", "TSA-SCAS-aco-designation", "tsa_surface_aco_lookup", "aco_status"),
        ("22.56.42", "TSA-SD Pipeline annual CIP attestation and corrective-action submission evidence", "TSA-SD-P-2021-02C-s6", "tsa_pipeline_cip_attestation_lookup", "attestation_status"),
        ("22.56.43", "TSA-SD Pipeline supply-chain and third-party cybersecurity risk register monitoring", "TSA-SD-P-2021-02C-s7", "tsa_pipeline_supply_chain_lookup", "vendor_risk_status"),
        ("22.56.44", "TSA-SD Pipeline OT configuration management — authorised baseline and drift detection", "TSA-SD-P-2021-02C-s8", "tsa_pipeline_config_lookup", "config_status"),
        ("22.56.45", "TSA-SD Pipeline cyber incidents affecting physical operations — correlated reporting evidence", "TSA-SD-P-2021-01-s4", "tsa_pipeline_physical_impact_lookup", "reporting_status"),
        ("22.56.46", "TSA-SD Pipeline recovery and resilience testing — exercise currency and evidence retention", "TSA-SD-P-2021-02C-s9", "tsa_pipeline_recovery_test_lookup", "recovery_test_status"),
    ]
    for uid, title, clause, lookup, field in tsa_entries:
        spl = tsa_spl_gov.format(lookup=lookup, field=field)
        m.append(
            _entry(
                uid,
                title,
                "tsa-surface",
                TSA_VERSION,
                clause,
                industry="Pipeline + Rail",
                spl=spl,
                description=f"Surfaces non-compliant rows in `{lookup}` for TSA Surface clause {clause}.",
                value=f"TSA Surface enforcement for {clause} requires demonstrable, current evidence—not static policy PDFs.",
                data_sources=f"KV Store `{lookup}`; ServiceNow GRC tasks (`index=itsm sourcetype=snow:task`); Splunk audit archive (`index=audit_evidence`).",
                evidence=f"Saved search `UC-{uid}` archived to `audit_evidence` with `tsa_sd_clause=\"{clause}\"`.",
                control_objective=f"Demonstrates ongoing compliance with {clause} via measurable operational evidence.",
                evidence_artifact=f"Saved search UC-{uid}, dashboard panel, and quarterly export filed in the TSA CSAS package.",
                assurance_rationale=f"Operationalises observable elements of {clause}. Marked partial where legal attestation or manual TSA filing remains outside Splunk.",
                prerequisite=["UC-22.56.1"],
                authoritative_url="https://www.tsa.gov/news/press/releases/2024/06/07/tsa-reissues-cybersecurity-requirements-pipeline-industry",
            )
        )

    # --- SG Cyber Act (22.57.16–24) ---
    sg_entries = [
        ("22.57.16", "SG Cyber Act Code of Practice implementation coverage — control-family attestation register", "SG-CA-s10"),
        ("22.57.17", "SG Cyber Act prescribed cybersecurity incident reporting to Commissioner — readiness and submission evidence", "SG-CA-s14(1)"),
        ("22.57.18", "SG Cyber Act Commissioner investigation cooperation — evidence-pack assembly and response SLA", "SG-CA-s19"),
        ("22.57.19", "SG CII Regulations Cybersecurity Officer and Alternate designation register", "SG-CII-Reg-3"),
        ("22.57.20", "SG CII Regulations 2-hour prescribed incident reporting clock-burn surveillance", "SG-CII-Reg-5"),
        ("22.57.21", "SG CSA Code of Practice — asset management and inventory completeness", "SG-CSA-COC-asset-mgmt"),
        ("22.57.22", "SG CSA Code of Practice — identity, access, MFA, and privileged-account evidence", "SG-CSA-COC-access-control"),
        ("22.57.23", "SG CSA Code of Practice — third-party and managed-service cybersecurity obligations", "SG-CSA-COC-supply-chain"),
        ("22.57.24", "SG CSA Code of Practice — business continuity and disaster recovery for the CII", "SG-CSA-COC-business-continuity"),
    ]
    for uid, title, clause in sg_entries:
        lookup = f"csa_{clause.lower().replace('-', '_')}_lookup"
        spl = f'| inputlookup {lookup}\n| eval status = case(compliance_state!="current", "action_required", 1=1, "current")\n| where status="action_required"\n| table cii_id clause compliance_state status'
        m.append(
            _entry(
                uid,
                title,
                "sg-cyber-act",
                SG_VERSION,
                clause,
                industry="CII (Singapore)",
                spl=spl,
                description=f"Tracks `{lookup}` for gaps against SG Cyber Act clause {clause}.",
                value="CSA enforcement on CII Owners is direct; missing evidence on CoP controls is a common inspection finding.",
                data_sources=f"KV Store `{lookup}`; CSA submission receipts (`index=grc sourcetype=csa:submission`); ES notables (`index=notable`).",
                evidence=f"Saved search `UC-{uid}` archived to `audit_evidence` with `csa_clause=\"{clause}\"`.",
                control_objective=f"Demonstrates CoP / Act compliance for {clause}.",
                evidence_artifact=f"Saved search UC-{uid}, CSA CII dashboard panel, and submission receipts.",
                assurance_rationale=f"Splunk supplies continuous evidence for {clause}; legal interpretation and Commissioner filings remain human-in-the-loop.",
                prerequisite=["UC-22.57.1"],
                authoritative_url="https://sso.agc.gov.sg/Act/CA2018",
            )
        )

    # --- SOCI (22.52.29–35) ---
    soci_entries = [
        ("22.52.29", "SOCI CIRMP natural hazards and business continuity exercise currency", "SOCI-CIRMP-r9.2", "soci_bc_exercise_lookup"),
        ("22.52.30", "SOCI Enhanced Cyber Security Obligations — vulnerability disclosure and remediation tracking", "SOCI-ECSO-vulnerability", "soci_ecso_vuln_lookup"),
        ("22.52.31", "SOCI OT zone-and-conduit segmentation — unauthorised cross-zone flow detection", "SOCI-cross-segmentation", "soci_ot_zones_lookup"),
        ("22.52.32", "SOCI OT asset inventory with criticality classification — completeness and freshness", "SOCI-cross-asset-inventory", "soci_ot_asset_inventory_lookup"),
        ("22.52.33", "SOCI Australian operational data residency and sovereignty attestation monitoring", "SOCI-cross-data-residency", "soci_data_residency_lookup"),
        ("22.52.34", "SOCI encryption of operational data in transit between OT zones", "SOCI-cross-encryption", "soci_ot_encryption_lookup"),
        ("22.52.35", "SOCI audit-evidence retention for CIRMP and cyber-incident reporting", "SOCI-cross-audit-evidence", "soci_audit_retention_lookup"),
    ]
    for uid, title, clause, lookup in soci_entries:
        spl = f'| inputlookup {lookup}\n| eval status = case(evidence_state!="current", "action_required", 1=1, "current")\n| where status="action_required"\n| table asset_id evidence_state status'
        m.append(
            _entry(
                uid,
                title,
                "soci",
                SOCI_VERSION,
                clause,
                spl=spl,
                description=f"Monitors `{lookup}` for SOCI clause {clause} evidence gaps.",
                value=f"CISC inspectors expect live evidence for {clause}, not point-in-time spreadsheets.",
                data_sources=f"KV Store `{lookup}`; OT flow telemetry (`index=ot`); CMDB (`snow:cmdb_ci`); `index=audit_evidence`.",
                evidence=f"Saved search `UC-{uid}` archived hourly to `audit_evidence` with `soci_clause=\"{clause}\"`.",
                control_objective=f"Surfaces gaps against {clause} across the in-scope SoNS / CIRMP estate.",
                evidence_artifact=f"Saved search UC-{uid} and SOCI compliance dashboard export.",
                assurance_rationale=f"Provides continuous monitoring evidence for {clause}; holistic 'reasonably practicable' test may require companion UCs.",
                prerequisite=["UC-22.52.1"],
                authoritative_url="https://www.legislation.gov.au/C2018A00029/latest/text",
            )
        )

    # --- CLC/TS 50701 (22.55.29–33) ---
    clc_entries = [
        ("22.55.29", "CLC/TS 50701 maintenance cybersecurity — depot and on-board system hardening evidence", "CLC-TS-50701-c12-1"),
        ("22.55.30", "CLC/TS 50701 maintenance-laptop cybersecurity baseline compliance", "CLC-TS-50701-c12-2"),
        ("22.55.31", "CLC/TS 50701 decommissioning cybersecurity — end-of-life data and component sanitisation", "CLC-TS-50701-c12-3"),
        ("22.55.32", "CLC/TS 50701 Annex A — threat-actor coverage mapped to detection use cases", "CLC-TS-50701-Annex-A"),
        ("22.55.33", "CLC/TS 50701 Annex D — rail zone-and-conduit reference architecture conformance", "CLC-TS-50701-Annex-D"),
    ]
    for uid, title, clause in clc_entries:
        lookup = f"rail50701_{clause.split('-')[-1].lower()}_lookup"
        spl = f'| inputlookup {lookup}\n| eval status = case(conformance!="pass", "action_required", 1=1, "current")\n| where status="action_required"\n| table system_id conformance status'
        m.append(
            _entry(
                uid,
                title,
                "clc-ts-50701",
                CLC_VERSION,
                clause,
                industry="Rail",
                spl=spl,
                description=f"Tracks rail cybersecurity conformance for {clause}.",
                value=f"Rail operators under CLC/TS 50701 must evidence {clause} during ENISA-aligned audits.",
                data_sources=f"KV Store `{lookup}`; rail OT IDS (`index=ot`); maintenance CMDB (`snow:cmdb_ci`).",
                evidence=f"Saved search `UC-{uid}` archived to `audit_evidence` with `rail_clause=\"{clause}\"`.",
                control_objective=f"Demonstrates monitoring evidence for {clause}.",
                evidence_artifact=f"Saved search UC-{uid} and rail cybersecurity dashboard.",
                assurance_rationale=f"Splunk evidences technical controls for {clause}; safety-case sign-off remains with the RAMS owner.",
                prerequisite=["UC-22.55.1"],
                authoritative_url="https://www.cenelec.eu/",
            )
        )

    # --- IEC 61511 (22.63.8–9) — read-only OT safety ---
    iec_entries = [
        ("22.63.8", "IEC 61511 SRS and SIL allocation traceability — safety-function register vs OT telemetry (read-only)", "IEC-61511-Cl-10"),
        ("22.63.9", "IEC 61511 operation and maintenance — procedure currency, training, and competence evidence", "IEC-61511-Cl-14"),
    ]
    for uid, title, clause in iec_entries:
        lookup = "iec61511_safety_register_lookup" if "Cl-10" in clause else "iec61511_om_competence_lookup"
        spl = f'| inputlookup {lookup}\n| eval status = case(record_state!="current", "action_required", 1=1, "current")\n| where status="action_required"\n| table safety_function_id record_state status'
        m.append(
            _entry(
                uid,
                title,
                "iec-61511",
                IEC61511_VERSION,
                clause,
                industry="Process Safety / OT",
                owner="Head of OT Security",
                spl=spl,
                description=f"Read-only surveillance of `{lookup}` for {clause}; no SIS write-back.",
                value=f"SIS cybersecurity overlays require evidence that {clause} is maintained without compromising safety independence.",
                data_sources=f"KV Store `{lookup}`; SIS engineering repository (read-only export); LMS training records (`index=hr sourcetype=lms:completion`).",
                evidence=f"Saved search `UC-{uid}` archived to `audit_evidence` with `iec61511_clause=\"{clause}\"`.",
                control_objective=f"Evidences {clause} via read-only monitoring; does not modify SIS logic.",
                evidence_artifact=f"Saved search UC-{uid} and safety-case evidence binder export.",
                assurance_rationale=f"Partial assurance: Splunk monitors evidence freshness for {clause}; SIL verification remains with the functional-safety engineer.",
                prerequisite=["UC-22.63.1"],
                authoritative_url="https://webstore.iec.ch/publication/5519",
                exclusions="Read-only acquisition only. No automated changes to SIS logic, setpoints, or safety interlocks.",
            )
        )

    # --- Singletons ---
    singletons = [
        (
            "22.53.29",
            "AWIA RRA methodology attestation — J100-21 / AWWA M19 / VSAT-Web usage evidence",
            "awia",
            AWIA_VERSION,
            "AWIA-EPA-vsat-j100",
            "awia_rra_methodology_lookup",
            "https://www.epa.gov/waterresilience/awia-section-2013",
        ),
        (
            "22.62.9",
            "CERT-In Directions KYC log retention — 5-year body-corporate retention evidence",
            "cert-in",
            CERTIN_VERSION,
            "CERT-In-Dir-7",
            "certin_kyc_retention_lookup",
            "https://www.cert-in.org.in/",
        ),
        (
            "22.61.13",
            "CN CSL Art.21(3) universal log retention — ≥6 months network and security log evidence",
            "cn-csl",
            CNSL_VERSION,
            "CSL-Art-21-3",
            "csl_log_retention_lookup",
            "https://www.cac.gov.cn/",
        ),
        (
            "22.58.9",
            "France LPM Décret 2015-351 — ANSSI 20-rules applicability to SIIV attestation",
            "fr-lpm",
            FRLPM_VERSION,
            "FR-Decret-2015-351",
            "fr_lpm_siiv_rules_lookup",
            "https://www.ssi.gouv.fr/",
        ),
        (
            "22.59.18",
            "IMO MSC.428(98) stakeholder and supply-chain cybersecurity considerations evidence",
            "imo-msc-428-98",
            IMO_VERSION,
            "IMO-MSC-FAL-Circ-3-s3-2",
            "imo_supply_chain_lookup",
            "https://www.imo.org/",
        ),
    ]
    for uid, title, reg, ver, clause, lookup, url in singletons:
        spl = f'| inputlookup {lookup}\n| eval status = case(evidence_state!="current", "action_required", 1=1, "current")\n| where status="action_required"\n| table entity_id evidence_state status'
        m.append(
            _entry(
                uid,
                title,
                reg,
                ver,
                clause,
                spl=spl,
                description=f"Monitors `{lookup}` for compliance with {clause}.",
                value=f"Regulators expect demonstrable, retained evidence for {clause}, not policy statements alone.",
                data_sources=f"KV Store `{lookup}`; GRC evidence index (`index=grc`); Splunk `_audit` retention metrics.",
                evidence=f"Saved search `UC-{uid}` archived to `audit_evidence` with `clause=\"{clause}\"`.",
                control_objective=f"Demonstrates ongoing evidence for {clause}.",
                evidence_artifact=f"Saved search UC-{uid} and compliance dashboard export.",
                assurance_rationale=f"Splunk operationalises observable elements of {clause}; legal filings remain outside scope.",
                authoritative_url=url,
            )
        )

    return m


def write_all(check_only: bool = False) -> int:
    entries = manifest()
    if len(entries) != 46:
        print(f"ERROR: expected 46 entries, got {len(entries)}", file=sys.stderr)
        return 1
    changed = 0
    for doc in entries:
        path = os.path.join(CONTENT, f"UC-{doc['id']}.json")
        new_bytes = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = fh.read()
            if old == new_bytes:
                continue
        if check_only:
            print(f"would write {path}")
            changed += 1
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_bytes)
        changed += 1
        print(f"wrote {path}")
    print(f"{'would write' if check_only else 'wrote'} {changed} files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_all(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
