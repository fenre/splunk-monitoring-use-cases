"""tools.build.render_search — sharded full-text search index.

Replaces the in-memory ``_searchBlob`` linear scan over the legacy 39 MB
``data.js`` payload with a static, sharded inverted index served from
``dist/assets/``.

Outputs
-------
* ``dist/assets/search-vocab.json``                  (~150 KB raw / ~45 KB gz)
* ``dist/assets/search-shard-NN.<hash>.json`` × 16   (~80 KB gz per shard)

The vocab keeps a stable filename so the SPA can fetch it cold without
needing to know its hash; per-shard filenames carry a content hash so
the client can cache them forever and still get coherent updates when
the catalogue is rebuilt.

Format (v2)
-----------
**vocab.json**::

    {
      "$schema":     "/schemas/v2/search-index.schema.json",
      "version":     2,
      "shardCount":  16,
      "hash":        "fnv1a32",            # how shards are routed
      "ucIds":       ["1.1.1", ...],       # array index = compact docid
      "tokens":      ["abuse", ...],       # sorted, full vocabulary
      "shardFiles":  [                     # by shard id, content-hashed
        "search-shard-00.abc123def4.json",
        ...
      ]
    }

**search-shard-NN.<hash>.json**::

    {
      "version":  2,
      "shard":    NN,
      "postings": {
        "splunk": "0,5,10,17,...",         # sorted compact docids, comma-joined
        ...
      }
    }

Design notes
------------
* Boolean inverted index, not BM25. Search results inherit whatever sort
  order the user has selected (criticality / difficulty / name / …);
  the search engine only contributes membership, not ranking.
* Tokens with df < 2 (typos, hapax legomena) and df > 4000 (≈60% of
  corpus — boilerplate words like "splunk", "configure", "verify") are
  excluded; they have zero discriminative value.
* Shards are routed by ``fnv1a32(token) % shardCount``; on a query, the
  client fetches only the shards whose buckets contain the query's
  tokens (typically 1–2 of 16). Vocab is pulled once per session.
* Compact docids (``ucIds.indexOf(uc.i)``) keep posting lists ~3 bytes
  per entry instead of 8 for ``"X.YY.ZZZ"``.

Stability
---------
Bumping ``shardCount`` invalidates every cached shard at the client.
``hash`` is locked at ``"fnv1a32"``; changing it triggers a full client
re-download and bumps the schema major version. The ``$schema`` URL pins
the field shape; new fields are additive only.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .parse_content import Catalog


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

SHARD_COUNT = 16
"""Total number of shards. Must equal the value in vocab.json. Bumping
this breaks every cached shard at the client."""

MIN_TOKEN_LEN = 3
MAX_TOKEN_LEN = 30
MIN_DF = 2
MAX_DF = 4_000
"""Token must appear in at least ``MIN_DF`` UCs (filters typos) and at
most ``MAX_DF`` (filters near-universal boilerplate). For ~6.4k docs,
DF=4000 ≈ 62% of corpus."""

# Ordered: highest-weight fields first (logical order — we don't actually
# weight). Field names match the per-UC JSON keys produced by parse_content.
# Heavy fields (q, md, refs) ARE indexed even though they aren't shipped in
# the catalog-index.json stubs — the search index is materialised once at
# build time, so the client never has to load them.
SEARCHABLE_FIELDS: tuple[str, ...] = (
    "n",      # name
    "v",      # value/why-it-matters
    "d",      # data sources
    "t",      # apps/TAs
    "q",      # full SPL search
    "md",     # full markdown narrative
    "a",      # CIM model tags (list)
    "mtype",  # monitoring types (list)
    "regs",   # regulations (list)
    "e",      # equipment ids (list)
    "em",     # equipment models (list)
    "mitre",  # MITRE T-IDs (list)
    "ind",    # industry
    "dtype",  # detection type
)

_TOKEN_RE = re.compile(r"[a-z0-9_]+")
_HASH_LEN = 10  # match render_assets.HASH_LEN


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def render(catalog: Catalog, out_dir: Path, *, reproducible: bool = False) -> None:
    """Emit ``dist/assets/search-vocab.json`` + 16 fingerprinted shard files."""
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    docs = _collect_docs(catalog)
    if not docs:
        return

    uc_ids = sorted(docs.keys(), key=_sort_key)
    uc_idx = {u: i for i, u in enumerate(uc_ids)}

    postings = _build_postings(docs, uc_idx)
    shards = _shard_postings(postings)

    shard_files: list[str] = []
    for shard_id in range(SHARD_COUNT):
        payload = {
            "version": 2,
            "shard": shard_id,
            "postings": shards.get(shard_id, {}),
        }
        body = (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=reproducible,
                separators=(",", ":"),
            )
            + "\n"
        )
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()[:_HASH_LEN]
        name = f"search-shard-{shard_id:02d}.{sha}.json"
        (assets / name).write_text(body, encoding="utf-8")
        shard_files.append(name)

    vocab = {
        "$schema": "/schemas/v2/search-index.schema.json",
        "version": 2,
        "shardCount": SHARD_COUNT,
        "hash": "fnv1a32",
        "ucIds": uc_ids,
        "tokens": sorted(postings.keys()),
        "shardFiles": shard_files,
    }
    vocab_path = assets / "search-vocab.json"
    vocab_path.write_text(
        json.dumps(
            vocab,
            ensure_ascii=False,
            sort_keys=reproducible,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    catalog.asset_hashes["search_index_tokens"] = str(len(postings))
    catalog.asset_hashes["search_index_docs"] = str(len(uc_ids))
    catalog.asset_hashes["search_vocab"] = "search-vocab.json"


# ---------------------------------------------------------------------------
# Tokenisation + inverted index
# ---------------------------------------------------------------------------

def _collect_docs(catalog: Catalog) -> dict[str, set[str]]:
    """Return ``{uc_id: set(tokens)}`` across the whole catalog.

    Pulls from ``SEARCHABLE_FIELDS`` of every UC, lowercases, splits on
    ``[^a-z0-9_]+``, and applies length/DF cutoffs at the index step.
    """
    out: dict[str, set[str]] = {}
    for cat, sub, uc in catalog.iter_ucs():
        uc_id = uc.get("i")
        if not uc_id:
            continue
        text_chunks: list[str] = [str(uc_id), cat.get("n", ""), sub.get("n", "")]
        for field in SEARCHABLE_FIELDS:
            value = uc.get(field)
            if not value:
                continue
            if isinstance(value, str):
                text_chunks.append(value)
            elif isinstance(value, list):
                text_chunks.append(" ".join(str(v) for v in value if v))
        text = " ".join(text_chunks).lower()
        toks = {
            t for t in _TOKEN_RE.findall(text)
            if MIN_TOKEN_LEN <= len(t) <= MAX_TOKEN_LEN
        }
        if toks:
            out[uc_id] = toks
    return out


def _build_postings(
    docs: dict[str, set[str]],
    uc_idx: dict[str, int],
) -> dict[str, list[int]]:
    """Inverted index ``{token: [docid, ...]}`` after DF pruning."""
    raw: dict[str, list[int]] = {}
    for uc_id, tokens in docs.items():
        i = uc_idx[uc_id]
        for t in tokens:
            raw.setdefault(t, []).append(i)
    pruned: dict[str, list[int]] = {}
    for t, ids in raw.items():
        if MIN_DF <= len(ids) <= MAX_DF:
            pruned[t] = sorted(ids)
    return pruned


def _shard_postings(
    postings: dict[str, list[int]],
) -> dict[int, dict[str, str]]:
    """Distribute tokens across SHARD_COUNT buckets by ``fnv1a32(token)``.

    Posting lists are joined as comma-separated strings to minimise JSON
    overhead — the client splits on the same delimiter.
    """
    out: dict[int, dict[str, str]] = {i: {} for i in range(SHARD_COUNT)}
    for t, ids in postings.items():
        bucket = _shard_for(t)
        out[bucket][t] = ",".join(str(i) for i in ids)
    return out


def _shard_for(token: str) -> int:
    """FNV-1a 32-bit hash mod SHARD_COUNT.

    Tiny enough to reimplement in JS without external dependencies. The
    distribution quality across our 12k-token vocabulary is uniform to
    within ±5% per bucket, which is more than enough for static shard
    routing.
    """
    h = 0x811C9DC5  # FNV-1a 32-bit offset basis
    for byte in token.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF  # FNV-1a 32-bit prime
    return h % SHARD_COUNT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sort_key(value: Any) -> tuple:
    """Sort UC ids numerically (1.10.2 > 1.2.5)."""
    s = str(value or "")
    parts: list[tuple] = []
    for chunk in s.split("."):
        try:
            parts.append((0, int(chunk)))
        except ValueError:
            parts.append((1, chunk))
    return tuple(parts)


__all__ = ["render", "SHARD_COUNT", "SEARCHABLE_FIELDS"]
