# Alert action templates

Task **H-4** emits derivative alert-action templates for every use case in
the catalogue. The generator reads UC sidecars under `content/cat-*/` (read
only) and writes three artefacts per UC under `dist/alert-actions/`:

| Path | Purpose |
|------|---------|
| `dist/alert-actions/soar/UC-X.Y.Z.yaml` | Splunk SOAR playbook stub (import manually) |
| `dist/alert-actions/email/UC-X.Y.Z.html` | HTML email body (tiered by `criticality`) |
| `dist/alert-actions/email/UC-X.Y.Z.txt` | Plain-text email fallback |

`dist/alert-actions/` is gitignored — rebuild on demand or in CI smoke runs.

## Quick commands

```bash
# Full corpus (local only; ~7.9 k UCs)
PYTHONPATH=src python3 -m splunk_uc generate-alert-actions

# CI drift guard (golden fixtures + smoke-render 20 UCs)
PYTHONPATH=src python3 -m splunk_uc generate-alert-actions --check --limit 20

# One UC
PYTHONPATH=src python3 -m splunk_uc generate-alert-actions --only UC-1.1.1

# High/critical UCs first when iterating
PYTHONPATH=src python3 -m splunk_uc generate-alert-actions --criticality high
```

Makefile targets: `make generate-alert-actions`, `make audit-alert-actions`.

## Severity tiering

Email subject lines and body tone follow the UC `criticality` field:

| `criticality` | Subject prefix | Tone |
|---------------|----------------|------|
| `critical`, `high` | `[CRITICAL] … immediate action required` | Urgent, action-first |
| `medium` | `[ALERT] … fired` | Investigative, context-first |
| `low` | `[INFO] … aggregated digest` | Digest / batched review |

SOAR stubs always set `human_acknowledgement_required: true` and include a
`do_not_section` block. OT/safety-adjacent UCs (category heuristics, equipment
tags, or narrative keywords) receive expanded OT escalation language per the
VISTA OT safety boundary.

## SOAR import (manual)

There is **no SOAR sandbox in CI**. After generating templates:

1. In Splunk SOAR, open **Playbooks → Import**.
2. Select `dist/alert-actions/soar/UC-X.Y.Z.yaml` for the UC tied to your
   saved search / correlation search.
3. Replace `escalation_contact_placeholder: "{customer-on-call}"` with your
   on-call roster, PagerDuty service, or SOAR contact list.
4. Wire the playbook to the Splunk adaptive response or ES notable workflow
   that fires on the UC SPL.
5. Tabletop-test OT-touching playbooks with OT engineering present before
   enabling automated actions.

The YAML is a **stub** aligned with SOAR import conventions (`name`,
`description`, metadata tags, SPL reference). It is not a complete visual
playbook export — maintainers extend branches (`investigate`, `notify`) in
SOAR after import.

## Email template import

Generated HTML uses table layout and inline CSS for broad mail-client
compatibility. Runtime placeholders left for the alerting platform:

- `{timestamp_placeholder}` — substituted when the alert fires
- `{spl_summary}` — first line of the firing SPL or platform-provided summary

Typical import paths:

- **Splunk Enterprise alert email action** — paste HTML into a custom email
  action or store the file and reference it from your alert manager.
- **SOAR / external ticketing** — use the `.txt` fallback for systems that
  strip HTML.

## Customisation guide

| Field / knob | Where to change |
|--------------|-----------------|
| Escalation contact | SOAR YAML `escalation_contact_placeholder` at import time |
| Email subject pattern | `templates/alert-actions/email-digest.*.template` |
| SOAR playbook metadata | `templates/alert-actions/soar-playbook.yaml.template` |
| SPL truncation limit (4000 chars) | `SPL_MAX_CHARS` in `generators/alert_actions.py` |
| Catalogue base URL | `CATALOGUE_BASE_URL` constant in the generator |

After editing templates, regenerate golden fixtures:

```bash
PYTHONPATH=src python3 -c "
from pathlib import Path
import sys; sys.path.insert(0,'src')
from splunk_uc.generators.alert_actions import load_uc_record, render_templates, write_templates
root = Path('tests/fixtures/alert-actions')
for uc in ('1.1.1','1.1.10','1.2.20'):
    p = sorted(Path('content').glob(f'cat-*/UC-{uc}.json'))[0]
    write_templates(render_templates(load_uc_record(p)), root)
"
PYTHONPATH=src python3 -m splunk_uc generate-alert-actions --check --limit 20
```

## Verification

CI step **Alert actions generator drift (Task H-4)** runs:

```bash
PYTHONPATH=src python3 -m splunk_uc generate-alert-actions --check --limit 20
```

Golden fixtures live under `tests/fixtures/alert-actions/` (3 UCs × 3 files).
Unit tests: `pytest tests/splunk_uc/generators/test_alert_actions.py -v`.

## Template engine

Templates use stdlib `string.Template` (`.template` suffix) — no Jinja2
runtime dependency. User-derived fields escape `$` so SPL dashboard tokens
survive rendering intact.
