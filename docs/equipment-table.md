# Equipment Table (Filter by "What You Have")

The dashboard lets users **filter use cases by equipment** they have (e.g. "Windows servers", "AWS", "Palo Alto"). This is powered by an **equipment table** that maps **IT equipment / platforms** to **Splunk add-ons (TAs)** and product terminology mentioned in use cases.

## How It Works

1. **Equipment table** (`EQUIPMENT` in `tools/build/enrichment.py`)
   Each entry has:
   - **id** — slug used in the UI and in use case data (e.g. `windows`, `aws`).
   - **label** — user-facing name (e.g. "Windows servers & workstations").
   - **tas** — list of substrings; if **any** of these appears in a use case's narrative text (see §3 for the authoritative matching rules), that use case is considered relevant for this equipment.
   - **models** (optional) — for hardware, a list of models/variants (each with id, label, tas) so the main list stays short; matching use cases get compound ids in **`uc.em`**.

2. **Per-use case equipment tags** (post–Phase 5.5 structured authoring)
   Every use case's tags live in two places:
   - **Compact `uc.e` / `uc.em`** in `catalog.json` and the built SPA payload — consumed by the UI dropdown and by the flat `/api/v1/recommender/uc-thin.json` endpoint.
   - **Structured `equipment[]` / `equipmentModels[]`** in each UC JSON (`content/cat-*/UC-*.json`) — validated against `schemas/uc.schema.json` and exposed on `/api/v1/compliance/ucs/{id}.json`, `/api/v1/compliance/ucs/index.json`, and the per-equipment facade at `/api/v1/equipment/{id}.json`.

3. **Precedence and matching**
   The build resolves each UC's `uc.e` / `uc.em` in the following order:

   1. **Structured sidecar fields first.** If `content/cat-*/UC-*.json` has `equipment[]` and/or `equipmentModels[]`, those values are the source of truth. Before Phase 5.5 only the `app` (App/TA) field of each UC was matched against the EQUIPMENT table, which produced a **33% false-negative rate on cat-22 regulatory UCs** — equipment like Azure AD, OPC UA, Modbus, ServiceNow, and Palo Alto GlobalProtect was referenced in `spl` / `dataSources` / `implementation` but invisible to the UI's equipment filter. Sidecar-first resolution closes that gap.
   2. **Legacy substring fallback.** For UCs without explicit equipment arrays, the build falls back to the original `EQUIPMENT.tas` substring match against the curated `app` text. This is bounded to the curated App/TA text, so false positives from narrative prose are avoided at the cost of leaving some equipment hidden — those UCs should get explicit `equipment[]` over time.

4. **UI**
   The **Equipment** dropdown lets users pick one equipment type. For equipment with **models** (e.g. **Hardware / BMC**), a second **Model** dropdown (sub-search) appears so users can filter by a specific model (e.g. Dell iDRAC, HPE iLO). "All models" filters by **`uc.e`**; a chosen model filters by **`uc.em`**. The main content and header count update accordingly.

## Where the Table Is Defined

- **Source of truth:** `tools/build/enrichment.py` — constant **`EQUIPMENT`** (list of `{id, label, tas}` and optional **models**).
- **Shared accessor:** `scripts/equipment_lib.py` — surgically parses the `EQUIPMENT` literal from the repo's build inputs so generators and linters use the same registry without importing the whole pipeline.
- **Per-UC writer:** `python3 -m splunk_uc generate-equipment-tags` — computes `equipment[]` / `equipmentModels[]` for every sidecar by substring-matching `app` + `dataSources` + `spl` + `implementation` + `description`. Deterministic, idempotent, `--check` mode for CI drift detection, `--report` mode for coverage stats.
- **Schema:** `schemas/uc.schema.json` defines both fields as `array` of `string`s with `uniqueItems: true` and slug patterns (`^[a-z0-9][a-z0-9_]*$` for equipment ids, `^[a-z0-9][a-z0-9_]*_[a-z0-9][a-z0-9_]*$` for compound model ids).
- **Output:** Emitted into **`catalog.json`** and the static site bundles as **`EQUIPMENT`**; each use case in **`DATA`** has **`e`** and **`em`** arrays.

## Structured Sidecar Fields: `equipment[]` and `equipmentModels[]`

Every UC JSON under `content/cat-*/UC-*.json` gets two equipment arrays:

```jsonc
{
  "id": "22.10.22",
  "title": "Remote ePHI Access — MFA Gap for VPN + O365 Clinical Mail",
  "equipment": ["azure", "exchange", "m365", "paloalto"],
  "equipmentModels": ["paloalto_globalprotect"],
  "…": "…"
}
```

Rules:

- **Generator-owned.** The fields are rewritten by `python3 -m splunk_uc generate-equipment-tags` on every run; do not hand-edit them. If you need to claim equipment coverage that the narrative text does not mention, add the appropriate term to the UC's `app` / `dataSources` / `implementation` / `spl` field (the places an auditor would read) so the generator picks it up.
- **Deterministic.** Values are sorted; the compound model ids use the `{equipmentId}_{modelId}` form consumed by the UI.
- **Schema-validated.** `python3 -m splunk_uc audit-compliance-mappings` runs `schemas/uc.schema.json` against every sidecar; any unknown slug or pattern mismatch blocks merges.
- **Lint-guarded.** `python3 -m splunk_uc audit-compliance-mappings` emits an informational `equipment-orphan` finding (warn-level, baselineable) whenever a cat-22 UC's narrative mentions equipment that is not in `equipment[]` / `equipmentModels[]`. This is the belt-and-suspenders check that catches drift between the generator and a hand-edited sidecar.
- **Outside the signed provenance ledger.** Equipment tags are an attribute of the UC's detection surface, not a compliance claim. They are therefore intentionally *excluded* from the `canonicalHash` in `data/provenance/mapping-ledger.json` — adding or changing an equipment tag mutates the sidecar's git commit hash (so the ledger's `firstSeenCommit` / `lastModifiedCommit` pointers still move) but does not alter the merkle root of compliance mappings.

## API Endpoints That Surface Equipment

After Phase 5.5 the `/api/v1/` static JSON tree exposes equipment at three layers:

| Endpoint | Shape |
| --- | --- |
| `/api/v1/compliance/ucs/{uc_id}.json` | Full sidecar, including `equipment[]` and `equipmentModels[]`. |
| `/api/v1/compliance/ucs/index.json` | Compact per-UC list with `equipment` and `equipmentModels` surfaced alongside `mitreAttack`, `regulationIds`, etc. |
| `/api/v1/recommender/uc-thin.json` | Compact records across the full **7,364**-UC catalogue with `equipment` / `equipmentModels` (drives the recommender UI). |
| `/api/v1/equipment/index.json` | Flat equipment registry → UC + regulation rollup (all 105 equipment slugs and 66 model compounds). |
| `/api/v1/equipment/{equipment_id}.json` | Per-equipment detail: UCs grouped by category, regulations grouped by framework with clause mappings. Answers the auditor question *"if I log equipment X, which regulatory clauses does it help me satisfy?"*. |

These endpoints are regenerated by `python3 -m splunk_uc generate-api-surface` and gated by the `api/v1/ regeneration check` CI step.

## Adding or Changing Equipment

1. Edit **`EQUIPMENT`** in **`tools/build/enrichment.py`**.
2. Add or adjust entries, e.g.:
   - **id:** unique slug (e.g. `new_platform`).
   - **label:** name shown in the dropdown.
   - **tas:** list of substrings that appear in a UC's narrative when the equipment is relevant (e.g. `["Splunk_TA_foo", "Foo Bar"]`). Matching is case-insensitive. Keep each substring ≥4 characters to avoid false-positives against unrelated prose.
   - **models** (optional): list of `{ "id": "model_slug", "label": "Display name", "tas": ["substring1", ...] }`. Use this for hardware (or other equipment) where you want a **sub-search** so the main equipment list doesn't get too long. The UI shows a second "Model" dropdown when this equipment is selected.
3. Regenerate the sidecars: **`python3 -m splunk_uc generate-equipment-tags`**. Review the diff; the generator only touches the two equipment arrays on each sidecar so `git diff --stat content/` stays scoped.
4. Regenerate the build outputs: **`make build`** or **`python3 tools/build/build.py --out dist`**. This rewrites `catalog.json` / `dist/` using the new sidecar tags.
5. Regenerate the API surface: **`python3 -m splunk_uc generate-api-surface`**.
6. Run the audit: **`python3 -m splunk_uc audit-compliance-mappings`** (validates schema, regulations, and the `equipment-orphan` lint).

Use cases that mention any of the **tas** strings in their narrative will then get that equipment **id** in `equipment[]` / `uc.e` and appear when the user selects that equipment. If the equipment has **models**, matching use cases also get compound ids in `equipmentModels[]` / `uc.em` (e.g. `hardware_bmc_idrac`) so users can filter by a specific model in the sub-dropdown.

## Coverage Snapshot (post-Phase 5.5)

The table below summarises the structured equipment footprint across the catalogue as of the last generator run. Counts come from `/api/v1/equipment/index.json` — regenerate to refresh.

- **105 equipment slugs** registered (see `EQUIPMENT` in `tools/build/enrichment.py`).
- **66 model compounds** (`equipmentId_modelId`) registered across hardware, network, and security product families.
- **~5,257 use cases** (~71% of the **7,364**-UC catalogue) carry at least one equipment tag *(re-run the generator and endpoint export for exact counts).*
- **941 of 1,287 cat-22 regulatory UCs** (73%) carry equipment tags — up from 65% before sidecar-first resolution closed the false-negative gap described above.
- **509 cat-22 UCs now carry two or more equipment tags**, versus ~137 pre-fix, closing the cross-equipment correlation gap that auditors hit when filtering on combinations like "Azure AD + Palo Alto GlobalProtect".

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Broadcom Inc. / VMware. (2026). *VMware vSphere Documentation*. Broadcom Inc. Retrieved May 11, 2026, from https://docs.vmware.com/en/VMware-vSphere/

<a id="ref-2"></a>**[2]** Cisco Meraki. (2026). *Cisco Meraki Documentation*. Cisco Systems, Inc. Retrieved May 11, 2026, from https://documentation.meraki.com/

<a id="ref-3"></a>**[3]** Cisco Systems, Inc. (2026). *Cisco Catalyst Center Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/site/us/en/products/networking/catalyst-center/index.html

<a id="ref-4"></a>**[4]** The Kubernetes Authors. (2026). *Kubernetes Documentation*. Cloud Native Computing Foundation. Retrieved May 11, 2026, from https://kubernetes.io/docs/

<a id="ref-5"></a>**[5]** Microsoft Corporation. (2026). *Microsoft Entra ID Documentation*. Retrieved May 11, 2026, from https://learn.microsoft.com/en-us/entra/identity/

<a id="ref-6"></a>**[6]** Microsoft Corporation. (2026). *Windows Server Documentation*. Retrieved May 11, 2026, from https://learn.microsoft.com/en-us/windows-server/

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

### Cited by

- [`README.md`](../README.md)
- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)
- [`docs/inventory-and-sizing.md`](inventory-and-sizing.md)
- [`docs/knowledge-graph-guide.md`](knowledge-graph-guide.md)

<!-- END-AUTOGENERATED-SOURCES -->
