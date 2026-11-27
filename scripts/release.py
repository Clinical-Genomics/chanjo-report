"""Prepare a release and print its notes. Needs only the standard library and `uv`.

    python scripts/release.py prepare patch|minor|major|X.Y.Z
    python scripts/release.py notes [VERSION]

`prepare` bumps the version in pyproject.toml and uv.lock with `uv version` and dates the
[unreleased] section of CHANGELOG.md. `notes` prints a changelog section, for the GitHub release.
"""

import argparse
import re
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNRELEASED = "## [unreleased]"
BUMPS = ("major", "minor", "patch")


def current_version(pyproject):
    with open(pyproject, "rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def section(text, version=None):
    """Return the changelog section of a version, or of [unreleased] when no version is given."""
    if version is None:
        is_heading = lambda line: line.strip() == UNRELEASED  # noqa: E731
    else:
        heading = re.compile(rf"^## \[?{re.escape(version)}\]?(\s|$)")
        is_heading = heading.match
    lines = text.splitlines()
    for start, line in enumerate(lines):
        if is_heading(line):
            break
    else:
        raise ValueError(f"CHANGELOG.md has no section for {version or 'unreleased'}")
    body = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip()


def check_unreleased(text):
    """Raise if there is nothing under [unreleased] to release."""
    if not section(text):
        raise ValueError("The [unreleased] section of CHANGELOG.md is empty, nothing to release")


def date_changelog(text, version, today):
    """Date the [unreleased] section as `version` and add a new, empty [unreleased] section."""
    check_unreleased(text)
    dated = f"{UNRELEASED}\n\n## {version} ({today:%Y-%m-%d})"
    return re.sub(rf"^{re.escape(UNRELEASED)}[ \t]*$", lambda _: dated, text, count=1, flags=re.M)


def prepare(target, root=ROOT, run=None, today=None):
    """Bump the version and date the changelog. Returns the new version."""
    run = run or subprocess.run
    if target in BUMPS:
        uv_args = ["uv", "version", "--bump", target]
    elif re.fullmatch(r"\d+\.\d+\.\d+", target):
        uv_args = ["uv", "version", target]
    else:
        raise ValueError(f"'{target}' is not one of {', '.join(BUMPS)} or a version like 1.2.3")
    changelog = root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    check_unreleased(text)  # fail before changing anything if there is nothing to release
    run(uv_args, cwd=root, check=True)
    version = current_version(root / "pyproject.toml")
    changelog.write_text(date_changelog(text, version, today or date.today()), encoding="utf-8")
    return version


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare").add_argument("target", help="patch, minor, major or X.Y.Z")
    commands.add_parser("notes").add_argument("version", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            version = prepare(args.target, root=root)
            print(f"Bumped to {version} and dated CHANGELOG.md. Next:")
            print(
                f"  1. Review `git diff`, commit it on a branch (git switch -c version_{version})"
            )
            print(f'     as "Bump version to {version}", open a pull request and merge it')
            print(
                "  2. On an up-to-date main, publish the release (see Releasing in CONTRIBUTING.md)"
            )
        else:
            version = args.version or current_version(root / "pyproject.toml")
            print(section((root / "CHANGELOG.md").read_text(encoding="utf-8"), version))
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
