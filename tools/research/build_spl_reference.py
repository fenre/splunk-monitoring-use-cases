#!/usr/bin/env python3
"""Build a local-only SPL reference vocabulary from third-party corpora.

This script reads any of the following sources that happen to be
present under ``external/`` and writes a normalised JSON vocabulary to
``data/spl-reference.local.json`` (gitignored). All sources are
optional — readers gracefully no-op when their root directory is
missing, so a partial install still produces a valid corpus file.

Splunkbase / Splunk Works (Splunk General Terms — *not redistributable*):

* ``external/searchbase/searchbase/`` — Searchbase app
  (`Splunkbase #7188 <https://splunkbase.splunk.com/app/7188>`_); 770
  vetted SPL searches and 15 macro definitions.
* ``external/is4s/splunk_insights/`` — Insights Suite for Splunk
  (`Splunkbase #7186 <https://splunkbase.splunk.com/app/7186>`_); the
  umbrella that bundles Searchbase, Use Case Explorer, and Value
  Insights. The Use Case Explorer ships canonical
  ``uce_sourcetype_mapping.csv`` (~7k Splunk-curated sourcetypes
  cross-referenced to Splunk Lantern), ``uce_usecase_mapping.csv``
  (~760 Lantern UCs), and ``ssef_splunkbase_apps.csv.gz`` (~4.5k
  Splunkbase apps with sourcetype + CIM-tag columns).
* ``external/sse/Splunk_Security_Essentials/`` — SSE
  (`Splunkbase #3435 <https://splunkbase.splunk.com/app/3435>`_); ~600
  curated security searches plus a ``SSE-default-data-inventory-products.csv``
  product/sourcetype regex catalogue.
* ``external/cim/Splunk_SA_CIM/`` — Common Information Model add-on
  (`Splunkbase #1621 <https://splunkbase.splunk.com/app/1621>`_); 27
  CIM datamodel JSON files with full dataset hierarchy and CIM-tag
  vocabulary in ``tags.conf``.

Open source:

* ``external/security_content/detections/**/*.yml`` — Splunk's public
  ``splunk/security_content`` (ESCU) repo (Apache 2.0). ~2,073
  detection YAMLs and 234 macro YAMLs.

This script extracts *vocabulary fingerprints* only — macro names,
sourcetype strings, index names, datamodel paths, function names, CIM
tag names — never SPL bodies, descriptive prose, or anything else
covered by the upstream license that prohibits redistribution.

The output JSON has stable top-level keys::

    {
      "version": 1,
      "generated_at": "...",
      "sources": [{...}],
      "macros": ["security_content_summariesonly", ...],
      "macros_with_arity": {"security_content_ctime": [1], ...},
      "sourcetypes": ["WinEventLog", "aws:cloudtrail", ...],
      "sourcetype_glob_patterns": ["*365:cas:api", ...],
      "indexes": ["_internal", "main", ...],
      "datamodel_paths": ["Risk.All_Risk", ...],
      "cim_models": ["Authentication", "Network_Traffic", ...],
      "cim_tags": ["authentication", "endpoint", ...],
      "lookups": ["asset_categories", ...],
      "eval_functions": ["coalesce", ...],
      "stats_functions": ["count", ...],
      "commands": ["search", "stats", ...]
    }

When no corpus is present the script still emits a valid JSON shell
with empty arrays so downstream audits can rely on the file shape.
Use ``--check`` to fail fast if no corpus is available.

Usage::

    python -m tools.research.build_spl_reference --out data/spl-reference.local.json
    python -m tools.research.build_spl_reference --check  # exit 1 if no corpus

This file is intentionally outside ``src/splunk_uc/`` because it is a
maintainer-side helper, not a CI gate.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import io
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

# Splunk allows ``*`` in sourcetype names as a wildcard. We track those
# separately so the audit can do glob-aware matching downstream
# without conflating them with concrete sourcetypes.
_WILDCARD_CHARS = set("*?")


def _is_real_value(v: str) -> bool:
    if not v or v != v.strip():
        return False
    if _PLACEHOLDER_RE.match(v):
        return False
    return True


def _is_glob(v: str) -> bool:
    return any(c in _WILDCARD_CHARS for c in v)


DEFAULT_OUT = _REPO / "data" / "spl-reference.local.json"

# Splunkbase / Splunk Works apps (Splunk General Terms — not redistributable).
SEARCHBASE_DIR = _REPO / "external" / "searchbase" / "searchbase"
IS4S_DIR = _REPO / "external" / "is4s" / "splunk_insights"
SSE_DIR = _REPO / "external" / "sse" / "Splunk_Security_Essentials"
CIM_DIR = _REPO / "external" / "cim" / "Splunk_SA_CIM"

# splunk/security_content (ESCU). Apache-2.0.
SECURITY_CONTENT_DIR = _REPO / "external" / "security_content"

# Searchbase and ESCU both ship MITRE ATT&CK enrichment lookups — we
# don't need them for vocabulary, but we do record their presence.
SEARCHBASE_CONF = SEARCHBASE_DIR / "default" / "searchbase.conf"
SEARCHBASE_MACROS_CONF = SEARCHBASE_DIR / "default" / "macros.conf"
SEARCHBASE_LOOKUPS_DIR = SEARCHBASE_DIR / "lookups"

IS4S_DEFAULT = IS4S_DIR / "default"
IS4S_LOOKUPS = IS4S_DIR / "lookups"

SSE_DEFAULT = SSE_DIR / "default"
SSE_LOOKUPS = SSE_DIR / "lookups"

CIM_DEFAULT = CIM_DIR / "default"
CIM_DATAMODELS_DIR = CIM_DEFAULT / "data" / "models"
CIM_TAGS_CONF = CIM_DEFAULT / "tags.conf"
CIM_EVENTTYPES_CONF = CIM_DEFAULT / "eventtypes.conf"

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


def _add_sourcetype(state: dict[str, Any], value: str) -> None:
    """Route a sourcetype string to the right bucket (literal vs. glob)."""
    if not _is_real_value(value):
        return
    bucket = "sourcetype_glob_patterns" if _is_glob(value) else "sourcetypes"
    state[bucket].add(value)


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
# IS4S — Insights Suite for Splunk (Splunkbase #7186)
# ---------------------------------------------------------------------------


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV (optionally gzip-compressed by extension) into a list of dicts.

    Returns an empty list if the file is missing, empty, or unreadable.
    """
    if not path.exists():
        return []
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
                return list(csv.DictReader(fh))
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            return list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return []


def _ingest_is4s_corpus(state: dict[str, Any]) -> dict[str, Any] | None:
    """Walk the IS4S app: Searchbase + Use Case Explorer + Value Insights.

    The Use Case Explorer lookups are the highest-value payload because
    ``uce_sourcetype_mapping.csv`` is a Splunk-curated catalogue of
    legitimate sourcetypes mapped to vendor / product / data model /
    Splunk Lantern use case. ``ssef_splunkbase_apps.csv.gz`` covers
    every published Splunkbase app with its ``sourcetypes`` and
    ``cim_tags`` columns, providing canonical CIM tag vocabulary.
    """
    if not IS4S_DEFAULT.exists():
        return None

    counters: dict[str, int] = {
        "searchbase_spls": 0,
        "savedsearches": 0,
        "macros_defined": 0,
        "uce_sourcetypes": 0,
        "uce_lantern_use_cases": 0,
        "splunkbase_apps": 0,
    }

    # IS4S ships its own copy of searchbase.conf; dedupe is implicit
    # because both feeds add to the same set.
    is4s_searchbase_conf = IS4S_DEFAULT / "searchbase.conf"
    if is4s_searchbase_conf.exists():
        for _name, kv in _read_conf_stanzas(is4s_searchbase_conf):
            spl = kv.get("search", "").strip()
            if spl and spl != "| noop":
                _ingest_one_spl(spl, state)
                counters["searchbase_spls"] += 1

    # Value Insights' scheduled searches.
    savedsearches_conf = IS4S_DEFAULT / "savedsearches.conf"
    if savedsearches_conf.exists():
        for _name, kv in _read_conf_stanzas(savedsearches_conf):
            spl = kv.get("search", "").strip()
            if spl:
                _ingest_one_spl(spl, state)
                counters["savedsearches"] += 1

    # Macros defined by IS4S itself are known-good identifiers.
    macros_conf = IS4S_DEFAULT / "macros.conf"
    if macros_conf.exists():
        for stanza_name, _kv in _read_conf_stanzas(macros_conf):
            m = re.match(r"^(?P<name>[^(]+)(?:\(\d+\))?\s*$", stanza_name)
            if m:
                state["macros"].add(m.group("name").strip())
                counters["macros_defined"] += 1

    # Use Case Explorer sourcetype catalogue.
    uce_st = IS4S_LOOKUPS / "uce_sourcetype_mapping.csv"
    for row in _read_csv_rows(uce_st):
        st = (row.get("sourcetype_name") or "").strip()
        if st:
            _add_sourcetype(state, st)
            counters["uce_sourcetypes"] += 1
        # The ``data_model`` column lists the CIM datasets that this
        # sourcetype feeds (pipe-separated free text). Strip the
        # cosmetic " data" suffix and route into cim_models.
        for dm in (row.get("data_model") or "").split("|"):
            dm = dm.strip().removesuffix(" data").strip()
            if dm and " " not in dm and "/" not in dm:
                # Filter out free-text values; CIM model names are
                # CamelCase or underscore_separated, never multi-word.
                state["cim_models"].add(dm)

    # Splunk Lantern use case index (provides UC names; we don't
    # store the URLs, only the names used for sanity checks).
    uce_uc = IS4S_LOOKUPS / "uce_usecase_mapping.csv"
    counters["uce_lantern_use_cases"] = sum(1 for _ in _read_csv_rows(uce_uc))

    # Splunkbase app catalogue: pull the sourcetypes & CIM tags columns.
    sb_apps = IS4S_LOOKUPS / "ssef_splunkbase_apps.csv.gz"
    for row in _read_csv_rows(sb_apps):
        counters["splunkbase_apps"] += 1
        for st in (row.get("sourcetypes") or "").split("|"):
            st = st.strip()
            if st:
                _add_sourcetype(state, st)
        for tag in (row.get("cim_tags") or "").split("|"):
            tag = tag.strip().lower()
            # CIM tag names are short, alphanumeric (with `_`), no spaces.
            if tag and re.match(r"^[a-z][a-z0-9_]{0,31}$", tag):
                state["cim_tags"].add(tag)

    return {
        "name": "Insights Suite for Splunk (IS4S)",
        "splunkbase_id": 7186,
        "license": "Splunk General Terms (not redistributable)",
        "path": str(IS4S_DIR.relative_to(_REPO)),
        **counters,
    }


# ---------------------------------------------------------------------------
# SSE — Splunk Security Essentials (Splunkbase #3435)
# ---------------------------------------------------------------------------


def _ingest_sse_corpus(state: dict[str, Any]) -> dict[str, Any] | None:
    if not SSE_DEFAULT.exists():
        return None

    counters: dict[str, int] = {
        "savedsearches": 0,
        "macros_defined": 0,
        "data_inventory_products": 0,
    }

    savedsearches = SSE_DEFAULT / "savedsearches.conf"
    if savedsearches.exists():
        for _name, kv in _read_conf_stanzas(savedsearches):
            spl = kv.get("search", "").strip()
            if spl:
                _ingest_one_spl(spl, state)
                counters["savedsearches"] += 1

    macros_conf = SSE_DEFAULT / "macros.conf"
    if macros_conf.exists():
        for stanza_name, _kv in _read_conf_stanzas(macros_conf):
            m = re.match(r"^(?P<name>[^(]+)(?:\(\d+\))?\s*$", stanza_name)
            if m:
                state["macros"].add(m.group("name").strip())
                counters["macros_defined"] += 1

    # SSE's data-inventory products lookup includes a regex column that
    # implies the canonical sourcetype prefix (e.g. ``^aws:cloudtrail.*$``).
    # We extract literal sourcetypes from the ``default_sourcetype_search``
    # column when it is a simple ``sourcetype=...`` form.
    products = SSE_LOOKUPS / "SSE-default-data-inventory-products.csv"
    for row in _read_csv_rows(products):
        counters["data_inventory_products"] += 1
        search_clause = (row.get("default_sourcetype_search") or "").strip()
        m = re.match(r"^sourcetype\s*=\s*(?P<v>[^\s]+)$", search_clause)
        if m:
            _add_sourcetype(state, m.group("v"))

    return {
        "name": "Splunk Security Essentials (SSE)",
        "splunkbase_id": 3435,
        "license": "Splunk General Terms (not redistributable)",
        "path": str(SSE_DIR.relative_to(_REPO)),
        **counters,
    }


# ---------------------------------------------------------------------------
# CIM — Common Information Model add-on (Splunkbase #1621)
# ---------------------------------------------------------------------------


def _ingest_cim_corpus(state: dict[str, Any]) -> dict[str, Any] | None:
    """Read the CIM datamodel JSONs and tag/eventtype configs.

    The datamodel JSONs are the canonical source for CIM model and
    dataset names; ``tags.conf`` plus the cim_tags column we already
    harvested from IS4S ssef_splunkbase_apps give us the CIM tag
    vocabulary that end users put in ``tag=...`` predicates.
    """
    if not CIM_DEFAULT.exists():
        return None

    counters: dict[str, int] = {
        "datamodel_files": 0,
        "datasets": 0,
        "tags_conf_lines": 0,
    }

    if CIM_DATAMODELS_DIR.exists():
        for jpath in sorted(CIM_DATAMODELS_DIR.glob("*.json")):
            try:
                payload = json.loads(jpath.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            counters["datamodel_files"] += 1
            model_name = payload.get("modelName") or jpath.stem
            state["cim_models"].add(model_name)

            # Walk the (possibly nested) object hierarchy collecting
            # every ``objectName`` as a dataset path (Model.dataset).
            def _walk_objects(objs: Any, path_prefix: str) -> None:
                if not isinstance(objs, list):
                    return
                for obj in objs:
                    if not isinstance(obj, dict):
                        continue
                    name = obj.get("objectName")
                    if not isinstance(name, str) or not name:
                        continue
                    full = f"{path_prefix}.{name}" if path_prefix else f"{model_name}.{name}"
                    state["datamodel_paths"].add(full)
                    counters["datasets"] += 1
                    _walk_objects(obj.get("children"), full)

            _walk_objects(payload.get("objects"), model_name)
            # Also add the bare model so audit-spl-references treats
            # ``datamodel=Authentication`` (no dataset) as known.
            state["datamodel_paths"].add(model_name)

    # tags.conf — parsed manually because Splunk's stanzas use the
    # ``[key=value]`` form, not the simple ``[name]`` form, so the
    # standard reader's stanza names look like ``action=failure``.
    if CIM_TAGS_CONF.exists():
        text = CIM_TAGS_CONF.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            counters["tags_conf_lines"] += 1
            line = line.strip()
            if not line or line.startswith(("#", "[")):
                continue
            m = re.match(r"^(?P<tag>[A-Za-z][\w]*)\s*=\s*enabled\s*$", line)
            if m:
                state["cim_tags"].add(m.group("tag").lower())

    return {
        "name": "Splunk Common Information Model (CIM) add-on",
        "splunkbase_id": 1621,
        "license": "Splunk General Terms (not redistributable)",
        "path": str(CIM_DIR.relative_to(_REPO)),
        **counters,
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
        "sourcetype_glob_patterns": set(),
        "indexes": set(),
        "datamodel_paths": set(),
        "cim_models": set(),
        "cim_tags": set(),
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
        "sourcetype_glob_patterns": sorted(state["sourcetype_glob_patterns"]),
        "indexes": sorted(state["indexes"]),
        "datamodel_paths": sorted(state["datamodel_paths"]),
        "cim_models": sorted(state["cim_models"]),
        "cim_tags": sorted(state["cim_tags"]),
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
    is4s = _ingest_is4s_corpus(state)
    if is4s:
        sources.append(is4s)
    sse = _ingest_sse_corpus(state)
    if sse:
        sources.append(sse)
    cim = _ingest_cim_corpus(state)
    if cim:
        sources.append(cim)
    escu = _ingest_escu_corpus(state)
    if escu:
        sources.append(escu)

    if not sources and args.check:
        sys.stderr.write(
            "ERROR: no reference corpus found.\n"
            "Looked under:\n"
            f"  {SEARCHBASE_CONF.relative_to(_REPO)}\n"
            f"  {IS4S_DIR.relative_to(_REPO)}\n"
            f"  {SSE_DIR.relative_to(_REPO)}\n"
            f"  {CIM_DIR.relative_to(_REPO)}\n"
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
            f"  commands:       {len(payload['commands'])}\n"
            f"  macros:         {len(payload['macros'])}\n"
            f"  sourcetypes:    {len(payload['sourcetypes'])}\n"
            f"  sourcetype globs: {len(payload['sourcetype_glob_patterns'])}\n"
            f"  indexes:        {len(payload['indexes'])}\n"
            f"  datamodels:     {len(payload['datamodel_paths'])}\n"
            f"  cim models:     {len(payload['cim_models'])}\n"
            f"  cim tags:       {len(payload['cim_tags'])}\n"
            f"  lookups:        {len(payload['lookups'])}\n"
            f"  eval functions: {len(payload['eval_functions'])}\n"
            f"  stats funcs:    {len(payload['stats_functions'])}\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
