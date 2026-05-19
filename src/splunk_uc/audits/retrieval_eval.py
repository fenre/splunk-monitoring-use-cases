#!/usr/bin/env python3
"""Retrieval-eval harness for the RAG chunked corpus (P17 wave D).

This audit closes the last unmet deliverable of phase **P17 — AI
readiness + LLM eval**: a hand-curated query set, a BM25 retrieval
baseline over the chunked corpus produced by
``generate-rag-chunks``, and a recall/MRR/nDCG metric rollup that
gates regressions in CI.

The harness is deliberately stdlib-only \u2014 no external embedding
model, no sentence-transformers, no PyTorch \u2014 because:

1. The BM25 baseline is the **floor** every embedding-based system
   must beat. Tracking it as the contracted minimum means future
   embedding upgrades are measured against a well-understood,
   reproducible point of comparison.
2. CI runners can run the eval in ~30s with no GPU and no network
   access, so the gate is always available on every PR.
3. Byte-deterministic outputs let us snapshot the baseline as a
   committed JSON artefact under
   :file:`data/baselines/retrieval-eval-v1.0.json` and drift-guard
   the per-query metrics line-by-line.

Architecture
------------

* **Tokeniser** \u2014 lowercase, split on non-alphanumeric, drop common
  English stopwords and single-char tokens. Operating on lowercase
  alphanumerics-only keeps SPL-significant chars like ``|`` and ``=``
  out of the term-space (they would only add noise) and avoids
  accent / Unicode normalisation surprises.
* **BM25 scorer** \u2014 Okapi BM25 with the standard ``k1=1.5, b=0.75``
  parameters. The inverted index is built once from
  :file:`dist/rag/chunks/UC-*.md` (skipping the YAML frontmatter
  block) and reused across all queries.
* **UC ranking** \u2014 BM25 produces per-chunk scores; we aggregate to
  UC level by taking the **max** chunk score per UC. This matches
  what a downstream retrieval system would do when its top-k chunks
  are surfaced as "this UC matches your query".
* **Metrics** \u2014 ``recall@{1,5,10,20}``, MRR (Mean Reciprocal
  Rank), and ``nDCG@10`` (Normalised Discounted Cumulative Gain at
  cutoff 10), all computed per query and then averaged.

Outputs (relative to repo root, re-emitted on every run):

* ``dist/rag/retrieval-eval.json`` \u2014 machine-readable per-query
  scores + aggregate rollup. Schema version pinned at 1.0.
* ``dist/rag/retrieval-eval.md``  \u2014 human-readable summary
  (aggregate table + per-query table).

Drift-guard contract (``--check`` mode):

* Compares every aggregate metric in
  ``data/baselines/retrieval-eval-v1.0.json`` against the freshly
  computed numbers.
* Fails CI if any metric regresses by more than ``--tolerance``
  (default 0.02, i.e. 2%); improvements are always allowed.
* Per-query regressions are surfaced in the diagnostic output but
  do not by themselves fail the gate (queries can shift slightly
  between corpus regenerations even when aggregates are stable;
  the aggregate gate is the contract).

Usage::

    python -m splunk_uc audit-retrieval-eval                # write outputs
    python -m splunk_uc audit-retrieval-eval --check        # CI drift gate
    python -m splunk_uc audit-retrieval-eval --write-baseline
                                                           # manual baseline bump
    python -m splunk_uc audit-retrieval-eval --tolerance 0.01
                                                           # tighter gate

Exit codes:

* 0 \u2014 success (outputs written, or ``--check`` passed).
* 1 \u2014 ``--check`` mode and at least one aggregate metric regressed
  more than ``--tolerance``.
* 2 \u2014 unexpected error (missing corpus, missing query set,
  malformed inputs).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Repo root resolution mirrors the convention used by the other
# audits in this package: walk up from this file until we hit a
# directory that contains the canonical SSOT layout (``content/``,
# ``data/``, ``dist/``). Refusing to guess silently avoids the
# bug where an audit run from a worktree picks up the wrong dist/.
_PKG_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent.parent.parent
DEFAULT_RAG_DIR = _REPO_ROOT / "dist" / "rag"
DEFAULT_QUERIES_PATH = _REPO_ROOT / "data" / "rag" / "retrieval-eval-queries.json"
DEFAULT_BASELINE_PATH = _REPO_ROOT / "data" / "baselines" / "retrieval-eval-v1.0.json"
DEFAULT_OUTPUT_JSON = DEFAULT_RAG_DIR / "retrieval-eval.json"
DEFAULT_OUTPUT_MD = DEFAULT_RAG_DIR / "retrieval-eval.md"

# Schema versions are bumped explicitly when the shape changes; the
# committed baseline file pins the version it was authored against
# so a future schema bump fails the --check gate loudly.
SCHEMA_VERSION = "1.0"

# Standard Okapi BM25 parameters. ``k1`` controls term-frequency
# saturation; ``b`` controls length normalisation. The values are
# the conventional defaults and the harness exposes them on the CLI
# so future tuning is a single-flag change.
DEFAULT_K1 = 1.5
DEFAULT_B = 0.75

# Default tolerance for the --check gate. A 2 % margin accommodates
# minor floating-point drift across Python releases without making
# the gate noisy. The number is exposed on the CLI for tighter
# gating once the harness has soaked.
DEFAULT_TOLERANCE = 0.02

# Cutoffs at which recall is computed. The set is fixed in the
# schema so downstream consumers (dashboards, stewardship digest)
# can rely on the keys being present.
RECALL_KS = (1, 5, 10, 20)

# nDCG is computed at a single cutoff; 10 is the conventional
# "first results page" value and matches what a hypothetical UI
# would show before pagination.
NDCG_K = 10

# A compact English stopword list. We do not use NLTK here because
# the only requirement is removing tokens that appear in virtually
# every document and so contribute no IDF signal. The list is
# derived from the canonical Lucene/Solr defaults but trimmed of
# domain-significant tokens like ``error`` and ``log`` that show
# up in real SPL/IT prose.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "by",
        "for", "from", "has", "have", "he", "her", "him", "his",
        "i", "if", "in", "into", "is", "it", "its", "of", "on",
        "or", "she", "so", "such", "that", "the", "their", "them",
        "then", "there", "these", "they", "this", "those", "to",
        "was", "we", "were", "what", "when", "where", "which",
        "who", "will", "with", "you", "your",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Tokenise *text* into BM25-suitable terms.

    The contract is intentionally simple and matches what a
    keyword-based retrieval system would do:

    1. Lowercase the input.
    2. Extract maximal alphanumeric runs (drops punctuation and
       SPL operators, which would only add noise to a bag-of-words
       index).
    3. Drop tokens shorter than 2 chars and tokens in the
       :data:`_STOPWORDS` set.

    The result is a list (not a set) because BM25 cares about
    term frequencies, and a list preserves the natural multiset
    of terms in a document or query.
    """
    return [
        t
        for t in _TOKEN_RE.findall(text.lower())
        if len(t) > 1 and t not in _STOPWORDS
    ]


@dataclass(frozen=True)
class Query:
    """One curated query from
    :file:`data/rag/retrieval-eval-queries.json`.

    A query is judged against the set of ``expected_ucs`` \u2014 the UC
    IDs that an ideal retriever should surface in the top-k. The
    ``tags`` field is informational only (used for filtering and
    cohort-level reporting) and never affects scoring.
    """

    id: str
    text: str
    expected_ucs: frozenset[str]
    tags: tuple[str, ...]


def load_queries(path: Path) -> list[Query]:
    """Parse the curated query set into :class:`Query` records.

    The query-set JSON is contract-stable: every entry must carry
    ``id``, ``text``, and ``expected_ucs`` (at least one UC ID).
    ``tags`` is optional and defaults to an empty tuple.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    queries = raw.get("queries")
    if not isinstance(queries, list):
        raise ValueError(
            f"{path}: top-level 'queries' missing or not a list"
        )
    out: list[Query] = []
    seen_ids: set[str] = set()
    for entry in queries:
        if not isinstance(entry, Mapping):
            raise ValueError(
                f"{path}: each query must be a JSON object"
            )
        qid = entry.get("id")
        text = entry.get("text")
        expected = entry.get("expected_ucs")
        if not isinstance(qid, str) or not qid:
            raise ValueError(f"{path}: query missing string id: {entry!r}")
        if qid in seen_ids:
            raise ValueError(f"{path}: duplicate query id {qid!r}")
        seen_ids.add(qid)
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{path}: query {qid} missing text")
        if not isinstance(expected, list) or not expected:
            raise ValueError(
                f"{path}: query {qid} missing non-empty expected_ucs"
            )
        if not all(isinstance(u, str) and u for u in expected):
            raise ValueError(
                f"{path}: query {qid} expected_ucs must be UC-ID strings"
            )
        tags = entry.get("tags") or []
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise ValueError(
                f"{path}: query {qid} tags must be a list of strings"
            )
        out.append(
            Query(
                id=qid,
                text=text.strip(),
                expected_ucs=frozenset(expected),
                tags=tuple(tags),
            )
        )
    return out


@dataclass(frozen=True)
class Chunk:
    """One indexed chunk: ``uc_id`` + ``chunk_id`` + tokenised body."""

    uc_id: str
    chunk_id: str
    tokens: tuple[str, ...]


def _strip_frontmatter(body: str) -> str:
    """Strip the leading ``---\\n...\\n---\\n`` YAML frontmatter, if any.

    The chunk emitter wraps every chunk in YAML frontmatter so
    consumers can read uc-id / section-title / fingerprints without
    parsing the body. For BM25 indexing we want the prose itself, so
    we strip the block when present.
    """
    if not body.startswith("---\n"):
        return body
    end = body.find("\n---\n", 4)
    if end == -1:
        return body
    return body[end + 5 :]


def _canonical_uc_id(uc_id: str) -> str:
    """Strip the display-only ``UC-`` prefix.

    The chunk manifest emits ``uc_id`` in the display form
    (``UC-1.1.1``) so each chunk file's frontmatter is
    self-describing, but the catalogue's authoritative ID schema is
    ``X.Y.Z`` (no prefix \u2014 see ``schemas/uc.schema.json``). The
    query set uses the canonical form so it stays portable across
    consumers that emit either shape; this helper normalises the
    two sides into one comparable namespace.
    """
    return uc_id[3:] if uc_id.startswith("UC-") else uc_id


def load_corpus(rag_dir: Path) -> list[Chunk]:
    """Load every chunk under *rag_dir* into a list of :class:`Chunk`.

    The walk is driven by the manifest (not a filesystem glob) so
    the index always reflects exactly what
    :func:`generate-rag-chunks` produced. Skipping the YAML
    frontmatter keeps front-matter terms (``uc_id: '1.1.1'`` etc.)
    out of the term space \u2014 they would otherwise be in every chunk
    of one UC and dominate the IDF distribution.
    """
    manifest_path = rag_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"{manifest_path} not found \u2014 run "
            "`python -m splunk_uc generate-rag-chunks` first."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out: list[Chunk] = []
    for entry in manifest["chunks"]:
        body = (rag_dir / entry["path"]).read_text(encoding="utf-8")
        body = _strip_frontmatter(body)
        out.append(
            Chunk(
                uc_id=_canonical_uc_id(entry["uc_id"]),
                chunk_id=entry["path"],
                tokens=tuple(tokenize(body)),
            )
        )
    return out


class BM25Index:
    """Inverted-index BM25 scorer over a corpus of chunks.

    The index is built once at construction time. For 136k chunks
    of ~900 chars each, the build takes ~10s on a developer laptop
    and the per-query scoring is dominated by sweeping the posting
    lists of the query's terms (well under a second per query).
    """

    def __init__(
        self,
        corpus: Sequence[Chunk],
        k1: float = DEFAULT_K1,
        b: float = DEFAULT_B,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.N = len(corpus)
        # Posting list: term \u2192 chunk_index \u2192 term-frequency.
        # Using chunk_index (not chunk_id) keeps the inner-loop
        # dict keys integer for cache friendliness.
        self._postings: dict[str, dict[int, int]] = {}
        self._doc_lens: list[int] = []
        self._chunk_ids: list[str] = []
        self._uc_ids: list[str] = []
        total_len = 0
        for i, chunk in enumerate(corpus):
            tf_local = Counter(chunk.tokens)
            dl = len(chunk.tokens)
            self._doc_lens.append(dl)
            self._chunk_ids.append(chunk.chunk_id)
            self._uc_ids.append(chunk.uc_id)
            total_len += dl
            for term, freq in tf_local.items():
                self._postings.setdefault(term, {})[i] = freq
        self._avgdl = total_len / self.N if self.N else 1.0
        # df: number of documents that contain the term. Cached
        # because we need it on every per-term IDF computation.
        self._df: dict[str, int] = {
            term: len(postings) for term, postings in self._postings.items()
        }

    def score_chunks(self, query_terms: Iterable[str]) -> dict[int, float]:
        """Compute BM25 score per chunk for the given query terms.

        Returns a mapping from chunk index to score. Chunks that do
        not contain any query term are *not* in the result (a zero
        score is mathematically distinct from "no signal").
        """
        scores: dict[int, float] = {}
        for term in query_terms:
            postings = self._postings.get(term)
            if not postings:
                continue
            df = self._df[term]
            # Standard BM25+ smoothing on IDF to avoid negatives when
            # a term appears in more than half of the corpus.
            idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1.0)
            for chunk_index, freq in postings.items():
                dl = self._doc_lens[chunk_index]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (
                    1.0 - self.b + self.b * dl / self._avgdl
                )
                scores[chunk_index] = (
                    scores.get(chunk_index, 0.0) + idf * numerator / denominator
                )
        return scores

    def rank_ucs(self, query_terms: Iterable[str]) -> list[tuple[str, float]]:
        """Return a UC-level ranked list ``[(uc_id, score), ...]``.

        Aggregation: per UC, take the maximum chunk score (the
        "best chunk" view that a downstream RAG system would surface
        to the user). Ties are broken by ascending UC ID so the
        ranking is byte-deterministic.
        """
        chunk_scores = self.score_chunks(query_terms)
        uc_best: dict[str, float] = {}
        for chunk_index, score in chunk_scores.items():
            uc_id = self._uc_ids[chunk_index]
            if score > uc_best.get(uc_id, float("-inf")):
                uc_best[uc_id] = score
        # Sort by (-score, uc_id) for stable, deterministic order.
        return sorted(uc_best.items(), key=lambda kv: (-kv[1], kv[0]))


def recall_at_k(ranked_ucs: Sequence[str], expected: frozenset[str], k: int) -> float:
    """Fraction of *expected* UCs that appear in the top-k of *ranked_ucs*."""
    if not expected:
        return 0.0
    top_k = set(ranked_ucs[:k])
    return len(top_k & expected) / len(expected)


def reciprocal_rank(ranked_ucs: Sequence[str], expected: frozenset[str]) -> float:
    """Reciprocal of the rank (1-indexed) of the first expected UC.

    Returns 0.0 if no expected UC appears in *ranked_ucs*.
    """
    for i, uc in enumerate(ranked_ucs):
        if uc in expected:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(
    ranked_ucs: Sequence[str], expected: frozenset[str], k: int
) -> float:
    """Normalised Discounted Cumulative Gain at cutoff *k*.

    Uses binary relevance (UC is either expected or not) and the
    canonical DCG formula ``\u03a3 rel_i / log2(i + 2)``. The ideal DCG
    is computed against ``min(|expected|, k)`` perfect rankings so
    queries with more expected UCs than ``k`` are not penalised.
    """
    if not expected:
        return 0.0
    dcg = sum(
        (1.0 if uc in expected else 0.0) / math.log2(i + 2)
        for i, uc in enumerate(ranked_ucs[:k])
    )
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(expected), k)))
    return dcg / idcg if idcg > 0 else 0.0


@dataclass(frozen=True)
class QueryResult:
    """Computed metrics for one query."""

    query_id: str
    text: str
    expected_ucs: tuple[str, ...]
    top10_ucs: tuple[str, ...]
    recall_at_k: Mapping[int, float]
    mrr: float
    ndcg_at_10: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "text": self.text,
            "expected_ucs": list(self.expected_ucs),
            "top10_ucs": list(self.top10_ucs),
            "recall_at_k": {str(k): self.recall_at_k[k] for k in sorted(self.recall_at_k)},
            "mrr": self.mrr,
            "ndcg_at_10": self.ndcg_at_10,
        }


@dataclass(frozen=True)
class AggregateMetrics:
    """Mean metrics across all queries (the CI gate dimension)."""

    mean_recall_at_k: Mapping[int, float]
    mean_mrr: float
    mean_ndcg_at_10: float
    query_count: int
    corpus_chunk_count: int
    corpus_uc_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_recall_at_k": {
                str(k): self.mean_recall_at_k[k]
                for k in sorted(self.mean_recall_at_k)
            },
            "mean_mrr": self.mean_mrr,
            "mean_ndcg_at_10": self.mean_ndcg_at_10,
            "query_count": self.query_count,
            "corpus_chunk_count": self.corpus_chunk_count,
            "corpus_uc_count": self.corpus_uc_count,
        }


@dataclass(frozen=True)
class EvalRun:
    """Whole-run snapshot: per-query + aggregate + index fingerprint."""

    schema_version: str
    queries: tuple[QueryResult, ...]
    aggregate: AggregateMetrics
    bm25_k1: float
    bm25_b: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "$schema_version": self.schema_version,
            "bm25": {"k1": self.bm25_k1, "b": self.bm25_b},
            "aggregate": self.aggregate.to_dict(),
            "queries": [q.to_dict() for q in self.queries],
        }


def evaluate(
    corpus: Sequence[Chunk],
    queries: Sequence[Query],
    k1: float = DEFAULT_K1,
    b: float = DEFAULT_B,
) -> EvalRun:
    """Run the full evaluation: build index, score every query, aggregate."""
    index = BM25Index(corpus, k1=k1, b=b)
    results: list[QueryResult] = []
    recall_sums: dict[int, float] = dict.fromkeys(RECALL_KS, 0.0)
    mrr_sum = 0.0
    ndcg_sum = 0.0
    for q in queries:
        terms = tokenize(q.text)
        ranked = index.rank_ucs(terms)
        ranked_ids = [uc for uc, _ in ranked]
        recalls: dict[int, float] = {
            k: recall_at_k(ranked_ids, q.expected_ucs, k) for k in RECALL_KS
        }
        rr = reciprocal_rank(ranked_ids, q.expected_ucs)
        ndcg = ndcg_at_k(ranked_ids, q.expected_ucs, NDCG_K)
        for k in RECALL_KS:
            recall_sums[k] += recalls[k]
        mrr_sum += rr
        ndcg_sum += ndcg
        results.append(
            QueryResult(
                query_id=q.id,
                text=q.text,
                expected_ucs=tuple(sorted(q.expected_ucs)),
                top10_ucs=tuple(ranked_ids[:10]),
                recall_at_k=recalls,
                mrr=rr,
                ndcg_at_10=ndcg,
            )
        )
    n = len(queries)
    aggregate = AggregateMetrics(
        mean_recall_at_k={k: recall_sums[k] / n if n else 0.0 for k in RECALL_KS},
        mean_mrr=mrr_sum / n if n else 0.0,
        mean_ndcg_at_10=ndcg_sum / n if n else 0.0,
        query_count=n,
        corpus_chunk_count=len(corpus),
        corpus_uc_count=len({c.uc_id for c in corpus}),
    )
    return EvalRun(
        schema_version=SCHEMA_VERSION,
        queries=tuple(results),
        aggregate=aggregate,
        bm25_k1=k1,
        bm25_b=b,
    )


def render_json(run: EvalRun) -> str:
    """Render *run* as canonical JSON (sorted keys + trailing newline).

    The byte-identical output is what the ``--check`` gate compares
    so this contract is load-bearing for CI determinism.
    """
    return json.dumps(run.to_dict(), indent=2, sort_keys=True) + "\n"


def render_markdown(run: EvalRun) -> str:
    """Render *run* as a human-readable markdown report."""
    lines: list[str] = []
    lines.append("# RAG Retrieval Evaluation Report")
    lines.append("")
    lines.append(
        "Curated query set + BM25 baseline over `dist/rag/chunks/`. "
        "See [`docs/health-check-2026-progress.md`](health-check-2026-progress.md) \u00a7 P17."
    )
    lines.append("")
    agg = run.aggregate
    lines.append(
        f"**Corpus:** {agg.corpus_chunk_count:,} chunks across "
        f"{agg.corpus_uc_count:,} UCs."
    )
    lines.append(f"**Query set:** {agg.query_count} curated queries.")
    lines.append(f"**BM25 parameters:** `k1={run.bm25_k1}, b={run.bm25_b}`")
    lines.append("")
    lines.append("## Aggregate metrics (means across all queries)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    for k in RECALL_KS:
        lines.append(f"| recall@{k} | {agg.mean_recall_at_k[k]:.4f} |")
    lines.append(f"| MRR | {agg.mean_mrr:.4f} |")
    lines.append(f"| nDCG@{NDCG_K} | {agg.mean_ndcg_at_10:.4f} |")
    lines.append("")
    lines.append("## Per-query metrics")
    lines.append("")
    lines.append(
        "| Query ID | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Question |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for q in run.queries:
        recalls = q.recall_at_k
        lines.append(
            "| {qid} | {r1:.2f} | {r5:.2f} | {r10:.2f} | {mrr:.3f} | "
            "{ndcg:.3f} | {text} |".format(
                qid=q.query_id,
                r1=recalls[1],
                r5=recalls[5],
                r10=recalls[10],
                mrr=q.mrr,
                ndcg=q.ndcg_at_10,
                text=q.text.replace("|", "\\|"),
            )
        )
    lines.append("")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class DriftFinding:
    """One regression detected by the ``--check`` gate."""

    metric: str
    baseline: float
    current: float
    delta: float
    tolerance: float


def compare_against_baseline(
    run: EvalRun,
    baseline_path: Path,
    tolerance: float = DEFAULT_TOLERANCE,
) -> list[DriftFinding]:
    """Compare *run*'s aggregate metrics against *baseline_path*.

    Returns the list of metrics that regressed by more than
    *tolerance* (relative). An empty list means no regression and
    the ``--check`` gate passes.
    """
    if not baseline_path.exists():
        raise FileNotFoundError(
            f"{baseline_path} not found \u2014 run "
            "`python -m splunk_uc audit-retrieval-eval --write-baseline` once "
            "and commit the result to freeze the baseline."
        )
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_agg = baseline["aggregate"]
    current_agg = run.aggregate.to_dict()
    findings: list[DriftFinding] = []

    def _check_metric(name: str, baseline_v: float, current_v: float) -> None:
        # A small absolute floor lets the gate tolerate noise when
        # the baseline is itself near zero (e.g. a query that's
        # genuinely hard). Absolute regression must exceed *both*
        # the relative tolerance and 0.01 absolute.
        rel = (current_v - baseline_v) / baseline_v if baseline_v else 0.0
        if rel < -tolerance and (baseline_v - current_v) > 0.01:
            findings.append(
                DriftFinding(
                    metric=name,
                    baseline=baseline_v,
                    current=current_v,
                    delta=rel,
                    tolerance=tolerance,
                )
            )

    for k in RECALL_KS:
        _check_metric(
            f"mean_recall_at_{k}",
            float(baseline_agg["mean_recall_at_k"][str(k)]),
            float(current_agg["mean_recall_at_k"][str(k)]),
        )
    _check_metric("mean_mrr", float(baseline_agg["mean_mrr"]), float(current_agg["mean_mrr"]))
    _check_metric(
        "mean_ndcg_at_10",
        float(baseline_agg["mean_ndcg_at_10"]),
        float(current_agg["mean_ndcg_at_10"]),
    )
    return findings


def _print_summary(run: EvalRun) -> None:
    agg = run.aggregate
    sys.stdout.write(
        f"Retrieval-eval: {agg.query_count} queries x "
        f"{agg.corpus_chunk_count:,} chunks ({agg.corpus_uc_count:,} UCs)\n"
    )
    for k in RECALL_KS:
        sys.stdout.write(f"  mean recall@{k:<2}: {agg.mean_recall_at_k[k]:.4f}\n")
    sys.stdout.write(f"  mean MRR      : {agg.mean_mrr:.4f}\n")
    sys.stdout.write(f"  mean nDCG@{NDCG_K} : {agg.mean_ndcg_at_10:.4f}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc audit-retrieval-eval",
        description=(
            "Run the curated retrieval-eval harness against the chunked "
            "RAG corpus. Emits JSON + markdown reports and optionally "
            "drift-guards against a frozen baseline."
        ),
    )
    parser.add_argument(
        "--rag-dir",
        type=Path,
        default=DEFAULT_RAG_DIR,
        help="RAG corpus directory (default: dist/rag/)",
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERIES_PATH,
        help="Curated query set JSON (default: data/rag/retrieval-eval-queries.json)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Baseline JSON to compare against (default: data/baselines/retrieval-eval-v1.0.json)",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Output JSON path (default: dist/rag/retrieval-eval.json)",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help="Output markdown path (default: dist/rag/retrieval-eval.md)",
    )
    parser.add_argument(
        "--k1",
        type=float,
        default=DEFAULT_K1,
        help=f"BM25 k1 (default: {DEFAULT_K1})",
    )
    parser.add_argument(
        "--b",
        type=float,
        default=DEFAULT_B,
        help=f"BM25 b (default: {DEFAULT_B})",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
        help=(
            f"--check tolerance (default: {DEFAULT_TOLERANCE}, i.e. "
            "2% relative regression allowed)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare against baseline; exit non-zero on regression.",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Overwrite the baseline JSON with the current run (manual op).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout summary.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        queries = load_queries(args.queries)
        corpus = load_corpus(args.rag_dir)
    except FileNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    run = evaluate(corpus, queries, k1=args.k1, b=args.b)
    json_text = render_json(run)
    md_text = render_markdown(run)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json_text, encoding="utf-8")
    args.out_md.write_text(md_text, encoding="utf-8")

    if args.write_baseline:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json_text, encoding="utf-8")
        if not args.quiet:
            sys.stdout.write(f"Wrote baseline: {args.baseline}\n")

    if not args.quiet:
        _print_summary(run)

    if args.check:
        try:
            findings = compare_against_baseline(
                run, args.baseline, tolerance=args.tolerance
            )
        except FileNotFoundError as exc:
            sys.stderr.write(f"error: {exc}\n")
            return 2
        if findings:
            sys.stderr.write(
                "error: retrieval-eval regressed against baseline:\n"
            )
            for f in findings:
                sys.stderr.write(
                    f"  {f.metric}: {f.baseline:.4f} \u2192 {f.current:.4f} "
                    f"(\u0394{f.delta:+.2%}, tolerance {f.tolerance:+.2%})\n"
                )
            return 1
        if not args.quiet:
            sys.stdout.write("baseline check: OK\n")

    return 0


# Re-export the public surface that other modules / tests import.
__all__ = [
    "NDCG_K",
    "RECALL_KS",
    "AggregateMetrics",
    "BM25Index",
    "Chunk",
    "DriftFinding",
    "EvalRun",
    "Query",
    "QueryResult",
    "compare_against_baseline",
    "evaluate",
    "load_corpus",
    "load_queries",
    "main",
    "ndcg_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "render_json",
    "render_markdown",
    "tokenize",
]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
