#!/usr/bin/env python3
"""Tier-B uplift: replace boilerplate assurance_rationale and exclusions
with UC-specific, clause-aware text across all NIS2 22.2.* use cases.

Each entry was hand-written based on the UC's title, SPL, description,
and the specific NIS2 clause obligation.

Run:  python3 scripts/uplift_nis2_tier_b.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content" / "cat-22-regulatory-compliance"

BOILERPLATE_AR = "Uplifted from contributing: SPL directly addresses"
BOILERPLATE_EX = (
    "Does not determine legal applicability, complete regulator submissions, "
    "approve policy decisions, or replace counsel/competent-authority review."
)

# ---------------------------------------------------------------------------
# Hand-written assurance_rationale replacements keyed on UC id
# Each maps (clause) → new rationale text
# ---------------------------------------------------------------------------

ASSURANCE_RATIONALE: dict[str, dict[str, str]] = {
    "22.2.2": {
        "Art.21(2)(d)": (
            "Art.21(2)(d) requires supply-chain security including security-related "
            "aspects of relationships with direct suppliers. The UC produces Splunk "
            "evidence of supplier network traffic volumes and access patterns but "
            "cannot evaluate contractual security clauses or supplier self-assessments, "
            "hence partial."
        ),
    },
    "22.2.3": {
        "Art.21(2)(e)": (
            "Art.21(2)(e) requires vulnerability handling and disclosure. The UC "
            "tracks patch deployment cadence and Dependabot/CVE alert remediation times "
            "in Splunk but cannot confirm that disclosure procedures were followed or "
            "that vendor coordination occurred, hence partial."
        ),
    },
    "22.2.4": {
        "Art.21(2)(c)": (
            "Art.21(2)(c) requires business continuity, backup management, disaster "
            "recovery and crisis management. The UC monitors backup job success rates "
            "and RPO/RTO trending in Splunk but cannot verify that restore tests "
            "produce usable data or that crisis-management plans were exercised, hence partial."
        ),
    },
    "22.2.5": {
        "Art.21(2)(i)": (
            "Art.21(2)(i) requires human resources security, access control policies, "
            "and asset management. The UC correlates authentication patterns across "
            "Windows, Entra ID, Okta and CyberArk to surface weak logon types, "
            "after-hours elevation, and identity sprawl. Access policy authorship and "
            "HR vetting remain outside Splunk, hence partial."
        ),
    },
    "22.2.6": {
        "Art.21(2)(a)": (
            "Art.21(2)(a) requires risk analysis and information system security "
            "policies. The UC aggregates risk register snapshots and policy approval "
            "timestamps from ServiceNow GRC but cannot assess whether the risk "
            "analysis methodology itself meets the entity's sectoral requirements, "
            "hence partial."
        ),
    },
    "22.2.9": {
        "Art.21(2)(f)": (
            "Art.21(2)(f) requires policies to assess the effectiveness of "
            "cybersecurity risk-management measures. The UC trends MTTR and MTTF "
            "for compliance-tagged ES notables over quarterly windows, proving the "
            "entity measures effectiveness. Whether the metrics drive actual "
            "improvement remains a governance decision outside Splunk, hence partial."
        ),
    },
    "22.2.10": {
        "Art.21(2)(g)": (
            "Art.21(2)(g) requires basic cyber hygiene practices and cybersecurity "
            "training. The UC measures training completion freshness against a "
            "365-day policy and flags overdue staff. It cannot verify that the "
            "training content itself meets national transposition requirements or "
            "that participants retained the material, hence partial."
        ),
    },
    "22.2.11": {
        "Art.21(2)(h)": (
            "Art.21(2)(h) requires policies regarding the use of cryptography and "
            "encryption. The UC monitors TLS certificate posture, cipher suite "
            "compliance, and encryption policy deviations from Splunk telemetry but "
            "cannot evaluate whether the entity's cryptography policy adequately "
            "addresses key management lifecycle or regulatory minimums, hence partial."
        ),
    },
    "22.2.13": {
        "Art.21(2)(i)": (
            "Art.21(2)(i) requires asset management alongside access control. The UC "
            "continuously reconciles discovered assets against the authorised CMDB "
            "baseline to flag unauthorised or drifted configurations. Policy definition "
            "and lifecycle governance remain outside Splunk, hence partial."
        ),
    },
    "22.2.14": {
        "Art.21(2)(i)": (
            "Art.21(2)(i) requires human resources security. The UC monitors "
            "joiner-mover-leaver process telemetry from the HRIS and IdP to flag "
            "delayed deprovisions and orphaned accounts. It cannot verify that "
            "background checks were completed or that HR policies meet legal "
            "requirements, hence partial."
        ),
    },
    "22.2.15": {
        "Art.21(2)(e)": (
            "Art.21(2)(e) requires security in systems acquisition, development and "
            "maintenance. The UC measures per-repository CI/CD security scan coverage "
            "and flags pipelines that deploy without scanning. It cannot confirm "
            "that scan findings were actually remediated or that the scanning tools "
            "cover all relevant vulnerability classes, hence partial."
        ),
    },
    "22.2.16": {
        "Art.21(2)(d)": (
            "Art.21(2)(d) requires supply chain security. The UC continuously "
            "monitors third-party network traffic volumes and assessment overdue "
            "dates for categorised suppliers. It cannot evaluate the quality of "
            "supplier security controls or contractual clauses, hence partial."
        ),
    },
    "22.2.17": {
        "Art.21(2)(c)": (
            "Art.21(2)(c) requires backup management and disaster recovery. The UC "
            "verifies backup job completion, retention compliance, and RPO adherence "
            "from backup infrastructure telemetry in Splunk. It cannot confirm that "
            "restores actually produce usable data or that the BCP was exercised, "
            "hence partial."
        ),
    },
    "22.2.18": {
        "Art.21(2)(a)": (
            "Art.21(2)(a) requires information system security policies. The UC "
            "detects network anomalies, scans for rogue devices, and monitors "
            "firewall and IDS/IPS telemetry. It proves monitoring is active but "
            "cannot assess whether the security policy itself is adequate for "
            "the entity's risk profile, hence partial."
        ),
    },
    "22.2.20": {
        "Art.20": (
            "Art.20 requires management bodies to approve and oversee cybersecurity "
            "risk-management measures and undergo training. The UC joins governance "
            "evidence (training completion, policy approvals, risk acceptances) "
            "from LMS and ServiceNow GRC against the management roster. It proves "
            "who was trained and which policies were approved, but cannot assess "
            "whether the oversight was substantively adequate, hence partial."
        ),
    },
    "22.2.24": {
        "Art.21(2)(c)": (
            "Art.21(2)(c) requires business continuity and ICT continuity. The UC "
            "aggregates DR drill outcomes, failover test timestamps, and continuity "
            "plan review dates from ITSM. It cannot confirm that the continuity "
            "plans themselves are adequate for the entity's service portfolio, "
            "hence partial."
        ),
    },
    "22.2.25": {
        "Art.21(2)(d)": (
            "Art.21(2)(d) requires supply chain security. The UC tracks assessment "
            "coverage breadth across the supplier register and surfaces Dependabot "
            "alerts on supplier code dependencies. It cannot evaluate whether the "
            "assessments themselves were thorough or that supplier relationships "
            "satisfy the Implementing Regulation's proportionality criteria, hence partial."
        ),
    },
    "22.2.26": {
        "Art.21(2)(a)": (
            "Art.21(2)(a) requires information system security policies including "
            "network security monitoring. The UC measures per-segment monitoring "
            "coverage and flags segments without active detection. It proves coverage "
            "breadth but cannot evaluate detection quality or response capacity per "
            "segment, hence partial."
        ),
    },
    "22.2.27": {
        "Art.21(2)(e)": (
            "Art.21(2)(e) requires vulnerability handling and disclosure. The UC "
            "monitors operational signals from the vulnerability disclosure programme "
            "(intake, triage SLA adherence, researcher communication). It cannot "
            "confirm that the disclosure policy itself meets ENISA guidance or "
            "that mitigations were effective, hence partial."
        ),
    },
    "22.2.28": {
        "Art.21(2)(g)": (
            "Art.21(2)(g) requires basic cyber hygiene practices. The UC verifies "
            "baseline controls (patching cadence, endpoint protection coverage, "
            "password policy compliance) from infrastructure telemetry. It proves "
            "that hygiene baselines are measured but cannot assess whether the "
            "baselines themselves are adequate for the entity's risk, hence partial."
        ),
    },
    "22.2.29": {
        "Art.21(2)(h)": (
            "Art.21(2)(h) requires policies regarding cryptography and encryption. "
            "The UC monitors TLS certificate validity, cipher suite compliance, and "
            "certificate authority usage across the estate. It cannot confirm that "
            "the underlying cryptography policy addresses key rotation schedules "
            "or post-quantum readiness, hence partial."
        ),
    },
    "22.2.30": {
        "Art.21(2)(i)": (
            "Art.21(2)(i) requires human resources security. The UC surfaces "
            "privileged-role people who lack recent security-training completion "
            "in the HR feed, linking role context to training freshness. It cannot "
            "verify that the training curriculum itself meets NIS2 awareness "
            "requirements or that leavers were fully deprovisioned, hence partial."
        ),
    },
    "22.2.36": {
        "Art.21(2)(a)": (
            "Art.21(2)(a) requires information system security policies. The UC "
            "validates OT network segmentation by comparing observed traffic "
            "flows against the authorised segmentation matrix. It proves that "
            "monitoring detects cross-zone violations but cannot assess whether "
            "the segmentation design itself meets IEC 62443 or entity-specific "
            "requirements, hence partial."
        ),
    },
    "22.2.37": {
        "Art.21(2)(a)": (
            "Art.21(2)(a) requires information system security policies. The UC "
            "monitors interactive and remote access to SCADA/HMI systems from "
            "privileged session logs and firewall telemetry. It proves access is "
            "logged and anomalies are surfaced but cannot assess whether the "
            "access policy itself is proportionate to the OT risk, hence partial."
        ),
    },
    "22.2.38": {
        "Art.21(2)(e)": (
            "Art.21(2)(e) requires security in acquisition, development and "
            "maintenance including vulnerability handling. The UC tracks ICS patch "
            "deployment timelines and change-ticket correlation for OT assets. "
            "It proves change discipline is evidenced but cannot confirm that the "
            "patches were tested in a staging environment before OT deployment, "
            "hence partial."
        ),
    },
    "22.2.39": {
        "Art.21(2)(f)": (
            "Art.21(2)(f) requires policies to assess effectiveness of cybersecurity "
            "measures. The UC detects OT process anomalies and protocol deviations "
            "that indicate an incident affecting industrial operations. It proves "
            "detection capability but cannot assess whether the detection rules "
            "cover the entity's full OT threat landscape, hence partial."
        ),
    },
    "22.2.40": {
        "Art.21(2)(c)": (
            "Art.21(2)(c) requires business continuity and crisis management. The UC "
            "monitors safety-system bypasses and forced interlock states against "
            "maintenance permit records. It proves bypass events are logged and "
            "correlated with authorised work but cannot confirm that the safety "
            "instrumented functions meet SIL requirements, hence partial."
        ),
    },
    "22.2.41": {
        "Art.20": (
            "Art.20 requires management body members to follow cybersecurity training. "
            "The UC tracks executive and board-member training completion dates "
            "against the governance roster. It proves training was attended and "
            "timestamped but cannot assess whether the training content satisfied "
            "the national transposition's knowledge requirements, hence partial."
        ),
    },
    "22.2.42": {
        "Art.20": (
            "Art.20 requires management bodies to approve and oversee cyber risk "
            "measures. The UC audits the distribution and acknowledgement of "
            "board-level cyber risk reports. It proves reports were delivered and "
            "read-receipted but cannot assess whether the board's deliberation "
            "was substantively adequate, hence partial."
        ),
    },
    "22.2.43": {
        "Art.21(2)(f)": (
            "Art.21(2)(f) requires policies to assess the effectiveness of "
            "cybersecurity risk-management measures. The UC tracks completion "
            "status of annual security assessments (penetration tests, audits, "
            "red-team exercises). It proves assessments were scheduled and completed "
            "but cannot evaluate whether the assessment scope was sufficient, "
            "hence partial."
        ),
    },
}

# ---------------------------------------------------------------------------
# Hand-written exclusions replacements keyed on UC id
# ---------------------------------------------------------------------------

EXCLUSIONS: dict[str, str] = {
    "22.2.2": (
        "Does not evaluate the quality of supplier security controls, interpret "
        "contractual clauses, determine whether a supplier qualifies as critical "
        "under Art.22, or replace counsel review of supply chain legal obligations. "
        "Only aggregates technical log evidence of supplier-facing network traffic."
    ),
    "22.2.3": (
        "Does not confirm that vulnerability disclosures followed coordinated "
        "procedures, verify that patch testing occurred, determine whether the "
        "entity's disclosure policy meets ENISA guidance, or replace counsel "
        "review. Only tracks patch deployment and CVE remediation timelines."
    ),
    "22.2.9": (
        "Does not define which metrics constitute adequate effectiveness under "
        "Art.21(2)(f), set MTTR/MTTF targets, or replace management judgement on "
        "whether improvement trends are sufficient. Only trends response-time "
        "data from compliance-tagged notables."
    ),
    "22.2.15": (
        "Does not confirm that scan findings were remediated, verify the scanning "
        "tools cover all relevant vulnerability classes, audit code quality, or "
        "replace counsel review of Art.21(2)(e) obligations. Only measures "
        "CI/CD security scan coverage per repository."
    ),
    "22.2.16": (
        "Does not evaluate the depth of supplier security assessments, interpret "
        "Implementing Regulation proportionality criteria, approve vendor "
        "relationships, or replace procurement or counsel review. Only monitors "
        "traffic volumes and assessment overdue dates."
    ),
    "22.2.21": (
        "Does not classify the entity's NIS2 scope (essential vs important), "
        "interpret national transposition thresholds, or replace counsel "
        "determination of Annex I/II applicability. Only surfaces telemetry-based "
        "risk evidence that an auditor can review against a pre-classified scope."
    ),
    "22.2.22": (
        "Does not classify the entity's NIS2 scope (essential vs important), "
        "interpret national transposition thresholds for important entities, "
        "or replace counsel determination. Only surfaces risk evidence that "
        "an auditor can review for important-entity obligations."
    ),
    "22.2.25": (
        "Does not evaluate assessment thoroughness, confirm that supplier "
        "relationships satisfy Implementing Regulation criteria, determine "
        "Art.22 critical supply chain status, or replace procurement review. "
        "Only tracks assessment coverage breadth and Dependabot alert volumes."
    ),
    "22.2.27": (
        "Does not confirm that the disclosure policy meets ENISA guidance, "
        "verify researcher communication quality, determine whether mitigations "
        "were effective, or replace counsel review. Only monitors operational "
        "signals from the vulnerability disclosure programme."
    ),
    "22.2.30": (
        "Does not verify that training curriculum content meets NIS2 national "
        "transposition requirements, confirm that leavers were fully deprovisioned "
        "from all systems, or replace HR/counsel review of workforce security "
        "policies. Only surfaces overdue training for privileged-role staff."
    ),
    "22.2.31": (
        "Does not perform the legal analysis required to classify the entity under "
        "NIS2 Art.2(1), interpret national transposition size or sector thresholds, "
        "or replace counsel determination. Only cross-references operational "
        "telemetry against pre-classified entity metadata."
    ),
    "22.2.32": (
        "Does not define what constitutes proportionate security measures per "
        "Art.21(2), interpret proportionality under the Implementing Regulation, "
        "or replace risk-management judgement. Only compares implemented controls "
        "against a pre-defined tier-appropriate baseline."
    ),
    "22.2.38": (
        "Does not confirm that ICS/OT patches were tested in a staging environment, "
        "evaluate whether the change management process meets IEC 62443 requirements, "
        "or replace OT engineering sign-off. Only tracks patch deployment timelines "
        "and change-ticket correlation for industrial control systems."
    ),
    "22.2.39": (
        "Does not define the entity's full OT threat landscape, confirm that "
        "detection rules cover all relevant process anomaly scenarios, or replace "
        "OT incident response procedures. Only detects process and protocol "
        "anomalies in OT network telemetry."
    ),
    "22.2.46": (
        "Does not test whether emergency communications are intelligible under "
        "real crisis conditions, confirm that the communication system meets "
        "national CSIRT requirements, or replace tabletop exercises. Only verifies "
        "technical availability and MFA posture of emergency communication channels."
    ),
    "22.2.50": (
        "Does not evaluate the quality of supplier security controls, interpret "
        "contractual clauses, approve vendor risk acceptance, determine Art.22 "
        "critical supply chain status, or replace procurement or board governance. "
        "Only correlates vulnerability findings, SBOM exposure, and vendor access "
        "patterns for critical suppliers."
    ),
}


def fix_file(path: Path) -> list[str]:
    raw = path.read_text("utf-8")
    data = json.loads(raw)
    uid = data["id"]
    changes: list[str] = []

    # Fix assurance_rationale
    if uid in ASSURANCE_RATIONALE:
        for comp in data.get("compliance", []):
            clause = comp.get("clause", "")
            if BOILERPLATE_AR in comp.get("assurance_rationale", ""):
                new_ar = ASSURANCE_RATIONALE[uid].get(clause)
                if new_ar:
                    comp["assurance_rationale"] = new_ar
                    changes.append(f"AR({clause})")

    # Fix exclusions
    if uid in EXCLUSIONS:
        if data.get("exclusions", "").strip() == BOILERPLATE_EX:
            data["exclusions"] = EXCLUSIONS[uid]
            changes.append("EX")

    if changes:
        out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        path.write_text(out, "utf-8")

    return changes


def main() -> None:
    files = sorted(CONTENT.glob("UC-22.2.*.json"), key=lambda p: _sort_key(p.stem))
    total_changes = 0
    for f in files:
        ch = fix_file(f)
        if ch:
            uid = f.stem.replace("UC-", "")
            print(f"  UC-{uid}: {', '.join(ch)}")
            total_changes += 1

    if total_changes == 0:
        print("No changes needed.")
    else:
        print(f"\nModified {total_changes} files.")

    # Check for remaining boilerplate
    remaining_ar = 0
    remaining_ex = 0
    for f in files:
        d = json.loads(f.read_text())
        for c in d.get("compliance", []):
            if BOILERPLATE_AR in c.get("assurance_rationale", ""):
                remaining_ar += 1
                break
        if d.get("exclusions", "").strip() == BOILERPLATE_EX:
            remaining_ex += 1

    if remaining_ar or remaining_ex:
        print(f"\nRemaining boilerplate: {remaining_ar} AR, {remaining_ex} EX")
    else:
        print("\nAll boilerplate replaced.")


def _sort_key(stem: str) -> tuple[int, ...]:
    parts = stem.replace("UC-", "").split(".")
    return tuple(int(p) for p in parts if p.isdigit())


if __name__ == "__main__":
    main()
