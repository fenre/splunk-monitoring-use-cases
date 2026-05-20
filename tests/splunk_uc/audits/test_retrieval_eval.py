"""Unit tests for ``audit-retrieval-eval`` (P17 wave D).

The harness has five orthogonal contracts and each one is pinned
explicitly so a future refactor catches a regression:

1. **Tokeniser** \u2014 lowercase, alphanumeric-only, stopword + min-length
   filter; deterministic across calls.
2. **Query-set loader** \u2014 happy path + schema enforcement (missing
   id, missing text, empty expected_ucs, duplicate ids, malformed
   tags).
3. **BM25 scorer** \u2014 IDF / TF saturation / length normalisation
   shape (no zeros where there should be a signal, ties broken by
   ascending UC ID).
4. **Metrics** \u2014 ``recall@k``, MRR, ``nDCG@k`` mathematical
   correctness on hand-crafted ranked lists.
5. **CLI + baseline gate** \u2014 the dispatcher entry point emits both
   artefacts, the ``--check`` gate passes on a fresh baseline,
   regression detection triggers the right exit code, and a
   missing baseline produces exit code 2.

The corpus-loader test deliberately fakes a 4-chunk manifest (no
need to spin up the whole 136k-chunk dist/rag/ tree) so the tests
stay hermetic and run in milliseconds.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits.retrieval_eval import (
    DEFAULT_B,
    DEFAULT_K1,
    NDCG_K,
    RECALL_KS,
    SCHEMA_VERSION,
    AggregateMetrics,
    BM25Index,
    Chunk,
    DriftFinding,
    EvalRun,
    Query,
    QueryResult,
    _canonical_uc_id,
    _strip_frontmatter,
    compare_against_baseline,
    evaluate,
    load_corpus,
    load_queries,
    main,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
    render_json,
    render_markdown,
    tokenize,
)

# ----------------------------------------------------------------------
# Tokeniser
# ----------------------------------------------------------------------


def test_tokenize_lowercases_and_alphanumeric_only() -> None:
    """Punctuation drops; numeric tokens survive."""
    assert tokenize("Splunk HEC v9.2 — brute force!") == [
        "splunk",
        "hec",
        "v9",
        "brute",
        "force",
    ]


def test_tokenize_drops_stopwords_and_single_chars() -> None:
    """Common English stopwords and 1-char tokens vanish."""
    assert tokenize("This is a test of the alert system") == [
        "test",
        "alert",
        "system",
    ]


def test_tokenize_preserves_term_frequency_as_list() -> None:
    """The result is a list (multiset) so BM25 sees real TF."""
    out = tokenize("alert alert alert log")
    assert out == ["alert", "alert", "alert", "log"]
    assert out.count("alert") == 3


def test_tokenize_handles_empty_and_pure_punctuation() -> None:
    assert tokenize("") == []
    assert tokenize("   --- ---   ") == []


# ----------------------------------------------------------------------
# UC-ID normalisation
# ----------------------------------------------------------------------


def test_canonical_uc_id_strips_uc_prefix() -> None:
    assert _canonical_uc_id("UC-1.1.1") == "1.1.1"
    assert _canonical_uc_id("UC-22.49.5") == "22.49.5"


def test_canonical_uc_id_passes_through_canonical_form() -> None:
    assert _canonical_uc_id("1.1.1") == "1.1.1"


# ----------------------------------------------------------------------
# Frontmatter stripping
# ----------------------------------------------------------------------


def test_strip_frontmatter_removes_yaml_header() -> None:
    body = "---\nuc_id: UC-1.1.1\nchunk_index: 0\n---\nReal body here.\n"
    assert _strip_frontmatter(body) == "Real body here.\n"


def test_strip_frontmatter_passes_body_with_no_frontmatter() -> None:
    body = "Just body, no frontmatter.\n"
    assert _strip_frontmatter(body) == body


def test_strip_frontmatter_tolerates_unterminated_block() -> None:
    """If the frontmatter is malformed (no closing ``---``), don't crash."""
    body = "---\nbroken frontmatter never closes\nstill not closed\n"
    assert _strip_frontmatter(body) == body


# ----------------------------------------------------------------------
# Query-set loader
# ----------------------------------------------------------------------


def _write_query_set(tmp_path: Path, queries: list[dict[str, Any]]) -> Path:
    p = tmp_path / "queries.json"
    p.write_text(json.dumps({"queries": queries}), encoding="utf-8")
    return p


def test_load_queries_happy_path(tmp_path: Path) -> None:
    p = _write_query_set(
        tmp_path,
        [
            {
                "id": "Q001",
                "text": "monitor cpu",
                "expected_ucs": ["1.1.1"],
                "tags": ["infrastructure"],
            }
        ],
    )
    queries = load_queries(p)
    assert len(queries) == 1
    q = queries[0]
    assert q.id == "Q001"
    assert q.text == "monitor cpu"
    assert q.expected_ucs == frozenset({"1.1.1"})
    assert q.tags == ("infrastructure",)


def test_load_queries_strips_text_whitespace(tmp_path: Path) -> None:
    p = _write_query_set(
        tmp_path,
        [{"id": "Q1", "text": "  brute force  ", "expected_ucs": ["9.1.1"]}],
    )
    assert load_queries(p)[0].text == "brute force"


def test_load_queries_rejects_duplicate_ids(tmp_path: Path) -> None:
    p = _write_query_set(
        tmp_path,
        [
            {"id": "Q1", "text": "a", "expected_ucs": ["1.1.1"]},
            {"id": "Q1", "text": "b", "expected_ucs": ["1.1.2"]},
        ],
    )
    with pytest.raises(ValueError, match="duplicate query id"):
        load_queries(p)


def test_load_queries_rejects_missing_id(tmp_path: Path) -> None:
    p = _write_query_set(
        tmp_path, [{"text": "a", "expected_ucs": ["1.1.1"]}]
    )
    with pytest.raises(ValueError, match="missing string id"):
        load_queries(p)


def test_load_queries_rejects_empty_text(tmp_path: Path) -> None:
    p = _write_query_set(
        tmp_path, [{"id": "Q1", "text": "   ", "expected_ucs": ["1.1.1"]}]
    )
    with pytest.raises(ValueError, match="missing text"):
        load_queries(p)


def test_load_queries_rejects_empty_expected_ucs(tmp_path: Path) -> None:
    p = _write_query_set(tmp_path, [{"id": "Q1", "text": "a", "expected_ucs": []}])
    with pytest.raises(ValueError, match="non-empty expected_ucs"):
        load_queries(p)


def test_load_queries_rejects_malformed_tags(tmp_path: Path) -> None:
    p = _write_query_set(
        tmp_path,
        [
            {
                "id": "Q1",
                "text": "a",
                "expected_ucs": ["1.1.1"],
                "tags": [123, "ok"],
            }
        ],
    )
    with pytest.raises(ValueError, match="tags must be a list of strings"):
        load_queries(p)


def test_load_queries_rejects_non_list_queries_field(tmp_path: Path) -> None:
    p = tmp_path / "queries.json"
    p.write_text(json.dumps({"queries": "not a list"}), encoding="utf-8")
    with pytest.raises(ValueError, match="top-level 'queries' missing"):
        load_queries(p)


# ----------------------------------------------------------------------
# BM25 scorer
# ----------------------------------------------------------------------


def _make_corpus(*specs: tuple[str, str, str]) -> list[Chunk]:
    """Convenience: tuples ``(uc_id, chunk_id, body)`` \u2192 list[Chunk]."""
    return [
        Chunk(uc_id=u, chunk_id=cid, tokens=tuple(tokenize(body)))
        for u, cid, body in specs
    ]


def test_bm25_returns_no_score_for_chunks_without_query_terms() -> None:
    """A chunk that shares zero query terms is *not* in the result."""
    corpus = _make_corpus(
        ("1.1.1", "c1", "the quick brown fox jumps over the lazy dog"),
        ("1.1.2", "c2", "completely unrelated content about kittens"),
    )
    idx = BM25Index(corpus)
    scores = idx.score_chunks(tokenize("fox dog"))
    assert 0 in scores
    assert 1 not in scores


def test_bm25_ranks_more_relevant_chunk_higher() -> None:
    """A chunk with two matches outranks a chunk with one."""
    corpus = _make_corpus(
        ("1.1.1", "c1", "splunk hec brute force splunk hec brute force"),
        ("1.1.2", "c2", "splunk hec brute mentioned once here only"),
    )
    idx = BM25Index(corpus)
    scores = idx.score_chunks(tokenize("brute force"))
    assert 0 in scores and 1 in scores
    assert scores[0] > scores[1]


def test_bm25_idf_penalises_common_terms() -> None:
    """A term that appears in every chunk has near-zero IDF."""
    corpus = _make_corpus(
        ("1.1.1", "c1", "alert here alert"),
        ("1.1.2", "c2", "alert there alert"),
        ("1.1.3", "c3", "alert everywhere alert"),
    )
    idx = BM25Index(corpus)
    # ``alert`` is in every doc; ``here`` is in exactly one.
    common = idx.score_chunks(["alert"])
    rare = idx.score_chunks(["here"])
    # Rare-term score should beat common-term score for the same chunk.
    assert rare[0] > common[0]


def test_bm25_rank_ucs_aggregates_by_max_chunk_score() -> None:
    """Two chunks of one UC: the higher chunk score wins."""
    corpus = _make_corpus(
        ("1.1.1", "c1", "brute force brute force"),
        ("1.1.1", "c2", "irrelevant filler"),
        ("1.1.2", "c3", "brute force"),
    )
    idx = BM25Index(corpus)
    ranked = idx.rank_ucs(tokenize("brute force"))
    assert ranked[0][0] == "1.1.1"
    assert ranked[1][0] == "1.1.2"


def test_bm25_rank_ucs_breaks_ties_by_uc_id_ascending() -> None:
    """Determinism contract: equal scores \u2192 ascending UC ID."""
    corpus = _make_corpus(
        ("2.2.2", "a", "alpha beta gamma"),
        ("1.1.1", "b", "alpha beta gamma"),
        ("3.3.3", "c", "alpha beta gamma"),
    )
    idx = BM25Index(corpus)
    ranked = idx.rank_ucs(tokenize("alpha"))
    assert [u for u, _ in ranked] == ["1.1.1", "2.2.2", "3.3.3"]


def test_bm25_empty_corpus_returns_empty_ranking() -> None:
    idx = BM25Index([])
    assert idx.rank_ucs(["whatever"]) == []


def test_bm25_score_chunks_zero_query_terms_returns_empty() -> None:
    corpus = _make_corpus(("1.1.1", "c1", "anything"))
    idx = BM25Index(corpus)
    assert idx.score_chunks([]) == {}


# ----------------------------------------------------------------------
# Metrics
# ----------------------------------------------------------------------


def test_recall_at_k_full_hit() -> None:
    """All expected UCs in top-k \u2192 recall = 1.0."""
    assert recall_at_k(["1.1.1", "1.1.2"], frozenset({"1.1.1", "1.1.2"}), 5) == 1.0


def test_recall_at_k_partial_hit() -> None:
    """Half of expected in top-k \u2192 recall = 0.5."""
    assert (
        recall_at_k(
            ["1.1.1", "junk"], frozenset({"1.1.1", "1.1.2"}), 5
        )
        == 0.5
    )


def test_recall_at_k_zero_when_no_hits() -> None:
    assert recall_at_k(["junk1", "junk2"], frozenset({"1.1.1"}), 5) == 0.0


def test_recall_at_k_zero_with_empty_expected() -> None:
    assert recall_at_k(["whatever"], frozenset(), 5) == 0.0


def test_recall_at_k_respects_cutoff() -> None:
    """Expected UC at rank 6 is missed by recall@5."""
    ranked = ["a", "b", "c", "d", "e", "1.1.1"]
    assert recall_at_k(ranked, frozenset({"1.1.1"}), 5) == 0.0
    assert recall_at_k(ranked, frozenset({"1.1.1"}), 10) == 1.0


def test_reciprocal_rank_top_hit() -> None:
    assert reciprocal_rank(["1.1.1", "junk"], frozenset({"1.1.1"})) == 1.0


def test_reciprocal_rank_rank_3() -> None:
    assert reciprocal_rank(["a", "b", "1.1.1"], frozenset({"1.1.1"})) == 1 / 3


def test_reciprocal_rank_zero_when_no_match() -> None:
    assert reciprocal_rank(["a", "b"], frozenset({"1.1.1"})) == 0.0


def test_ndcg_at_k_perfect_ranking() -> None:
    """Perfect ranking \u2192 nDCG = 1.0."""
    ranked = ["1.1.1", "1.1.2", "junk"]
    expected = frozenset({"1.1.1", "1.1.2"})
    assert ndcg_at_k(ranked, expected, 10) == pytest.approx(1.0)


def test_ndcg_at_k_punishes_later_hits() -> None:
    """Same hits but at later ranks \u2192 lower nDCG."""
    early = ndcg_at_k(["1.1.1", "junk", "junk"], frozenset({"1.1.1"}), 10)
    late = ndcg_at_k(["junk", "junk", "1.1.1"], frozenset({"1.1.1"}), 10)
    assert early > late > 0
    assert early == 1.0  # rank 1 is the perfect placement


def test_ndcg_at_k_zero_with_no_match() -> None:
    assert ndcg_at_k(["a", "b"], frozenset({"1.1.1"}), 10) == 0.0


def test_ndcg_at_k_zero_with_empty_expected() -> None:
    assert ndcg_at_k(["a"], frozenset(), 10) == 0.0


def test_ndcg_at_k_clips_idcg_to_k() -> None:
    """More expected than k \u2192 IDCG capped at k perfect hits."""
    expected = frozenset({"a", "b", "c", "d", "e"})
    ranked = ["a", "b", "junk1", "junk2", "junk3"]
    # k=2: top-2 has all relevant docs at top \u2192 nDCG = 1
    assert ndcg_at_k(ranked, expected, 2) == pytest.approx(1.0)


# ----------------------------------------------------------------------
# evaluate() end-to-end on a tiny fake corpus
# ----------------------------------------------------------------------


def test_evaluate_produces_run_with_correct_shape() -> None:
    corpus = _make_corpus(
        ("1.1.1", "c1", "brute force login detection account lockout"),
        ("1.1.2", "c2", "irrelevant text about kittens and rainbows"),
        ("1.1.3", "c3", "cpu utilization on linux servers metric"),
    )
    queries = [
        Query(
            id="Q1",
            text="brute force login",
            expected_ucs=frozenset({"1.1.1"}),
            tags=(),
        ),
        Query(
            id="Q2",
            text="linux cpu utilization",
            expected_ucs=frozenset({"1.1.3"}),
            tags=(),
        ),
    ]
    run = evaluate(corpus, queries)
    assert run.schema_version == SCHEMA_VERSION
    assert run.bm25_k1 == DEFAULT_K1
    assert run.bm25_b == DEFAULT_B
    assert run.aggregate.query_count == 2
    assert run.aggregate.corpus_chunk_count == 3
    assert run.aggregate.corpus_uc_count == 3
    for k in RECALL_KS:
        assert run.aggregate.mean_recall_at_k[k] == 1.0
    assert run.aggregate.mean_mrr == 1.0
    assert run.aggregate.mean_ndcg_at_10 == 1.0


def test_evaluate_perfect_scores_on_distinguishing_queries() -> None:
    """Sanity: queries with distinct lexical signatures get perfect MRR."""
    corpus = _make_corpus(
        ("1.1.1", "c1", "alpha alpha alpha alpha alpha"),
        ("1.1.2", "c2", "beta beta beta beta beta"),
        ("1.1.3", "c3", "gamma gamma gamma gamma gamma"),
    )
    queries = [
        Query(id="Q1", text="alpha", expected_ucs=frozenset({"1.1.1"}), tags=()),
        Query(id="Q2", text="beta", expected_ucs=frozenset({"1.1.2"}), tags=()),
        Query(id="Q3", text="gamma", expected_ucs=frozenset({"1.1.3"}), tags=()),
    ]
    run = evaluate(corpus, queries)
    assert run.aggregate.mean_mrr == 1.0


# ----------------------------------------------------------------------
# Render functions
# ----------------------------------------------------------------------


def _build_tiny_run() -> EvalRun:
    """Helper: a fixed two-query EvalRun for render tests."""
    return EvalRun(
        schema_version="1.0",
        queries=(
            QueryResult(
                query_id="Q1",
                text="brute force",
                expected_ucs=("1.1.1",),
                top10_ucs=("1.1.1", "1.1.2"),
                recall_at_k={1: 1.0, 5: 1.0, 10: 1.0, 20: 1.0},
                mrr=1.0,
                ndcg_at_10=1.0,
            ),
            QueryResult(
                query_id="Q2",
                text="cpu | utilization",
                expected_ucs=("1.1.3",),
                top10_ucs=("1.1.5",),
                recall_at_k={1: 0.0, 5: 0.0, 10: 0.0, 20: 0.0},
                mrr=0.0,
                ndcg_at_10=0.0,
            ),
        ),
        aggregate=AggregateMetrics(
            mean_recall_at_k={1: 0.5, 5: 0.5, 10: 0.5, 20: 0.5},
            mean_mrr=0.5,
            mean_ndcg_at_10=0.5,
            query_count=2,
            corpus_chunk_count=10,
            corpus_uc_count=5,
        ),
        bm25_k1=DEFAULT_K1,
        bm25_b=DEFAULT_B,
    )


def test_render_json_is_canonical() -> None:
    """Output is sorted-keys + indent=2 + trailing newline."""
    run = _build_tiny_run()
    out = render_json(run)
    assert out.endswith("\n")
    assert "  " in out  # indented
    # Sorted-keys contract: the first top-level key should be ``$schema_version``
    # (starts with '$' which sorts before letters) followed by ``aggregate``.
    parsed = json.loads(out)
    keys = list(parsed.keys())
    assert keys == sorted(keys)


def test_render_json_round_trips() -> None:
    """Re-parsing the canonical JSON yields the same dict."""
    run = _build_tiny_run()
    again = json.loads(render_json(run))
    assert again["aggregate"]["query_count"] == 2
    assert again["queries"][0]["query_id"] == "Q1"


def test_render_markdown_includes_aggregate_and_per_query_rows() -> None:
    run = _build_tiny_run()
    md = render_markdown(run)
    assert "# RAG Retrieval Evaluation Report" in md
    assert "| recall@1 |" in md
    assert "| Q1 |" in md
    assert "| Q2 |" in md


def test_render_markdown_escapes_pipe_in_query_text() -> None:
    """A query containing a literal ``|`` must not break the table."""
    run = _build_tiny_run()
    md = render_markdown(run)
    # Q2's text "cpu | utilization" must be escaped as "cpu \| utilization".
    assert "cpu \\| utilization" in md


# ----------------------------------------------------------------------
# Baseline drift gate
# ----------------------------------------------------------------------


def _write_baseline(tmp_path: Path, **overrides: float) -> Path:
    """Write a minimal baseline file with given aggregate metrics."""
    agg = {
        "mean_recall_at_k": {"1": 0.3, "5": 0.6, "10": 0.8, "20": 0.9},
        "mean_mrr": 0.5,
        "mean_ndcg_at_10": 0.5,
        "query_count": 30,
        "corpus_chunk_count": 100,
        "corpus_uc_count": 50,
    }
    for k, v in overrides.items():
        if k.startswith("recall_"):
            cutoff = k.split("_")[1]
            agg["mean_recall_at_k"][cutoff] = v  # type: ignore[index]
        else:
            agg[k] = v
    p = tmp_path / "baseline.json"
    p.write_text(
        json.dumps({"$schema_version": "1.0", "aggregate": agg}),
        encoding="utf-8",
    )
    return p


def test_compare_against_baseline_passes_on_identical_run(tmp_path: Path) -> None:
    p = _write_baseline(tmp_path)
    run = EvalRun(
        schema_version="1.0",
        queries=(),
        aggregate=AggregateMetrics(
            mean_recall_at_k={1: 0.3, 5: 0.6, 10: 0.8, 20: 0.9},
            mean_mrr=0.5,
            mean_ndcg_at_10=0.5,
            query_count=30,
            corpus_chunk_count=100,
            corpus_uc_count=50,
        ),
        bm25_k1=DEFAULT_K1,
        bm25_b=DEFAULT_B,
    )
    assert compare_against_baseline(run, p, tolerance=0.0001) == []


def test_compare_against_baseline_passes_on_improvement(tmp_path: Path) -> None:
    """Higher current metrics are always accepted."""
    p = _write_baseline(tmp_path)
    run = EvalRun(
        schema_version="1.0",
        queries=(),
        aggregate=AggregateMetrics(
            mean_recall_at_k={1: 0.5, 5: 0.7, 10: 0.9, 20: 0.95},
            mean_mrr=0.7,
            mean_ndcg_at_10=0.7,
            query_count=30,
            corpus_chunk_count=100,
            corpus_uc_count=50,
        ),
        bm25_k1=DEFAULT_K1,
        bm25_b=DEFAULT_B,
    )
    assert compare_against_baseline(run, p, tolerance=0.0001) == []


def test_compare_against_baseline_flags_regression(tmp_path: Path) -> None:
    """A 10 % drop in MRR triggers a finding when tolerance is 2 %."""
    p = _write_baseline(tmp_path)
    run = EvalRun(
        schema_version="1.0",
        queries=(),
        aggregate=AggregateMetrics(
            mean_recall_at_k={1: 0.3, 5: 0.6, 10: 0.8, 20: 0.9},
            mean_mrr=0.45,  # 10% drop from 0.5
            mean_ndcg_at_10=0.5,
            query_count=30,
            corpus_chunk_count=100,
            corpus_uc_count=50,
        ),
        bm25_k1=DEFAULT_K1,
        bm25_b=DEFAULT_B,
    )
    findings = compare_against_baseline(run, p, tolerance=0.02)
    assert len(findings) == 1
    assert findings[0].metric == "mean_mrr"
    assert findings[0].delta < -0.02


def test_compare_against_baseline_absolute_floor_suppresses_tiny_regressions(
    tmp_path: Path,
) -> None:
    """A regression of 0.001 absolute is below the 0.01 floor \u2192 no finding."""
    p = _write_baseline(tmp_path, mean_mrr=0.5)
    run = EvalRun(
        schema_version="1.0",
        queries=(),
        aggregate=AggregateMetrics(
            mean_recall_at_k={1: 0.3, 5: 0.6, 10: 0.8, 20: 0.9},
            mean_mrr=0.499,  # 0.2 % relative drop, but tiny absolute
            mean_ndcg_at_10=0.5,
            query_count=30,
            corpus_chunk_count=100,
            corpus_uc_count=50,
        ),
        bm25_k1=DEFAULT_K1,
        bm25_b=DEFAULT_B,
    )
    assert compare_against_baseline(run, p, tolerance=0.0001) == []


def test_compare_against_baseline_raises_on_missing_baseline(tmp_path: Path) -> None:
    p = tmp_path / "missing.json"
    run = _build_tiny_run()
    with pytest.raises(FileNotFoundError):
        compare_against_baseline(run, p, tolerance=0.02)


# ----------------------------------------------------------------------
# CLI / main()
# ----------------------------------------------------------------------


def _build_hermetic_eval_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """Create a self-contained rag-dir + query-set for CLI smoke tests.

    Two chunks per UC across two UCs is enough to exercise the
    BM25 index without needing the real 136k-chunk dist/rag/.
    """
    rag_dir = tmp_path / "rag"
    chunks_dir = rag_dir / "chunks"
    chunks_dir.mkdir(parents=True)

    def _write_chunk(name: str, body: str) -> dict[str, Any]:
        path = chunks_dir / name
        path.write_text(
            f"---\nuc_id: {name.split('--')[0]}\n---\n{body}\n", encoding="utf-8"
        )
        return {
            "uc_id": name.split("--")[0],
            "chunk_index": int(name.split("--")[1].split(".")[0]),
            "path": f"chunks/{name}",
            "char_count": len(body),
        }

    manifest = {
        "$schema_version": "1.1",
        "chunks": [
            _write_chunk(
                "UC-1.1.1--00.md",
                "monitor cpu utilization linux server load average",
            ),
            _write_chunk(
                "UC-1.1.1--01.md",
                "additional content about cpu and metrics on linux",
            ),
            _write_chunk(
                "UC-2.2.2--00.md",
                "completely different topic about kittens and rainbows",
            ),
        ],
    }
    (rag_dir / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    queries_path = tmp_path / "queries.json"
    queries_path.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "id": "Q1",
                        "text": "monitor cpu linux",
                        "expected_ucs": ["1.1.1"],
                        "tags": ["test"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return rag_dir, queries_path


def test_main_default_mode_writes_outputs(tmp_path: Path) -> None:
    rag_dir, queries_path = _build_hermetic_eval_workspace(tmp_path)
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    rc = main(
        [
            "--rag-dir", str(rag_dir),
            "--queries", str(queries_path),
            "--out-json", str(out_json),
            "--out-md", str(out_md),
            "--quiet",
        ]
    )
    assert rc == 0
    assert out_json.exists()
    assert out_md.exists()
    parsed = json.loads(out_json.read_text())
    assert parsed["aggregate"]["query_count"] == 1
    assert parsed["aggregate"]["corpus_chunk_count"] == 3
    assert parsed["aggregate"]["mean_recall_at_k"]["1"] == 1.0  # perfect


def test_main_check_passes_on_fresh_baseline(tmp_path: Path) -> None:
    rag_dir, queries_path = _build_hermetic_eval_workspace(tmp_path)
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    baseline = tmp_path / "baseline.json"
    # Write baseline, then check.
    rc = main(
        [
            "--rag-dir", str(rag_dir),
            "--queries", str(queries_path),
            "--out-json", str(out_json),
            "--out-md", str(out_md),
            "--baseline", str(baseline),
            "--write-baseline",
            "--quiet",
        ]
    )
    assert rc == 0
    rc = main(
        [
            "--rag-dir", str(rag_dir),
            "--queries", str(queries_path),
            "--out-json", str(out_json),
            "--out-md", str(out_md),
            "--baseline", str(baseline),
            "--check",
            "--quiet",
        ]
    )
    assert rc == 0


def test_main_check_exits_2_when_baseline_missing(tmp_path: Path) -> None:
    rag_dir, queries_path = _build_hermetic_eval_workspace(tmp_path)
    rc = main(
        [
            "--rag-dir", str(rag_dir),
            "--queries", str(queries_path),
            "--out-json", str(tmp_path / "out.json"),
            "--out-md", str(tmp_path / "out.md"),
            "--baseline", str(tmp_path / "absent.json"),
            "--check",
            "--quiet",
        ]
    )
    assert rc == 2


def test_main_exits_2_when_rag_dir_missing(tmp_path: Path) -> None:
    """No corpus \u2192 exit 2 (operator error, not a metric regression)."""
    queries = tmp_path / "queries.json"
    queries.write_text(
        json.dumps(
            {"queries": [{"id": "Q1", "text": "x", "expected_ucs": ["1.1.1"]}]}
        ),
        encoding="utf-8",
    )
    rc = main(
        [
            "--rag-dir", str(tmp_path / "nope"),
            "--queries", str(queries),
            "--out-json", str(tmp_path / "out.json"),
            "--out-md", str(tmp_path / "out.md"),
            "--quiet",
        ]
    )
    assert rc == 2


def test_main_exits_2_when_query_set_malformed(tmp_path: Path) -> None:
    rag_dir, _ = _build_hermetic_eval_workspace(tmp_path)
    bad_queries = tmp_path / "bad.json"
    bad_queries.write_text(json.dumps({"queries": "not a list"}), encoding="utf-8")
    rc = main(
        [
            "--rag-dir", str(rag_dir),
            "--queries", str(bad_queries),
            "--out-json", str(tmp_path / "out.json"),
            "--out-md", str(tmp_path / "out.md"),
            "--quiet",
        ]
    )
    assert rc == 2


# ----------------------------------------------------------------------
# Integration smoke: live corpus loader sanity
# ----------------------------------------------------------------------


def test_load_corpus_handles_missing_rag_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_corpus(tmp_path / "missing")
