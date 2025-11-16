"""Test suite for westupdate tool.

Unlike test_westlock.py which tests against frozen lockfiles with exact SHAs,
this test validates that westupdate can process west.yml manifests and produce
structurally correct output with valid (but not necessarily matching) revisions.
"""

import re
import subprocess
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from conftest import Implementation, get_implementations


FIXTURES_DIR: Final = Path(__file__).parent / "fixtures" / "westupdate"


class ExpectedProject(NamedTuple):
    """Expected project in westupdate output."""

    name: str
    path: str
    url: str


def get_westupdate_test_cases() -> tuple[tuple[str, Path, list[ExpectedProject]], ...]:
    """Discover test cases for westupdate by scanning fixture directories.

    Returns tuples of (test_name, west.yml path, expected projects).
    """
    test_cases = []

    for fixture_dir in FIXTURES_DIR.iterdir():
        if not fixture_dir.is_dir():
            continue

        manifest_path = fixture_dir / "in" / "west.yml"
        if not manifest_path.exists():
            continue

        # Read expected output to extract project list
        out_file = fixture_dir / "out" / "westlock.nix"
        if not out_file.exists():
            continue

        # Parse expected projects from output file
        expected_projects = []
        content = out_file.read_text()

        # Simple regex to extract name, path, url from each project block
        project_pattern = re.compile(
            r'\{\s*'
            r'name\s*=\s*"([^"]+)";\s*'
            r'path\s*=\s*"([^"]+)";\s*'
            r'url\s*=\s*"([^"]+)";',
            re.MULTILINE | re.DOTALL
        )

        for match in project_pattern.finditer(content):
            name, path, url = match.groups()
            expected_projects.append(ExpectedProject(name=name, path=path, url=url))

        if expected_projects:
            test_cases.append((fixture_dir.name, manifest_path, expected_projects))

    return tuple(test_cases)


@pytest.mark.parametrize("impl", get_implementations(), ids=lambda impl: impl.name)
@pytest.mark.parametrize(
    "test_name,manifest_path,expected_projects",
    get_westupdate_test_cases(),
    ids=lambda x: x[0] if isinstance(x, str) else "",
)
def test_westupdate_implementation(
    impl: Implementation,
    test_name: str,
    manifest_path: Path,
    expected_projects: list[ExpectedProject],
    build_implementations: dict[str, Path],
) -> None:
    """Test westupdate implementation produces valid output structure."""

    exe_path: Final = build_implementations[f"{impl.name}-westupdate"]

    print(f"Running {impl.name} westupdate on {test_name}...")
    result: Final = subprocess.run(
        [str(exe_path), str(manifest_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,  # 5 minutes timeout for git cloning
    )

    assert result.returncode == 0, (
        f"Command failed for {impl.name} on {test_name}:\n"
        f"stderr: {result.stderr}\n"
        f"stdout: {result.stdout}"
    )

    output = result.stdout

    # Validate output starts with header comment
    assert output.startswith("# This file is auto-generated"), "Missing auto-generated header"

    # Parse all project entries using regex
    project_pattern = re.compile(
        r'\{\s*'
        r'name\s*=\s*"([^"]+)";\s*'
        r'path\s*=\s*"([^"]+)";\s*'
        r'url\s*=\s*"([^"]+)";\s*'
        r'rev\s*=\s*"([^"]+)";\s*'
        r'sha256\s*=\s*"([^"]+)";\s*'
        r'\}',
        re.MULTILINE | re.DOTALL
    )

    found_projects = project_pattern.findall(output)

    # Validate we found the expected number of projects
    assert len(found_projects) == len(expected_projects), (
        f"Expected {len(expected_projects)} projects, found {len(found_projects)}\n"
        f"Output:\n{output}"
    )

    # Validate each project has the expected structure
    for (name, path, url, rev, sha256), expected in zip(found_projects, expected_projects):
        # Check expected fields match
        assert name == expected.name, f"Project name mismatch: {name} != {expected.name}"
        assert path == expected.path, f"Project path mismatch: {path} != {expected.path}"
        assert url == expected.url, f"Project URL mismatch: {url} != {expected.url}"

        # Validate rev looks like a git commit SHA (40 hex chars)
        assert re.match(r'^[0-9a-f]{40}$', rev), (
            f"Project {name} has invalid revision: {rev} (should be 40-char SHA)"
        )

        # Validate sha256 looks like a nix hash (32 base32 chars)
        assert re.match(r'^[0-9a-z]{32,52}$', sha256), (
            f"Project {name} has invalid sha256: {sha256} (should be nix base32 hash)"
        )

    print(f"✓ {impl.name} westupdate on {test_name} passed validation")
