#!/usr/bin/env python3
"""Regenerate the ``"22": { ... }`` block in ``non-technical-view.js``.

Phase 4.3 of the compliance gold-standard plan: elevate the cat-22
(regulatory compliance) non-technical view with plain-language
``whatItIs`` / ``whoItAffects`` / ``splunkValue`` narrative plus
``primer`` and ``evidencePack`` cross-references into
``docs/regulatory-primer.md`` and ``docs/evidence-packs/*.md``.

Why a generator rather than hand-edited JS:

* 40 areas × 3-5 new fields is a lot of prose and auditing it by hand
  every time would cause drift between the regulatory primer and the
  dashboard copy.  Keeping a single authoritative Python dictionary
  means anyone editing the narrative sees every area side by side.
* The generator emits byte-identical output on re-runs, so the CI
  determinism guard (``--check``) stays truthful.  That mirrors the
  pattern already established by ``generate_evidence_packs.py``,
  ``generate_api_surface.py``, ``generate_phase3_2_cross_cutting.py``,
  and ``generate_phase3_3_derivatives.py``.
* The content intentionally stays zero-opinion: every ``primer`` and
  ``evidencePack`` link points to a file that already exists in the
  repo, and every ``ucs[].id`` references a real UC (cross-checked by
  ``scripts/audit_non_technical_sync.py`` after regeneration).

Usage::

    python3 scripts/regenerate_cat22_ntv.py           # rewrite the file
    python3 scripts/regenerate_cat22_ntv.py --check   # CI drift guard
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
JS_PATH = REPO_ROOT / "non-technical-view.js"

# The block delimiters we rewrite.  We rely on the surrounding structure
# being stable, which it has been since Phase 2.2.
BLOCK_START = '  "22": {\n'
NEXT_BLOCK_START = '  "23": {\n'


# ---------------------------------------------------------------------------
# Content authoring
# ---------------------------------------------------------------------------

# Each entry represents one ``areas[]`` element.  Fields:
#   name:        short plain-language area name (existing)
#   description: 1-2 sentences describing what we monitor (existing)
#   whatItIs:    plain-language explanation of the regulation / family
#   whoItAffects: who has to comply (size, sector, jurisdiction)
#   splunkValue: what the catalogue delivers specifically for this area
#   primer:      relative path into docs/regulatory-primer.md (+#anchor)
#   evidencePack: relative path into docs/evidence-packs/<slug>.md
#   ucs:         list of (id, why) tuples — exactly the same shape as
#                the existing non-technical-view.js

_OUTCOMES: list[str] = [
    "We monitor compliance with 30+ regulations across GDPR, HIPAA, PCI DSS, NERC CIP, NIST, SOX, DORA, NIS2, and regional frameworks worldwide.",
    "We automatically collect and organise evidence for auditors, assessors, and regulators — saving weeks of manual preparation.",
    "We spot compliance gaps, missed deadlines, and control failures before regulators or auditors find them.",
    "We cover sector-specific requirements for healthcare, finance, energy, critical infrastructure, and government — each with regulation-specific monitoring.",
]

# Primer anchor helpers — these match the GitHub-rendered anchors for
# headers in ``docs/regulatory-primer.md``.  If the primer headers are
# renamed, refresh these values in lockstep.
_PRIMER = "docs/regulatory-primer.md"


def _p(anchor: str) -> str:
    return f"{_PRIMER}#{anchor}"


def _ev(slug: str) -> str:
    return f"docs/evidence-packs/{slug}.md"


_AREAS: list[dict[str, Any]] = [
    # ----- Tier-1 regulation areas (full 5 fields) -----
    {
        "name": "GDPR compliance",
        "description": "EU General Data Protection Regulation — personal data detection, breach notification, data subject rights, processor oversight, DPIA tracking, consent enforcement, international transfers, and privacy-by-design evidence across all key GDPR articles.",
        "whatItIs": "The EU privacy law that protects personal data about anyone in Europe. It sets rules for how companies collect, store, share, and delete that data — and gives people the right to see, correct, or remove what is held about them.",
        "whoItAffects": "Any organisation that holds or processes personal data about people in the EU or EEA, no matter where the organisation itself is based. Small businesses are covered too, not just large enterprises.",
        "splunkValue": "We watch where personal data lives, detect breaches that trigger the 72-hour notification clock, capture evidence that access / deletion / portability requests were handled on time, and flag cross-border transfers that lack a current legal agreement — so an EU DPA can be answered with live data, not PowerPoint.",
        "primer": _p("41-gdpr--general-data-protection-regulation-eueea--t1"),
        "evidencePack": _ev("gdpr"),
        "ucs": [
            ("22.1.7", "We monitor encryption and pseudonymisation of systems processing personal data — Article 32 requires appropriate security measures."),
            ("22.1.11", "We verify that personal data is actually deleted after an erasure request — catching incomplete right-to-be-forgotten execution."),
            ("22.1.30", "We detect unauthorised cloud services processing personal data — shadow IT that bypasses your GDPR controls."),
        ],
    },
    {
        "name": "UK GDPR",
        "description": "UK General Data Protection Regulation — the post-Brexit UK version of GDPR. Inherits the full GDPR clause set with UK-specific adjustments for ICO notification, national security exemptions, and UK Data Protection Act 2018 interaction.",
        "whatItIs": "The UK's own version of GDPR, kept almost identical to the EU rules but enforced by the UK Information Commissioner's Office (ICO) instead of European regulators. It applies whether you are in the UK or outside it.",
        "whoItAffects": "Any organisation holding personal data about people in the UK. After Brexit, UK operations handling UK residents' data rely on this law even if they previously only prepared for EU GDPR.",
        "splunkValue": "Because UK GDPR inherits GDPR's clauses, the same catalogue detections apply — we re-badge the evidence so an ICO audit sees UK-specific coverage, and we flag UK-only gaps such as ICO 72-hour breach notification routing.",
        "primer": _p("42-uk-gdpr--uk-general-data-protection-regulation-uk--t2--derivative"),
        "evidencePack": _ev("uk-gdpr"),
        "ucs": [
            ("22.1.7", "Inherited from GDPR Art.32 — encryption of personal data systems satisfies the UK ICO security obligation."),
            ("22.1.11", "Inherited deletion-verification coverage — UK residents have the same right to erasure as EU residents."),
            ("22.1.30", "Inherited shadow-IT detection — unsanctioned UK data flows surface even though the UK is now a third country for EU transfers."),
        ],
    },
    {
        "name": "CCPA privacy",
        "description": "California Consumer Privacy Act — consumer data requests, opt-out tracking, sensitive PI categories, automated decision profiling, dark pattern detection, and sale-of-data monitoring.",
        "whatItIs": "California's privacy law that gives residents the right to see what personal data is held about them, delete it, correct it, and opt out of its sale or sharing. CPRA extended CCPA with stricter rules for sensitive personal information.",
        "whoItAffects": "Businesses that sell to California residents and meet any of these: annual revenue over USD 25M, personal data on 100k+ Californians, or 50 %+ revenue from selling or sharing personal data.",
        "splunkValue": "We track consumer request response times, watch opt-out signal propagation across marketing and analytics, detect dark-pattern consent designs, and catch sales of data that happened without the opt-out being honoured.",
        "ucs": [
            ("22.4.1", "We track CCPA consumer data requests — access and deletion requests must be handled on time."),
            ("22.4.12", "We monitor automated decision-making systems for bias and profiling — consumers have the right to opt out."),
            ("22.4.20", "We detect dark pattern designs in consent flows — deceptive UI that undermines genuine consumer choice."),
        ],
    },
    {
        "name": "NIS2 compliance",
        "description": "EU NIS2 directive — incident reporting timelines, supply chain risk, encryption monitoring, MFA enforcement, training tracking, OT-specific requirements, and board-level governance evidence.",
        "whatItIs": "The EU's updated cybersecurity law for important and essential service providers. It raises the bar on risk management, incident reporting, and personal board-member accountability for cyber governance.",
        "whoItAffects": "Operators in 18 sectors including energy, transport, banking, healthcare, water, digital infrastructure, public administration, and cloud / data-centre providers in the EU. Medium and large entities are automatically in scope.",
        "splunkValue": "We start the 24-hour early-warning clock the moment an incident is detected, capture supply-chain risk telemetry, evidence MFA and patching compliance, and produce board-level dashboards that demonstrate the Article 21 risk-management measures are working.",
        "primer": _p("410-nis2--network-and-information-security-directive-2-eu--t1"),
        "evidencePack": _ev("nis2"),
        "ucs": [
            ("22.2.1", "We track NIS2 incident detection and 24-hour early warning reporting obligations."),
            ("22.2.9", "We dashboard the effectiveness of all cybersecurity measures — MFA, patching, backups, training — as Article 21 requires."),
            ("22.2.35", "We validate OT network segmentation for essential entities — industrial control systems have specific NIS2 requirements."),
        ],
    },
    {
        "name": "ISO 27001:2022",
        "description": "International information-security management system standard. Annex A.5 / A.6 / A.7 / A.8 controls across organisational, people, physical, and technological domains, with continuous monitoring and improvement evidence.",
        "whatItIs": "The world's most widely recognised information-security management standard. An accredited auditor checks that the organisation has a working security programme — not just written policies — and awards certification every three years with yearly surveillance audits.",
        "whoItAffects": "Any organisation seeking a recognised ISMS certification to demonstrate security maturity to customers, regulators, and insurers. Common in technology, finance, healthcare, and public-sector procurement bids.",
        "splunkValue": "We give the ISMS owner live evidence that Annex A controls are operating — access reviews, log monitoring, backups, change management, supplier risk, and incident response — so surveillance audits become a data pull rather than a month-long evidence hunt.",
        "primer": _p("47-iso-270012022--information-security-management-system-global--t1"),
        "evidencePack": _ev("iso-27001"),
        "ucs": [
            ("22.6.1", "We monitor how well your ISO 27001 security controls are working across the board."),
            ("22.6.20", "We track Annex A.8 technological controls — privileged access, logging, network segmentation, and cryptography."),
            ("22.6.7", "We capture evidence for Annex A.5 organisational controls — policies, roles, asset ownership, and supplier agreements."),
        ],
    },
    {
        "name": "NIST CSF 2.0",
        "description": "NIST Cybersecurity Framework 2.0 — six functions (Govern, Identify, Protect, Detect, Respond, Recover) with the new Govern function covering oversight, strategy, and supply-chain risk.",
        "whatItIs": "A voluntary framework from the US National Institute of Standards and Technology that helps organisations describe and improve their cybersecurity posture. Version 2.0 added a dedicated Govern function and explicit cyber supply-chain risk management.",
        "whoItAffects": "Any organisation that needs a common language to describe cyber risk and capability maturity — widely adopted in the US private sector, by US federal agencies (alongside 800-53), and increasingly in EU and APAC procurement questionnaires.",
        "splunkValue": "We produce maturity scores for each CSF function and category, highlight the weakest sub-categories, and generate evidence packs the CISO can show the board — aligning cyber investment to the function that needs it most.",
        "primer": _p("48-nist-csf-20--cybersecurity-framework-us--global--t1"),
        "evidencePack": _ev("nist-csf"),
        "ucs": [
            ("22.7.1", "We dashboard your NIST CSF maturity across all six functions — including the new Govern function."),
            ("22.7.12", "We score GV.SC-* supply-chain categories — the single biggest v2.0 addition for third-party risk."),
            ("22.7.20", "We track Detect → Respond → Recover throughput so board reports show actual response muscle, not theoretical capability."),
        ],
    },
    {
        "name": "DORA digital resilience",
        "description": "EU Digital Operational Resilience Act for financial services — ICT risk management, incident reporting, third-party oversight, TLPT testing, concentration risk, information sharing, and exit strategies.",
        "whatItIs": "The EU's single rulebook for operational resilience in the financial sector. It consolidates scattered ICT requirements into one regulation covering risk management, incident reporting, testing, third-party oversight, and information-sharing arrangements.",
        "whoItAffects": "All EU regulated financial entities — banks, insurers, investment firms, crypto-asset service providers, payment institutions — plus the critical ICT third parties they depend on.",
        "splunkValue": "We classify incidents against DORA's seven major-incident criteria to trigger the 4-hour clock, track TLPT lifecycle evidence, measure concentration risk across cloud and critical ICT providers, and evidence the 2-hour major-incident initial report with timestamps.",
        "primer": _p("411-dora--digital-operational-resilience-act-eu--t1"),
        "evidencePack": _ev("dora"),
        "ucs": [
            ("22.3.11", "We automatically classify incidents as major using DORA's seven criteria — triggering the 4-hour reporting deadline."),
            ("22.3.25", "We track threat-led penetration testing (TLPT) lifecycle — from scoping through execution to remediation evidence."),
            ("22.3.21", "We monitor ICT concentration risk — how dependent you are on a single cloud or service provider."),
        ],
    },
    {
        "name": "MiFID II",
        "description": "EU Markets in Financial Instruments Directive II — algorithmic trading controls, best execution, market abuse detection, transaction reporting, and record-keeping for regulated trading activity.",
        "whatItIs": "The EU regulation governing investment firms, trading venues, and market infrastructure. It mandates detailed transaction reporting, best execution proof, market-abuse surveillance, and strict algorithmic-trading risk controls.",
        "whoItAffects": "Investment firms and trading venues authorised to operate in the EU, plus algorithmic traders and high-frequency-trading participants.",
        "splunkValue": "We monitor trade-reporting completeness and latency, detect circuit-breaker events and algo kill-switch activations, and correlate order-flow anomalies against market-abuse patterns — the evidence ESMA and national competent authorities ask for on inspection.",
        "ucs": [
            ("22.5.1", "We monitor MiFID II trade reporting completeness — missing reports mean regulatory fines."),
            ("22.5.10", "We detect algorithmic trading circuit breaker events — required controls to prevent market disruption."),
            ("22.5.14", "We watch pre-trade and post-trade controls firing rates so algo-trading risk remains within policy."),
        ],
    },
    {
        "name": "SOC 2",
        "description": "AICPA SOC 2 Trust Services Criteria across all CC categories plus availability, confidentiality, and processing integrity — continuous monitoring evidence for Type 1 and Type 2 attestation reports.",
        "whatItIs": "A US attestation report issued by an independent CPA that proves a service provider has designed (Type 1) and operated (Type 2) controls around security, availability, processing integrity, confidentiality, and privacy. It is the dominant vendor-assurance report in North America.",
        "whoItAffects": "Technology and service providers whose customers require SOC 2 — especially SaaS platforms, managed services, hosting providers, fintech, healthtech, and any B2B vendor handling customer data.",
        "splunkValue": "We collect Type 2 evidence continuously — access reviews, change management, backup tests, incident response, vulnerability SLAs — so the auditor field-work is a query instead of an interview, and the Type 2 reporting window is fully evidenced rather than sampled.",
        "primer": _p("46-soc-2--aicpa-trust-services-criteria-us--global--t1"),
        "evidencePack": _ev("soc-2"),
        "ucs": [
            ("22.8.1", "We continuously monitor SOC 2 trust service criteria — collecting evidence for auditors."),
            ("22.8.12", "We evidence SOC 2 logical access controls (CC6) — user provisioning, least privilege, and periodic review."),
            ("22.8.28", "We evidence Availability and Processing Integrity — backup testing, restore drills, and job-completion monitoring."),
        ],
    },
    {
        "name": "HIPAA healthcare",
        "description": "We monitor ePHI access, security safeguards, breach notification timelines, business associate oversight, and privacy rule compliance across Administrative, Technical, and Physical safeguards.",
        "whatItIs": "The US federal law protecting Protected Health Information (PHI). Its Security Rule sets Administrative, Physical, and Technical safeguards; its Breach Notification Rule runs a 60-day clock; its Privacy Rule limits who may use or disclose PHI.",
        "whoItAffects": "US healthcare providers, health plans, healthcare clearinghouses, and any Business Associate that handles PHI on their behalf (cloud hosters, billing firms, analytics vendors, MSPs).",
        "splunkValue": "We detect unauthorised patient-record access (the 'snooping' pattern auditors always ask about), prove ePHI encryption at rest and in transit, start the 60-day breach clock the moment discovery happens, and produce a business-associate evidence pack on demand.",
        "primer": _p("44-hipaa-security--health-insurance-portability-and-accountability-act-security-rule-us--t1"),
        "evidencePack": _ev("hipaa-security"),
        "ucs": [
            ("22.10.1", "We track risk analysis completion and risk management plans — the foundation of HIPAA Security Rule compliance."),
            ("22.10.33", "We detect when staff access patient records they are not treating — preventing snooping and privacy violations."),
            ("22.10.43", "We track breach discovery timelines — ensuring the 60-day notification requirement is met."),
        ],
    },
    {
        "name": "PCI DSS v4.0",
        "description": "All 12 PCI DSS v4.0 requirements — network security, secure configurations, data protection, encryption, malware defence, secure development, access control, authentication, physical security, logging, testing, and security policies.",
        "whatItIs": "The Payment Card Industry Data Security Standard — the global rulebook card brands impose on any merchant or service provider that stores, processes, or transmits cardholder data. v4.0 strengthens authentication, logging, and customised-approach flexibility.",
        "whoItAffects": "Any organisation that touches card data — from small merchants (SAQ) to tier-1 merchants and service providers (RoC with QSA). Non-compliance carries card-brand fines and acquirer-contract consequences.",
        "splunkValue": "We evidence each of the 12 requirements continuously, detect PANs that slipped into logs or non-CDE systems, watch critical file integrity on the cardholder environment, and pre-populate the RoC workbook with timestamped query evidence for every control.",
        "primer": _p("43-pci-dss-v40--payment-card-industry-data-security-standard-global--t1"),
        "evidencePack": _ev("pci-dss"),
        "ucs": [
            ("22.11.1", "We review network security controls around payment systems — so assessors see active governance of card data boundaries."),
            ("22.11.14", "We detect payment card numbers in logs — so stored data stays within retention and masking rules."),
            ("22.11.67", "We track all access to payment systems — reconstructing who did what for investigations and audits."),
        ],
    },
    {
        "name": "SOX / ITGC",
        "description": "Sarbanes-Oxley IT General Controls — logical access, change management, computer operations, financial system controls, and audit evidence for financial reporting integrity.",
        "whatItIs": "The US federal law that makes executives of publicly listed companies personally accountable for financial reporting accuracy. IT General Controls (ITGC) are the subset of controls over the IT systems that process financial data — access, change, and operations.",
        "whoItAffects": "US-listed public companies and their subsidiaries — and often private companies preparing for IPO. External auditors test ITGC every year under PCAOB guidance; deficiencies flow into management's Section 404 assertions.",
        "splunkValue": "We catch privileged access to financial systems without a ticket, detect emergency changes that bypassed approval, evidence user-access reviews and termination timeliness, and produce year-end ITGC evidence packs with sample-set timestamps auditors can independently walk through.",
        "primer": _p("45-sox-itgc--sarbanes-oxley-it-general-controls-us--t1"),
        "evidencePack": _ev("sox-itgc"),
        "ucs": [
            ("22.12.1", "We track user provisioning and deprovisioning for financial systems — access must match job responsibilities."),
            ("22.12.8", "We monitor emergency changes to production financial systems — each must be retrospectively approved."),
            ("22.12.22", "We verify financial close process controls — ensuring data integrity during period-end processing."),
        ],
    },
    {
        "name": "NERC CIP power grid",
        "description": "North American Electric Reliability Corporation Critical Infrastructure Protection — CIP-002 through CIP-014 covering BES Cyber Systems, electronic security perimeters, physical security, personnel, change management, incident reporting, and supply chain.",
        "whatItIs": "The mandatory cybersecurity standard for North America's bulk electric system. NERC CIP requires grid operators to identify critical cyber assets, wall them off behind Electronic Security Perimeters, and prove compliance to regional entities such as WECC, RFC, and SERC.",
        "whoItAffects": "Registered entities on the North American bulk electric system — generation operators, transmission owners, balancing authorities, reliability coordinators, and their contractors — in the US, Canada, and parts of Mexico.",
        "splunkValue": "We evidence BES Cyber System categorisation, monitor Electronic Security Perimeter traffic for unapproved protocols, log privileged-access sessions to EMS / SCADA, and prepare the CIP-008 incident response artefacts a regional audit team expects to see.",
        "ucs": [
            ("22.13.1", "We validate BES Cyber System categorisation — ensuring all critical assets are properly identified and classified."),
            ("22.13.15", "We monitor Electronic Security Perimeter boundaries — detecting unauthorised traffic traversal into control system networks."),
            ("22.13.38", "We track cyber security incident identification and classification — supporting CIP-008 reporting requirements."),
        ],
    },
    {
        "name": "NIST 800-53",
        "description": "Comprehensive NIST 800-53 Rev. 5 control monitoring across Audit, Access Control, Identification, System Integrity, Incident Response, Configuration, Assessment, Communications, Risk, and Contingency families.",
        "whatItIs": "The US federal catalogue of security and privacy controls. Version Rev.5 integrates privacy, supply-chain risk, and outcome-based language; it is the underpinning control set for FedRAMP authorisations and many state and sector programmes.",
        "whoItAffects": "US federal agencies, contractors supporting federal systems, FedRAMP cloud providers, and organisations that voluntarily adopt 800-53 as a gold-standard baseline (common in healthcare, finance, and critical infrastructure).",
        "splunkValue": "We evidence each control family — AU-2 logging completeness, AC-2 account lifecycle, SI-4 system monitoring, CM-6 configuration compliance, and more — with per-control dashboards and tstats-backed reports suitable for a FedRAMP ConMon package.",
        "primer": _p("49-nist-800-53-rev5--security-and-privacy-controls-us--t1"),
        "evidencePack": _ev("nist-800-53"),
        "ucs": [
            ("22.14.1", "We verify that all required events are being logged per AU-2 — the foundation of any audit programme."),
            ("22.14.16", "We monitor account management lifecycle — creation, modification, disabling, and removal per AC-2."),
            ("22.14.41", "We track system monitoring activities per SI-4 — detecting anomalies and unauthorized access attempts."),
        ],
    },
    {
        "name": "IEC 62443 industrial",
        "description": "Industrial automation and control system security — zones and conduits, security requirements from SR 1.1 through SR 5.4, component security, and IACS programme evidence.",
        "whatItIs": "The international standard family for industrial automation and control system security. It defines zones, conduits, security levels (SL-C/T), and detailed requirements for IACS programmes, system integrators, and component vendors.",
        "whoItAffects": "Owner-operators of industrial automation systems (manufacturing, utilities, oil and gas, pharma), system integrators building control systems, and component vendors supplying PLCs, HMIs, and historians.",
        "splunkValue": "We watch zone-boundary traffic for unapproved protocols, evidence human-user identification on HMIs and engineering workstations, and prepare the IACS programme artefacts that certifiers look for during SL-C assessments.",
        "ucs": [
            ("22.15.1", "We verify the security programme covers all industrial automation systems — not just IT-connected ones."),
            ("22.15.46", "We monitor zone boundary traffic — ensuring only approved protocols cross between security zones."),
            ("22.15.11", "We track human user identification and authentication on control systems — SR 1.1 requires this for all IACS users."),
        ],
    },
    {
        "name": "TSA Pipeline security",
        "description": "Post-Colonial Pipeline TSA Security Directives — network segmentation, access control, incident response, architecture reviews, and continuous monitoring for pipeline SCADA systems.",
        "whatItIs": "US Transportation Security Administration security directives, tightened after the 2021 Colonial Pipeline ransomware attack. They mandate IT/OT segmentation, access control, incident reporting, and annual cybersecurity architecture reviews for pipeline operators.",
        "whoItAffects": "Hazardous-liquid and natural-gas pipeline owner-operators in the United States designated as critical by TSA.",
        "splunkValue": "We prove IT/OT segmentation continuously, log privileged access to pipeline SCADA, evidence the 24-hour incident reporting timeline to CISA, and capture the architecture-review artefacts TSA inspectors verify on site.",
        "ucs": [
            ("22.16.1", "We validate IT/OT segmentation for pipeline control systems — the core TSA security directive requirement."),
            ("22.16.7", "We track OT incident detection and TSA reporting compliance — pipeline incidents must be reported promptly."),
            ("22.16.19", "We monitor pipeline SCADA system availability — ensuring continuous operation of critical control systems."),
        ],
    },
    {
        "name": "FDA Part 11 pharma",
        "description": "Electronic records and signatures for regulated pharmaceutical and medical device environments — audit trails, operator attribution, data integrity (ALCOA+), and GxP system validation.",
        "whatItIs": "US FDA 21 CFR Part 11 — the rules that let pharmaceutical, biotech, and medical-device companies use electronic records and signatures instead of paper. It demands comprehensive audit trails, operator attribution, and data-integrity guarantees under the ALCOA+ principles.",
        "whoItAffects": "Pharmaceutical, biotech, and medical-device manufacturers, CROs, and labs that run GxP systems (QMS, MES, LIMS, electronic batch records) under FDA jurisdiction — plus their equivalents in ICH-member regions.",
        "splunkValue": "We watch GxP system audit-trail completeness, detect disabled or bypassed audit trails, prove operator identity on every signed record, and flag ALCOA+ exceptions that will otherwise surface during an FDA 483 inspection.",
        "ucs": [
            ("22.17.1", "We verify audit trail completeness for all electronic records — every change must be captured with who, what, when."),
            ("22.17.11", "We track operator attribution for all system actions — Part 11 requires knowing exactly who performed each step."),
            ("22.17.16", "We monitor ALCOA+ data integrity principles — ensuring records are Attributable, Legible, Contemporaneous, Original, and Accurate."),
        ],
    },
    {
        "name": "API 1164 pipeline SCADA",
        "description": "American Petroleum Institute standard for SCADA security — RTU/HMI access, command authentication, field device integrity, network segmentation, and pipeline cybersecurity compliance.",
        "whatItIs": "The American Petroleum Institute's recommended-practice standard for pipeline SCADA cybersecurity. It complements TSA directives with detailed guidance on operator authentication, command authorisation, field-device integrity, and secure remote access.",
        "whoItAffects": "Oil and gas pipeline operators in North America that follow API's recommended practice, often alongside TSA security directives and NIST 800-82 industrial guidance.",
        "splunkValue": "We monitor operator authentication on HMIs and engineering workstations, log and justify control commands issued to the field, and detect firmware or configuration drift on RTUs and PLCs before it becomes a safety event.",
        "ucs": [
            ("22.18.1", "We monitor operator authentication on SCADA systems — only authorised personnel should control pipeline operations."),
            ("22.18.8", "We verify SCADA command authentication — critical control commands must be authorised before execution."),
            ("22.18.22", "We track firmware versions and configuration changes on field devices — detecting unauthorised modifications to PLCs and RTUs."),
        ],
    },
    {
        "name": "FISMA / FedRAMP",
        "description": "US Federal information security — continuous monitoring, authorisation to operate, POA&M management, PIV authentication, and federal incident reporting.",
        "whatItIs": "The Federal Information Security Modernization Act requires US federal agencies to run a continuous monitoring programme over their systems. FedRAMP extends that to cloud providers that want to sell to the federal government, with a standardised authorisation-to-operate.",
        "whoItAffects": "US federal agencies, their contractors, and cloud service providers pursuing FedRAMP authorisation (Low, Moderate, High impact levels). State agencies and higher education often adopt FISMA-aligned programmes as well.",
        "splunkValue": "We produce the ConMon deliverables — vulnerability metrics, POA&M ageing, inventory, configuration compliance, and incident metrics — in the format expected by the JAB and agency authorising officials, not a home-grown template.",
        "ucs": [
            ("22.19.1", "We track ISCM dashboard metrics — the continuous monitoring programme that underpins every federal ATO."),
            ("22.19.6", "We manage Plan of Action and Milestones — tracking known weaknesses and remediation commitments."),
            ("22.19.11", "We ensure federal incident reporting timelines are met — US-CERT notification within required timeframes."),
        ],
    },
    {
        "name": "CMMC defence",
        "description": "Cybersecurity Maturity Model Certification — protecting Controlled Unclassified Information in the defence supply chain with Level 2 and Level 3 practices.",
        "whatItIs": "The US Department of Defense cybersecurity maturity framework. It standardises how defence contractors protect Controlled Unclassified Information, with three maturity levels and third-party certification for Level 2 and Level 3.",
        "whoItAffects": "Every contractor and subcontractor in the DoD supply chain that handles Federal Contract Information (Level 1) or Controlled Unclassified Information (Levels 2 and 3) — roughly 300,000 organisations.",
        "splunkValue": "We evidence every CMMC practice continuously, map catalogue coverage to 800-171 controls, prove the self-assessment scoring is data-backed rather than attested, and pre-build the evidence package a C3PAO expects during Level 2 or Level 3 assessment.",
        "primer": _p("412-cmmc-20--cybersecurity-maturity-model-certification-us--t1"),
        "evidencePack": _ev("cmmc"),
        "ucs": [
            ("22.20.1", "We track CUI identification and marking — the starting point for protecting defence information."),
            ("22.20.11", "We monitor for advanced persistent threats targeting CUI environments — Level 3 enhanced detection."),
            ("22.20.16", "We collect self-assessment evidence and practice implementation scores — readiness for CMMC certification."),
        ],
    },
    {
        "name": "EU AI Act",
        "description": "High-risk AI system logging, traceability, human oversight, conformity assessment, and post-market monitoring under the EU Artificial Intelligence Act.",
        "whatItIs": "The EU's horizontal regulation on artificial intelligence. It bans unacceptable AI uses, imposes strict obligations on high-risk AI systems (healthcare, employment, credit, law enforcement, biometric, safety-critical), and adds general-purpose AI model transparency duties.",
        "whoItAffects": "Providers, deployers, importers, and distributors of AI systems placed on the EU market — including non-EU vendors whose AI is used in the EU. Obligations apply whether you built the model or merely integrate an upstream one.",
        "splunkValue": "We capture the Article 12 automatic logs, track model version and training-data lineage, evidence human-override events under Article 14, and maintain the post-market monitoring artefacts national market-surveillance authorities will request.",
        "ucs": [
            ("22.21.1", "We ensure high-risk AI systems maintain automatic recording of events — Article 12 requires comprehensive logging."),
            ("22.21.6", "We track model version history and training data lineage — traceability is mandatory for high-risk AI."),
            ("22.21.11", "We log human override actions on AI decisions — Article 14 requires meaningful human oversight capability."),
        ],
    },
    {
        "name": "PSD2 payments",
        "description": "EU Payment Services Directive — strong customer authentication, fraud monitoring, Open Banking API security, transaction integrity, and incident reporting to national authorities.",
        "whatItIs": "The EU's Payment Services Directive (2). It mandates Strong Customer Authentication for electronic payments, forces banks to open APIs to licensed third parties, and introduces a common major-incident reporting regime under the EBA guidelines.",
        "whoItAffects": "Banks, payment institutions, electronic money institutions, and licensed third-party providers (account information service providers and payment initiation service providers) operating in the EEA.",
        "splunkValue": "We watch SCA challenge rates by channel, detect fraud patterns in real time, monitor third-party API access to Open Banking interfaces, and evidence major-incident reporting to national competent authorities within EBA timelines.",
        "ucs": [
            ("22.22.1", "We monitor strong customer authentication challenge rates — ensuring SCA is applied where required."),
            ("22.22.7", "We detect transaction fraud patterns — real-time scoring and unusual payment behaviour."),
            ("22.22.13", "We track third-party provider API access — monitoring who uses your Open Banking interfaces and how."),
        ],
    },
    {
        "name": "EU Cyber Resilience Act",
        "description": "Product security requirements — security-by-default evidence, vulnerability handling, SBOM maintenance, incident reporting to ENISA, and secure development lifecycle.",
        "whatItIs": "The EU's horizontal regulation on products with digital elements. It imposes security-by-design, vulnerability handling, and 24-hour actively-exploited-vulnerability reporting obligations on manufacturers of connected products sold in the EU.",
        "whoItAffects": "Manufacturers, importers, and distributors of products with digital elements placed on the EU market — IoT device makers, software vendors, connected-appliance manufacturers, industrial-automation vendors.",
        "splunkValue": "We evidence secure-by-default configurations in production, maintain SBOMs and track dependency vulnerabilities, trigger the 24-hour exploited-vulnerability notification clock to ENISA, and record the coordinated vulnerability disclosure artefacts the CRA demands.",
        "ucs": [
            ("22.23.1", "We verify security-by-default configurations in products — the CRA requires products to ship secure out of the box."),
            ("22.23.6", "We track coordinated vulnerability disclosure — handling reported vulnerabilities within required timelines."),
            ("22.23.11", "We maintain and monitor Software Bills of Materials — tracking component vulnerabilities across your product portfolio."),
        ],
    },
    {
        "name": "eIDAS 2.0 trust services",
        "description": "EU electronic identification — qualified trust service audit trails, EU Digital Identity Wallet security, timestamping integrity, and certificate lifecycle management.",
        "whatItIs": "The EU regulation on electronic identification and trust services. Version 2.0 introduces the EU Digital Identity Wallet, expands qualified trust service categories, and tightens audit and supervision requirements on trust service providers.",
        "whoItAffects": "Qualified and non-qualified trust service providers (certificate authorities, timestamp authorities, eSignature and eSeal providers), EU Digital Identity Wallet providers, and relying parties that accept qualified credentials.",
        "splunkValue": "We audit certificate issuance and revocation, track wallet credential presentation integrity, verify qualified timestamp traceability, and evidence the supervision artefacts national supervisory bodies demand during conformity assessment.",
        "ucs": [
            ("22.24.1", "We audit certificate issuance and revocation — qualified trust services must maintain complete audit trails."),
            ("22.24.5", "We track EU Digital Identity Wallet issuance and credential presentations — monitoring the security of wallet operations."),
            ("22.24.9", "We verify qualified timestamp accuracy — timestamps must be traceable to coordinated universal time."),
        ],
    },
    {
        "name": "AML / CFT",
        "description": "Anti-money laundering and counter-terrorist financing — transaction monitoring, suspicious activity reports, KYC lifecycle, sanctions screening, PEP monitoring, and institution-wide risk assessment.",
        "whatItIs": "The global regime requiring financial and designated non-financial businesses to detect and report money laundering and terrorist financing. Delivered via FATF recommendations, EU AMLD directives, the US Bank Secrecy Act, and equivalent national rules.",
        "whoItAffects": "Banks, payment firms, e-money institutions, crypto-asset service providers, real estate, gambling, dealers in high-value goods, accountants, auditors, and legal professionals performing designated activities.",
        "splunkValue": "We detect structuring / smurfing, monitor SAR / STR filing timeliness, run real-time sanctions screening, surface PEP and adverse-media hits, and produce the institution-wide AML/CFT risk assessment evidence supervisors expect.",
        "ucs": [
            ("22.25.1", "We detect structuring and smurfing patterns — transactions deliberately kept below reporting thresholds."),
            ("22.25.8", "We track SAR filing timelines — suspicious activity reports must be filed within regulatory deadlines."),
            ("22.25.18", "We perform real-time sanctions screening — every transaction checked against current sanctions lists."),
        ],
    },
    {
        "name": "Norwegian regulations",
        "description": "Sikkerhetsloven national security, Kraftberedskapsforskriften power preparedness, Petroleumsforskriften oil and gas HSE, and Personopplysningsloven data protection specific to Norway.",
        "whatItIs": "Norway's national regulatory stack for security-classified information (Sikkerhetsloven), grid operator preparedness (NVE's Kraftberedskapsforskriften), offshore petroleum HSE (PSA's Petroleumsforskriften), and supplementary data protection (Personopplysningsloven on top of GDPR).",
        "whoItAffects": "Norwegian public administration, operators of classified systems, power system operators regulated by NVE, offshore oil and gas operators regulated by PSA / Havtil, and any controller processing Norwegian personal data.",
        "splunkValue": "We evidence classified-information system controls, track NVE preparedness metrics, capture HSE-critical OT telemetry from offshore platforms, and localise GDPR evidence so Datatilsynet inspections see Norwegian-specific coverage.",
        "ucs": [
            ("22.26.1", "We monitor classified information systems per Sikkerhetsloven — protecting national security information."),
            ("22.26.6", "We track power system availability and SCADA access — NVE requires preparedness evidence for grid operators."),
            ("22.26.11", "We monitor offshore platform control systems — PSA requires safety-critical system integrity monitoring."),
        ],
    },
    {
        "name": "UK NIS & FCA/PRA",
        "description": "UK NIS Regulations for essential services, FCA operational resilience, PRA outsourcing requirements, Senior Managers and Certification Regime, and Cyber Essentials certification.",
        "whatItIs": "The UK's post-Brexit regulatory stack: the UK NIS Regulations for operators of essential services, FCA and PRA operational-resilience rules for financial firms, the Senior Managers and Certification Regime, and the government-backed Cyber Essentials scheme.",
        "whoItAffects": "UK operators of essential services (energy, transport, health, water, digital infrastructure, digital services), FCA-authorised firms, PRA-supervised banks and insurers, and public-sector and supply-chain entities required to hold Cyber Essentials.",
        "splunkValue": "We evidence NIS security measures, track operational resilience impact tolerances and severe-but-plausible scenario testing, monitor material-outsourcing registers, and generate SM&CR personal-accountability artefacts.",
        "ucs": [
            ("22.27.1", "We monitor security measures for operators of essential services — UK NIS requires demonstrable security."),
            ("22.27.11", "We track important business service resilience — FCA requires firms to set and test impact tolerances."),
            ("22.27.19", "We monitor material outsourcing registers — PRA requires oversight of third-party dependencies."),
        ],
    },
    {
        "name": "German KRITIS / BSI",
        "description": "IT-Sicherheitsgesetz 2.0 critical infrastructure, BSI-KritisV sector thresholds, BSI IT-Grundschutz methodology, and BAIT/KAIT banking and insurance IT governance.",
        "whatItIs": "Germany's national cybersecurity stack: IT-SiG 2.0 obligations on critical-infrastructure operators, BSI-KritisV thresholds that determine who is KRITIS, BSI IT-Grundschutz as a baseline methodology, and BAIT / KAIT for banks and insurers supervised by BaFin.",
        "whoItAffects": "Operators of KRITIS sectors in Germany (energy, water, food, transport, health, finance, IT/telecoms, media, government, waste disposal), BaFin-regulated financial and insurance firms, and federal administration bodies using IT-Grundschutz.",
        "splunkValue": "We support BSI 24-hour incident reporting, evidence IT-Grundschutz module implementation, capture BAIT / KAIT IT-governance artefacts, and maintain the KRITIS asset inventory and sector-threshold calculations supervisors check.",
        "ucs": [
            ("22.28.1", "We track critical infrastructure operator reporting to BSI — incidents must be reported within 24 hours."),
            ("22.28.6", "We monitor KRITIS asset inventory and sector threshold compliance — operators must know what they protect."),
            ("22.28.11", "We track BSI IT-Grundschutz module compliance — the German standard for baseline security."),
        ],
    },
    {
        "name": "APAC data protection",
        "description": "Data protection across Asia-Pacific — China PIPL, Singapore PDPA, Japan APPI, Thailand PDPA, and Korea K-ISMS — covering cross-border transfers, breach notification, security safeguards, and consent management.",
        "whatItIs": "A patchwork of national data-protection laws across APAC: China PIPL (with strict cross-border transfer rules), Singapore PDPA (with a Do-Not-Call regime), Japan APPI (aligned with GDPR for adequacy), Thailand PDPA, and Korea's K-ISMS / PIPA regime.",
        "whoItAffects": "Any organisation that processes personal data about APAC residents — regional headquarters, multinational HR platforms, e-commerce, ad-tech, and cloud service providers operating in Asia-Pacific.",
        "splunkValue": "We localise breach-notification timelines per jurisdiction, enforce data-localisation under PIPL, monitor DPO appointment and reporting obligations, and cross-reference each APAC regime against the catalogue's GDPR-aligned detections.",
        "ucs": [
            ("22.29.1", "We enforce data localisation requirements under China PIPL Article 38 — personal data must stay within borders unless transfer conditions are met."),
            ("22.29.7", "We track breach notification timelines by jurisdiction — each APAC country has different requirements."),
            ("22.29.19", "We monitor DPO appointment compliance — several APAC laws require designated data protection officers."),
        ],
    },
    {
        "name": "APAC financial regulation",
        "description": "Financial sector technology risk across Asia-Pacific — MAS TRM Singapore, HKMA Hong Kong, RBI India, and APRA CPS 234 Australia.",
        "whatItIs": "APAC-specific financial-sector technology-risk regimes: MAS Technology Risk Management (Singapore), HKMA cybersecurity guidance (Hong Kong), RBI technology risk and cyber resilience (India), and APRA CPS 234 (Australia) on information security.",
        "whoItAffects": "Banks, insurers, asset managers, capital markets participants, and licensed fintechs supervised by MAS, HKMA, RBI, or APRA. Many rules reach into service providers of regulated firms as well.",
        "splunkValue": "We evidence technology-risk management controls, capture cybersecurity-assessment evidence on the timelines each regulator expects, and translate CPS 234 control-testing requirements into continuous-evidence dashboards.",
        "ucs": [
            ("22.30.1", "We monitor technology risk management per MAS guidelines — Singapore financial institutions must demonstrate IT governance."),
            ("22.30.8", "We track cybersecurity assessments per HKMA requirements — Hong Kong banks must regularly test their defences."),
            ("22.30.20", "We verify APRA CPS 234 information security capability — Australian financial institutions must maintain and test controls."),
        ],
    },
    {
        "name": "Australia & New Zealand",
        "description": "Privacy Act and Notifiable Data Breaches scheme, ASD Essential Eight maturity, APRA CPS 234 detail, and New Zealand ISM compliance.",
        "whatItIs": "The Australian privacy and cybersecurity stack — Privacy Act with Notifiable Data Breaches, ASD's Essential Eight maturity model, APRA CPS 234 information security for regulated entities — plus New Zealand's Information Security Manual for government agencies.",
        "whoItAffects": "Australian entities covered by the Privacy Act (with specific thresholds and exemptions), APRA-regulated banks / insurers / superannuation funds, federal agencies using Essential Eight, and New Zealand public-sector agencies covered by the ISM.",
        "splunkValue": "We assess Notifiable Data Breach thresholds, score Essential Eight maturity continuously, evidence CPS 234 information-security capability, and evidence the NZ ISM control baseline for agency accreditation.",
        "ucs": [
            ("22.31.1", "We assess notifiable data breaches under Australian law — determining if a breach is likely to cause serious harm."),
            ("22.31.6", "We monitor ASD Essential Eight controls — application control, patching, MFA, and admin privilege restriction."),
            ("22.31.14", "We track CPS 234 information security roles and control testing — Australian prudential requirements for financial institutions."),
        ],
    },
    {
        "name": "Americas regulations",
        "description": "LGPD Brazil data protection, FISMA/FedRAMP federal compliance, CMMC defence supply chain, and CJIS criminal justice information security.",
        "whatItIs": "A group of Americas-region regimes: Brazil's LGPD data-protection law, US federal FISMA / FedRAMP for government and cloud providers, CMMC for the DoD supply chain, and CJIS for criminal-justice information handled by law enforcement.",
        "whoItAffects": "Any organisation handling Brazilian personal data (LGPD), US federal or FedRAMP cloud services, US defence-supply-chain CUI (CMMC), or US criminal-justice information systems (CJIS).",
        "splunkValue": "We generate LGPD consent artefacts, populate ConMon packages for FedRAMP, prepare CMMC Level 2/3 practice evidence, and enforce CJIS advanced-authentication and audit-trail requirements.",
        "ucs": [
            ("22.32.1", "We track LGPD consent management — Brazilian data protection requires documented legal basis for processing."),
            ("22.32.9", "We monitor continuous monitoring metrics for FedRAMP — federal cloud authorisations require ongoing compliance evidence."),
            ("22.32.22", "We log access to criminal justice information — CJIS requires advanced authentication and complete audit trails."),
        ],
    },
    {
        "name": "Middle East cybersecurity",
        "description": "National cybersecurity frameworks — UAE NESA, Saudi Arabia SAMA and PDPL, Qatar QCB — covering critical infrastructure, financial services, and data protection requirements.",
        "whatItIs": "Middle East national cybersecurity and data-protection regimes: UAE NESA IAS (now NCSS) for national critical infrastructure, Saudi Arabia SAMA cybersecurity framework and SDAIA PDPL data protection, Qatar QCB information-security guidance, and similar regimes across the GCC.",
        "whoItAffects": "Critical-infrastructure operators and financial institutions in the UAE, Saudi Arabia, Qatar and neighbouring GCC states, plus any organisation processing personal data of residents of those jurisdictions under emerging national privacy laws.",
        "splunkValue": "We evidence NESA / NCSS control implementations, populate SAMA cybersecurity framework artefacts, enforce Saudi PDPL consent and localisation rules, and deliver the regulator-specific dashboards each national authority requires.",
        "ucs": [
            ("22.33.1", "We track UAE national cybersecurity standard compliance — NESA requires critical infrastructure operators to demonstrate security."),
            ("22.33.6", "We monitor SAMA cybersecurity framework compliance — Saudi financial institutions must meet specific security controls."),
            ("22.33.11", "We enforce Saudi PDPL data protection — personal data processing must comply with the new privacy law."),
        ],
    },
    {
        "name": "SWIFT CSP",
        "description": "SWIFT Customer Security Programme — secure zone protection, operator account control, system hardening, intrusion detection, and annual attestation evidence.",
        "whatItIs": "SWIFT's Customer Security Programme mandates baseline security controls for every user of the SWIFT network and requires an annual self-attestation (now independently assessed) of compliance with the Customer Security Controls Framework.",
        "whoItAffects": "Every organisation that connects to SWIFT — banks, central banks, broker-dealers, large corporates, and service bureaus — regardless of size. Non-compliance can be reported to counterparties and national regulators.",
        "splunkValue": "We evidence secure-zone segregation, operator-authentication strength, intrusion detection on SWIFT hosts, and produce the CSCF workbook with timestamped query evidence instead of screenshots for the annual KYC-SA attestation.",
        "ucs": [
            ("22.34.1", "We monitor the SWIFT secure zone environment — protecting the infrastructure that processes financial messages."),
            ("22.34.4", "We track operator authentication and session integrity — every SWIFT operator action must be attributable."),
            ("22.34.10", "We collect annual KYC-SA attestation evidence — demonstrating compliance to counterparties."),
        ],
    },
    {
        "name": "Compliance trending",
        "description": "We chart posture scores, audit closure, control tests, incident response time, and policy violations over time so you see direction, not a single snapshot.",
        "whatItIs": "A cross-framework trending layer. Instead of reporting a single snapshot score on audit day, we track how each framework's posture moves quarter over quarter, surfacing the controls whose trend is declining before they turn into findings.",
        "whoItAffects": "CISOs, privacy officers, compliance leaders, and audit committees that need to show direction of travel to boards, regulators, and insurers.",
        "splunkValue": "We ingest every control's pass/fail signal, chart compliance score curves by framework and business unit, and compute time-to-close for findings — so leadership reporting becomes evidence-based rather than narrative-based.",
        "ucs": [
            ("22.9.1", "We track how overall compliance scores move across major frameworks quarter by quarter — so leadership sees whether posture is improving."),
            ("22.9.2", "We watch open versus closed audit findings and how long fixes take — so backlogs and slow remediation surface before the next audit."),
            ("22.9.6", "We trend framework-specific compliance over time — so you see which regulation is improving and which needs attention."),
        ],
    },

    # ----- 15 cross-cutting control families (primer-only) -----
    {
        "name": "Evidence continuity & log integrity",
        "description": "We prove your audit logs are complete, unbroken, and tamper-evident — so auditors across GDPR, HIPAA, PCI, SOC 2, and SOX accept the same chain of custody.",
        "whatItIs": "The foundational control every framework relies on: the organisation must produce complete, contemporaneous, and tamper-evident audit logs. A gap or missing source destroys the evidentiary value of everything else.",
        "whoItAffects": "Every organisation with an audit obligation — privacy, financial, healthcare, or operational. In practice, any team that will ever have to defend a control decision to a third party.",
        "splunkValue": "We watch for collection gaps across sources, detect tampering of stored logs, confirm off-site replication, and produce the chain-of-custody timeline a forensic investigator or regulator expects.",
        "primer": _p("31-2235--evidence-continuity-and-log-integrity"),
        "ucs": [
            ("22.35.1", "We watch for gaps in security logging so you can prove to auditors that nothing slipped through the cracks."),
            ("22.35.2", "We detect if anyone tampers with stored audit logs — turning a silent integrity failure into actionable evidence within minutes."),
            ("22.35.3", "We monitor that every audit log is replicated to a second location — protecting against a single storage failure wiping your evidence trail."),
        ],
    },
    {
        "name": "Data subject rights fulfilment",
        "description": "We track every request from individuals asking to see, correct, or delete their personal data — and prove they were handled on time and completely.",
        "whatItIs": "The end-to-end lifecycle of privacy requests individuals can make under GDPR, UK GDPR, CCPA, LGPD, PDPA, and equivalent laws — access, rectification, erasure, portability, restriction, and objection — with deadlines that range from 30 to 45 days depending on jurisdiction.",
        "whoItAffects": "Any organisation processing personal data subject to a privacy law with data-subject rights provisions.",
        "splunkValue": "We time-stamp every request, measure response times against each legal deadline, verify that deletion actually reached backups and analytics stores, and produce the audit trail a DPA can follow end to end.",
        "primer": _p("32-2236--data-subject-rights-fulfillment"),
        "ucs": [
            ("22.36.1", "We track how long it takes to answer every data access or deletion request — so you never miss a regulatory deadline."),
            ("22.36.2", "We verify deletion requests actually removed data everywhere — not just from the main system while copies linger in backups or data warehouses."),
            ("22.36.3", "We monitor data export requests for portability — so individuals get their data in machine-readable form as the law requires."),
        ],
    },
    {
        "name": "Consent & lawful basis",
        "description": "We follow consent through every step — from the cookie banner to the backend — so you know marketing, analytics, and profiling only run on data that was lawfully collected.",
        "whatItIs": "The record of why the organisation is lawfully processing each piece of personal data — consent, contract, legal obligation, vital interest, public task, or legitimate interest — and evidence that downstream systems respect withdrawal and preference changes.",
        "whoItAffects": "Any organisation relying on consent or another lawful basis under GDPR, CCPA, LGPD, PDPA, or equivalent laws — especially marketing, analytics, ad-tech, and profiling teams.",
        "splunkValue": "We correlate consent-ledger state with downstream marketing and analytics activity, detect tags that fire against 'reject all', and flag marketing audiences built on expired or missing consent.",
        "primer": _p("33-2237--consent-lifecycle-and-lawful-basis"),
        "ucs": [
            ("22.37.1", "We watch when people withdraw consent and prove downstream systems stopped processing their data — the key signal regulators look for."),
            ("22.37.2", "We detect advertising or tracking scripts that ignore 'reject all' in the cookie banner — the single most common GDPR/CCPA enforcement trigger."),
            ("22.37.3", "We monitor marketing lists for expired or missing consent — so no one gets messaged without a lawful basis on file."),
        ],
    },
    {
        "name": "Cross-border transfers",
        "description": "We watch where personal data actually goes — so transfers to other countries only happen under the right legal framework and never by accident.",
        "whatItIs": "The rules that permit personal data to flow to other countries — GDPR Chapter V (SCCs, BCRs, adequacy decisions, derogations), UK IDTA, China PIPL Article 38, LGPD, and APPI equivalents. Accidental or undocumented transfers are a headline enforcement risk.",
        "whoItAffects": "Any organisation whose cloud, backups, analytics, or business partners result in personal data moving between jurisdictions — in practice almost every multinational.",
        "splunkValue": "We detect unauthorised copies of personal data to foreign cloud regions, verify SCC / DPA coverage per data flow, and flag email attachments or file shares that move personal data outside the approved jurisdiction.",
        "primer": _p("34-2238--cross-border-transfer-controls"),
        "ucs": [
            ("22.38.1", "We detect unauthorised copies of personal data to foreign cloud regions — a key red line under GDPR and national data-localisation rules."),
            ("22.38.2", "We verify every cross-border transfer has a current legal agreement (SCC or DPA) — no paperwork gaps when regulators ask."),
            ("22.38.3", "We monitor email attachments and file-share activity for personal data leaving the approved jurisdiction."),
        ],
    },
    {
        "name": "Incident notification timeliness",
        "description": "We turn the clock on every reportable incident and measure each regulatory deadline — 24h, 72h, 4h — across GDPR, HIPAA, NIS2, DORA, and national rules.",
        "whatItIs": "The cross-framework set of regulator-notification deadlines an organisation must hit after detecting a qualifying incident: GDPR 72h, NIS2 24h early warning, DORA 4h major-incident, HIPAA 60-day breach, plus many national overlays.",
        "whoItAffects": "Every organisation subject to at least one incident-reporting regime — in practice virtually every business in a regulated sector or with regulated personal data.",
        "splunkValue": "We start each clock automatically when the trigger condition is detected, alert before a deadline is about to miss, capture the submission trail to each regulator, and record the individual-notification evidence per breach.",
        "primer": _p("35-2239--incident-notification-timeliness"),
        "ucs": [
            ("22.39.1", "We alert when a breach notification deadline is about to be missed — so regulators hear about it on time and fines are avoided."),
            ("22.39.2", "We track every regulator communication through to acknowledgement — proving the notification actually landed with the right authority."),
            ("22.39.3", "We notify affected individuals within legal deadlines — and keep an audit trail of what each person was told."),
        ],
    },
    {
        "name": "Privileged access evidence",
        "description": "We watch every administrator, break-glass, and elevated-access session — and provide recordings, approvals, and timelines as evidence that access was justified.",
        "whatItIs": "The control expected by every framework of any maturity — privileged access is justified, just-in-time, logged, and reviewed. Failures here produce the most impactful audit findings in financial and healthcare audits.",
        "whoItAffects": "Any organisation with privileged technical users — so, everyone with technology infrastructure. The depth of control expected scales with the sensitivity of the data and the regulator.",
        "splunkValue": "We flag break-glass access with no ticket, ensure privileged sessions are recorded, detect shared or generic admin accounts, and feed the access-review process with live data instead of spreadsheet snapshots.",
        "primer": _p("36-2240--privileged-access-evidence"),
        "ucs": [
            ("22.40.1", "We flag break-glass admin access with no ticket or approval — the single most damaging audit finding in financial and healthcare audits."),
            ("22.40.2", "We track privileged-session recording completeness — so every admin action on regulated systems has a replayable video record."),
            ("22.40.3", "We detect shared or generic admin accounts still in active use — and enforce named accountability."),
        ],
    },
    {
        "name": "Encryption & key management",
        "description": "We prove every database, backup, and communication channel is encrypted — and that the keys protecting them are rotated, separated, and stored safely.",
        "whatItIs": "The technical baseline every framework demands: data at rest and in transit is encrypted with modern algorithms, keys are rotated inside their cryptoperiod, and key material is stored in an HSM or managed KMS with least-privilege access.",
        "whoItAffects": "Every organisation storing or transmitting sensitive data — in practice every modern business.",
        "splunkValue": "We detect systems storing sensitive data without encryption, watch key-age against rotation SLAs, detect weak cipher suites and expiring TLS certificates, and monitor KMS administrative events.",
        "primer": _p("37-2241--encryption-and-key-management-attestation"),
        "ucs": [
            ("22.41.1", "We detect systems storing sensitive data without encryption — turning a silent gap into a remediation ticket before audit day."),
            ("22.41.2", "We monitor key rotation so cryptographic keys never exceed their allowed lifetime — a key requirement under PCI DSS and NIST."),
            ("22.41.3", "We watch for weak cipher suites and expiring TLS certificates — the common source of unexpected service outages and audit exceptions."),
        ],
    },
    {
        "name": "Change management & baselines",
        "description": "We confirm every production change on regulated systems had a ticket, an approver, and a test record — and flag changes that drift away from the approved baseline.",
        "whatItIs": "The control every framework requires around changes to regulated systems — every change has a ticket, an approver, a test record, and a rollback plan. Baseline-drift monitoring is the complementary control ensuring the approved state persists.",
        "whoItAffects": "Any organisation where IT changes can affect regulated processes — ePHI systems, financial-reporting systems, card-data environments, OT systems, and more.",
        "splunkValue": "We correlate each production-change event with an approved ticket, detect emergency changes, flag configuration drift against the approved baseline, and produce the change-management sample-set auditors request.",
        "primer": _p("38-2242--change-management-and-configuration-baseline"),
        "ucs": [
            ("22.42.1", "We detect production changes that bypassed the change-management ticket — so unauthorised changes are investigated, not rubber-stamped."),
            ("22.42.2", "We alert on host configuration drift away from the approved security baseline — catching bad changes that compromise the control posture."),
        ],
    },
    {
        "name": "Vulnerability & patch SLAs",
        "description": "We measure how quickly critical vulnerabilities are fixed — by severity, by system, and by regulation — so SLAs are met, not just documented.",
        "whatItIs": "The control expected by every framework: each vulnerability has a severity-driven fix deadline, progress is tracked, and exceptions are documented. Missing a patch SLA is a very common audit finding.",
        "whoItAffects": "Any organisation running software that receives security updates — which is every business. Regulated sectors have explicit SLAs; unregulated ones still face breach-notification exposure.",
        "splunkValue": "We track every critical vulnerability against its patch deadline, highlight systems that repeatedly miss their SLA, and feed exception-management with age, severity, exploit maturity, and CISA KEV signals.",
        "primer": _p("39-2243--vulnerability-management-and-patch-slas"),
        "ucs": [
            ("22.43.1", "We track every critical vulnerability against its patch deadline — and escalate anything about to breach the regulatory SLA."),
            ("22.43.2", "We watch which systems repeatedly slip their patching deadline — so the cause is fixed, not just the individual finding."),
        ],
    },
    {
        "name": "Third-party & supply-chain risk",
        "description": "We extend your monitoring to vendors who process your data — so regulator questions about supplier oversight are answered with live evidence, not an annual questionnaire.",
        "whatItIs": "The control set around third parties who process regulated data — risk assessments, DPAs, sub-processor disclosure, SBOM tracking, and ongoing monitoring. Many regulators now audit supplier oversight before auditing internal controls.",
        "whoItAffects": "Any organisation that outsources technology or data processing — cloud, SaaS, MSP, BPO, payment processors, analytics vendors, marketing vendors, and supply-chain partners.",
        "splunkValue": "We track every vendor risk assessment to expiry, publish an accurate sub-processor list matching DPA disclosures, and surface SBOM findings across the vendor estate so supply-chain incidents can be acted on.",
        "primer": _p("310-2244--third-party-and-supply-chain-risk"),
        "ucs": [
            ("22.44.1", "We track every vendor risk assessment to expiry — so no supplier is ever processing your data on an outdated attestation."),
            ("22.44.2", "We publish the list of sub-processors actually used — matching what the law requires you to disclose to customers."),
            ("22.44.3", "We monitor Software-Bill-of-Materials findings across vendors — so software-supply-chain incidents are spotted and acted on."),
        ],
    },
    {
        "name": "Backup integrity & recovery testing",
        "description": "We prove backups work, are protected from ransomware, and can actually restore — by measuring drill success, not just backup job status.",
        "whatItIs": "The control DORA, HIPAA, NIS2, and ISO 27001 demand: backups are taken, protected from tampering (immutability / air gap), tested by actual restore drills, and measured against recovery-time and recovery-point objectives.",
        "whoItAffects": "Any organisation with data it cannot afford to lose — in practice every business.",
        "splunkValue": "We verify restore drills succeeded, alert when immutability or air-gap protection is disabled, and measure RTO achievement per critical system against the numbers the regulator asks for by name.",
        "primer": _p("311-2245--backup-integrity-and-recovery-testing"),
        "ucs": [
            ("22.45.1", "We verify that every restore drill succeeded — turning a 'we back up nightly' assumption into auditable evidence."),
            ("22.45.2", "We alert when immutability or air-gap protection is disabled on critical backups — the signal that ransomware preparation has begun."),
            ("22.45.3", "We track how long a critical system takes to recover in a drill — the RTO number that DORA, HIPAA and NIS2 ask for by name."),
        ],
    },
    {
        "name": "Training & awareness",
        "description": "We measure who has completed mandatory training, phishing simulation results, and role-based learning — so the human side of compliance is evidenced continuously.",
        "whatItIs": "The human-side control every framework embeds — mandatory training completion, phishing simulation performance, and role-based learning such as secure-coding, privileged-user, and developer-security training.",
        "whoItAffects": "Every organisation with employees or regular contractors — and any partner whose access demands training before handling regulated data.",
        "splunkValue": "We join training-platform completion data with HR source-of-truth, detect missed deadlines, measure phishing-click trends over time, and show whether awareness is actually improving or just being recorded.",
        "primer": _p("312-2246--training-and-awareness"),
        "ucs": [
            ("22.46.1", "We track which staff missed a mandatory training deadline — so HR and CISO can close gaps before the audit."),
            ("22.46.2", "We measure phishing simulation click rates over time — so you know whether awareness is really improving, not just that campaigns are running."),
        ],
    },
    {
        "name": "Control testing freshness",
        "description": "We measure when each compliance control was last tested — so your audit evidence stays fresh instead of quietly going stale.",
        "whatItIs": "The meta-control every mature framework expects: every control is tested on a defined cadence, test results are recorded, exceptions are investigated, and evidence never ages past the reviewer's tolerance.",
        "whoItAffects": "Any organisation operating a control-testing programme — internal audit, second-line assurance, or control-owner self-testing.",
        "splunkValue": "We track test results per control, alert when a cadence is breached, chart coverage against policy requirements, and produce the management-evidence report the audit committee expects each quarter.",
        "primer": _p("313-2247--control-testing-evidence-freshness"),
        "ucs": [
            ("22.47.1", "We alert when a control test is overdue — catching stale controls before the auditor does."),
            ("22.47.2", "We chart the cadence of control testing versus policy requirements — so leadership sees evidence quality at a glance."),
        ],
    },
    {
        "name": "Segregation of duties",
        "description": "We detect when the same person can request, approve, and release a sensitive change — the toxic combinations that SOX, PCI and healthcare audits look for.",
        "whatItIs": "The control SOX, PCI DSS, and major healthcare audits embed throughout — no single person can request, approve, and release a sensitive change. Toxic role combinations are analysed, monitored, and mitigated before auditors uncover them.",
        "whoItAffects": "Any organisation with financial systems, card-data environments, healthcare data, or high-privilege operations — very often including privileged IT roles.",
        "splunkValue": "We detect conflicting role assignments in financial and operational systems, monitor temporary elevations against business-need expiry, and evidence compensating controls when an SoD conflict cannot be resolved.",
        "primer": _p("314-2248--segregation-of-duties-enforcement"),
        "ucs": [
            ("22.48.1", "We flag people who have conflicting roles in financial systems — the combinations auditors write findings about."),
            ("22.48.2", "We monitor temporary role grants and ensure they are removed when the business need ends — instead of drifting into permanent access."),
        ],
    },
    {
        "name": "Retention & disposal",
        "description": "We confirm data is actually deleted when retention periods expire — and that litigation holds pause deletion exactly when required.",
        "whatItIs": "The control at the tail end of every data lifecycle — records are kept only as long as needed, deleted when retention expires, and paused on litigation hold when required. Weak retention is a privacy-regulator favourite.",
        "whoItAffects": "Any organisation with retention obligations — which is every business subject to privacy, financial, tax, healthcare, or sectoral record-keeping law.",
        "splunkValue": "We detect personal data retained past its legal retention period, verify scheduled deletion jobs actually executed, and alert on litigation-hold changes that happened without a matching legal ticket.",
        "primer": _p("315-2249--retention-and-disposal-automation"),
        "ucs": [
            ("22.49.1", "We detect personal data retained past its legal retention period — turning silent retention drift into a ticket your DPO can close."),
            ("22.49.2", "We verify scheduled deletion jobs actually ran — so expired data does not sit in backups and data warehouses forever."),
            ("22.49.3", "We alert on litigation-hold changes that happen without a matching legal ticket — protecting you from spoliation claims."),
        ],
    },
]


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def _js_string(value: str) -> str:
    """Serialise a Python string as a JavaScript double-quoted string literal."""
    # ``json.dumps`` emits an identical subset for our content: pure text with
    # no non-ASCII control characters.  We keep non-ASCII characters as-is
    # (UTF-8) because the existing file embeds them directly, and we only
    # escape the minimum needed.
    escaped = (
        value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _render_outcomes(outcomes: list[str]) -> str:
    lines = ["    outcomes: ["]
    for i, o in enumerate(outcomes):
        comma = "," if i < len(outcomes) - 1 else ""
        lines.append(f"      {_js_string(o)}{comma}")
    lines.append("    ],")
    return "\n".join(lines) + "\n"


def _render_uc(uc_id: str, why: str) -> str:
    return f'        {{ id: {_js_string(uc_id)}, why: {_js_string(why)} }}'


def _render_area(area: dict[str, Any], is_last: bool) -> str:
    """Render one area as a JS object literal matching the surrounding style."""
    ucs = area["ucs"]
    # Open: { name: "...", description: "...",
    inner: list[str] = []
    inner.append(f"name: {_js_string(area['name'])}")
    inner.append(f"description: {_js_string(area['description'])}")
    for key in ("whatItIs", "whoItAffects", "splunkValue", "primer", "evidencePack"):
        if area.get(key):
            inner.append(f"{key}: {_js_string(area[key])}")

    # All scalar fields stay on the first line to keep diffs reviewable.
    head = "      { " + ", ".join(inner) + ", ucs: ["
    uc_lines = [_render_uc(uc_id, why) for uc_id, why in ucs]
    tail_close = "      ]}"
    trailing = "," if not is_last else ""

    # Join UC entries with commas (JS array syntax requires them).  The final
    # entry carries no trailing comma so the emitted literal is strict-mode safe.
    body = ",\n".join(uc_lines)
    return f"{head}\n{body}\n{tail_close}{trailing}"


def render_block() -> str:
    """Render the full ``"22": { ... }`` block, ready to splice into the JS."""
    lines = ['  "22": {']
    lines.append(_render_outcomes(_OUTCOMES).rstrip())
    lines.append("    areas: [")
    for i, area in enumerate(_AREAS):
        lines.append(_render_area(area, is_last=(i == len(_AREAS) - 1)))
    lines.append("    ]")
    lines.append("  }")
    return "\n".join(lines) + ",\n"


# ---------------------------------------------------------------------------
# File splicing
# ---------------------------------------------------------------------------

def _locate_block(text: str) -> tuple[int, int]:
    start = text.find(BLOCK_START)
    if start == -1:
        raise ValueError('Could not find the start of the "22" block in non-technical-view.js.')
    next_start = text.find(NEXT_BLOCK_START, start)
    if next_start == -1:
        raise ValueError('Could not find the start of the "23" block after "22" block.')
    return start, next_start


def rewrite_file(js_path: pathlib.Path = JS_PATH) -> str:
    text = js_path.read_text(encoding="utf-8")
    start, end = _locate_block(text)
    new_block = render_block()
    new_text = text[:start] + new_block + text[end:]
    js_path.write_text(new_text, encoding="utf-8")
    return new_text


def check_file(js_path: pathlib.Path = JS_PATH) -> bool:
    """Return True if the on-disk content already matches the generator output."""
    text = js_path.read_text(encoding="utf-8")
    start, end = _locate_block(text)
    current = text[start:end]
    expected = render_block()
    return current == expected


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the file already matches the generator output; exit 1 on drift.",
    )
    args = parser.parse_args()

    if args.check:
        if check_file():
            sys.stdout.write(
                "cat-22 non-technical block is up to date.\n"
            )
            return 0
        sys.stderr.write(
            "cat-22 non-technical block drift detected — rerun with\n"
            "  python3 scripts/regenerate_cat22_ntv.py\n"
        )
        return 1

    rewrite_file()
    sys.stdout.write(
        f"Rewrote cat-22 non-technical block in {JS_PATH.relative_to(REPO_ROOT)}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
