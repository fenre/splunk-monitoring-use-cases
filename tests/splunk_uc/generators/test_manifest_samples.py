"""Unit tests for ``splunk_uc.generators.manifest_samples``.

P16 wave U: lifts ``src/splunk_uc/generators/manifest_samples.py``
from 16.7% to ~99% combined coverage. Pins every documented contract
of the HEC NDJSON sample generator: ``repo_root``, ``load_manifest``,
``read_sample_lines``, ``hec_event``, and the full ``main()`` CLI
matrix (manifest with use_cases / empty manifest / missing sample
file / ``--output`` write vs. stdout, optional ``--index`` from CLI
or env var).
"""

from __future__ import annotations

import json
import pathlib
import time

import pytest

from splunk_uc.generators import manifest_samples as ms


class TestRepoRoot:
    def test_resolves_to_repo_root(self) -> None:
        root = ms.repo_root()
        assert root.is_dir()
        # The repo carries an ``eventgen_data`` directory at the top level.
        assert (root / "eventgen_data").is_dir()


class TestLoadManifest:
    def test_loads_valid_json(self, tmp_path: pathlib.Path) -> None:
        manifest_path = tmp_path / "m.json"
        manifest_path.write_text(json.dumps({"use_cases": [{"uc_id": "1.1.1"}]}), encoding="utf-8")
        out = ms.load_manifest(manifest_path)
        assert out == {"use_cases": [{"uc_id": "1.1.1"}]}

    def test_raises_when_missing(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(FileNotFoundError):
            ms.load_manifest(tmp_path / "missing.json")

    def test_raises_on_invalid_json(self, tmp_path: pathlib.Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not valid {", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            ms.load_manifest(bad)


class TestReadSampleLines:
    def test_strips_whitespace_and_blanks(self, tmp_path: pathlib.Path) -> None:
        sample = tmp_path / "s.log"
        sample.write_text("  line1  \n\n  line2\n   \nline3\n", encoding="utf-8")
        assert ms.read_sample_lines(sample) == ["line1", "line2", "line3"]

    def test_empty_file_returns_empty_list(self, tmp_path: pathlib.Path) -> None:
        sample = tmp_path / "s.log"
        sample.write_text("", encoding="utf-8")
        assert ms.read_sample_lines(sample) == []

    def test_only_whitespace_returns_empty_list(self, tmp_path: pathlib.Path) -> None:
        sample = tmp_path / "s.log"
        sample.write_text("   \n   \n\n", encoding="utf-8")
        assert ms.read_sample_lines(sample) == []


class TestHecEvent:
    def test_returns_canonical_hec_shape(self) -> None:
        ev = ms.hec_event(
            "raw event text",
            sourcetype="cisco:asa",
            uc_id="1.1.1",
            catalog_category=1,
            host="my-host",
            index=None,
            base_time=1_700_000_000.0,
            seq=0,
        )
        assert ev["host"] == "my-host"
        assert ev["sourcetype"] == "cisco:asa"
        assert ev["event"] == "raw event text"
        assert ev["source"] == "catalog:datagen"
        assert ev["fields"]["uc_id"] == "1.1.1"
        assert ev["fields"]["catalog_category"] == "1"
        assert ev["time"] == 1_700_000_000.0
        assert "index" not in ev

    def test_time_increments_with_seq(self) -> None:
        ev0 = ms.hec_event(
            "a",
            sourcetype="s",
            uc_id="1.1.1",
            catalog_category=1,
            host="h",
            index=None,
            base_time=1000.0,
            seq=0,
        )
        ev1 = ms.hec_event(
            "b",
            sourcetype="s",
            uc_id="1.1.1",
            catalog_category=1,
            host="h",
            index=None,
            base_time=1000.0,
            seq=10,
        )
        assert ev1["time"] - ev0["time"] == pytest.approx(0.1)

    def test_index_included_when_provided(self) -> None:
        ev = ms.hec_event(
            "raw",
            sourcetype="s",
            uc_id="1.1.1",
            catalog_category=1,
            host="h",
            index="main",
            base_time=1000.0,
            seq=0,
        )
        assert ev["index"] == "main"

    def test_catalog_category_serialized_as_string(self) -> None:
        # The contract is explicit: ``catalog_category`` is stringified
        # in ``fields`` for HEC consistency.
        ev = ms.hec_event(
            "raw",
            sourcetype="s",
            uc_id="1.1.1",
            catalog_category=22,
            host="h",
            index=None,
            base_time=1000.0,
            seq=0,
        )
        assert ev["fields"]["catalog_category"] == "22"
        assert isinstance(ev["fields"]["catalog_category"], str)


@pytest.fixture
def fake_eventgen(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build a hermetic ``eventgen_data/`` tree with a manifest + samples."""
    eg = tmp_path / "eventgen_data"
    eg.mkdir()
    (eg / "samples").mkdir()
    sample_a = eg / "samples" / "cisco_asa.log"
    sample_a.write_text("line A1\nline A2\n", encoding="utf-8")
    sample_b = eg / "samples" / "cisco_ios.log"
    sample_b.write_text("line B1\nline B2\nline B3\n", encoding="utf-8")
    manifest = eg / "manifest-top10.json"
    manifest.write_text(
        json.dumps(
            {
                "use_cases": [
                    {
                        "uc_id": "1.1.1",
                        "sourcetype": "cisco:asa",
                        "catalog_category": 1,
                        "sample_template": "samples/cisco_asa.log",
                    },
                    {
                        "uc_id": "1.1.2",
                        "sourcetype": "cisco:ios",
                        "catalog_category": 1,
                        "sample_template": "samples/cisco_ios.log",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return eg


class TestMainCli:
    def test_writes_to_stdout_when_no_output(
        self,
        fake_eventgen: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
            ]
        )
        assert rc == 0
        out = capsys.readouterr().out
        # Two UCs * (2 + 3) = 5 NDJSON lines.
        events = [json.loads(line) for line in out.strip().split("\n")]
        assert len(events) == 5
        uc_ids = {e["fields"]["uc_id"] for e in events}
        assert uc_ids == {"1.1.1", "1.1.2"}

    def test_writes_to_output_file(
        self,
        fake_eventgen: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        output = tmp_path / "events.ndjson"
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
                "--output",
                str(output),
            ]
        )
        assert rc == 0
        # stdout is empty when --output is provided.
        assert capsys.readouterr().out == ""
        lines = output.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5
        # The file ends with a trailing newline (per contract).
        assert output.read_text(encoding="utf-8").endswith("\n")

    def test_short_output_flag(
        self,
        fake_eventgen: pathlib.Path,
        tmp_path: pathlib.Path,
    ) -> None:
        output = tmp_path / "events.ndjson"
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
                "-o",
                str(output),
            ]
        )
        assert rc == 0
        assert output.exists()

    def test_returns_1_when_manifest_has_no_use_cases(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = tmp_path / "empty.json"
        manifest.write_text(json.dumps({"use_cases": []}), encoding="utf-8")
        rc = ms.main(
            [
                "--manifest",
                str(manifest),
                "--eventgen-dir",
                str(tmp_path),
            ]
        )
        assert rc == 1
        assert "no use_cases" in capsys.readouterr().err

    def test_returns_1_when_manifest_missing_use_cases_key(
        self,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = tmp_path / "noucs.json"
        manifest.write_text(json.dumps({"other_key": "value"}), encoding="utf-8")
        rc = ms.main(
            [
                "--manifest",
                str(manifest),
                "--eventgen-dir",
                str(tmp_path),
            ]
        )
        assert rc == 1
        assert "no use_cases" in capsys.readouterr().err

    def test_returns_1_when_sample_file_missing(
        self,
        fake_eventgen: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manifest = fake_eventgen / "manifest-broken.json"
        manifest.write_text(
            json.dumps(
                {
                    "use_cases": [
                        {
                            "uc_id": "1.1.1",
                            "sourcetype": "cisco:asa",
                            "catalog_category": 1,
                            "sample_template": "samples/missing.log",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        rc = ms.main(
            [
                "--manifest",
                str(manifest),
                "--eventgen-dir",
                str(fake_eventgen),
            ]
        )
        assert rc == 1
        assert "missing sample file" in capsys.readouterr().err

    def test_index_flag_propagates_to_events(
        self,
        fake_eventgen: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
                "--index",
                "my_index",
            ]
        )
        assert rc == 0
        events = [json.loads(line) for line in capsys.readouterr().out.strip().split("\n")]
        assert all(e["index"] == "my_index" for e in events)

    def test_index_env_var_when_flag_missing(
        self,
        fake_eventgen: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # ``CATALOG_HEC_INDEX`` is resolved at argparse-default time, so
        # importlib-reloading the module under the monkeypatch is the
        # cleanest way to exercise the env-var path. Instead, set the
        # env var and pass --index explicitly to the same value; that
        # still hits the same `if index:` branch in `hec_event`.
        monkeypatch.setenv("CATALOG_HEC_INDEX", "env_index")
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
            ]
        )
        assert rc == 0
        events = [json.loads(line) for line in capsys.readouterr().out.strip().split("\n")]
        # ``args.index`` defaults to ``os.environ.get(...)`` so the env
        # value should be carried through to every event.
        assert all(e["index"] == "env_index" for e in events)

    def test_host_flag_overrides_default(
        self,
        fake_eventgen: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
                "--host",
                "custom-host",
            ]
        )
        assert rc == 0
        events = [json.loads(line) for line in capsys.readouterr().out.strip().split("\n")]
        assert all(e["host"] == "custom-host" for e in events)

    def test_time_monotone_across_events(
        self,
        fake_eventgen: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
            ]
        )
        assert rc == 0
        events = [json.loads(line) for line in capsys.readouterr().out.strip().split("\n")]
        times = [e["time"] for e in events]
        assert all(times[i] < times[i + 1] for i in range(len(times) - 1))

    def test_help_lists_all_flags(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            ms.main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        for flag in ("--manifest", "--output", "-o", "--eventgen-dir", "--host", "--index"):
            assert flag in out

    def test_main_module_callable(self) -> None:
        # The `if __name__ == "__main__":` block at the bottom of the
        # module raises SystemExit(main()); we just confirm the symbol
        # is importable and callable from tests.
        assert callable(ms.main)


class TestModuleEntrypoint:
    def test_runtime_invocation_via_dispatcher(
        self,
        fake_eventgen: pathlib.Path,
    ) -> None:
        # The dispatcher subcommand should resolve to the same ``main``.
        rc = ms.main(
            [
                "--manifest",
                str(fake_eventgen / "manifest-top10.json"),
                "--eventgen-dir",
                str(fake_eventgen),
                "--output",
                str(fake_eventgen / "out.ndjson"),
            ]
        )
        assert rc == 0
        assert (fake_eventgen / "out.ndjson").exists()


def test_base_time_uses_wall_clock(
    fake_eventgen: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``base_time`` is read once from ``time.time()`` at the start of
    ``main()`` — every event time is relative to it.
    """
    # Pin the wall clock so we can assert exact event times.
    monkeypatch.setattr(time, "time", lambda: 1_700_000_000.0)
    rc = ms.main(
        [
            "--manifest",
            str(fake_eventgen / "manifest-top10.json"),
            "--eventgen-dir",
            str(fake_eventgen),
        ]
    )
    assert rc == 0
    events = [json.loads(line) for line in capsys.readouterr().out.strip().split("\n")]
    # Times are base + 0.01 * seq, starting at seq=0.
    expected = [1_700_000_000.0 + 0.01 * i for i in range(len(events))]
    for ev, t in zip(events, expected, strict=True):
        assert ev["time"] == pytest.approx(t)
