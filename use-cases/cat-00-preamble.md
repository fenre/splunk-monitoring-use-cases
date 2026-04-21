# Splunk Core Infrastructure Monitoring — Enriched Use Case Repository

> A comprehensive collection of IT infrastructure monitoring use cases for Splunk,
> enriched with criticality ratings, example SPL, implementation guidance, and visualization recommendations.

### Legend

| Field | Description |
|-------|-------------|
| **Criticality** | 🔴 Critical — Service-impacting, immediate action needed · 🟠 High — Significant risk if not monitored · 🟡 Medium — Operational value, supports proactive management · 🟢 Low — Nice-to-have, reporting/compliance focused |
| **Difficulty** | 🟢 Beginner — Simple SPL, single data source, standard TA setup · 🔵 Intermediate — Multi-command SPL, some custom config or tuning · 🟠 Advanced — Complex SPL, deep product knowledge, custom scripts/integrations · 🔴 Expert — ML/anomaly detection, multi-system correlation, specialized threat hunting |
| **Value** | Why this use case matters to the business or operations team |
| **App/TA** | Splunk add-on or app required (free unless marked *Premium*) |
| **Data Sources** | Sourcetypes, indexes, or log paths needed |
| **SPL** | Example Splunk search (simplified — adapt indexes/sourcetypes to your environment) |
| **Implementation** | Key steps to get this use case running |
| **Monitoring type** | Analytics, Anomaly, Audit, Availability, Business, Capacity, Change, Compliance, Configuration, Cost, Data Quality, DevSecOps, Fault, Fraud, Governance, Inventory, Operations, Patient Safety, Performance, Physical Security, Quality, Reliability, Resilience, Revenue Assurance, Risk, Safety, Security, Trading, Vulnerability |
| **Visualization** | Recommended dashboard panel type(s) |
| **Wave** *(optional)* | Implementation wave — `crawl` (foundation: turn on the TA and ship one panel or alert), `walk` (intermediate: refines or correlates a crawl signal), or `run` (advanced: depends on multiple crawls/walks). Drives the per-category *Crawl → Walk → Run* roadmap and the in-panel wave badge. See [docs/implementation-ordering.md](../docs/implementation-ordering.md). |
| **Prerequisite UCs** *(optional)* | Comma-separated list of `UC-X.Y.Z` ids that should be implemented first (shared data sources, lookups, ITSI services, macros, etc.). Rendered as clickable "Implement first" chips in the UC panel and reverse-indexed into an "Enables" list on every referenced UC. Validated by [`scripts/audit_prerequisites.py`](../scripts/audit_prerequisites.py) — unknown ids, self-references, and cycles fail CI. |

---

