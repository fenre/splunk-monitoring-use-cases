"""tools.validate — pre-build validation of source-of-truth content.

Runs before ``tools/build/build.py`` so that bad content fails fast with
a precise per-file pointer instead of a stack trace deep inside the
renderer.

Modules
-------
validate_md         Per-UC validator (validates content/cat-NN-slug/UC-X.Y.Z.{md,json}
                    against schemas/uc.schema.json, checks SPL syntax, CIM compliance).
                    Successor to scripts/run_uc_tests.py.
"""

__all__ = ["validate_md"]
