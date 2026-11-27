"""Tests for scripts/release.py, which prepares releases."""

import importlib.util
import subprocess
from collections.abc import Callable
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "release.py"

CHANGELOG = """# Change log

## [unreleased]
### Added
- A new feature

## 1.1.0 (2026-01-02)
### Fixed
- A bug

## 1.0.0 (2025-12-01)
- First release

## 1.0.0 (2025-12-01)
- Duplicated heading
"""
PYPROJECT = '[project]\nname = "demo"\nversion = "1.1.0"\n'

UvRunner = Callable[..., None]


def load_release_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("release", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load_release_script()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project directory with a changelog and a pyproject.toml at version 1.1.0."""
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    return tmp_path


def fake_uv(new_version: str, calls: list[list[str]]) -> UvRunner:
    """Stand-in for `uv version`, which would rewrite pyproject.toml and uv.lock."""

    def run(args: list[str], cwd: Path, check: bool) -> None:
        calls.append(args)
        (cwd / "pyproject.toml").write_text(PYPROJECT.replace("1.1.0", new_version))

    return run


def test_current_version(project: Path) -> None:
    # GIVEN a project whose pyproject.toml says version 1.1.0
    # WHEN the current version is read
    version = release.current_version(project / "pyproject.toml")

    # THEN it is 1.1.0
    assert version == "1.1.0"


def test_section_of_a_version() -> None:
    # GIVEN a changelog with several versions
    # WHEN the section of 1.1.0 is requested
    notes = release.section(CHANGELOG, "1.1.0")

    # THEN only the content under that heading is returned
    assert notes == "### Fixed\n- A bug"


def test_section_of_unreleased() -> None:
    # GIVEN a changelog with unreleased changes
    # WHEN no version is given
    notes = release.section(CHANGELOG)

    # THEN the unreleased content is returned
    assert notes == "### Added\n- A new feature"


def test_section_uses_the_first_of_duplicated_headings() -> None:
    # GIVEN a changelog where the heading 1.0.0 appears twice
    # WHEN the section of 1.0.0 is requested
    notes = release.section(CHANGELOG, "1.0.0")

    # THEN the first one is used
    assert notes == "- First release"


def test_section_that_does_not_exist() -> None:
    # GIVEN a changelog without a 9.9.9 section
    # WHEN that section is requested
    # THEN it is an error that names the version
    with pytest.raises(ValueError, match="no section for 9.9.9"):
        release.section(CHANGELOG, "9.9.9")


def test_date_changelog_adds_a_new_unreleased_section() -> None:
    # GIVEN a changelog with unreleased changes
    # WHEN it is dated as version 1.2.0
    result = release.date_changelog(CHANGELOG, "1.2.0", date(2026, 3, 4))

    # THEN a new empty [unreleased] section sits above the dated one
    assert "## [unreleased]\n\n## 1.2.0 (2026-03-04)\n### Added\n- A new feature" in result
    assert release.section(result) == ""
    # AND the unreleased changes now belong to 1.2.0
    assert release.section(result, "1.2.0") == "### Added\n- A new feature"
    # AND older sections are untouched
    assert release.section(result, "1.1.0") == "### Fixed\n- A bug"


def test_date_changelog_refuses_an_empty_unreleased_section() -> None:
    # GIVEN a changelog with nothing under [unreleased]
    empty = "## [unreleased]\n\n## 1.0.0 (2025-12-01)\n- x\n"

    # WHEN it is dated
    # THEN it is an error, because there is nothing to release
    with pytest.raises(ValueError, match="empty"):
        release.date_changelog(empty, "1.1.0", date(2026, 3, 4))


@pytest.mark.parametrize(
    ("target", "new_version", "uv_args"),
    [
        ("minor", "1.2.0", ["uv", "version", "--bump", "minor"]),
        ("patch", "1.1.1", ["uv", "version", "--bump", "patch"]),
        ("2.0.0", "2.0.0", ["uv", "version", "2.0.0"]),
    ],
)
def test_prepare(project: Path, target: str, new_version: str, uv_args: list[str]) -> None:
    # GIVEN a project with unreleased changes
    calls: list[list[str]] = []

    # WHEN a release is prepared with a bump or an exact version
    version = release.prepare(
        target, root=project, run=fake_uv(new_version, calls), today=date(2026, 3, 4)
    )

    # THEN uv is asked to set that version
    assert calls == [uv_args]
    assert version == new_version
    # AND the changelog is dated with it
    text = (project / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [unreleased]\n\n## {new_version} (2026-03-04)" in text


def test_prepare_rejects_a_bad_target(project: Path) -> None:
    # GIVEN a target that is neither a bump nor a version number
    calls: list[list[str]] = []

    # WHEN a release is prepared
    # THEN it is an error
    with pytest.raises(ValueError, match="not one of"):
        release.prepare("sideways", root=project, run=fake_uv("1.2.0", calls))
    # AND uv was never called
    assert calls == []


def test_prepare_changes_nothing_when_there_is_nothing_to_release(project: Path) -> None:
    # GIVEN a changelog with nothing under [unreleased]
    (project / "CHANGELOG.md").write_text("## [unreleased]\n\n## 1.1.0 (2026-01-02)\n- x\n")
    calls: list[list[str]] = []

    # WHEN a release is prepared
    # THEN it is an error
    with pytest.raises(ValueError, match="empty"):
        release.prepare("minor", root=project, run=fake_uv("1.2.0", calls))
    # AND the version was not bumped
    assert calls == []
    assert release.current_version(project / "pyproject.toml") == "1.1.0"


def test_main_prints_notes_for_the_current_version(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # GIVEN a project at version 1.1.0
    # WHEN the notes are requested without a version
    exit_code = release.main(["notes"], root=project)

    # THEN the notes of 1.1.0 are printed
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "### Fixed\n- A bug"


def test_main_prints_notes_for_a_given_version(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # GIVEN a changelog with an older version 1.0.0
    # WHEN the notes of that version are requested
    exit_code = release.main(["notes", "1.0.0"], root=project)

    # THEN its notes are printed
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "- First release"


def test_main_reports_errors(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # GIVEN a changelog without a 9.9.9 section
    # WHEN the notes of 9.9.9 are requested
    exit_code = release.main(["notes", "9.9.9"], root=project)

    # THEN the script fails with the reason on stderr
    assert exit_code == 1
    assert "no section for 9.9.9" in capsys.readouterr().err


def test_main_reports_a_failing_uv(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # GIVEN uv failing when it is asked to bump the version
    def failing_uv(args: list[str], cwd: Path, check: bool) -> None:
        raise subprocess.CalledProcessError(2, args)

    monkeypatch.setattr(release.subprocess, "run", failing_uv)

    # WHEN a release is prepared
    exit_code = release.main(["prepare", "minor"], root=project)

    # THEN the script fails with the reason on stderr
    assert exit_code == 1
    assert "Error:" in capsys.readouterr().err
    # AND the changelog is not dated
    assert "## [unreleased]\n### Added" in (project / "CHANGELOG.md").read_text()


def test_main_prepare_prints_next_steps(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # GIVEN uv bumping the version to 1.2.0
    calls: list[list[str]] = []
    monkeypatch.setattr(release.subprocess, "run", fake_uv("1.2.0", calls))

    # WHEN a release is prepared
    exit_code = release.main(["prepare", "minor"], root=project)

    # THEN the new version and the branch to use are printed
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Bumped to 1.2.0" in output
    assert "version_1.2.0" in output
