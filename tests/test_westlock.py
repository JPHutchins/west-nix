"""Test suite for westlock implementations."""

import subprocess
from pathlib import Path
from typing import NamedTuple, Final

import pytest


REPO_ROOT: Final = Path(__file__).parent.parent
FIXTURES_DIR: Final = Path(__file__).parent / "fixtures"


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


def get_fixture_cases() -> tuple[tuple[str, Path, Path], ...]:
    """Discover all test fixtures with in/out directories."""
    fixtures = []
    for fixture_dir in FIXTURES_DIR.iterdir():
        if not fixture_dir.is_dir():
            continue

        in_dir = fixture_dir / "in"
        out_dir = fixture_dir / "out"

        if in_dir.exists() and out_dir.exists():
            fixtures.append((fixture_dir.name, in_dir, out_dir))

    return fixtures


@pytest.fixture(scope="session")
def build_implementations() -> dict[str, Path]:
    """Build all implementations once per test session."""
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

    return built_exes


@pytest.mark.parametrize("impl", get_implementations(), ids=lambda impl: impl.name)
@pytest.mark.parametrize("fixture_name,in_dir,out_dir", get_fixture_cases())
def test_westlock_implementation(
    impl: Implementation,
    fixture_name: str,
    in_dir: Path,
    out_dir: Path,
    build_implementations: dict[str, Path],
) -> None:
    """Test a westlock implementation against a fixture."""

    input_files: Final = [f for f in in_dir.iterdir() if f.is_file()]
    assert len(input_files) == 1, (
        f"Expected exactly 1 input file in {in_dir}, found {len(input_files)}"
    )
    input_file: Final = input_files[0]

    output_files: Final = [f for f in out_dir.iterdir() if f.is_file()]
    assert len(output_files) == 1, (
        f"Expected exactly 1 output file in {out_dir}, found {len(output_files)}"
    )
    expected_output_file: Final = output_files[0]

    exe_path: Final = build_implementations[impl.name]

    with input_file.open() as stdin_file:
        print(f"Running {impl.name} implementation on {fixture_name}...")
        result: Final = subprocess.run(
            [str(exe_path)],
            stdin=stdin_file,
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0, (
        f"Command failed for {impl.name} on {fixture_name}:\n"
        f"stderr: {result.stderr}\n"
        f"stdout: {result.stdout}"
    )

    expected: Final = expected_output_file.read_text()
    actual: Final = result.stdout
    expected_lines: Final = [line.rstrip() for line in expected.splitlines()]
    actual_lines: Final = [line.rstrip() for line in actual.splitlines()]

    assert actual_lines == expected_lines, (
        f"Output mismatch for {impl.name} on {fixture_name}:\n"
        f"Expected:\n{expected}\n"
        f"Actual:\n{actual}"
    )
