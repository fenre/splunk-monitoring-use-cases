# Use Case Quality Mandate

> **This document is the law for all agents authoring use cases in this
> repository. Read it before touching any UC file. No exceptions.**

## The mandate

**Quality is king. Content must be true, accurate, and well-researched.**

- Do NOT save on tokens. Use as many as needed to get the content right.
  Quality is the only metric that counts.
- A user should be able to find ALL the information they need about what
  the use case does, the value it brings, and what is needed to implement
  it — from the UC content alone.
- Every statement must be factually correct and verifiable against vendor
  documentation, the TA's actual behavior, or the product's API reference.
- Never invent field names, API paths, error messages, UI navigation paths,
  RBAC roles, or version numbers. If you don't know, look it up. If you
  can't verify it, say so explicitly rather than guessing.
- Never pad content to make it longer. Short and accurate beats long and
  fabricated. Length is never a goal. Accuracy is.
- Sources and references go in the `references` field of the UC JSON.

---

## The three quality tests

Every UC must pass all three tests before it is considered done:

### 1. The page test

"If I printed this UC and handed it to a junior engineer with Splunk access,
could they implement a working detection without opening any other document?"

If the answer is no, the UC is not done.

### 2. The accuracy test

"Is every field name, API path, RBAC role, UI path, and error message in
this UC factually correct?"

If any statement is invented or guessed, either verify it or replace it
with honest language ("verify the exact field name in your environment").

### 3. The value test

"Does every sentence add information the reader needs?"

If a sentence is padding — restating what the SPL already shows, repeating
the description in the DI, or offering generic advice — delete it.

---

## Before writing anything

### Build domain knowledge first

Read these in priority order before writing any UC content:

1. **The subcategory's integration guide** (e.g., `docs/guides/catalyst-center.md`)
   — field dictionaries, sourcetype tables, API paths, TA input names, RBAC
   requirements, sizing, troubleshooting
2. **The `_category.json`** for the subcategory — TA, data sources, existing UCs
3. **The TA's actual configuration** — `props.conf`, `inputs.conf` stanza names,
   field extractions (from Splunkbase<sup class="ref">[<a href="#ref-5">5</a>]</sup> listing or TA documentation)
4. **Vendor API documentation** — verify endpoint paths, response schemas, fields
5. **Existing sibling UCs** — cross-reference for consistency in field names,
   API paths, RBAC descriptions, and shared facts
6. **Domain packs if they exist** (e.g., `data/catalyst-center-domain-packs.json`,
   `data/nis2-domain-packs.json`) — canonical facts for cross-UC coherence

### Read the quality standards

- `docs/gold-standard-template.md` — tier definitions, 5-step structure, exemplars
- `docs/gold-standard-authoring-playbook.md` — the batch-uplift methodology
- This document — the quality mandate

### Assess the subcategory holistically

Before touching individual UCs:
- Are there redundant or near-duplicate UCs? Propose consolidation.
- Are there obvious monitoring gaps not yet covered?
- What tier target is appropriate given the product's complexity?

---

## Implementation strategy

### Hand-write every UC

**Do NOT delegate UC content authoring to sub-agents.**

Sub-agents take shortcuts:
- They template KFPs with generic phrases instead of naming real scenarios
- They write "check splunkd.log" instead of naming the exact input and error
- They invent field names and API paths to fill templates
- They break cross-UC coherence by inventing different facts for the same data source

The correction passes cost more than writing correctly the first time.

When uplifting a batch of UCs:
1. Read the domain pack and integration guide for the batch's data sources
2. Read every UC in the batch to understand current content
3. For each UC, in sequence:
   a. Read the existing content fully
   b. Identify every gap against the quality contract
   c. Hand-write the complete uplift
   d. Apply the three quality tests before moving to the next UC
4. After the batch: run `audit_gold_profile.py` against the batch files

---

## Quality principles

- **Product knowledge over template filling.** Understand what the product
  does and how the TA collects data. Write from that understanding.
- **Accuracy over volume.** A correct 2,000-character DI is better than an
  invented 12,000-character DI. Length is never a goal.
- **Fewer excellent UCs beat many shallow ones.** If 15 UCs are threshold
  variations of the same alert, consolidate into fewer UCs with tuning guidance.
- **Distinct description vs value.** Description says *what it detects*.
  Value says *why it matters to the business*. Never duplicate them.
- **Honest scope.** State PII sensitivity, licensing needs, version
  constraints, and what the UC does *not* cover.
- **Cross-UC coherence.** Sibling UCs sharing a data source must use the same
  field names, API paths, TA names, and RBAC descriptions. If one UC says
  the RBAC role is `SUPER-ADMIN-ROLE`, every sibling UC using that API must
  say the same — not a different spelling or a different role.

---

## The detailedImplementation structure

Use the 5-step structure. The structure ensures completeness; the content
within each section must be researched and accurate.

### Prerequisites

What must already be true before starting:
- Product/platform version requirements (verified against vendor docs)
- TA name, Splunkbase ID, minimum version, install scope (UF/HF/SH)
- RBAC roles or service account permissions (exact role name)
- Network access requirements (ports, protocols, proxy considerations)
- License requirements (Splunk and vendor-side)
- Baseline knowledge expected

Only include what you can verify. Do not invent version constraints.

### Step 1 — Configure data collection

Specific, actionable, verified instructions:
- **Name the modular input** by its exact stanza name in `inputs.conf`
- **Name the API path** (verified against vendor API documentation)
- **State the default poll interval** (verified against TA defaults)
- **Expected event volume** per entity per poll (estimate honestly)
- **Key fields** — list every field name the SPL depends on.
  Only list fields that actually exist in the data.

A section that says "Install the TA and enable the input" without naming
*which* input, *which* API path, and *which* fields is padding. It fails
quality review.

### Step 2 — Create the search and alert

- SPL in a fenced code block
- **"Understanding this SPL"** — why these thresholds? What should be tuned?
  What does each pipeline stage do? What are the tradeoffs?
- **Pipeline walkthrough** for complex SPL
- Scheduling, throttle, and alert action recommendations

### Step 3 — Validate

Concrete checks the reader can actually perform:
- Compare to vendor UI (name the specific path only if you know it is accurate)
- Spot-check specific records against the source of truth
- Gap detection query (`timechart count` over 24h)
- Field validation query

Every check should be a specific action with expected output.

### Step 4 — Operationalize

- Dashboard layout (panel types, positions, time pickers)
- Access control (which Splunk role, why)
- Runbook: numbered remediation steps with decision points
- Alerting integration recommendations
- Capacity review cadence if applicable

### Step 5 — Troubleshooting

Failure modes that genuinely occur with this TA and data source:
- Each with: symptom, root cause, and fix
- Must be product-specific, not generic
- Draw from integration guide troubleshooting, common TA behaviors (auth
  expiry, API throttling, pagination), and known platform behaviors
- Only describe failure modes you can reason about from the product's actual
  behavior. Never invent error messages or log entries.

---

## Per-field quality contract

### `description` (≥80 chars)

What is detected. Names the monitorable surface and the detection rule.
Specific enough that a reader knows exactly what triggers this UC without
reading the SPL.

### `value` (≥80 chars, distinct from description)

Why it matters to the business. Names the consequence of NOT having this
detection. If `description` and `value` read similarly, rewrite both.

### `dataSources`

Fully specified, factually accurate: index, sourcetype, API endpoint path
(verified against vendor docs), TA input name, default poll interval, key
extracted fields. Only list fields that actually exist in the data.

### `app`

TA name with Splunkbase ID and minimum version. Premium apps (ES, ITSI,
SOAR) go in `premiumApps[]`. Verify the Splunkbase ID is correct.

### `spl`

Must run against the fields named in `dataSources`. No invented field names,
no placeholder indexes, no `your_lookup_here`. The SPL should produce
actionable output with stable column names.

### `knownFalsePositives`

Realistic scenarios that actually occur in production. Each scenario:
- (a) Names a system, process, or condition (specific, not generic)
- (b) States how to distinguish it from a real finding
- (c) Names the suppression mechanism (lookup, time filter, or config)

Do not invent scenarios to hit a count target. 3 well-researched KFPs
are better than 6 made-up ones.

### `visualization`

Concrete and implementable: panel types, field names in columns, time
picker defaults, drilldown behavior, how it fits in a broader dashboard.
Not "table and chart."

### `references` (≥4 for gold)

Authoritative links. Every gold UC gets at minimum:
1. Splunkbase link for the TA
2. Vendor API/product documentation for the specific feature monitored
3. The integration guide (if one exists for the subcategory)
4. A topic-specific reference relevant to THIS UC's subject

### `grandmaExplanation` (≤400 chars)

"We" voice. No jargon. No `index=`, no SPL, no MITRE, no `Splunkbase`,
no `TA`, no `CIM`, no API paths, no acronyms. One to three sentences.
Read existing exemplars in the subcategory to match the voice.

### `implementation`

The TL;DR of `detailedImplementation`. Compressed runbook for someone who
knows Splunk. This is distinct from the DI — it's the summary, not the guide.

---

## Anti-patterns that fail review

| Anti-pattern | Why it fails |
|---|---|
| `cimModels: ["N/A"]` | Omit the field instead |
| Description and value say the same thing | They serve different audiences |
| "Install the TA and enable the input" | Which TA? Which input? What index? |
| Five DI sections with one sentence each | Structure without depth |
| Invented field names or API paths | Misleads the implementer |
| Invented error messages or log entries | Creates false expectations |
| Generic KFPs: "planned maintenance" | Name the maintenance, the SPL to distinguish, the suppression |
| Generic troubleshooting: "check splunkd.log" | Name the input, the error pattern, the fix |
| Padding sentences | Every sentence must add information |
| Character count targets leading to fabrication | Accuracy over volume, always |
| 15 UCs for the same alert with different thresholds | Consolidate with tuning guidance |

---

## Field requirements by tier

**Gold** (API-polled products, complex TAs):
All of: `criticality`, `difficulty`, `monitoringType`, `splunkPillar`,
`dataSources` (index + sourcetype + API path), `app` (with Splunkbase ID),
`spl`, `description` (≥80 chars), `value` (≥80 chars, distinct from
description), `implementation`, `detailedImplementation` (5 sections with
product-specific detail), `visualization`, `references` (≥4),
`equipment`, `equipmentModels`, `grandmaExplanation`, `wave`,
`prerequisiteUseCases`, `knownFalsePositives`.

**Silver** (syslog-based, simpler integrations):
Core fields + `detailedImplementation` (3+ sections),
`references` (≥2). `equipmentModels` optional.

**Bronze** (minimum viable):
`criticality`, `difficulty`, `spl`, `description`, `value`,
`dataSources`, `app`, `implementation`.

---

## After writing

1. **Validate:** Run `python3 -m splunk_uc audit-gold-profile --files <changed files>`
2. **Fix failures** — the audit checks for shallow content, not just missing fields
3. **Update counts:** If UCs were added or consolidated, update
   `useCaseCount` in `_category.json` subcategory entries

## JSON is the source of truth

Edit only the `.json` files under `content/`. Everything else is derived.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

### Cited by

- [`docs/mitre-attack-mapping.md`](mitre-attack-mapping.md)

<!-- END-AUTOGENERATED-SOURCES -->
