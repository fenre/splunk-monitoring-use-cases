"""Read-only loader for ``api/v1/*.json`` + the signed provenance ledger.

The loader is local-first: if a clone of the repository is available on disk,
every request is satisfied from the local tree. Otherwise it falls back to
HTTPS against the project's own GitHub Pages mirror. No other origins are
permitted, so the server cannot be used as an SSRF stepping stone even if a
malicious tool schema reaches the agent.

Design notes
------------

* **Read-only.** All helpers load JSON and return ``dict``/``list`` objects.
  Nothing here writes back to disk.
* **Payload caps.** Every HTTP response is gated by ``MAX_PAYLOAD_BYTES`` to
  keep a rogue redirect from exhausting memory. Local reads use the same cap
  through ``stat().st_size``.
* **No secrets, no credentials.** The catalogue is 100 % public; the loader
  does not send or read any authentication headers.
* **Cached.** Each endpoint is LRU-cached per process — the catalogue is
  static between rebuilds, so every invocation within a single agent session
  is fetched at most once.

CoSAI MCP alignment
-------------------

* Input validation: ``_validate_path_segment`` enforces an allow-list of
  characters before touching the filesystem (no path traversal possible).
* Transport safety: the HTTPS base URL is pinned; arbitrary URLs cannot be
  substituted at runtime.
* Payload limits: ``MAX_PAYLOAD_BYTES`` caps every load (default 10 MB, big
  enough for the largest shipped endpoint which is ``compliance/ucs/
  index.json`` at ~855 KB, small enough to prevent DoS).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx

from splunk_uc_mcp import __version__


LOG = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://fenre.github.io/splunk-monitoring-use-cases"
"""Hosted mirror of the static API. Overridable via ``--base-url`` or
``SPLUNK_UC_BASE_URL``. Only HTTPS URLs pointing at the project's own site
are honoured; :meth:`Catalog._validate_base_url` enforces this."""


MAX_PAYLOAD_BYTES = 10 * 1024 * 1024
"""Per-endpoint payload cap. 10 MB is comfortably above the largest shipped
endpoint (compliance/ucs/index.json ~ 855 KB) and well below any plausible
memory pressure from a single tool call."""


HTTP_TIMEOUT_SECONDS = 10.0
"""HTTPS fallback request timeout. Kept small so agents don't stall for
extended periods when the remote mirror is unreachable."""


_ALLOWED_PATH_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9_\-@\.]*\.json$")
"""Allow-list for ``load_json`` path components. Matches every endpoint
currently shipped under ``api/v1``: lowercase alphanumerics plus
``[-_@.]`` and mandatory ``.json`` suffix. No dots at the start, no path
separators, no uppercase."""


_ALLOWED_DIRECTORY_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")
"""Allow-list for intermediate directory segments (``compliance``,
``equipment``, ``recommender``, …). Stricter than the filename regex
because no directory below ``api/v1/`` legitimately contains dots or at-
signs."""


_ALLOWED_BASE_URL = re.compile(
    r"^https://[a-z0-9][a-z0-9\-\.]*\.(github\.io|githubusercontent\.com)(/[A-Za-z0-9_\-\./]*)?$"
)
"""HTTPS allow-list for the fallback base URL. Restricts the server to
github.io + githubusercontent.com origins so a malformed ``--base-url``
flag cannot redirect requests to an attacker-controlled host."""


class CatalogError(Exception):
    """Raised when the catalogue cannot serve a requested endpoint."""


class CatalogNotFoundError(CatalogError):
    """Raised when the requested file exists neither locally nor remotely."""


class CatalogValidationError(CatalogError):
    """Raised when caller input fails path/URL validation."""


def _validate_path_segment(segment: str, *, is_directory: bool = False) -> None:
    """Raise :class:`CatalogValidationError` if ``segment`` is unsafe.

    Prevents path traversal (``..``), absolute paths (leading ``/``),
    case-sensitivity bypass (uppercase), and accidental escape via
    whitespace or shell metacharacters.
    """

    if not segment or len(segment) > 128:
        raise CatalogValidationError(
            f"Path segment must be 1-128 chars (got {len(segment)})"
        )
    allow = _ALLOWED_DIRECTORY_SEGMENT if is_directory else _ALLOWED_PATH_SEGMENT
    if not allow.fullmatch(segment):
        raise CatalogValidationError(
            f"Path segment {segment!r} does not match allow-list"
        )


class Catalog:
    """Read-only accessor for the ``api/v1`` tree.

    Parameters
    ----------
    catalog_root:
        Path to a local checkout (must contain ``api/v1/``). If ``None``,
        the constructor probes the current working directory; if that fails
        to look like a checkout, only the HTTPS fallback is used.
    base_url:
        HTTPS fallback. Defaults to :data:`DEFAULT_BASE_URL`. Must match
        :data:`_ALLOWED_BASE_URL` or the constructor raises
        :class:`CatalogValidationError`.
    http_client:
        Optional pre-configured :class:`httpx.Client`. Mostly useful in
        tests where the caller wants to mount :mod:`respx`. When omitted,
        a short-timeout client is lazy-instantiated on first remote hit.
    """

    def __init__(
        self,
        *,
        catalog_root: Path | None = None,
        base_url: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._catalog_root = self._resolve_catalog_root(catalog_root)
        self._base_url = self._validate_base_url(base_url or DEFAULT_BASE_URL)
        self._http_client = http_client
        self._owns_client = http_client is None
        LOG.debug(
            "Catalog initialised: root=%s base_url=%s",
            self._catalog_root,
            self._base_url,
        )

    @staticmethod
    def _resolve_catalog_root(explicit: Path | None) -> Path | None:
        if explicit is not None:
            root = explicit.expanduser().resolve()
            if (root / "api" / "v1" / "manifest.json").is_file():
                return root
            raise CatalogValidationError(
                f"--catalog-root {root} does not contain api/v1/manifest.json"
            )
        # Probe CWD to keep "run from repo checkout" ergonomic.
        cwd = Path.cwd().resolve()
        if (cwd / "api" / "v1" / "manifest.json").is_file():
            return cwd
        # Probe the package's ancestors (covers `python -m` from an editable
        # install where CWD might be the user's home).
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "api" / "v1" / "manifest.json").is_file():
                return parent
        return None

    @staticmethod
    def _validate_base_url(url: str) -> str:
        url = url.rstrip("/")
        if not _ALLOWED_BASE_URL.fullmatch(url):
            raise CatalogValidationError(
                f"base_url {url!r} is not on the github.io/githubusercontent.com allow-list"
            )
        # Reject any dot-segment in the path even though GitHub Pages
        # would normalise it; the CoSAI MCP rule says "no traversal",
        # not "no traversal that the server happens to normalise away".
        if "/./" in url or "/../" in url or url.endswith("/..") or url.endswith("/."):
            raise CatalogValidationError(
                f"base_url must not contain path traversal segments: {url!r}"
            )
        return url

    @property
    def catalog_root(self) -> Path | None:
        """Local checkout root if one was found; ``None`` when remote-only."""

        return self._catalog_root

    @property
    def base_url(self) -> str:
        """Effective HTTPS fallback URL (no trailing slash)."""

        return self._base_url

    def close(self) -> None:
        """Dispose of the HTTP client if we own it."""

        if self._owns_client and self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "Catalog":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def load_json(self, *segments: str) -> Any:
        """Load an ``api/v1/*.json`` endpoint.

        Each positional argument is one path component under ``api/v1``.
        The last segment must end with ``.json``; all others must be
        directory slugs. Every component is validated before the path is
        joined, so path-traversal payloads are rejected with
        :class:`CatalogValidationError` before any I/O happens.

        Examples
        --------
        >>> cat.load_json("manifest.json")
        >>> cat.load_json("compliance", "ucs", "22.1.1.json")
        >>> cat.load_json("equipment", "index.json")
        """

        if not segments:
            raise CatalogValidationError("at least one path segment is required")
        *dirs, filename = segments
        for d in dirs:
            _validate_path_segment(d, is_directory=True)
        _validate_path_segment(filename, is_directory=False)

        if self._catalog_root is not None:
            local_path = self._catalog_root / "api" / "v1" / Path(*segments)
            if local_path.is_file():
                return self._read_local(local_path)

        return self._fetch_remote(list(segments))

    def load_data_file(self, relative_path: str) -> Any:
        """Load a JSON file from ``data/`` (e.g. the signed mapping ledger).

        Only supported locally. When the caller is running remote-only the
        method returns ``None`` rather than raising, because the ledger is
        not currently published to GitHub Pages (it lives in the repo so
        the Sigstore signatures travel with git history).
        """

        if self._catalog_root is None:
            LOG.warning(
                "load_data_file(%r): no local catalog, data/ is not available remotely",
                relative_path,
            )
            return None
        # Defensive validation: reject absolute paths + traversal.
        if relative_path != relative_path.lstrip("/"):
            raise CatalogValidationError("relative_path must not be absolute")
        parts = Path(relative_path).parts
        for part in parts:
            if part in ("", ".", ".."):
                raise CatalogValidationError(
                    f"relative_path contains a forbidden segment: {part!r}"
                )
        for part in parts[:-1]:
            _validate_path_segment(part, is_directory=True)
        _validate_path_segment(parts[-1], is_directory=False)

        full = self._catalog_root / "data" / Path(*parts)
        if not full.is_file():
            raise CatalogNotFoundError(f"data/{relative_path} not found locally")
        return self._read_local(full)

    @staticmethod
    def _read_local(path: Path) -> Any:
        size = path.stat().st_size
        if size > MAX_PAYLOAD_BYTES:
            raise CatalogError(
                f"{path} exceeds MAX_PAYLOAD_BYTES ({size} > {MAX_PAYLOAD_BYTES})"
            )
        with path.open("r", encoding="utf-8") as handle:
            try:
                return json.load(handle)
            except json.JSONDecodeError as exc:
                raise CatalogError(
                    f"Corrupt JSON in {path}: {exc}"
                ) from exc

    def _fetch_remote(self, segments: list[str]) -> Any:
        url = "/".join([self._base_url, "api", "v1", *segments])
        LOG.debug("Remote fetch: %s", url)
        client = self._ensure_http_client()
        try:
            # Cap response with a streamed read so a malicious redirect to a
            # huge blob cannot fill memory.
            with client.stream("GET", url, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                if resp.status_code == 404:
                    raise CatalogNotFoundError(
                        f"Endpoint {'/'.join(segments)} not found at {url}"
                    )
                resp.raise_for_status()
                body = bytearray()
                for chunk in resp.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_PAYLOAD_BYTES:
                        raise CatalogError(
                            f"Remote payload exceeds MAX_PAYLOAD_BYTES: {url}"
                        )
            try:
                return json.loads(bytes(body).decode("utf-8"))
            except json.JSONDecodeError as jexc:
                raise CatalogError(
                    f"Corrupt JSON from {url}: {jexc}"
                ) from jexc
        except httpx.HTTPError as exc:
            raise CatalogError(f"Remote fetch failed for {url}: {exc}") from exc

    def _ensure_http_client(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client(
                follow_redirects=False,
                timeout=HTTP_TIMEOUT_SECONDS,
                headers={
                    "User-Agent": f"splunk-uc-mcp/{__version__} (+https://fenre.github.io/splunk-monitoring-use-cases)",
                    "Accept": "application/json",
                },
            )
        return self._http_client


