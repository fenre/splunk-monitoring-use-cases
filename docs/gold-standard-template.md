# Gold Standard Template

> **The quality test:** Could an engineer who has never used this product
> implement this UC end-to-end from this page alone? If not, what's missing?

This document defines what quality looks like for use cases in this catalog.
It is the contract that all authoring — human or AI — must satisfy.

## Guiding Principles

1. **Quality is operational utility.** A UC is good when it gives someone
   everything they need to go from zero to a working implementation.
2. **Fewer excellent UCs beat many shallow ones.** If a subcategory has
   redundant UCs (same alert, different thresholds), consolidate them.
3. **Product knowledge over template filling.** The 5-step structure is a
   means to operational depth, not the end itself. A section that says
   "Install the TA and enable the input" without naming *which* input is
   padding, not content.
4. **Honest scope.** State what the UC does *not* cover. Note PII sensitivity,
   licensing requirements, version constraints.

---

## Quality Tiers

### Gold — "implement from this page alone"

For product integrations with API-polled data, complex TAs, or multi-step
configurations. The UC contains everything an engineer needs.

**All fields required.** See `schemas/uc-profile-gold.json` for the full list.

### Silver — "implement with some external reference"

For syslog-based or simpler integrations where the "Configure" step is
genuinely short. The UC has good depth but may point to vendor docs for
some details.

**Core fields required** plus `detailedImplementation` with 3+ substantive
sections and at least 1 reference.

### Bronze — "understand and start investigating"

Minimum viable. The UC has enough metadata, SPL, and a short implementation
note to be useful, but lacks depth.

**When Bronze is acceptable:** draft UCs, UCs pending vendor documentation,
simple metric checks where the implementation truly is "enable one input."

---

## The 5-Step detailedImplementation Structure

This structure ensures operational completeness. Each step has a purpose —
adapt the depth to the product's complexity, but never skip the *intent*.

### Prerequisites

What must already be true before starting:
- Product/platform version requirements (e.g. "Catalyst Center 2.3.5+")
- Licensing requirements (e.g. "Assurance license required")
- RBAC roles or service account permissions (e.g. "SUPER-ADMIN-ROLE")
- Network access requirements (e.g. "Splunk HF must reach the API endpoint")
- Link to the app install guide if applicable

### Step 1 — Configure data collection

Specific, actionable instructions:
- **Name the modular input** (e.g. "enable the `devicehealth` input")
- **Name the API path** (e.g. "`GET /dna/intent/api/v1/device-health`")
- **State the default poll interval** (e.g. "900 seconds / 15 minutes")
- **Expected event volume** (e.g. "one event per managed device per poll")
- **Key fields to validate** in Search (list field names the SPL depends on)

### Step 2 — Create the search and alert

- Present the SPL in a fenced code block
- Include an **"Understanding this SPL"** explanation:
  - Why these thresholds? What should be tuned?
  - What does `latest()` / `stats` / `eval` do in this context?
  - When would you add filters or change the `by` clause?
- **Pipeline walkthrough** for complex SPL

### Step 3 — Validate

How to verify the data is correct and complete:
- **Compare counts** to the vendor UI (name the specific UI location)
- **Spot-check specific records** (pick two known devices/events, compare)
- **Check for gaps** (`timechart count` over 24h to find silent periods)
- **Field validation** (are expected fields present and populated?)

### Step 4 — Operationalize

- Dashboard layout suggestions (where to place this panel)
- Recommended time ranges for different audiences
- Access control considerations
- Runbook integration (what to do when the alert fires)
- Scheduling recommendations

### Step 5 — Troubleshooting

**Product-specific failure modes**, not generic advice:
- "No events → check RBAC role, verify API endpoint URL, look for ERROR in splunkd.log for *this specific input name*"
- "All values NULL → confirm licensing, verify feature is enabled in vendor UI"
- "Fewer records than expected → check scope/filter, virtual domain configuration"
- "Stale timestamps → NTP, proxy timeouts, API throttling (specific HTTP codes)"

---

## Anti-Patterns

| Anti-pattern | Example | Why it's bad |
|---|---|---|
| Duplicated description/value | `"description": "BGP drops cause outages."` / `"value": "BGP drops cause outages."` | Description says *what*, value says *why it matters*. They serve different audiences. |
| Generic boilerplate | "Step 1 — Install the TA and enable the input." | Which TA? Which input? What index? This could apply to any UC. |
| Padding the 5 steps | Five sections with one sentence each | The structure exists to hold depth. If the product is simple, Silver is the right tier. |
| "N/A" in populated fields | `"cimModels": ["N/A"]` | Omit the field instead. "N/A" pollutes filters. |
| Threshold variations | 15 UCs for "CPU > 70%", "CPU > 80%", "CPU > 90%" | Consolidate into one UC that explains threshold tuning. |
| Missing vendor UI reference | Validation says "check the data looks right" | Name the specific vendor page/screen to compare against. |

---

## Exemplar: UC-5.13.1

The Catalyst Center subcategory (5.13) is the reference implementation.
UC-5.13.1 "Device Health Score Overview" demonstrates Gold quality:

- **dataSources** names index, sourcetype, *and* API path with poll interval
- **detailedImplementation** runs ~2,500 words with API paths, RBAC roles,
  version requirements, vendor UI comparison points, and specific failure modes
- **description** and **value** are distinct: "what it monitors" vs "why NOC cares"
- **grandmaExplanation** is jargon-free: "We watch the health of every network
  device managed by Catalyst Center..."
- **wave** is `crawl` with empty `prerequisiteUseCases` (foundational UC)
- **references** link to Splunkbase, vendor API docs, and the integration guide

Read the full file at `content/cat-05-network-infrastructure/UC-5.13.1.json`.

---

## Consolidation Guidance

During uplift, actively look for consolidation opportunities:

**Merge when:**
- Multiple UCs share >80% of the same SPL with different thresholds
- UCs are trivial variations (same alert, different severity labels)
- UCs could be one UC with a "tuning" section explaining variants

**Keep separate when:**
- UCs serve different audiences (NOC vs Security vs Capacity)
- UCs use different sourcetypes or data sources
- UCs have genuinely different implementation prerequisites
- One is crawl-tier and another is walk/run-tier with real dependencies

**After consolidation:** update `_category.json` use case counts,
update `prerequisiteUseCases` references in other UCs, and note the
consolidation in the PR description.
