"""Shared pytest configuration and fixtures for west-nix tests."""

import subprocess
from pathlib import Path
from typing import Final, NamedTuple

import pytest


REPO_ROOT: Final = Path(__file__).parent.parent


class Implementation(NamedTuple):
    """Describes a westlock implementation."""

    name: str
    build_cmd: tuple[str, ...] | None
    exe_path: Path


def get_implementations() -> tuple[Implementation, ...]:
    """Get list of available westlock implementations."""
    return (
        Implementation(
            name="python",
            build_cmd=("nix", "build", ".#westlock-python", "--out-link", "result-python"),
            exe_path=REPO_ROOT / "result-python/bin/westlock",
        ),
    )


@pytest.fixture(scope="session")
def build_implementations() -> dict[str, Path]:
    """Build all implementations once per test session.

    Returns a dict mapping implementation name to executable path.
    This fixture is shared across all test files to avoid rebuilding.
    """
    built_exes = {}

    for impl in get_implementations():
        if impl.build_cmd:
            print(f"\nBuilding {impl.name} implementation with Nix...")
            result = subprocess.run(
                impl.build_cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                pytest.fail(
                    f"Failed to build {impl.name}:\n"
                    f"stdout: {result.stdout}\n"
                    f"stderr: {result.stderr}"
                )

        if not impl.exe_path.exists():
            pytest.fail(f"Executable not found after build: {impl.exe_path}")

        built_exes[impl.name] = impl.exe_path

    # Also register westupdate executable from the same build
    for impl in get_implementations():
        westupdate_path = impl.exe_path.parent / "westupdate"
        if westupdate_path.exists():
            built_exes[f"{impl.name}-westupdate"] = westupdate_path

    return built_exes
