import re
import sys
from pathlib import Path
from typing import Literal

import semver

LITERAL_PART = Literal["major", "minor", "patch"]


def get_version_from_init(init_path: Path) -> str:
    with init_path.open("r") as file:
        data = file.readline()
    match = re.search(r'^__version__ = "(.*)"', data)
    assert match is not None
    return match.group(1)


def bump_version(version: str, part: LITERAL_PART) -> str:
    match part:
        case "major":
            return semver.bump_major(version)
        case "minor":
            return semver.bump_minor(version)
        case "patch":
            return semver.bump_patch(version)


def update_init_version(init_path: Path, new_version: str) -> None:
    with init_path.open("r") as file:
        lines = file.readlines()

    # Update the first line with the new version
    lines[0] = f'__version__ = "{new_version}"\n'

    with init_path.open("w") as file:
        file.writelines(lines)


def update_readme_badge(readme_path: Path, new_version: str) -> None:
    with readme_path.open("r") as file:
        lines = file.readlines()

    if lines:
        # Update the first line with the new version
        lines[0] = (
            f"![Test Status](https://github.com/TimChild/reflex-clerk-api/actions/workflows/ci.yml/badge.svg?branch=v{new_version})\n"
        )

    with readme_path.open("w") as file:
        file.writelines(lines)


def main(part: LITERAL_PART, init_path: Path, readme_path: Path) -> None:
    current_version = get_version_from_init(init_path)
    new_version = bump_version(current_version, part)
    update_init_version(init_path, new_version)
    update_readme_badge(readme_path, new_version)
    print(f"Successfully bumped from {current_version} to {new_version}")  # noqa: T201


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise ValueError(
            "Usage: bump-version.py <major|minor|patch> <package.__init__.py-path> <readme-path>"
        )
    part = sys.argv[1]
    assert part in ("major", "minor", "patch")
    init_path = Path(sys.argv[2])
    assert init_path.exists()
    readme_path = Path(sys.argv[3])
    assert readme_path.exists()
    main(part, init_path, readme_path)
