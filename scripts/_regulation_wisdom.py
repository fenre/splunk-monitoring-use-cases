#!/usr/bin/env python3
"""
Regulation-specific operational wisdom library.

Each regulation maps to 3-5 unique operational caveats ("failure modes
specific to this regulatory context"). These appear in Step 5 of the
generated DI to ground the troubleshooting guidance in the actual
regulation's requirements, not generic log-pipeline advice.

Keys match exactly the strings seen in compliance[0].regulation across
the 1345 cat-22 UCs. Variant spellings (e.g. "ISO 27001" vs "ISO/IEC
27001", "SOX ITGC" vs "SOX-ITGC") are normalized in the resolver below.
"""

REGULATION_WISDOM = {
    "GDPR": [
        "Lawful basis drift: a detection that worked when the processing activity had consent as its lawful basis becomes misleading when the business team silently changes the RoPA (Record of Processing Activities) entry to 'legitimate interest.' Every GDPR compliance search should reference the RoPA entry ID in its comments and re-review the detection when the RoPA is revised — at minimum annually.",
        "Data Subject Rights timers: Article 12(3) requires response to access/erasure/portability requests within one month. Detections that measure DSR fulfilment must use business-day clocks (not wall-clock 30 days) for regulators that enforce the distinction; the threshold value in the search should align with the local Supervisory Authority's interpretation, not the ISO 8601 literal.",
        "Cross-border transfer fragility: Schrems II invalidated the EU-US Privacy Shield in 2020 and the EU-US Data Privacy Framework (2023) replaced it; any detection involving transfer monitoring must key off the current adequacy decision list, not a hardcoded country allowlist. Maintain `gdpr_adequacy_list.csv` and refresh when the EDPB updates the adequacy register.",
        "Breach notification 72-hour window (Art. 33): the clock starts at awareness, not at the forensically-confirmed moment of compromise. Detections must capture the first-awareness event (SOC alert acknowledgment, first ticket open, first email notification) — not just the incident-resolved timestamp — or the notification SLA metric will understate breaches that took 72h+1h to confirm.",
        "Joint controllership (Art. 26) ambiguity: when both your organisation and a processor/partner log activity against the same data subject, double-counting is easy. Dedupe on (data_subject_id, action_type, timestamp_minute) rather than trusting distinct (event_id) from each side.",
    ],

    "HIPAA Security": [
        "Minimum-necessary principle: access-anomaly detections (excessive chart views, unexpected departments) must NOT flag clinicians accessing records for treatment purposes — §164.502(b) explicitly permits this. Join detections against the clinician's current department and patient's active encounter to avoid generating thousands of false positives on ED doctors seeing admitted patients.",
        "Break-glass and emergency access (§164.312(a)(2)(ii)): emergency accounts will legitimately bypass normal access controls during downtime events. Maintain a lookup `breakglass_declarations.csv` written by the clinical informatics on-call; correlate every break-glass access against a declared event — un-declared emergency access is the finding.",
        "Audit log retention (§164.312(b)): HIPAA requires 6 years of audit log retention, longer than most Splunk index default settings. Verify `frozenTimePeriodInSecs >= 189216000` for every index named in an HIPAA UC's search, and that the archive tier (S3, cold storage) is provisioned.",
        "Covered vs non-covered entity scope: if the search unintentionally pulls data from a non-covered business unit (e.g. a research arm not operating as a HIPAA Covered Entity), findings are noise. Filter using the facility/cost-center lookup that the Privacy Officer maintains, not by index name alone.",
        "Business Associate responsibility: HIPAA §164.308(b) requires BAA before transfer of ePHI. Detections that see an Epic interface firing to a remote host must fail closed if the remote host is not on the BA register — a missing vendor is a control failure, not a data quality issue.",
    ],

    "PCI DSS": [
        "Scope creep: PCI Requirement 1.2 requires CDE (Cardholder Data Environment) documentation. Every PCI DSS detection must explicitly reference the CDE inventory lookup; an 'all hosts' search that happens to catch CDE hosts is NOT compliant evidence — the QSA needs to see the scope boundary enforced in the query itself.",
        "Log retention vs online availability: Req 10.5.1 requires 1 year of audit log retention with at least 3 months immediately available. The index's `frozenTimePeriodInSecs` must be >= 31536000; additionally, Splunk's summary index or an accelerated datamodel must cover the last 90 days for immediate auditor retrieval. One-year hot/warm is not required; the distinction matters for cost.",
        "Daily log review (Req 10.4): PCI requires DAILY review evidence. Detections backing this control must produce signed evidence per calendar day, not per 24-hour rolling window — a search scheduled at 23:55 daily is compliant; one running every 24h from an arbitrary start time is not.",
        "FIM (File Integrity Monitoring, Req 11.5.2) scope: FIM detections must cover critical system files on CDE devices, not 'all changes anywhere.' Use the CDE host list as the first-pass filter; flags on non-CDE hosts dilute the signal and are out of scope for the RoC.",
        "Compensating controls: Req 12.3.4 allows compensating controls with risk-analysis evidence. If the detection is a compensating control for an unremediable weakness (e.g. legacy payment terminal that cannot take patches), the UC must cite the TRA (Targeted Risk Analysis) document ID — auditors will ask to see the original risk assessment.",
    ],

    "PCI-DSS": "PCI DSS",

    "NIS2": [
        "24/7 reporting obligation (Art. 23): NIS2 requires early warning within 24 hours of awareness of a significant incident. Detections that back this SLA must compute elapsed time from the SOC's first-acknowledged timestamp (not the resolve-time) and must trigger independently of business hours — the regulatory clock does not pause overnight.",
        "Member-state variation: NIS2 is transposed individually by each EU Member State with some latitude on thresholds and sector scoping. A detection correct for German IT-SiG 3 (BSI) may be misaligned with Dutch CWV or French LPM. Use `nis2_member_state_config.csv` to parametrize thresholds per jurisdiction; never hardcode.",
        "Essential vs Important entity criteria: the applicable obligations depend on sector + size. Before alerting, verify the monitored entity's designation; a detection firing on an out-of-scope subsidiary causes unnecessary regulatory notifications that erode trust with the national CSIRT.",
        "Supply-chain (Art. 21(2)(d)) extent: NIS2 explicitly includes direct suppliers' cybersecurity posture. Detections must cover monitored-by-you-not-owned-by-you infrastructure (outsourced SaaS, managed SIEM tenants) — these are in scope even if operationally run by a third party. BA/BAA-style governance applies.",
        "Cross-CSIRT notifications: a cross-border incident requires reports to multiple CSIRTs simultaneously. The detection must surface the geographic attack span (source IPs, affected data subjects per country) in the alert payload so the incident commander can fan out to the right authorities without reconstructing the evidence from logs.",
    ],

    "DORA": [
        "Third-party ICT risk register (Art. 28): DORA requires a Register of Information listing every critical ICT third-party service provider. Detections touching supplier risk must reference this register; if a supplier appears in telemetry but not in the Register, that is a Register-completeness finding, not just a technical anomaly.",
        "Testing cadence (Art. 24-27): DORA's TLPT (Threat-Led Penetration Testing) is required every 3 years for significant institutions. Detections measuring resilience testing must differentiate TLPT (supervisor-led) from self-assessment — mixing them dilutes the evidence.",
        "Incident classification thresholds (Art. 18): DORA uses specific criteria for 'major' vs 'significant' incidents — client impact, duration, data volume. Detections must classify against these specific thresholds, which differ from GDPR breach criteria; a single event can be major-DORA but not a personal-data breach.",
        "Resilience testing record retention (Art. 27): results of digital operational resilience tests must be retained. Align log retention to match — typically 5+ years. Verify `frozenTimePeriodInSecs >= 157680000` on any index named by a DORA resilience-testing UC.",
        "Intra-group vs external ICT provider: DORA treats intra-group arrangements differently from external ones. Detections using a supplier register must carry the entity relationship type (intra-group/external/subcontractor) because the regulatory expectations differ.",
    ],

    "ISO 27001": [
        "Statement of Applicability (SoA) drift: ISO 27001 requires a SoA listing which Annex A controls are applicable and which are excluded with justification. A detection for a control excluded in the SoA adds noise to the audit evidence pile; reconcile UC-to-SoA mapping annually. Maintain `iso27001_soa.csv` with current applicability.",
        "Context of the organisation (Cl. 4): controls calibrated for a 50-person company's threat model do not suit a 5000-person multinational's. Detection thresholds, log retention, and escalation paths must align with the organisation's ISMS scope — a single 'enterprise default' for ISO 27001 is a tell-tale sign of a cookie-cutter implementation.",
        "Internal audit programme (Cl. 9.2) evidence: detections that support internal audits must produce records that can be attached to audit evidence packs. Tag the alert payload with audit_cycle=YYYY-HN so evidence bundling is trivial.",
        "Management review inputs (Cl. 9.3): control effectiveness metrics must be reviewable at management review. A detection that only raises alerts (no trend metric) cannot be brought to the management meeting; schedule a companion report that produces trend data per control.",
        "Risk treatment option alignment: ISO 27001 risk treatment options are accept/mitigate/transfer/avoid. A detection flagging a 'risk' that has been formally accepted by the risk owner is noise. Maintain `iso27001_risk_treatment_register.csv` and suppress findings on accepted items.",
    ],

    "ISO/IEC 27001": "ISO 27001",

    "NERC CIP": [
        "BES Cyber System classification (CIP-002): every NERC CIP detection must filter to BES Cyber Systems only. A general 'Windows login' search across the entire estate is not CIP evidence; a search filtered through `bes_cyber_asset_inventory.csv` is.",
        "Low-Impact vs Medium-Impact vs High-Impact: CIP requirements scale with impact rating. A detection that fires identically for Low and High-Impact systems over-applies controls (wastes IR effort) and under-applies audit attention. Include impact rating in the alert payload and route by rating.",
        "ERC (Electronic Security Perimeter) boundary: CIP-005 requires strict ESP documentation. Firewall-rule detections must reference the ESP boundary register — a rule change on a firewall that's not an EAP is NOT a CIP finding; a rule change on an EAP is.",
        "CIP-010 configuration baselines: baseline monitoring must use an approved baseline, not an informal one. Reference the CIP-010 attestation register in the UC; baselines without dated attestation signatures are not regulatory evidence.",
        "BES Cyber Asset changes (CIP-007 R2.1): patching evidence must be presented per CIP-assessable 35-day window, not generic monthly. Schedule the detection to produce evidence at 35-day boundaries and retain for the 3-year retention requirement.",
    ],

    "NIST 800-53": [
        "Control baseline selection: NIST 800-53 has Low/Moderate/High/Privacy baselines via FIPS 199 categorisation. A detection written to a High baseline threshold produces false alarms against Low-categorised systems. Join with the system categorisation register `nist_800_53_system_categorization.csv` before thresholding.",
        "CA-7 continuous monitoring cadence: specifies 'ongoing' authorisation activities. Detections supporting CA-7 must produce metrics at the organisation's ConMon cadence (monthly is common for most agencies) — weekly fires are fine but not themselves evidence of monthly compliance.",
        "Control inheritance: in a cloud-hybrid deployment, some controls are inherited from the Cloud Service Provider. Detections must not flag 'missing' controls the CSP provides (documented in the SSP via Control Inheritance matrix); reference the SSP appendix and suppress matching findings.",
        "SP 800-53 Rev 5 restructure: controls were renumbered between Rev 4 and Rev 5. Detections that cite Rev 4 numbering (e.g. AC-2.12) may not match the SSP if the organisation has migrated. Store both Rev numbers in the UC metadata and reconcile.",
        "POA&M (Plan of Action and Milestones) alignment: a detection firing on a weakness already in the POA&M is expected — it's acceptance documented. Cross-reference `nist_800_53_poam_register.csv` and suppress POA&M-accepted findings during their planned remediation window.",
    ],

    "NIST-800-53": "NIST 800-53",

    "NIST CSF": [
        "Tier calibration: NIST CSF defines four Implementation Tiers (Partial, Risk Informed, Repeatable, Adaptive). Detections tuned for Tier 4 (Adaptive) organisations over-report on Tier 1-2 organisations still establishing risk processes. Tag the UC's intended Tier in metadata; adjust thresholds per organisational maturity.",
        "CSF 2.0 'Govern' function: added in version 2.0 (Feb 2024), covering governance and supply-chain risk. UCs authored against CSF 1.1 do not explicitly touch Govern — reconcile the UC set annually against the current subcategory list.",
        "Profile alignment: CSF Profiles (current and target) describe an organisation's prioritised outcomes. A detection that doesn't map to the current Profile produces uncontextualised noise. Reference the Profile ID in the UC; revisit when the profile is updated.",
        "Informative References: NIST CSF maps subcategories to NIST 800-53, ISO 27001, COBIT etc. Detections should not claim framework coverage solely on the strongest mapping — if the CSF subcategory lists multiple frameworks, the UC's evidence should be usable for all of them.",
        "Outcome vs activity: CSF is outcome-oriented; each subcategory describes a state to achieve, not a specific control to implement. A detection measuring 'control activity happened' does NOT prove 'outcome achieved' — wire outcomes into the detection logic, e.g. measure time-to-detect, not 'alert was generated'.",
    ],

    "IEC 62443": [
        "Zone and Conduit model (IEC 62443-3-2): every OT/ICS detection must reference zone and conduit definitions. A generic 'unauthorised network connection' search without zone context cannot be presented as 62443 evidence; the zone register is authoritative.",
        "Security Levels SL-T (Target) vs SL-A (Achieved): detections must differentiate target vs achieved SL. Firing on an SL-T=3 zone with SL-A=2 is expected — the gap is being tracked — not a new finding. Reference the zone's current SL-A in the detection.",
        "Patch window constraints: OT environments tolerate patching only during plant shutdowns. Detections on patch levels must reference the plant's maintenance calendar (`plant_maintenance_windows.csv`) and consider findings during production hours as 'tracked-not-actioned,' not 'overdue.'",
        "CRS (Common Required Security) vs FR (Foundational Requirement) hierarchy: 62443 organises controls under 7 FRs. Detections claiming multi-FR coverage must prove each FR independently — a single telemetry source rarely satisfies all 7.",
        "Safety vs security tradeoff: IEC 62443 explicitly subordinates security to safety. A detection whose response action could interfere with safety-instrumented function (SIF) operation is not acceptable in OT. Tag such detections `response_action=observe_only` and require human-in-loop for any containment.",
    ],

    "SOX ITGC": [
        "Scope is financial-reporting systems: SOX ITGC covers systems that feed the general ledger. Detections on HR, research, or operational systems that do not touch GL are out of scope. Maintain `sox_in_scope_systems.csv`; suppress alerts on out-of-scope hosts.",
        "Change management evidence: PCAOB AS 5 requires 'adequate' evidence of change controls. 'Adequate' is interpreted by the external auditor — typically this means the ticket exists, ticket was approved before change, approver != implementer, and change can be tied to a specific deployment record. Missing any one of these loses SOX compliance.",
        "Segregation of duties (SoD): the famous 'one person cannot both create AND approve a payment' rule. SoD detections must use the HR authoritative role register, not AD groups, which accumulate historical access and drift.",
        "Key reports (key reports classification): the external auditor designates 'key reports' — reports used in the financial-close process. Detections on report access only need to fire for key reports; non-key report access is noise.",
        "Year-end cutover: SOX focuses on fiscal-year boundaries. Detections should produce evidence packs aligned to fiscal year (not calendar year) — a cadence of 'every December 31' is wrong for organisations with June or March fiscal years.",
    ],

    "SOX-ITGC": "SOX ITGC",

    "FISMA": [
        "ATO (Authorization to Operate) scope: FISMA findings fire only against ATO-in-scope systems. A detection that picks up a development or pre-ATO system as 'non-compliant' is a scoping error — filter against `fisma_ato_register.csv`.",
        "Plan of Action and Milestones (POA&M): FISMA requires POA&M for every known weakness. Detections recognising a known weakness should reference the POA&M ID — without it, the detection creates duplicate tracking entries, polluting the POA&M itself.",
        "FIPS 199 categorisation: impact baseline (Low/Moderate/High) determines required control strength. Detection thresholds must scale with impact baseline; a single threshold across Low/Moderate/High systems is non-compliant.",
        "CIO quarterly reporting (OMB A-130): FISMA metrics feed quarterly CIO reports. The detection must produce QoQ-comparable numbers — any change in methodology mid-year produces a discontinuity that auditors (and Congress) flag.",
        "Third-party ATO inheritance: when using a FedRAMP-authorised cloud, the CSP's ATO can be inherited. Don't fire detections that require the customer to prove controls the CSP provides (check the responsibility matrix).",
    ],

    "FDA Part 11": [
        "Predicate rule context: 21 CFR Part 11 overlays a predicate rule (e.g. 21 CFR Part 211 for pharma GMP). Detections must reference the predicate rule — Part 11 alone doesn't define what must be recorded, only how electronic records are treated.",
        "Signature semantics: Part 11 distinguishes between 'electronic signature' (legally equivalent to wet ink) and 'electronic approval.' Detections on signature integrity must identify WHICH signature type an event represents; generic 'approval recorded' is not evidence of 11-compliant signing.",
        "Audit trail independence (§11.10(e)): the audit trail must be independent of operator action. A detection measuring 'audit trail presence' must test for independence — if operators can modify the audit trail, the system fails Part 11 regardless of what events were captured.",
        "Time source authority: §11.10(d) requires operator actions to be 'time-stamped.' The time source must be documented and auditable (not the user's desktop clock). Detections must verify events use the authoritative time source; clock drift >5 seconds is a deviation.",
        "Closed vs open system: §11.10 (closed) and §11.30 (open) have different requirements. The detection must know which regime applies — an open system (internet-connected) requires additional integrity controls that closed systems do not.",
    ],

    "SOC 2": [
        "Trust Services Criteria scope: SOC 2 covers five TSCs (Security, Availability, Processing Integrity, Confidentiality, Privacy). Every UC must specify which TSCs it evidences; 'SOC 2' alone is ambiguous. Most organisations scope to Security + Availability — don't assume all five.",
        "Type 1 vs Type 2: Type 1 is point-in-time; Type 2 is 6-12 months of evidence. Detections supporting Type 2 must produce date-stamped evidence continuously, not just at snapshots — gaps in evidence are findings.",
        "CSOC (Control Owner / Service Organisation Control) assertions: SOC 2 depends on management's written assertion about the control. Detection output must be reconcilable to the assertion wording; a mismatch between 'what the control says' and 'what the detection measures' invalidates the evidence.",
        "Carve-out vs inclusive method: if subservice organisations are carved out, the UC must not cover them (they're not in scope). If inclusive, the UC must cover them even if owned by a third party — clarify in the UC metadata.",
        "Auditor's view of evidence: SOC 2 auditors want evidence samples, not totals. A detection producing 'control violated 15 times' is less useful than 'here are 15 specific records with request-id' — structure the alert payload so individual records can be drilled into.",
    ],

    "SOC-2": "SOC 2",

    "EU AML": [
        "Risk-Based Approach (Art. 8, 5AMLD/6AMLD): detections must calibrate to customer risk rating, not transaction thresholds alone. A €3,000 payment from a HIGH-risk customer is more suspicious than €8,000 from a LOW-risk customer; a detection that uses amount alone misses this.",
        "STR/SAR filing obligations: Article 33 requires 'without delay' filing upon suspicion. Detections measuring filing SLA must track from first-analyst-suspicion, not from case-open — the analyst's note is often the regulatory clock start.",
        "PEP (Politically Exposed Persons) list dynamism: PEP screening lists change continuously. A detection that relies on a stale PEP list produces retrospective findings; the lookup must be refreshed at least daily and the refresh SLA itself should be monitored.",
        "Beneficial ownership transparency: AMLD expands BO reporting. Detections on entity ownership must cross-check against the UBO register; a transaction counterparty whose beneficiary ownership is unclear is a higher-risk event than the raw amount suggests.",
        "Cross-border correspondent banking: enhanced due diligence required for non-EU correspondent relationships. Detections on correspondent banking must differentiate intra-EU from non-EU flows; different thresholds apply.",
    ],

    "PSD2": [
        "Strong Customer Authentication (SCA) exemptions: PSD2 RTS on SCA has exemptions (low-value, trusted beneficiary, corporate). Detections on SCA failures must factor in which transactions are legitimately exempt; flagging an exempt transaction as 'missing SCA' is a false positive.",
        "Access to Account (XS2A) API semantics: AISPs and PISPs have specific access patterns. A detection treating third-party access as 'unauthorised' misses PSD2's open-banking framework — differentiate TPP-sourced access from direct-consumer access.",
        "90-day reauthentication (Art. 10, RTS): AISPs must reauthenticate every 90 days. Detections on consent lifecycle must fire at 90 days even if the consent 'still works' technically — the regulatory clock is the trigger, not the technical session expiry.",
        "Fraud reporting thresholds (EBA guidelines): PSD2 requires fraud data reported to NCAs. Detections feeding this reporting must align with EBA's exact fraud-classification taxonomy (unauthorised, manipulation, etc.) — local terminology may not match.",
        "Liability shift: PSD2 shifts unauthorised-transaction liability to the PSP unless gross negligence is proved. Detections flagging 'customer negligence' must produce defensible evidence (multiple repeated ignored warnings), not just 'click without reading.'",
    ],

    "CCPA/CPRA": [
        "Consumer Request categories: CCPA distinguishes Right to Know, Right to Delete, Right to Opt-Out, Right to Correct, Right to Limit. Detections on 'consumer request' must specify category — the 45-day clock applies differently to each.",
        "Verifiable Consumer Requests: the consumer identity must be verified 'to a reasonable degree.' Detections measuring request-to-response latency must start the clock at verification complete, not at request receipt — this is a common source of false SLA failures.",
        "Sale vs share distinction: CPRA broadens 'sale' to include 'share' for cross-context behavioural advertising. Detections on consent-to-share must use the current law wording; a CCPA-only detection misses the CPRA expansion.",
        "Do Not Sell / Do Not Share signal (GPC): Global Privacy Control must be honoured. Detections must treat GPC-asserting browsers as opted-out irrespective of UI consent state — the technical signal is authoritative.",
        "Minor consent (13-16): affirmative opt-in required for sale/share of minor data. Detections on data sharing must intersect with age assertion; lack of age data on shared minor info is itself a finding.",
    ],

    "FDA Part 11": [
        "Predicate rule context: 21 CFR Part 11 overlays a predicate rule (e.g. 21 CFR Part 211 for pharma GMP). Detections must reference the predicate rule — Part 11 alone doesn't define what must be recorded, only how electronic records are treated.",
        "Signature semantics: Part 11 distinguishes between 'electronic signature' (legally equivalent to wet ink) and 'electronic approval.' Detections on signature integrity must identify WHICH signature type an event represents; generic 'approval recorded' is not evidence of 11-compliant signing.",
        "Audit trail independence (§11.10(e)): the audit trail must be independent of operator action. A detection measuring 'audit trail presence' must test for independence — if operators can modify the audit trail, the system fails Part 11 regardless of what events were captured.",
        "Time source authority: §11.10(d) requires operator actions to be 'time-stamped.' The time source must be documented and auditable (not the user's desktop clock). Detections must verify events use the authoritative time source; clock drift >5 seconds is a deviation.",
        "Closed vs open system: §11.10 (closed) and §11.30 (open) have different requirements. The detection must know which regime applies — an open system (internet-connected) requires additional integrity controls that closed systems do not.",
    ],

    "CMMC": [
        "Level 1/2/3 distinction: CMMC 2.0 has three levels (Foundational/Advanced/Expert). Detections must specify level — Level 1 is self-assessed against basic cyber hygiene; Level 3 requires NIST SP 800-172 enhanced controls plus triennial assessment.",
        "FCI vs CUI boundary: CMMC applies only to systems handling Federal Contract Information (FCI) or Controlled Unclassified Information (CUI). Detections scoped to 'entire organisation' fire on out-of-boundary systems, wasting audit effort.",
        "POA&M acceptance limitation: unlike FISMA, CMMC limits POA&M use — certain controls cannot have open POA&M items at assessment. Detections must know which controls can have open POA&M and which cannot.",
        "C3PAO assessment cadence: Level 2+ requires third-party assessment every 3 years. Detections measuring control stability must span the full triennial cycle; short-window detections miss drift between assessments.",
        "800-171 Rev 3 migration: CMMC is aligning with NIST 800-171 Rev 3. Organisations mid-migration have mixed controls; reconcile the UC's cited revision against the target assessment date.",
    ],

    "EU AI Act": [
        "Risk category sensitivity: AI Act defines Prohibited / High / Limited / Minimal risk. Detections must fire only on systems classified High or above — Minimal-risk systems like spam filters are out of scope and noise from them hides real findings.",
        "General-Purpose AI (GPAI) disclosure: foundation models have specific transparency obligations. Detections on model provenance must differentiate GPAI from task-specific models; GPAI adds requirements that task-specific models don't trigger.",
        "Post-market monitoring (Art. 72): High-risk AI systems require post-market monitoring plans. Detections are evidence of such monitoring — align the detection's measurement cadence and scope with the system's PMMS document.",
        "Fundamental Rights Impact Assessment: FRIA is required for many public-sector deployments. Detections on fairness/bias metrics must be reconcilable to the FRIA's specific risk indicators, not generic AI fairness metrics.",
        "Human-in-the-loop requirement: High-risk AI requires human oversight. A detection on 'autonomous decisions without human review' is a core AI Act control; the detection must know who the designated human is (role-based, from the deployment's governance document).",
    ],

    "MiFID II": [
        "Best execution evidence (RTS 27/28): MiFID II requires venue-level best execution reporting. Detections must cover ALL execution venues the firm uses, not just the primary — a detection missing a single venue fails the 'all venues' requirement.",
        "Transaction reporting (MiFIR Art. 26): T+1 reporting to competent authority. The detection's latency must be tight enough to catch missing-report within the T+1 window; a 7-day cadence is regulatorily too slow.",
        "Pre-trade and post-trade transparency: pre-trade quotes and post-trade trade reports are separate obligations. Detections on transparency must differentiate; missing pre-trade quote != missing post-trade report.",
        "Systematic Internaliser thresholds: SI designation triggers at specific volume thresholds. Detections on SI obligations must read the latest SI thresholds (ESMA updates them periodically); a hardcoded threshold goes stale within months.",
        "Clock synchronisation (RTS 25): UTC within 100 μs for HFT, 1 ms for others. Detections timestamping trades must verify the authoritative clock source; clock drift detections are themselves MiFID controls.",
    ],

    "EU CRA": [
        "Product scope: Cyber Resilience Act applies to 'products with digital elements.' The scope depends on whether the product is placed on the EU market — a product sold only within an enterprise isn't in scope. Reference `cra_product_scope.csv`.",
        "Important vs Critical product designation: CRA has three tiers (default / important / critical). Detections calibrated for critical products over-apply to default; separate thresholds by designation.",
        "Conformity assessment route: CRA offers internal control or third-party assessment routes. The evidence the detection produces must match the chosen route; internal-control route requires more detailed internal evidence than the third-party route.",
        "Vulnerability disclosure (Art. 11): manufacturer obligation to actively exploit-monitor. Detections on exploitation attempts must feed the vulnerability disclosure workflow; a detection without a pipeline to the disclosure process is insufficient.",
        "SBOM (Software Bill of Materials): CRA effectively requires SBOM. Detections on component tracking must tie to the SBOM format (CycloneDX, SPDX); format mismatch fails the 'machine-readable' requirement.",
    ],

    "EU-CRA": "EU CRA",

    "API RP 1164": [
        "Physical vs cyber correlation: API 1164 specifically addresses Pipeline SCADA. Detections must correlate physical (pressure, flow, valve) telemetry with cyber events — treating them separately misses the purpose of 1164.",
        "PSIR (Pipeline SCADA Integrity & Reliability) zone model: similar to IEC 62443 zones but pipeline-specific. Detections must use the PSIR zone register, not generic IT segmentation.",
        "Control room operator workflow: detections interfering with operator's control room workflow are safety risks. Coordinate all automated responses with the control room shift supervisor — observe-only is the default for SCADA telemetry detections.",
        "TSA Security Directives overlap: TSA SDs for pipelines overlap with API 1164 but are more prescriptive. Reconcile the UC against both; TSA takes regulatory precedence where they conflict.",
        "Restoration priority: API 1164 includes emergency restoration priorities. Detections on incident response must understand that restoration is prioritised above attribution in pipeline events.",
    ],

    "TSA SD": [
        "Covered surface transportation: TSA SDs cover specific rail, pipeline, and transit operators. Detections must scope to covered operations; non-covered assets are noise.",
        "Cybersecurity Coordinator designation: each covered entity has a designated CC. Detections on IR must route through the CC's communication channel; bypassing the CC is a procedural finding.",
        "CISA reporting timelines: different incident types have different reporting windows (e.g. 24h for certain classes). Detections on reporting SLA must encode the specific window per incident type.",
        "OT/IT segmentation: TSA SDs strongly emphasise OT/IT separation. Detections on cross-domain access must identify which side is which; an alert that doesn't know its physical/cyber domain is ambiguous.",
        "Vulnerability mitigation timelines: TSA SDs set specific time-to-mitigate for critical CVEs. Reconcile the detection's threshold to the applicable SD's current mitigation table — this table updates.",
    ],

    "eIDAS": [
        "Qualified vs non-qualified trust services: eIDAS 910/2014 and eIDAS 2 distinguish qualified (regulated) from advanced electronic signatures. Detections must differentiate; non-qualified signatures lack the same legal presumption.",
        "EU Digital Identity Wallet (eIDAS 2.0): the revised regulation introduces the EUDI Wallet. Detections on identity verification must know whether EUDI is in use — different evidence applies.",
        "Qualified timestamp requirement: certain documents require qualified timestamps (QTSP-issued). Detections on timestamp authority must verify QTSP status against the EU Trusted List; a non-QTSP timestamp doesn't carry legal weight.",
        "Cross-border recognition: eIDAS mandates cross-border recognition. Detections on identity assurance must respect the issuing Member State's LoA; rejecting a valid MS LoA is a compliance violation.",
        "Ancillary services: eIDAS covers delivery services (qualified electronic delivery). Detections on message-delivery integrity must distinguish qualified from non-qualified delivery paths.",
    ],

    "PIPL": [
        "Cross-border transfer mechanism: PIPL Art. 38 mandates specific cross-border transfer mechanisms (CAC security assessment, CN standard contract, certification). Detections on cross-border data flow must verify which mechanism applies; using the wrong mechanism is a major finding.",
        "Sensitive personal information: PIPL's SPI category is broader than GDPR's — includes biometric, religious, specific identity, medical, financial, whereabouts, minors. Detections must match the PIPL definition, not the GDPR definition.",
        "Large-scale handler threshold: PIPL Art. 58 applies to handlers processing PI of >1M people. Detections supporting large-scale obligations must validate scale against this specific threshold.",
        "Individual consent granularity: PIPL requires separate consent for sensitive PI vs regular PI, and separate consent for cross-border. Detections on consent coverage must check all applicable consent types, not just one bundled 'yes.'",
        "CAC filing obligations: certain processing requires filing with Cyberspace Administration of China. Detections on regulatory-reporting completeness must check filing status per activity.",
    ],

    "SWIFT CSP": [
        "CSCF (Customer Security Controls Framework) Mandatory vs Advisory: CSCF distinguishes mandatory (must implement) from advisory. Detections must tag which category each finding belongs to — advisory findings don't prevent attestation.",
        "Architecture Type A vs B: SWIFT defines two architecture types. Detections must know which architecture applies; the same control has different implementation expectations per architecture.",
        "Swift CSP attestation cadence: annual attestation on July 31 anchoring point. Detections producing attestation evidence must align to this annual cycle; quarterly evidence is over-frequent, daily is too granular.",
        "Controls shifted mandatory (framework drift): SWIFT moves controls from advisory to mandatory each year. Reconcile UC-to-framework mapping annually as of the latest CSCF version.",
        "Third-party service provider coverage: some SWIFT-using firms use shared infrastructure. Detections must understand the boundary between own-infrastructure and SSP-provided; claims of compliance on SSP-provided infrastructure require SSP attestation.",
    ],

    "AU Privacy Act": [
        "APP (Australian Privacy Principles) scope: APPs define 13 principles covering collection, use, disclosure. Detections on privacy controls must cite specific APP number — 'privacy violation' alone is not actionable.",
        "Notifiable Data Breach scheme: 30-day OAIC notification from awareness of eligible data breach. Detections measuring breach SLA start from first eligible-breach determination, not raw incident detection.",
        "Serious harm threshold: NDB scheme only triggers on 'likely to result in serious harm' breaches. Detections must include harm likelihood scoring; routine access anomalies don't automatically meet the threshold.",
        "Privacy Act 2024 reforms: major reforms introduce mandatory Privacy Impact Assessments and direct right of action. Detections must anticipate the revised APPs; UCs authored pre-reform need reconciliation.",
        "Small business exemption: APs apply to entities >$3M annual turnover by default. Detections on policies specific to the AU Privacy Act must not fire on exempt subsidiaries.",
    ],

    "APRA CPS 234": [
        "APRA-regulated entity scope: CPS 234 applies to APRA-regulated financial institutions. Detections on information security controls must verify entity is in scope.",
        "Third-party information security: CPS 234 Part 6 requires oversight of information security of third parties. Detections on supplier cyber posture align here; without the supplier register, the detection's scope is unclear.",
        "Incident notification to APRA: 72h notification for material incidents. Detections on IR metrics must measure time-to-APRA-notification, not just time-to-internal-closure.",
        "Control testing cadence: CPS 234 requires annual testing of ISMS effectiveness. Detections supporting testing must produce annual evidence packs; quarterly testing is fine but doesn't itself satisfy the annual requirement.",
        "Information asset classification: asset classification must be documented. Detections referring to 'classified information' must reconcile to the asset register's classification scheme, not assume a universal one.",
    ],

    "UK NIS": [
        "Operator of Essential Services (OES) scope: UK NIS applies to designated OES + Digital Service Providers. Detections must scope to designated entities; non-designated are out of scope.",
        "Competent Authority variation: UK NIS has multiple Competent Authorities per sector. Detections on CA-reporting must differentiate (ICO for digital services, HSE for transport, etc.).",
        "72h incident notification to NCSC: similar to EU NIS2 but UK-specific. Detection timeline must target NCSC reporting, not EU CSIRT chains.",
        "NIS2 vs UK NIS divergence: UK is diverging from EU NIS2. Detections written for UK jurisdiction must track UK's specific transposition, not assume alignment with EU NIS2.",
        "CAF (Cyber Assessment Framework) self-assessment: NCSC CAF is the common self-assessment tool. Detections should map to CAF outcomes, making the self-assessment evidence-backed.",
    ],

    "FCA SS1/21": [
        "Operational Resilience scope: SS1/21 focuses on IBSI (Important Business Services and Indicators). Detections must reference the firm's IBSI register; detections on non-IBSI are out of scope.",
        "Impact Tolerance statement: every IBSI has a documented impact tolerance. Detections measuring service disruption must compare to the tolerance, not fire on any outage.",
        "Self-assessment vs independent review: FCA expects both internal self-assessment and periodic independent review. Detections support self-assessment; independent review is separate.",
        "Third-party scenario testing: SS1/21 requires testing third-party dependencies. Detections on supplier resilience must include contingency-testing evidence, not just uptime metrics.",
        "Annual report alignment: SS1/21 outputs align with annual operational resilience report. Detections should produce evidence fit for annual reporting.",
    ],

    "MAS TRM": [
        "MAS TRM scope: applies to Singapore-regulated financial institutions. Detections on technology risk controls must verify MAS regulatory scope.",
        "Critical System definition: MAS TRM defines 'critical system' in specific terms. Detections on critical system controls must reference the critical system register.",
        "Incident notification within 1 hour for critical outages: tight SLA. Detections on IR must trigger within the hour window; 24h detections miss the regulatory clock.",
        "Third-party risk management (TRM Ch. 7): MAS TRM has specific TPRM requirements. Detections on third parties must cite the specific MAS TRM expectation.",
        "Cyber Hygiene Notice: MAS CHN sets baseline cyber hygiene expectations. Detections supporting CHN compliance must align with the specific 6 control categories.",
    ],

    "ASD E8": [
        "Essential Eight Mitigation Strategies: 8 specific strategies. Detections must cite which E8 mitigation; non-E8 controls don't count toward E8 maturity.",
        "Maturity Level 0/1/2/3: E8 has maturity levels per strategy. Detections must score against the target maturity level; a ML1-calibrated detection falls short of ML3 organisations.",
        "Australian Government scope: E8 primarily applies to Commonwealth entities. Private-sector adoption is voluntary; detections should clarify regulatory driver.",
        "Microsoft-centric assumptions: E8 is written against a primarily Microsoft estate (Office macros, application control). Non-Microsoft detections require translation.",
        "ISM (Information Security Manual) overlap: ACSC's ISM has overlapping controls. Detections satisfying E8 may not fully satisfy ISM; reconcile explicitly.",
    ],

    "LGPD": [
        "LGPD scope (Art. 1): applies to processing of personal data in Brazil or with Brazilian data subjects. Detections on data residency must account for extraterritorial application.",
        "ANPD (National Data Protection Authority) sanctions: ANPD active since 2021. Detections on regulatory exposure must reflect ANPD's current enforcement posture.",
        "Legal bases (Art. 7): LGPD defines 10 legal bases (broader than GDPR). Detections on lawful-basis drift must cover all 10 bases.",
        "Good faith and transparency: LGPD emphasises good-faith processing. Detections on consent gaps must consider whether processing is in good faith — a technical gap may not be a compliance gap if good faith is documented.",
        "International transfer: LGPD Art. 33 requires specific transfer mechanisms. Detections on transfer must verify mechanism; hardcoding 'US is safe' is a violation.",
    ],

    "NO Sikkerhetsloven": [
        "Sikkerhetsloven scope: Norwegian Security Act applies to national security assets. Detections must reference the classification register — only classified assets are in scope.",
        "NSM (Nasjonal sikkerhetsmyndighet) coordination: NSM is the authority. Detections on incident response must route to NSM at the thresholds defined in classification.",
        "Forsvarssektorens Grunnsyn: military-sector specific. Detections on defence-sector assets may apply grunnsyn in addition to Sikkerhetsloven.",
        "Object/Asset classification scheme: unique to Norway (Beskyttet/Konfidensielt/Hemmelig/Strengt Hemmelig). Detections must use Norwegian classifications, not GDPR/NATO equivalents.",
        "Sector-specific implementing regulations: petroleum, telecom, financial services have specific implementing regulations (forskrifter). Detections must map to the applicable forskrift.",
    ],

    "NO Petroleumsforskriften": [
        "Petroleum sector scope: applies to offshore petroleum operations on the Norwegian Continental Shelf. Detections on petroleum-specific risks must differentiate from general IT detections.",
        "Petroleumstilsynet (PTIL) coordination: PTIL is the regulator for offshore safety. Detections on safety-critical IT must align with PTIL reporting.",
        "Sikkerhetsloven interaction: Petroleumsforskriften references Sikkerhetsloven for national security aspects. Detections must track both.",
        "Norsk Olje og Gass framework: industry-specific framework referenced by the regulation. Detections on cyber risk should align with the current NOG recommendations.",
        "Offshore/onshore distinction: some obligations apply only offshore, some apply to onshore facilities supporting offshore ops. Detections must know which side of the boundary they cover.",
    ],

    "NO Personopplysningsloven": [
        "Datatilsynet (DPA) coordination: Norwegian DPA. Detections on personal data obligations route to Datatilsynet, not EDPB.",
        "GDPR supplementation: Personopplysningsloven supplements GDPR in Norway. Detections must track both — Norway-specific rules (e.g. fødselsnummer handling) are additional.",
        "Fødselsnummer (national ID) handling: special rules apply to national identifier processing. Detections on PII must differentiate fødselsnummer from other IDs.",
        "Employee monitoring: Norway has strict employee monitoring rules. Detections on user activity monitoring must consider the employment-law overlay.",
        "Research exemptions: Art. 9 LGGDPR has specific research exemptions in Norway. Detections on health/research data must know whether research exemption applies.",
    ],

    "SG PDPA": [
        "PDPC (Personal Data Protection Commission) coordination: Singapore DPA.",
        "Consent obligation (Sec. 13): Consent is specific in Singapore PDPA. Detections on consent drift must track consent per purpose.",
        "Do Not Call (DNC) Registry: Singapore PDPA includes DNC. Detections on outbound communications must verify DNC compliance.",
        "Data Breach Notification (2021 amendments): notification required to PDPC and affected individuals. Detections must measure both.",
        "Data Protection Officer requirement: organisations must designate DPO. Detections on governance must cite the DPO role.",
    ],

    "SA PDPL": [
        "SDAIA scope: Saudi Data & AI Authority. Detections on personal data in KSA route to SDAIA.",
        "Data residency requirement: PDPL has strict data residency. Detections on cross-border data must verify the specific transfer mechanism.",
        "Controller/Processor registration: certain entities must register. Detections on governance must include registration status.",
        "KSA-specific definition of personal data: distinctions from GDPR. Detections must use the PDPL definitions.",
        "Penalties for non-compliance: PDPL has significant penalties. Detections on risk exposure must quantify PDPL-specific exposure.",
    ],

    "APPI": [
        "PPC (Personal Information Protection Commission) coordination: Japan DPA.",
        "Consent vs opt-out distinction: APPI allows opt-out for non-sensitive; detections must differentiate.",
        "Cross-border transfer approval (Art. 24): specific consent or approved country list. Detections on transfer must verify approach.",
        "Anonymization vs pseudonymization: APPI distinguishes tokunmi-joho from other forms. Detections on anonymization must use APPI terms.",
        "2024 amendments: recent changes to sensitive personal info and transfer. Detections should track latest APPI revision.",
    ],

    "RBI Cyber": [
        "RBI scope: applies to banks and payment system operators in India.",
        "Cyber Security Framework: RBI's framework is specific. Detections must map to RBI CS framework, not generic NIST.",
        "Incident reporting (2-6h): RBI has strict incident reporting timeline depending on severity.",
        "Data localisation: RBI has payment system data localisation. Detections on data residency must verify compliance.",
        "DPSS (Department of Payment and Settlement Systems): coordination point for payments.",
    ],

    "NESA IAS": [
        "UAE scope: applies to UAE Critical Information Infrastructure.",
        "NESA (UAE National Electronic Security Authority): coordination authority.",
        "5 Security Domains: NESA IAS organises controls in 5 domains.",
        "Compliance levels: multiple compliance tiers. Detections must specify target tier.",
        "Quarterly attestation: detections produce quarterly evidence.",
    ],

    "QCB Cyber": [
        "Qatar Central Bank scope: QCB Cyber Security Framework for banks and payment operators.",
        "Governance, Identify, Protect, Detect, Respond, Recover: 6-function structure.",
        "Regulatory sandbox considerations: QCB operates sandbox; detections may differ in sandbox vs production.",
        "Data residency within Qatar: QCB has data localisation expectations.",
        "Incident reporting timelines specific to QCB.",
    ],

    "NO KBF": [
        "Kraftberedskapsforskriften scope: Norwegian power sector regulation (NVE).",
        "NVE coordination: National Water Resources and Energy Directorate.",
        "Kraftsystemet (power system) criticality: detections on grid-connected assets differ from generic IT.",
        "Interaction with Sikkerhetsloven: national-security aspects of power grid.",
        "Beredskapstiltak (preparedness measures): detections on preparedness differ from generic IR.",
    ],

    "PRA SS2/21": [
        "PRA scope: Prudential Regulation Authority (UK). Applies to banks and insurers.",
        "Third-party risk management focus: SS2/21 strengthens TPRM expectations.",
        "Alignment with FCA SS1/21: similar resilience framing but from prudential perspective.",
        "Operational resilience testing: severe-but-plausible scenarios required.",
        "Senior Manager accountability: detections on TPRM link to SMCR-specific roles.",
    ],

    "FCA SM&CR": [
        "Senior Manager Functions (SMF): SMCR defines specific SMFs. Detections on executive accountability must reference SMF numbers.",
        "Certification Regime: applies to non-SMF staff performing significant roles. Detections on personnel controls differentiate SMFs from certified.",
        "Conduct Rules: 5 individual conduct rules, 4 senior manager. Detections on personal conduct must map to specific rule.",
        "Statement of Responsibilities (SoR): every SMF has a written SoR. Detections on accountability must reconcile to SoR text.",
        "Breach notification (Form H): FCA Form H for conduct breaches. Detections must support Form H evidence.",
    ],

    "IT-SiG 2.0": [
        "BSI coordination: German Federal Office for Information Security. IT-SiG 2.0 expanded obligations.",
        "KRITIS operator scope: applies to Critical Infrastructure operators. Detections must verify KRITIS status.",
        "Company of special public interest (UBI): additional category under 2.0. Detections differ for UBI.",
        "Attack detection systems (Angriffserkennung): specific technical expectation. Detections must be Angriffserkennung-compliant.",
        "Reporting timeline: 4 hours for critical incidents in KRITIS. Tight SLA.",
    ],

    "BSI-KritisV": [
        "KRITIS sector thresholds: KritisV defines sector-specific thresholds (population served, revenue, etc.). Detections must verify threshold crossing.",
        "Specific sectors: energy, water, food, telecom, finance, transport, health, waste. Detections differ per sector.",
        "Transition periods: when thresholds change, there's a transition. Detections during transition must handle both old and new.",
        "BSI registration requirement: KRITIS operators register with BSI. Detections must verify registration status.",
        "Branchenstandard (sector standard): sector-specific standards complement KritisV. Detections should align to applicable Branchenstandard.",
    ],

    "IT-Grundschutz": [
        "BSI IT-Grundschutz catalogue: the authoritative control catalogue. Detections must cite specific catalogue reference (Baustein, Modul).",
        "Basisschutz vs Standardschutz vs erhöhter Schutz: three protection levels. Detections must scale with target level.",
        "Kernschutz (core protection): specific minimum-effort path. Detections on minimum compliance differ from standard.",
        "Interaction with BSI-KritisV: IT-Grundschutz supports KRITIS compliance but is broader.",
        "ISO 27001 auf Basis IT-Grundschutz: specific certification path combining both.",
    ],

    "BAIT/KAIT": [
        "BaFin scope: German Federal Financial Supervisory Authority.",
        "BAIT (banks) vs KAIT (insurers): similar framework, different sector.",
        "Incident reporting to BaFin: specific timelines.",
        "IT risk management integration: BAIT/KAIT emphasise integrated IT risk governance.",
        "DORA alignment: EU DORA now partially supersedes BAIT/KAIT. Detections should track the transition.",
    ],

    "HKMA TM-G-2": [
        "HKMA (Hong Kong Monetary Authority) scope: HK banks.",
        "GS-GS (General Supervision/Gazetted Supervision) distinctions.",
        "Cybersecurity Fortification Initiative (CFI): broader programme referenced by TM-G-2.",
        "iCAST (Intelligence-led Cyber Attack Simulation Testing): periodic testing expectation.",
        "Breach notification timelines specific to HKMA.",
    ],

    "NZISM": [
        "NZ Government scope: NZISM primary scope is NZ Government agencies.",
        "GCSB (Government Communications Security Bureau) coordination.",
        "Classification scheme: CONFIDENTIAL / SECRET / TOP SECRET. Detections must use NZ scheme.",
        "PROTECTIVE MARKING REQUIREMENTS: NZISM has specific marking rules.",
        "NZ Information Security Manual update cadence: detections must track latest NZISM version.",
    ],

    "CJIS": [
        "FBI CJIS scope: US criminal justice information. Applies to agencies accessing CJI.",
        "Advanced Authentication: specific CJIS AA requirements. Detections on auth must verify CJIS AA compliance.",
        "Incident response timelines: CJIS has specific IR expectations.",
        "Personnel Security: specific background check requirements.",
        "Encryption: FIPS 140-2 (soon -3) validated modules required for CJI.",
    ],

    "SAMA CSF": [
        "SAMA (Saudi Central Bank) scope: KSA banks and financial institutions.",
        "CSF vs PDPL distinction: CSF for cybersecurity, PDPL for personal data.",
        "Maturity levels: 4 maturity levels in SAMA CSF. Detections must target level.",
        "Third-party outsourcing: specific SAMA expectations.",
        "Reporting to SAMA: specific timelines and format.",
    ],

    "COSO": [
        "COSO Internal Control framework: 5 components, 17 principles.",
        "COSO ERM framework: distinct from Internal Control framework.",
        "Entity-level vs activity-level controls: detections must specify level.",
        "Control owner attestation: COSO expects attestation by control owner.",
        "SOX linkage: COSO is the most common framework underlying SOX ITGC.",
    ],

    "Cyber Essentials": [
        "UK scope: Cyber Essentials is a UK government scheme (IASME).",
        "CE vs CE Plus: Plus includes independent assessment.",
        "5 technical controls: firewalls, secure config, access control, malware protection, patch management. Detections must map to one of these.",
        "Annual recertification: detections support annual cycle.",
        "Common for UK Government supplier qualification.",
    ],

    "COBIT": [
        "COBIT 2019 framework: 40 governance and management objectives.",
        "Governance objectives (EDM) vs Management objectives (APO/BAI/DSS/MEA).",
        "Design factors: COBIT 2019 uses design factors to tailor the framework.",
        "Maturity levels: 0-5 capability/maturity assessment.",
        "Integration with other frameworks: COBIT often maps to ISO 27001, NIST.",
    ],

    "GLBA": [
        "FFIEC scope: US financial institutions.",
        "Safeguards Rule: 2023 amendments expanded technical requirements.",
        "Privacy Rule: separate from Safeguards, covers consumer data handling.",
        "Annual CISO report to Board: GLBA requires designated qualified individual's annual report.",
        "Incident notification: 30-day notification for events affecting 500+ customers (2023 update).",
    ],

    "HIPAA": "HIPAA Security",

    "HIPAA Privacy": [
        "Privacy Rule scope (45 CFR 164 Subpart E): distinct from Security Rule.",
        "Minimum necessary standard: applies to most uses/disclosures. Detections must consider minimum-necessary.",
        "Notice of Privacy Practices: must be provided at first service delivery. Detections on NPP distribution.",
        "Authorizations: specific uses require authorization. Detections on authorization tracking.",
        "Individual rights: access, amendment, accounting of disclosures. Detections on rights fulfilment.",
    ],

    "Basel III": [
        "BCBS (Basel Committee on Banking Supervision) scope: international banking.",
        "BCBS 239 (Principles for effective risk data aggregation): IT/data quality focus.",
        "Pillar 1/2/3 structure: detections must specify pillar.",
        "Liquidity Coverage Ratio (LCR) and NSFR: detections on data quality for these ratios.",
        "Local implementation varies: EU (CRD V), US (Dodd-Frank), UK (PRA) etc.",
    ],

    "COPPA": [
        "Under-13 scope: COPPA specifically for children under 13.",
        "Verifiable parental consent: required for personal information collection. Detections on consent capture.",
        "Safe Harbor programs: FTC-approved programs provide compliance assurance.",
        "$51,744 per violation (2024): maximum civil penalty. Detections on risk exposure.",
        "Recent updates (2024 proposed): anticipate rule changes.",
    ],

    "FERPA": [
        "US education records scope: FERPA applies to schools receiving federal funding.",
        "Student vs parent rights transition: at age 18 or post-secondary enrolment.",
        "Directory information: narrower than other PII regimes.",
        "School official exception: FERPA allows sharing with school officials having legitimate interest.",
        "Health records interaction: FERPA vs HIPAA boundary can be complex.",
    ],

    "UN R155": [
        "UN R155 scope: vehicle cybersecurity management system (CSMS) for type approval.",
        "OEM vs supplier responsibilities: detections differ.",
        "Lifecycle phases: R155 covers development, production, post-production.",
        "Type approval: detections supporting type approval evidence.",
        "Annex 5 threats: specific threat catalogue referenced.",
    ],

    "UN R156": [
        "UN R156 scope: software update management system (SUMS) for vehicles.",
        "Over-the-air (OTA) update specifics: R156 emphasises OTA.",
        "Vehicle identification: VIN-based tracking of update state.",
        "Rollback capability: R156 expects rollback support.",
        "Coordination with R155: R156 for software updates, R155 for broader cybersecurity.",
    ],

    "FERC CIP": [
        "FERC-approved CIP standards: reliability standards for bulk electric system.",
        "NERC coordination: FERC approves; NERC implements.",
        "Current CIP standards: CIP-002 through CIP-014. Detections must cite current version.",
        "High/Medium/Low impact: impact rating drives applicable CIP standards.",
        "Interactive remote access: CIP-005 specific attention.",
    ],

    "Swiss nFADP": [
        "FDPIC (Federal Data Protection and Information Commissioner) coordination.",
        "nFADP since Sep 2023: revised Swiss data protection law.",
        "High-risk data processing: similar to GDPR DPIA concept.",
        "Cross-border transfers: FDPIC list of adequate countries.",
        "Notification to FDPIC: specific timelines for breach.",
    ],
}


def resolve_wisdom_key(regulation: str) -> str:
    """Resolve variant spellings to the canonical key in REGULATION_WISDOM."""
    if regulation in REGULATION_WISDOM:
        v = REGULATION_WISDOM[regulation]
        if isinstance(v, str):
            return v  # follow alias
        return regulation
    # Fallback: case-insensitive + whitespace normalization
    norm = regulation.strip().upper().replace("  ", " ")
    for key in REGULATION_WISDOM.keys():
        if key.upper().strip() == norm:
            v = REGULATION_WISDOM[key]
            if isinstance(v, str):
                return v
            return key
    return ""


def get_wisdom(regulation: str) -> list[str]:
    """Return list of operational caveats for a regulation, or empty list."""
    key = resolve_wisdom_key(regulation)
    if not key:
        return []
    v = REGULATION_WISDOM.get(key, [])
    if isinstance(v, str):
        # follow alias one more time
        v = REGULATION_WISDOM.get(v, [])
    return v if isinstance(v, list) else []

