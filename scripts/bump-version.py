import sys
from pathlib import Path
from typing import Literal

import semver
import tomlkit

LITERAL_PART = Literal["major", "minor", "patch"]


def get_version_from_pyproject_toml(file_path: Path) -> str:
    with file_path.open("r") as file:
        data = tomlkit.parse(file.read())
    version = data["project"]["version"]  # pyright: ignore[reportIndexIssue]
    assert isinstance(version, str)
    return version


def bump_version(version: str, part: LITERAL_PART) -> str:
    match part:
        case "major":
            return semver.bump_major(version)
        case "minor":
            return semver.bump_minor(version)
        case "patch":
            return semver.bump_patch(version)


def update_toml_project_version(file_path: Path, new_version: str) -> None:
    with file_path.open("r") as file:
        data = tomlkit.parse(file.read())
    data["project"]["version"] = new_version  # pyright: ignore[reportIndexIssue]
    with file_path.open("w") as file:
        file.write(tomlkit.dumps(data))


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


def main(part: LITERAL_PART, pyproject_path: Path, readme_path: Path) -> None:
    current_version = get_version_from_pyproject_toml(pyproject_path)
    new_version = bump_version(current_version, part)
    update_toml_project_version(pyproject_path, new_version)
    update_readme_badge(readme_path, new_version)
    print(f"Successfully bumped from {current_version} to {new_version}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise ValueError(
            "Usage: bump-version.py <major|minor|patch> <pyproject.toml-path> <readme-path>"
        )
    part = sys.argv[1]
    assert part in ("major", "minor", "patch")
    pyproject_path = Path(sys.argv[2])
    assert pyproject_path.exists()
    readme_path = Path(sys.argv[3])
    assert readme_path.exists()
    main(part, pyproject_path, readme_path)
