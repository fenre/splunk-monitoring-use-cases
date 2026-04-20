"""tools.build.build_info — emit dist/BUILD-INFO.json.

Per docs/architecture.md, every release publishes a BUILD-INFO.json
adjacent to ``integrity.json``. The file lets downstream consumers:

* Pin to a known catalogue version without trusting the URL alone.
* Verify the schema versions a particular ``/api/v1/`` payload was built
  against (cross-checked against ``schemas/`` headers).
* Audit the build environment (git SHA, Python version, builder).

Stability
---------
Field set is fixed by docs/api-versioning.md. New fields are additive
only. Removing or renaming a field is a major version bump.
"""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

from .parse_content import Catalog


def write(out_dir: Path, catalog: Catalog, *, reproducible: bool = False) -> Path:
    project_root = catalog.project_root
    payload: dict[str, Any] = {
        "$schema": "/schemas/v2/build-info.schema.json",
        "version": "2.0.0",
        "catalogueVersion": _read_version(project_root),
        "apiVersion": "v1",
        "git": _git_info(project_root),
        "build": {
            "timestamp": _build_timestamp(project_root, reproducible=reproducible),
            "reproducible": reproducible,
            "python": platform.python_version(),
            "platform": platform.platform() if not reproducible else "ubuntu-latest",
            "tool": "tools/build/build.py",
            "toolVersion": _own_version(),
        },
        "counts": {
            "categories": len(catalog.categories),
            "regulations": len(catalog.regulations),
            "useCases": catalog.uc_count,
        },
        "schemas": _schema_versions(project_root),
        "stability": {
            "urls": "frozen-at-v7.0.0",
            "api": "v1 active",
            "schemas": "see /schemas/v2/index.json",
        },
    }

    out_path = out_dir / "BUILD-INFO.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def _read_version(project_root: Path) -> str:
    p = project_root / "VERSION"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _own_version() -> str:
    from . import __version__
    return __version__


def _git_info(project_root: Path) -> dict[str, str]:
    info: dict[str, str] = {}
    for key, args in (
        ("sha", ["rev-parse", "HEAD"]),
        ("shortSha", ["rev-parse", "--short", "HEAD"]),
        ("branch", ["rev-parse", "--abbrev-ref", "HEAD"]),
        ("commitTimestamp", ["log", "-1", "--format=%cI"]),
        ("tag", ["describe", "--tags", "--abbrev=0"]),
    ):
        try:
            info[key] = subprocess.check_output(
                ["git"] + args,
                cwd=str(project_root),
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            info[key] = "unknown"
    return info


def _build_timestamp(project_root: Path, *, reproducible: bool) -> str:
    if reproducible:
        return _git_info(project_root).get("commitTimestamp", "1970-01-01T00:00:00Z")
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _schema_versions(project_root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    schemas_dir = project_root / "schemas"
    if not schemas_dir.exists():
        return out
    for path in sorted(schemas_dir.rglob("*.schema.json")):
        try:
            with path.open(encoding="utf-8") as f:
                obj = json.load(f)
            ver = obj.get("version") or obj.get("schemaVersion") or "0"
        except (OSError, json.JSONDecodeError):
            ver = "0"
        rel = path.relative_to(schemas_dir).as_posix()
        out[rel] = str(ver)
    return out
