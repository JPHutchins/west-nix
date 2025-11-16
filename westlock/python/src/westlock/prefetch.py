"""Prefetch git repositories to get SHA256 hashes for Nix."""

import asyncio
import json
import subprocess
from typing import NamedTuple


class PrefetchResult(NamedTuple):
    """Result of prefetching a git repository."""

    sha256: str
    url: str
    rev: str


async def prefetch_git(url: str, rev: str) -> PrefetchResult:
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
        proc = await asyncio.create_subprocess_exec(
            "nix-prefetch-git",
            "--url",
            url,
            "--rev",
            rev,
            "--quiet",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise subprocess.CalledProcessError(
                proc.returncode or 1, "nix-prefetch-git", stderr=error_msg
            )

    except FileNotFoundError:
        raise FileNotFoundError(
            "nix-prefetch-git not found in PATH. "
            "Please ensure Nix is installed and nix-prefetch-git is available."
        )

    data = json.loads(stdout.decode())

    return PrefetchResult(
        sha256=data["sha256"],
        url=data["url"],
        rev=data["rev"],
    )
