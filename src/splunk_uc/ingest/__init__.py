"""External-data ingestion pipelines.

Ingestion verbs pull data from authoritative external sources
(NIST, MITRE, ENISA, regulatory portals, vendor docs) and emit
structured catalogue inputs. They are interactive (rate-limited
external HTTP) and tend to require an ``--out`` parameter, a
``--dry-run`` mode, and a ``--force`` mode to overwrite existing
sidecars.

Migration source: ``scripts/ingest_*.py``, ``scripts/scrape_*.py``,
and ``scripts/fetch_*.py``.
"""

from __future__ import annotations

__all__: list[str] = []
