"""Production ingest pipelines for authoritative compliance sources.

Each ingest driver:
  * downloads raw bytes from a trusted public source,
  * records SHA-256 + HTTP metadata in the shared retrieval manifest,
  * transforms the raw artefact into a normalised JSON shape under
    ``data/crosswalks/<source>/``.

The manifest is the cryptographic provenance layer: every downstream
artefact in this repository can be traced back to a byte-identical copy
of the source.
"""
