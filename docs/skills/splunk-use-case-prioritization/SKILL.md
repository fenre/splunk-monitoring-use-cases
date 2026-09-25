---
name: splunk-use-case-prioritization
description: >
  Author and consume Splunk monitoring use-case recommendation profiles.
  Use when ranking "which use cases first" for a product, writing a
  recommendation profile, mapping VISTA wizard context, or reviewing
  equipment tags for ISE, Palo Alto, Linux, VMware, AWS, or Kubernetes.
  Do NOT use for compliance evidence packs — those live in docs/evidence-packs/.
---

# Splunk use-case prioritization

Copy of the VISTA skill for catalog authors who do not have the VISTA
checkout. Canonical consumer implementation lives in Splunk-Vista
`methodology/skills/splunk-use-case-prioritization/`. Sync via
`python3 methodology/tools/sync-skills.py sync` in VISTA.

## Source order

1. Vendor operations docs (HA, certificates, control plane).
2. Splunk Lantern / TA documentation.
3. SRE practice (SLOs, saturation, error budgets) — qualitative only.
4. Catalogue gold UCs that already implement those controls.

Never invent ROI. Customer stories are measurement patterns only.

## Profile authoring

- File: `data/recommendation-profiles/<slug>.json`
- Schema: `schemas/recommendation-profile.schema.json`
- Ordered core pack of 5–10 existing `ucId` values.
- If a cited control has no UC, author the UC first.
- Linux means OS telemetry, not every mention of Linux.
- Review date and `sourceIds` from `data/source-references.json` are required.

## Mapping

- Graph and VISTA consume compact `graph-recommend.json` /
  `api/v1/recommender/profiles.json`.
- Value = profile rank. Readiness = prereqs, data, suites, maturity, inventory.
- Classes: Start now; High value, unblock first; Foundation; Later.
- Quality tier is confidence, not value.
- Zero-context copy: "Best-practice starting point."

## VISTA

- Fetch profiles only when the catalogue toggle is on (air-gapped default off).
- Map wizard vertical, outcomes, suites, and maturity into the shared context
  object used by `graph-recommend.js`.
- Badge Recommended from profile core IDs and `public_catalog_ids`, not
  vertical alone.
- Fill `public_catalog_ids` on curated VISTA UCs that map to Fenre IDs.

## Freshness

Re-review profiles when vendor docs or TA sourcetypes change, or when a
core UC is retitled. Run `python -m splunk_uc generate-recommendation-profiles --check`.

## Verification

- Every `ucId` exists in `content/`.
- ISE-titled UCs have `cisco_ise`. Palo Alto is not tagged on VMware titles.
- Anchor UCs appear in the top 5/10 for each pilot product.
