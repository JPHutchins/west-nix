"""Parse West lockfiles into validated NamedTuple structures."""

import sys
from pathlib import Path
from typing import Any, TextIO

import yaml

from .schema import WestLockfile, WestManifest, WestProject, WestSelf


def parse_project(data: dict[str, Any]) -> WestProject:
    """Parse a single project entry from YAML data."""
    return WestProject(
        name=data["name"],
        url=data["url"],
        revision=data["revision"],
        path=data.get("path"),
        groups=data.get("groups"),
        west_commands=data.get("west-commands"),
    )


def parse_self(data: dict[str, Any]) -> WestSelf:
    """Parse the 'self' section from YAML data."""
    return WestSelf(
        path=data["path"],
        west_commands=data.get("west-commands"),
    )


def parse_manifest(data: dict[str, Any]) -> WestManifest:
    """Parse the manifest section from YAML data."""
    projects = [parse_project(p) for p in data["projects"]]
    self_data = parse_self(data["self"])
    group_filter = data.get("group-filter")

    return WestManifest(
        projects=projects,
        self=self_data,
        group_filter=group_filter,
    )


def parse_lockfile(lockfile_path: Path | None = None, stream: TextIO | None = None) -> WestLockfile:
    """Parse a West lockfile from a YAML file or stream.

    Args:
        lockfile_path: Path to the westlock.yaml file (optional if stream is provided)
        stream: File-like object to read from (optional if lockfile_path is provided)

    Returns:
        Validated WestLockfile structure

    Raises:
        ValueError: If neither lockfile_path nor stream is provided
        FileNotFoundError: If the lockfile doesn't exist
        yaml.YAMLError: If the YAML is malformed
        KeyError: If required fields are missing
        TypeError: If field types don't match the schema
    """
    if lockfile_path is None and stream is None:
        raise ValueError("Either lockfile_path or stream must be provided")

    if stream is not None:
        data = yaml.safe_load(stream)
    else:
        with open(lockfile_path) as f:
            data = yaml.safe_load(f)

    if not isinstance(data, dict) or "manifest" not in data:
        raise ValueError("Invalid lockfile: missing 'manifest' key")

    manifest = parse_manifest(data["manifest"])
    return WestLockfile(manifest=manifest)
