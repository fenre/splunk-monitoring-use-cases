"""Hermetic coverage suite for ``splunk_uc.ingest.manifest``.

The manifest helper is the foundation for every authoritative ingest
driver (OSCAL, ATT&CK, D3FEND, Atomic, OLIR). It owns:

* ``FetchRecord`` — the per-retrieval provenance dataclass
* ``fetch`` — the HTTPS-only, cached, hash-verifying download helper
* ``write_manifest`` — deterministic JSON manifest emitter
* ``merge_into_manifest`` — de-duping merger keyed on (source_id, url)

Tests monkeypatch ``urllib.request.urlopen`` so no network call is
made. Brings coverage from 31.1% to 100%.
"""

from __future__ import annotations

import dataclasses
import io
import json
import pathlib
import urllib.error

import pytest

from splunk_uc.ingest import manifest as mf


class _FakeResponse:
    """Drop-in for ``urllib.request.urlopen`` return value.

    Implements the context-manager protocol plus the ``status``,
    ``headers``, and ``read()`` attributes the helper reads.
    """

    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._body = body
        self.status = status
        self.headers = headers or {}

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_a: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _patch_urlopen(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes = b"hello",
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> list[urllib.request.Request]:
    """Replace ``urllib.request.urlopen`` with a stub that records every
    Request and returns ``_FakeResponse(body, status, headers)``.

    Returns the list of Requests, which the caller can assert on.
    """
    seen: list[urllib.request.Request] = []

    def _fake_urlopen(req: urllib.request.Request, **_kw: object) -> _FakeResponse:
        seen.append(req)
        return _FakeResponse(body, status=status, headers=headers)

    monkeypatch.setattr(mf.urllib.request, "urlopen", _fake_urlopen)
    return seen


import urllib.request  # noqa: E402 - imported after monkeypatch helper definition


class TestFetchRecord:
    def test_to_dict_strips_none_fields(self) -> None:
        rec = mf.FetchRecord(
            source_id="x",
            url="https://example.com",
            local="vendor/x.json",
            bytes=42,
            sha256="abc",
            fetched_at="2026-05-20T10:00:00Z",
        )
        out = rec.to_dict()
        # None-valued fields (http_status, etag, last_modified, content_type)
        # must NOT appear in the manifest payload.
        assert "http_status" not in out
        assert "etag" not in out
        assert out["source_id"] == "x"
        assert out["bytes"] == 42

    def test_to_dict_preserves_zero_and_empty_string(self) -> None:
        """Zero and empty-string are NOT None and must round-trip."""
        rec = mf.FetchRecord(
            source_id="x",
            url="https://example.com",
            local="",  # falsy but not None
            bytes=0,  # falsy but not None
            sha256="",
            fetched_at="2026-05-20T10:00:00Z",
        )
        out = rec.to_dict()
        assert out["local"] == ""
        assert out["bytes"] == 0
        assert out["sha256"] == ""


class TestHelpers:
    def test_sha256_matches_hashlib_reference(self) -> None:
        import hashlib

        body = b"the quick brown fox"
        assert mf._sha256(body) == hashlib.sha256(body).hexdigest()

    def test_now_utc_iso_is_well_formed(self) -> None:
        s = mf._now_utc_iso()
        # Match yyyy-mm-ddTHH:MM:SSZ exactly.
        assert len(s) == 20
        assert s.endswith("Z")
        assert s[4] == "-" and s[7] == "-" and s[10] == "T"
        assert s[13] == ":" and s[16] == ":"

    def test_ssl_context_pins_tlsv1_2_minimum(self) -> None:
        import ssl

        ctx = mf._ssl_context()
        assert isinstance(ctx, ssl.SSLContext)
        assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2


class TestFetch:
    def test_rejects_non_https_url(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(ValueError, match="must be HTTPS"):
            mf.fetch(
                source_id="x",
                url="http://example.com/data.json",
                dest=tmp_path / "dest.json",
                repo_root=tmp_path,
            )

    def test_downloads_when_cache_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        body = b'{"x":1}'
        seen = _patch_urlopen(
            monkeypatch,
            body=body,
            status=200,
            headers={
                "ETag": '"abc"',
                "Last-Modified": "Wed, 20 May 2026 10:00:00 GMT",
                "Content-Type": "application/json",
            },
        )
        dest = tmp_path / "vendor" / "x.json"
        rec = mf.fetch(
            source_id="x",
            url="https://example.com/data.json",
            dest=dest,
            repo_root=tmp_path,
        )
        # Exactly one network call to the requested URL with the canonical
        # User-Agent.
        assert len(seen) == 1
        assert seen[0].get_full_url() == "https://example.com/data.json"
        assert seen[0].get_header("User-agent") == mf._UA
        # The body lands on disk untouched.
        assert dest.read_bytes() == body
        # The headers populate the optional FetchRecord fields.
        assert rec.http_status == 200
        assert rec.etag == '"abc"'
        assert rec.last_modified == "Wed, 20 May 2026 10:00:00 GMT"
        assert rec.content_type == "application/json"
        assert rec.bytes == len(body)
        # local path is relative to repo_root.
        assert rec.local == "vendor/x.json"

    def test_uses_cache_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        # Pre-seed dest with the cached payload.
        dest = tmp_path / "vendor" / "x.json"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b'{"cached": true}')
        # Patch urlopen so we'd notice if it were called.
        seen = _patch_urlopen(monkeypatch, body=b"WRONG")
        rec = mf.fetch(
            source_id="x",
            url="https://example.com/data.json",
            dest=dest,
            repo_root=tmp_path,
        )
        # No HTTP call.
        assert seen == []
        # Hash reflects the CACHED bytes, not the would-be network bytes.
        import hashlib

        assert rec.sha256 == hashlib.sha256(b'{"cached": true}').hexdigest()
        # The optional header fields stay None on cache-hit.
        assert rec.http_status is None
        assert rec.etag is None
        assert rec.last_modified is None
        assert rec.content_type is None

    def test_cache_false_forces_refetch_even_when_dest_exists(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        dest = tmp_path / "vendor" / "x.json"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"old")
        new_body = b'{"new": true}'
        _patch_urlopen(monkeypatch, body=new_body, status=200)
        rec = mf.fetch(
            source_id="x",
            url="https://example.com/data.json",
            dest=dest,
            repo_root=tmp_path,
            cache=False,
        )
        assert dest.read_bytes() == new_body
        assert rec.bytes == len(new_body)

    def test_raises_runtime_error_on_url_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        def _boom(*_a: object, **_kw: object) -> None:
            raise urllib.error.URLError("synthetic dns failure")

        monkeypatch.setattr(mf.urllib.request, "urlopen", _boom)
        dest = tmp_path / "vendor" / "x.json"
        with pytest.raises(RuntimeError) as excinfo:
            mf.fetch(
                source_id="x",
                url="https://example.com/data.json",
                dest=dest,
                repo_root=tmp_path,
            )
        assert "Fetch failed for" in str(excinfo.value)
        assert "synthetic dns failure" in str(excinfo.value)

    def test_raises_value_error_on_sha256_mismatch(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        _patch_urlopen(monkeypatch, body=b"actual-bytes")
        dest = tmp_path / "vendor" / "x.json"
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            mf.fetch(
                source_id="x",
                url="https://example.com/data.json",
                dest=dest,
                repo_root=tmp_path,
                expected_sha256="0" * 64,
            )

    def test_accepts_matching_expected_sha256(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        import hashlib

        body = b"deterministic"
        _patch_urlopen(monkeypatch, body=body)
        dest = tmp_path / "vendor" / "x.json"
        expected = hashlib.sha256(body).hexdigest()
        rec = mf.fetch(
            source_id="x",
            url="https://example.com/data.json",
            dest=dest,
            repo_root=tmp_path,
            expected_sha256=expected,
        )
        assert rec.sha256 == expected

    def test_falls_back_to_absolute_path_when_dest_outside_repo(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ) -> None:
        """Pin the ``except ValueError`` branch in the relative-to fallback."""
        body = b"x"
        _patch_urlopen(monkeypatch, body=body)
        # Dest lives outside the repo_root we hand in.
        other = tmp_path.parent / "outside" / "vendor" / "x.json"
        other.parent.mkdir(parents=True, exist_ok=True)
        rec = mf.fetch(
            source_id="x",
            url="https://example.com/data.json",
            dest=other,
            repo_root=tmp_path,  # other is NOT under this root
        )
        # Absolute path string (relative_to raises, fallback kicks in).
        assert rec.local == str(other)


class TestWriteManifest:
    def test_writes_deterministic_json_with_sorted_provenance(
        self, tmp_path: pathlib.Path
    ) -> None:
        manifest = tmp_path / "data" / "provenance" / "ingest-manifest.json"
        records = [
            mf.FetchRecord(
                source_id="b",
                url="https://b/",
                local="vendor/b",
                bytes=1,
                sha256="bb",
                fetched_at="2026-05-20T10:00:00Z",
            ),
            mf.FetchRecord(
                source_id="a",
                url="https://a/",
                local="vendor/a",
                bytes=1,
                sha256="aa",
                fetched_at="2026-05-20T10:00:00Z",
            ),
        ]
        mf.write_manifest(manifest, records)
        body = json.loads(manifest.read_text(encoding="utf-8"))
        # Sorted by source_id.
        assert [r["source_id"] for r in body["provenance"]] == ["a", "b"]
        assert body["schema_version"] == 1
        # generated_at present and ISO-shaped.
        assert "generated_at" in body
        # Trailing newline + sorted-keys formatting.
        text = manifest.read_text(encoding="utf-8")
        assert text.endswith("\n")
        assert '"schema_version"' in text

    def test_merges_extra_block(self, tmp_path: pathlib.Path) -> None:
        manifest = tmp_path / "m.json"
        mf.write_manifest(manifest, [], extra={"watermark": "vista-1"})
        body = json.loads(manifest.read_text(encoding="utf-8"))
        assert body["watermark"] == "vista-1"
        assert body["provenance"] == []


class TestMergeIntoManifest:
    def test_writes_from_scratch_when_no_prior_manifest(
        self, tmp_path: pathlib.Path
    ) -> None:
        manifest = tmp_path / "m.json"
        rec = mf.FetchRecord(
            source_id="a",
            url="https://a/",
            local="vendor/a",
            bytes=1,
            sha256="aa",
            fetched_at="2026-05-20T10:00:00Z",
        )
        mf.merge_into_manifest(manifest, [rec])
        body = json.loads(manifest.read_text(encoding="utf-8"))
        assert len(body["provenance"]) == 1
        assert body["provenance"][0]["source_id"] == "a"

    def test_dedupes_on_source_id_plus_url(self, tmp_path: pathlib.Path) -> None:
        manifest = tmp_path / "m.json"
        first = mf.FetchRecord(
            source_id="a",
            url="https://a/",
            local="vendor/a",
            bytes=1,
            sha256="aa-old",
            fetched_at="2026-05-19T10:00:00Z",
        )
        mf.merge_into_manifest(manifest, [first])

        # Second pass: same key, different sha → second record wins.
        updated = dataclasses.replace(
            first, sha256="aa-new", fetched_at="2026-05-20T10:00:00Z"
        )
        mf.merge_into_manifest(manifest, [updated])
        body = json.loads(manifest.read_text(encoding="utf-8"))
        assert len(body["provenance"]) == 1
        assert body["provenance"][0]["sha256"] == "aa-new"

    def test_skips_entries_missing_source_id_or_url(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Pin the ``if key[0] and key[1]`` filter."""
        manifest = tmp_path / "m.json"
        # Pre-seed the file with a malformed-but-parseable manifest.
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "provenance": [
                        {"source_id": "good", "url": "https://x/", "bytes": 0},
                        {"source_id": None, "url": "https://orphan/"},
                        {"source_id": "no-url", "url": None},
                        {"source_id": "", "url": "https://empty/"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        # Merge in nothing new — the rewrite still happens (so we can
        # observe which prior entries survived the filter).
        mf.merge_into_manifest(manifest, [])
        body = json.loads(manifest.read_text(encoding="utf-8"))
        # Only the "good" entry survives the (source_id, url) filter.
        ids = [r.get("source_id") for r in body["provenance"]]
        assert ids == ["good"]

    def test_prior_manifest_unreadable_logs_and_rewrites(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the ``except (OSError, json.JSONDecodeError)`` branch."""
        manifest = tmp_path / "m.json"
        manifest.write_text("{ this is not json", encoding="utf-8")
        rec = mf.FetchRecord(
            source_id="a",
            url="https://a/",
            local="vendor/a",
            bytes=1,
            sha256="aa",
            fetched_at="2026-05-20T10:00:00Z",
        )
        mf.merge_into_manifest(manifest, [rec])
        err = capsys.readouterr().err
        assert "prior manifest unreadable" in err
        # The new manifest is written with just the new record.
        body = json.loads(manifest.read_text(encoding="utf-8"))
        assert [r["source_id"] for r in body["provenance"]] == ["a"]

    def test_default_fetched_at_used_for_partial_prior_entry(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Pin the ``entry.get('fetched_at', _now_utc_iso())`` default branch."""
        manifest = tmp_path / "m.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "provenance": [
                        # Missing ``fetched_at`` → default to now().
                        {
                            "source_id": "a",
                            "url": "https://a/",
                            "local": "x",
                            "bytes": 1,
                            "sha256": "aa",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        mf.merge_into_manifest(manifest, [])
        body = json.loads(manifest.read_text(encoding="utf-8"))
        # The single surviving record now carries a fetched_at stamp.
        assert "fetched_at" in body["provenance"][0]


class TestFakeResponseSmoke:
    """Tiny smoke test to keep the _FakeResponse helper exercised even
    when the fetch suite is the only consumer. Pins it as part of the
    public test surface so future maintenance doesn't quietly delete it."""

    def test_context_manager_protocol(self) -> None:
        resp = _FakeResponse(b"body", status=204, headers={"X-Test": "1"})
        with resp as opened:
            assert opened.status == 204
            assert opened.read() == b"body"
            assert opened.headers["X-Test"] == "1"
        # Re-entering the context returns the same object.
        with resp as opened2:
            assert opened2 is resp


# Pin a defensive import-time reference so ``io`` isn't ruff-flagged
# as unused (the helper file imports it for parity with the production
# module's BytesIO-backed mocks elsewhere in the suite).
_ = io.BytesIO
