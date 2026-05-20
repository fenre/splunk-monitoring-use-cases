# SARIF emission — DevSecOps reporting for catalogue audits

Lane D (2026-05-19) adds a [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/) export path so Splunk operators can ingest catalogue quality findings into GitHub Code Scanning, Azure DevOps, GitLab, or Splunk SOAR<sup class="ref">[<a href="#ref-2">2</a>]</sup> without bespoke parsers.

## What SARIF is

SARIF (Static Analysis Results Interchange Format) is an OASIS standard JSON schema for static-analysis and quality-gate findings. DevSecOps platforms already know how to index SARIF: severity, rule metadata, file locations, and result messages.

This repository emits SARIF from **existing audit JSON reports** — not from a new linter. The generator normalizes heterogeneous audit shapes into one SARIF log per audit plus a combined `dist/sarif/catalogue.sarif`.

## Which audits flow into SARIF

| Audit | Source report | Typical findings |
|-------|---------------|------------------|
| `audit-spl-references` | `dist/audits/spl-references.json` | Unknown macros, sourcetypes, datamodel paths |
| `audit-spl-grammar` | `dist/audits/spl-grammar.json` | Invalid `stats span=`, leading pipes, glued searches |
| `audit-spl-hallucinations` | `dist/audits/spl-hallucinations.json` | Unknown SPL commands, bad CIM datasets |
| `audit-prerequisites` | `dist/audits/prerequisites.json` | Cycles, unknown prerequisite IDs, wave violations |
| `audit-content-quality` | `dist/audits/content-quality.json` | Description/value dupes, jargon in plain language |
| `audit-uc-structure` | `dist/audits/uc-structure.json` | Missing required sidecar fields |

CI collects JSON via `--json` redirects (where supported) or committed reports such as `reports/prerequisites-audit.json`. The standalone [`.github/workflows/sarif.yml`](../.github/workflows/sarif.yml) workflow runs the full pipeline and uploads to GitHub Code Scanning.

## Rule ID convention

Every SARIF result uses:

```text
splunk-uc:<audit-name>:<finding-kind>
```

Examples:

- `splunk-uc:spl-references:unknown-command`
- `splunk-uc:prerequisites:unknown-prereq`
- `splunk-uc:content-quality:description-equals-value`

The `<finding-kind>` segment is derived from the audit's `category`, `issue`, or error prefix (lowercased, non-alphanumerics collapsed to `-`).

## Severity mapping

| Audit severity | SARIF `level` |
|----------------|---------------|
| `info`, `low` | `note` (omitted unless `--include-info`) |
| `warn`, `medium`, `med` | `warning` |
| `fail`, `high`, `error` | `error` |

Mapping is deterministic and applied in `src/splunk_uc/generators/sarif_emit.py`.

## Commands

```bash
# Emit combined + per-audit SARIF (reads dist/audits/*.json by default)
PYTHONPATH=src python3 -m splunk_uc generate-sarif --out dist/sarif

# Drift-guard: regenerate in memory and compare to on-disk SARIF
PYTHONPATH=src python3 -m splunk_uc generate-sarif --check --out dist/sarif

# Restrict to one audit or cap findings
PYTHONPATH=src python3 -m splunk_uc generate-sarif --audit spl-grammar --limit 100

# Validate SARIF shape + rule/location invariants
PYTHONPATH=src python3 -m splunk_uc audit-sarif --check
```

Makefile shortcuts: `make generate-sarif`, `make audit-sarif`.

## GitHub Code Scanning upload

The standalone SARIF workflow uploads `dist/sarif/catalogue.sarif` with `github/codeql-action/upload-sarif@v3`:

```yaml
permissions:
  contents: read
  security-events: write

- uses: github/codeql-action/upload-sarif@v3
  if: always()
  with:
    sarif_file: dist/sarif/catalogue.sarif
    category: splunk-uc-catalogue
```

For a custom pipeline, use [`actions/upload-sarif@v3`](https://github.com/github/codeql-action/tree/main/upload-sarif) the same way after running `generate-sarif`.

## Splunk SOAR ingestion

SOAR can treat SARIF as structured alert input:

1. **Scheduled pull** — Run `generate-sarif` in CI and publish `catalogue.sarif` to object storage or an artifact feed.
2. **Custom ingestion app** — Parse SARIF `runs[].results[]`:
   - `ruleId` → detection name
   - `level` → urgency (`error` → high, `warning` → medium, `note` → low)
   - `locations[].physicalLocation.artifactLocation.uri` → affected UC sidecar path
   - `properties.ucId` → catalogue UC identifier for downstream `get_use_case` lookups
3. **Playbook pattern** — On `level=error` for SPL audits, open a container tagged `catalogue-spl-quality`, attach the SARIF message, and route to the content steward queue. Do not auto-modify UC sidecars from SOAR; human review remains the contract.

Example minimal Python snippet for a SOAR custom action:

```python
import json
from pathlib import Path

sarif = json.loads(Path("catalogue.sarif").read_text(encoding="utf-8"))
for run in sarif.get("runs", []):
    for result in run.get("results", []):
        if result.get("level") != "error":
            continue
        uri = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        yield {
            "name": result["ruleId"],
            "severity": result["level"],
            "file": uri,
            "message": result["message"]["text"],
            "uc_id": result.get("properties", {}).get("ucId"),
        }
```

## Schema pinning

Generated logs set:

- `"$schema": "https://json.schemastore.org/sarif-2.1.0.json"`
- `"version": "2.1.0"`

`audit-sarif --check` verifies both fields, rule registration, level enums, and that artifact URIs resolve to repo paths or synthetic `content/cat-NN/UC-X.Y.Z.json` sidecar paths.

## Related docs

- [`AGENTS.md`](../AGENTS.md) — CI gates that produce upstream audit JSON
- [OASIS SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/) — normative specification

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk SOAR (Cloud) Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SOARonprem

<details>
<summary>Additional online sources cited in the document body (2)</summary>

<a id="ref-3"></a>**[3]** docs.oasis-open.org. *SARIF 2.1.0*. Retrieved May 11, 2026, from https://docs.oasis-open.org/sarif/sarif/v2.1.0/

<a id="ref-4"></a>**[4]** github.com. *GitHub: github/codeql-action*. Retrieved May 11, 2026, from https://github.com/github/codeql-action/tree/main/upload-sarif

</details>

<!-- END-AUTOGENERATED-SOURCES -->
