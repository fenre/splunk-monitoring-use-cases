"""Unit tests for ``python -m splunk_uc audit-codeowners-coverage``."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"


@pytest.fixture(scope="module")
def coc():
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    import splunk_uc.audits.codeowners_coverage as module

    return module


@pytest.fixture()
def mini_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Hermetic git repo with tracked files and a CODEOWNERS file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
    )

    (repo / "src" / "splunk_uc").mkdir(parents=True)
    (repo / "src" / "splunk_uc" / "kept.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "readme.md").write_text("# hi\n", encoding="utf-8")
    (repo / "tools").mkdir()
    (repo / "tools" / "extra.py").write_text("y = 2\n", encoding="utf-8")

    github = repo / ".github"
    github.mkdir()
    codeowners = github / "CODEOWNERS"
    codeowners.write_text(
        "\n".join(
            [
                "# header comment",
                "",
                "# team docs",
                "docs/ @docs-team @docs-backup",
                "",
                "src/splunk_uc/ @core",
                "/stale-path/ @ghost",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

    monkeypatch.setattr("splunk_uc.audits.codeowners_coverage.REPO_ROOT", repo)
    monkeypatch.setattr(
        "splunk_uc.audits.codeowners_coverage.CODEOWNERS_PATH", codeowners
    )
    return repo


def test_parse_codeowners_comments_blanks_multi_owner(coc, mini_repo: Path) -> None:
    rules = coc.parse_codeowners(coc.CODEOWNERS_PATH)
    assert len(rules) == 3
    assert rules[0].pattern == "docs/"
    assert rules[0].owners == ("@docs-team", "@docs-backup")
    assert rules[1].pattern == "src/splunk_uc/"
    assert rules[2].pattern == "/stale-path/"


def test_latest_match_wins(coc) -> None:
    rules = [
        coc.CodeownersRule("*", ("@catch-all",), 1),
        coc.CodeownersRule("docs/", ("@docs",), 2),
        coc.CodeownersRule("docs/readme.md", ("@readme",), 3),
    ]
    winner = coc._winning_rule("docs/readme.md", rules)
    assert winner is not None
    assert winner.owners == ("@readme",)


def test_evaluate_coverage_counters(coc, mini_repo: Path) -> None:
    rules = coc.parse_codeowners(coc.CODEOWNERS_PATH)
    files = coc.enumerate_repo_files(mini_repo)
    report = coc.evaluate_coverage(files, rules)
    assert report.files_total == 4
    assert report.files_covered == 2
    assert report.files_uncovered == [".github/CODEOWNERS", "tools/extra.py"]


def test_uncovered_files_listed(coc, mini_repo: Path) -> None:
    rules = coc.parse_codeowners(coc.CODEOWNERS_PATH)
    files = coc.enumerate_repo_files(mini_repo)
    report = coc.evaluate_coverage(files, rules)
    assert "tools/extra.py" in report.files_uncovered
    assert "src/splunk_uc/kept.py" not in report.files_uncovered


def test_evaluate_orphan_rules(coc, mini_repo: Path) -> None:
    rules = coc.parse_codeowners(coc.CODEOWNERS_PATH)
    files = coc.enumerate_repo_files(mini_repo)
    orphans = coc.evaluate_orphan_rules(rules, files)
    assert len(orphans) == 1
    assert orphans[0].pattern == "/stale-path/"


def test_cli_check_passes_above_threshold(coc, mini_repo: Path) -> None:
    rc = coc.main(["--check", "--threshold", "50"])
    assert rc == 0


def test_cli_check_fails_below_threshold(coc, mini_repo: Path) -> None:
    rc = coc.main(["--check", "--threshold", "99"])
    assert rc == 1


def test_cli_out_writes_json_and_markdown(coc, mini_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    rc = coc.main(["--out", str(out_dir), "--directory-cap", "5"])
    assert rc == 0
    json_path = out_dir / "codeowners-coverage.json"
    md_path = out_dir / "codeowners-coverage.md"
    assert json_path.is_file()
    assert md_path.is_file()
    assert "Lane rollups" in md_path.read_text(encoding="utf-8")


def test_json_output_is_deterministic(coc, mini_repo: Path, tmp_path: Path) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    coc.main(["--out", str(out_a), "--directory-cap", "3"])
    coc.main(["--out", str(out_b), "--directory-cap", "3"])
    payload_a = json.loads((out_a / "codeowners-coverage.json").read_text())
    payload_b = json.loads((out_b / "codeowners-coverage.json").read_text())
    payload_a.pop("generated_utc")
    payload_b.pop("generated_utc")
    assert payload_a == payload_b
    text_a = (out_a / "codeowners-coverage.json").read_text(encoding="utf-8")
    assert text_a.index('"by_directory"') < text_a.index('"coverage_percent"')


def test_empty_codeowners_everything_uncovered(
    coc, mini_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coc.CODEOWNERS_PATH.write_text("\n# only comments\n", encoding="utf-8")
    rules = coc.parse_codeowners(coc.CODEOWNERS_PATH)
    files = coc.enumerate_repo_files(mini_repo)
    report = coc.evaluate_coverage(files, rules)
    assert report.files_covered == 0
    assert report.files_uncovered == sorted(
        [
            ".github/CODEOWNERS",
            "docs/readme.md",
            "src/splunk_uc/kept.py",
            "tools/extra.py",
        ]
    )


def test_missing_codeowners_warns_and_remediation(
    coc, mini_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    coc.CODEOWNERS_PATH.unlink()
    out_dir = tmp_path / "out"
    rc = coc.main(["--out", str(out_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "WARN:" in captured.err
    assert coc.DEFAULT_REMEDIATION in captured.err
    md = (out_dir / "codeowners-coverage.md").read_text(encoding="utf-8")
    assert "Remediation" in md
    assert coc.DEFAULT_REMEDIATION in md


def test_git_ls_files_failure_clear_error(
    coc, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def _boom(_root: Path) -> list[Path]:
        raise RuntimeError("git ls-files failed (exit 128): fatal: not a git repo")

    monkeypatch.setattr(coc, "enumerate_repo_files", _boom)
    rc = coc.main(["--check", "--threshold", "0"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err
    assert "git ls-files failed" in captured.err
