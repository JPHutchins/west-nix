"""West update and freeze workflow orchestrator.

This module provides a tool that automates the process of:
1. Creating a temporary West workspace
2. Running west update to clone repos and resolve imports
3. Running west freeze to generate a lockfile with SHAs
4. Piping the frozen manifest to westlock for Nix conversion
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def westupdate(manifest_path: Path) -> int:
    """Run west update workflow and convert to Nix.

    Args:
        manifest_path: Path to the west.yml manifest file

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if not manifest_path.exists():
        print(f"Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        return 1

    # Check that west is available
    if not shutil.which("west"):
        print(
            "Error: west command not found in PATH. "
            "Please install west (pip install west).",
            file=sys.stderr,
        )
        return 1

    # Create temporary workspace
    with tempfile.TemporaryDirectory(prefix="westupdate-") as tmpdir:
        workspace = Path(tmpdir)
        manifest_dir = workspace / "manifest"
        manifest_dir.mkdir()

        # Copy the manifest file
        dest_manifest = manifest_dir / "west.yml"
        shutil.copy(manifest_path, dest_manifest)

        print(f"Created temporary workspace at {workspace}", file=sys.stderr)

        # Initialize west workspace
        print("Initializing west workspace...", file=sys.stderr)
        result = subprocess.run(
            ["west", "init", "-l", "manifest"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Error: west init failed:\n{result.stderr}", file=sys.stderr)
            return result.returncode

        # Run west update
        print("Running west update (this may take a while)...", file=sys.stderr)
        result = subprocess.run(
            ["west", "update"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Error: west update failed:\n{result.stderr}", file=sys.stderr)
            return result.returncode

        print("Update complete. Freezing manifest...", file=sys.stderr)

        # Run west freeze
        result = subprocess.run(
            ["west", "manifest", "--freeze"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Error: west manifest --freeze failed:\n{result.stderr}", file=sys.stderr)
            return result.returncode

        frozen_manifest = result.stdout

        print("Frozen manifest generated. Converting to Nix...", file=sys.stderr)

        # Run westlock on the frozen manifest
        # TODO: run programmatically instead of spawning a subprocess
        result = subprocess.run(
            ["westlock"],
            input=frozen_manifest,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"Error: westlock failed:\n{result.stderr}", file=sys.stderr)
            return result.returncode

        # Output the Nix expression to stdout
        print(result.stdout, end="")

        print("\nConversion complete!", file=sys.stderr)

    return 0


def main() -> int:
    """Main entry point for westupdate CLI."""
    if len(sys.argv) != 2:
        print("Usage: westupdate <west.yml>", file=sys.stderr)
        print(
            "\nGenerates Nix derivations from a West manifest by:\n"
            "1. Creating a temporary workspace\n"
            "2. Running 'west update' to resolve imports and clone repos\n"
            "3. Running 'west manifest --freeze' to generate SHAs\n"
            "4. Converting the frozen manifest to Nix with westlock\n",
            file=sys.stderr,
        )
        return 1

    manifest_path = Path(sys.argv[1])
    return westupdate(manifest_path)


if __name__ == "__main__":
    sys.exit(main())
