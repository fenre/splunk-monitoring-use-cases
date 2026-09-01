# UC identifier bulk-migration manifests

When a pull request changes more than **10** UC identifiers (adds, removes, or
remaps sidecar files under `content/cat-*/UC-*.json`), CI requires a committed
manifest in this directory.

## Format

Each manifest is a JSON file validated against
[`schemas/uc-id-migration.schema.json`](../../schemas/uc-id-migration.schema.json).

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

`identityPreserved` must be `true` when the title+SPL fingerprint is unchanged
(content moved only). Set `false` when the identifier now refers to different
content (strongly discouraged; prefer leaving a gap and issuing a new id).

## CI gate

`python -m splunk_uc audit-uc-id-migration-blast --check` compares the PR diff
against `origin/main` (or `GITHUB_BASE_REF` in Actions). Every detected change
must appear in a manifest file touched by the same PR.
