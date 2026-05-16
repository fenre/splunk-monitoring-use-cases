"""Local-only research helpers — build read-only reference vocabularies
from third-party SPL corpora dropped into ``external/``.

This package is intentionally outside ``src/splunk_uc/`` because it does
not run in CI and never ships in our distributed wheel. The audits in
``splunk_uc.audits`` consult its emitted JSON when present, and
gracefully degrade to Splunk-core-baseline-only when it is not.
"""
