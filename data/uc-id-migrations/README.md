# UC identifier bulk-migration manifests

When a pull request changes more than **10** UC identifiers (adds, removes,
remaps, or same-id fingerprint churn on sidecar files under
`content/cat-*/UC-*.json`), CI requires a committed manifest in this directory.

## Format

Each manifest is a JSON file validated against
[`schemas/uc-id-migration.schema.json`](../../schemas/uc-id-migration.schema.json).

### Identifier remap (one row per change)

```json
{
  "schemaVersion": "1.0.0",
  "description": "Human-readable summary of why this bulk remap happened",
  "changes": [
    {
      "kind": "remap",
      "from": "25.100.1",
      "to": "25.7.129",
      "identityPreserved": true,
      "note": "Optional curator note"
    }
  ]
}
```

### Content edit with preserved identity (bulk row)

When many identifiers keep the same id but title/SPL changes (for example
refreshing a deprecated SPL command across a cluster of related use cases), use
one bulk row instead of repeating `fingerprint_change` per id:

```json
{
  "schemaVersion": "1.0.0",
  "description": "Refresh deprecated stats syntax across cluster-monitoring UCs",
  "changes": [
    {
      "kind": "bulk_fingerprint_change",
      "identifiers": [
        "3.1.1",
        "3.1.2",
        "3.1.3"
      ],
      "identityPreserved": true,
      "reason": "Replace stats count with eventstats per Splunk 9.3 search reference; detection intent unchanged"
    }
  ]
}
```

`identityPreserved` must be `true` when monitoring intent is unchanged
(editorial SPL/title refresh only). Set `false` when the identifier now refers
to different content (strongly discouraged; prefer leaving a gap and issuing a
new id).

Per-identifier rows remain valid when you only need to declare a handful of
changes:

```json
{
  "kind": "fingerprint_change",
  "from": "3.1.1",
  "to": "3.1.1",
  "identityPreserved": true,
  "note": "Optional per-row note"
}
```

### Retiring a duplicate (remove row with a pointer)

When two use cases cover the same detection, delete the duplicate's sidecar
and add a `remove` row whose `to` names the use case that is kept. The
identifier stays retired and is never reissued
([ADR-0016](../../docs/adr/0016-permanent-uc-identifiers.md)).
`generate-id-ledger` copies `to` into the removed entry's `replacedBy`, and
fails if `to` is not an active use case:

```json
{
  "kind": "remove",
  "from": "10.3.587",
  "to": "10.3.300",
  "identityPreserved": false,
  "note": "Ran the same ESCU search as UC-10.3.300. UC-10.3.300 is kept."
}
```

## CI gate

`python -m splunk_uc audit-uc-id-migration-blast --check` compares the **whole
PR** — `git diff <merge-base>...HEAD` from `origin/main` (or
`GITHUB_BASE_REF` in Actions) — so splitting work into commits of nine inside
one PR does not bypass the threshold. Every detected change must appear in a
manifest file touched by the same PR.
