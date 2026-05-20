"""Hermetic tests for ``tools/build/render_search.py``.

Covers tokenisation, DF pruning, FNV-1a sharding, and the end-to-end
``render()`` orchestration that emits ``search-vocab.json`` plus 16
content-hashed shard files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from build import render_search
from build.parse_content import Catalog


def _empty_catalog(tmp_path: Path, **overrides) -> Catalog:
    kwargs = dict(
        project_root=tmp_path,
        categories=[],
        cat_meta={},
        cat_groups={},
        equipment=[],
        regulations={},
        recently_added=[],
        facets={},
    )
    kwargs.update(overrides)
    return Catalog(**kwargs)


def _catalog_with_uc(
    tmp_path: Path, uc_id: str = "1.1.1", **uc_fields
) -> Catalog:
    """Catalog with a single UC carrying ``uc_fields``."""
    uc = {"i": uc_id, **uc_fields}
    return _empty_catalog(
        tmp_path,
        categories=[
            {
                "i": 1,
                "n": "Network",
                "s": [{"i": "1.1", "n": "Routing", "u": [uc]}],
            }
        ],
    )


# ---------------------------------------------------------------------------
# _sort_key — UC-id ordering
# ---------------------------------------------------------------------------


class TestSortKey:
    def test_numeric_chunks_sort_numerically_not_lexically(self):
        """``1.10.2`` MUST sort AFTER ``1.2.5`` because the chunks are
        compared as integers, not strings (covers lines 277, 280)."""
        a = render_search._sort_key("1.2.5")
        b = render_search._sort_key("1.10.2")
        assert a < b
        assert a == ((0, 1), (0, 2), (0, 5))
        assert b == ((0, 1), (0, 10), (0, 2))

    def test_alpha_chunks_fall_through_to_string_tagged_branch(self):
        """Non-integer chunks (e.g. ``"1.1.alpha"``) take the
        ``except ValueError`` path (line 278-279) and tag with
        ``(1, str)``."""
        assert render_search._sort_key("1.1.alpha") == (
            (0, 1),
            (0, 1),
            (1, "alpha"),
        )
        # Numeric chunks sort before alpha chunks at the same position
        # because (0, ...) < (1, ...).
        assert render_search._sort_key("1.1.1") < render_search._sort_key("1.1.alpha")

    def test_none_treated_as_empty_string(self):
        """``_sort_key(None)`` should coerce to an empty-string key
        rather than raise. Covers ``str(value or "")`` on line 273."""
        # Empty string → single empty chunk → ``(1, "")``.
        assert render_search._sort_key(None) == ((1, ""),)


# ---------------------------------------------------------------------------
# _shard_for — FNV-1a 32-bit hash
# ---------------------------------------------------------------------------


class TestShardFor:
    def test_shard_for_returns_value_in_bucket_range(self):
        """All returned values MUST be in ``[0, SHARD_COUNT)`` (covers
        the ``h % SHARD_COUNT`` on line 264)."""
        for token in ("splunk", "alpha", "zzz", "x", "12345"):
            bucket = render_search._shard_for(token)
            assert 0 <= bucket < render_search.SHARD_COUNT

    def test_shard_for_is_deterministic_for_same_token(self):
        assert render_search._shard_for("splunk") == render_search._shard_for("splunk")

    def test_shard_for_is_stable_across_runs_for_known_string(self):
        """FNV-1a 32-bit of 'splunk' is locked: 0xb5083b2c — confirms
        the offset basis 0x811C9DC5 and prime 0x01000193 are correct
        (any drift here would invalidate every cached shard at every
        SPA client)."""
        # Reference implementation (locked):
        ref = 0x811C9DC5
        for byte in b"splunk":
            ref ^= byte
            ref = (ref * 0x01000193) & 0xFFFFFFFF
        assert render_search._shard_for("splunk") == ref % render_search.SHARD_COUNT

    def test_shard_for_distributes_tokens_across_buckets(self):
        """A small sample of distinct tokens MUST hit at least 2
        buckets — guards against accidental hash collapse."""
        tokens = [f"token{i:04d}" for i in range(64)]
        buckets = {render_search._shard_for(t) for t in tokens}
        assert len(buckets) >= 2


# ---------------------------------------------------------------------------
# _collect_docs — tokenisation + length-cutoff
# ---------------------------------------------------------------------------


class TestCollectDocs:
    def test_uc_without_id_is_skipped(self, tmp_path: Path):
        """Covers the ``if not uc_id: continue`` guard on line 199."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "Network",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "Routing",
                            "u": [
                                {"n": "headless"},  # no `i` → skipped
                                {"i": "1.1.1", "n": "real ospf neighbour"},
                            ],
                        }
                    ],
                }
            ],
        )
        docs = render_search._collect_docs(cat)
        assert list(docs.keys()) == ["1.1.1"]
        # "real", "ospf", "neighbour" all in {3..30} chars range
        assert {"real", "ospf", "neighbour", "routing", "network"}.issubset(docs["1.1.1"])

    def test_empty_field_values_skip_chunk(self, tmp_path: Path):
        """A UC with an empty string / empty list / None value must
        NOT contribute to text_chunks. Covers the false arm of
        ``if not value: continue`` (line 204)."""
        cat = _catalog_with_uc(
            tmp_path,
            n="alpha",
            v="",          # empty — skipped
            d=None,        # None — skipped
            t=[],          # empty list — skipped
        )
        docs = render_search._collect_docs(cat)
        assert "alpha" in docs["1.1.1"]
        # No leakage of placeholder noise
        assert not any(t.startswith("none") for t in docs["1.1.1"])

    def test_list_field_values_are_space_joined(self, tmp_path: Path):
        """List values become a space-separated string before
        tokenisation. Covers lines 208-209."""
        cat = _catalog_with_uc(
            tmp_path,
            mtype=["realtime", "scheduled"],
            regs=["NIST", "SOC2"],
            e=["palo", "cisco", None, ""],  # falsy entries filtered out
        )
        docs = render_search._collect_docs(cat)["1.1.1"]
        assert {"realtime", "scheduled", "nist", "soc2", "palo", "cisco"}.issubset(docs)

    def test_tokens_outside_length_window_are_dropped(self, tmp_path: Path):
        """Tokens shorter than MIN_TOKEN_LEN (3) or longer than
        MAX_TOKEN_LEN (30) MUST be discarded (covers line 213)."""
        long_word = "x" * 35  # > MAX_TOKEN_LEN
        cat = _catalog_with_uc(
            tmp_path,
            n=f"ab in {long_word} the qz",  # 'ab' < 3, long_word > 30, 'qz' < 3, 'the' = 3 → kept
        )
        docs = render_search._collect_docs(cat)["1.1.1"]
        assert "the" in docs  # length 3 boundary
        assert "in" not in docs  # length 2 → dropped
        assert "ab" not in docs  # length 2 → dropped
        assert "qz" not in docs  # length 2 → dropped
        assert long_word not in docs  # length 35 → dropped

    def test_non_string_non_list_field_value_is_skipped(self, tmp_path: Path):
        """If a SEARCHABLE_FIELD carries a value that is neither a
        string nor a list (e.g. an int or dict), the tokeniser must
        silently drop it. Covers the elif-falsethrough branch 208→202
        in render_search.py."""
        cat = _catalog_with_uc(
            tmp_path,
            n="alpha bravo",
            v=42,                # int — neither str nor list → fall through
            t={"nested": "dict"},  # dict — neither str nor list → fall through
        )
        docs = render_search._collect_docs(cat)["1.1.1"]
        # The token tree contains tokens from `n` and nothing from v/t.
        assert {"alpha", "bravo"}.issubset(docs)
        # The string "42" never makes it in; nor does "nested" from the dict.
        assert "nested" not in docs
        # And the str(42) literal is also absent.
        assert "42" not in docs

    def test_uc_with_no_resulting_tokens_is_excluded(self, tmp_path: Path):
        """A UC whose every text chunk is empty after tokenisation
        must NOT appear in the index at all (covers the false arm of
        ``if toks: out[uc_id] = toks`` on line 215). To trigger this
        the UC id, cat name, and sub name all need to be empty AND
        every searchable field needs to be missing — which here means
        directly invoking ``_collect_docs`` with an artificial empty
        cat tree."""
        cat = Catalog(
            project_root=tmp_path,
            categories=[
                {
                    "i": "",      # empty cat id (won't tokenise)
                    "n": "",      # empty cat name
                    "s": [
                        {
                            "i": "",
                            "n": "",
                            "u": [
                                # uc_id is "ab" — length 2, gets dropped at
                                # token filter; UC has no other text-bearing
                                # fields → toks is empty → UC excluded.
                                {"i": "ab"},
                            ],
                        }
                    ],
                }
            ],
        )
        docs = render_search._collect_docs(cat)
        assert "ab" not in docs


# ---------------------------------------------------------------------------
# _build_postings — DF pruning
# ---------------------------------------------------------------------------


class TestBuildPostings:
    def test_token_below_min_df_is_pruned(self):
        """A token appearing in fewer than MIN_DF (2) UCs is dropped
        (covers the false arm of the MIN_DF guard on line 232)."""
        docs = {
            "1.1.1": {"shared", "unique"},   # 'unique' appears only here
            "1.1.2": {"shared"},
        }
        uc_idx = {"1.1.1": 0, "1.1.2": 1}
        out = render_search._build_postings(docs, uc_idx)
        assert "shared" in out
        assert "unique" not in out

    def test_token_above_max_df_is_pruned(self, monkeypatch: pytest.MonkeyPatch):
        """A token whose DF exceeds MAX_DF is dropped. Use a tiny
        MAX_DF stand-in to avoid generating 4000+ documents."""
        monkeypatch.setattr(render_search, "MAX_DF", 2)
        docs = {
            "1.1.1": {"too_common", "rare"},
            "1.1.2": {"too_common", "rare"},
            "1.1.3": {"too_common"},  # bumps DF to 3 → > MAX_DF
        }
        uc_idx = {"1.1.1": 0, "1.1.2": 1, "1.1.3": 2}
        out = render_search._build_postings(docs, uc_idx)
        assert "too_common" not in out
        assert out["rare"] == [0, 1]  # postings sorted

    def test_postings_are_sorted_by_docid(self):
        docs = {"u3": {"foo"}, "u1": {"foo"}, "u2": {"foo"}}
        uc_idx = {"u1": 0, "u2": 1, "u3": 2}  # arbitrary
        out = render_search._build_postings(docs, uc_idx)
        assert out["foo"] == [0, 1, 2]


# ---------------------------------------------------------------------------
# _shard_postings — bucket distribution
# ---------------------------------------------------------------------------


class TestShardPostings:
    def test_each_token_lands_in_its_own_fnv_bucket(self):
        postings = {
            "alpha": [0, 1, 2],
            "beta": [1, 3],
        }
        shards = render_search._shard_postings(postings)
        assert set(shards.keys()) == set(range(render_search.SHARD_COUNT))
        alpha_bucket = render_search._shard_for("alpha")
        beta_bucket = render_search._shard_for("beta")
        assert shards[alpha_bucket]["alpha"] == "0,1,2"
        assert shards[beta_bucket]["beta"] == "1,3"


# ---------------------------------------------------------------------------
# render() — end-to-end orchestration
# ---------------------------------------------------------------------------


class TestRender:
    def test_empty_catalog_short_circuits(self, tmp_path: Path):
        """No documents → no vocab + no shards. Covers lines 130-131."""
        cat = _empty_catalog(tmp_path)
        out_dir = tmp_path / "dist"
        render_search.render(cat, out_dir, reproducible=True)
        assets = out_dir / "assets"
        assert assets.is_dir()  # always created (line 127)
        assert not (assets / "search-vocab.json").exists()
        assert "search_vocab" not in cat.asset_hashes

    def test_render_emits_vocab_and_16_shards(self, tmp_path: Path):
        """Smoke-test that a non-empty catalog produces a valid vocab
        file + exactly SHARD_COUNT (16) shard files, all referenced
        from ``vocab.shardFiles`` and with content-hashed filenames."""
        # Build many UCs so token DFs land in [MIN_DF, MAX_DF).
        ucs = []
        for i in range(1, 8):
            ucs.append(
                {
                    "i": f"1.1.{i}",
                    "n": f"alpha bravo {i}",   # 'alpha'/'bravo' shared → DF 7
                    "v": "splunk routing",     # 'splunk'/'routing' shared
                    "regs": ["NIST"],
                }
            )
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {"i": 1, "n": "Network", "s": [{"i": "1.1", "n": "Routing", "u": ucs}]},
            ],
        )

        out_dir = tmp_path / "dist"
        render_search.render(cat, out_dir, reproducible=True)
        assets = out_dir / "assets"
        vocab = json.loads((assets / "search-vocab.json").read_text(encoding="utf-8"))

        assert vocab["$schema"] == "/schemas/v2/search-index.schema.json"
        assert vocab["version"] == 2
        assert vocab["shardCount"] == render_search.SHARD_COUNT
        assert vocab["hash"] == "fnv1a32"
        assert len(vocab["shardFiles"]) == render_search.SHARD_COUNT
        # Every shard file is on disk and lookups by name resolve.
        for sf in vocab["shardFiles"]:
            assert (assets / sf).exists()
            # Filename = search-shard-NN.<10char>.json
            assert sf.startswith("search-shard-")
            assert sf.endswith(".json")
            # Hash segment is exactly 10 chars
            short = sf.rsplit(".", 2)[-2]
            assert len(short) == 10
        # ucIds is sorted numerically (1.1.1 .. 1.1.7).
        assert vocab["ucIds"] == [f"1.1.{i}" for i in range(1, 8)]
        # Catalog asset hashes are stamped.
        assert cat.asset_hashes["search_vocab"] == "search-vocab.json"
        assert cat.asset_hashes["search_index_docs"] == "7"
        assert int(cat.asset_hashes["search_index_tokens"]) > 0

    def test_shard_filename_hash_is_deterministic_in_reproducible_mode(
        self, tmp_path: Path
    ):
        """Two consecutive reproducible builds MUST emit identical
        shard filenames — otherwise the byte-identical guarantee in
        ``audit-reproducibility`` would fail."""
        cat = _catalog_with_uc(
            tmp_path,
            n="alpha bravo charlie",
            v="splunk routing data",
        )
        # Need at least 2 UCs for DF cutoff — add a second.
        cat.categories[0]["s"][0]["u"].append(
            {"i": "1.1.2", "n": "alpha bravo charlie", "v": "splunk routing data"}
        )

        out1 = tmp_path / "dist1"
        out2 = tmp_path / "dist2"
        render_search.render(cat, out1, reproducible=True)
        # Reset asset_hashes so second run mirrors the first
        cat.asset_hashes.clear()
        render_search.render(cat, out2, reproducible=True)

        v1 = json.loads((out1 / "assets" / "search-vocab.json").read_text(encoding="utf-8"))
        v2 = json.loads((out2 / "assets" / "search-vocab.json").read_text(encoding="utf-8"))
        assert v1["shardFiles"] == v2["shardFiles"]

    def test_shard_payload_has_expected_structure(self, tmp_path: Path):
        """Each shard file is a JSON object with ``version``,
        ``shard``, and ``postings``. ``postings`` is
        ``{token: "comma,joined,docids"}``."""
        cat = _catalog_with_uc(
            tmp_path,
            n="alpha bravo",
            v="splunk routing",
        )
        cat.categories[0]["s"][0]["u"].append(
            {"i": "1.1.2", "n": "alpha bravo", "v": "splunk routing"}
        )

        out_dir = tmp_path / "dist"
        render_search.render(cat, out_dir, reproducible=True)
        vocab = json.loads(
            (out_dir / "assets" / "search-vocab.json").read_text(encoding="utf-8")
        )
        # Find any shard that has at least one token and inspect it.
        non_empty_shards = []
        for sf in vocab["shardFiles"]:
            payload = json.loads(
                (out_dir / "assets" / sf).read_text(encoding="utf-8")
            )
            assert payload["version"] == 2
            assert 0 <= payload["shard"] < render_search.SHARD_COUNT
            assert isinstance(payload["postings"], dict)
            for token, posting in payload["postings"].items():
                # Token routes to the shard's own bucket.
                assert render_search._shard_for(token) == payload["shard"]
                # Posting is a comma-joined list of integer docids.
                assert all(p.isdigit() for p in posting.split(","))
            if payload["postings"]:
                non_empty_shards.append(payload["shard"])
        assert non_empty_shards, "expected at least one shard to carry tokens"
