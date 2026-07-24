"""Hand-craft validation helpers for ``lift-validate --require-handcraft``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from splunk_uc.audits._template_fingerprints import (
    check_domain_token_binding,
    check_minimum_substantive_delta,
    detect_template_flags,
    narrative_similarity,
)
from splunk_uc.tools.lift._common import load_sidecar, resolve_sidecar_path

SIMILARITY_CAP = 0.85


def validate_handcraft(
    *,
    original: dict[str, Any],
    lifted: dict[str, Any],
    lifted_field_names: set[str],
    anchor_uc: str | None = None,
    batch_manifest: Path | None = None,
    content_root: Path | None = None,
) -> list[str]:
    """Return refusal reasons; empty list means hand-craft gates passed."""
    reasons: list[str] = []

    remaining_flags = detect_template_flags(lifted)
    if remaining_flags:
        reasons.append(
            "template provenance: enricher fingerprints remain: "
            + ", ".join(remaining_flags)
        )

    reasons.extend(check_domain_token_binding(lifted))
    reasons.extend(
        check_minimum_substantive_delta(original, lifted, lifted_field_names)
    )

    if anchor_uc:
        try:
            anchor_path = resolve_sidecar_path(anchor_uc, content_root=content_root)
            anchor_data = load_sidecar(anchor_path)
            ratio = narrative_similarity(lifted, anchor_data)
            if ratio >= SIMILARITY_CAP:
                reasons.append(
                    f"cross-UC similarity: narrative {ratio:.2f} >= {SIMILARITY_CAP} "
                    f"vs anchor {anchor_uc}"
                )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            reasons.append(f"cross-UC similarity: cannot load anchor {anchor_uc!r}: {exc}")

    if batch_manifest and batch_manifest.is_file():
        try:
            manifest = json.loads(batch_manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            reasons.append(f"batch manifest unreadable: {exc}")
        else:
            uc_ids = manifest.get("ucs") or manifest.get("uc_ids") or []
            lifted_id = str(lifted.get("id", ""))
            for other_id in uc_ids:
                other_bare = str(other_id).removeprefix("UC-")
                if other_bare == lifted_id:
                    continue
                try:
                    other_path = resolve_sidecar_path(str(other_id), content_root=content_root)
                    other_data = load_sidecar(other_path)
                except (FileNotFoundError, RuntimeError, ValueError):
                    continue
                ratio = narrative_similarity(lifted, other_data)
                if ratio >= SIMILARITY_CAP:
                    reasons.append(
                        f"cross-UC similarity: narrative {ratio:.2f} >= {SIMILARITY_CAP} "
                        f"vs batch sibling {other_id}"
                    )
                    break

    return reasons
