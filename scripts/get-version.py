"""Reads the version from the __init__.py file and returns to stdout."""

import re
import sys
from pathlib import Path


def get_version_from_init(init_path: Path) -> str:
    with init_path.open("r") as file:
        data = file.readline()
    match = re.search(r'^__version__ = "(.*)"', data)
    assert match is not None
    return match.group(1)


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        raise ValueError("Usage: get-version.py <package.__init__.py")
    path = Path(args[1])
    assert path.exists()
    print(get_version_from_init(path))  # noqa: T201
