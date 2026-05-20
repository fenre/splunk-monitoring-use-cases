#!/usr/bin/env python3
"""Generate the RAG-ready chunked corpus under ``dist/rag/``.

Every UC in the catalogue already produces a pure-markdown twin at
``dist/uc/UC-X.Y.Z/uc.md`` (see ``tools/build/render_legacy_artifacts``).
LLM-retrieval pipelines, however, do not want one 30 kB document per
UC; they want many small, self-contained chunks they can embed and
retrieve.

This generator is the **first LLM-eval primitive** called for by
repo-health phase **P17**. It walks every ``dist/uc/UC-*/uc.md`` file,
splits each one on its natural ``## Section`` boundaries, and emits:

* **``dist/rag/chunks/UC-X.Y.Z--NN.md``** \u2014 one self-contained
  markdown chunk per section (or per sub-chunk when a section exceeds
  the size budget). Every chunk is prefixed with a short YAML-style
  frontmatter block carrying the UC ID, the chunk index, the section
  title, the chunk byte count, and a stable content hash. The
  frontmatter is deliberately YAML-compatible plain text \u2014 no
  PyYAML dependency required, just key/value lines.
* **``dist/rag/manifest.json``** \u2014 a single JSON document that
  enumerates every chunk with its metadata. Downstream eval and
  retrieval pipelines treat this manifest as the authoritative
  index of what's been chunked.
* **``dist/rag/manifest.md``** \u2014 a human-readable summary of the
  chunking run: total UCs, total chunks, char/chunk histogram, and
  the largest / smallest chunks.

Chunking strategy
-----------------
The chunker is deliberately stdlib-only (per ADR-0004) and uses a
simple but principled algorithm:

1. Split the ``uc.md`` body on lines that start with ``## `` (level-2
   markdown headings). Each split becomes a candidate chunk owning
   its section title.
2. If a candidate chunk exceeds ``MAX_CHARS`` (default 2,000 chars
   \u2248 500 tokens at ~4 chars/token), split it on level-3 headings
   (``### ``). If a sub-chunk still exceeds the budget, fall back to
   splitting on paragraph (blank-line) boundaries.
3. Every chunk inherits the UC's H1 title and quick-facts table by
   default so that an LLM looking at a chunk in isolation still
   knows which UC it came from.

The resulting chunks honour the *single-responsibility* principle:
one chunk \u2248 one self-contained answer unit.

Determinism
-----------
The generator is byte-deterministic given identical inputs. Two
consecutive runs produce byte-identical ``manifest.json`` files and
byte-identical chunk files, with a stable ``content_hash`` per chunk
(``sha256`` of the chunk body, no frontmatter). This is what lets the
``--check`` flag work as a CI drift guard.

Usage
-----

    python -m splunk_uc generate-rag-chunks            # write mode
    python -m splunk_uc generate-rag-chunks --check    # CI drift guard
    python -m splunk_uc generate-rag-chunks --stats    # summary only

Exit codes
----------
* 0 \u2014 success.
* 1 \u2014 (``--check`` only) committed manifest differs from a fresh
  rebuild; rerun without ``--check`` and commit.
* 2 \u2014 unexpected error (missing ``dist/uc/``, malformed input).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DIST_DIR = REPO_ROOT / "dist"
UC_INPUT_DIR = DIST_DIR / "uc"
RAG_OUT_DIR = DIST_DIR / "rag"
CHUNKS_OUT_DIR = RAG_OUT_DIR / "chunks"
MANIFEST_JSON_PATH = RAG_OUT_DIR / "manifest.json"
MANIFEST_MD_PATH = RAG_OUT_DIR / "manifest.md"

# Maximum characters per chunk before we fall back to a sub-split.
# 2,000 chars \u2248 500 tokens at 4 chars/token \u2014 a comfortable size
# for any modern embedding model's input window.
MAX_CHARS = 2_000

# Per-slice splitter budget. ``chunk_uc_markdown`` appends a single
# trailing ``\n`` to every chunk body just before stamping it, so a
# splitter slice of exactly ``MAX_CHARS`` chars becomes a
# ``MAX_CHARS + 1`` chunk \u2014 one byte over budget. Targeting
# ``MAX_CHARS - 1`` inside the splitters keeps the final
# ``char_count`` at or under :data:`MAX_CHARS` without the chunker
# having to know about the splitter's internal accounting.
_SLICE_BUDGET = MAX_CHARS - 1

# Minimum useful chunk size in characters. Anything below this is a
# stub (e.g. "## SPL\n" with no body), and emitting it would just
# pollute the retrieval index. The threshold also short-circuits the
# H1-preamble-only chunk for UCs whose body is entirely empty.
MIN_CHARS = 80

# Pattern matching markdown section boundaries.
_H2_RE = re.compile(r"(?m)^## (?P<title>.+?)$")
_H3_RE = re.compile(r"(?m)^### (?P<title>.+?)$")

# Pattern matching a fenced code block at the start of a paragraph.
# Matches the opening fence with an optional language tag, the body,
# and the closing fence; allows arbitrary text *after* the closing
# fence (the common authoring pattern where an SPL block is
# immediately followed by a one-line "Alert actions: ..." note inside
# the same logical paragraph). ``re.DOTALL`` lets ``.`` match
# newlines inside the body.
_CODE_FENCE_RE = re.compile(
    r"\A(?P<fence>```[A-Za-z0-9_+\-]*)\n(?P<body>.*?)\n(?P<close>```)(?P<trailing>.*)\Z",
    re.DOTALL,
)

# A line beginning a new SPL pipe stage. Splunk authors conventionally
# put each ``| <command>`` on its own line, so a line-leading ``|``
# (after optional whitespace) is the canonical pipe-stage boundary.
# Detected here without ``re`` so the test surface stays minimal.

# Pipe-stage chunking overhead per output sub-chunk: the opening
# fence + its newline + the closing fence + trailing newline. Computed
# at call time because the opening fence varies by language tag.


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class Chunk:
    """One self-contained chunk of one UC.

    Two hash fields are deliberately distinct:

    * ``content_hash`` \u2014 ``sha256(body)`` truncated to 16 hex chars.
      Sensitive to *any* byte change, including whitespace and case;
      this is what powers the ``--check`` byte-determinism gate.
    * ``embedding_fingerprint`` \u2014 ``sha256(normalised(body))``
      truncated to 16 hex chars. Stable across cosmetic differences
      (lowercase, collapsed whitespace, markdown-noise stripped);
      this is what downstream RAG / eval pipelines use to detect
      near-duplicate chunks during ingest. Collisions across UCs are
      a feature, not a bug \u2014 they reveal "the same answer in
      different wrapping" (e.g. the same SPL block embedded under
      ``## Description``, ``## SPL``, and ``## Detailed
      implementation`` in one UC's markdown twin).
    """

    uc_id: str  # "1.1.1"
    chunk_index: int  # 0-based, gap-free within a UC
    section_title: str  # e.g. "Description" or "(intro)"
    body: str  # the chunk body (without frontmatter)
    char_count: int
    content_hash: str  # sha256 of body (byte-exact)
    embedding_fingerprint: str  # sha256 of normalise_for_fingerprint(body)

    def to_manifest_entry(self) -> dict[str, Any]:
        """Render as a manifest.json entry (display id with ``UC-`` prefix)."""
        return {
            "uc_id": f"UC-{self.uc_id}",
            "chunk_index": self.chunk_index,
            "section_title": self.section_title,
            "char_count": self.char_count,
            "content_hash": self.content_hash,
            "embedding_fingerprint": self.embedding_fingerprint,
            "path": f"chunks/UC-{self.uc_id}--{self.chunk_index:02d}.md",
        }

    def to_markdown(self) -> str:
        """Render to disk: frontmatter + body."""
        return (
            "---\n"
            f"uc_id: UC-{self.uc_id}\n"
            f"chunk_index: {self.chunk_index}\n"
            f"section_title: {_yaml_escape(self.section_title)}\n"
            f"char_count: {self.char_count}\n"
            f"content_hash: {self.content_hash}\n"
            f"embedding_fingerprint: {self.embedding_fingerprint}\n"
            "---\n\n"
            f"{self.body.rstrip()}\n"
        )


@dataclass
class ChunkStats:
    """Aggregate stats over one generator run."""

    uc_count: int = 0
    chunk_count: int = 0
    total_chars: int = 0
    largest_chunk_chars: int = 0
    smallest_chunk_chars: int = 0
    over_budget_chunk_count: int = 0
    unique_fingerprint_count: int = 0
    duplicate_fingerprint_count: int = 0
    per_uc_chunk_count: dict[str, int] = field(default_factory=dict)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


# Markdown-noise characters stripped from the embedding-fingerprint
# normalisation. We keep characters that carry semantic meaning even
# in plain text (e.g. ``=`` and ``|`` matter for SPL, ``:`` matters
# for key/value pairs in YAML-ish frontmatter, ``/`` matters for
# paths) and strip only the typographic markup. ``#`` and ``>`` are
# stripped because in markdown they appear at line starts to mark
# headers and blockquotes \u2014 they don't change what the chunk *says*.
_MD_NOISE_RE = re.compile(r"[#>*_`~\[\]()]+")
_WS_COLLAPSE_RE = re.compile(r"\s+")


def _normalise_for_fingerprint(body: str) -> str:
    """Reduce *body* to a cosmetic-difference-insensitive form.

    Two chunks whose bodies differ only by formatting (whitespace,
    case, markdown emphasis markers, header level, link wrapping)
    must produce identical normalised strings, and therefore
    identical :class:`Chunk.embedding_fingerprint` values. The
    canonical form is:

    1. Lowercase. SPL keywords are case-insensitive (``STATS`` ==
       ``stats``); markdown section titles are usually not
       semantically distinguished by case either.
    2. Strip markdown noise (``#``, ``>``, ``*``, ``_``,
       backticks, ``~``, ``[``, ``]``, ``(``, ``)``). These mark
       formatting intent but do not change what the chunk says.
    3. Collapse every run of whitespace (spaces, tabs, newlines)
       to a single space.
    4. Strip leading and trailing whitespace.

    The result is **not** intended to be human-readable; it exists
    solely to feed :func:`hashlib.sha256` so that two near-duplicate
    chunks collide on the same fingerprint.
    """
    text = body.lower()
    text = _MD_NOISE_RE.sub("", text)
    text = _WS_COLLAPSE_RE.sub(" ", text)
    return text.strip()


def _yaml_escape(value: str) -> str:
    """Wrap a section title in quotes if it contains YAML-special chars.

    The chunk frontmatter is plain text \u2014 not parsed by anything in
    this repo \u2014 but downstream consumers may treat it as YAML.
    Quoting on ``:`` / ``#`` / leading dashes is enough to keep parsers
    happy without pulling in PyYAML.
    """
    risky = (":", "#", '"', "'")
    if any(value.startswith(p) or p in value for p in risky):
        # Escape any embedded double-quotes by doubling them, YAML-style.
        return '"' + value.replace('"', '""') + '"'
    return value


def _extract_h1_block(text: str) -> str:
    """Return everything from the first H1 to (but not including) the
    first H2. This is the document's preamble that every sub-chunk
    inherits so each chunk knows which UC it belongs to.
    """
    m = _H2_RE.search(text)
    if m is None:
        return text.strip()
    return text[: m.start()].rstrip()


def _split_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split on H2 boundaries.

    Returns a list of ``(section_title, section_body)`` pairs. The
    section body **includes** the H2 line so each chunk renders
    cleanly. An ``intro`` synthetic section captures any text before
    the first H2 (the preamble \u2014 see :func:`_extract_h1_block`).
    """
    matches = list(_H2_RE.finditer(text))
    if not matches:
        return [("(intro)", text.strip())]
    sections: list[tuple[str, str]] = []
    pre = text[: matches[0].start()].strip()
    if pre:
        sections.append(("(intro)", pre))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].rstrip()
        title = m.group("title").strip()
        sections.append((title, body))
    return sections


def _split_oversized_section(section_body: str) -> list[str]:
    """Split a too-large H2 section into sub-chunks.

    First tries H3 boundaries; if any sub-chunk is still over budget,
    falls back to paragraph (blank-line) boundaries on that sub-chunk.
    Returns a list of strings, each of which is at-or-under
    :data:`MAX_CHARS` whenever possible. (If a *single paragraph* is
    over budget we emit it as one oversized chunk \u2014 stats will flag
    it, and the human can fix the source markdown.)
    """
    h3_matches = list(_H3_RE.finditer(section_body))
    chunks: list[str] = []

    if h3_matches:
        # Split on H3.
        boundaries = [m.start() for m in h3_matches]
        boundaries.append(len(section_body))
        # If there's a preamble before the first H3, keep it as its own piece.
        if boundaries[0] > 0:
            head = section_body[: boundaries[0]].rstrip()
            if head:
                chunks.append(head)
        for i in range(len(boundaries) - 1):
            piece = section_body[boundaries[i] : boundaries[i + 1]].rstrip()
            if piece:
                chunks.append(piece)
    else:
        chunks.append(section_body)

    # Second pass: any chunk still over budget gets paragraph-split.
    out: list[str] = []
    for chunk in chunks:
        if len(chunk) <= MAX_CHARS:
            out.append(chunk)
            continue
        out.extend(_paragraph_split(chunk))
    return out


def _paragraph_split(text: str) -> list[str]:
    """Greedy paragraph-pack into chunks of at-most :data:`MAX_CHARS`.

    Splits on the ``\\n\\n`` boundary and packs paragraphs into
    chunks left-to-right, never crossing the budget if a paragraph
    fits in a new chunk. Single paragraphs over budget get a final
    pass through, in order:

    1. :func:`_split_oversized_code_block` — fenced code blocks split
       at line-leading ``|`` pipe-stage boundaries and re-wrap each
       slice in the same fence.
    2. :func:`_split_oversized_markdown_table` — markdown tables
       (every line begins with ``|``) split between data rows and
       re-emit the header + delimiter rows on every slice so each
       slice renders as a valid markdown table.
    3. :func:`_split_oversized_bullet_list` — bulleted prose where
       every top-level item starts with ``- `` or ``* `` packs items
       into slices of at-most :data:`MAX_CHARS`.

    Paragraphs that don't match any structured shape are emitted as
    one oversized chunk and the caller decides what to do.
    """
    paragraphs: list[str] = []
    for p in text.split("\n\n"):
        if not p.strip():
            continue
        if len(p) > MAX_CHARS:
            split = _split_oversized_code_block(p)
            if split == [p]:
                split = _split_oversized_markdown_table(p)
            if split == [p]:
                split = _split_oversized_bullet_list(p)
            paragraphs.extend(split)
        else:
            paragraphs.append(p)
    out: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for para in paragraphs:
        para_len = len(para) + 2  # +2 accounts for the blank line we re-insert
        if buf_len + para_len > MAX_CHARS and buf:
            out.append("\n\n".join(buf).rstrip())
            buf = [para]
            buf_len = para_len
        else:
            buf.append(para)
            buf_len += para_len
    if buf:
        out.append("\n\n".join(buf).rstrip())
    return out


def _split_oversized_code_block(paragraph: str) -> list[str]:
    """If *paragraph* is a fenced code block over :data:`MAX_CHARS`,
    split its interior at line-leading ``|`` pipe-stage boundaries
    and re-wrap each slice in the same opening / closing fence.
    Otherwise return ``[paragraph]`` unchanged.

    Splunk authors conventionally place each ``| <command>`` on its
    own line, so line-leading ``|`` is the canonical pipe-stage
    boundary and a line-based split is correct without needing to
    track quote / paren depth (those are only needed for *single-
    line* SPL, where there's no useful split point anyway).

    Splitting strategy:

    1. Strip the opening and closing fences; remember the language
       tag so each slice can be re-wrapped identically.
    2. Walk the body line by line, accumulating each "pipe stage"
       (a leading line that does *not* start with ``|`` is the
       search-clause / preamble stage; every subsequent line that
       starts with ``|`` opens a new stage).
    3. Greedy-pack stages into output slices of at-most
       :data:`MAX_CHARS` characters (counting the fence overhead).
       The first slice keeps the preamble stage; every other slice
       only contains continuation stages, all of which start with
       ``|``, so a slice viewed in isolation is unambiguously a
       continuation rather than a complete SPL query.
    4. If a *single* pipe stage is still over budget (e.g. a
       multi-line ``[ subsearch ]`` block with no internal pipe
       breaks), emit it as one over-budget slice. This is rare and
       a deliberate trade-off: splitting inside a subsearch would
       corrupt the SPL grammar, so the chunker preserves
       correctness over budget compliance.

    If the body has only one pipe stage (or none — pure literal),
    splitting can't help and we return ``[paragraph]`` unchanged.
    """
    m = _CODE_FENCE_RE.match(paragraph.strip())
    if m is None:
        return [paragraph]
    fence = m.group("fence")
    close = m.group("close")
    body = m.group("body")
    trailing = m.group("trailing").strip()
    fence_overhead = len(fence) + 1 + len(close) + 1  # opening + \n + close + \n

    stages = _group_spl_pipe_stages(body)
    if len(stages) <= 1:
        # No useful split points (pure literal or single pipe stage).
        # If there's trailing prose we can still split *that* off.
        if trailing:
            return [_render_fence_slice(fence, close, stages), trailing]
        return [paragraph]

    out: list[str] = []
    buf: list[str] = []
    buf_chars = 0
    for stage in stages:
        stage_chars = len(stage) + (1 if buf else 0)  # +1 for join newline
        if buf and buf_chars + stage_chars + fence_overhead > _SLICE_BUDGET:
            out.append(_render_fence_slice(fence, close, buf))
            buf = [stage]
            buf_chars = len(stage)
        else:
            buf.append(stage)
            buf_chars += stage_chars
    if buf:
        out.append(_render_fence_slice(fence, close, buf))
    # Trailing prose becomes its own paragraph so the parent
    # _paragraph_split can pack it normally.
    if trailing:
        out.append(trailing)
    return out


def _group_spl_pipe_stages(body: str) -> list[str]:
    """Group lines of a code-block body into "pipe stages".

    A pipe stage is the leading-line (preamble — search clause,
    ``comment(...)`` macro, or top-level generating command) followed
    by any continuation lines that do *not* themselves start with
    ``|``. Every line whose first non-whitespace character is ``|``
    opens a new stage.

    Strategy:

    * Lines are scanned in order. The first stage absorbs every line
      up to (but not including) the first line that starts with
      ``|``.
    * Each subsequent ``|`` line opens a new stage that also absorbs
      its non-``|`` continuation lines.
    * If the body contains no ``|`` lines at all, the whole body is
      one stage (caller treats this as "no useful split available").

    The return is a list of stage strings already joined with
    ``\\n`` so the caller can re-assemble slices without re-inserting
    newlines.
    """
    lines = body.split("\n")
    stages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("|") and current:
            stages.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        stages.append(current)
    return ["\n".join(stage) for stage in stages]


def _render_fence_slice(fence: str, close: str, stages: list[str]) -> str:
    """Wrap a sequence of pipe stages back in their fence."""
    return f"{fence}\n" + "\n".join(stages) + f"\n{close}"


# Pattern recognising the markdown table-delimiter row that follows
# a header row: pipes around runs of dashes (with optional alignment
# colons). The header itself just needs to start with ``|``; the
# delimiter row is what distinguishes a real table from prose that
# happens to start with a bare pipe character.
_TABLE_DELIMITER_RE = re.compile(r"^\s*\|(\s*:?-{3,}:?\s*\|)+\s*$")


def _split_oversized_markdown_table(paragraph: str) -> list[str]:
    """If *paragraph* is a markdown table over :data:`MAX_CHARS`,
    split between data rows and re-emit the header + delimiter rows
    on every slice so each slice renders as a valid table.
    Otherwise return ``[paragraph]`` unchanged.

    A "table" here means a sequence of lines where every non-empty
    line starts with ``|`` AND the second line matches
    :data:`_TABLE_DELIMITER_RE` (``| --- | --- |``). The header is
    the first row, the delimiter is the second row, and every
    remaining row is a data row.

    If a *single* data row already exceeds the budget (a single cell
    containing a very long ``Data sources`` description) it is
    emitted as its own slice with the header re-emitted; chunk count
    stays above-budget but the slice still renders as a valid
    one-row table, which is more useful to a retrieval pipeline
    than the original wedged-together block.
    """
    lines = paragraph.split("\n")
    if len(lines) < 3:
        return [paragraph]
    if not lines[0].lstrip().startswith("|"):
        return [paragraph]
    if not _TABLE_DELIMITER_RE.match(lines[1]):
        return [paragraph]
    if not all(ln.lstrip().startswith("|") or not ln.strip() for ln in lines[2:]):
        return [paragraph]

    header = lines[0]
    delimiter = lines[1]
    data_rows = [ln for ln in lines[2:] if ln.strip()]
    if not data_rows:
        return [paragraph]

    header_overhead = len(header) + 1 + len(delimiter) + 1  # +\n after each
    out: list[str] = []
    buf: list[str] = []
    buf_chars = 0
    for row in data_rows:
        # +1 for the join newline if this isn't the first row in the buf
        row_chars = len(row) + (1 if buf else 0)
        if buf and buf_chars + row_chars + header_overhead > _SLICE_BUDGET:
            out.append(_render_table_slice(header, delimiter, buf))
            buf = [row]
            buf_chars = len(row)
        else:
            buf.append(row)
            buf_chars += row_chars
    if buf:
        out.append(_render_table_slice(header, delimiter, buf))
    return out


def _render_table_slice(header: str, delimiter: str, rows: list[str]) -> str:
    """Render one slice: header + delimiter + rows."""
    return header + "\n" + delimiter + "\n" + "\n".join(rows)


# Pattern recognising the start of a top-level bullet list item.
# ``- `` and ``* `` are markdown; ``1. ``-style numbered lists are
# also detected. Indented continuation lines stay with their parent
# item.
_BULLET_ITEM_RE = re.compile(r"^(?:[-*]|\d+\.)\s+")


def _split_oversized_bullet_list(paragraph: str) -> list[str]:
    """If *paragraph* is a single logical bullet list over
    :data:`MAX_CHARS`, pack items into slices of at-most
    :data:`MAX_CHARS`. Otherwise return ``[paragraph]`` unchanged.

    A "bullet list" here means a paragraph where the first
    non-whitespace character is a bullet marker (``- ``, ``* ``, or
    ``1. ``) AND at least three lines start with a bullet marker
    (lists with two items are usually too short to be worth
    splitting; bullet markers appear in random prose often enough
    that a stricter threshold avoids false positives).

    Each item absorbs its non-bullet continuation lines. Items
    larger than :data:`MAX_CHARS` are emitted as their own
    oversized slice; the chunker has no further splitting strategy
    for individual bullets without losing semantic continuity.
    """
    lines = paragraph.split("\n")
    if not lines:
        return [paragraph]
    stripped = lines[0].lstrip()
    if not _BULLET_ITEM_RE.match(stripped):
        return [paragraph]
    bullet_line_count = sum(
        1 for ln in lines if _BULLET_ITEM_RE.match(ln.lstrip())
    )
    if bullet_line_count < 3:
        return [paragraph]

    items = _group_bullet_items(lines)
    if len(items) <= 1:
        return [paragraph]

    out: list[str] = []
    buf: list[str] = []
    buf_chars = 0
    for item in items:
        item_chars = len(item) + (1 if buf else 0)  # +1 for join newline
        if buf and buf_chars + item_chars > _SLICE_BUDGET:
            out.append("\n".join(buf))
            buf = [item]
            buf_chars = len(item)
        else:
            buf.append(item)
            buf_chars += item_chars
    if buf:
        out.append("\n".join(buf))
    return out


def _group_bullet_items(lines: list[str]) -> list[str]:
    """Group lines of a bullet list into one string per item.

    A new item starts on every line whose first non-whitespace
    character is a bullet marker (``-``, ``*``, ``1.``). Non-bullet
    continuation lines stay with the previous item.
    """
    items: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _BULLET_ITEM_RE.match(line.lstrip()) and current:
            items.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        items.append(current)
    return ["\n".join(item) for item in items]


# ----------------------------------------------------------------------
# Chunker core
# ----------------------------------------------------------------------


_UC_DIR_RE = re.compile(r"^UC-(?P<id>(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*))$")


def _iter_uc_md_paths(uc_dir: Path) -> Iterable[tuple[str, Path]]:
    """Yield ``(uc_id, uc.md path)`` for every UC under ``dist/uc/``."""
    if not uc_dir.exists():
        return
    for sub in sorted(uc_dir.iterdir()):
        if not sub.is_dir():
            continue
        m = _UC_DIR_RE.match(sub.name)
        if m is None:
            continue
        md = sub / "uc.md"
        if not md.exists():
            continue
        yield m.group("id"), md


def chunk_uc_markdown(uc_id: str, text: str) -> list[Chunk]:
    """Chunk one ``uc.md`` body into a list of :class:`Chunk` records.

    The first chunk always carries the H1 preamble so a single chunk
    is enough context for an LLM to identify the UC. Subsequent chunks
    are also stamped with the UC id in their frontmatter, but we keep
    the preamble out of *their* bodies to avoid duplicating tens of
    kilobytes across the corpus.
    """
    preamble = _extract_h1_block(text)
    sections = _split_h2_sections(text)
    chunks: list[Chunk] = []
    next_index = 0

    for title, body in sections:
        candidates: list[str] = (
            [body] if len(body) <= MAX_CHARS else _split_oversized_section(body)
        )
        for piece in candidates:
            piece = piece.strip()
            if not piece:
                continue
            # The first chunk of the UC owns the H1 preamble; subsequent
            # chunks do not, to keep the corpus from ballooning.
            if next_index == 0:
                body_text = piece if title == "(intro)" else f"{preamble}\n\n{piece}"
            else:
                body_text = piece
            body_text = body_text.strip() + "\n"
            # Filter stubs: a section that is only its own header line
            # (e.g. ``## SPL\n`` with no content rendered yet) is noise
            # for retrieval. Skip anything below MIN_CHARS unless it's
            # the very first chunk and would otherwise leave the UC
            # absent from the corpus.
            if len(body_text) < MIN_CHARS and next_index > 0:
                continue
            content_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()[:16]
            embedding_fp = hashlib.sha256(
                _normalise_for_fingerprint(body_text).encode("utf-8")
            ).hexdigest()[:16]
            chunks.append(
                Chunk(
                    uc_id=uc_id,
                    chunk_index=next_index,
                    section_title=title,
                    body=body_text,
                    char_count=len(body_text),
                    content_hash=content_hash,
                    embedding_fingerprint=embedding_fp,
                )
            )
            next_index += 1

    return chunks


def build_corpus(
    uc_dir: Path | None = None,
) -> tuple[list[Chunk], ChunkStats]:
    """Walk every UC markdown twin and return all chunks + stats.

    *uc_dir* defaults to ``dist/uc/``, but it is resolved at call time
    so monkeypatching :data:`UC_INPUT_DIR` in tests works as expected.
    """
    if uc_dir is None:
        uc_dir = UC_INPUT_DIR
    chunks: list[Chunk] = []
    stats = ChunkStats()
    for uc_id, md_path in _iter_uc_md_paths(uc_dir):
        text = md_path.read_text(encoding="utf-8")
        uc_chunks = chunk_uc_markdown(uc_id, text)
        if not uc_chunks:
            continue
        chunks.extend(uc_chunks)
        stats.uc_count += 1
        stats.per_uc_chunk_count[uc_id] = len(uc_chunks)
        for c in uc_chunks:
            stats.chunk_count += 1
            stats.total_chars += c.char_count
            stats.largest_chunk_chars = max(stats.largest_chunk_chars, c.char_count)
            stats.smallest_chunk_chars = (
                c.char_count
                if stats.smallest_chunk_chars == 0
                else min(stats.smallest_chunk_chars, c.char_count)
            )
            if c.char_count > MAX_CHARS:
                stats.over_budget_chunk_count += 1
    # Fingerprint roll-up: count distinct vs. duplicate chunks across
    # the *entire* corpus. Duplicates aren't an error \u2014 the same SPL
    # block legitimately appears in multiple sections of one UC's
    # markdown twin \u2014 but the count tells downstream eval pipelines
    # how much "free" deduplication is available.
    fingerprints = {c.embedding_fingerprint for c in chunks}
    stats.unique_fingerprint_count = len(fingerprints)
    stats.duplicate_fingerprint_count = stats.chunk_count - stats.unique_fingerprint_count
    return chunks, stats


# ----------------------------------------------------------------------
# Writers
# ----------------------------------------------------------------------


def render_manifest_json(
    chunks: list[Chunk],
    stats: ChunkStats,
) -> dict[str, Any]:
    """Render the on-disk ``manifest.json`` shape."""
    avg = stats.total_chars / stats.chunk_count if stats.chunk_count else 0
    return {
        "$schema_version": "1.1",
        "generator": "splunk_uc.generators.rag_chunks",
        "max_chars": MAX_CHARS,
        "uc_count": stats.uc_count,
        "chunk_count": stats.chunk_count,
        "total_chars": stats.total_chars,
        "avg_chars_per_chunk": round(avg, 1),
        "largest_chunk_chars": stats.largest_chunk_chars,
        "smallest_chunk_chars": stats.smallest_chunk_chars,
        "over_budget_chunk_count": stats.over_budget_chunk_count,
        "unique_fingerprint_count": stats.unique_fingerprint_count,
        "duplicate_fingerprint_count": stats.duplicate_fingerprint_count,
        "chunks": [c.to_manifest_entry() for c in chunks],
    }


def render_manifest_md(stats: ChunkStats, chunks: list[Chunk]) -> str:
    """Render the human-readable manifest.md summary."""
    avg = stats.total_chars / stats.chunk_count if stats.chunk_count else 0
    largest_examples = sorted(chunks, key=lambda c: -c.char_count)[:5]
    smallest_examples = sorted(chunks, key=lambda c: c.char_count)[:5]
    most_split = sorted(
        stats.per_uc_chunk_count.items(), key=lambda kv: -kv[1]
    )[:5]
    lines: list[str] = [
        "# RAG chunked corpus",
        "",
        (
            "Auto-generated by "
            "`python3 -m splunk_uc generate-rag-chunks`. Do not edit "
            "by hand. Companion JSON: `manifest.json`."
        ),
        "",
        "## Summary",
        "",
        f"- UCs chunked: **{stats.uc_count:,}**",
        f"- Total chunks: **{stats.chunk_count:,}**",
        f"- Total chars across all chunks: **{stats.total_chars:,}**",
        f"- Mean chars / chunk: **{avg:.1f}**",
        f"- Largest chunk: **{stats.largest_chunk_chars:,} chars**",
        f"- Smallest chunk: **{stats.smallest_chunk_chars:,} chars**",
        f"- Chunks over budget ({MAX_CHARS:,} chars): **{stats.over_budget_chunk_count}**",
        f"- Unique fingerprints: **{stats.unique_fingerprint_count:,}**",
        f"- Duplicate fingerprints: **{stats.duplicate_fingerprint_count:,}**",
        "",
        "## Largest chunks",
        "",
        "| UC | Chunk | Section | Chars |",
        "| -- | ----- | ------- | ----- |",
    ]
    for c in largest_examples:
        lines.append(
            f"| `UC-{c.uc_id}` | {c.chunk_index} | `{c.section_title}` "
            f"| {c.char_count:,} |"
        )
    lines.extend(
        [
            "",
            "## Smallest chunks",
            "",
            "| UC | Chunk | Section | Chars |",
            "| -- | ----- | ------- | ----- |",
        ]
    )
    for c in smallest_examples:
        lines.append(
            f"| `UC-{c.uc_id}` | {c.chunk_index} | `{c.section_title}` "
            f"| {c.char_count:,} |"
        )
    if most_split:
        lines.extend(
            [
                "",
                "## Most-split UCs",
                "",
                "| UC | Chunks |",
                "| -- | ------ |",
            ]
        )
        for uc_id, count in most_split:
            lines.append(f"| `UC-{uc_id}` | {count} |")
    lines.append("")
    return "\n".join(lines)


def write_corpus(chunks: list[Chunk], stats: ChunkStats, out_dir: Path) -> None:
    """Write the chunked corpus + manifest into ``out_dir/``.

    Idempotent: clears any pre-existing ``chunks/`` directory before
    writing so the file set always matches the manifest.
    """
    chunks_dir = out_dir / "chunks"
    if chunks_dir.exists():
        for old in chunks_dir.iterdir():
            if old.is_file():
                old.unlink()
    chunks_dir.mkdir(parents=True, exist_ok=True)
    for c in chunks:
        path = chunks_dir / f"UC-{c.uc_id}--{c.chunk_index:02d}.md"
        path.write_text(c.to_markdown(), encoding="utf-8")
    (out_dir / "manifest.json").write_text(
        json.dumps(render_manifest_json(chunks, stats), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "manifest.md").write_text(
        render_manifest_md(stats, chunks), encoding="utf-8"
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def _argv_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="generate-rag-chunks",
        description="Generate the RAG-ready chunked corpus under dist/rag/.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help=(
            "CI drift guard: rebuild the manifest in-memory and exit "
            "non-zero if it differs from the committed dist/rag/manifest.json."
        ),
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print the chunking stats summary and exit (no file writes).",
    )
    return p


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - dispatcher-driven
    parser = _argv_parser()
    args = parser.parse_args(argv)

    if not UC_INPUT_DIR.exists():
        print(
            f"ERROR: {UC_INPUT_DIR} not found. Run `make build` first so "
            "dist/uc/ exists, then re-run.",
            file=sys.stderr,
        )
        return 2

    try:
        chunks, stats = build_corpus()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    manifest_dict = render_manifest_json(chunks, stats)

    if args.stats:
        print(json.dumps(asdict(stats), indent=2, sort_keys=True))
        return 0

    if args.check:
        existing = MANIFEST_JSON_PATH
        if not existing.exists():
            print(
                f"ERROR: {existing} not found \u2014 run "
                "`python -m splunk_uc generate-rag-chunks` and commit.",
                file=sys.stderr,
            )
            return 1
        committed = json.loads(existing.read_text(encoding="utf-8"))
        if committed != manifest_dict:
            print(
                "ERROR: dist/rag/manifest.json is out of date \u2014 "
                "run `python -m splunk_uc generate-rag-chunks` and "
                "commit the regenerated dist/rag/.",
                file=sys.stderr,
            )
            return 1
        return 0

    RAG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_corpus(chunks, stats, RAG_OUT_DIR)
    try:
        display_dir = RAG_OUT_DIR.relative_to(REPO_ROOT)
    except ValueError:
        # In tests RAG_OUT_DIR may be monkeypatched to a tmp dir outside
        # the repo. Fall back to the full path.
        display_dir = RAG_OUT_DIR
    print(
        f"Wrote {stats.chunk_count:,} chunks across {stats.uc_count:,} UCs "
        f"to {display_dir}/."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - dispatcher-driven
    raise SystemExit(main())
