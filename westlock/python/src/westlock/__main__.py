"""CLI entry point for westlock converter."""

import asyncio
import sys

from .generator import NixProject, generate_nix_expression
from .parser import parse_lockfile
from .prefetch import prefetch_git


async def main() -> int:
    """Main entry point for westlock.

    Reads West manifest from stdin and writes Nix expression to stdout.

    Returns:
        Exit code (0 for success, non-zero for error)
    """

    lockfile = parse_lockfile(stream=sys.stdin)

    results = await asyncio.gather(
        *[prefetch_git(project.url, project.revision) for project in lockfile.manifest.projects]
    )

    nix_projects = [
        NixProject(project=project, sha256=result.sha256)
        for project, result in zip(lockfile.manifest.projects, results, strict=True)
    ]

    nix_expr = generate_nix_expression(nix_projects)

    print(nix_expr)

    return 0



if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
