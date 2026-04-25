"""tools.build.parse_content — load source-of-truth into an in-memory Catalog.

This module owns the **read** side of the build. Every subsequent
``render_*`` module consumes a single ``Catalog`` object so they can run
in parallel CI jobs without re-reading the filesystem.

Two loaders coexist here, selected by the ``SPLUNK_UC_LOADER`` env var:

* ``content`` (default, v7+): walks ``content/cat-NN-slug/UC-X.Y.Z.json`` —
  the per-UC canonical files emitted by ``migrate_to_per_uc.py`` and
  validated against ``schemas/uc.schema.json``. JSON keys are converted
  back to the v6 short-key form on the way out so downstream renderers
  (``render_api``, ``render_html``, ``templates/uc.py`` …) keep working
  without knowing the on-disk shape changed.

* ``legacy`` (opt-in fallback): delegates to
  ``build.parse_category_file`` + ``build.parse_index_metadata`` —
  the v6 monolithic markdown parser. Useful while the migration is in
  flight; will be removed after ``cleanup-and-docs``.

Both loaders run the same legacy post-processor block (``escu``,
``escu_rba``, ``e``, ``em``, ``sapp``, ``ta_link``, ``pillar``,
``premium``, ``regs``) so every renderer sees byte-identical UC dicts
regardless of which loader produced them.

The Catalog object is intentionally minimal — it carries the same shape
the v6 site uses (see docs/catalog-schema.md):

* ``categories``  list of category dicts ({"i", "n", "s": [...]}; "s" is
                  list of subcategory dicts each with "u" list of UC dicts)
* ``cat_meta``    {str(cat_id): {desc, quick, icon, ...}}
* ``cat_groups``  high-level domain groupings (infra, security, ...)
* ``equipment``   list of equipment definitions
* ``regulations`` regulation_id -> regulation dict (loaded from data/regulations.json)
* ``recently_added`` list of UC IDs added since the previous catalog
* ``files``       list of source markdown filenames (legacy)
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Loader selection
# ---------------------------------------------------------------------------

_LOADER_ENV = "SPLUNK_UC_LOADER"
_LOADER_CONTENT = "content"
_LOADER_LEGACY = "legacy"
_LOADER_DEFAULT = _LOADER_CONTENT


def _resolve_loader_kind() -> str:
    """Return ``"content"`` or ``"legacy"`` based on ``SPLUNK_UC_LOADER``.

    Unknown values fall back to the default loader so a typo in CI
    doesn't silently swap the build to a stale code path.
    """
    raw = (os.environ.get(_LOADER_ENV) or "").strip().lower()
    if raw in (_LOADER_CONTENT, _LOADER_LEGACY):
        return raw
    return _LOADER_DEFAULT


@dataclass
class Catalog:
    """In-memory snapshot of every data source the renderers consume."""

    project_root: Path
    categories: list[dict[str, Any]] = field(default_factory=list)
    cat_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    cat_groups: dict[str, list[int]] = field(default_factory=dict)
    equipment: list[dict[str, Any]] = field(default_factory=list)
    regulations: dict[str, dict[str, Any]] = field(default_factory=dict)
    recently_added: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    facets: dict[str, Any] = field(default_factory=dict)
    loader: str = _LOADER_DEFAULT
    # Populated by render_assets so later stages (html_rewrite, integrity)
    # can resolve the fingerprinted bundle filenames + critical-CSS payload.
    asset_hashes: dict[str, str] = field(default_factory=dict)
    critical_css: str = ""

    @property
    def uc_count(self) -> int:
        return sum(
            len(sub.get("u", []))
            for cat in self.categories
            for sub in cat.get("s", [])
        )

    def iter_ucs(self):
        for cat in self.categories:
            for sub in cat.get("s", []):
                for uc in sub.get("u", []):
                    yield cat, sub, uc

    def uc_by_id(self, uc_id: str) -> Optional[dict[str, Any]]:
        for _cat, _sub, uc in self.iter_ucs():
            if uc.get("i") == uc_id:
                return uc
        return None


def empty(project_root: Optional[Path] = None) -> Catalog:
    """Return an empty Catalog (used when stages run with --only)."""
    return Catalog(project_root=project_root or Path.cwd())


def load(project_root: Path, *, reproducible: bool = False) -> Catalog:
    """Load every source-of-truth artefact into a single Catalog."""
    cat = Catalog(project_root=project_root, loader=_resolve_loader_kind())
    _load_categories(cat, project_root, reproducible=reproducible)
    _load_cat_meta(cat, project_root)
    _load_cat_groups(cat)
    _load_equipment(cat)
    _load_regulations(cat, project_root)
    _load_recently_added(cat, project_root)
    _load_facets(cat)
    return cat


# ---------------------------------------------------------------------------
# Legacy module loader (shared by both loader paths)
# ---------------------------------------------------------------------------

_LEGACY = None


def _legacy_module():
    """Import the v6 build.py as a callable module.

    We load it by absolute path with importlib so the import does not
    collide with the new ``tools.build`` package (which shadows the
    bare ``build`` name on sys.path). We also cache the imported module
    so repeated calls don't re-exec 3 366 lines of legacy code.
    """
    global _LEGACY
    if _LEGACY is not None:
        return _LEGACY
    import importlib.util

    legacy_path = Path(__file__).resolve().parent.parent.parent / "build.py"
    spec = importlib.util.spec_from_file_location("_legacy_build", legacy_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load legacy build.py from {legacy_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_legacy_build"] = module
    spec.loader.exec_module(module)
    _LEGACY = module
    return module


# ---------------------------------------------------------------------------
# Category loaders
# ---------------------------------------------------------------------------

def _load_categories(cat: Catalog, project_root: Path, *, reproducible: bool) -> None:
    """Dispatch to the configured loader and populate ``cat.categories``."""
    if cat.loader == _LOADER_CONTENT:
        _load_categories_from_content(cat, project_root, reproducible=reproducible)
    else:
        _load_categories_from_legacy(cat, project_root, reproducible=reproducible)


def _load_categories_from_legacy(
    cat: Catalog, project_root: Path, *, reproducible: bool
) -> None:
    legacy = _legacy_module()
    pattern = str(project_root / "use-cases" / "cat-[0-9]*.md")
    files = sorted(glob.glob(pattern))
    cat.files = [Path(f).name for f in files]
    for filepath in files:
        record = legacy.parse_category_file(filepath)
        if "i" not in record:
            continue
        cat.categories.append(record)
    if reproducible:
        cat.categories.sort(key=lambda c: c["i"])


def _load_categories_from_content(
    cat: Catalog, project_root: Path, *, reproducible: bool
) -> None:
    """Walk content/cat-NN-slug/ → emit short-key category records.

    Behaviour parity with ``_load_categories_from_legacy``:

    * The category record schema is identical
      ({"i", "n", "s": [{"i", "n", "u": [...]}]}).
    * Every UC dict is initialised with the same default short-keys
      ``parse_category_file`` produces, so consumers calling
      ``uc.get("kfp", "")`` etc. see the same shape.
    * The same post-processor block runs at the end of each category
      (``is_escu_detection`` → ``escu`` / ``escu_rba`` / regenerated
      ``md``; equipment tagging from sidecar or TA string; ``sapp``;
      ``ta_link``; ``pillar``; ``premium``; ``regs``).
    """
    content_dir = project_root / "content"
    if not content_dir.exists():
        # Defensive: never explode in CI when the migration hasn't run.
        return
    cat_dirs = sorted(d for d in content_dir.iterdir() if d.is_dir())
    legacy = _legacy_module()
    legacy.UC_DIR = str(project_root / "use-cases")  # equipment sidecars still live there until cleanup
    cat.files = []
    for cat_dir in cat_dirs:
        meta_path = cat_dir / "_category.json"
        if not meta_path.exists():
            continue
        try:
            with meta_path.open(encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: skipping {meta_path}: {exc}", file=sys.stderr)
            continue
        cat_id = meta.get("id")
        if cat_id is None:
            continue
        try:
            cat_id_int = int(cat_id)
        except (TypeError, ValueError):
            continue

        record: dict[str, Any] = {
            "i": cat_id_int,
            "n": meta.get("name", ""),
            "s": [],
        }
        if meta.get("src"):
            cat.files.append(meta["src"])

        # Build subcategory shells in the order ``_category.json``
        # advertises them. A handful of legacy categories (notably
        # cat-22) have two markdown sections sharing the same numerical
        # id (e.g. '### 22.3 DORA' and '### 22.3 — DORA (extended
        # clauses)'). We disambiguate them via an optional ``bucketKey``
        # field on each sub entry (format ``"<id>#<n>"``, 1-indexed for
        # the second and later occurrences). The sub record's public
        # ``"i"`` always remains the bare public id so downstream
        # renderers / schema validators see the same shape they did
        # under the legacy loader.
        sub_buckets: dict[str, dict[str, Any]] = {}
        for sub in meta.get("subcategories", []) or []:
            sub_id = sub.get("id")
            if not sub_id:
                continue
            bucket_key = sub.get("bucketKey") or sub_id
            sub_record: dict[str, Any] = {
                "i": sub_id,
                "n": sub.get("name", ""),
                "u": [],
            }
            if sub.get("guide"):
                sub_record["g"] = sub["guide"]
            sub_buckets[bucket_key] = sub_record
            record["s"].append(sub_record)

        # Read every UC-X.Y.Z.json under this category and place it in
        # the matching subcategory bucket. The bucket key is determined
        # by ``canonical["subcategory"]`` when present (UC explicitly
        # cross-listed — e.g. UC-4.4.32 → '4.5' — or filed under a
        # disambiguated duplicate id — e.g. '22.3#1'); otherwise we
        # fall back to the natural id prefix. UCs whose bucket isn't
        # declared in _category.json get an auto-stub bucket so the
        # build never silently drops a UC. The stub's public ``"i"``
        # has any ``#<n>`` disambiguator stripped so it stays a valid
        # ``^\d+\.\d+$`` id.
        uc_files = sorted(cat_dir.glob("UC-*.json"))
        for uc_path in uc_files:
            try:
                with uc_path.open(encoding="utf-8") as f:
                    canonical = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"WARNING: skipping {uc_path}: {exc}", file=sys.stderr)
                continue
            uc_id = canonical.get("id") or ""
            if not uc_id:
                continue
            explicit_sub = canonical.get("subcategory")
            if isinstance(explicit_sub, str) and explicit_sub.strip():
                bucket_key = explicit_sub.strip()
            else:
                bucket_key = ".".join(uc_id.split(".")[:2])
            sub_record = sub_buckets.get(bucket_key)
            if sub_record is None:
                public_sub_id = bucket_key.split("#", 1)[0]
                sub_record = {"i": public_sub_id, "n": "", "u": []}
                sub_buckets[bucket_key] = sub_record
                record["s"].append(sub_record)
            uc_short = _canonical_uc_to_legacy(canonical)
            sub_record["u"].append(uc_short)

        # Re-derive every field the legacy post-processor block sets.
        _post_process_category(record, legacy)

        # Compute quality scores and inject into UC + subcategory dicts.
        _inject_quality_scores(record)

        cat.categories.append(record)

    if reproducible:
        cat.categories.sort(key=lambda c: c["i"])


# ---------------------------------------------------------------------------
# Canonical → short-key conversion
# ---------------------------------------------------------------------------

# Empty-string defaults that ``parse_category_file`` initialises on every
# UC dict. We mirror them so downstream code calling ``uc.get("v")``
# (no default) continues to get ``""`` instead of ``None``.
_LEGACY_STRING_DEFAULTS = (
    "c", "f", "v", "t", "d", "q", "m", "z",
    "kfp", "refs", "dtype", "sdomain", "reqf", "md", "script",
    "premium", "hw", "dma", "schema", "status", "reviewed", "sver", "rby",
    "ge",  # grandmaExplanation — plain-language summary for non-technical view
)
_LEGACY_LIST_DEFAULTS = ("mitre",)


def _legacy_default_uc() -> dict[str, Any]:
    """Return the same UC skeleton ``parse_category_file`` initialises."""
    out: dict[str, Any] = {key: "" for key in _LEGACY_STRING_DEFAULTS}
    for key in _LEGACY_LIST_DEFAULTS:
        out[key] = []
    return out


def _premium_to_legacy(value: Any) -> str:
    """Flatten canonical premiumApps (list of str / object) → legacy string.

    The canonical schema lets curators record the same parenthetical
    qualifier in two places: as a trailing ``(…)`` baked into
    ``displayName`` *and* as a structured ``note`` field. Without
    de-duplication that round-trips to the legacy renderer as
    ``"X (note) (note)"`` (see UC-22.1.6 regression). When ``displayName``
    already carries the note, drop the structured copy. When only one of
    the two is present, render that one.
    """
    if not isinstance(value, list):
        return ""
    parts: list[str] = []
    for item in value:
        if isinstance(item, str):
            parts.append(item.strip())
            continue
        if not isinstance(item, dict):
            continue
        display = (item.get("displayName") or item.get("name") or "").strip()
        if not display:
            continue
        note = (item.get("note") or "").strip()
        if note and f"({note})" not in display:
            parts.append(f"{display} ({note})")
        else:
            parts.append(display)
    return ", ".join(p for p in parts if p)


def _references_to_legacy(value: Any) -> str:
    """Flatten canonical references (list of objects) → legacy string."""
    if not isinstance(value, list):
        return ""
    parts: list[str] = []
    for ref in value:
        if not isinstance(ref, dict):
            continue
        url = (ref.get("url") or "").strip()
        if not url:
            continue
        title = (ref.get("title") or "").strip()
        parts.append(f"[{title}]({url})" if title else url)
    return ", ".join(parts)


def _list_to_csv(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ", ".join(str(v).strip() for v in value if str(v).strip())


def _canonical_uc_to_legacy(canonical: dict[str, Any]) -> dict[str, Any]:
    """Convert a canonical UC dict back to the v6 short-key shape.

    Lossy fields (``references``, ``premiumApps``, ``splunkVersions``,
    ``requiredFields``) are flattened to the comma-separated string form
    the legacy parser produced — this is the form every downstream
    renderer expects. The post-processor block replaces ``pillar`` and
    ``premium`` if it can derive better values from the apps registry.
    """
    uc = _legacy_default_uc()
    uc["i"] = str(canonical.get("id") or "")
    uc["n"] = str(canonical.get("title") or "").strip()

    # Direct string passthroughs (canonical key → short key)
    str_passthroughs = (
        ("criticality", "c"),
        ("difficulty", "f"),
        ("value", "v"),
        ("app", "t"),
        ("dataSources", "d"),
        ("spl", "q"),
        ("implementation", "m"),
        ("detailedImplementation", "md"),
        ("scriptExample", "script"),
        ("visualization", "z"),
        ("knownFalsePositives", "kfp"),
        ("detectionType", "dtype"),
        ("securityDomain", "sdomain"),
        ("dataModelAcceleration", "dma"),
        ("schema", "schema"),
        ("status", "status"),
        ("lastReviewed", "reviewed"),
        ("reviewer", "rby"),
        ("industry", "ind"),
        ("hardware", "hw"),
        ("telcoUseCase", "tuc"),
        ("wave", "wv"),
        ("grandmaExplanation", "ge"),
    )
    for canonical_key, short_key in str_passthroughs:
        v = canonical.get(canonical_key)
        if isinstance(v, str) and v != "":
            uc[short_key] = v

    # NOTE: ``splunkPillar`` is intentionally *not* propagated to
    # ``uc["pillar"]`` here. The legacy post-processor's
    # ``assign_pillar`` returns early if ``uc.get("pillar")`` already
    # holds a value, which would short-circuit the v6-equivalent
    # category-aware derivation and leave 345 UCs with a different
    # pillar than the legacy build produces. We let assign_pillar
    # always recompute from cat_id + sub_id + app + dataSources.

    # Lists that legacy stores as lists.
    if isinstance(canonical.get("monitoringType"), list):
        mtypes = [str(m).strip() for m in canonical["monitoringType"] if str(m).strip()]
        if mtypes:
            uc["mtype"] = mtypes
    if isinstance(canonical.get("cimModels"), list):
        models = [str(m).strip() for m in canonical["cimModels"] if str(m).strip()]
        if models:
            uc["a"] = models
    if isinstance(canonical.get("mitreAttack"), list):
        ids = [str(m).strip() for m in canonical["mitreAttack"] if str(m).strip()]
        if ids:
            uc["mitre"] = ids
    if isinstance(canonical.get("equipment"), list):
        eq = [str(e).strip() for e in canonical["equipment"] if str(e).strip()]
        if eq:
            uc["e"] = eq
    if isinstance(canonical.get("equipmentModels"), list):
        em = [str(e).strip() for e in canonical["equipmentModels"] if str(e).strip()]
        if em:
            uc["em"] = em

    # prerequisiteUseCases → sorted, deduped list stored as "pre".
    # Normalised to the canonical "UC-X.Y.Z" form. Validation (unknown
    # ids, cycles) happens later in build.py::validate_prerequisites.
    if isinstance(canonical.get("prerequisiteUseCases"), list):
        pre = sorted(
            {
                str(p).strip()
                for p in canonical["prerequisiteUseCases"]
                if isinstance(p, str) and str(p).strip()
            }
        )
        if pre:
            uc["pre"] = pre

    # cimSpl
    cim_spl = canonical.get("cimSpl")
    if isinstance(cim_spl, str) and cim_spl.strip():
        uc["qs"] = cim_spl

    # premiumApps → legacy string
    premium_str = _premium_to_legacy(canonical.get("premiumApps"))
    if premium_str:
        uc["premium"] = premium_str

    # references → legacy "[Title](url), ..." string
    refs_str = _references_to_legacy(canonical.get("references"))
    if refs_str:
        uc["refs"] = refs_str

    # requiredFields list → legacy comma string
    req_str = _list_to_csv(canonical.get("requiredFields"))
    if req_str:
        uc["reqf"] = req_str

    # splunkVersions list → legacy string ("9.2+, Cloud").
    sver_str = _list_to_csv(canonical.get("splunkVersions"))
    if sver_str:
        uc["sver"] = sver_str

    # ``regs``: legacy populates this from the markdown line; in canonical
    # we materialised it via the ``compliance`` array. Pull both back so
    # the post-processor's ``manual_regs ∪ auto_regs`` union behaves the
    # same as v6.
    manual_regs: list[str] = []
    seen_regs: set[str] = set()
    if isinstance(canonical.get("compliance"), list):
        for entry in canonical["compliance"]:
            if not isinstance(entry, dict):
                continue
            reg = entry.get("regulation")
            if isinstance(reg, str) and reg and reg not in seen_regs:
                manual_regs.append(reg)
                seen_regs.add(reg)
    # An optional ``regs`` field on the canonical (sidecar-merged) UC
    # always wins — it's the curator-facing list rendered on the card.
    if isinstance(canonical.get("regs"), list):
        for raw in canonical["regs"]:
            if isinstance(raw, str) and raw and raw not in seen_regs:
                manual_regs.append(raw)
                seen_regs.add(raw)
    if manual_regs:
        uc["regs"] = manual_regs

    # ``cmp``: compact projection of the canonical ``compliance[]`` array
    # for the Phase 3a clause-level implementer UI. We only forward the
    # fields the detail panel and the two-level filter actually need so
    # ``data.js`` does not bloat the initial bundle. The full record
    # (assurance rationale, provenance, legal caveat, obligationRef,
    # etc.) stays in ``api/v1/compliance/clauses/*.json`` and is pulled
    # on demand when a user opens the panel. Keys used here match the
    # Phase 1 schema v1.6.0 fields: ``regulation`` / ``version`` /
    # ``clause`` / ``mode`` / ``assurance`` / ``controlObjective`` /
    # ``evidenceArtifact`` / ``clauseUrl``. Entries without
    # regulation+version+clause are dropped because they can't be
    # deep-linked in the clause filter.
    raw_compliance = canonical.get("compliance")
    if isinstance(raw_compliance, list):
        cmp_rows: list[dict[str, Any]] = []
        for entry in raw_compliance:
            if not isinstance(entry, dict):
                continue
            reg = entry.get("regulation")
            ver = entry.get("version")
            clause = entry.get("clause")
            if not (isinstance(reg, str) and reg and isinstance(ver, str) and ver
                    and isinstance(clause, str) and clause):
                continue
            row: dict[str, Any] = {
                "r": reg.strip(),
                "v": ver.strip(),
                "cl": clause.strip(),
            }
            mode = entry.get("mode")
            if isinstance(mode, str) and mode.strip():
                row["m"] = mode.strip()
            assurance = entry.get("assurance")
            if isinstance(assurance, str) and assurance.strip():
                row["a"] = assurance.strip()
            co = entry.get("controlObjective")
            if isinstance(co, str) and co.strip():
                row["co"] = co.strip()
            ea = entry.get("evidenceArtifact")
            if isinstance(ea, str) and ea.strip():
                row["ea"] = ea.strip()
            url = entry.get("clauseUrl")
            if isinstance(url, str) and url.strip():
                row["u"] = url.strip()
            cmp_rows.append(row)
        if cmp_rows:
            cmp_rows.sort(key=lambda x: (x["r"], x["v"], x["cl"]))
            uc["cmp"] = cmp_rows

    return uc


# ---------------------------------------------------------------------------
# Post-processor (shared by both loaders)
# ---------------------------------------------------------------------------

def _post_process_category(record: dict[str, Any], legacy) -> None:
    """Re-run the v6 build.py post-processor block on a category record.

    Mirrors lines 2231-2287 of build.py exactly so the resulting UC
    dicts are byte-identical to the legacy build's output.
    """
    cat_id = record.get("i", 0)
    for sub in record.get("s", []):
        sub_id = sub.get("i", "")
        for uc in sub.get("u", []):
            if legacy.is_escu_detection(uc):
                uc["escu"] = True
                uc["escu_rba"] = legacy._escu_is_rba(uc)
                uc["md"] = legacy.generate_escu_detailed_impl(uc)
                m_text = (uc.get("m") or "").lower()
                if (
                    m_text.startswith(legacy.ESCU_GENERIC_IMPL_PREFIX)
                    or not m_text.strip()
                ):
                    uc["m"] = legacy.generate_escu_short_impl(uc)
            elif not (uc.get("md") or "").strip():
                uc["md"] = legacy.generate_detailed_impl(uc)

            sidecar_eq, sidecar_models = legacy._sidecar_equipment_tags(
                cat_id, uc.get("i")
            )
            if sidecar_eq is not None:
                uc["e"] = sidecar_eq
                uc["em"] = sidecar_models
            elif not uc.get("e"):
                eq_ids, model_ids = legacy.equipment_ids_for_ta_string(uc.get("t"))
                uc["e"] = eq_ids
                uc["em"] = model_ids
            elif uc.get("em") is None:
                # Content-loader path: ``e`` arrived from canonical (the
                # legacy build had already derived it from the TA string
                # at migration time and we round-tripped it), but
                # ``em`` was dropped because it was an empty list (the
                # migration script only emits non-empty fields). The
                # legacy build always sets ``em`` to *some* list value
                # — never leaves it ``None`` — so re-derive from the
                # TA string here to restore byte-identical output.
                _, model_ids = legacy.equipment_ids_for_ta_string(uc.get("t"))
                uc["em"] = model_ids

            matched_apps = legacy.apps_for_ta_string(uc.get("t"))
            if matched_apps:
                uc["sapp"] = matched_apps
            ta_link = legacy.ta_link_for_ta_string(uc.get("t"))
            if ta_link:
                uc["ta_link"] = ta_link
            uc["pillar"] = legacy.assign_pillar(uc, cat_id)

            if not uc.get("premium"):
                auto_premium = legacy.assign_premium(uc)
                if auto_premium:
                    uc["premium"] = auto_premium

            manual_regs = set(uc.get("regs", []))
            auto_regs = set(legacy.assign_regulations(uc, cat_id, sub_id))
            final_regs = sorted(manual_regs | auto_regs)
            if final_regs:
                uc["regs"] = final_regs


# ---------------------------------------------------------------------------
# Quality score computation (Gold Standard)
# ---------------------------------------------------------------------------

_QUALITY_BRONZE_FIELDS = {"i", "n", "c", "f", "q", "v", "d", "t", "m"}
_QUALITY_SILVER_EXTRA = {"mtype", "md", "refs", "e", "ge", "wv"}
_QUALITY_GOLD_EXTRA = {"z", "em"}

_QS_BOILERPLATE_RE = re.compile(
    r"install the (?:ta|add-on|app) and (?:configure|enable)|"
    r"check (?:splunkd\.log|the logs|your data)|"
    r"ensure (?:the|your) (?:ta|add-on|app) is (?:installed|configured)",
    re.IGNORECASE,
)
_QS_PRODUCT_RE = re.compile(
    r"sourcetype\s*[=:\"]\s*\S+|index\s*=\s*\S+|"
    r"/(?:api|dna|v[12]|rest)/|inputs\.conf|modular\s+input|"
    r"(?:GET|POST|PUT)\s+/|\d+\s*(?:seconds?|minutes?|hours?)\b|"
    r"(?:RBAC|role|permission|SUPER-ADMIN|NETWORK-ADMIN)|"
    r"(?:Splunkbase|splunkbase)\s+\d{3,}",
    re.IGNORECASE,
)
_QS_SECTION_PATTERNS = [
    re.compile(r"(?:prerequisite|step\s*0|before\s+you\s+begin)", re.IGNORECASE),
    re.compile(r"(?:step\s*1|configure\s+data|data\s+collection)", re.IGNORECASE),
    re.compile(r"(?:step\s*2|create\s+the\s+search|understanding\s+this\s+spl)", re.IGNORECASE),
    re.compile(r"(?:step\s*3|validat)", re.IGNORECASE),
    re.compile(r"(?:step\s*4|step\s*5|operationaliz|troubleshoot)", re.IGNORECASE),
]


def _compute_quality(uc: dict[str, Any]) -> tuple[str, int, list[str]]:
    """Return (tier, depth_score, gaps) for a legacy-keyed UC dict."""
    def _present(key: str) -> bool:
        v = uc.get(key)
        if v is None:
            return False
        if isinstance(v, str):
            return len(v.strip()) > 0
        return True

    gaps: list[str] = []

    # Bronze
    bronze = all(_present(k) for k in _QUALITY_BRONZE_FIELDS)
    if not bronze:
        missing = [k for k in _QUALITY_BRONZE_FIELDS if not _present(k)]
        return ("none", max(0, 10 - len(missing) * 2), [f"missing: {k}" for k in missing])

    depth = 25

    # Silver
    silver_missing = [k for k in _QUALITY_SILVER_EXTRA if not _present(k)]
    silver = not silver_missing
    md_text = uc.get("md", "") or ""
    sections_matched = 0
    if isinstance(md_text, str):
        sections_matched = sum(1 for p in _QS_SECTION_PATTERNS if p.search(md_text))
    if silver and isinstance(md_text, str):
        if sections_matched < 3:
            silver = False
            gaps.append("detailedImplementation needs at least 3 named sections (has %d)" % sections_matched)
        if len(md_text) < 200:
            silver = False
            gaps.append("detailedImplementation is too short for Silver (%d chars, need 200+)" % len(md_text))
    if silver_missing:
        for k in silver_missing:
            _FIELD_LABELS = {"mtype": "monitoring type", "md": "detailed implementation",
                             "refs": "references", "e": "equipment", "ge": "plain-language explanation", "wv": "wave"}
            gaps.append("add %s for Silver tier" % _FIELD_LABELS.get(k, k))
    if silver:
        depth = 50

    # Gold
    gold_missing = [k for k in _QUALITY_GOLD_EXTRA if not _present(k)]
    gold = silver and not gold_missing
    if gold and isinstance(md_text, str):
        if sections_matched < 4:
            gold = False
            gaps.append("detailedImplementation needs at least 4 named sections for Gold (has %d)" % sections_matched)
        if len(md_text) < 500:
            gold = False
            gaps.append("detailedImplementation is too short for Gold (%d chars, need 500+)" % len(md_text))
        refs = uc.get("refs", "")
        if isinstance(refs, str):
            ref_count = len([u for u in refs.split("),") if u.strip()])
        else:
            ref_count = 0
        if ref_count < 2:
            gold = False
            gaps.append("add at least 2 references for Gold tier")
    elif silver and gold_missing:
        _GOLD_LABELS = {"z": "visualization guidance", "em": "equipment models"}
        for k in gold_missing:
            gaps.append("add %s for Gold tier" % _GOLD_LABELS.get(k, k))
    if gold:
        depth = 75

    # Depth bonuses/penalties with gap tracking
    has_specificity_bonus = False
    has_vendor_ui = False
    has_troubleshooting = False

    if isinstance(md_text, str) and md_text:
        specificity = len(_QS_PRODUCT_RE.findall(md_text))
        if specificity >= 5:
            depth += 10
            has_specificity_bonus = True
        elif specificity >= 3:
            depth += 5
            has_specificity_bonus = True
        elif specificity < 2 and len(md_text) > 300:
            gaps.append("implementation lacks product-specific terms (sourcetypes, API paths, field names)")

        sentences = [s.strip() for s in re.split(r"[.!?\n]", md_text) if len(s.strip()) > 15]
        if sentences:
            generic = sum(1 for s in sentences if _QS_BOILERPLATE_RE.search(s))
            if generic / len(sentences) > 0.5:
                depth -= 15
                gaps.append("implementation is >50%% generic boilerplate")

        md_lower = md_text.lower()
        has_vendor_ui = bool(re.search(
            r"vendor\s+(?:ui|dashboard|console|portal|gui)|compare\s+(?:to|with|against)\s+(?:the\s+)?(?:vendor|native)|"
            r"(?:assurance|dashboard|portal|console)\s*(?:>|›|→|page)|cross.?reference|verify\s+(?:in|against)\s+(?:the\s+)?(?:vendor|native)",
            md_lower))
        if has_vendor_ui:
            depth += 5
        elif gold:
            gaps.append("validation step should reference vendor UI for comparison")

        has_troubleshooting = bool(re.search(
            r"(?:no\s+events?\s+appear|events?\s+(?:are\s+)?missing|data\s+(?:is\s+)?not\s+(?:arriving|flowing|appearing))|"
            r"(?:permission\s+denied|access\s+denied|unauthorized|403|401)|"
            r"(?:timeout|connection\s+refused|unreachable|dns\s+resolution)|"
            r"(?:check\s+(?:that|whether|if)\s+the\s+(?:input|modular\s+input|scripted\s+input))",
            md_lower))
        if has_troubleshooting:
            depth += 5
        elif gold or silver:
            gaps.append("troubleshooting should mention product-specific failure modes")

    tier = "gold" if gold else ("silver" if silver else "bronze")
    return (tier, max(0, min(100, depth)), gaps)


def _inject_quality_scores(record: dict[str, Any]) -> None:
    """Add quality scores to each UC and aggregate per subcategory."""
    for sub in record.get("s", []):
        scores: list[int] = []
        tier_dist = {"gold": 0, "silver": 0, "bronze": 0, "none": 0}
        for uc in sub.get("u", []):
            tier, depth, gaps = _compute_quality(uc)
            uc["_qs"] = depth
            uc["_qt"] = tier
            if gaps:
                uc["_qg"] = gaps
            scores.append(depth)
            tier_dist[tier] += 1
        if scores:
            sub["qa"] = round(sum(scores) / len(scores), 1)
            sub["qd"] = tier_dist


# ---------------------------------------------------------------------------
# Cat-meta loaders
# ---------------------------------------------------------------------------

def _load_cat_meta(cat: Catalog, project_root: Path) -> None:
    if cat.loader == _LOADER_CONTENT:
        _load_cat_meta_from_content(cat, project_root)
    else:
        legacy = _legacy_module()
        legacy.UC_DIR = str(project_root / "use-cases")
        cat_meta, _starters = legacy.parse_index_metadata()
        cat.cat_meta = cat_meta


def _load_cat_meta_from_content(cat: Catalog, project_root: Path) -> None:
    """Build ``cat_meta`` from per-category ``_category.json`` files.

    Mirrors what ``parse_index_metadata`` returns for the cat_meta half
    (icon/desc/quick). Quick-Start data is exposed via the per-category
    JSON's ``quickStart`` field; the renderers that need it should read
    it from there.
    """
    content_dir = project_root / "content"
    if not content_dir.exists():
        return
    out: dict[str, dict[str, Any]] = {}
    for cat_dir in sorted(content_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        meta_path = cat_dir / "_category.json"
        if not meta_path.exists():
            continue
        try:
            with meta_path.open(encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        cid = meta.get("id")
        if cid is None:
            continue
        entry: dict[str, Any] = {"icon": "", "desc": ""}
        if meta.get("icon"):
            entry["icon"] = meta["icon"]
        if meta.get("description"):
            entry["desc"] = meta["description"]
        if meta.get("quickTip"):
            entry["quick"] = meta["quickTip"]
        out[str(cid)] = entry
    cat.cat_meta = out


def _load_cat_groups(cat: Catalog) -> None:
    legacy = _legacy_module()
    cat.cat_groups = legacy.CAT_GROUPS


def _load_equipment(cat: Catalog) -> None:
    legacy = _legacy_module()
    cat.equipment = legacy.EQUIPMENT


def _load_regulations(cat: Catalog, project_root: Path) -> None:
    p = project_root / "data" / "regulations.json"
    if not p.exists():
        return
    try:
        with p.open(encoding="utf-8") as f:
            obj = json.load(f)
    except (OSError, json.JSONDecodeError):
        return

    candidates = []
    if isinstance(obj, dict):
        for key in ("frameworks", "regulations"):
            if isinstance(obj.get(key), list):
                candidates = obj[key]
                break
    elif isinstance(obj, list):
        candidates = obj

    for reg in candidates:
        if not isinstance(reg, dict):
            continue
        reg_id = reg.get("id") or reg.get("shortName") or reg.get("name")
        if not reg_id:
            continue
        cat.regulations[str(reg_id)] = reg


def _load_recently_added(cat: Catalog, project_root: Path) -> None:
    p = project_root / "recently-added.json"
    if not p.exists():
        return
    try:
        with p.open(encoding="utf-8") as f:
            cat.recently_added = json.load(f) or []
    except (OSError, json.JSONDecodeError, ValueError):
        cat.recently_added = []


def _load_facets(cat: Catalog) -> None:
    legacy = _legacy_module()
    if hasattr(legacy, "extract_filter_facets"):
        cat.facets = legacy.extract_filter_facets(cat.categories)


# ---------------------------------------------------------------------------
# Diagnostics helpers (used by tests / CLI)
# ---------------------------------------------------------------------------

def loader_kind() -> str:
    """Public read of the active loader kind. Test-friendly."""
    return _resolve_loader_kind()


def reset_legacy_module_cache() -> None:
    """Drop the cached legacy module. Required for env-var-flip tests."""
    global _LEGACY
    _LEGACY = None
    sys.modules.pop("_legacy_build", None)


# Catch any future re-export needs without cluttering the public surface.
__all__ = [
    "Catalog",
    "empty",
    "load",
    "loader_kind",
    "reset_legacy_module_cache",
]


# Internal: keep ``re`` import live (used inside helper hooks once
# ``_canonical_uc_to_legacy`` grows free-form parsing). Avoid the
# F401 lint warning explicitly.
_ = re
