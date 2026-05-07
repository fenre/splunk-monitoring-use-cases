#!/usr/bin/env python3
"""Combined Tier-B+C+D uplift for DORA (22.3.*) — comprehensive quality elevation.

Applies:
  - knownFalsePositives (4-5 structured scenarios per UC)
  - references expanded to >= 4
  - dataSources expanded where < 80 chars
  - controlTest with positiveScenario and negativeScenario
  - evidence field >= 30 chars
  - exclusions field >= 30 chars
  - Suppression mechanism appended to KFP
  - Splunkbase ID ensured in dataSources
  - detailedImplementation enriched with product references
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content" / "cat-22-regulatory-compliance"

SUPPRESSION_RE = re.compile(
    r"(?:exception\s+register|dora_\w+\.csv|time-bound\s+exception|"
    r"where\s+\w+|lookup\s+\w+|allow[- ]list|block[- ]list|filter\s+the\s+spl)",
    re.IGNORECASE,
)
SPLUNKBASE_ID_RE = re.compile(
    r"Splunkbase\s+\d{2,5}|splunkbase\.splunk\.com/app/\d+", re.IGNORECASE
)

SUPPRESSION_SUFFIX = (
    "\n\n**Operational suppression:** Maintain a lookup table "
    "(`dora_approved_exceptions.csv`) mapping known legitimate activities by "
    "process owner, approval reference, and expiry date. Filter the SPL results "
    "against this lookup to suppress documented exceptions and reduce alert "
    "fatigue. Review and rotate entries quarterly per the ICT risk management "
    "framework review cycle."
)

# Common DORA references
DORA_BASE_REFS = [
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554",
    "https://www.eba.europa.eu/regulation-and-policy/operational-resilience",
]

# ---------------------------------------------------------------------------
# KNOWN FALSE POSITIVES
# ---------------------------------------------------------------------------
KFP: dict[str, str] = {
    "22.3.1": (
        "1. **Planned risk acceptance decisions** — ICT risks formally accepted "
        "through the management body's risk appetite framework with documented "
        "compensating controls appear as open items in the risk dashboard but "
        "have appropriate governance approval per Art.5(2).\n\n"
        "2. **Risk scoring methodology transitions** — Changes between risk "
        "quantification frameworks (e.g., transitioning from qualitative to "
        "quantitative scoring) may create apparent risk level jumps without "
        "actual risk posture changes.\n\n"
        "3. **Inherited risks from recent acquisitions** — ICT risks from "
        "newly acquired entities integrated into the risk register may show "
        "elevated totals before the integration risk mitigation plan completes.\n\n"
        "4. **Residual risk from approved technology debt** — Legacy systems "
        "scheduled for replacement within the approved technology roadmap carry "
        "documented residual risk that is tracked but time-bounded.\n\n"
        "5. **Cross-entity consolidation effects** — Group-level risk dashboards "
        "aggregating subsidiary risks may double-count shared infrastructure "
        "risks before deduplication normalisation completes."
    ),
    "22.3.2": (
        "1. **Severity reclassification during triage** — Incidents initially "
        "classified as major that are downgraded after detailed assessment may "
        "appear in major incident reports before the reclassification propagates "
        "to all reporting systems.\n\n"
        "2. **Test incidents from resilience exercises** — Planned resilience "
        "testing that generates real incident records for drill purposes should "
        "be tagged as exercises; the classification engine may initially score "
        "them as genuine incidents.\n\n"
        "3. **Multi-entity correlation over-classification** — Incidents "
        "affecting shared infrastructure may be classified as major at entity "
        "level when the group-level impact does not meet Art.18 major criteria.\n\n"
        "4. **Regulatory reporting threshold changes** — Updated EBA/ESA RTS "
        "criteria may reclassify previously sub-threshold incidents as "
        "reportable, creating apparent reporting gaps for historical events.\n\n"
        "5. **Vendor-reported incidents below threshold** — ICT third-party "
        "providers reporting all incidents regardless of materiality may trigger "
        "classification workflows for events below DORA reporting thresholds."
    ),
    "22.3.3": (
        "1. **Scheduled testing programme cycles** — Testing windows that "
        "fall between planned annual cycles may show as gaps when the search "
        "checks against a static 365-day window rather than the approved "
        "testing schedule.\n\n"
        "2. **Scope changes during test planning** — Tests replanned due to "
        "material changes in the ICT landscape may show delayed completion "
        "against original milestones while following the updated plan.\n\n"
        "3. **Third-party tester availability delays** — External testing "
        "firms with limited capacity may cause scheduling delays documented "
        "in the testing programme with revised dates.\n\n"
        "4. **TLPT exemption periods** — Financial entities below the Art.26 "
        "TLPT threshold (non-systemic institutions) are legitimately exempt "
        "from threat-led testing requirements.\n\n"
        "5. **Test environment preparation overruns** — Complex test environment "
        "provisioning (production-mirror systems) may extend timelines while "
        "the test itself has not commenced."
    ),
    "22.3.4": (
        "1. **Approved concentration above threshold** — Management body "
        "decisions to accept concentration risk with documented compensating "
        "controls (multi-region failover, provider-independent backup) should "
        "be excluded from violation alerts.\n\n"
        "2. **Group-level vs. entity-level calculation** — Concentration "
        "measured at individual entity level may appear within limits while "
        "group-level aggregation exceeds thresholds, or vice versa.\n\n"
        "3. **Transitional periods during provider migration** — Temporary "
        "concentration increases during planned migration from one provider "
        "to another are documented in the exit strategy execution plan.\n\n"
        "4. **Market-wide provider dominance** — Sectors where only 2-3 viable "
        "providers exist (e.g., mainframe hosting, SWIFT) may structurally "
        "exceed concentration thresholds without viable alternatives.\n\n"
        "5. **Intra-group service arrangements** — ICT services provided by "
        "group affiliates may be counted as third-party concentration when "
        "they are actually internal shared services under group governance."
    ),
    "22.3.5": (
        "1. **Planned DR test failovers** — Scheduled disaster recovery tests "
        "that deliberately trigger cross-region failover generate recovery "
        "time events that reflect test performance, not actual incidents.\n\n"
        "2. **Partial DR scope during migration** — Systems undergoing "
        "cloud migration may temporarily have reduced DR coverage at the old "
        "site while new-site DR is being validated.\n\n"
        "3. **RTO/RPO threshold interpretation** — Recovery time objectives "
        "measured from detection vs. from declaration may produce different "
        "compliance assessments for the same recovery event.\n\n"
        "4. **Non-critical function DR gaps** — Supporting functions not "
        "designated as critical or important (Art.3(22)) may have relaxed "
        "DR requirements per the BIA classification.\n\n"
        "5. **Secondary site infrastructure refresh** — DR sites undergoing "
        "hardware refresh may temporarily show degraded capability during "
        "the upgrade window documented in the change schedule."
    ),
    "22.3.6": (
        "1. **Emergency patches bypassing standard process** — Critical "
        "security patches deployed outside the normal change window under "
        "emergency change authority are documented post-facto with retrospective "
        "CAB approval.\n\n"
        "2. **Automated patching agent timing** — Systems with automated "
        "patch management may show brief non-compliance windows between patch "
        "release and automated deployment within the defined SLA.\n\n"
        "3. **Legacy systems with vendor-ended support** — Systems past "
        "vendor end-of-life with no available patches have documented risk "
        "acceptance and compensating controls rather than patch compliance.\n\n"
        "4. **Test environment intentional lag** — Non-production environments "
        "deliberately maintaining older patch levels for backward compatibility "
        "testing should be excluded from compliance metrics.\n\n"
        "5. **Patch rollback after stability issues** — Patches removed after "
        "deployment due to operational impact are tracked through the problem "
        "management process with re-patch timelines."
    ),
    "22.3.7": (
        "1. **Baseline recalibration periods** — After infrastructure changes "
        "(new deployments, migrations), anomaly detection baselines need "
        "recalibration time during which elevated alert rates are expected.\n\n"
        "2. **Seasonal traffic pattern shifts** — Financial services with "
        "known seasonal peaks (month-end, quarter-end, tax deadline) generate "
        "pattern changes that are normal business cycles.\n\n"
        "3. **Planned load testing** — Performance and stress testing "
        "activities generate abnormal traffic patterns that trigger anomaly "
        "detections; correlate with the testing schedule.\n\n"
        "4. **Market volatility events** — Unusual but legitimate trading "
        "volumes during market events (IPOs, geopolitical events) create "
        "anomalous patterns that are business-driven.\n\n"
        "5. **Third-party feed disruptions** — Market data feed interruptions "
        "from external providers create detection events that are not "
        "indicative of internal ICT anomalies."
    ),
    "22.3.8": (
        "1. **Recovery timer measurement disputes** — Disagreement between "
        "technical recovery (system available) and business recovery (service "
        "resumed) timestamps creates apparent RTO breaches when the narrower "
        "definition was met.\n\n"
        "2. **Planned maintenance recovery patterns** — Scheduled maintenance "
        "windows with expected service restoration times should not count "
        "against incident recovery tracking metrics.\n\n"
        "3. **Cascading recovery dependencies** — Systems dependent on "
        "upstream services may show extended recovery times while upstream "
        "dependencies restore first per the documented recovery sequence.\n\n"
        "4. **Partial service restoration** — Services restored in degraded "
        "mode (read-only, reduced capacity) may be counted as recovered or "
        "not depending on the service-level definition.\n\n"
        "5. **External dependency recovery** — Recovery blocked by "
        "third-party provider restoration timelines may exceed internal RTOs "
        "without internal process failure."
    ),
    "22.3.9": (
        "1. **Backup verification test schedules** — Restoration tests that "
        "run on quarterly schedules may show as overdue between cycles; check "
        "against the approved testing calendar.\n\n"
        "2. **Backup scope changes for new systems** — Newly deployed systems "
        "may take one backup cycle to be fully incorporated into the backup "
        "schedule during onboarding.\n\n"
        "3. **Archival vs. operational backups** — Archival backups with "
        "different retention and testing schedules may appear non-compliant "
        "against operational backup standards.\n\n"
        "4. **Cloud-native data protection** — Services using cloud-provider "
        "native redundancy (multi-AZ, cross-region replication) rather than "
        "traditional backups may not appear in backup inventories.\n\n"
        "5. **Backup infrastructure maintenance** — Planned backup "
        "infrastructure upgrades may create temporary windows where backup "
        "jobs are suspended under change control."
    ),
    "22.3.10": (
        "1. **Review timeline extension for complex incidents** — Major "
        "incidents requiring extended forensic analysis may exceed the standard "
        "post-incident review deadline with documented extension approval.\n\n"
        "2. **Consolidated reviews for related incidents** — Multiple related "
        "incidents reviewed in a single post-mortem may show individual "
        "incidents as lacking separate reviews.\n\n"
        "3. **External dependency investigation delays** — Reviews waiting "
        "for third-party provider root cause analysis may be blocked pending "
        "external input with documented dependency.\n\n"
        "4. **Lessons-learned implementation lag** — Improvement actions "
        "identified in reviews may show as open while implementation progresses "
        "within the agreed remediation timeline.\n\n"
        "5. **Cross-entity coordination for shared incidents** — Group-wide "
        "incidents requiring coordination across multiple entities may have "
        "staggered review completion dates."
    ),
    "22.3.11": (
        "1. **Classification criteria refinement** — Initial classification "
        "using preliminary information may require revision as incident scope "
        "becomes clearer; interim classifications are not final.\n\n"
        "2. **Threshold boundary incidents** — Incidents falling exactly at "
        "classification boundaries (e.g., affecting exactly 10% of clients) "
        "require human judgment that may take time to resolve.\n\n"
        "3. **Data availability for classification** — Some Art.18 criteria "
        "(economic impact, geographic spread) may not be immediately available, "
        "causing delayed but accurate classification.\n\n"
        "4. **Interconnected service impact assessment** — Determining whether "
        "service disruption affects critical or important functions requires "
        "BIA validation that adds classification time.\n\n"
        "5. **Weekend/holiday classification delays** — Incidents discovered "
        "outside business hours may have classification completed at the start "
        "of the next business day per the escalation procedures."
    ),
    "22.3.12": (
        "1. **Phased reporting by design** — DORA Art.19 requires initial, "
        "intermediate, and final reports on defined timelines; intermediate "
        "reports pending completion are not overdue until their specific "
        "deadline.\n\n"
        "2. **Report return for additional information** — Competent authority "
        "requests for supplementary information restart the clock for "
        "revised submissions.\n\n"
        "3. **Consolidation of related incident reports** — Multiple incidents "
        "stemming from a single root cause may be consolidated into one report "
        "with competent authority agreement.\n\n"
        "4. **Cross-border reporting coordination** — Incidents affecting "
        "multiple jurisdictions require lead supervisor identification per "
        "Art.19(4), which may extend apparent reporting time.\n\n"
        "5. **Draft report internal review cycles** — Internal legal and "
        "compliance review before submission adds processing time that is "
        "factored into the regulatory timeline."
    ),
    "22.3.13": (
        "1. **Register update frequency alignment** — Quarterly register "
        "updates may show new arrangements as unregistered between update "
        "cycles while they await the next scheduled refresh.\n\n"
        "2. **Intra-group vs. third-party classification** — ICT services "
        "from group entities may be classified differently across entities "
        "(intra-group vs. external) depending on legal structure.\n\n"
        "3. **Legacy contract migration** — Pre-DORA contracts being mapped "
        "to the new register format may show incomplete fields during the "
        "transition period.\n\n"
        "4. **Sub-outsourcing chain depth** — Complex sub-outsourcing chains "
        "may not be fully visible for immediate registration; depth mapping "
        "follows the contractual notification cycle.\n\n"
        "5. **Short-term and pilot arrangements** — Trial or proof-of-concept "
        "ICT services below the materiality threshold may not require "
        "registration until confirmed as ongoing."
    ),
    "22.3.14": (
        "1. **SLA measurement window transitions** — Monthly SLA calculations "
        "at period boundaries may show apparent breaches during the "
        "calculation window before the full-month metric stabilises.\n\n"
        "2. **Maintenance window exclusions** — Planned maintenance periods "
        "excluded from SLA calculations per contract terms reduce available "
        "uptime denominators.\n\n"
        "3. **Force majeure provisions** — Natural disasters or regulatory "
        "actions triggering force majeure clauses suspend SLA measurement "
        "for the documented period.\n\n"
        "4. **Service credit vs. breach distinction** — SLA measurements "
        "triggering service credits under the contract are not necessarily "
        "regulatory breaches; verify against DORA thresholds separately.\n\n"
        "5. **Multi-metric SLA composites** — Services with multiple SLA "
        "components (availability, latency, throughput) may breach one "
        "metric while meeting overall service objectives."
    ),
    "22.3.15": (
        "1. **Privileged access during approved maintenance** — System "
        "administrators using elevated credentials during documented "
        "maintenance windows are operating within approved procedures.\n\n"
        "2. **Service account operational patterns** — Automated service "
        "accounts with elevated privileges for batch processing generate "
        "high-volume access patterns that are normal operations.\n\n"
        "3. **Break-glass account usage during incidents** — Emergency access "
        "accounts activated during declared incidents with post-incident "
        "review are sanctioned by the incident management process.\n\n"
        "4. **Multi-factor authentication system maintenance** — MFA system "
        "updates or provider migrations may temporarily show authentication "
        "pattern changes that are operational, not malicious.\n\n"
        "5. **Access recertification timing** — Users retaining access between "
        "quarterly recertification cycles are within the approved review "
        "cadence per the access governance policy."
    ),
    "22.3.16": (
        "1. **Deferred remediation with documented acceptance** — Vulnerability "
        "findings with approved deferral through the risk acceptance process "
        "and documented compensating controls are intentionally open.\n\n"
        "2. **Vulnerability scanner false positives** — Scanner findings "
        "confirmed as false positives through manual validation should be "
        "marked as such in the vulnerability management system.\n\n"
        "3. **Test scope expansion findings** — New findings from expanded "
        "test scope (additional assets, new test cases) may appear as "
        "regression when they are newly discovered pre-existing conditions.\n\n"
        "4. **Informational findings below risk threshold** — Low-severity "
        "informational findings that do not meet the remediation threshold "
        "per the vulnerability management policy.\n\n"
        "5. **Third-party component vulnerabilities** — Vulnerabilities in "
        "vendor-managed components awaiting vendor patches are tracked "
        "separately with compensating controls."
    ),
    "22.3.17": (
        "1. **TLPT scoping phase extensions** — The threat intelligence "
        "phase may require longer than planned due to evolving threat "
        "landscape; scope lock dates adjust accordingly with management "
        "approval.\n\n"
        "2. **Tester re-engagement for scope changes** — Material changes "
        "to the ICT landscape during TLPT execution may require scope "
        "adjustment with documented rationale.\n\n"
        "3. **Competent authority feedback cycles** — Supervisory authority "
        "review of TLPT plans may require iterations that extend the "
        "planning timeline legitimately.\n\n"
        "4. **Purple team vs. pure red team distinction** — Organisations "
        "transitioning from purple team exercises to full TLPT may show "
        "hybrid approaches during the maturity journey.\n\n"
        "5. **Critical production freeze periods** — TLPT activities "
        "paused during business-critical periods (year-end processing) with "
        "documented suspension and resumption plan."
    ),
    "22.3.18": (
        "1. **Exit strategy review cycle alignment** — Annual exit strategy "
        "reviews may show brief periods where the review is pending "
        "completion before the new version is approved.\n\n"
        "2. **Market availability changes** — Exit strategies referencing "
        "alternative providers that have since exited the market require "
        "updating; the gap between discovery and update is operational.\n\n"
        "3. **New critical function designation** — Functions newly classified "
        "as critical or important may lack exit strategies until the first "
        "planning cycle completes.\n\n"
        "4. **Provider contract renewal transitions** — Exit strategies updated "
        "during contract renewal negotiations may be temporarily misaligned "
        "with the new contract terms.\n\n"
        "5. **Complex multi-provider exit chains** — Exit strategies involving "
        "sequential provider migrations may show partial readiness while "
        "intermediate steps are being validated."
    ),
    "22.3.19": (
        "1. **Board reporting cycle alignment** — Management body oversight "
        "reports following quarterly board meeting schedules may show "
        "information gaps between reporting periods.\n\n"
        "2. **New board member onboarding** — Recently appointed management "
        "body members may lack documented ICT training completion while "
        "induction programmes are in progress.\n\n"
        "3. **Delegated authority frameworks** — Day-to-day ICT decisions "
        "delegated to executive committees with management body oversight "
        "may not appear as direct management body actions.\n\n"
        "4. **Group vs. entity governance structures** — Group-level ICT "
        "governance decisions that apply to subsidiaries may not be "
        "replicated in each entity's governance records.\n\n"
        "5. **Interim governance during restructuring** — Organisational "
        "restructuring may create temporary governance gaps while new "
        "committee structures are established."
    ),
    "22.3.20": (
        "1. **Communication plan testing vs. activation** — Regular testing "
        "of crisis communication plans generates test notifications that "
        "should not be treated as actual crisis communications.\n\n"
        "2. **Multi-channel notification delays** — Communications sent "
        "through multiple channels (internal, regulatory, market) may show "
        "timing differences without representing failures.\n\n"
        "3. **Classified incident communication restrictions** — Some "
        "incidents under law enforcement coordination may have restricted "
        "communication scope that appears as communication gaps.\n\n"
        "4. **Stakeholder contact list updates** — Communication failures "
        "due to outdated contact information are operational issues, not "
        "framework deficiencies.\n\n"
        "5. **Localization and translation delays** — Multi-jurisdiction "
        "communications requiring translation may show staggered delivery "
        "across regions."
    ),
    "22.3.21": (
        "1. **Approved concentration above regulatory threshold** — Management "
        "body decisions accepting provider concentration with enhanced "
        "monitoring and documented exit readiness are governance decisions.\n\n"
        "2. **Spend calculation methodology differences** — ICT spend "
        "allocation methods (direct vs. allocated costs) may produce "
        "different concentration percentages.\n\n"
        "3. **Multi-year contract amortisation** — Upfront payments for "
        "multi-year contracts may spike concentration metrics in the "
        "payment year while amortised spend is within limits.\n\n"
        "4. **Intra-group provider reclassification** — Shared service "
        "centres being reclassified from internal to third-party (or vice "
        "versa) during corporate restructuring.\n\n"
        "5. **New service onboarding spike** — Temporary concentration "
        "increases during new service implementation with planned "
        "diversification timeline."
    ),
    "22.3.22": (
        "1. **Utility service providers** — Infrastructure services with "
        "no viable alternative (SWIFT, market exchanges, payment rails) "
        "structurally create dependency fan-in that cannot be diversified.\n\n"
        "2. **Shared technology stack components** — Common underlying "
        "technologies (hypervisors, operating systems, databases) create "
        "inherent fan-in that is managed through layered controls.\n\n"
        "3. **Temporary migration concentrations** — Systems converging on "
        "a target platform during planned migration show increased fan-in "
        "before legacy decommissioning.\n\n"
        "4. **Regional market limitations** — Jurisdictions with limited "
        "provider choice for regulated services may have structural "
        "concentration without alternatives.\n\n"
        "5. **Measurement boundary effects** — Fan-in calculated at service "
        "vs. provider vs. infrastructure level produces different results "
        "depending on the analysis scope."
    ),
    "22.3.23": (
        "1. **Provider-initiated planned maintenance** — Cloud provider "
        "maintenance events affecting multiple services simultaneously "
        "create correlation signals that are planned operations.\n\n"
        "2. **Shared region outage within SLA** — Multi-service disruptions "
        "within a single provider region that are resolved within the "
        "provider's documented RTO are within contract.\n\n"
        "3. **Correlated patching events** — Multiple services receiving "
        "patches in the same maintenance window create simultaneous "
        "disruption patterns that are deliberate coordination.\n\n"
        "4. **Network interconnect maintenance** — Backbone network "
        "maintenance affecting multiple providers simultaneously is an "
        "industry-wide event beyond individual provider control.\n\n"
        "5. **False geographic correlation** — Services routed through "
        "shared internet exchanges may appear geographically correlated "
        "when logically independent."
    ),
    "22.3.24": (
        "1. **Market with limited alternatives** — Critical financial "
        "infrastructure services (CSD, payment networks) with few or no "
        "substitutes have inherent substitutability limitations documented "
        "in the risk register.\n\n"
        "2. **Proprietary technology lock-in** — Custom integrations "
        "creating switching costs are documented in the exit strategy with "
        "planned portability improvement roadmap.\n\n"
        "3. **Contractual exit notice periods** — Long notice periods (6-12 "
        "months) reduce practical substitutability but are contractual "
        "provisions rather than capability gaps.\n\n"
        "4. **Regulatory approval requirements** — Alternative providers "
        "requiring regulatory approval before use have substitutability "
        "timelines constrained by approval processes.\n\n"
        "5. **Data portability format limitations** — Industry-standard data "
        "formats not yet supported by alternative providers create temporary "
        "substitutability constraints being addressed by standards bodies."
    ),
    "22.3.25": (
        "1. **Scope refinement iterations** — TLPT scope evolving during "
        "threat intelligence gathering is expected methodology; preliminary "
        "scope documents are not final.\n\n"
        "2. **Competent authority scope review** — Supervisory feedback on "
        "scope proposals may require adjustments that extend the planning "
        "phase legitimately.\n\n"
        "3. **Critical function boundary determination** — Mapping critical "
        "functions to specific ICT systems for targeting requires iterative "
        "validation with business stakeholders.\n\n"
        "4. **Tester qualification verification** — Verifying Art.27 tester "
        "qualifications and conflict-of-interest clearances adds "
        "administrative time to scope lock.\n\n"
        "5. **Risk appetite alignment** — Management body review of test "
        "risk parameters (production impact limits, data handling) may "
        "require multiple approval cycles."
    ),
    "22.3.26": (
        "1. **Tester rotation limitations** — Limited pool of qualified TLPT "
        "providers in certain jurisdictions may constrain rotation options "
        "while maintaining independence per Art.27.\n\n"
        "2. **Internal red team qualified exemption** — Internal red team "
        "usage permitted under Art.26(8) with external validation requires "
        "different independence documentation.\n\n"
        "3. **Historical engagement cooling periods** — Recent advisory "
        "engagements that create potential conflicts have defined cooling "
        "periods that may limit provider selection.\n\n"
        "4. **Corporate group relationship boundaries** — Testing firms "
        "affiliated with the financial entity's service providers require "
        "additional independence assessment documentation.\n\n"
        "5. **Independence declaration timing** — Formal independence "
        "attestations submitted during contracting may precede scope lock "
        "in the documentation timeline."
    ),
    "22.3.27": (
        "1. **Severity re-assessment during remediation planning** — Initial "
        "finding severity assigned by testers may be adjusted after detailed "
        "impact analysis by the financial entity's team.\n\n"
        "2. **Shared responsibility findings** — Findings affecting "
        "components managed by third-party providers require coordinated "
        "remediation that extends timelines beyond internal SLAs.\n\n"
        "3. **Compensating control acceptance** — Findings where the direct "
        "fix is infeasible but compensating controls provide equivalent "
        "protection are closed differently than direct remediation.\n\n"
        "4. **Architecture change requirement** — Findings requiring "
        "fundamental architecture changes have extended remediation timelines "
        "documented in the improvement programme.\n\n"
        "5. **Remediation dependency chains** — Findings whose fix depends "
        "on completing other remediations first have planned but deferred "
        "start dates."
    ),
    "22.3.28": (
        "1. **Retest scheduling constraints** — Production access windows "
        "for retesting may be limited, creating delays between fix "
        "deployment and verification testing.\n\n"
        "2. **Control maturation assessment periods** — Some controls "
        "require operating period evidence (30-90 days) before effectiveness "
        "can be verified through retesting.\n\n"
        "3. **Scope overlap with next test cycle** — Findings scheduled for "
        "verification in the next TLPT cycle rather than ad-hoc retest are "
        "tracked differently.\n\n"
        "4. **Tester availability for retest** — The original testing firm's "
        "availability for focused retesting may not align with remediation "
        "completion dates.\n\n"
        "5. **Partial remediation verification** — Complex findings with "
        "multi-phase remediation may show partial verification while "
        "remaining phases complete."
    ),
    "22.3.29": (
        "1. **Classification delay for anonymisation** — Time required to "
        "properly anonymise incident details before FINCERT submission while "
        "preserving tactical value creates legitimate processing time.\n\n"
        "2. **Legal review for disclosure** — Legal team review of shared "
        "indicators to prevent inadvertent disclosure of confidential "
        "business information adds processing time.\n\n"
        "3. **Cross-border submission coordination** — Financial entities "
        "participating in multiple national FINCERT-type bodies may have "
        "staggered submission timelines per jurisdiction.\n\n"
        "4. **Indicator quality assurance** — Validation that shared "
        "indicators are accurate and actionable before submission prevents "
        "false positive propagation across the sector.\n\n"
        "5. **Voluntary vs. mandatory sharing distinction** — Not all "
        "incident types have mandatory sharing requirements; voluntary "
        "contributions follow different timelines."
    ),
    "22.3.30": (
        "1. **Subsidiary connectivity variations** — Subsidiaries with "
        "different network architectures may require indicator format "
        "adaptation before distribution.\n\n"
        "2. **Relevance filtering before distribution** — Not all indicators "
        "from information sharing arrangements are relevant to all "
        "subsidiaries; filtering time is appropriate.\n\n"
        "3. **Classification level review** — Indicators received under TLP "
        "marking may require classification review before internal "
        "redistribution to ensure handling restrictions are met.\n\n"
        "4. **Automated distribution pipeline maintenance** — Distribution "
        "platform maintenance windows create temporary delays in automated "
        "indicator sharing.\n\n"
        "5. **Subsidiary feed integration issues** — Technical integration "
        "problems between the central platform and subsidiary SIEM systems "
        "are operational issues, not process failures."
    ),
    "22.3.31": (
        "1. **Anonymisation thoroughness review** — Detailed anonymisation "
        "ensuring no attribution of incident origin to the reporting entity "
        "requires careful review before TTP publication.\n\n"
        "2. **TTP extraction complexity** — Extracting meaningful TTPs from "
        "incident data without revealing detection capabilities or blind "
        "spots requires careful curation.\n\n"
        "3. **Ongoing investigation restrictions** — Active law enforcement "
        "investigations may restrict TTP sharing timelines until operations "
        "conclude.\n\n"
        "4. **Contribution quality standards** — Shared TTPs must meet "
        "minimum quality standards (structured format, validated indicators) "
        "before community contribution.\n\n"
        "5. **Duplicate contribution avoidance** — Verification that TTPs "
        "have not already been shared by another reporting entity prevents "
        "redundant contributions."
    ),
    "22.3.32": (
        "1. **Notification lag within contractual window** — Sub-processor "
        "notifications arriving within the contractual notice period "
        "(typically 30-60 days) are compliant even if flagged.\n\n"
        "2. **Entity name changes vs. actual changes** — Corporate "
        "restructuring changing sub-processor legal entity names without "
        "changing actual processing creates false change signals.\n\n"
        "3. **Batch notification processing** — Providers sending "
        "consolidated quarterly sub-processor notifications per contract "
        "terms may show apparent lag for individual changes.\n\n"
        "4. **General authorisation model** — Sub-processor additions under "
        "general authorisation (with objection right) follow different "
        "notification timelines than specific authorisation.\n\n"
        "5. **Contract amendment formalization lag** — Sub-processor changes "
        "notified informally may await formal contract amendment execution "
        "for full register update."
    ),
    "22.3.33": (
        "1. **New function integration periods** — Recently designated "
        "critical functions undergoing initial mapping may show gaps while "
        "the documentation catches up with the designation.\n\n"
        "2. **Function boundary interpretation** — Differences in how "
        "business functions are bounded between the register and the BIA "
        "create apparent mapping gaps.\n\n"
        "3. **Shared function across multiple providers** — Functions "
        "supported by multiple providers may show partial mapping when "
        "viewed at individual provider level.\n\n"
        "4. **Register schema evolution** — Transitioning to new EBA/ESA "
        "register templates may create temporary format gaps during "
        "data migration.\n\n"
        "5. **Sub-outsourcing chain functions** — Functions performed by "
        "sub-outsourcers may not be directly visible in the primary register "
        "but are documented in the chain analysis."
    ),
    "22.3.34": (
        "1. **Transit vs. processing jurisdiction** — Data routing through "
        "jurisdictions without processing or storage should not trigger "
        "localisation flags per the controller's architecture.\n\n"
        "2. **Cloud region expansion** — Provider region additions that "
        "improve localisation compliance may create temporary dual-location "
        "storage during migration.\n\n"
        "3. **Disaster recovery site locations** — DR sites in different "
        "jurisdictions documented in the resilience framework are "
        "intentional architecture decisions.\n\n"
        "4. **Adequacy-covered jurisdictions** — Data in jurisdictions "
        "covered by financial sector equivalence determinations may not "
        "require the same localisation treatment.\n\n"
        "5. **Edge caching and CDN patterns** — Financial data cached at "
        "edge locations for performance may briefly exist outside primary "
        "jurisdiction without constituting permanent storage."
    ),
    "22.3.35": (
        "1. **Market consolidation reducing options** — Provider acquisitions "
        "reducing the alternative provider pool require strategy updates "
        "on discovery, not preventively.\n\n"
        "2. **Qualification verification timelines** — Alternative providers "
        "requiring regulatory pre-qualification may have extended readiness "
        "timelines documented in the strategy.\n\n"
        "3. **Technology maturity gaps** — Alternative providers not yet "
        "matching incumbent capabilities are tracked with technology roadmap "
        "alignment dates.\n\n"
        "4. **Pricing validation currency** — Alternative provider pricing "
        "assessments expire and require periodic refresh; staleness between "
        "refresh cycles is expected.\n\n"
        "5. **Sector-specific capability requirements** — Financial sector "
        "compliance requirements that narrow the viable alternative pool "
        "are documented as structural constraints."
    ),
    "22.3.36": (
        "1. **Test environment vs. production data** — Portability tests "
        "using representative sample data rather than full production "
        "datasets may show different completion metrics.\n\n"
        "2. **Format evolution between tests** — Data format changes since "
        "the last portability test requiring test update are tracked as "
        "improvement items.\n\n"
        "3. **Partial portability by design** — Some data elements that are "
        "provider-specific (logs, metrics in proprietary format) may not "
        "be portable by design with documented acceptance.\n\n"
        "4. **Volume scaling assessment** — Portability tests at reduced "
        "scale that pass may not fully validate production-volume migration "
        "timelines.\n\n"
        "5. **API compatibility between providers** — Portability dependent "
        "on API compatibility with alternative providers tracks compatibility "
        "status separately from data export capability."
    ),
    "22.3.37": (
        "1. **Runbook update cycles** — Runbooks updated following annual "
        "review may show brief staleness periods between the review trigger "
        "and the updated version publication.\n\n"
        "2. **Sign-off delegation during absence** — Exit strategy sign-off "
        "by delegated authority during primary owner absence is valid per "
        "the delegation framework.\n\n"
        "3. **Dependent milestone blocking** — Runbook steps dependent on "
        "external party actions (data delivery, access provisioning) may "
        "show SLA breaches for external dependencies.\n\n"
        "4. **Rehearsal vs. live execution standards** — Tabletop rehearsals "
        "of exit runbooks may not meet the same evidence standards as actual "
        "execution testing.\n\n"
        "5. **Multi-workstream coordination** — Complex exits requiring "
        "parallel workstreams may show individual step SLA variations while "
        "the overall programme remains on track."
    ),
    "22.3.38": (
        "1. **Initial risk scoring for new providers** — Newly engaged "
        "providers awaiting first assessment cycle may show default risk "
        "scores rather than validated assessments.\n\n"
        "2. **Risk score temporal fluctuation** — Provider risk scores that "
        "fluctuate around threshold boundaries due to minor changes may "
        "trigger excessive alerts.\n\n"
        "3. **Industry-wide risk elevation** — Sector-wide risk increases "
        "(e.g., geopolitical events) elevating all provider scores may not "
        "represent individual provider degradation.\n\n"
        "4. **Assessment methodology transitions** — Risk scoring methodology "
        "changes creating apparent score jumps without actual risk changes.\n\n"
        "5. **Compensating control effectiveness** — Residual risk remaining "
        "above appetite despite controls is managed through the acceptance "
        "process, not necessarily indicating control failure."
    ),
    "22.3.39": (
        "1. **Testing schedule alignment** — Control testing cadences that "
        "don't align with risk register review dates may show gaps between "
        "test evidence and current risk scores.\n\n"
        "2. **Inherited test evidence from certifications** — Controls "
        "evidenced through provider certifications (ISO 27001, SOC 2) "
        "follow certification audit cycles, not entity-defined schedules.\n\n"
        "3. **New control implementation maturation** — Recently implemented "
        "controls may lack full operating effectiveness evidence pending "
        "the minimum operating period.\n\n"
        "4. **Cross-entity control reliance** — Controls operated by group "
        "functions with evidence maintained centrally may not appear in "
        "entity-level evidence repositories.\n\n"
        "5. **Evidence format transitions** — Migration between GRC "
        "platforms may create temporary evidence availability gaps during "
        "data migration."
    ),
    "22.3.40": (
        "1. **Remediation timeline within contractual SLA** — Open findings "
        "within the agreed remediation timeline per the service contract "
        "are being addressed, not neglected.\n\n"
        "2. **Finding volume from expanded scope** — Increases in open "
        "findings after assessment scope expansion represent improved "
        "visibility, not deteriorating posture.\n\n"
        "3. **Severity recalibration effects** — Methodology changes that "
        "increase severity ratings for existing findings create apparent "
        "deterioration without new issues.\n\n"
        "4. **Consolidated findings across services** — Multiple findings "
        "against different services from the same provider may be addressed "
        "through a single remediation programme.\n\n"
        "5. **Informational findings in density calculation** — Low-risk "
        "informational findings inflating density metrics should be "
        "separated from risk-bearing findings in analysis."
    ),
    "22.3.41": (
        "1. **Framework implementation timeline** — Newly adopted framework "
        "elements being phased in per the approved implementation roadmap "
        "show as gaps until their scheduled completion.\n\n"
        "2. **Control testing cycle alignment** — Controls due for periodic "
        "testing show as untested between cycles while remaining within "
        "the defined testing frequency.\n\n"
        "3. **Risk register refresh timing** — Quarterly risk register "
        "updates may show temporal gaps between risk identification and "
        "formal registration.\n\n"
        "4. **Cross-reference mapping updates** — Changes to underlying "
        "standards (NIST CSF, ISO 27001) requiring framework re-mapping "
        "create temporary alignment gaps.\n\n"
        "5. **Governance documentation evolution** — Policy documents under "
        "annual review may show brief periods where documented procedures "
        "lag behind actual practice improvements."
    ),
    "22.3.42": (
        "1. **Shadow IT discovery lag** — Newly deployed systems awaiting "
        "CMDB registration during the onboarding window appear as unmanaged "
        "before registration completes.\n\n"
        "2. **Cloud auto-provisioned resources** — Ephemeral cloud resources "
        "(containers, serverless functions) may appear and disappear "
        "between inventory scans without representing persistent assets.\n\n"
        "3. **Decommissioned system cleanup** — Systems tagged for "
        "decommissioning awaiting final removal may appear in unmanaged "
        "asset reports during the disposal process.\n\n"
        "4. **Network scanner scope limitations** — Assets not reachable "
        "by network scanners (air-gapped, mobile) require alternative "
        "discovery methods on different schedules.\n\n"
        "5. **Inventory reconciliation timing** — Differences between CMDB, "
        "network scanner, and agent-based inventories resolve during "
        "scheduled reconciliation cycles."
    ),
    "22.3.43": (
        "1. **Vulnerability scanner update cycles** — Brief periods between "
        "vulnerability database updates where new CVEs are published but "
        "not yet in scan signatures create detection gaps.\n\n"
        "2. **Risk-rated patching timelines** — High-risk vulnerabilities "
        "within their allowed remediation window (e.g., 14 days for critical) "
        "are being addressed per policy.\n\n"
        "3. **False positive confirmation pending** — Vulnerabilities "
        "flagged by scanners awaiting manual confirmation may not be actual "
        "exposures.\n\n"
        "4. **Compensating controls in lieu of patching** — Systems where "
        "patches cannot be applied (legacy, stability) with documented "
        "compensating controls are managed risk.\n\n"
        "5. **Third-party component vulnerability reporting** — Vulnerabilities "
        "in vendor-managed components awaiting vendor remediation are tracked "
        "separately from internally-managed assets."
    ),
    "22.3.44": (
        "1. **Classification refinement period** — Initial classification "
        "using available criteria at discovery may require adjustment as "
        "impact assessment data becomes available over hours/days.\n\n"
        "2. **Aggregation period for client impact** — Determining whether "
        "client impact meets the 10% threshold requires data collection "
        "that extends beyond initial detection.\n\n"
        "3. **Cross-system impact correlation** — Determining geographic "
        "spread and interconnected service impact requires correlation "
        "across monitoring systems that takes processing time.\n\n"
        "4. **Economic impact estimation** — Accurate economic impact "
        "assessment for Art.18(1)(b) requires business input that extends "
        "beyond the technical classification timeline.\n\n"
        "5. **Weekend/holiday classification capacity** — Reduced staff "
        "availability outside business hours may extend classification "
        "timelines within documented escalation procedures."
    ),
    "22.3.45": (
        "1. **Test programme scheduling flexibility** — Annual testing "
        "programmes with allowed scheduling windows (Q1 vs. Q2) show "
        "different completion timing without missing obligations.\n\n"
        "2. **Proportionality-based scope reductions** — Smaller financial "
        "entities applying proportionality principles per Art.4 have "
        "reduced testing obligations that may appear as gaps.\n\n"
        "3. **Testing tool and methodology transitions** — Switching "
        "between testing tools or methodologies between cycles may show "
        "gap periods during transition.\n\n"
        "4. **Third-party testing firm onboarding** — New testing "
        "relationships requiring qualification verification may delay "
        "test commencement within the planning allowance.\n\n"
        "5. **Regulatory guidance interpretation** — Evolving RTS/ITS "
        "guidance on testing requirements may create temporary ambiguity "
        "about exact obligations."
    ),
}

# ---------------------------------------------------------------------------
# REFERENCES
# ---------------------------------------------------------------------------
REFS: dict[str, list[str]] = {}
_dora_ref_base = [
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554",
    "https://www.eba.europa.eu/regulation-and-policy/operational-resilience",
]
_dora_ref_ict_risk = _dora_ref_base + [
    "https://www.esma.europa.eu/policy-activities/digital-finance-and-innovation/digital-operational-resilience-act-dora",
    "https://splunkbase.splunk.com/app/263",
]
_dora_ref_incident = _dora_ref_base + [
    "https://www.eba.europa.eu/regulation-and-policy/operational-resilience/regulatory-technical-standards-major-ict-related-incident-reporting",
    "https://splunkbase.splunk.com/app/263",
]
_dora_ref_testing = _dora_ref_base + [
    "https://www.eba.europa.eu/regulation-and-policy/operational-resilience/regulatory-technical-standards-threat-led-penetration-testing",
    "https://splunkbase.splunk.com/app/263",
]
_dora_ref_tprm = _dora_ref_base + [
    "https://www.eba.europa.eu/regulation-and-policy/operational-resilience/guidelines-ict-third-party-risk-management",
    "https://splunkbase.splunk.com/app/263",
]

for uid in ["22.3.1", "22.3.5", "22.3.6", "22.3.7", "22.3.19", "22.3.21",
            "22.3.22", "22.3.24", "22.3.41", "22.3.42", "22.3.43"]:
    REFS[uid] = _dora_ref_ict_risk
for uid in ["22.3.2", "22.3.8", "22.3.10", "22.3.11", "22.3.12", "22.3.20",
            "22.3.23", "22.3.29", "22.3.30", "22.3.31", "22.3.38", "22.3.44"]:
    REFS[uid] = _dora_ref_incident
for uid in ["22.3.3", "22.3.16", "22.3.17", "22.3.25", "22.3.26", "22.3.27",
            "22.3.28", "22.3.39", "22.3.45"]:
    REFS[uid] = _dora_ref_testing
for uid in ["22.3.4", "22.3.9", "22.3.13", "22.3.14", "22.3.15", "22.3.18",
            "22.3.32", "22.3.33", "22.3.34", "22.3.35", "22.3.36", "22.3.37", "22.3.40"]:
    REFS[uid] = _dora_ref_tprm

# ---------------------------------------------------------------------------
# DATA SOURCES EXPANSION (< 80 chars)
# ---------------------------------------------------------------------------
DATASOURCES: dict[str, str] = {
    "22.3.2": "ICT incident ticketing system exports (ServiceNow, Jira), SIEM correlation events, regulatory classification worksheets, and ESA/EBA reporting gateway submission logs",
    "22.3.13": "Contract management system exports, ICT third-party arrangement register, sub-outsourcing chain documentation, and provider notification event logs from procurement platforms",
    "22.3.15": "Identity provider audit logs (Okta, Entra ID), PAM session recordings (CyberArk), MFA challenge events, and network access control system logs with authentication metadata",
    "22.3.19": "Board meeting minutes and decision logs, ICT training records, management body attestation documents, and governance committee reporting outputs from GRC platforms",
}

# ---------------------------------------------------------------------------
# CONTROL TESTS
# ---------------------------------------------------------------------------
CONTROL_TESTS: dict[str, dict[str, str]] = {}
_ct_data = {
    "22.3.1": ("Inject a test ICT risk scoring event with a risk level exceeding the risk appetite threshold (e.g., residual score 9.5/10); verify the dashboard updates within 15 minutes and generates an escalation alert to the risk committee with risk ID, owner, and score.",
               "Inject a test ICT risk scoring event with a residual score within appetite (e.g., 3/10); verify no escalation alert fires and the risk appears correctly categorised in the dashboard as within tolerance."),
    "22.3.2": ("Create a test ICT incident and classify it against all 7 Art.18 criteria with at least 2 criteria breached (client impact > 10%, data loss); verify the classification engine flags it as major and triggers the regulatory reporting workflow within 4 hours.",
               "Create a test ICT incident affecting a single non-critical system with no client impact; verify the classification engine correctly identifies it as non-major and no regulatory reporting workflow is triggered."),
    "22.3.3": ("Create a test resilience testing milestone with an overdue completion date; verify the tracking search identifies the overdue test and escalates to the CISO with test name, original deadline, and days overdue.",
               "Record a test resilience testing milestone completed 5 days before its deadline; verify no overdue alert fires and the test programme dashboard shows green status."),
    "22.3.4": ("Configure a test ICT third-party arrangement with spend exceeding 35% of total ICT budget and fewer than 2 alternative providers documented; verify the concentration risk alert fires with provider name, percentage, and substitutability score.",
               "Configure a test ICT third-party arrangement with spend at 15% of ICT budget and 3 qualified alternative providers documented; verify no concentration alert fires."),
    "22.3.5": ("Simulate a test DR failover event with recovery time exceeding the defined RTO by 30 minutes; verify the compliance search detects the RTO breach and alerts the resilience team with service name, RTO target, and actual recovery time.",
               "Simulate a test DR failover event completing recovery 10 minutes within the RTO target; verify the dashboard shows compliant recovery with green status."),
    "22.3.6": ("Log a test change management event deploying a patch 15 days after its critical-patch SLA deadline; verify the patch compliance search identifies the overdue patch with CVE reference, affected systems, and days overdue.",
               "Log a test change management event deploying a critical patch within 7 days of release (within SLA); verify no compliance alert fires and the patch appears as timely in the dashboard."),
    "22.3.7": ("Generate test network traffic at 3x the normal baseline volume for a monitored critical system; verify the anomaly detection search identifies the deviation and generates an investigation alert with system name, baseline, and observed values.",
               "Generate test network traffic within normal baseline parameters (±15%); verify no anomaly alert fires and the system appears normal in the monitoring dashboard."),
    "22.3.8": ("Log a test incident with resolution timestamp exceeding the 4-hour RTO target by 2 hours; verify the recovery tracking search identifies the RTO breach and calculates the exact overrun with incident ID and affected service.",
               "Log a test incident with resolution timestamp 30 minutes within the RTO target; verify the tracking shows compliant recovery and no breach alert is generated."),
    "22.3.9": ("Set a test backup restoration test date to 120 days ago (exceeding the 90-day quarterly schedule); verify the completeness search identifies the overdue restoration test with backup name and days overdue.",
               "Record a test backup restoration completed successfully 45 days ago (within the 90-day cycle); verify no overdue alert fires and the backup shows as verified."),
    "22.3.10": ("Create a test incident record closed 45 days ago with no linked post-incident review; verify the learning search identifies the missing review and generates a reminder with incident ID, closure date, and review deadline.",
                "Create a test incident record with a linked completed post-incident review submitted within 14 days of closure; verify no missing-review alert fires."),
    "22.3.11": ("Submit a test incident for classification with incomplete data (missing client count and geographic spread fields); verify the classification timeliness search flags the incomplete classification with missing criteria identified.",
                "Submit a test incident with all 7 Art.18 criteria fully assessed within 4 hours of detection; verify the classification shows as timely and complete."),
    "22.3.12": ("Create a test major incident classified 10 days ago with no intermediate report submitted; verify the reporting tracker identifies the missing report with incident ID and deadline information.",
                "Create a test major incident with initial report submitted within 24 hours and intermediate report within 72 hours; verify no reporting gap is identified."),
    "22.3.13": ("Add a test ICT third-party arrangement without a corresponding entry in the Art.28(3) register; verify the register completeness check identifies the unregistered arrangement.",
                "Add a test ICT third-party arrangement with full register entry including all required fields (provider, function, criticality, location); verify no completeness gap is reported."),
    "22.3.14": ("Log test SLA performance data showing availability at 99.2% against a 99.9% contractual target; verify the SLA monitoring search detects the breach and calculates the shortfall.",
                "Log test SLA performance data showing availability at 99.95% against a 99.9% target; verify the monitoring confirms compliance with no breach alert."),
    "22.3.15": ("Generate a test privileged access event from an unrecognised device/location combination outside any maintenance window; verify the access monitoring search flags the anomalous access for investigation.",
                "Generate a test privileged access event from a registered device during an approved maintenance window; verify no anomalous access alert fires."),
    "22.3.16": ("Log a test vulnerability scan result with 3 critical findings older than 30 days without remediation tickets; verify the tracking search identifies unresolved critical findings with CVE references and age.",
                "Log a test vulnerability scan result with all critical findings having linked remediation tickets created within 7 days; verify no unresolved-finding alert fires."),
    "22.3.17": ("Set a test TLPT milestone to 30 days overdue with no completion evidence; verify the lifecycle search identifies the overdue milestone and alerts the TLPT programme manager.",
                "Record all test TLPT milestones completed within their planned dates; verify the lifecycle dashboard shows green status throughout."),
    "22.3.18": ("Create a test exit strategy with last review date exceeding 18 months and no alternative provider validation; verify the readiness search flags the stale exit strategy for review.",
                "Create a test exit strategy reviewed within the last 6 months with validated alternative providers and tested data portability; verify no readiness alert fires."),
    "22.3.19": ("Log a test governance reporting cycle with the management body ICT risk report overdue by 15 days beyond the quarterly schedule; verify the oversight search identifies the reporting gap.",
                "Log management body ICT risk reports delivered on schedule for the last 4 quarters; verify no governance gap is reported."),
    "22.3.20": ("Simulate a test crisis scenario with no communication sent to internal stakeholders within 2 hours; verify the readiness search identifies the communication gap and escalates to the crisis management team.",
                "Simulate a test crisis scenario with internal and external communications sent within the 1-hour target; verify the communication readiness dashboard shows compliant response."),
    "22.3.21": ("Configure a test provider with 42% of ICT spend and no documented risk mitigation for the concentration; verify the concentration search flags the excessive spend with provider details.",
                "Configure test providers with maximum 20% spend per provider and documented alternatives; verify no concentration alert fires."),
    "22.3.22": ("Map a test critical function depending on a single provider with no alternative identified; verify the fan-in search detects the single-provider dependency and alerts the third-party risk team.",
                "Map a test critical function with primary and validated secondary providers; verify no single-dependency alert fires."),
    "22.3.23": ("Simulate correlated outage events across 3 services from the same regional provider exceeding normal variance; verify the correlation search identifies the provider-common-cause pattern.",
                "Log independent service events from different providers and regions; verify no regional correlation alert fires."),
    "22.3.24": ("Assess a test critical provider with substitutability score below threshold (< 3/10) and no active alternative qualification programme; verify the search flags the low substitutability.",
                "Assess a test provider with substitutability score 7/10 and two qualified alternatives in the register; verify no substitutability alert fires."),
    "22.3.25": ("Log a test TLPT scope document 45 days past its planned lock date without formal sign-off; verify the audit trail search flags the unlocked scope with milestone details.",
                "Log a test TLPT scope document locked and signed-off on the planned date; verify no scope-lock alert fires."),
    "22.3.26": ("Submit a test tester independence attestation with a previously undisclosed advisory engagement for the same entity; verify the conflict-of-interest check flags the potential conflict.",
                "Submit a test tester independence attestation with no conflicts identified and 3-year cooling period confirmed; verify no independence alert fires."),
    "22.3.27": ("Log a test TLPT finding rated critical with no remediation owner assigned after 14 days; verify the tracking search identifies the unassigned finding and escalates.",
                "Log a test TLPT finding with remediation owner assigned within 5 days and due date set; verify no unassigned-finding alert fires."),
    "22.3.28": ("Record a test remediated finding with no retest evidence 60 days after fix deployment; verify the verification search flags the unverified remediation.",
                "Record a test remediated finding with successful retest evidence submitted 30 days after fix; verify no verification gap is reported."),
    "22.3.29": ("Create a test anonymised incident report 10 days after the sharing deadline; verify the timeline search identifies the late submission with days overdue.",
                "Create a test anonymised incident report submitted 2 days before the sharing deadline; verify no timeline alert fires."),
    "22.3.30": ("Publish test threat indicators to the distribution platform and verify one subsidiary has not received them after 24 hours; verify the distribution search identifies the delivery gap.",
                "Publish test threat indicators and verify all subsidiaries acknowledge receipt within 4 hours; verify no distribution gap is reported."),
    "22.3.31": ("Create a test TTP contribution 30 days after the incident closure with no documented reason for delay; verify the contribution search flags the late submission.",
                "Create a test TTP contribution within 14 days of incident closure; verify no timeline alert fires."),
    "22.3.32": ("Log a test sub-processor notification arriving 75 days after the change (exceeding a 60-day contractual SLA); verify the lag detection identifies the late notification.",
                "Log a test sub-processor notification arriving within 30 days of the change; verify no lag alert fires."),
    "22.3.33": ("Create a test critical function with no provider mapping in the outsourcing register; verify the completeness search identifies the unmapped function.",
                "Create a test critical function fully mapped to its supporting provider(s) with all required fields; verify no mapping gap is reported."),
    "22.3.34": ("Log a test ICT arrangement storing data in a restricted jurisdiction with no documented justification; verify the localization search flags the cross-border storage.",
                "Log a test ICT arrangement with data stored in the approved home jurisdiction; verify no localization alert fires."),
    "22.3.35": ("Set a test alternative provider entry to last-validated 18 months ago (exceeding annual review); verify the currency search flags the stale entry for refresh.",
                "Set a test alternative provider entry validated within the last 6 months; verify no staleness alert fires."),
    "22.3.36": ("Record a test data portability exercise that failed to export 20% of required data categories; verify the evidence search identifies the incomplete export with missing categories.",
                "Record a test data portability exercise successfully exporting all required data categories; verify no incompleteness alert fires."),
    "22.3.37": ("Log a test exit runbook step with sign-off exceeding the 5-day SLA; verify the completion search identifies the overdue sign-off with step details.",
                "Log all test exit runbook steps signed off within 3 days; verify no SLA breach is reported."),
    "22.3.38": ("Create a test provider risk assessment showing inherent risk of 9/10 and residual risk of 8/10 (minimal control effectiveness); verify the search identifies inadequate risk reduction.",
                "Create a test provider risk assessment showing inherent 9/10 reduced to residual 3/10 through validated controls; verify the assessment shows effective risk management."),
    "22.3.39": ("Set a test control testing evidence date to 14 months ago (exceeding annual schedule); verify the evidence search flags the stale control test for refresh.",
                "Set a test control testing evidence date to 8 months ago (within annual cycle); verify no staleness alert fires."),
    "22.3.40": ("Configure a test provider risk register with 15 open findings (exceeding the 10-finding density threshold); verify the density search flags the excessive finding count for management review.",
                "Configure a test provider risk register with 5 open findings (below threshold); verify no density alert fires."),
    "22.3.41": ("Log a test ICT risk framework control with no testing evidence in the last 13 months; verify the framework evidence search identifies the untested control.",
                "Log all test framework controls with testing evidence within the last 10 months; verify no evidence gap is reported."),
    "22.3.42": ("Deploy a test system to the network without CMDB registration; verify the inventory search identifies the unmanaged endpoint within 24 hours of detection.",
                "Deploy a test system with proper CMDB registration and classification before network connection; verify no unmanaged endpoint alert fires."),
    "22.3.43": ("Log a test high-risk vulnerability (CVSS 9.0+) discovered 20 days ago with no risk assessment or remediation plan; verify the identification search flags the unaddressed vulnerability.",
                "Log a test high-risk vulnerability with risk assessment completed within 48 hours and remediation plan created within 7 days; verify no gap is reported."),
    "22.3.44": ("Create a test incident hitting 3 of 7 major criteria but with classification not completed within 4 hours; verify the timeliness search identifies the slow classification.",
                "Create a test incident with classification completed against all 7 criteria within 2 hours; verify no timeliness alert fires."),
    "22.3.45": ("Set a test resilience testing programme with the next test overdue by 30 days beyond annual schedule; verify the programme search identifies the overdue test.",
                "Record the latest resilience test completed 2 months ago (within the annual cycle); verify no overdue test alert fires."),
}
for uid, (pos, neg) in _ct_data.items():
    CONTROL_TESTS[uid] = {"positiveScenario": pos, "negativeScenario": neg}

# ---------------------------------------------------------------------------
# EVIDENCE
# ---------------------------------------------------------------------------
EVIDENCE: dict[str, str] = {
    "22.3.1": "ICT risk dashboard exports showing risk inventory, scoring methodology, residual scores, mitigation status, and management body acceptance decisions archived quarterly for competent authority requests.",
    "22.3.2": "Incident classification records showing Art.18 criteria assessment, classification decision rationale, regulatory reporting submission timestamps, and competent authority acknowledgement references.",
    "22.3.3": "Resilience testing programme evidence showing scheduled tests, completion dates, scope documentation, findings summaries, and remediation tracking per testing cycle.",
    "22.3.4": "Third-party concentration analysis reports showing provider spend percentages, critical function dependencies, substitutability assessments, and management body risk acceptance documentation.",
    "22.3.5": "Disaster recovery test evidence showing RTO/RPO measurements, cross-region failover results, recovery sequence verification, and any identified gaps with remediation timelines.",
    "22.3.6": "Change management and patch compliance reports showing patch deployment timelines against SLA, CAB approvals, emergency change records, and compensating controls for deferred patches.",
    "22.3.7": "Anomaly detection capability evidence showing detection rules configured, baseline definitions, alert volumes, investigation outcomes, and detection effectiveness metrics.",
    "22.3.8": "Incident response and recovery evidence showing timeline from detection to restoration, RTO/RPO achievement, communication records, and recovery verification steps completed.",
    "22.3.9": "Backup completeness reports showing all critical systems in backup schedule, successful backup verification, restoration test results, and RPO compliance measurements.",
    "22.3.10": "Post-incident review evidence showing review completion dates, root cause findings, improvement actions identified, implementation tracking, and lessons-learned distribution records.",
    "22.3.11": "Major incident classification evidence showing all 7 Art.18 criteria assessments with data sources, threshold calculations, and classification decision records timestamped.",
    "22.3.12": "Regulatory reporting evidence showing initial notification timestamps, intermediate report content and delivery, final report submission confirmation, and authority feedback handling.",
    "22.3.13": "Register of information exports showing all ICT third-party arrangements with contractual details, function mapping, criticality designation, and completeness validation results.",
    "22.3.14": "SLA performance monitoring evidence showing availability, latency, and throughput measurements against contractual targets with breach identification and service credit calculations.",
    "22.3.15": "Access control evidence showing authentication events, privilege assignments, access review completion rates, anomaly investigations, and MFA enforcement statistics.",
    "22.3.16": "Vulnerability assessment evidence showing scan coverage, finding severity distribution, remediation timelines, retest results, and risk acceptance documentation for deferred items.",
    "22.3.17": "TLPT lifecycle evidence showing threat intelligence phase, scope lock documents, test execution timeline, findings report, remediation plans, and competent authority notifications.",
    "22.3.18": "Exit strategy evidence showing alternative provider assessments, data portability test results, transition plan documentation, cost estimates, and management body approval records.",
    "22.3.19": "Management body oversight evidence showing ICT risk reporting frequency, training completion records, strategic decision documentation, and governance committee meeting minutes.",
    "22.3.20": "Crisis communication evidence showing plan test dates, stakeholder notification logs, regulatory communication records, and post-crisis communication effectiveness reviews.",
    "22.3.21": "Concentration analysis evidence showing per-provider ICT spend, workload distribution, trend analysis, alternative provider readiness, and management body acceptance where applicable.",
    "22.3.22": "Critical service dependency evidence showing fan-in analysis per provider, single-point-of-failure identification, and mitigation controls documented for unavoidable concentrations.",
    "22.3.23": "Regional correlation evidence showing provider outage patterns, cross-service impact analysis, and resilience architecture validation for shared-infrastructure dependencies.",
    "22.3.24": "Substitutability assessment evidence showing alternative provider qualifications, switching cost estimates, transition timelines, and technology compatibility validation results.",
    "22.3.25": "TLPT planning evidence showing scope proposals, threat intelligence deliverables, scope lock sign-offs, competent authority correspondence, and risk parameter documentation.",
    "22.3.26": "Tester independence evidence showing conflict-of-interest declarations, cooling period verification, qualification certifications, and Art.27 compliance attestations.",
    "22.3.27": "TLPT findings evidence showing severity ratings, remediation owner assignments, due dates, progress tracking, and management body briefing records on critical findings.",
    "22.3.28": "Retest evidence showing original finding reference, remediation confirmation, retest methodology, effectiveness assessment results, and closure approvals.",
    "22.3.29": "FINCERT submission evidence showing anonymised report preparation, submission timestamps, acknowledgement records, and community feedback incorporation.",
    "22.3.30": "Indicator distribution evidence showing publication timestamps, subsidiary acknowledgement records, integration confirmation, and effectiveness metrics for distributed IOCs.",
    "22.3.31": "TTP contribution evidence showing anonymisation review, structured format compliance, community submission confirmation, and quality feedback from recipients.",
    "22.3.32": "Sub-processor notification evidence showing change dates, notification timestamps, acknowledgement records, due diligence completion, and register update confirmation.",
    "22.3.33": "Function mapping evidence showing all critical and important functions with provider linkages, data flow documentation, and completeness validation against the BIA.",
    "22.3.34": "Data localization evidence showing storage locations, jurisdictional classification, regulatory requirements mapping, and exception documentation with justification.",
    "22.3.35": "Alternative provider evidence showing shortlist currency, capability assessments, pricing validation dates, regulatory qualification status, and management body review records.",
    "22.3.36": "Data portability evidence showing export format specifications, test execution logs, completeness measurements, restoration validation results, and identified format gaps.",
    "22.3.37": "Exit runbook evidence showing step completion records, sign-off timestamps, SLA compliance measurements, dependency tracking, and rehearsal results.",
    "22.3.38": "Risk register evidence showing inherent and residual scores, control effectiveness assessments, trend analysis, and management body risk decisions for each provider.",
    "22.3.39": "Control testing evidence showing test dates, methodology documentation, results, effectiveness ratings, and remediation tracking for identified weaknesses.",
    "22.3.40": "Issue density evidence showing finding counts by severity, age analysis, remediation progress, and trend reports for management body oversight.",
    "22.3.41": "Framework evidence showing control inventory, testing schedules, compliance status per Art.6 requirement, gap analysis, and remediation programme tracking.",
    "22.3.42": "ICT inventory evidence showing discovery scan results, CMDB coverage metrics, unmanaged asset identification, classification completeness, and reconciliation reports.",
    "22.3.43": "Risk identification evidence showing vulnerability discovery timeline, risk assessment completion, remediation plan creation, and tracking to closure.",
    "22.3.44": "Classification timeliness evidence showing incident detection timestamp, classification completion timestamp, criteria assessment documentation, and elapsed time calculations.",
    "22.3.45": "Testing programme evidence showing annual plan, test execution dates, coverage measurements, findings summaries, and programme completion attestation.",
}

# ---------------------------------------------------------------------------
# EXCLUSIONS
# ---------------------------------------------------------------------------
EXCLUSIONS: dict[str, str] = {
    "22.3.1": "ICT risks formally accepted through the management body's risk appetite framework with documented compensating controls and time-bounded review dates; risks from systems scheduled for decommissioning within 90 days.",
    "22.3.2": "Test incidents generated during resilience exercises clearly tagged as drills; incidents reclassified below major threshold after detailed impact assessment; incidents under active classification refinement within the allowed period.",
    "22.3.3": "Financial entities below DORA proportionality thresholds with reduced testing obligations per Art.4; TLPT-exempt entities per competent authority determination; tests in approved rescheduling during scope changes.",
    "22.3.4": "Concentration in utility services with no viable alternatives (SWIFT, market exchanges); intra-group service arrangements under consolidated group governance; approved concentration with management body acceptance.",
    "22.3.5": "Non-critical functions with relaxed DR requirements per BIA classification; planned DR test events generating expected recovery metrics; systems in active migration with documented reduced-coverage acceptance.",
    "22.3.6": "Emergency patches deployed under emergency change authority with retrospective approval; systems past vendor end-of-life with documented risk acceptance; non-production environments with intentional patch lag.",
    "22.3.7": "Known seasonal traffic patterns documented in baseline definitions; planned load testing activities on schedule; market events generating legitimate volume spikes within business-expected parameters.",
    "22.3.8": "Planned maintenance events with expected service windows; partial service restoration in documented degraded modes meeting minimum service definitions; recovery blocked by documented external dependencies.",
    "22.3.9": "Cloud-native services using provider redundancy instead of traditional backup with documented justification; backup infrastructure maintenance under change control; archival backups on different testing schedules.",
    "22.3.10": "Incident reviews with approved timeline extensions for complex multi-party incidents; consolidated reviews covering multiple related incidents; reviews awaiting third-party input with documented dependency.",
    "22.3.11": "Classification refinement within the allowed assessment period; incidents at exact threshold boundaries requiring additional data collection; weekend/holiday incidents with next-business-day classification per procedures.",
    "22.3.12": "Reports in the phased reporting timeline per Art.19 schedule; reports returned by authorities for additional information with restarted timelines; consolidated reports with authority approval.",
    "22.3.13": "Short-term trial arrangements below materiality threshold; legacy contracts in active migration to new register format; intra-group services with different classification per legal structure.",
    "22.3.14": "Planned maintenance windows excluded from SLA calculations per contract; force majeure periods with documented evidence; service credit events below DORA regulatory breach thresholds.",
    "22.3.15": "Approved maintenance window access; automated service account operations per approved register; break-glass access during declared incidents with post-incident review; access within recertification cycle.",
    "22.3.16": "Confirmed false positives from scanner validation; findings with approved risk acceptance and compensating controls; third-party managed components awaiting vendor patches with tracked compensating controls.",
    "22.3.17": "TLPT-exempt entities per proportionality determination; scope changes during threat intelligence phase with documented rationale; critical production freeze periods with approved suspension.",
    "22.3.18": "Exit strategies under active review within the annual cycle; new critical function designations within first planning cycle; strategies being updated following provider market changes.",
    "22.3.19": "Interim governance arrangements during documented restructuring; delegated authority frameworks with management body oversight confirmation; new board member induction periods.",
    "22.3.20": "Communication plan tests generating test notifications; classified incidents with restricted communication per law enforcement coordination; communication channel maintenance windows.",
    "22.3.21": "Approved concentration decisions with management body acceptance; multi-year contract amortisation effects; intra-group provider reclassification during restructuring.",
    "22.3.22": "Market utility providers with structural single-provider dominance; common technology stack dependencies managed through layered controls; temporary migration concentrations on approved timelines.",
    "22.3.23": "Provider-initiated planned maintenance affecting multiple services; correlated patching within coordination schedules; network interconnect maintenance events beyond provider control.",
    "22.3.24": "Market infrastructure with no practical alternatives (CSD, payment rails); contractual lock-in within documented exit strategy timelines; regulatory approval constraints on alternative providers.",
    "22.3.25": "Scope refinement during threat intelligence gathering (expected methodology); competent authority review iterations; risk appetite alignment requiring multiple management body approvals.",
    "22.3.26": "Limited provider pool in jurisdiction with documented market constraints; internal red team usage under Art.26(8) with external validation; historical engagement cooling periods within defined timeframes.",
    "22.3.27": "Severity re-assessment with documented rationale; shared-responsibility findings awaiting provider cooperation; compensating control closures with equivalent protection documentation.",
    "22.3.28": "Control maturation periods requiring operating evidence before retest; retests scheduled in next TLPT cycle per programme design; tester availability constraints with documented timeline.",
    "22.3.29": "Voluntary sharing outside mandatory scope; anonymisation quality review time for complex incidents; legal review for confidential information protection; cross-border coordination timing.",
    "22.3.30": "Relevance filtering for subsidiary-specific content; TLP marking review for classification compliance; distribution platform maintenance windows; subsidiary integration issues under remediation.",
    "22.3.31": "Active law enforcement restrictions on TTP sharing; anonymisation quality review for complex incidents; duplicate contribution verification; ongoing investigation coordination holds.",
    "22.3.32": "Notifications within contractual notice period; entity name changes without processing changes; batch notification processing per contractual terms; general authorisation model objection windows.",
    "22.3.33": "New function designations within initial mapping period; register schema migration during format transitions; sub-outsourcing chain functions documented in chain analysis separately.",
    "22.3.34": "Transit routing through jurisdictions without processing; DR sites in approved alternative locations per resilience framework; adequacy-covered jurisdictions; CDN edge caching of non-critical data.",
    "22.3.35": "Market consolidation impacts requiring strategy refresh on discovery; providers under regulatory qualification with documented timelines; annual pricing refresh cycles between validation dates.",
    "22.3.36": "Sample-data portability tests per methodology design; partial portability by design for provider-specific elements with acceptance; format evolution between cycles triggering planned updates.",
    "22.3.37": "Runbook updates between annual review cycles; delegated sign-off per absence framework; external dependency blocking with documented tracking; tabletop rehearsals meeting exercise-level evidence.",
    "22.3.38": "New providers within initial assessment window; industry-wide risk elevation from geopolitical events; assessment methodology transitions creating non-comparable score changes.",
    "22.3.39": "Testing evidence from provider certifications following certification audit cycles; new controls within maturation period; cross-entity control evidence maintained in group repositories.",
    "22.3.40": "Findings within contractual remediation SLA; finding increases from expanded assessment scope (improved visibility); informational findings below risk threshold excluded from density calculations.",
    "22.3.41": "Framework elements being phased in per approved roadmap; controls between testing cycles within defined frequency; policy documents under scheduled annual review.",
    "22.3.42": "Ephemeral cloud resources (containers, serverless); systems in decommissioning disposal process; assets pending discovery via alternative methods; reconciliation timing between inventory sources.",
    "22.3.43": "Vulnerabilities within policy remediation windows; confirmed false positives; compensating controls for unpatachable legacy systems; vendor-managed component vulnerabilities tracked separately.",
    "22.3.44": "Classification refinement using initial incomplete data; aggregation period for client impact assessment; weekend/holiday capacity constraints within escalation procedures.",
    "22.3.45": "Proportionality-based reduced obligations per Art.4; testing tool transitions between cycles; third-party tester onboarding within planning allowance; evolving RTS/ITS interpretation ambiguity.",
}

# ---------------------------------------------------------------------------
# DI ENRICHMENT
# ---------------------------------------------------------------------------
DI_ENRICHMENT: dict[str, str] = {}
_di_base_ict_risk = "\n\n**Ecosystem integration:** Feed ICT risk scores to Splunk ES for correlation with operational events. Integrate ServiceNow GRC for risk register synchronisation. Pull vulnerability context from Tenable or Qualys for risk scoring enrichment. Trigger Splunk SOAR playbooks for automated risk escalation workflows. Report to Microsoft Defender for Cloud for multi-cloud risk posture integration. Feed governance evidence to CMDB for asset-to-risk linkage."
_di_base_incident = "\n\n**Ecosystem integration:** Correlate with Splunk ES notable events for incident context enrichment. Trigger Splunk SOAR playbooks for automated classification and reporting workflows. Integrate ServiceNow ITSM for incident lifecycle management. Pull threat intelligence from Microsoft Sentinel for attack vector analysis. Feed regulatory reporting data to the GRC platform for competent authority submissions. Enrich with Okta identity context for user impact assessment."
_di_base_testing = "\n\n**Ecosystem integration:** Import findings from Tenable, Qualys, or Rapid7 for vulnerability and testing evidence. Track remediation in ServiceNow with automated SLA management. Correlate with Splunk ES risk framework for organisational security posture. Trigger Splunk SOAR for finding escalation and retest coordination. Feed testing evidence to the GRC platform for Art.24/25 compliance packs. Integrate CyberArk for privileged access testing context."
_di_base_tprm = "\n\n**Ecosystem integration:** Pull provider risk data from ServiceNow vendor risk management. Correlate with Splunk ES for third-party security event monitoring. Trigger Splunk SOAR for provider SLA breach and exit strategy workflows. Integrate Microsoft Defender for Cloud for provider cloud security posture. Feed concentration and dependency analysis to the GRC platform for management body reporting. Enrich with CMDB for function-to-provider mapping."

for uid in ["22.3.1", "22.3.5", "22.3.6", "22.3.7", "22.3.19", "22.3.20", "22.3.21",
            "22.3.22", "22.3.23", "22.3.24", "22.3.41", "22.3.42", "22.3.43"]:
    DI_ENRICHMENT[uid] = _di_base_ict_risk
for uid in ["22.3.2", "22.3.8", "22.3.10", "22.3.11", "22.3.12", "22.3.29",
            "22.3.30", "22.3.31", "22.3.38", "22.3.44"]:
    DI_ENRICHMENT[uid] = _di_base_incident
for uid in ["22.3.3", "22.3.16", "22.3.17", "22.3.25", "22.3.26", "22.3.27",
            "22.3.28", "22.3.39", "22.3.45"]:
    DI_ENRICHMENT[uid] = _di_base_testing
for uid in ["22.3.4", "22.3.9", "22.3.13", "22.3.14", "22.3.15", "22.3.18",
            "22.3.32", "22.3.33", "22.3.34", "22.3.35", "22.3.36", "22.3.37", "22.3.40"]:
    DI_ENRICHMENT[uid] = _di_base_tprm


def fix_file(path: Path) -> list[str]:
    raw = path.read_text("utf-8")
    data = json.loads(raw)
    uid = data["id"]
    changes: list[str] = []

    if uid in KFP:
        data["knownFalsePositives"] = KFP[uid]
        changes.append("replaced knownFalsePositives")

    if uid in REFS:
        data["references"] = REFS[uid]
        changes.append(f"set references ({len(REFS[uid])})")

    if uid in DATASOURCES:
        data["dataSources"] = DATASOURCES[uid]
        changes.append("expanded dataSources")

    if uid in CONTROL_TESTS and "controlTest" not in data:
        data["controlTest"] = CONTROL_TESTS[uid]
        changes.append("added controlTest")

    if uid in EVIDENCE:
        if len(data.get("evidence", "") or "") < 30:
            data["evidence"] = EVIDENCE[uid]
            changes.append("added evidence")

    if uid in EXCLUSIONS:
        if len(data.get("exclusions", "") or "") < 30:
            data["exclusions"] = EXCLUSIONS[uid]
            changes.append("added exclusions")

    kfp = data.get("knownFalsePositives", "") or ""
    if kfp and not SUPPRESSION_RE.search(kfp):
        data["knownFalsePositives"] = kfp + SUPPRESSION_SUFFIX
        changes.append("appended suppression mechanism")

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
    files = sorted(
        CONTENT.glob("UC-22.3.*.json"),
        key=lambda p: int(p.stem.split(".")[-1]),
    )
    print(f"Processing {len(files)} DORA UCs (Tier B+C+D)...")
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
