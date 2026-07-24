"""Load domain-pack reference material for hand-craft lift prompts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PACKS_DIR = REPO_ROOT / "data" / "domain-packs"

# Sidecar path substring -> default pack id
_CATEGORY_PACK_HINTS: tuple[tuple[str, str], ...] = (
    ("cat-25-personal", "personal-hec"),
    ("cat-01-server-compute", "linux-nix-ta"),
    ("cat-09-identity", "windows-ta"),
    ("cat-04-cloud", "aws-azure-gcp"),
    ("cat-10-security", "es-notables"),
    ("cat-22-regulatory", "compliance-by-regulation"),
)


def resolve_pack_path(pack_id: str, *, packs_dir: Path | None = None) -> Path:
    root = packs_dir if packs_dir is not None else DEFAULT_PACKS_DIR
    return root / f"{pack_id}.json"


def infer_pack_id(sidecar_path: Path) -> str | None:
    path_str = str(sidecar_path)
    for needle, pack_id in _CATEGORY_PACK_HINTS:
        if needle in path_str:
            return pack_id
    return None


def load_domain_pack(pack_id: str, *, packs_dir: Path | None = None) -> dict[str, Any] | None:
    path = resolve_pack_path(pack_id, packs_dir=packs_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def format_pack_excerpt(pack: dict[str, Any], *, max_chars: int = 6000) -> str:
    """Render a compact excerpt for injection into lift-prompt."""
    chunks: list[str] = []
    if pack.get("purpose"):
        chunks.append(f"Purpose: {pack['purpose']}")
    if pack.get("pack_id"):
        chunks.append(f"Pack ID: {pack['pack_id']}")

    kfps = pack.get("kfps") or pack.get("packs", {})
    if isinstance(kfps, list):
        chunks.append("KFP scenarios (adapt — do not copy verbatim):")
        for item in kfps[:6]:
            if isinstance(item, dict):
                chunks.append(f"- {item.get('scenario', item)}")
            else:
                chunks.append(f"- {item}")
    elif isinstance(kfps, dict):
        chunks.append("Pack sections:")
        for key in list(kfps.keys())[:4]:
            chunks.append(f"- {key}")

    troubleshooting = pack.get("troubleshooting")
    if isinstance(troubleshooting, list):
        chunks.append("Troubleshooting modes:")
        for item in troubleshooting[:4]:
            if isinstance(item, dict):
                chunks.append(f"- {item.get('symptom', item)}")

    text = "\n".join(chunks)
    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text
