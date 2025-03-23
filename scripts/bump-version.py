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


def main(part: LITERAL_PART, pyproject_path: Path) -> None:
    current_version = get_version_from_pyproject_toml(pyproject_path)
    new_version = bump_version(current_version, part)
    update_toml_project_version(pyproject_path, new_version)
    print(f"Successfully bumped from {current_version} to {new_version}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise ValueError(
            "Usage: bump-version.py <major|minor|patch> <pyproject.toml-path>"
        )
    part = sys.argv[1]
    assert part in ("major", "minor", "patch")
    path = sys.argv[2]
    assert Path(path).exists()
    main(part, Path(path))
