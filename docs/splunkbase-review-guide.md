# Splunkbase mapping SME review guide (v9.0)

> **Status**: active from v9.0 onwards. Required gate for clearing
> `requiresSmeReview: true` on every UC's `splunkbaseApps[]` array.
> **Audience**: project maintainers and Splunk engineers familiar with
> the Splunkbase app catalog and the equipment slug → TA mapping.
> **What this is**. A concise rubric for reviewing the Splunkbase-app
> mappings that `scripts/generate_splunkbase_mappings.py` proposes for
> every UC. SME sign-off is the gate that flips a proposed mapping
> from "machine-drafted" to "human-verified" and unlocks the recommender
> app's per-card "Required Splunkbase apps" UI from a hedged "Splunkbase
> mapping pending" state to confident install guidance.

---

## 1. What you are reviewing

Each UC sidecar under `content/cat-*/UC-*.json` may now carry a
`splunkbaseApps[]` array (added in `uc.schema.json` v1.7.0). Every
machine-drafted entry has `requiresSmeReview: true`. Your job is to
confirm three things per entry, in order:

1. **The id is correct.** The numeric `id` matches the actual Splunkbase
   app the UC depends on. No typos, no guesses, no deprecated apps.
2. **The role is correct.**
   - `primary` — the app the UC is built on (usually the TA).
   - `data-source` — supplies the events/metrics consumed by the UC.
   - `premium` — Splunk premium app (ES, ITSI, SOAR, UBA, PCI, MLTK,
     Edge Hub).
   - `optional` — recommended but not required to make the UC work.
3. **The name is the canonical Splunkbase displayName.** Pull it from
   `data/splunkbase-catalog.json` (or from the live Splunkbase page if
   the catalog is stale).

If all three are correct, clear `requiresSmeReview` (delete the field
or set it to `false`) and record the sign-off. If any are wrong, fix
the entry first; only a *correct* mapping should be signed off.

## 2. How to review in batches (recommended)

Reviewing 7,300+ UCs one at a time is impractical. The expected workflow
batches by **equipment slug**: the `equipment[]` field on each UC names
the upstream technology (e.g. `cisco-meraki`, `linux`, `vmware`), and
each equipment slug has a small, well-known Splunkbase app set. Reviewing
all UCs that share an equipment slug at once is fast and consistent.

```
# 1. List the open backlog grouped by equipment slug:
python3 scripts/review_splunkbase_mappings.py list

# 2. Pick an equipment slug, list its open UCs:
python3 scripts/review_splunkbase_mappings.py list --equipment cisco-meraki

# 3. Inspect each UC. Open `content/cat-NN/UC-X.Y.Z.json` and verify the
#    `splunkbaseApps[]` array. Fix any wrong entries by hand.
# 4. When the batch is correct, sign off the whole equipment group:
python3 scripts/review_splunkbase_mappings.py signoff \
    --equipment cisco-meraki \
    --reviewer "Pat Smith (Splunk PS)" \
    --pr "#1234"
```

The signoff command:

* Strips `requiresSmeReview: true` from every UC in the batch.
* Appends one entry to `data/provenance/splunkbase-mappings-signoffs.json`
  with the reviewer, PR, commit SHA, equipment scope, and the list of UC
  ids covered.
* Keeps the JSON sorted and deterministic so the diff is reviewable.

## 3. Acceptable shortcuts

* **Catalog-only deletion**. If a proposed entry references an app that
  is not actually used by the UC, simply remove that entry from
  `splunkbaseApps[]` (do not just clear `requiresSmeReview`). Fewer
  entries is better than wrong entries.
* **Empty array**. A UC with `"splunkbaseApps": []` means "no Splunkbase
  app required" (typical for UCs that lean on built-in indexes or
  forwarders only). This is a valid sign-off state.
* **Hand-editing after sign-off**. The migration generator
  (`scripts/generate_splunkbase_mappings.py`) preserves any UC whose
  `splunkbaseApps[]` has at least one entry without `requiresSmeReview:
  true`. Once you have signed off, your edits are stable.

## 4. What blocks merge

The audit `tools/audits/splunkbase_coverage.py` runs in CI and tracks
the open backlog. Until v9.0 GA we **do not** fail the build on missing
sign-offs (the migration is staged); from v9.0 GA onward, the audit
fails the build for any UC that lacks `splunkbaseApps[]` entirely or
where every entry still carries `requiresSmeReview: true`. Coverage % is
reported in [`README.md`](../README.md) so progress is visible to the
project.

## 5. Provenance and trust chain

`data/provenance/splunkbase-mappings-signoffs.json` is ingested by
`python -m splunk_uc generate-mapping-ledger` (impl. `src/splunk_uc/generators/mapping_ledger.py`) and covered by the Sigstore
attestation on `data/provenance/mapping-ledger.json`. Auditors verifying
the recommender's install guidance can therefore prove that every
machine-proposed mapping was reviewed by a named SME before the v9.0
release. See [`docs/architecture.md`](architecture.md) for the broader
provenance story.
