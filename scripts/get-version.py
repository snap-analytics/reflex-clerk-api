"""Reads the version from the pyproject.toml file and returns to stdout."""

import sys
from pathlib import Path

import tomlkit


def get_version_from_pyproject_toml(file_path: Path) -> str:
    with file_path.open("r") as file:
        data = tomlkit.parse(file.read())
    version = data["project"]["version"]  # pyright: ignore[reportIndexIssue]
    assert isinstance(version, str)
    return version


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        raise ValueError("Usage: get-version.py <pyproject.toml-path>")
    path = Path(args[1])
    assert path.exists()
    print(get_version_from_pyproject_toml(path))
