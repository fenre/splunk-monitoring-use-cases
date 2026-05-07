#!/usr/bin/env python3
"""Tier-B+C uplift for GDPR (22.1.*) — hand-written knownFalsePositives,
references, and dataSources expansion.

Each UC receives:
  - 4-5 structured, named false-positive scenarios specific to its detection
  - References expanded to >= 4 (adds GDPR official text, EDPB guidelines,
    Splunk documentation, and domain-specific references)
  - dataSources expanded to >= 80 chars with specific source details

UC-22.1.5 is skipped as it already has gold-quality KFP (2787 chars).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content" / "cat-22-regulatory-compliance"

# ---------------------------------------------------------------------------
# KNOWN FALSE POSITIVES — hand-written per UC
# ---------------------------------------------------------------------------

KFP: dict[str, str] = {
    "22.1.1": (
        "1. **Authorized data exports** — Scheduled exports of PII for payroll, "
        "benefits administration, or financial reporting generate legitimate PII "
        "detections that are pre-approved by the Data Protection Officer and "
        "documented in the Records of Processing Activities (ROPA).\n\n"
        "2. **Customer support ticket content** — Support agents handling "
        "complaints or account queries may paste customer details into ticketing "
        "systems; this is a normal processing activity under the service contract "
        "lawful basis and should be excluded per the support-operations tag.\n\n"
        "3. **Anonymisation pipeline intermediate logs** — Data flowing through "
        "pseudonymisation or anonymisation pipelines may briefly appear in "
        "cleartext in processing logs before the transform completes; correlate "
        "with pipeline job IDs to confirm legitimate activity.\n\n"
        "4. **Developer test data in non-production** — Synthetic or sample PII "
        "used in dev/staging environments may trigger regex detections; exclude "
        "events tagged with environment=dev or environment=staging.\n\n"
        "5. **Legal hold data preservation** — PII retained beyond normal "
        "retention periods due to active litigation holds is intentional and "
        "documented in the legal-hold register; suppress alerts when a matching "
        "legal-hold reference exists."
    ),
    "22.1.2": (
        "1. **Multi-system extraction delays** — DSARs that span legacy systems "
        "with batch-only interfaces may show extraction times exceeding SLA "
        "thresholds; verify the DSAR ticket contains an approved extension "
        "documented under Art.12(3) before treating as a genuine breach.\n\n"
        "2. **Vendor-managed system coordination** — Third-party processor "
        "responses may arrive outside the controller's normal business hours, "
        "creating apparent SLA violations that resolve once the processor's "
        "response is ingested into the tracking system.\n\n"
        "3. **Complex identity verification cycles** — DSARs requiring additional "
        "identity verification under Art.12(6) pause the response clock; the "
        "search may flag the overall elapsed time without accounting for the "
        "verification hold period.\n\n"
        "4. **Bulk DSAR campaigns** — Organised campaigns (e.g., privacy advocacy "
        "groups) may generate dozens of simultaneous requests that temporarily "
        "exceed capacity, triggering SLA alerts that are already being managed "
        "under the manifestly excessive provision of Art.12(5).\n\n"
        "5. **Withdrawn requests** — Data subjects who voluntarily withdraw their "
        "DSAR before completion may leave open tickets that appear as unfulfilled "
        "requests; check the ticket status for withdrawal confirmation."
    ),
    "22.1.3": (
        "1. **Initial triage vs. confirmed breach** — The 72-hour notification "
        "clock starts at awareness of a confirmed breach, not at initial anomaly "
        "detection; security events under investigation that have not yet been "
        "confirmed as breaches should not count against the notification timer.\n\n"
        "2. **Weekend and public holiday discovery** — Incidents discovered "
        "outside business hours may appear to breach the timeline if the "
        "awareness timestamp is incorrectly recorded as the first alert rather "
        "than when the on-call DPO was actually notified and acknowledged.\n\n"
        "3. **Multi-jurisdictional coordination** — Breaches affecting multiple "
        "EU Member States require lead supervisory authority identification, "
        "which may extend apparent notification time while the organisation "
        "determines the correct authority under Art.56.\n\n"
        "4. **Phased notifications** — Art.33(4) permits phased notification "
        "where full details are not immediately available; initial notifications "
        "filed within 72 hours followed by supplementary reports may appear as "
        "delayed if the search only tracks final submission timestamps.\n\n"
        "5. **False breach classifications** — Security incidents initially "
        "classified as personal data breaches during triage but later "
        "downgraded (e.g., encrypted data exposure with keys intact) create "
        "notification timer entries that are subsequently voided."
    ),
    "22.1.4": (
        "1. **Legal hold retention overrides** — Data retained beyond its "
        "scheduled deletion date due to active litigation or regulatory "
        "investigation is intentional; cross-reference the legal-hold register "
        "to suppress retention policy violation alerts.\n\n"
        "2. **Archival migration in progress** — During data migration projects, "
        "records may exist in both source and destination systems temporarily, "
        "appearing as retention violations until the migration completes and "
        "source copies are purged.\n\n"
        "3. **Backup retention windows** — Backup systems may retain data beyond "
        "the primary system's retention period due to backup rotation schedules "
        "(e.g., monthly full backups retained for 12 months); this is documented "
        "in the backup retention policy as a technical limitation.\n\n"
        "4. **Consent-extended retention** — Some data subjects provide explicit "
        "consent for extended retention (e.g., loyalty programme history); these "
        "records carry a different retention class that the search may not "
        "distinguish from standard processing records.\n\n"
        "5. **Staged deletion rollouts** — Phased deletion jobs that process "
        "records by region or business unit may flag records awaiting their "
        "scheduled batch window as overdue when they are simply queued."
    ),
    "22.1.6": (
        "1. **Pre-approved vendor transfers** — Transfers to processors in "
        "adequate jurisdictions or under executed SCCs are lawful and expected; "
        "the search flags all cross-border flows including those already covered "
        "by the Art.46 safeguard inventory.\n\n"
        "2. **CDN and cloud edge nodes** — Content delivery networks and cloud "
        "providers may route data through third-country nodes as part of normal "
        "infrastructure; verify against the cloud provider's data processing "
        "addendum for permitted transit locations.\n\n"
        "3. **Emergency business continuity failover** — Disaster recovery "
        "failovers to secondary regions outside the EEA are documented in the "
        "business continuity plan and covered under Art.49(1)(f) vital interests "
        "derogation during active incidents.\n\n"
        "4. **Intra-group transfers under BCRs** — Multinational organisations "
        "with approved Binding Corporate Rules (Art.47) have standing authority "
        "for intra-group transfers; these should be excluded when BCR status is "
        "confirmed in the transfer register.\n\n"
        "5. **SCC renewal timing gaps** — Brief periods between SCC expiry and "
        "renewal execution may trigger alerts for transfers that are covered by "
        "the renewal already in legal review; check the contract management "
        "system for pending renewals."
    ),
    "22.1.7": (
        "1. **Key rotation windows** — Scheduled cryptographic key rotations "
        "temporarily show gaps in encryption coverage as old keys are retired "
        "and new keys propagated; correlate with the key management system's "
        "rotation schedule.\n\n"
        "2. **Development environment exceptions** — Non-production environments "
        "using self-signed certificates or reduced encryption for debugging may "
        "trigger coverage gaps; exclude environments tagged as non-production "
        "where no real personal data is processed.\n\n"
        "3. **Legacy system migration projects** — Systems being migrated to "
        "encrypted storage may show partial coverage during the transition; "
        "verify against the approved migration timeline and risk acceptance.\n\n"
        "4. **Pseudonymisation vs. encryption confusion** — Some systems use "
        "tokenisation or pseudonymisation as the Art.32 safeguard rather than "
        "encryption; the search may flag these as unencrypted when they are "
        "actually protected under an alternative technical measure.\n\n"
        "5. **Internal transport encryption exclusions** — Data flowing within "
        "a single physically secured facility over a dedicated VLAN may be "
        "exempted from TLS requirements per the risk assessment; verify against "
        "the network security architecture documentation."
    ),
    "22.1.8": (
        "1. **Newly onboarded processing activities** — Newly created processing "
        "records may take up to 30 days to fully populate all ROPA fields as "
        "data owners complete their submissions; check the onboarding workflow "
        "status before flagging as incomplete.\n\n"
        "2. **Archival processing activities** — Processing activities marked for "
        "decommissioning may show fields as outdated while the formal closure "
        "process completes; verify against the decommissioning register.\n\n"
        "3. **Seasonal or periodic processing** — Activities that only occur "
        "during specific periods (e.g., annual employee surveys) may appear "
        "stale between cycles; validate against the processing schedule.\n\n"
        "4. **Merger and acquisition transitions** — During M&A integration, "
        "processing activities from the acquired entity may not yet be fully "
        "mapped into the acquiring company's ROPA format, creating temporary "
        "completeness gaps.\n\n"
        "5. **Third-party ROPA contributions** — Processors required to maintain "
        "ROPA entries under Art.30(2) may submit updates on different schedules "
        "than the controller's ROPA refresh cycle."
    ),
    "22.1.9": (
        "1. **Analytics enrichment fields** — Some applications collect additional "
        "metadata fields for system performance monitoring that do not constitute "
        "personal data but may be flagged by data-minimisation checks due to "
        "field naming patterns (e.g., user_session_hash).\n\n"
        "2. **Audit trail requirements** — Certain fields collected for regulatory "
        "audit trails (e.g., IP addresses in financial transaction logs) are "
        "required by other regulations and should not be treated as excessive "
        "under GDPR minimisation.\n\n"
        "3. **Consent-based expanded collection** — Users who opt into enhanced "
        "services may have additional data points collected under explicit consent "
        "(Art.6(1)(a)); the minimisation check may not distinguish between "
        "standard and consent-enhanced profiles.\n\n"
        "4. **Schema migration artefacts** — Database schema changes may "
        "temporarily retain deprecated columns during migration windows; verify "
        "against the migration plan for scheduled removal dates.\n\n"
        "5. **Federated identity attributes** — SSO/SAML assertions may carry "
        "additional identity attributes required by the identity provider but "
        "not used by the relying party; these transit through logs without being "
        "stored for processing."
    ),
    "22.1.10": (
        "1. **Scheduled DBA maintenance** — Database administrators performing "
        "approved maintenance tasks (index rebuilds, statistics updates, schema "
        "migrations) during change windows generate privileged access events that "
        "are pre-authorised in the change management system.\n\n"
        "2. **Automated ETL service accounts** — Extract-Transform-Load pipelines "
        "running under service accounts with elevated privileges produce "
        "high-volume read patterns that are normal operational behaviour; "
        "correlate with the ETL schedule in the orchestration platform.\n\n"
        "3. **Disaster recovery testing** — Periodic DR drills requiring database "
        "restores and validation queries generate privileged access patterns "
        "outside normal windows; cross-reference with the DR test calendar.\n\n"
        "4. **Security team forensic investigations** — Incident responders "
        "querying personal data stores during active investigations have "
        "documented authorisation in the incident ticket; suppress when the "
        "access correlates with an open incident.\n\n"
        "5. **Application deployment rollbacks** — Emergency rollback procedures "
        "may require direct database access to revert data changes; verify "
        "against the deployment ticket and rollback approval chain."
    ),
    "22.1.11": (
        "1. **Technical deletion propagation delays** — Erasure requests completed "
        "in primary systems may take 24-48 hours to propagate to downstream "
        "replicas, caches, and search indices; allow for the documented "
        "propagation window before flagging as incomplete.\n\n"
        "2. **Backup system exclusions** — Data in offline or cold-tier backups "
        "is typically excluded from immediate erasure per the documented backup "
        "retention exception; the search may flag these as unerased records when "
        "they are scheduled for expiry with the backup rotation.\n\n"
        "3. **Legal obligation retention** — Data that must be retained under "
        "other legal obligations (tax records, anti-money-laundering) overrides "
        "the right to erasure under Art.17(3)(b); verify the exemption basis "
        "against the retention schedule.\n\n"
        "4. **Pseudonymised research data** — Data that has been pseudonymised "
        "for scientific research under Art.17(3)(d) exemption may appear as "
        "unerased when it is actually lawfully retained.\n\n"
        "5. **Partial erasure for interconnected records** — Records that are "
        "interleaved with other data subjects' data may require redaction rather "
        "than full deletion; the verification check may flag partially-redacted "
        "records as incomplete erasure."
    ),
    "22.1.12": (
        "1. **Duplicate log entries from failover** — High-availability logging "
        "architectures may duplicate breach scope events during node failover, "
        "inflating affected data subject counts until deduplication completes.\n\n"
        "2. **Shared account attribution** — Systems with shared service accounts "
        "may show a single compromised credential affecting more records than "
        "actual unique data subjects; cross-reference with the identity registry "
        "for actual individual counts.\n\n"
        "3. **Encrypted data exposure reclassification** — Initially broad scope "
        "estimates that are later reduced when encryption status is confirmed "
        "(data was encrypted at rest and key was not compromised) create revised "
        "counts that differ from initial quantification.\n\n"
        "4. **Test data in affected systems** — Systems containing both production "
        "and test data may inflate breach scope counts when test records are "
        "included; subtract records matching the test data namespace.\n\n"
        "5. **Historical records beyond retention** — Data subjects whose records "
        "should have been deleted per the retention schedule but appear in the "
        "breach scope may represent a separate compliance issue rather than "
        "actual additional affected individuals."
    ),
    "22.1.13": (
        "1. **Risk assessment downgrade** — Breaches initially classified as "
        "high-risk that are subsequently downgraded after detailed impact "
        "assessment (e.g., encryption confirmed intact) no longer require "
        "data subject communication under Art.34(3)(a).\n\n"
        "2. **Communication already delivered by processor** — In cases where "
        "the processor has directly notified affected data subjects on behalf "
        "of the controller, the controller's communication tracking may show "
        "no outbound communication while the obligation is already fulfilled.\n\n"
        "3. **Public communication substitute** — Where individual communication "
        "would involve disproportionate effort, Art.34(3)(c) permits public "
        "communication; the search may flag absence of direct notifications "
        "when a public notice was the approved approach.\n\n"
        "4. **Supervisory authority direction** — The supervisory authority may "
        "direct that communication is not required under Art.34(4) after "
        "reviewing the breach; document the authority's decision reference.\n\n"
        "5. **Delayed contact information availability** — Some affected data "
        "subjects may have outdated contact details requiring skip-tracing or "
        "alternative channels, creating delivery delays that appear as "
        "non-communication."
    ),
    "22.1.14": (
        "1. **Low-risk processing pre-screened** — Processing activities that "
        "were assessed using the organisation's DPIA screening criteria and "
        "determined to be low-risk do not require a full DPIA; the absence of "
        "a DPIA record is documented in the screening register.\n\n"
        "2. **Legacy processing grandfathered** — Processing activities that "
        "existed before GDPR applicability (25 May 2018) and have not "
        "materially changed may have a lighter DPIA requirement per EDPB "
        "guidance; verify the change log for material modifications.\n\n"
        "3. **DPIA in progress** — New high-risk processing activities may "
        "show as uncovered while the DPIA is being drafted; check the DPIA "
        "project tracker for in-progress assessments with their expected "
        "completion dates.\n\n"
        "4. **Consolidated DPIAs** — Multiple related processing activities "
        "covered by a single umbrella DPIA may show individual activities as "
        "lacking their own DPIA when they are covered collectively.\n\n"
        "5. **Processing re-classification** — Activities recently reclassified "
        "as high-risk due to updated EDPB guidance or supervisory authority "
        "lists may have a grace period before the DPIA obligation triggers."
    ),
    "22.1.15": (
        "1. **Scheduled attestation cycles** — Processor compliance assessments "
        "that run on annual cycles may show gaps between attestation periods; "
        "verify the assessment schedule and acceptable evidence windows.\n\n"
        "2. **Certification equivalence** — Processors holding ISO 27001 or "
        "SOC 2 Type II certifications may provide these as compliance evidence "
        "rather than completing the controller's specific questionnaire; map "
        "certification controls to GDPR requirements.\n\n"
        "3. **New processor onboarding** — Recently engaged processors may be "
        "within the contractual onboarding period before their first compliance "
        "assessment is due; check the DPA execution date.\n\n"
        "4. **Processor M&A transitions** — Acquired processors may temporarily "
        "lack documentation in the controller's system while integration "
        "completes; verify the transition plan timeline.\n\n"
        "5. **Sub-processor compliance delegation** — Primary processors who "
        "manage sub-processor compliance under the Art.28(4) model may not "
        "surface sub-processor evidence directly to the controller; confirm "
        "the delegation arrangement in the DPA."
    ),
    "22.1.16": (
        "1. **Processing pipeline flush delay** — After consent withdrawal, "
        "data already in processing pipelines may take one processing cycle "
        "(typically 24-48 hours) to be suppressed; this is the documented "
        "technical implementation window, not a compliance failure.\n\n"
        "2. **Legitimate interest fallback** — Some processing activities may "
        "continue under Art.6(1)(f) legitimate interest after consent is "
        "withdrawn if the organisation has documented the alternative lawful "
        "basis; verify the legal basis mapping.\n\n"
        "3. **Contractual necessity override** — Processing necessary for "
        "contract performance under Art.6(1)(b) continues regardless of "
        "consent withdrawal for the marketing purpose; the search may flag "
        "continued processing without distinguishing purpose.\n\n"
        "4. **Partial consent withdrawal** — Data subjects may withdraw consent "
        "for specific purposes (e.g., marketing) while maintaining consent for "
        "others (e.g., personalisation); the search may flag continued "
        "processing under the retained consents.\n\n"
        "5. **Withdrawal during active service delivery** — Mid-transaction "
        "consent withdrawals (e.g., during an active session) may not take "
        "effect until the current interaction completes per the implementation "
        "design."
    ),
    "22.1.17": (
        "1. **Log rotation during maintenance** — Scheduled log management "
        "operations (rotation, compression, archival) may temporarily modify "
        "log file metadata without altering content; correlate with the log "
        "management schedule.\n\n"
        "2. **SIEM ingestion reprocessing** — Re-ingestion of historical logs "
        "after parser updates may create duplicate or modified entries that "
        "appear as tampering; verify against the SIEM change log.\n\n"
        "3. **Clock synchronisation adjustments** — NTP corrections on log "
        "sources may create apparent sequence anomalies in audit trails without "
        "actual content modification; check for corresponding NTP sync events.\n\n"
        "4. **Storage tier migration** — Logs moving between hot, warm, and cold "
        "storage tiers may change checksum values if the storage layer applies "
        "compression; verify the storage migration preserves content integrity.\n\n"
        "5. **Log forwarding chain modifications** — Adding or removing log "
        "forwarding hops (e.g., new syslog relay) may alter transport metadata "
        "while preserving payload integrity; document topology changes."
    ),
    "22.1.18": (
        "1. **Model retraining pipelines** — Scheduled ML model retraining that "
        "processes personal data for model improvement may trigger automated "
        "decision-making alerts during the training window; correlate with the "
        "ML operations schedule.\n\n"
        "2. **Human-in-the-loop overrides** — Systems with automated scoring "
        "that always require human review before action (Art.22(3) safeguard) "
        "may be flagged as purely automated when they have meaningful human "
        "intervention documented in the process flow.\n\n"
        "3. **A/B testing with random assignment** — Randomised content "
        "selection (A/B tests) may appear as profiling when it uses no personal "
        "data characteristics for the assignment; verify the randomisation "
        "method documentation.\n\n"
        "4. **Rule-based vs. AI-based distinction** — Simple business rules "
        "(e.g., age verification for alcohol sales) may trigger profiling "
        "alerts when they are deterministic eligibility checks rather than "
        "profiling under Art.4(4).\n\n"
        "5. **Aggregate analytics without individual impact** — Processing that "
        "uses personal data for aggregate statistics without producing "
        "individual-level decisions does not constitute automated decision-making "
        "with legal or significant effects."
    ),
    "22.1.19": (
        "1. **Clock pauses during identity verification** — The response clock "
        "pauses while the organisation verifies the data subject's identity "
        "under Art.12(6); the dashboard may show elapsed calendar time without "
        "accounting for the pause.\n\n"
        "2. **Art.12(3) extension applied** — Complex requests may be extended "
        "by two additional months with notification to the data subject; the "
        "dashboard should distinguish between standard and extended timelines.\n\n"
        "3. **Manifestly unfounded or excessive requests** — Requests that have "
        "been legitimately refused under Art.12(5) may appear as overdue if the "
        "refusal is not reflected in the status field.\n\n"
        "4. **Multi-right requests** — A single communication exercising multiple "
        "rights (access + erasure + portability) may show different completion "
        "dates for each component, creating partial-completion appearances.\n\n"
        "5. **System downtime during processing** — Scheduled system maintenance "
        "or unplanned outages may delay automated fulfilment steps; verify "
        "against the incident log for legitimate processing interruptions."
    ),
    "22.1.20": (
        "1. **Approved operational processing** — Data processing that appears "
        "novel but is actually covered by an existing purpose in the ROPA under "
        "a broadly-defined processing description may be flagged as lacking "
        "a legitimate interest assessment.\n\n"
        "2. **Pre-existing balancing tests** — Processing activities assessed "
        "before the current tracking system was implemented may lack digital "
        "records of the balancing test while paper records exist in the "
        "compliance archive.\n\n"
        "3. **Low-risk standard processing** — Routine business operations "
        "clearly within the reasonable expectations of the data subject (e.g., "
        "order fulfilment) may not require formal documented LIA per "
        "proportionality; verify against the LIA screening criteria.\n\n"
        "4. **Inherited processing from legacy entities** — Processing activities "
        "inherited through business acquisitions may reference the predecessor "
        "entity's balancing test documentation rather than the current entity's "
        "format.\n\n"
        "5. **Controller-to-controller sharing** — Data shared between joint "
        "controllers under Art.26 arrangements may have the LIA documented in "
        "the joint controller agreement rather than individual assessments."
    ),
    "22.1.21": (
        "1. **Key management transition windows** — During cryptographic key "
        "rotation, data briefly exists under both old and new keys; the audit "
        "may report coverage gaps during the rotation window.\n\n"
        "2. **In-memory processing exclusion** — Data processed exclusively in "
        "memory (e.g., real-time stream processing) without persistence to disk "
        "may not have at-rest encryption because it is never at rest; document "
        "the processing pattern as an acceptable exclusion.\n\n"
        "3. **Legacy system migration queues** — Systems queued for encryption "
        "migration may show as non-compliant while the migration project "
        "progresses through its approved timeline; verify milestone status.\n\n"
        "4. **Hardware security module offload** — Some HSM-protected systems "
        "may not report encryption status through standard APIs; verify "
        "directly with the HSM management console.\n\n"
        "5. **Compensating controls documentation** — Systems with alternative "
        "security controls (physical isolation, network segmentation) accepted "
        "through the risk management process as equivalent to encryption may "
        "appear as lacking encryption evidence."
    ),
    "22.1.22": (
        "1. **Scheduled access review cycles** — Alerts for users retaining "
        "access between quarterly access review dates are expected; the review "
        "date determines when access decisions are made.\n\n"
        "2. **Break-glass account usage** — Emergency access accounts used "
        "during critical incidents generate privileged access events that are "
        "documented in the incident record and reviewed post-incident.\n\n"
        "3. **Service account privilege accumulation** — Automated service "
        "accounts may accumulate permissions during application deployment; "
        "these are reviewed during the application security review cycle.\n\n"
        "4. **Temporary project-based access** — Staff assigned to time-limited "
        "projects may receive elevated access that appears excessive when "
        "viewed outside the project context; check project assignment records.\n\n"
        "5. **Identity provider synchronisation delays** — Deprovisioning "
        "initiated in the identity provider may take up to 4 hours to propagate "
        "to all connected applications; this is within the documented SLA."
    ),
    "22.1.23": (
        "1. **Pipeline warm-up with sample data** — Pseudonymisation pipelines "
        "processing test payloads during startup validation may log sample "
        "identifiers that trigger detection; verify the source is a test harness.\n\n"
        "2. **Reversible pseudonymisation by design** — Some implementations "
        "intentionally allow re-identification by authorised parties (e.g., "
        "healthcare researchers with ethics approval); this is a valid "
        "Art.4(5) implementation, not a failure.\n\n"
        "3. **Format-preserving encryption artefacts** — FPE-transformed values "
        "that retain the format of the original (e.g., same-length strings) may "
        "appear in logs as untransformed data when they are actually pseudonymised.\n\n"
        "4. **Cross-environment pipeline references** — Log entries referencing "
        "production identifiers in non-production pipeline configurations are "
        "configuration artefacts, not actual data processing.\n\n"
        "5. **Tokenisation service audit entries** — The tokenisation service "
        "itself logs both tokens and original values for its own audit trail; "
        "these logs are access-controlled separately and are part of the "
        "pseudonymisation mechanism, not a bypass."
    ),
    "22.1.24": (
        "1. **Scheduled penetration test activities** — Authorised penetration "
        "testing generates security events that should correlate with the "
        "approved test window in the change management system; suppress alerts "
        "during documented testing periods.\n\n"
        "2. **Red team exercise coordination** — Sanctioned red team activities "
        "may trigger security controls and generate evidence that appears as "
        "genuine attacks; cross-reference with the red team exercise register.\n\n"
        "3. **Vulnerability scanner noise** — Automated vulnerability scanners "
        "produce findings that require triage; new scan results may appear as "
        "security gaps before the remediation cycle classifies them.\n\n"
        "4. **Decommissioned system legacy findings** — Findings against systems "
        "scheduled for decommissioning within the accepted risk window may "
        "persist in reports until the system is retired.\n\n"
        "5. **Accepted risk items** — Vulnerabilities formally accepted through "
        "the risk management process with documented compensating controls "
        "appear as open findings in testing evidence but have governance "
        "approval."
    ),
    "22.1.25": (
        "1. **Post-incident review timeline** — The connection between a security "
        "incident and personal data impact may take several days to establish "
        "during forensic analysis; early alerts may not yet have impact "
        "classification.\n\n"
        "2. **Shared infrastructure incidents** — Incidents affecting shared "
        "infrastructure may be linked to personal data systems that were not "
        "actually impacted; the blast radius determination may initially "
        "over-scope.\n\n"
        "3. **Non-personal data systems misclassified** — Systems incorrectly "
        "tagged as containing personal data in the asset inventory create "
        "false linkages; verify the data classification register.\n\n"
        "4. **Resolved incidents without breach** — Security incidents that are "
        "contained before personal data is actually accessed (e.g., blocked "
        "intrusion attempts) may still appear in the tracking system.\n\n"
        "5. **Test/drill incidents** — Tabletop exercises and security drills "
        "that create test incident records for training purposes should be "
        "tagged as exercises to prevent false correlation."
    ),
    "22.1.26": (
        "1. **Planned maintenance windows** — Scheduled downtime for database "
        "maintenance, patching, or upgrades generates availability alerts that "
        "are pre-approved in the change schedule.\n\n"
        "2. **Failover testing** — Planned failover tests between primary and "
        "secondary data centres create brief availability gaps that are part "
        "of the resilience validation programme.\n\n"
        "3. **Auto-scaling events** — Cloud services scaling down during "
        "low-demand periods may temporarily reduce redundancy levels while "
        "maintaining the required minimum; this is by design.\n\n"
        "4. **Monitoring system false negatives** — Health check failures due "
        "to monitoring infrastructure issues (network partition to the monitor, "
        "not the service) may report downtime when the service is operational.\n\n"
        "5. **Graceful degradation modes** — Services operating in degraded "
        "mode (read-only, cached responses) during partial outages still "
        "protect personal data integrity while showing reduced availability "
        "metrics."
    ),
    "22.1.27": (
        "1. **Certification renewal cycles** — Annual certification renewals "
        "(ISO 27001, SOC 2) may show brief gaps between certificate expiry and "
        "reissuance while the audit report is finalised.\n\n"
        "2. **Attestation format differences** — Processors providing attestation "
        "through their own portal or format rather than the controller's template "
        "may appear as non-compliant until the evidence is mapped.\n\n"
        "3. **Sub-processor attestation flow** — Attestations flowing through "
        "the primary processor may arrive on different schedules than direct "
        "processor attestations, creating apparent gaps.\n\n"
        "4. **New contractual period transitions** — Contract renewals may reset "
        "attestation timelines, creating a new evidence collection window that "
        "appears as a gap from the previous period.\n\n"
        "5. **Evidence system migration** — Processors transitioning to new "
        "compliance management platforms may temporarily have evidence in "
        "both systems, with neither showing complete history."
    ),
    "22.1.28": (
        "1. **Standard sub-processor additions** — Changes to commonly-used "
        "sub-processors (e.g., CDN providers, email delivery services) listed "
        "in the processor's standard sub-processor register that fall within "
        "the pre-approved categories.\n\n"
        "2. **Internal reorganisation renames** — Sub-processors that change "
        "legal entity names due to corporate restructuring without changing "
        "the actual processing may appear as new sub-processors.\n\n"
        "3. **Notification latency** — Processors who notify sub-processor "
        "changes within the contractual notification period (typically 30 days) "
        "may show as changed before the controller's tracking system is "
        "updated.\n\n"
        "4. **General authorisation model** — Under Art.28(2) general written "
        "authorisation, the processor may add sub-processors unless the "
        "controller objects within the notice period; alerts during the "
        "objection window are informational, not violations.\n\n"
        "5. **Identical processing with entity change** — Acquisitions of "
        "sub-processors by other companies that continue identical processing "
        "may trigger change alerts without actual processing differences."
    ),
    "22.1.29": (
        "1. **Cross-timezone notification timing** — Processors in different "
        "time zones may report breaches within their contractual SLA based on "
        "their local business hours, creating apparent delays when measured "
        "against the controller's timezone.\n\n"
        "2. **Initial vs. full notification** — Processors providing an initial "
        "notification within SLA followed by a detailed report may appear to "
        "miss the SLA if only the detailed report timestamp is tracked.\n\n"
        "3. **Non-personal-data incidents** — Processors may report security "
        "incidents that do not constitute personal data breaches out of "
        "abundance of caution; these do not carry Art.33 notification obligations.\n\n"
        "4. **Communication channel delays** — Notifications sent via agreed "
        "channels (e.g., secure portal) that require controller login to "
        "acknowledge may show delivery timestamps later than actual send time.\n\n"
        "5. **Coordinated disclosure processes** — Processors participating in "
        "multi-party breach coordination may delay individual notification per "
        "law enforcement request under Art.33(3)."
    ),
    "22.1.30": (
        "1. **DPA refresh cycle alignment** — Data Processing Agreements under "
        "review for standard annual refresh may temporarily show obligations "
        "mapped to the previous version while the new version is executed.\n\n"
        "2. **Obligation inheritance from master agreements** — DPA obligations "
        "incorporated by reference from master service agreements may not appear "
        "in the DPA-specific control matrix but are contractually binding.\n\n"
        "3. **Regional DPA variations** — Multinational processors may have "
        "regional DPA supplements that carry obligations not present in the "
        "master DPA; check regional addenda.\n\n"
        "4. **Obligation mapping interpretation differences** — Different teams "
        "may map the same DPA clause to different control matrix entries based "
        "on interpretation; verify with legal for the canonical mapping.\n\n"
        "5. **Transitional processing during DPA negotiation** — Processing that "
        "continues under an interim arrangement while a new DPA is negotiated "
        "may show against the expired DPA's obligation set."
    ),
    "22.1.31": (
        "1. **Audit scheduling coordination** — Planned audits may be postponed "
        "due to mutual scheduling conflicts; a documented rescheduling does not "
        "constitute a compliance gap.\n\n"
        "2. **Remote audit acceptance** — Processors offering remote audit "
        "alternatives (questionnaires, video walkthroughs) per the DPA terms "
        "may not show traditional on-site audit evidence.\n\n"
        "3. **Third-party audit reliance** — Controllers relying on independent "
        "third-party audit reports (e.g., SOC 2 Type II) as permitted by the "
        "DPA may not conduct separate direct audits.\n\n"
        "4. **Audit evidence format differences** — Processors providing audit "
        "evidence through their compliance portal rather than direct document "
        "submission may have evidence not yet downloaded into the controller's "
        "system.\n\n"
        "5. **Annual audit cadence variations** — DPAs specifying 'no more than "
        "once annually' create legitimate gaps between audit periods that "
        "should not be flagged as non-compliance."
    ),
    "22.1.32": (
        "1. **Risk score recalculation pending** — Processing activities awaiting "
        "annual risk reassessment may show outdated scores; check the assessment "
        "schedule for pending reviews.\n\n"
        "2. **DPIA threshold interpretation changes** — Updated supervisory "
        "authority guidance on high-risk thresholds may reclassify previously "
        "low-risk activities; allow a reasonable adoption period.\n\n"
        "3. **Pre-GDPR processing grandfathering** — Activities operational "
        "before 25 May 2018 that have not materially changed may have lighter "
        "DPIA documentation per transitional provisions.\n\n"
        "4. **Grouped DPIA coverage** — Multiple processing activities covered "
        "under a single DPIA may individually appear as lacking coverage; "
        "check the DPIA scope statement for grouped activities.\n\n"
        "5. **Processing volume changes** — Activities that crossed the high-risk "
        "threshold due to organic growth may have a documented timeline for "
        "DPIA completion following the threshold trigger."
    ),
    "22.1.33": (
        "1. **Accepted residual risks** — Risks formally accepted through the "
        "governance process with documented compensating controls show as open "
        "items in the scoring dashboard but have appropriate approval.\n\n"
        "2. **Risk scoring methodology transitions** — Changes between risk "
        "scoring frameworks (qualitative to quantitative, or scale changes) "
        "may create apparent score jumps without actual risk changes.\n\n"
        "3. **Mitigation implementation in progress** — Risks with approved "
        "mitigation plans actively being implemented may show high residual "
        "scores until the control is operational.\n\n"
        "4. **Shared risk ownership ambiguity** — Risks shared between the "
        "controller and processor may have split ownership that creates "
        "incomplete scoring on either side's register.\n\n"
        "5. **Inherent vs. residual score confusion** — Dashboards showing "
        "inherent risk scores (before controls) rather than residual scores "
        "(after controls) may overstate the actual exposure."
    ),
    "22.1.34": (
        "1. **No high-risk processing identified** — Organisations whose "
        "processing activities do not meet the Art.35(1) high-risk threshold "
        "legitimately have no supervisory authority consultation records; "
        "verify the risk screening documentation.\n\n"
        "2. **Informal guidance vs. formal consultation** — Pre-emptive queries "
        "to the supervisory authority for guidance may not constitute formal "
        "Art.36 prior consultation; distinguish between informal and formal "
        "engagements.\n\n"
        "3. **DPIA mitigation sufficiency** — Where the DPIA identifies high "
        "residual risk but mitigations are subsequently implemented that reduce "
        "risk to acceptable levels, consultation is no longer required.\n\n"
        "4. **Consultation tracking system migration** — Historical consultation "
        "records may exist in a previous DPO's filing system rather than the "
        "current compliance platform.\n\n"
        "5. **Multi-jurisdiction consultation routing** — Cross-border processing "
        "requiring consultation with the lead supervisory authority may show as "
        "pending in local tracking systems while the lead authority responds."
    ),
    "22.1.35": (
        "1. **Remediation timeline extensions** — Formally approved timeline "
        "extensions for complex mitigations (e.g., system replacements) may "
        "show items as overdue against original dates while being on track "
        "per the revised approved schedule.\n\n"
        "2. **Dependency on third-party deliverables** — Remediation items "
        "dependent on vendor software releases or service changes may be "
        "blocked pending external delivery; document the dependency.\n\n"
        "3. **Partial closure criteria** — Remediation items with multiple "
        "sub-tasks may show as open when some components are complete; check "
        "completion criteria for staged closure approval.\n\n"
        "4. **Risk acceptance as alternative closure** — Items where the "
        "residual risk is formally accepted as an alternative to technical "
        "remediation should be closed as 'accepted' rather than remaining open.\n\n"
        "5. **Compensating control implementation** — Alternative controls "
        "implemented in lieu of the originally specified remediation may not "
        "match the closure criteria literally while providing equivalent "
        "protection."
    ),
    "22.1.36": (
        "1. **Adequacy decision changes** — Transfers to countries with recently "
        "invalidated adequacy decisions (e.g., post-Schrems) may require TIA "
        "updates that are in progress; check the TIA remediation timeline.\n\n"
        "2. **Standard assessment templates** — Transfers using standardised TIA "
        "templates (e.g., IAPP template) may have assessments stored in a "
        "different format than the tracking system expects.\n\n"
        "3. **Low-volume occasional transfers** — Art.49(1)(b) derogation for "
        "occasional transfers necessary for contract performance may not require "
        "a full TIA; verify the derogation documentation.\n\n"
        "4. **Group-level TIA coverage** — Corporate groups performing a single "
        "TIA covering all subsidiaries' transfers to a jurisdiction may not have "
        "individual entity-level assessments.\n\n"
        "5. **TIA refresh pending post-legislative change** — New legislation in "
        "the recipient country may trigger TIA refresh requirements; allow the "
        "documented reassessment period."
    ),
    "22.1.37": (
        "1. **SCC version transition periods** — Organisations transitioning "
        "from old SCCs to new EC 2021/914 SCCs within the regulatory deadline "
        "may show mixed SCC versions during the migration window.\n\n"
        "2. **Multi-module SCC complexity** — Transfers requiring multiple SCC "
        "modules (controller-to-processor and processor-to-processor) may show "
        "partial completion while all modules are being executed.\n\n"
        "3. **SCC supplementary measures** — SCCs requiring supplementary "
        "technical or organisational measures per Schrems II may show as "
        "incomplete if only the contractual clauses are tracked without the "
        "supplementary measures inventory.\n\n"
        "4. **Inter-company SCC management** — SCCs between group companies "
        "managed centrally may not appear in individual entity compliance "
        "tracking systems.\n\n"
        "5. **SCC execution timing for new processors** — New processor "
        "engagements may have SCCs in legal review during the contracting "
        "period with data processing not yet commenced."
    ),
    "22.1.38": (
        "1. **Metadata routing vs. data processing** — System metadata (DNS, "
        "routing information) may transit through restricted jurisdictions "
        "without personal data payload being processed there; distinguish "
        "between routing and processing.\n\n"
        "2. **Temporary failover to approved DR sites** — Automated failover "
        "to disaster recovery sites in permitted alternate jurisdictions is "
        "pre-authorised in the data localisation policy.\n\n"
        "3. **Content delivery network edge caching** — CDN caches in restricted "
        "jurisdictions serving static content without personal data do not "
        "constitute localisation violations; verify cached content classification.\n\n"
        "4. **Encryption in transit through restricted zones** — Encrypted data "
        "transiting through restricted jurisdictions without decryption keys "
        "present in that jurisdiction may be covered by the 'mere conduit' "
        "interpretation.\n\n"
        "5. **Support staff remote access** — Support personnel physically "
        "located in restricted jurisdictions accessing data through approved "
        "access controls with appropriate safeguards (SCCs/BCRs) represent "
        "controlled access, not data transfer for localisation purposes."
    ),
    "22.1.39": (
        "1. **Adequacy decision monitoring lag** — Newly published EC adequacy "
        "decisions may take time to be reflected in the monitoring system's "
        "reference data; manual verification against the official EU list "
        "may be needed.\n\n"
        "2. **Partial adequacy decisions** — Some jurisdictions have sector-"
        "specific adequacy (e.g., Japan's amended APPI coverage); transfers "
        "outside the covered sector require alternative safeguards.\n\n"
        "3. **UK adequacy bridge provisions** — Post-Brexit transitional "
        "adequacy provisions have specific expiry dates and renewal conditions "
        "that require monitoring distinct from full adequacy decisions.\n\n"
        "4. **Adequacy challenge proceedings** — Pending legal challenges to "
        "adequacy decisions (court referrals) may not immediately affect the "
        "validity of transfers; monitor for actual invalidation rulings.\n\n"
        "5. **Adequacy sunset provisions** — Adequacy decisions with built-in "
        "review periods approaching expiry require monitoring but remain valid "
        "until formal revocation or non-renewal."
    ),
    "22.1.40": (
        "1. **BCR approval processing time** — BCR applications submitted to "
        "the lead supervisory authority may take 12-18 months for approval; "
        "transfers under interim safeguards during this period are documented.\n\n"
        "2. **BCR scope amendments** — Changes to group structure (new entities, "
        "divestitures) requiring BCR amendments may show gaps while amendments "
        "are being processed; check the amendment application status.\n\n"
        "3. **Intra-group entity name changes** — Corporate restructuring that "
        "changes entity names without changing processing relationships may "
        "trigger BCR mapping alerts.\n\n"
        "4. **BCR annual compliance report timing** — The annual BCR compliance "
        "report to the supervisory authority may show temporary non-conformities "
        "being addressed as part of continuous improvement.\n\n"
        "5. **BCR training rollout phases** — New group entities being integrated "
        "into BCR training programmes may show compliance gaps during the "
        "onboarding period documented in the BCR implementation plan."
    ),
    "22.1.41": (
        "1. **Sanctioned SaaS evaluation periods** — IT teams evaluating new "
        "SaaS solutions during approved trial periods may generate cloud access "
        "patterns before formal approval; check the IT evaluation register.\n\n"
        "2. **BYOD personal cloud usage** — Employee personal cloud storage "
        "access from corporate networks that does not involve corporate data "
        "may be flagged as shadow IT; verify whether corporate data was "
        "actually uploaded.\n\n"
        "3. **Marketing technology tools** — Marketing teams using approved "
        "category-level authorisations for campaign tools may show as "
        "unapproved individual tools within an approved category.\n\n"
        "4. **API integration middleware** — Approved applications connecting "
        "through third-party integration platforms (Zapier, MuleSoft) may "
        "show the middleware as an unapproved service.\n\n"
        "5. **Browser-based utilities** — Non-data-processing web utilities "
        "(calculators, converters) accessed from corporate browsers do not "
        "constitute shadow SaaS processing personal data."
    ),
    "22.1.42": (
        "1. **Approved departmental tools** — Department-level approved tools "
        "not yet registered in the central IT asset inventory may appear as "
        "shadow IT; verify departmental approval records.\n\n"
        "2. **Personal device synchronisation** — Mobile device management "
        "solutions syncing non-personal-data configurations may generate "
        "traffic patterns resembling shadow IT without actual personal data "
        "processing.\n\n"
        "3. **External collaboration platforms** — Partners sharing documents "
        "through their own platforms (customer portals, vendor systems) require "
        "corporate users to access unregistered services legitimately.\n\n"
        "4. **Legacy application migrations** — Applications being migrated to "
        "approved platforms may show dual usage during transition, with the "
        "legacy instance appearing as shadow IT.\n\n"
        "5. **Training and certification platforms** — Employee access to "
        "training platforms (Coursera, LinkedIn Learning) for professional "
        "development may be flagged despite not processing operational "
        "personal data."
    ),
    "22.1.43": (
        "1. **ROPA update lag** — Processing activities registered but awaiting "
        "ROPA synchronisation may temporarily appear in systems not yet "
        "reflected in the latest ROPA export; check the ROPA update schedule.\n\n"
        "2. **System classification pending** — Newly deployed systems awaiting "
        "data classification assessment may temporarily appear as non-approved "
        "while the assessment completes.\n\n"
        "3. **Data processing that does not involve PII** — Systems processing "
        "only aggregated, anonymised, or non-personal operational data may be "
        "flagged by name-based detection when no personal data is actually "
        "present.\n\n"
        "4. **Testing environments with synthetic data** — Non-production "
        "environments processing synthetic data that mimics PII formats may "
        "trigger ROPA drift alerts without actual compliance risk.\n\n"
        "5. **Shared infrastructure services** — Infrastructure services "
        "(logging, monitoring, DNS) that process metadata from personal data "
        "systems may be flagged as non-approved personal data processing when "
        "they are support services documented under the system owner's ROPA "
        "entry."
    ),
    "22.1.44": (
        "1. **CDN and anycast routing** — Global content delivery networks "
        "routing requests through geographically distributed nodes may create "
        "cross-border flow patterns that are infrastructure-level, not "
        "application-level data transfers.\n\n"
        "2. **Geo-location accuracy limitations** — IP-based geolocation may "
        "misidentify the country of data flow endpoints, particularly for "
        "corporate VPNs, satellite internet, and mobile networks.\n\n"
        "3. **Legitimate business travel** — Employees accessing personal data "
        "systems while travelling internationally create cross-border access "
        "patterns that are controlled by the access policy.\n\n"
        "4. **Cloud provider internal replication** — Cloud infrastructure "
        "replicating data within the same legal jurisdiction across physically "
        "distributed data centres may create apparent cross-border flows when "
        "monitored at the network level.\n\n"
        "5. **DNS resolution and service discovery** — DNS queries and service "
        "mesh routing that traverse international networks do not constitute "
        "personal data transfers when only routing metadata is involved."
    ),
    "22.1.45": (
        "1. **Feature flags for progressive rollout** — New features deployed "
        "with privacy-protective defaults but tested with expanded settings "
        "for beta users who explicitly opted in may show non-default "
        "configurations.\n\n"
        "2. **Platform update default resets** — System updates that temporarily "
        "display reset defaults before user preferences are loaded from the "
        "profile store may appear as non-default settings during the brief "
        "loading window.\n\n"
        "3. **Admin configuration for organisational accounts** — Enterprise "
        "administrators configuring tenant-wide settings that override individual "
        "defaults per the organisational data processing agreement.\n\n"
        "4. **Accessibility accommodations** — Privacy settings adjusted for "
        "accessibility requirements (e.g., larger fonts requiring additional "
        "data display) that technically expand data visibility.\n\n"
        "5. **Consent-upgraded profiles** — Users who have explicitly consented "
        "to additional processing through the consent management platform have "
        "legitimately non-default settings."
    ),
    "22.1.46": (
        "1. **Consent version transitions** — During CMP configuration updates, "
        "brief periods may show consent records against outdated consent "
        "versions while the new configuration propagates to all touchpoints.\n\n"
        "2. **Implied consent for contract performance** — Processing necessary "
        "for contract performance under Art.6(1)(b) does not require consent; "
        "the absence of consent records for these purposes is correct.\n\n"
        "3. **Backend consent synchronisation** — Consent captured on one "
        "channel (web) may take time to propagate to all processing systems; "
        "check the consent propagation SLA.\n\n"
        "4. **Pre-GDPR user base** — Long-standing users whose accounts predate "
        "the current consent mechanism may have equivalent consent captured "
        "under previous terms accepted at registration.\n\n"
        "5. **Bot and crawler interactions** — Automated web crawlers and bots "
        "interacting with consent banners may generate consent events that are "
        "not associated with real data subjects."
    ),
    "22.1.47": (
        "1. **Legitimate processing purposes** — Data fields that appear "
        "excessive but serve documented processing purposes (e.g., IP addresses "
        "for security monitoring under legitimate interest) should be verified "
        "against the purpose register.\n\n"
        "2. **Regulatory requirements for data retention** — Fields retained for "
        "compliance with other regulations (AML, tax) that exceed GDPR "
        "minimisation expectations are justified by legal obligation basis.\n\n"
        "3. **Debugging and support metadata** — API request metadata logged for "
        "operational debugging that contains personal data identifiers is "
        "time-limited and access-controlled; verify retention period.\n\n"
        "4. **Schema evolution artefacts** — Deprecated API fields still present "
        "in responses due to backward compatibility requirements scheduled for "
        "removal in the next major version.\n\n"
        "5. **Enrichment for fraud detection** — Additional data points collected "
        "specifically for fraud prevention under Art.6(1)(f) that would "
        "otherwise appear excessive for the primary service purpose."
    ),
    "22.1.48": (
        "1. **Cross-purpose legitimate interest** — Data originally collected "
        "for one purpose reused for a compatible purpose under Art.6(4) "
        "compatibility assessment; verify the compatibility test documentation.\n\n"
        "2. **Security processing across all data** — Security monitoring that "
        "processes data across all purposes for anomaly detection operates "
        "under a separate security purpose; this is not purpose creep.\n\n"
        "3. **Analytics on aggregated data** — Processing that uses personal "
        "data as input but produces only aggregate outputs may appear as "
        "secondary purpose processing when it is a legitimate operational "
        "purpose.\n\n"
        "4. **Legal compliance requirements** — Processing required by law "
        "(reporting, audit) that uses data collected for a different purpose "
        "is explicitly permitted under Art.6(1)(c).\n\n"
        "5. **Data subject-initiated processing** — Users who voluntarily use "
        "features that process their data for additional purposes (e.g., "
        "recommendations) have actively triggered that processing."
    ),
    "22.1.49": (
        "1. **Retention holds from active litigation** — Legal holds that "
        "override automated deletion schedules are intentional and documented "
        "in the legal department's hold register.\n\n"
        "2. **Archive migration in progress** — Data moving from primary to "
        "archive storage may temporarily exist in both locations during the "
        "migration window without constituting over-retention.\n\n"
        "3. **Deletion job scheduling delays** — Automated deletion jobs running "
        "on weekly or monthly schedules may show data slightly beyond its "
        "retention period between job runs.\n\n"
        "4. **Regulatory reporting retention** — Data retained specifically for "
        "regulatory reporting cycles (quarterly, annual) beyond the operational "
        "retention period is covered under legal obligation basis.\n\n"
        "5. **Pseudonymised data retention** — Data that has been pseudonymised "
        "and retained for statistical purposes under Art.89 exemptions may "
        "appear as over-retained personal data when it is no longer directly "
        "identifiable."
    ),
    "22.1.50": (
        "1. **Privacy notice version transition** — During website updates, "
        "brief periods may serve the previous privacy notice version from CDN "
        "cache while the new version propagates.\n\n"
        "2. **Multi-language translation timing** — Privacy notice updates in "
        "the primary language may deploy before all translations are complete, "
        "showing version mismatches across language variants.\n\n"
        "3. **Acquired entity integration** — Newly acquired business units "
        "maintaining separate privacy notices during integration may show "
        "discrepancies until consolidated into the group notice.\n\n"
        "4. **Embedded third-party notices** — Third-party services embedded in "
        "the organisation's platform (payment processors, analytics) maintain "
        "their own privacy notices with independent update cycles.\n\n"
        "5. **Dark pattern audit false triggers** — Transparency checks that "
        "flag consent mechanisms as potentially deceptive may need manual "
        "review to distinguish between dark patterns and legitimate UX "
        "design choices."
    ),
}

# ---------------------------------------------------------------------------
# REFERENCES — per UC, expand to >= 4
# Common references pool for GDPR UCs:
GDPR_COMMON_REFS = [
    "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
]

REFS: dict[str, list[str]] = {
    "22.1.1": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.2": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2022-01/edpb_guidelines_012022_right-of-access_0.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/right-of-access/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.3": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_9-2022_personal_data_breach_notification_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/report-a-breach/personal-data-breach/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.4": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/the-principles/storage-limitation/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.6": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.7": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://www.enisa.europa.eu/publications/guidelines-for-smes-on-the-security-of-personal-data-processing",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.8": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/documentation/records-of-processing-and-lawful-basis/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.9": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-11/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-by-design-and-default/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.10": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://www.enisa.europa.eu/publications/guidelines-for-smes-on-the-security-of-personal-data-processing",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.11": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2022-01/edpb_guidelines_012022_right-of-access_0.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.12": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_9-2022_personal_data_breach_notification_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/report-a-breach/personal-data-breach/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.13": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_9-2022_personal_data_breach_notification_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/report-a-breach/personal-data-breach/personal-data-breach-examples/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.14": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-07/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.15": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/contracts-and-liabilities-between-controllers-and-processors-dp-guidance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.16": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2020-05/edpb_guidelines_202005_consent_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/consent/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.17": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/",
        "https://docs.splunk.com/Documentation/Splunk/latest/Security/Aboutauditevents",
    ],
    "22.1.18": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2023-02/edpb_guidelines_on_automated_individual_decision-making_and_profiling_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/automated-decision-making-and-profiling/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.19": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2022-01/edpb_guidelines_012022_right-of-access_0.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.20": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/legitimate-interests/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.21": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.enisa.europa.eu/publications/guidelines-for-smes-on-the-security-of-personal-data-processing",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/security/encryption/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.22": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://www.enisa.europa.eu/publications/guidelines-for-smes-on-the-security-of-personal-data-processing",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.23": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-04/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://www.enisa.europa.eu/publications/pseudonymisation-techniques-and-best-practices",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.24": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://www.enisa.europa.eu/publications/guidelines-for-smes-on-the-security-of-personal-data-processing",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.25": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_9-2022_personal_data_breach_notification_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/report-a-breach/personal-data-breach/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.26": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://www.enisa.europa.eu/publications/guidelines-for-smes-on-the-security-of-personal-data-processing",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.27": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/contracts-and-liabilities-between-controllers-and-processors-dp-guidance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.28": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/contracts-and-liabilities-between-controllers-and-processors-dp-guidance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.29": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_9-2022_personal_data_breach_notification_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/contracts-and-liabilities-between-controllers-and-processors-dp-guidance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.30": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/contracts-and-liabilities-between-controllers-and-processors-dp-guidance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.31": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/contracts-and-liabilities-between-controllers-and-processors-dp-guidance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.32": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-07/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.33": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-07/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.34": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-07/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/when-do-we-need-to-do-a-dpia/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.35": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-07/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.36": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-data-transfer-agreement/transfer-risk-assessments/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.37": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://ec.europa.eu/info/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en",
        "https://www.edpb.europa.eu/system/files/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.38": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.39": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://ec.europa.eu/info/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en",
        "https://www.edpb.europa.eu/system/files/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.40": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/our-documents/recommendations/recommendations-012020-measures-supplement-transfer_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/binding-corporate-rules/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.41": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.42": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.43": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/documentation/records-of-processing-and-lawful-basis/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.44": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.45": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-11/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-by-design-and-default/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.46": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2020-05/edpb_guidelines_202005_consent_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/consent/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.47": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2019-11/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/the-principles/data-minimisation/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.48": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/the-principles/purpose-limitation/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.49": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/the-principles/storage-limitation/",
        "https://splunkbase.splunk.com/app/263",
    ],
    "22.1.50": [
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://www.edpb.europa.eu/system/files/2022-10/edpb_guidelines_082022_right_of_access_en.pdf",
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/",
        "https://splunkbase.splunk.com/app/263",
    ],
}

# ---------------------------------------------------------------------------
# DATA SOURCES EXPANSIONS — for UCs currently under 80 chars
# ---------------------------------------------------------------------------

DATASOURCES: dict[str, str] = {
    "22.1.9": (
        "Application configuration exports, database schema metadata, API "
        "endpoint field inventories, CMP consent scope definitions, and ROPA "
        "field-level data dictionaries"
    ),
    "22.1.17": (
        "Splunk internal audit logs (_audit index), syslog integrity metadata, "
        "file integrity monitoring (FIM) events, NTP synchronisation status, "
        "and SIEM forwarding chain health checks"
    ),
    "22.1.19": (
        "DSAR ticketing system exports (ServiceNow, Jira), consent management "
        "platform logs, identity verification workflow events, and Art.12 "
        "response correspondence tracking records"
    ),
    "22.1.34": (
        "DPO consultation register exports, supervisory authority correspondence "
        "logs, DPIA output documents with residual risk scores, and Art.36 "
        "formal consultation application records"
    ),
    "22.1.35": (
        "DPIA remediation trackers, project management system exports (Jira, "
        "Azure DevOps), risk register updates, and mitigation closure evidence "
        "including compensating control documentation"
    ),
    "22.1.36": (
        "Transfer impact assessment registers, legal basis documentation for "
        "third-country transfers, supplementary measures inventories, and "
        "adequacy decision monitoring feeds"
    ),
    "22.1.37": (
        "Contract management system exports, SCC execution records and metadata, "
        "supplementary technical measures documentation, and vendor onboarding "
        "compliance workflow events"
    ),
    "22.1.42": (
        "Network proxy logs, CASB (Cloud Access Security Broker) discovery events, "
        "endpoint DLP alerts, DNS query logs for unclassified SaaS domains, and "
        "mobile device management traffic classification"
    ),
    "22.1.44": (
        "Network flow data (NetFlow/sFlow), firewall geo-location enriched logs, "
        "cloud provider VPC flow logs with region tags, CASB transfer events, "
        "and DNS resolution geolocation lookups"
    ),
    "22.1.48": (
        "Application access logs with purpose codes, data warehouse query audit "
        "trails, consent management platform scope definitions, API gateway "
        "request logs with client application identifiers, and ROPA purpose "
        "mapping exports"
    ),
}


def apply_changes(path: Path) -> list[str]:
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
        changes.append(f"expanded dataSources ({len(DATASOURCES[uid])} chars)")

    if not changes:
        return []

    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(out, "utf-8")
    return changes


def main() -> None:
    files = sorted(
        CONTENT.glob("UC-22.1.*.json"),
        key=lambda p: int(p.stem.split(".")[-1]),
    )
    print(f"Processing {len(files)} GDPR UCs...")
    modified = 0
    for f in files:
        ch = apply_changes(f)
        if ch:
            uid = f.stem.replace("UC-", "")
            print(f"  UC-{uid}: {', '.join(ch)}")
            modified += 1
    print(f"\nModified {modified}/{len(files)} files.")


if __name__ == "__main__":
    main()
