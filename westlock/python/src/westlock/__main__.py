"""CLI entry point for westlock converter."""

import sys

from .generator import NixProject, generate_nix_expression
from .parser import parse_lockfile
from .prefetch import prefetch_git


def main() -> int:
    """Main entry point for westlock.

    Reads West manifest from stdin and writes Nix expression to stdout.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        lockfile = parse_lockfile(stream=sys.stdin)
    except Exception as e:
        print(f"Error parsing lockfile: {e}", file=sys.stderr)
        return 1

    # Prefetch each project
    nix_projects = []
    for project in lockfile.manifest.projects:
        try:
            result = prefetch_git(project.url, project.revision)
            nix_projects.append(NixProject(project=project, sha256=result.sha256))
        except Exception as e:
            print(f"Error prefetching {project.name}: {e}", file=sys.stderr)
            return 1

    # Generate Nix expression
    nix_expr = generate_nix_expression(nix_projects)

    # Write output to stdout
    print(nix_expr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
