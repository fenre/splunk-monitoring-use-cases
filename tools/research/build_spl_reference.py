#!/usr/bin/env python3
"""Build a local-only SPL reference vocabulary from third-party corpora.

This script reads any of the following sources that happen to be
present under ``external/`` and writes a normalised JSON vocabulary to
``data/spl-reference.local.json`` (gitignored):

* ``external/searchbase/searchbase/default/searchbase.conf`` — Splunk
  Works' Searchbase app (``Splunkbase #7188``); 771 vetted SPL searches
  spanning Splunk-platform monitoring, security, web servers, threat
  hunting, and industry-specific use cases. **Licensed under Splunk
  General Terms — not redistributable.** This script extracts only
  *vocabulary fingerprints* (macro names, sourcetypes, indexes,
  datamodel paths, function names) — never SPL bodies or descriptive
  prose.

* ``external/security_content/detections/**/*.yml`` — Splunk's public
  ``splunk/security_content`` repo (Apache 2.0 — redistributable).
  ~2,073 detection YAMLs with full SPL.

The output JSON has stable top-level keys::

    {
      "version": 1,
      "generated_at": "...",
      "sources": [{...}],
      "macros": ["security_content_summariesonly", ...],
      "macros_with_arity": {"security_content_ctime": [1], ...},
      "sourcetypes": ["WinEventLog", "aws:cloudtrail", ...],
      "indexes": ["_internal", "main", ...],
      "datamodel_paths": ["Risk.All_Risk", ...],
      "lookups": ["asset_categories", ...],
      "eval_functions": ["coalesce", ...],
      "stats_functions": ["count", ...],
      "commands": ["search", "stats", ...]
    }

When neither corpus is present the script still emits a valid JSON
shell with empty arrays so downstream audits can rely on the file
shape. Use ``--check`` to fail fast if no corpus is available.

Usage::

    python -m tools.research.build_spl_reference --out data/spl-reference.local.json
    python -m tools.research.build_spl_reference --check  # exit 1 if no corpus

This file is intentionally outside ``src/splunk_uc/`` because it is a
maintainer-side helper, not a CI gate.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

# Make the splunk_uc package importable when invoked as a script.
_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from splunk_uc.audits import _spl_parse as parse  # noqa: E402

# Searchbase uses ``<<index>>`` / ``<<sourcetype>>`` as templated parameter
# placeholders. They aren't real values — strip them from the corpus.
_PLACEHOLDER_RE = re.compile(r"^<<.*>>$")


def _is_real_value(v: str) -> bool:
    if not v or v != v.strip():
        return False
    if _PLACEHOLDER_RE.match(v):
        return False
    return True


DEFAULT_OUT = _REPO / "data" / "spl-reference.local.json"
SEARCHBASE_DIR = _REPO / "external" / "searchbase" / "searchbase"
SECURITY_CONTENT_DIR = _REPO / "external" / "security_content"

# Searchbase and ESCU both ship MITRE ATT&CK enrichment lookups — we
# don't need them for vocabulary, but we do record their presence.
SEARCHBASE_CONF = SEARCHBASE_DIR / "default" / "searchbase.conf"
SEARCHBASE_MACROS_CONF = SEARCHBASE_DIR / "default" / "macros.conf"
SEARCHBASE_LOOKUPS_DIR = SEARCHBASE_DIR / "lookups"
ESCU_DETECTIONS_DIR = SECURITY_CONTENT_DIR / "detections"
ESCU_MACROS_DIR = SECURITY_CONTENT_DIR / "macros"


# ---------------------------------------------------------------------------
# Searchbase (.conf) reader
# ---------------------------------------------------------------------------


def _read_conf_stanzas(path: Path) -> list[tuple[str, dict[str, str]]]:
    """Parse a Splunk-style ``.conf`` file into ``[(stanza, {key: value}), ...]``.

    Supports line continuations (``\\\\`` at end of line) which are
    pervasive in Searchbase's ``search`` field. Comments (``#``) and
    blank lines are skipped at the top level. Values can themselves
    contain ``#`` so we don't strip from values.
    """
    stanzas: list[tuple[str, dict[str, str]]] = []
    cur_name: str | None = None
    cur_kv: dict[str, str] = {}
    cur_key: str | None = None
    raw = path.read_text(encoding="utf-8", errors="replace")

    # Stitch line continuations BEFORE splitting on newlines so that
    # multi-line `search = ...` values become one logical line.
    raw = re.sub(r"\\\n", "", raw)

    for line in raw.split("\n"):
        if line.startswith("#"):
            continue
        if line.startswith("["):
            # Close out the previous stanza.
            if cur_name is not None:
                stanzas.append((cur_name, cur_kv))
            m = re.match(r"^\[(?P<name>[^\]]*)\]\s*$", line)
            cur_name = m.group("name") if m else None
            cur_kv = {}
            cur_key = None
            continue
        if cur_name is None:
            continue
        # Key = value form, with `=` allowed inside the value.
        m = re.match(r"^(?P<k>[A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(?P<v>.*)$", line)
        if m:
            cur_key = m.group("k")
            cur_kv[cur_key] = m.group("v")
        elif cur_key is not None:
            # Continuation of previous value (rare since we stitched \, but safe).
            cur_kv[cur_key] = cur_kv[cur_key] + "\n" + line

    if cur_name is not None:
        stanzas.append((cur_name, cur_kv))
    return stanzas


def _ingest_one_spl(spl: str, state: dict[str, Any]) -> None:
    """Extract every reference from one SPL string into ``state``.

    Wildcards and placeholder values (``<<sourcetype>>``) are dropped at
    ingest time so the emitted vocabulary is real-world only.
    """
    ext = parse.extract_all(spl)
    for cmd in ext.commands:
        state["commands"].add(cmd)
    for mref in ext.macros:
        if not _is_real_value(mref.name):
            continue
        state["macros"].add(mref.name)
        state["macros_with_arity"].setdefault(mref.name, set()).add(mref.arity)
    for sref in ext.sourcetypes:
        if sref.is_wildcard:
            continue
        if not _is_real_value(sref.value):
            continue
        state["sourcetypes"].add(sref.value)
    for iref in ext.indexes:
        if iref.is_wildcard:
            continue
        if not _is_real_value(iref.value):
            continue
        state["indexes"].add(iref.value)
    for dref in ext.datamodels:
        path_label = dref.model + ("." + dref.dataset if dref.dataset else "")
        state["datamodel_paths"].add(path_label)
    for lref in ext.lookups:
        if not _is_real_value(lref.name):
            continue
        state["lookups"].add(lref.name)
    for fref in ext.eval_functions:
        state["eval_functions"].add(fref.name)
    for fref in ext.stats_functions:
        state["stats_functions"].add(fref.name)


def _ingest_searchbase_corpus(state: dict[str, Any]) -> dict[str, Any] | None:
    """Walk Searchbase ``searchbase.conf`` and ``macros.conf`` if present."""
    if not SEARCHBASE_CONF.exists():
        return None

    # Search corpus
    spls: list[str] = []
    for _name, kv in _read_conf_stanzas(SEARCHBASE_CONF):
        spl = kv.get("search", "").strip()
        if not spl or spl == "| noop":
            continue
        spls.append(spl)

    # Macros defined inside Searchbase. These ALL count as known-good
    # macro identifiers because they exist in a real Splunk app.
    sb_defined: list[tuple[str, list[str]]] = []
    if SEARCHBASE_MACROS_CONF.exists():
        for stanza_name, kv in _read_conf_stanzas(SEARCHBASE_MACROS_CONF):
            # Macro stanza names look like `mymacro` or `mymacro(2)` for
            # parameterised macros.
            m = re.match(r"^(?P<name>[^(]+)(?:\((?P<args>\d+)\))?\s*$", stanza_name)
            if not m:
                continue
            name = m.group("name").strip()
            arity_str = m.group("args")
            args_field = kv.get("args", "")
            if arity_str is not None:
                arity = int(arity_str)
            elif args_field.strip():
                arity = len([a for a in args_field.split(",") if a.strip()])
            else:
                arity = 0
            sb_defined.append((name, [str(arity)]))

    # MITRE lookup
    mitre_lookup_present = (SEARCHBASE_LOOKUPS_DIR / "sb_mitre_enrichment.csv").exists()

    # Extract vocabulary from every search.
    for spl in spls:
        _ingest_one_spl(spl, state)

    # The Searchbase-defined macros are also known-good even if no
    # search references them yet.
    for name, _arities in sb_defined:
        state["macros"].add(name)

    return {
        "name": "Searchbase",
        "version": "1.1.5",
        "license": "Splunk General Terms (not redistributable)",
        "path": str(SEARCHBASE_CONF.relative_to(_REPO)),
        "search_count": len(spls),
        "defined_macros": len(sb_defined),
        "mitre_lookup_present": mitre_lookup_present,
    }


# ---------------------------------------------------------------------------
# ESCU YAML reader (very small subset — just the search field)
# ---------------------------------------------------------------------------


def _ingest_escu_corpus(state: dict[str, Any]) -> dict[str, Any] | None:
    """Walk ``external/security_content/detections/**/*.yml`` if present.

    We use a minimal hand-rolled YAML extractor for the ``search`` field
    so this script has no third-party dependencies. ESCU's YAML follows
    a predictable shape::

        search: |-
          | tstats ...
          | eval ...

    or a single-line form with ``search: '...'``.
    """
    if not ESCU_DETECTIONS_DIR.exists():
        return None

    yml_files = sorted(ESCU_DETECTIONS_DIR.rglob("*.yml"))
    if not yml_files:
        return None

    spls: list[str] = []
    for yml in yml_files:
        spl = _extract_yaml_search_field(yml)
        if spl:
            spls.append(spl)

    macro_files = list(ESCU_MACROS_DIR.glob("*.yml")) if ESCU_MACROS_DIR.exists() else []

    for spl in spls:
        _ingest_one_spl(spl, state)

    # Add ESCU-defined macros as known-good identifiers.
    for mf in macro_files:
        name = mf.stem
        # Macro YAMLs may also encode arity in `arguments:` — we just
        # record the identifier; arity comes from references at use sites.
        state["macros"].add(name)

    return {
        "name": "splunk/security_content (ESCU)",
        "license": "Apache-2.0",
        "path": str(ESCU_DETECTIONS_DIR.relative_to(_REPO)),
        "detection_count": len(spls),
        "macro_files": len(macro_files),
    }


_YAML_BLOCK_SEARCH_RE = re.compile(
    r"^search:\s*\|-?\s*$",
    re.MULTILINE,
)
_YAML_INLINE_SEARCH_RE = re.compile(
    r"^search:\s*(?P<v>['\"].*?['\"]|\S.*?)$",
    re.MULTILINE | re.DOTALL,
)


def _extract_yaml_search_field(yml: Path) -> str | None:
    """Pull the ``search:`` field out of an ESCU-style YAML without a YAML lib."""
    text = yml.read_text(encoding="utf-8", errors="replace")
    # Block scalar: ``search: |-`` then indented lines until next top-level key.
    m = _YAML_BLOCK_SEARCH_RE.search(text)
    if m:
        start = m.end()
        # Walk lines from `start` until we hit a line that is not indented.
        out: list[str] = []
        for line in text[start:].split("\n"):
            if line.strip() == "":
                out.append("")
                continue
            if not line.startswith((" ", "\t")):
                break
            out.append(line.lstrip())
        body = "\n".join(out).strip()
        return body or None
    # Inline scalar
    m = _YAML_INLINE_SEARCH_RE.search(text)
    if m:
        v = m.group("v").strip()
        if v.startswith(("'", '"')) and v.endswith(("'", '"')) and len(v) >= 2:
            v = v[1:-1]
        return v
    return None


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _new_state() -> dict[str, Any]:
    return {
        "commands": set(),
        "macros": set(),
        "macros_with_arity": {},  # name -> set of arities
        "sourcetypes": set(),
        "indexes": set(),
        "datamodel_paths": set(),
        "lookups": set(),
        "eval_functions": set(),
        "stats_functions": set(),
    }


def _serialise(state: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sources": sources,
        "commands": sorted(state["commands"]),
        "macros": sorted(state["macros"]),
        "macros_with_arity": {
            name: sorted(state["macros_with_arity"][name])
            for name in sorted(state["macros_with_arity"])
        },
        "sourcetypes": sorted(state["sourcetypes"]),
        "indexes": sorted(state["indexes"]),
        "datamodel_paths": sorted(state["datamodel_paths"]),
        "lookups": sorted(state["lookups"]),
        "eval_functions": sorted(state["eval_functions"]),
        "stats_functions": sorted(state["stats_functions"]),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output JSON path.")
    p.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if no external corpus is available (CI guard).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational stderr output.",
    )
    args = p.parse_args(argv)

    state = _new_state()
    sources: list[dict[str, Any]] = []

    sb = _ingest_searchbase_corpus(state)
    if sb:
        sources.append(sb)
    escu = _ingest_escu_corpus(state)
    if escu:
        sources.append(escu)

    if not sources and args.check:
        sys.stderr.write(
            "ERROR: no reference corpus found.\n"
            "Looked under:\n"
            f"  {SEARCHBASE_CONF.relative_to(_REPO)}\n"
            f"  {ESCU_DETECTIONS_DIR.relative_to(_REPO)}\n"
        )
        return 1

    payload = _serialise(state, sources)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    if not args.quiet:
        sys.stderr.write(
            f"Wrote {args.out.relative_to(_REPO) if args.out.is_relative_to(_REPO) else args.out}\n"
            f"  sources:        {len(sources)}\n"
            f"  macros:         {len(payload['macros'])}\n"
            f"  sourcetypes:    {len(payload['sourcetypes'])}\n"
            f"  indexes:        {len(payload['indexes'])}\n"
            f"  datamodels:     {len(payload['datamodel_paths'])}\n"
            f"  lookups:        {len(payload['lookups'])}\n"
            f"  eval functions: {len(payload['eval_functions'])}\n"
            f"  stats funcs:    {len(payload['stats_functions'])}\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
