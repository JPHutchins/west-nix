"""Prefetch git repositories to get SHA256 hashes for Nix."""

import json
import subprocess
from typing import NamedTuple


class PrefetchResult(NamedTuple):
    """Result of prefetching a git repository."""

    sha256: str
    url: str
    rev: str


def prefetch_git(url: str, rev: str) -> PrefetchResult:
    """Prefetch a git repository using nix-prefetch-git.

    Args:
        url: Git repository URL
        rev: Git revision (commit SHA, tag, or branch)

    Returns:
        PrefetchResult containing the SHA256 hash

    Raises:
        subprocess.CalledProcessError: If nix-prefetch-git fails
        FileNotFoundError: If nix-prefetch-git is not in PATH
        json.JSONDecodeError: If nix-prefetch-git output is not valid JSON
    """
    try:
        result = subprocess.run(
            ["nix-prefetch-git", "--url", url, "--rev", rev, "--quiet"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "nix-prefetch-git not found in PATH. "
            "Please ensure Nix is installed and nix-prefetch-git is available."
        )

    data = json.loads(result.stdout)

    return PrefetchResult(
        sha256=data["sha256"],
        url=data["url"],
        rev=data["rev"],
    )
