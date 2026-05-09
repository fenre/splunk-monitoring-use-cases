#!/usr/bin/env python3
"""License inventory auditor.

Repo-overhaul plan §P11 (2026-05-09).
Relocated to ``splunk_uc.audits.license_inventory`` under §P6, 2026-05-09.

Every Python dependency declared
in ``pyproject.toml`` (root + ``mcp/``) carries a software licence, and
every ``LICENSE*`` file the repo vendors covers some upstream code. A
contributor adding a new dependency or vendoring a new third-party app
must record the licence so legal/release reviewers can spot anything
incompatible with the repo's own MIT licence before it ships.

The committed snapshot lives at ``data/license-inventory.json`` (typed
by ``schemas/license-inventory.schema.json``); the human-readable
rollup lives at ``docs/license-inventory.md``. Both are regenerated
together by ``--write`` and gated together by ``--check``.

CI calls ``--check``: it rebuilds the inventory from the working tree
plus ``importlib.metadata`` (so every dep declared in ``pyproject.toml``
must be importable in the running interpreter — ``make dev-install``
covers that) and fails if the result differs from the committed file.

Maintainer workflow when adding a dependency::

    pip install -e ".[audits,test,dev]"
    # ... edit pyproject.toml to add the new dep ...
    pip install -e ".[audits,test,dev]"
    python3 scripts/audit_license_inventory.py --write
    git add pyproject.toml mcp/pyproject.toml \\
            data/license-inventory.json docs/license-inventory.md
    git commit -m "deps: add <pkg>"

Why a committed snapshot
------------------------

A live "query PyPI on every CI run" approach is non-deterministic
(network failures, rate limits, upstream metadata edits) and offers no
audit trail of *when* a licence changed. A committed snapshot makes the
diff self-evident in code review and forces an explicit decision when
upstream re-licences.

SPDX resolution order
---------------------

Modern packages declare ``License-Expression`` (PEP 639) — that's the
gold standard and is taken verbatim. Older packages fill ``License``
with anything from a 6-character SPDX identifier to a paragraph of
prose; ``_normalise_license_string`` extracts an SPDX from a curated
alias table when possible. As a last resort the script walks the
``Classifier`` lines (``License :: OSI Approved :: ...``) which is the
oldest reliable signal in the Python packaging ecosystem.

Stdlib-only per ADR-0004; uses ``tomllib`` (Python 3.11+) and
``importlib.metadata`` only.

Exit codes
----------

* ``0`` — committed inventory matches the live computation; every
  reported licence is on the allowlist.
* ``1`` — drift detected (committed file is stale, or a non-allowlisted
  licence appeared, or a vendored ``LICENSE`` file was added/removed).
* ``2`` — usage / I/O error (missing file, malformed TOML, missing
  dependency in the running interpreter).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from importlib import metadata as _importlib_metadata
from pathlib import Path
from typing import Any, Protocol, cast


class _MetadataLike(Protocol):
    """Runtime-stable interface a package-metadata object must expose.

    ``importlib.metadata.metadata()`` returns an ``email.message.Message``
    in CPython; the stubs type it as the abstract ``PackageMetadata``
    protocol which (as of typeshed 2026.05) doesn't surface ``.get`` /
    ``.get_all``. This local Protocol lets us type-check the code that
    drives those methods without sacrificing the runtime contract.
    """

    def get(self, key: str) -> str | None: ...

    def get_all(self, key: str) -> list[str] | None: ...


# ``parents[3]`` resolves: license_inventory.py -> audits/ ->
# splunk_uc/ -> src/ -> repo root. The previous home (scripts/) was
# only one level deep so this is the only path adjustment needed.
REPO_ROOT = Path(__file__).resolve().parents[3]

# Two pyproject.toml files contribute Python deps. Order is stable so
# the rendered docs/output order is deterministic.
_PYPROJECT_FILES: tuple[tuple[str, Path], ...] = (
    ("splunk-uc", REPO_ROOT / "pyproject.toml"),
    ("splunk-uc-mcp", REPO_ROOT / "mcp" / "pyproject.toml"),
)

_INVENTORY_PATH = REPO_ROOT / "data" / "license-inventory.json"
_INVENTORY_MD_PATH = REPO_ROOT / "docs" / "license-inventory.md"
_SCHEMA_REL = "../schemas/license-inventory.schema.json"

# Default allowlist of SPDX identifiers compatible with the repo's MIT
# licence. Curated against the OSI permissive-licence list and the
# Linux Foundation FOSSA SPDX cheatsheet. Adding to this list requires
# legal sign-off in the same PR — the audit will print a clear error
# pointing at this constant when an unknown licence appears.
DEFAULT_ALLOWLIST: tuple[str, ...] = (
    "0BSD",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD-3-Clause-Modification",
    "CC0-1.0",
    "ISC",
    "MIT",
    "MIT-0",
    "MPL-2.0",
    "PSF-2.0",
    "Python-2.0",
    "Python-2.0.1",
    "Unlicense",
    # Dual licences expressed as SPDX expressions, sorted alphabetically.
    "Apache-2.0 OR MIT",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-3-Clause OR Apache-2.0",
    "MIT OR Apache-2.0",
)

# Curated alias table mapping the messy "License" metadata field values
# we've seen in the wild back to canonical SPDX identifiers. Keys are
# lowercased and stripped of trailing punctuation. Extend on demand.
_LICENSE_ALIASES: dict[str, str] = {
    "apache 2.0": "Apache-2.0",
    "apache 2": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "bsd 2-clause": "BSD-2-Clause",
    "bsd 2-clause license": "BSD-2-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "bsd 3-clause license": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "isc": "ISC",
    "isc license": "ISC",
    "mit": "MIT",
    "mit license": "MIT",
    "mit-0": "MIT-0",
    "mozilla public license 2.0": "MPL-2.0",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "mpl-2.0": "MPL-2.0",
    "psf": "PSF-2.0",
    "psf-2.0": "PSF-2.0",
    "python software foundation license": "PSF-2.0",
    "python-2.0": "Python-2.0",
    "the unlicense": "Unlicense",
    "unlicense": "Unlicense",
    "0bsd": "0BSD",
    "cc0 1.0 universal": "CC0-1.0",
    "cc0-1.0": "CC0-1.0",
}

# Trove classifier -> SPDX. Only the ones we've seen in the dependency
# graph need entries; extend as new packages arrive.
_CLASSIFIER_TO_SPDX: dict[str, str] = {
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: BSD License": "BSD-3-Clause",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: MIT No Attribution License (MIT-0)": "MIT-0",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
    "License :: OSI Approved :: The Unlicense (Unlicense)": "Unlicense",
}

# PEP 508 extracts: bare distribution name from a requirement string.
# Examples we need to handle:
#   "jsonschema>=4.21"             -> "jsonschema"
#   "pytest-cov>=5.0"              -> "pytest-cov"
#   "respx>=0.21"                  -> "respx"
#   "splunk-uc[audits,build,test,dev]" -> "splunk-uc"  (self-reference; skipped)
#   "types-PyYAML>=6.0.12"         -> "types-pyyaml" (lowercased)
_REQUIREMENT_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._\-]*)")
_VERSION_SPECIFIER_RE = re.compile(r"[<>=!~][<>=!~ ]*[0-9].*")


def _read_pyproject(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing pyproject.toml: {path}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _normalise_distribution_name(raw: str) -> str:
    """Lowercase + collapse runs of `_`/`.` to `-` per PEP 503."""
    return re.sub(r"[-_.]+", "-", raw).lower()


def _split_requirement(req: str) -> tuple[str, str]:
    """Split a PEP 508 requirement into ``(name, constraint)``.

    Discards markers (``; python_version >= ...``) for the purposes of
    inventorying because the dependency *exists* regardless of marker.
    The full string is preserved verbatim in ``version_constraint`` so
    reviewers can spot conditional pulls.
    """
    base, _, _marker = req.partition(";")
    base = base.strip()
    name_match = _REQUIREMENT_NAME_RE.match(base)
    if not name_match:
        raise ValueError(f"unparseable requirement: {req!r}")
    name = name_match.group(1)
    rest = base[name_match.end() :].lstrip()
    # Drop a leading "[extras]" group so "splunk-uc[audits,build]" -> "splunk-uc".
    if rest.startswith("["):
        close = rest.find("]")
        if close == -1:
            raise ValueError(f"unterminated extras group in requirement: {req!r}")
        rest = rest[close + 1 :].lstrip()
    constraint = rest if _VERSION_SPECIFIER_RE.match(rest) else ""
    return _normalise_distribution_name(name), constraint


def _collect_declared_dependencies(
    pyproject: dict[str, Any],
    *,
    skip_self: str,
) -> dict[str, dict[str, Any]]:
    """Return ``{normalised_name: {extras: set, constraints: set}}``.

    ``extras`` carries the dependency-group names this package falls
    into (``""`` for the runtime ``[project].dependencies`` group, or
    one of the keys in ``[project.optional-dependencies]``). The
    ``"all"`` meta-extra (the convenience that pulls every other
    extra by self-referencing) is ignored — its members already
    appear under their first-class extras.
    """
    project = pyproject.get("project") or {}
    out: dict[str, dict[str, Any]] = {}

    def _add(name: str, *, extra: str, constraint: str) -> None:
        if name == skip_self:
            return
        record = out.setdefault(
            name,
            {"extras": set(), "constraints": set()},
        )
        record["extras"].add(extra)
        if constraint:
            record["constraints"].add(constraint)

    runtime = project.get("dependencies") or []
    for req in runtime:
        if not isinstance(req, str):
            continue
        try:
            name, constraint = _split_requirement(req)
        except ValueError:
            # Surface as a hard error in main(); this helper stays tolerant.
            raise
        _add(name, extra="runtime", constraint=constraint)

    extras = project.get("optional-dependencies") or {}
    for extra_name, deps in extras.items():
        if not isinstance(deps, list):
            continue
        if extra_name == "all":
            # Self-referencing meta-extra; skip to avoid duplicate
            # entries (its members already show up under their
            # first-class extra above).
            continue
        for req in deps:
            if not isinstance(req, str):
                continue
            try:
                name, constraint = _split_requirement(req)
            except ValueError:
                raise
            _add(name, extra=str(extra_name), constraint=constraint)

    return out


def _normalise_license_string(raw: str) -> str | None:
    """Map a metadata ``License`` value to an SPDX identifier or None."""
    if not raw:
        return None
    cleaned = raw.strip().rstrip(".").strip()
    if not cleaned:
        return None
    # Already a recognisable SPDX expression like "Apache-2.0"? Take it.
    if re.fullmatch(r"[A-Za-z0-9.\-+]+(\s+(OR|AND|WITH)\s+[A-Za-z0-9.\-+]+)*", cleaned):
        return cleaned
    return _LICENSE_ALIASES.get(cleaned.lower())


def _extract_spdx_from_metadata(
    meta: _MetadataLike,
) -> tuple[str, str]:
    """Return ``(spdx, source)`` where source identifies which probe won."""
    expr = meta.get("License-Expression")
    if expr:
        return str(expr).strip(), "license-expression"

    legacy = meta.get("License")
    if legacy:
        normalised = _normalise_license_string(str(legacy))
        if normalised:
            return normalised, "license"

    classifiers = meta.get_all("Classifier") or []
    license_classifiers = [c for c in classifiers if c.startswith("License ::")]
    for cls in license_classifiers:
        if cls in _CLASSIFIER_TO_SPDX:
            return _CLASSIFIER_TO_SPDX[cls], "classifier"
    if license_classifiers:
        return license_classifiers[0], "classifier"

    return "UNKNOWN", "unknown"


def _resolve_python_packages(
    declared: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Materialise the typed ``python_packages`` records.

    ``declared`` is ``{consumer_name: {dep_name: {extras, constraints}}}``
    as returned by :func:`_collect_declared_dependencies` per project.
    Multiple consumers wanting the same dep collapse into one record.
    """
    by_dep: dict[str, dict[str, Any]] = {}
    for consumer, deps in declared.items():
        for name, attrs in deps.items():
            record = by_dep.setdefault(
                name,
                {
                    "name": name,
                    "consumers": set(),
                    "extras": set(),
                    "constraints": set(),
                },
            )
            record["consumers"].add(consumer)
            record["extras"].update(attrs["extras"])
            record["constraints"].update(attrs["constraints"])

    out: list[dict[str, Any]] = []
    missing: list[str] = []
    for name in sorted(by_dep.keys()):
        record = by_dep[name]
        try:
            meta = _importlib_metadata.metadata(name)
        except _importlib_metadata.PackageNotFoundError:
            missing.append(name)
            continue
        # ``importlib.metadata.metadata()`` returns an
        # ``email.message.Message`` at runtime, which carries the
        # ``.get`` and ``.get_all`` methods our protocol requires.
        # The typeshed stub for ``PackageMetadata`` doesn't yet
        # surface those (typeshed 2026.05); cast through Any so
        # the structural protocol match isn't blocked.
        spdx, source = _extract_spdx_from_metadata(cast(_MetadataLike, meta))
        # Pick the strictest single declared constraint when present;
        # if multiple consumers declare different constraints we record
        # them all space-joined for transparency. Edge case in practice;
        # both pyproject.tomls usually agree.
        constraint = " | ".join(sorted(record["constraints"])) if record["constraints"] else ""
        out.append(
            {
                "name": name,
                "spdx": spdx,
                "license_source": source,
                "consumers": sorted(record["consumers"]),
                "extras": sorted(record["extras"]),
                "version_constraint": constraint,
            }
        )

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "audit_license_inventory: the following declared dependencies are "
            f"not importable in the running interpreter: {joined}. "
            'Run `pip install -e ".[audits,test,dev]"` (and `pip install -e '
            "mcp/[test]` for the MCP package) before re-running this audit."
        )
    return out


def _read_top_license(repo_root: Path) -> dict[str, str]:
    """Best-effort SPDX from the top-level LICENSE file."""
    license_file = repo_root / "LICENSE"
    if not license_file.is_file():
        return {"spdx": "UNKNOWN", "file": "LICENSE"}
    head = license_file.read_text(encoding="utf-8").splitlines()
    return {
        "spdx": _identify_license_header(head),
        "file": "LICENSE",
    }


def _identify_license_header(lines: list[str]) -> str:
    """Heuristic SPDX detector for the first few lines of a LICENSE file."""
    head = " ".join(line.strip() for line in lines[:10] if line.strip())
    if not head:
        return "UNKNOWN"
    lowered = head.lower()
    if "mit license" in lowered or lowered.startswith("mit license"):
        return "MIT"
    if "apache license" in lowered and "2.0" in lowered:
        return "Apache-2.0"
    if "bsd 3-clause" in lowered or "redistribution and use in source and binary forms" in lowered:
        return "BSD-3-Clause" if "neither the name" in lowered else "BSD-2-Clause"
    if "isc license" in lowered:
        return "ISC"
    if "mozilla public license" in lowered and "2.0" in lowered:
        return "MPL-2.0"
    if "creative commons" in lowered and "cc0" in lowered:
        return "CC0-1.0"
    if "the unlicense" in lowered or "this is free and unencumbered software" in lowered:
        return "Unlicense"
    return "UNKNOWN"


# Vendored LICENSE files we recognise. The pattern is intentionally
# narrow:
#
# 1. A bare ``LICENSE``/``LICENCE`` filename (any case), with no
#    extension or one of the allowlisted extensions ``.txt``, ``.md``,
#    ``.rst``.
# 2. A ``LICENSE-<SPDX>``/``LICENCE-<SPDX>`` filename where ``<SPDX>``
#    is a curated tag mirroring SPDX root identifiers (e.g. ``MIT``,
#    ``APACHE``, ``BSD``). Dual-licensed packages (Rust crates, npm
#    packages) ship multiple ``LICENSE-MIT`` / ``LICENSE-APACHE``
#    files; this case captures those.
#
# Anything else — including the repo's own ``docs/license-inventory.md``
# (named ``LICENSE-INVENTORY.MD`` once uppercased) and
# ``schemas/license-inventory.schema.json`` — is rejected because the
# tag does not match the SPDX allowlist.
_LICENSE_EXTENSIONS = ("", ".txt", ".md", ".rst")
_LICENSE_TAG_ALLOWLIST: frozenset[str] = frozenset(
    {
        "0BSD",
        "AGPL",
        "APACHE",
        "APACHE2",
        "APL",
        "BOOST",
        "BSD",
        "BSD2",
        "BSD3",
        "BSL",
        "CC0",
        "CDDL",
        "EPL",
        "GPL",
        "GPL2",
        "GPL3",
        "ISC",
        "LGPL",
        "LGPL2",
        "LGPL3",
        "MIT",
        "MPL",
        "PSF",
        "UNLICENSE",
        "ZLIB",
    }
)


def _is_license_filename(name: str) -> bool:
    upper = name.upper()
    base = upper
    suffix = ""
    if "." in upper:
        base, sep, raw_suffix = upper.rpartition(".")
        suffix = ("." + raw_suffix.lower()) if sep else ""
    if suffix not in _LICENSE_EXTENSIONS:
        return False
    if base in ("LICENSE", "LICENCE"):
        return True
    if base.startswith(("LICENSE-", "LICENCE-")):
        tag = base.split("-", 1)[1]
        # Reject when the tag itself contains another separator
        # (e.g. ``LICENSE-INVENTORY-V2`` or anything with a dot).
        if "." in tag or "-" in tag:
            return False
        return tag in _LICENSE_TAG_ALLOWLIST
    return False


# Top-level directories that are either gitignored build output, fetched
# upstream content, transient venvs, or editor caches. Anything under
# these is excluded from the vendored-license enumeration. Mirrors the
# repo .gitignore — keep in sync with that file when adding new
# generated-output directories.
_SKIP_TOP_LEVEL_DIRS: frozenset[str] = frozenset(
    {
        "build",
        "dist",
        "dist1",
        "dist2",
        "dist-legacy",
        "dist-content",
        "dist-before",
        ".build-tmp",
        "node_modules",
        "vendor",
        "htmlcov",
    }
)


def _is_inside_skip_dir(path: Path, repo_root: Path) -> bool:
    """Return True if any ancestor of ``path`` is a transient/output dir.

    Two classes of skip:

    1. Hidden directories at any depth (``__pycache__/``, ``.git/``,
       ``.mypy_cache/``, ``.ruff_cache/``, ``.cursor/``, ``.idea/``,
       ``.vscode/``, ``.venv/``, ``.venv-feasibility/``, …). Anything
       starting with ``.`` or named ``__pycache__`` is treated as
       infrastructure noise.
    2. Top-level build/vendor output dirs listed in
       :data:`_SKIP_TOP_LEVEL_DIRS`. Always gitignored.
    """
    relative = path.relative_to(repo_root)
    parts = relative.parts
    if not parts:
        return False
    for part in parts:
        if part.startswith(".") or part == "__pycache__":
            return True
    if parts[0] in _SKIP_TOP_LEVEL_DIRS:
        return True
    return False


def _enumerate_vendored_licenses(repo_root: Path) -> list[dict[str, str]]:
    """Find every LICENSE-style file in the working tree except the top one.

    Excludes:
      * ``dist/`` (build output, not source)
      * ``node_modules/`` + ``.git/`` + ``build/`` (transient)
      * any directory whose top-level name starts with ``.venv``
      * the top-level ``LICENSE`` (handled separately as ``repo_license``)
    """
    out: list[dict[str, str]] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if _is_inside_skip_dir(path, repo_root):
            continue
        if path == repo_root / "LICENSE":
            continue
        if not _is_license_filename(path.name):
            continue
        rel = path.relative_to(repo_root).as_posix()
        try:
            head = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            head = []
        out.append(
            {
                "path": rel,
                "spdx": _identify_license_header(head),
                "subject": _vendored_subject(rel),
            }
        )
    return out


def _vendored_subject(rel_path: str) -> str:
    """Return a curated description of the vendored content for known paths.

    Falls back to a structural description for unknown paths so the
    inventory always has a non-empty ``subject``.
    """
    curated = {
        "splunk-apps/splunk-uc-recommender/LICENSE": (
            "splunk-uc-recommender Splunk app vendored verbatim under "
            "splunk-apps/. Built and packaged separately from the catalogue."
        ),
    }
    if rel_path in curated:
        return curated[rel_path]
    parts = Path(rel_path).parts
    if len(parts) >= 2:
        return f"Vendored content under {parts[0]}/{parts[1]}/"
    return f"Vendored content at {rel_path}"


def _git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return out.decode("ascii").strip() or "unknown"


def _read_repo_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if not version_file.is_file():
        return "unknown"
    return version_file.read_text(encoding="utf-8").strip() or "unknown"


def build_inventory(
    *,
    captured_at: str | None = None,
    git_head: str | None = None,
    allowlist: Iterable[str] = DEFAULT_ALLOWLIST,
) -> dict[str, Any]:
    """Materialise the typed inventory dict from the working tree."""
    declared_per_project: dict[str, dict[str, dict[str, Any]]] = {}
    for project_name, path in _PYPROJECT_FILES:
        pyproject = _read_pyproject(path)
        declared_per_project[project_name] = _collect_declared_dependencies(
            pyproject, skip_self=project_name
        )

    python_packages = _resolve_python_packages(declared_per_project)
    vendored = _enumerate_vendored_licenses(REPO_ROOT)
    repo_license = _read_top_license(REPO_ROOT)

    return {
        "$schema": _SCHEMA_REL,
        "version": _read_repo_version(),
        "captured_at": captured_at or _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": git_head if git_head is not None else _git_head(),
        "repo_license": repo_license,
        "allowlist": sorted(set(allowlist)),
        "python_packages": python_packages,
        "vendored_licenses": vendored,
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    """Return a human-readable rollup of ``inventory`` as Markdown."""
    lines: list[str] = []
    lines.append("# License inventory")
    lines.append("")
    lines.append(
        "Auto-generated by `scripts/audit_license_inventory.py --write`. "
        "Edit the source pyproject.toml(s) or rerun the audit; do not hand-edit "
        "this file. See `data/license-inventory.json` for the machine-readable "
        "form, and `schemas/license-inventory.schema.json` for the contract."
    )
    lines.append("")
    lines.append(
        f"- **Repo licence**: `{inventory['repo_license']['spdx']}` "
        f"(`{inventory['repo_license']['file']}`)"
    )
    lines.append(f"- **Captured at**: {inventory['captured_at']}")
    lines.append(f"- **Repo version**: {inventory['version']}")
    lines.append(f"- **Git HEAD**: `{inventory['git_head']}`")
    lines.append("")
    lines.append("## Allowlist")
    lines.append("")
    lines.append(
        "These SPDX identifiers are treated as compatible with the repo's MIT "
        "licence. Anything outside this list fails the audit and requires "
        "legal review before merging."
    )
    lines.append("")
    for spdx in inventory["allowlist"]:
        lines.append(f"- `{spdx}`")
    lines.append("")
    lines.append("## Python dependencies")
    lines.append("")
    lines.append("| Package | SPDX | Source | Consumers | Extras | Version |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for pkg in inventory["python_packages"]:
        consumers = ", ".join(pkg["consumers"])
        extras = ", ".join(pkg["extras"])
        # ``|`` in a Markdown table cell is interpreted as a column
        # separator. ``version_constraint`` joins multiple consumer
        # constraints with ``" | "``, so escape every pipe in any cell
        # before rendering.
        version_raw = pkg["version_constraint"] or "—"
        lines.append(
            f"| `{pkg['name']}` | `{pkg['spdx']}` | `{pkg['license_source']}` "
            f"| {_md_cell(consumers)} | {_md_cell(extras)} | `{_md_cell(version_raw)}` |"
        )
    lines.append("")
    lines.append("## Vendored LICENSE files")
    lines.append("")
    if not inventory["vendored_licenses"]:
        lines.append("_No vendored LICENSE files found outside the top-level `LICENSE`._")
    else:
        lines.append("| Path | SPDX | Subject |")
        lines.append("| --- | --- | --- |")
        for v in inventory["vendored_licenses"]:
            lines.append(f"| `{v['path']}` | `{v['spdx']}` | {_md_cell(v['subject'])} |")
    lines.append("")
    return "\n".join(lines)


def _md_cell(value: str) -> str:
    """Escape Markdown table-cell pipe characters."""
    return value.replace("|", "\\|")


def _write_inventory_json(path: Path, inventory: dict[str, Any]) -> None:
    payload = json.dumps(inventory, indent=2, sort_keys=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _violations_against_allowlist(inventory: dict[str, Any]) -> list[str]:
    allow = set(inventory["allowlist"])
    violations: list[str] = []
    for pkg in inventory["python_packages"]:
        if pkg["spdx"] not in allow:
            violations.append(
                f"python-package {pkg['name']!r} has license "
                f"{pkg['spdx']!r} (source: {pkg['license_source']}) "
                "which is not on the allowlist"
            )
    for v in inventory["vendored_licenses"]:
        if v["spdx"] not in allow:
            violations.append(
                f"vendored-license {v['path']!r} declares {v['spdx']!r} "
                "which is not on the allowlist"
            )
    if inventory["repo_license"]["spdx"] not in allow:
        violations.append(
            f"repo-license {inventory['repo_license']['file']!r} declares "
            f"{inventory['repo_license']['spdx']!r} which is not on the allowlist"
        )
    return violations


def _strip_volatile(inventory: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with ``captured_at`` and ``git_head`` redacted.

    Used for ``--check``: the CI environment never matches the
    maintainer's local ``captured_at`` exactly, and ``git_head`` rolls
    on every commit, so structural drift is the only signal that
    matters.
    """
    redacted = dict(inventory)
    redacted["captured_at"] = "<redacted>"
    redacted["git_head"] = "<redacted>"
    return redacted


def _diff_inventories(committed: dict[str, Any], live: dict[str, Any]) -> list[str]:
    """Return human-readable diff lines for two inventories.

    Compares the volatile-stripped views so timestamps don't trigger
    spurious failures.
    """
    a = json.dumps(_strip_volatile(committed), indent=2, sort_keys=True).splitlines()
    b = json.dumps(_strip_volatile(live), indent=2, sort_keys=True).splitlines()
    if a == b:
        return []
    import difflib

    return list(
        difflib.unified_diff(
            a,
            b,
            fromfile="committed (data/license-inventory.json)",
            tofile="live (this run)",
            lineterm="",
        )
    )


def _run_check(
    *,
    inventory_path: Path,
    inventory_md_path: Path,
) -> int:
    if not inventory_path.is_file():
        print(
            f"error: committed inventory missing at {inventory_path.relative_to(REPO_ROOT)}; "
            "run `python3 scripts/audit_license_inventory.py --write` and commit the result.",
            file=sys.stderr,
        )
        return 1
    if not inventory_md_path.is_file():
        print(
            f"error: committed rollup missing at {inventory_md_path.relative_to(REPO_ROOT)}; "
            "run `python3 scripts/audit_license_inventory.py --write` and commit the result.",
            file=sys.stderr,
        )
        return 1

    committed = json.loads(inventory_path.read_text(encoding="utf-8"))
    try:
        live = build_inventory()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    diff_lines = _diff_inventories(committed, live)
    if diff_lines:
        print(
            "error: committed license inventory drifted vs. the live computation. "
            "Re-run `python3 scripts/audit_license_inventory.py --write` and commit "
            "the result alongside your dependency change.",
            file=sys.stderr,
        )
        for line in diff_lines:
            print(line)
        return 1

    # Markdown rollup must reflect the *committed* JSON exactly; if a
    # human edits the JSON without rerunning ``--write``, or if --write
    # mis-renders, this gate trips. Rendering against the committed JSON
    # rather than the freshly-built one decouples this check from
    # captured_at / git_head drift between local and CI clocks.
    expected_md = render_markdown(committed)
    actual_md = inventory_md_path.read_text(encoding="utf-8")
    if expected_md != actual_md:
        print(
            "error: committed Markdown rollup does not match the committed JSON. "
            "Re-run `python3 scripts/audit_license_inventory.py --write` and commit "
            "the regenerated docs/license-inventory.md.",
            file=sys.stderr,
        )
        return 1

    violations = _violations_against_allowlist(live)
    if violations:
        print(
            "error: license inventory contains entries that are not on the allowlist:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        print(
            "\nRemediation: confirm with legal that the licence is acceptable, "
            "then add the SPDX to DEFAULT_ALLOWLIST in "
            "scripts/audit_license_inventory.py in the same PR.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK — license inventory matches: "
        f"{len(live['python_packages'])} python packages + "
        f"{len(live['vendored_licenses'])} vendored LICENSE files, "
        "all on the allowlist."
    )
    return 0


def _run_write(
    *,
    inventory_path: Path,
    inventory_md_path: Path,
) -> int:
    try:
        live = build_inventory()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    violations = _violations_against_allowlist(live)
    if violations:
        print(
            "warning: writing inventory but the following entries are not on "
            "the allowlist (CI --check will fail until they are added):",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)

    _write_inventory_json(inventory_path, live)
    inventory_md_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_md_path.write_text(render_markdown(live), encoding="utf-8")

    print(
        f"wrote {inventory_path.relative_to(REPO_ROOT)} and "
        f"{inventory_md_path.relative_to(REPO_ROOT)}: "
        f"{len(live['python_packages'])} python packages, "
        f"{len(live['vendored_licenses'])} vendored LICENSE files."
    )
    return 0


def _run_print(*, json_output: bool) -> int:
    try:
        live = build_inventory()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if json_output:
        print(json.dumps(live, indent=2))
    else:
        print(render_markdown(live))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_license_inventory.py",
        description=__doc__.split("\n\n", 1)[0] if __doc__ else None,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help=(
            "Default mode. Rebuild the inventory and fail with exit code 1 "
            "if it drifts from the committed JSON or Markdown, or if any "
            "entry is not on the allowlist."
        ),
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help=(
            "Regenerate data/license-inventory.json + docs/license-inventory.md "
            "from the live working tree. Run after editing pyproject.toml."
        ),
    )
    mode.add_argument(
        "--print-json",
        action="store_true",
        help="Print the live-computed inventory to stdout as JSON. No write.",
    )
    mode.add_argument(
        "--print-md",
        action="store_true",
        help="Print the live-computed inventory to stdout as Markdown. No write.",
    )
    args = parser.parse_args(argv)

    inventory_path = _INVENTORY_PATH
    inventory_md_path = _INVENTORY_MD_PATH

    if args.write:
        return _run_write(
            inventory_path=inventory_path,
            inventory_md_path=inventory_md_path,
        )
    if args.print_json:
        return _run_print(json_output=True)
    if args.print_md:
        return _run_print(json_output=False)
    return _run_check(
        inventory_path=inventory_path,
        inventory_md_path=inventory_md_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
