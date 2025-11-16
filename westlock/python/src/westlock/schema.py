"""NamedTuple schema for West lockfile format.

This module defines the exact structure of westlock.yaml files using
NamedTuples for type-safe validation.
"""

from typing import NamedTuple


class WestProject(NamedTuple):
    """A single project in the West manifest."""

    name: str
    url: str
    revision: str
    path: str | None = None
    groups: list[str] | None = None
    west_commands: str | None = None

    @property
    def nix_path(self) -> str:
        """Get the path where this project should be placed in the workspace.

        If no path is specified, the project name is used as the path.
        This matches West's behavior.
        """
        return self.path if self.path is not None else self.name


class WestSelf(NamedTuple):
    """The 'self' section of the West manifest."""

    path: str
    west_commands: str | None = None


class WestManifest(NamedTuple):
    """The manifest section containing projects and configuration."""

    projects: list[WestProject]
    self: WestSelf
    group_filter: list[str] | None = None


class WestLockfile(NamedTuple):
    """The complete West lockfile structure."""

    manifest: WestManifest
